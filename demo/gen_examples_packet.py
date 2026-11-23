"""Builds demo/gen/examples_packet.md (CPU): the game rules of the original teacher packet, then the 100 LoRA TRAINING cases
(demo/gen/lora_train_cells.json, the fixed name variant of each) as blocks with an opaque id and the lines that differ
(resale value, the five listed prices, price scale, farm-cost limits, seller's last line). No best offers, regrets, Gemma outputs,
paragraphs or earlier results. Ids are shuffled opaque ids (c001...), so the id carries no label information; the map from ids to
case ids is written to demo/gen/examples_id_map.json (not shown to the teacher)."""
import json, os, random, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_cases as g

cases = {c["cid"]: c for c in map(json.loads, open(os.path.join(g.OUT, "cases.jsonl")))}
spec = json.load(open(os.path.join(g.OUT, "lora_train_cells.json")))
cids = [f"{k}-n{v['name_variant']}" for k, v in spec.items()]
assert len(cids) == 100 and all(cases[c]["split"] == "train" for c in cids)
rng = random.Random(20261126)
rng.shuffle(cids)
ids = {f"c{i + 1:03d}": cid for i, cid in enumerate(cids)}
orig = open(os.path.join(g.OUT, "teacher_packet.md")).read()
rules = orig[orig.index("## The game"):orig.index("## The prompt the language model sees")].strip()
coin = lambda n: f"{n} coin" + ("" if n == 1 else "s")


def block(i, cid):
  case = cases[cid]
  text, _ = g.render(case, g.orders()[0])
  lines = text.split("\n")
  obs = [l for l in lines if " -- " in l][-1]
  value = [l for l in lines if "coins back in her home town" in l][0].split(". ")[-1].replace(case["buyer"], "The buyer")
  seller_line = obs.split(" -- ", 1)[1].strip('"')
  scale = [l for l in lines if "on average" in l][0]
  prior = [l for l in lines if "coins per kilogram at the farm" in l][0]
  for bad in (case["buyer"], case["seller"], case["buyer"].split()[0], case["seller"].split()[0]):
    assert bad not in value + seller_line + scale + prior, (cid, bad)
  return (f"### {i}\n- Value line: \"{value}\"\n- Listed prices: {', '.join(coin(p) for p in case['grid'])}\n- Price scale line: \"{scale}\"\n"
          f"- Farm cost line: \"{prior}\"\n- The seller's last line: \"{seller_line}\"\n")


P = f"""# Packet: choose the offer in each case

You are helping to build training material for a language model that plays a buyer in a small haggling game. Read everything, then answer with ONE JSON object and nothing else.

{rules}

## The cases
Below are {len(ids)} separate cases. Each case lists the resale value, the five prices the buyer may offer (exactly these five), a line about typical prices, the line about what sellers at this market pay at the farm, and the seller's last line. Cases are independent of each other.

""" + "\n".join(block(i, cid) for i, cid in ids.items()) + f"""

## What to produce
For each case, decide which ONE of the listed prices the buyer should offer to earn the highest expected profit. Output ONE JSON object whose keys are the case ids (for example "c001") and whose values are the chosen price as a whole number taken from that case's listed prices (for example 4). Include all {len(ids)} ids and nothing else; no commentary.
"""
json.dump(ids, open(os.path.join(g.OUT, "examples_id_map.json"), "w"), indent=1)
open(os.path.join(g.OUT, "examples_packet.md"), "w").write(P)
print(len(P), "chars", len(ids), "cases")
