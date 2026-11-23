"""CPU-only solvers: baselines and smoke tests. No model, no torch."""
from __future__ import annotations

import hashlib
import random


def _sha(s): return hashlib.sha256(s.encode()).hexdigest()


class _Base:
  name = "base"
  def __init__(self, **kw): self.kw = kw
  def describe(self): return {"solver": self.name, **self.kw}


class UniformSolver(_Base):
  name = "uniform"
  def letter_probs(self, task, case, order):
    text, l2o = task.render(case, order)
    return {"probs": {l: 1 / len(l2o) for l in l2o}, "mass": 1.0, "prompt_sha256": _sha(text)}


class ConstantSolver(_Base):
  """Always put all mass on option index `option` (e.g. 'always offer 2' is option 1 of the grid 1..5)."""
  name = "constant"
  def __init__(self, option=0, **kw): super().__init__(option=option, **kw); self.option = option
  def letter_probs(self, task, case, order):
    text, l2o = task.render(case, order)
    return {"probs": {l: float(o == self.option) for l, o in l2o.items()}, "mass": 1.0, "prompt_sha256": _sha(text)}


class OracleSolver(_Base):
  """Uses the task's reference solver (a ceiling, and a check that the pipeline can score zero)."""
  name = "oracle"
  def letter_probs(self, task, case, order):
    text, l2o = task.render(case, order)
    best = task.reference(case)["best_options"]
    return {"probs": {l: (1 / len(best) if o in best else 0.0) for l, o in l2o.items()}, "mass": 1.0, "prompt_sha256": _sha(text)}


class RandomSolver(_Base):
  name = "random"
  def __init__(self, seed=0, **kw): super().__init__(seed=seed, **kw); self.seed = seed
  def letter_probs(self, task, case, order):
    text, l2o = task.render(case, order)
    rng = random.Random(f"{self.seed}|{case['cid']}|{order}")
    w = {l: rng.random() for l in l2o}; z = sum(w.values())
    return {"probs": {l: x / z for l, x in w.items()}, "mass": 1.0, "prompt_sha256": _sha(text)}
