"""Text rows on generated TRAIN and TUNE cells (GPU): original method paragraph, teacher method, same-length neutral text, wrong
rule. Plain comes from demo_out/gen_plain_scores.jsonl. Refuses any split but train/tune. Resumable.
  python demo/gen_textrows.py            -> demo_out/gen_text_rows.jsonl"""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import common
import gen_cases as g
import gen_notes
import textrows
from refimpl import core, phase3, runtime
from refimpl.local_gemma2 import LocalGemma2

OUT = os.path.join(common.ROOT, "demo_out", "gen_text_rows.jsonl")
ROWS = tuple(sys.argv[1:]) or ("method_original", "teacher", "neutral", "wrong_rule")


def row_texts():
  return {"method_original": textrows.METHOD, "teacher": open(os.path.join(g.OUT, "teacher_method.txt")).read().strip(),
          "neutral": open(os.path.join(g.OUT, "neutral_text.txt")).read().strip(), "wrong_rule": textrows.FIXED["wrong_rule"]}


def main():
  texts = row_texts()
  cases = [json.loads(l) for l in open(os.path.join(g.OUT, "cases.jsonl"))]
  cases = [c for c in cases if c["split"] in ("train", "tune")]
  assert cases and all(c["split"] in ("train", "tune") for c in cases)
  cells = {c["cell"]: c for c in json.load(open(os.path.join(g.OUT, "cells.json")))["cells"]}
  done = {(r["row"], r["cid"]) for r in map(json.loads, open(OUT))} if os.path.exists(OUT) else set()
  model, tok = runtime.load_gemma("9b", "cuda")
  lm = LocalGemma2(model, tok)
  t0, n = time.time(), 0
  with open(OUT, "a") as f:
    for row in ROWS:
      for c in cases:
        if (row, c["cid"]) in done:
          continue
        lab = cells[c["cell"]]
        per, masses = [], []
        for order in g.orders():
          user, l2p = gen_notes.render_notes(c, order, texts[row])
          lm.letter_scores(user, phase3.LETTERS, whole_answer=False)
          pr = core.softmax_scores(dict(lm.last_first_token), l2p)
          masses.append(float(lm.last_letter_mass)); per.append([float(pr[k]) for k in c["grid"]])
        probs = np.mean(per, axis=0)
        f.write(json.dumps({"row": row, "cid": c["cid"], "cell": c["cell"], "split": c["split"], "probs": [float(x) for x in probs], "mass": float(np.mean(masses)),
                            "soft_regret": float(lab["best_payoff"] - np.dot(probs, lab["payoffs"])), "expected_offer": float(np.dot(probs, c["grid"]))}) + "\n")
        f.flush(); n += 1
        if n % 100 == 0:
          print(row, n, f"{time.time() - t0:.0f}s", flush=True)
  print("GEN TEXT ROWS DONE", flush=True)


if __name__ == "__main__":
  main()
