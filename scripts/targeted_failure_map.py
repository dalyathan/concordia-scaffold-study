"""Step 1 of TARGETED_PLAN.md: the failure map of the examples-100 adapters (A0) and plain Qwen on the 90 probe3 cells (build data).

  GPU:  PYTHONPATH=concordia:. .venv/bin/python scripts/targeted_failure_map.py --score [--model qwen25_7b]
        one process per arm (plain, A0 seeds 0-2), each: the frozen adapter (hash-checked, fp32 reload as for the test2 look), a
        preflight that re-scores the arm's tune cases against its committed tune record (max |dp| < 1e-3), then one probe3 run record
        (config step "targeted failure map"). An arm whose probe3 record exists is skipped.
  CPU:  python scripts/targeted_failure_map.py --table [--model qwen25_7b]
        writes demo/gen/failure_map_probe3_<model>.json and .md: per probe cell its features, A0's soft regret per seed and seed mean,
        the number of seeds above 0.1, plain's regret. This table is the ONLY input the targeting Claude gets (TARGETED_PLAN.md step 2).
No tune, test or test3 number enters the table."""
from __future__ import annotations

import argparse
import glob
import importlib.util
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
STEP = "targeted failure map"
FEATURES = ("type", "V", "grid_name", "grid", "C", "prior", "line", "wording")


def _look():
  spec = importlib.util.spec_from_file_location("test2_look", os.path.join(ROOT, "scripts", "test2_look.py"))
  m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
  return m


def arms(model):
  fz = json.load(open(os.path.join(ROOT, "demo", "gen", f"test2_freeze_{model}.json")))
  return [a for a in fz["arms"] if a["label"] in ("plain", "examples-100")]


def records(model, runs=None):
  from harness import records as R
  out = []
  for p in sorted(glob.glob(os.path.join(runs or R.RUNS, "haggling", model, "*.json"))):
    r = json.load(open(p))
    if r.get("split") == "probe3" and (r.get("config") or {}).get("step") == STEP:
      r["_path"] = os.path.relpath(p, ROOT); out.append(r)
  return out


def score_one(model, i):
  from harness import modelspec
  from harness.evaluate import evaluate
  from harness.tasks.haggling3 import Haggling3Task
  L = _look()
  arm = arms(model)[i]
  if any((r["solver"], r["seed"]) == (arm["solver"], arm["seed"]) for r in records(model)):
    print(f"{arm['label']} seed {arm['seed']}: probe3 already recorded"); return
  spec, task = modelspec.load(model), Haggling3Task()
  s = L.make_solver(L.load_backend(spec), arm)
  dev = L.preflight(task, s, arm, spec)
  rec = evaluate(task, s, "probe3", arm["seed"], spec, {"step": STEP, "arm": arm["label"], "preflight_tune_max_abs_prob_diff": dev})
  print(f"{arm['label']} seed {arm['seed']}: probe3 soft regret {rec['summary']['soft_regret_mean']:.3f} -> {rec['_written_to']}", flush=True)


def soft(x):
  return max(x["payoffs"]) - sum(p * v for p, v in zip(x["probs"], x["payoffs"]))


def table(model, runs=None, out_dir=None):
  recs = records(model, runs)
  want = {(a["solver"], a["seed"]) for a in arms(model)}
  got = {(r["solver"], r["seed"]) for r in recs}
  if got != want:
    raise SystemExit(f"failure map incomplete: missing {sorted(want - got)}")
  plain = next(r for r in recs if r["solver"] == "plain")
  a0 = sorted((r for r in recs if r["solver"] != "plain"), key=lambda r: r["seed"])
  rows = []
  for x in (x for x in plain["cases"] if not x["planted"]):
    cid = x["cid"]
    per = [soft(next(y for y in r["cases"] if y["cid"] == cid)) for r in a0]
    rows.append({"cell": x["inputs"]["cell"], **{k: x["inputs"][k] for k in FEATURES},
                 "a0_soft_regret_per_seed": [round(v, 4) for v in per], "a0_soft_regret_mean": round(sum(per) / len(per), 4),
                 "a0_seeds_above_0.1": sum(v > 0.1 for v in per), "plain_soft_regret": round(soft(x), 4)})
  rows.sort(key=lambda r: (r["type"], r["V"], r["grid_name"], str(r["prior"]), str(r["C"])))
  out = {"model": model, "split": "probe3", "n_cells": len(rows), "records": [r["_path"] for r in recs], "rows": rows}
  base = os.path.join(out_dir or os.path.join(ROOT, "demo", "gen"), f"failure_map_probe3_{model}")
  json.dump(out, open(base + ".json", "w"), indent=1, sort_keys=True)
  md = ["| type | V | grid | prices | stated cost | cost range | seller line | wording | A0 regret per seed | A0 mean | seeds > 0.1 | plain |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
  for r in rows:
    md.append(f"| {r['type']} | {r['V']} | {r['grid_name']} | {'-'.join(map(str, r['grid']))} | {'-' if r['C'] is None else r['C']} | "
              f"{r['prior'][0]}-{r['prior'][1]} | {r['line']} | {r['wording']} | {', '.join(f'{v:.3f}' for v in r['a0_soft_regret_per_seed'])} | "
              f"{r['a0_soft_regret_mean']:.3f} | {r['a0_seeds_above_0.1']} | {r['plain_soft_regret']:.3f} |")
  open(base + ".md", "w").write("\n".join(md) + "\n")
  print("wrote", os.path.relpath(base, ROOT) + ".json/.md", f"({len(rows)} cells)")
  return out


def main(argv=None):
  ap = argparse.ArgumentParser()
  ap.add_argument("--model", default="qwen25_7b"); ap.add_argument("--score", action="store_true"); ap.add_argument("--table", action="store_true")
  ap.add_argument("--one", type=int, help=argparse.SUPPRESS)
  a = ap.parse_args(argv)
  if a.one is not None:
    score_one(a.model, a.one); return
  if a.score:
    for i in range(len(arms(a.model))):
      r = subprocess.run([sys.executable, os.path.abspath(__file__), "--model", a.model, "--one", str(i)], cwd=ROOT)
      if r.returncode:
        raise SystemExit(f"arm {i} stopped (exit {r.returncode})")
  if a.table:
    table(a.model)


if __name__ == "__main__":
  main()
