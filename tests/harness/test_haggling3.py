"""harness/tasks/haggling3.py: the targeted experiment's splits. CPU only; no model; rendering text is not a look."""
import hashlib, os, shutil, sys

import pytest

from conftest import ROOT
from harness import evaluate
from harness.solvers import cpu
from harness.tasks import haggling3 as h3

sys.path.insert(0, os.path.join(ROOT, "demo"))
import common  # noqa: E402,F401
import gen_cases as g  # noqa: E402
import gen_test2 as t2  # noqa: E402

t2.install()
T = h3.Haggling3Task()
NEW = ("test3", "pool3", "probe3", "select3")


def test_splits_and_lock():
  assert set(NEW) <= set(T.splits) and "test3" in T.locked_splits
  assert not {"pool3", "probe3", "select3"} & set(T.locked_splits)
  assert set(h3.HagglingTask.locked_splits) <= set(T.locked_splits)       # test_same, test_hard, test2_* stay locked


def test_counts_and_subsets():
  n = {s: len(T.cases(s)) for s in NEW}
  assert n == h3.COUNTS
  pool = {c["cell"] for c in T.cases("pool3")}
  probe, sel = {c["cell"] for c in T.cases("probe3")}, {c["cell"] for c in T.cases("select3")}
  assert probe <= pool and sel <= pool and not probe & sel
  assert not {c["cell"] for c in T.cases("test3")} & pool


def test_prompts_equal_the_generator_render():
  for s in ("test3", "pool3"):
    for c in T.cases(s):
      for o in T.orders(c):
        a, am = h3.HagglingTask.render(T, c, o)
        b, bm = g.render(c, o)
        assert hashlib.sha256(a.encode()).digest() == hashlib.sha256(b.encode()).digest(), c["cid"]


def test_payoffs_reproduce_stored_labels():
  for s in ("test3", "pool3"):
    _, cells = T._load(s)
    for c in T.cases(s):
      assert sorted(T.reference(c)["best_options"]) == sorted(cells[c["cell"]]["best_positions"])


def test_changed_file_is_refused(tmp_path, monkeypatch):
  d = tmp_path / "gen"; d.mkdir()
  for f in ("test3_cases.jsonl", "test3_cells.json", "pool3_cases.jsonl", "pool3_cells.json", "test3_fingerprints.json"):
    shutil.copy(os.path.join(h3.GEN_DIR, f), d / f)
  with open(d / "pool3_cases.jsonl", "a") as fh:
    fh.write("\n")
  monkeypatch.setattr(h3, "GEN_DIR", str(d)); monkeypatch.setattr(h3.Haggling3Task, "FINGERPRINTS", str(d / "test3_fingerprints.json"))
  with pytest.raises(RuntimeError, match="fingerprint"):
    h3.Haggling3Task().cases("probe3")


def test_test3_refused_without_lock(tmp_path, monkeypatch):
  monkeypatch.setenv("HARNESS_PIN_REF", "test-pin")
  monkeypatch.setattr(evaluate.lock_protected, "pin_mismatches", lambda ref: [])
  with pytest.raises(evaluate.EvaluationRefused, match="locked"):
    evaluate.evaluate(T, cpu.OracleSolver(), "test3", directory=str(tmp_path))


def test_build_split_scores_without_lock(tmp_path):
  rec = evaluate.evaluate(T, cpu.OracleSolver(), "select3", directory=str(tmp_path), write=False)
  assert rec["summary"]["n_cases"] == 30 and rec["summary"]["soft_regret_mean"] == 0


def test_failure_map_table_from_synthetic_records(tmp_path):
  """The table builder on stand-in records (CPU solvers posing as plain and A0 seeds 0-2), written to a scratch folder."""
  import importlib.util, json
  sp = importlib.util.spec_from_file_location("fm", os.path.join(ROOT, "scripts", "targeted_failure_map.py"))
  fm = importlib.util.module_from_spec(sp); sp.loader.exec_module(fm)
  from harness import modelspec
  for a in fm.arms("qwen25_7b"):
    s = cpu.RandomSolver(seed=a["seed"]); s.name = a["solver"]
    evaluate.evaluate(T, s, "probe3", a["seed"], modelspec.load("qwen25_7b"), {"step": fm.STEP}, directory=str(tmp_path))
  out = fm.table("qwen25_7b", runs=str(tmp_path), out_dir=str(tmp_path))
  assert out["n_cells"] == 90 and all(len(r["a0_soft_regret_per_seed"]) == 3 for r in out["rows"])
  assert not any(k in json.dumps(out["rows"]) for k in ("test3", "tune"))
