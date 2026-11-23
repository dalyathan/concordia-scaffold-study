"""Report for the learning-curve runs on the 42 TUNE cells (CPU; descriptive; GEN_CURVE_PLAN.md). Scores nothing, reads stored run files.
Writes demo_out/gen_curve_report.md and demo/gen/gen_curve_summary.json and scores PREDICTIONS.md mechanically.
Bootstraps are paired over tune cells (10,000 resamples, numpy default_rng(0), 95% percentile) and CLUSTERED: by decision problem (V, grid, C or prior) and,
for every 'lower bound > 0' condition, by (V, grid) (the wider interval)."""
import collections, glob, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import common
import gen_cases as g
import gen_curve
import gen_curve_freeze

gen_curve_freeze.verify(code=False)
ROOT = common.ROOT
cells = {c["cell"]: c for c in json.load(open(os.path.join(g.OUT, "cells.json")))["cells"]}
cases = {c["cid"]: c for c in map(json.loads, open(os.path.join(g.OUT, "cases.jsonl")))}
spec = json.load(open(os.path.join(g.OUT, "lora_train_cells.json")))
labels = json.load(open(os.path.join(g.OUT, "claude_labels.json")))["labels"]
TUNE = sorted(k for k, c in cells.items() if c["split"] == "tune")
prob = lambda k: (cells[k]["V"], cells[k]["grid_name"], cells[k]["C"] if cells[k]["C"] is not None else tuple(cells[k]["prior"]))
vg = lambda k: (cells[k]["V"], cells[k]["grid_name"])
def clusters(key):
  d = collections.defaultdict(list)
  for i, k in enumerate(TUNE):
    d[key(k)].append(i)
  return list(d.values())
CLUS_P, CLUS_W = clusters(prob), clusters(vg)
RUNDIR = os.path.join(ROOT, "demo_out", "gen_lora")
LR = 1e-4
SUBS = {n: set(gen_curve.load(n)) for n in gen_curve.SIZES}


def rid(arm, n, s):
  return f"gen_{arm}_lr{LR:.0e}_s{s}" if n == 100 else f"gen_{arm}_n{n}_lr{LR:.0e}_s{s}"


