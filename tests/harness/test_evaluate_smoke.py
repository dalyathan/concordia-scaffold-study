"""CPU smoke test on the toy second task, and on haggling with model-free solvers."""
import json, pytest
from harness import evaluate
from harness.solvers import cpu
from harness.task import get_task


def run(task, solver, split, tmp_path, **kw):
  return evaluate.evaluate(get_task(task), solver, split, directory=str(tmp_path), **kw)


def test_parity_oracle_is_perfect(tmp_path):
  rec = run("parity", cpu.OracleSolver(), "tune", tmp_path)
  assert rec["summary"]["soft_regret_mean"] == 0 and rec["planted"]["all_ok"]


def test_parity_uniform_is_chance(tmp_path):
  rec = run("parity", cpu.UniformSolver(), "tune", tmp_path)
  assert rec["summary"]["soft_regret_mean"] == pytest.approx(0.8)


def test_record_has_required_fields(tmp_path):
  rec = run("parity", cpu.RandomSolver(seed=3), "tune", tmp_path, seed=3, config={"x": 1})
  for k in ("model", "task", "solver", "seed", "config", "git", "input_hashes", "environment", "timing", "cases", "planted", "solver_config"):
    assert k in rec
  assert rec["git"]["commit"] and "approx_usd" in rec["timing"] and "gpu_seconds" in rec["timing"]
  c = rec["cases"][0]
  for k in ("inputs", "probs", "payoffs", "score", "prompt_sha256", "letter_mass"):
    assert k in c


def test_locked_split_refused(tmp_path):
  with pytest.raises(evaluate.EvaluationRefused):
    run("parity", cpu.OracleSolver(), "test", tmp_path)
  rec = run("parity", cpu.OracleSolver(), "test", tmp_path, lock_token="G3-OWNER-GO:test-only")
  assert rec["summary"]["n_cases"] == 10


def test_haggling_baselines_ordering(tmp_path):
  o = run("haggling", cpu.OracleSolver(), "tune", tmp_path)
  c = run("haggling", cpu.ConstantSolver(option=1), "tune", tmp_path)       # 'always offer 2' on grids that contain 2 at index 1
  u = run("haggling", cpu.UniformSolver(), "tune", tmp_path)
  assert o["summary"]["soft_regret_mean"] == 0
  assert 0 < c["summary"]["soft_regret_mean"] < u["summary"]["soft_regret_mean"] + 1
  assert set(o["summary"]["by_type"]) == {"below", "at_or_above", "no_cost"}


def test_planted_case_failure_is_flagged(tmp_path):
  """A solver that is always wrong on the planted cases is caught and reported separately, not in the headline mean."""
  rec = run("haggling", cpu.ConstantSolver(option=4), "tune", tmp_path)
  assert not rec["planted"]["all_ok"] and rec["planted"]["failed"]
  assert all(not r["planted"] for r in rec["cases"] if r["split"] == "tune")


def test_independent_recompute_agrees(tmp_path):
  from tools import recompute
  rec = run("haggling", cpu.RandomSolver(seed=1), "tune", tmp_path)
  out, problems = recompute.recompute(json.loads(json.dumps(rec)))
  assert problems == [] and out["soft_regret_mean"] == pytest.approx(rec["summary"]["soft_regret_mean"])


def test_recompute_catches_edited_number(tmp_path):
  from tools import recompute
  rec = json.loads(json.dumps(run("haggling", cpu.RandomSolver(seed=1), "tune", tmp_path)))
  rec["summary"]["soft_regret_mean"] -= 0.05          # someone 'improves' the headline
  assert recompute.recompute(rec)[1]
  rec2 = json.loads(json.dumps(run("haggling", cpu.RandomSolver(seed=1), "tune", tmp_path)))
  rec2["cases"][0]["score"]["soft_regret"] = 0.0      # or a single case score
  assert recompute.recompute(rec2)[1]


def test_recompute_does_not_import_project_code():
  import ast, tools.recompute as r
  mods = set()
  for n in ast.walk(ast.parse(open(r.__file__).read())):
    if isinstance(n, ast.Import):
      mods |= {a.name.split(".")[0] for a in n.names}
    elif isinstance(n, ast.ImportFrom):
      mods.add((n.module or "").split(".")[0])
  assert mods <= {"json", "math", "os", "sys"}, mods
