import math
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from refimpl import core, analysis


def test_prompt_set_counts():
  ps = core.prompt_set()
  assert len(ps) == 420
  assert len({p.pid for p in ps}) == 420
  assert len(core.all_cells()) == 35


def test_oracle_table():
  # Hand-computed values (section 1.2).
  exp = {2: ([1], 0.2), 3: ([1, 2], 0.4), 4: ([2], 0.8), 5: ([2, 3], 1.2), 6: ([3], 1.8)}
  for V, (bids, pay) in exp.items():
    p = core.Prompt(1, V, "neutral", None)
    assert core.oracle_bids(p) == bids
    assert math.isclose(core.oracle_payoff(p), pay)
  p = core.Prompt(1, 5, "information", 3)
  assert core.oracle_bids(p) == [3] and core.oracle_payoff(p) == 2.0
  p = core.Prompt(1, 3, "information", 3)          # C == V: k < C or k == C, payoff 0
  assert core.oracle_bids(p) == [1, 2, 3] and core.oracle_payoff(p) == 0.0
  p = core.Prompt(1, 2, "information", 4)          # C > V
  assert core.oracle_bids(p) == [1, 2, 3]
  assert core.hard_regret(p, 5) == 3.0             # overpay by 3 when accepted


def test_regret_nonnegative_everywhere():
  for p in core.prompt_set([1]):
    for k in core.PRICES:
      assert core.hard_regret(p, k) >= -1e-12


def test_split_is_disjoint_and_sized():
  cells = core.all_cells()
  dev = [c for c in cells if core.steering_cell_split(c) == "dev"]
  test = [c for c in cells if core.steering_cell_split(c) == "test"]
  assert len(dev) == 17 and len(test) == 18 and not set(dev) & set(test)
  ext = core.all_cells(core.VALUES + core.EXT_VALUES)      # extension: V = 7, 8
  assert len(ext) == 49
  assert sum(core.steering_cell_split(c) == "test" for c in ext) == 25


def test_seed_varies_with_draw():
  a = core.call_seed("x", "agent", "pid", 0)
  b = core.call_seed("x", "agent", "pid", 1)
  assert a != b and 0 <= a < 2**64


def test_reasoning_entry():
  e = core.reasoning_entry("Ctx\nQuestion: What would Ann do?\nAnswer: Ann would ",
                           " offer two coins. ")
  assert e == "Question: What would Ann do?\nAnswer: Ann would offer two coins."
  e = core.reasoning_entry("Some context\nLast line here", "x")
  assert e.startswith("Question: Last line here")
  # The prompt's own answer stem is kept, so the entry reads as the model saw it.
  e = core.reasoning_entry("Ctx\nQuestion: What would Ann do?\nAnswer: Ann would ", "offer 2.")
  assert e == "Question: What would Ann do?\nAnswer: Ann would offer 2."
  e = core.reasoning_entry("Question: Summarize the observations.\nAnswer: ", "Ann haggles.")
  assert e == "Question: Summarize the observations.\nAnswer: Ann haggles."
  calls = [("Question: Summarize the observations.\nAnswer: ", "x."),
           ("Question: What would Ann do?\nAnswer: Ann would ", "offer 2.")]
  assert core.build_S(calls, reasoning_only=True) == "Question: What would Ann do?\nAnswer: Ann would offer 2."




def test_softmax_and_expected_bid():
  probs = core.softmax_scores({"a": 0.0, "b": 0.0, "c": -100, "d": -100, "e": -100},
                              {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5})
  assert math.isclose(probs[1], 0.5, abs_tol=1e-9)
  assert math.isclose(core.expected_bid(probs), 1.5, abs_tol=1e-9)


def test_cyclic_orders():
  o = core.cyclic_orders()
  assert o[0] == (1, 2, 3, 4, 5) and o[1] == (2, 3, 4, 5, 1) and len(o) == 5


def test_holm_and_iut():
  h = analysis.holm({"a": 0.001, "b": 0.02, "c": 0.04})
  assert h == {"a": True, "b": True, "c": True}
  h = analysis.holm({"a": 0.001, "b": 0.04, "c": 0.04})
  assert h["a"] and not h["b"] and not h["c"]
  assert analysis.iut(0.01, 0.2) == 0.2


def test_signflip_and_wilcoxon_direction():
  assert analysis.signflip_greater([0.1] * 20 + [0.2] * 15) < 1e-4
  assert analysis.signflip_greater([-0.1] * 18) == 1.0
  assert analysis.signflip_less([-0.1] * 18) < 1e-4


def test_wilcoxon_direction():
  assert analysis.wilcoxon_greater([0.1] * 20 + [0.2] * 15) < 1e-4
  assert analysis.wilcoxon_greater([-0.1] * 35) > 0.99




def test_seed_only_inside_call_context():
  import random
  from refimpl.local_gemma2 import LocalGemma2, call_context, context_is_set
  lm = object.__new__(LocalGemma2)                    # _seed needs no model
  assert not context_is_set()
  random.seed(123); expected = random.random()
  random.seed(123)
  assert lm._seed("prompt") is None                    # Phase 1: launcher seed untouched
  assert random.random() == expected
  with call_context(agent="a", pid="p"):
    assert context_is_set()
    s = lm._seed("prompt")
    assert s == core.call_seed("prompt", "a", "p", 0)
    x = random.random()
    lm._seed("prompt")
    assert random.random() == x                        # Phases 2-3: per-call seed
  with call_context():                                 # an empty context still counts as set
    assert context_is_set()
  assert not context_is_set()


def test_bootstrap_t_direction():
  assert analysis.bootstrap_t_greater([0.1] * 20 + [0.2] * 15) < 1e-3
  assert analysis.bootstrap_t_greater([-0.1, -0.2, 0.05, -0.3] * 5) > 0.5


def test_equivalence_family_and_union_family():
  assert analysis.confirmatory_family(False)[-1] == "K1" and len(analysis.confirmatory_family(False)) == 10
  assert analysis.confirmatory_family(True)[-1] == "K2" and len(analysis.confirmatory_family(True)) == 11
  p = analysis.bootstrap_equivalence_p([0.001, -0.002, 0.003, 0.0] * 9, 0.05)
  assert p < 0.001
  assert analysis.bootstrap_equivalence_p([0.04, 0.06, 0.05, 0.07] * 9, 0.05) > 0.4
