"""demo/ledger.py runs on the current files, and every row has a source."""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_ledger_runs_and_every_row_has_a_source():
  env = dict(os.environ, PYTHONPATH=os.pathsep.join([os.path.join(ROOT, "concordia"), ROOT]))
  out = subprocess.run([sys.executable, os.path.join(ROOT, "demo", "ledger.py")],
                       capture_output=True, text=True, env=env, cwd=ROOT, timeout=600)
  assert out.returncode == 0, out.stderr[-2000:]
  led = json.load(open(os.path.join(ROOT, "demo_out", "ledger.json")))
  rows = led["rows"]
  assert len(rows) >= 20
  for r in rows:
    assert r["source"], r["method"]
    assert os.path.exists(os.path.join(ROOT, r["source"])), r["source"]
    assert r["beat"] in ("failure-is-real", "one-sentence", "inside-the-model", "take-home")
    assert r["beats_control"] in ("yes", "no", "n/a")
    assert len(r["verdict"].split()) <= 12
  methods = [r["method"] for r in rows]
  assert any("tune job v1" in m for m in methods) and any("tune job v2" in m for m in methods)
  assert len(led["best"]) == 3 and len(led["failed"]) == 3
  md = open(os.path.join(ROOT, "RESULTS_LEDGER.md")).read()
  assert "## Three best methods" in md and "## Three that failed" in md and "## Slow runs" in md
