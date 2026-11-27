"""Import the stored Gemma 2 9B TUNE results needed for the Gemma-vs-Llama table as run records (no model is run, tune only).

Sources (files copied unchanged from branch demo where missing here):
  A10G (the original runs; LLAMA_PREDICTIONS.md quotes these):
    demo_out/gen_text_rows.jsonl                       in-prompt Notes rows method_original, teacher, neutral, wrong_rule (tune cases)
    demo_out/gen_lora/<run>.json  tune_probs_best      LoRA arms (examples N = 25 and 100, cheapest-label N = 25 and 100, shuffled)
  A40 rescore of the same adapters and plain (HARDWARE_PARITY.md on demo):
    demo_out/hw_parity/A40_probs.json  ["gen"][<run>]
Plain on the A10G is already imported (legacy-plain-tune-s0.json). Record names: legacy-gemma-<arm>-tune-s<seed>-<gpu>.

  python tools/import_legacy_gemma_tune.py [--out runs]"""
import argparse, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from harness import records
from harness.tasks.haggling import HagglingTask
from tools.import_legacy import build_record

TEXT_ROWS = ("method_original", "teacher", "neutral", "wrong_rule")
LORA_RUNS = {  # arm label -> (run file stem, seed)
    "claude_examples_n100": [("gen_claude_examples_lr1e-04_s0", 0), ("gen_claude_examples_lr1e-04_s1", 1), ("gen_claude_examples_lr1e-04_s2", 2)],
    "claude_examples_n25": [("gen_claude_examples_n25_lr1e-04_s0", 0), ("gen_claude_examples_n25_lr1e-04_s1", 1), ("gen_claude_examples_n25_lr1e-04_s2", 2)],
    "cheapest_label_n25": [("gen_cheapest_label_n25_lr1e-04_s0", 0)],
    "cheapest_label_n100": [("gen_cheapest_label_lr1e-04_s0", 0)],
    "shuffled_claude_n100": [("gen_shuffled_claude_lr1e-04_s0", 0)],
}


def main():
  ap = argparse.ArgumentParser(); ap.add_argument("--out", default=records.RUNS); a = ap.parse_args()
  task = HagglingTask(); _, cases = task.build_all()
  by_id = {c["cid"]: c for c in cases}
  tune = {c["cid"] for c in cases if c["split"] == "tune"}
  written = []

  def put(arm, seed, gpu, probs, masses, src, extra):
    assert set(probs) == tune, f"{arm}: expected the 84 tune cases"
    rec = build_record(task, by_id, f"gemma-{arm}", "tune", probs, src, seed, {"gpu": gpu, **extra}, masses)
    rec["run_id"] = f"legacy-gemma-{arm}-tune-s{seed}-{gpu.lower()}"
    rec["config"]["note"] = f"Gemma 2 9B-it per-case tune probabilities from the pre-refactor code on the {gpu}; imported, not re-run"
    written.append(records.write(rec, a.out))

  src = "demo_out/gen_text_rows.jsonl"
  rows = {}
  for l in open(os.path.join(ROOT, src)):
    d = json.loads(l)
    if d["split"] == "tune" and d["row"] in TEXT_ROWS:
      rows.setdefault(d["row"], {})[d["cid"]] = (d["probs"], d["mass"])
  for row in TEXT_ROWS:
    put(f"notes_{row}", 0, "A10G", {k: v[0] for k, v in rows[row].items()}, {k: v[1] for k, v in rows[row].items()}, [src], {"row": row})
  a40src = "demo_out/hw_parity/A40_probs.json"
  a40 = json.load(open(os.path.join(ROOT, a40src)))["gen"]
  put("plain", 0, "A40", {k: v["probs"] for k, v in a40["plain"].items()}, {k: v["mass"] for k, v in a40["plain"].items()}, [a40src], {"run": "plain"})
  for arm, runs in LORA_RUNS.items():
    for stem, seed in runs:
      f = f"demo_out/gen_lora/{stem}.json"
      d = json.load(open(os.path.join(ROOT, f)))
      put(arm, seed, "A10G", {k: list(v) for k, v in d["tune_probs_best"].items()}, d.get("tune_mass_best"), [f], {"run": stem, "lr": d["lr"]})
      put(arm, seed, "A40", {k: v["probs"] for k, v in a40[stem].items()}, {k: v["mass"] for k, v in a40[stem].items()}, [a40src], {"run": stem})
  print("records written:", len(written))


if __name__ == "__main__":
  main()
