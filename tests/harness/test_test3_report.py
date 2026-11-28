"""tools/test3_report.py on SYNTHETIC test3 records (CPU stand-ins for the arms, written to a scratch folder; the real runs/ folder is
checked untouched). Checks the frozen rules: both-parts H1, per-seed condition, H2, H3, readout gate and wording."""
import glob, os, sys

import pytest

from conftest import ROOT
from harness import evaluate, modelspec, records
from harness.solvers import cpu
from harness.tasks.haggling3 import Haggling3Task

sys.path.insert(0, os.path.join(ROOT, "tools"))
import test3_report as R3  # noqa: E402

TOK = "G3-OWNER-GO:test-only"


class Mix(cpu._Base):
  """oracle with weight w_nc on no-cost cases and w_ot on the others, uniform otherwise; `mass` is the letter mass"""
  def __init__(self, name, seed, w_nc, w_ot, mass=1.0):
    super().__init__(tag=f"{name}-{seed}"); self.name, self.wn, self.wo, self.m = name, w_nc, w_ot, mass
  def letter_probs(self, task, case, order):
    o = cpu.OracleSolver().letter_probs(task, case, order)
    w = self.wn if case.get("type") == "no_cost" else self.wo
    return {"probs": {l: w * p + (1 - w) / 5 for l, p in o["probs"].items()}, "mass": self.m, "prompt_sha256": o["prompt_sha256"]}


@pytest.fixture(autouse=True)
def _runs_untouched():
  before = set(glob.glob(os.path.join(ROOT, "runs", "haggling", "*", "*test3*.json")))
  yield
  assert set(glob.glob(os.path.join(ROOT, "runs", "haggling", "*", "*test3*.json"))) == before


def look(tmp_path, monkeypatch, w, mass=None):
  monkeypatch.setenv("HARNESS_PIN_REF", "test-pin")
  monkeypatch.setattr(evaluate.lock_protected, "pin_mismatches", lambda ref: [])
  monkeypatch.setattr(records, "RUNS", str(tmp_path / "runs"))
  task, ms = Haggling3Task(), modelspec.load("qwen25_7b")
  sol = R3.arm_solvers("qwen25_7b")
  for arm in ("T", "R", "N", "A0"):
    for s in (0, 1, 2):
      wn, wo = w[arm][s] if isinstance(w[arm], list) else w[arm]
      evaluate.evaluate(task, Mix(sol[arm], s, wn, wo, (mass or {}).get(arm, 1.0)), "test3", s, ms, {"step": "test3 look"}, TOK,
                        directory=str(tmp_path / "runs"))
  evaluate.evaluate(task, cpu.BaselineSolver(policy="cheapest"), "test3", 0, None, {"step": "test3 look reference"}, TOK, directory=str(tmp_path / "runs"))
  return R3.build("qwen25_7b", R3.load("qwen25_7b", root=str(tmp_path)))


def test_both_parts_hold(tmp_path, monkeypatch):
  md, J = look(tmp_path, monkeypatch, {"T": (0.95, 0.95), "R": (0.5, 0.95), "N": (0.7, 0.95), "A0": (0.4, 0.95)})
  assert J["H1"]["R"]["holds"] and J["H1"]["N"]["holds"] and J["conclusion"]["H1"] == "both" and J["conclusion"]["H2"]
  assert J["H3"]["T"]["holds"] and R3.WORDING["both"] in md


def test_beats_random_but_not_no_cost_random(tmp_path, monkeypatch):
  _, J = look(tmp_path, monkeypatch, {"T": (0.9, 0.95), "R": (0.4, 0.95), "N": (0.9, 0.95), "A0": (0.4, 0.95)})
  assert J["H1"]["R"]["holds"] and not J["H1"]["N"]["holds"] and J["conclusion"]["H1"] == "R_only"


def test_one_bad_seed_breaks_the_every_seed_condition(tmp_path, monkeypatch):
  _, J = look(tmp_path, monkeypatch, {"T": [(0.95, 0.95), (0.95, 0.95), (0.3, 0.95)], "R": (0.5, 0.95), "N": (0.6, 0.95), "A0": (0.4, 0.95)})
  assert not J["H1"]["R"]["conditions"]["every seed below"] and not J["H1"]["R"]["holds"]


def test_harm_elsewhere_fails_h2(tmp_path, monkeypatch):
  _, J = look(tmp_path, monkeypatch, {"T": (0.95, 0.2), "R": (0.5, 0.95), "N": (0.7, 0.95), "A0": (0.4, 0.95)})
  assert not J["conclusion"]["H2"] and R3.WORDING["H2_fails"] in J["conclusion"]["wording"]


def test_low_letter_mass_is_not_concluded(tmp_path, monkeypatch):
  _, J = look(tmp_path, monkeypatch, {"T": (0.95, 0.95), "R": (0.5, 0.95), "N": (0.7, 0.95), "A0": (0.4, 0.95)}, mass={"T": 0.5})
  assert J["conclusion"]["H1"] == "not_concluded"


def test_incomplete_look():
  md, J = R3.build("qwen25_7b", [])
  assert J["status"] == "incomplete" and "No complete look" in md


def test_t_beats_no_cost_random_only(tmp_path, monkeypatch):
  _, J = look(tmp_path, monkeypatch, {"T": (0.8, 0.95), "R": (0.8, 0.95), "N": (0.3, 0.95), "A0": (0.4, 0.95)})
  assert J["conclusion"]["H1"] == "N_only"


def test_missing_seed_is_not_concluded(tmp_path, monkeypatch):
  md, J = look(tmp_path, monkeypatch, {"T": (0.95, 0.95), "R": (0.5, 0.95), "N": (0.7, 0.95), "A0": (0.4, 0.95)})
  recs = [r for r in R3.load("qwen25_7b", root=str(tmp_path)) if not (r["solver"].endswith("_R_lr3e-04") and r["seed"] == 2)]
  md, J = R3.build("qwen25_7b", recs, root=str(tmp_path))
  assert J["conclusion"]["H1"] == "not_concluded" and "Incomplete arms" in md


def test_stray_and_duplicate_records(tmp_path, monkeypatch):
  import json, shutil
  look(tmp_path, monkeypatch, {"T": (0.95, 0.95), "R": (0.5, 0.95), "N": (0.7, 0.95), "A0": (0.4, 0.95)})
  d = tmp_path / "runs" / "haggling" / "qwen25_7b"
  f = sorted(d.glob("*n150_T*test3-s0*.json"))[0]
  r = json.load(open(f)); r["config"]["step"] = "something else"; json.dump(r, open(d / "stray.json", "w"))
  assert len(R3.load("qwen25_7b", root=str(tmp_path))) == 13              # the stray record is not read
  shutil.copy(f, d / "dup.json")
  with pytest.raises(SystemExit, match="two test3 records"):
    R3.load("qwen25_7b", root=str(tmp_path))


def test_descriptive_and_predictions_present(tmp_path, monkeypatch):
  md, J = look(tmp_path, monkeypatch, {"T": (0.95, 0.95), "R": (0.5, 0.95), "N": (0.7, 0.95), "A0": (0.4, 0.95)})
  assert "V 10-15" in J["descriptive"]["slices"] and "T" in J["descriptive"]["planted_nocost"]
  assert set(J["predictions"]["outcomes"]) >= {"Q1", "Q2", "Q3", "Q5", "Q6", "Q7", "Q8"}
