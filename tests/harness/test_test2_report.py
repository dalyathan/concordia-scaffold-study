"""tools/test2_report.py and scripts/test2_look.py on SYNTHETIC records (CPU solvers standing in for the arms, written to a temp folder).
No model is loaded and no real arm is scored; this checks the report's rules, its refusals and the freeze file, before the look."""
import json, os

import pytest

from conftest import ROOT
from harness import evaluate, modelspec
from harness.solvers import cpu
from harness.tasks.haggling import HagglingTask

import importlib.util
spec = importlib.util.spec_from_file_location("test2_look", os.path.join(ROOT, "scripts", "test2_look.py"))
look = importlib.util.module_from_spec(spec); spec.loader.exec_module(look)
import sys; sys.path.insert(0, os.path.join(ROOT, "tools"))
import test2_report as T2  # noqa: E402

MODELS = ("llama31_8b", "qwen25_7b")
CELLS = json.load(open(os.path.join(ROOT, "demo", "gen", "test2_cells.json")))["cells"]


class Mix(cpu._Base):
  """w * oracle + (1 - w) * uniform, posing as a frozen arm (its name, seed and adapter hash)."""
  def __init__(self, name, w, adapter=None, seed=0):
    super().__init__(adapter_weights_sha256=adapter, training={"seed": seed} if adapter else None)
    self.name, self.w = name, w
  def letter_probs(self, task, case, order):
    o = cpu.OracleSolver().letter_probs(task, case, order)
    return {"probs": {l: self.w * p + (1 - self.w) / 5 for l, p in o["probs"].items()}, "mass": 1.0, "prompt_sha256": o["prompt_sha256"]}


@pytest.fixture
def pinned(monkeypatch):
  monkeypatch.setenv("HARNESS_PIN_REF", "test-pin")
  monkeypatch.setattr(evaluate.lock_protected, "pin_mismatches", lambda ref: [])


def fake_look(tmp_path, model, weights):
  fz = look.build_freeze(model)
  runs = tmp_path / "runs"
  task, ms = HagglingTask(), modelspec.load(model)
  tok = "G3-OWNER-GO:test-only"
  for split in look.SPLITS:
    for name, s in (("oracle", cpu.OracleSolver()), ("uniform", cpu.UniformSolver()), ("c", cpu.BaselineSolver(policy="cheapest")),
                    ("r", cpu.BaselineSolver(policy="stated_cost_rule"))):
      evaluate.evaluate(task, s, split, 0, None, {"step": "test2 look reference"}, tok, directory=str(runs))
    for a in fz["arms"]:
      w = weights[a["label"]]
      s = Mix(a["solver"], w, a["adapter"]["weights_sha256"] if a["adapter"] else None, a["seed"])
      evaluate.evaluate(task, s, split, a["seed"], ms, {"step": "test2 look"}, tok, directory=str(runs))
  return fz


@pytest.mark.parametrize("model", MODELS)
def test_freeze_covers_the_planned_arms(model):
  fz = look.build_freeze(model)
  labels = [(a["label"], a["seed"]) for a in fz["arms"]]
  assert labels == [("plain", 0), ("examples-100", 0), ("examples-100", 1), ("examples-100", 2), ("scrambled N=100", 0), ("cheapest-label N=100", 0)]
  assert all(a["adapter"]["version"].startswith("selected") for a in fz["arms"] if a["adapter"])
  assert not any("_last" in a["solver"] for a in fz["arms"])


def test_committed_freeze_files_match_the_records():
  for m in MODELS:
    if os.path.exists(look.freeze_path(m)):
      assert look.check_freeze(m)[1] == []


def test_no_look_yet_report():
  md, J = T2.build("qwen25_7b", [], [], look.build_freeze("qwen25_7b"), CELLS)
  assert J["status"] == "no look" and "No look yet" in md


def test_report_rules_on_synthetic_records(tmp_path, pinned, monkeypatch):
  monkeypatch.setattr(evaluate.records, "RUNS", str(tmp_path / "runs"))
  w = {"plain": 0.0, "examples-100": 0.95, "scrambled N=100": 0.3, "cheapest-label N=100": 0.1}
  fz = fake_look(tmp_path, "qwen25_7b", w)
  own, ref = T2.load_records("qwen25_7b", root=str(tmp_path))
  assert len(own) == 12 and len(ref) == 8
  md, J = T2.build("qwen25_7b", own, ref, fz, CELLS)
  assert J["T1"]["holds"] and J["T2"]["holds"] and J["conclusion"]["case"] == "both hold"
  assert "test2_newkey" in J and all(nm in J["test2_newkey"] for nm, _ in T2.SLICES)
  # a weak examples arm fails T1 and gets the fixed wording
  md2, J2 = T2.build("qwen25_7b", own, ref, fz, CELLS)
  assert md2 == md      # deterministic


def test_weak_arm_fails_t1(tmp_path, pinned, monkeypatch):
  monkeypatch.setattr(evaluate.records, "RUNS", str(tmp_path / "runs"))
  fz = fake_look(tmp_path, "llama31_8b", {"plain": 0.2, "examples-100": 0.1, "scrambled N=100": 0.3, "cheapest-label N=100": 0.1})
  own, ref = T2.load_records("llama31_8b", root=str(tmp_path))
  _, J = T2.build("llama31_8b", own, ref, fz, CELLS)
  assert not J["T1"]["holds"] and J["conclusion"]["wording"] == T2.WORDING["T1 fails"]


def test_report_refuses_unfrozen_adapter(tmp_path, pinned, monkeypatch):
  monkeypatch.setattr(evaluate.records, "RUNS", str(tmp_path / "runs"))
  fz = fake_look(tmp_path, "qwen25_7b", {"plain": 0.0, "examples-100": 0.9, "scrambled N=100": 0.3, "cheapest-label N=100": 0.1})
  own, ref = T2.load_records("qwen25_7b", root=str(tmp_path))
  bad = json.loads(json.dumps(fz)); bad["arms"][1]["adapter"]["weights_sha256"] = "0" * 64
  with pytest.raises(SystemExit, match="adapter hash"):
    T2.build("qwen25_7b", own, ref, bad, CELLS)


def test_second_look_at_an_arm_is_refused(tmp_path, pinned, monkeypatch):
  monkeypatch.setattr(evaluate.records, "RUNS", str(tmp_path / "runs"))
  fz = fake_look(tmp_path, "qwen25_7b", {"plain": 0.0, "examples-100": 0.9, "scrambled N=100": 0.3, "cheapest-label N=100": 0.1})
  a = fz["arms"][1]
  with pytest.raises(evaluate.EvaluationRefused, match="already scored"):
    evaluate.evaluate(HagglingTask(), Mix(a["solver"], 1.0, "f" * 64, a["seed"]), "test2_same", a["seed"], modelspec.load("qwen25_7b"),
                      {}, "G3-OWNER-GO:test-only", directory=str(tmp_path / "elsewhere"))
