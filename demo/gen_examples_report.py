"""Report for the worked-examples arms on the 42 TUNE cells (CPU). Applies the pass rule frozen in GEN_EXAMPLES_PLAN.md and prints tags T1-T5.
Writes demo_out/gen_examples_report.md and demo/gen/gen_examples_summary.json. Tune only; nothing else is read."""
import collections, glob, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import common
import gen_cases as g

ROOT = common.ROOT
cells = {c["cell"]: c for c in json.load(open(os.path.join(g.OUT, "cells.json")))["cells"]}
cases = {c["cid"]: c for c in map(json.loads, open(os.path.join(g.OUT, "cases.jsonl")))}
TUNE = sorted(k for k, c in cells.items() if c["split"] == "tune")
assert all(cells[k]["grid"][0] == min(cells[k]["grid"]) for k in cells), "grid position 0 must be the cheapest price"
BELOW = [k for k in TUNE if cells[k]["type"] == "below"]
tr = json.load(open(os.path.join(g.OUT, "lora_train_cells.json")))
key = lambda k: (cells[k]["V"], cells[k]["grid_name"], cells[k]["C"], None if cells[k]["C"] is not None else tuple(cells[k]["prior"]))
trk = {key(k) for k in tr}
NOV = [k for k in TUNE if key(k) not in trk]
runs = {}
for f in glob.glob(os.path.join(ROOT, "demo_out", "gen_lora", "*_s?.json")):
  r = json.load(open(f)); runs[r["run_id"]] = r
rid = lambda a, lr, s: f"gen_{a}_lr{lr:.0e}_s{s}"
get = lambda a, lr, s: runs.get(rid(a, lr, s))


def cellp(r):
  by = collections.defaultdict(list)
  for cid, p in r["tune_probs_best"].items(): by[cases[cid]["cell"]].append(p)
  return {k: np.mean(v, 0) for k, v in by.items()}


def avgp(rs):
  cp = [cellp(r) for r in rs]
  return {k: np.mean([c[k] for c in cp], 0) for k in TUNE}


soft = lambda P, k: cells[k]["best_payoff"] - float(np.dot(P[k], cells[k]["payoffs"]))
cellsoft = lambda P: {k: soft(P, k) for k in TUNE}
plain_rows = collections.defaultdict(list)
for r in map(json.loads, open(os.path.join(ROOT, "demo_out", "gen_plain_scores.jsonl"))):
  if cases[r["cid"]]["split"] == "tune": plain_rows[cases[r["cid"]]["cell"]].append(r["probs"])
PLAIN = {k: np.mean(v, 0) for k, v in plain_rows.items()}
plain_mass = float(np.mean([r["mass"] for r in map(json.loads, open(os.path.join(ROOT, "demo_out", "gen_plain_scores.jsonl"))) if cases[r["cid"]]["split"] == "tune"]))


def boot(d):
  v = np.asarray(d, float)
  b = np.random.default_rng(0).choice(v, size=(10000, len(v)), replace=True).mean(1)
  return float(v.mean()), float(np.quantile(b, .025)), float(np.quantile(b, .975))


fmt = lambda b: f"{b[0]:+.3f} [{b[1]:+.3f}, {b[2]:+.3f}]"
ar = [r for r in runs.values() if r["arm"] == "claude_examples"]
if not ar:
  sys.exit("no claude_examples runs yet")
sel = {r["lr"]: r["select_best"]["soft_regret"] for r in ar if r["seed"] == 0}
lr = min(sel, key=lambda k: (sel[k], k)) if len(sel) == 2 else None
if lr is None:
  sys.exit("lr grid for claude_examples incomplete")
