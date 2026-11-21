"""Unit tests for the condition builders and the confirmatory statistics."""
import math
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

from refimpl import analysis, conditions, core, steering


class WordTok:
  """Whitespace stand-in tokenizer for unit tests (real runs use Gemma's)."""
  def encode(self, text, add_special_tokens=False):
    return text.split(" ")
  def decode(self, ids):
    return " ".join(ids)


# ------------------------------------------------------------- conditions
def test_strict_removal():
  t = ("Anya can sell the fruit for 5 coins. The seller paid 3 coins. "
       "Offering 3 coins gives a profit of 2 coins. 2 coins: 0.4, 3 coins: 1.2. "
       "Option (b) looks best. Prices range from 1 coin to 5 coins. She is careful. "
       "She should offer 2. A price of 3 seems fair. She will pay $2 tops. "
       "The average price is 3 coins. Fruit weighs 2 kg each.")
  out = conditions.remove_recommendations_strict(t)
  for kept in ("sell the fruit for 5 coins", "paid 3 coins", "She is careful",
               "average price is 3 coins", "weighs 2 kg"):
    assert kept in out, kept
  for gone in ("profit", "0.4", "(b)", "range from", "offer 2", "price of 3", "$2"):
    assert gone not in out, gone


def test_qa_filler_exact_length_and_format():
  tok = WordTok()
  f = conditions.qa_filler(["A busy square.", "Stalls everywhere."], 37, tok)
  assert len(tok.encode(f)) == 37 and f.startswith("Question: ")


def test_condition_set():
  p = core.Prompt(1, 5, "information", 3)
  vp = conditions.v_prime(p)
  S = {a: {p.pid: f"Question: q\nAnswer: text of {a}", vp.pid: "other"} for a in conditions.AGENTS}
  off = {a: {p.pid: 3} for a in conditions.AGENTS}
  para = {a: {p.pid: "para"} for a in conditions.AGENTS}
  c = conditions.build_conditions(p, S, S, off, para, ["Open."], WordTok())
  assert len(c) == conditions.CONDITION_COUNT == 28
  assert c["N0"] is None and c["N10"] == "Anya Blossomwood should offer 3 coins."
  para[conditions.ENTRIES[0]][p.pid] = None
  c = conditions.build_conditions(p, S, S, off, para, ["Open."], WordTok())
  assert len(c) == 27                                    # failed paraphrase dropped


def test_audit_prompt():
  text, m = conditions.audit_prompt("Some notes.")
  assert text.endswith("Answer: (") and "(f) The notes do not favour any price" in text
  assert m["a"] == 1 and m["e"] == 5 and m["f"] is None


# ------------------------------------------------------------------ tuner
def test_tuner_can_choose_no_steering():
  assert steering.tune(lambda L, a: (-0.1, 1.0)) is None          # all settings hurt
  assert steering.tune(lambda L, a: (0.2, 0.5)) is None           # none coherent
  best = steering.tune(lambda L, a: (0.1 * a if L == 9 else 0.0, 1.0))
  assert best[:2] == (9, 4.0)


# ------------------------------------------------------------ basic stats
def test_signflip_exact_and_mc():
  x = [0.05] * 12 + [-0.01] * 6
  p_exact = analysis.signflip_greater(x)                       # n = 18: exact
  p_mc = analysis.signflip_greater(x * 2, n_mc=20_000)         # n = 36: Monte Carlo
  assert 0 < p_exact < 0.01 and 0 < p_mc < 0.01


def test_bh_holm_reverse_and_verdicts():
  r = analysis.benjamini_hochberg({"a": 0.01, "b": 0.02, "c": 0.035, "d": 0.5})
  assert r == {"a": True, "b": True, "c": True, "d": False}
  assert analysis.reverse_p(0.004, 0.5, 0.9) == 0.012
  assert analysis.verdict(False, True, (-0.4, -0.2), 0.05) == "reversed"
  assert analysis.verdict(False, False, (-0.01, 0.02), 0.05) == "equivalent"
  assert analysis.verdict(False, False, None, 0.05) == "inconclusive"
  v = analysis.confirmatory_verdicts({
      "good": {"p": 1e-4, "p_reverse": 1.0, "effect_cells": [0.2] * 35},
      "bad": {"p": 1.0, "p_reverse": 1e-5, "effect_cells": [-0.2] * 35},
      "null": {"p": 0.6, "p_reverse": 0.4, "effect_cells": [0.0, 0.01, -0.01] * 12}})
  assert v == {"good": "supported", "bad": "reversed", "null": "equivalent"}


def test_power_simulation_monotone():
  lo = analysis.power_simulation(sd=0.3, n_cells=35, n_sim=300)
  hi = analysis.power_simulation(sd=0.05, n_cells=35, n_sim=300)
  assert hi > 0.95 and lo < hi


