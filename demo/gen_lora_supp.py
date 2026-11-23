"""POST-HOC descriptive checks requested by the G2 reviewers (tune cells only, CPU; nothing here changes the frozen verdict).
Writes demo_out/gen_lora_supp.md."""
import collections, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import common
import gen_cases as g
ROOT = common.ROOT
cells = {c["cell"]: c for c in json.load(open(os.path.join(g.OUT, "cells.json")))["cells"]}
cases = {c["cid"]: c for c in map(json.loads, open(os.path.join(g.OUT, "cases.jsonl")))}
TUNE = sorted(k for k, c in cells.items() if c["split"] == "tune")
tr = json.load(open(os.path.join(g.OUT, "lora_train_cells.json")))
key = lambda k: (cells[k]["V"], cells[k]["grid_name"], cells[k]["C"], None if cells[k]["C"] is not None else tuple(cells[k]["prior"]))
trk = {key(k) for k in tr}
overlap = {k: key(k) in trk for k in TUNE}
def run(a, lr, s): return json.load(open(f"{ROOT}/demo_out/gen_lora/gen_{a}_lr{lr}_s{s}.json"))
def cellprobs(probs):
  by = collections.defaultdict(list)
  for cid, p in probs.items(): by[cases[cid]["cell"]].append(p)
  return {k: np.mean(v, 0) for k, v in by.items()}
def avg(rs):
  cp = [cellprobs(r["tune_probs_best"]) for r in rs]
  return {k: np.mean([c[k] for c in cp], 0) for k in TUNE}
plain = {}
for r in map(json.loads, open(f"{ROOT}/demo_out/gen_plain_scores.jsonl")):
  if cases[r["cid"]]["split"] == "tune": plain.setdefault(cases[r["cid"]]["cell"], []).append(r["probs"])
plain = {k: np.mean(v, 0) for k, v in plain.items()}
P = {"plain": plain, "teacher-distil": avg([run("teacher", "1e-04", s) for s in (0, 1, 2)]),
     "method-distil": avg([run("method_original", "1e-04", s) for s in (0, 1, 2)]),
     "wrong-rule-distil (1 seed)": avg([run("wrong_rule", "1e-04", 0)]),
     "ceiling lr 3e-4": avg([run("answer_only", "3e-04", 0)]), "ceiling lr 1e-4": avg([run("answer_only", "1e-04", 0)])}
soft = lambda p, k: cells[k]["best_payoff"] - float(np.dot(p[k], cells[k]["payoffs"]))
def boot(v):
  v = np.asarray(v, float); b = np.random.default_rng(0).choice(v, size=(10000, len(v)), replace=True).mean(1)
  return f"{v.mean():+.3f} [{np.quantile(b, .025):+.3f}, {np.quantile(b, .975):+.3f}]"
types = ("below", "at_or_above", "no_cost")
cheap_soft = {k: cells[k]["best_payoff"] - cells[k]["payoffs"][0] for k in TUNE}
L = ["# Post-hoc descriptive checks (G2 reviewer requests; tune cells; do not change the frozen verdict)", "",
     "## Mass on the cheapest option (position 0), mean over cells, by type; and soft regret", "",
     "| Arm | cheapest mass below | at_or_above | no_cost | soft regret all |", "| --- | --- | --- | --- | --- |"]
for n, p in P.items():
  L.append(f"| {n} | " + " | ".join(f"{np.mean([p[k][0] for k in TUNE if cells[k]['type'] == t]):.2f}" for t in types) + f" | {np.mean([soft(p, k) for k in TUNE]):.3f} |")
L += ["", "## Teacher-distil vs always-cheapest (cheapest regret minus teacher regret; positive = teacher better), paired cell bootstrap", ""]
for t in (None,) + types:
  ks = [k for k in TUNE if t is None or cells[k]["type"] == t]
  L.append(f"- {t or 'all'} ({len(ks)} cells): {boot([cheap_soft[k] - soft(P['teacher-distil'], k) for k in ks])}")
L += ["", f"## Gain over plain by overlap of (V, grid, C or prior) with the 100 training cells ({sum(overlap.values())} overlapping, {len(TUNE) - sum(overlap.values())} not)", ""]
for n in ("teacher-distil", "method-distil"):
  for lab, f in (("overlapping", True), ("non-overlapping", False)):
    ks = [k for k in TUNE if overlap[k] == f]
    L.append(f"- {n}, {lab}: plain minus arm {boot([soft(plain, k) - soft(P[n], k) for k in ks])}")
tp = {}
import glob
for r in map(json.loads, open(f"{ROOT}/demo_out/gen_text_rows.jsonl")):
  if r["row"] == "teacher" and cases[r["cid"]]["split"] == "tune": tp.setdefault(cases[r["cid"]]["cell"], []).append(r["soft_regret"])
tp = {k: np.mean(v) for k, v in tp.items()}
for lab, f in (("overlapping", True), ("non-overlapping", False)):
  ks = [k for k in TUNE if overlap[k] == f]
  L.append(f"- teacher text in the prompt, {lab}: plain minus text {boot([soft(plain, k) - tp[k] for k in ks])}")
L += ["", "## Ceiling at both learning rates (tune soft regret)", ""]
for n in ("ceiling lr 3e-4", "ceiling lr 1e-4"):
  L.append(f"- {n}: {np.mean([soft(P[n], k) for k in TUNE]):.3f}")
L += ["", "## Neutral-distil selection-set soft regret by epoch (set B; plain = epoch 0)", ""]
for s in (0, 1, 2):
  r = run("neutral", "1e-04", s); L.append(f"- seed {s}: " + ", ".join(f"{h['tune']['soft_regret']:.3f}" for h in r["history"]))
open(f"{ROOT}/demo_out/gen_lora_supp.md", "w").write("\n".join(L) + "\n")
print("\n".join(L))
