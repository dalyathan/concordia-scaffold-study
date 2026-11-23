"""Task interface. A task supplies cases, prompt rendering, payoffs (from harness/protected/payoffs), a reference solver,
case types for per-type reporting, and planted known-answer cases. Shared code never names a task."""
from __future__ import annotations

import importlib
from typing import Protocol, Sequence

TASKS = {"haggling": "harness.tasks.haggling", "parity": "harness.tasks.parity"}


class Task(Protocol):
  name: str
  splits: Sequence[str]
  locked_splits: Sequence[str]      # evaluate() refuses these without a lock token (G3 + owner go)

  def cases(self, split: str) -> list[dict]: ...            # each case has "cid", "split", "type"
  def n_options(self, case: dict) -> int: ...
  def orders(self, case: dict) -> Sequence[Sequence[int]]: ...    # option orders the readout averages over
  def render(self, case: dict, order: Sequence[int]) -> tuple[str, dict]: ...   # (prompt, {letter: option index})
  def option_labels(self, case: dict) -> list[str]: ...
  def payoffs(self, case: dict) -> list[float]: ...         # delegates to harness.protected.payoffs.<task>
  def reference(self, case: dict) -> dict: ...              # {"best_options": [...], "best_payoff": x}
  def case_type(self, case: dict) -> str: ...
  def planted_cases(self) -> list[dict]: ...
  def planted_expected(self) -> dict: ...                   # cid -> list of acceptable best option indices


def get_task(name: str):
  if name not in TASKS:
    raise KeyError(f"unknown task {name!r}; registered: {sorted(TASKS)}")
  return importlib.import_module(TASKS[name]).TASK()
