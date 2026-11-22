"""The registered analysis, from records to verdicts (Protocol sections 1.2-1.6, 9, 10.5, 11).

Everything here reads the records written by refimpl/pipeline.py (or equivalent
in-memory tables) and calls refimpl/analysis.py; nothing here runs a model.

  exclusions               failed prompts (dropped for every agent) and per-agent rates
  tables                   order-averaged soft regret, p(k), hard regret, letter mass
  confirmatory             A1-A3, B1-B3, R1-R3, K1 (and K2 with the extension), verdicts, labels
  secondary                E1-E9 (and K2 without the extension), Benjamini-Hochberg
  sensitivity              Wilcoxon, bootstrap-t, cell-type subsets, near-ceiling subset,
                           whole-answer and Phase 3 hard regret, effect sizes
  mixed_model_table        prompt-level D for the R mixed model (analysis/mixed_model.R)
"""
from __future__ import annotations

import collections
import csv
import json
from typing import Mapping, Sequence

import numpy as np
from scipy import stats

from . import analysis, conditions, core

ENTRY_NUMBER = {a: i + 1 for i, a in enumerate(conditions.ENTRIES)}        # A1 = taehun, ...
TAG = {a: a.rsplit(".", 1)[-1] for a in conditions.AGENTS}
BASE_TAG = TAG[conditions.BASELINE]


# ------------------------------------------------------------- exclusions
def exclusions(phase2_records: Sequence[dict]) -> dict:
  """Protocol 11, Exclusions. A prompt whose decision failed twice for any agent is
  dropped for every agent and condition. An agent with more than 10% of its prompts
  failing has its tests labelled inconclusive."""
  attempts = collections.defaultdict(dict)
  for r in phase2_records:
    attempts[(r["agent"], r["pid"])][r["attempt"]] = "error" not in r
  failed = collections.defaultdict(set)
  for (agent, pid), att in attempts.items():
    if not any(att.values()):
      failed[agent].add(pid)
  n = collections.Counter(a for (a, _) in attempts)
  dropped = set().union(*failed.values()) if failed else set()
  rate = {a: len(failed.get(a, ())) / n[a] for a in n}
  return {"dropped_pids": sorted(dropped), "failure_rate": rate,
          "over_10pct": sorted(a for a, v in rate.items() if v > 0.10)}


def keep(prompts: Sequence[core.Prompt], dropped: Sequence[str]) -> list[core.Prompt]:
  d = set(dropped)
  return [p for p in prompts if p.pid not in d]


# ------------------------------------------------------------------ tables
def phase3_tables(phase3_records: Sequence[dict], prompts: Sequence[core.Prompt]) -> dict:
  """(pid, cond) -> order-averaged quantities from records/phase3.jsonl:
  soft (first-token soft regret, primary), soft_full (whole-answer), hard (mean
  hard regret over orders), probs and probs_full (order-averaged p(k)), mass."""
  P = {p.pid: p for p in prompts}
  by = collections.defaultdict(list)
  for r in phase3_records:
    if r["pid"] in P:
      by[(r["pid"], r["cond"])].append(r)
  t = {k: {} for k in ("soft", "soft_full", "hard", "probs", "probs_full", "mass")}
  for key, rs in by.items():
    p = P[key[0]]
    pr = [{int(k): v for k, v in r["probs"].items()} for r in rs]
    pf = [{int(k): v for k, v in r["probs_full"].items()} for r in rs]
    mp = {k: float(np.mean([d[k] for d in pr])) for k in core.PRICES}
    mf = {k: float(np.mean([d[k] for d in pf])) for k in core.PRICES}
    t["probs"][key], t["probs_full"][key] = mp, mf
    t["soft"][key] = float(np.mean([core.soft_regret(p, d) for d in pr]))
    t["soft_full"][key] = float(np.mean([core.soft_regret(p, d) for d in pf]))
    t["hard"][key] = float(np.mean([core.hard_regret(p, int(r["hard"])) for r in rs]))
    t["mass"][key] = float(np.mean([r["letter_mass"] for r in rs]))
  return t


def two_sided(x: Sequence[float]) -> float:
  return float(min(1.0, 2 * min(analysis.signflip_greater(x), analysis.signflip_less(x))))


# ------------------------------------------------------------ confirmatory
def _rename(abr: Mapping[str, dict]) -> dict:
  out = {}
  for a in conditions.ENTRIES:
    for fam in ("A", "B", "R"):
      out[f"{fam}{ENTRY_NUMBER[a]}"] = abr[f"{fam}:{TAG[a]}"]
  return out


