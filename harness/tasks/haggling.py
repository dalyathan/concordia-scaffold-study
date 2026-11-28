"""Haggling task (ported from demo/gen_cases.py; same seed, quotas, labels and text, so cases.jsonl and cells.json are
reproduced byte for byte: tests/harness/test_haggling_port.py compares sha256).

One buying decision from the 2024 Concordia haggling game: five price options, regret in coins against the exact best offer.
Splits: train, tune, select_B, test_same, test_hard, test2_same, test2_newkey (the four test splits are LOCKED: harness.evaluate refuses them
without a lock token and the owner pin; test2 is read from the committed files after a fingerprint check)."""
from __future__ import annotations

import hashlib
import json
import os
import random
import string
import sys

from refimpl import core   # pure Python (no torch); only its name lists and cell split are used
from harness.protected.payoffs import haggling as _payoffs

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GEN_DIR = os.path.join(ROOT, "demo", "gen")
LETTERS = list(string.ascii_lowercase[:5])


def _ensure_concordia():
  c = os.path.join(ROOT, "concordia")
  if os.path.isdir(c) and c not in sys.path:
    sys.path.insert(0, c)


class _FV:
  """VISUAL_SCENE_OPENINGS read from the pinned Concordia file by AST, so no Concordia dependency has to be importable."""
  _cache = None

  @property
  def VISUAL_SCENE_OPENINGS(self):
    if _FV._cache is None:
      import ast
      path = os.path.join(ROOT, "concordia", "examples", "modular", "environment", "modules", "fruitville_haggling.py")
      for node in ast.parse(open(path).read()).body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == "VISUAL_SCENE_OPENINGS" for t in node.targets):
          _FV._cache = ast.literal_eval(node.value)
    return _FV._cache


def instructions_text(buyer: str) -> str:
  """v1.8.9 concordia/components/agent/instructions.py, name substituted (copy of refimpl.phase3.instructions_text)."""
  n = buyer
  return (f"The instructions for how to play the role of {n} are as follows. This is "
          f"a social science experiment studying how well you play the role of a "
          f"character named {n}. The experiment is structured as a tabletop "
          "roleplaying game (like dungeons and dragons). However, in this case it "
          "is a serious social science experiment and simulation. The goal is to be "
          f"realistic. It is important to play the role of a person like {n} as "
          "accurately as possible, i.e., by responding in ways that you think it is "
          f"likely a person like {n} would respond, and taking into account all "
          f"information about {n} that you have. Always use third-person limited "
          "perspective.")


SHARED_MEMORY_1 = "Fruits are sold by weight."

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
# test2 only (demo/gen_test2.py NEW_WORDING, index 3; reserved for test2, never in a training cell). Kept out of SELLER_LINES so
# build() and the train/tune/test port are untouched; tests/harness/test_test2_port.py checks it equals demo/gen_test2.NEW_WORDING.
TEST2_WORDING_INDEX = 3
TEST2_WORDING = {"neutral": "I'm listening. What price do you have in mind for the fruit?",
                 "pressure": "Make it quick: name a serious price now or I turn to the next customer in line.",
                 "information": "For your information, I paid {C} for this fruit at the farm. Bear that in mind when you make your offer."}
_BUYER_FIRST = ["Alma", "Briar", "Calla", "Dessa", "Edda", "Fenna", "Gwyn", "Hollis", "Isla", "Joss", "Kestra", "Linnea", "Marnie",
                "Neve", "Odile", "Perrin", "Quilla", "Rhea", "Sorrel", "Tamsin", "Una", "Verity", "Wren", "Xanthe", "Yara", "Zelda"]
_SELLER_FIRST = ["Alder", "Bram", "Corin", "Davin", "Emrys", "Fergus", "Galen", "Hollin", "Ilar", "Jory", "Kellan", "Lorcan", "Merrick",
                 "Niall", "Osric", "Penn", "Quill", "Rowan", "Silas", "Tavish", "Ulric", "Varrin", "Wystan", "Yorick", "Zane", "Dunstan"]
