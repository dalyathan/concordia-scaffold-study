"""Chain for the worked-examples arms (GEN_EXAMPLES_PLAN.md). One process per run, resumable, budget 5 GPU-hours (measured).
  python demo/gen_examples_chain.py --plan | python demo/gen_examples_chain.py
Order: claude_examples lr 1e-4 s0, lr 3e-4 s0 -> choose lr on selection set B -> cheapest_label s0 -> claude_examples s1, s2 -> shuffled_claude s0."""
import argparse, glob, hashlib, json, os, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import common
import gen_cases as g

FROZEN = "0b6f0febaa1d32302bf275bab823893db481d0386e1eccb36e52a1cbb7f95839"
GRID = (1e-4, 3e-4)
DEFAULT = 2400
OUT = os.path.join(common.ROOT, "demo_out", "gen_lora")
ARMS = ("claude_examples", "cheapest_label", "shuffled_claude")
ap = argparse.ArgumentParser(); ap.add_argument("--plan", action="store_true"); ap.add_argument("--budget-hours", type=float, default=5.0)
args = ap.parse_args()
rid = lambda a, lr, s: f"gen_{a}_lr{lr:.0e}_s{s}"
path = lambda a, lr, s: os.path.join(OUT, rid(a, lr, s) + ".json")
done = lambda a, lr, s: os.path.exists(path(a, lr, s))
res = lambda a, lr, s: json.load(open(path(a, lr, s)))
STATUS = os.path.join(g.OUT, "gen_examples_chain_status.json")
t0 = time.time()


def mean_wall():
  v = [json.load(open(f))["wall_s"] for a in ARMS for f in glob.glob(os.path.join(OUT, f"gen_{a}_*_s?.json"))]
  return float(np.mean(v)) if v else DEFAULT


def spent():
  return sum(json.load(open(f))["wall_s"] for a in ARMS for f in glob.glob(os.path.join(OUT, f"gen_{a}_*_s?.json"))) / 3600


def run(a, lr, s):
  if done(a, lr, s):
    return
  est = mean_wall() / 3600
  if max(spent(), (time.time() - t0) / 3600) + est > args.budget_hours:
    print(f"BUDGET GUARD: {spent():.2f} h spent + {est:.2f} h estimated > {args.budget_hours} h; skipping {rid(a, lr, s)} and everything after it", flush=True)
    json.dump({"outcome": f"BUDGET GUARD: stopped before {rid(a, lr, s)}"}, open(STATUS, "w"))
    print("EXAMPLES CHAIN DONE (BUDGET STOP: later runs were not run)", flush=True)
    sys.exit(0)
  log = os.path.join(common.ROOT, "logs", f"gen_{a}_lr{lr:.0e}_s{s}.log")
  with open(log, "w") as f:
    rc = subprocess.run([sys.executable, "demo/gen_lora.py", "--arm", a, "--lr", str(lr), "--seed", str(s)], stdout=f, stderr=subprocess.STDOUT, cwd=common.ROOT).returncode
  if rc != 0 or not done(a, lr, s):
    print(f"failed: {rid(a, lr, s)} (exit {rc}); see {log}", flush=True)
    sys.exit(1)
  subprocess.run([sys.executable, "demo/ledger.py"], cwd=common.ROOT, check=False)
  g_ = ["git", "-c", "credential.helper=", "-c", "credential.helper=!gh auth git-credential"]
  subprocess.run(["git", "add", "demo_out/gen_lora", "demo_out/lora_progress.jsonl", "RESULTS_LEDGER.md", "demo_out/ledger.json", "demo/gen"], cwd=common.ROOT)
  subprocess.run(["git", "commit", "-qm", f"gen examples run {rid(a, lr, s)}\n\nCo-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01SjA2UwPwxQicQ6boGHZXU2"], cwd=common.ROOT)
  subprocess.run(g_ + ["pull", "-q", "--rebase", "--autostash", "origin", "demo"], cwd=common.ROOT)
  subprocess.run(g_ + ["push", "-q", "origin", "demo"], cwd=common.ROOT)
  print(f"[done] {rid(a, lr, s)} ({spent():.2f} h in this chain)", flush=True)


if args.plan:
  print(f"6 runs x {mean_wall():.0f} s = {6 * mean_wall() / 3600:.1f} GPU-hours (budget {args.budget_hours})")
  sys.exit(0)
assert hashlib.sha256(open(os.path.join(g.OUT, "claude_labels.json"), "rb").read()).hexdigest() == FROZEN, "claude_labels.json changed"
for lr in GRID:
  run("claude_examples", lr, 0)
if all(res("claude_examples", lr, 0)["best_epoch_is_zero"] for lr in GRID):
  print("STOP: both claude_examples runs kept epoch 0 (nothing learned); halting", flush=True)
  print("EXAMPLES CHAIN DONE", flush=True)
  sys.exit(0)
sel = {lr: res("claude_examples", lr, 0)["select_best"]["soft_regret"] for lr in GRID}
lr = min(sel, key=lambda k: (sel[k], k))
print(f"CHOSEN claude_examples lr {lr:.0e} (selection set: {sel})", flush=True)
run("cheapest_label", lr, 0)
for s in (1, 2):
  run("claude_examples", lr, s)
run("shuffled_claude", lr, 0)
print("EXAMPLES CHAIN DONE", flush=True)
