"""Import the OLD fixed-cell test look (demo_out/test_look_raw.json + demo_out/cases.jsonl, 72 cases, 18 cells) as run records.
No model is run and no split is newly evaluated: these are the stored per-case probabilities of the one look that was already made.
Arm value as in demo/test_look.py: the mean of the seeds' per-case probabilities (plain and the text-in-prompt arm are single runs).

  python -m tools.import_legacy_testlook [--out runs]"""
import argparse, hashlib, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from harness import records
from harness.protected.payoffs import haggling as pay
from harness.protected import scorer
from tools.import_legacy import build_record

TYPE = lambda c: "no cost" if c["C"] is None else ("cost below resale" if c["C"] < c["V"] else "cost at or above resale")


class OldTask:
  """Only what build_record needs."""
  def payoffs(self, case): return pay.payoffs(case)
  def case_type(self, case): return case["type"]


def main():
  ap = argparse.ArgumentParser(); ap.add_argument("--out", default=records.RUNS); a = ap.parse_args()
  raw = json.load(open(os.path.join(ROOT, "demo_out/test_look_raw.json")))
  src = ["demo_out/test_look_raw.json", "demo_out/cases.jsonl"]
  old = {}
  for l in open(os.path.join(ROOT, "demo_out/cases.jsonl")):
    c = json.loads(l)
    old[c["pid"]] = {"cid": c["pid"], "split": "old_test", "type": TYPE(c), "V": c["V"], "grid": [1, 2, 3, 4, 5], "C": c["C"],
                     "prior": [1, 5], "line": c["line"], "buyer": c["buyer"], "seller": c["seller"], "_plain": [c["probs"][str(k)] for k in range(1, 6)]}
  pids = sorted(raw["text_probs"])
  cases = {p: {k: v for k, v in old[p].items() if k != "_plain"} for p in pids}
  vec = lambda d: [d[str(k)] for k in range(1, 6)]
  arms = {"plain": {p: old[p]["_plain"] for p in pids}, "method_text_in_prompt": {p: vec(raw["text_probs"][p]) for p in pids}}
  seeds = {}
  for name, per in raw["per"].items():
    arm, seed = name.rsplit("_s", 1)
    arm = arm.split("_lr")[0]
    seeds.setdefault(arm, {})[int(seed)] = {p: vec(per[p]) for p in pids}
  for arm, bys in seeds.items():
    arms[arm + "_lora_3seed_mean_probs"] = {p: [sum(bys[s][p][i] for s in bys) / len(bys) for i in range(5)] for p in pids}
    for s, probs in bys.items():
      arms[f"{arm}_lora_seed{s}"] = probs
  n = 0
  for arm, probs in sorted(arms.items()):
    rec = build_record(OldTask(), cases, arm, "old_test", probs, src, 0, {"note": "old fixed-cell test look (18 cells, 72 cases); arm = mean of seeds' probabilities where named 3seed_mean_probs"})
    rec["run_id"] = f"legacy-oldtest-{arm}"
    rec["solver"] = f"legacy:oldtest:{arm}"
    records.write(rec, a.out); n += 1
  print("records written:", n)


if __name__ == "__main__":
  main()
