"""Step 8: score a teacher response (JSON, see demo/teacher_packet.md).

  python demo/check_teacher.py demo/teacher_response.json

Predictions are scored against plain Gemma's actual top offer on those test cases
('right' = a best offer, 'too_high' / 'too_low' = above / below every best offer),
beside two baselines: the majority class, and the rule "below about 3 coins it
overbids, above it underbids" (applied to the case's smallest best offer: < 3 ->
too_high, > 3 -> too_low, = 3 -> right). Pairs are checked with the step 5 checks
(pairs_template.checks) plus: each good offer is a best offer, each bad offer is not."""
import collections, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common, pairs_template
from refimpl import core

LABELS = ("too_high", "too_low", "right")


def truth(pids):
  cases = {c["pid"]: c for c in common.load_cases()}
  return {pid: ("right" if cases[pid]["direction"] == "best" else cases[pid]["direction"]) for pid in pids}


def rule(p):
  b = min(core.oracle_bids(p))
  return "too_high" if b < 3 else "too_low" if b > 3 else "right"


def score_predictions(pred: dict, pids) -> dict:
  P = common.prompts_by_id()
  t = truth(pids)
  maj = collections.Counter(t.values()).most_common(1)[0][0]
  acc = lambda f: sum(f(pid) == t[pid] for pid in pids) / len(pids)
  return {"n": len(pids), "teacher": acc(lambda pid: pred.get(pid)),
          "missing": [pid for pid in pids if pred.get(pid) not in LABELS],
          "majority_class": maj, "majority_baseline": acc(lambda pid: maj),
          "rule_baseline": acc(lambda pid: rule(P[pid])),
          "truth_counts": dict(collections.Counter(t.values()))}


def check_pairs(pairs: list, n_tokens) -> dict:
  P = common.prompts_by_id()
  rows = []
  for x in pairs:
    p = P[x["pid"]]
    best = core.oracle_bids(p)
    rows.append({**x, "bad_direction": "above" if x["bad_offer"] > max(best) else "below"})
  c = pairs_template.checks(rows, n_tokens)
  c["good_offers_are_best"] = all(x["good_offer"] in core.oracle_bids(P[x["pid"]]) for x in pairs)
  c["bad_offers_are_not_best"] = all(x["bad_offer"] not in core.oracle_bids(P[x["pid"]]) for x in pairs)
  return c


def main(path):
  resp = json.load(open(path))
  idx = json.load(open(os.path.join(common.DEMO_DIR, "teacher_packet_index.json")))
  from transformers import AutoTokenizer
  from refimpl import runtime
  tok = AutoTokenizer.from_pretrained(runtime.resolve("9b")[0])
  n_tok = lambda s: len(tok.encode(s, add_special_tokens=False))
  import re
  out = {"predictions": score_predictions(resp.get("predictions", {}), idx["test_predict"]),
         "pairs": check_pairs(resp.get("pairs", []), n_tok) if resp.get("pairs") else None,
         "method_has_digits": bool(re.search(r"\d", resp.get("method", "")))}
  print(json.dumps(out, indent=1))
  return out


if __name__ == "__main__":
  main(sys.argv[1])
