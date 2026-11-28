"""tools/test2_report.py and scripts/test2_look.py on SYNTHETIC records (CPU solvers standing in for the arms, written to a temp folder).
No model is loaded and no real arm is scored; this checks the report's rules and refusals, the driver path (references, per-arm
scoring, resume, preflight) and the freeze file, before the look."""
import glob, json, os, shutil

import pytest

from conftest import ROOT
from harness import evaluate, modelspec, records
from harness.solvers import cpu
from harness.tasks.haggling import HagglingTask

import importlib.util
spec = importlib.util.spec_from_file_location("test2_look", os.path.join(ROOT, "scripts", "test2_look.py"))
look = importlib.util.module_from_spec(spec); spec.loader.exec_module(look)
import sys; sys.path.insert(0, os.path.join(ROOT, "tools"))
import test2_report as T2  # noqa: E402

MODELS = ("llama31_8b", "qwen25_7b")
CELLS = json.load(open(os.path.join(ROOT, "demo", "gen", "test2_cells.json")))["cells"]
TOK = "G3-OWNER-GO:test-only"


class Mix(cpu._Base):
  """w * oracle + (1 - w) * uniform, posing as a frozen arm (its name, seed, adapter hash and model pin); `mass` is the letter mass."""
  def __init__(self, arm, w, revision, mass=1.0):
    a = arm["adapter"]
    super().__init__(adapter_weights_sha256=a["weights_sha256"] if a else None, training=arm["training"], revision=revision)
    self.name, self.w, self.m = arm["solver"], w, mass
  def letter_probs(self, task, case, order):
    o = cpu.OracleSolver().letter_probs(task, case, order)
    return {"probs": {l: self.w * p + (1 - self.w) / 5 for l, p in o["probs"].items()}, "mass": self.m, "prompt_sha256": o["prompt_sha256"]}


class Echo(cpu._Base):
  """Returns the per-order probabilities stored in a tune record (what a correctly reloaded adapter would give); `bump` perturbs them."""
  def __init__(self, arm, bump=0.0):
    super().__init__(); self.name = arm["solver"]
    rec = json.load(open(os.path.join(ROOT, arm["tune_record"])))
    self.po = {x["cid"]: x["per_order_probs"] for x in rec["cases"]}; self.bump = bump
  def letter_probs(self, task, case, order):
    text, l2o = task.render(case, order)
    k = list(task.orders(case)).index(tuple(order))
    p = {l: self.po[case["cid"]][k][o] for l, o in l2o.items()}
    if k == 0:                       # one order only (a bump in every cyclic order would average out)
      p["a"] += self.bump; p["b"] -= self.bump
    return {"probs": p, "mass": 1.0, "prompt_sha256": "x"}


@pytest.fixture
def scratch(tmp_path, monkeypatch):
  """Pin stubbed, records written to a scratch runs folder (never the repository's runs/)."""
  monkeypatch.setenv("HARNESS_PIN_REF", "test-pin")
  monkeypatch.setattr(evaluate.lock_protected, "pin_mismatches", lambda ref: [])
  runs = tmp_path / "runs"
  monkeypatch.setattr(records, "RUNS", str(runs))
  real = evaluate.evaluate            # its `directory` default was bound to the real runs/ at import: always pass the scratch folder
  def scratch_evaluate(*a, **kw):
    kw.setdefault("directory", str(runs))
    return real(*a, **kw)
  monkeypatch.setattr(evaluate, "evaluate", scratch_evaluate)
  return tmp_path


@pytest.fixture(autouse=True)
def _repository_runs_untouched():
  """No test may leave a test2 record in the repository's runs/ folder (it would also block the real look)."""
  before = set(glob.glob(os.path.join(ROOT, "runs", "haggling", "*", "*test2_*.json")))
  yield
  after = set(glob.glob(os.path.join(ROOT, "runs", "haggling", "*", "*test2_*.json")))
  assert after == before, f"test wrote into the repository runs/: {sorted(after - before)[:3]}"


