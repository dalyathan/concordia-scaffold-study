"""Demo cases outside the registered experiment.

Name variants 1-14 belong to the registered experiment (core.FEMALE_NAMES /
MALE_NAMES: variants 1-12 confirmatory, 13-14 pilot) and are refused here. Demo
variants 15-18 use names from v1.8.9's fruitville_haggling.py name lists that
variants 1-14 do not use, in file order, with one skip: file position 18 would pair
buyer "Rowan Cranberry" with seller "Rowan Cranberryfield" (the same first name for
both speakers), so variant 18 takes file position 19 instead. Openings follow the
same rule as the experiment: VISUAL_SCENE_OPENINGS[(variant - 1) mod 5].
"""
from __future__ import annotations

import dataclasses
from typing import Iterable

from . import core

# fruitville_haggling.py file positions 15, 16, 17 and 19 (1-based).
DEMO_NAMES = {
    15: ("Opal Apricot", "Orion Apricotwood"),
    16: ("Sasha Grapevine", "Peregrine Grapehill"),
    17: ("Quinn Cherryblossom", "Quentin Cherrybrook"),
    18: ("Sage Honeycomb", "Silas Honeybrook"),
}
DEMO_VARIANTS = tuple(sorted(DEMO_NAMES))
REGISTERED_VARIANTS = tuple(range(1, 15))


@dataclasses.dataclass(frozen=True)
class DemoPrompt(core.Prompt):
  """A core.Prompt whose names come from DEMO_NAMES; refuses variants 1-14."""

  def __post_init__(self):
    if self.variant in REGISTERED_VARIANTS:
      raise ValueError(f"variant {self.variant} belongs to the registered experiment "
                       "(1-14); demo cases use variants 15-18")
    if self.variant not in DEMO_NAMES:
      raise ValueError(f"no demo names for variant {self.variant}")

  @property
  def buyer(self) -> str:
    return DEMO_NAMES[self.variant][0]

  @property
  def seller(self) -> str:
    return DEMO_NAMES[self.variant][1]


def demo_prompts(variants: Iterable[int] = DEMO_VARIANTS,
                 values: Iterable[int] = core.VALUES) -> list[DemoPrompt]:
  """35 cells per variant (V = 2-6; neutral, pressure, and stated cost C = 1-5).
  Raises ValueError for any registered variant (1-14)."""
  variants = list(variants)
  bad = [v for v in variants if v in REGISTERED_VARIANTS]
  if bad:
    raise ValueError(f"variants {bad} belong to the registered experiment (1-14)")
  return [DemoPrompt(p.variant, p.V, p.line, p.C) for p in core.prompt_set(variants, values)]


def offer_direction(p: core.Prompt, k: int) -> str:
  """'best', 'too_high' (above every best offer) or 'too_low' (below every best offer)."""
  best = core.oracle_bids(p)
  if k in best:
    return "best"
  return "too_high" if k > max(best) else "too_low"