_SURNAMES = ["Applecroft", "Barleyfield", "Cherrydale", "Damsonhill", "Elderglen", "Fennelmoor", "Gooseberry", "Hazelmere",
             "Juniperfold", "Kumquatridge", "Limeharbor", "Medlarwick", "Nectarvale", "Olivebrook", "Papayafold", "Quinceton",
             "Raspberrow", "Sloefield", "Tangelo", "Ugliwood", "Vineyard", "Walnutlea", "Yewbank", "Zestmoor"]


# ------------------------------------------------------------------ payoff (rule lives in harness/protected)
from harness.protected.payoffs.haggling import payoff  # noqa: E402


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
  fv = _FV()
  grid, (lo, hi), buyer, seller, V = case["grid"], case["prior"], case["buyer"], case["seller"], case["V"]
  step = grid[1] - grid[0]
  mid = grid[2]
  coin = lambda n: f"{n} coin" + ("" if n == 1 else "s")
  m2 = (f"The price of one kilogram of fruit is, on average, {mid} coins. {coin(grid[0])} is really cheap and {coin(grid[-1])} is "
        f"really expensive. The smallest value of transaction is {coin(step)}, all prices have to be in multiples of {coin(step)}. "
        "No fractional values are allowed.")
  rules = (f"Sellers at this market pay between {lo} and {hi} coins per kilogram at the farm, and each amount is equally likely.",
           core.RULE_MEMORIES[1], core.RULE_MEMORIES[2])
  wording = TEST2_WORDING[case["line"]] if case["wording"] == TEST2_WORDING_INDEX else SELLER_LINES[case["line"]][case["wording"]]
  last = wording.format(C=("" if case["C"] is None else coin(case["C"])))
  opening = fv.VISUAL_SCENE_OPENINGS[case["opening"]]
  turns = [(buyer, core.SCRIPT[0]), (seller, core.SCRIPT[1]), (buyer, core.SCRIPT[2]), (seller, last)]
  lines = [instructions_text(buyer), "", "Memories:", SHARED_MEMORY_1, m2, *rules, f"{buyer} always drives a hard bargain.", "",
           "Observations:", f"{opening} {buyer} is trying to buy some fruit from {seller}. They are negotiating a price. {buyer} can sell "
           f"the fruit for {V} coins back in her home town.", *[f'{s} -- "{t}"' for s, t in turns], f"{buyer} is ready to make an offer.", ""]
  text = "\n".join(lines) + "\n" + f"Question: What price would {buyer} propose?:\n"
  l2p = {}
  for l, pos in zip(LETTERS, order):
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


def fingerprints_v2(cells):
  """Test-cell entries INCLUDING labels, plus the generator and the text modules the prompts depend on."""
  sha = lambda b: hashlib.sha256(b).hexdigest()
  root = ROOT
  here = os.path.join(ROOT, "demo")
  fv = os.path.join(root, "concordia", "examples", "modular", "environment", "modules", "fruitville_haggling.py")
  out = {"generator_sha256_excluding_this_function_note": "see files", "files": {
      "demo/gen_cases.py": sha(open(os.path.join(here, "gen_cases.py"), "rb").read()),
      "refimpl/core.py": sha(open(os.path.join(root, "refimpl", "core.py"), "rb").read()),
      "refimpl/phase3.py": sha(open(os.path.join(root, "refimpl", "phase3.py"), "rb").read()),
      "fruitville_haggling.py": sha(open(fv, "rb").read())}, "seed": SEED, "cells": {}}
  for name, sel in (("test_same", lambda c: c["split"] == "test_same"), ("test_hard", lambda c: c["split"] == "test_hard"),
                    ("hard_V", lambda c: c["slice"] == "hard_V"), ("hard_grid", lambda c: c["slice"] == "hard_grid"),
                    ("hard_wording", lambda c: c["slice"] == "hard_wording")):
    sub = sorted((c for c in cells if sel(c)), key=lambda c: c["cell"])
    out["cells"][name] = {"n_cells": len(sub), "sha256_with_labels": sha(json.dumps(sub, sort_keys=True).encode())}
  out["quotas"] = "train 100/type, tune 14/type, test_same 20/type, hard_V 10 below + 10 no_cost, hard_grid 7/type, hard_wording 7/type (single RNG stream: changing a quota changes later splits)"
  out.pop("generator_sha256_excluding_this_function_note")
  return out