def load(arm, n, seeds):
  out = []
  for s in seeds:
    f = os.path.join(RUNDIR, rid(arm, n, s) + ".json")
    if os.path.exists(f):
      r = json.load(open(f))
      assert r["arm"] == arm and r["lr"] == LR and r["seed"] == s and r.get("n_cells", 100) == n and r["rank"] == 4, f"unexpected config in {f}"
      if n < 100:
        assert set(r["train_cells"]) == SUBS[n] and r["patience"] == 2 and r["max_epochs"] == -(-500 // n), f"unexpected training setup in {f}"
      else:
        assert r["epochs_run"] <= 5
      out.append(r)
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
hard = lambda P: np.array([cells[k]["best_payoff"] - cells[k]["payoffs"][int(np.argmax(P[k]))] for k in TUNE])
plain_rows = collections.defaultdict(list)
for r in map(json.loads, open(os.path.join(ROOT, "demo_out", "gen_plain_scores.jsonl"))):
  if cases[r["cid"]]["split"] == "tune":
    plain_rows[cases[r["cid"]]["cell"]].append(r["probs"])
PLAIN = {k: np.mean(v, 0) for k, v in plain_rows.items()}


def cboot(d, clus=None, idx=None):
  """mean of d over tune cells with a cluster bootstrap; idx restricts to a subset of cells"""
  clus = clus or CLUS_W
  d = np.asarray(d, float)
  keep = set(range(len(TUNE))) if idx is None else set(idx)
  cl = [[i for i in c if i in keep] for c in clus]; cl = [c for c in cl if c]
  ix = np.random.default_rng(0).integers(0, len(cl), size=(10000, len(cl)))
  sums = np.array([d[c].sum() for c in cl]); cnt = np.array([len(c) for c in cl])
  m = sums[ix].sum(1) / cnt[ix].sum(1)
  return float(d[sorted(keep)].mean()), float(np.quantile(m, .025)), float(np.quantile(m, .975))


fmt = lambda b: f"{b[0]:+.3f} [{b[1]:+.3f}, {b[2]:+.3f}]"
type_idx = {t: [i for i, k in enumerate(TUNE) if cells[k]["type"] == t] for t in g.TYPES}
BELOW = type_idx["below"]


def slope(P, idx=None):
  idx = BELOW if idx is None else idx
  x = np.array([cells[TUNE[i]]["C"] for i in idx], float); y = np.array([float(np.dot(P[TUNE[i]], cells[TUNE[i]]["grid"])) for i in idx])
  return float(np.polyfit(x, y, 1)[0]) if len(set(x)) >= 2 else float("nan")


def slope_ci(P):
  cl = [[i for i in c if i in set(BELOW)] for c in CLUS_W]; cl = [c for c in cl if c]
  rng = np.random.default_rng(0); vals = []
  for _ in range(10000):
    v = slope(P, [i for j in rng.integers(0, len(cl), len(cl)) for i in cl[j]])
    if v == v:
      vals.append(v)
  return slope(P), float(np.quantile(vals, .025)), float(np.quantile(vals, .975))


ARMS = [("examples-10", "claude_examples", 10, (0, 1, 2)), ("examples-25", "claude_examples", 25, (0, 1, 2)), ("examples-50", "claude_examples", 50, (0, 1, 2)),
        ("examples-100", "claude_examples", 100, (0, 1, 2)), ("rule-soft-25", "teacher", 25, (0,)), ("rule-soft-100 (3 seeds)", "teacher", 100, (0, 1, 2)),
        ("rule-soft-100 seed 0", "teacher", 100, (0,)), ("rule-hard-25", "rule_hard", 25, (0,)), ("rule-hard-100", "rule_hard", 100, (0,)), ("cheapest-label-25", "cheapest_label", 25, (0,))]
P, R, S, H = {"plain": PLAIN}, {}, {}, {}
for name, arm, n, seeds in ARMS:
  rs = load(arm, n, seeds)
  if rs:
    R[name] = rs; P[name] = avgp(rs); S[name] = soft(P[name]); H[name] = hard(P[name])
S["plain"] = soft(PLAIN); H["plain"] = hard(PLAIN)
S["always-cheapest"] = np.array([cells[k]["best_payoff"] - cells[k]["payoffs"][0] for k in TUNE])
S["stated-cost rule"] = np.array([cells[k]["best_payoff"] - cells[k]["payoffs"][(next((i for i, x in enumerate(cells[k]["grid"]) if x >= cells[k]["C"]), 4) if cells[k]["C"] is not None and cells[k]["C"] < cells[k]["V"] else 0)] for k in TUNE])
mean_ = lambda n: float(np.mean(S[n])) if n in S else None
L = ["# Learning curve and rules-vs-examples on the 42 TUNE cells (descriptive; read against PREDICTIONS.md)", "",
     f"{len(TUNE)} tune cells in {len(CLUS_P)} decision problems and {len(CLUS_W)} (V, grid) groups. Intervals: clustered paired bootstrap by (V, grid) (the wider one; used for every 'lower bound > 0' condition) and, in the arm table, also by problem. Soft regret: lower is better. Seeds averaged per arm.", "",
     "## Soft regret by arm", "", "| Arm | seeds | all [95% by (V, grid)] [95% by problem] | below | at_or_above | no_cost | argmax (hard) regret | letter mass | slope on stated cost (below) | best steps | epoch-0 kept |", "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
summ = {}
for name in ["plain", "always-cheapest", "stated-cost rule"] + [a[0] for a in ARMS if a[0] in R]:
  b, bp = cboot(S[name]), cboot(S[name], CLUS_P); bt = {t: float(np.mean(S[name][type_idx[t]])) for t in g.TYPES}
  rs = R.get(name, [])
  mass = float(np.mean([np.mean(list(r["tune_mass_best"].values())) for r in rs])) if rs else float("nan")
  sl = slope_ci(P[name]) if name in P else (None,)
  hr = f"{float(np.mean(H[name])):.3f}" if name in H else ""
  L.append(f"| {name} | {len(rs) or ''} | {b[0]:.3f} [{b[1]:.3f}, {b[2]:.3f}] [{bp[1]:.3f}, {bp[2]:.3f}] | {bt['below']:.3f} | {bt['at_or_above']:.3f} | {bt['no_cost']:.3f} | {hr} | {'' if not rs else f'{mass:.2f}'} | "
           f"{'' if sl[0] is None else f'{sl[0]:.2f} [{sl[1]:.2f}, {sl[2]:.2f}]'} | {','.join(str(r.get('best_step', r['best_epoch'] * 100)) for r in rs)} | {','.join(str(bool(r['best_epoch_is_zero'])) for r in rs)} |")
  summ[name] = {"soft": b[0], "by_type": bt, "mass": mass, "slope": None if sl[0] is None else list(sl), "hard": None if name not in H else float(np.mean(H[name]))}
L += ["", "## Comparisons (first minus second; lower bound > 0 means the second is better; (V, grid)-clustered interval, by-type point differences)", ""]
DIFFS = {}
for a, b2 in (("rule-soft-25", "examples-25"), ("rule-hard-25", "examples-25"), ("rule-soft-100 (3 seeds)", "examples-100"), ("rule-hard-100", "examples-100"), ("rule-soft-100 seed 0", "examples-100"),
              ("rule-hard-25", "rule-soft-25"), ("rule-hard-100", "rule-soft-100 seed 0"), ("cheapest-label-25", "examples-25"), ("examples-10", "examples-100"), ("examples-25", "examples-100"),
              ("examples-50", "examples-100"), ("plain", "examples-10"), ("plain", "examples-25"), ("plain", "examples-50")):
  if a in S and b2 in S:
    d = S[a] - S[b2]; DIFFS[(a, b2)] = cboot(d)
    L.append(f"- {a} - {b2}: {fmt(DIFFS[(a, b2)])}; problem-clustered {fmt(cboot(d, CLUS_P))}; by type " + ", ".join(f"{t} {np.mean(d[type_idx[t]]):+.3f}" for t in g.TYPES))
# training coverage
L += ["", "## What the training subsets cover (CPU, from the subset lists)", "", "| N | distinct training problems | tune cells whose problem is in the subset | examples-N regret covered / uncovered | share of cheapest Claude labels | rule-soft target: soft / argmax regret on the subset | always-cheapest regret on the subset |", "| --- | --- | --- | --- | --- | --- | --- |"]
trows = collections.defaultdict(list)
for r in map(json.loads, open(os.path.join(ROOT, "demo_out", "gen_text_rows.jsonl"))):
  if r["row"] == "teacher" and cases[r["cid"]]["split"] == "train":
    trows[cases[r["cid"]]["cell"]].append(r["probs"])
for n in gen_curve.SIZES:
  tp = {prob(k) for k in SUBS[n]}
  cov = [i for i, k in enumerate(TUNE) if prob(k) in tp]; unc = [i for i in range(len(TUNE)) if i not in set(cov)]
  ex = S.get(f"examples-{n}")
  chp = np.mean([labels[f"{k}-n{spec[k]['name_variant']}"]["position"] == 0 for k in SUBS[n]])
  tsoft, thard = [], []
  for k in SUBS[n]:
    p = np.mean(trows[k], 0); tsoft.append(cells[k]["best_payoff"] - float(np.dot(p, cells[k]["payoffs"]))); thard.append(cells[k]["best_payoff"] - cells[k]["payoffs"][int(np.argmax(p))])
  chr_ = np.mean([cells[k]["best_payoff"] - cells[k]["payoffs"][0] for k in SUBS[n]])
  L.append(f"| {n} | {len(tp)} | {len(cov)} of {len(TUNE)} | " + (f"{np.mean(ex[cov]):.3f} / {np.mean(ex[unc]):.3f}" if ex is not None and cov and unc else "") +
           f" | {chp:.2f} | {np.mean(tsoft):.2f} / {np.mean(thard):.2f} | {chr_:.2f} |")
L += ["", "Claude labels have regret 0 on every training cell by construction; the in-prompt teacher paragraph's own regret (order-averaged) is shown above, so a rule student cannot be expected to beat it by much."]
# rule-hard disagreement
for name in ("rule-hard-25", "rule-hard-100"):
  for r in R.get(name, []):
    L.append(f"- {name}: share of training cases whose argmax price differs across their three orders {r.get('rule_hard_cases_with_order_disagreement', float('nan')):.2f}; share of cheapest target prices {r.get('rule_hard_share_cheapest_target', float('nan')):.2f}")
# seed spreads
L += ["", "## Seed spread (max - min of per-run tune soft regret) and per-run values", ""]
spread = {}
for name, rs in R.items():
  v = [r["tune_full_best"]["soft_regret"] for r in rs]
  spread[name] = max(v) - min(v) if len(v) > 1 else None
  for r in rs:
    sl = slope(avgp([r]))
    L.append(f"- {r['run_id']}: tune {r['tune_full_best']['soft_regret']:.3f} (by type " + ", ".join(f"{t} {r['tune_full_best']['soft_by_type'][t]:.3f}" for t in g.TYPES) + f"); selection set B {r['select_best']['soft_regret']:.3f}; slope {sl:.2f}; best step {r.get('best_step', r['best_epoch'] * 100)}; {r['epochs_run']} epochs run; {r['wall_s']:.0f} s")
  if spread[name] is not None:
    L.append(f"  - {name}: seed spread {spread[name]:.3f}")
# predictions (mechanical)
L += ["", "## Predictions scored mechanically (rule at the top of PREDICTIONS.md)", ""]
SC = []
def point(pid, name, lo, hi, val):
  if val is None:
    SC.append((pid, "UNCLEAR", f"{name}: run missing")); return
  SC.append((pid, "HELD" if lo <= val <= hi else "FAILED", f"{name} = {val:.3f} (range {lo}..{hi})"))
def comp(pid, a, b2, lo, hi):
  if (a, b2) not in DIFFS:
    SC.append((pid, "UNCLEAR", f"{a} - {b2}: run missing")); return
  d = DIFFS[(a, b2)]
  v = "FAILED" if (d[0] < lo or d[0] > hi) else ("HELD" if d[1] > 0 else "UNCLEAR")
  SC.append((pid, v, f"{a} - {b2} = {fmt(d)} (range {lo}..{hi})"))
m = {n: mean_(f"examples-{n}") for n in (10, 25, 50, 100)}
point("P1a", "examples-10", .15, .50, m[10]); point("P1b", "examples-25", .05, .18, m[25]); point("P1c", "examples-50", .03, .09, m[50])
if None in m.values():
  SC.append(("P1m", "UNCLEAR", "a curve point is missing"))
else:
  SC.append(("P1m", "HELD" if m[10] > m[25] > m[50] and m[50] - m[100] <= 0.02 else "FAILED", f"means {m[10]:.3f} > {m[25]:.3f} > {m[50]:.3f}; 50 - 100 = {m[50] - m[100]:+.3f}"))
thr = (m[100] + 0.05) if m[100] is not None else None
briers = []
for pid, n, op, p in (("P2a", 25, ">", 0.65), ("P2b", 50, "<=", 0.80), ("P2c", 10, ">", 0.90)):
  if m[n] is None:
    SC.append((pid, "UNCLEAR", f"examples-{n} missing")); continue
  occurred = (m[n] > thr) if op == ">" else (m[n] <= thr)
  briers.append((p - float(occurred)) ** 2)
  SC.append((pid, "HELD" if occurred else "FAILED", f"examples-{n} mean {m[n]:.3f} {op} {thr:.3f}: {'yes' if occurred else 'no'} (stated p = {p}; Brier term {(p - float(occurred)) ** 2:.3f})"))
comp("P3a", "rule-soft-25", "examples-25", .20, .50); comp("P3b", "rule-hard-25", "examples-25", .15, .45)
comp("P3c", "rule-soft-100 (3 seeds)", "examples-100", .20, .50); comp("P3d", "rule-hard-100", "examples-100", .22, .50)
point("P4a", "rule-soft-25", .33, .55, mean_("rule-soft-25")); point("P4b", "rule-hard-25", .30, .55, mean_("rule-hard-25")); point("P4c", "rule-hard-100", .30, .50, mean_("rule-hard-100"))
for n, soft_n, hard_n, ex in ((25, "rule-soft-25", "rule-hard-25", "examples-25"), (100, "rule-soft-100 seed 0", "rule-hard-100", "examples-100")):
  if soft_n in S and hard_n in S:
    SC.append((f"P4d N={n}", "HELD" if abs(mean_(soft_n) - mean_(hard_n)) <= 0.08 else "FAILED", f"|{hard_n} - {soft_n}| = {abs(mean_(soft_n) - mean_(hard_n)):.3f} (limit 0.08; seed spread of rule-soft-100: {spread.get('rule-soft-100 (3 seeds)')})"))
    den = mean_(soft_n) - mean_(ex)
    SC.append((f"P4e N={n}", "UNCLEAR" if den < 0.10 else ("HELD" if (mean_(soft_n) - mean_(hard_n)) / den < 0.25 else "FAILED"), f"closed share {(mean_(soft_n) - mean_(hard_n)) / den:.2f} (denominator {den:.3f})"))
    SC.append((f"P4f N={n}", "HELD" if float(np.mean(H[hard_n])) >= 0.25 else "FAILED", f"{hard_n} argmax regret {float(np.mean(H[hard_n])):.3f} (>= 0.25)"))
  else:
    SC += [(f"P4d/e/f N={n}", "UNCLEAR", "run missing")]
if "cheapest-label-25" in S:
  point("P5a", "cheapest-label-25", .40, .46, mean_("cheapest-label-25")); comp("P5b", "cheapest-label-25", "examples-25", 0.0, 9.9)
for pid, name, lo, hi in (("P6a", "examples-50", .55, .80), ("P6b", "examples-25", .30, .75), ("P6c", "examples-10", 0.0, .55), ("P6e", "cheapest-label-25", -.15, .20)):
  point(pid, f"slope {name}", lo, hi, summ[name]["slope"][0] if name in summ else None)
rule_slopes = {n: summ[n]["slope"][0] for n in ("rule-soft-25", "rule-hard-25", "rule-soft-100 (3 seeds)", "rule-hard-100") if n in summ}
SC.append(("P6d", "UNCLEAR" if len(rule_slopes) < 4 else ("HELD" if all(v < 0.40 for v in rule_slopes.values()) else "FAILED"), f"rule-arm slopes {({k: round(v, 2) for k, v in rule_slopes.items()})} (each < 0.40)"))
allm = [float(np.mean(list(r["tune_mass_best"].values()))) for rs in R.values() for r in rs]
SC.append(("P7", "HELD" if allm and min(allm) >= 0.98 else "FAILED", f"minimum letter mass {min(allm):.3f}"))
k25 = [r["best_epoch_is_zero"] for n in (25, 50, 100) for r in R.get(f"examples-{n}", [])]
SC.append(("P8a", "HELD" if k25 and not any(k25) else "FAILED", f"epoch-0 kept flags for examples N >= 25: {k25}"))
k10 = [r["best_epoch_is_zero"] for r in R.get("examples-10", [])]
if k10:
  occurred = any(k10); briers.append((0.15 - float(occurred)) ** 2)
  SC.append(("P8b", "HELD" if occurred else "FAILED", f"examples-10 epoch-0 kept flags {k10} (stated p = 0.15; Brier term {(0.15 - float(occurred)) ** 2:.3f})"))
for pid, v, txt in SC:
  L.append(f"- {pid}: **{v}** - {txt}")
L.append(f"- Brier score of the probability statements (P2a-c, P8b): {np.mean(briers):.3f} over {len(briers)} statements" if briers else "- Brier: no statement scored")
L.append(f"- Tally: HELD {sum(v == 'HELD' for _, v, _ in SC)}, FAILED {sum(v == 'FAILED' for _, v, _ in SC)}, UNCLEAR {sum(v == 'UNCLEAR' for _, v, _ in SC)}")
open(os.path.join(ROOT, "demo_out", "gen_curve_report.md"), "w").write("\n".join(L) + "\n")
json.dump({"arms": summ, "predictions": [{"id": i, "verdict": v, "detail": t} for i, v, t in SC]}, open(os.path.join(g.OUT, "gen_curve_summary.json"), "w"), indent=1)
print("\n".join(L))
