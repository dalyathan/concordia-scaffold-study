"""Shared helpers for the demo tools (demo cases are variants 15-18 only; see
refimpl/demo.py, which refuses the registered variants 1-14)."""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "concordia")):
  if p not in sys.path:
    sys.path.insert(0, p)

from refimpl import core, demo  # noqa: E402

DEMO_DIR = os.path.join(ROOT, "demo")
CASES = os.path.join(ROOT, "demo_out", "cases.jsonl")
SPLITS = os.path.join(DEMO_DIR, "splits.json")
BUILD_VARIANTS, TUNING_VARIANTS = (15, 16), (17, 18)


def case_split(p: core.Prompt) -> str:
  """Development cells (core.steering_cell_split == 'dev'): variants 15-16 'build',
  17-18 'tuning'. Test cells: all four variants 'test'."""
  if core.steering_cell_split(p.cell) == "test":
    return "test"
  return "build" if p.variant in BUILD_VARIANTS else "tuning"


def case_type(p_or_rec) -> str:
  C = p_or_rec.C if isinstance(p_or_rec, core.Prompt) else p_or_rec["C"]
  V = p_or_rec.V if isinstance(p_or_rec, core.Prompt) else p_or_rec["V"]
  if C is None:
    return "no cost"
  return "cost below resale" if C < V else "cost at or above resale"


def prompts_by_id() -> dict[str, demo.DemoPrompt]:
  return {p.pid: p for p in demo.demo_prompts()}


def load_cases(path: str = CASES) -> list[dict]:
  return [json.loads(l) for l in open(path)]


def load_splits() -> dict:
  return json.load(open(SPLITS))


def cases_in(split: str) -> list[demo.DemoPrompt]:
  s = load_splits()["case_split"]
  return [p for p in demo.demo_prompts() if s[p.pid] == split]


def cell_id(p: core.Prompt) -> str:
  return str(p.cell)
