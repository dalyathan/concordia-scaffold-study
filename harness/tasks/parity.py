"""Toy second task for CPU smoke tests: five numbers are shown as options; the right one equals `target` modulo `modulus`.
Exactly one option is right, so regret is 0 or 1. Cases come from a seeded generator; no model is needed to run it."""
from __future__ import annotations

import random
import string

from harness.protected.payoffs import parity as _payoffs

LETTERS = list(string.ascii_lowercase[:5])


def _build(seed=7):
  rng = random.Random(seed)
  out = []
  for split, n in (("train", 30), ("tune", 10), ("test", 10)):
    for i in range(n):
      m = rng.choice((3, 4, 5, 7)); t = rng.randrange(m)
      vals = [t + m * rng.randrange(0, 6)]
      while len(vals) < 5:
        v = rng.randrange(1, 60)
        if v % m != t and v not in vals:
          vals.append(v)
      rng.shuffle(vals)
      out.append({"cid": f"parity-{split}-{i:03d}", "split": split, "type": f"mod{m}", "modulus": m, "target": t, "options": vals})
  return out


class ParityTask:
  name = "parity"
  splits = ("train", "tune", "test")
  locked_splits = ("test",)

  def __init__(self):
    self._cases = _build()

  def cases(self, split):
    return [c for c in self._cases if c["split"] == split]

  def n_options(self, case):
    return 5

  def orders(self, case):
    return [tuple((s + i) % 5 for i in range(5)) for s in range(5)]

  def render(self, case, order):
    text = f"Which number leaves remainder {case['target']} when divided by {case['modulus']}?\n"
    l2o = {}
    for l, pos in zip(LETTERS, order):
      text += f"  ({l}) {case['options'][pos]}\n"
      l2o[l] = pos
    return text + "Answer: (", l2o

  def option_labels(self, case):
    return [str(v) for v in case["options"]]

  def payoffs(self, case):
    return _payoffs.payoffs(case)

  def reference(self, case):
    p = self.payoffs(case)
    return {"best_options": [i for i, x in enumerate(p) if x == max(p)], "best_payoff": max(p)}

  def case_type(self, case):
    return case["type"]

  def planted_cases(self):
    return [{"cid": "planted-par-0", "split": "planted", "type": "planted", "modulus": 3, "target": 1, "options": [3, 6, 9, 10, 12]},
            {"cid": "planted-par-1", "split": "planted", "type": "planted", "modulus": 5, "target": 0, "options": [1, 2, 3, 4, 25]}]

  def planted_expected(self):
    return {"planted-par-0": [3], "planted-par-1": [4]}


TASK = ParityTask
