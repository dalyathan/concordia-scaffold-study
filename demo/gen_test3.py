"""test3 (a new locked test set weighted to deals with no stated cost) and the build pool for the targeted experiment (TARGETED_PLAN.md).

CPU only; scores nothing. Built from demo/gen_cases.py and demo/gen_test2.py (imported, unchanged; gen_test2.install() adds grid F and
wording 3) with a NEW fixed seed. Every cell poses a decision problem ((V, grid, stated cost) or (V, grid, cost range)) that occurs in
no earlier cell (the 400 cells of cells.json: train, tune, test_same, test_hard; and the 240 test2 cells), and test3 and the pool share no
problem. All-tie cells are dropped. Resale values 2-15, grids A-F, wordings 0-3, the five cost ranges.

  test3   120 cells: 60 no_cost, 30 below, 30 at_or_above; one cell per problem; V-balanced draw; two name variants (240 cases); LOCKED:
          written once with fingerprints, loaded by the harness only after a fingerprint check and only in a locked look.
  pool    every remaining non-tie problem, one cell each (seeded choice of line, wording and cell); name variant 0 only. Build data:
          the probe set (failure map) and the extra training cells of arms T and R are drawn from it (TARGETED_PLAN.md).
  probe   90 pool cells (45 no_cost, 30 below, 15 at_or_above), V-balanced, for the failure map of the examples-100 adapters.

Names: new first-name and surname lists, disjoint from every name used so far (gen_cases pools, refimpl.core names), so no prompt in test3
or the pool repeats a buyer or seller name."""
from __future__ import annotations

import collections
import hashlib
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: F401,E402
import gen_cases as g  # noqa: E402
import gen_test2 as t2  # noqa: E402
from refimpl import core  # noqa: E402

SEED3 = 20261203
OUT = g.OUT
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VS = tuple(range(2, 16))
GRIDS = ("A", "B", "C", "D", "E", "F")
WORDINGS = (0, 1, 2, 3)
TEST3 = {"no_cost": 60, "below": 30, "at_or_above": 30}
PROBE = {"no_cost": 45, "below": 30, "at_or_above": 15}
BUYER_FIRST = ["Aster", "Bryony", "Clover", "Dahlia", "Elowen", "Fern", "Gilia", "Heather", "Iris", "Jessamine", "Kalmia", "Lobelia",
               "Myrtle", "Nerine", "Oxalis", "Primrose", "Rosalind", "Saffron", "Tansy", "Ulmaria", "Violet", "Winnow", "Yarrow", "Zinnia"]
SELLER_FIRST = ["Ambrose", "Barnaby", "Crispin", "Desmond", "Edgar", "Fabian", "Godfrey", "Horace", "Ignatius", "Jethro", "Leopold",
                "Mortimer", "Nathaniel", "Octavian", "Percival", "Quentin", "Rupert", "Sebastian", "Thaddeus", "Valentin", "Wilfred",
                "Xavier", "Yves", "Zebedee"]
SURNAMES = ["Almondbury", "Bilberry", "Crabapple", "Dewberry", "Elmstead", "Fenugreek", "Greengage", "Hawthorn", "Islemere", "Jujube",
            "Kiwifield", "Loganberry", "Marrowfield", "Nutmeg", "Orchardley", "Pearwood", "Quinceford", "Rhubarb", "Sorbus", "Tamarind",
            "Uplands", "Verjuice", "Whortle", "Yuzu"]


def used_names():
  names = set(g._BUYER_FIRST) | set(g._SELLER_FIRST) | set(g._SURNAMES)
  names |= {part for n in core.FEMALE_NAMES + core.MALE_NAMES for part in n.split()}
  return names


def name_pools(rng):
  assert not (set(BUYER_FIRST) | set(SELLER_FIRST) | set(SURNAMES)) & used_names(), "a new name repeats an old one"
  buyers = [f"{a} {s}" for a in BUYER_FIRST for s in SURNAMES]
  sellers = [f"{a} {s}" for a in SELLER_FIRST for s in SURNAMES]
  rng.shuffle(buyers); rng.shuffle(sellers)
  h = len(buyers) // 2
  return {"test3": (buyers[:h], sellers[:h]), "pool": (buyers[h:], sellers[h:])}


