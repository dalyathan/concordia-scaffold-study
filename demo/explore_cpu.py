"""EXPLORATORY analyses on saved LoRA results (CPU only; nothing here changes the frozen
verdict). Rule (written before running): mean of seeds per arm, each arm at the learning
rate its own seed-0 grid chose, scored on the 6 held-out cells, paired cell bootstrap
(10,000 resamples, seed 0). Primary: slope of expected offer on stated cost, method vs
wrong-rule. Slope = OLS slope of the cell-mean expected offer on C over held-out cells with
C < V (3 cells: (3,C2), (5,C4), (6,C1); same cases as the slope in lora.py). Bootstrap
resamples of cells with a single distinct C have no slope and are dropped (count reported).

  python demo/explore_cpu.py --seeds 0     step-1 tables (seed 0 only)
  python demo/explore_cpu.py --seeds 0 1 2  full 3-seed exploratory comparison"""
import argparse, glob, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import common
from refimpl import core

ap = argparse.ArgumentParser()
ap.add_argument("--seeds", type=int, nargs="+", default=[0])
ap.add_argument("--out", default=os.path.join(common.ROOT, "demo_out", "explore_cpu"))
args = ap.parse_args()
P = common.prompts_by_id()
SPLIT = json.load(open(os.path.join(common.DEMO_DIR, "splits_lora.json")))["case_split"]
TUNE = [i for i, s in SPLIT.items() if s == "lora_tune"]
CELLS = sorted({P[i].cell for i in TUNE}, key=str)
BYCELL = {c: [i for i in TUNE if P[i].cell == c] for c in CELLS}
SLOPE_CELLS = [c for c in CELLS if P[BYCELL[c][0]].C is not None and P[BYCELL[c][0]].C < P[BYCELL[c][0]].V]
N, SEED = 10000, 0
LORA = os.path.join(common.ROOT, "demo_out", "lora")
LRS = (1e-4, 3e-4, 1e-3)


def run(arm, lr, seed):
  f = os.path.join(LORA, f"{arm}_lr{lr:.0e}_s{seed}.json")
  return json.load(open(f)) if os.path.exists(f) else None


def chosen_lr(arm):
  vals = {lr: run(arm, lr, 0)["tune_best"]["soft_regret"] for lr in LRS if run(arm, lr, 0)}
  return min(vals, key=lambda k: (vals[k], k)), vals


def exp_of(pr):
  return core.expected_bid({int(k): v for k, v in pr.items()})


def cell_arrays(probs_list):
  """probs_list: list of {pid: probs} (one per seed). -> per-cell mean soft regret, expected offer
  (averaged over seeds first)."""
  reg = {c: np.mean([np.mean([core.soft_regret(P[i], {int(k): v for k, v in pr[i].items()}) for i in BYCELL[c]]) for pr in probs_list]) for c in CELLS}
  exp = {c: np.mean([np.mean([exp_of(pr[i]) for i in BYCELL[c]]) for pr in probs_list]) for c in CELLS}
  return reg, exp


def slope(exp, cells):
  x = np.array([P[BYCELL[c][0]].C for c in cells], float)
  if len(set(x)) < 2:
    return np.nan
  return float(np.polyfit(x, [exp[c] for c in cells], 1)[0])


def boot_slope_diff(ea, eb, cells):
  """paired over cells: slope(ea) - slope(eb)"""
  rng = np.random.default_rng(SEED)
  out, dropped = [], 0
  for _ in range(N):
    s = [cells[j] for j in rng.integers(0, len(cells), len(cells))]
    d = slope(ea, s) - slope(eb, s)
    if np.isnan(d):
      dropped += 1
    else:
      out.append(d)
  return float(np.quantile(out, 0.025)), float(np.quantile(out, 0.975)), dropped


