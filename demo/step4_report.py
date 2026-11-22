"""Step 4 report: regret per text row and case type on the tuning cases."""
import collections, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import common, textrows

recs = [json.loads(l) for l in open(os.path.join(common.ROOT, "demo_out", "text_rows_tuning.jsonl"))]
P = common.prompts_by_id()
types = ("cost below resale", "cost at or above resale", "no cost", "all")
tab = collections.defaultdict(dict)
for row in textrows.ROWS:
  for t in types:
    rs = [r for r in recs if r["row"] == row and (t == "all" or common.case_type(P[r["pid"]]) == t)]
    tab[row][t] = {"n": len(rs), "hard": float(np.mean([r["hard_regret"] for r in rs])),
                   "soft": float(np.mean([r["soft_regret"] for r in rs])),
                   "nonzero": float(np.mean([r["hard_regret"] > 0 for r in rs])),
                   "mass": float(np.mean([r["mass"] for r in rs]))}
json.dump(tab, open(os.path.join(common.DEMO_DIR, "step4.json"), "w"), indent=1)
label = {"answer_only": "answer-only (UPPER BOUND)", "template": "template reasoning",
         "wrong_rule": "wrong rule", "acceptance_rule": "acceptance rule",
         "neutral": "same-length neutral"}
print("| Row | Soft regret: cost < resale | cost ≥ resale | no cost | all | Hard regret (all) | Non-zero (all) | Letter mass |")
print("| --- | --- | --- | --- | --- | --- | --- | --- |")
for row in textrows.ROWS:
  d = tab[row]
  print(f"| {label.get(row, row)} | " + " | ".join(f"{d[t]['soft']:.3f}" for t in types)
        + f" | {d['all']['hard']:.3f} | {d['all']['nonzero']:.0%} | {d['all']['mass']:.2f} |")