A = [get("claude_examples", lr, s) for s in (0, 1, 2)]; A = [r for r in A if r]
B = get("cheapest_label", lr, 0); C = get("shuffled_claude", lr, 0)
CEIL = {l: get("answer_only", l, 0) for l in (1e-4, 3e-4)}
TEACH = [get("teacher", 1e-4, s) for s in (0, 1, 2)]; TEACH = [r for r in TEACH if r]
PA = avgp(A); sA = cellsoft(PA); sP = cellsoft(PLAIN)
sCheap = {k: cells[k]["best_payoff"] - cells[k]["payoffs"][0] for k in TUNE}
byt = lambda d, t, ks=None: float(np.mean([d[k] for k in (ks or TUNE) if t is None or cells[k]["type"] == t]))
L = [f"# Worked-examples arms on the 42 TUNE cells (labels sha256 0b6f0feb...; selection on set B; tune scored once per run)", "",
     f"claude_examples lr chosen on selection set B: {lr:.0e} (selection soft regret {sel}); seeds completed: {[r['seed'] for r in A]}; best epochs {[r['best_epoch'] for r in A]}; epoch-0 flags {[bool(r['best_epoch_is_zero']) for r in A]}", "",
     "## Soft regret on tune cells (cell means, seeds averaged), by type", "", "| Arm | all [95%] | below | at_or_above | no_cost | letter mass | cheapest-option mass below / at_or_above / no_cost | best epochs |", "| --- | --- | --- | --- | --- | --- | --- | --- |"]
arms = {"plain": (PLAIN, None, plain_mass), "always-cheapest": ({k: np.eye(5)[0] for k in TUNE}, None, None), "claude_examples (a)": (PA, A, None)}
if B: arms["cheapest_label (b)"] = (avgp([B]), [B], None)
if C: arms["shuffled_claude (c)"] = (avgp([C]), [C], None)
for l, r in CEIL.items():
  if r: arms[f"answer-trained ceiling lr {l:.0e}"] = (avgp([r]), [r], None)
if TEACH: arms["teacher-distil (earlier, 3 seeds)"] = (avgp(TEACH), TEACH, None)
for n, (P, rs, m) in arms.items():
  cs = cellsoft(P); b = boot(list(cs.values()))
  mass = m if m is not None else (float(np.mean([np.mean(list(r["tune_mass_best"].values())) for r in rs])) if rs else float("nan"))
  L.append(f"| {n} | {b[0]:.3f} [{b[1]:.3f}, {b[2]:.3f}] | {byt(cs, 'below'):.3f} | {byt(cs, 'at_or_above'):.3f} | {byt(cs, 'no_cost'):.3f} | {mass:.2f} | " +
           " / ".join(f"{np.mean([P[k][0] for k in TUNE if cells[k]['type'] == t]):.2f}" for t in g.TYPES) + " | " + (",".join(str(r["best_epoch"]) for r in rs) if rs else "") + " |")
L += ["", "## Pass rule (GEN_EXAMPLES_PLAN.md, frozen): paired cell bootstrap, 10,000 resamples, seed 0, two-sided 95% percentile (lower = 2.5th percentile)", ""]
res = {}
def cond(name, d, ks=None):
  ks = ks or TUNE
  b = boot([d[k] for k in ks]); res[name] = b
  L.append(f"- {name}: {fmt(b)}, lower bound > 0: **{'yes' if b[1] > 0 else 'no'}**")
  return b[1] > 0
