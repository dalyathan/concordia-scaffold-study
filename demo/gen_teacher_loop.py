"""Closed teacher loop on SELECTION cells only (never tune or test; no best offers).

  python demo/gen_teacher_loop.py packet --round K    writes demo/gen/loop/round_K_packet.md from the original packet + the current
                                                      paragraph + Gemma's in-prompt results with it on the 42 selection cells
  python demo/gen_teacher_loop.py score --round K     GPU: scores demo/gen/loop/round_K_method.txt in the prompt on the selection cells
                                                      (name variant 0, five orders) -> demo/gen/loop/round_K_scores.jsonl
  python demo/gen_teacher_loop.py summary             per-round selection soft regret by type, winner, stop decision
Round 0 is the frozen first paragraph (demo/gen/teacher_method.txt, scored in demo_out/gen_text_rows.jsonl). The paragraph checked for round K>0
(no digits, <= 150 words, no names, no 'case' references) is in round_K_method.txt, the verbatim reply in round_K_reply.json."""
import argparse, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import common
import gen_cases as g
import gen_notes

LOOP = os.path.join(g.OUT, "loop")
SEL = json.load(open(os.path.join(g.OUT, "lora_select_cells.json")))
cells = {c["cell"]: c for c in json.load(open(os.path.join(g.OUT, "cells.json")))["cells"]}
cases = {c["cid"]: c for c in map(json.loads, open(os.path.join(g.OUT, "cases.jsonl")))}
# SEL = loop set A (feedback and winner choice). It must be train cells, disjoint from the LoRA training cells, the LoRA selection set B and tune.
B = set(json.load(open(os.path.join(g.OUT, "lora_select_cells_B.json"))))
TRAINED = set(json.load(open(os.path.join(g.OUT, "lora_train_cells.json"))))
PACKET = set(json.load(open(os.path.join(g.OUT, "packet_cells.json"))))        # the 50 cells shown in the original packet
assert all(cells[k]["split"] == "train" for k in SEL)
assert not set(SEL) & TRAINED and not set(SEL) & B and len(SEL) == 42
assert not B & TRAINED and not B & PACKET
SHOW = [k for k in SEL if k not in PACKET]                                        # displayed cases exclude cells the teacher saw in Part 1
coin = lambda n: f"{n} coin" + ("" if n == 1 else "s")


def paragraph(k):
  if k == 0:
    return open(os.path.join(g.OUT, "teacher_method_v1.txt" if os.path.exists(os.path.join(g.OUT, "teacher_method_v1.txt")) else "teacher_method.txt")).read().strip()
  return open(os.path.join(LOOP, f"round_{k}_method.txt")).read().strip()


def results(k):
  """{cid: {'probs': [...], 'soft_regret': x}} for the selection cells with round k's paragraph"""
  if k == 0 and not os.path.exists(os.path.join(LOOP, "round_0_scores.jsonl")):
    out = {}
    for r in map(json.loads, open(os.path.join(common.ROOT, "demo_out", "gen_text_rows.jsonl"))):
      if r["row"] in ("teacher", "teacher_v1") and r["cid"] in {f"{c}-n0" for c in SEL} and r["cid"] not in out:
        out[r["cid"]] = r
    return out
  return {r["cid"]: r for r in map(json.loads, open(os.path.join(LOOP, f"round_{k}_scores.jsonl")))}


def decide(k):
  """Pre-registered rule: the incumbent (start: pass 0) is replaced by pass k only if the soft regret on the 42 loop cells improves by at least 0.02
  AND by more than one paired standard error (paired over cells). The loop stops at the first pass that does not replace the incumbent (ties keep
  the incumbent) and after pass 3."""
  st = state()
  inc = st["incumbent"]
  a, b = results(inc), results(k)
  d = np.array([np.mean([a[f"{c}-n0"]["soft_regret"] for c in [key]]) - b[f"{key}-n0"]["soft_regret"] for key in SEL])
  mean, se = float(d.mean()), float(d.std(ddof=1) / np.sqrt(len(d)))
  replace = mean >= 0.02 and mean > se
  rec = {"round": k, "incumbent": inc, "improvement": mean, "paired_se": se, "replaced": bool(replace), "by_type": by_type(b)}
  st["history"].append(rec)
  if replace:
    st["incumbent"] = k
  st["stop"] = (not replace) or k >= 3
  os.makedirs(LOOP, exist_ok=True)
  json.dump(st, open(STATE, "w"), indent=1)
  print(json.dumps(rec, indent=1), "STOP" if st["stop"] else "CONTINUE", "incumbent:", st["incumbent"])


def by_type(res):
  d = {t: [] for t in g.TYPES}
  for k in SEL:
    d[cells[k]["type"]].append(res[f"{k}-n0"]["soft_regret"])
  allv = [x for v in d.values() for x in v]
  return {t: float(np.mean(v)) for t, v in d.items()} | {"all": float(np.mean(allv))}


def case_block(i, k, res):
  c = cases[f"{k}-n0"]
  text, _ = g.render(c, g.orders()[0])
  lines = text.split("\n")
  sale = [l for l in lines if "coins back in her home town" in l][0].split(". ")[-1].replace(c["buyer"], "The buyer")
  scale = [l for l in lines if "on average" in l][0]
  prior = [l for l in lines if "coins per kilogram at the farm" in l][0]
  seller_line = [l for l in lines if " -- " in l][-1].split(" -- ")[1].strip('"')
  dist = ", ".join(f"{coin(p)}: {100 * q:.0f}%" for p, q in zip(c["grid"], res[c["cid"]]["probs"]))
  return (f"### Case {i}\n- Value line: \"{sale}\"\n- Price scale line: \"{scale}\"\n- Farm cost line: \"{prior}\"\n- The seller's last line: \"{seller_line}\"\n"
          f"- Gemma's offer distribution WITH your paragraph in its notes (average over the five option orders): {dist}\n")


