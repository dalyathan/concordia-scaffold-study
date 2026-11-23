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
