#!/usr/bin/env python3
"""GPU readout parity: the new harness solver must reproduce the stored pre-refactor numbers BEFORE it is used for any new number.

Tolerances are fixed here (and in DECISIONS.md) before the run:
  per case: max |p_new - p_old| over the five options <= MAX_ABS_PROB      (order-averaged probabilities)
  headline: |mean soft regret new - old| <= MAX_ABS_REGRET
  planted:  all planted cases pass in the new record
Known, accepted differences of design: the old code also scored whole answers and trimmed long prompts; the harness reads the first token only.

  # on the GPU box (model weights present, pinned revision, nothing else using the GPU):
  python -m harness.run --task haggling --solver plain --model gemma2_9b --split tune
  python tools/parity_check.py runs/haggling/gemma2_9b/<the new plain-tune record>.json  [--legacy runs/haggling/gemma2_9b/legacy-plain-tune-s0.json]
  # then the same with --solver lora --kw '{"adapter_dir": "demo_out/adapters/<name>"}' against legacy-<arm>-tune-s<seed>-preflight.json
Exit 0 only if every check holds. The CPU part (compare) is unit-tested in tests/harness/test_parity_compare.py."""
import json, os, sys

MAX_ABS_PROB = 1e-3
MAX_ABS_REGRET = 0.005
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def compare(new, old):
  """-> (ok, report dict). `new` and `old` are run records of the same task/split."""
  a = {r["cid"]: r for r in new["cases"] if not r["planted"]}
  b = {r["cid"]: r for r in old["cases"] if not r["planted"]}
  rep = {"missing_in_new": sorted(set(b) - set(a)), "extra_in_new": sorted(set(a) - set(b))}
  worst, worst_cid = 0.0, None
  for cid in set(a) & set(b):
    d = max(abs(x - y) for x, y in zip(a[cid]["probs"], b[cid]["probs"]))
    if d > worst:
      worst, worst_cid = d, cid
  m = lambda rs: sum(r["score"]["soft_regret"] for r in rs.values()) / len(rs)
  rep.update(max_abs_prob_diff=worst, worst_case=worst_cid, regret_new=m(a), regret_old=m(b),
             regret_diff=abs(m(a) - m(b)), planted_all_ok=new["planted"]["all_ok"], letter_mass_ok=new["letter_mass"]["ok"])
  ok = (not rep["missing_in_new"] and not rep["extra_in_new"] and worst <= MAX_ABS_PROB and rep["regret_diff"] <= MAX_ABS_REGRET
        and rep["planted_all_ok"] is True and rep["letter_mass_ok"])
  rep["tolerances"] = {"max_abs_prob": MAX_ABS_PROB, "max_abs_regret": MAX_ABS_REGRET}
  return ok, rep


def main(argv):
  new = json.load(open(argv[0]))
  legacy = argv[argv.index("--legacy") + 1] if "--legacy" in argv else os.path.join(
      ROOT, "runs", new["task"], new["model"], f"legacy-plain-{new['split']}-s0.json")
  ok, rep = compare(new, json.load(open(legacy)))
  print(json.dumps(rep, indent=1)); print("PARITY OK" if ok else "PARITY FAILED")
  return 0 if ok else 1


if __name__ == "__main__":
  sys.exit(main(sys.argv[1:]))
