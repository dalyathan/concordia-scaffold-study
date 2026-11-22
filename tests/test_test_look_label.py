import importlib.util, os
spec = importlib.util.spec_from_file_location("tl", os.path.join(os.path.dirname(__file__), "..", "demo", "test_look.py"))
tl = importlib.util.module_from_spec(spec); spec.loader.exec_module(tl)
d = lambda a, b, c: [a, b, c, 3]
BASE = {"plain": d(.3, .1, .5), "neutral": d(.3, .1, .5), "wrong_rule": d(.12, .01, .3), "always2": d(.02, -.1, .1)}


def test_labels():
  assert tl.label({"diff": BASE, "harm_C_ge_V": None}) == "SUPPORT"
  assert tl.label({"diff": dict(BASE, wrong_rule=d(.2, -.01, .4)), "harm_C_ge_V": None}).startswith("PARTIAL")
  assert tl.label({"diff": dict(BASE, plain=d(.1, -.1, .3)), "harm_C_ge_V": None}).startswith("NOT SHOWN")
  assert tl.label({"diff": dict(BASE, always2=d(-.05, -.2, .1)), "harm_C_ge_V": None}) != "SUPPORT"
  assert "HARM flag" in tl.label({"diff": BASE, "harm_C_ge_V": d(-.1, -.2, -.05)})