def boot_mean_diff(a, b):
  d = np.array([a[c] - b[c] for c in CELLS])
  rng = np.random.default_rng(SEED)
  bs = rng.choice(d, size=(N, len(d)), replace=True).mean(1)
  return float(d.mean()), float(np.quantile(bs, .025)), float(np.quantile(bs, .975)), int((d > 0).sum())


plain = {c["pid"]: c["probs"] for c in common.load_cases()}
arms = {"method": None, "neutral": None, "wrong_rule": None}
data = {"plain": cell_arrays([plain])}
info = {}
for a in arms:
  lr, vals = chosen_lr(a)
  seeds = [s for s in args.seeds if run(a, lr, s)]
  info[a] = {"lr": lr, "grid_seed0": {f"{k:.0e}": v for k, v in vals.items()}, "seeds": seeds}
  data[a] = cell_arrays([run(a, lr, s)["tune_probs_best"] for s in seeds])
L = ["# EXPLORATORY analyses (CPU, saved results; the frozen verdict 'not passed' stands)", "",
     f"Seeds used: {args.seeds}. Arms at their own seed-0 chosen lr: " + ", ".join(f"{a} {info[a]['lr']:.0e} (seeds {info[a]['seeds']}, grid {info[a]['grid_seed0']})" for a in arms) + ".",
     "Held-out cells are selected-on (lr, epoch). Bootstrap: paired over the 6 held-out cells, 10,000 resamples, seed 0.", ""]
S = {a: {"soft": data[a][0], "exp": data[a][1]} for a in data}
# soft regret table
L += ["## A. Soft regret on held-out cells (arm mean over seeds), difference control − method", "",
      "| Control | Control soft regret | Method soft regret | Difference [95% interval] | Cells method better |", "| --- | --- | --- | --- | --- |"]
res = {"soft": {}, "slope": {}}
for k in ("plain", "neutral", "wrong_rule"):
  m, lo, hi, nb = boot_mean_diff(data[k][0], data["method"][0])
  res["soft"][k] = [m, lo, hi, nb]
  L.append(f"| {k} | {np.mean(list(data[k][0].values())):.3f} | {np.mean(list(data['method'][0].values())):.3f} | {m:+.3f} [{lo:+.3f}, {hi:+.3f}] | {nb} of 6 |")
# split by cell type (G1 review: the slope is tied to the C<V cells; show the other cells apart)
OTHER = [c for c in CELLS if c not in SLOPE_CELLS]
L += ["", f"### A2. Same difference split by cell type (descriptive, no interval): C<V cells {SLOPE_CELLS} vs other cells {OTHER}", "",
      "| Control | mean diff (control − method) on C<V cells | on other cells |", "| --- | --- | --- |"]
for k in ("plain", "neutral", "wrong_rule"):
  L.append(f"| {k} | {np.mean([data[k][0][c] - data['method'][0][c] for c in SLOPE_CELLS]):+.3f} | {np.mean([data[k][0][c] - data['method'][0][c] for c in OTHER]):+.3f} |")
L.append("")
# per-seed
L += ["### A3. Per-seed held-out soft regret at each arm's chosen lr (seed 0 is the seed that chose the lr)", "", "| Arm | " + " | ".join(f"seed {s}" for s in (0, 1, 2)) + " |", "| --- | --- | --- | --- |"]
for a in arms:
  L.append(f"| {a} {info[a]['lr']:.0e} | " + " | ".join("—" if not run(a, info[a]['lr'], s) else f"{run(a, info[a]['lr'], s)['tune_best']['soft_regret']:.3f} (best ep {run(a, info[a]['lr'], s)['best_epoch']})" for s in (0, 1, 2)) + " |")
L.append("")
# slope
L += ["", f"## B. (a) Slope of expected offer on stated cost, cells with C < V ({len(SLOPE_CELLS)} cells: {SLOPE_CELLS})", "",
      "| Arm | Slope | Method − arm [95% interval] | resamples dropped (one distinct C) |", "| --- | --- | --- | --- |"]
