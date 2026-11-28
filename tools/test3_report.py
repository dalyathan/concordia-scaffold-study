"""Report of the one test3 look of the targeted experiment (TARGETED_PLAN.md). Written and tested on synthetic records BEFORE the look.

  python tools/test3_report.py [--model qwen25_7b]           writes TARGETED_TEST3_RESULTS.md and demo_out/targeted_test3_report.json
  python tools/test3_report.py [--model qwen25_7b] --check   exit 1 if the markdown differs from what the records give

Arms (test3 records, config step "test3 look"): T, R, N (solver lora:claude_examples_n150_<arm>_lr3e-04, seeds 0-2), A0 (the
examples-100 adapters, seeds 0-2), plain, and the references (oracle, uniform, always-cheapest, stated-cost rule; step "test3 look
reference"); only records with those step tags are read, and exactly one per (arm, seed). Arm E is not in this look (DECISIONS.md T3).
A frozen arm with a missing seed makes every rule that uses it "not concluded" (crashed runs are reported, never rerun).

Statistics (frozen):
  per case: soft regret from payoffs and the order- and name-averaged probabilities; arm value per case = mean over its seeds.
  two-level bootstrap: for each resample, draw each arm's seeds with replacement, then (V, grid) groups with replacement, within the slice;
    PCG64 seed 0, 10,000 resamples; 95% percentile interval of the mean difference.
  permutation: group sign-flip of the seed-mean case differences, 10,000 flips, PCG64 seed 0, two-sided, (k + 1) / (B + 1).
  readout gate (every rule): "not concluded (readout)" if any seed of an adapter the rule uses has mean letter mass < 0.90 on its cases.
  With three seeds the seed level has 27 resampling combinations, so the two-level interval stays narrow at that level; the every-seed
  condition of H1 is there for that reason (stated in the report).
Rules: H1 (primary, test3 no-cost cases): for T - R and for T - N: mean < 0, interval below 0, p < 0.05 and every seed's T_s - X_s mean < 0.
  H2 (below + at-or-above pooled): upper bound of T - R and of T - N <= +0.10. H3 (no-cost): T beats always-cheapest (mean < 0, interval
  below 0, p < 0.05), also reported for R, N, A0. Seeds are paired by seed id for the every-seed condition.
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
  out, seen = [], {}
  for d, step in ((model, "test3 look"), ("none", "test3 look reference")):
    for p in sorted(glob.glob(os.path.join(root, "runs", "haggling", d, "*.json"))):
      r = json.load(open(p))
      if r.get("split") == "test3" and (r.get("config") or {}).get("step") == step:
        k = (r["solver"], r["seed"])
        if k in seen:
          raise SystemExit(f"two test3 records for {k}: {seen[k]} and {p}")
        if not (r.get("lock_token") or "").startswith("G3-OWNER-GO:"):
          raise SystemExit(f"test3 record without a lock token: {p}")
        seen[k] = p; r["_path"] = os.path.relpath(p, root); out.append(r)
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
    for r, rec in zip(rows, recs):
      for c in self.cids:
        if not r[c].get("letter_mass") or any(m is None for m in r[c]["letter_mass"]):
          raise SystemExit(f"{rec['_path']}: case {c} has no letter mass")
    self.M = np.array([[float(np.mean(r[c]["letter_mass"])) for c in self.cids] for r in rows])
    self.seeds = [r["seed"] for r in recs]
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
  """T_s - X_s on the kept cases, paired by seed id (not array position)"""
  return {s: float(a.S[a.seeds.index(s), idx].mean() - b.S[b.seeds.index(s), idx].mean()) for s in sorted(set(a.seeds) & set(b.seeds))}


def mass_ok(arms, idx):
  """every seed of every adapter the rule uses has mean letter mass >= 0.90 on the rule's cases"""
  return all(float(a.M[s, idx].mean()) >= MASS_MIN for a in arms if a is not None for s in range(a.M.shape[0]))


def f3(x): return "-" if x is None else f"{x:.3f}"
def fci(t): return "-" if t is None else f"{t[0]:.3f} [{t[1]:.3f}, {t[2]:.3f}]"


