"""Step 2 GPU job (plain model only). Writes:
  demo_out/plain_per_order.jsonl  per case: per-order first-token log-probs of the
                                  five letters (the saved run kept only averages;
                                  this rescore is checked against it)
  demo_out/say.jsonl              greedy free-text answer and parsed offer per case
  demo/dial_cost.json             cost dial on 6 development cases
  demo_out/reworded_cases.jsonl   plain scoring with the reworded scaffold"""
import argparse, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
import scoring
from refimpl import core, demo, runtime
from refimpl.local_gemma2 import LocalGemma2

ap = argparse.ArgumentParser()
ap.add_argument("--model", default="9b")
ap.add_argument("--only-dial", action="store_true")
args = ap.parse_args()
t0 = time.time()
model, tok = runtime.load_gemma(args.model, "cuda")
lm = LocalGemma2(model, tok)
print(f"loaded in {time.time() - t0:.0f}s", flush=True)
prompts = demo.demo_prompts()
saved = {c["pid"]: c for c in common.load_cases()}
out = os.path.join(common.ROOT, "demo_out")

maxdiff = 0.0
if args.only_dial:
  prompts = []
with open(f"{out}/plain_per_order.jsonl", "a" if args.only_dial else "w") as f:
  for p in prompts:
    r = scoring.score(lm, p)
    maxdiff = max(maxdiff, max(abs(r.probs[k] - saved[p.pid]["probs"][str(k)]) for k in core.PRICES))
    f.write(json.dumps({"pid": p.pid, "orders": r.orders, "logp_letters": r.logp_letters}) + "\n")
print(f"plain rescore done; max |p - saved p| = {maxdiff:.3e}", flush=True)

with open(f"{out}/say.jsonl", "a" if args.only_dial else "w") as f:
  for p in prompts:
    t = time.perf_counter()
    text, k = scoring.say(lm, p)
    f.write(json.dumps({"pid": p.pid, "text": text, "offer": k, "sec": time.perf_counter() - t}) + "\n")
print("say done", flush=True)

# Six distinct prompts once the cost is overridden: distinct (variant, V); V + C odd (dev).
DIAL = [(15, 3, 2), (15, 4, 1), (15, 5, 2), (15, 6, 1), (16, 4, 3), (16, 6, 3)]
dial = {"cases": [], "settings": [1, 2, 3, 4, None]}
for v, V, C in DIAL:
  p = demo.DemoPrompt(v, V, "information", C)
  assert common.case_split(p) == "build"
  row = {"pid": p.pid, "V": V, "C": C, "dial": {}}
  for c in dial["settings"]:
    q = scoring.with_cost(p, c)
    r = scoring.score(lm, q)
    row["dial"][str(c)] = {"probs": r.probs, "top": r.top, "expected": r.expected(),
                           "best": core.oracle_bids(q), "hard_regret": core.hard_regret(q, r.top)}
  dial["cases"].append(row)
json.dump(dial, open(os.path.join(common.DEMO_DIR, "dial_cost.json"), "w"), indent=1)
print("dial done", flush=True)

if args.only_dial:
  print("DIAL ONLY COMPLETED", flush=True)
  sys.exit(0)
with open(f"{out}/reworded_cases.jsonl", "w") as f:
  for p in prompts:
    r = scoring.score(lm, p, reword=True)
    hr, sr = scoring.regret(p, r)
    f.write(json.dumps({"pid": p.pid, "probs": r.probs, "top": r.top, "expected": r.expected(),
                        "hard_regret": hr, "soft_regret": sr, "mass": r.mass}) + "\n")
print("STEP 2 JOB COMPLETED", flush=True)