def confirmatory(prompts: Sequence[core.Prompt], tables: Mapping[str, dict],
                 phase2_regret: Mapping[str, Mapping[str, float]], k: Mapping[str, dict] | None,
                 extension: bool, labels_in: Mapping[str, Mapping] = {}) -> dict:
  """The confirmatory family and its verdicts.

  k: output of analysis.k_tests (K1, K2), or None if Phase 3b has not run.
  labels_in: {'leakage': pipeline.leakage_flags(...), 'replay':
  pipeline.native_replay_labels(...), 'exclusion': exclusions(...)}."""
  entries = {a: (c, TAG[a]) for a, c in conditions.ENTRY_CODE.items()}
  tests = _rename(analysis.abr_tests(prompts, tables["soft"], phase2_regret,
                                     conditions.BASELINE, entries))
  if k is not None:
    tests["K1"] = k["K1"]
    if extension:
      tests["K2"] = k["K2"]
  family = [t for t in analysis.confirmatory_family(extension) if t in tests]
  verdicts = analysis.confirmatory_verdicts({t: tests[t] for t in family})
  labels = collections.defaultdict(list)
  # Leakage flag: a passing R cannot be "supported" (Protocol 9.2).
  for a in conditions.ENTRIES:
    t = f"R{ENTRY_NUMBER[a]}"
    if labels_in.get("leakage", {}).get(TAG[a], {}).get("flag"):
      labels[t].append("possibly carried by implied advice")
      if verdicts.get(t) == "supported":
        verdicts[t] = "inconclusive"
    if labels_in.get("replay", {}).get(a, {}).get("transplant_sensitive"):
      for fam in ("B", "R"):
        labels[f"{fam}{ENTRY_NUMBER[a]}"].append("transplant-sensitive")
    if a in labels_in.get("exclusion", {}).get("over_10pct", []):
      for fam in ("A", "B", "R"):
        t = f"{fam}{ENTRY_NUMBER[a]}"
        verdicts[t] = "inconclusive"
        labels[t].append("more than 10% of prompts excluded")
  # Disagreement rule (Protocol 1.2): whole-answer effect of the opposite sign.
  whole = _rename(analysis.abr_tests(prompts, tables["soft_full"], phase2_regret,
                                     conditions.BASELINE, entries))
  for t in ("B1", "B2", "B3", "R1", "R2", "R3"):
    if verdicts.get(t) == "supported" and np.mean(whole[t]["effect_cells"]) < 0:
      verdicts[t] = "supported (scoring-sensitive)"
  # Letter-mass rule (Protocol 1.2): any cell whose two conditions differ by > 0.10.
  for a in conditions.ENTRIES:
    code, tag, n = conditions.ENTRY_CODE[a], TAG[a], ENTRY_NUMBER[a]
    for t, pairs in ((f"B{n}", [("N0", code), ("N1", code), (f"N6:{tag}", code), (f"N7:{tag}", code)]),
                     (f"R{n}", [("N0", f"N8:{tag}"), ("N1s", f"N8:{tag}")])):
      for c1, c2 in pairs:
        m1 = {p.pid: tables["mass"].get((p.pid, c1)) for p in prompts}
        m2 = {p.pid: tables["mass"].get((p.pid, c2)) for p in prompts}
        d = analysis.cell_diffs({k: v for k, v in m1.items() if v is not None},
                                {k: v for k, v in m2.items() if v is not None}, prompts)
        if d and max(abs(x) for x in d) > 0.10:
          labels[t].append("letter-mass-sensitive")
          break
  return {"tests": tests, "family": family, "verdicts": verdicts,
          "labels": {k: sorted(set(v)) for k, v in labels.items()},
          "descriptive": {k: v for k, v in analysis.abr_tests(
              prompts, tables["soft"], phase2_regret, conditions.BASELINE, entries).items()
              if k.startswith("descr:")}}


# --------------------------------------------------------------- secondary
def e1_diffs(e1_records: Sequence[dict], prompts: Sequence[core.Prompt]) -> dict[str, list[float]]:
  """E1: per entry, cell means of the draw-averaged D = baseline regret - entry regret."""
  reg = collections.defaultdict(lambda: collections.defaultdict(list))
  for r in e1_records:
    if "error" not in r and not r.get("sealed"):
      reg[r["agent"]][r["pid"]].append(r["hard_regret"])
  mean = {a: {pid: float(np.mean(v)) for pid, v in d.items()} for a, d in reg.items()}
  return {a: analysis.cell_diffs(mean.get(conditions.BASELINE, {}), mean.get(a, {}), prompts)
          for a in conditions.ENTRIES}


