"""Fresh locked test sets for the next Gemma experiments (CPU ONLY: no model, no GPU, nothing is scored).

  python demo/gen_test2.py            writes demo/gen/test2_cells.json, test2_cases.jsonl, test2_fingerprints.json, demo_out/gen_test2_report.md

Built from demo/gen_cases.py (imported, unchanged) with a NEW fixed seed. Two sets, disjoint BY CELL from each other and from every cell of the
first generated dataset (train, tune, selection sets A and B, the teacher loop and packet cells, the LoRA training cells - all subsets of the
train split - test_same and test_hard) and from the original study's cell space (grid A, prior 1-5, resale values 2-6: excluded wholesale, not
only its test half). Names come from unused parts of the name pools (buyers/sellers [480:624]), so no name of the first dataset and none of the
old variants 1-14 appears; the two sets use different halves of that part.

  test2_same    40 cells per type (below / at_or_above / no_cost) drawn from the TRAINING RANGES (resale 2-9, grids A-C, wordings 0-1,
                the five priors, stated cost below resale or 0-2 above, or no cost).
  test2_newkey  40 cells per type whose key pair (resale value V, stated cost C - or the cost range prior when there is no stated cost) occurs in
                NONE of the 300 train cells (which contain the 100 LoRA training cells). Rule: up to 20 per type from the training ranges
                (when fewer pairs remain, all of them); the rest from the EXTENSION: resale values 10-15, one new grid F = (8, 10, 12, 14, 16)
                (plus A-C), wordings 0, 1 and one new wording (index 3, reserved for test2 and never used in any training cell).
Every cell has two name variants (names differ; the opening scene is fixed within a cell). At most ONE cell per decision problem (V, grid, C - or
prior when there is no stated cost) per set, because priors and wordings do not change the label of stated-cost cells. The extension is stratified
across its novelties (new V >= 10, new grid F, new wording 3) so they are not all changed at once. Orders: the five cyclic orders of
gen_cases.orders() are frozen for any scoring.
Every cell has two name variants. Cells where every offer ties are dropped (counted). V is drawn uniformly among the values that still have
candidates, then a candidate of that value uniformly (the same V-balanced scheme as gen_cases.build).

Anything that renders test2 cases must `import gen_test2; gen_test2.install()` first (it adds grid F and wording 3 to gen_cases in-process)."""
from __future__ import annotations

import collections, hashlib, itertools, json, os, random, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: F401
import gen_cases as g
from refimpl import core

SEED2 = 20261201
OUT = g.OUT
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NEW_GRID = ("F", (8, 10, 12, 14, 16))
NEW_WORDING = {"neutral": "I'm listening. What price do you have in mind for the fruit?",
               "pressure": "Make it quick: name a serious price now or I turn to the next customer in line.",
               "information": "For your information, I paid {C} for this fruit at the farm. Bear that in mind when you make your offer."}
PER_TYPE = 40
INRANGE_CAP = 20        # test2_newkey: at most this many per type from the training ranges
EXT_V = tuple(range(10, 16))


def install():
  """Add grid F and wording 3 to gen_cases (idempotent)."""
  g.GRIDS[NEW_GRID[0]] = NEW_GRID[1]
  for line, text in NEW_WORDING.items():
    if len(g.SELLER_LINES[line]) == 3:
      g.SELLER_LINES[line] = tuple(g.SELLER_LINES[line]) + (text,)


def pair_key(V, C, prior):
  """(resale value, stated cost) or (resale value, cost range) when there is no stated cost"""
  return (V, C) if C is not None else (V, tuple(prior))


def cur_key(V, gname, C, prior):
  return (V, gname, C, None if C is not None else tuple(prior))


def original_study_cell(V, gname, prior):
  """the original study's cell space, excluded wholesale: grid A, prior 1-5, resale values 2-6"""
  return gname == "A" and tuple(prior) == (1, 5) and V in core.VALUES


def candidates(typ, Vs, grids, wordings):
  out = []
  for V, gn, w, pr in itertools.product(Vs, grids, wordings, g.PRIORS):
    if typ == "no_cost":
      out += [(V, gn, line, None, pr, w) for line in ("neutral", "pressure")]
    else:
      out += [(V, gn, "information", C, pr, w) for C in (range(1, V) if typ == "below" else range(V, V + 3))]
  return out


def problem(x):
  """the decision problem a candidate poses (what the label depends on): (V, grid, C) or (V, grid, prior)"""
  V, gn, line, C, prior, w = x
  return (V, gn, C) if C is not None else (V, gn, tuple(prior))


