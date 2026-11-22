"""Chain for the generated-dataset LoRA arms (one process per run, never two models at once, resumable).
  python demo/gen_chain.py --plan | python demo/gen_chain.py
Budget (--budget-hours, default 8): the estimate is runs x MEASURED seconds per run (mean wall_s of finished runs; default 2400 s before
any run has finished). Reduction ladder, first plan that fits:
  L0 lr grid {1e-4, 3e-4, 1e-3} at seed 0 for teacher, method_original, neutral, wrong_rule, answer_only; seeds 1-2 for the four distil arms
  L1 neutral, wrong_rule and answer_only run only at the teacher's chosen lr (no grid)
  L2 method_original also only at the teacher's chosen lr
  L3 neutral and wrong_rule get seeds 0-1 only (teacher and method_original keep 3 seeds)
  L4 method_original gets seeds 0-1 only
The lr is chosen on the SELECTION set (train cells outside the training set), never on tune.
Preconditions (checked before any run): in-prompt teacher text beats plain and the neutral text on the selection set (demo_out/gen_text_rows.jsonl).
Order: teacher lr grid; answer_only, neutral, wrong_rule, method_original at seed 0; teacher seeds 1-2; method_original seeds; control seeds.
Stop rules: halt if all three teacher runs keep epoch 0, if answer_only fails to beat plain, if the teacher is not better than neutral on the selection
set after seed 0 of both, and before any run whose estimate would pass the budget (cumulative measured hours)."""
import argparse, glob, json, os, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import common
import gen_cases as g

LR_GRID = (1e-4, 3e-4, 1e-3)
DEFAULT_RUN_SEC = 2400
OUT = os.path.join(common.ROOT, "demo_out", "gen_lora")
LOGS = os.path.join(common.ROOT, "logs")
STATUS = os.path.join(g.OUT, "gen_chain_status.json")
ap = argparse.ArgumentParser()
ap.add_argument("--plan", action="store_true")
ap.add_argument("--budget-hours", type=float, default=8.0)
args = ap.parse_args()
t0 = time.time()
rid = lambda arm, lr, s: f"gen_{arm}_lr{lr:.0e}_s{s}"
path = lambda arm, lr, s: os.path.join(OUT, rid(arm, lr, s) + ".json")
done = lambda arm, lr, s: os.path.exists(path(arm, lr, s))
res = lambda arm, lr, s: json.load(open(path(arm, lr, s)))
sel = lambda arm, lr, s: res(arm, lr, s)["select_best"]["soft_regret"]


def run_sec():
  v = [json.load(open(f))["wall_s"] for f in glob.glob(os.path.join(OUT, "*_s?.json"))]
  return float(np.mean(v)) if v else DEFAULT_RUN_SEC


def chosen_lr(arm):
  vals = {lr: sel(arm, lr, 0) for lr in LR_GRID if done(arm, lr, 0)}
  if len(vals) < len(LR_GRID):
    raise SystemExit(f"cannot choose a learning rate for {arm}: grid incomplete")
  return min(vals, key=lambda k: (vals[k], k))


def plan_for(level, lr_t=None):
  lr_t = lr_t or 3e-4
  P = [("teacher", lr, 0) for lr in LR_GRID]
  full_grid = {"method_original": level <= 1, "neutral": level == 0, "wrong_rule": level == 0, "answer_only": level == 0}
  for a in ("answer_only", "neutral", "wrong_rule", "method_original"):
    P += [(a, lr, 0) for lr in (LR_GRID if full_grid[a] else (lr_t,))]
  P += [("teacher", lr_t, s) for s in (1, 2)]
  P += [("method_original", lr_t, s) for s in ((1, 2) if level < 4 else (1,))]
  cs = (1, 2) if level < 3 else (1,)
  P += [(a, lr_t, s) for a in ("neutral", "wrong_rule") for s in cs]
  seen, out = set(), []
  for r in P:
    if r not in seen:
      seen.add(r); out.append(r)
  return out


LADDER = ("L0 full", "L1 controls and ceiling at teacher's lr only", "L2 method_original at teacher's lr only too", "L3 controls 2 seeds", "L4 method_original 2 seeds")


def choose(lr_t=None):
  sec = run_sec()
  for level, name in enumerate(LADDER):
    P = plan_for(level, lr_t)
    est = len(P) * sec / 3600
    print(f"plan {name}: {len(P)} runs, about {est:.1f} GPU-hours at {sec:.0f} s per run", flush=True)
    if est <= args.budget_hours:
      return level, name, P, est
  return None