SEEDS = (0, 1, 2)
FULL = ("T", "R", "N", "A0")
PRED = {"Q1": 0.7, "Q2": 0.55, "Q3": 0.75, "Q4": 0.4, "Q5": 0.65, "Q6": 0.4, "Q7": 0.7, "Q8": 0.7}


def extras_by_seed(model, root=ROOT):
  """(arm, seed) -> set of (V, grid) of that run's extra cells, from the committed draws file"""
  p = os.path.join(root, "demo", "gen", f"targeted_draws_{model}.json")
  if not os.path.exists(p):
    return {}
  d = json.load(open(p))
  cells = {c["cell"]: c for c in json.load(open(os.path.join(ROOT, "demo", "gen", "pool3_cells.json")))["cells"]}
  return {(k.split("_s")[0], int(k.split("_s")[1])): {(cells[c]["V"], cells[c]["grid_name"]) for c in v} for k, v in d["draws"].items()}


def h_rule(a, b, idx, every_seed):
  m, lo, hi = two_level(a, b, idx); p = perm(a, b, idx)
  cond = {"mean < 0": m < 0, "interval below 0": hi < 0, "p < 0.05": p < P_MAX}
  ps = None
  if every_seed:
    ps = per_seed(a, b, idx)
    cond["every seed below"] = len(ps) == len(SEEDS) and all(v < 0 for v in ps.values())
  return {"mean": m, "ci": [lo, hi], "p": p, "per_seed": ps, "conditions": cond}


