"""One look at test2_same and test2_newkey for Llama 3.1 8B or Qwen 2.5 7B (LLAMA_TEST_PLAN.md, QWEN_TEST_PLAN.md).

  python scripts/test2_look.py --model qwen25_7b --freeze          CPU: write demo/gen/test2_freeze_<model>.json from the committed
                                                                    tune records (the frozen arms, adapter hashes, tune references,
                                                                    package versions, file hashes)
  python scripts/test2_look.py --model qwen25_7b --dry              CPU: check the freeze file against the repository; print the plan
  python scripts/test2_look.py --model qwen25_7b --look --lock-token G3-OWNER-GO:<date>
                                                                    GPU: the look (needs HARNESS_PIN_REF = the owner's scorer pin tag)

The look, in order (any failed check stops it before a test case is scored):
  1. Parent process, before anything is written: git tree clean; every frozen file committed and equal to its frozen sha256;
     HARNESS_PIN_REF set (harness.evaluate checks the protected files against it); lock token starts with G3-OWNER-GO:.
  2. Model-free references (oracle, uniform, always-cheapest, stated-cost rule) on both splits, once (a split/reference with a record
     is skipped); committed.
  3. Each frozen arm in its own process. The process checks the frozen files again (run records may now exist; they are not frozen
     files), that torch / transformers / peft and the GPU model equal those of the tune records, loads the model, and for an adapter
     checks the adapter directory and adapter_model.safetensors against the frozen sha256 and loads it with fp32 LoRA weights, as
     harness/train_lora.py reloads its best epoch. PREFLIGHT: it re-scores the arm's tune cases (84 plus the planted cases) and
     requires the same case ids and max |p - p_stored| < 1e-3 against the committed tune record. Then it scores each test2 split that
     has no record for this arm; harness.evaluate refuses a second record of the same (model, split, solver name, seed). The parent
     commits the arm's records before the next arm starts.
Resume rule (fixed at G3): after a crash, rerunning --look scores only the (arm, split) pairs without a record. Scoring a split that has
no record is not a second look. A failed preflight stops the look; that arm scores nothing until the cause is logged in DECISIONS.md.
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
PACKAGES = ("torch", "transformers", "peft")
FROZEN_FILES = ["harness/evaluate.py", "harness/task.py", "harness/records.py", "harness/tasks/haggling.py", "harness/solvers/hf.py",
                "harness/solvers/cpu.py", "harness/solver.py", "harness/modelspec.py", "harness/protected/scorer.py",
                "harness/protected/payoffs/haggling.py", "tools/lock_protected.py", "tools/llama_report.py", "tools/test2_report.py",
                "scripts/test2_look.py", "demo/gen/test2_cases.jsonl", "demo/gen/test2_cells.json", "demo/gen/test2_fingerprints.json",
                "LLAMA_TEST_PLAN.md", "QWEN_TEST_PLAN.md", "TEST2_PREDICTIONS.md"]


def freeze_path(model):
  return os.path.join(ROOT, "demo", "gen", f"test2_freeze_{model}.json")


def sha_file(p):
  return hashlib.sha256(open(p, "rb").read()).hexdigest()


def git(*args):
  return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)


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
  import yaml
  spec_path = os.path.join(ROOT, "harness", "models", f"{model}.yaml")
  arms = []
  p = tune_record(model, "plain", 0)
  env = json.load(open(p))["environment"]
  arms.append({"label": "plain", "solver": "plain", "seed": 0, "adapter": None, "training": None, "tune_record": os.path.relpath(p, ROOT),
               "tune_record_sha256": sha_file(p)})
  for label, arm, seeds in GPU_ARMS:
    solver = f"lora:{arm}_lr{LR[model]}"
    for s in seeds:
      p = tune_record(model, solver, s)
      r = json.load(open(p))
      t = r["solver_config"]["training"]
      assert t["version"].startswith("selected"), (p, t["version"])
      assert r["solver_config"]["adapter_weights_sha256"], p
      assert {k: r["environment"]["packages"][k] for k in PACKAGES} == {k: env["packages"][k] for k in PACKAGES}, p
      arms.append({"label": label, "solver": solver, "seed": s, "tune_record": os.path.relpath(p, ROOT), "tune_record_sha256": sha_file(p),
                   "adapter": {"dir": r["solver_config"]["adapter_dir"], "weights_sha256": r["solver_config"]["adapter_weights_sha256"],
                               "dir_sha256": r["solver_config"]["adapter_sha256"], "best_epoch": t["best_epoch"], "version": t["version"]},
                   "training": {"seed": s, "arm": t.get("arm"), "best_epoch": t["best_epoch"], "version": t["version"]}})
  files = FROZEN_FILES + [f"harness/models/{model}.yaml"]
  return {"model": model, "plan": {"llama31_8b": "LLAMA_TEST_PLAN.md", "qwen25_7b": "QWEN_TEST_PLAN.md"}[model], "splits": list(SPLITS),
          "model_revision": yaml.safe_load(open(spec_path))["revision"],
          "readout": "forced-choice letter (the config's assistant prefix), five cyclic orders, the two stored name variants",
          "environment": {"packages": {k: env["packages"][k] for k in PACKAGES}, "gpu_model": "A40"},
          "arms": arms, "references": list(REFS),
          "file_sha256": {f: sha_file(os.path.join(ROOT, f)) for f in files},
          "bootstrap": {"generator": "PCG64", "seed": 0, "resamples": 10000, "clusters": "(V, grid) groups within each slice"},
          "preflight": {"split": "tune", "max_abs_prob_diff": PREFLIGHT_TOL}}


def check_freeze(model, committed=False, tree_clean=False):
  """Frozen files and tune records equal to the freeze; with committed=True also tracked and unmodified in git (run records are
  not frozen files, so new records never fail this); with tree_clean=True the whole tree must be clean (the parent, before writing)."""
  fz = json.load(open(freeze_path(model)))
  problems = []
  for a in fz["arms"]:
    if sha_file(os.path.join(ROOT, a["tune_record"])) != a["tune_record_sha256"]:
      problems.append(f"tune record changed: {a['tune_record']}")
  for f, h in fz["file_sha256"].items():
    if sha_file(os.path.join(ROOT, f)) != h:
      problems.append(f"frozen file changed: {f}")
  if committed:
    rel = [os.path.relpath(freeze_path(model), ROOT)] + list(fz["file_sha256"]) + [a["tune_record"] for a in fz["arms"]]
    for f in rel:
      if git("ls-files", "--error-unmatch", f).returncode:
        problems.append(f"not committed: {f}")
    if git("diff", "--quiet", "HEAD", "--", *rel).returncode:
      problems.append("frozen files differ from HEAD")
  if tree_clean and git("status", "--porcelain").stdout.strip():
    problems.append("git tree not clean")
  return fz, problems


def existing(model, solver, seed, split, runs_dir):
  out = []
  for p in glob.glob(os.path.join(runs_dir, "haggling", model or "none", "*.json")):
    r = json.load(open(p))
    if (r.get("solver"), r.get("split")) == (solver, split) and (model is None or r.get("seed") == seed):
      out.append(p)
  return out


# ------------------------------------------------------------------ GPU part (load_backend / make_solver can be replaced in tests)
def load_backend(spec):
  from harness.solvers.hf import Backend
  return Backend(spec)


def make_solver(backend, arm):
  from harness.solvers.hf import PlainSolver, _HFSolver, file_sha
  if arm["adapter"] is None:
    return PlainSolver(backend)
  from peft import PeftModel
  from peft.utils import set_peft_model_state_dict
  from safetensors.torch import load_file

  class FrozenLoRA(_HFSolver):
    name = arm["solver"]
    uses_adapter = True

    def _extra(self):
      return {"adapter_dir": arm["adapter"]["dir"], "adapter_sha256": arm["adapter"]["dir_sha256"],
              "adapter_weights_sha256": arm["adapter"]["weights_sha256"], "training": arm["training"],
              "loaded_for": "test2 look (frozen, selected adapter)"}

  d = os.path.join(ROOT, arm["adapter"]["dir"])
  wf = os.path.join(d, "adapter_model.safetensors")
  if sha_file(wf) != arm["adapter"]["weights_sha256"] or file_sha(d) != arm["adapter"]["dir_sha256"]:
    raise SystemExit(f"{arm['solver']} seed {arm['seed']}: adapter files differ from the freeze; no test case scored")
  s = FrozenLoRA(backend)
  peft = PeftModel.from_pretrained(backend.model, d).eval()
  for n, p in peft.named_parameters():
    if "lora_" in n:
      p.data = p.data.float()
  rr = set_peft_model_state_dict(peft, load_file(wf))
  assert not getattr(rr, "unexpected_keys", None), "unexpected adapter keys"
  backend.peft = peft
  s.peft = peft
  return s


def check_environment(fz):
  from harness import records
  env = records.environment()
  got = {k: env["packages"].get(k) for k in PACKAGES}
  if got != fz["environment"]["packages"]:
    raise SystemExit(f"package versions {got} differ from the tune records' {fz['environment']['packages']}; no test case scored")
  if fz["environment"]["gpu_model"] not in (env.get("gpu") or ""):
    raise SystemExit(f"GPU {env.get('gpu')} is not the frozen {fz['environment']['gpu_model']}; no test case scored")


def preflight(task, solver, arm, spec):
  """Re-score the arm's tune cases; the same case ids and every averaged option probability as the committed tune record."""
  from harness.evaluate import evaluate
  stored = json.load(open(os.path.join(ROOT, arm["tune_record"])))
  want = {x["cid"]: x["probs"] for x in stored["cases"]}
  rec = evaluate(task, solver, "tune", arm["seed"], spec, write=False)
  got = {x["cid"]: x["probs"] for x in rec["cases"]}
  if set(got) != set(want):
    raise SystemExit(f"PREFLIGHT FAILED for {arm['solver']} seed {arm['seed']}: case ids differ from the tune record; no test case scored")
  worst = max(abs(a - b) for c in got for a, b in zip(got[c], want[c]))
  print(f"preflight {arm['solver']} seed {arm['seed']}: tune max |dp| {worst:.2e} over {len(got)} cases (tolerance {PREFLIGHT_TOL})", flush=True)
  if worst >= PREFLIGHT_TOL:
    raise SystemExit(f"PREFLIGHT FAILED for {arm['solver']} seed {arm['seed']}: {worst:.3e}; no test case scored")
  return worst


