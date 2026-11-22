"""Prompt with a Notes block for generated cases (same insertion as phase3.decision_user_turn: 'Notes:' before the question)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_cases as g


def render_notes(case, order, notes):
  text, l2p = g.render(case, order)
  if notes is None:
    return text, l2p
  head, tail = text.split("Question:", 1)
  return head + "Notes:\n" + notes + "\n\n" + "Question:" + tail, l2p
