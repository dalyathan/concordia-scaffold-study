"""Generated dataset (CPU only): the same haggling game and prompt template, five price options always, with
varied resale value (2-12), stated cost, shifted price grids, a stated farm-cost prior, three fresh wordings per
seller line and new invented names. Labels from the payoff rule of refimpl.core generalised to any grid and prior
(the generalisation is unit-tested to equal core.payoff / core.oracle_bids on the original game).

  python demo/gen_cases.py        writes demo/gen/{cells.json, cases.jsonl, fingerprints.json}

Never uses name variants 1-14 (the old name lists are read only to prove the new names are disjoint from them) and
never uses the old test cells (V, line, C at grid 1-5 / prior 1-5 for the cells core.steering_cell_split calls 'test').
Splits are by WHOLE cells with a fixed seed; the split rule is below and logged in DEMO_STATUS.md."""
from __future__ import annotations

import hashlib
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: F401  (sets sys.path)
from refimpl import core, phase3

SEED = 20261122
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gen")
GRIDS = {"A": (1, 2, 3, 4, 5), "B": (2, 3, 4, 5, 6), "C": (3, 4, 5, 6, 7), "D": (2, 4, 6, 8, 10), "E": (4, 5, 6, 7, 8)}
PRIORS = ((1, 5), (2, 6), (3, 7), (1, 10), (2, 10))
SEEN_V, HARD_V = tuple(range(2, 10)), (10, 11, 12)
SEEN_GRIDS, HARD_GRIDS = ("A", "B", "C"), ("D", "E")
SEEN_W, HARD_W = (0, 1), (2,)
LINES = ("neutral", "pressure", "information")
TYPES = ("below", "at_or_above", "no_cost")
SELLER_LINES = {   # three fresh wordings per line (none is the original text); {C} only for 'information'
    "neutral": ("Go ahead, tell me what price you are thinking of for this fruit.",
                "No rush. What would you like to offer for the fruit?",
                "Whenever you are ready, say what you would pay for it."),
    "pressure": ("There are other buyers waiting. Give me a real offer right now or step aside.",
                 "I'm busy, so make your best offer immediately or I'll move on to the next customer.",
                 "Time is money here. Put a serious price on the table now, or I'll sell elsewhere."),
    "information": ("I'll be straight with you: I paid {C} for this fruit at the farm, so keep that in mind when you name a price.",
                    "Between us, the farm charged me {C} for it. Let that guide your offer.",
                    "Full disclosure, my cost at the farm was {C}. Name your price with that in mind."),
}
_BUYER_FIRST = ["Alma", "Briar", "Calla", "Dessa", "Edda", "Fenna", "Gwyn", "Hollis", "Isla", "Joss", "Kestra", "Linnea", "Marnie",
                "Neve", "Odile", "Perrin", "Quilla", "Rhea", "Sorrel", "Tamsin", "Una", "Verity", "Wren", "Xanthe", "Yara", "Zelda"]
_SELLER_FIRST = ["Alder", "Bram", "Corin", "Davin", "Emrys", "Fergus", "Galen", "Hollin", "Ilar", "Jory", "Kellan", "Lorcan", "Merrick",
                 "Niall", "Osric", "Penn", "Quill", "Rowan", "Silas", "Tavish", "Ulric", "Varrin", "Wystan", "Yorick", "Zane", "Dunstan"]
_SURNAMES = ["Applecroft", "Barleyfield", "Cherrydale", "Damsonhill", "Elderglen", "Fennelmoor", "Gooseberry", "Hazelmere",
             "Juniperfold", "Kumquatridge", "Limeharbor", "Medlarwick", "Nectarvale", "Olivebrook", "Papayafold", "Quinceton",
             "Raspberrow", "Sloefield", "Tangelo", "Ugliwood", "Vineyard", "Walnutlea", "Yewbank", "Zestmoor"]


# ------------------------------------------------------------------ payoff
def payoff(V: int, grid, C, prior, k: int) -> float:
  """Expected payoff of offer k. Stated cost C: V - k if k >= C else 0. No cost: the farm cost is uniform on the
  integers prior[0]..prior[1], so P(accept) = clamp((k - lo + 1) / (hi - lo + 1), 0, 1)."""
  if C is not None:
    return float(V - k) if k >= C else 0.0
  lo, hi = prior
  return (V - k) * min(1.0, max(0.0, (k - lo + 1) / (hi - lo + 1)))