def e1_prompts() -> list[core.Prompt]:
  """Protocol 8.6: no-information prompts of variants 1-6, information prompts of 1-2."""
  return [p for p in core.prompt_set()
          if (p.C is None and p.variant <= 6) or (p.C is not None and p.variant <= 2)]


def secondary(prompts: Sequence[core.Prompt], test: Sequence[core.Prompt],
              tables: Mapping[str, dict], e1_records: Sequence[dict] | None = None,
              k_per_entry: Mapping[str, dict] | None = None, k_e6: Mapping[str, dict] | None = None,
              k2_if_secondary: dict | None = None, steered_content: Mapping[str, tuple] | None = None,
              phase2_regret: Mapping[str, Mapping[str, float]] | None = None) -> dict:
  """E1-E9 (Protocol 1.5) with one Benjamini-Hochberg family at q = 0.05.
  Inputs that are not yet available are skipped and listed under 'missing'."""
  soft, probs = tables["soft"], tables["probs"]
  def col(t, cond):
    return {p.pid: t[(p.pid, cond)] for p in prompts if (p.pid, cond) in t}
  p_values, effects, missing = {}, {}, []
  if e1_records is not None:
    for a, d in e1_diffs(e1_records, e1_prompts()).items():
      p_values[f"E1:{TAG[a]}"] = analysis.signflip_greater(d)
      effects[f"E1:{TAG[a]}"] = float(np.mean(d)) if d else float("nan")
  else:
    missing.append("E1")
  for a, code in conditions.ENTRY_CODE.items():                         # E2
    r = analysis.calibration_test(prompts, col(probs, "N1"), col(probs, code), n_boot=2000)
    p_values[f"E2:{TAG[a]}"] = r["p"]
    effects[f"E2:{TAG[a]}"] = r["rho_partial"]
  if k_per_entry:                                                         # E3
    for a, kk in k_per_entry.items():
      p_values[f"E3:{TAG[a]}"] = kk["K1"]["p"]
  else:
    missing.append("E3")
  for cond in ("N0", "N1"):                                               # E4 (two-sided)
    bias = {pid: core.expected_bid(pr) - core.oracle_bid_point(next(p for p in prompts if p.pid == pid))
            for pid, pr in col(probs, cond).items()}
    cells = list(analysis.cell_means(bias, prompts).values())
    p_values[f"E4:{cond}"] = two_sided(cells)
    effects[f"E4:{cond}"] = float(np.mean(cells))
  for a in conditions.AGENTS:                                             # E5 wording
    own = conditions.ENTRY_CODE.get(a, "N1")
    para = col(soft, f"N5:{TAG[a]}")
    if para:
      d = analysis.cell_diffs(para, col(soft, own), prompts)
      p_values[f"E5:wording:{TAG[a]}"] = two_sided(d)
      effects[f"E5:wording:{TAG[a]}"] = float(np.mean(d))
  for a in conditions.ENTRIES:                                            # E5 length
    d = analysis.cell_diffs(col(soft, f"N6:{BASE_TAG}"), col(soft, f"N6:{TAG[a]}"), prompts)
    p_values[f"E5:length:{TAG[a]}"] = analysis.signflip_greater(d)
    effects[f"E5:length:{TAG[a]}"] = float(np.mean(d))
  if k_e6:                                                                # E6
    p_values["E6"] = k_e6["K1"]["p"]
  else:
    missing.append("E6")
  if phase2_regret is not None:                                           # E7
    entries_r = {a: (c + "r", TAG[a]) for a, c in conditions.ENTRY_CODE.items()}
    e7 = analysis.abr_tests(prompts, soft, phase2_regret, conditions.BASELINE, entries_r)
    for a in conditions.ENTRIES:
      for fam in ("B", "R"):
        p_values[f"E7:{fam}:{TAG[a]}"] = e7[f"{fam}:{TAG[a]}"]["p"]
  else:
    missing.append("E7")
  means = {a: float(np.mean(list(col(soft, c).values()))) for a, c in conditions.ENTRY_CODE.items()}
  best, worst = min(means, key=means.get), max(means, key=means.get)     # E8
  d = analysis.cell_diffs(col(soft, conditions.ENTRY_CODE[worst]),
                          col(soft, conditions.ENTRY_CODE[best]), prompts)
  p_values["E8"] = analysis.signflip_greater(d)
  effects["E8"] = {"best": TAG[best], "worst": TAG[worst], "mean_diff": float(np.mean(d))}
  if k2_if_secondary is not None:
    p_values["K2"] = k2_if_secondary["p"]
  descriptive = {}
  if steered_content is not None:                                         # E9
    descriptive["E9_fidelity"] = analysis.fidelity(test, soft, steered_content)
  return {"p": p_values, "effects": effects,
          "bh": analysis.benjamini_hochberg(p_values) if p_values else {},
          "descriptive": descriptive, "missing": missing}


