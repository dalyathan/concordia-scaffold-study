"""Freeze record for the learning-curve runs: sha256 of every input, of the reused N = 100 run files and of the code, plus library versions.
  python demo/gen_curve_freeze.py          writes demo/gen/curve_freeze.json (done once, before the first run)
  gen_curve_freeze.verify()                asserts the current files equal the record (the chain calls it; the report calls it)"""
import hashlib, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

ROOT = common.ROOT
PATH = os.path.join(ROOT, "demo", "gen", "curve_freeze.json")
INPUTS = ["demo/gen/curve_subsets.json", "demo/gen/lora_train_cells.json", "demo/gen/lora_select_cells_B.json", "demo/gen/lora_select_cells.json", "demo/gen/packet_cells.json",
          "demo/gen/claude_labels.json", "demo/gen/teacher_method.txt", "demo/gen/cells.json", "demo/gen/cases.jsonl", "demo_out/gen_plain_scores.jsonl", "demo_out/gen_text_rows.jsonl"]
REUSED = [f"demo_out/gen_lora/gen_claude_examples_lr1e-04_s{s}.json" for s in (0, 1, 2)] + [f"demo_out/gen_lora/gen_teacher_lr1e-04_s{s}.json" for s in (0, 1, 2)]
CODE = ["demo/gen_lora.py", "demo/gen_curve.py", "demo/gen_curve_chain.py", "demo/gen_curve_report.py", "demo/gen_curve_freeze.py", "demo/gen_cases.py", "demo/gen_notes.py", "refimpl/core.py", "refimpl/phase3.py",
        "refimpl/local_gemma2.py", "PREDICTIONS.md", "GEN_CURVE_PLAN.md"]
sha = lambda p: hashlib.sha256(open(os.path.join(ROOT, p), "rb").read()).hexdigest()


def versions():
  import torch, transformers, peft
  return {"torch": torch.__version__, "transformers": transformers.__version__, "peft": peft.__version__}


def record():
  return {"inputs": {p: sha(p) for p in INPUTS}, "reused_runs": {p: sha(p) for p in REUSED}, "code": {p: sha(p) for p in CODE}, "versions": versions()}


def verify(code=True):
  d = json.load(open(PATH))
  now = record()
  for k in ("inputs", "reused_runs", "versions") + (("code",) if code else ()):
    assert now[k] == d[k], f"frozen record differs in {k}: {[p for p in now[k] if now[k][p] != d[k].get(p)]}"


if __name__ == "__main__":
  json.dump(record(), open(PATH, "w"), indent=1)
  print("wrote", PATH)
