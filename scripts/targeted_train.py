"""Step 5 of TARGETED_PLAN.md (GPU): the nine targeted runs (arms T, R, N x seeds 0-2) on Qwen, in a fixed order, plus the plain select3
record their epoch-0 check needs.

  HF_HUB_OFFLINE=1 CUBLAS_WORKSPACE_CONFIG=:4096:8 HARNESS_PROVIDER=runpod HARNESS_GPU_USD_PER_HOUR=0.60 \
    PYTHONPATH=concordia:. .venv/bin/python scripts/targeted_train.py [--model qwen25_7b] [--budget-stop-h 6]

Needs demo/gen/targeted_draws_<model>.json and demo/gen/targeted_labels_<model>.json, committed. Order: plain on select3 (one record,
config step "targeted plain select3"), then T_s0, R_s0, N_s0, T_s1, R_s1, N_s1, T_s2, R_s2, N_s2, each a separate process of
harness/train_lora.py (lr 3e-4, 150 cells, 750 steps, select3), so a stop leaves whole seeds. A run whose tune record exists is skipped
(restartable); a run that fails or diverges is reported and never rerun (TARGETED_PLAN.md). Stops before a new run when the GPU time of
this experiment's records reaches the budget."""
from __future__ import annotations

import argparse
import glob
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
LR = {"qwen25_7b": "3e-04"}
ORDER = [f"{a}_s{s}" for s in (0, 1, 2) for a in ("T", "R", "N")]
PLAIN_STEP = "targeted plain select3"


def recs(model):
  out = []
  for p in sorted(glob.glob(os.path.join(ROOT, "runs", "haggling", model, "*.json"))):
    r = json.load(open(p)); r["_path"] = p; out.append(r)
  return out


def plain_select3(model):
  have = [r for r in recs(model) if r.get("split") == "select3" and r.get("solver") == "plain" and (r.get("config") or {}).get("step") == PLAIN_STEP]
  if have:
    return have[0]["_path"]
  from harness import modelspec
  from harness.evaluate import evaluate
  from harness.solvers.hf import Backend, PlainSolver
  from harness.tasks.haggling3 import Haggling3Task
  spec = modelspec.load(model)
  rec = evaluate(Haggling3Task(), PlainSolver(Backend(spec)), "select3", 0, spec, {"step": PLAIN_STEP}, planted=False)
  print("plain select3:", rec["_written_to"], flush=True)
  return rec["_written_to"]


def done(model, key):
  arm, s = key.split("_s")
  solver = f"lora:claude_examples_n150_{arm}_lr{LR[model]}"
  return any(r.get("split") == "tune" and r.get("solver") == solver and r.get("seed") == int(s) for r in recs(model))


def gpu_h(model):
  return sum((r.get("timing") or {}).get("gpu_seconds", 0) or 0 for r in recs(model)
             if "_n150_" in (r.get("solver") or "") or (r.get("config") or {}).get("step") in (PLAIN_STEP, "targeted failure map")) / 3600


def main(argv=None):
  ap = argparse.ArgumentParser(); ap.add_argument("--model", default="qwen25_7b"); ap.add_argument("--budget-stop-h", type=float, default=4.5)
  a = ap.parse_args(argv)
  dr = os.path.join(ROOT, "demo", "gen", f"targeted_draws_{a.model}.json"); lb = os.path.join(ROOT, "demo", "gen", f"targeted_labels_{a.model}.json")
  for f in (dr, lb):
    if subprocess.run(["git", "ls-files", "--error-unmatch", f], cwd=ROOT, capture_output=True).returncode or \
       subprocess.run(["git", "diff", "--quiet", "HEAD", "--", f], cwd=ROOT).returncode:
      raise SystemExit(f"{f} must be committed and unmodified before training")
  plain = os.path.relpath(plain_select3(a.model), ROOT)
  for key in ORDER:
    if done(a.model, key):
      print(key, "already trained"); continue
    if gpu_h(a.model) >= a.budget_stop_h:
      raise SystemExit(f"budget stop: {gpu_h(a.model):.2f} GPU-h in this experiment's records")
    cmd = [sys.executable, "-m", "harness.train_lora", "--model", a.model, "--arm", "claude_examples", "--n-cells", "150", "--max-steps", "750",
           "--lr", LR[a.model], "--seed", key.split("_s")[1], "--select", "select3", "--extra-draws", dr, "--extra-key", key,
           "--extra-labels", lb, "--plain-select-record", plain]
    print("RUN", key, flush=True)
    r = subprocess.run(cmd, cwd=ROOT)
    print(f"RUN {key} exit {r.returncode}", flush=True)       # a failed run is reported, never rerun
  print("TARGETED TRAINING DONE", flush=True)


if __name__ == "__main__":
  main()
