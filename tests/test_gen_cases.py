import json, os, sys, collections
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "demo"))
import gen_cases as g
from refimpl import core

DATA = os.path.join(os.path.dirname(__file__), "..", "demo", "gen")
CELLS = json.load(open(os.path.join(DATA, "cells.json")))["cells"]
CASES = [json.loads(l) for l in open(os.path.join(DATA, "cases.jsonl"))]


def test_payoff_equals_core_on_the_original_game():
  for V in core.VALUES:
    for line, C in [("neutral", None), ("pressure", None)] + [("information", c) for c in core.COSTS]:
      p = core.Prompt(1, V, line, C)
      lab = g.label(V, g.GRIDS["A"], C, (1, 5))
      assert lab["best_offers"] == core.oracle_bids(p)
      for k in core.PRICES:
        assert abs(g.payoff(V, g.GRIDS["A"], C, (1, 5), k) - core.payoff(p, k)) < 1e-12


def test_known_labels():
  assert g.label(6, g.GRIDS["B"], 3, (1, 5))["best_offers"] == [3]            # offer exactly the stated cost
  assert g.label(3, g.GRIDS["B"], 5, (1, 5))["best_offers"] == [2, 3, 4]    # cost >= resale: every offer below the cost ties at 0
  lab = g.label(8, g.GRIDS["D"], None, (1, 10))                              # no cost, step-2 grid, uniform prior 1..10
  assert lab["payoffs"][1] == (8 - 4) * 0.4 and lab["best_offers"] == [4]
  assert g.label(9, g.GRIDS["A"], 9, (1, 5))["all_tie"] is True              # stated cost above every price: all offers tie at 0


def test_ties_flagged_and_excluded():
  assert not any(c["all_tie"] for c in CELLS)
  assert g.label(10, g.GRIDS["C"], 12, (1, 5))["all_tie"]


def test_splits_are_by_whole_cells_and_balanced():
  by = collections.defaultdict(set)
  for c in CASES:
    by[c["cell"]].add(c["split"])
  assert all(len(v) == 1 for v in by.values())
  assert len({c["cell"] for c in CELLS}) == len(CELLS)
  cnt = collections.Counter((c["split"], c["type"]) for c in CELLS)
  assert cnt[("train", "below")] == cnt[("train", "at_or_above")] == cnt[("train", "no_cost")] == 100
  assert cnt[("tune", "below")] == cnt[("tune", "at_or_above")] == cnt[("tune", "no_cost")] == 14
  assert cnt[("test_same", "below")] == cnt[("test_same", "at_or_above")] == cnt[("test_same", "no_cost")] == 20
  assert collections.Counter(len([c for c in CASES if c["cell"] == k["cell"]]) for k in CELLS) == {2: len(CELLS)}


def test_hard_slices_use_unseen_values():
  tr = [c for c in CELLS if c["split"] == "train"]
  seen_V, seen_g, seen_w = {c["V"] for c in tr}, {c["grid_name"] for c in tr}, {c["wording"] for c in tr}
  for c in CELLS:
    if c["slice"] == "hard_V":
      assert c["V"] not in seen_V and c["V"] >= 10
    if c["slice"] == "hard_grid":
      assert c["grid_name"] not in seen_g
    if c["slice"] == "hard_wording":
      assert c["wording"] not in seen_w
    if c["split"] in ("train", "tune", "test_same"):
      assert c["V"] in g.SEEN_V and c["grid_name"] in g.SEEN_GRIDS and c["wording"] in g.SEEN_W


def test_no_old_names_or_old_test_cells_and_pools_disjoint():
  old = set(core.FEMALE_NAMES) | set(core.MALE_NAMES)
  assert not any(c["buyer"] in old or c["seller"] in old for c in CASES)
  pool = lambda sp: {c["buyer"] for c in CASES if c["split"] in sp} | {c["seller"] for c in CASES if c["split"] in sp}
  assert not pool(("train",)) & pool(("tune", "test_same", "test_hard"))
  assert not pool(("tune",)) & pool(("test_same", "test_hard"))
  assert not any(g.old_test_cell(c["V"], c["grid_name"], c["line"], c["C"], c["prior"]) for c in CELLS)


def test_prompt_has_five_options_and_states_grid_and_prior():
  for c in CASES[::37]:
    text, l2p = g.render(c, g.orders()[2])
    assert sorted(l2p.values()) == sorted(c["grid"]) and len(l2p) == 5
    assert f"between {c['prior'][0]} and {c['prior'][1]} coins per kilogram" in text
    assert f"{c['V']} coins back" in text
    if c["C"] is not None:
      assert f"{c['C']} coin" in text


def test_fingerprints_match_the_committed_lists():
  fp = json.load(open(os.path.join(DATA, "fingerprints.json")))
  cells, cases, _ = g.build()
  assert g.fingerprints(cells, cases) == fp


def test_payoff_matches_an_independent_brute_force_over_the_whole_space():
  from fractions import Fraction
  for gname, grid in g.GRIDS.items():
    for prior in g.PRIORS:
      lo, hi = prior
      for V in range(2, 13):
        for k in grid:                                       # no stated cost: enumerate every possible farm cost
          costs = range(lo, hi + 1)
          exp = sum(Fraction(V - k) for c in costs if c <= k) / len(costs)
          assert abs(g.payoff(V, grid, None, prior, k) - float(exp)) < 1e-12
        for C in range(1, 15):
          for k in grid:
            assert g.payoff(V, grid, C, prior, k) == (V - k if k >= C else 0)


def test_hard_slice_composition_and_v2_fingerprints():
  cnt = collections.Counter((c["slice"], c["type"]) for c in CELLS if c["split"] == "test_hard")
  assert cnt[("hard_V", "at_or_above")] == 0 and cnt[("hard_V", "below")] == cnt[("hard_V", "no_cost")] == 10
  for sl in ("hard_grid", "hard_wording"):
    assert {cnt[(sl, t)] for t in g.TYPES} == {7}
  assert all(c["wording"] == 2 for c in CELLS if c["slice"] == "hard_wording")
  assert all(c["grid_name"] in g.HARD_GRIDS for c in CELLS if c["slice"] == "hard_grid")
  assert json.load(open(os.path.join(DATA, "fingerprints_v2.json")))["cells"] == g.fingerprints_v2(CELLS)["cells"]
