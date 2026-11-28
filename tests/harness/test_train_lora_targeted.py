"""harness/train_lora.py extension for the targeted arms (TARGETED_PLAN.md step 5). CPU only: argument rules, the extra-cell assembly,
run ids and solver names per arm, and that the 100-cell recipe is unchanged. No model is loaded."""
import importlib.util, json, os, types

import pytest

from conftest import ROOT
from harness import train_lora as TL
from harness.tasks.haggling3 import Haggling3Task

sp = importlib.util.spec_from_file_location("tp", os.path.join(ROOT, "scripts", "targeted_prepare.py"))
tp = importlib.util.module_from_spec(sp); sp.loader.exec_module(tp)
RULE = {"clauses": [{"where": {"type": ["no_cost"]}, "weight": 1}], "reasoning": "stand-in"}


@pytest.fixture
def files(tmp_path):
  _, cells = tp.pool()
  d, _ = tp.draws(RULE, cells)
  allc = sorted({i for v in d.values() for i in v})
  dr = {"draws": d, "draws_sha256": tp.sha_obj(d), "rule_sha256": tp.sha_obj(RULE), "orders": {c: tp.orders_for(c) for c in allc},
        "orders_sha256": tp.sha_obj({c: tp.orders_for(c) for c in allc})}
  lab = {c: min(cells[c]["best_positions"]) for c in allc}
  lb = {"labels": lab, "labels_sha256": tp.sha_obj(lab)}
  json.dump(dr, open(tmp_path / "d.json", "w")); json.dump(lb, open(tmp_path / "l.json", "w"))
  return tmp_path


BASE = ["--model", "qwen25_7b", "--arm", "claude_examples", "--lr", "3e-4"]


def run_args(argv, monkeypatch, tmp_path):
  """Run main() up to the model load; return the adapter folder it would create (its name is the run id)."""
  monkeypatch.setattr(TL, "ADAPTERS", str(tmp_path / "adapters"))
  class Stop(Exception): pass
  def stub(*a, **k): raise Stop()
  monkeypatch.setattr(TL, "Backend", stub)
  with pytest.raises(Stop):
    TL.main(argv)
  return sorted(os.listdir(tmp_path / "adapters"))


GEN = os.path.join(ROOT, "demo", "gen")
DRAWS, LABELS = os.path.join(GEN, "targeted_draws_qwen25_7b.json"), os.path.join(GEN, "targeted_labels_qwen25_7b.json")


def test_targeted_run_ids_differ_by_arm(monkeypatch, tmp_path):
  """with the committed, pinned draws and labels"""
  common = ["--n-cells", "150", "--max-steps", "750", "--select", "select3", "--extra-draws", DRAWS,
            "--extra-labels", LABELS, "--plain-select-record", "x.json", "--seed", "0"]
  ids = []
  for arm in ("T", "R", "N"):
    ids += run_args(BASE + common + ["--extra-key", f"{arm}_s0"], monkeypatch, tmp_path / arm)
  assert ids == ["qwen25_7b_claude_examples_n150_T_lr3e-04_s0", "qwen25_7b_claude_examples_n150_R_lr3e-04_s0", "qwen25_7b_claude_examples_n150_N_lr3e-04_s0"]


def test_old_recipe_run_id_unchanged(monkeypatch, tmp_path):
  ids = run_args(BASE + ["--plain-train-record", "x.json", "--seed", "1"], monkeypatch, tmp_path)
  assert ids == ["qwen25_7b_claude_examples_n100_lr3e-04_s1"]


@pytest.mark.parametrize("bad, msg", [
    (["--n-cells", "150", "--max-steps", "500", "--select", "select3", "--extra-key", "T_s0", "--seed", "0"], "max-steps 750"),
    (["--n-cells", "150", "--max-steps", "750", "--select", "select3", "--extra-key", "T_s1", "--seed", "0"], "another seed"),
    (["--n-cells", "150", "--max-steps", "750", "--select", "select_B", "--extra-key", "T_s0", "--seed", "0"], "select3"),
])
def test_argument_rules(files, monkeypatch, tmp_path, bad, msg, capsys):
  argv = BASE + ["--extra-draws", str(files / "d.json"), "--extra-labels", str(files / "l.json"), "--plain-select-record", "x.json"] + bad
  with pytest.raises(SystemExit):
    TL.main(argv)
  assert msg in capsys.readouterr().err


def test_select3_without_extras_and_150_without_extras_are_refused(capsys):
  with pytest.raises(SystemExit):
    TL.main(BASE + ["--n-cells", "150", "--plain-train-record", "x.json"])
  assert "only for the targeted arms" in capsys.readouterr().err


def test_add_extra_cells_assembles_150(files):
  task = Haggling3Task()
  a = types.SimpleNamespace(extra_draws=str(files / "d.json"), extra_labels=str(files / "l.json"), extra_key="N_s2", select="select3")
  tspec = json.load(open(TL.TRAIN_CELLS))
  train = [None] * 100; by_id, labels, claude, orders_of = {}, {}, {}, {}
  info = TL.add_extra_cells(a, task, tspec, train, by_id, labels, claude, orders_of)
  ext = train[100:]
  assert len(train) == 150 and {c["split"] for c in ext} == {"pool"} and all(c["type"] == "no_cost" for c in ext)
  assert all(len(orders_of[c["cell"]]) == 3 for c in ext) and info["extra_key"] == "N_s2"
  sel3 = {c["cell"] for c in task.cases("select3")}
  assert not {c["cell"] for c in ext} & sel3


def test_edited_draws_file_is_refused(files):
  d = json.load(open(files / "d.json")); d["draws"]["T_s0"][0] = d["draws"]["R_s0"][0]
  json.dump(d, open(files / "d.json", "w"))
  a = types.SimpleNamespace(extra_draws=str(files / "d.json"), extra_labels=str(files / "l.json"), extra_key="T_s0", select="select3")
  with pytest.raises(AssertionError, match="edited"):
    TL.add_extra_cells(a, Haggling3Task(), json.load(open(TL.TRAIN_CELLS)), [None] * 100, {}, {}, {}, {})


def test_committed_files_pass_the_pins_and_an_edited_copy_fails(tmp_path):
  task = Haggling3Task(); tspec = json.load(open(TL.TRAIN_CELLS))
  a = types.SimpleNamespace(extra_draws=DRAWS, extra_labels=LABELS, extra_key="T_s1", select="select3")
  info = TL.add_extra_cells(a, task, tspec, [None] * 100, {}, {}, {}, {}, pins=TL.PINNED_TARGETED["qwen25_7b"])
  assert len(info["extra_cells"]) == 50
  d = json.load(open(DRAWS)); k = sorted(d["orders"])[0]; d["orders"][k] = [0, 1, 2] if d["orders"][k] != [0, 1, 2] else [1, 2, 3]
  d["orders_sha256"] = TL._sha_obj(d["orders"]); json.dump(d, open(tmp_path / "d.json", "w"))
  a.extra_draws = str(tmp_path / "d.json")
  with pytest.raises(AssertionError, match="pinned"):
    TL.add_extra_cells(a, task, tspec, [None] * 100, {}, {}, {}, {}, pins=TL.PINNED_TARGETED["qwen25_7b"])


def test_orders_function_matches_the_prepare_script():
  for c in ("a", "V10-gF-neutral-p1_5-w3", "zz"):
    assert TL.targeted_orders(c) == tp.orders_for(c)
