"""Dose scan before the tuning job (8 tuning cases, five orders).

Vectors offer_lower, cheap and sentence, each unit-normalised and scaled to a
fraction of the mean plain P1 residual norm at the layer (tuning cases, from
demo_out/p1_acts.pt); layers 12, 18, 24; fractions 0.1, 0.25, 0.5, 1.0, 2.0; two
position modes: P1 only on ("p1") and every position from P3 on ("p3"). Reports,
per condition, the mean change in expected offer against plain, the mean soft
regret and the letter mass relative to plain. Writes demo_out/dose_scan.json."""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import torch
import common, scoring
from refimpl import core, runtime
from refimpl.local_gemma2 import LocalGemma2

VECTORS = ("offer_lower", "cheap", "sentence")
LAYERS, FRACTIONS, MODES = (12, 18, 24), (0.1, 0.25, 0.5, 1.0, 2.0), ("p1", "p3")
model, tok = runtime.load_gemma("9b", "cuda")
lm = LocalGemma2(model, tok)
tuning = common.cases_in("tuning")
cases = tuning[::4][:8]                      # every fourth tuning case: 8, spread over cells
plain_acts = torch.load(os.path.join(common.ROOT, "demo_out", "p1_acts.pt"))
resid = {L: float(np.mean([plain_acts[p.pid][L].float().norm().item() for p in tuning])) for L in LAYERS}
vecs = torch.load(os.path.join(common.ROOT, "demo_out", "vectors.pt"))
t0 = time.time()
base = {p.pid: scoring.score(lm, p) for p in cases}
plain = {"expected": float(np.mean([base[p.pid].expected() for p in cases])),
         "soft_regret": float(np.mean([core.soft_regret(p, base[p.pid].probs) for p in cases])),
         "mass": float(np.mean([base[p.pid].mass for p in cases]))}
rows = []
for name in VECTORS:
  for mode in MODES:
    for L in LAYERS:
      u = vecs[name][L].float()
      u = u / u.norm()
      for f in FRACTIONS:
        rs = {p.pid: scoring.score(lm, p, steer=(L, f * resid[L] * u), steer_from=mode) for p in cases}
        rows.append({"vector": name, "mode": mode, "layer": L, "fraction": f,
                     "d_expected": float(np.mean([rs[p.pid].expected() - base[p.pid].expected() for p in cases])),
                     "soft_regret": float(np.mean([core.soft_regret(p, rs[p.pid].probs) for p in cases])),
                     "mass_ratio": float(np.mean([rs[p.pid].mass for p in cases]) / plain["mass"])})
        r = rows[-1]
        print(f"[{time.time() - t0:5.0f}s] {name:<11} {mode} L{L:<2} f={f:<4} dE={r['d_expected']:+.3f} "
              f"regret={r['soft_regret']:.3f} mass={r['mass_ratio']:.2f}", flush=True)
json.dump({"cases": [p.pid for p in cases], "resid_norm": resid, "plain": plain, "rows": rows,
           "vectors": VECTORS, "layers": LAYERS, "fractions": FRACTIONS, "modes": MODES},
          open(os.path.join(common.ROOT, "demo_out", "dose_scan.json"), "w"), indent=1)
print("DOSE SCAN COMPLETED", flush=True)
