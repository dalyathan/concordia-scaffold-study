"""scripts/targeted_prepare.py on CPU with a stand-in rule and stand-in replies, writing only to a scratch folder."""
import importlib.util, json, os, shutil

import pytest

from conftest import ROOT

sp = importlib.util.spec_from_file_location("tp", os.path.join(ROOT, "scripts", "targeted_prepare.py"))
tp = importlib.util.module_from_spec(sp); sp.loader.exec_module(tp)
RULE = {"clauses": [{"where": {"type": ["no_cost"], "V_min": 10}, "weight": 3}, {"where": {"type": ["no_cost"]}, "weight": 1}],
        "reasoning": "stand-in"}


@pytest.fixture
def gen(tmp_path, monkeypatch):
  for f in ("examples_packet.md",):
    shutil.copy(os.path.join(tp.GEN, f), tmp_path / f)
  monkeypatch.setattr(tp, "GEN", str(tmp_path))
  json.dump(RULE, open(tmp_path / "targeting_rule_qwen25_7b.json", "w"))
  return tmp_path


def test_draws_rules():
  _, cells = tp.pool()
  d, w = tp.draws(RULE, cells)
  assert set(d) == {f"{a}_s{s}" for a in "TRN" for s in (0, 1, 2)}
  for k, ids in d.items():
    assert len(ids) == 50 == len(set(ids)) and not any(cells[i]["select3"] for i in ids)
    if k[0] in "TN":
      assert all(cells[i]["type"] == "no_cost" for i in ids)
  assert d["R_s0"] != d["R_s1"] and d == tp.draws(RULE, cells)[0]          # per-seed draws, deterministic
  assert sum(cells[i]["V"] >= 10 for i in d["T_s0"]) > sum(cells[i]["V"] >= 10 for i in d["N_s0"]) - 5


def test_unknown_rule_key_and_too_narrow_rule_are_refused():
  _, cells = tp.pool()
  with pytest.raises(SystemExit, match="unknown keys"):
    tp.draws({"clauses": [{"where": {"colour": ["red"]}, "weight": 1}]}, cells)
  with pytest.raises(SystemExit, match="needs 50"):
    tp.draws({"clauses": [{"where": {"type": ["at_or_above"]}, "weight": 1}]}, cells)


def test_orders_are_a_function_of_the_cell():
  assert tp.orders_for("x") == tp.orders_for("x") and len(set(tp.orders_for("x"))) == 3


def test_packets_are_arm_blind_and_labels_check(gen):
  tp.cmd_draw("qwen25_7b"); tp.cmd_packets("qwen25_7b")
  ids = json.load(open(gen / "targeted_label_ids_qwen25_7b.json"))
  texts = "".join(open(p).read() for p in gen.glob("targeted_label_packet_*.md"))
  import re
  assert not re.search(r"\b[TRN]_s[0-2]\b|\barms?\b|targeted|random", texts)
  _, cells = tp.pool()
  # stand-in replies: the payoff-optimal lowest price (the label rule Claude matched on the original 100)
  ks = sorted(ids)
  for n, k in enumerate(range(0, len(ks), tp.PACKET_SIZE)):
    json.dump({i: cells[ids[i]]["grid"][min(cells[ids[i]]["best_positions"])] for i in ks[k:k + tp.PACKET_SIZE]},
              open(gen / f"targeted_label_reply_qwen25_7b_{n + 1}.json", "w"))
  tp.cmd_labels("qwen25_7b")
  out = json.load(open(gen / "targeted_labels_qwen25_7b.json"))
  assert all(v == 1.0 for arm in out["agreement_with_payoff_rule_by_arm_and_type"].values() for v in arm.values())
