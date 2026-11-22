"""Builds demo/gen/teacher_packet.md from TRAIN cells only (CPU). Shows the game rules in words, the prompt template once, and for
40 high-regret and 10 low-regret train cells the lines that differ between cases plus plain Gemma's order-averaged offer
distribution. It does not show best offers, regrets, any method paragraph or any earlier result; high/low is not labelled."""
import json, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
import gen_cases as g

cells = {c["cell"]: c for c in json.load(open(os.path.join(g.OUT, "cells.json")))["cells"]}
cases = {c["cid"]: c for c in map(json.loads, open(os.path.join(g.OUT, "cases.jsonl")))}
rows = [json.loads(l) for l in open(os.path.join(common.ROOT, "demo_out", "gen_plain_scores.jsonl"))]
by = {}
for r in rows:
  if r["split"] == "train":
    by.setdefault(r["cell"], []).append(r)
score = {k: sum(x["soft_regret"] for x in v) / len(v) for k, v in by.items()}
order = sorted(score, key=lambda k: -score[k])
rng = random.Random(20261123)
high = order[:40]
low = rng.sample(order[-75:], 10)                 # the lowest quarter of train cells
chosen = high + low
rng.shuffle(chosen)
coin = lambda n: f"{n} coin" + ("" if n == 1 else "s")


def show(name, i):
  c = cells[name]
  case = cases[f"{name}-n0"]
  text, _ = g.render(case, g.orders()[0])
  lines = text.split("\n")
  keep = [l for l in lines if "coins per kilogram at the farm" in l or "coins back in her home town" in l or "on average" in l]
  obs = [l for l in lines if " -- " in l][-1]
  sale = [l for l in lines if "coins back in her home town" in l][0].split(". ")[-1].replace(case["buyer"], "The buyer")
  seller_line = obs.split(' -- ')[1].strip('"')
  prior = [l for l in lines if "coins per kilogram at the farm" in l][0]
  scale = [l for l in lines if "on average" in l][0]
  probs = [sum(r["probs"][j] for r in by[name]) / len(by[name]) for j in range(5)]
  dist = ", ".join(f"{coin(k)}: {100 * p:.0f}%" for k, p in zip(c["grid"], probs))
  return (f"### Case {i}\n- Value line: \"{sale}\"\n- Price scale line: \"{scale}\"\n- Farm cost line: \"{prior}\"\n- The seller's last line: \"{seller_line}\"\n"
          f"- Gemma's offer distribution (average over the five option orders): {dist}\n")


example = g.render(cases["V6-gB-information-C3-p1_5-w0-n0"] if "V6-gB-information-C3-p1_5-w0-n0" in cases else cases[next(iter(cases))], g.orders()[0])[0]
# the template example must not be a locked test case: take a train case
tr_case = next(c for c in cases.values() if c["split"] == "train" and c["line"] == "information")
example = g.render(tr_case, g.orders()[0])[0]
P = f"""# Packet for the teacher

You are helping to improve how a language model plays a buyer in a small haggling game. Read everything, then answer with ONE JSON object and nothing else.

## The game
A buyer wants to buy fruit from a seller and can resell it for a known value (in coins) in her home town. The buyer chooses one of five prices to offer; the five prices are shown as lettered options and may differ between cases (for example 1 to 5 coins or 3 to 7 coins). The seller accepts an offer if it is at or above the seller's own farm cost and refuses a lower offer. If the offer is accepted, the buyer's profit is the resale value minus the offer (it can be negative); if it is refused, the profit is zero. When the seller says what the fruit cost at the farm, that is true. When no cost is stated, the prompt says that every whole-number farm cost between two stated limits is equally likely. The buyer wants the highest expected profit.

## The prompt the language model sees (one example; the model sees only this text and answers with the letter of an option)
```
{example}
```
The numbers, the price options, the farm-cost limits and the seller's last line change from case to case.

## What the language model did (from its first-token letter probabilities, averaged over five random orders of the options)
Below are {len(chosen)} cases. For each, the lines of the prompt that differ between cases, and how often the model chose each price. Some cases are ones it handles well and some are not; they are not labelled.

""" + "\n".join(show(n, i + 1) for i, n in enumerate(chosen)) + """

## What to produce
Study where the model's behaviour departs from what would earn the buyer the most. Then write ONE JSON object with exactly two keys:
- "diagnosis": two to four sentences about what the model gets wrong and why you think so.
- "method": ONE paragraph of at most 150 words, written as notes to the buyer, that would be placed in the buyer's notes before the question and that teaches how to choose the offer. Rules for the paragraph: no digits at all (write any number as a word or avoid numbers), no reference to the cases above or to any particular case, no names, and it must make sense for any resale value, any set of five prices and any farm-cost limits.

Output only the JSON object.
"""
open(os.path.join(g.OUT, "teacher_packet.md"), "w").write(P)
print(len(P), "chars;", len(chosen), "cases;", "high:", len(high), "low:", len(low))
