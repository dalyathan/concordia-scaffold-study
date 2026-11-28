"""Steps 2-4 of TARGETED_PLAN.md (CPU only): the targeting prompt, the per-seed draws of arms T, R and N, the fixed orders of each extra
cell, and the labelling packets and their check. Nothing here touches tune, test or test3 cells.

  python scripts/targeted_prepare.py prompt   [--model qwen25_7b]   demo/gen/targeting_prompt_<model>.md from the failure-map table only
  python scripts/targeted_prepare.py draw     [--model qwen25_7b]   needs demo/gen/targeting_rule_<model>.json (Claude's reply, verbatim);
                                                                     writes demo/gen/targeted_draws_<model>.json (per arm and seed: 50 cells,
                                                                     counts by type, V band, grid, wording) and the orders file
  python scripts/targeted_prepare.py packets  [--model qwen25_7b]   labelling packets for the union of drawn cells: shuffled, arm-blind,
                                                                     at most 100 cases each, in the original packet format
  python scripts/targeted_prepare.py labels   [--model qwen25_7b]   reads the verbatim replies, writes demo/gen/targeted_labels_<model>.json and
                                                                     the agreement with the payoff rule (lowest-price ties) by arm and type

Rule format (the targeting Claude's reply): {"clauses": [{"where": {...}, "weight": w}, ...], "reasoning": "..."}. Allowed keys in
"where": type (list), V_min, V_max, grid (list of grid names), prior (list of [lo, hi]), line (list), wording (list), stated_cost_minus_V_min,
stated_cost_minus_V_max. A cell's weight is the sum of the weights of the clauses it matches; weight 0 cells are never drawn.
Draws: one cell per decision problem, never a select3 cell. T_s: weighted sampling without replacement (numpy PCG64 seed 100 + s);
R_s: uniform (seed 200 + s); N_s: no-cost cells, V uniform among values with cells left, then a cell uniform (seed 300 + s)."""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "demo"))
GEN = os.path.join(ROOT, "demo", "gen")
N_EXTRA, SEEDS, ORDER_SEED, PACKET_SIZE = 50, (0, 1, 2), 20261204, 100
WHERE_KEYS = {"type", "V_min", "V_max", "grid", "prior", "line", "wording", "stated_cost_minus_V_min", "stated_cost_minus_V_max"}


def path(kind, model, ext="json"):
  return os.path.join(GEN, f"{kind}_{model}.{ext}")


def sha_obj(o):
  return hashlib.sha256(json.dumps(o, sort_keys=True).encode()).hexdigest()


def pool():
  from harness.tasks.haggling3 import Haggling3Task
  t = Haggling3Task()
  cells = t._load("pool3")[1]
  return t, cells


# ------------------------------------------------------------------ step 2: the prompt
PROMPT = """# Where should the next training examples go?

A small language model (Qwen 2.5 7B Instruct) plays a buyer in a one-shot haggling game. It sees the resale value V, five listed prices (a "grid"), the range of farm costs sellers pay at this market (every whole number in the range equally likely), and the seller's last line, which sometimes states the seller's farm cost. The seller accepts any offer at or above the farm cost; the buyer's profit is V minus the offer if accepted, else 0. The buyer should pick the offer with the highest expected profit. "Soft regret" is the expected profit lost against the best offer, in coins (0 is perfect).

The model was fine-tuned on 100 worked examples (resale values 2-9, grids A-C, seller wordings 0-1). Three fine-tuned copies (seeds 0, 1, 2) were then scored on the 90 build cases below, which it never trained on. Case types: "below" = a stated cost below V; "at_or_above" = a stated cost at or above V (any offer below the cost is refused, so offering the cheapest price is best); "no_cost" = no cost is stated, so the buyer must reason from the cost range.

Your task: choose where 50 extra training examples should go to fix the fine-tuned model's remaining failures. A held-out test set exists; you are not told anything about it, and you should aim at the failures you see here. The 50 cells will be drawn from a pool of 519 unused cells (189 no_cost, 315 below, 15 at_or_above; resale values 2-15; grids A-F; wordings 0-3), one cell per decision problem, with probability proportional to the weight your rule gives each cell.

Answer with ONE JSON object and nothing else:
{"clauses": [{"where": {...}, "weight": <positive number>}, ...], "reasoning": "<two sentences>"}
Allowed keys in "where": "type" (list of case types), "V_min", "V_max", "grid" (list of grid names), "prior" (list of [low, high] cost ranges), "line" (list of "neutral", "pressure", "information"), "wording" (list of 0-3), "stated_cost_minus_V_min", "stated_cost_minus_V_max". A cell's weight is the sum of the weights of the clauses it matches; cells matching no clause are never drawn. At least 50 pool cells must match.

Grids: A = 1-5, B = 2-6, C = 3-7, D = 2-10 in steps of 2, E = 4-8, F = 8-16 in steps of 2 (coins).

## The 90 build cases (A0 = the fine-tuned model; plain = before fine-tuning)

"""


