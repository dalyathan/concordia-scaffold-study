"""CLI: python -m harness.run --task parity --solver oracle --split tune [--model <config name>] [--seed 0]
CPU solvers need no model. Model-backed solvers (plain/lesson/steering/lora) need a GPU box; see REFACTOR_STATUS.md."""
import argparse, json

from harness import modelspec, solver as solver_mod
from harness.evaluate import evaluate
from harness.task import get_task


def main(argv=None):
  ap = argparse.ArgumentParser()
  ap.add_argument("--task", required=True); ap.add_argument("--solver", required=True); ap.add_argument("--split", required=True)
  ap.add_argument("--model"); ap.add_argument("--seed", type=int, default=0); ap.add_argument("--kw", default="{}", help="JSON solver kwargs")
  ap.add_argument("--lock-token"); ap.add_argument("--out", default=None)
  a = ap.parse_args(argv)
  task = get_task(a.task)
  spec = modelspec.load(a.model) if a.model else None
  cls = solver_mod.registry()[a.solver]; kw = json.loads(a.kw)
  if a.solver in ("plain", "lesson", "steering", "lora"):
    from harness.solvers.hf import Backend
    s = cls(Backend(spec), **kw)
  else:
    s = cls(**kw)
  extra = {"directory": a.out} if a.out else {}
  rec = evaluate(task, s, a.split, a.seed, spec, {"kw": kw}, a.lock_token, **extra)
  print(json.dumps({k: rec[k] for k in ("run_id", "summary", "planted")}, indent=1)); print(rec.get("_written_to"))


if __name__ == "__main__":
  main()
