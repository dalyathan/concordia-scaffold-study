"""LoRA chain driver: plans the runs, estimates GPU time, applies the reduction rules,
and runs them one process at a time (never two models). Resumable: a run whose
result file exists is skipped.

Order (priority):
  0 trainability check: answer_only at lr 3e-4. Passes if its best-epoch train-cell
    soft regret is below 0.15 (plain on the train cells: 0.778). If not, the
    pre-declared fallback is run once (lr 1e-3, rank 16) and the outcome logged.
  1 method and neutral (matched control), lr grid {1e-4, 3e-4, 1e-3}
  2 wrong_rule; answer_only (remaining lrs); shuffled x 3 derangements
  3 const2; template (leaky upper bound)
  4 seeds 1 and 2 at each arm's chosen lr (lowest best held-out tune soft regret)
    for method, neutral and wrong_rule
Reduction rule (message of 2026-11-22): if the estimate exceeds 10 GPU-hours, the
controls get 1 seed, then const2 is dropped, then template. The estimate uses the
measured seconds per epoch (--sec-per-epoch) and 6.5 epochs per run.

  python demo/lora_chain.py --plan      print the estimate and the plan
  python demo/lora_chain.py             run it"""
import argparse, glob, json, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

LR_GRID = (1e-4, 3e-4, 1e-3)
EPOCHS_PER_RUN = 6.5
LORA_DIR = os.path.join(common.ROOT, "demo_out", "lora")
ap = argparse.ArgumentParser()
ap.add_argument("--plan", action="store_true")
ap.add_argument("--sec-per-epoch", type=float, default=330.0)
ap.add_argument("--budget-hours", type=float, default=10.0)
args = ap.parse_args()


def rid(arm, perm, lr, seed):
  return f"{arm}{perm if arm == 'shuffled' else ''}_lr{lr:g}_s{seed}"


def done(arm, perm, lr, seed):
  return os.path.exists(os.path.join(LORA_DIR, rid(arm, perm, lr, seed) + ".json"))


def result(arm, perm, lr, seed):
  return json.load(open(os.path.join(LORA_DIR, rid(arm, perm, lr, seed) + ".json")))


def chosen_lr(arm):
  best = None
  for lr in LR_GRID:
    if done(arm, 0, lr, 0):
      r = result(arm, 0, lr, 0)["tune_best"]["soft_regret"]
      if best is None or r < best[0]:
        best = (r, lr)
  return best[1] if best else 3e-4


def plan(drop_const2=False, drop_template=False, control_seeds=1):
  runs = [("answer_only", 0, 3e-4, 0)]                                      # 0: trainability check
  for arm in ("method", "neutral"):
    runs += [(arm, 0, lr, 0) for lr in LR_GRID]
  runs += [("wrong_rule", 0, lr, 0) for lr in LR_GRID]
  runs += [("answer_only", 0, lr, 0) for lr in LR_GRID if lr != 3e-4]
  runs += [("shuffled", k, lr, 0) for k in (0, 1, 2) for lr in LR_GRID]
  if not drop_const2:
    runs += [("const2", 0, lr, 0) for lr in LR_GRID]
  if not drop_template:
    runs += [("template", 0, lr, 0) for lr in LR_GRID]
  seeds = [("method", 1), ("method", 2)] + ([("neutral", s) for s in (1, 2)] + [("wrong_rule", s) for s in (1, 2)]
                                           if control_seeds >= 3 else [])
  return runs, seeds


def hours(n_runs):
  return n_runs * EPOCHS_PER_RUN * args.sec_per_epoch / 3600


variants = [("full", dict()), ("controls 1 seed", dict(control_seeds=1)),
            ("controls 1 seed, no const2", dict(control_seeds=1, drop_const2=True)),
            ("controls 1 seed, no const2, no template", dict(control_seeds=1, drop_const2=True, drop_template=True))]
chosen = None
for name, kw in variants:
  kw2 = dict(kw)
  kw2.setdefault("control_seeds", 3)
  runs, seeds = plan(**kw2)
  est = hours(len(runs) + len(seeds))
  print(f"plan '{name}': {len(runs)} grid runs + {len(seeds)} extra-seed runs = {len(runs) + len(seeds)} runs, "
        f"about {est:.1f} GPU-hours at {args.sec_per_epoch:.0f} s/epoch", flush=True)
  if chosen is None and est <= args.budget_hours:
    chosen = (name, kw2, runs, seeds, est)
if chosen is None:
  chosen = (name, kw2, runs, seeds, est)
print(f"CHOSEN plan: '{chosen[0]}' (estimate {chosen[4]:.1f} h; budget {args.budget_hours} h)", flush=True)
json.dump({"plan": chosen[0], "estimate_hours": chosen[4], "sec_per_epoch": args.sec_per_epoch,
           "runs": [list(r) for r in chosen[2]], "extra_seeds": [list(s) for s in chosen[3]]},
          open(os.path.join(common.ROOT, "demo", "lora_plan.json"), "w"), indent=1)
if args.plan:
  sys.exit(0)


def launch(arm, perm, lr, seed, rank=4):
  if done(arm, perm, lr, seed) and rank == 4:
    return
  cmd = [sys.executable, "demo/lora.py", "--arm", arm, "--perm", str(perm), "--lr", str(lr), "--seed", str(seed),
         "--rank", str(rank)]
  with open(os.path.join(common.ROOT, "logs", f"demo_lora_{rid(arm, perm, lr, seed)}.log"), "w") as f:
    subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, cwd=common.ROOT)
  subprocess.run([sys.executable, "demo/ledger.py"], cwd=common.ROOT, check=False)          # ledger after every run


runs, seeds = chosen[2], chosen[3]
# 0: trainability check
launch("answer_only", 0, 3e-4, 0)
r0 = result("answer_only", 0, 3e-4, 0)
train_reg = r0["train_best"]["soft_regret"]
status = {"trainability": {"train_soft_regret_best": train_reg, "pass": train_reg < 0.15}}
if train_reg >= 0.15:
  launch("answer_only", 0, 1e-3, 0, rank=16)
  status["trainability"]["fallback_run"] = "answer_only lr 1e-3 rank 16"
json.dump(status, open(os.path.join(common.ROOT, "demo", "lora_status.json"), "w"), indent=1)
for arm, perm, lr, seed in runs[1:]:
  launch(arm, perm, lr, seed)
for arm, seed in seeds:
  launch(arm, 0, chosen_lr(arm), seed)
print("LORA CHAIN DONE", flush=True)
