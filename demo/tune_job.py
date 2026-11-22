"""Step 7 tuning job (tuning cases only; in-sample).

Strength is a fraction of the mean plain P1 residual norm at the layer (mean over
the tuning cases of |h_L| at P1, from demo_out/p1_acts.pt). Every direction -- the
candidate vectors, their negation and every random or Gaussian reference -- is
normalised to unit length and multiplied by that norm, so the grid value is the
fraction and all directions are compared at equal norm.
Grid (29 points): no steering, plus layers 6, 9, ..., 24 x fractions 0.02, 0.05,
0.10, 0.20. Full budget (five orders): template, offer_lower, sentence and the
negated template. Matched budget (one order per case, rotating with the variant):
template, 20 random directions (differences of plain P1 activations between tuning
cases from different cells; pairs drawn with PCG64 seed 11) and 5 Gaussian
directions (seed 12). Unit: the cell; intervals by resampling cells.
Checkpoint: each finished (vector, budget, layer, fraction) point is appended to
demo_out/tune_partial.jsonl (flushed and fsynced); --resume skips points already
there, so an interruption loses at most the point being computed.
Writes demo_out/tune_results.json and prints the steercheck table.

  python demo/tune_job.py --sanity       offer_lower check on 4 tuning cases, layer 18
  python demo/tune_job.py --estimate     time 20 passes and print the job estimate
  python demo/tune_job.py [--resume]     the job
"""
import argparse, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import torch
import common, scoring, steercheck
from refimpl import core, runtime, steering
from refimpl.local_gemma2 import LocalGemma2

LAYERS = tuple(L for L in steering.LAYERS if L <= 24)          # 6 .. 24: 7 layers
GRID_FILE = os.path.join(common.DEMO_DIR, "tune_grid.json")     # demo/choose_grid.py
if os.path.exists(GRID_FILE):
  _g = json.load(open(GRID_FILE))
  FRACTIONS, MODE = tuple(_g["fractions"]), _g["mode"]
  assert tuple(_g["layers"]) == LAYERS
else:
  FRACTIONS, MODE = (0.02, 0.05, 0.10, 0.20), "p1"
GRID = [(None, 0.0)] + [(L, f) for L in LAYERS for f in FRACTIONS]
PARTIAL = os.path.join(common.ROOT, "demo_out", "tune_partial.jsonl")
FULL = ("template", "offer_lower", "sentence", "cheap")
N_RANDOM, N_GAUSS = 20, 5

ap = argparse.ArgumentParser()
ap.add_argument("--model", default="9b")
ap.add_argument("--estimate", action="store_true")
ap.add_argument("--sanity", action="store_true")
ap.add_argument("--resume", action="store_true")
ap.add_argument("--out", default=os.path.join(common.ROOT, "demo_out", "tune_results.json"))
args = ap.parse_args()
assert len(GRID) <= 30
model, tok = runtime.load_gemma(args.model, "cuda")
lm = LocalGemma2(model, tok)
cases = common.cases_in("tuning")
assert all(common.load_splits()["case_split"][p.pid] == "tuning" for p in cases)
plain = torch.load(os.path.join(common.ROOT, "demo_out", "p1_acts.pt"))
# Mean plain P1 residual norm per layer over the tuning cases: the strength unit.
resid = {L: float(np.mean([plain[p.pid][L].float().norm().item() for p in cases])) for L in LAYERS}
def unit_scaled(v):
  """{layer: unit(v_L) * resid_L}: alpha in the grid is then a fraction of resid_L."""
  return {L: v[L].float() / v[L].float().norm() * resid[L] for L in LAYERS}
vecs = torch.load(os.path.join(common.ROOT, "demo_out", "vectors.pt"))
vectors = {n: unit_scaled(vecs[n]) for n in FULL}
rng = np.random.Generator(np.random.PCG64(11))
reference = {}
while len(reference) < N_RANDOM:
  i, j = rng.integers(0, len(cases), 2)
  a, b = cases[i], cases[j]
  if a.cell == b.cell:
    continue
  d = plain[a.pid].float() - plain[b.pid].float()
  reference[f"random {len(reference) + 1}"] = unit_scaled(d)
g = np.random.Generator(np.random.PCG64(12))
hidden = vectors["template"][LAYERS[0]].numel()
for n in range(N_GAUSS):
  v = torch.from_numpy(g.standard_normal(hidden).astype(np.float32))
  reference[f"gauss {n + 1}"] = unit_scaled({L: v for L in LAYERS})

def score(p, steer, orders):
  r = scoring.score(lm, p, orders=orders, steer=steer, steer_from=MODE)
  return r.probs, r.mass

