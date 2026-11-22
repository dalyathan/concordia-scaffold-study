"""The LoRA pass rule on synthetic runs (no model): a method adapter that copies the
method-text distribution passes the owner's rule; one that copies plain does not."""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "demo"))
import common  # noqa: E402
from refimpl import core  # noqa: E402


def fake_run(arm, lr, seed, probs, mass=0.9, train=0.4, slope=0.4, say_hr=0.1, perm=0):
  rid = f"{arm}{perm if arm == 'shuffled' else ''}_lr{lr:.0e}_s{seed}"
  return {"run_id": rid, "arm": arm, "perm": perm, "lr": lr, "seed": seed, "rank": 4, "best_epoch": 3, "epochs_run": 5,
          "tune_best": {"soft_regret": 0.0, "mass": mass, "slope_stated_cost": slope},
          "train_best": {"soft_regret": train}, "train_min_soft_regret": train,
          "tune_probs_best": probs, "sec_per_epoch": 300.0,
          "history": [{"tune": {"mass": 0.64}}], "say_plain": {"agreement": 0.5, "say_hard_regret": 0.5},
          "say_best": {"agreement": 0.7, "say_hard_regret": say_hr}}


def run_report(tmp, runs, status=None):
  os.makedirs(os.path.join(tmp, "lora"), exist_ok=True)
  for r in runs:
    json.dump(r, open(os.path.join(tmp, "lora", r["run_id"] + ".json"), "w"))
  json.dump(status or {}, open(os.path.join(tmp, "status.json"), "w"))
  env = dict(os.environ, LORA_OUT=tmp, LORA_SUMMARY=os.path.join(tmp, "summary.json"),
             LORA_STATUS=os.path.join(tmp, "status.json"),
             PYTHONPATH=os.pathsep.join([os.path.join(ROOT, "concordia"), ROOT]))
  out = subprocess.run([sys.executable, os.path.join(ROOT, "demo", "lora_report.py")], capture_output=True,
                       text=True, env=env, cwd=ROOT, timeout=300)
  assert out.returncode == 0, out.stderr[-1500:]
  return json.load(open(os.path.join(tmp, "summary.json"))), out.stdout


def test_pass_rule_on_synthetic_runs(tmp_path):
  sp = json.load(open(os.path.join(ROOT, "demo", "splits_lora.json")))["case_split"]
  tune = [pid for pid, s in sp.items() if s == "lora_tune"]
  plain = {c["pid"]: c["probs"] for c in common.load_cases()}
  mrows = {}
  for f in ("text_rows_tuning.jsonl", "text_rows_build.jsonl"):
    for l in open(os.path.join(ROOT, "demo_out", f)):
      r = json.loads(l)
      if r["row"] == "method":
        mrows[r["pid"]] = r["probs"]
  copy = lambda src: {pid: src[pid] for pid in tune}
  good = [fake_run("method", 3e-4, 0, copy(mrows)), fake_run("neutral", 3e-4, 0, copy(plain)),
          fake_run("wrong_rule", 3e-4, 0, copy(plain)), fake_run("shuffled", 3e-4, 0, copy(plain))]
  summ, text = run_report(str(tmp_path / "good"), good)
  assert summ["owner_pass"] is True and summ["strict"]["S3 mass >= 0.9 x plain"] is True
  assert summ["outcome"].startswith("the method's effect transfers")
  bad = [fake_run("method", 3e-4, 0, copy(plain)), fake_run("neutral", 3e-4, 0, copy(plain)),
         fake_run("wrong_rule", 3e-4, 0, copy(plain))]
  summ, _ = run_report(str(tmp_path / "bad"), bad)
  assert summ["owner_pass"] is False and summ["strict_pass"] is False
  low_mass = [fake_run("method", 3e-4, 0, copy(mrows), mass=0.3)] + good[1:]
  summ, _ = run_report(str(tmp_path / "lowmass"), low_mass)
  assert summ["owner_pass"] is True and summ["strict"]["S3 mass >= 0.9 x plain"] is False and summ["strict_pass"] is False
  summ, _ = run_report(str(tmp_path / "untrainable"), good, status={"trainability": {"pass": False}})
  assert summ["outcome"].startswith("UNDERTRAINED")
