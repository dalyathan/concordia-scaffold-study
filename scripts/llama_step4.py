"""Step 4 of LLAMA_PROMPT.md (GPU; train and tune splits only): model-free references, the plain failure map and the prompt arms,
one model load, one run record per (solver, split). Refuses every split except train and tune.

  HF_HUB_OFFLINE=1 CUBLAS_WORKSPACE_CONFIG=:4096:8 HARNESS_PROVIDER=runpod HARNESS_GPU_USD_PER_HOUR=0.60 \
    PYTHONPATH=concordia:. .venv/bin/python scripts/llama_step4.py [--model llama31_8b] [--splits tune,train] [--only plain,notes_teacher]

Order: CPU references (oracle, uniform, cheapest, stated_cost_rule) -> plain tune -> plain train -> notes arms tune -> notes arms train.
Stops (exit 2) after plain tune if its mean first-token letter mass is below the harness floor (0.5): the readout would be wrong."""
import argparse, json, os, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from harness import modelspec
from harness.evaluate import evaluate
from harness.solvers import cpu
from harness.task import get_task

NOTES = ("method_original", "teacher", "neutral", "wrong_rule")
ALLOWED = ("train", "tune")


def main():
  ap = argparse.ArgumentParser()
  ap.add_argument("--model", default="llama31_8b"); ap.add_argument("--splits", default="tune,train"); ap.add_argument("--only")
  a = ap.parse_args()
  splits = a.splits.split(",")
  assert all(s in ALLOWED for s in splits), "step 4 runs on train and tune only"
  only = set(a.only.split(",")) if a.only else None
  want = lambda n: only is None or n in only
  task = get_task("haggling")
  os.makedirs(os.path.join(ROOT, "logs"), exist_ok=True)
  log = open(os.path.join(ROOT, "logs", "llama_step4.jsonl"), "a")
  def note(**kw):
    kw["t"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()); log.write(json.dumps(kw) + "\n"); log.flush(); print(json.dumps(kw), flush=True)
  for split in splits:
    for name, s in (("oracle", cpu.OracleSolver()), ("uniform", cpu.UniformSolver()), ("cheapest", cpu.BaselineSolver(policy="cheapest")),
                    ("stated_cost_rule", cpu.BaselineSolver(policy="stated_cost_rule"))):
      if want(name):
        r = evaluate(task, s, split, 0, None, {"step": "llama step 4 reference"})
        note(solver=name, split=split, soft=r["summary"]["soft_regret_mean"], planted=f"{r['planted']['n_ok']}/{r['planted']['n']}", path=r["_written_to"])
        if name == "oracle" and not r["planted"]["all_ok"]:
          note(event="STOP: oracle fails a planted case (pipeline)"); sys.exit(2)
        if name == "cheapest" and "planted-high" not in r["planted"]["failed"]:
          note(event="STOP: always-cheapest passes planted-high (negative control)"); sys.exit(2)
  spec = modelspec.load(a.model)
  from harness.solvers.hf import Backend, NotesSolver, PlainSolver
  t0 = time.time(); b = Backend(spec); note(event="model loaded", seconds=time.time() - t0, revision=b.revision)
  jobs = [("plain", PlainSolver(b), sp) for sp in splits] + \
         [("plain_noprefix", PlainSolver(b, prefix=""), "train")] * ("train" in splits) + \
         [(f"notes_{n}", NotesSolver(b, os.path.join(ROOT, "harness", "lessons", n + ".txt")), sp) for sp in splits for n in NOTES]
  for name, s, split in jobs:
    if not want(name):
      continue
    r = evaluate(task, s, split, 0, spec, {"step": "llama step 4", "arm": name})
    note(solver=name, split=split, soft=r["summary"]["soft_regret_mean"], by_type={k: v["soft_regret_mean"] for k, v in r["summary"]["by_type"].items()},
         mass=r["letter_mass"]["mean"], planted=f"{r['planted']['n_ok']}/{r['planted']['n']}", gpu_s=r["timing"]["gpu_seconds"], path=r["_written_to"])
    if name == "plain" and split == "tune" and r["letter_mass"]["mean"] < 0.9:
      note(event="STOP: plain tune letter mass below 0.9 (LLAMA_PLAN.md mass bands)", mass=r["letter_mass"]["mean"]); sys.exit(2)
  note(event="step 4 done", seconds=time.time() - t0)


if __name__ == "__main__":
  main()
