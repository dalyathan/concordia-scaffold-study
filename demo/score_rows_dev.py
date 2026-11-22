"""Score the method, neutral and wrong_rule text rows on the build-variant development
cases (variants 15-16), which step 4 did not score, so that every LoRA baseline
exists on the train and held-out tune cells. Writes demo_out/text_rows_build.jsonl."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common, scoring, textrows
from refimpl import runtime
from refimpl.local_gemma2 import LocalGemma2

model, tok = runtime.load_gemma("9b", "cuda")
lm = LocalGemma2(model, tok)
with open(os.path.join(common.ROOT, "demo_out", "text_rows_build.jsonl"), "w") as f:
  for p in common.cases_in("build"):
    for name in ("method", "neutral", "wrong_rule"):
      r = scoring.score(lm, p, notes=textrows.row_text(name, p))
      hr, sr = scoring.regret(p, r)
      f.write(json.dumps({"pid": p.pid, "row": name, "probs": r.probs, "top": r.top, "expected": r.expected(),
                          "hard_regret": hr, "soft_regret": sr, "mass": r.mass, "sec": r.sec}) + "\n")
print("ROWS DEV COMPLETED", flush=True)