full = lambda p: scoring.ORDERS
matched = lambda p: [core.cyclic_orders()[(p.variant - 1) % 5]]
best = lambda p: set(core.oracle_bids(p))
value = lambda p, k: core.payoff(p, int(k))
cell = lambda p: str(p.cell)

if args.sanity:
  # offer_lower at fractions 0.10 and 0.20 of the residual norm at layer 18 should
  # lower the expected offer; its negation should raise it.
  L, sub = 18, cases[:4]
  out = {"layer": L, "resid_norm": resid[L], "cases": [p.pid for p in sub], "rows": []}
  plain_e = {p.pid: scoring.score(lm, p).expected() for p in sub}
  for frac in (0.10, 0.20):
    for sign in (1.0, -1.0):
      v = sign * frac * vectors["offer_lower"][L]
      e = {p.pid: scoring.score(lm, p, steer=(L, v)).expected() for p in sub}
      d = [e[k] - plain_e[k] for k in e]
      out["rows"].append({"vector": ("" if sign > 0 else "-") + "offer_lower", "fraction": frac,
                          "mean_change_in_expected_offer": float(np.mean(d)),
                          "per_case": [round(x, 3) for x in d]})
  for r in out["rows"]:
    want = "lower" if not r["vector"].startswith("-") else "raise"
    ok = (r["mean_change_in_expected_offer"] < 0) == (want == "lower")
    r["expected"] = want
    r["as_expected"] = ok
    print(f"{r['vector']:>13} at {r['fraction']:.2f}: mean change in expected offer "
          f"{r['mean_change_in_expected_offer']:+.3f} (should {want}: {'yes' if ok else 'NO'}) "
          f"per case {r['per_case']}")
  print(f"plain expected offers: { {k: round(v, 3) for k, v in plain_e.items()} }")
  json.dump(out, open(os.path.join(common.ROOT, "demo_out", "tune_sanity.json"), "w"), indent=1)
  sys.exit(0)

if args.estimate:
  t = time.perf_counter()
  for p in cases[:4]:
    score(p, (12, vectors["template"][12]), scoring.ORDERS)
  per_pass = (time.perf_counter() - t) / 20
  n_full = (len(FULL) + 1) * (len(GRID) - 1) * len(cases) * 5
  n_matched = (1 + N_RANDOM + N_GAUSS) * (len(GRID) - 1) * len(cases)
  n_eval = (4 * 5 + 26) * len(cases) + 6 * len(cases)
  total = n_full + n_matched + n_eval
  print(json.dumps({"sec_per_pass": per_pass, "passes": total, "full_budget_passes": n_full,
                    "matched_budget_passes": n_matched, "estimate_hours": total * per_pass / 3600}))
  sys.exit(0)

class JsonlCheckpoint(steercheck.MemoryCheckpoint):
  """One JSON line per finished grid point, flushed and fsynced."""

  def __init__(self, path, resume):
    super().__init__()
    if os.path.exists(path) and not resume:
      sys.exit(f"{path} exists: use --resume to continue it, or move it away to start over")
    if os.path.exists(path):
      for line in open(path):
        try:
          r = json.loads(line)
        except json.JSONDecodeError:
          continue                       # a line cut by an interruption: recomputed
        self.data[tuple(r["key"])] = {pid: ({int(k): v for k, v in pr.items()}, m)
                                      for pid, (pr, m) in r["results"].items()}
    self.f = open(path, "a")
    print(f"checkpoint: {len(self.data)} points already done", flush=True)

  def put(self, key, value):
    super().put(key, value)
    self.f.write(json.dumps({"key": list(key), "results": value}) + "\n")
    self.f.flush()
    os.fsync(self.f.fileno())


t0 = time.time()
ckpt = JsonlCheckpoint(PARTIAL, args.resume)
res = steercheck.run_controls(score, cases, best, value, cell, vectors, GRID, full, matched,
                              reference, n_boot=2000, negate=["template"], checkpoint=ckpt,
                              case_key=lambda p: p.pid,
                              log=lambda m: print(f"[{time.time() - t0:6.0f}s] {m}", flush=True))
res["grid"] = GRID
res["position_mode"] = MODE
res["strength"] = "fraction of the mean plain P1 residual norm at the layer (tuning cases)"
res["resid_norm"] = resid
res["cases"] = [p.pid for p in cases]
res["note"] = "tuning cases only; settings tuned and evaluated on the same cases (in-sample)"
json.dump(res, open(args.out, "w"), indent=1, default=float)
print("\n".join(steercheck.format_table(res, colour=False)))
print(f"TUNE JOB COMPLETED in {time.time() - t0:.0f}s", flush=True)
# Keep the results ledger current (CPU, reads saved files only).
import subprocess  # noqa: E402
subprocess.run([sys.executable, os.path.join(common.DEMO_DIR, "ledger.py")], check=False)
