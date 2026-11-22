"""Step 4 GPU job: text rows on the tuning cases only.
Writes demo/text_rows.json (frozen row texts), demo_out/text_rows_tuning.jsonl and
demo_out/acts_rows.pt ({row: {pid: [layers, hidden]}} for plain, method, neutral)."""
import argparse, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import torch
import common, scoring, textrows
from refimpl import conditions, core, runtime
from refimpl.local_gemma2 import LocalGemma2

ap = argparse.ArgumentParser()
ap.add_argument("--model", default="9b")
args = ap.parse_args()
model, tok = runtime.load_gemma(args.model, "cuda")
lm = LocalGemma2(model, tok)
n_tok = lambda t: conditions.n_tokens(t, tok)
check = textrows.check_method()
assert check["ok"], check
neutral = conditions.qa_filler(scoring.OPENINGS, n_tok(textrows.METHOD), tok)
tuning = common.cases_in("tuning")
rows = {
  "plain": {"kind": "none", "text": None},
  "method": {"kind": "fixed", "text": textrows.METHOD, "tokens": n_tok(textrows.METHOD),
             "oracle_check": check},
  "neutral": {"kind": "fixed", "text": neutral, "tokens": n_tok(neutral),
              "note": "conditions.qa_filler cut to the method's token count"},
  **{k: {"kind": "fixed", "text": v, "tokens": n_tok(v)} for k, v in textrows.FIXED.items()},
  "template": {"kind": "per_case", "generator": "pairs_template.paragraph(p, min(best))",
               "texts": {p.pid: textrows.row_text("template", p) for p in tuning}},
  "answer_only": {"kind": "per_case", "note": "UPPER BOUND: names the best offer",
                  "generator": "core.answer_only(buyer, min(best))",
                  "texts": {p.pid: textrows.row_text("answer_only", p) for p in tuning}},
}
json.dump({"rows": rows, "order": list(textrows.ROWS)}, open(textrows.PATH, "w"), indent=1)
print("text_rows.json frozen", flush=True)
acts = {"plain": {}, "method": {}, "neutral": {}}
t0 = time.time()
with open(os.path.join(common.ROOT, "demo_out", "text_rows_tuning.jsonl"), "w") as f:
  for p in tuning:
    for name in textrows.ROWS:
      cap = name in acts
      r = scoring.score(lm, p, notes=textrows.row_text(name, p), capture=cap)
      hr, sr = scoring.regret(p, r)
      f.write(json.dumps({"pid": p.pid, "row": name, "probs": r.probs, "top": r.top,
                          "expected": r.expected(), "hard_regret": hr, "soft_regret": sr,
                          "mass": r.mass, "sec": r.sec}) + "\n")
      if cap:
        acts[name][p.pid] = r.acts.half()
    print(f"{p.pid} done ({time.time() - t0:.0f}s)", flush=True)
torch.save(acts, os.path.join(common.ROOT, "demo_out", "acts_rows.pt"))
print("STEP 4 JOB COMPLETED", flush=True)
