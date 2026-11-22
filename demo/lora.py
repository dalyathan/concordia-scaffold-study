"""LoRA arms (rung 5): distillation and supervision, trained on the 11 train cells,
early-stopped on the 6 held-out tune cells (demo/splits_lora.json). Test cells and
variants 1-14 are never used.

  python demo/lora.py --arm ARM [--lr 3e-4] [--seed 0] [--perm 0] [--rank 4]

Arms (targets are distributions over the five option letters, one per case and
option order):
  method       the model's own first-token letter distribution with the frozen
               method paragraph as the Notes block, computed before training
               (context distillation: can the sentence live in the weights?)
  neutral      the same with the same-length neutral text (matched control)
  wrong_rule   the same with the wrong-rule text "Offer half the stated cost."
  answer_only  uniform over the letters of the case's best offers
  shuffled     answer_only targets with the best-offer sets permuted over the
               train CELLS by a derangement that also avoids cells with an
               identical set (--perm 0, 1, 2 give three different ones); the
               fraction of labels still correct is reported
  const2       one-hot on the letter of 2 coins (a constant-offer target)
  template     distillation of the template reasoning, which names the best offer
               (a LEAKY upper bound)
Loss (letter-only): cross-entropy of the answer letter at P1 against the target
distribution over the five letters, using the letters' FULL-VOCABULARY log-probs
(ordinary SFT on the answer token). It equals the renormalised cross-entropy plus
-log(letter mass), so every arm is pushed equally to keep the answer format and the
arms differ only in which letter they favour. Letter mass is logged. (The first
version used the renormalised distribution only; letter mass collapsed to 0.01 in
one epoch, see demo_out/dead_ends/.)
LoRA: rank 4 (--rank), alpha 2 x rank, q/k/v/o projections, float32 adapter
weights, AdamW, one optimizer step per case (its five orders), gradient
checkpointing, at most 8 epochs, early stopping on the held-out tune cells' mean
cell soft regret (patience 2). The best adapter is saved with PEFT. Each epoch logs
the train-cell and held-out-cell regret, letter mass and seconds. At the best epoch
the free-text answer (scoring.say) is also scored on the held-out cases."""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import torch

import common
import pairs_template
import scoring
import steer_lib
import textrows
from refimpl import analysis, core, phase3, runtime
from refimpl.local_gemma2 import CHOICE_SYSTEM, LocalGemma2, build_messages, ensure_prompt_not_too_long

LETTERS = phase3.LETTERS
LORA_DIR = os.path.join(common.ROOT, "demo_out", "lora")
ADAPTERS = os.path.join(common.ROOT, "demo_out", "adapters")
ARMS = ("method", "neutral", "wrong_rule", "answer_only", "shuffled", "const2", "template")


def run_id(arm, perm, lr, seed, rank=4):
  # no "." in a run id: PEFT adapter names become module-dict keys
  return f"{arm}{perm if arm == 'shuffled' else ''}_lr{lr:.0e}_s{seed}" + (f"_r{rank}" if rank != 4 else "")


def derangement_of_sets(cells, sets, perm_id):
  """A permutation of the cells (cell i gets the best-offer set of cell perm[i]) with
  no fixed point and no cell receiving a set equal to its own; seeded by perm_id."""
  rng = np.random.Generator(np.random.PCG64(1000 + perm_id))
  n = len(cells)
  for _ in range(100000):
    q = rng.permutation(n)
    if all(q[i] != i and sets[q[i]] != sets[i] for i in range(n)):
      return [int(x) for x in q]
  raise RuntimeError("no derangement found")


