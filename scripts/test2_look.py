"""One look at test2_same and test2_newkey for Llama 3.1 8B or Qwen 2.5 7B (LLAMA_TEST_PLAN.md, QWEN_TEST_PLAN.md).

  python scripts/test2_look.py --model qwen25_7b --freeze          CPU: write demo/gen/test2_freeze_<model>.json from the committed
                                                                    tune records (the frozen arms, adapter weight hashes, tune references)
  python scripts/test2_look.py --model qwen25_7b --dry              CPU: check the freeze file against the records; print the plan
  python scripts/test2_look.py --model qwen25_7b --look --lock-token G3-OWNER-GO:<date>
                                                                    GPU: the look (needs HARNESS_PIN_REF = the owner's scorer pin tag)

The look, in order (any failed check stops it before a test case is scored):
  1. git tree clean; the freeze file committed and unchanged; HARNESS_PIN_REF set and the protected files equal to the pin;
     the lock token starts with G3-OWNER-GO:.
  2. Model-free references (oracle, uniform, always-cheapest, stated-cost rule) on both splits, once (skipped if their records exist).
  3. Each frozen GPU arm in its own process: load the model; for an adapter, check adapter_model.safetensors against the frozen sha256
     and load it as fp32 LoRA weights; PREFLIGHT: re-score the arm's 84 tune cases and require max |p - p_stored| < 1e-3 against the
     committed tune record (adapter-off for plain); then score test2_same and test2_newkey once each through harness.evaluate, which
     refuses a second look at the same (model, split, arm, seed).
Nothing is retrained, no seed, lr or epoch is chosen, and `_last` adapters are never loaded."""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

SPLITS = ("test2_same", "test2_newkey")
LR = {"llama31_8b": "1e-04", "qwen25_7b": "3e-04"}
GPU_ARMS = [("examples-100", "claude_examples_n100", (0, 1, 2)), ("scrambled N=100", "shuffled_claude_n100", (0,)),
            ("cheapest-label N=100", "cheapest_label_n100", (0,))]
REFS = ("oracle", "uniform", "baseline:cheapest", "baseline:stated_cost_rule")
PREFLIGHT_TOL = 1e-3


def freeze_path(model):
  return os.path.join(ROOT, "demo", "gen", f"test2_freeze_{model}.json")


def sha_file(p):
  return hashlib.sha256(open(p, "rb").read()).hexdigest()


def tune_record(model, solver, seed):
  out = []
  for p in sorted(glob.glob(os.path.join(ROOT, "runs", "haggling", model, "*.json"))):
    r = json.load(open(p))
    if r.get("split") == "tune" and r.get("solver") == solver and r.get("seed") == seed:
      out.append(p)
  if len(out) != 1:
    raise SystemExit(f"{model} {solver} seed {seed}: expected one tune record, found {out}")
  return out[0]


def build_freeze(model):
  spec_path = os.path.join(ROOT, "harness", "models", f"{model}.yaml")
  arms = []
  p = tune_record(model, "plain", 0)
  arms.append({"label": "plain", "solver": "plain", "seed": 0, "adapter": None, "tune_record": os.path.relpath(p, ROOT),
               "tune_record_sha256": sha_file(p)})
  for label, arm, seeds in GPU_ARMS:
    solver = f"lora:{arm}_lr{LR[model]}"
    for s in seeds:
      p = tune_record(model, solver, s)
      r = json.load(open(p))
      t = r["solver_config"]["training"]
      assert t["version"].startswith("selected"), (p, t["version"])
      assert r["solver_config"]["adapter_weights_sha256"], p
      arms.append({"label": label, "solver": solver, "seed": s, "tune_record": os.path.relpath(p, ROOT), "tune_record_sha256": sha_file(p),
                   "adapter": {"dir": r["solver_config"]["adapter_dir"], "weights_sha256": r["solver_config"]["adapter_weights_sha256"],
                               "best_epoch": t["best_epoch"], "version": t["version"]},
                   "training": {"seed": s, "arm": t.get("arm"), "best_epoch": t["best_epoch"], "version": t["version"]}})
  files = ["harness/evaluate.py", "harness/tasks/haggling.py", "harness/solvers/hf.py", "harness/modelspec.py", "scripts/test2_look.py",
           "tools/test2_report.py", "demo/gen/test2_cases.jsonl", "demo/gen/test2_cells.json", "demo/gen/test2_fingerprints.json",
           f"harness/models/{model}.yaml"]
  return {"model": model, "plan": {"llama31_8b": "LLAMA_TEST_PLAN.md", "qwen25_7b": "QWEN_TEST_PLAN.md"}[model], "splits": list(SPLITS),
          "readout": "forced-choice letter (the config's assistant prefix), five cyclic orders, the two stored name variants",
          "model_yaml_sha256": sha_file(spec_path), "arms": arms, "references": list(REFS),
          "file_sha256": {f: sha_file(os.path.join(ROOT, f)) for f in files},
          "bootstrap": {"generator": "PCG64", "seed": 0, "resamples": 10000, "clusters": "(V, grid) groups within each slice"},
          "preflight": {"split": "tune", "max_abs_prob_diff": PREFLIGHT_TOL}}


