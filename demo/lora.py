"""Rung 5: LoRA adapters trained on build cases with a letter-only loss.

  python demo/lora.py --arm answer_only|template|shuffled [--model 9b] [--device cuda]

Training data: the 34 build cases x the five option orders, plain prompt (no Notes).
Loss (letter-only): at P1, the full-vocabulary log-probabilities of the five option
letters only, against a target distribution over the letters:
  answer_only  uniform over the letters of the case's best offers (core.oracle_bids);
  template     the model's own first-token letter distribution with the template
               reasoning paragraph (pairs_template.paragraph(case, smallest best
               offer)) as the Notes block, computed before training (context
               distillation of the template reasoning into the plain prompt);
  shuffled     the answer_only targets, with the best-offer sets permuted across the
               build cases (PCG64 seed 0): a label-noise control.
LoRA: rank 4, alpha 8, dropout 0, on q/k/v/o projections, float32 adapter weights,
AdamW lr 1e-4, one optimizer step per case (its five orders), seed 0, gradient
checkpointing. Early stopping on the tuning cases: after every epoch, the mean cell
soft regret (order-averaged first-token p(k), five orders); patience 2; at most 8
epochs. The best adapter is saved with PEFT's save_pretrained to
demo_out/adapters/<arm>/ (live loading: scoring.load_adapters). Never touches test
cases or variants 1-14. Writes demo_out/lora_<arm>.json."""
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
from refimpl import analysis, core, phase3, runtime
from refimpl.local_gemma2 import CHOICE_SYSTEM, LocalGemma2, build_messages, ensure_prompt_not_too_long

ap = argparse.ArgumentParser()
ap.add_argument("--arm", required=True, choices=("answer_only", "template", "shuffled"))
ap.add_argument("--model", default="9b")
ap.add_argument("--device", default="cuda")
ap.add_argument("--rank", type=int, default=4)
ap.add_argument("--lr", type=float, default=1e-4)
ap.add_argument("--max-epochs", type=int, default=8)
ap.add_argument("--patience", type=int, default=2)
ap.add_argument("--limit", type=int, default=0, help="smoke test: use only this many build/tuning cases")
ap.add_argument("--out", default=os.path.join(common.ROOT, "demo_out"))
args = ap.parse_args()
torch.manual_seed(0)
T_START = time.time()
LETTERS = phase3.LETTERS

model, tok = runtime.load_gemma(args.model, args.device)
lm = LocalGemma2(model, tok)
build = common.cases_in("build")
tuning = common.cases_in("tuning")
split = common.load_splits()["case_split"]
assert all(split[p.pid] == "build" for p in build) and all(split[p.pid] == "tuning" for p in tuning)
if args.limit:
  build, tuning = build[:args.limit], tuning[:args.limit]
letter_ids = [tok.convert_tokens_to_ids(l) for l in LETTERS]
assert all(isinstance(i, int) and i > 0 for i in letter_ids)


def prefix_ids(p, order):
  user, l2p = scoring.user_turn(scoring.key(p), None, tuple(order), False)
  ids = lm.encode(lm.render(build_messages(CHOICE_SYSTEM, ensure_prompt_not_too_long(user, 1)), True))[0]
  return ids, l2p


# ----------------------------------------------------------------- targets
best_sets = {p.pid: core.oracle_bids(p) for p in build}
if args.arm == "shuffled":
  rng = np.random.Generator(np.random.PCG64(0))
  perm = rng.permutation(len(build))
  best_sets = {p.pid: core.oracle_bids(build[perm[i]]) for i, p in enumerate(build)}
examples = []
t0 = time.time()
for p in build:
  for order in core.cyclic_orders():
    ids, l2p = prefix_ids(p, order)
    if args.arm == "template":
      r = scoring.score(lm, p, notes=pairs_template.paragraph(p, min(core.oracle_bids(p))), orders=[order])
      target = torch.tensor([r.per_order[0][l2p[l]] for l in LETTERS])
    else:
      best = best_sets[p.pid]
      target = torch.tensor([1.0 / len(best) if l2p[l] in best else 0.0 for l in LETTERS])
    examples.append({"pid": p.pid, "ids": ids, "target": target / target.sum()})
print(f"{len(examples)} training examples ({args.arm}) in {time.time() - t0:.0f}s", flush=True)


# ------------------------------------------------------------------- model
from peft import LoraConfig, get_peft_model  # noqa: E402

cfg = LoraConfig(r=args.rank, lora_alpha=2 * args.rank, lora_dropout=0.0, bias="none",
                 target_modules=["q_proj", "k_proj", "v_proj", "o_proj"], task_type="CAUSAL_LM")
