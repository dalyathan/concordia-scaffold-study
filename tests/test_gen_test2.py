"""test2 sets (demo/gen_test2.py): disjointness, no ties, quotas, unseen pairs, names, determinism, fingerprints, CPU-only."""
import json, os, subprocess, sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "demo"))
import common  # noqa: E402
import gen_cases as g  # noqa: E402
import gen_test2 as t2  # noqa: E402
from refimpl import core  # noqa: E402

t2.install()
CELLS = json.load(open(os.path.join(g.OUT, "test2_cells.json")))["cells"]
CASES = [json.loads(l) for l in open(os.path.join(g.OUT, "test2_cases.jsonl"))]
FIRST = json.load(open(os.path.join(g.OUT, "cells.json")))["cells"]
FIRST_CASES = [json.loads(l) for l in open(os.path.join(g.OUT, "cases.jsonl"))]
S = {n: [c for c in CELLS if c["split"] == n] for n in ("test2_same", "test2_newkey")}


def test_sizes_types_and_variants():
  for n, cs in S.items():
    assert len(cs) == 120 and all(sum(c["type"] == t for c in cs) == 40 for t in g.TYPES)
    cases = [c for c in CASES if c["split"] == n]
    assert len(cases) == 240 and {c["name_variant"] for c in cases} == {0, 1}
    assert all(sum(1 for c in cases if c["cell"] == k["cell"]) == 2 for k in cs)


def test_disjoint_by_cell_and_no_ties():
  first = {c["cell"] for c in FIRST}
  a, b = ({c["cell"] for c in S[n]} for n in S)
  assert not (a & first) and not (b & first) and not (a & b) and len(a) == len(S["test2_same"]) == 120
  assert all(not c["all_tie"] for c in CELLS)
  assert all(c["grid"][0] == min(c["grid"]) for c in CELLS)


def test_original_study_space_and_old_test_cells_excluded():
  assert not any(t2.original_study_cell(c["V"], c["grid_name"], c["prior"]) for c in CELLS)
  assert not any(g.old_test_cell(c["V"], c["grid_name"], c["line"], c["C"], c["prior"]) for c in CELLS)


def test_same_set_stays_in_training_ranges():
  for c in S["test2_same"]:
    assert c["V"] in g.SEEN_V and c["grid_name"] in g.SEEN_GRIDS and c["wording"] in g.SEEN_W and c["region"] == "training ranges"


def test_newkey_pairs_never_in_train_and_extension_is_reserved():
  train_pairs = {t2.pair_key(c["V"], c["C"], c["prior"]) for c in FIRST if c["split"] == "train"}
  assert all(t2.pair_key(c["V"], c["C"], c["prior"]) not in train_pairs for c in S["test2_newkey"])
  assert all(c["V"] <= 15 for c in S["test2_newkey"])
  used_new = lambda c: c["grid_name"] == "F" or c["wording"] == 3 or c["V"] >= 10
  assert not any(c["grid_name"] == "F" or c["wording"] == 3 for c in FIRST) and not any(used_new(c) for c in S["test2_same"])


def test_names_disjoint_from_first_dataset_old_variants_and_between_sets():
  old = set(core.FEMALE_NAMES) | set(core.MALE_NAMES)
  first = {c["buyer"] for c in FIRST_CASES} | {c["seller"] for c in FIRST_CASES}
  names = {n: {c["buyer"] for c in CASES if c["split"] == n} | {c["seller"] for c in CASES if c["split"] == n} for n in S}
  assert not names["test2_same"] & first and not names["test2_newkey"] & first and not names["test2_same"] & names["test2_newkey"]
  assert not (names["test2_same"] | names["test2_newkey"]) & old


def test_rebuild_is_deterministic_and_fingerprints_match():
  cells, cases, stats, ctx = t2.build()
  assert json.dumps(cells, sort_keys=True) == json.dumps(CELLS, sort_keys=True) and cases == CASES
  fp = json.load(open(os.path.join(g.OUT, "test2_fingerprints.json")))
  assert t2.fingerprints(cells, cases)["sets"] == fp["sets"]


def test_new_wording_renders_and_is_not_in_first_dataset_text():
  c = next(c for c in CASES if c["wording"] == 3 and c["line"] == "information")
  text, l2p = g.render(c, g.orders()[0])
  assert "For your information, the farm asked me" in text and f"{c['C']} coin" in text and set(l2p.values()) == set(c["grid"])


def test_cpu_only_no_cuda_no_model():
  r = subprocess.run([sys.executable, "-c", "import sys; sys.path[:0]=['demo','concordia','.']; import gen_test2; gen_test2.build(); import torch; assert not torch.cuda.is_initialized(), 'CUDA initialised'"],
                     cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))), capture_output=True, text=True)
  assert r.returncode == 0, r.stderr[-400:]