def build(model, recs, root=ROOT):
  sol = arm_solvers(model)
  A, missing = {}, []
  for name, s in sol.items():
    if name == "E":
      continue
    rs = [r for r in recs if r["solver"] == s]
    if name in FULL and sorted(r["seed"] for r in rs) != list(SEEDS):
      missing.append(f"{name} (seeds present: {sorted(r['seed'] for r in rs)})")
    if rs:
      A[name] = Arm(rs)
  J = {"model": model, "missing": missing,
       "arms": {k: {"records": [r["_path"] for r in v.recs], "seeds": v.seeds} for k, v in A.items()}}
  out = [f"# TARGETED_TEST3_RESULTS: the one test3 look of the targeted experiment ({model}; generated by tools/test3_report.py)", "",
         "Soft regret in coins (lower is better), forced-choice letter, five orders and two name variants per cell. Rules and wording were "
         "fixed before the look (TARGETED_PLAN.md; this file's docstring). Intervals: two-level bootstrap (arm seeds, then (V, grid) groups); "
         "with three seeds the seed level has only 27 combinations, so the interval is narrow at that level and H1 also needs every seed "
         "to agree. Arm E is not in this look; last-epoch adapters are tune-only.", ""]
  if not all(k in A for k in ("T", "R", "N")):
    out += ["**No complete look yet** (arms present: " + ", ".join(sorted(A)) + ").", ""]
    J["status"] = "incomplete"
    return "\n".join(out) + "\n", J
  if missing:
    out += ["**Incomplete arms:** " + "; ".join(missing) + ". Rules that use them are not concluded.", ""]
  T = A["T"]
  for k in A:
    assert A[k].cids == T.cids, f"{k} scored other cases"
  NC = idx_of(T, lambda c: c["type"] == "no_cost"); OT = idx_of(T, lambda c: c["type"] != "no_cost")
  full = lambda k: k in A and not any(m.startswith(k + " ") for m in missing)
  out += ["| arm | seeds | all cases | no-cost | below | at or above | letter mass (min over seeds) |", "| --- | --- | --- | --- | --- | --- | --- |"]
  for k, a in A.items():
    by = {t: a.mean(idx_of(a, lambda c, t=t: c["type"] == t)) for t in ("no_cost", "below", "at_or_above")}
    out.append(f"| {k} | {len(a.seeds)} | {a.mean(np.arange(len(a.cids))):.3f} | {by['no_cost']:.3f} | {by['below']:.3f} | {by['at_or_above']:.3f} | {min(a.mass):.3f} |")
    J["arms"][k].update({"all": a.mean(np.arange(len(a.cids))), **by, "mass_min": min(a.mass),
                         "per_seed_no_cost": {s: float(a.S[i, NC].mean()) for i, s in enumerate(a.seeds)}})
  out.append("")
  res = {}
  for X in ("R", "N"):
    if not (full("T") and full(X)):
      res[X] = {"holds": None, "reason": "missing seed"}; continue
    h = h_rule(T, A[X], NC, True)
    h["readout_ok"] = mass_ok([T, A[X]], NC)
    h["holds"] = all(h["conditions"].values()) if h["readout_ok"] else None
    h2 = two_level(T, A[X], OT)
    h["H2"] = {"mean": h2[0], "ci": [h2[1], h2[2]], "readout_ok": mass_ok([T, A[X]], OT),
               "holds": (h2[2] <= H2_MARGIN) if mass_ok([T, A[X]], OT) else None}
    res[X] = h
    out.append(f"**T minus {X}, no-cost cases:** {fci((h['mean'], *h['ci']))}, p {h['p']:.4f}, per seed "
               + ", ".join(f"s{s} {v:.3f}" for s, v in h["per_seed"].items()) + "; "
               + "; ".join(f"{k}: {'yes' if v else 'no'}" for k, v in h["conditions"].items()) + f"; readout ok: {'yes' if h['readout_ok'] else 'no'}. "
               f"Other types (H2): {fci(h2)} (bound <= +{H2_MARGIN}: {'yes' if h2[2] <= H2_MARGIN else 'no'}; readout ok: {'yes' if h['H2']['readout_ok'] else 'no'}).")
  out.append("")
  J["H1"] = res
  if res["R"]["holds"] is None or res["N"]["holds"] is None:
    key = "not_concluded"
  else:
    key = {(True, True): "both", (True, False): "R_only", (False, True): "N_only", (False, False): "neither"}[(res["R"]["holds"], res["N"]["holds"])]
  h2s = [res[X].get("H2", {}).get("holds") for X in ("R", "N")]
  h2 = None if None in h2s else all(h2s)
  H3 = {}
  ac = A.get("always-cheapest")
  if ac is not None:
    for k in ("T", "R", "N", "A0"):
      if full(k):
        h = h_rule(A[k], ac, NC, False)
        ok = mass_ok([A[k]], NC)
        H3[k] = {**h, "readout_ok": ok, "holds": all(h["conditions"].values()) if ok else None}
    out += ["**H3 (no-cost cases, minus always-cheapest):** " + "; ".join(f"{k} {fci((v['mean'], *v['ci']))} p {v['p']:.4f} "
            f"({'holds' if v['holds'] else ('not concluded' if v['holds'] is None else 'not shown')})" for k, v in H3.items()), ""]
  J["H3"] = H3
  wording = WORDING[key] + "; " + (WORDING["H2_holds"] if h2 else WORDING["H2_fails"] if h2 is False else "harm elsewhere not concluded")
  J["conclusion"] = {"H1": key, "H2": h2, "wording": wording}
  out += ["## Conclusion (wording fixed before the look)", "", f"**{wording}.**", "",
          "'Not shown' means the frozen test did not establish it, not that it is absent.", ""]
  out += descriptive(A, NC, model, root, J)
  out += predictions(A, res, H3, J, NC, OT)
  return "\n".join(out) + "\n", J


