"""LoRA results and the pass rule (CPU; reads demo_out/lora/*.json). Written and
committed before any training result exists.

  python demo/lora_report.py     -> demo_out/lora_report.md, demo/lora_summary.json

OWNER'S RULE (frozen 2026-11-22, DEMO_STATUS.md section 4): the method arm passes if
its held-out tune-cell soft regret beats plain and both distillation controls
(neutral, wrong_rule), with the lower 95% cell-bootstrap bound of each difference
above 0. Unit: the 6 held-out tune cells; 10,000 resamples of cells, seed 0; the
comparison uses seed 0 of every arm, each at its chosen learning rate (equal
footing); other seeds are reported separately.

STRICT PASS (added after the G1 reviews, each criterion reported separately): the
owner's rule AND
  S1 method also beats always-2 and the best shuffled arm (lower bound above 0);
  S2 effect floor: method recovers at least 50% of the gap between plain and the
     in-prompt method text on the held-out cells;
  S3 coherence: held-out letter mass at least 0.9 x plain's;
  S4 free text: the held-out free-text hard regret (scoring.say) is below plain's;
  S5 content: the slope of the expected offer on the stated cost over the held-out
     cost-below-resale cases is at least 0.25 (plain 0.05, method text 0.53).
All numbers on the held-out tune cells are selected-on (learning rate and epoch
were chosen on them): a pass licenses spending the one test look (gate G3 and the
owner's go), it is not independent evidence.

OUTCOME TABLE (method arm, seed 0): teacher matched on the train cells = best-epoch
train soft regret within 0.05 of the method text's train-cell regret (0.428).
  matched + owner pass      "the method's effect transfers to held-out cells"
  matched + owner fail, beats plain and neutral  "improves held-out cells over plain and neutral-distil; not separated from wrong-rule-distil"
  matched + owner fail otherwise  "learned the train cells, did not transfer"
  not matched               "undertrained or not learnable at this rank/rate"
  trainability check failed "UNDERTRAINED: no arm result is informative"
A null with 6 held-out cells is uninformative about the idea; it is read only as
"not shown here"."""
import glob, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import common
from refimpl import core

OUT = os.environ.get("LORA_OUT", os.path.join(common.ROOT, "demo_out"))
SUMMARY = os.environ.get("LORA_SUMMARY", os.path.join(common.DEMO_DIR, "lora_summary.json"))
STATUS = os.environ.get("LORA_STATUS", os.path.join(common.DEMO_DIR, "lora_status.json"))
P = common.prompts_by_id()
SPLIT = json.load(open(os.path.join(common.DEMO_DIR, "splits_lora.json")))["case_split"]
TUNE = [pid for pid, s in SPLIT.items() if s == "lora_tune"]
TRAIN = [pid for pid, s in SPLIT.items() if s == "lora_train"]
TUNE_CELLS = sorted({P[i].cell for i in TUNE}, key=str)
METHOD_TEXT_TRAIN = 0.428
MASS_FLOOR, SLOPE_MIN, EFFECT_FLOOR = 0.9, 0.25, 0.5


def probs_of(d):
  return {int(k): v for k, v in d.items()}


def cell_soft(probs_by_pid, pids=TUNE):
  by = {}
  for i in pids:
    by.setdefault(P[i].cell, []).append(core.soft_regret(P[i], probs_of(probs_by_pid[i])))
  return {c: float(np.mean(v)) for c, v in by.items()}


def lower_bound(diffs, n=10000, seed=0):
  x = np.array(diffs, float)
  rng = np.random.default_rng(seed)
  b = rng.choice(x, size=(n, len(x)), replace=True).mean(1)
  return float(np.quantile(b, 0.025)), float(np.quantile(b, 0.975))


def compare(a, b):
  """per-cell soft regret dicts; difference (a - b), positive = b better. Returns stats."""
  d = [a[c] - b[c] for c in TUNE_CELLS]
  lo, hi = lower_bound(d)
  return {"mean": float(np.mean(d)), "ci": [lo, hi], "per_cell": [float(x) for x in d],
          "cells_b_better": int(sum(x > 0 for x in d)), "lower_above_0": lo > 0}


def load_runs():
  runs = {}
  for f in glob.glob(os.path.join(OUT, "lora", "*.json")):
    if f.endswith("_smoke.json") or os.path.basename(f).startswith("teacher_"):
      continue
    r = json.load(open(f))
    runs[r["run_id"]] = r
  return runs


