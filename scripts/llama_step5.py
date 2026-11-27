"""Step 5 driver (GPU, tune only for the verdict): the LoRA runs of LLAMA_PLAN.md in order, the lr rule in code, the 8 GPU-hour stop.

  HF_HUB_OFFLINE=1 CUBLAS_WORKSPACE_CONFIG=:4096:8 HARNESS_PROVIDER=runpod HARNESS_GPU_USD_PER_HOUR=0.60 \
    PYTHONPATH=concordia:. .venv/bin/python scripts/llama_step5.py
Needs the step-4 plain train record (epoch-0 check). Each run is a separate process (one adapter per process). A run whose tune record
already exists is skipped, so the driver can be restarted. Stops before a new run when the Llama records' GPU time reaches 8 h."""
import glob, json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNS = os.path.join(ROOT, "runs", "haggling", "llama31_8b")
BUDGET_STOP_H = 8.0


def recs():
  return [json.load(open(p)) for p in sorted(glob.glob(os.path.join(RUNS, "*.json")))]


def plain_train():
  r = [p for p in sorted(glob.glob(os.path.join(RUNS, "*.json"))) if json.load(open(p))["solver"] == "plain" and json.load(open(p))["split"] == "train"]
  if len(r) != 1:
    sys.exit(f"need exactly one plain train record, found {len(r)}")
  return r[0]


def gpu_hours():
  return sum((r.get("timing") or {}).get("gpu_seconds") or 0 for r in recs()) / 3600


def done(arm, n, lr, seed):
  return any(r["solver"] == f"lora:{arm}_n{n}_lr{lr:.0e}" and r["seed"] == seed and r["split"] == "tune" for r in recs())


def run(arm, n, lr, seed):
  if done(arm, n, lr, seed):
    print("skip (record exists):", arm, n, lr, seed, flush=True); return
  if gpu_hours() >= BUDGET_STOP_H:
    sys.exit(f"budget stop: {gpu_hours():.2f} GPU-h in the records (>= {BUDGET_STOP_H})")
  cmd = [sys.executable, "-m", "harness.train_lora", "--model", "llama31_8b", "--arm", arm, "--n-cells", str(n), "--lr", str(lr),
         "--seed", str(seed), "--plain-train-record", plain_train()]
  print("RUN", " ".join(cmd[2:]), flush=True)
  subprocess.run(cmd, cwd=ROOT, check=True)


def select_b(lr):
  r = [x for x in recs() if x["solver"] == f"lora:claude_examples_n100_lr{lr:.0e}" and x["seed"] == 0 and x["split"] == "tune"]
  return r[0]["config"]["training"]["select_B_best_soft_regret"]


def main():
  run("claude_examples", 100, 1e-4, 0)
  run("claude_examples", 100, 3e-4, 0)
  s1, s3 = select_b(1e-4), select_b(3e-4)
  lr = 3e-4 if s3 < s1 - 0.005 else 1e-4          # frozen rule (LLAMA_PLAN.md): lower select_B; ties within 0.005 -> 1e-4
  print(f"lr choice: select_B {s1:.4f} at 1e-4, {s3:.4f} at 3e-4 -> {lr:.0e}", flush=True)
  for arm, n, seed in (("claude_examples", 100, 1), ("claude_examples", 100, 2), ("claude_examples", 25, 0),
                       ("cheapest_label", 25, 0), ("cheapest_label", 100, 0), ("shuffled_claude", 100, 0)):
    run(arm, n, lr, seed)
  print(f"step 5 done; {gpu_hours():.2f} GPU-h in the records", flush=True)


if __name__ == "__main__":
  main()
