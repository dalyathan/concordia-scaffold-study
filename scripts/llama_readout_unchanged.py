"""Check that the soft-cap readout fix (DECISIONS.md L38) changes no Llama number: rescore stored Llama tune records with the current
harness code (no record written) and compare per case, bit for bit.

  HF_HUB_OFFLINE=1 CUBLAS_WORKSPACE_CONFIG=:4096:8 PYTHONPATH=concordia:. .venv/bin/python scripts/llama_readout_unchanged.py
Rescored: plain (tune), notes:wrong_rule (tune), and the examples-100 seed-0 adapter (tune), one model load (the adapter last).
Writes demo_out/llama/readout_unchanged.json."""
import glob, json, os, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def stored(solver, seed=0):
  r = [json.load(open(p)) for p in sorted(glob.glob(os.path.join(ROOT, "runs", "haggling", "llama31_8b", "*-tune-*.json")))]
  r = [x for x in r if x["solver"] == solver and x["seed"] == seed]
  assert len(r) == 1, (solver, len(r))
  return r[0]


def compare(new, old):
  a = {x["cid"]: x for x in new["cases"]}; b = {x["cid"]: x for x in old["cases"]}
  assert set(a) == set(b)
  diffs = [max(abs(p - q) for p, q in zip(a[c]["probs"], b[c]["probs"])) for c in a]
  per_order = [max(abs(p - q) for po, qo in zip(a[c]["per_order_probs"], b[c]["per_order_probs"]) for p, q in zip(po, qo)) for c in a]
  return {"n_cases": len(a), "max_abs_dp": max(diffs), "max_abs_dp_per_order": max(per_order), "bit_identical": max(diffs) == 0.0 and max(per_order) == 0.0,
          "soft_new": new["summary"]["soft_regret_mean"], "soft_old": old["summary"]["soft_regret_mean"]}


def main():
  from harness import modelspec
  from harness.evaluate import evaluate
  from harness.solvers.hf import Backend, LoRASolver, NotesSolver, PlainSolver
  from harness.task import get_task
  t0 = time.time()
  spec = modelspec.load("llama31_8b"); b = Backend(spec); task = get_task("haggling")
  assert not getattr(b.model.config, "final_logit_softcapping", None), "Llama config has a final soft-cap?"
  out = {}
  for label, s, old in (("plain", PlainSolver(b), stored("plain")),
                        ("notes:wrong_rule", NotesSolver(b, os.path.join(ROOT, "harness", "lessons", "wrong_rule.txt")), stored("notes:wrong_rule"))):
    out[label] = compare(evaluate(task, s, "tune", 0, spec, {"check": "readout unchanged"}, write=False), old)
    print(label, out[label], flush=True)
  old = stored("lora:claude_examples_n100_lr1e-04", 0)
  s = LoRASolver(b, old["solver_config"]["adapter_dir"])
  out["lora:claude_examples_n100_lr1e-04 s0"] = compare(evaluate(task, s, "tune", 0, spec, {"check": "readout unchanged"}, write=False), old)
  print("lora", out["lora:claude_examples_n100_lr1e-04 s0"], flush=True)
  out["all_bit_identical"] = all(v["bit_identical"] for v in out.values() if isinstance(v, dict))
  out["gpu_seconds"] = time.time() - t0
  json.dump(out, open(os.path.join(ROOT, "demo_out", "llama", "readout_unchanged.json"), "w"), indent=1)
  print("ALL BIT-IDENTICAL:", out["all_bit_identical"])


if __name__ == "__main__":
  main()
