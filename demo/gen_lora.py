"""LoRA arms on the GENERATED dataset (train and tune cells only; test_same, test_hard, the old cells and the old adapters are never
touched). One process per run.

  python demo/gen_lora.py --arm teacher|method_original|neutral|wrong_rule|answer_only [--lr 3e-4] [--seed 0]

Arms (targets are distributions over the five option letters, per case and option order):
  teacher / method_original / neutral / wrong_rule   context distillation: the model's own first-token letter distribution with the
        frozen teacher paragraph / the earlier method paragraph / the same-length neutral text / "Offer half the stated cost." as the
        Notes block, computed before training;   answer_only  uniform over the letters of the case's best offers (ceiling).
Loss: cross-entropy of the answer letter at P1 against the target over the five letters, using the letters' FULL-VOCABULARY log-probs.
LoRA rank 4, alpha 8, q/k/v/o, fp32 adapter weights, AdamW, one optimizer step per case (its fixed 3 option orders), gradient
checkpointing, at most 5 epochs, early stopping (patience 2) on a SELECTION set of 42 train cells that are not in the training set
(demo/gen/lora_select_cells.json, 14 per type, name variant 0, five orders). The lr is chosen on the same set. The 42 TUNE cells are scored
only once, at the best epoch, and are used for the verdict only (they are not used for any selection).
Training set: demo/gen/lora_train_cells.json (100 train cells, one fixed name variant each, 3 fixed orders per case: 300 examples)."""
from __future__ import annotations

import argparse, hashlib, json, os, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import torch

import common
import gen_cases as g
import gen_notes
from refimpl import core, phase3, runtime
from refimpl.local_gemma2 import CHOICE_SYSTEM, LocalGemma2, build_messages, ensure_prompt_not_too_long

LETTERS = phase3.LETTERS
OUT = os.path.join(common.ROOT, "demo_out", "gen_lora")
ADAPTERS = os.path.join(common.ROOT, "demo_out", "adapters")
ARMS = ("teacher", "method_original", "neutral", "wrong_rule", "answer_only")
TRAIN_CELLS = os.path.join(g.OUT, "lora_train_cells.json")
SELECT_CELLS = os.path.join(g.OUT, "lora_select_cells_B.json")   # (set A, lora_select_cells.json, is the teacher-loop feedback/winner set)


def run_id(arm, lr, seed):
  return f"gen_{arm}_lr{lr:.0e}_s{seed}"


def make_train_cells():
  """100 train cells (34 / 33 / 33 per type), one name variant and three option orders per case, fixed by seed."""
  cells = [c for c in json.load(open(os.path.join(g.OUT, "cells.json")))["cells"] if c["split"] == "train"]
  rng = np.random.Generator(np.random.PCG64(20261124))
  chosen = []
  for typ, n in zip(g.TYPES, (34, 33, 33)):
    pool = sorted(c["cell"] for c in cells if c["type"] == typ)
    chosen += [pool[i] for i in sorted(rng.choice(len(pool), n, replace=False))]
  spec = {c: {"name_variant": int(rng.integers(0, 2)), "orders": sorted(int(x) for x in rng.choice(5, 3, replace=False))} for c in chosen}
  json.dump(spec, open(TRAIN_CELLS, "w"), indent=1)
  return spec


def make_select_cells():
  """(superseded: demo/gen/lora_select_cells_B.json was built once, disjoint from the training cells, the loop set A and the teacher packet cells)"""
  raise RuntimeError("lora_select_cells_B.json is missing")
  """42 train cells outside the 100 training cells (14 per type), fixed by seed: used for early stopping and the lr choice."""
  used = set(json.load(open(TRAIN_CELLS)))
  cells = [c for c in json.load(open(os.path.join(g.OUT, "cells.json")))["cells"] if c["split"] == "train" and c["cell"] not in used]
  rng = np.random.Generator(np.random.PCG64(20261125))
  chosen = []
  for typ in g.TYPES:
    pool = sorted(c["cell"] for c in cells if c["type"] == typ)
    chosen += [pool[i] for i in sorted(rng.choice(len(pool), 14, replace=False))]
  json.dump(chosen, open(SELECT_CELLS, "w"), indent=1)
  return chosen


