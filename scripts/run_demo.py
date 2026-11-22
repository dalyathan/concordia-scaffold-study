"""Demo baseline run: plain Gemma (no Notes block) on the 140 demo cases
(variants 15-18; refimpl/demo.py refuses 1-14).

For every case, phase3.score_prompt is run over the five cyclic option orders with
first-token probabilities at P1 (the P1 pass alone) and activation capture. Saved
per case (out/cases.jsonl): p(k) averaged over orders, the top offer (argmax of the
averaged p(k), ties to the lower price), the expected offer, the best offer(s) from
core.oracle_bids, hard regret of the top offer, soft regret, letter mass, and the
per-order top offers. out/p1_acts.pt holds {pid: float16 [n_layers, hidden]}: the
decision-token (P1) activation at every layer, averaged over the five orders.
Resumable: cases already in cases.jsonl are skipped (and their activations kept)."""
import argparse, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
import torch
from examples.modular.environment.modules import fruitville_haggling as fv
from refimpl import core, demo, phase3, runtime
from refimpl.local_gemma2 import LocalGemma2

ap = argparse.ArgumentParser()
ap.add_argument("--model", default="9b")
ap.add_argument("--out", default="demo_out")
args = ap.parse_args()
os.makedirs(args.out, exist_ok=True)
cases_path, acts_path = f"{args.out}/cases.jsonl", f"{args.out}/p1_acts.pt"
done = {json.loads(l)["pid"] for l in open(cases_path)} if os.path.exists(cases_path) else set()
acts = torch.load(acts_path) if os.path.exists(acts_path) and done else {}
t0 = time.time()
model, tok = runtime.load_gemma(args.model, "cuda")
lm = LocalGemma2(model, tok, sequential=True)
openings = list(fv.VISUAL_SCENE_OPENINGS)
prompts = demo.demo_prompts()
print(f"loaded {args.model} in {time.time() - t0:.0f}s; {len(prompts)} cases, {len(done)} done",
      flush=True)
torch.cuda.reset_peak_memory_stats()
times = []
for i, p in enumerate(prompts):
  if p.pid in done:
    continue
  t = time.perf_counter()
  dists, masses, tops, layer_acts = [], [], [], []
  for order in core.cyclic_orders():
    probs, hard, store, _ = phase3.score_prompt(lm, p, openings[p.opening_index], None, order,
                                                capture=True, whole_answer=False)
    dists.append(probs); masses.append(lm.last_letter_mass); tops.append(hard)
    layer_acts.append(torch.stack([store[L]["P1"].float() for L in sorted(store)]))
  mean_p = {k: float(np.mean([d[k] for d in dists])) for k in core.PRICES}
  top = max(core.PRICES, key=lambda k: (mean_p[k], -k))
  rec = {"pid": p.pid, "variant": p.variant, "V": p.V, "line": p.line, "C": p.C,
         "buyer": p.buyer, "seller": p.seller, "probs": mean_p, "top_offer": top,
         "expected_offer": core.expected_bid(mean_p), "best_offers": core.oracle_bids(p),
         "best_payoff": core.oracle_payoff(p), "hard_regret": core.hard_regret(p, top),
         "soft_regret": core.soft_regret(p, mean_p), "direction": demo.offer_direction(p, top),
         "letter_mass": float(np.mean(masses)), "top_offer_by_order": tops,
         "sec": time.perf_counter() - t}
  acts[p.pid] = torch.stack(layer_acts).mean(0).half()
  with open(cases_path, "a") as f:
    f.write(json.dumps(rec) + "\n")
  times.append(rec["sec"])
  if len(times) % 10 == 0 or i == len(prompts) - 1:
    torch.save(acts, acts_path)
    print(f"{len(done) + len(times)}/{len(prompts)} cases; {np.mean(times):.2f}s per case; "
          f"peak {torch.cuda.max_memory_allocated() / 2**30:.2f} GiB", flush=True)
torch.save(acts, acts_path)
meta = {"model": args.model, "n_cases": len(prompts), "layers": int(next(iter(acts.values())).shape[0]),
        "hidden": int(next(iter(acts.values())).shape[1]),
        "sec_per_case_mean": float(np.mean(times)) if times else None,
        "passes_per_case": 5, "peak_gpu_GiB": round(torch.cuda.max_memory_allocated() / 2**30, 2)}
json.dump(meta, open(f"{args.out}/meta.json", "w"), indent=1)
print("DEMO RUN COMPLETED", json.dumps(meta), flush=True)