def novelty(x):
  V, gn, line, C, prior, w = x
  return (V >= 10, gn == NEW_GRID[0], w == 3)


def draw(cands, n, rng, taken, cap=1):
  """V-balanced draw without replacement, at most one cell per decision problem in `taken` (updated): V uniform among values that still have
  candidates, then a candidate of that V uniform."""
  by = collections.defaultdict(list)
  for c in sorted(cands):
    if taken[problem(c)] < cap:
      by[c[0]].append(c)
  chosen = []
  while len(chosen) < n and by:
    V = rng.choice(sorted(by))
    c = by[V].pop(rng.randrange(len(by[V])))
    if not by[V]:
      del by[V]
    if taken[problem(c)] >= cap:
      continue
    taken[problem(c)] += 1; chosen.append(c)
  return chosen


def draw_stratified(cands, n, rng, taken, cap=1):
  """spread n over the novelty groups (new V, new grid, new wording) as evenly as the groups allow, then fill the rest from any group"""
  groups = collections.defaultdict(list)
  for c in cands:
    groups[novelty(c)].append(c)
  keys = sorted(groups)
  out, left = [], n
  while left > 0 and keys:
    share = max(1, left // len(keys))
    progressed = False
    for k in list(keys):
      take = draw(groups[k], min(share, left), rng, taken, cap)
      out += take; left -= len(take); progressed |= bool(take)
      if not take or not [c for c in groups[k] if taken[problem(c)] < cap]:
        keys.remove(k)
      if left <= 0:
        break
    if not progressed:
      break
  return out


def name_pools():
  """buyers/sellers exactly as gen_cases.names_pool builds them; the first 480 are the first dataset's, [480:624] are unused so far"""
  rng = random.Random(g.SEED)
  buyers = [f"{a} {s}" for a in g._BUYER_FIRST for s in g._SURNAMES]
  sellers = [f"{a} {s}" for a in g._SELLER_FIRST for s in g._SURNAMES]
  rng.shuffle(buyers); rng.shuffle(sellers)
  old = g.names_pool()
  assert buyers[:300] == old["train"][0] and buyers[360:480] == old["test"][0] and sellers[360:480] == old["test"][1]
  assert not (set(buyers) | set(sellers)) & (set(core.FEMALE_NAMES) | set(core.MALE_NAMES))
  return {"test2_same": (buyers[480:552], sellers[480:552]), "test2_newkey": (buyers[552:624], sellers[552:624])}


def build():
  install()
  first = json.load(open(os.path.join(OUT, "cells.json")))["cells"]
  used = {c["cell"] for c in first}
  train = [c for c in first if c["split"] == "train"]
  lora = json.load(open(os.path.join(OUT, "lora_train_cells.json")))
  assert len(train) == 300 and len(lora) == 100 and set(lora) <= {c["cell"] for c in train}
  train_pairs = {pair_key(c["V"], c["C"], c["prior"]) for c in train}
  train_cur = {cur_key(c["V"], c["grid_name"], c["C"], c["prior"]) for c in train}
  rng = random.Random(SEED2)
  stats = {"ties_dropped": collections.Counter(), "original_study_excluded": 0}
  cells = []

  lora_cells_ = {c["cell"] for c in train if c["cell"] in set(lora)}
  lora_cur = {cur_key(c["V"], c["grid_name"], c["C"], c["prior"]) for c in train if c["cell"] in lora_cells_}

  def finish(split, typ, sel, region):
    for V, gn, line, C, prior, w in sel:
      lab = g.label(V, g.GRIDS[gn], C, prior)
      srt = sorted(lab["payoffs"], reverse=True)
      nv, ng, nw = novelty((V, gn, line, C, prior, w))
      cells.append({"cell": g.cell_key(V, gn, line, C, prior, w), "split": split, "slice": split, "region": region, "type": typ, "V": V, "grid_name": gn,
                    "grid": list(g.GRIDS[gn]), "line": line, "C": C, "prior": list(prior), "wording": w, **lab,
                    "novel_V": nv, "novel_grid": ng, "novel_wording": nw, "V_ge_13": V >= 13, "best_is_cheapest": 0 in lab["best_positions"],
                    "margin_best_second": round(srt[0] - srt[1], 6), "problem": list(problem((V, gn, line, C, prior, w))),
                    "key_in_train300": cur_key(V, gn, C, prior) in train_cur, "key_in_lora100": cur_key(V, gn, C, prior) in lora_cur})
      used.add(cells[-1]["cell"])

  def ok_cands(typ, Vs, grids, wordings, newkey_only):
    keep = []
    for x in candidates(typ, Vs, grids, wordings):
      V, gn, line, C, prior, w = x
      if g.cell_key(*x) in used:
        continue
      if original_study_cell(V, gn, prior):
        stats["original_study_excluded"] += 1; continue
      if newkey_only and pair_key(V, C, prior) in train_pairs:
        continue
      if g.label(V, g.GRIDS[gn], C, prior)["all_tie"]:
        stats["ties_dropped"][typ] += 1; continue
      keep.append(x)
    return keep

  # test2_same: the training ranges, one cell per decision problem
  taken_same, taken_new = collections.Counter(), collections.Counter()
  stats["same_problem_cap"] = {}
  for typ in g.TYPES:
    c = ok_cands(typ, g.SEEN_V, g.SEEN_GRIDS, g.SEEN_W, False)
    cap = 1
    while len({problem(x) for x in c}) * cap < PER_TYPE:      # the training ranges hold only 33 non-tie at-or-above problems: allow 2 cells per problem there
      cap += 1
    stats["same_problem_cap"][typ] = cap
    sel = draw(c, PER_TYPE, rng, taken_same, cap)
    assert len(sel) == PER_TYPE, (typ, len(sel))
    finish("test2_same", typ, sel, "training ranges")
  # test2_newkey: unseen (V, C | prior) pairs; in-range first (capped), then the extension
  stats["newkey_space"] = {}
  for typ in g.TYPES:
    inr = ok_cands(typ, g.SEEN_V, g.SEEN_GRIDS, g.SEEN_W, True)
    ext = ok_cands(typ, tuple(range(2, 10)) + EXT_V, g.SEEN_GRIDS + (NEW_GRID[0],), g.SEEN_W + (3,), True)
    ext = [x for x in ext if g.cell_key(*x) not in used and novelty(x) != (False, False, False)]
    stats["newkey_space"][typ] = {"in_range_pairs_available_cells": len(inr), "in_range_problems_available": len({problem(x) for x in inr}),
                                  "extension_available_cells": len(ext), "extension_problems_available": len({problem(x) for x in ext})}
    cap = 1
    while len({problem(x) for x in inr + ext}) * cap < PER_TYPE:       # only 28-29 distinct at-or-above problems exist outside the train cells' pairs
      cap += 1
    stats.setdefault("newkey_problem_cap", {})[typ] = cap
    sel = draw(inr, min(INRANGE_CAP, len(inr)), rng, taken_new, cap)
    finish("test2_newkey", typ, sel, "training ranges")
    need = PER_TYPE - len(sel)
    got = draw_stratified(ext, need, rng, taken_new, cap)
    assert len(got) == need, (typ, len(got), need)
    finish("test2_newkey", typ, got, "extension")
  pools = name_pools()
  cases = []
  for c in cells:
    pb, ps = pools[c["split"]]
    h = int(hashlib.sha256((str(SEED2) + c["cell"]).encode()).hexdigest(), 16)
    for v in (0, 1):
      cases.append({"cid": f"{c['cell']}-n{v}", "cell": c["cell"], "name_variant": v, "buyer": pb[(h + 7 * v) % len(pb)], "seller": ps[(h // 3 + 11 * v) % len(ps)],
                    "opening": h % 5, **{k: c[k] for k in ("split", "slice", "type", "V", "grid_name", "grid", "line", "C", "prior", "wording")}})
  stats["ties_dropped"] = dict(stats["ties_dropped"])
  return cells, cases, stats, {"train_pairs": train_pairs, "train_cur": train_cur, "lora": lora, "train": train}


def fingerprints(cells, cases):
  install()
  sha = lambda b: hashlib.sha256(b).hexdigest()
  fp = {"seed": SEED2, "files": {"demo/gen_test2.py": sha(open(os.path.join(ROOT, "demo", "gen_test2.py"), "rb").read()),
                                 "demo/gen_cases.py": sha(open(os.path.join(ROOT, "demo", "gen_cases.py"), "rb").read()),
                                 "demo/gen/cells.json": sha(open(os.path.join(OUT, "cells.json"), "rb").read()),
                                 "refimpl/core.py": sha(open(os.path.join(ROOT, "refimpl", "core.py"), "rb").read()),
                                 "refimpl/phase3.py": sha(open(os.path.join(ROOT, "refimpl", "phase3.py"), "rb").read()),
                                 "demo/gen/lora_train_cells.json": sha(open(os.path.join(OUT, "lora_train_cells.json"), "rb").read()),
                                 "demo/gen/test2_cells.json": sha(open(os.path.join(OUT, "test2_cells.json"), "rb").read()),
                                 "demo/gen/test2_cases.jsonl": sha(open(os.path.join(OUT, "test2_cases.jsonl"), "rb").read()),
                                 "fruitville_haggling.py": sha(open(os.path.join(ROOT, "concordia", "examples", "modular", "environment", "modules", "fruitville_haggling.py"), "rb").read())},
        "orders": [list(o) for o in g.orders()], "sets": {}}
  for name in ("test2_same", "test2_newkey"):
    cs = sorted((c for c in cases if c["split"] == name), key=lambda c: c["cid"])
    cl = sorted((c for c in cells if c["split"] == name), key=lambda c: c["cell"])
    blob = json.dumps([[c["cid"], [g.render(c, o)[0] for o in g.orders()]] for c in cs], sort_keys=True)     # all five frozen cyclic orders
    fp["sets"][name] = {"n_cells": len(cl), "n_cases": len(cs), "rendered_prompts_sha256": sha(blob.encode()),
                        "cells_with_labels_sha256": sha(json.dumps(cl, sort_keys=True).encode()),
                        "cell_ids_sha256": sha(json.dumps([c["cell"] for c in cl]).encode())}
  return fp


def report(cells, cases, stats, ctx):
  by_split = {s: [c for c in cells if c["split"] == s] for s in ("test2_same", "test2_newkey")}
  tp, tc = ctx["train_pairs"], ctx["train_cur"]
  lora_cells = [c for c in ctx["train"] if c["cell"] in set(ctx["lora"])]
  lp = {pair_key(c["V"], c["C"], c["prior"]) for c in lora_cells}
  lc = {cur_key(c["V"], c["grid_name"], c["C"], c["prior"]) for c in lora_cells}
  tvc = {(c["V"], c["C"]) for c in ctx["train"]}; lvc = {(c["V"], c["C"]) for c in lora_cells}
  L = ["# test2 sets: fresh locked test cells (CPU only, nothing scored)", "",
       f"seed {SEED2}; two name variants per cell; extension: grid F {NEW_GRID[1]}, resale values 10-15, seller wording index 3 (reserved for test2).", "",
       f"(counts of candidate evaluations, summed over the enumerations, not distinct cells: all-tie candidates dropped {stats['ties_dropped']}; original-study-space candidates excluded {stats['original_study_excluded']}); no cell in either set is a tie",
       f"availability for test2_newkey (cells not used, not tie, pair not in the 300 train cells): {json.dumps(stats['newkey_space'])}", ""]
  for s, cs in by_split.items():
    L += [f"## {s}: {len(cs)} cells, {2 * len(cs)} cases", "", "| type | cells | single best offer | in training ranges | extension |", "| --- | --- | --- | --- | --- |"]
    for t in g.TYPES:
      x = [c for c in cs if c["type"] == t]
      L.append(f"| {t} | {len(x)} | {sum(c['unique_best'] for c in x)} ({100 * sum(c['unique_best'] for c in x) / len(x):.0f}%) | {sum(c['region'] == 'training ranges' for c in x)} | {sum(c['region'] == 'extension' for c in x)} |")
    L.append(f"| all | {len(cs)} | {sum(c['unique_best'] for c in cs)} ({100 * sum(c['unique_best'] for c in cs) / len(cs):.0f}%) | {sum(c['region'] == 'training ranges' for c in cs)} | {sum(c['region'] == 'extension' for c in cs)} |")
    L += ["", f"V values: {dict(sorted(collections.Counter(c['V'] for c in cs).items()))}; grids: {dict(collections.Counter(c['grid_name'] for c in cs))}; wordings: {dict(collections.Counter(c['wording'] for c in cs))}", "",
          "Cells sharing a label key with training (counts of cells; by type below / at_or_above / no_cost):", ""]
    L += ["| key | vs the 300 train cells | vs the 100 LoRA training cells |", "| --- | --- | --- |"]
    def cnt(fn, ref):
      return " / ".join(str(sum(fn(c) in ref for c in cs if c["type"] == t)) for t in g.TYPES) + f" (total {sum(fn(c) in ref for c in cs)})"
    L.append(f"| current key (V, grid, C or prior) | {cnt(lambda c: cur_key(c['V'], c['grid_name'], c['C'], c['prior']), tc)} | {cnt(lambda c: cur_key(c['V'], c['grid_name'], c['C'], c['prior']), lc)} |")
    L.append(f"| stricter (V, C) key, C = none for no-cost cells | {cnt(lambda c: (c['V'], c['C']), tvc)} | {cnt(lambda c: (c['V'], c['C']), lvc)} |")
    L.append(f"| pair (V, C or cost range) | {cnt(lambda c: pair_key(c['V'], c['C'], c['prior']), tp)} | {cnt(lambda c: pair_key(c['V'], c['C'], c['prior']), lp)} |")
    L += ["", "Effective size and trivial references (label-only, nothing scored; soft regret = best payoff minus expected payoff of the policy; one value per cell, mean over cells):", "",
          "| type | cells | distinct problems (V, grid, C or prior) | distinct pairs | best = cheapest price | mean best-set size | uniform-random regret | always-cheapest regret | stated-cost-rule regret | median margin best-second |",
          "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    import statistics
    def rule_pos(c):
      return next((i for i, x in enumerate(c["grid"]) if x >= c["C"]), 4) if c["C"] is not None and c["C"] < c["V"] else 0
    for t in g.TYPES:
      x = [c for c in cs if c["type"] == t]
      L.append(f"| {t} | {len(x)} | {len({tuple(c['problem']) for c in x})} | {len({pair_key(c['V'], c['C'], c['prior']) for c in x})} | {sum(c['best_is_cheapest'] for c in x)} | "
               f"{sum(len(c['best_positions']) for c in x) / len(x):.2f} | {sum(c['best_payoff'] - sum(c['payoffs']) / 5 for c in x) / len(x):.2f} | "
               f"{sum(c['best_payoff'] - c['payoffs'][0] for c in x) / len(x):.2f} | {sum(c['best_payoff'] - c['payoffs'][rule_pos(c)] for c in x) / len(x):.2f} | {statistics.median(c['margin_best_second'] for c in x):.2f} |")
    L += ["", "Slices (pre-declared; never report one pooled number for test2_newkey):", "",
          "| slice | below | at_or_above | no_cost |", "| --- | --- | --- | --- |"]
    sl = {"training ranges (no novelty)": lambda c: not (c["novel_V"] or c["novel_grid"] or c["novel_wording"]),
          "new V only (>=10, grids A-C, wordings 0-1)": lambda c: c["novel_V"] and not c["novel_grid"] and not c["novel_wording"],
          "new grid F (any V, wordings 0-1)": lambda c: c["novel_grid"] and not c["novel_wording"],
          "new wording 3 (any V, grids A-C)": lambda c: c["novel_wording"] and not c["novel_grid"],
          "new grid F and new wording 3": lambda c: c["novel_grid"] and c["novel_wording"],
          "V 13-15 (the clean extension: V 10-12 also occur in test_hard)": lambda c: c["V_ge_13"],
          "label key (V, grid, C or prior) seen in the 100 LoRA cells": lambda c: c["key_in_lora100"],
          "label key seen in the 300 train cells": lambda c: c["key_in_train300"]}
    for nm, fn in sl.items():
      L.append(f"| {nm} | " + " | ".join(str(sum(1 for c in cs if c["type"] == t and fn(c))) for t in g.TYPES) + " |")
    L.append("")
  L += ["Notes: (1) the (V, C) row with C = none is vacuous for no-cost cells (every no-cost cell at a trained V matches). (2) test2_same is a within-distribution check and partly overlaps training problems; report it stratified by key seen / unseen. "
        "(3) For at-or-above cells every offer below the stated cost is best (best payoff 0), so that type tests avoiding overpayment, not finding one best offer; headline soft regret, never pooled hit rate. "
        "(4) Below-cost cells whose best offer is the cheapest price are solved by always offering the cheapest price; the references above must be beaten. (5) V below the smallest grid price forces a negative best payoff (the model cannot decline to trade)."]
  return "\n".join(L) + "\n"


def main():
  cells, cases, stats, ctx = build()
  json.dump({"seed": SEED2, "stats": stats, "cells": cells}, open(os.path.join(OUT, "test2_cells.json"), "w"), indent=1)
  with open(os.path.join(OUT, "test2_cases.jsonl"), "w") as f:
    for c in cases:
      f.write(json.dumps(c) + "\n")
  fp = fingerprints(cells, cases)
  json.dump(fp, open(os.path.join(OUT, "test2_fingerprints.json"), "w"), indent=1)
  rep = report(cells, cases, stats, ctx)
  open(os.path.join(ROOT, "demo_out", "gen_test2_report.md"), "w").write(rep)
  print(rep)
  print(json.dumps(fp["sets"], indent=1))


if __name__ == "__main__":
  main()
