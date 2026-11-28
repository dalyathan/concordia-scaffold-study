"""Report of the one test2 look for Llama 3.1 8B or Qwen 2.5 7B (LLAMA_TEST_PLAN.md, QWEN_TEST_PLAN.md). Written and frozen BEFORE the look.

  python tools/test2_report.py --model qwen25_7b            write QWEN_TEST2_RESULTS.md and demo_out/qwen_test2_report.json
  python tools/test2_report.py --model qwen25_7b --check    exit 1 if the files differ from what the records give

Inputs: the test2 records of the model (runs/haggling/<model>/, split test2_same / test2_newkey) and the references
(runs/haggling/none/, config step "test2 look reference"); the frozen arms in demo/gen/test2_freeze_<model>.json; the cell flags in
demo/gen/test2_cells.json. Every GPU record must carry the frozen adapter weight hash and a lock token, and there must be exactly one
record per (arm, seed, split); otherwise the report stops. Statistics reuse tools/llama_report.py (soft regret from payoffs and
probabilities; seeds averaged per case; 95% cluster bootstrap over (V, grid) groups, PCG64 seed 0, 10,000 resamples).

Decision rules and the conclusion wording are copied from the plans and fixed here before the look:
  T1 (test2_same): examples-100 3-seed mean <= 0.15, every seed's mean below plain, and the paired 95% intervals of examples-100 minus
     plain and minus scrambled N=100 entirely below 0. Examples-100 minus the stated-cost rule is reported, not part of T1.
  T2 (test2_newkey, primary slice V 13-15): examples-100 mean below plain and below the stated-cost rule, with both paired intervals
     entirely below 0. The other slices are descriptive; test2_newkey is never pooled into one number.
  Planted cases are reported per adapter (top pick correct or not, mass on the expected options) and are not part of T1 or T2."""
from __future__ import annotations

import glob
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
T1_MAX = 0.15
SLICES = [  # demo/gen_test2.py report slices, in order; the V 13-15 slice is the primary T2 slice
    ("training ranges (no novelty)", lambda c: not (c["novel_V"] or c["novel_grid"] or c["novel_wording"])),
    ("new V only (>=10, grids A-C, wordings 0-1)", lambda c: c["novel_V"] and not c["novel_grid"] and not c["novel_wording"]),
    ("new grid F (any V, wordings 0-1)", lambda c: c["novel_grid"] and not c["novel_wording"]),
    ("new wording 3 (any V, grids A-C)", lambda c: c["novel_wording"] and not c["novel_grid"]),
    ("new grid F and new wording 3", lambda c: c["novel_grid"] and c["novel_wording"]),
    ("V 13-15 (primary T2 slice)", lambda c: c["V_ge_13"])]
WORDING = {
    "T1 holds, T2 fails": "in-family fit replicates on fresh cells; no evidence of generalisation to new values",
    "both hold": "generalises to V 13-15 on the forced-choice readout",
    "T1 fails": "the tune result does not replicate on fresh in-family cells",
    "T1 holds, T2 untestable": "in-family fit replicates on fresh cells; generalisation not judged (T2 slice incomplete)"}


def paths(model):
  n = NAME[model]
  return os.path.join(ROOT, f"{n.upper()}_TEST2_RESULTS.md"), os.path.join(ROOT, "demo_out", f"{n.lower()}_test2_report.json")


def f3(x): return "-" if x is None else f"{x:.3f}"
def fci(t): return "-" if t is None else f"{t[0]:.3f} [{t[1]:.3f}, {t[2]:.3f}]"


def load_records(model, root=ROOT):
  own = [LR.load(p) for p in sorted(glob.glob(os.path.join(root, "runs", "haggling", model, "*.json")))]
  ref = [LR.load(p) for p in sorted(glob.glob(os.path.join(root, "runs", "haggling", "none", "*.json")))]
  own = [r for r in own if r.get("split") in ("test2_same", "test2_newkey")]
  ref = [r for r in ref if r.get("split") in ("test2_same", "test2_newkey") and (r.get("config") or {}).get("step") == "test2 look reference"]
  return own, ref


def check(own, freeze):
  """Every record is a frozen arm with the frozen adapter, written under a lock token; one record per (arm, seed, split)."""
  frozen = {(a["solver"], a["seed"]): a for a in freeze["arms"]}
  seen = {}
  for r in own:
    k = (r["solver"], r["seed"], r["split"])
    if (r["solver"], r["seed"]) not in frozen:
      raise SystemExit(f"record of an arm that is not frozen: {r['_path']}")
    a = frozen[(r["solver"], r["seed"])]
    if a["adapter"] and r["solver_config"].get("adapter_weights_sha256") != a["adapter"]["weights_sha256"]:
      raise SystemExit(f"adapter hash differs from the freeze: {r['_path']}")
    if not (r.get("lock_token") or "").startswith("G3-OWNER-GO:"):
      raise SystemExit(f"test2 record without a lock token: {r['_path']}")
    if k in seen:
      raise SystemExit(f"two records for {k}: {seen[k]} and {r['_path']}")
    seen[k] = r["_path"]


