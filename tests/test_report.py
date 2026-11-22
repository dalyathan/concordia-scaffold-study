"""Synthetic end-to-end run of the registered analysis (refimpl/report.py).

Fake Phase 2 and Phase 3 records for all 420 prompts and 28 conditions, with an
effect planted for the first entry only, go through exclusions, tables, the
confirmatory family with its labels, the secondary family, the sensitivity
analyses and the mixed-model export. No model is involved."""
import csv
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from refimpl import analysis, conditions, core, report  # noqa: E402

TAGS = {a: a.rsplit(".", 1)[-1] for a in conditions.AGENTS}
GOOD = conditions.ENTRIES[0]                          # taehun: planted effect


def _probs_towards(p, strength, rng):
  best = core.oracle_bids(p)[0]
  w = {k: (strength if k == best else (1 - strength) / 4) + rng.uniform(0, 0.02) for k in core.PRICES}
  z = sum(w.values())
  return {k: v / z for k, v in w.items()}


def _records(prompts, rng):
  conds = ["N0", "N1", "N1s", "N10"]
  for a in conditions.AGENTS:
    t = TAGS[a]
    conds += [f"N5:{t}", f"N6:{t}", f"N9:{t}"]
    if a in conditions.ENTRY_CODE:
      c = conditions.ENTRY_CODE[a]
      conds += [c, c + "r", f"N7:{t}", f"N8:{t}"]
  strength = {c: 0.3 for c in conds}
  for c in (conditions.ENTRY_CODE[GOOD], conditions.ENTRY_CODE[GOOD] + "r", f"N8:{TAGS[GOOD]}"):
    strength[c] = 0.9
  recs = []
  for p in prompts:
    for c in conds:
      for o in range(5):
        pr = _probs_towards(p, strength[c], rng)
        recs.append({"pid": p.pid, "cond": c, "order": o, "probs": {str(k): v for k, v in pr.items()},
                     "probs_full": {str(k): v for k, v in pr.items()},
                     "hard": max(pr, key=pr.get), "letter_mass": 0.6})
  return recs


def test_full_analysis_on_synthetic_records(tmp_path):
  rng = np.random.default_rng(5)
  prompts = core.prompt_set()
  p2 = []
  for a in conditions.AGENTS:
    for p in prompts:
      k = core.oracle_bids(p)[0] if a == GOOD else int(rng.integers(1, 6))
      p2.append({"agent": a, "pid": p.pid, "attempt": 0, "k": k, "hard_regret": core.hard_regret(p, k)})
  # A failed first attempt followed by a successful retry: not excluded.
  for r in p2:
    if r["agent"] == conditions.ENTRIES[1] and r["pid"] == "v01-V2-neutral":
      r["attempt"] = 1
  p2.append({"agent": conditions.ENTRIES[1], "pid": "v01-V2-neutral", "attempt": 0, "error": "x"})
  ex = report.exclusions(p2)
  assert ex["dropped_pids"] == [] and ex["over_10pct"] == []        # retry succeeded
  regret = {}
  for r in p2:
    if "error" not in r:
      regret.setdefault(r["agent"], {})[r["pid"]] = r["hard_regret"]
  tables = report.phase3_tables(_records(prompts, rng), prompts)
  assert len(tables["soft"]) == 420 * 28
  conf = report.confirmatory(prompts, tables, regret, None, extension=False,
                             labels_in={"leakage": {TAGS[GOOD]: {"flag": False}}})
  assert conf["family"] == ["A1", "A2", "A3", "B1", "B2", "B3", "R1", "R2", "R3"]
  v = conf["verdicts"]
  assert v["A1"] == v["B1"] == v["R1"] == "supported"
  assert v["B2"] != "supported" and v["B3"] != "supported"
  # The leakage flag stops a passing R from being "supported".
  conf2 = report.confirmatory(prompts, tables, regret, None, extension=False,
                              labels_in={"leakage": {TAGS[GOOD]: {"flag": True}}})
  assert conf2["verdicts"]["R1"] == "inconclusive"
  assert "possibly carried by implied advice" in conf2["labels"]["R1"]
  test = [p for p in prompts if core.steering_cell_split(p.cell) == "test"]
  sec = report.secondary(prompts, test, tables, phase2_regret=regret)
  for k in ("E2:taehun_cgcal", "E4:N0", "E5:length:taehun_cgcal", "E7:B:taehun_cgcal", "E8"):
    assert k in sec["p"], k
  assert sec["effects"]["E8"]["best"] == TAGS[GOOD]
  assert set(sec["missing"]) == {"E1", "E3", "E6"}
  sens = report.sensitivity(prompts, tables, regret, near_ceiling=[(2, "neutral")])
  assert "subset:C_below_V:p" in sens["B1"] and "hard:p" in sens["B1"]
  assert sens["B1"]["effect"]["mean"] > 0
  path = str(tmp_path / "mm.csv")
  report.mixed_model_table(prompts, tables, regret, path)
  rows = list(csv.DictReader(open(path)))
  assert len(rows) == 3 * (1 + 4 + 2) * 420


def test_exclusion_rule_drops_prompt_for_all_and_labels_agent():
  prompts = core.prompt_set([1])
  recs = []
  for a in conditions.AGENTS:
    for i, p in enumerate(prompts):
      fail = a == conditions.ENTRIES[2] and i < 5                   # 5 of 35 > 10%
      for att in ((0, 1) if fail else (0,)):
        recs.append({"agent": a, "pid": p.pid, "attempt": att, **({"error": "x"} if fail else {})})
  ex = report.exclusions(recs)
  assert len(ex["dropped_pids"]) == 5 and ex["over_10pct"] == [conditions.ENTRIES[2]]
  assert len(report.keep(prompts, ex["dropped_pids"])) == 30