def cmd_prompt(model):
  ft = json.load(open(path("failure_map_probe3", model)))
  md = open(path("failure_map_probe3", model, "md")).read()
  text = PROMPT + md
  open(path("targeting_prompt", model, "md"), "w").write(text)
  print("wrote", os.path.relpath(path("targeting_prompt", model, "md"), ROOT), f"({ft['n_cells']} cells)")


# ------------------------------------------------------------------ step 3: the draws
def matches(where, c):
  if set(where) - WHERE_KEYS:
    raise SystemExit(f"rule uses unknown keys {sorted(set(where) - WHERE_KEYS)}")
  if "type" in where and c["type"] not in where["type"]: return False
  if "V_min" in where and c["V"] < where["V_min"]: return False
  if "V_max" in where and c["V"] > where["V_max"]: return False
  if "grid" in where and c["grid_name"] not in where["grid"]: return False
  if "prior" in where and list(c["prior"]) not in [list(p) for p in where["prior"]]: return False
  if "line" in where and c["line"] not in where["line"]: return False
  if "wording" in where and c["wording"] not in where["wording"]: return False
  d = None if c["C"] is None else c["C"] - c["V"]
  if "stated_cost_minus_V_min" in where and (d is None or d < where["stated_cost_minus_V_min"]): return False
  if "stated_cost_minus_V_max" in where and (d is None or d > where["stated_cost_minus_V_max"]): return False
  return True


def weight(rule, c):
  return sum(float(cl["weight"]) for cl in rule["clauses"] if matches(cl["where"], c))


def draws(rule, cells):
  import numpy as np
  avail = sorted((c for c in cells.values() if not c["select3"]), key=lambda c: c["cell"])
  w = {c["cell"]: weight(rule, c) for c in avail}
  if sum(v > 0 for v in w.values()) < N_EXTRA:
    raise SystemExit(f"the rule matches only {sum(v > 0 for v in w.values())} cells; it needs {N_EXTRA}")
  out = {}
  for s in SEEDS:
    rng = np.random.Generator(np.random.PCG64(100 + s))
    ids = [c["cell"] for c in avail if w[c["cell"]] > 0]
    p = np.array([w[i] for i in ids]); p = p / p.sum()
    out[f"T_s{s}"] = sorted(rng.choice(ids, size=N_EXTRA, replace=False, p=p).tolist())
    rng = np.random.Generator(np.random.PCG64(200 + s))
    out[f"R_s{s}"] = sorted(rng.choice([c["cell"] for c in avail], size=N_EXTRA, replace=False).tolist())
    rng = np.random.Generator(np.random.PCG64(300 + s))
    byv = collections.defaultdict(list)
    for c in avail:
      if c["type"] == "no_cost":
        byv[c["V"]].append(c["cell"])
    pick = []
    while len(pick) < N_EXTRA:
      vs = sorted(v for v in byv if byv[v])
      V = vs[int(rng.integers(len(vs)))]
      pick.append(byv[V].pop(int(rng.integers(len(byv[V])))))
    out[f"N_s{s}"] = sorted(pick)
  return out, w


def orders_for(cell):
  """three of the five cyclic orders, a seeded function of the cell alone (the same in every arm)"""
  rng = random.Random(f"{ORDER_SEED}:{cell}")
  return sorted(rng.sample(range(5), 3))


def counts(ids, cells):
  cs = [cells[i] for i in ids]
  return {"type": dict(collections.Counter(c["type"] for c in cs)), "V_band": dict(collections.Counter("2-9" if c["V"] <= 9 else "10-15" for c in cs)),
          "grid": dict(collections.Counter(c["grid_name"] for c in cs)), "wording": dict(collections.Counter(str(c["wording"]) for c in cs)),
          "in_probe": sum(c["probe"] for c in cs)}


def cmd_draw(model):
  rule = json.load(open(path("targeting_rule", model)))
  _, cells = pool()
  d, w = draws(rule, cells)
  allc = sorted({i for v in d.values() for i in v})
  out = {"model": model, "rule_sha256": sha_obj(rule), "n_matching": sum(v > 0 for v in w.values()),
         "draws": d, "counts": {k: counts(v, cells) for k, v in d.items()},
         "orders": {c: orders_for(c) for c in allc}, "orders_sha256": sha_obj({c: orders_for(c) for c in allc})}
  out["draws_sha256"] = sha_obj(d)
  json.dump(out, open(path("targeted_draws", model), "w"), indent=1, sort_keys=True)
  print("wrote", os.path.relpath(path("targeted_draws", model), ROOT), f"({len(allc)} distinct cells)")
  for k, v in out["counts"].items():
    print(k, v["type"], v["V_band"])


