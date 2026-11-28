"""scripts/test3_look.py driver path with stand-in solvers in a scratch runs folder: references once, every arm once, resume, report."""
import glob, importlib.util, os, sys

import pytest

from conftest import ROOT
from harness import evaluate, records
from harness.solvers import cpu

sp = importlib.util.spec_from_file_location("t3l", os.path.join(ROOT, "scripts", "test3_look.py"))
t3l = importlib.util.module_from_spec(sp); sp.loader.exec_module(t3l)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import test3_report as R3  # noqa: E402

TOK = "G3-OWNER-GO:test-only"


def test_driver_path_and_resume(tmp_path, monkeypatch):
  before = set(glob.glob(os.path.join(ROOT, "runs", "haggling", "*", "*test3*.json")))
  monkeypatch.setenv("HARNESS_PIN_REF", "test-pin")
  monkeypatch.setattr(evaluate.lock_protected, "pin_mismatches", lambda ref: [])
  runs = str(tmp_path / "runs"); monkeypatch.setattr(records, "RUNS", runs)
  real = evaluate.evaluate
  monkeypatch.setattr(evaluate, "evaluate", lambda *a, **k: real(*a, **{"directory": runs, **k}))
  sol = R3.arm_solvers("qwen25_7b")
  arms = [{"label": "plain", "solver": "plain", "seed": 0, "adapter": None}] + \
         [{"label": X, "solver": sol[X], "seed": s, "adapter": {"weights_sha256": "x"}} for X in ("A0", "T", "R", "N") for s in (0, 1, 2)]
  fz = {"arms": arms}
  monkeypatch.setattr(t3l, "check", lambda m, committed=False, clean=False: (fz, []))
  look = t3l.L()
  class Stub(cpu.OracleSolver):
    def __init__(self, name, seed): super().__init__(n=name, training={"seed": seed}); self.name = name
  monkeypatch.setattr(t3l, "L", lambda: type("M", (), {"check_environment": staticmethod(lambda fz: None), "load_backend": staticmethod(lambda s: None),
                                                     "make_solver": staticmethod(lambda b, arm: Stub(arm["solver"], arm["seed"])),
                                                     "preflight": staticmethod(lambda task, s, arm, spec: 0.0), "git": look.git})())
  t3l.references(TOK); t3l.references(TOK)
  for i in range(len(arms)):
    t3l.run_one("qwen25_7b", i, TOK)
  for i in range(len(arms)):
    t3l.run_one("qwen25_7b", i, TOK)                    # rerun: nothing new
  recs = R3.load("qwen25_7b", root=str(tmp_path))
  assert len([r for r in recs if r["solver"] != "plain" and r["model"]]) == 12 and len([r for r in recs if r["model"] is None]) == 4
  md, J = R3.build("qwen25_7b", recs)
  assert "conclusion" in J
  assert set(glob.glob(os.path.join(ROOT, "runs", "haggling", "*", "*test3*.json"))) == before
