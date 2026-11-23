"""Report for the learning-curve runs on the 42 TUNE cells (CPU; descriptive; GEN_CURVE_PLAN.md). Scores nothing, reads stored run files.
Writes demo_out/gen_curve_report.md and demo/gen/gen_curve_summary.json. Bootstraps are paired over tune cells and CLUSTERED by decision problem
(V, grid, C or prior): problems are resampled with replacement, all their cells kept."""
import collections, glob, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import common
import gen_cases as g

ROOT = common.ROOT
cells = {c["cell"]: c for c in json.load(open(os.path.join(g.OUT, "cells.json")))["cells"]}
cases = {c["cid"]: c for c in map(json.loads, open(os.path.join(g.OUT, "cases.jsonl")))}
TUNE = sorted(k for k, c in cells.items() if c["split"] == "tune")
prob = lambda k: (cells[k]["V"], cells[k]["grid_name"], cells[k]["C"] if cells[k]["C"] is not None else tuple(cells[k]["prior"]))
CL = collections.defaultdict(list)
for i, k in enumerate(TUNE):
  CL[prob(k)].append(i)
CLUS = list(CL.values())
RUNDIR = os.path.join(ROOT, "demo_out", "gen_lora")
LR = 1e-4


def rid(arm, n, s):
  return f"gen_{arm}_lr{LR:.0e}_s{s}" if n == 100 else f"gen_{arm}_n{n}_lr{LR:.0e}_s{s}"


def load(arm, n, seeds):
  out = []
  for s in seeds:
    f = os.path.join(RUNDIR, rid(arm, n, s) + ".json")
    if os.path.exists(f):
      out.append(json.load(open(f)))
  return out


def cellp(r):
  by = collections.defaultdict(list)
  for cid, p in r["tune_probs_best"].items():
    by[cases[cid]["cell"]].append(p)
  return {k: np.mean(v, 0) for k, v in by.items()}


def avgp(rs):
  cp = [cellp(r) for r in rs]
  return {k: np.mean([c[k] for c in cp], 0) for k in TUNE}


soft = lambda P: np.array([cells[k]["best_payoff"] - float(np.dot(P[k], cells[k]["payoffs"])) for k in TUNE])
plain_rows = collections.defaultdict(list)
for r in map(json.loads, open(os.path.join(ROOT, "demo_out", "gen_plain_scores.jsonl"))):
  if cases[r["cid"]]["split"] == "tune":
    plain_rows[cases[r["cid"]]["cell"]].append(r["probs"])
PLAIN = {k: np.mean(v, 0) for k, v in plain_rows.items()}
RNG_IDX = np.random.default_rng(0).integers(0, len(CLUS), size=(10000, len(CLUS)))      # one set of problem resamples for every comparison (paired)


def cboot(d, idx_cells=None):
  """clustered bootstrap of the mean of d (per tune cell) over resampled problems; idx_cells restricts to a subset of cells"""
  d = np.asarray(d, float)
  keep = set(range(len(TUNE))) if idx_cells is None else set(idx_cells)
  cl = [[i for i in c if i in keep] for c in CLUS]
  cl = [c for c in cl if c]
  rng = np.random.default_rng(0)
  ix = rng.integers(0, len(cl), size=(10000, len(cl)))
  sums = np.array([d[c].sum() for c in cl]); cnt = np.array([len(c) for c in cl])
  m = sums[ix].sum(1) / cnt[ix].sum(1)
  return float(d[list(keep)].mean()), float(np.quantile(m, .025)), float(np.quantile(m, .975))


fmt = lambda b: f"{b[0]:+.3f} [{b[1]:+.3f}, {b[2]:+.3f}]"
type_idx = {t: [i for i, k in enumerate(TUNE) if cells[k]["type"] == t] for t in g.TYPES}
BELOW = type_idx["below"]


def slope(P, idx=None):
  idx = BELOW if idx is None else idx
  x = np.array([cells[TUNE[i]]["C"] for i in idx], float); y = np.array([float(np.dot(P[TUNE[i]], cells[TUNE[i]]["grid"])) for i in idx])
  return float(np.polyfit(x, y, 1)[0]) if len(set(x)) >= 2 else float("nan")


def slope_ci(P):
  cl = [[i for i in c if i in set(BELOW)] for c in CLUS]; cl = [c for c in cl if c]
  rng = np.random.default_rng(0); vals = []
  for _ in range(10000):
    sel = [i for j in rng.integers(0, len(cl), len(cl)) for i in cl[j]]
    v = slope(P, sel)
    if v == v:
      vals.append(v)
  return slope(P), float(np.quantile(vals, .025)), float(np.quantile(vals, .975))


ARMS = [("plain", None, None, None), ("examples-10", "claude_examples", 10, (0, 1, 2)), ("examples-25", "claude_examples", 25, (0, 1, 2)), ("examples-50", "claude_examples", 50, (0, 1, 2)),
        ("examples-100", "claude_examples", 100, (0, 1, 2)), ("rule-soft-25", "teacher", 25, (0,)), ("rule-soft-100 (3 seeds)", "teacher", 100, (0, 1, 2)),
        ("rule-soft-100 seed 0", "teacher", 100, (0,)), ("rule-hard-25", "rule_hard", 25, (0,)), ("rule-hard-100", "rule_hard", 100, (0,)), ("cheapest-label-25", "cheapest_label", 25, (0,))]