STATE = os.path.join(LOOP, "state.json")


def state():
  return json.load(open(STATE)) if os.path.exists(STATE) else {"incumbent": 0, "history": []}


def packet(k):
  orig = open(os.path.join(g.OUT, "teacher_packet.md")).read()
  inc = state()["incumbent"]
  res = results(inc)
  tp = by_type(res)
  rng = np.random.Generator(np.random.PCG64(1000 + k))
  order = list(rng.permutation(len(SHOW)))
  body = "\n".join(case_block(i + 1, SHOW[j], res) for i, j in enumerate(order))
  P = f"""# Revision packet (read everything, then answer with ONE JSON object and nothing else)

Part 1 is the original task you were given. Part 2 shows the current paragraph and what the language model actually did when that paragraph was placed in its notes.

## Part 1: the original packet
{orig}

## Part 2: the current paragraph and its effect
The paragraph that was placed in the language model's notes, before the question, in the cases below:

\"\"\"{paragraph(inc)}\"\"\"

Over {len(SEL)} cases of the same kind, with that paragraph in its notes, the language model's average expected loss compared with the best possible offer ("soft regret"; lower is better, zero is perfect) was: {tp['all']:.3f} over all cases; {tp['below']:.3f} where the seller states a cost below the resale value; {tp['at_or_above']:.3f} where the stated cost is at or above the resale value; {tp['no_cost']:.3f} where no cost is stated.

Below are {len(SHOW)} of those cases (none of them is a case of Part 1), with how often the model chose each price:

{body}
## What to produce now
Revise the paragraph. This is a small model (about nine billion parameters) and it often does not follow long or abstract instructions; write for what it can actually follow: short plain sentences, one clear step at a time, concrete rather than general. The same constraints apply: at most 150 words, no digits at all, no reference to the cases above or to any particular case, no names, and it must make sense for any resale value, any set of five prices and any farm-cost limits. Output ONE JSON object with exactly two keys: "diagnosis" (two to four sentences on why the model still falls short of the best offers and what your revision changes) and "method" (the revised paragraph).
"""
  os.makedirs(LOOP, exist_ok=True)
  open(os.path.join(LOOP, f"round_{k}_packet.md"), "w").write(P)
  print(k, len(P), "chars")


def check(text):
  bad = []
  if re.search(r"\d", text): bad.append("digit")
  if len(text.split()) > 150: bad.append("over 150 words")
  if re.search(r"\bcase\b|\bcases\b", text, re.I): bad.append("case reference")
  old = set(__import__("refimpl.core", fromlist=["core"]).FEMALE_NAMES) | set(__import__("refimpl.core", fromlist=["core"]).MALE_NAMES)
  if any(w in text for w in {n.split()[0] for n in old} | {n.split()[1] for n in old}): bad.append("old name")
  pool = g.names_pool()
  if any(n.split()[0] in text or n.split()[1] in text for side in (0, 1) for part in pool.values() for n in part[side][:60]): bad.append("name")
  return bad


def score(k):
  from refimpl import core, phase3, runtime
  from refimpl.local_gemma2 import LocalGemma2
  text = paragraph(k)
  bad = check(text)
  assert not bad, f"paragraph fails the checks: {bad}"
  out = os.path.join(LOOP, f"round_{k}_scores.jsonl")
  assert not os.path.exists(out), f"{out} exists; refusing to overwrite"
  if k > 0:
    assert json.load(open(os.path.join(LOOP, f"round_{k}_reply.json")))["method"].strip() == text, "round reply and method.txt differ"
  model, tok = runtime.load_gemma("9b", "cuda")
  lm = LocalGemma2(model, tok)
  with open(out, "w") as f:
    for key in SEL:
      c = cases[f"{key}-n0"]
      per = []
      for order in g.orders():
        user, l2p = gen_notes.render_notes(c, order, text)
        lm.letter_scores(user, phase3.LETTERS, whole_answer=False)
        pr = core.softmax_scores(dict(lm.last_first_token), l2p)
        per.append([float(pr[x]) for x in c["grid"]])
      probs = np.mean(per, axis=0)
      lab = cells[key]
      f.write(json.dumps({"cid": c["cid"], "probs": [float(x) for x in probs], "soft_regret": float(lab["best_payoff"] - np.dot(probs, lab["payoffs"]))}) + "\n")
  print("scored round", k)


def summary():
  rows = []
  k = 0
  while True:
    try:
      res = results(k)
    except FileNotFoundError:
      break
    if len(res) < len(SEL):
      break
    rows.append((k, by_type(res)))
    k += 1
  best = min(rows, key=lambda r: r[1]["all"])
  print(json.dumps({"rounds": rows, "winner_round": best[0], "winner_all": best[1]["all"]}, indent=1))


if __name__ == "__main__":
  ap = argparse.ArgumentParser()
  ap.add_argument("cmd", choices=("packet", "score", "decide", "summary"))
  ap.add_argument("--round", type=int, default=1)
  a = ap.parse_args()
  {"packet": lambda: packet(a.round), "score": lambda: score(a.round), "decide": lambda: decide(a.round), "summary": summary}[a.cmd]()
