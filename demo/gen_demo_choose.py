"""Choose the live demo cases by a FIXED RULE (written before running; display only, no test-set conclusion is drawn or reported).

Candidates: the first case (name variant n0) of each test_same cell, in cases.jsonl order.
Main case  : the first candidate of type 'below' (stated cost below resale) whose plain soft regret is >= 1 coin and whose examples-adapter
             top offer (order-averaged) is a best offer.
Backups    : the same rule for type 'no_cost' and for type 'at_or_above'. If no candidate of a type has plain soft regret >= 1 coin, the
             fallback is the candidate of that type with the largest plain soft regret among those where the examples top offer is a best
             offer (first in file order on ties), and the record says so.
The scan stops for a type at its first qualifying candidate. Writes demo/gen/demo_live_cases.json.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
import floor
import gen_cases as g

THRESH = 1.0


def main():
  eng = floor.GenEngine("9b")
  seen, cands = set(), []
  for c in eng.cases.values():
    if c["split"] == "test_same" and c["cell"] not in seen:
      seen.add(c["cell"]); cands.append(c)
  chosen, scanned, fallback = {}, {t: [] for t in g.TYPES}, {}
  for c in cands:
    t = c["type"]
    if t in chosen:
      continue
    pl = eng.score(c, ("plain", None)); ex = eng.score(c, ("adapter", "examples"))
    reg = floor.gen_soft_regret(c, pl.probs); top = c["grid"][floor.gen_top(ex.probs)]
    ok_top = top in c["best_offers"]
    scanned[t].append({"cid": c["cid"], "plain_soft_regret": round(reg, 3), "examples_top": top, "examples_top_is_best": ok_top})
    if ok_top and reg >= THRESH:
      chosen[t] = c["cid"]
    elif ok_top and (t not in fallback or reg > fallback[t][0] + 1e-12):
      fallback[t] = (reg, c["cid"])
    if len(chosen) == 3:
      break
  rule_used = {}
  for t in g.TYPES:
    if t in chosen:
      rule_used[t] = "primary rule"
    else:
      # type never qualified: scan finished all candidates for it (the loop only breaks when all three are chosen)
      chosen[t] = fallback[t][1]; rule_used[t] = f"FALLBACK (no candidate with plain soft regret >= {THRESH}); largest plain soft regret {fallback[t][0]:.2f}"
  out = {"rule": __doc__.strip(), "main": chosen["below"], "backup_no_cost": chosen["no_cost"], "backup_at_or_above": chosen["at_or_above"],
         "how": rule_used, "n_scanned_per_type": {t: len(v) for t, v in scanned.items()}, "scan": scanned}
  json.dump(out, open(os.path.join(g.OUT, "demo_live_cases.json"), "w"), indent=1)
  print(json.dumps({k: out[k] for k in ("main", "backup_no_cost", "backup_at_or_above", "how", "n_scanned_per_type")}, indent=1))


if __name__ == "__main__":
  main()
