"""Report of the one test3 look of the targeted experiment (TARGETED_PLAN.md). Written and tested on synthetic records BEFORE the look.

  python tools/test3_report.py [--model qwen25_7b]           writes TARGETED_TEST3_RESULTS.md and demo_out/targeted_test3_report.json
  python tools/test3_report.py [--model qwen25_7b] --check   exit 1 if the markdown differs from what the records give

Arms (test3 records, config step "test3 look"): T, R, N (solver lora:claude_examples_n150_<arm>_lr3e-04, seeds 0-2), A0 (the
examples-100 adapters, seeds 0-2), plain, and the references (oracle, uniform, always-cheapest, stated-cost rule; step "test3 look
reference"). Arm E is added when its record exists (one edit, group resampling only).

Statistics (frozen):
  per case: soft regret from payoffs and the order- and name-averaged probabilities; arm value per case = mean over its seeds.
  two-level bootstrap: for each resample, draw each arm's seeds with replacement, then (V, grid) groups with replacement, within the slice;
    PCG64 seed 0, 10,000 resamples; 95% percentile interval of the mean difference.
  permutation: group sign-flip of the seed-mean case differences, 10,000 flips, PCG64 seed 0, two-sided, (k + 1) / (B + 1).
  readout gate: a rule is "not concluded (readout)" if any adapter it uses has mean first-token letter mass < 0.90 on its cases.
Rules: H1 (primary, test3 no-cost cases): for T - R and for T - N: mean < 0, interval below 0, p < 0.05 and every seed's T_s - X_s mean < 0.
  H2 (below + at-or-above pooled): upper bound of T - R and of T - N <= +0.10. H3 (no-cost): T beats always-cheapest (mean < 0, interval
  below 0, p < 0.05), also reported for R, N, A0. E-H1 / E-H2 for arm E against A0 seed 0 (group resampling only).
Wording is fixed in WORDING below."""
from __future__ import annotations

import glob
import hashlib
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
B, MASS_MIN, P_MAX, H2_MARGIN = 10000, 0.90, 0.05, 0.10
LR = {"qwen25_7b": "3e-04"}
WORDING = {
    "both": "examples aimed by Claude at the model's failures fix them better than the same number of random examples, and better than random examples of the failing type",
    "R_only": "adding examples of the failing type helps; Claude's aiming was not shown to add to that",
    "N_only": "Claude's examples beat random examples of the failing type but were not shown to beat random examples of every type",
    "neither": "aiming the extra examples was not shown to beat random ones",
    "not_concluded": "the targeting comparison is not concluded",
    "H2_holds": "no large harm elsewhere", "H2_fails": "harm elsewhere not excluded",
    "E_holds": "a single edit Claude chose and computed closed part of the gap without retraining", "E_fails": "a direct edit was not shown to help"}


def soft(x):
  return max(x["payoffs"]) - float(np.dot(x["payoffs"], x["probs"]))


def group(x):
  return (x["inputs"]["V"], x["inputs"]["grid_name"])


def load(model, root=ROOT):
  out = []
  for d in (model, "none"):
    for p in sorted(glob.glob(os.path.join(root, "runs", "haggling", d, "*.json"))):
      r = json.load(open(p))
      if r.get("split") == "test3":
        r["_path"] = os.path.relpath(p, root); out.append(r)
  return out


def arm_solvers(model):
  lr = LR[model]
  return {"T": f"lora:claude_examples_n150_T_lr{lr}", "R": f"lora:claude_examples_n150_R_lr{lr}", "N": f"lora:claude_examples_n150_N_lr{lr}",
          "A0": f"lora:claude_examples_n100_lr{lr}", "plain": "plain", "E": "edit:E",
          "oracle": "oracle", "uniform": "uniform", "always-cheapest": "baseline:cheapest", "stated-cost rule": "baseline:stated_cost_rule"}


class Arm:
  """per-seed per-case soft regret and letter mass on the (non-planted) test3 cases"""
  def __init__(self, recs):
    recs = sorted(recs, key=lambda r: r["seed"])
    rows = [{x["cid"]: x for x in r["cases"] if not x["planted"]} for r in recs]
    self.cids = sorted(rows[0])
    assert all(sorted(r) == self.cids for r in rows), "seeds cover different cases"
    self.case = {c: rows[0][c] for c in self.cids}
    self.S = np.array([[soft(r[c]) for c in self.cids] for r in rows])          # seeds x cases
    self.M = np.array([[float(np.mean([m for m in (r[c]["letter_mass"] or [1.0]) if m is not None] or [1.0])) for c in self.cids] for r in rows])
    self.mass = [float(v) for v in self.M.mean(1)]
    self.recs = recs

  def mean(self, idx):
    return float(self.S[:, idx].mean())