P, R, S = {"plain": PLAIN}, {}, {}
for name, arm, n, seeds in ARMS[1:]:
  rs = load(arm, n, seeds)
  if rs:
    R[name] = rs; P[name] = avgp(rs); S[name] = soft(P[name])
S["plain"] = soft(PLAIN)
S["always-cheapest"] = np.array([cells[k]["best_payoff"] - cells[k]["payoffs"][0] for k in TUNE])
S["stated-cost rule"] = np.array([cells[k]["best_payoff"] - cells[k]["payoffs"][(next((i for i, x in enumerate(cells[k]["grid"]) if x >= cells[k]["C"]), 4) if cells[k]["C"] is not None and cells[k]["C"] < cells[k]["V"] else 0)] for k in TUNE])
L = ["# Learning curve and rules-vs-examples on the 42 TUNE cells (descriptive; read against PREDICTIONS.md)", "",
     f"{len(TUNE)} tune cells, {len(CLUS)} distinct decision problems; clustered paired bootstrap (10,000 resamples, numpy default_rng(0), 95% percentile). Soft regret: lower is better. Seeds averaged per arm; per-run values below.", "",
     "## Soft regret by arm", "", "| Arm | seeds | all [95% clustered] | below | at_or_above | no_cost | letter mass | slope on stated cost (below) | best steps | epoch-0 kept |", "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
summ = {}
for name in ["plain", "always-cheapest", "stated-cost rule"] + [a[0] for a in ARMS[1:] if a[0] in R]:
  b = cboot(S[name]); bt = {t: float(np.mean(S[name][type_idx[t]])) for t in g.TYPES}
  rs = R.get(name, [])
  mass = float(np.mean([np.mean(list(r["tune_mass_best"].values())) for r in rs])) if rs else float("nan")
  sl = slope_ci(P[name]) if name in P else (None,)
  L.append(f"| {name} | {len(rs) or ''} | {b[0]:.3f} [{b[1]:.3f}, {b[2]:.3f}] | {bt['below']:.3f} | {bt['at_or_above']:.3f} | {bt['no_cost']:.3f} | {'' if not rs else f'{mass:.2f}'} | "
           f"{'' if sl[0] is None else f'{sl[0]:.2f} [{sl[1]:.2f}, {sl[2]:.2f}]'} | {','.join(str(r.get('best_step', r['best_epoch'] * 100)) for r in rs)} | {','.join(str(bool(r['best_epoch_is_zero'])) for r in rs)} |")
  summ[name] = {"soft": b[0], "by_type": bt, "mass": mass, "slope": None if sl[0] is None else list(sl)}
L += ["", "## Comparisons (difference of cell-level soft regret, first minus second; lower bound > 0 means the second is better)", ""]
for a, b2 in (("rule-soft-25", "examples-25"), ("rule-hard-25", "examples-25"), ("rule-soft-100 (3 seeds)", "examples-100"), ("rule-hard-100", "examples-100"),
              ("rule-soft-100 seed 0", "examples-100"), ("rule-hard-25", "rule-soft-25"), ("rule-hard-100", "rule-soft-100 seed 0"), ("cheapest-label-25", "examples-25"),
              ("examples-10", "examples-100"), ("examples-25", "examples-100"), ("examples-50", "examples-100"), ("plain", "examples-10"), ("plain", "examples-25")):
  if a in S and b2 in S:
    d = S[a] - S[b2]
    L.append(f"- {a} - {b2}: {fmt(cboot(d))}; by type " + ", ".join(f"{t} {np.mean(d[type_idx[t]]):+.3f}" for t in g.TYPES))
L += ["", "## Prediction checks (raw statements; scoring held / failed / unclear is done in DEMO_STATUS.md after G2)", ""]
mean_ = lambda n: float(np.mean(S[n])) if n in S else float("nan")
ex100 = mean_("examples-100")
for n in ("examples-10", "examples-25", "examples-50"):
  L.append(f"- {n}: " + (f"mean {mean_(n):.3f}; within 0.05 of examples-100 ({ex100:.3f})? {'yes' if mean_(n) <= ex100 + 0.05 else 'no'}" if n in S else "not run"))
for n in (25, 100):
  rs_, rh_, ex = f"rule-soft-{n}" if n == 25 else "rule-soft-100 (3 seeds)", f"rule-hard-{n}", f"examples-{n}"
  if rs_ in S and rh_ in S and ex in S:
    closed = (mean_(rs_) - mean_(rh_)) / (mean_(rs_) - mean_(ex))
    L.append(f"- N={n}: rule-soft {mean_(rs_):.3f}, rule-hard {mean_(rh_):.3f}, examples {mean_(ex):.3f}; share of the rule-soft-to-examples gap closed by hard targets {closed:.2f}")
L += ["", "## Per run", ""]
for name, rs in R.items():
  for r in rs:
    L.append(f"- {r['run_id']}: tune {r['tune_full_best']['soft_regret']:.3f} (selection set B {r['select_best']['soft_regret']:.3f}; best step {r.get('best_step', r['best_epoch'] * 100)}; epochs run {r['epochs_run']}; {r['wall_s']:.0f} s)")
open(os.path.join(ROOT, "demo_out", "gen_curve_report.md"), "w").write("\n".join(L) + "\n")
json.dump(summ, open(os.path.join(g.OUT, "gen_curve_summary.json"), "w"), indent=1)
print("\n".join(L))
