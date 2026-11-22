"""Step 5: steering vectors from P1 activations (every layer, averaged over the five
orders). Vectors per layer: template (good - bad, build cases), offer_lower (A - B,
build cases), sentence (method row - neutral row, step 4 tuning activations); each
also with the option-letter span removed (pipeline.project_out_letters).
Writes demo_out/vectors.pt ({name: {layer: float32 tensor}}) and demo/directions.json."""
import argparse, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import torch
import common, pairs_template, scoring
from refimpl import pipeline, runtime, steering
from refimpl.local_gemma2 import LocalGemma2

ap = argparse.ArgumentParser()
ap.add_argument("--model", default="9b")
args = ap.parse_args()
model, tok = runtime.load_gemma(args.model, "cuda")
lm = LocalGemma2(model, tok)
P = common.prompts_by_id()
pairs, lower = pairs_template.build_pairs()
t0 = time.time()
def act(p, text):
  return scoring.score(lm, p, notes=text, capture=True).acts          # [L, d] float32
diffs = {"template": [], "offer_lower": []}
for x in pairs:
  p = P[x["pid"]]
  diffs["template"].append(act(p, x["good"]) - act(p, x["bad"]))
print(f"template pairs done ({time.time() - t0:.0f}s)", flush=True)
for x in lower:
  p = P[x["pid"]]
  diffs["offer_lower"].append(act(p, x["A"]) - act(p, x["B"]))
print(f"offer-lower pairs done ({time.time() - t0:.0f}s)", flush=True)
rows = torch.load(os.path.join(common.ROOT, "demo_out", "acts_rows.pt"))
diffs["sentence"] = [rows["method"][pid].float() - rows["neutral"][pid].float() for pid in rows["method"]]
plain = torch.load(os.path.join(common.ROOT, "demo_out", "p1_acts.pt"))
resid = torch.stack([v.float() for v in plain.values()]).norm(dim=-1).mean(0)     # [L]
n_layers = resid.shape[0]
vectors, stats = {}, {}
for name, ds in diffs.items():
  D = torch.stack(ds)                                                     # [n, L, d]
  v = D.mean(0)
  vectors[name] = {L: v[L].clone() for L in range(n_layers)}
  vectors[name + "_proj"] = {L: pipeline.project_out_letters(lm, v[L]) for L in range(n_layers)}
  per_layer = {}
  for L in range(n_layers):
    u = torch.nn.functional.normalize(D[:, L], dim=-1)
    cos = (u @ u.T)[~torch.eye(len(ds), dtype=bool)].mean().item() if len(ds) > 1 else float("nan")
    per_layer[L] = {"norm_frac": float(v[L].norm() / resid[L]),
                    "norm_frac_proj": float(vectors[name + "_proj"][L].norm() / resid[L]),
                    "mean_pairwise_cos": cos}
  stats[name] = {"n_pairs": len(ds), "per_layer": per_layer,
                 "at_tuning_layers": {L: per_layer[L] for L in steering.LAYERS if L < n_layers}}
torch.save(vectors, os.path.join(common.ROOT, "demo_out", "vectors.pt"))
json.dump(stats, open(os.path.join(common.DEMO_DIR, "directions.json"), "w"), indent=1)
for name, s in stats.items():
  print(name, s["n_pairs"], {L: (round(x["norm_frac"], 3), round(x["mean_pairwise_cos"], 3))
                             for L, x in s["at_tuning_layers"].items()})
print("DIRECTIONS COMPLETED", flush=True)