def idx_of(arm, keep):
  return np.array([i for i, c in enumerate(arm.cids) if keep(arm.case[c])])


def two_level(a, b, idx, rng_seed=0):
  """mean of (a - b) over the kept cases; 95% interval resampling each arm's seeds then (V, grid) groups; b may be a one-record arm"""
  rng = np.random.Generator(np.random.PCG64(rng_seed))
  groups = [group(a.case[a.cids[i]]) for i in idx]
  gs = sorted(set(groups)); gi = np.array([gs.index(g) for g in groups])
  sa = rng.integers(0, a.S.shape[0], size=(B, a.S.shape[0]))
  sb = rng.integers(0, b.S.shape[0], size=(B, b.S.shape[0]))
  gg = rng.integers(0, len(gs), size=(B, len(gs)))
  A = a.S[:, idx]; Bm = b.S[:, idx]
  stats = np.empty(B)
  for k in range(B):
    d = A[sa[k]].mean(0) - Bm[sb[k]].mean(0)
    S = np.bincount(gi, weights=d, minlength=len(gs)); N = np.bincount(gi, minlength=len(gs))
    stats[k] = S[gg[k]].sum() / N[gg[k]].sum()
  mean = float(A.mean(0).mean() - Bm.mean(0).mean())
  return mean, float(np.percentile(stats, 2.5)), float(np.percentile(stats, 97.5))


def perm(a, b, idx):
  d = a.S[:, idx].mean(0) - b.S[:, idx].mean(0)
  groups = [group(a.case[a.cids[i]]) for i in idx]
  gs = sorted(set(groups)); gi = np.array([gs.index(g) for g in groups])
  S = np.bincount(gi, weights=d, minlength=len(gs)); n = len(d)
  obs = abs(S.sum() / n)
  flips = np.random.Generator(np.random.PCG64(0)).choice([-1.0, 1.0], size=(B, len(gs)))
  return (int((np.abs((flips * S).sum(1) / n) >= obs - 1e-12).sum()) + 1) / (B + 1)


def per_seed(a, b, idx):
  return [float(a.S[s, idx].mean() - b.S[s, idx].mean()) for s in range(min(a.S.shape[0], b.S.shape[0]))]


def mass_ok(arms, idx):
  """every seed of every adapter the rule uses has mean letter mass >= 0.90 on the rule's cases"""
  return all(float(a.M[s, idx].mean()) >= MASS_MIN for a in arms if a is not None for s in range(a.M.shape[0]))


def f3(x): return "-" if x is None else f"{x:.3f}"
def fci(t): return "-" if t is None else f"{t[0]:.3f} [{t[1]:.3f}, {t[2]:.3f}]"