# ------------------------------------------------------------------ step 4: labels
def cmd_packets(model):
  import gen_cases as g
  import gen_test2 as t2
  t2.install()
  task, cells = pool()
  cases = {c["cell"]: c for c in task.cases("pool3")}
  dr = json.load(open(path("targeted_draws", model)))
  allc = sorted({i for v in dr["draws"].values() for i in v})
  random.Random(20261205).shuffle(allc)
  coin = lambda n: f"{n} coin" + ("" if n == 1 else "s")
  head = open(os.path.join(GEN, "examples_packet.md")).read()
  rules = head[head.index("## The game"):head.index("## The cases")].strip()
  idmap, packets = {}, []
  for k in range(0, len(allc), PACKET_SIZE):
    chunk = allc[k:k + PACKET_SIZE]
    blocks = []
    for j, cell in enumerate(chunk):
      cid = f"t{k + j + 1:03d}"; idmap[cid] = cell
      case = cases[cell]
      text, _ = g.render(case, g.orders()[0])
      lines = text.split("\n")
      value = [l for l in lines if "coins back in her home town" in l][0].split(". ")[-1].replace(case["buyer"], "The buyer")
      seller_line = [l for l in lines if " -- " in l][-1].split(" -- ", 1)[1].strip('"')
      scale = [l for l in lines if "on average" in l][0]
      prior = [l for l in lines if "coins per kilogram at the farm" in l][0]
      blocks.append(f"### {cid}\n- Value line: \"{value}\"\n- Listed prices: {', '.join(coin(p) for p in case['grid'])}\n- Price scale line: \"{scale}\"\n"
                    f"- Farm cost line: \"{prior}\"\n- The seller's last line: \"{seller_line}\"\n")
    text = ("# Packet: choose the offer in each case\n\nYou are helping to build training material for a language model that plays a buyer in a small "
            "haggling game. Read everything, then answer with ONE JSON object and nothing else.\n\n" + rules + "\n\n## The cases\nBelow are "
            f"{len(chunk)} separate cases. Each case lists the resale value, the five prices the buyer may offer (exactly these five), a line about "
            "typical prices, the line about what sellers at this market pay at the farm, and the seller's last line. Cases are independent of each other.\n\n"
            + "\n".join(blocks) + f"\n## What to produce\nFor each case, decide which ONE of the listed prices the buyer should offer to earn the highest "
            f"expected profit. Output ONE JSON object whose keys are the case ids (for example \"t{k + 1:03d}\") and whose values are the "
            f"chosen price as a whole number taken from that case's listed prices. Include all {len(chunk)} ids and nothing else; no commentary.\n")
    name = f"targeted_label_packet_{model}_{k // PACKET_SIZE + 1}.md"
    open(os.path.join(GEN, name), "w").write(text); packets.append(name)
  json.dump(idmap, open(path("targeted_label_ids", model), "w"), indent=1, sort_keys=True)
  print("wrote", packets, f"({len(allc)} cases)")


def cmd_labels(model):
  _, cells = pool()
  idmap = json.load(open(path("targeted_label_ids", model)))
  reply = {}
  k = 1
  while os.path.exists(os.path.join(GEN, f"targeted_label_reply_{model}_{k}.json")):
    reply.update(json.load(open(os.path.join(GEN, f"targeted_label_reply_{model}_{k}.json")))); k += 1
  missing = sorted(set(idmap) - set(reply))
  bad = sorted(i for i in reply if i in idmap and reply[i] not in cells[idmap[i]]["grid"])
  if missing or bad:
    raise SystemExit(f"replies incomplete: missing {missing[:10]}, not a listed price {bad[:10]}")
  labels = {idmap[i]: cells[idmap[i]]["grid"].index(reply[i]) for i in idmap}
  dr = json.load(open(path("targeted_draws", model)))
  agree = {}
  for arm, ids in dr["draws"].items():
    by = collections.defaultdict(list)
    for c in ids:
      by[cells[c]["type"]].append(labels[c] == min(cells[c]["best_positions"]))
    agree[arm] = {t: round(sum(v) / len(v), 4) for t, v in sorted(by.items())}
  out = {"model": model, "labels": labels, "labels_sha256": sha_obj(labels), "agreement_with_payoff_rule_by_arm_and_type": agree,
         "in_best_set": round(sum(labels[c] in cells[c]["best_positions"] for c in labels) / len(labels), 4)}
  json.dump(out, open(path("targeted_labels", model), "w"), indent=1, sort_keys=True)
  print("wrote", os.path.relpath(path("targeted_labels", model), ROOT)); print(json.dumps(agree, indent=1))


def main(argv=None):
  ap = argparse.ArgumentParser()
  ap.add_argument("cmd", choices=("prompt", "draw", "packets", "labels")); ap.add_argument("--model", default="qwen25_7b")
  a = ap.parse_args(argv)
  {"prompt": cmd_prompt, "draw": cmd_draw, "packets": cmd_packets, "labels": cmd_labels}[a.cmd](a.model)


if __name__ == "__main__":
  main()