c1 = cond("1. plain - a", {k: sP[k] - sA[k] for k in TUNE})
sB = cellsoft(avgp([B])) if B else None
c2 = cond("2. (b) - a", {k: sB[k] - sA[k] for k in TUNE}) if B else None
c3 = cond("3. always-cheapest - a", {k: sCheap[k] - sA[k] for k in TUNE})
c4 = cond("4. plain - a on below cells (14)", {k: sP[k] - sA[k] for k in BELOW}, BELOW)
c5 = all(byt(sA, t) - byt(sP, t) <= 0.05 for t in g.TYPES)
L.append("- 5. type means (a) minus plain: " + ", ".join(f"{t} {byt(sA, t) - byt(sP, t):+.3f}" for t in g.TYPES) + f" (each <= +0.05): **{'yes' if c5 else 'no'}**")
mass = float(np.mean([np.mean(list(r["tune_mass_best"].values())) for r in A]))
c6 = mass >= 0.9 * plain_mass
L.append(f"- 6. letter mass {mass:.2f} vs 0.9 x plain {0.9 * plain_mass:.2f}: **{'yes' if c6 else 'no'}**")
conds = [c1, c2, c3, c4, c5, c6]
verdict = "INCOMPLETE (cheapest-label control missing)" if B is None else ("PASSED" if all(conds) else "NOT PASSED")
L += ["", f"**Owner's pass rule: {verdict}** (mean over completed seeds {[r['seed'] for r in A]})", "", "## Tags (not part of the rule; they decide how a pass may be worded)", ""]
T = {}
if B:
  t1a = cond("T1a plain - a on the 26 non-overlapping cells", {k: sP[k] - sA[k] for k in NOV}, NOV)
  t1b = cond("T1b (b) - a on the 26 non-overlapping cells", {k: sB[k] - sA[k] for k in NOV}, NOV)
  T["T1"] = t1a and t1b
  # stricter overlap keys (post-hoc, added after G2): ignore the grid / ignore the prior
  for nm, kf in (("V and C only", lambda k: (cells[k]["V"], cells[k]["C"])), ("V and grid only", lambda k: (cells[k]["V"], cells[k]["grid_name"]))):
    tk = {kf(k) for k in tr}; nv = [k for k in TUNE if kf(k) not in tk]
    if len(nv) >= 5:
      cond(f"T1 POST-HOC strict key ({nm}): plain - a on {len(nv)} non-overlapping cells", {k: sP[k] - sA[k] for k in nv}, nv)
      cond(f"T1 POST-HOC strict key ({nm}): (b) - a on {len(nv)} non-overlapping cells", {k: sB[k] - sA[k] for k in nv}, nv)
a12 = [r for r in A if r["seed"] in (1, 2)]
if len(a12) == 2 and B:
  s12 = cellsoft(avgp(a12))
  T["T2"] = all([cond("T2 plain - a (seeds 1-2)", {k: sP[k] - s12[k] for k in TUNE}), cond("T2 (b) - a (seeds 1-2)", {k: sB[k] - s12[k] for k in TUNE}), cond("T2 always-cheapest - a (seeds 1-2)", {k: sCheap[k] - s12[k] for k in TUNE}),
                cond("T2 plain - a below (seeds 1-2)", {k: sP[k] - s12[k] for k in BELOW}, BELOW)] + [byt(s12, t) - byt(sP, t) <= 0.05 for t in g.TYPES])
s0 = cellsoft(avgp([next(r for r in A if r["seed"] == 0)]))
if B:
  T["T3"] = cond("T3 (b) - a seed 0 (equal footing)", {k: sB[k] - s0[k] for k in TUNE})
  for t in ("below", "no_cost"):
    ks = [k for k in TUNE if cells[k]["type"] == t]; T[f"T4b_{t}"] = cond(f"T4 (b) - a on {t} cells", {k: sB[k] - sA[k] for k in ks}, ks)
if C:
  sC = cellsoft(avgp([C]))
  for t in ("below", "no_cost"):
    ks = [k for k in TUNE if cells[k]["type"] == t]; T[f"T4c_{t}"] = cond(f"T4 (c) - a on {t} cells (differing labels)", {k: sC[k] - sA[k] for k in ks}, ks)
  for r in A:
    sr = cellsoft(avgp([r])); L.append(f"- POST-HOC per-seed (c) - a seed {r['seed']} on below+no_cost cells: {fmt(boot([sC[k] - sr[k] for k in TUNE if cells[k]['type'] != 'at_or_above']))}")
