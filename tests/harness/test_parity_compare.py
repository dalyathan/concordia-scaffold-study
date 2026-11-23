import copy, json
from tools import parity_check as pc
from harness import evaluate
from harness.solvers import cpu
from harness.task import get_task


def rec(tmp_path, solver=None):
  return json.loads(json.dumps(evaluate.evaluate(get_task("haggling"), solver or cpu.OracleSolver(), "tune", directory=str(tmp_path))))


def test_identical_records_pass(tmp_path):
  r = rec(tmp_path); ok, rep = pc.compare(r, copy.deepcopy(r)); assert ok and rep["max_abs_prob_diff"] == 0


def test_small_probability_drift_fails(tmp_path):
  r = rec(tmp_path, cpu.RandomSolver(seed=1)); o = copy.deepcopy(r)
  c = o["cases"][0]; c["probs"][0] += 0.01; c["probs"][1] -= 0.01
  ok, rep = pc.compare(r, o); assert not ok and rep["max_abs_prob_diff"] > pc.MAX_ABS_PROB


def test_missing_case_fails(tmp_path):
  r = rec(tmp_path); o = copy.deepcopy(r); r["cases"] = r["cases"][1:]
  assert not pc.compare(r, o)[0]