def run_one(model, index, token, env_check=True):
  from harness import modelspec, records
  from harness.evaluate import evaluate
  from harness.task import get_task
  fz, problems = check_freeze(model, committed=True)
  if problems:
    raise SystemExit("freeze check failed: " + "; ".join(problems))
  arm = fz["arms"][index]
  todo = [s for s in SPLITS if not existing(model, arm["solver"], arm["seed"], s, records.RUNS)]
  if not todo:
    print(f"{arm['label']} seed {arm['seed']}: both splits already recorded"); return
  if env_check:
    check_environment(fz)
  spec = modelspec.load(model)
  task = get_task("haggling")
  t0 = time.time()
  s = make_solver(load_backend(spec), arm)
  dev = preflight(task, s, arm, spec)
  print("solver_config_sha256", hashlib.sha256(json.dumps(s.describe(), sort_keys=True, default=str).encode()).hexdigest(), flush=True)
  for split in todo:
    rec = evaluate(task, s, split, arm["seed"], spec, {"step": "test2 look", "arm": arm["label"], "freeze": os.path.relpath(freeze_path(model), ROOT),
                                                        "preflight_tune_max_abs_prob_diff": dev}, token)
    print(f"{arm['label']} seed {arm['seed']} {split}: written {rec['_written_to']}", flush=True)
  print(f"arm done in {time.time() - t0:.0f}s", flush=True)


