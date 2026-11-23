"""Nested, type-stratified training subsets of the 100 LoRA training cells for the learning-curve experiment (CPU only).

  python demo/gen_curve.py        writes demo/gen/curve_subsets.json (sizes 10 < 25 < 50 < 100; each is a prefix of a fixed per-type permutation)

Per-type counts (below / at_or_above / no_cost; the 100 cells are 34 / 33 / 33): N=10: 4/3/3, N=25: 9/8/8, N=50: 17/17/16, N=100: 34/33/33.
Each cell keeps its fixed name variant and three option orders from demo/gen/lora_train_cells.json. Seed 20261202 (numpy PCG64)."""
import hashlib, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import gen_cases as g

SIZES = (10, 25, 50, 100)
COUNTS = {10: (4, 3, 3), 25: (9, 8, 8), 50: (17, 17, 16), 100: (34, 33, 33)}
SEED = 20261202
PATH = os.path.join(g.OUT, "curve_subsets.json")


def build():
  spec = json.load(open(os.path.join(g.OUT, "lora_train_cells.json")))
  cells = {c["cell"]: c for c in json.load(open(os.path.join(g.OUT, "cells.json")))["cells"]}
  rng = np.random.Generator(np.random.PCG64(SEED))
  order = {}
  for t in g.TYPES:
    ids = sorted(k for k in spec if cells[k]["type"] == t)
    order[t] = [ids[i] for i in rng.permutation(len(ids))]
  assert [len(order[t]) for t in g.TYPES] == [34, 33, 33]
  subsets = {str(n): sorted(c for t, k in zip(g.TYPES, COUNTS[n]) for c in order[t][:k]) for n in SIZES}
  for a, b in zip(SIZES, SIZES[1:]):
    assert set(subsets[str(a)]) < set(subsets[str(b)]), "subsets must be nested"
  assert all(len(subsets[str(n)]) == n for n in SIZES) and set(subsets["100"]) == set(spec)
  return {"seed": SEED, "counts": {str(n): COUNTS[n] for n in SIZES}, "subsets": subsets}


def load(n):
  d = json.load(open(PATH))
  assert hashlib.sha256(json.dumps(build(), sort_keys=True).encode()).hexdigest() == hashlib.sha256(json.dumps(d, sort_keys=True).encode()).hexdigest(), "curve_subsets.json differs from its rebuild"
  return d["subsets"][str(n)]


if __name__ == "__main__":
  d = build()
  json.dump(d, open(PATH, "w"), indent=1)
  print({n: len(v) for n, v in d["subsets"].items()}, hashlib.sha256(open(PATH, "rb").read()).hexdigest())