def score_case(lm, c, notes=None, orders=None):
  """order-averaged first-token probabilities over the case's grid, per-order list, letter mass"""
  per, masses = [], []
  for order in (orders or g.orders()):
    user, l2p = gen_notes.render_notes(c, order, notes)
    lm.letter_scores(user, phase3.LETTERS, whole_answer=False)
    pr = core.softmax_scores(dict(lm.last_first_token), l2p)
    per.append([float(pr[k]) for k in c["grid"]]); masses.append(float(lm.last_letter_mass))
  return np.mean(per, axis=0), per, float(np.mean(masses))


def main():
  ap = argparse.ArgumentParser()
  ap.add_argument("--arm", required=True, choices=ARMS)
  ap.add_argument("--lr", type=float, default=3e-4)
  ap.add_argument("--seed", type=int, default=0)
  ap.add_argument("--rank", type=int, default=4)
  ap.add_argument("--max-epochs", type=int, default=5)
  ap.add_argument("--patience", type=int, default=2)
  ap.add_argument("--limit", type=int, default=0, help="smoke test: this many train cells and tune cases")
  args = ap.parse_args()
  t_start = time.time()
  rid = run_id(args.arm, args.lr, args.seed) + ("_smoke" if args.limit else "")
  os.makedirs(OUT, exist_ok=True)
  cells = {c["cell"]: c for c in json.load(open(os.path.join(g.OUT, "cells.json")))["cells"]}
  allcases = {c["cid"]: c for c in map(json.loads, open(os.path.join(g.OUT, "cases.jsonl")))}
  spec = json.load(open(TRAIN_CELLS)) if os.path.exists(TRAIN_CELLS) else make_train_cells()
  train = [allcases[f"{k}-n{v['name_variant']}"] for k, v in spec.items()]
  tune_all = [c for c in allcases.values() if c["split"] == "tune"]
  sel_cells = json.load(open(SELECT_CELLS)) if os.path.exists(SELECT_CELLS) else make_select_cells()
  assert not set(sel_cells) & set(spec), "selection cells overlap the training cells"
  assert not set(sel_cells) & set(json.load(open(os.path.join(g.OUT, "lora_select_cells.json")))), "selection set B overlaps the teacher-loop set A"
  assert not set(sel_cells) & set(json.load(open(os.path.join(g.OUT, "packet_cells.json")))), "selection set B overlaps the teacher packet cells"
  tune_mon = [allcases[f"{k}-n0"] for k in sel_cells]          # SELECTION set (train cells outside the training set), name variant 0
  mon_train = train[::5][:20]                                  # small train-side monitor (not used for selection)
  if args.limit:
    train, tune_mon, tune_all, mon_train = train[:args.limit], tune_mon[:args.limit], tune_all[:args.limit], mon_train[:args.limit]
  assert all(c["split"] in ("train", "tune") for c in train + tune_all + tune_mon)
  model, tok = runtime.load_gemma("9b", "cuda")
  lm = LocalGemma2(model, tok)
  letter_ix = torch.tensor([tok.convert_tokens_to_ids(l) for l in LETTERS])
  orders = g.orders()
  texts = {"teacher": open(os.path.join(g.OUT, "teacher_method.txt")).read().strip(),
           "method_original": __import__("textrows").METHOD, "neutral": open(os.path.join(g.OUT, "neutral_text.txt")).read().strip(),
           "wrong_rule": __import__("textrows").FIXED["wrong_rule"]}

  # ---------------------------------------------------------------- targets
  teach = {}
  targets = {}
  for c in train:
    for oi in spec[c["cell"]]["orders"]:
      if args.arm == "answer_only":
        lab = cells[c["cell"]]["best_positions"]
        t = [0.0] * 5
        for pos in lab:                                           # letter j shows grid position orders[oi][j]
          t[list(orders[oi]).index(pos)] = 1.0 / len(lab)
      else:
        _, per, _ = score_case(lm, c, texts[args.arm], [orders[oi]])
        # per is the price distribution by grid position; the target is by letter
        t = [per[0][orders[oi][j]] for j in range(5)]
      targets[(c["cid"], oi)] = t
  print(f"{rid}: {len(train)} train cases ({len(targets)} examples), {len(tune_all)} tune cases; targets built ({time.time() - t_start:.0f}s)", flush=True)
  examples = []
  for c in train:
    for oi in spec[c["cell"]]["orders"]:
      user, _ = gen_notes.render_notes(c, orders[oi], None)
      ids = lm.encode(lm.render(build_messages(CHOICE_SYSTEM, ensure_prompt_not_too_long(user, 1)), True))[0]
      examples.append({"cid": c["cid"], "ids": ids, "target": torch.tensor(targets[(c["cid"], oi)], dtype=torch.float32)})
  by_case = {}
  for ex in examples:
    by_case.setdefault(ex["cid"], []).append(ex)

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

  def loss_on(ex):
    hidden = model.model(input_ids=ex["ids"][None], use_cache=False).last_hidden_state[:, -1]
    logits = model.lm_head(hidden).float()
    if cap:
      logits = torch.tanh(logits / cap) * cap
    lp = torch.log_softmax(logits, dim=-1)[0, letter_ix.to(logits.device)]
    return -(ex["target"].to(lp.device) * lp).sum()

  def evaluate(cases):
    model.eval()
    probs, mass = {}, {}
    for c in cases:
      p, _, m = score_case(lm, c)
      probs[c["cid"]], mass[c["cid"]] = [float(x) for x in p], m
    model.train()
    return probs, mass

  def summarize(probs, mass, cases):
    soft = {}
    for c in cases:
      lab = cells[c["cell"]]
      soft.setdefault(c["cell"], []).append(float(lab["best_payoff"] - np.dot(probs[c["cid"]], lab["payoffs"])))
    cm = {k: float(np.mean(v)) for k, v in soft.items()}
    below = [(c["C"], float(np.dot(probs[c["cid"]], c["grid"]))) for c in cases if c["type"] == "below"]
    sl = float(np.polyfit([x for x, _ in below], [y for _, y in below], 1)[0]) if len({x for x, _ in below}) >= 2 else None
    return {"soft_regret": float(np.mean(list(cm.values()))), "mass": float(np.mean(list(mass.values()))), "slope_stated_cost_below": sl,
            "soft_by_type": {t: float(np.mean([v for k, v in cm.items() if cells[k]["type"] == t])) for t in g.TYPES if any(cells[k]["type"] == t for k in cm)}}

  # the training forward path must equal the scoring path (adapter at its zero initialisation)
  model.eval()
  with torch.no_grad():
    worst = 0.0
    for c in train[:3]:
      oi = spec[c["cell"]]["orders"][0]
      user, _ = gen_notes.render_notes(c, orders[oi], None)
      ids = lm.encode(lm.render(build_messages(CHOICE_SYSTEM, ensure_prompt_not_too_long(user, 1)), True))[0]
      hidden = model.model(input_ids=ids[None], use_cache=False).last_hidden_state[:, -1]
      lg = model.lm_head(hidden).float()
      lg = torch.tanh(lg / cap) * cap if cap else lg
      lp = torch.log_softmax(lg, dim=-1)[0, letter_ix.to(lg.device)].cpu().numpy()
      lm.letter_scores(user, phase3.LETTERS, whole_answer=False)
      ref = np.array([lm.last_first_token[l] for l in LETTERS])
      worst = max(worst, float(np.max(np.abs(lp - ref))))
  assert worst < 1e-2, f"training forward path differs from the scoring path by {worst} nats"
  model.train()
  print(f"training path vs scoring path max abs log-prob difference {worst:.1e}", flush=True)
  save_dir = os.path.join(ADAPTERS, rid)
  history = []
  tp, tm = evaluate(tune_mon)
  s0 = summarize(tp, tm, tune_mon)
  plain_saved = {r["cid"]: r for r in map(json.loads, open(os.path.join(common.ROOT, "demo_out", "gen_plain_scores.jsonl")))}
  dev = max(abs(a - b) for c in tune_mon for a, b in zip(tp[c["cid"]], plain_saved[c["cid"]]["probs"]))
  assert dev < 1e-3, f"epoch-0 scoring differs from the saved plain scores by {dev}"
  trp, trm = evaluate(mon_train)
  history.append({"epoch": 0, "train_loss": None, "tune": s0, "train_sample": summarize(trp, trm, mon_train), "sec": None})
  print(f"epoch 0 (= plain): selection-set soft regret {s0['soft_regret']:.3f} (max dev from saved plain {dev:.1e})", flush=True)
  best = {"epoch": 0, "tune": s0}
  peft_model.save_pretrained(save_dir)
  bad = 0
  rng = np.random.Generator(np.random.PCG64(args.seed))
  cids = [c["cid"] for c in train]
  model.train()
  for epoch in range(1, args.max_epochs + 1):
    t = time.time()
    losses = []
    for i in rng.permutation(len(cids)):
      opt.zero_grad(set_to_none=True)
      exs = by_case[cids[i]]
      for ex in exs:
        loss = loss_on(ex) / len(exs)
        loss.backward()
        losses.append(float(loss) * len(exs))
      opt.step()
    t_train = time.time() - t
    tp, tm = evaluate(tune_mon)
    tn = summarize(tp, tm, tune_mon)
    trp, trm = evaluate(mon_train)
    trs = summarize(trp, trm, mon_train)
    history.append({"epoch": epoch, "train_loss": float(np.mean(losses)), "tune": tn, "train_sample": trs, "sec": time.time() - t, "sec_training": t_train})
    print(f"epoch {epoch}: loss {np.mean(losses):.3f}; selection-set soft {tn['soft_regret']:.3f} (mass {tn['mass']:.2f}); train-sample soft {trs['soft_regret']:.3f}; {time.time() - t:.0f}s", flush=True)
    with open(os.path.join(common.ROOT, "demo_out", "lora_progress.jsonl"), "a") as pf:
      pf.write(json.dumps({"run": rid, "arm": args.arm, "lr": args.lr, "seed": args.seed, "epoch": epoch, "train_soft_regret": trs["soft_regret"],
                           "heldout_soft_regret": tn["soft_regret"], "heldout_letter_mass": tn["mass"], "seconds": time.time() - t}) + "\n")
    if tn["soft_regret"] < best["tune"]["soft_regret"] - 1e-9:
      best = {"epoch": epoch, "tune": tn}
      peft_model.save_pretrained(save_dir)
      bad = 0
    else:
      bad += 1
      if bad >= args.patience:
        print(f"early stop after epoch {epoch} (best epoch {best['epoch']})", flush=True)
        break
  # full tune set (both variants, five orders) with the best adapter
  best_sd = __import__("safetensors.torch", fromlist=["load_file"]).load_file(os.path.join(save_dir, "adapter_model.safetensors"))
  from peft.utils import set_peft_model_state_dict
  rr = set_peft_model_state_dict(peft_model, best_sd)
  assert not getattr(rr, "unexpected_keys", None), f"best-adapter reload: unexpected keys {rr.unexpected_keys[:3]}"
  bp, bm = evaluate(tune_mon)
  rl = summarize(bp, bm, tune_mon)["soft_regret"]
  assert abs(rl - best["tune"]["soft_regret"]) < 1e-3, f"reloaded best adapter scores {rl}, expected {best['tune']['soft_regret']}"
  fp, fm = evaluate(tune_all)
  full = summarize(fp, fm, tune_all)
  res = {"run_id": rid, "arm": args.arm, "lr": args.lr, "seed": args.seed, "rank": args.rank, "trainable_parameters": n_train,
         "best_epoch": best["epoch"], "best_epoch_is_zero": best["epoch"] == 0, "select_best": best["tune"], "tune_monitor_best": best["tune"], "tune_full_best": full, "tune_probs_best": fp, "tune_mass_best": fm,
         "history": history, "epochs_run": len(history) - 1, "adapter_dir": os.path.relpath(save_dir, common.ROOT), "wall_s": time.time() - t_start,
         "adapter_sha256": hashlib.sha256(open(os.path.join(save_dir, "adapter_model.safetensors"), "rb").read()).hexdigest(),
         "adapter_config_sha256": hashlib.sha256(open(os.path.join(save_dir, "adapter_config.json"), "rb").read()).hexdigest(),
         "sec_per_epoch": float(np.mean([h["sec"] for h in history[1:]])) if len(history) > 1 else None,
         "note": "lr and early stopping use the selection set (train cells outside the training set); the tune cells are scored once at the best epoch"}
  json.dump(res, open(os.path.join(OUT, f"{rid}.json"), "w"), indent=1)
  print(f"GENLORA {rid} COMPLETED: best epoch {best['epoch']}, selection set {best['tune']['soft_regret']:.3f}, tune full {full['soft_regret']:.3f}, {time.time() - t_start:.0f}s", flush=True)


if __name__ == "__main__":
  main()
