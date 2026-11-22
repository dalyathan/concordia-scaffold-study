"""Step B report (CPU): soft regret of plain and the four text rows by case type on generated TRAIN and TUNE cells, with cell-bootstrap
intervals (10,000, seed 0), the slope of the expected offer on the stated cost (cost-below cells), baselines, and the difference
to plain. Writes demo_out/gen_text_report.md."""
import collections, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import common
import gen_cases as g

ROOT = common.ROOT
cells = {c["cell"]: c for c in json.load(open(os.path.join(g.OUT, "cells.json")))["cells"]}
cases = {c["cid"]: c for c in map(json.loads, open(os.path.join(g.OUT, "cases.jsonl")))}
plain = {r["cid"]: r for r in map(json.loads, open(os.path.join(ROOT, "demo_out", "gen_plain_scores.jsonl")))}
rows = collections.defaultdict(dict)
for r in map(json.loads, open(os.path.join(ROOT, "demo_out", "gen_text_rows.jsonl"))):
  rows[r["row"]][r["cid"]] = r
rows["plain"] = plain
NAMES = ("plain", "method_original", "teacher_v1", "teacher", "neutral", "wrong_rule")


def cellvals(row, split, typ=None):
  by = collections.defaultdict(list)
  for cid, r in rows[row].items():
    c = cases[cid]
    if c["split"] == split and (typ is None or c["type"] == typ):
      by[c["cell"]].append(r["soft_regret"])
  return {k: float(np.mean(v)) for k, v in by.items() if len(v) == 2}


def boot(d, n=10000):
  v = np.asarray(d, float)
  b = np.random.default_rng(0).choice(v, size=(n, len(v)), replace=True).mean(1)
  return float(v.mean()), float(np.quantile(b, .025)), float(np.quantile(b, .975))


def slope(row, split):
  xs, ys = [], []
  for cid, r in rows[row].items():
    c = cases[cid]
    if c["split"] == split and c["type"] == "below":
      xs.append(c["C"]); ys.append(r["expected_offer"] if "expected_offer" in r else float(np.dot(r["probs"], c["grid"])))
  return float(np.polyfit(xs, ys, 1)[0]) if len(set(xs)) > 1 else float("nan")


def baseline(split, typ, kind):
  v = []
  for k, c in cells.items():
    if c["split"] != split or (typ and c["type"] != typ):
      continue
    pay, best, grid = c["payoffs"], c["best_payoff"], c["grid"]
    if kind == "cheapest":
      v.append(best - pay[0])
    else:
      pos = next((i for i, x in enumerate(grid) if x >= c["C"]), len(grid) - 1) if c["C"] is not None and c["C"] < c["V"] else 0
      v.append(best - pay[pos])
  return float(np.mean(v))


L = ["# Text rows on generated train and tune cells (plain Gemma 2 9B-it, five orders; test sets not scored)", "",
     "Notes block inserted before the question. Rows: plain (no notes), original method paragraph (earlier work), teacher method (Claude Opus, frozen), "
     "same-length neutral text, wrong rule; teacher_v1 = the first paragraph, teacher = the frozen winner of the closed loop (selected on 42 loop cells, so optimistic there) (\"Offer half the stated cost.\"). Soft regret = best expected payoff minus the model's; cell means "
     "(two name variants), cell-bootstrap 95% intervals (10,000, seed 0). 'diff' = plain minus row (positive = row better).", ""]
for split in ("train", "tune"):
  n = len(cellvals("plain", split))
  L += [f"## {split} ({n} cells)", "", "| Row | all types | below | at_or_above | no_cost | slope of expected offer on stated cost (below cells) | letter mass | diff vs plain, all types [95%] |", "| --- | --- | --- | --- | --- | --- | --- | --- |"]
  for name in NAMES:
    ok = sum(1 for cid in rows[name] if cases[cid]["split"] == split)
    if ok < 2 * n:
      L.append(f"| {name} | (incomplete: {ok // 2} of {n} cells) | | | | | | |")
      continue
    allv = cellvals(name, split)
    pv = cellvals("plain", split)
    cols = []
    for t in (None, "below", "at_or_above", "no_cost"):
      v = cellvals(name, split, t)
      m = boot(list(v.values()))
      cols.append(f"{m[0]:.3f} [{m[1]:.3f}, {m[2]:.3f}]")
    d = boot([pv[k] - allv[k] for k in allv])
    mass = float(np.mean([r["mass"] for cid, r in rows[name].items() if cases[cid]["split"] == split]))
    L.append(f"| {name} | " + " | ".join(cols) + f" | {slope(name, split):.2f} | {mass:.2f} | {d[0]:+.3f} [{d[1]:+.3f}, {d[2]:+.3f}] |")
  L.append("| always-cheapest | " + " | ".join(f"{baseline(split, t, 'cheapest'):.3f}" for t in (None, "below", "at_or_above", "no_cost")) + " | | | |")
  L.append("| stated-cost rule | " + " | ".join(f"{baseline(split, t, 'rule'):.3f}" for t in (None, "below", "at_or_above", "no_cost")) + " | | | |")
  L.append("")
B = json.load(open(os.path.join(g.OUT, "lora_select_cells_B.json")))
A = json.load(open(os.path.join(g.OUT, "lora_select_cells.json")))
for label, keys in (("LoRA selection set B (42 train cells not used by the loop, the packet or LoRA training)", B), ("loop set A (42 cells the winner was selected on: optimistic)", A)):
  L += [f"## {label}", "", "| Row | soft regret [95%] | below | at_or_above | no_cost |", "| --- | --- | --- | --- | --- |"]
  for name in NAMES:
    by = collections.defaultdict(list)
    for cid, r in rows[name].items():
      if cases[cid]["cell"] in keys and cases[cid]["name_variant"] == 0:
        by[cases[cid]["cell"]].append(r["soft_regret"])
    if len(by) < len(keys):
      L.append(f"| {name} | incomplete ({len(by)} of {len(keys)}) | | | |"); continue
    v = {k: float(np.mean(x)) for k, x in by.items()}
    m = boot(list(v.values()))
    L.append(f"| {name} | {m[0]:.3f} [{m[1]:.3f}, {m[2]:.3f}] | " + " | ".join(f"{np.mean([x for k, x in v.items() if cells[k]['type'] == t]):.3f}" for t in g.TYPES) + " |")
  L.append("")
open(os.path.join(ROOT, "demo_out", "gen_text_report.md"), "w").write("\n".join(L) + "\n")
print("\n".join(L))
