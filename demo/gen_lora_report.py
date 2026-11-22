"""Report for the generated-dataset LoRA arms on the 42 TUNE cells (CPU). Applies the frozen pass rule of GEN_PLAN.md to teacher-distil.
Unit = cell (mean of two name variants, then mean over an arm's seeds); paired cell bootstrap, 10,000 resamples, seed 0.
Writes demo_out/gen_lora_report.md and demo/gen/gen_lora_summary.json."""
import collections, glob, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import common
import gen_cases as g

ROOT = common.ROOT
cells = {c["cell"]: c for c in json.load(open(os.path.join(g.OUT, "cells.json")))["cells"]}
cases = {c["cid"]: c for c in map(json.loads, open(os.path.join(g.OUT, "cases.jsonl")))}
TUNE = sorted(k for k, c in cells.items() if c["split"] == "tune")
train_spec = json.load(open(os.path.join(g.OUT, "lora_train_cells.json")))
train_keys = {(cells[k]["V"], cells[k]["grid_name"], cells[k]["C"], None if cells[k]["C"] is not None else tuple(cells[k]["prior"])) for k in train_spec}
LR_GRID = (1e-4, 3e-4, 1e-3)
runs = {}
for f in glob.glob(os.path.join(ROOT, "demo_out", "gen_lora", "*_s?.json")):
  r = json.load(open(f)); runs[r["run_id"]] = r


def rid(arm, lr, s):
  return f"gen_{arm}_lr{lr:.0e}_s{s}"


def sel(arm, lr, s=0):
  r = runs.get(rid(arm, lr, s))
  return r["select_best"]["soft_regret"] if r else None


def chosen(arm, default):
  vals = {lr: sel(arm, lr) for lr in LR_GRID}
  if all(v is not None for v in vals.values()):
    return min(vals, key=lambda k: (vals[k], k))
  return default


def case_soft(probs):
  return {cid: cells[cases[cid]["cell"]]["best_payoff"] - float(np.dot(p, cells[cases[cid]["cell"]]["payoffs"])) for cid, p in probs.items()}


def to_cells(per_case):
  by = collections.defaultdict(list)
  for cid, v in per_case.items():
    by[cases[cid]["cell"]].append(v)
  return {k: float(np.mean(v)) for k, v in by.items()}


def arm_cells(run_list):
  vals = [to_cells(case_soft(r["tune_probs_best"])) for r in run_list]
  return {k: float(np.mean([v[k] for v in vals])) for k in TUNE}


def arm_mass(run_list):
  return float(np.mean([np.mean(list(r["tune_mass_best"].values())) for r in run_list]))


def boot(d, n=10000):
  v = np.asarray(d, float)
  b = np.random.default_rng(0).choice(v, size=(n, len(v)), replace=True).mean(1)
  return float(v.mean()), float(np.quantile(b, .025)), float(np.quantile(b, .975)), int((v > 0).sum())


plain_rows = {r["cid"]: r for r in map(json.loads, open(os.path.join(ROOT, "demo_out", "gen_plain_scores.jsonl")))}
plain = to_cells({cid: r["soft_regret"] for cid, r in plain_rows.items() if cases[cid]["split"] == "tune"})
plain_mass = float(np.mean([r["mass"] for cid, r in plain_rows.items() if cases[cid]["split"] == "tune"]))
base = {"plain": plain}
for name, kind in (("always-cheapest", "cheapest"), ("stated-cost rule", "rule")):
  base[name] = {k: cells[k]["best_payoff"] - cells[k]["payoffs"][0 if kind == "cheapest" else (next((i for i, x in enumerate(cells[k]["grid"]) if x >= cells[k]["C"]), 4) if cells[k]["C"] is not None and cells[k]["C"] < cells[k]["V"] else 0)] for k in TUNE}
trow = collections.defaultdict(dict)
for r in map(json.loads, open(os.path.join(ROOT, "demo_out", "gen_text_rows.jsonl"))):
  if cases[r["cid"]]["split"] == "tune":
    trow[r["row"]][r["cid"]] = r["soft_regret"]
for name in ("teacher", "method_original"):
  base[f"{name} text in prompt"] = to_cells(trow[name])

