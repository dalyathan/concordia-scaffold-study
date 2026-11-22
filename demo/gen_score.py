"""Score PLAIN Gemma 2 9B-it on generated cases (first-token letter probabilities at P1, renormalised over the five
letters, five cyclic option orders). TRAIN and TUNE ONLY: the script refuses any other split (test sets are not scored
here). GPU; one model; resumable (skips cids already in the output).

  python demo/gen_score.py            writes demo_out/gen_plain_scores.jsonl
"""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import common
import gen_cases as g
from refimpl import core, phase3, runtime
from refimpl.local_gemma2 import LocalGemma2

ALLOWED = ("train", "tune")
OUT = os.path.join(common.ROOT, "demo_out", "gen_plain_scores.jsonl")


def main():
  cases = [json.loads(l) for l in open(os.path.join(g.OUT, "cases.jsonl"))]
  cells = {c["cell"]: c for c in json.load(open(os.path.join(g.OUT, "cells.json")))["cells"]}
  cases = [c for c in cases if c["split"] in ALLOWED]
  assert cases and all(c["split"] in ALLOWED for c in cases), "refusing to score a test split"
  done = {json.loads(l)["cid"] for l in open(OUT)} if os.path.exists(OUT) else set()
  model, tok = runtime.load_gemma("9b", "cuda")
  lm = LocalGemma2(model, tok)
  t0 = time.time()
  with open(OUT, "a") as f:
    for n, c in enumerate(cases):
      if c["cid"] in done:
        continue
      lab = cells[c["cell"]]
      per, masses = [], []
      for order in g.orders():
        user, l2p = g.render(c, order)
        lm.letter_scores(user, phase3.LETTERS, whole_answer=False)
        first = dict(lm.last_first_token)
        masses.append(float(lm.last_letter_mass))
        pr = core.softmax_scores(first, l2p)
        per.append([float(pr[k]) for k in c["grid"]])
      probs = np.mean(per, axis=0)
      pay = lab["payoffs"]
      row = {"cid": c["cid"], "cell": c["cell"], "split": c["split"], "probs": [float(x) for x in probs], "per_order": per,
             "mass": float(np.mean(masses)), "soft_regret": float(lab["best_payoff"] - np.dot(probs, pay)),
             "hard_regret": float(lab["best_payoff"] - pay[int(np.argmax(probs))]), "top_position": int(np.argmax(probs)),
             "expected_offer": float(np.dot(probs, c["grid"]))}
      f.write(json.dumps(row) + "\n"); f.flush()
      if n % 25 == 0:
        print(n, len(cases), f"{time.time() - t0:.0f}s", flush=True)
  print("GEN SCORE DONE", flush=True)


if __name__ == "__main__":
  main()
