"""Report of the one test2 look for Llama 3.1 8B or Qwen 2.5 7B (LLAMA_TEST_PLAN.md, QWEN_TEST_PLAN.md). Written and frozen BEFORE the look.

  python tools/test2_report.py --model qwen25_7b            write QWEN_TEST2_RESULTS.md and demo_out/qwen_test2_report.json
  python tools/test2_report.py --model qwen25_7b --check    exit 1 if the files differ from what the records give

Inputs: the test2 records of the model (runs/haggling/<model>/, split test2_same / test2_newkey) and the references
(runs/haggling/none/, config step "test2 look reference"); the frozen arms in demo/gen/test2_freeze_<model>.json; the cell flags in
demo/gen/test2_cells.json. The report refuses to run if any frozen file (this file, tools/llama_report.py, the harness, the plans, the
predictions) differs from its frozen sha256, and it refuses records that are not frozen arms, carry another adapter hash, model pin, step
tag or case list, lack a lock token, or are duplicated. A frozen arm with no record makes the rules that need it "not concluded".
Statistics reuse tools/llama_report.py (soft regret from payoffs and probabilities; seeds averaged per case; 95% cluster bootstrap over
(V, grid) groups, PCG64 seed 0, 10,000 resamples) and its group sign-flip permutation test (PCG64 seed 0, 10,000 flips).

Decision rules, fixed before the look (the same for both models; each model gets its own verdict and the models are never pooled):
  Readout rule: every arm a rule uses (examples-100 seeds, plain, and for T1 scrambled N=100) must have mean first-token letter mass
     >= 0.90 on the cases the rule uses; otherwise that rule is "not concluded (readout)".
  T1 (test2_same) holds if the examples-100 3-seed mean <= 0.15, every seed's mean is below plain, and the paired 95% intervals of
     examples-100 minus plain and minus scrambled N=100 lie entirely below 0. Examples-100 minus the stated-cost rule is reported and is
     not part of T1 (so T1 can hold with a mean above the rule).
  T2a (test2_newkey, slice V 13-15): examples-100 mean below plain, paired interval entirely below 0, and permutation p < 0.05.
  T2b (same slice): the same against the model-free stated-cost rule. On this slice the rule's regret comes only from no-cost cells.
  "Fails" means the frozen test did not show the effect, not that the effect is absent. The other slices, the per-seed checks, the
  seen/unseen key strata and the planted known-answer cases are descriptive."""
from __future__ import annotations

import glob
import hashlib
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "tools"))
import llama_report as LR  # noqa: E402

NAME = {"llama31_8b": "Llama", "qwen25_7b": "Qwen"}
TYPES = ("below", "at_or_above", "no_cost")
REF_LABEL = {"oracle": "oracle", "uniform": "uniform", "baseline:cheapest": "always-cheapest", "baseline:stated_cost_rule": "stated-cost rule"}
T1_MAX, MASS_MIN, P_MAX = 0.15, 0.90, 0.05
V13 = "V 13-15 (T2 slice)"
SLICES = [  # demo/gen_test2.py report slices, in order (they overlap); the V 13-15 slice carries T2a and T2b
    ("training ranges (no novelty)", lambda c: not (c["novel_V"] or c["novel_grid"] or c["novel_wording"])),
    ("new V only (>=10, grids A-C, wordings 0-1)", lambda c: c["novel_V"] and not c["novel_grid"] and not c["novel_wording"]),
    ("new grid F (any V, wordings 0-1)", lambda c: c["novel_grid"] and not c["novel_wording"]),
    ("new wording 3 (any V, grids A-C)", lambda c: c["novel_wording"] and not c["novel_grid"]),
    ("new grid F and new wording 3", lambda c: c["novel_grid"] and c["novel_wording"]),
    (V13, lambda c: c["V_ge_13"])]
T1_TEXT = {"holds": "in-family fit replicates on fresh cells",
           "fails": "the tune result does not replicate on fresh in-family cells",
           "not concluded": "in-family replication is not concluded"}