def arms_for(split, own, ref, freeze):
  A = {}
  for solver, label in REF_LABEL.items():
    rs = [r for r in ref if r["solver"] == solver and r["split"] == split]
    if rs:
      A[label] = LR.Arm(rs[:1], label)
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
  if not sub:
    return None
  return LR.ci_mean(sub, cases)


def paired(a, b, keep=lambda c: True):
  assert a.cids == b.cids, f"{a.label} vs {b.label}: different cases"
  return ci_subset({c: a.soft[c] - b.soft[c] for c in a.cids}, a.case, keep)


def n_groups(arm, keep=lambda c: True):
  return len({LR.group(arm.case[c]) for c in arm.cids if keep(c)})


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


def build(model, own, ref, freeze, cells):
  out, J = [], {"model": model}
  n = NAME[model]
  flag = {c["cell"]: c for c in cells}
  out += [f"# {n.upper()}_TEST2_RESULTS: the one look at test2 for {n} (generated by tools/test2_report.py; do not edit by hand)", "",
          "Every number is soft regret in coins (lower is better) from the forced-choice letter (the config's assistant prefix), "
          "five cyclic orders and the two stored name variants per cell, as on tune. Intervals: 95% cluster bootstrap over (V, grid) groups "
          "within each slice (PCG64 seed 0, 10,000 resamples); they leave out seed-to-seed variance, so the per-seed values are given next to "
          "the 3-seed mean. Decision rules and wording were fixed before the look (tools/test2_report.py docstring, "
          f"{freeze['plan']}).", ""]
  rp = os.path.join(ROOT, "demo_out", f"{n.lower()}_report.json")
  if os.path.exists(rp):
    T = json.load(open(rp))
    ag = [T[k]["agreement_on_parsed"] for k in sorted(T) if k.startswith("freegen_adapter/")]
    out += [f"Readout (from tune probe prompts, not test): forced-choice letter agrees with the free answer on {T['freegen']['agreement_on_parsed']:.2f} "
            f"of prompts for plain {n} and on " + ", ".join(f"{v:.2f}" for v in ag) + " for the examples-100 adapters.", ""]
  if not own:
    out += ["**No look yet.** No test2 record exists for this model.", ""]
    J["status"] = "no look"
    return "\n".join(out) + "\n", J
  check(own, freeze)
  verdict = {}
  order = ["oracle", "uniform", "always-cheapest", "stated-cost rule", "plain", "examples-100", "scrambled N=100", "cheapest-label N=100"]
  for split in ("test2_same", "test2_newkey"):
    A = arms_for(split, own, ref, freeze)
    J[split] = {}
    out += [f"## {split}", ""]
    if split == "test2_same":
      e = A.get("examples-100")
      out += ["| arm | n cases | soft regret [95%] | below | at or above | no cost | hard regret | per seed | planted |", "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
      for label in order:
        a = A.get(label)
        if a is None:
          out.append(f"| {label} | not run | | | | | | | |"); continue
        ps = ", ".join(f"{v:.3f}" for v in a.seed_soft) if len(a.recs) > 1 else "-"
        out.append(f"| {label} | {len(a.cids)} | {fci(LR.ci_mean(a.soft, a.case))} | " + " | ".join(f3(a.mean(t)) for t in TYPES) +
                   f" | {f3(a.mean(metric='hard'))} | {ps} | {LR.planted(a.recs)} |")
        J[split][label] = {"soft": a.mean(), "ci": LR.ci_mean(a.soft, a.case), "by_type": {t: a.mean(t) for t in TYPES},
                           "hard": a.mean(metric="hard"), "per_seed": a.seed_soft, "records": [r["_path"] for r in a.recs]}
      out += ["", f"{n_groups(e) if e else '-'} (V, grid) groups.", ""]
      if e and A.get("plain") and A.get("scrambled N=100"):
        dp, ds = paired(e, A["plain"]), paired(e, A["scrambled N=100"])
        dr = paired(e, A["stated-cost rule"]) if A.get("stated-cost rule") else None
        J[split]["paired"] = {"ex100_minus_plain": dp, "ex100_minus_scrambled": ds, "ex100_minus_rule": dr}
        out += ["| examples-100 minus | difference [95%] |", "| --- | --- |", f"| plain | {fci(dp)} |", f"| scrambled N=100 | {fci(ds)} |",
                f"| stated-cost rule (reported, not part of T1) | {fci(dr)} |", ""]
        seen = lambda c: flag[e.case[c]["inputs"]["cell"]]["key_in_lora100"]
        rows_ = []
        for nm, keep in (("label key seen in the 100 LoRA cells", seen), ("label key not seen", lambda c: not seen(c))):
          k = [c for c in e.cids if keep(c)]
          rows_.append(f"| {nm} | {len(k)} | {f3(np.mean([e.soft[c] for c in k]) if k else None)} | "
                       f"{f3(np.mean([A['plain'].soft[c] for c in k]) if k else None)} |")
        out += ["| stratum | n cases | examples-100 | plain |", "| --- | --- | --- | --- |", *rows_, ""]
        t1 = {"mean <= 0.15": e.mean() <= T1_MAX, "every seed below plain": all(v < A["plain"].mean() for v in e.seed_soft),
              "examples-100 minus plain interval below 0": dp[2] < 0, "examples-100 minus scrambled interval below 0": ds[2] < 0}
        verdict["T1"] = all(t1.values())
        J["T1"] = {"conditions": t1, "holds": verdict["T1"]}
        out += ["**T1:** " + "; ".join(f"{k}: {'yes' if v else 'no'}" for k, v in t1.items()) + f" -> **T1 {'holds' if verdict['T1'] else 'fails'}**.", ""]
    else:
      e, p, rule = A.get("examples-100"), A.get("plain"), A.get("stated-cost rule")
      out += ["Never one pooled number: each pre-declared slice separately. Slices overlap (a cell can carry several novelties).", "",
              "| slice | n cases | groups | examples-100 (per seed) | plain | stated-cost rule | scrambled N=100 | ex100 minus plain [95%] | ex100 minus rule [95%] |",
              "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
      for nm, fn in SLICES:
        if not (e and p and rule):
          out.append(f"| {nm} | not run | | | | | | | |"); continue
        keep = lambda c, fn=fn: fn(flag[e.case[c]["inputs"]["cell"]])
        k = [c for c in e.cids if keep(c)]
        if not k:
          out.append(f"| {nm} | 0 | | | | | | | |"); continue
        m = lambda a: float(np.mean([a.soft[c] for c in k]))
        per = ", ".join(f"{np.mean([LR.soft(x) for x in LR.rows(r) if keep(x['cid'])]):.3f}" for r in e.recs)
        sc = A.get("scrambled N=100")
        dp, dr = paired(e, p, keep), paired(e, rule, keep)
        out.append(f"| {nm} | {len(k)} | {n_groups(e, keep)} | {m(e):.3f} ({per}) | {m(p):.3f} | {m(rule):.3f} | {f3(m(sc) if sc else None)} | {fci(dp)} | {fci(dr)} |")
        J[split][nm] = {"n": len(k), "groups": n_groups(e, keep), "ex100": m(e), "plain": m(p), "rule": m(rule), "scrambled": m(sc) if sc else None,
                        "ex100_minus_plain": dp, "ex100_minus_rule": dr}
        if nm.startswith("V 13-15"):
          t2 = {"examples-100 below plain": m(e) < m(p), "examples-100 below the stated-cost rule": m(e) < m(rule),
                "minus plain interval below 0": dp[2] < 0, "minus rule interval below 0": dr[2] < 0}
          verdict["T2"] = all(t2.values())
          J["T2"] = {"conditions": t2, "holds": verdict["T2"]}
      out.append("")
      if "T2" in J:
        out += ["**T2 (V 13-15):** " + "; ".join(f"{k}: {'yes' if v else 'no'}" for k, v in J["T2"]["conditions"].items()) +
                f" -> **T2 {'holds' if verdict['T2'] else 'fails'}**.", ""]
    out += [f"Planted cases on {split} (not part of T1 or T2):", "", "| arm | seed | case | top pick | mass on expected | passes (mass >= 0.9) |", "| --- | --- | --- | --- | --- | --- |"]
    for label in ("plain", "examples-100", "scrambled N=100", "cheapest-label N=100"):
      if A.get(label):
        for seed, cid, top, mass, ok in planted_rows(A[label]):
          out.append(f"| {label} | {seed} | {cid} | {top} | {mass:.2f} | {'yes' if ok else 'no'} |")
    out.append("")
  if "T1" in verdict:
    key = "T1 fails" if not verdict["T1"] else ("both hold" if verdict.get("T2") else ("T1 holds, T2 fails" if "T2" in verdict else "T1 holds, T2 untestable"))
    J["conclusion"] = {"case": key, "wording": WORDING[key]}
    out += ["## Conclusion (wording fixed before the look)", "", f"**{WORDING[key]}.**", "",
            "Gemma numbers on test2, if any, come from a different scoring script and are description only.", ""]
  return "\n".join(out) + "\n", J


def main(argv=None):
  argv = sys.argv[1:] if argv is None else argv
  model = argv[argv.index("--model") + 1]
  freeze = json.load(open(os.path.join(ROOT, "demo", "gen", f"test2_freeze_{model}.json")))
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
