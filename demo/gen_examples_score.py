"""Scores Claude's example labels against the oracle (CPU) and freezes them as demo/gen/claude_labels.json. No label is corrected.
  python demo/gen_examples_score.py check   -> lists ids that are missing or not a listed price (for the one allowed re-ask)
  python demo/gen_examples_score.py freeze  -> accuracy and regret by case type; writes claude_labels.json (+ sha256) and demo_out/gen_examples_labels.md
Reply file: demo/gen/examples_reply.json (verbatim) and optionally demo/gen/examples_reply_reask.json (verbatim, for missing/invalid ids only)."""
import hashlib, json, os, re, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import common
import gen_cases as g

cells = {c["cell"]: c for c in json.load(open(os.path.join(g.OUT, "cells.json")))["cells"]}
cases = {c["cid"]: c for c in map(json.loads, open(os.path.join(g.OUT, "cases.jsonl")))}
idmap = json.load(open(os.path.join(g.OUT, "examples_id_map.json")))


def parse(path):
  txt = open(path).read()
  m = re.search(r"\{.*\}", txt, re.S)
  return json.loads(m.group(0)) if m else {}


def merged():
  out, src = {}, {}
  for name in ("examples_reply.json", "examples_reply_reask.json"):
    p = os.path.join(g.OUT, name)
    if os.path.exists(p):
      for k, v in parse(p).items():
        if k not in out or not valid(k, out[k]):          # a re-ask only fills ids that were missing or invalid
          out[k], src[k] = v, name
  return out, src


def valid(i, v):
  return i in idmap and isinstance(v, int) and not isinstance(v, bool) and v in cases[idmap[i]]["grid"]


def bad_ids():
  lab, _ = merged()
  return [i for i in idmap if i not in lab or not valid(i, lab[i])]


if sys.argv[1] == "check":
  print("missing or invalid:", bad_ids())
  sys.exit(0)

lab, src = merged()
bad = bad_ids()
labels = {}
for i, cid in idmap.items():
  if i in lab and valid(i, lab[i]):
    labels[cid] = {"id": i, "price": int(lab[i]), "position": cases[cid]["grid"].index(int(lab[i])), "source": src[i]}
rows = []
for cid, d in labels.items():
  c = cells[cases[cid]["cell"]]
  rows.append({"cid": cid, "type": c["type"], "regret": c["best_payoff"] - c["payoffs"][d["position"]], "hit": d["position"] in c["best_positions"],
               "cheapest": d["position"] == 0})
out = {"labels": labels, "unusable_ids": bad, "n_labels": len(labels)}
json.dump(out, open(os.path.join(g.OUT, "claude_labels.json"), "w"), indent=1, sort_keys=True)
sha = hashlib.sha256(open(os.path.join(g.OUT, "claude_labels.json"), "rb").read()).hexdigest()
L = ["# Claude's example labels vs the oracle (100 LoRA training cases; no label corrected)", "", f"claude_labels.json sha256 {sha}; usable labels {len(labels)} of {len(idmap)}; unusable ids after at most one re-ask: {bad}", "",
     "| Type | n | accuracy (label is an oracle-best price) | mean regret | share labelled cheapest |", "| --- | --- | --- | --- | --- |"]
for t in (None,) + tuple(g.TYPES):
  r = [x for x in rows if t is None or x["type"] == t]
  if r:
    L.append(f"| {t or 'all'} | {len(r)} | {np.mean([x['hit'] for x in r]):.2f} | {np.mean([x['regret'] for x in r]):.3f} | {np.mean([x['cheapest'] for x in r]):.2f} |")
open(os.path.join(common.ROOT, "demo_out", "gen_examples_labels.md"), "w").write("\n".join(L) + "\n")
print("\n".join(L))
