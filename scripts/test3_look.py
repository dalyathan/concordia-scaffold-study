"""The one test3 look of the targeted experiment (TARGETED_PLAN.md step 7). Same mechanics as scripts/test2_look.py (whose checked functions
are imported unchanged): freeze file, clean tree and pin before anything is written, references once, one process per arm, a tune
preflight per adapter (max |dp| < 1e-3 against the committed tune record), one record per (arm, seed) on test3, a commit after each arm,
resume by scoring only arms without a record.

  python scripts/test3_look.py --freeze [--model qwen25_7b]     CPU, after training: demo/gen/test3_freeze_<model>.json
  python scripts/test3_look.py --dry    [--model qwen25_7b]     CPU: check the freeze; print the arms
  HARNESS_PIN_REF=scorer-pin-1 python scripts/test3_look.py --look --lock-token G3-OWNER-GO:<date> [--model qwen25_7b]

Arms: plain; A0 (examples-100, seeds 0-2, as frozen for test2); T, R, N (seeds 0-2, the selected adapters of the targeted runs).
Arm E is NOT in this look (G1 no-go; DECISIONS.md T3): it is redesigned as a follow-up with its own held-out set. Last-epoch adapters are
tune-only (not scored on test3)."""
from __future__ import annotations

import argparse
import glob
import hashlib
import importlib.util
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
LR = {"qwen25_7b": "3e-04"}
FILES = ["harness/evaluate.py", "harness/task.py", "harness/records.py", "harness/tasks/haggling.py", "harness/tasks/haggling3.py",
         "harness/solvers/hf.py", "harness/solvers/cpu.py", "harness/protected/scorer.py", "harness/protected/payoffs/haggling.py",
         "tools/lock_protected.py", "tools/test3_report.py", "scripts/test3_look.py", "scripts/test2_look.py", "TARGETED_PLAN.md",
         "TARGETED_PREDICTIONS.md", "tools/llama_report.py", "harness/train_lora.py", "demo/gen/test3_cases.jsonl", "demo/gen/test3_cells.json", "demo/gen/test3_fingerprints.json"]
REFS = ("oracle", "uniform", "baseline:cheapest", "baseline:stated_cost_rule")


def L():
  spec = importlib.util.spec_from_file_location("test2_look", os.path.join(ROOT, "scripts", "test2_look.py"))
  m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def freeze_path(model):
  return os.path.join(ROOT, "demo", "gen", f"test3_freeze_{model}.json")


def sha(p):
  return hashlib.sha256(open(os.path.join(ROOT, p), "rb").read()).hexdigest()


def build_freeze(model):
  look = L()
  base = json.load(open(os.path.join(ROOT, "demo", "gen", f"test2_freeze_{model}.json")))
  arms = [a for a in base["arms"] if a["label"] in ("plain", "examples-100")]
  for a in arms:
    a["label"] = "A0" if a["label"] == "examples-100" else "plain"
  envs = set()
  for X in ("T", "R", "N"):
    solver = f"lora:claude_examples_n150_{X}_lr{LR[model]}"
    for s in (0, 1, 2):
      try:
        p = look.tune_record(model, solver, s)
      except SystemExit:
        print(f"{X} seed {s}: no tune record (crashed or not run); reported as missing, never rerun"); continue
      r = json.load(open(p)); sc = r["solver_config"]; tr = sc["training"]
      envs.add(json.dumps({k: r["environment"]["packages"][k] for k in look.PACKAGES}, sort_keys=True))
      arms.append({"label": X, "solver": solver, "seed": s, "tune_record": os.path.relpath(p, ROOT), "tune_record_sha256": look.sha_file(p),
                   "adapter": {"dir": sc["adapter_dir"], "weights_sha256": sc["adapter_weights_sha256"], "dir_sha256": sc["adapter_sha256"],
                               "best_epoch": tr["best_epoch"], "version": tr["version"]},
                   "training": {"seed": s, "arm": tr.get("arm"), "best_epoch": tr["best_epoch"], "version": tr["version"],
                                "extra_key": tr.get("extra_key")}})
  if len(envs) > 1 or (envs and json.loads(envs.pop()) != base["environment"]["packages"]):
    raise SystemExit("the targeted runs' package versions differ from each other or from A0's; the preflight could not be exact")
  files = FILES + [f"harness/models/{model}.yaml", f"demo/gen/targeted_draws_{model}.json", f"demo/gen/targeted_labels_{model}.json",
                   f"demo/gen/targeting_rule_{model}.json"]
  return {**{k: base[k] for k in ("model", "model_revision", "environment", "readout")}, "plan": "TARGETED_PLAN.md", "splits": ["test3"],
          "arms": arms, "references": list(REFS), "file_sha256": {f: sha(f) for f in files},
          "preflight": {"split": "tune", "max_abs_prob_diff": 1e-3}}


