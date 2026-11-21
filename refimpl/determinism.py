"""Patches that make Phases 2-3 deterministic (Protocol section 4, "Determinism")."""
from __future__ import annotations

import concurrent.futures
import contextlib
import os

import numpy as np
import torch

from . import core
from .local_gemma2 import CONTEXT


class _SequentialExecutor(concurrent.futures.Executor):
  """Runs every submitted task immediately, in submission order, on this thread."""

  def __init__(self, *args, **kwargs):
    pass

  def submit(self, fn, /, *args, **kwargs):
    fut = concurrent.futures.Future()
    try:
      fut.set_result(fn(*args, **kwargs))
    except BaseException as e:  # noqa: BLE001 - propagate through the future
      fut.set_exception(e)
    return fut

  def map(self, fn, *iterables, timeout=None, chunksize=1):
    return [fn(*a) for a in zip(*iterables)]

  def shutdown(self, wait=True, *, cancel_futures=False):
    pass


_ORIGINAL_DEFAULT_RNG = np.random.default_rng
_RNG_COUNTER = {"n": 0}


def _seeded_default_rng(seed=None):
  """default_rng(): unseeded calls get a seed from the current call context.

  The counter resets at each agent decision (reset_decision_counter), so the k-th
  unseeded generator within a decision always gets the same seed.
  """
  if seed is not None:
    return _ORIGINAL_DEFAULT_RNG(seed)
  ctx = CONTEXT.get()
  _RNG_COUNTER["n"] += 1
  s = core.call_seed(f"default_rng#{_RNG_COUNTER['n']}", ctx.agent, ctx.pid, ctx.draw)
  return _ORIGINAL_DEFAULT_RNG(np.random.PCG64(s))


def reset_decision_counter():
  _RNG_COUNTER["n"] = 0


@contextlib.contextmanager
def deterministic_execution():
  """Apply all Phase 2-3 patches for the duration of the block."""
  os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
  torch.use_deterministic_algorithms(True)
  saved_pool = concurrent.futures.ThreadPoolExecutor
  saved_rng = np.random.default_rng
  concurrent.futures.ThreadPoolExecutor = _SequentialExecutor
  np.random.default_rng = _seeded_default_rng
  # concordia.utils.concurrency (run_tasks, map_parallel, ...) creates its pools via
  # concurrent.futures.ThreadPoolExecutor at call time, so this one patch covers it.
  try:
    yield
  finally:
    concurrent.futures.ThreadPoolExecutor = saved_pool
    np.random.default_rng = saved_rng