def fake_look(tmp_path, model, weights, mass=None, skip=()):
  fz = look.build_freeze(model)
  task, ms = HagglingTask(), modelspec.load(model)
  look.references(TOK)
  for a in fz["arms"]:
    for split in look.SPLITS:
      if (a["label"], a["seed"], split) in skip:
        continue
      s = Mix(a, weights[a["label"]], fz["model_revision"], (mass or {}).get(a["label"], 1.0))
      evaluate.evaluate(task, s, split, a["seed"], ms, {"step": "test2 look"}, TOK)
  return fz


def report(tmp_path, model, fz):
  own, ref = T2.load_records(model, root=str(tmp_path))
  return T2.build(model, own, ref, fz, CELLS)


STRONG = {"plain": 0.0, "examples-100": 0.97, "scrambled N=100": 0.3, "cheapest-label N=100": 0.1}


@pytest.mark.parametrize("model", MODELS)
def test_freeze_covers_the_planned_arms(model):
  fz = look.build_freeze(model)
  labels = [(a["label"], a["seed"]) for a in fz["arms"]]
  assert labels == [("plain", 0), ("examples-100", 0), ("examples-100", 1), ("examples-100", 2), ("scrambled N=100", 0), ("cheapest-label N=100", 0)]
  assert all(a["adapter"]["version"].startswith("selected") for a in fz["arms"] if a["adapter"])
  assert not any("_last" in a["solver"] for a in fz["arms"])
  assert "tools/llama_report.py" in fz["file_sha256"] and "harness/solvers/cpu.py" in fz["file_sha256"]
  assert set(fz["environment"]["packages"]) == {"torch", "transformers", "peft"}


def test_committed_freeze_files_match_the_repository():
  for m in MODELS:
    if os.path.exists(look.freeze_path(m)):
      assert look.check_freeze(m)[1] == []


def test_no_look_yet_report():
  md, J = T2.build("qwen25_7b", [], [], look.build_freeze("qwen25_7b"), CELLS)
  assert J["status"] == "no look" and "No look yet" in md


def test_strong_arm_all_rules_hold(scratch):
  fz = fake_look(scratch, "qwen25_7b", STRONG)
  own, ref = T2.load_records("qwen25_7b", root=str(scratch))
  assert len(own) == 12 and len(ref) == 8
  md, J = report(scratch, "qwen25_7b", fz)
  assert J["T1"]["result"] == "holds" and J["T2"]["result"] == {"T2a": "holds", "T2b": "holds"}
  assert J["conclusion"]["wording"].startswith(T2.T1_TEXT["holds"]) and T2.T2_TEXT[(True, True)] in md
  assert all(nm in J["test2_newkey"] for nm, _ in T2.SLICES)
  c = J["T2"]["composition"]
  assert c["cells"] == 33 and sum(c["by_type"].values()) == 33
  assert J["predictions"]["brier"] is not None and report(scratch, "qwen25_7b", fz)[0] == md     # deterministic


def test_weak_arm_fails_t1_and_t2a(scratch):
  fz = fake_look(scratch, "llama31_8b", {"plain": 0.2, "examples-100": 0.1, "scrambled N=100": 0.3, "cheapest-label N=100": 0.1})
  _, J = report(scratch, "llama31_8b", fz)
  assert J["T1"]["result"] == "fails" and J["T2"]["result"]["T2a"] == "fails"
  assert J["conclusion"]["wording"] == f"{T2.T1_TEXT['fails']}; {T2.T2_TEXT[(False, False)]}"


def test_low_letter_mass_is_not_concluded(scratch):
  fz = fake_look(scratch, "qwen25_7b", STRONG, mass={"examples-100": 0.6})
  _, J = report(scratch, "qwen25_7b", fz)
  assert J["T1"]["result"] == "not concluded" and J["T2"]["result"] == "not concluded"


def test_missing_arm_is_not_concluded(scratch):
  fz = fake_look(scratch, "qwen25_7b", STRONG, skip={("examples-100", 2, "test2_same")})
  md, J = report(scratch, "qwen25_7b", fz)
  assert "Incomplete look" in md and J["T1"]["result"] == "not concluded" and J["T2"]["result"]["T2a"] == "holds"