def check(model, committed=False, clean=False):
  look = L()
  fz = json.load(open(freeze_path(model)))
  problems = [f"frozen file changed: {f}" for f, h in fz["file_sha256"].items() if sha(f) != h]
  problems += [f"tune record changed: {a['tune_record']}" for a in fz["arms"] if look.sha_file(os.path.join(ROOT, a["tune_record"])) != a["tune_record_sha256"]]
  if committed:
    rel = [os.path.relpath(freeze_path(model), ROOT)] + list(fz["file_sha256"]) + [a["tune_record"] for a in fz["arms"]]
    if any(look.git("ls-files", "--error-unmatch", f).returncode for f in rel) or look.git("diff", "--quiet", "HEAD", "--", *rel).returncode:
      problems.append("frozen files not committed or differ from HEAD")
  if clean and look.git("status", "--porcelain").stdout.strip():
    problems.append("git tree not clean")
  return fz, problems


def has_record(model, solver, seed, runs):
  for p in glob.glob(os.path.join(runs, "haggling", model or "none", "*.json")):
    r = json.load(open(p))
    if (r.get("split"), r.get("solver")) == ("test3", solver) and (model is None or r.get("seed") == seed):
      return True
  return False


def run_one(model, i, token):
  from harness import modelspec, records
  from harness.evaluate import evaluate
  from harness.tasks.haggling3 import Haggling3Task
  look = L()
  fz, problems = check(model, committed=True)
  if problems:
    raise SystemExit("freeze check failed: " + "; ".join(problems))
  arm = fz["arms"][i]
  if has_record(model, arm["solver"], arm["seed"], records.RUNS):
    print(arm["label"], arm["seed"], "already recorded"); return
  look.check_environment(fz)
  spec, task = modelspec.load(model), Haggling3Task()
  s = look.make_solver(look.load_backend(spec), arm)
  dev = look.preflight(task, s, arm, spec)
  rec = evaluate(task, s, "test3", arm["seed"], spec, {"step": "test3 look", "arm": arm["label"], "preflight_tune_max_abs_prob_diff": dev}, token)
  print(f"{arm['label']} seed {arm['seed']} test3: written {rec['_written_to']}", flush=True)


def references(token):
  from harness import records
  from harness.evaluate import evaluate
  from harness.solvers import cpu
  from harness.tasks.haggling3 import Haggling3Task
  mk = {"oracle": cpu.OracleSolver, "uniform": cpu.UniformSolver, "baseline:cheapest": lambda: cpu.BaselineSolver(policy="cheapest"),
        "baseline:stated_cost_rule": lambda: cpu.BaselineSolver(policy="stated_cost_rule")}
  for name in REFS:
    if has_record(None, name, 0, records.RUNS):
      continue
    rec = evaluate(Haggling3Task(), mk[name](), "test3", 0, None, {"step": "test3 look reference"}, token)
    if name == "oracle" and not rec["planted"]["all_ok"]:
      raise SystemExit("STOP: the oracle fails a planted case")


def commit_records(model, what):
  look = L()
  look.git("add", "runs/haggling/none", f"runs/haggling/{model}")
  if look.git("diff", "--cached", "--quiet").returncode:
    r = look.git("commit", "-q", "-m", f"test3 look {model}: {what} (records written by scripts/test3_look.py)")
    if r.returncode:
      raise SystemExit(f"could not commit the records: {r.stderr}")


def main(argv=None):
  ap = argparse.ArgumentParser(); ap.add_argument("--model", default="qwen25_7b")
  ap.add_argument("--freeze", action="store_true"); ap.add_argument("--dry", action="store_true"); ap.add_argument("--look", action="store_true")
  ap.add_argument("--one", type=int, help=argparse.SUPPRESS); ap.add_argument("--lock-token")
  a = ap.parse_args(argv)
  look = L()
  if a.freeze:
    json.dump(build_freeze(a.model), open(freeze_path(a.model), "w"), indent=1, sort_keys=True); print("wrote", freeze_path(a.model)); return
  if a.dry:
    fz, problems = check(a.model, committed=True)
    for x in fz["arms"]:
      print(f"{x['label']:6s} {x['solver']:40s} seed {x['seed']} " + (x["adapter"]["weights_sha256"][:16] if x["adapter"] else "no adapter"))
    print("problems:", problems or "none"); return
  if not (a.lock_token or "").startswith("G3-OWNER-GO:") or not os.environ.get("HARNESS_PIN_REF"):
    raise SystemExit("the look needs --lock-token G3-OWNER-GO:<date> and HARNESS_PIN_REF")
  if a.one is not None:
    run_one(a.model, a.one, a.lock_token); return
  if a.look:
    fz, problems = check(a.model, committed=True, clean=True)
    if problems:
      raise SystemExit("freeze check failed (nothing written): " + "; ".join(problems))
    references(a.lock_token); commit_records(a.model, "references")
    for i, arm in enumerate(fz["arms"]):
      r = subprocess.run([sys.executable, os.path.abspath(__file__), "--model", a.model, "--one", str(i), "--lock-token", a.lock_token], cwd=ROOT)
      commit_records(a.model, f"{arm['label']} seed {arm['seed']}")
      if r.returncode:
        raise SystemExit(f"arm {i} stopped (exit {r.returncode}); rerun --look to resume")
    print("TEST3 LOOK DONE")


if __name__ == "__main__":
  main()