if CEIL.get(lr):
  sCe = cellsoft(avgp([CEIL[lr]])); b = boot([sA[k] - sCe[k] for k in TUNE])
  T["T5"] = b[0] <= 0.05
  L.append(f"- T5 (a) minus ceiling at lr {lr:.0e}: {fmt(b)}; mean <= 0.05: **{'yes' if T['T5'] else 'no'}** (upper bound {b[2]:+.3f}; ceiling has ONE seed; (a) per-seed spread {min(boot(list(cellsoft(avgp([r])).values()))[0] for r in A):.3f}-{max(boot(list(cellsoft(avgp([r])).values()))[0] for r in A):.3f}); by type (a) - ceiling: " + ", ".join(f"{t} {byt(sA, t) - byt(sCe, t):+.3f}" for t in g.TYPES))
# post-hoc (added after G2, not in the frozen rule): the stated-cost rule as a stronger simple comparator
sRule = {k: cells[k]["best_payoff"] - cells[k]["payoffs"][(next((i for i, x in enumerate(cells[k]["grid"]) if x >= cells[k]["C"]), 4) if cells[k]["C"] is not None and cells[k]["C"] < cells[k]["V"] else 0)] for k in TUNE}
L.append(f"- POST-HOC (not in rule) stated-cost rule - a: {fmt(boot([sRule[k] - sA[k] for k in TUNE]))}; rule soft regret {np.mean(list(sRule.values())):.3f}")
if TEACH:
  sT = cellsoft(avgp(TEACH)); L.append(f"- (a) vs earlier teacher-distil: teacher-distil minus (a) {fmt(boot([sT[k] - sA[k] for k in TUNE]))}")
# slope on stated cost over below cells
def slope(P, ks=BELOW):
  x = np.array([cells[k]["C"] for k in ks], float); y = np.array([float(np.dot(P[k], cells[k]["grid"])) for k in ks])
  return float(np.polyfit(x, y, 1)[0])
def slope_ci(P):
  rng = np.random.default_rng(0); out = []
  for _ in range(5000):
    ix = rng.integers(0, len(BELOW), len(BELOW)); ks = [BELOW[i] for i in ix]
    if len({cells[k]["C"] for k in ks}) > 1: out.append(slope(P, ks))
  return float(np.quantile(out, .025)), float(np.quantile(out, .975))
L += ["", "## Slope of the expected offer on the stated cost over the 14 below cells (OLS; bootstrap interval over cells)", ""]
for n, (P, rs, m) in arms.items():
  lo, hi = slope_ci(P); L.append(f"- {n}: {slope(P):.2f} [{lo:.2f}, {hi:.2f}]")
oracle = {k: np.eye(5)[cells[k]["best_positions"][0]] for k in TUNE}
L.append(f"- oracle (first best price): {slope(oracle):.2f}")
ov = [k for k in TUNE if key(k) in trk]
L += ["", f"## By label-key overlap with the 100 training cells ({len(ov)} overlapping, {len(NOV)} not): soft regret", "", "| Arm | overlapping | non-overlapping |", "| --- | --- | --- |"]
for n, (P, rs, m) in arms.items():
  cs = cellsoft(P); L.append(f"| {n} | {np.mean([cs[k] for k in ov]):.3f} | {np.mean([cs[k] for k in NOV]):.3f} |")
L += ["", "## Per-run tune soft regret", ""] + [f"- {r['run_id']}: {np.mean(list(cellsoft(avgp([r])).values())):.3f} (best epoch {r['best_epoch']}, selection {r['select_best']['soft_regret']:.3f}, {r['wall_s']:.0f} s)" for r in sorted(runs.values(), key=lambda r: r["run_id"]) if r["arm"] in ("claude_examples", "cheapest_label", "shuffled_claude")]
open(os.path.join(ROOT, "demo_out", "gen_examples_report.md"), "w").write("\n".join(L) + "\n")
json.dump({"lr": lr, "verdict": verdict, "conds": [bool(c) if c is not None else None for c in conds], "tags": {k: bool(v) for k, v in T.items()}, "res": res}, open(os.path.join(g.OUT, "gen_examples_summary.json"), "w"), indent=1, default=float)
print("\n".join(L))
