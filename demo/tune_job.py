"""Step 7 tuning job (tuning cases only; in-sample).

Grid: layers 6, 9, ..., 24 (7 of steering.LAYERS) x steering.ALPHAS (4) = 28 points,
plus no steering. Full budget (five orders): template, offer_lower, sentence and the
negated template. Matched budget (one order per case, rotating with the variant):
template, 20 random directions (differences of plain P1 activations between tuning
cases from different cells; pairs drawn with PCG64 seed 11) and 5 Gaussian
directions (seed 12), all rescaled to the template norm per layer. Unit: the cell;
intervals by resampling cells. Writes demo_out/tune_results.json and prints the
steercheck table.

  python demo/tune_job.py --estimate     time 20 passes and print the job estimate
"""
import argparse, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import torch
import common, scoring, steercheck
from refimpl import core, runtime, steering
from refimpl.local_gemma2 import LocalGemma2

LAYERS = tuple(L for L in steering.LAYERS if L <= 24)          # 6 .. 24: 7 layers
GRID = [(None, 0.0)] + [(L, a) for L in LAYERS for a in steering.ALPHAS]
FULL = ("template", "offer_lower", "sentence")
N_RANDOM, N_GAUSS = 20, 5

ap = argparse.ArgumentParser()
ap.add_argument("--model", default="9b")
ap.add_argument("--estimate", action="store_true")
ap.add_argument("--out", default=os.path.join(common.ROOT, "demo_out", "tune_results.json"))
args = ap.parse_args()
assert len(GRID) <= 30
model, tok = runtime.load_gemma(args.model, "cuda")
lm = LocalGemma2(model, tok)
cases = common.cases_in("tuning")
assert all(common.load_splits()["case_split"][p.pid] == "tuning" for p in cases)
vecs = torch.load(os.path.join(common.ROOT, "demo_out", "vectors.pt"))
vectors = {n: {L: vecs[n][L].float() for L in LAYERS} for n in FULL}
tmpl_norm = {L: float(vectors["template"][L].norm()) for L in LAYERS}
plain = torch.load(os.path.join(common.ROOT, "demo_out", "p1_acts.pt"))
rng = np.random.Generator(np.random.PCG64(11))
reference = {}
while len(reference) < N_RANDOM:
  i, j = rng.integers(0, len(cases), 2)
  a, b = cases[i], cases[j]
  if a.cell == b.cell:
    continue
  d = plain[a.pid].float() - plain[b.pid].float()
  reference[f"random {len(reference) + 1}"] = {L: d[L] * tmpl_norm[L] / float(d[L].norm()) for L in LAYERS}
g = np.random.Generator(np.random.PCG64(12))
hidden = vectors["template"][LAYERS[0]].numel()
for n in range(N_GAUSS):
  v = torch.from_numpy(g.standard_normal(hidden).astype(np.float32))
  reference[f"gauss {n + 1}"] = {L: v * tmpl_norm[L] / float(v.norm()) for L in LAYERS}

def score(p, steer, orders):
  r = scoring.score(lm, p, orders=orders, steer=steer)
  return r.probs, r.mass

full = lambda p: scoring.ORDERS
matched = lambda p: [core.cyclic_orders()[(p.variant - 1) % 5]]
best = lambda p: set(core.oracle_bids(p))
value = lambda p, k: core.payoff(p, int(k))
cell = lambda p: str(p.cell)

if args.estimate:
  t = time.perf_counter()
  for p in cases[:4]:
    score(p, (12, vectors["template"][12]), scoring.ORDERS)
  per_pass = (time.perf_counter() - t) / 20
  n_full = 4 * (len(GRID) - 1) * len(cases) * 5
  n_matched = (1 + N_RANDOM + N_GAUSS) * (len(GRID) - 1) * len(cases)
  n_eval = (4 * 5 + 26) * len(cases) + 6 * len(cases)
  total = n_full + n_matched + n_eval
  print(json.dumps({"sec_per_pass": per_pass, "passes": total, "full_budget_passes": n_full,
                    "matched_budget_passes": n_matched, "estimate_hours": total * per_pass / 3600}))
  sys.exit(0)

t0 = time.time()
res = steercheck.run_controls(score, cases, best, value, cell, vectors, GRID, full, matched,
                              reference, n_boot=2000, negate=["template"],
                              log=lambda m: print(f"[{time.time() - t0:6.0f}s] {m}", flush=True))
res["grid"] = GRID
res["cases"] = [p.pid for p in cases]
res["note"] = "tuning cases only; settings tuned and evaluated on the same cases (in-sample)"
json.dump(res, open(args.out, "w"), indent=1, default=float)
print("\n".join(steercheck.format_table(res, colour=False)))
print(f"TUNE JOB COMPLETED in {time.time() - t0:.0f}s", flush=True)
