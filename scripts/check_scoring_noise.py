"""Numerical noise of the scoring in regret units, and the cost of each pass.

Off-grid prompts only (variants 13-14 with V = 9, 10, which no phase uses), 28
prompts x 2 Notes settings (none; 1,500 tokens of format-matched filler) x 5
orders. For each, p(k) is computed four ways:
  first-token at P1 from the prefix pass (the registered primary);
  first-token at P1 read from the sequential whole-answer passes;
  first-token at P1 read from one batched whole-answer pass;
  whole-answer, sequential (registered) and batched.
Reports only differences between these numerical routes, as soft regret in
coins (prompt level and two-variant cell means), against 10% of the 0.05-coin
smallest effect of interest; plus time per pass. No regret level is reported."""
import argparse, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
import torch
from examples.modular.environment.modules import fruitville_haggling as fv
from refimpl import conditions, core, phase3, runtime
from refimpl.local_gemma2 import LocalGemma2

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="logs/check_scoring_noise.json")
args = ap.parse_args()
model, tok = runtime.load_gemma("9b", "cuda")
lm = LocalGemma2(model, tok, sequential=True)
openings = list(fv.VISUAL_SCENE_OPENINGS)
prompts = [p for v in (13, 14) for p in core.prompt_set([v], values=(9, 10))]
assert all(p.V not in core.VALUES + core.EXT_VALUES for p in prompts) and len(prompts) == 28
filler = conditions.qa_filler(openings, 1500, tok)
routes = ("first_prefix", "first_seq", "first_batched", "whole_seq", "whole_batched")
reg = {r: {} for r in routes}
t_prefix, t_whole_seq, n_tok = [], [], []
for p in prompts:
  for nname, notes in (("N0", None), ("filler1500", filler)):
    acc = {r: [] for r in routes}
    for order in core.cyclic_orders():
      user, l2p = phase3.decision_user_turn(p, openings[p.opening_index], notes, order)
      torch.cuda.synchronize(); t = time.perf_counter()
      lm.letter_scores(user, phase3.LETTERS, whole_answer=False)
      torch.cuda.synchronize(); t_prefix.append(time.perf_counter() - t)
      first_prefix = dict(lm.last_first_token)
      t = time.perf_counter()
      seq, p1, _ = lm.letter_scores(user, phase3.LETTERS, sequential=True)
      torch.cuda.synchronize(); t_whole_seq.append(time.perf_counter() - t)
      n_tok.append(p1 + 1)
      assert lm.last_first_token == first_prefix          # prefix pass is deterministic
      first_seq = dict(lm.last_first_token_wholepass)
      bat, _, _ = lm.letter_scores(user, phase3.LETTERS, sequential=False)
      first_bat = dict(lm.last_first_token_wholepass)
      for r, sc in (("first_prefix", first_prefix), ("first_seq", first_seq),
                    ("first_batched", first_bat), ("whole_seq", seq), ("whole_batched", bat)):
        acc[r].append(core.softmax_scores(sc, l2p))
    for r in routes:
      mean_p = {k: float(np.mean([d[k] for d in acc[r]])) for k in core.PRICES}
      reg[r][(p.pid, nname)] = core.soft_regret(p, mean_p)
def diffs(a, b):
  keys = sorted(reg[a])
  d = np.array([reg[a][k] - reg[b][k] for k in keys])
  cells = {}
  for (pid, n), x in zip(keys, d):
    p = next(q for q in prompts if q.pid == pid)
    cells.setdefault((p.cell, n), []).append(x)
  dc = np.array([np.mean(v) for v in cells.values()])
  return {"prompt_max_abs": float(np.max(np.abs(d))), "prompt_mean_abs": float(np.mean(np.abs(d))),
          "cell_max_abs": float(np.max(np.abs(dc))), "cell_mean_abs": float(np.mean(np.abs(dc))),
          "n_prompt_settings": int(len(d)), "n_cells": int(len(dc))}
res = {"comparisons": {
         "first_prefix_vs_first_seq": diffs("first_prefix", "first_seq"),
         "first_prefix_vs_first_batched": diffs("first_prefix", "first_batched"),
         "whole_seq_vs_whole_batched": diffs("whole_seq", "whole_batched")},
       "threshold_coins": 0.005,
       "tokens_per_prefix": {"min": int(min(n_tok)), "max": int(max(n_tok))},
       "sec_prefix_pass_mean": float(np.mean(t_prefix)),
       "sec_whole_answer_5_passes_mean": float(np.mean(t_whole_seq))}
for k, v in res["comparisons"].items():
  v["pass"] = v["cell_max_abs"] < res["threshold_coins"]
json.dump(res, open(args.out, "w"), indent=1)
print(json.dumps(res, indent=1))