# -------------------------------------------------------------------- A/B/R
def test_abr_tests_orientation():
  ps = core.prompt_set([1, 2])
  base, ent = conditions.BASELINE, conditions.ENTRIES[0]
  tag = ent.rsplit(".", 1)[-1]
  reg = {base: {p.pid: 0.5 for p in ps}, ent: {p.pid: 0.2 for p in ps}}
  soft = {}
  for p in ps:
    for c, v in {"N0": 0.6, "N1": 0.5, "N1s": 0.55, "N2": 0.2, f"N6:{tag}": 0.6, f"N7:{tag}": 0.5,
                 f"N8:{tag}": 0.3, f"N9:{tag}": 0.25, "N10": 0.0}.items():
      soft[(p.pid, c)] = v + 0.01 * (p.variant % 3)
  out = analysis.abr_tests(ps, soft, reg, base, {ent: ("N2", tag)})
  for k in ("A", "B", "R"):
    assert out[f"{k}:{tag}"]["p"] < 1e-4 and out[f"{k}:{tag}"]["p_reverse"] == 1.0


# -------------------------------------------------------------------- K1
def test_k1_single_pvalue_and_sharpen_null():
  d = [0.2] * 18
  r = analysis.k1_test(d, {"wording": [0.0] * 18, "sharpen": [0.05] * 18}, 0.2, [0.0] * 1000)
  assert r["p"] < 0.05 / 11 and r["min_attainable_random_p"] < 0.05 / 11
  r = analysis.k1_test(d, {"wording": [0.0] * 18, "sharpen": [0.3] * 18}, 0.2, [0.0] * 1000)
  assert r["p"] > 0.5                    # mere sharpening does better: fails
  p = {1: 0.1, 2: 0.6, 3: 0.2, 4: 0.05, 5: 0.05}
  s = analysis.sharpen(p, 3.0)
  assert max(s, key=s.get) == 2 and s[2] > p[2]


# -------------------------------------------------------------------- K2
def _base(ps):
  def around(m):
    w = {k: math.exp(-(k - m) ** 2) for k in core.PRICES}
    z = sum(w.values())
    return {k: w[k] / z for k in core.PRICES}
  return {p.pid: around(min(5, p.V - 1) + 0.3 * (p.variant % 3)) for p in ps}


def _test_prompts():
  return [p for p in core.prompt_set([1, 2, 3]) if core.steering_cell_split(p.cell) == "test"]


def test_k2_uses_unique_best_cells_only():
  ps = _test_prompts()
  base = _base(ps)
  r = analysis.calibration_test(ps, base, {k: analysis.flatten(v, 0.5) for k, v in base.items()},
                                n_boot=100)
  assert r["n_cells"] == 12


def test_k2_controls_do_not_pass():
  ps = _test_prompts()
  base = _base(ps)
  for steer in ({pid: analysis.attractor(pr, 2, 0.6) for pid, pr in base.items()},
                {pid: analysis.flatten(pr, 0.6) for pid, pr in base.items()},
                {pid: analysis.sharpen(pr, 3.0) for pid, pr in base.items()}):
    r = analysis.calibration_test(ps, base, steer, n_boot=300)
    assert r["p"] > 0.05, r


def test_k2_oracle_steering_passes():
  ps = _test_prompts()
  base = _base(ps)
  steer = {p.pid: {j: (0.96 if j == core.oracle_bids(p)[0] else 0.01) for j in core.PRICES}
           for p in ps}
  r = analysis.calibration_test(ps, base, steer, n_boot=300)
  assert r["rho_partial"] > 0.5 and r["p"] < 0.05, r


def test_k_tests_assembly_and_fidelity():
  test = [p for p in core.prompt_set([1, 2]) if core.steering_cell_split(p.cell) == "test"]
  flat = {k: 0.2 for k in core.PRICES}
  def toward(p):
    return {j: (0.96 if j == round(core.oracle_bid_point(p)) else 0.01) for j in core.PRICES}
  def res(gain, steer):
    r0 = {p.pid: core.soft_regret(p, flat) for p in test}
    return {p.pid: (r0[p.pid], r0[p.pid] - gain, flat, steer(p)) for p in test}
  named = {"content": res(0.3, toward), "wording": res(0.0, lambda p: flat),
           "length": res(0.0, lambda p: flat), "answer": res(0.0, lambda p: flat)}
  out = analysis.k_tests(test, named, res(0.3, toward),
                         [res(0.0, lambda p: flat) for _ in range(1000)], gamma=1.0, n_boot=200)
  assert out["K1"]["p"] < 0.05 / 11
  assert out["K2"]["rho_partial"] > 0.5
  soft = {}
  for p in test:
    soft[(p.pid, "N1")] = 1.0
    for c in ("N2", "N3", "N4"):
      soft[(p.pid, c)] = 0.4
  half = {p.pid: (1.0, 0.7, flat, flat) for p in test}
  assert abs(analysis.fidelity(test, soft, half) - 0.5) < 1e-9