def label(V, grid, C, prior) -> dict:
  pay = [payoff(V, grid, C, prior, k) for k in grid]
  best = max(pay)
  idx = [i for i, x in enumerate(pay) if abs(x - best) < 1e-12]
  return {"payoffs": pay, "best_payoff": best, "best_offers": [grid[i] for i in idx], "best_positions": idx,
          "all_tie": len(idx) == len(grid), "unique_best": len(idx) == 1}


def cell_type(line, V, C):
  return "no_cost" if line != "information" else ("below" if C < V else "at_or_above")


# ------------------------------------------------------------------ names
def names_pool():
  old = set(core.FEMALE_NAMES) | set(core.MALE_NAMES)
  rng = random.Random(SEED)
  buyers = [f"{a} {s}" for a in _BUYER_FIRST for s in _SURNAMES]
  sellers = [f"{a} {s}" for a in _SELLER_FIRST for s in _SURNAMES]
  rng.shuffle(buyers); rng.shuffle(sellers)
  assert not (set(buyers) | set(sellers)) & old
  # disjoint name pools per split family (a name never crosses a split boundary)
  return {"train": (buyers[:300], sellers[:300]), "tune": (buyers[300:360], sellers[300:360]),
          "test": (buyers[360:480], sellers[360:480])}


# ------------------------------------------------------------------ prompt text
def render(case: dict, order) -> tuple[str, dict]:
  """Decision prompt for `case` with the five options shown in `order` (positions into the grid).
  Same template as refimpl.phase3.decision_user_turn; the farm-cost memory and the price-scale memory state the
  case's prior and grid. Returns (text, letter -> price)."""
  from examples.modular.environment.modules import fruitville_haggling as fv
  grid, (lo, hi), buyer, seller, V = case["grid"], case["prior"], case["buyer"], case["seller"], case["V"]
  step = grid[1] - grid[0]
  mid = grid[2]
  coin = lambda n: f"{n} coin" + ("" if n == 1 else "s")
  m2 = (f"The price of one kilogram of fruit is, on average, {mid} coins. {coin(grid[0])} is really cheap and {coin(grid[-1])} is "
        f"really expensive. The smallest value of transaction is {coin(step)}, all prices have to be in multiples of {coin(step)}. "
        "No fractional values are allowed.")
  rules = (f"Sellers at this market pay between {lo} and {hi} coins per kilogram at the farm, and each amount is equally likely.",
           core.RULE_MEMORIES[1], core.RULE_MEMORIES[2])
  last = SELLER_LINES[case["line"]][case["wording"]].format(C=("" if case["C"] is None else coin(case["C"])))
  opening = fv.VISUAL_SCENE_OPENINGS[case["opening"]]
  turns = [(buyer, core.SCRIPT[0]), (seller, core.SCRIPT[1]), (buyer, core.SCRIPT[2]), (seller, last)]
  lines = [phase3.instructions_text(buyer), "", "Memories:", phase3.SHARED_MEMORY_1, m2, *rules, f"{buyer} always drives a hard bargain.", "",
           "Observations:", f"{opening} {buyer} is trying to buy some fruit from {seller}. They are negotiating a price. {buyer} can sell "
           f"the fruit for {V} coins back in her home town.", *[f'{s} -- "{t}"' for s, t in turns], f"{buyer} is ready to make an offer.", ""]
  text = "\n".join(lines) + "\n" + f"Question: What price would {buyer} propose?:\n"
  l2p = {}
  for l, pos in zip(phase3.LETTERS, order):
    text += f"  ({l}) {grid[pos]} coins\n"
    l2p[l] = grid[pos]
  return text + "Answer: (", l2p


def orders():
  return [tuple((s + i) % 5 for i in range(5)) for s in range(5)]


# ------------------------------------------------------------------ cells
def cell_key(V, gname, line, C, prior, wording):
  return f"V{V}-g{gname}-{line}{'' if C is None else f'-C{C}'}-p{prior[0]}_{prior[1]}-w{wording}"


def old_test_cell(V, gname, line, C, prior) -> bool:
  """The old test cells: grid 1-5 / prior 1-5 and the old cell split's 'test' half, whatever the wording."""
  if gname != "A" or tuple(prior) != (1, 5) or V not in core.VALUES:
    return False
  cell = (V, line) if C is None else (V, "C", C)
  return core.steering_cell_split(cell) == "test"


def sample_cell(rng, typ, Vs, gnames, ws):
  V = rng.choice(Vs); g = rng.choice(gnames); w = rng.choice(ws); prior = rng.choice(PRIORS)
  if typ == "no_cost":
    return V, g, rng.choice(("neutral", "pressure")), None, prior, w
  C = rng.randint(1, V - 1) if typ == "below" else rng.randint(V, V + 2)
  return V, g, "information", C, prior, w