def build_targets(arm, train, perm_id, teacher_fn):
  """-> {pid: [target over letters for each of the 5 orders]}, info"""
  info = {}
  orders = core.cyclic_orders()
  def letters_of(order):
    return {k: LETTERS[order.index(k)] for k in core.PRICES}
  labels = {p.pid: set(core.oracle_bids(p)) for p in train}
  if arm == "shuffled":
    cells = sorted({p.cell for p in train}, key=str)
    sets = [frozenset(core.oracle_bids(next(p for p in train if p.cell == c))) for c in cells]
    q = derangement_of_sets(cells, sets, perm_id)
    assign = {cells[i]: set(sets[q[i]]) for i in range(len(cells))}
    labels = {p.pid: assign[p.cell] for p in train}
    true = {p.pid: set(core.oracle_bids(p)) for p in train}
    info = {"permutation_of_cells": q,
            "assigned_equals_true": float(np.mean([labels[i] == true[i] for i in labels])),
            "assigned_overlaps_true": float(np.mean([bool(labels[i] & true[i]) for i in labels])),
            "mean_jaccard": float(np.mean([len(labels[i] & true[i]) / len(labels[i] | true[i]) for i in labels]))}
  out = {}
  for p in train:
    per = []
    for oi, order in enumerate(orders):
      lt = letters_of(list(order))
      if arm in ("answer_only", "shuffled"):
        t = [1.0 / len(labels[p.pid]) if k in labels[p.pid] else 0.0 for k in sorted(core.PRICES, key=lambda k: LETTERS.index(lt[k]))]
      elif arm == "const2":
        t = [1.0 if k == 2 else 0.0 for k in sorted(core.PRICES, key=lambda k: LETTERS.index(lt[k]))]
      else:
        probs = teacher_fn(p, oi)
        t = [probs[k] for k in sorted(core.PRICES, key=lambda k: LETTERS.index(lt[k]))]
      per.append(t)
    out[p.pid] = per
  # targets are listed in letter order a..e: entry j is the probability of the price at letter j
  return out, info