def references(token):
  from harness import records
  from harness.evaluate import evaluate
  from harness.solvers import cpu
  from harness.task import get_task
  task = get_task("haggling")
  mk = {"oracle": cpu.OracleSolver, "uniform": cpu.UniformSolver,
        "baseline:cheapest": lambda: cpu.BaselineSolver(policy="cheapest"),
        "baseline:stated_cost_rule": lambda: cpu.BaselineSolver(policy="stated_cost_rule")}
  for split in SPLITS:
    for name in REFS:
      have = existing(None, name, 0, split, records.RUNS)
      if len(have) > 1:
        raise SystemExit(f"two reference records for {name} {split}: {have}")
      if have:
        print(f"reference {name} {split}: already recorded"); continue
      rec = evaluate(task, mk[name](), split, 0, None, {"step": "test2 look reference"}, token)
      if name == "oracle" and not rec["planted"]["all_ok"]:
        raise SystemExit("STOP: the oracle fails a planted case (pipeline)")
      print(f"reference {name} {split}: {rec['_written_to']}")


def commit_records(model, what):
  git("add", "runs/haggling/none", f"runs/haggling/{model}")
  if git("diff", "--cached", "--quiet").returncode:
    r = git("commit", "-q", "-m", f"test2 look {model}: {what} (records written by scripts/test2_look.py)")
    if r.returncode:
      raise SystemExit(f"could not commit the records: {r.stderr}")
    print("committed:", what, flush=True)


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
    fz, problems = check_freeze(a.model, committed=True)
    for x in fz["arms"]:
      print(f"{x['label']:22s} {x['solver']:38s} seed {x['seed']}  " + (x["adapter"]["weights_sha256"][:16] if x["adapter"] else "no adapter"))
    print("environment:", fz["environment"], "| model pin:", fz["model_revision"])
    print("problems:", problems or "none")
    return
  if not (a.lock_token or "").startswith("G3-OWNER-GO:"):
    raise SystemExit("the look needs --lock-token G3-OWNER-GO:<date> (G3 and the owner's explicit go)")
  if not os.environ.get("HARNESS_PIN_REF"):
    raise SystemExit("the look needs HARNESS_PIN_REF (the owner's scorer pin tag)")
  if a.one is not None:
    run_one(a.model, a.one, a.lock_token); return
  if a.look:
    fz, problems = check_freeze(a.model, committed=True, tree_clean=True)
    if problems:
      raise SystemExit("freeze check failed (nothing written): " + "; ".join(problems))
    references(a.lock_token)
    commit_records(a.model, "references")
    for i, arm in enumerate(fz["arms"]):
      r = subprocess.run([sys.executable, os.path.abspath(__file__), "--model", a.model, "--one", str(i), "--lock-token", a.lock_token], cwd=ROOT)
      commit_records(a.model, f"{arm['label']} seed {arm['seed']}")
      if r.returncode:
        raise SystemExit(f"arm {i} stopped (exit {r.returncode}); later arms not run. Rerun --look to resume (only splits without a record).")
    print("LOOK DONE for", a.model)


if __name__ == "__main__":
  main()
