"""Compare the rescored tune probabilities (demo/hw_parity.py output) with the stored A10G numbers. CPU only.

  PYTHONPATH=concordia:. .venv/bin/python demo/hw_parity_report.py demo_out/hw_parity/A40_probs.json
Writes demo_out/hw_parity/summary.json and prints a markdown table.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import common
import gen_cases as g
import steer_lib
from refimpl import core

THRESH = 0.005          # coins, soft regret per arm
PREC = 3                # stated precision of reported soft regrets (gen_lora_report.md, gen_examples_report.md, lora_report.md)


def gen_summary(probs, cases, cells):
  per_cell = {}
  for c in cases:
    lab = cells[c["cell"]]
    per_cell.setdefault(c["cell"], []).append(float(lab["best_payoff"] - np.dot(probs[c["cid"]], lab["payoffs"])))
  cm = {k: float(np.mean(v)) for k, v in per_cell.items()}
  by = {t: float(np.mean([v for k, v in cm.items() if cells[k]["type"] == t])) for t in g.TYPES}
  return float(np.mean(list(cm.values()))), by, cm


def otype(p):
  return "no_cost" if p.C is None else ("below" if p.C < p.V else "at_or_above")


def orig_summary(probs, cases):
  per_cell, typ = {}, {}
  for p in cases:
    per_cell.setdefault(p.cell, []).append(core.soft_regret(p, {int(k): v for k, v in probs[p.pid].items()}))
    typ[p.cell] = otype(p)
  cm = {k: float(np.mean(v)) for k, v in per_cell.items()}
  by = {t: float(np.mean([v for k, v in cm.items() if typ[k] == t])) for t in sorted(set(typ.values()))}
  return float(np.mean(list(cm.values()))), by, cm


def compare(a10, a40, keys, vec):
  d = np.array([abs(x - y) for k in keys for x, y in zip(vec(a10[k]), vec(a40[k]))])
  return float(d.max()), float(d.mean())


def flips(x, y):
  return round(x, PREC) != round(y, PREC)


def main():
  new = json.load(open(sys.argv[1]))
  cells = {c["cell"]: c for c in json.load(open(os.path.join(g.OUT, "cells.json")))["cells"]}
  gcases = [c for c in map(json.loads, open(os.path.join(g.OUT, "cases.jsonl"))) if c["split"] == "tune"]
  ocases = steer_lib.lora_cases("lora_tune")
  rows = []
  # references
  ref_gen = {"plain": {r["cid"]: r["probs"] for r in map(json.loads, open(os.path.join(common.ROOT, "demo_out", "gen_plain_scores.jsonl"))) if r["split"] == "tune"}}
  stored_summ = {}
  for f in sorted(os.listdir(os.path.join(common.ROOT, "demo_out", "gen_lora"))):
    r = json.load(open(os.path.join(common.ROOT, "demo_out", "gen_lora", f)))
    ref_gen[r["run_id"]] = r["tune_probs_best"]; stored_summ[r["run_id"]] = r["tune_full_best"]
  ref_orig, plains = {}, []
  for f in sorted(os.listdir(os.path.join(common.ROOT, "demo_out", "lora"))):
    if f.startswith("teacher_"):
      continue
    r = json.load(open(os.path.join(common.ROOT, "demo_out", "lora", f)))
    ref_orig[r["run_id"]] = r["tune_probs_best"]; stored_summ["orig:" + r["run_id"]] = r["tune_best"]
    if r["history"][0].get("tune_probs"):
      plains.append(r["history"][0]["tune_probs"])
  plain_ref_spread = max(abs(a[k][j] - b[k][j]) for a in plains for b in plains for k in a for j in a[k])
  ref_orig["plain"] = plains[0]
  for ds, ref, cases, summ, vec, keyf in (
      ("gen", ref_gen, gcases, lambda pr: gen_summary(pr, gcases, cells), lambda v: v, lambda c: c["cid"]),
      ("orig", ref_orig, ocases, lambda pr: orig_summary(pr, ocases), lambda v: [v[k] for k in sorted(v)], lambda p: p.pid)):
    for arm in ["plain"] + sorted(k for k in ref if k != "plain"):
      if arm not in new[ds]:
        rows.append({"ds": ds, "arm": arm, "missing": True}); continue
      a40 = {k: v["probs"] for k, v in new[ds][arm].items()}
      keys = [keyf(c) for c in cases]
      mx, mn = compare(ref[arm], a40, keys, vec)
      s10, b10, c10 = summ(ref[arm]); s40, b40, c40 = summ(a40)
      # the recomputed A10G summary must equal what the run file stored (checks this script's regret code)
      st = stored_summ.get(arm if ds == "gen" else "orig:" + arm)
      if st is not None:
        assert abs(st["soft_regret"] - s10) < 1e-9, (arm, st["soft_regret"], s10)
      cell_d = {k: c40[k] - c10[k] for k in c10}
      kmax = max(cell_d, key=lambda k: abs(cell_d[k]))
      mass10 = None
      rows.append({"ds": ds, "arm": arm, "max_abs_prob": mx, "mean_abs_prob": mn, "soft_a10g": s10, "soft_a40": s40, "d_soft": s40 - s10,
                   "by_type_a10g": b10, "by_type_a40": b40, "d_by_type": {t: b40[t] - b10[t] for t in b10},
                   "max_cell": str(kmax), "max_cell_d": cell_d[kmax],
                   "flips_3dp": [n for n, x, y in [("overall", s10, s40)] + [(t, b10[t], b40[t]) for t in b10] if flips(x, y)],
                   "argmax_changes": sum(int(np.argmax(vec(ref[arm][k])) != np.argmax(vec(a40[k]))) for k in keys)})
  rep = new["gen"].get("repeat:gen_teacher_lr1e-04_s0")
  repeat_identical = rep is not None and all(rep[k]["probs"] == new["gen"]["gen_teacher_lr1e-04_s0"][k]["probs"] for k in rep)
  ok = [r for r in rows if not r.get("missing")]
  verdict = {"all_scored": all(not r.get("missing") for r in rows),
             "max_abs_d_soft": max(abs(r["d_soft"]) for r in ok),
             "max_abs_d_soft_by_type": max(abs(v) for r in ok for v in r["d_by_type"].values()),
             "arms_over_threshold": [r["arm"] for r in ok if abs(r["d_soft"]) >= THRESH],
             "arms_with_3dp_flips": {r["ds"] + ":" + r["arm"]: r["flips_3dp"] for r in ok if r["flips_3dp"]},
             "repeat_teacher_bit_identical": repeat_identical, "orig_plain_reference_spread_a10g": plain_ref_spread}
  json.dump({"gpu": new["gpu"], "rows": rows, "verdict": verdict, "sec": new["sec"]}, open(os.path.join(os.path.dirname(sys.argv[1]), "summary.json"), "w"), indent=1)
  print("| Data | Arm | max abs dp | mean abs dp | soft A10G | soft A40 | Δ soft | Δ below | Δ at/above | Δ no-cost | largest cell Δ | argmax changes | 3-dp flips |")
  print("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
  for r in rows:
    if r.get("missing"):
      print(f"| {r['ds']} | {r['arm']} | MISSING |"); continue
    dt = r["d_by_type"]
    print(f"| {r['ds']} | {r['arm']} | {r['max_abs_prob']:.1e} | {r['mean_abs_prob']:.1e} | {r['soft_a10g']:.4f} | {r['soft_a40']:.4f} | {r['d_soft']:+.1e} | "
          f"{dt.get('below', float('nan')):+.1e} | {dt.get('at_or_above', float('nan')):+.1e} | {dt.get('no_cost', float('nan')):+.1e} | {r['max_cell_d']:+.1e} | {r['argmax_changes']} | {','.join(r['flips_3dp']) or '-'} |")
  print(json.dumps(verdict, indent=1))


if __name__ == "__main__":
  main()
