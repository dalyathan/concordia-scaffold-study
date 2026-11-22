"""Failure map of PLAIN Gemma on the generated TRAIN and TUNE cells (CPU; reads demo_out/gen_plain_scores.jsonl).
Unit = cell (mean of its two name variants); intervals are cell bootstrap, 10,000 resamples, seed 0. Test splits are
never read. Writes demo_out/gen_failure_map.md and .json."""
import collections, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import common
import gen_cases as g
from refimpl import core

ROOT = common.ROOT
cells = {c["cell"]: c for c in json.load(open(os.path.join(g.OUT, "cells.json")))["cells"]}
rows = [json.loads(l) for l in open(os.path.join(ROOT, "demo_out", "gen_plain_scores.jsonl"))]
assert all(r["split"] in ("train", "tune") for r in rows)
by = collections.defaultdict(list)
for r in rows:
  by[r["cell"]].append(r)
OLD_DEV = {core.steering_cell_split(((V, line) if C is None else (V, "C", C))) for V in core.VALUES for line, C in ()}


def baselines(c):
  grid, pay = c["grid"], c["payoffs"]
  best = c["best_payoff"]
  uni = best - float(np.mean(pay))
  cheapest = best - pay[0]
  if c["C"] is not None and c["C"] < c["V"]:
    pos = next((i for i, k in enumerate(grid) if k >= c["C"]), len(grid) - 1)
  else:
    pos = 0
  return {"uniform": uni, "cheapest": cheapest, "stated_cost_rule": best - pay[pos]}


def cell_row(name):
  c, rs = cells[name], by[name]
  probs = np.mean([r["probs"] for r in rs], axis=0)
  top = int(np.argmax(probs))
  bp = c["best_positions"]
  b = baselines(c)
  Vb = "2-3" if c["V"] <= 3 else "4-5" if c["V"] <= 5 else "6-7" if c["V"] <= 7 else "8-9"
  grid = c["grid"]
  if c["C"] is None:
    crel = "no stated cost"
  elif c["C"] < grid[0]:
    crel = "C below grid min"
  elif c["C"] in grid:
    crel = "C on grid"
  else:
    crel = "C between grid prices"
  lo, hi = c["prior"]
  return {"cell": name, "split": c["split"], "type": c["type"], "V": c["V"], "Vband": Vb, "grid": c["grid_name"], "wording": c["wording"],
          "line": c["line"], "soft": float(np.mean([r["soft_regret"] for r in rs])), "hard": float(np.mean([r["hard_regret"] for r in rs])),
          "mass_on_best": float(sum(probs[i] for i in bp)), "top_in_best": float(top in bp), "letter_mass": float(np.mean([r["mass"] for r in rs])),
          "top_position": top, "n_best": len(bp), "best_le_0": c["best_payoff"] <= 1e-12, "crel": crel,
          "C_in_prior": None if c["C"] is None else bool(lo <= c["C"] <= hi), "uniform": b["uniform"], "cheapest": b["cheapest"],
          "stated_cost_rule": b["stated_cost_rule"], "chance_mass": len(bp) / 5.0, "label_key": (c["V"], c["grid_name"], c["C"], None if c["C"] is not None else tuple(c["prior"]))}


R = [cell_row(n) for n in by if len(by[n]) == 2]
assert len(R) == len(by)


def boot(vals, n=10000):
  v = np.asarray(vals, float)
  b = np.random.default_rng(0).choice(v, size=(n, len(v)), replace=True).mean(1)
  return float(v.mean()), float(np.quantile(b, .025)), float(np.quantile(b, .975))


