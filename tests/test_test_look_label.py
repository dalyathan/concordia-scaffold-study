import importlib.util, os
spec = importlib.util.spec_from_file_location("tl", os.path.join(os.path.dirname(__file__), "..", "demo", "test_look.py"))
tl = importlib.util.module_from_spec(spec); spec.loader.exec_module(tl)
d = lambda a, b, c: [a, b, c, 3]
BASE = {"plain": d(.3, .1, .5), "neutral": d(.3, .1, .5), "wrong_rule": d(.12, .01, .3), "always2": d(.02, -.1, .1)}
L = lambda diff, harm=None: tl.label({"diff": diff, "harm_C_ge_V": harm})


def test_labels():
  assert L(BASE) == "SUPPORT (beats always-2 with lower bound > 0: no)"
  assert L(dict(BASE, always2=d(.1, .02, .2))).endswith("yes)")
  p = L(dict(BASE, wrong_rule=d(.2, -.01, .4)))
  assert p.startswith("PARTIAL") and "wrong_rule" in p
  p = L(dict(BASE, wrong_rule=d(.05, .01, .4)))                       # lower bound > 0 but D < 0.10
  assert p.startswith("PARTIAL") and "wrong_rule" in p
  p = L(dict(BASE, always2=d(-.05, -.2, .1)))                         # worse than always-2 in mean
  assert p.startswith("PARTIAL") and "always2" in p
  assert L(dict(BASE, neutral=d(.1, -.05, .3))).startswith("PLAIN-ONLY")
  assert L(dict(BASE, plain=d(.1, -.1, .3))).startswith("NOT SHOWN")
  assert "HARM flag" in L(BASE, d(-.1, -.2, -.05))
  assert "HARM flag" not in L(BASE, d(-.1, -.2, .05))
