"""Run one solver on one split of one task and write a run record. Scores come only from harness.protected.scorer.

Planted known-answer cases are added to every evaluation and reported separately (never in the headline mean)."""
from __future__ import annotations

import hashlib
import json
import os
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


MIN_LETTER_MASS = 0.5        # records below this mean first-token letter mass are flagged (a wrong-token readout renormalises to plausible numbers)
PLANTED_MIN_MASS = 0.9       # a planted case passes only if the model puts at least this much probability on the acceptable options


def _prior_look(directory, task_name, split, model, solver_cfg_sha):
  hits = []
  for dp, _, fs in os.walk(directory):
    for f in fs:
      if f.endswith(".json"):
        try:
          r = json.load(open(os.path.join(dp, f)))
        except Exception:
          continue
        if (r.get("task"), r.get("split"), r.get("model")) == (task_name, split, model) and r.get("solver_config_sha256") == solver_cfg_sha:
          hits.append(os.path.join(dp, f))
  return hits


def evaluate(task, solver, split: str, seed: int = 0, model_spec=None, config: dict | None = None, lock_token: str | None = None,
             write: bool = True, directory: str = records.RUNS, gpu_seconds: float | None = None, planted: bool = True,
             min_letter_mass: float = MIN_LETTER_MASS) -> dict:
  _check_protected()
  if split not in task.splits:
    raise EvaluationRefused(f"{task.name} has no split {split!r}; known: {list(task.splits)}")
  solver_cfg_sha = hashlib.sha256(json.dumps(solver.describe(), sort_keys=True, default=str).encode()).hexdigest()
  locked = split in task.locked_splits
  if locked:
    if not (lock_token or "").startswith(LOCK_TOKEN_PREFIX):
      raise EvaluationRefused(f"{task.name}/{split} is a locked test split: needs G3 and an explicit owner go "
                              f"(pass lock_token='{LOCK_TOKEN_PREFIX}<date>')")
    if not write:
      raise EvaluationRefused("a look at a locked split must be written to a record (write=True)")
    ref = os.environ.get("HARNESS_PIN_REF")
    if not ref:
      raise EvaluationRefused("a look at a locked split needs HARNESS_PIN_REF: the owner's git tag that pins the protected files "
                              "(see DECISIONS.md, 'Owner pin')")
    try:
      drift = lock_protected.pin_mismatches(ref)
    except RuntimeError as e:
      raise EvaluationRefused(f"pin {ref} unreadable: {e}")
    if drift:
      raise EvaluationRefused(f"protected files differ from the owner's pin {ref}: {[f for f, _ in drift]}")
    prior = _prior_look(directory, task.name, split, model_spec.name if model_spec else None, solver_cfg_sha)
    if prior:
      raise EvaluationRefused(f"locked split {split} was already scored with this exact solver config: {prior[0]} (each look is once)")
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
      acc = expected[case["cid"]]
      row["planted_mass_on_expected"] = sum(avg[i] for i in acc)
      row["planted_ok"] = row["score"]["top_option"] in acc and row["planted_mass_on_expected"] >= PLANTED_MIN_MASS
    rows.append(row)
  real = [r for r in rows if not r["planted"]]
  pl = [r for r in rows if r["planted"]]
  mean = lambda xs: sum(xs) / len(xs) if xs else None
  by_type = {}
  for r in real:
    by_type.setdefault(r["type"], []).append(r["score"]["soft_regret"])
  all_masses = [m for r in real for m in (r["letter_mass"] or []) if m is not None]
  mean_mass = sum(all_masses) / len(all_masses) if all_masses else None
  wall = time.time() - t0
  gpu_s = wall if gpu_seconds is None and model_spec is not None else (gpu_seconds or 0.0)
  case_blob = json.dumps([[c["cid"]] for c in cases]).encode()
  rec = {
      "schema": records.SCHEMA, "run_id": records.new_run_id(task.name, model_spec.name if model_spec else None, solver.name, split, seed),
      "model": model_spec.name if model_spec else None, "model_config": __import__("dataclasses").asdict(model_spec) if model_spec else None,
      "task": task.name, "split": split, "solver": solver.name, "solver_config": solver.describe(), "seed": seed, "config": config or {},
      "solver_config_sha256": solver_cfg_sha, "lock_token": lock_token if locked else None,
      "letter_mass": {"mean": mean_mass, "floor": min_letter_mass, "ok": (mean_mass is None or mean_mass >= min_letter_mass)},
      "git": records.git_info(), "environment": records.environment(),
      "input_hashes": {
          "case_ids_sha256": hashlib.sha256(case_blob).hexdigest(),
          "cases_sha256": hashlib.sha256(json.dumps(cases, sort_keys=True).encode()).hexdigest(),
          "protected_scorer": {f: records.sha256_file(f"{records.ROOT}/{f}") for f in lock_protected.hashes()}},
      "timing": {"wall_seconds": wall, **records.cost(gpu_s)},
      "summary": {"n_cases": len(real), "soft_regret_mean": mean([r["score"]["soft_regret"] for r in real]),
                  "hard_regret_mean": mean([r["score"]["hard_regret"] for r in real]),
                  "by_type": {k: {"n": len(v), "soft_regret_mean": mean(v)} for k, v in sorted(by_type.items())}},
      "planted": {"min_mass_required": PLANTED_MIN_MASS, "n": len(pl), "n_ok": sum(r["planted_ok"] for r in pl), "all_ok": all(r["planted_ok"] for r in pl),
                  "failed": [r["cid"] for r in pl if not r["planted_ok"]]},
      "cases": rows}
  if write:
    rec["_written_to"] = records.write({k: v for k, v in rec.items() if k != "_written_to"}, directory)
  return rec