# ------------------------------------------------------------------ Task interface
class HagglingTask:
  name = "haggling"
  splits = ("train", "tune", "test_same", "test_hard", "select_B", "test2_same", "test2_newkey")
  locked_splits = ("test_same", "test_hard", "test2_same", "test2_newkey")
  # test2_same / test2_newkey: the second held-out sets (demo/gen_test2.py, seed 20261201, locked Nov 23 before any model saw them).
  # They are read from the committed files, never rebuilt, and only after the files match demo/gen/test2_fingerprints.json.
  TEST2_CASES = os.path.join(GEN_DIR, "test2_cases.jsonl")
  TEST2_FINGERPRINTS = os.path.join(GEN_DIR, "test2_fingerprints.json")
  # select_B: the LoRA selection set of the Gemma study (42 train cells outside the 100 training cells, name variant 0;
  # demo/gen/lora_select_cells_B.json). It is a subset of `train`, used for early stopping and the lr choice only.
  SELECT_B = os.path.join(GEN_DIR, "lora_select_cells_B.json")
  system_prompt = None     # the haggling prompt carries its own instructions; the model system text is set by the solver

  def __init__(self):
    self._cells, self._cases, self._rej = None, None, None

  def _build(self):
    if self._cases is None:
      self._cells, self._cases, self._rej = build()
    return self._cells, self._cases

  def build_all(self):
    cells, cases = self._build()
    return {"seed": SEED, "rejected": self._rej, "cells": cells}, cases

  def cases(self, split: str) -> list[dict]:
    if split == "select_B":
      sel = set(json.load(open(self.SELECT_B)))
      out = [c for c in self._build()[1] if c["split"] == "train" and c["cell"] in sel and c["name_variant"] == 0]
      assert len(out) == len(sel) == 42, "selection set B must be 42 train cells"
      return out
    if split in ("test2_same", "test2_newkey"):
      return self._test2_cases(split)
    return [c for c in self._build()[1] if c["split"] == split]

  def _test2_cases(self, split: str) -> list[dict]:
    """The committed test2 cases of one set, after a sha256 check of the cases file against the locked fingerprint file."""
    fp = json.load(open(self.TEST2_FINGERPRINTS))
    want = fp["files"]["demo/gen/test2_cases.jsonl"]
    raw = open(self.TEST2_CASES, "rb").read()
    got = hashlib.sha256(raw).hexdigest()
    if got != want:
      raise RuntimeError(f"demo/gen/test2_cases.jsonl sha256 {got} differs from the locked fingerprint {want}")
    out = [c for c in (json.loads(l) for l in raw.decode().splitlines() if l.strip()) if c["split"] == split]
    if len(out) != 240:
      raise RuntimeError(f"{split}: expected 240 cases, found {len(out)}")
    return out

  def insert_notes(self, text: str, notes: str) -> str:
    """A Notes block before the question, exactly as demo/gen_notes.render_notes (the Gemma text rows and distillation targets)."""
    head, tail = text.split("Question:", 1)
    return head + "Notes:\n" + notes + "\n\n" + "Question:" + tail

  BASELINES = ("cheapest", "stated_cost_rule")

  def baseline_option(self, name: str, case: dict) -> int:
    """Model-free reference policies (grid index). cheapest: the lowest price. stated_cost_rule (demo/gen_curve_report.py): if a
    cost is stated below the resale value, the cheapest listed price >= the cost (the dearest if none), otherwise the cheapest."""
    grid = case["grid"]
    if name == "cheapest":
      return grid.index(min(grid))
    if name == "stated_cost_rule":
      if case["C"] is not None and case["C"] < case["V"]:
        return next((i for i, x in enumerate(grid) if x >= case["C"]), len(grid) - 1)
      return grid.index(min(grid))
    raise KeyError(name)

  def n_options(self, case) -> int:
    return len(case["grid"])

  def orders(self, case):
    return orders()

  def render(self, case, order):
    """-> (prompt text, {letter: option index})."""
    text, l2p = render(case, order)
    grid = case["grid"]
    return text, {l: grid.index(p) for l, p in l2p.items()}

  def option_labels(self, case):
    return [f"{k} coins" for k in case["grid"]]

  def payoffs(self, case) -> list:
    return _payoffs.payoffs(case)

  def reference(self, case) -> dict:
    """Reference solver: the exact best offer(s)."""
    lab = label(case["V"], case["grid"], case["C"], case["prior"])
    return {"best_options": lab["best_positions"], "best_payoff": lab["best_payoff"]}

  def case_type(self, case) -> str:
    return case["type"]

  def planted_cases(self) -> list[dict]:
    """Known-answer cases (one per type), built by hand from first principles; never part of any split."""
    out = []
    base = {"split": "planted", "slice": "planted", "grid_name": "A", "grid": [1, 2, 3, 4, 5], "prior": [1, 5], "wording": 0,
            "buyer": "Planta Applecroft", "seller": "Plant Barleyfield", "opening": 0, "name_variant": 0}
    # stated cost 2, resale 5: any offer >= 2 pays 5-k, so 2 is the unique best (payoff 3)
    out.append({**base, "cid": "planted-below", "cell": "planted-below", "type": "below", "V": 5, "line": "information", "C": 2})
    # no cost, prior 1..5, V=6: payoffs (6-k)*k/5 = 1,1.6,1.8,1.6,1 -> unique best is 3
    out.append({**base, "cid": "planted-nocost", "cell": "planted-nocost", "type": "no_cost", "V": 6, "line": "neutral", "C": None})
    # stated cost 4 >= resale 3: every offer pays 0 or is below cost; offers of 4+ pay (3-k)<0 -> best is any offer < 4 (payoff 0)
    out.append({**base, "cid": "planted-atabove", "cell": "planted-atabove", "type": "at_or_above", "V": 3, "line": "information", "C": 4})
    # stated cost 5, resale 9: only an offer of 5 pays (4); "always offer 2" fails it, so the known failure of the plain model is caught
    out.append({**base, "cid": "planted-high", "cell": "planted-high", "type": "below", "V": 9, "line": "information", "C": 5})
    return out

  def planted_expected(self) -> dict:
    return {"planted-below": [1], "planted-nocost": [2], "planted-atabove": [0, 1, 2], "planted-high": [4]}


TASK = HagglingTask


def main():
  t = HagglingTask()
  meta, cases = t.build_all()
  return meta, cases


if __name__ == "__main__":
  import sys as _s
  if len(_s.argv) < 2:
    raise SystemExit("usage: python -m harness.tasks.haggling <scratch output dir>   (never demo/gen: it is the reference)")
  out = _s.argv[1]
  if os.path.realpath(out).startswith(os.path.realpath(GEN_DIR)):
    raise SystemExit("refusing to write into demo/gen (the byte-for-byte reference, fingerprinted elsewhere)")
  os.makedirs(out, exist_ok=True)
  cells, cases, rej = build()
  json.dump({"seed": SEED, "rejected": rej, "cells": cells}, open(os.path.join(out, "cells.json"), "w"), indent=1)
  with open(os.path.join(out, "cases.jsonl"), "w") as f:
    for c in cases:
      f.write(json.dumps(c) + "\n")
  json.dump(fingerprints(cells, cases), open(os.path.join(out, "fingerprints.json"), "w"), indent=1)
