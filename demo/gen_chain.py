"""Chain for the generated-dataset LoRA arms (one process per run, never two models at once, resumable).
  python demo/gen_chain.py --plan | python demo/gen_chain.py
Budget (--budget-hours, default 8): runs x (epochs per run x measured s/epoch + load/target/eval allowance). Reduction ladder, first plan that fits:
  L0 lr grid {1e-4, 3e-4, 1e-3} at seed 0 for teacher, method_original, neutral, wrong_rule, answer_only; seeds 1-2 for the four distil arms
  L1 neutral, wrong_rule and answer_only run only at the teacher's chosen lr (no grid)
  L2 method_original also only at the teacher's chosen lr
  L3 neutral and wrong_rule get seeds 0-1 only (teacher and method_original keep 3 seeds)
  L4 method_original gets seeds 0-1 only
Order of work: teacher grid; method_original, neutral, wrong_rule, answer_only at seed 0; teacher seeds 1-2; method_original seeds; control seeds."""
import argparse, glob, json, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import common

LR_GRID = (1e-4, 3e-4, 1e-3)
EPOCHS_PER_RUN, OVERHEAD_SEC, DEFAULT_SEC_EPOCH = 4.5, 360, 400
OUT = os.path.join(common.ROOT, "demo_out", "gen_lora")
LOGS = os.path.join(common.ROOT, "logs")
ap = argparse.ArgumentParser()
ap.add_argument("--plan", action="store_true")
ap.add_argument("--budget-hours", type=float, default=8.0)
args = ap.parse_args()
rid = lambda arm, lr, s: f"gen_{arm}_lr{lr:.0e}_s{s}"
path = lambda arm, lr, s: os.path.join(OUT, rid(arm, lr, s) + ".json")
done = lambda arm, lr, s: os.path.exists(path(arm, lr, s))
res = lambda arm, lr, s: json.load(open(path(arm, lr, s)))


def sec_epoch():
  v = [json.load(open(f))["sec_per_epoch"] for f in glob.glob(os.path.join(OUT, "*_s?.json")) if "_smoke" not in f]
  v = [x for x in v if x]
  return float(np.mean(v)) if v else DEFAULT_SEC_EPOCH


def chosen_lr(arm):
  vals = {}
  for lr in LR_GRID:
    if not done(arm, lr, 0):
      raise SystemExit(f"cannot choose a learning rate for {arm}: {lr:.0e} missing")
    vals[lr] = res(arm, lr, 0)["tune_monitor_best"]["soft_regret"]
  return min(vals, key=lambda k: (vals[k], k))


def plan_for(level, lr_t=None):
  """-> ordered list of (arm, lr, seed); lr_t = teacher's chosen lr (placeholder 3e-4 before it is known)"""
  lr_t = lr_t or 3e-4
  P = [("teacher", lr, 0) for lr in LR_GRID]
  grid_arms = ("method_original", "neutral", "wrong_rule", "answer_only")
  for a in grid_arms:
    lrs = LR_GRID if (level == 0 or (level == 1 and a == "method_original")) and a != "answer_only" or (level == 0 and a == "answer_only") else (lr_t,)
    P += [(a, lr, 0) for lr in lrs]
  P += [("teacher", lr_t, s) for s in (1, 2)]
  P += [("method_original", lr_t if level >= 1 and False else lr_t, s) for s in ((1, 2) if level < 4 else (1,))]
  ctrl_seeds = (1, 2) if level < 3 else (1,)
  P += [(a, lr_t, s) for a in ("neutral", "wrong_rule") for s in ctrl_seeds]
  seen, out = set(), []
  for r in P:
    if r not in seen:
      seen.add(r); out.append(r)
  return out


LADDER = ("L0 full", "L1 controls and ceiling at teacher's lr only", "L2 method_original at teacher's lr only too", "L3 controls 2 seeds", "L4 method_original 2 seeds")


def choose(sec, lr_t=None):
  for level, name in enumerate(LADDER):
    P = plan_for(level, lr_t)
    est = len(P) * (EPOCHS_PER_RUN * sec + OVERHEAD_SEC) / 3600
    print(f"plan {name}: {len(P)} runs, about {est:.1f} GPU-hours at {sec:.0f} s/epoch", flush=True)
    if est <= args.budget_hours:
      return level, name, P, est
  return None


def launch(arm, lr, seed):
  if done(arm, lr, seed):
    return
  with open(os.path.join(LOGS, f"gen_{arm}_lr{lr:.0e}_s{seed}.log"), "w") as f:
    rc = subprocess.run([sys.executable, "demo/gen_lora.py", "--arm", arm, "--lr", str(lr), "--seed", str(seed)], stdout=f, stderr=subprocess.STDOUT, cwd=common.ROOT).returncode
  if rc != 0 or not done(arm, lr, seed):
    raise SystemExit(f"run {rid(arm, lr, seed)} failed (exit {rc})")
  subprocess.run(["git", "add", path(arm, lr, seed)], cwd=common.ROOT)
  subprocess.run(["git", "commit", "-q", "-m", f"gen lora run {rid(arm, lr, seed)}", "-m", "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01SjA2UwPwxQicQ6boGHZXU2"], cwd=common.ROOT)
  g = ["git", "-c", "credential.helper=", "-c", "credential.helper=!gh auth git-credential"]
  if subprocess.run(g + ["push", "-q", "origin", "demo"], cwd=common.ROOT).returncode != 0:
    subprocess.run(g + ["pull", "-q", "--rebase", "--autostash", "origin", "demo"], cwd=common.ROOT)
    subprocess.run(g + ["push", "-q", "origin", "demo"], cwd=common.ROOT)
  print(f"[done] {rid(arm, lr, seed)}", flush=True)


plan = choose(sec_epoch())
if args.plan:
  print("chosen:", plan[1] if plan else "none fits")
  sys.exit(0)
if plan is None:
  raise SystemExit("no plan on the ladder fits the budget")
level = plan[0]
for lr in LR_GRID:
  launch("teacher", lr, 0)
lr_t = chosen_lr("teacher")
plan = choose(sec_epoch(), lr_t)
if plan is None:
  raise SystemExit("BUDGET: no plan fits after the teacher grid; halted")
print(f"CHOSEN {plan[1]} (teacher lr {lr_t:.0e}, estimate {plan[3]:.1f} h)", flush=True)
for arm, lr, seed in plan[2]:
  launch(arm, lr, seed)
print("GEN CHAIN DONE", flush=True)
