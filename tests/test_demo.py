import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from refimpl import core, demo  # noqa: E402


def test_demo_loader_refuses_registered_variants():
  for v in (1, 12, 13, 14):
    with pytest.raises(ValueError):
      demo.demo_prompts([v])
    with pytest.raises(ValueError):
      demo.DemoPrompt(v, 5, "neutral", None)
  with pytest.raises(ValueError):
    demo.demo_prompts([15, 3])


def test_demo_cases_and_names():
  ps = demo.demo_prompts()
  assert len(ps) == 140 and {p.variant for p in ps} == {15, 16, 17, 18}
  assert len({p.cell for p in ps}) == 35
  used = set(core.FEMALE_NAMES) | set(core.MALE_NAMES)
  for p in ps:
    assert p.buyer not in used and p.seller not in used
    assert p.buyer.split()[0] != p.seller.split()[0]
  assert ps[0].pid.startswith("v15-")


def test_offer_direction():
  p = core.Prompt(1, 5, "information", 3)                  # best offer 3
  assert [demo.offer_direction(p, k) for k in (2, 3, 4)] == ["too_low", "best", "too_high"]
