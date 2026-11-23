#!/usr/bin/env python3
"""Independent recompute of headline numbers from RAW per-case outputs. Standard library only: imports nothing from harness/,
refimpl/ or demo/ (so a bug or edit there cannot reach it). It re-derives the payoffs from each case's stored inputs with its
own copy of the payoff rule, then soft regret = best payoff - sum(p * payoff).

  python tools/recompute.py runs/            # every record; exit 1 on any disagreement
  python tools/recompute.py runs/x.json --json
"""
import json, math, os, sys

TOL = 1e-9


def payoffs(task, c):
  if task == "haggling":
    out = []
    for k in c["grid"]:
      if c["C"] is not None:
        out.append(float(c["V"] - k) if k >= c["C"] else 0.0)
      else:
        lo, hi = c["prior"]
        out.append((c["V"] - k) * min(1.0, max(0.0, (k - lo + 1) / (hi - lo + 1))))
    return out
  if task == "parity":
    return [1.0 if v % c["modulus"] == c["target"] else 0.0 for v in c["options"]]
  raise SystemExit(f"recompute.py has no independent payoff rule for task {task!r}; add one here (and keep it independent)")


def recompute(rec):
  rows = [r for r in rec["cases"] if not r["planted"]]
  soft, hard, by = [], [], {}
  problems = []
  for r in rec["cases"]:
    pay = payoffs(rec["task"], r["inputs"])
    if any(abs(a - b) > TOL for a, b in zip(pay, r["payoffs"])):
      problems.append(f"{r['cid']}: stored payoffs differ from the independent rule")
    p = r["probs"]
    if len(p) != len(pay):
      problems.append(f"{r['cid']}: {len(p)} probabilities for {len(pay)} options"); continue
    po = r.get("per_order_probs")
    if po:
      mean = [sum(o[i] for o in po) / len(po) for i in range(len(p))]
      if any(abs(a - b) > 1e-9 for a, b in zip(mean, p)):
        problems.append(f"{r['cid']}: probs differ from the mean of per_order_probs")
    if abs(sum(p) - 1) > 1e-6:
      problems.append(f"{r['cid']}: probabilities sum to {sum(p)}")
    sr = max(pay) - sum(a * b for a, b in zip(p, pay))
    if abs(sr - r["score"]["soft_regret"]) > TOL:
      problems.append(f"{r['cid']}: soft regret {r['score']['soft_regret']} stored, {sr} recomputed")
    top = max(range(len(p)), key=lambda i: (p[i], -i))
    hr = max(pay) - pay[top]
    if abs(hr - r["score"]["hard_regret"]) > TOL:
      problems.append(f"{r['cid']}: hard regret {r['score']['hard_regret']} stored, {hr} recomputed")
    if not r["planted"]:
      soft.append(sr); hard.append(hr); by.setdefault(r["type"], []).append(sr)
  m = lambda x: sum(x) / len(x) if x else None
  out = {"n_cases": len(rows), "soft_regret_mean": m(soft), "hard_regret_mean": m(hard),
         "by_type": {k: {"n": len(v), "soft_regret_mean": m(v)} for k, v in sorted(by.items())}}
  for k, v in out["by_type"].items():
    sv = rec["summary"]["by_type"].get(k)
    if sv is None or sv["n"] != v["n"] or abs(sv["soft_regret_mean"] - v["soft_regret_mean"]) > TOL:
      problems.append(f"by_type {k}: stored {sv}, recomputed {v}")
  ids = [r["cid"] for r in rec["cases"]]
  if len(ids) != len(set(ids)):
    problems.append("duplicate case ids")
  s = rec["summary"]
  for k in ("n_cases", "soft_regret_mean", "hard_regret_mean"):
    if (out[k] is None) != (s[k] is None) or (out[k] is not None and abs(out[k] - s[k]) > TOL):
      problems.append(f"summary {k}: stored {s[k]}, recomputed {out[k]}")
  return out, problems


def main(argv):
  paths = []
  for a in argv:
    if a.startswith("--"):
      continue
    if os.path.isdir(a):
      paths += [os.path.join(dp, f) for dp, _, fs in os.walk(a) for f in fs if f.endswith(".json")]
    else:
      paths.append(a)
  bad = 0
  for p in sorted(paths):
    rec = json.load(open(p))
    out, problems = recompute(rec)
    print(("FAIL " if problems else "ok   ") + p + f"  soft={out['soft_regret_mean']}")
    for q in problems[:10]:
      print("   ", q)
    bad += bool(problems)
  return 1 if bad else 0


if __name__ == "__main__":
  sys.exit(main(sys.argv[1:]))
