import ast, os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _textrows():
  vals = {}
  for n in ast.parse(open(os.path.join(ROOT, "demo", "textrows.py")).read()).body:
    if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") in ("METHOD", "FIXED"):
      vals[n.targets[0].id] = ast.literal_eval(n.value)
  return vals


def test_lessons_equal_their_sources():
  v = _textrows()
  src = {"method_original": v["METHOD"], "wrong_rule": v["FIXED"]["wrong_rule"],
         "teacher": open(os.path.join(ROOT, "demo", "gen", "teacher_method.txt")).read().strip(),
         "neutral": open(os.path.join(ROOT, "demo", "gen", "neutral_text.txt")).read().strip()}
  for k, s in src.items():
    assert open(os.path.join(ROOT, "harness", "lessons", k + ".txt")).read() == s, k
