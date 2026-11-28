"""test2 in the harness (QWEN_TEST_PLAN.md / LLAMA_TEST_PLAN.md, code item 1 and 2). CPU only; no model, no score of a model.

Rendering a test2 prompt as text is not a look: these tests compare prompt hashes with the generator's own renderer and the
stored labels with the protected payoff rule, and check that evaluate() refuses the test2 splits without the lock."""
import hashlib, json, os, shutil, sys

import pytest

from conftest import ROOT
from harness import evaluate
from harness.solvers import cpu
from harness.tasks import haggling as h

sys.path.insert(0, os.path.join(ROOT, "demo"))
import common  # noqa: E402,F401
import gen_cases as g  # noqa: E402
import gen_test2 as t2  # noqa: E402

t2.install()
SPLITS = ("test2_same", "test2_newkey")


def sha(s):
  return hashlib.sha256(s.encode()).hexdigest()


def test_test2_splits_are_locked():
  t = h.HagglingTask()
  for s in SPLITS:
    assert s in t.splits and s in t.locked_splits


def test_wording_and_grid_match_the_generator():
  assert h.TEST2_WORDING == t2.NEW_WORDING
  assert h.TEST2_WORDING_INDEX == 3 == len(g.SELLER_LINES["neutral"]) - 1
  assert tuple(t2.NEW_GRID[1]) == tuple(g.GRIDS[t2.NEW_GRID[0]])


def test_cases_load_with_fingerprint_check_and_counts():
  t = h.HagglingTask()
  for s in SPLITS:
    cs = t.cases(s)
    assert len(cs) == 240 and {c["split"] for c in cs} == {s}
    assert sorted({c["type"] for c in cs}) == ["at_or_above", "below", "no_cost"]


def test_changed_cases_file_is_refused(tmp_path, monkeypatch):
  bad = tmp_path / "test2_cases.jsonl"
  shutil.copy(h.HagglingTask.TEST2_CASES, bad)
  with open(bad, "a") as f:
    f.write("\n")
  monkeypatch.setattr(h.HagglingTask, "TEST2_CASES", str(bad))
  with pytest.raises(RuntimeError, match="fingerprint"):
    h.HagglingTask().cases("test2_same")


def test_prompts_equal_the_generator_render():
  """Every test2 case and order renders to the same text and letter map as demo/gen_cases.render after gen_test2.install()."""
  t = h.HagglingTask()
  n = 0
  for s in SPLITS:
    for c in t.cases(s):
      for order in t.orders(c):
        a_text, a_map = h.render(c, order)
        b_text, b_map = g.render(c, order)
        assert sha(a_text) == sha(b_text), c["cid"]
        assert a_map == b_map
        n += 1
  assert n == 2 * 240 * 5


def test_payoffs_agree_with_stored_labels():
  """The protected payoff rule gives the best offers stored in test2_cells.json when the sets were built."""
  t = h.HagglingTask()
  cells = {c["cell"]: c for c in json.load(open(os.path.join(g.OUT, "test2_cells.json")))["cells"]}
  for s in SPLITS:
    for c in t.cases(s):
      ref = t.reference(c)
      cell = cells[c["cell"]]
      assert sorted(ref["best_options"]) == sorted(cell["best_positions"]), c["cid"]
      assert ref["best_payoff"] == pytest.approx(cell["best_payoff"])


@pytest.mark.parametrize("split", SPLITS)
def test_evaluate_refuses_test2_without_lock_token(tmp_path, split, monkeypatch):
  monkeypatch.setenv("HARNESS_PIN_REF", "test-pin")
  monkeypatch.setattr(evaluate.lock_protected, "pin_mismatches", lambda ref: [])
  with pytest.raises(evaluate.EvaluationRefused, match="locked"):
    evaluate.evaluate(h.HagglingTask(), cpu.OracleSolver(), split, directory=str(tmp_path))


def test_evaluate_refuses_test2_without_owner_pin(tmp_path, monkeypatch):
  monkeypatch.delenv("HARNESS_PIN_REF", raising=False)
  with pytest.raises(evaluate.EvaluationRefused, match="HARNESS_PIN_REF"):
    evaluate.evaluate(h.HagglingTask(), cpu.OracleSolver(), "test2_same", directory=str(tmp_path), lock_token="G3-OWNER-GO:test-only")


# ---------------------------------------------------------------- one look per arm (code item 2), on the toy parity task
class _Named(cpu.OracleSolver):
  """An oracle whose name and config can be set, to stand in for a LoRA arm whose adapter or config changed."""
  def __init__(self, name, **kw):
    super().__init__(**kw)
    self.name = name


@pytest.fixture
def pinned(monkeypatch):
  monkeypatch.setenv("HARNESS_PIN_REF", "test-pin")
  monkeypatch.setattr(evaluate.lock_protected, "pin_mismatches", lambda ref: [])


def _parity(solver, tmp_path, seed=0):
  from harness.task import get_task
  return evaluate.evaluate(get_task("parity"), solver, "test", seed=seed, directory=str(tmp_path), lock_token="G3-OWNER-GO:test-only")


def test_second_look_same_arm_new_config_is_refused(tmp_path, pinned):
  _parity(_Named("lora:arm_x", adapter="v1"), tmp_path)
  with pytest.raises(evaluate.EvaluationRefused, match="already scored"):
    _parity(_Named("lora:arm_x", adapter="v2-retrained"), tmp_path)


def test_other_seed_of_same_arm_is_its_own_look(tmp_path, pinned):
  _parity(_Named("lora:arm_x", adapter="s0"), tmp_path, seed=0)
  _parity(_Named("lora:arm_x", adapter="s1"), tmp_path, seed=1)
  with pytest.raises(evaluate.EvaluationRefused):
    _parity(_Named("lora:arm_x", adapter="s1-again"), tmp_path, seed=1)


def test_seed_must_match_adapter_training_seed(tmp_path, pinned):
  with pytest.raises(evaluate.EvaluationRefused, match="training seed"):
    _parity(_Named("lora:arm_y", training={"seed": 2}), tmp_path, seed=0)


def test_writing_elsewhere_does_not_hide_an_earlier_look(tmp_path, pinned, monkeypatch):
  a, b = tmp_path / "a", tmp_path / "b"
  a.mkdir(); b.mkdir()
  monkeypatch.setattr(evaluate.records, "RUNS", str(a))       # the default runs folder
  _parity(_Named("lora:arm_z"), a)
  with pytest.raises(evaluate.EvaluationRefused):
    _parity(_Named("lora:arm_z", note="other folder"), b)
