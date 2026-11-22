"""Unit tests for the demo tools (no model): split, pair balance checks, offline
baselines, steercheck on a toy problem, and floor.py's command parser and screens."""
import os
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "demo"))
import common  # noqa: E402
import floor  # noqa: E402
import pairs_template  # noqa: E402
import steercheck  # noqa: E402
import textrows  # noqa: E402
from refimpl import analysis, core, demo  # noqa: E402


# ------------------------------------------------------------------ split
def test_split_by_cell():
  ps = demo.demo_prompts()
  s = {p.pid: common.case_split(p) for p in ps}
  assert sum(v == "build" for v in s.values()) == 34
  assert sum(v == "tuning" for v in s.values()) == 34
  assert sum(v == "test" for v in s.values()) == 72
  for p in ps:
    dev = core.steering_cell_split(p.cell) == "dev"
    assert (s[p.pid] == "test") == (not dev)
    if dev:
      assert s[p.pid] == ("build" if p.variant in (15, 16) else "tuning")
  # No cell is shared between test and the development splits.
  cells = lambda name: {p.cell for p in ps if s[p.pid] == name}
  assert not cells("test") & (cells("build") | cells("tuning"))
  assert cells("build") == cells("tuning") and len(cells("build")) == 17


def test_saved_splits_and_live_case():
  sp = common.load_splits()
  live = common.prompts_by_id()[sp["live_case"]]
  assert sp["case_split"][live.pid] == "test" and live.C is not None and live.C < live.V
  assert {k: sum(v == k for v in sp["case_split"].values()) for k in ("build", "tuning", "test")} == \
      sp["counts"]


# ------------------------------------------------------------------ pairs
def _words(t):
  return len(t.split())


def test_pair_balance_checks():
  pairs, lower = pairs_template.build_pairs()
  c = pairs_template.checks(pairs, _words)
  assert c["lengths_within_10pct"] and c["direction_balanced"] and c["means_within_0.25"]
  P = common.prompts_by_id()
  for x in pairs:
    best = core.oracle_bids(P[x["pid"]])
    assert x["good_offer"] in best and x["bad_offer"] not in best
  assert all(x["A_offer"] == x["B_offer"] - 1 for x in lower)
  assert not any(pairs_template.all_optimal(P[x["pid"]]) for x in pairs)


def test_pair_checks_detect_imbalance():
  pairs, _ = pairs_template.build_pairs()
  skewed = [dict(x, bad_offer=5, bad_direction="above") for x in pairs]
  c = pairs_template.checks(skewed, _words)
  assert not c["direction_balanced"] and not c["means_within_0.25"]


def test_method_paragraph_is_correct_and_numberless():
  c = textrows.check_method()
  assert c["ok"] and c["cells_checked"] == 49


# -------------------------------------------------------------- baselines
def test_offline_baselines():
  p = demo.DemoPrompt(15, 5, "information", 2)
  d = {1: 0.1, 2: 0.2, 3: 0.4, 4: 0.2, 5: 0.1}
  assert analysis.tilt(d, 0.0) == pytest.approx(d)
  lowered = analysis.tilt(d, -1.0)
  assert core.expected_bid(lowered) < core.expected_bid(d)
  assert analysis.attractor(d, 2, 1.0)[2] == pytest.approx(1.0)
  assert analysis.flatten(d, 1.0)[3] == pytest.approx(0.2)
  beta = floor.best_shift([d], [p])
  loss = lambda b: core.soft_regret(p, analysis.tilt(d, b))
  assert loss(beta) <= loss(0.0) + 1e-12 and beta < 0       # best offer 2 is below the mode


# ------------------------------------------------------------- steercheck
def test_steercheck_toy():
  res = steercheck.toy()
  rows = {(r["name"], r["budget"]): r for r in res["rows"]}
  plain, toy = rows[("plain", "full")], rows[("toy", "full")]
  assert toy["reduction"] > 0.3 and toy["soft_regret"] < plain["soft_regret"]
  assert toy["reduction_ci"][0] > 0                            # cell-bootstrap interval
  assert rows[("-toy", "full")]["reduction"] <= 1e-12          # negation never helps here
  assert res["summary"]["matched_rank_p"] < 0.5
  assert any(n.startswith("const shift") for n, _ in rows)
  lines = steercheck.format_table(res, colour=False)
  assert max(len(l) for l in lines) <= 80


# ------------------------------------------------------------------ floor
def test_floor_parser():
  assert floor.parse_command("case v15-V3-information-C1") == ("case", ["v15-V3-information-C1"])
  assert floor.parse_command("cost none") == ("cost", ["none"])
  assert floor.parse_command("dial show") == ("dial", ["show"])
  assert floor.parse_command("text wrong_rule") == ("text", ["wrong_rule"])
  assert floor.parse_command("adapter template") == ("adapter", ["template"])
  for bad in ("", "fly", "case", "case v01-V3-neutral", "case v14-V3-neutral",
              "case v15-V3-information", "cost 7", "adapter has.dot", "adapter two words", "shuffle now"):
    with pytest.raises(floor.CommandError):
      floor.parse_command(bad)


