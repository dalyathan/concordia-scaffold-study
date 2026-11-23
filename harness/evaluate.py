"""Run one solver on one split of one task and write a run record. Scores come only from harness.protected.scorer.

Planted known-answer cases are added to every evaluation and reported separately (never in the headline mean)."""
from __future__ import annotations

import hashlib
import json
import time

from harness import records
from harness.protected import scorer
from tools import lock_protected

LOCK_TOKEN_PREFIX = "G3-OWNER-GO:"


class EvaluationRefused(RuntimeError):
  pass


def _check_protected():
  bad = lock_protected.unexplained()
  if bad:
    raise EvaluationRefused(f"protected scorer files changed without a DECISIONS.md entry: {bad}")


def evaluate(task, solver, split: str, seed: int = 0, model_spec=None, config: dict | None = None, lock_token: str | None = None,
             write: bool = True, directory: str = records.RUNS, gpu_seconds: float | None = None, planted: bool = True) -> dict:
  _check_protected()
  if split in task.locked_splits and not (lock_token or "").startswith(LOCK_TOKEN_PREFIX):
    raise EvaluationRefused(f"{task.name}/{split} is a locked test split: needs G3 and an explicit owner go "
                            f"(pass lock_token='{LOCK_TOKEN_PREFIX}<date>')")
  t0 = time.time()
  cases = list(task.cases(split))
  expected = task.planted_expected() if planted else {}
  work = [(c, False) for c in cases] + ([(c, True) for c in task.planted_cases()] if planted else [])
  rows = []
  for case, is_planted in work:
    pay = task.payoffs(case)
    n = task.n_options(case)
    per_order, avg, masses, prompt_hashes = [], [0.0] * n, [], []
    orders = list(task.orders(case))
    for order in orders:
      out = solver.letter_probs(task, case, order)
      _, l2o = task.render(case, order)
      p = [0.0] * n
      for l, idx in l2o.items():
        p[idx] += out["probs"][l]
      per_order.append(p)
      masses.append(out.get("mass"))
      prompt_hashes.append(out.get("prompt_sha256"))
      avg = [a + x / len(orders) for a, x in zip(avg, p)]
    row = {"cid": case["cid"], "inputs": case, "type": task.case_type(case), "planted": is_planted, "split": case["split"],
           "payoffs": pay, "probs": avg, "per_order_probs": per_order, "letter_mass": masses, "prompt_sha256": prompt_hashes,
           "score": scorer.score_case(pay, avg), "per_order_soft_regret": [scorer.soft_regret(pay, p) for p in per_order]}
    if is_planted:
      row["planted_ok"] = row["score"]["top_option"] in expected[case["cid"]]
    rows.append(row)
  real = [r for r in rows if not r["planted"]]
  pl = [r for r in rows if r["planted"]]
  mean = lambda xs: sum(xs) / len(xs) if xs else None
  by_type = {}
  for r in real:
    by_type.setdefault(r["type"], []).append(r["score"]["soft_regret"])
  wall = time.time() - t0
  gpu_s = wall if gpu_seconds is None and model_spec is not None else (gpu_seconds or 0.0)
  case_blob = json.dumps([[c["cid"]] for c in cases]).encode()
  rec = {
      "schema": records.SCHEMA, "run_id": records.new_run_id(task.name, model_spec.name if model_spec else None, solver.name, split, seed),
      "model": model_spec.name if model_spec else None, "model_config": __import__("dataclasses").asdict(model_spec) if model_spec else None,
      "task": task.name, "split": split, "solver": solver.name, "solver_config": solver.describe(), "seed": seed, "config": config or {},
      "git": records.git_info(), "environment": records.environment(),
      "input_hashes": {
          "case_ids_sha256": hashlib.sha256(case_blob).hexdigest(),
          "cases_sha256": hashlib.sha256(json.dumps(cases, sort_keys=True).encode()).hexdigest(),
          "protected_scorer": {f: records.sha256_file(f"{records.ROOT}/{f}") for f in lock_protected.hashes()}},
      "timing": {"wall_seconds": wall, **records.cost(gpu_s)},
      "summary": {"n_cases": len(real), "soft_regret_mean": mean([r["score"]["soft_regret"] for r in real]),
                  "hard_regret_mean": mean([r["score"]["hard_regret"] for r in real]),
                  "by_type": {k: {"n": len(v), "soft_regret_mean": mean(v)} for k, v in sorted(by_type.items())}},
      "planted": {"n": len(pl), "n_ok": sum(r["planted_ok"] for r in pl), "all_ok": all(r["planted_ok"] for r in pl),
                  "failed": [r["cid"] for r in pl if not r["planted_ok"]]},
      "cases": rows}
  if write:
    rec["_written_to"] = records.write({k: v for k, v in rec.items() if k != "_written_to"}, directory)
  return rec