sl = {a: slope(data[a][1], SLOPE_CELLS) for a in data}
for a in ("method", "plain", "neutral", "wrong_rule"):
  if a == "method":
    L.append(f"| method | {sl[a]:.3f} | | |")
    continue
  lo, hi, dr = boot_slope_diff(data["method"][1], data[a][1], SLOPE_CELLS)
  res["slope"][a] = [sl["method"] - sl[a], lo, hi, dr]
  L.append(f"| {a} | {sl[a]:.3f} | {sl['method'] - sl[a]:+.3f} [{lo:+.3f}, {hi:+.3f}] | {dr} of {N} |")
L += ["", "POST HOC choice (seed-0 slopes were seen before the rule was written). With 3 cost cells the bootstrap has about 7 distinct outcomes and is conditioned on dropping 1/9 of resamples; the interval is arithmetic on 3 points, NOT a sampling interval. Descriptive only.", ""]
# per-cell table
L += ["## B. (b) Per-cell table (arm mean over seeds)", "",
      "| Cell | Line | Best offer(s) | Expected offer: plain | method | neutral | wrong-rule | Soft regret: plain | method | neutral | wrong-rule | Method beats wrong-rule? |", "| " + " | ".join(["---"] * 12) + " |"]
for c in CELLS:
  p = P[BYCELL[c][0]]
  better = data["wrong_rule"][0][c] - data["method"][0][c] > 0
  L.append(f"| {c} | {p.line} | {core.oracle_bids(p)} | " + " | ".join(f"{data[a][1][c]:.2f}" for a in ("plain", "method", "neutral", "wrong_rule")) + " | " +
           " | ".join(f"{data[a][0][c]:.3f}" for a in ("plain", "method", "neutral", "wrong_rule")) + f" | {'yes' if better else 'NO'} |")
