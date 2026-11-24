"""CPU follow-up to demo/gen_curve_report.py after gate G2 (post hoc, labelled as such; scores nothing new; tune cells only).
Adds: (A) curve and comparisons on tune cells whose decision problem is NOT in the N=100 training subset;
(B) bootstrap that resamples seeds together with (V, grid) clusters; per-seed 'within 0.05 of examples-100' counts;
(C) the corrected prediction tally (probability statements P2a-c, P8b are scored by Brier only);
(D) hard-minus-soft against the rule-soft-100 seed spread, and the largest gap share the intervals allow hard targets to have closed.
Writes demo_out/gen_curve_followup.md. Runs the report script first (deterministic; rewrites the same report files)."""
import os, runpy, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ns = runpy.run_path(os.path.join(HERE, "gen_curve_report.py"))
np, TUNE, cells, S, R, P, SUBS, prob, cellp, soft, CLUS_W, cboot, fmt, SC, ROOT = (ns[k] for k in
  ("np", "TUNE", "cells", "S", "R", "P", "SUBS", "prob", "cellp", "soft", "CLUS_W", "cboot", "fmt", "SC", "ROOT"))
tp100 = {prob(k) for k in SUBS[100]}
UNC = [i for i, k in enumerate(TUNE) if prob(k) not in tp100]
L = ["# Follow-up after gate G2 (post hoc, CPU, tune cells only)", ""]
L += [f"## A. Tune cells whose decision problem is not in the N = 100 training subset ({len(UNC)} cells of {len(TUNE)})", "",
      "| Arm | soft regret [95% by (V, grid)] on these cells |", "| --- | --- |"]
for name in ["plain", "always-cheapest", "stated-cost rule", "examples-10", "examples-25", "examples-50", "examples-100", "rule-soft-25", "rule-soft-100 (3 seeds)", "rule-hard-25", "rule-hard-100", "cheapest-label-25"]:
  if name in S:
    b = cboot(S[name], idx=UNC); L.append(f"| {name} | {b[0]:.3f} [{b[1]:.3f}, {b[2]:.3f}] |")
L += ["", "Comparisons on these cells (first minus second):", ""]
for a, b in (("examples-10", "examples-100"), ("examples-25", "examples-100"), ("examples-50", "examples-100"), ("rule-soft-25", "examples-25"), ("rule-hard-25", "examples-25"),
             ("rule-soft-100 (3 seeds)", "examples-100"), ("rule-hard-100", "examples-100"), ("rule-hard-25", "rule-soft-25"), ("rule-hard-100", "rule-soft-100 seed 0")):
  if a in S and b in S:
    L.append(f"- {a} - {b}: {fmt(cboot(S[a] - S[b], idx=UNC))}")
# B. seeds + clusters
def per_seed(name):
  return np.array([soft({k: cellp(r)[k] for k in TUNE}) for r in R[name]])   # seeds x cells
rng = np.random.default_rng(0)
cl = [np.array(c) for c in CLUS_W]
ref = per_seed("examples-100")
L += ["", "## B. Seed-and-cluster bootstrap and per-seed counts (examples-N minus examples-100)", "",
      "Per-seed tune soft regret and whether it is within 0.05 of the examples-100 3-seed mean (%.3f):" % float(np.mean(S["examples-100"])), ""]
for n in (10, 25, 50, 100):
  ps = per_seed(f"examples-{n}"); m = ps.mean(1)
  L.append(f"- examples-{n}: seeds {', '.join('%.3f' % v for v in m)}; within 0.05 of examples-100 mean: {int((m <= float(np.mean(S['examples-100'])) + 0.05).sum())} of {len(m)}")
L += [""]
for n in (10, 25, 50):
  ps = per_seed(f"examples-{n}"); vals = []
  for _ in range(10000):
    ix = rng.integers(0, len(cl), len(cl)); cells_ix = np.concatenate([cl[j] for j in ix])
    sa = ps[rng.integers(0, len(ps), len(ps))][:, cells_ix].mean(); sb = ref[rng.integers(0, len(ref), len(ref))][:, cells_ix].mean()
    vals.append(sa - sb)
  vals = np.array(vals)
  L.append(f"- examples-{n} - examples-100, seeds resampled with clusters: {float(np.mean(S[f'examples-{n}'] - S['examples-100'])):+.3f} [{np.quantile(vals, .025):+.3f}, {np.quantile(vals, .975):+.3f}]; "
           f"share of resamples with difference <= 0.05: {float(np.mean(vals <= 0.05)):.2f}")
# C. corrected tally
prob_ids = {"P2a", "P2b", "P2c", "P8b"}
held = sum(v == "HELD" for i, v, _ in SC if i not in prob_ids); failed = [i for i, v, _ in SC if v == "FAILED" and i not in prob_ids]
unclear = sum(v == "UNCLEAR" for i, v, _ in SC if i not in prob_ids)
L += ["", "## C. Corrected tally (probability statements scored by Brier only, as PREDICTIONS.md says)", "",
      f"HELD {held}, FAILED {len(failed)} ({', '.join(failed)}), UNCLEAR {unclear}; Brier statements P2a-c, P8b listed separately (mean 0.124 over 4)."]
# D. hard vs soft
spread = float(np.ptp([np.mean(soft({k: cellp(r)[k] for k in TUNE})) for r in R["rule-soft-100 (3 seeds)"]]))
L += ["", "## D. Hard vs soft targets", ""]
for n, hard_n, soft_n, ex_n in ((25, "rule-hard-25", "rule-soft-25", "examples-25"), (100, "rule-hard-100", "rule-soft-100 seed 0", "examples-100")):
  d = cboot(S[hard_n] - S[soft_n]); gap = float(np.mean(S[soft_n] - S[ex_n]))
  L.append(f"- N = {n}: hard - soft {fmt(d)}; rule-soft-100 seed spread {spread:.3f} (single seeds: difference is {'noise-sized' if abs(d[0]) < spread else 'larger than the seed spread'}); "
           f"the interval allows hard targets to have closed up to {max(0.0, -d[1]) / gap:.0%} of the soft-to-examples gap ({gap:.3f}); point estimate {max(0.0, -d[0]) / gap:.0%}.")
open(os.path.join(ROOT, "demo_out", "gen_curve_followup.md"), "w").write("\n".join(L) + "\n")
print("\n".join(L))
