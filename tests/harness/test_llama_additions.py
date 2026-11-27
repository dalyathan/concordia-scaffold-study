"""CPU tests for the pieces added on branch llama: notes placement, rule baselines, selection split."""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "demo"))
from harness.tasks.haggling import HagglingTask
from harness.solvers.cpu import BaselineSolver
from harness.evaluate import evaluate

T = HagglingTask()


def test_notes_placement_equals_gemma_render_notes():
  import gen_notes
  for c in T.cases("tune")[:6]:
    for order in T.orders(c):
      text, _ = T.render(c, order)
      ref, _ = gen_notes.render_notes(c, order, "NOTE TEXT")
      assert T.insert_notes(text, "NOTE TEXT") == ref


def test_select_b_is_42_train_cells_outside_the_training_cells():
  import json
  cs = T.cases("select_B")
  assert len(cs) == 42 and all(c["split"] == "train" and c["name_variant"] == 0 for c in cs)
  train_cells = set(json.load(open(os.path.join(ROOT, "demo", "gen", "lora_train_cells.json"))))
  assert not {c["cell"] for c in cs} & train_cells
  assert {c["type"] for c in cs} == {"below", "at_or_above", "no_cost"}


def test_stated_cost_rule_matches_the_gemma_report_value():
  # demo/gen_curve_report.py: stated-cost rule 0.214 on the 42 tune cells; always-cheapest 0.429
  r = evaluate(T, BaselineSolver(policy="stated_cost_rule"), "tune", write=False, planted=False)
  assert round(r["summary"]["soft_regret_mean"], 3) == 0.214
  r = evaluate(T, BaselineSolver(policy="cheapest"), "tune", write=False, planted=False)
  assert round(r["summary"]["soft_regret_mean"], 3) == 0.429