peft_model = get_peft_model(model, cfg)
for n, prm in peft_model.named_parameters():
  if prm.requires_grad:
    prm.data = prm.data.float()
n_train = sum(prm.numel() for prm in peft_model.parameters() if prm.requires_grad)
print(f"trainable parameters: {n_train:,}", flush=True)
model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
cap = model.config.final_logit_softcapping
opt = torch.optim.AdamW([prm for prm in peft_model.parameters() if prm.requires_grad], lr=args.lr,
                        weight_decay=0.0)


def loss_on(ex):
  hidden = model.model(input_ids=ex["ids"][None], use_cache=False).last_hidden_state[:, -1]
  logits = model.lm_head(hidden).float()
  if cap:
    logits = torch.tanh(logits / cap) * cap
  logp = torch.log_softmax(logits, dim=-1)[0, letter_ids]
  return -(ex["target"].to(logp.device) * logp).sum()


def evaluate(cases) -> dict:
  model.eval()
  with torch.no_grad():
    rs = {p.pid: scoring.score(lm, p) for p in cases}
  model.train()
  soft = {p.pid: core.soft_regret(p, rs[p.pid].probs) for p in cases}
  hard = {p.pid: core.hard_regret(p, rs[p.pid].top) for p in cases}
  cm = lambda d: float(np.mean(list(analysis.cell_means(d, cases).values())))
  return {"soft_regret": cm(soft), "hard_regret": cm(hard),
          "mass": float(np.mean([rs[p.pid].mass for p in cases])),
          "expected_offer": float(np.mean([rs[p.pid].expected() for p in cases])),
          "probs": {pid: r.probs for pid, r in rs.items()}}


save_dir = os.path.join(args.out, "adapters", args.arm)
history = []
ev = evaluate(tuning)
history.append({"epoch": 0, "train_loss": None, **{k: v for k, v in ev.items() if k != "probs"}})
print(f"epoch 0 (= plain): tuning soft regret {ev['soft_regret']:.3f}", flush=True)
best = {"epoch": 0, "soft_regret": ev["soft_regret"], "probs": ev["probs"]}
peft_model.save_pretrained(save_dir)
bad = 0
by_case = {}
for ex in examples:
  by_case.setdefault(ex["pid"], []).append(ex)
g = np.random.Generator(np.random.PCG64(0))
model.train()
for epoch in range(1, args.max_epochs + 1):
  t = time.time()
  losses = []
  for i in g.permutation(len(by_case)):
    opt.zero_grad(set_to_none=True)
    for ex in list(by_case.values())[i]:
      loss = loss_on(ex) / 5
      loss.backward()
      losses.append(float(loss) * 5)
    opt.step()
  ev = evaluate(tuning)
  history.append({"epoch": epoch, "train_loss": float(np.mean(losses)),
                  **{k: v for k, v in ev.items() if k != "probs"}})
  print(f"epoch {epoch}: train loss {np.mean(losses):.3f}; tuning soft regret {ev['soft_regret']:.3f}, "
        f"hard {ev['hard_regret']:.3f}, mass {ev['mass']:.2f} ({time.time() - t:.0f}s)", flush=True)
  if ev["soft_regret"] < best["soft_regret"] - 1e-9:
    best = {"epoch": epoch, "soft_regret": ev["soft_regret"], "probs": ev["probs"]}
    peft_model.save_pretrained(save_dir)
    bad = 0
  else:
    bad += 1
    if bad >= args.patience:
      print(f"early stop after epoch {epoch} (best epoch {best['epoch']})", flush=True)
      break
res = {"arm": args.arm, "model": args.model, "rank": args.rank, "lr": args.lr,
       "wall_s": time.time() - T_START,
       "trainable_parameters": n_train, "n_train_examples": len(examples),
       "best_epoch": best["epoch"], "history": history, "adapter_dir": os.path.relpath(save_dir, common.ROOT),
       "tuning_probs_best": best["probs"],
       "note": "early stopping on the tuning cases, so tuning results are in-sample"}
if args.arm == "shuffled":
  res["shuffle_permutation"] = [int(x) for x in perm]
json.dump(res, open(os.path.join(args.out, f"lora_{args.arm}{'_smoke' if args.limit else ''}.json"), "w"),
          indent=1)
print(f"LORA {args.arm} COMPLETED: best epoch {best['epoch']}, tuning soft regret {best['soft_regret']:.3f}",
      flush=True)
# Keep the results ledger current (CPU, reads saved files only).
import subprocess  # noqa: E402
subprocess.run([sys.executable, os.path.join(common.DEMO_DIR, "ledger.py")], check=False)