def chosen(runs, arm, perm=0):
  cands = [r for r in runs.values() if r["arm"] == arm and r["perm"] == perm and r["seed"] == 0 and r["rank"] == 4]
  return min(cands, key=lambda r: (r["tune_best"]["soft_regret"], r["lr"])) if cands else None


def main():
  runs = load_runs()
  plain = {c["pid"]: c["probs"] for c in common.load_cases()}
  mrows = {}
  for f in ("text_rows_tuning.jsonl", "text_rows_build.jsonl"):
    for l in open(os.path.join(common.ROOT, "demo_out", f)):
      r = json.loads(l)
      if r["row"] == "method":
        mrows[r["pid"]] = r["probs"]
  const2 = {i: {k: float(k == 2) for k in core.PRICES} for i in plain}
  base = {"plain": cell_soft(plain), "method text (prompt)": cell_soft(mrows), "always-2": cell_soft(const2)}
  L = ["# LoRA results (held-out tune cells: selected-on, not independent evidence)", ""]
  arms = {}
  for arm in ("method", "neutral", "wrong_rule", "answer_only", "const2", "template"):
    r = chosen(runs, arm)
    if r:
      arms[arm] = r
  shuf = [r for r in (chosen(runs, "shuffled", k) for k in (0, 1, 2)) if r]
  best_shuf = min(shuf, key=lambda r: r["tune_best"]["soft_regret"]) if shuf else None
  cells = {a: cell_soft(r["tune_probs_best"]) for a, r in arms.items()}
  if best_shuf:
    cells["shuffled (best of %d)" % len(shuf)] = cell_soft(best_shuf["tune_probs_best"])
  L += ["## Arms (seed 0, chosen learning rate)", "",
        "| Arm | lr | Best epoch (of run) | Held-out soft regret | Train soft regret (best / min) | Held-out mass | Fidelity KL (train / held-out) | Say agreement (plain → arm) | Say hard regret (plain → arm) | Slope on stated cost | s/epoch |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
  for name, r in list(arms.items()) + ([("shuffled (best of %d)" % len(shuf), best_shuf)] if best_shuf else []):
    tb, trb = r["tune_best"], r["train_best"]
    p0 = r["history"][0]["tune"]
    sp, sb = r["say_plain"], r["say_best"]
    kl = lambda h: "—" if h.get("kl_teacher_student") is None else f"{h['kl_teacher_student']:.3f}"
    L.append(f"| {name} | {r['lr']:.0e} | {r['best_epoch']} ({r['epochs_run']}) | {tb['soft_regret']:.3f} | "
             f"{trb['soft_regret']:.3f} / {r['train_min_soft_regret']:.3f} | {tb['mass']:.2f} (plain {p0['mass']:.2f}) | "
             f"{kl(trb)} / {kl(tb)} | {sp['agreement']:.2f} → {sb['agreement']:.2f} | "
             f"{sp['say_hard_regret']:.2f} → {sb['say_hard_regret']:.2f} | "
             f"{'—' if tb.get('slope_stated_cost') is None else format(tb['slope_stated_cost'], '.2f')} | {r['sec_per_epoch']:.0f} |")
  L += ["", "Reference on the same cells: " + "; ".join(f"{k} {np.mean(list(v.values())):.3f}" for k, v in base.items()) + ".", ""]
  summary = {"arms": {a: r["run_id"] for a, r in arms.items()}, "best_run": None}
  if "method" in arms:
    m = cells["method"]
    L += ["## Pass rule (owner's rule, frozen)", "",
          "| Comparison (control − method, per held-out cell) | Mean | 95% interval | Cells where method is better | Lower bound > 0 |",
          "| --- | --- | --- | --- | --- |"]
    owner = {}
    for name, ctrl in (("plain", base["plain"]), ("neutral-distil", cells.get("neutral")), ("wrong-rule-distil", cells.get("wrong_rule"))):
      if ctrl is None:
        owner[name] = None
        L.append(f"| {name} | — | — | — | not run |")
        continue
      c = compare(ctrl, m); owner[name] = c
      L.append(f"| {name} | {c['mean']:+.3f} | [{c['ci'][0]:+.3f}, {c['ci'][1]:+.3f}] | {c['cells_b_better']} of 6 | {'yes' if c['lower_above_0'] else 'no'} |")
    owner_pass = all(v is not None and v["lower_above_0"] for v in owner.values())
    L += ["", f"**Owner's rule: {'PASS' if owner_pass else 'NOT PASSED'}**" + ("" if all(v is not None for v in owner.values()) else " (a control has not been run)"), ""]
    # strict criteria
    tb = arms["method"]["tune_best"]; h0 = arms["method"]["history"][0]["tune"]
    S = {}
    extra = {"always-2": base["always-2"]}
    if best_shuf:
      extra["best shuffled"] = cells["shuffled (best of %d)" % len(shuf)]
    for k, ctrl in extra.items():
      S[f"S1 vs {k}"] = compare(ctrl, m)["lower_above_0"]
    gap_text = np.mean(list(base["plain"].values())) - np.mean(list(base["method text (prompt)"].values()))
    gap_student = np.mean(list(base["plain"].values())) - np.mean(list(m.values()))
    S["S2 effect floor (>= 50% of the plain-to-method-text gap)"] = bool(gap_student >= EFFECT_FLOOR * gap_text)
    S["S3 mass >= 0.9 x plain"] = bool(tb["mass"] >= MASS_FLOOR * h0["mass"])
    sb, sp = arms["method"]["say_best"], arms["method"]["say_plain"]
    S["S4 free-text hard regret below plain"] = bool(sb["say_hard_regret"] is not None and sp["say_hard_regret"] is not None
                                                      and sb["say_hard_regret"] < sp["say_hard_regret"])
    S["S5 slope on stated cost >= 0.25"] = bool(tb.get("slope_stated_cost") is not None and tb["slope_stated_cost"] >= SLOPE_MIN)
    L += ["## Strict criteria (reported separately)", "", "| Criterion | Met |", "| --- | --- |"]
    L += [f"| {k} | {'yes' if v else 'no'} |" for k, v in S.items()]
    strict = owner_pass and all(S.values())
    L += ["", f"**Strict pass: {'YES' if strict else 'NO'}.**", ""]
    # seeds
    seeds = sorted((r for r in runs.values() if r["arm"] == "method" and r["rank"] == 4 and r["lr"] == arms["method"]["lr"]),
                   key=lambda r: r["seed"])
    if len(seeds) > 1:
      L += ["## Method seeds (same learning rate)", "", "| Seed | Held-out soft regret | Best epoch | vs plain: lower bound > 0 |", "| --- | --- | --- | --- |"]
      for r in seeds:
        c = compare(base["plain"], cell_soft(r["tune_probs_best"]))
        L.append(f"| {r['seed']} | {r['tune_best']['soft_regret']:.3f} | {r['best_epoch']} | {'yes' if c['lower_above_0'] else 'no'} |")
      L.append("")
    # outcome table
    trs = arms["method"]["train_best"]["soft_regret"]
    matched = trs <= METHOD_TEXT_TRAIN + 0.05   # one-sided: reaching or beating the teacher counts as matched
    beats_plain_neutral = all(v is not None and v['lower_above_0'] for k, v in owner.items() if k != 'wrong-rule-distil')
    status_f = STATUS
    trainable = json.load(open(status_f)).get("trainability", {}).get("pass", True) if os.path.exists(status_f) else True
    outcome = ("UNDERTRAINED: the trainability check failed" if not trainable else
               "the method's effect transfers to held-out cells" if matched and owner_pass else
               "improves held-out cells over plain and neutral-distil; not separated from wrong-rule-distil" if matched and beats_plain_neutral else
               "learned the train cells, did not transfer" if matched else
               "undertrained or not learnable at this rank and rate")
    L += ["## Outcome (method arm, seed 0)", "",
          f"- Train-cell soft regret at the best epoch {trs:.3f}; method text on the train cells {METHOD_TEXT_TRAIN:.3f}; teacher matched: {'yes' if matched else 'no'}.",
          f"- Outcome: **{outcome}**.",
          "- All held-out numbers are selected-on; with 6 cells a null is read only as \"not shown here\".", ""]
    summary.update({"owner_pass": owner_pass, "strict_pass": strict, "strict": S, "outcome": outcome,
                    "best_run": arms["method"]["run_id"]})
  if "best_run" in summary and summary["best_run"] is None and arms:
    summary["best_run"] = min(arms.values(), key=lambda r: r["tune_best"]["soft_regret"])["run_id"]
  open(os.path.join(OUT, "lora_report.md"), "w").write("\n".join(L) + "\n")
  json.dump(summary, open(SUMMARY, "w"), indent=1, default=float)
  print("\n".join(L))


if __name__ == "__main__":
  main()
