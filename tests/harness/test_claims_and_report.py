import json, os, shutil, subprocess, sys, yaml
from conftest import ROOT


def test_claims_checker_passes_on_repo():
  r = subprocess.run([sys.executable, "tools/check_claims.py"], cwd=ROOT, capture_output=True, text=True)
  assert r.returncode == 0, r.stdout


def test_generated_results_are_fresh():
  assert subprocess.run([sys.executable, "tools/make_report.py", "--check"], cwd=ROOT).returncode == 0


def _run_checker(tmp, claims, readme):
  d = tmp / "repo"; (d / "tools").mkdir(parents=True); (d / "runs").mkdir()
  shutil.copy(os.path.join(ROOT, "tools", "check_claims.py"), d / "tools")
  (d / "CLAIMS.yaml").write_text(yaml.safe_dump(claims)); (d / "README.md").write_text(readme)
  (d / "r.json").write_text(json.dumps({"v": 0.50}))
  return subprocess.run([sys.executable, "tools/check_claims.py"], cwd=d, capture_output=True, text=True)


def claim(shown, ev):
  return {"scan": [{"file": "README.md", "from": "## Results"}],
          "claims": [{"id": "c", "file": "README.md", "text": f"loss {shown}", "numbers": [{"shown": shown, "evidence": ev}]}]}


import hashlib
GOOD = {"kind": "file_value", "path": "r.json", "key": "v", "sha256": hashlib.sha256(json.dumps({"v": 0.50}).encode()).hexdigest()}


def test_checker_accepts_matching_number(tmp_path):
  assert _run_checker(tmp_path, claim("0.50", GOOD), "## Results\nloss 0.50\n").returncode == 0


def test_checker_fails_mismatched_number(tmp_path):
  r = _run_checker(tmp_path, claim("0.40", GOOD), "## Results\nloss 0.40\n")
  assert r.returncode == 1 and "evidence gives" in r.stdout


def test_checker_fails_claim_without_evidence_in_strict(tmp_path):
  c = claim("0.50", {"kind": "none", "reason": "x"})
  d = tmp_path
  r = _run_checker(d, c, "## Results\nloss 0.50\n")
  assert "UNBACKED" not in r.stdout or r.returncode == 0       # reported with --list-unbacked
  s = subprocess.run([sys.executable, "tools/check_claims.py", "--strict"], cwd=d / "repo", capture_output=True, text=True)
  assert s.returncode == 1 and "UNBACKED" in s.stdout


def test_checker_fails_new_uncovered_number(tmp_path):
  r = _run_checker(tmp_path, claim("0.50", GOOD), "## Results\nloss 0.50 and a new hand-typed 0.99\n")
  assert r.returncode == 1 and "uncovered number" in r.stdout


def test_checker_fails_when_claim_text_edited(tmp_path):
  r = _run_checker(tmp_path, claim("0.50", GOOD), "## Results\nloss 0.51\n")
  assert r.returncode == 1


def test_model_configs_load_and_are_consistent():
  from harness import modelspec
  names = modelspec.all_names()
  assert set(names) == {"gemma2_9b", "gemma2_2b", "llama31_8b", "qwen25_7b", "mistral7b_v03"}
  for n in names:
    s = modelspec.load(n)
    assert len(s.layer_names()) == s.num_layers and len(set(s.answer_letters)) == 5
    if s.answer_letter_token_ids is not None:
      assert len(set(s.answer_letter_token_ids)) == 5 and "tokenizer" in s.verified


def test_shared_code_names_no_model():
  import re
  bad = re.compile(r"gemma|llama|qwen|mistral", re.I)
  for f in ("harness/solvers/hf.py", "harness/solvers/cpu.py", "harness/evaluate.py", "harness/records.py", "harness/solver.py",
            "harness/task.py", "harness/modelspec.py", "harness/run.py", "tools/make_report.py", "tools/check_claims.py"):
    hits = [l for l in open(os.path.join(ROOT, f)).read().splitlines() if bad.search(l)]
    assert not hits, (f, hits[:2])


def test_unbacked_numbers_are_exactly_the_known_five():
  """The checker is non-strict on the repo; this pins the unbacked set so a new unbacked number fails the suite."""
  r = subprocess.run([sys.executable, "tools/check_claims.py", "--list-unbacked"], cwd=ROOT, capture_output=True, text=True)
  got = sorted(l.split(":")[1].split("--")[0].strip() for l in r.stdout.splitlines() if l.startswith("UNBACKED"))
  assert got == sorted(["0.12", "1", "0.58", "0.17", "0.2"]), got


def test_recompute_passes_on_all_run_records():
  r = subprocess.run([sys.executable, "tools/recompute.py", "runs"], cwd=ROOT, capture_output=True, text=True)
  assert r.returncode == 0, r.stdout[-800:]


def test_checker_rejects_unlisted_number_in_claim_text(tmp_path):
  c = claim("0.50", GOOD); c["claims"][0]["text"] = "loss 0.50 vs 0.31"
  r = _run_checker(tmp_path, c, "## Results\nloss 0.50 vs 0.31\n")
  assert r.returncode == 1 and "no evidence entry" in r.stdout


def test_checker_run_mean_needs_matching_model(tmp_path):
  ev = {"kind": "run_mean", "task": "t", "model": "m", "solver": "s", "split": "x"}
  r = _run_checker(tmp_path, claim("0.50", ev), "## Results\nloss 0.50\n")
  assert r.returncode == 1 and "no run records" in r.stdout


def test_checker_file_value_is_hash_pinned(tmp_path):
  r = _run_checker(tmp_path, claim("0.50", {**GOOD, "sha256": "0" * 64}), "## Results\nloss 0.50\n")
  assert r.returncode == 1 and "changed since" in r.stdout
