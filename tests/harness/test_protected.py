"""The scorer lives in harness/protected; its sha256 must be registered in DECISIONS.md."""
import hashlib, os, pytest
from conftest import ROOT
from tools import lock_protected as lp
from harness.protected import scorer


def test_protected_hashes_are_registered_in_decisions():
  assert lp.unexplained() == [], "protected file changed: add `PROTECTED <path> sha256 <hash>` with a reason to DECISIONS.md"


def test_detects_tampering(tmp_path, monkeypatch):
  """A changed scorer without a DECISIONS.md line is reported."""
  fake = tmp_path / "harness" / "protected"; fake.mkdir(parents=True)
  (fake / "scorer.py").write_text("x = 1\n")
  (tmp_path / "DECISIONS.md").write_text("nothing registered\n")
  monkeypatch.setattr(lp, "ROOT", str(tmp_path)); monkeypatch.setattr(lp, "PDIR", str(fake))
  assert lp.unexplained()
  h = hashlib.sha256(b"x = 1\n").hexdigest()
  (tmp_path / "DECISIONS.md").write_text(f"PROTECTED harness/protected/scorer.py sha256 {h}\n")
  assert lp.unexplained() == []


def test_evaluate_refuses_tampered_scorer(monkeypatch):
  from harness import evaluate
  monkeypatch.setattr(evaluate.lock_protected, "unexplained", lambda: [("harness/protected/scorer.py", "abc")])
  with pytest.raises(evaluate.EvaluationRefused):
    evaluate._check_protected()


def test_scorer_known_values():
  pay = [0.0, 3.0, 2.0, 1.0, 0.0]
  assert scorer.soft_regret(pay, [0, 1, 0, 0, 0]) == 0
  assert scorer.soft_regret(pay, [0.2] * 5) == pytest.approx(3 - 1.2)
  assert scorer.hard_regret(pay, [0, 0, 1, 0, 0]) == 1
  with pytest.raises(ValueError):
    scorer.soft_regret(pay, [0.5, 0.1, 0, 0, 0])


def test_newest_registration_wins(tmp_path, monkeypatch):
  fake = tmp_path / "harness" / "protected"; fake.mkdir(parents=True)
  (fake / "scorer.py").write_text("x = 1\n")
  h1 = hashlib.sha256(b"x = 1\n").hexdigest(); h0 = hashlib.sha256(b"x = 0\n").hexdigest()
  monkeypatch.setattr(lp, "ROOT", str(tmp_path)); monkeypatch.setattr(lp, "PDIR", str(fake)); monkeypatch.setattr(lp, "EXTRA", ())
  (tmp_path / "DECISIONS.md").write_text(f"PROTECTED harness/protected/scorer.py sha256 {h1}\nPROTECTED harness/protected/scorer.py sha256 {h0}\n")
  assert lp.unexplained()                       # an old hash registered earlier does not cover the current file once a newer line exists
  (tmp_path / "DECISIONS.md").write_text(f"PROTECTED harness/protected/scorer.py sha256 {h0}\nPROTECTED harness/protected/scorer.py sha256 {h1}\n")
  assert lp.unexplained() == []


def test_pin_detects_edit_even_with_decisions_entry(tmp_path, monkeypatch):
  import subprocess
  r = tmp_path
  def git(*a): subprocess.check_call(["git", "-C", str(r), *a], stdout=subprocess.DEVNULL)
  git("init", "-q"); git("config", "user.email", "t@t"); git("config", "user.name", "t")
  (r / "harness" / "protected").mkdir(parents=True); f = r / "harness" / "protected" / "scorer.py"; f.write_text("x = 1\n")
  git("add", "-A"); git("commit", "-qm", "pin"); git("tag", "scorer-pin-1")
  monkeypatch.setattr(lp, "ROOT", str(r)); monkeypatch.setattr(lp, "PDIR", str(r / "harness" / "protected")); monkeypatch.setattr(lp, "EXTRA", ())
  assert lp.pin_mismatches("scorer-pin-1") == []
  f.write_text("x = 2\n")
  h = hashlib.sha256(b"x = 2\n").hexdigest()
  (r / "DECISIONS.md").write_text(f"PROTECTED harness/protected/scorer.py sha256 {h}\n")
  assert lp.unexplained() == []                 # self-attested registration passes ...
  assert lp.pin_mismatches("scorer-pin-1")      # ... the owner's tag does not
  with pytest.raises(RuntimeError):
    lp.pin_mismatches("no-such-tag")


def test_locked_look_needs_owner_pin(tmp_path, monkeypatch):
  from harness import evaluate
  from harness.solvers import cpu
  from harness.task import get_task
  monkeypatch.delenv("HARNESS_PIN_REF", raising=False)
  with pytest.raises(evaluate.EvaluationRefused, match="HARNESS_PIN_REF"):
    evaluate.evaluate(get_task("parity"), cpu.OracleSolver(), "test", directory=str(tmp_path), lock_token="G3-OWNER-GO:x")