# ------------------------------------------------------------- sensitivity
def effect_sizes(cells: Sequence[float]) -> dict:
  x = np.asarray(cells, dtype=float)
  nz = x[x != 0]
  ranks = stats.rankdata(np.abs(nz))
  rbc = float((ranks[nz > 0].sum() - ranks[nz < 0].sum()) / ranks.sum()) if len(nz) else 0.0
  sd = x.std(ddof=1) if len(x) > 1 else float("nan")
  return {"mean": float(x.mean()), "ci95": analysis.bootstrap_ci(x, 0.95),
          "rank_biserial": rbc, "standardised_mean": float(x.mean() / sd) if sd else float("nan")}


def cell_type(p_or_cell) -> str:
  c = p_or_cell.cell if isinstance(p_or_cell, core.Prompt) else p_or_cell
  if c[1] != "C":
    return "no_information"
  return "C_below_V" if c[2] < c[0] else "C_at_or_above_V"


def sensitivity(prompts: Sequence[core.Prompt], tables: Mapping[str, dict],
                phase2_regret: Mapping[str, Mapping[str, float]], near_ceiling: Sequence[tuple] = ()
                ) -> dict:
  """Protocol 11, sensitivity analyses for A, B and R: Wilcoxon and bootstrap-t on
  the primary cell differences; the cell-type subsets; the near-ceiling-excluded
  subset; whole-answer soft regret and Phase 3 hard regret (B, R); effect sizes."""
  entries = {a: (c, TAG[a]) for a, c in conditions.ENTRY_CODE.items()}
  def run(ps, table):
    return _rename(analysis.abr_tests(ps, table, phase2_regret, conditions.BASELINE, entries))
  primary = run(prompts, tables["soft"])
  out = {}
  for t, v in primary.items():
    x = v["effect_cells"]
    out[t] = {"wilcoxon_p": analysis.wilcoxon_greater(x), "bootstrap_t_p": analysis.bootstrap_t_greater(x),
              "effect": effect_sizes(x)}
  for name in ("no_information", "C_below_V", "C_at_or_above_V"):
    sub = [p for p in prompts if cell_type(p) == name]
    for t, v in run(sub, tables["soft"]).items():
      out[t][f"subset:{name}:p"] = v["p"]
  nc = set(map(tuple, near_ceiling))
  sub = [p for p in prompts if p.cell not in nc]
  for t, v in run(sub, tables["soft"]).items():
    out[t]["subset:not_near_ceiling:p"] = v["p"]
  for key in ("soft_full", "hard"):
    for t, v in run(prompts, tables[key]).items():
      if t[0] in "BR":
        out[t][f"{key}:p"] = v["p"]
  return out


def mixed_model_table(prompts: Sequence[core.Prompt], tables: Mapping[str, dict],
                      phase2_regret: Mapping[str, Mapping[str, float]], path: str) -> None:
  """Prompt-level D for every confirmatory comparison, for analysis/mixed_model.R
  (lmer(D ~ 1 + (1|cell) + (1|variant)), REML, Satterthwaite, one-sided)."""
  soft = tables["soft"]
  rows = []
  for a in conditions.ENTRIES:
    code, tag, n = conditions.ENTRY_CODE[a], TAG[a], ENTRY_NUMBER[a]
    comps = {f"A{n}": lambda p: phase2_regret[conditions.BASELINE][p.pid] - phase2_regret[a][p.pid]}
    for c in ("N0", "N1", f"N6:{tag}", f"N7:{tag}"):
      comps[f"B{n}:{c}"] = lambda p, c=c: soft[(p.pid, c)] - soft[(p.pid, code)]
    for c in ("N0", "N1s"):
      comps[f"R{n}:{c}"] = lambda p, c=c: soft[(p.pid, c)] - soft[(p.pid, f"N8:{tag}")]
    for name, fn in comps.items():
      for p in prompts:
        try:
          rows.append({"test": name, "pid": p.pid, "cell": str(p.cell), "variant": p.variant,
                       "D": fn(p)})
        except KeyError:
          pass
  with open(path, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["test", "pid", "cell", "variant", "D"])
    w.writeheader()
    w.writerows(rows)


def write(path: str, obj) -> None:
  with open(path, "w") as f:
    json.dump(obj, f, indent=1, default=str)
