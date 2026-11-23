"""Chain for the learning-curve runs (GEN_CURVE_PLAN.md). One process per run, resumable, budget 8 GPU-hours (measured).
  python demo/gen_curve_chain.py --plan | python demo/gen_curve_chain.py
Order (a cut falls on the last runs first): examples-25 s0, examples-10 s0, rule-soft-25, rule-hard-25, rule-hard-100, cheapest-label-25,
examples-25 s1-2, examples-10 s1-2, examples-50 s0-2. All at lr 1e-4. N = 100 examples and rule-soft runs already exist and are reused."""
import argparse, glob, hashlib, json, os, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import common
import gen_cases as g
import gen_curve

FROZEN = "0b6f0febaa1d32302bf275bab823893db481d0386e1eccb36e52a1cbb7f95839"
LR, DEFAULT = 1e-4, 2100
OUT = os.path.join(common.ROOT, "demo_out", "gen_lora")
RUNS = [("claude_examples", 25, 0), ("claude_examples", 10, 0), ("teacher", 25, 0), ("rule_hard", 25, 0), ("rule_hard", 100, 0), ("cheapest_label", 25, 0),
        ("claude_examples", 25, 1), ("claude_examples", 25, 2), ("claude_examples", 10, 1), ("claude_examples", 10, 2),
        ("claude_examples", 50, 0), ("claude_examples", 50, 1), ("claude_examples", 50, 2)]
ap = argparse.ArgumentParser(); ap.add_argument("--plan", action="store_true"); ap.add_argument("--budget-hours", type=float, default=8.0)
args = ap.parse_args()
rid = lambda a, n, s: f"gen_{a}_lr{LR:.0e}_s{s}" if n == 100 else f"gen_{a}_n{n}_lr{LR:.0e}_s{s}"
path = lambda a, n, s: os.path.join(OUT, rid(a, n, s) + ".json")
STATUS = os.path.join(g.OUT, "gen_curve_chain_status.json")
t0 = time.time()
mine = lambda: [path(*r) for r in RUNS if os.path.exists(path(*r))]


def mean_wall():
  v = [json.load(open(f))["wall_s"] for f in mine()]
  return float(np.mean(v)) if v else DEFAULT


def spent():
  return sum(json.load(open(f))["wall_s"] for f in mine()) / 3600


def run(a, n, s):
  if os.path.exists(path(a, n, s)):
    return
  est = mean_wall() / 3600
  if max(spent(), (time.time() - t0) / 3600) + est > args.budget_hours:
    left = [rid(*r) for r in RUNS if not os.path.exists(path(*r))]
    print(f"BUDGET GUARD: {spent():.2f} h spent + {est:.2f} h estimated > {args.budget_hours} h; NOT RUN: {left}", flush=True)
    json.dump({"outcome": "BUDGET GUARD", "not_run": left}, open(STATUS, "w"))
    print("CURVE CHAIN DONE (BUDGET STOP: later runs were not run)", flush=True)
    sys.exit(0)
  log = os.path.join(common.ROOT, "logs", rid(a, n, s) + ".log")
  with open(log, "w") as f:
    rc = subprocess.run([sys.executable, "demo/gen_lora.py", "--arm", a, "--lr", str(LR), "--seed", str(s), "--n-cells", str(n)], stdout=f, stderr=subprocess.STDOUT, cwd=common.ROOT).returncode
  if rc != 0 or not os.path.exists(path(a, n, s)):
    print(f"failed: {rid(a, n, s)} (exit {rc}); see {log}", flush=True)
    sys.exit(1)
  subprocess.run([sys.executable, "demo/ledger.py"], cwd=common.ROOT, check=False)
  g_ = ["git", "-c", "credential.helper=", "-c", "credential.helper=!gh auth git-credential"]
  subprocess.run(["git", "add", "demo_out/gen_lora", "demo_out/lora_progress.jsonl", "RESULTS_LEDGER.md", "demo_out/ledger.json", "demo/gen"], cwd=common.ROOT)
  subprocess.run(["git", "commit", "-qm", f"gen curve run {rid(a, n, s)}\n\nCo-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01SjA2UwPwxQicQ6boGHZXU2"], cwd=common.ROOT)
  subprocess.run(g_ + ["pull", "-q", "--rebase", "--autostash", "origin", "demo"], cwd=common.ROOT)
  subprocess.run(g_ + ["push", "-q", "origin", "demo"], cwd=common.ROOT)
  print(f"[done] {rid(a, n, s)} ({spent():.2f} h in this chain)", flush=True)


if args.plan:
  todo = [r for r in RUNS if not os.path.exists(path(*r))]
  print(f"{len(todo)} runs to do x {mean_wall():.0f} s = {len(todo) * mean_wall() / 3600:.1f} GPU-hours (budget {args.budget_hours})")
  sys.exit(0)
assert hashlib.sha256(open(os.path.join(g.OUT, "claude_labels.json"), "rb").read()).hexdigest() == FROZEN, "claude_labels.json changed"
gen_curve.load(10)                                           # asserts curve_subsets.json equals its rebuild
for a, n, s in RUNS:
  run(a, n, s)
print("CURVE CHAIN DONE", flush=True)
