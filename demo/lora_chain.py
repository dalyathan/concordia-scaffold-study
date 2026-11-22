"""LoRA chain driver (one process per run, never two models at once; resumable).

  python demo/lora_chain.py --plan     print the budget plans and the chosen one
  python demo/lora_chain.py            run the chain

Gates before anything starts: demo_out/lora_checks.json must show checks 1-3 passed
and the adapter-cache unit test must pass.

Order: 0 trainability check (answer_only, lr 3e-4); then method and neutral, then
wrong_rule, answer_only (other rates), shuffled, then the optional arms, then the
extra seeds.
Trainability check: passes if the MINIMUM train-cell soft regret over the run's
epochs is below 0.15 (plain on the train cells 0.778). If it fails, the pre-declared
fallback (lr 1e-3, rank 16) runs once; if that also fails the chain HALTS and the
outcome is "undertrained" (written to demo/lora_status.json).

Budget (10 GPU-hours, --budget-hours). The estimate is runs x epochs-per-run x
seconds-per-epoch, with seconds per epoch MEASURED from finished runs (default 330
until one finishes), 6.5 epochs per run, and a 3-minute allowance per run for model
loading and teacher scoring. Pre-declared reduction ladder, first plan that fits:
  L0 full: lr grid {1e-4, 3e-4, 1e-3} for method, neutral, wrong_rule, answer_only,
     shuffled x 3 derangements, const2, template; seeds 1-2 for method, neutral,
     wrong_rule
  L1 controls (neutral, wrong_rule) get 1 seed
  L2 drop the const2 TRAINING arm (always-2, computed from the labels, remains a
     required comparator)
  L3 drop template
  L4 shuffled: 1 derangement
  L5 wrong_rule, answer_only and shuffled run only at the rate chosen for method
If no plan fits the chain refuses to run."""
import argparse, glob, json, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import common

LR_GRID = (1e-4, 3e-4, 1e-3)
EPOCHS_PER_RUN, LOAD_SEC = 6.5, 180
LORA_DIR = os.path.join(common.ROOT, "demo_out", "lora")
LOGS = os.path.join(common.ROOT, "logs")
ap = argparse.ArgumentParser()
ap.add_argument("--plan", action="store_true")
ap.add_argument("--budget-hours", type=float, default=10.0)
args = ap.parse_args()


def rid(arm, perm, lr, seed, rank=4):
  return f"{arm}{perm if arm == 'shuffled' else ''}_lr{lr:.0e}_s{seed}" + (f"_r{rank}" if rank != 4 else "")


def path(arm, perm, lr, seed, rank=4):
  return os.path.join(LORA_DIR, rid(arm, perm, lr, seed, rank) + ".json")


def done(*a, **k):
  return os.path.exists(path(*a, **k))


def result(*a, **k):
  return json.load(open(path(*a, **k)))


def measured_sec_per_epoch():
  secs = [json.load(open(f))["sec_per_epoch"] for f in glob.glob(os.path.join(LORA_DIR, "*.json"))
          if not f.endswith("_smoke.json") and "teacher_" not in f]
  secs = [s for s in secs if s]
  return float(np.mean(secs)) if secs else 330.0


def chosen_lr(arm):
  """Lowest best held-out soft regret over the complete grid (seed 0); an incomplete
  grid is an error, not a default."""
  vals = {}
  for lr in LR_GRID:
    if not done(arm, 0, lr, 0):
      raise SystemExit(f"cannot choose a learning rate for {arm}: run at lr {lr:.0e} is missing")
    vals[lr] = result(arm, 0, lr, 0)["tune_best"]["soft_regret"]
  return min(vals, key=lambda k: (vals[k], k))


LADDER = ("L0 full", "L1 controls 1 seed", "L2 no const2 arm", "L3 no template", "L4 one shuffled",
          "L5 non-core arms at method's rate only")


def runs_for(level, method_lr=None):
  """-> (grid runs [(arm, perm, lr, seed)], seed runs [(arm, seed)])"""
  # L5: one rate for the non-core arms (method's rate once known; priced as one placeholder rate before)
  rates = lambda arm: LR_GRID if level < 5 else ((method_lr,) if method_lr is not None else (3e-4,))
  runs = [("answer_only", 0, 3e-4, 0)]
  runs += [(a, 0, lr, 0) for a in ("method", "neutral") for lr in LR_GRID]
  runs += [("wrong_rule", 0, lr, 0) for lr in rates("wrong_rule")]
  runs += [("answer_only", 0, lr, 0) for lr in rates("answer_only") if lr != 3e-4]
  perms = (0, 1, 2) if level < 4 else (0,)
  runs += [("shuffled", k, lr, 0) for k in perms for lr in rates("shuffled")]
  if level < 2:
    runs += [("const2", 0, lr, 0) for lr in LR_GRID]
  if level < 3:
    runs += [("template", 0, lr, 0) for lr in LR_GRID]
  seeds = [("method", s) for s in (1, 2)]
  if level < 1:
    seeds += [(a, s) for a in ("neutral", "wrong_rule") for s in (1, 2)]
  return runs, seeds


def hours(n, sec):
  return n * (EPOCHS_PER_RUN * sec + LOAD_SEC) / 3600


def choose_plan(sec, method_lr=None):
  for level, name in enumerate(LADDER):
    runs, seeds = runs_for(level, method_lr)
    pending = [r for r in runs if not done(*r)] + [s for s in seeds if not done(s[0], 0, 3e-4, s[1])]
    est = hours(len(runs) + len(seeds), sec)
    print(f"plan {name}: {len(runs)} grid + {len(seeds)} seed runs = {len(runs) + len(seeds)} runs, "
          f"about {est:.1f} GPU-hours at {sec:.0f} s/epoch", flush=True)
    if est <= args.budget_hours:
      return level, name, runs, seeds, est
  return None