def build():
  rng = random.Random(SEED)
  used, ties_rejected, old_rejected = set(), 0, 0
  # hard_V has no 'at_or_above' cells: with V >= 10 and the seen grids (largest price 7) a stated cost >= V exceeds every
  # offer, so every offer ties at payoff 0 (flagged, excluded); the slice is balanced between 'below' and 'no_cost' instead.
  plan = [  # (split, slice, per-type quota, V set, grids, wordings)
      ("train", "train", 100, SEEN_V, SEEN_GRIDS, SEEN_W),
      ("tune", "tune", 14, SEEN_V, SEEN_GRIDS, SEEN_W),
      ("test_same", "same", 20, SEEN_V, SEEN_GRIDS, SEEN_W),
      ("test_hard", "hard_V", {"below": 10, "no_cost": 10, "at_or_above": 0}, HARD_V, SEEN_GRIDS, SEEN_W),
      ("test_hard", "hard_grid", 7, SEEN_V, HARD_GRIDS, SEEN_W),
      ("test_hard", "hard_wording", 7, SEEN_V, SEEN_GRIDS, HARD_W)]
  cells = []
  for split, sl, quota, Vs, gs, ws in plan:
    for typ in TYPES:
      n = 0
      q = quota[typ] if isinstance(quota, dict) else quota
      while n < q:
        V, g, line, C, prior, w = sample_cell(rng, typ, Vs, gs, ws)
        key = cell_key(V, g, line, C, prior, w)
        if key in used:
          continue
        if old_test_cell(V, g, line, C, prior):
          old_rejected += 1
          continue
        lab = label(V, GRIDS[g], C, prior)
        if lab["all_tie"]:
          ties_rejected += 1                       # flagged (all offers tie): regret is always 0, excluded from the splits
          continue
        used.add(key)
        cells.append({"cell": key, "split": split, "slice": sl, "type": typ, "V": V, "grid_name": g, "grid": list(GRIDS[g]),
                      "line": line, "C": C, "prior": list(prior), "wording": w, **lab})
        n += 1
  pools = names_pool()
  cases = []
  for c in cells:
    pool = pools["train" if c["split"] == "train" else "tune" if c["split"] == "tune" else "test"]
    h = int(hashlib.sha256((str(SEED) + c["cell"]).encode()).hexdigest(), 16)
    for v in (0, 1):
      b = pool[0][(h + 7 * v) % len(pool[0])]
      s = pool[1][(h // 3 + 11 * v) % len(pool[1])]
      cases.append({"cid": f"{c['cell']}-n{v}", "cell": c["cell"], "name_variant": v, "buyer": b, "seller": s, "opening": (h + v) % 5,
                    **{k: c[k] for k in ("split", "slice", "type", "V", "grid_name", "grid", "line", "C", "prior", "wording")}})
  return cells, cases, {"ties_rejected": ties_rejected, "old_test_cells_rejected": old_rejected}


def fingerprints(cells, cases):
  fp = {}
  for name in ("test_same", "test_hard"):
    cs = sorted((c for c in cases if c["split"] == name), key=lambda c: c["cid"])
    blob = json.dumps([[c["cid"], render(c, orders()[0])[0]] for c in cs], sort_keys=True)
    fp[name] = {"n_cells": len({c["cell"] for c in cs}), "n_cases": len(cs), "sha256": hashlib.sha256(blob.encode()).hexdigest()}
    if name == "test_hard":
      for sl in ("hard_V", "hard_grid", "hard_wording"):
        sub = [c for c in cs if c["slice"] == sl]
        fp[f"test_hard/{sl}"] = {"n_cells": len({c["cell"] for c in sub}), "n_cases": len(sub),
                                 "sha256": hashlib.sha256(json.dumps([[c["cid"], render(c, orders()[0])[0]] for c in sub], sort_keys=True).encode()).hexdigest()}
  return fp


if __name__ == "__main__":
  cells, cases, rej = build()
  os.makedirs(OUT, exist_ok=True)
  json.dump({"seed": SEED, "rejected": rej, "cells": cells}, open(os.path.join(OUT, "cells.json"), "w"), indent=1)
  with open(os.path.join(OUT, "cases.jsonl"), "w") as f:
    for c in cases:
      f.write(json.dumps(c) + "\n")
  fp = fingerprints(cells, cases)
  json.dump(fp, open(os.path.join(OUT, "fingerprints.json"), "w"), indent=1)
  import collections
  print(collections.Counter((c["split"], c["slice"], c["type"]) for c in cells))
  print(rej, json.dumps(fp, indent=1))
