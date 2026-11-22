"""Step 4: the text rows inserted as the Notes block, and the method check.

Fixed rows are frozen in demo/text_rows.json (written by demo/step4_run.py);
per-case rows (template reasoning, answer-only) are generated from the case."""
from __future__ import annotations

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402
from refimpl import core  # noqa: E402

METHOD = (
    "How to choose the offer. First check whether the seller has said what the fruit cost "
    "them at the farm. If a cost is stated and it is below the resale value, offer exactly "
    "that cost: the seller accepts it, any higher offer only gives away profit, and any "
    "lower offer is refused. If the stated cost is at or above the resale value, no "
    "accepted offer can make a profit, so offer the lowest possible price. If no cost is "
    "stated, every farm cost is equally likely; for each possible offer, multiply the "
    "chance that it is accepted (the share of possible costs at or below it) by the profit "
    "it would leave (resale value minus offer), and choose the offer with the largest "
    "result.")
FIXED = {
    "wrong_rule": "Offer half the stated cost.",
    "disposition": "Only your own profit matters.",
    "acceptance_rule": "The seller accepts any offer at or above their cost.",
}
ROWS = ("plain", "method", "neutral", "wrong_rule", "disposition", "acceptance_rule",
        "template", "answer_only")
PATH = os.path.join(common.DEMO_DIR, "text_rows.json")


def method_offer(p: core.Prompt) -> int:
  """The METHOD paragraph's rule, executed literally."""
  if p.C is not None:
    return p.C if p.C < p.V else min(core.PRICES)
  return max(core.PRICES, key=lambda k: (k / len(core.PRICES) * (p.V - k), -k))


def check_method(values=tuple(range(2, 9))) -> dict:
  """The method's offer must be a best offer (core.oracle_bids) in every cell of all
  three case types, including the V = 7, 8 extension values."""
  assert not re.search(r"\d", METHOD), "method text must contain no numbers"
  bad = [p.pid for p in core.prompt_set([1], values) if method_offer(p) not in core.oracle_bids(p)]
  return {"cells_checked": len(core.prompt_set([1], values)), "wrong": bad, "ok": not bad}


def row_text(name: str, p: core.Prompt) -> str | None:
  if name == "plain":
    return None
  if name == "template":
    import pairs_template
    return pairs_template.paragraph(p, min(core.oracle_bids(p)))
  if name == "answer_only":
    return core.answer_only(p.buyer, min(core.oracle_bids(p)))
  if name == "method":
    return METHOD
  if name in FIXED:
    return FIXED[name]
  if name == "neutral":
    return json.load(open(PATH))["rows"]["neutral"]["text"]
  raise KeyError(f"unknown text row '{name}' (rows: {', '.join(ROWS)})")
