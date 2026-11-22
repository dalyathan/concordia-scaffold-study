"""Step 5: good/bad and offer-lower reasoning paragraphs from one template.

paragraph(p, k) fills one template with the case's facts and a concluded offer k
(arithmetic for k is stated truthfully). Good pairs conclude a best offer
(core.oracle_bids); bad pairs conclude an offer just outside the best set, chosen so
that about half are above and half below, and the mean concluded price of the good
and bad sets differ by at most 0.25 coins. Offer-lower pairs: A concludes one coin
below B. Cases where every offer is optimal are skipped.

  python demo/pairs_template.py            print both checks (needs the tokenizer)
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402
from refimpl import core  # noqa: E402


def coins(k: int) -> str:
  return f"{k} coin" if k == 1 else f"{k} coins"


def paragraph(p: core.Prompt, k: int) -> str:
  """One template for every case type; only the facts and the concluded offer vary."""
  n = p.buyer
  if p.C is not None:
    fact = (f"The seller says the fruit cost {coins(p.C)} at the farm, and a seller accepts "
            f"any offer at or above that cost.")
    accepted = k >= p.C
    profit = (p.V - k) if accepted else 0
    value = (f"An offer of {coins(k)} would be {'accepted' if accepted else 'refused'}, "
             f"leaving a profit of {profit} coins.")
  else:
    fact = ("The seller's farm cost is unknown and equally likely to be any price from 1 to 5 "
            "coins, and a seller accepts any offer at or above that cost.")
    value = (f"An offer of {coins(k)} would be accepted with chance {k} in 5, leaving an "
             f"expected profit of {(p.V - k) * k / 5:.1f} coins.")
  return (f"{n} thinks it through. {fact} {n} can resell the fruit for {coins(p.V)}. "
          f"{value} So {n} should offer {coins(k)}.")


def all_optimal(p: core.Prompt) -> bool:
  return len(core.oracle_bids(p)) == len(core.PRICES)


def choose_pairs(prompts) -> list[dict]:
  """(good k, bad k) per case, balancing direction and mean concluded price."""
  out, diff, above, below = [], 0.0, 0, 0
  for p in prompts:
    if all_optimal(p):
      continue
    best = core.oracle_bids(p)
    opts = []
    for g in best:
      if max(best) + 1 <= 5:
        opts.append((g, max(best) + 1, "above"))
      if min(best) - 1 >= 1:
        opts.append((g, min(best) - 1, "below"))
    def cost(o):
      g, b, d = o
      a2, b2 = above + (d == "above"), below + (d == "below")
      return abs(diff + b - g) + 0.5 * abs(a2 - b2)
    g, b, d = min(opts, key=cost)
    diff += b - g
    above += d == "above"; below += d == "below"
    out.append({"pid": p.pid, "good_offer": g, "bad_offer": b, "bad_direction": d,
                "good": paragraph(p, g), "bad": paragraph(p, b)})
  return out


def lower_pairs(prompts) -> list[dict]:
  """Offer-lower positive control: A concludes one coin below B."""
  out = []
  for p in prompts:
    if all_optimal(p):
      continue
    b = max(2, max(core.oracle_bids(p)))
    out.append({"pid": p.pid, "A_offer": b - 1, "B_offer": b,
                "A": paragraph(p, b - 1), "B": paragraph(p, b)})
  return out


def checks(pairs: list[dict], n_tokens) -> dict:
  """Token lengths within 10% per pair; about half the bad offers above, half below;
  mean concluded price of the good and bad sets within 0.25 coins."""
  ratios = [n_tokens(x["bad"]) / n_tokens(x["good"]) for x in pairs]
  above = sum(x["bad_direction"] == "above" for x in pairs)
  mg = sum(x["good_offer"] for x in pairs) / len(pairs)
  mb = sum(x["bad_offer"] for x in pairs) / len(pairs)
  return {"n_pairs": len(pairs),
          "length_ratio_min": min(ratios), "length_ratio_max": max(ratios),
          "lengths_within_10pct": all(0.9 <= r <= 1.1 for r in ratios),
          "bad_above": above, "bad_below": len(pairs) - above,
          "direction_balanced": abs(2 * above - len(pairs)) <= max(2, round(0.2 * len(pairs))),
          "mean_good_offer": mg, "mean_bad_offer": mb,
          "means_within_0.25": abs(mg - mb) <= 0.25}


def build_pairs():
  prompts = common.cases_in("build")
  return choose_pairs(prompts), lower_pairs(prompts)


if __name__ == "__main__":
  from transformers import AutoTokenizer
  from refimpl import runtime
  tok = AutoTokenizer.from_pretrained(runtime.resolve("9b")[0])
  n_tok = lambda t: len(tok.encode(t, add_special_tokens=False))
  pairs, lower = build_pairs()
  c = checks(pairs, n_tok)
  lr = [n_tok(x["A"]) / n_tok(x["B"]) for x in lower]
  c_lower = {"n_pairs": len(lower), "length_ratio_min": min(lr), "length_ratio_max": max(lr),
             "lengths_within_10pct": all(0.9 <= r <= 1.1 for r in lr),
             "all_A_one_below_B": all(x["A_offer"] == x["B_offer"] - 1 for x in lower)}
  json.dump({"template_pairs": pairs, "offer_lower_pairs": lower, "checks": c,
             "checks_offer_lower": c_lower},
            open(os.path.join(common.DEMO_DIR, "pairs_template.json"), "w"), indent=1)
  print("template pairs:", json.dumps(c, indent=1))
  print("offer-lower pairs:", json.dumps(c_lower, indent=1))
