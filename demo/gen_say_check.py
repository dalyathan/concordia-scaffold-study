"""Free-text (greedy `say`) check for the stage: plain vs the examples adapter vs the teacher-distil adapter on 30 TUNE cells
(the first 10 of each case type in file order, name variant n0). Per condition: the first-token pick (order-averaged), the parsed free-text
offer, whether they agree, and hard regret of both. No training, no test cells. Writes demo_out/gen_say_check.json and prints a table.

  PYTHONPATH=concordia:. .venv/bin/python demo/gen_say_check.py
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import common
import floor
import gen_cases as g


def main():
  eng = floor.GenEngine("9b")
  chosen = []
  for t in g.TYPES:
    chosen += [c for c in eng.cases.values() if c["split"] == "tune" and c["type"] == t and c["name_variant"] == 0][:10]
  assert len(chosen) == 30
  rows = []
  for cond in (("plain", None), ("adapter", "examples"), ("adapter", "teacher")):
    for c in chosen:
      probs = eng.score(c, cond).probs
      pick = c["grid"][floor.gen_top(probs)]
      text, k = eng.say(c, cond)
      pay = lambda price: g.payoff(c["V"], c["grid"], c["C"], c["prior"], price)
      rows.append({"condition": cond[1] or "plain", "cid": c["cid"], "type": c["type"], "pick": pick, "say": text.strip(), "say_offer": k,
                   "agree": k == pick, "on_grid": k in c["grid"] if k is not None else False,
                   "hard_pick": c["best_payoff"] - pay(pick), "hard_say": c["best_payoff"] - pay(k) if (k is not None and k in c["grid"]) else None})
  out = ["condition   n  parsed on-grid agree  hard(pick,all) hard(pick,on-grid cases) hard(say,on-grid)"]
  summ = {}
  for cond in ("plain", "examples", "teacher"):
    r = [x for x in rows if x["condition"] == cond]
    parsed = [x for x in r if x["hard_say"] is not None]       # on-grid offers only: off-grid prices have no comparable regret
    summ[cond] = {"n": len(r), "parsed": len(parsed), "on_grid": sum(x["on_grid"] for x in r), "agree": sum(x["agree"] for x in r),
                  "hard_pick": float(np.mean([x["hard_pick"] for x in r])), "hard_pick_on_those": float(np.mean([x["hard_pick"] for x in parsed])) if parsed else None, "agree_among_on_grid": sum(x["agree"] for x in parsed), "hard_say_parsed": float(np.mean([x["hard_say"] for x in parsed])) if parsed else None,
                  "by_type": {t: {"agree": sum(x["agree"] for x in r if x["type"] == t), "hard_pick": float(np.mean([x["hard_pick"] for x in r if x["type"] == t])),
                                  "hard_say": float(np.mean([x["hard_say"] for x in parsed if x["type"] == t])) if any(x["type"] == t for x in parsed) else None} for t in g.TYPES}}
    s = summ[cond]
    out.append(f"{cond:<10} {s['n']:>2} {s['parsed']:>7} {s['on_grid']:>7} {s['agree']:>5}  {s['hard_pick']:>9.2f} {s['hard_pick_on_those']:>14.2f} {s['hard_say_parsed']:>16.2f}")
  json.dump({"rule": "first 10 tune cells per type in file order, name variant n0", "summary": summ, "rows": rows}, open(os.path.join(common.ROOT, "demo_out", "gen_say_check.json"), "w"), indent=1)
  print("\n".join(out))
  for t in g.TYPES:
    print(t, {c: (summ[c]["by_type"][t]["agree"], round(summ[c]["by_type"][t]["hard_pick"], 2), None if summ[c]["by_type"][t]["hard_say"] is None else round(summ[c]["by_type"][t]["hard_say"], 2)) for c in summ})
  print("examples of disagreement:")
  for x in [x for x in rows if not x["agree"]][:8]:
    print(x["condition"], x["cid"][:30], "pick", x["pick"], "say", repr(x["say"][:40]))


if __name__ == "__main__":
  main()