def gates():
  ck = os.path.join(common.ROOT, "demo_out", "lora_checks.json")
  if not os.path.exists(ck):
    raise SystemExit("refusing to start: demo_out/lora_checks.json is missing (run lora_checks.py)")
  c = json.load(open(ck))
  ok = (c.get("check1_epoch0", {}).get("pass") and c.get("check1_trained", {}).get("pass")
        and c.get("check2", {}).get("pass") and c.get("check3", {}).get("pass"))
  if not ok:
    raise SystemExit(f"refusing to start: LoRA safety checks did not all pass: {json.dumps({k: c.get(k) for k in ('check1_epoch0', 'check1_trained', 'check2', 'check3')})[:400]}")
  r = subprocess.run([sys.executable, "-m", "pytest", "-q", "tests/test_demo_tools.py", "-k", "cache_is_keyed_by_adapter"],
                     cwd=common.ROOT, capture_output=True, text=True,
                     env=dict(os.environ, PYTHONPATH=os.pathsep.join([os.path.join(common.ROOT, "concordia"), common.ROOT])))
  if r.returncode != 0:
    raise SystemExit("refusing to start: the adapter-keyed cache test failed\n" + r.stdout[-500:])


def launch(arm, perm, lr, seed, rank=4):
  if done(arm, perm, lr, seed, rank):
    return
  cmd = [sys.executable, "demo/lora.py", "--arm", arm, "--perm", str(perm), "--lr", str(lr), "--seed", str(seed),
         "--rank", str(rank)]
  with open(os.path.join(LOGS, f"demo_lora_{rid(arm, perm, lr, seed, rank)}.log"), "w") as f:
    rc = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, cwd=common.ROOT).returncode
  if rc != 0 or not done(arm, perm, lr, seed, rank):
    raise SystemExit(f"run {rid(arm, perm, lr, seed, rank)} failed (exit {rc}); see logs/demo_lora_{rid(arm, perm, lr, seed, rank)}.log")
  subprocess.run([sys.executable, "demo/ledger.py"], cwd=common.ROOT, check=False)          # ledger after every run
  print(f"[done] {rid(arm, perm, lr, seed, rank)}", flush=True)


plan = choose_plan(measured_sec_per_epoch())
if args.plan:
  print("PROVISIONAL" if not glob.glob(os.path.join(LORA_DIR, "*_s0.json")) else "MEASURED",
        "plan:", plan[1] if plan else "none fits", flush=True)
  sys.exit(0)
if plan is None:
  # The epoch time is not measured yet: the placeholder may be pessimistic. Only the
  # trainability run (needed in every plan) is allowed before the plan is checked
  # against the budget with a measured time.
  if glob.glob(os.path.join(LORA_DIR, "*.json")):
    raise SystemExit("refusing to run: no plan on the reduction ladder fits the budget")
  print("no plan fits at the placeholder epoch time; running the trainability check to measure it", flush=True)

gates()
status_path = os.path.join(common.ROOT, "demo", "lora_status.json")
status = json.load(open(status_path)) if os.path.exists(status_path) else {}
def save_status(): json.dump(status, open(status_path, "w"), indent=1)

# 0: trainability check
launch("answer_only", 0, 3e-4, 0)
tr0 = result("answer_only", 0, 3e-4, 0)["train_min_soft_regret"]
status["trainability"] = {"min_train_soft_regret": tr0, "threshold": 0.15, "pass": tr0 < 0.15}
if tr0 >= 0.15:
  launch("answer_only", 0, 1e-3, 0, rank=16)
  fb = result("answer_only", 0, 1e-3, 0, rank=16)["train_min_soft_regret"]
  status["trainability"]["fallback"] = {"run": "answer_only lr 1e-3 rank 16", "min_train_soft_regret": fb, "pass": fb < 0.15}
  if fb >= 0.15:
    status["outcome"] = "UNDERTRAINED: answer_only did not fit the train cells at either setting; chain halted"
    save_status()
    raise SystemExit(status["outcome"])
save_status()

# re-plan with the measured epoch time before spending more GPU time
plan = choose_plan(measured_sec_per_epoch())
if plan is None:
  status["outcome"] = (f"BUDGET: no plan on the reduction ladder fits {args.budget_hours} h at the measured "
                       f"{measured_sec_per_epoch():.0f} s/epoch; chain halted after the trainability run")
  save_status()
  raise SystemExit(status["outcome"])
print(f"provisional choice with measured time: {plan[1]} ({plan[4]:.1f} h)", flush=True)
for arm in ("method", "neutral"):
  for lr in LR_GRID:
    launch(arm, 0, lr, 0)
method_lr = chosen_lr("method")
plan = choose_plan(measured_sec_per_epoch(), method_lr)
if plan is None:
  status["outcome"] = "BUDGET: no plan fits after the method and neutral grids; chain halted"
  save_status()
  raise SystemExit(status["outcome"])
status["plan"] = {"level": plan[1], "estimate_hours": plan[4], "method_lr": method_lr}
save_status()
print(f"CHOSEN after measuring: {plan[1]} (estimate {plan[4]:.1f} h)", flush=True)
runs, seeds = plan[2], plan[3]
for arm, perm, lr, seed in runs:
  launch(arm, perm, lr, seed)
for arm, seed in seeds:
  # extra seeds at the arm's chosen rate (its grid is complete by now, or it ran at method's rate only)
  lr = chosen_lr(arm) if all(done(arm, 0, g, 0) for g in LR_GRID) else method_lr
  launch(arm, 0, lr, seed)
print("LORA CHAIN DONE", flush=True)