def main():
  ap = argparse.ArgumentParser()
  ap.add_argument("--arm", required=True, choices=ARMS)
  ap.add_argument("--perm", type=int, default=0)
  ap.add_argument("--lr", type=float, default=3e-4)
  ap.add_argument("--seed", type=int, default=0)
  ap.add_argument("--rank", type=int, default=4)
  ap.add_argument("--model", default="9b")
  ap.add_argument("--device", default="cuda")
  ap.add_argument("--max-epochs", type=int, default=8)
  ap.add_argument("--patience", type=int, default=2)
  ap.add_argument("--limit", type=int, default=0, help="smoke test: this many train/tune cases")
  ap.add_argument("--out", default=LORA_DIR)
  ap.add_argument("--adapters", default=ADAPTERS)
  args = ap.parse_args()
  t_start = time.time()
  rid = run_id(args.arm, args.perm, args.lr, args.seed, args.rank) + ("_smoke" if args.limit else "")
  os.makedirs(args.out, exist_ok=True)
  model, tok = runtime.load_gemma(args.model, args.device)
  lm = LocalGemma2(model, tok)
  train, tune = steer_lib.lora_cases("lora_train"), steer_lib.lora_cases("lora_tune")
  split = common.load_splits()["case_split"]
  assert all(split[p.pid] in ("build", "tuning") for p in train + tune)       # development cells only
  assert all(p.variant in common.BUILD_VARIANTS + common.TUNING_VARIANTS for p in train + tune)
  if args.limit:
    train, tune = train[:args.limit], tune[:args.limit]
  letter_ids = [tok.convert_tokens_to_ids(l) for l in LETTERS]
  orders = core.cyclic_orders()

  # ---------------------------------------------------------------- targets
  texts = {"method": lambda p: textrows.METHOD, "neutral": lambda p: textrows.row_text("neutral", p),
           "wrong_rule": lambda p: textrows.FIXED["wrong_rule"],
           "template": lambda p: pairs_template.paragraph(p, min(core.oracle_bids(p)))}
  import hashlib
  cache_path = os.path.join(args.out, f"teacher_{args.arm}{'_smoke' if args.limit else ''}.json")
  teacher_cache = json.load(open(cache_path)) if os.path.exists(cache_path) else {}
  def teacher(p, oi):
    """The teacher's renormalised letter distribution; the cache key includes a hash of
    the teacher text, so an edited text never reuses stale targets."""
    text = texts[args.arm](p)
    k = f"{hashlib.sha1(text.encode()).hexdigest()[:12]}|{p.pid}|{oi}"
    if k not in teacher_cache:
      r = scoring.score(lm, p, notes=text, orders=[orders[oi]])
      teacher_cache[k] = {str(a): b for a, b in r.per_order[0].items()}
    return {int(a): b for a, b in teacher_cache[k].items()}
  targets, tinfo = build_targets(args.arm, train, args.perm, teacher)
  teach_eval = {}                      # per-order teacher distributions on train and tune cases, for fidelity
  if args.arm in texts:
    for p in train + tune:
      teach_eval[p.pid] = [teacher(p, oi) for oi in range(len(orders))]
    json.dump(teacher_cache, open(cache_path, "w"))
  print(f"{rid}: {len(train)} train cases, {len(tune)} held-out tune cases; targets built "
        f"({time.time() - t_start:.0f}s) {tinfo}", flush=True)

  examples = {}
  for p in train:
    for oi, order in enumerate(orders):
      user, _ = scoring.user_turn(scoring.key(p), None, tuple(order), False)
      ids = lm.encode(lm.render(build_messages(CHOICE_SYSTEM, ensure_prompt_not_too_long(user, 1)), True))[0]
      examples.setdefault(p.pid, []).append({"ids": ids, "target": torch.tensor(targets[p.pid][oi], dtype=torch.float32)})

  # ------------------------------------------------------------------ model
  from peft import LoraConfig, get_peft_model
  torch.manual_seed(args.seed)
  cfg = LoraConfig(r=args.rank, lora_alpha=2 * args.rank, lora_dropout=0.0, bias="none",
                   target_modules=["q_proj", "k_proj", "v_proj", "o_proj"], task_type="CAUSAL_LM")
  peft_model = get_peft_model(model, cfg)
  for _, prm in peft_model.named_parameters():
    if prm.requires_grad:
      prm.data = prm.data.float()
  params = [prm for prm in peft_model.parameters() if prm.requires_grad]
  n_train = sum(prm.numel() for prm in params)
  model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
  cap = model.config.final_logit_softcapping
  opt = torch.optim.AdamW(params, lr=args.lr, weight_decay=0.0)
  letter_ix = torch.tensor(letter_ids)

  def loss_on(ex):
    hidden = model.model(input_ids=ex["ids"][None], use_cache=False).last_hidden_state[:, -1]
    logits = model.lm_head(hidden).float()
    if cap:
      logits = torch.tanh(logits / cap) * cap
    # Full-vocabulary log-probabilities of the five letters (the answer token, as in ordinary
    # SFT). This equals the cross-entropy on the letter distribution renormalised over the
    # five letters PLUS -log(letter mass): every arm is also pushed to keep the answer
    # format, so arms differ only in WHICH letter they favour. (A renormalised-only loss let
    # the letter mass collapse to 0.01 in one epoch; demo_out/dead_ends/.)
    lp = torch.log_softmax(logits, dim=-1)[0, letter_ix.to(logits.device)]
    return -(ex["target"].to(lp.device) * lp).sum()

  def evaluate(cases):
    model.eval()
    rs = {p.pid: scoring.score(lm, p) for p in cases}
    model.train()
    soft = {p.pid: core.soft_regret(p, rs[p.pid].probs) for p in cases}
    hard = {p.pid: core.hard_regret(p, rs[p.pid].top) for p in cases}
    cm = lambda d: float(np.mean(list(analysis.cell_means(d, cases).values())))
    out = {"soft_regret": cm(soft), "hard_regret": cm(hard), "mass": float(np.mean([r.mass for r in rs.values()])),
           "expected": float(np.mean([r.expected() for r in rs.values()])),
           "probs": {pid: r.probs for pid, r in rs.items()}, "tops": {pid: r.top for pid, r in rs.items()}}
    if teach_eval:                                  # fidelity to the arm's own teacher
      kl = []
      for p in cases:
        for oi in range(len(orders)):
          t, st = teach_eval[p.pid][oi], rs[p.pid].per_order[oi]
          kl.append(sum(t[k] * (np.log(max(t[k], 1e-12)) - np.log(max(st[k], 1e-12))) for k in core.PRICES if t[k] > 0))
      out["kl_teacher_student"] = float(np.mean(kl))
    below = [p for p in cases if p.C is not None and p.C < p.V]      # slope of the offer on the stated cost
    if len(below) >= 3 and len({p.C for p in below}) >= 2:
      out["slope_stated_cost"] = float(np.polyfit([p.C for p in below], [rs[p.pid].expected() for p in below], 1)[0])
    return out

  def say_eval(cases, tops):
    model.eval()
    out = {}
    for p in cases:
      text, k = scoring.say(lm, p)
      out[p.pid] = {"offer": k, "agrees_with_first_token": (k == tops[p.pid]) if k is not None else None,
                    "hard_regret": core.hard_regret(p, k) if k is not None else None}
    model.train()
    ag = [v["agrees_with_first_token"] for v in out.values() if v["agrees_with_first_token"] is not None]
    hr = [v["hard_regret"] for v in out.values() if v["hard_regret"] is not None]
    return {"agreement": float(np.mean(ag)) if ag else None, "say_hard_regret": float(np.mean(hr)) if hr else None,
            "n": len(out), "per_case": out}

  strip = lambda d: {k: v for k, v in d.items() if k not in ("probs", "tops")}
  save_dir = os.path.join(args.adapters, rid)
  history = []
  tune0, train0 = evaluate(tune), evaluate(train)
  history.append({"epoch": 0, "train_loss": None, "tune": strip(tune0), "train": strip(train0), "sec": None})
  print(f"epoch 0 (= plain): held-out tune soft regret {tune0['soft_regret']:.3f}, train {train0['soft_regret']:.3f}", flush=True)
  say0 = say_eval(tune, tune0["tops"])
  best = {"epoch": 0, "tune": tune0, "train": train0, "say": say0}
  peft_model.save_pretrained(save_dir)
  bad = 0
  g = np.random.Generator(np.random.PCG64(args.seed))
  pids = [p.pid for p in train]
  model.train()
  for epoch in range(1, args.max_epochs + 1):
    t = time.time()
    losses = []
    for i in g.permutation(len(pids)):
      opt.zero_grad(set_to_none=True)
      for ex in examples[pids[i]]:
        loss = loss_on(ex) / len(orders)
        loss.backward()
        losses.append(float(loss) * len(orders))
      opt.step()
    t_train = time.time() - t
    tn, tr = evaluate(tune), evaluate(train)
    history.append({"epoch": epoch, "train_loss": float(np.mean(losses)), "tune": strip(tn), "train": strip(tr),
                    "sec": time.time() - t, "sec_training": t_train})
    print(f"epoch {epoch}: loss {np.mean(losses):.3f}; held-out tune soft {tn['soft_regret']:.3f} (mass {tn['mass']:.2f}); "
          f"train soft {tr['soft_regret']:.3f} (mass {tr['mass']:.2f}); {time.time() - t:.0f}s/epoch", flush=True)
    if tn["soft_regret"] < best["tune"]["soft_regret"] - 1e-9:
      best = {"epoch": epoch, "tune": tn, "train": tr, "say": say_eval(tune, tn["tops"])}
      peft_model.save_pretrained(save_dir)
      bad = 0
    else:
      bad += 1
      if bad >= args.patience:
        print(f"early stop after epoch {epoch} (best epoch {best['epoch']})", flush=True)
        break
  res = {"run_id": rid, "arm": args.arm, "perm": args.perm, "lr": args.lr, "seed": args.seed, "rank": args.rank,
         "trainable_parameters": n_train, "targets_info": tinfo, "best_epoch": best["epoch"],
         "tune_best": strip(best["tune"]), "train_best": strip(best["train"]),
         "train_min_soft_regret": min(h["train"]["soft_regret"] for h in history),
         "train_final_soft_regret": history[-1]["train"]["soft_regret"],
         "tune_probs_best": best["tune"]["probs"],
         "train_probs_best": best["train"]["probs"], "say_plain": say0, "say_best": best["say"],
         "history": history, "epochs_run": len(history) - 1,
         "adapter_dir": os.path.relpath(save_dir, common.ROOT), "wall_s": time.time() - t_start,
         "adapter_sha256": __import__("hashlib").sha256(open(os.path.join(save_dir, "adapter_model.safetensors"), "rb").read()).hexdigest(),
         "sec_per_epoch": float(np.mean([h["sec"] for h in history[1:]])) if len(history) > 1 else None,
         "note": "early stopping on the held-out tune cells, so their numbers are selected-on (in-sample)"}
  json.dump(res, open(os.path.join(args.out, f"{rid}.json"), "w"), indent=1)
  print(f"LORA {rid} COMPLETED: best epoch {best['epoch']}, held-out tune soft regret {best['tune']['soft_regret']:.3f}, "
        f"train soft regret {best['train']['soft_regret']:.3f}, {time.time() - t_start:.0f}s", flush=True)


if __name__ == "__main__":
  main()