def test_report_refuses_unfrozen_adapter_and_wrong_pin(scratch):
  fz = fake_look(scratch, "qwen25_7b", STRONG)
  own, ref = T2.load_records("qwen25_7b", root=str(scratch))
  bad = json.loads(json.dumps(fz)); bad["arms"][1]["adapter"]["weights_sha256"] = "0" * 64
  with pytest.raises(SystemExit, match="adapter hash"):
    T2.build("qwen25_7b", own, ref, bad, CELLS)
  bad = json.loads(json.dumps(fz)); bad["model_revision"] = "f" * 40
  with pytest.raises(SystemExit, match="model pin"):
    T2.build("qwen25_7b", own, ref, bad, CELLS)


def test_report_refuses_wrong_step_and_duplicate_reference(scratch):
  fz = fake_look(scratch, "qwen25_7b", STRONG)
  own, ref = T2.load_records("qwen25_7b", root=str(scratch))
  own[0]["config"]["step"] = "something else"
  with pytest.raises(SystemExit, match="step"):
    T2.build("qwen25_7b", own, ref, fz, CELLS)
  own, ref = T2.load_records("qwen25_7b", root=str(scratch))
  with pytest.raises(SystemExit, match="two records"):
    T2.build("qwen25_7b", own, ref + [json.loads(json.dumps(ref[0]))], fz, CELLS)


def test_second_look_at_an_arm_is_refused(scratch):
  fz = fake_look(scratch, "qwen25_7b", STRONG)
  a = fz["arms"][1]
  with pytest.raises(evaluate.EvaluationRefused, match="already scored"):
    evaluate.evaluate(HagglingTask(), Mix(a, 1.0, fz["model_revision"]), "test2_same", a["seed"], modelspec.load("qwen25_7b"),
                      {}, TOK, directory=str(scratch / "elsewhere"))


# ---------------------------------------------------------------- the driver path with stub model and solvers
def stub_driver(monkeypatch, fz, w=0.9):
  monkeypatch.setattr(look, "load_backend", lambda spec: None)
  monkeypatch.setattr(look, "make_solver", lambda b, arm: Mix(arm, w, fz["model_revision"]))
  monkeypatch.setattr(look, "preflight", lambda task, s, arm, spec: 0.0)


def test_driver_scores_every_arm_once_and_resumes(scratch, monkeypatch):
  fz = look.build_freeze("qwen25_7b")
  stub_driver(monkeypatch, fz)
  monkeypatch.setattr(look, "check_freeze", lambda m, committed=False, tree_clean=False: (fz, []))
  look.references(TOK)
  look.references(TOK)                                   # second call skips: references already recorded
  a = fz["arms"][1]
  evaluate.evaluate(HagglingTask(), Mix(a, 0.9, fz["model_revision"]), "test2_same", a["seed"], modelspec.load("qwen25_7b"),
                    {"step": "test2 look"}, TOK)        # a crash after test2_same of arm 1
  for i in range(len(fz["arms"])):
    look.run_one("qwen25_7b", i, TOK, env_check=False)
  for i in range(len(fz["arms"])):
    look.run_one("qwen25_7b", i, TOK, env_check=False)  # a rerun scores nothing new
  own, ref = T2.load_records("qwen25_7b", root=str(scratch))
  assert len(own) == 12 and len(ref) == 8
  _, J = report(scratch, "qwen25_7b", fz)
  assert not J["missing"]


def test_preflight_passes_for_the_stored_probabilities_and_fails_otherwise():
  fz = look.build_freeze("qwen25_7b")
  task, ms = HagglingTask(), modelspec.load("qwen25_7b")
  arm = fz["arms"][1]
  assert look.preflight(task, Echo(arm), arm, ms) < 1e-12
  with pytest.raises(SystemExit, match="PREFLIGHT FAILED"):
    look.preflight(task, Echo(arm, bump=1e-2), arm, ms)