def descriptive(A, NC, model, root, J):
  """Frozen descriptive tables (G1): no-cost regret by V band and grid, the extras stratum, planted no-cost mass per adapter."""
  T = A["T"]
  out = ["## Descriptive (no rule)", "", "No-cost cases by V band and grid, seed means:", "",
         "| slice | n cases | " + " | ".join(k for k in A if k not in ("oracle",)) + " |", "| --- | --- | " + " | ".join("---" for k in A if k != "oracle") + " |"]
  J["descriptive"] = {"slices": {}, "extras_stratum": {}, "planted_nocost": {}}
  slices = [("V 2-9", lambda c: c["V"] <= 9), ("V 10-15", lambda c: c["V"] >= 10)] + \
           [(f"grid {g}", lambda c, g=g: c["inputs"]["grid_name"] == g) for g in "ABCDEF"]
  for nm, fn in slices:
    idx = np.array([i for i in NC if fn(T.case[T.cids[i]]["inputs"] if nm.startswith("V") else T.case[T.cids[i]])])
    if len(idx) == 0:
      continue
    vals = {k: a.mean(idx) for k, a in A.items() if k != "oracle"}
    J["descriptive"]["slices"][nm] = {"n": int(len(idx)), **vals}
    out.append(f"| {nm} | {len(idx)} | " + " | ".join(f"{v:.3f}" for v in vals.values()) + " |")
  ex = extras_by_seed(model, root)
  if ex:
    out += ["", "Extras stratum (no-cost cases; is the test cell's (V, grid) among that run's extra cells?), mean over seeds:", "",
            "| arm | yes: n, regret | no: n, regret |", "| --- | --- | --- |"]
    for X in ("T", "R", "N"):
      if X not in A:
        continue
      a = A[X]; yes, no = [], []
      for si, s in enumerate(a.seeds):
        for i in NC:
          x = a.case[a.cids[i]]["inputs"]
          (yes if (x["V"], x["grid_name"]) in ex.get((X, s), set()) else no).append(float(a.S[si, i]))
      J["descriptive"]["extras_stratum"][X] = {"yes": [len(yes), float(np.mean(yes)) if yes else None], "no": [len(no), float(np.mean(no)) if no else None]}
      out.append(f"| {X} | {len(yes)}, {f3(np.mean(yes) if yes else None)} | {len(no)}, {f3(np.mean(no) if no else None)} |")
  out += ["", "Planted no-cost case: mass on the expected options per adapter (passes at >= 0.9):", "", "| arm | per seed |", "| --- | --- |"]
  for k, a in A.items():
    if k in ("oracle", "uniform", "always-cheapest", "stated-cost rule"):
      continue
    ms = {}
    for r in a.recs:
      x = next((y for y in r["cases"] if y["planted"] and y["cid"] == "planted-nocost"), None)
      if x is not None:
        ms[r["seed"]] = float(x["planted_mass_on_expected"])
    J["descriptive"]["planted_nocost"][k] = ms
    out.append(f"| {k} | " + ", ".join(f"s{s} {v:.2f}" for s, v in ms.items()) + " |")
  return out + [""]


def predictions(A, res, H3, J, NC, OT):
  """TARGETED_PREDICTIONS.md, each scored by ITS OWN definition (G1): Q2 is T - R only (mean, interval, p); Q3 uses +0.05."""
  T, R, A0 = A.get("T"), A.get("R"), A.get("A0")
  rows = {}
  if T and R:
    d = T.mean(NC) - R.mean(NC); rows["Q1"] = -0.40 <= d <= 0.00
    m, lo, hi = two_level(T, R, NC); rows["Q2"] = m < 0 and hi < 0 and perm(T, R, NC) < P_MAX
    rows["Q3"] = two_level(T, R, OT)[2] <= 0.05
  if "T" in H3:
    rows["Q4"] = bool(H3["T"]["holds"])
  if R and A0:
    rows["Q5"] = R.mean(NC) - A0.mean(NC) < 0
  if T:
    ms = J["descriptive"]["planted_nocost"].get("T", {})
    rows["Q6"] = sum(v >= 0.9 for v in ms.values()) >= 2
    rows["Q8"] = 0.05 <= T.mean(NC) <= 0.45
  if A0:
    rows["Q7"] = 0.15 <= A0.mean(NC) <= 0.70
  brier = float(np.mean([(PRED[k] - float(v)) ** 2 for k, v in rows.items()])) if rows else None
  J["predictions"] = {"outcomes": rows, "brier": brier}
  return ["## Predictions (TARGETED_PREDICTIONS.md, each by its own definition)", "", "| id | probability | outcome |", "| --- | --- | --- |"] + \
         [f"| {k} | {PRED[k]} | {'yes' if v else 'no'} |" for k, v in sorted(rows.items())] + ["", f"Brier score: {f3(brier)}.", ""]


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
