"""test3 and the build pool (demo/gen_test3.py): sizes, disjointness by problem from every earlier set and from each other, no ties,
new names, determinism, fingerprints. CPU only; nothing is scored."""
import hashlib, json, os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "demo"))
import common  # noqa: E402,F401
import gen_cases as g  # noqa: E402
import gen_test2 as t2  # noqa: E402
import gen_test3 as t3  # noqa: E402

OUT = g.OUT
T3 = json.load(open(os.path.join(OUT, "test3_cells.json")))["cells"]
POOL = json.load(open(os.path.join(OUT, "pool3_cells.json")))["cells"]
CASES = [json.loads(l) for l in open(os.path.join(OUT, "test3_cases.jsonl"))]
PCASES = [json.loads(l) for l in open(os.path.join(OUT, "pool3_cases.jsonl"))]
EARLIER = json.load(open(os.path.join(OUT, "cells.json")))["cells"] + json.load(open(os.path.join(OUT, "test2_cells.json")))["cells"]
P = lambda c: (c["V"], c["grid_name"], c["C"]) if c["C"] is not None else (c["V"], c["grid_name"], tuple(c["prior"]))


def test_sizes():
  assert {t: sum(c["type"] == t for c in T3) for t in g.TYPES} == t3.TEST3
  assert len(CASES) == 240 and {c["name_variant"] for c in CASES} == {0, 1}
  assert len(PCASES) == len(POOL) and {c["name_variant"] for c in PCASES} == {0}
  assert {t: sum(c["type"] == t and c["probe"] for c in POOL) for t in g.TYPES} == t3.PROBE


def test_problems_disjoint_and_unique():
  early = {P(c) for c in EARLIER}
  tp, pp = [P(c) for c in T3], [P(c) for c in POOL]
  assert len(set(tp)) == len(tp) and len(set(pp)) == len(pp)
  assert not set(tp) & early and not set(pp) & early and not set(tp) & set(pp)
  assert not {c["cell"] for c in T3 + POOL} & {c["cell"] for c in EARLIER}


def test_no_ties_and_labels_match_payoff_rule():
  t2.install()
  for c in T3 + POOL:
    lab = g.label(c["V"], g.GRIDS[c["grid_name"]], c["C"], tuple(c["prior"]))
    assert not lab["all_tie"] and lab["best_positions"] == c["best_positions"]


def test_names_are_new_and_split_between_test3_and_pool():
  old = t3.used_names()
  for c in CASES + PCASES:
    assert not set(c["buyer"].split()) & old and not set(c["seller"].split()) & old
  tn = {c["buyer"] for c in CASES} | {c["seller"] for c in CASES}
  pn = {c["buyer"] for c in PCASES} | {c["seller"] for c in PCASES}
  assert not tn & pn


def test_rebuild_is_deterministic_and_fingerprints_match():
  cells, cases, _ = t3.build()
  fp = json.load(open(os.path.join(OUT, "test3_fingerprints.json")))
  assert t3.fingerprints(cells, cases)["sets"] == fp["sets"]
  for n in ("test3_cells.json", "test3_cases.jsonl", "pool3_cells.json", "pool3_cases.jsonl"):
    assert hashlib.sha256(open(os.path.join(OUT, n), "rb").read()).hexdigest() == fp["files"][f"demo/gen/{n}"]


def test_prompts_render():
  t2.install()
  for c in CASES[:20] + PCASES[:20]:
    text, l2p = g.render(c, g.orders()[0])
    assert c["buyer"] in text and text.endswith("Answer: (") and sorted(l2p.values()) == sorted(c["grid"])