def check_freeze(model, need_committed=False):
  fz = json.load(open(freeze_path(model)))
  problems = []
  for a in fz["arms"]:
    if sha_file(os.path.join(ROOT, a["tune_record"])) != a["tune_record_sha256"]:
      problems.append(f"tune record changed: {a['tune_record']}")
  for f, h in fz["file_sha256"].items():
    if sha_file(os.path.join(ROOT, f)) != h:
      problems.append(f"frozen file changed: {f}")
  if sha_file(os.path.join(ROOT, "harness", "models", f"{model}.yaml")) != fz["model_yaml_sha256"]:
    problems.append("model yaml changed")
  if need_committed:
    st = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    if st:
      problems.append(f"git tree not clean:\n{st}")
  return fz, problems


# ------------------------------------------------------------------ GPU part
class FrozenLoRA:
  """The saved, selected adapter of one arm, loaded with fp32 LoRA weights exactly as harness/train_lora.py reloads its best epoch."""

  def __new__(cls, backend, arm):
    from harness.solvers.hf import _HFSolver
    from peft import PeftModel
    from peft.utils import set_peft_model_state_dict
    from safetensors.torch import load_file

    class _S(_HFSolver):
      name = arm["solver"]
      uses_adapter = True

      def _extra(self):
        return {"adapter_dir": arm["adapter"]["dir"], "adapter_weights_sha256": arm["adapter"]["weights_sha256"],
                "training": arm["training"], "loaded_for": "test2 look (frozen, selected adapter)"}

    d = os.path.join(ROOT, arm["adapter"]["dir"])
    wf = os.path.join(d, "adapter_model.safetensors")
    got = sha_file(wf)
    if got != arm["adapter"]["weights_sha256"]:
      raise SystemExit(f"{arm['solver']} seed {arm['seed']}: adapter weights {got} differ from the frozen {arm['adapter']['weights_sha256']}")
    s = _S(backend)
    peft = PeftModel.from_pretrained(backend.model, d).eval()
    for n, p in peft.named_parameters():
      if "lora_" in n:
        p.data = p.data.float()
    rr = set_peft_model_state_dict(peft, load_file(wf))
    assert not getattr(rr, "unexpected_keys", None), "unexpected adapter keys"
    backend.peft = peft
    s.peft = peft
    return s


def preflight(task, solver, arm):
  """Re-score the arm's tune cases; every averaged option probability must match the committed tune record."""
  from harness.evaluate import evaluate
  stored = json.load(open(os.path.join(ROOT, arm["tune_record"])))
  want = {x["cid"]: x["probs"] for x in stored["cases"]}
  rec = evaluate(task, solver, "tune", arm["seed"], solver.b.spec, write=False)
  worst = max(abs(a - b) for x in rec["cases"] for a, b in zip(x["probs"], want[x["cid"]]))
  print(f"preflight {arm['solver']} seed {arm['seed']}: tune max |dp| {worst:.2e} (tolerance {PREFLIGHT_TOL})", flush=True)
  if worst >= PREFLIGHT_TOL:
    raise SystemExit(f"PREFLIGHT FAILED for {arm['solver']} seed {arm['seed']}: {worst:.3e}; no test case scored")
  return worst