def build():
  t2.install()
  first = json.load(open(os.path.join(OUT, "cells.json")))["cells"]
  second = json.load(open(os.path.join(OUT, "test2_cells.json")))["cells"]
  key = lambda c: (c["V"], c["grid_name"], c["line"], c["C"], tuple(c["prior"]), c["wording"])
  used_problems = {t2.problem(key(c)) for c in first + second}
  used_cells = {c["cell"] for c in first + second}
  rng = random.Random(SEED3)
  stats = {"ties_dropped": collections.Counter()}
  by_problem = {t: collections.defaultdict(list) for t in g.TYPES}
  for typ in g.TYPES:
    for x in t2.candidates(typ, VS, GRIDS, WORDINGS):
      V, gn, line, C, prior, w = x
      if g.cell_key(*x) in used_cells or t2.problem(x) in used_problems:
        continue
      if g.label(V, g.GRIDS[gn], C, prior)["all_tie"]:
        stats["ties_dropped"][typ] += 1; continue
      by_problem[typ][t2.problem(x)].append(x)
  cells = []

  def add(split, typ, x):
    V, gn, line, C, prior, w = x
    lab = g.label(V, g.GRIDS[gn], C, prior)
    srt = sorted(lab["payoffs"], reverse=True)
    cells.append({"cell": g.cell_key(V, gn, line, C, prior, w), "split": split, "slice": split, "type": typ, "V": V, "grid_name": gn,
                  "grid": list(g.GRIDS[gn]), "line": line, "C": C, "prior": list(prior), "wording": w, **lab,
                  "problem": list(t2.problem(x)), "best_is_cheapest": 0 in lab["best_positions"], "margin_best_second": round(srt[0] - srt[1], 6)})

  def v_balanced(problems, n):
    """n problems, V uniform among values that still have problems, then a problem of that V uniform (sorted for determinism)"""
    byv = collections.defaultdict(list)
    for p in sorted(problems):
      byv[p[0]].append(p)
    out = []
    while len(out) < n and byv:
      V = rng.choice(sorted(byv))
      out.append(byv[V].pop(rng.randrange(len(byv[V]))))
      if not byv[V]:
        del byv[V]
    assert len(out) == n, (n, len(out))
    return out

  stats["available_problems"] = {t: len(by_problem[t]) for t in g.TYPES}
  for typ in g.TYPES:
    chosen = v_balanced(by_problem[typ], TEST3[typ])
    for p in chosen:
      add("test3", typ, rng.choice(sorted(by_problem[typ][p])))
      del by_problem[typ][p]
  for typ in g.TYPES:                        # the pool: every remaining problem, one cell each
    for p in sorted(by_problem[typ]):
      add("pool", typ, rng.choice(sorted(by_problem[typ][p])))
  pool = [c for c in cells if c["split"] == "pool"]
  probe = []
  for typ in g.TYPES:
    cand = [tuple(c["problem"]) for c in pool if c["type"] == typ]
    pick = set(map(tuple, v_balanced(cand, PROBE[typ])))
    probe += [c["cell"] for c in pool if c["type"] == typ and tuple(c["problem"]) in pick]
  for c in cells:
    c["probe"] = c["cell"] in set(probe)
  pools = name_pools(random.Random(SEED3 + 1))
  cases = []
  for c in cells:
    pb, ps = pools[c["split"]]
    h = int(hashlib.sha256((str(SEED3) + c["cell"]).encode()).hexdigest(), 16)
    for v in ((0, 1) if c["split"] == "test3" else (0,)):
      cases.append({"cid": f"{c['cell']}-n{v}", "cell": c["cell"], "name_variant": v, "buyer": pb[(h + 7 * v) % len(pb)],
                    "seller": ps[(h // 3 + 11 * v) % len(ps)], "opening": h % 5,
                    **{k: c[k] for k in ("split", "slice", "type", "V", "grid_name", "grid", "line", "C", "prior", "wording")}})
  stats["ties_dropped"] = dict(stats["ties_dropped"])
  stats["counts"] = {s: dict(collections.Counter(c["type"] for c in cells if c["split"] == s)) for s in ("test3", "pool")}
  stats["probe"] = dict(collections.Counter(c["type"] for c in cells if c["probe"]))
  return cells, cases, stats


def fingerprints(cells, cases):
  sha = lambda b: hashlib.sha256(b).hexdigest()
  f = lambda p: sha(open(os.path.join(ROOT, p), "rb").read())
  fp = {"seed": SEED3, "files": {p: f(p) for p in ("demo/gen_test3.py", "demo/gen_test2.py", "demo/gen_cases.py", "refimpl/core.py",
                                                    "demo/gen/cells.json", "demo/gen/test2_cells.json")}, "sets": {}}
  for s in ("test3", "pool"):
    cs = sorted((c for c in cells if c["split"] == s), key=lambda c: c["cell"])
    ks = sorted((c for c in cases if c["split"] == s), key=lambda c: c["cid"])
    fp["sets"][s] = {"n_cells": len(cs), "n_cases": len(ks), "cells_sha256": sha(json.dumps(cs, sort_keys=True).encode()),
                     "cases_sha256": sha(json.dumps(ks, sort_keys=True).encode())}
  return fp


def main():
  cells, cases, stats = build()
  for name, obj in (("test3_cells.json", {"seed": SEED3, "stats": stats, "cells": [c for c in cells if c["split"] == "test3"]}),
                    ("pool3_cells.json", {"seed": SEED3, "stats": stats, "cells": [c for c in cells if c["split"] == "pool"]})):
    json.dump(obj, open(os.path.join(OUT, name), "w"), indent=1, sort_keys=True)
  with open(os.path.join(OUT, "test3_cases.jsonl"), "w") as fh:
    for c in cases:
      if c["split"] == "test3":
        fh.write(json.dumps(c, sort_keys=True) + "\n")
  with open(os.path.join(OUT, "pool3_cases.jsonl"), "w") as fh:
    for c in cases:
      if c["split"] == "pool":
        fh.write(json.dumps(c, sort_keys=True) + "\n")
  fp = fingerprints(cells, cases)
  fp["files"].update({f"demo/gen/{n}": hashlib.sha256(open(os.path.join(OUT, n), "rb").read()).hexdigest()
                      for n in ("test3_cells.json", "test3_cases.jsonl", "pool3_cells.json", "pool3_cases.jsonl")})
  json.dump(fp, open(os.path.join(OUT, "test3_fingerprints.json"), "w"), indent=1, sort_keys=True)
  print(json.dumps(stats, indent=1))


if __name__ == "__main__":
  main()