def preconditions():
  """in-prompt teacher text must beat plain and neutral text on the selection set (a distilled adapter cannot exceed its teacher)"""
  sel_cells = json.load(open(os.path.join(g.OUT, "lora_select_cells_B.json")))
  cells = {c["cell"]: c for c in json.load(open(os.path.join(g.OUT, "cells.json")))["cells"]}
  rows = [json.loads(l) for l in open(os.path.join(common.ROOT, "demo_out", "gen_text_rows.jsonl"))]
  plain = {r["cid"]: r for r in map(json.loads, open(os.path.join(common.ROOT, "demo_out", "gen_plain_scores.jsonl")))}
  def mean(get, rowname=None):
    v = []
    for k in sel_cells:
      cid = f"{k}-n0"
      r = plain[cid] if rowname is None else next(x for x in rows if x["row"] == rowname and x["cid"] == cid)
      v.append(r["soft_regret"])
    return float(np.mean(v))
  out = {"plain": mean(None), "teacher_text": mean(None, "teacher"), "neutral_text": mean(None, "neutral"), "method_original_text": mean(None, "method_original")}
  out["ok"] = out["teacher_text"] < out["plain"] and out["teacher_text"] < out["neutral_text"]
  return out


def status(**kw):
  s = json.load(open(STATUS)) if os.path.exists(STATUS) else {}
  s.update(kw)
  json.dump(s, open(STATUS, "w"), indent=1)


def launch(arm, lr, seed):
  if done(arm, lr, seed):
    return
  with open(os.path.join(LOGS, f"gen_{arm}_lr{lr:.0e}_s{seed}.log"), "w") as f:
    rc = subprocess.run([sys.executable, "demo/gen_lora.py", "--arm", arm, "--lr", str(lr), "--seed", str(seed)], stdout=f, stderr=subprocess.STDOUT, cwd=common.ROOT).returncode
  if rc != 0 or not done(arm, lr, seed):
    raise SystemExit(f"run {rid(arm, lr, seed)} failed (exit {rc})")
  subprocess.run([sys.executable, "demo/ledger.py"], cwd=common.ROOT)
  subprocess.run(["git", "add", path(arm, lr, seed), "RESULTS_LEDGER.md", "demo_out/ledger.json"], cwd=common.ROOT)
  subprocess.run(["git", "commit", "-q", "-m", f"gen lora run {rid(arm, lr, seed)}", "-m", "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01SjA2UwPwxQicQ6boGHZXU2"], cwd=common.ROOT)
  gg = ["git", "-c", "credential.helper=", "-c", "credential.helper=!gh auth git-credential"]
  if subprocess.run(gg + ["push", "-q", "origin", "demo"], cwd=common.ROOT).returncode != 0:
    subprocess.run(gg + ["pull", "-q", "--rebase", "--autostash", "origin", "demo"], cwd=common.ROOT)
    subprocess.run(gg + ["push", "-q", "origin", "demo"], cwd=common.ROOT)
  print(f"[done] {rid(arm, lr, seed)} ({(time.time() - t0) / 3600:.2f} h in this chain)", flush=True)


def halt(msg):
  status(outcome=msg)
  raise SystemExit(msg)


plan = choose()
if args.plan:
  print("chosen:", plan[1] if plan else "none fits")
  sys.exit(0)
if plan is None:
  halt("BUDGET: no plan fits")
pre = preconditions()
status(preconditions=pre)
print("preconditions", pre, flush=True)
if not pre["ok"]:
  halt("PRECONDITION FAILED: the in-prompt teacher text does not beat plain and neutral text on the selection set; no LoRA run started")
for lr in LR_GRID:
  launch("teacher", lr, 0)
if all(res("teacher", lr, 0)["best_epoch"] == 0 for lr in LR_GRID):
  halt("STOP: all three teacher runs kept epoch 0 (no improvement on the selection set)")
lr_t = chosen_lr("teacher")
launch("answer_only", 3e-4, 0)
if res("answer_only", 3e-4, 0)["best_epoch"] == 0:
  halt("STOP: the answer-trained ceiling did not improve on plain; this setup cannot learn")
launch("neutral", lr_t, 0)
if sel("teacher", lr_t, 0) >= sel("neutral", lr_t, 0):
  halt("STOP: teacher-distil is not better than neutral-distil on the selection set at seed 0")
plan = choose(lr_t)
if plan is None:
  halt("BUDGET: no plan fits after measuring the first runs")
status(plan={"level": plan[1], "estimate_hours": plan[3], "teacher_lr": lr_t})
print(f"CHOSEN {plan[1]} (teacher lr {lr_t:.0e}, estimate {plan[3]:.1f} h)", flush=True)
for arm, lr, seed in plan[2]:
  if not done(arm, lr, seed) and (time.time() - t0) / 3600 + run_sec() / 3600 > args.budget_hours:
    status(outcome=f"BUDGET GUARD: stopped before {rid(arm, lr, seed)}; later runs skipped")
    print("BUDGET GUARD: stopped", flush=True)
    break
  launch(arm, lr, seed)
print("GEN CHAIN DONE", flush=True)
