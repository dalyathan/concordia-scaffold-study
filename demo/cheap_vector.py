"""Positive control "cheap": for each build case, the P1 activation (every layer,
averaged over the five orders) with pairs_template.paragraph(case, 1) as the Notes
block minus the same with pairs_template.paragraph(case, 4); averaged over cases.
It means "say 1 coin, not 4" in absolute terms. Adds "cheap" and "cheap_proj" to
demo_out/vectors.pt and their statistics to demo/directions.json."""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import torch
import common, pairs_template, scoring
from refimpl import pipeline, runtime, steering
from refimpl.local_gemma2 import LocalGemma2

model, tok = runtime.load_gemma("9b", "cuda")
lm = LocalGemma2(model, tok)
build = common.cases_in("build")
t0 = time.time()
diffs = []
for p in build:
  a = scoring.score(lm, p, notes=pairs_template.paragraph(p, 1), capture=True).acts
  b = scoring.score(lm, p, notes=pairs_template.paragraph(p, 4), capture=True).acts
  diffs.append(a - b)
print(f"{len(diffs)} build cases in {time.time() - t0:.0f}s", flush=True)
D = torch.stack(diffs)
v = D.mean(0)
plain = torch.load(os.path.join(common.ROOT, "demo_out", "p1_acts.pt"))
resid = torch.stack([x.float() for x in plain.values()]).norm(dim=-1).mean(0)
vp = os.path.join(common.ROOT, "demo_out", "vectors.pt")
vectors = torch.load(vp)
vectors["cheap"] = {L: v[L].clone() for L in range(v.shape[0])}
vectors["cheap_proj"] = {L: pipeline.project_out_letters(lm, v[L]) for L in range(v.shape[0])}
torch.save(vectors, vp)
per_layer = {}
for L in range(v.shape[0]):
  u = torch.nn.functional.normalize(D[:, L], dim=-1)
  per_layer[L] = {"norm_frac": float(v[L].norm() / resid[L]),
                  "norm_frac_proj": float(vectors["cheap_proj"][L].norm() / resid[L]),
                  "mean_pairwise_cos": (u @ u.T)[~torch.eye(len(diffs), dtype=bool)].mean().item(),
                  "cos_with_projected": float(torch.nn.functional.cosine_similarity(
                      v[L], vectors["cheap_proj"][L], dim=0))}
dp = os.path.join(common.DEMO_DIR, "directions.json")
stats = json.load(open(dp))
stats["cheap"] = {"n_pairs": len(diffs), "per_layer": per_layer,
                  "at_tuning_layers": {L: per_layer[L] for L in steering.LAYERS if L < v.shape[0]}}
json.dump(stats, open(dp, "w"), indent=1)
for L in (6, 12, 18, 24):
  x = per_layer[L]
  print(L, {k: round(val, 3) for k, val in x.items()}, flush=True)
print("CHEAP VECTOR COMPLETED", flush=True)