lr_t = chosen("teacher", 3e-4)
arm_lr = {"teacher": lr_t, "method_original": chosen("method_original", lr_t), "neutral": chosen("neutral", lr_t), "wrong_rule": chosen("wrong_rule", lr_t), "answer_only": chosen("answer_only", 3e-4)}
arms, notes = {}, []
for a, lr in arm_lr.items():
  rl = [r for s in (0, 1, 2) if (r := runs.get(rid(a, lr, s)))]
  good = [r for r in rl if not r["best_epoch_is_zero"]]
  if len(good) < len(rl):
    notes.append(f"{a}: {len(rl) - len(good)} run(s) kept epoch 0 (no improvement; flagged and not counted as arms)")
  if good:
    arms[a] = {"lr": lr, "runs": good, "seeds": [r["seed"] for r in good], "cells": arm_cells(good), "mass": arm_mass(good)}
L = ["# Generated-dataset LoRA arms on the 42 TUNE cells (selection on 42 separate train cells; tune scored once per run)", "",
     f"Chosen lr: teacher {lr_t:.0e} (lowest selection-set soft regret at seed 0); other arms at their own grid if complete, else the teacher's lr (answer-trained ceiling 3e-4). " + " ".join(notes), "",
     "## Arms: soft regret on tune cells (mean over cells, seeds averaged), by type", "",
     "| Arm | lr | seeds | all [95%] | below | at_or_above | no_cost | letter mass | slope on stated cost (below) | best epochs | s/epoch |", "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
bytype = lambda cv, t: float(np.mean([v for k, v in cv.items() if t is None or cells[k]["type"] == t]))
def row(name, cv, lr="", seeds="", mass="", slope="", ep="", sec=""):
  b = boot(list(cv.values()))
  return f"| {name} | {lr} | {seeds} | {b[0]:.3f} [{b[1]:.3f}, {b[2]:.3f}] | " + " | ".join(f"{bytype(cv, t):.3f}" for t in g.TYPES) + f" | {mass} | {slope} | {ep} | {sec} |"
L.append(row("plain", plain, mass=f"{plain_mass:.2f}"))
for name in ("always-cheapest", "stated-cost rule", "teacher text in prompt", "method_original text in prompt"):
  L.append(row(name, base[name]))
for a, d in arms.items():
  sl = [r["tune_full_best"]["slope_stated_cost_below"] for r in d["runs"] if r["tune_full_best"]["slope_stated_cost_below"] is not None]
  L.append(row(f"{a}-distil" if a != "answer_only" else "answer-trained ceiling", d["cells"], f"{d['lr']:.0e}", ",".join(map(str, d["seeds"])), f"{d['mass']:.2f}",
               f"{np.mean(sl):.2f}" if sl else "", ",".join(str(r["best_epoch"]) for r in d["runs"]), f"{np.mean([r['sec_per_epoch'] for r in d['runs'] if r['sec_per_epoch']]):.0f}"))
L.append("")
summary = {"teacher_lr": lr_t, "arm_lr": arm_lr, "pass": None}
if "teacher" in arms:
  T = arms["teacher"]
  L += ["## Pass rule (GEN_PLAN.md, frozen): control minus teacher, paired cell bootstrap", "", "| Comparison | mean diff [95%] | cells where teacher better | lower bound > 0 |", "| --- | --- | --- | --- |"]
  checks = {}
  for name, cv, key in (("plain", plain, "plain"), ("neutral-distil", arms.get("neutral", {}).get("cells"), "neutral"), ("wrong-rule-distil", arms.get("wrong_rule", {}).get("cells"), "wrong_rule"),
                        ("our-method-distil (not in rule)", arms.get("method_original", {}).get("cells"), "method_original"), ("always-cheapest (not in rule)", base["always-cheapest"], "cheap"),
                        ("stated-cost rule (not in rule)", base["stated-cost rule"], "rule")):
    if cv is None:
      L.append(f"| {name} | not run | | |"); continue
    b = boot([cv[k] - T["cells"][k] for k in TUNE])
    checks[key] = b
    L.append(f"| {name} | {b[0]:+.3f} [{b[1]:+.3f}, {b[2]:+.3f}] | {b[3]} of {len(TUNE)} | {'yes' if b[1] > 0 else 'no'} |")
  below = [k for k in TUNE if cells[k]["type"] == "below"]
  bb = boot([plain[k] - T["cells"][k] for k in below])
  other = {t: bytype(T["cells"], t) - bytype(plain, t) for t in ("at_or_above", "no_cost")}
  c1 = all(k in checks and checks[k][1] > 0 for k in ("plain", "neutral", "wrong_rule"))
  c2 = checks["plain"][0] >= 0.15
  c3 = bb[1] > 0 and bb[3] / len(below) >= 0.6
  c4 = all(v <= 0.05 for v in other.values())
  c5 = T["mass"] >= 0.9 * plain_mass
  L += ["", f"1. beats plain, neutral-distil and wrong-rule-distil with lower bound > 0: **{'yes' if c1 else 'no'}**",
        f"2. effect floor, improvement over plain >= 0.15: {checks['plain'][0]:+.3f} -> **{'yes' if c2 else 'no'}**",
        f"3. below cells: improvement over plain {bb[0]:+.3f} [{bb[1]:+.3f}, {bb[2]:+.3f}], better in {bb[3]} of {len(below)} cells (need lower bound > 0 and >= 60%) -> **{'yes' if c3 else 'no'}**",
        f"4. no harm (teacher minus plain <= +0.05): at_or_above {other['at_or_above']:+.3f}, no_cost {other['no_cost']:+.3f} -> **{'yes' if c4 else 'no'}**",
        f"5. letter mass {T['mass']:.2f} vs 0.9 x plain {0.9 * plain_mass:.2f} -> **{'yes' if c5 else 'no'}**", ""]
  ok = c1 and c2 and c3 and c4 and c5
  L.append(f"**Pass rule (all seeds): {'PASSED' if ok else 'NOT PASSED'}** (seeds {T['seeds']}; replication on seeds 1-2 only below)")
  rep = [r for r in T["runs"] if r["seed"] in (1, 2)]
  if rep:
    tc = arm_cells(rep)
    L += ["", "Replication, teacher seeds 1-2 only vs all available control seeds:", ""]
    for name, key in (("plain", None), ("neutral-distil", "neutral"), ("wrong-rule-distil", "wrong_rule")):
      cv = plain if key is None else arms.get(key, {}).get("cells")
      if cv is None:
        continue
      b = boot([cv[k] - tc[k] for k in TUNE])
      L.append(f"- vs {name}: {b[0]:+.3f} [{b[1]:+.3f}, {b[2]:+.3f}], teacher better in {b[3]} of {len(TUNE)} cells")
  summary["pass"] = bool(ok)
  # label-key overlap
  ov = [k for k in TUNE if (cells[k]["V"], cells[k]["grid_name"], cells[k]["C"], None if cells[k]["C"] is not None else tuple(cells[k]["prior"])) in train_keys]
  nov = [k for k in TUNE if k not in ov]
  L += ["", f"## By overlap of the cell's label key (V, grid, C or prior) with the 100 training cells: {len(ov)} overlapping, {len(nov)} not", "",
        "| Arm | overlapping cells | non-overlapping cells |", "| --- | --- | --- |", f"| plain | {np.mean([plain[k] for k in ov]):.3f} | {np.mean([plain[k] for k in nov]):.3f} |"]
  for a, d in arms.items():
    L.append(f"| {a} | {np.mean([d['cells'][k] for k in ov]):.3f} | {np.mean([d['cells'][k] for k in nov]):.3f} |")
  L += ["", "## Per-seed tune soft regret (cell means)", ""] + [f"- {r['run_id']}: {np.mean(list(to_cells(case_soft(r['tune_probs_best'])).values())):.3f} (best epoch {r['best_epoch']}, selection set {r['select_best']['soft_regret']:.3f})" for r in sorted(runs.values(), key=lambda r: r['run_id'])]
open(os.path.join(ROOT, "demo_out", "gen_lora_report.md"), "w").write("\n".join(L) + "\n")
json.dump(summary, open(os.path.join(g.OUT, "gen_lora_summary.json"), "w"), indent=1, default=float)
print("\n".join(L))