def build(model, recs):
  sol = arm_solvers(model)
  A = {}
  for name, s in sol.items():
    rs = [r for r in recs if r["solver"] == s]
    if rs:
      A[name] = Arm(rs)
  J = {"model": model, "arms": {k: {"records": [r["_path"] for r in v.recs], "seeds": [r["seed"] for r in v.recs]} for k, v in A.items()}}
  out = [f"# TARGETED_TEST3_RESULTS: the one test3 look of the targeted experiment ({model}; generated by tools/test3_report.py)", "",
         "Soft regret in coins (lower is better), forced-choice letter, five orders and two name variants per cell. Rules and wording were "
         "fixed before the look (TARGETED_PLAN.md; this file's docstring). Intervals: two-level bootstrap (arm seeds, then (V, grid) groups).", ""]
  need = ("T", "R", "N")
  if not all(k in A for k in need):
    out += ["**No complete look yet** (arms present: " + ", ".join(sorted(A)) + ").", ""]
    J["status"] = "incomplete"
    return "\n".join(out) + "\n", J
  T = A["T"]
  NC = idx_of(T, lambda c: c["type"] == "no_cost"); OT = idx_of(T, lambda c: c["type"] != "no_cost")
  for k in A:
    assert A[k].cids == T.cids, f"{k} scored other cases"
  out += ["| arm | seeds | all cases | no-cost | below | at or above | letter mass (min over seeds) |", "| --- | --- | --- | --- | --- | --- | --- |"]
  for k, a in A.items():
    by = {t: a.mean(idx_of(a, lambda c, t=t: c["type"] == t)) for t in ("no_cost", "below", "at_or_above")}
    out.append(f"| {k} | {a.S.shape[0]} | {a.mean(np.arange(len(a.cids))):.3f} | {by['no_cost']:.3f} | {by['below']:.3f} | {by['at_or_above']:.3f} | {min(a.mass):.3f} |")
    J["arms"][k].update({"all": a.mean(np.arange(len(a.cids))), **by, "mass_min": min(a.mass),
                         "per_seed_no_cost": [float(a.S[s, NC].mean()) for s in range(a.S.shape[0])]})
  out.append("")
  res = {}
  for X in ("R", "N"):
    m, lo, hi = two_level(T, A[X], NC); p = perm(T, A[X], NC); ps = per_seed(T, A[X], NC)
    ok = mass_ok([T, A[X]], NC)
    cond = {"mean < 0": m < 0, "interval below 0": hi < 0, "p < 0.05": p < P_MAX, "every seed below": all(v < 0 for v in ps)}
    res[X] = {"mean": m, "ci": [lo, hi], "p": p, "per_seed": ps, "conditions": cond, "readout_ok": ok,
              "holds": (all(cond.values()) if ok else None)}
    h2 = two_level(T, A[X], OT)
    res[X]["H2"] = {"mean": h2[0], "ci": [h2[1], h2[2]], "holds": h2[2] <= H2_MARGIN}
    out.append(f"**T minus {X}, no-cost cases:** {fci((m, lo, hi))}, p {p:.4f}, per seed {', '.join(f'{v:.3f}' for v in ps)}; "
               + "; ".join(f"{k}: {'yes' if v else 'no'}" for k, v in cond.items()) + f"; readout ok: {'yes' if ok else 'no'}. "
               f"Other types (H2): {fci(h2)} (bound <= +{H2_MARGIN}: {'yes' if h2[2] <= H2_MARGIN else 'no'}).")
  out.append("")
  J["H1"] = res
  if res["R"]["holds"] is None or res["N"]["holds"] is None:
    key = "not_concluded"
  else:
    key = {(True, True): "both", (True, False): "R_only", (False, True): "N_only", (False, False): "neither"}[(res["R"]["holds"], res["N"]["holds"])]
  h2 = res["R"]["H2"]["holds"] and res["N"]["H2"]["holds"]
  H3 = {}
  ac = A.get("always-cheapest")
  if ac is not None:
    for k in ("T", "R", "N", "A0"):
      if k in A:
        m, lo, hi = two_level(A[k], ac, NC); p = perm(A[k], ac, NC)
        H3[k] = {"mean": m, "ci": [lo, hi], "p": p, "holds": m < 0 and hi < 0 and p < P_MAX}
    out += ["**H3 (no-cost cases, minus always-cheapest):** " + "; ".join(f"{k} {fci((v['mean'], *v['ci']))} p {v['p']:.4f} "
            f"({'holds' if v['holds'] else 'not shown'})" for k, v in H3.items()), ""]
  J["H3"] = H3
  if "E" in A and "A0" in A:
    a0s0 = Arm([r for r in A["A0"].recs if r["seed"] == 0])
    m, lo, hi = two_level(A["E"], a0s0, NC); p = perm(A["E"], a0s0, NC); h = two_level(A["E"], a0s0, OT)
    J["E"] = {"mean": m, "ci": [lo, hi], "p": p, "holds": m < 0 and hi < 0 and p < P_MAX and mass_ok([A["E"]], NC), "H2": {"ci": [h[1], h[2]], "holds": h[2] <= H2_MARGIN}}
    out += [f"**Arm E minus A0 seed 0, no-cost cases:** {fci((m, lo, hi))}, p {p:.4f} ({'holds' if J['E']['holds'] else 'not shown'}); "
            f"other types {fci(h)}.", ""]
  wording = WORDING[key] + "; " + WORDING["H2_holds" if h2 else "H2_fails"]
  if "E" in J:
    wording += ". Arm E: " + WORDING["E_holds" if J["E"]["holds"] else "E_fails"]
  J["conclusion"] = {"H1": key, "H2": h2, "wording": wording}
  out += ["## Conclusion (wording fixed before the look)", "", f"**{wording}.**", "",
          "'Not shown' means the frozen test did not establish it, not that it is absent. Descriptive tables (per V band, grid, extras "
          "stratum, planted cases, last-epoch adapters) follow the plan and are added before G2 from the same records.", ""]
  return "\n".join(out) + "\n", J


def main(argv=None):
  argv = sys.argv[1:] if argv is None else argv
  model = argv[argv.index("--model") + 1] if "--model" in argv else "qwen25_7b"
  md, J = build(model, load(model))
  mp, jp = os.path.join(ROOT, "TARGETED_TEST3_RESULTS.md"), os.path.join(ROOT, "demo_out", "targeted_test3_report.json")
  if "--check" in argv:
    ok = os.path.exists(mp) and open(mp).read() == md
    print("up to date" if ok else "DIFFERS"); sys.exit(0 if ok else 1)
  open(mp, "w").write(md); os.makedirs(os.path.dirname(jp), exist_ok=True)
  json.dump(J, open(jp, "w"), indent=1, sort_keys=True, default=float)
  print("wrote", os.path.relpath(mp, ROOT))


if __name__ == "__main__":
  main()