L.append("")
# fixed epochs
L += ["## B. (c) Held-out soft regret at fixed epochs (all saved runs, seed 0; history holds aggregates only, so no per-cell interval is possible)", "",
      "| Run | ep0 (plain) | ep1 | ep2 | ep3 | ep4 | slope ep1 | ep2 | ep3 | ep4 |", "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
for a in ("method", "neutral", "wrong_rule"):
  for lr in LRS:
    r = run(a, lr, 0)
    if not r:
      continue
    h = {x["epoch"]: x["tune"] for x in r["history"]}
    f = lambda e, k: "—" if e not in h or h[e].get(k) is None else f"{h[e][k]:.3f}"
    L.append(f"| {a} {lr:.0e} | {f(0, 'soft_regret')} | " + " | ".join(f(e, "soft_regret") for e in (1, 2, 3, 4)) + " | " + " | ".join(f(e, "slope_stated_cost") for e in (1, 2, 3, 4)) + " |")
L.append("")
# per-cell fixed-epoch (runs logged after the G1 change keep per-epoch held-out probabilities)
L += ["### Fixed-epoch per-cell soft regret difference (control − method), runs that logged per-epoch probabilities", ""]
for a in ("neutral", "wrong_rule"):
  for lr in LRS:
    for s_ in (0, 1, 2):
      rm, rc = run("method", info["method"]["lr"], s_), run(a, lr, s_)
      if not (rm and rc and "tune_probs" in rm["history"][-1] and "tune_probs" in rc["history"][-1]):
        continue
      for e in (1, 2, 3, 4):
        hm = {x["epoch"]: x for x in rm["history"]}; hc = {x["epoch"]: x for x in rc["history"]}
        if e in hm and e in hc:
          dm = cell_arrays([hm[e]["tune_probs"]])[0]; dc = cell_arrays([hc[e]["tune_probs"]])[0]
          m_, lo_, hi_, nb_ = boot_mean_diff(dc, dm)
          L.append(f"- {a} {lr:.0e} seed {s_} vs method seed {s_}, epoch {e}: {m_:+.3f} [{lo_:+.3f}, {hi_:+.3f}], method better in {nb_} of 6")
L.append("")
# free text
def say_cells(key, seeds_runs):
  out = {}
  for c in CELLS:
    out[c] = np.mean([np.mean([r[key]["per_case"][i]["hard_regret"] for i in BYCELL[c]]) for r in seeds_runs])
  return out
mr = [run("method", info["method"]["lr"], s) for s in info["method"]["seeds"]]
sp, sm = say_cells("say_plain", mr), say_cells("say_best", mr)
m, lo, hi, nb = boot_mean_diff(sp, sm)
L += ["## B. (d) Free-text hard regret, method vs plain (cell bootstrap)", "",
      f"plain {np.mean(list(sp.values())):.3f}, method {np.mean(list(sm.values())):.3f}; difference plain − method {m:+.3f} [{lo:+.3f}, {hi:+.3f}], method better in {nb} of 6 cells.", ""]
res["say"] = [m, lo, hi, nb]
os.makedirs(os.path.dirname(args.out), exist_ok=True)
open(args.out + f"_seeds{''.join(map(str, args.seeds))}.md", "w").write("\n".join(L) + "\n")
json.dump({"info": info, "res": res, "slope": sl}, open(args.out + f"_seeds{''.join(map(str, args.seeds))}.json", "w"), indent=1, default=float)
print("\n".join(L))

# ---- G2 additions: always-2 comparator, leave-one-cell-out, train-cell paired difference
L2 = ["", "## C. G2 additions (exploratory)", ""]
const2 = {c: float(np.mean([core.soft_regret(P[i], {k: float(k == 2) for k in core.PRICES}) for i in BYCELL[c]])) for c in CELLS}
m_, lo_, hi_, nb_ = boot_mean_diff(const2, data["method"][0])
L2.append(f"- always-2 − method: {m_:+.3f} [{lo_:+.3f}, {hi_:+.3f}], method better in {nb_} of 6 cells (always-2 mean {np.mean(list(const2.values())):.3f}).")
for k in ("wrong_rule", "neutral"):
  d = {c: data[k][0][c] - data["method"][0][c] for c in CELLS}
  L2.append(f"- leave-one-cell-out mean of ({k} − method): " + ", ".join(f"without {c}: {np.mean([v for cc, v in d.items() if cc != c]):+.3f}" for c in CELLS))
# train cells (fitted, not selected-on, each arm fits its own teacher)
TRAIN = [i for i, s in SPLIT.items() if s == "lora_train"]
TC = sorted({P[i].cell for i in TRAIN}, key=str)
def train_cells(arm_runs):
  return {c: np.mean([np.mean([core.soft_regret(P[i], {int(k): v for k, v in r["train_probs_best"][i].items()}) for i in TRAIN if P[i].cell == c]) for r in arm_runs]) for c in TC}
tp = {c: np.mean([core.soft_regret(P[i], {int(k): v for k, v in plain[i].items()}) for i in TRAIN if P[i].cell == c]) for c in TC}
tr = {a: train_cells([run(a, info[a]["lr"], s) for s in info[a]["seeds"]]) for a in arms}
L2.append(f"- train cells (11, fitted; each arm fits its own teacher): plain {np.mean(list(tp.values())):.3f}, " + ", ".join(f"{a} {np.mean(list(tr[a].values())):.3f}" for a in arms))
d = np.array([tr["wrong_rule"][c] - tr["method"][c] for c in TC]); rng = np.random.default_rng(SEED); bs = rng.choice(d, size=(N, len(d))).mean(1)
L2.append(f"- train cells wrong-rule − method: {d.mean():+.3f} [{np.quantile(bs, .025):+.3f}, {np.quantile(bs, .975):+.3f}] over 11 cells")
L2.append("- fixed-epoch per-cell section above is empty because the method runs predate the per-epoch probability logging (only wrong-rule 3e-4/1e-3 and neutral seed 1 have it).")
open(args.out + f"_seeds{''.join(map(str, args.seeds))}.md", "a").write("\n".join(L2) + "\n")
print("\n".join(L2))