T2_TEXT = {(True, True): "on the V 13-15 cells (which also carry grid F or the new seller wording in part) the examples-100 adapters beat both plain "
                         "and the model-free stated-cost rule",
           (True, False): "on the V 13-15 cells they improve on plain but are not shown to beat the model-free stated-cost rule",
           (False, True): "on the V 13-15 cells they beat the stated-cost rule but an improvement over plain is not shown",
           (False, False): "on the V 13-15 cells an improvement over plain is not shown"}
T2_NC = "on the V 13-15 cells the comparison is not concluded"


def paths(model):
  n = NAME[model]
  return os.path.join(ROOT, f"{n.upper()}_TEST2_RESULTS.md"), os.path.join(ROOT, "demo_out", f"{n.lower()}_test2_report.json")


def f3(x): return "-" if x is None else f"{x:.3f}"
def fci(t): return "-" if t is None else f"{t[0]:.3f} [{t[1]:.3f}, {t[2]:.3f}]"
def sha_file(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()


def self_check(freeze):
  bad = [f for f, h in freeze["file_sha256"].items() if sha_file(os.path.join(ROOT, f)) != h]
  if bad:
    raise SystemExit(f"frozen files changed since the freeze: {bad}")


def load_records(model, root=ROOT):
  own = [LR.load(p) for p in sorted(glob.glob(os.path.join(root, "runs", "haggling", model, "*.json")))]
  ref = [LR.load(p) for p in sorted(glob.glob(os.path.join(root, "runs", "haggling", "none", "*.json")))]
  own = [r for r in own if r.get("split") in ("test2_same", "test2_newkey")]
  ref = [r for r in ref if r.get("split") in ("test2_same", "test2_newkey")]
  return own, ref


def check(own, ref, freeze):
  """Refuse anything that is not exactly the frozen look; return the set of (solver, seed, split) present."""
  frozen = {(a["solver"], a["seed"]): a for a in freeze["arms"]}
  seen, case_sha = {}, {}
  ref_ids = {id(x) for x in ref}
  for r in own + ref:
    is_ref = id(r) in ref_ids
    if not (r.get("lock_token") or "").startswith("G3-OWNER-GO:"):
      raise SystemExit(f"test2 record without a lock token: {r['_path']}")
    step = (r.get("config") or {}).get("step")
    if step != ("test2 look reference" if is_ref else "test2 look"):
      raise SystemExit(f"test2 record with step {step!r}: {r['_path']}")
    if is_ref:
      if r["solver"] not in REF_LABEL:
        raise SystemExit(f"unknown reference: {r['_path']}")
    else:
      a = frozen.get((r["solver"], r["seed"]))
      if a is None:
        raise SystemExit(f"record of an arm that is not frozen: {r['_path']}")
      if a["adapter"] and r["solver_config"].get("adapter_weights_sha256") != a["adapter"]["weights_sha256"]:
        raise SystemExit(f"adapter hash differs from the freeze: {r['_path']}")
      if r["solver_config"].get("revision") != freeze["model_revision"]:
        raise SystemExit(f"model pin differs from the freeze: {r['_path']}")
    k = (r["solver"], r["seed"] if not is_ref else None, r["split"])
    if k in seen:
      raise SystemExit(f"two records for {k}: {seen[k]} and {r['_path']}")
    seen[k] = r["_path"]
    h = r["input_hashes"]["cases_sha256"]
    if case_sha.setdefault(r["split"], h) != h:
      raise SystemExit(f"{r['_path']} scored another case list than the other {r['split']} records")
  return set(seen)


def arms_for(split, own, ref, freeze):
  """Arms whose records are complete for this split; an incomplete arm is left out (its rules are then not concluded)."""
  A = {}
  for solver, label in REF_LABEL.items():
    rs = [r for r in ref if r["solver"] == solver and r["split"] == split]
    if rs:
      A[label] = LR.Arm(rs, label)
  by_label = {}
  for a in freeze["arms"]:
    by_label.setdefault(a["label"], []).append(a)
  for label, fa in by_label.items():
    rs = [r for a in fa for r in own if (r["solver"], r["seed"], r["split"]) == (a["solver"], a["seed"], split)]
    if len(rs) == len(fa):
      A[label] = LR.Arm(sorted(rs, key=lambda r: r["seed"]), label)
  return A


def ci_subset(values, cases, keep):
  sub = {c: v for c, v in values.items() if keep(c)}
  return LR.ci_mean(sub, cases) if sub else None


def paired(a, b, keep=lambda c: True):
  assert a.cids == b.cids, f"{a.label} vs {b.label}: different cases"
  return ci_subset({c: a.soft[c] - b.soft[c] for c in a.cids}, a.case, keep)


def perm(a, b, keep=lambda c: True):
  """two-sided group sign-flip permutation p of the paired mean difference on the kept cases (as llama_report.perm_p)."""
  cids = [c for c in a.cids if keep(c)]
  d = {c: a.soft[c] - b.soft[c] for c in cids}
  gs = sorted({LR.group(a.case[c]) for c in cids})
  S = np.array([sum(d[c] for c in cids if LR.group(a.case[c]) == g) for g in gs]); n = len(cids)
  obs = abs(S.sum() / n)
  flips = np.random.Generator(np.random.PCG64(0)).choice([-1.0, 1.0], size=(LR.B, len(gs)))
  return (int((np.abs((flips * S).sum(1) / n) >= obs - 1e-12).sum()) + 1) / (LR.B + 1)


def n_groups(arm, keep=lambda c: True):
  return len({LR.group(arm.case[c]) for c in arm.cids if keep(c)})


def mass(arm, keep=lambda c: True):
  """mean and min over records and kept cases of the case's mean first-token letter mass (None for model-free arms)."""
  vals = []
  for r in arm.recs:
    for x in LR.rows(r):
      if keep(x["cid"]) and x.get("letter_mass") and all(m is not None for m in x["letter_mass"]):
        vals.append(float(np.mean(x["letter_mass"])))
  return (float(np.mean(vals)), float(np.min(vals))) if vals else (None, None)


def mass_ok(arms, keep=lambda c: True):
  return all((mass(a, keep)[0] or 0) >= MASS_MIN for a in arms)


def planted_rows(arm):
  from harness.tasks.haggling import HagglingTask
  expected = HagglingTask().planted_expected()
  out = []
  for r in arm.recs:
    for x in r["cases"]:
      if x["planted"]:
        top_ok = x["score"]["top_option"] in expected[x["cid"]]
        out.append((r["seed"], x["cid"], "correct" if top_ok else "incorrect", x["planted_mass_on_expected"], x["planted_ok"]))
  return out


# ------------------------------------------------------------------ predictions (TEST2_PREDICTIONS.md), scored by a fixed rule
def score_predictions(model, J):
  """Each prediction is a yes/no event with a stated probability; a range prediction's event is 'the point estimate lies in the range'.
  Reported: the event's outcome per prediction and the Brier score over the model's scorable predictions. Not scorable -> left out."""
  S, N = J.get("test2_same", {}), J.get("test2_newkey", {})
  e = S.get("examples-100"); v13 = N.get(V13, {})
  inr = lambda x, lo, hi: None if x is None else lo <= x <= hi
  get = lambda d, *k: (d.get(k[0]) if len(k) == 1 else get(d.get(k[0]) or {}, *k[1:])) if isinstance(d, dict) else None
  L = model == "llama31_8b"
  out = []
  def add(pid, text, p, outcome):
    out.append({"id": pid, "prediction": text, "p": p, "outcome": outcome})
  ex = e["soft"] if e else None
  add("P1" if L else "P2", "test2_same examples-100 mean in " + ("0.03-0.15" if L else "0.04-0.18"), 0.8 if L else 0.75,
      inr(ex, 0.03, 0.15) if L else inr(ex, 0.04, 0.18))
  t1 = J.get("T1", {}).get("result")
  add("P3" if L else "P4", "T1 holds", 0.8 if L else 0.7, None if t1 in (None, "not concluded") else t1 == "holds")
  st = S.get("strata", {})
  add("P5", "examples-100: key-unseen stratum worse than key-seen", 0.75,
      None if not st else st["unseen"]["examples-100"] > st["seen"]["examples-100"])
  add("P6" if L else "P7", "V 13-15 examples-100 mean in " + ("0.10-0.80" if L else "0.10-0.90"), 0.7, inr(v13.get("ex100"), 0.10, 0.80 if L else 0.90))
  dp = v13.get("ex100_minus_plain")
  add("P8", "V 13-15: examples-100 below plain with the paired interval below 0", 0.85,
      None if dp is None else (v13["ex100"] < v13["plain"] and dp[2] < 0))
  dr = v13.get("ex100_minus_rule")
  add("P9" if L else "P10", "examples-100 below the stated-cost rule on V 13-15 with the interval below 0 (the 'T2' of the predictions)", 0.35 if L else 0.3,
      None if dr is None else (v13["ex100"] < v13["rule"] and dr[2] < 0))
  w3, tr = N.get("new wording 3 (any V, grids A-C)", {}), N.get("training ranges (no novelty)", {})
  add("P11", "new wording 3 slice within 0.10 of the training-ranges slice (examples-100)", 0.7,
      None if not (w3 and tr) else abs(w3["ex100"] - tr["ex100"]) <= 0.10)
  pl = J.get("planted_nocost_ex100")
  add("P12", "every examples-100 adapter fails the planted no-cost case on both splits", 0.85, None if pl is None else all(not ok for ok in pl))
  sc = get(S, "scrambled N=100", "soft")
  add("P13", "scrambled N=100 at least 0.3 worse than examples-100 on test2_same", 0.9, None if (sc is None or ex is None) else sc - ex >= 0.3)
  scored = [x for x in out if x["outcome"] is not None]
  brier = float(np.mean([(x["p"] - float(x["outcome"])) ** 2 for x in scored])) if scored else None
  return out, brier


def build(model, own, ref, freeze, cells):
  out, J = [], {"model": model}
  n = NAME[model]
  flag = {c["cell"]: c for c in cells}
  out += [f"# {n.upper()}_TEST2_RESULTS: the one look at test2 for {n} (generated by tools/test2_report.py; do not edit by hand)", "",
          "Every number is soft regret in coins (lower is better) from the forced-choice letter (the config's assistant prefix), "
          "five cyclic orders and the two stored name variants per cell, as on tune. Intervals: 95% cluster bootstrap over (V, grid) groups "
          "within each slice (PCG64 seed 0, 10,000 resamples); they leave out seed-to-seed variance, so the per-seed values are given next to "
          "the 3-seed mean. Rules and wording were fixed before the look (tools/test2_report.py docstring, "
          f"{freeze['plan']}). This is {n}'s own verdict; the models are not pooled.", ""]
  rp = os.path.join(ROOT, "demo_out", f"{n.lower()}_report.json")
  if os.path.exists(rp):
    T = json.load(open(rp))
    ag = [T[k]["agreement_on_parsed"] for k in sorted(T) if k.startswith("freegen_adapter/")]
    out += [f"Readout (from tune probe prompts, not test): forced-choice letter agrees with the free answer on {T['freegen']['agreement_on_parsed']:.2f} "
            f"of prompts for plain {n} and on " + ", ".join(f"{v:.2f}" for v in ag) + " for the examples-100 adapters.", ""]
  if not own and not ref:
    out += ["**No look yet.** No test2 record exists for this model.", ""]
    J["status"] = "no look"
    return "\n".join(out) + "\n", J
  present = check(own, ref, freeze)
  missing = [(a["label"], a["seed"], s) for a in freeze["arms"] for s in ("test2_same", "test2_newkey") if (a["solver"], a["seed"], s) not in present]
  if missing:
    out += ["**Incomplete look.** Frozen arms without a record: " + "; ".join(f"{l} seed {s} on {sp}" for l, s, sp in missing) +
            ". Rules that need them are not concluded.", ""]
  J["missing"] = missing
  order = ["oracle", "uniform", "always-cheapest", "stated-cost rule", "plain", "examples-100", "scrambled N=100", "cheapest-label N=100"]
  planted_nc = []
  for split in ("test2_same", "test2_newkey"):
    A = arms_for(split, own, ref, freeze)
    J[split] = {}
    out += [f"## {split}", ""]
    out += ["| arm | n cases | soft regret [95%] | below | at or above | no cost | hard regret | per seed | letter mass mean / min | planted |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for label in order:
      a = A.get(label)
      if a is None:
        out.append(f"| {label} | not run | | | | | | | | |"); continue
      ps = ", ".join(f"{v:.3f}" for v in a.seed_soft) if len(a.recs) > 1 else "-"
      mm = mass(a)
      out.append(f"| {label} | {len(a.cids)} | {fci(LR.ci_mean(a.soft, a.case))} | " + " | ".join(f3(a.mean(t)) for t in TYPES) +
                 f" | {f3(a.mean(metric='hard'))} | {ps} | {f3(mm[0])} / {f3(mm[1])} | {LR.planted(a.recs)} |")
      J[split][label] = {"soft": a.mean(), "ci": LR.ci_mean(a.soft, a.case), "by_type": {t: a.mean(t) for t in TYPES},
                         "hard": a.mean(metric="hard"), "per_seed": a.seed_soft, "mass": mm, "records": [r["_path"] for r in a.recs]}
    out.append("")
    e, p, rule, sc = A.get("examples-100"), A.get("plain"), A.get("stated-cost rule"), A.get("scrambled N=100")
    if split == "test2_same":
      if e and p and sc:
        out += [f"{n_groups(e)} (V, grid) groups.", ""]
        dp, ds = paired(e, p), paired(e, sc)
        dr = paired(e, rule) if rule else None
        J[split]["paired"] = {"ex100_minus_plain": dp, "ex100_minus_scrambled": ds, "ex100_minus_rule": dr}
        out += ["| examples-100 minus | difference [95%] |", "| --- | --- |", f"| plain | {fci(dp)} |", f"| scrambled N=100 | {fci(ds)} |",
                f"| stated-cost rule (reported, not part of T1) | {fci(dr)} |", ""]
        seen = lambda c: flag[e.case[c]["inputs"]["cell"]]["key_in_lora100"]
        J[split]["strata"] = {}
        rows_ = []
        for key, nm, keep in (("seen", "label key seen in the 100 LoRA cells", seen), ("unseen", "label key not seen", lambda c: not seen(c))):
          k = [c for c in e.cids if keep(c)]
          vals = {"n": len(k), "examples-100": float(np.mean([e.soft[c] for c in k])), "plain": float(np.mean([p.soft[c] for c in k]))}
          J[split]["strata"][key] = vals
          rows_.append(f"| {nm} | {vals['n']} | {vals['examples-100']:.3f} | {vals['plain']:.3f} |")
        out += ["| stratum | n cases | examples-100 | plain |", "| --- | --- | --- | --- |", *rows_, ""]
        cond = {"mean <= 0.15": e.mean() <= T1_MAX, "every seed below plain": all(v < p.mean() for v in e.seed_soft),
                "examples-100 minus plain interval below 0": dp[2] < 0, "examples-100 minus scrambled interval below 0": ds[2] < 0}
        rok = mass_ok([e, p, sc])
        res = "not concluded" if not rok else ("holds" if all(cond.values()) else "fails")
        J["T1"] = {"conditions": cond, "readout_ok": rok, "result": res}
        out += ["**T1:** " + "; ".join(f"{k}: {'yes' if v else 'no'}" for k, v in cond.items()) +
                f"; readout (mass >= {MASS_MIN}): {'yes' if rok else 'no'} -> **T1 {res}**.", ""]
      else:
        J["T1"] = {"result": "not concluded", "reason": "an arm T1 needs has no complete record"}
        out += ["**T1 not concluded:** an arm it needs has no complete record.", ""]
    else:
      out += ["Never one pooled number: each pre-declared slice separately. Slices overlap (a cell can carry several novelties).", "",
              "| slice | n cases | groups | examples-100 (per seed) | plain | stated-cost rule | scrambled N=100 | ex100 minus plain [95%] (perm p) | ex100 minus rule [95%] (perm p) | ex100 mass mean / min |",
              "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
      for nm, fn in SLICES:
        if not (e and p and rule):
          out.append(f"| {nm} | not run | | | | | | | | |"); continue
        keep = lambda c, fn=fn: fn(flag[e.case[c]["inputs"]["cell"]])
        k = [c for c in e.cids if keep(c)]
        if not k:
          out.append(f"| {nm} | 0 | | | | | | | | |"); continue
        m = lambda a: float(np.mean([a.soft[c] for c in k]))
        per = [float(np.mean([LR.soft(x) for x in LR.rows(r) if keep(x["cid"])])) for r in e.recs]
        dp, dr = paired(e, p, keep), paired(e, rule, keep)
        pp, pr = perm(e, p, keep), perm(e, rule, keep)
        mm = mass(e, keep)
        out.append(f"| {nm} | {len(k)} | {n_groups(e, keep)} | {m(e):.3f} ({', '.join(f'{v:.3f}' for v in per)}) | {m(p):.3f} | {m(rule):.3f} | "
                   f"{f3(m(sc) if sc else None)} | {fci(dp)} ({pp:.3f}) | {fci(dr)} ({pr:.3f}) | {f3(mm[0])} / {f3(mm[1])} |")
        J[split][nm] = {"n": len(k), "groups": n_groups(e, keep), "ex100": m(e), "ex100_per_seed": per, "plain": m(p), "rule": m(rule),
                        "scrambled": m(sc) if sc else None, "ex100_minus_plain": dp, "ex100_minus_rule": dr, "perm_p_plain": pp, "perm_p_rule": pr,
                        "ex100_mass": mm}
        if nm == V13:
          cs = [flag[e.case[c]["inputs"]["cell"]] for c in k]
          comp = {"cells": len({c["cell"] for c in cs}), "by_type": {t: len({c["cell"] for c in cs if c["type"] == t}) for t in TYPES},
                  "grid_F": len({c["cell"] for c in cs if c["novel_grid"]}), "wording_3": len({c["cell"] for c in cs if c["novel_wording"]})}
          rok = mass_ok([e, p], keep)
          a_ = m(e) < m(p) and dp[2] < 0 and pp < P_MAX
          b_ = m(e) < m(rule) and dr[2] < 0 and pr < P_MAX
          seeds = []
          for r, v in zip(e.recs, per):
            ea = LR.Arm([r], "seed"); seeds.append({"seed": r["seed"], "mean": v, "minus_plain": paired(ea, p, keep), "minus_rule": paired(ea, rule, keep)})
          J["T2"] = {"composition": comp, "readout_ok": rok, "T2a": a_, "T2b": b_, "per_seed": seeds,
                     "result": "not concluded" if not rok else {"T2a": "holds" if a_ else "fails", "T2b": "holds" if b_ else "fails"}}
      out.append("")
      if "T2" in J:
        T = J["T2"]; c = T["composition"]
        out += [f"V 13-15 slice: {c['cells']} cells (below {c['by_type']['below']}, at or above {c['by_type']['at_or_above']}, no cost {c['by_type']['no_cost']}); "
                f"{c['grid_F']} on grid F, {c['wording_3']} with the new seller wording. The stated-cost rule has zero regret on below and at-or-above cells, "
                "so T2b is decided by the no-cost cells.", "",
                "Per seed (descriptive): " + "; ".join(f"seed {s['seed']}: {s['mean']:.3f}, minus plain {fci(s['minus_plain'])}, minus rule {fci(s['minus_rule'])}" for s in T["per_seed"]) + ".", ""]
        if T["result"] == "not concluded":
          out += [f"**T2 not concluded (readout):** an arm's mean letter mass on the slice is below {MASS_MIN}.", ""]
        else:
          out += [f"**T2a (beats plain):** {T['result']['T2a']}. **T2b (beats the stated-cost rule):** {T['result']['T2b']}. "
                  f"Each needs the mean lower, the paired interval below 0 and permutation p < {P_MAX}.", ""]
      else:
        J["T2"] = {"result": "not concluded", "reason": "an arm T2 needs has no complete record"}
        out += ["**T2 not concluded:** an arm it needs has no complete record.", ""]
    out += [f"Planted cases on {split} (not part of any rule):", "", "| arm | seed | case | top pick | mass on expected | passes (mass >= 0.9) |", "| --- | --- | --- | --- | --- | --- |"]
    for label in ("plain", "examples-100", "scrambled N=100", "cheapest-label N=100"):
      if A.get(label):
        for seed, cid, top, mss, ok in planted_rows(A[label]):
          out.append(f"| {label} | {seed} | {cid} | {top} | {mss:.2f} | {'yes' if ok else 'no'} |")
          if label == "examples-100" and cid == "planted-nocost":
            planted_nc.append(ok)
    out.append("")
  J["planted_nocost_ex100"] = planted_nc if len(planted_nc) == 6 else None
  t1 = J["T1"]["result"]
  t2 = J["T2"]["result"]
  s2 = T2_NC if t2 == "not concluded" else T2_TEXT[(t2["T2a"] == "holds", t2["T2b"] == "holds")]
  J["conclusion"] = {"T1": t1, "T2": t2, "wording": f"{T1_TEXT[t1]}; {s2}"}
  out += ["## Conclusion (wording fixed before the look)", "", f"**{n}: {T1_TEXT[t1]}; {s2}.**", "",
          "'Not shown' means the frozen test did not establish the effect, not that it is absent. Gemma numbers on test2, if any, come from a "
          "different scoring script and are description only.", ""]
  preds, brier = score_predictions(model, J)
  J["predictions"] = {"items": preds, "brier": brier}
  out += ["## Predictions (TEST2_PREDICTIONS.md; scored by the rule in this file)", "", "| id | prediction | probability | outcome |", "| --- | --- | --- | --- |"]
  out += [f"| {x['id']} | {x['prediction']} | {x['p']} | {'-' if x['outcome'] is None else ('yes' if x['outcome'] else 'no')} |" for x in preds]
  out += ["", f"Brier score over the scorable predictions: {f3(brier)} (0 is perfect; always saying 0.5 scores 0.25).", ""]
  return "\n".join(out) + "\n", J


def main(argv=None):
  argv = sys.argv[1:] if argv is None else argv
  model = argv[argv.index("--model") + 1]
  freeze = json.load(open(os.path.join(ROOT, "demo", "gen", f"test2_freeze_{model}.json")))
  self_check(freeze)
  cells = json.load(open(os.path.join(ROOT, "demo", "gen", "test2_cells.json")))["cells"]
  own, ref = load_records(model)
  md, J = build(model, own, ref, freeze, cells)
  mp, jp = paths(model)
  js = json.dumps(J, indent=1, sort_keys=True, default=float) + "\n"
  if "--check" in argv:
    ok = os.path.exists(mp) and open(mp).read() == md and os.path.exists(jp) and open(jp).read() == js
    print("up to date" if ok else "DIFFERS"); sys.exit(0 if ok else 1)
  open(mp, "w").write(md); os.makedirs(os.path.dirname(jp), exist_ok=True); open(jp, "w").write(js)
  print("wrote", os.path.relpath(mp, ROOT), os.path.relpath(jp, ROOT))


if __name__ == "__main__":
  main()
