"""Solver interface (as in Inspect): every condition is an interchangeable solver.

A solver turns (task, case, option order) into a probability for each answer letter. `describe()` is stored in the run record
so the exact condition (lesson text hash, adapter hash, steering vector hash and layer, ...) is on file."""
from __future__ import annotations

from typing import Protocol


class Solver(Protocol):
  name: str

  def describe(self) -> dict: ...                       # config + input hashes for the run record
  def letter_probs(self, task, case, order) -> dict: ...  # {"probs": {letter: p}, "mass": float|None, "prompt_sha256": str}


def registry():
  from harness.solvers import cpu, hf
  return {"constant": cpu.ConstantSolver, "uniform": cpu.UniformSolver, "oracle": cpu.OracleSolver, "random": cpu.RandomSolver, "baseline": cpu.BaselineSolver,
          "plain": hf.PlainSolver, "lesson": hf.LessonSolver, "notes": hf.NotesSolver, "steering": hf.SteeringSolver, "lora": hf.LoRASolver}
