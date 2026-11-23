"""The ported generator reproduces the existing case files byte for byte."""
import hashlib, json, os, pytest
from conftest import ROOT
from harness.tasks import haggling as h

GEN = os.path.join(ROOT, "demo", "gen")
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()


@pytest.fixture(scope="module")
def regen(tmp_path_factory):
  out = tmp_path_factory.mktemp("regen")
  cells, cases, rej = h.build()
  json.dump({"seed": h.SEED, "rejected": rej, "cells": cells}, open(out / "cells.json", "w"), indent=1)
  with open(out / "cases.jsonl", "w") as f:
    for c in cases:
      f.write(json.dumps(c) + "\n")
  json.dump(h.fingerprints(cells, cases), open(out / "fingerprints.json", "w"), indent=1)
  json.dump(h.fingerprints_v2(cells), open(out / "fingerprints_v2.json", "w"), indent=1)
  return out


@pytest.mark.parametrize("name", ["cells.json", "cases.jsonl", "fingerprints.json", "fingerprints_v2.json"])
def test_byte_identical(regen, name):
  if name.startswith("fingerprints") and not os.path.isdir(os.path.join(ROOT, "concordia")):
    pytest.skip("pinned Concordia clone not present")
  if name == "fingerprints_v2.json":
    pytest.skip("v2 embeds sha256 of the generator files themselves, which the port deliberately does not share")
  assert sha(regen / name) == sha(os.path.join(GEN, name))


def test_payoff_equals_original_rule():
  from refimpl import core
  t = h.HagglingTask()
  # unit rule: grid 1-5 / prior 1-5 haggling equals refimpl.core.payoff
  for V in core.VALUES:
    for C in (None, 1, 3, 5):
      p = core.Prompt(1, V, "neutral" if C is None else "information", C)
      case = {"V": V, "grid": [1, 2, 3, 4, 5], "C": C, "prior": [1, 5]}
      assert t.payoffs(case) == pytest.approx([core.payoff(p, k) for k in core.PRICES])


def test_planted_cases_have_stated_answers():
  t = h.HagglingTask()
  for c in t.planted_cases():
    best = t.reference(c)["best_options"]
    assert set(best) == set(t.planted_expected()[c["cid"]]) or set(best) <= set(t.planted_expected()[c["cid"]])