def table(title, rs, key, metrics=("soft", "mass_on_best", "top_in_best", "letter_mass", "cheapest", "stated_cost_rule", "uniform")):
  L = [f"### {title}", "", "| " + key + " | cells | soft regret [95%] | mass on best set (chance) | top in best set | letter mass | always-cheapest | stated-cost rule | uniform |", "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
  groups = collections.defaultdict(list)
  for r in rs:
    groups[r[key] if not isinstance(r[key], tuple) else str(r[key])].append(r)
  for k in sorted(groups, key=str):
    g_ = groups[k]
    s = boot([r["soft"] for r in g_])
    L.append(f"| {k} | {len(g_)} | {s[0]:.3f} [{s[1]:.3f}, {s[2]:.3f}] | {np.mean([r['mass_on_best'] for r in g_]):.2f} ({np.mean([r['chance_mass'] for r in g_]):.2f}) | "
             f"{np.mean([r['top_in_best'] for r in g_]):.2f} | {np.mean([r['letter_mass'] for r in g_]):.2f} | {np.mean([r['cheapest'] for r in g_]):.3f} | "
             f"{np.mean([r['stated_cost_rule'] for r in g_]):.3f} | {np.mean([r['uniform'] for r in g_]):.3f} |")
  return L + [""]


L = ["# Failure map of plain Gemma 2 9B-it on generated TRAIN and TUNE cells (the test sets were not scored)", "",
     f"{len(R)} cells ({sum(r['split'] == 'train' for r in R)} train, {sum(r['split'] == 'tune' for r in R)} tune), 2 name variants each, five orders. "
     "Soft regret = best expected payoff minus the model's expected payoff (order-averaged first-token probabilities). Cell-clustered bootstrap (10,000, seed 0). "
     "Baselines use the same labels: uniform over the five offers, always-cheapest, and a stated-cost rule (cheapest grid price >= C if C < V, else cheapest).", ""]
for sp in ("train", "tune"):
  rs = [r for r in R if r["split"] == sp]
  L += [f"## {sp}", ""]
  s = boot([r["soft"] for r in rs]); h = boot([r["hard"] for r in rs])
  L += [f"Overall: soft regret {s[0]:.3f} [{s[1]:.3f}, {s[2]:.3f}], hard regret {h[0]:.3f} [{h[1]:.3f}, {h[2]:.3f}], mass on best set {np.mean([r['mass_on_best'] for r in rs]):.2f} "
        f"(chance {np.mean([r['chance_mass'] for r in rs]):.2f}), letter mass {np.mean([r['letter_mass'] for r in rs]):.2f}; "
        f"baselines: uniform {np.mean([r['uniform'] for r in rs]):.3f}, always-cheapest {np.mean([r['cheapest'] for r in rs]):.3f}, stated-cost rule {np.mean([r['stated_cost_rule'] for r in rs]):.3f}.", ""]
  for key, title in (("type", "by type"), ("Vband", "by resale-value band"), ("grid", "by price grid"), ("wording", "by wording"), ("line", "by seller line (collinear with type)"),
                     ("crel", "by stated cost relative to the grid (information cells and no-cost)")):
    L += table(f"{sp}: {title}", rs, key)
  for typ in g.TYPES:
    L += table(f"{sp}: type = {typ}, by V band", [r for r in rs if r["type"] == typ], "Vband")
  L += table(f"{sp}: by number of best offers", rs, "n_best")
  L += table(f"{sp}: cells where the best payoff is <= 0 (arbitrary labels)", rs, "best_le_0")
  L += table(f"{sp}: stated cost inside the stated prior range", [r for r in rs if r["C_in_prior"] is not None], "C_in_prior")
  pos = collections.Counter(r["top_position"] for r in rs)
  L += [f"Position of the model's top offer in the grid (0 = cheapest): {dict(sorted(pos.items()))}; best-offer positions in the labels (first best): "
        f"{dict(sorted(collections.Counter(cells[r['cell']]['best_positions'][0] for r in rs).items()))}", ""]
# matched analogues of the hard slices, on train only
tr = [r for r in R if r["split"] == "train"]
L += ["## Train analogues of the hard slices (for reading the test-hard slices later)", ""]
L += table("train: always-profitable regime (V >= largest price of the grid)", [r for r in tr if r["V"] >= max(cells[r["cell"]]["grid"])], "type")
L += table("train: V 8-9 on grid A", [r for r in tr if r["V"] >= 8 and r["grid"] == "A"], "type")
# label-key overlap
trk = {r["label_key"] for r in R if r["split"] == "train"}
for sp in ("tune",):
  ks = [r["label_key"] for r in R if r["split"] == sp]
  L += [f"Label-key overlap (V, grid, C or prior) of {sp} cells with train cells: {sum(k in trk for k in ks)} of {len(ks)} (cells whose label is identical to a train cell's).", ""]
cs = json.load(open(os.path.join(g.OUT, "cells.json")))["cells"]
trk_all = trk
L += [f"For the locked test sets (labels only, no scoring): test_same cells with a label key identical to a train cell: "
      f"{sum((c['V'], c['grid_name'], c['C'], None if c['C'] is not None else tuple(c['prior'])) in trk_all for c in cs if c['split'] == 'test_same')} of {sum(c['split'] == 'test_same' for c in cs)}; "
      f"test_hard: {sum((c['V'], c['grid_name'], c['C'], None if c['C'] is not None else tuple(c['prior'])) in trk_all for c in cs if c['split'] == 'test_hard')} of {sum(c['split'] == 'test_hard' for c in cs)}.", ""]
old_dev = [c for c in cs if c["grid_name"] == "A" and tuple(c["prior"]) == (1, 5) and c["V"] in core.VALUES]
L += [f"Cells at grid A, prior (1,5), V 2-6 (same game structure as the old cells; old test cells excluded by construction; old train/tune cells possible): "
      + ", ".join(f"{s}: {sum(c['split'] == s for c in old_dev)}" for s in ("train", "tune", "test_same", "test_hard")) + ". Old adapters and old rule-teacher data must not be scored on this set.", ""]
open(os.path.join(ROOT, "demo_out", "gen_failure_map.md"), "w").write("\n".join(L) + "\n")
json.dump(R, open(os.path.join(ROOT, "demo_out", "gen_failure_map.json"), "w"), default=str)
print("\n".join(L))