class FakeResult:
  def __init__(self, probs):
    self.probs, self.sec = probs, 0.01

  @property
  def top(self):
    return max(core.PRICES, key=lambda k: (self.probs[k], -k))


class FakeEngine:
  def score(self, p, condition, orders=None):
    k = 2 if condition[0] == "plain" else 1
    return FakeResult({j: (0.6 if j == k else 0.1) for j in core.PRICES})

  def say(self, p, condition=None):
    return " 2 coins.", 2


def test_floor_session_screens(tmp_path):
  f = floor.Floor(FakeEngine(), str(tmp_path / "log.jsonl"), colour=True)
  live = "v15-V3-information-C1"                 # a test case
  dev = "v17-V3-information-C2"                  # a held-out tune case
  for cmd in (f"case {live}", "cost 3", "cost none", "shuffle", "say", "adapter off", "plain", "table",
              "fly", "case v02-V3-neutral", f"case {dev}", "text method", "adapter on", "plain"):
    out = f.run(cmd)
    assert len(out) <= floor.SCREEN, cmd
    assert max(floor.visible_len(l) for l in out) <= floor.WIDTH, cmd
    assert out[-1].startswith("[") and out[-1].endswith("s]")
  assert f.rows[0]["offer"] == 2 and f.rows[0]["regret"] == 1.0       # best offer is 1
  assert any(r["condition"] == "text method" and r["offer"] == 1 for r in f.rows)
  log = [l for l in open(tmp_path / "log.jsonl")]
  assert len(log) == 14 and "\033[" not in "".join(log)                # replayable, no colour


def test_floor_refuses_interventions_on_test_cases():
  f = floor.Floor(FakeEngine(), None, colour=False)
  live = "v15-V3-information-C1"
  f.run(f"case {live}")
  for cmd in ("text method", "steer demo/configs/random_l12.json", "adapter on", "adapter method_lr3e-04_s0"):
    out = f.run(cmd)
    assert "not allowed" in out[0], (cmd, out)
  assert f.condition == ("plain", None)
  assert not any(r["condition"].startswith(("text", "steer", "adapter")) for r in f.rows if r["ok"])
  # plain-only analyses stay available on the test case
  assert "error" not in f.run("cost 3")[0] and "error" not in f.run("shuffle")[0]


def test_model_engine_cache_is_keyed_by_adapter():
  """Two adapters (or none) on one case must never share a cached result."""
  import contextlib
  calls = []
  class FakeScoring:
    ORDERS = core.cyclic_orders()
    def key(self, p): return (p.variant, p.V, p.line, p.C)
    def adapter_context(self, peft, name):
      self.active = name
      return contextlib.nullcontext()
    def score(self, lm, p, notes=None, orders=None, steer=None):
      calls.append(self.active)
      return FakeResult({k: (0.6 if k == (1 if self.active == "A" else 2 if self.active == "B" else 3) else 0.1)
                         for k in core.PRICES})
  eng = object.__new__(floor.ModelEngine)
  eng.scoring, eng.cache, eng.lm, eng.peft, eng.vectors = FakeScoring(), {}, None, object(), {}
  p = demo.DemoPrompt(17, 3, "information", 2)
  a = eng.score(p, ("adapter", "A")); b = eng.score(p, ("adapter", "B")); n = eng.score(p, ("plain", None))
  assert (a.top, b.top, n.top) == (1, 2, 3)
  eng.score(p, ("adapter", "A")); eng.score(p, ("plain", None))
  assert calls == ["A", "B", None]                  # repeats are served from the cache, per adapter


def test_regret_colour_only():
  assert floor.regret_text(0.0).startswith(floor.GREEN)
  assert floor.regret_text(0.5).startswith(floor.RED)
  assert floor.regret_text(0.5, colour=False) == "0.50"


def test_steercheck_checkpoint_resume_skips_done_points():
  import math
  calls = {"n": 0}
  cases = [(i, (i % 5) + 1) for i in range(10)]
  def score(case, steer, orders):
    calls["n"] += 1
    a = 0.0 if steer is None else float(steer[1][0])
    logits = {k: -abs(k - 2) - a * abs(k - case[1]) for k in range(1, 6)}
    z = sum(math.exp(v) for v in logits.values())
    return {k: math.exp(v) / z for k, v in logits.items()}, 0.8
  args = dict(best=lambda c: {c[1]}, value=lambda c, k: float(k == c[1]), cell=lambda c: c[1],
              vectors={"v": {0: np.array([1.0])}}, grid=[(None, 0.0), (0, 1.0), (0, 2.0)],
              full_orders=lambda c: [0], matched_orders=lambda c: [0],
              reference={"r": {0: np.array([-1.0])}}, n_boot=50, log=lambda *a: None,
              case_key=lambda c: c[0])
  ck = steercheck.MemoryCheckpoint()
  first = steercheck.run_controls(score, cases, checkpoint=ck, **args)
  n_first = calls["n"]
  calls["n"] = 0
  second = steercheck.run_controls(score, cases, checkpoint=ck, **args)
  assert calls["n"] == 2 * len(cases)                 # only the two plain baselines
  assert n_first > calls["n"]
  assert [r["soft_regret"] for r in first["rows"]] == [r["soft_regret"] for r in second["rows"]]