def run_one(model, index, token):
  from harness import modelspec
  from harness.evaluate import evaluate
  from harness.solvers.hf import Backend, PlainSolver
  from harness.task import get_task
  fz, problems = check_freeze(model, need_committed=True)
  if problems:
    raise SystemExit("freeze check failed: " + "; ".join(problems))
  arm = fz["arms"][index]
  spec = modelspec.load(model)
  task = get_task("haggling")
  t0 = time.time()
  b = Backend(spec)
  s = PlainSolver(b) if arm["adapter"] is None else FrozenLoRA(b, arm)
  dev = preflight(task, s, arm)
  print("solver_config_sha256", hashlib.sha256(json.dumps(s.describe(), sort_keys=True, default=str).encode()).hexdigest(), flush=True)
  for split in SPLITS:
    rec = evaluate(task, s, split, arm["seed"], spec, {"step": "test2 look", "arm": arm["label"], "freeze": os.path.relpath(freeze_path(model), ROOT),
                                                        "preflight_tune_max_abs_prob_diff": dev}, token)
    print(f"{arm['label']} seed {arm['seed']} {split}: written {rec['_written_to']}", flush=True)
  print(f"arm done in {time.time() - t0:.0f}s", flush=True)


def references(token):
  from harness.evaluate import evaluate
  from harness.solvers import cpu
  from harness.task import get_task
  task = get_task("haggling")
  mk = {"oracle": cpu.OracleSolver, "uniform": cpu.UniformSolver,
        "baseline:cheapest": lambda: cpu.BaselineSolver(policy="cheapest"),
        "baseline:stated_cost_rule": lambda: cpu.BaselineSolver(policy="stated_cost_rule")}
  for split in SPLITS:
    for name in REFS:
      have = [p for p in glob.glob(os.path.join(ROOT, "runs", "haggling", "none", "*.json"))
              if (lambda r: (r.get("split"), r.get("solver")) == (split, name))(json.load(open(p)))]
      if have:
        print(f"reference {name} {split}: already recorded ({os.path.relpath(have[0], ROOT)})"); continue
      rec = evaluate(task, mk[name](), split, 0, None, {"step": "test2 look reference"}, token)
      if name == "oracle" and not rec["planted"]["all_ok"]:
        raise SystemExit("STOP: the oracle fails a planted case (pipeline)")
      print(f"reference {name} {split}: {rec['_written_to']}")


def main(argv=None):
  ap = argparse.ArgumentParser()
  ap.add_argument("--model", required=True, choices=sorted(LR))
  ap.add_argument("--freeze", action="store_true"); ap.add_argument("--dry", action="store_true"); ap.add_argument("--look", action="store_true")
  ap.add_argument("--one", type=int, help=argparse.SUPPRESS); ap.add_argument("--lock-token")
  a = ap.parse_args(argv)
  if a.freeze:
    fz = build_freeze(a.model)
    json.dump(fz, open(freeze_path(a.model), "w"), indent=1, sort_keys=True)
    print("wrote", os.path.relpath(freeze_path(a.model), ROOT), f"({len(fz['arms'])} GPU arms)")
    return
  if a.dry:
    fz, problems = check_freeze(a.model)
    for x in fz["arms"]:
      print(f"{x['label']:22s} {x['solver']:38s} seed {x['seed']}  " + (x["adapter"]["weights_sha256"][:16] if x["adapter"] else "no adapter"))
    print("problems:", problems or "none")
    return
  if not (a.lock_token or "").startswith("G3-OWNER-GO:"):
    raise SystemExit("the look needs --lock-token G3-OWNER-GO:<date> (G3 and the owner's explicit go)")
  if not os.environ.get("HARNESS_PIN_REF"):
    raise SystemExit("the look needs HARNESS_PIN_REF (the owner's scorer pin tag)")
  if a.one is not None:
    run_one(a.model, a.one, a.lock_token); return
  if a.look:
    fz, problems = check_freeze(a.model, need_committed=True)
    if problems:
      raise SystemExit("freeze check failed: " + "; ".join(problems))
    references(a.lock_token)
    for i in range(len(fz["arms"])):
      r = subprocess.run([sys.executable, os.path.abspath(__file__), "--model", a.model, "--one", str(i), "--lock-token", a.lock_token], cwd=ROOT)
      if r.returncode:
        raise SystemExit(f"arm {i} stopped (exit {r.returncode}); later arms not run")
    print("LOOK DONE for", a.model)


if __name__ == "__main__":
  main()
