"""Is the per-order cheap steering content-sensitive, or a constant push toward the
letter of 1 coin? (12 held-out tune cases, vectors from the 11 train cells.)

For the best per-order settings of check (a): per-case change in expected offer by
case type; hard regret of the steered top offer by case type; the (partial)
Spearman correlation between the steered expected offer and each case's smallest
best offer, with the plain expected offer partialled out; and a comparison with the
final-layer push unit(W_U[letter of 1 coin] - W_U[letter of 4 coins]) per order,
scaled (grid of fractions) to the same mean change in expected offer: the
per-case agreement of the two. Writes demo_out/steer_content_check.json."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import torch
import common, steer_lib, steercheck, scoring
from refimpl import core, runtime
from refimpl.local_gemma2 import LocalGemma2

model, tok = runtime.load_gemma("9b", "cuda")
lm = LocalGemma2(model, tok)
R = steer_lib.Runner(lm)
ev = steer_lib.eval_cases()
train = steer_lib.lora_cases("lora_train")
acts = torch.load(os.path.join(common.ROOT, "demo_out", "steer_acts_train.pt"))
LAYERS = list(range(12, 40, 3)); li = {L: i for i, L in enumerate(LAYERS)}
resid = {L: float(torch.stack([acts["plain"][p.pid][:, li[L]].norm(dim=-1).mean() for p in train]).mean()) for L in LAYERS}
resid[41] = json.load(open(os.path.join(common.ROOT, "demo_out", "steer_verify_hooks.json")))["resid_norm_layer41"]
cheap_order = torch.stack([acts["cheap1"][p.pid] - acts["cheap4"][p.pid] for p in train]).mean(0)       # [5, layers, d]
W = lm.model.lm_head.weight


def per_case(vec_fn, L, f):
  """order-averaged probs per case under the per-order direction vec_fn(oi) at layer L, fraction f"""
  out = {}
  for p in ev:
    ps = [R.run(p, oi, None, R.steer(L, f * resid[L] * vec_fn(oi)) if f else None)[0] for oi in range(5)]
    out[p.pid] = {k: float(np.mean([d[k] for d in ps])) for k in core.PRICES}
  return out


def summarise(name, probs, base):
  E = {p.pid: core.expected_bid(probs[p.pid]) for p in ev}
  dE = {p.pid: E[p.pid] - core.expected_bid(base[p.pid]) for p in ev}
  hard = {p.pid: core.hard_regret(p, max(core.PRICES, key=lambda k: (probs[p.pid][k], -k))) for p in ev}
  best = [float(min(core.oracle_bids(p))) for p in ev]
  rho_E, _ = steercheck.partial_spearman([E[p.pid] for p in ev], best, [core.expected_bid(base[p.pid]) for p in ev], n_perm=2000)
  by = {}
  for t in ("cost below resale", "cost at or above resale", "no cost"):
    ids = [p.pid for p in ev if common.case_type(p) == t]
    by[t] = {"n": len(ids), "mean_dE": float(np.mean([dE[i] for i in ids])), "mean_hard_regret": float(np.mean([hard[i] for i in ids]))}
  return {"name": name, "mean_dE": float(np.mean(list(dE.values()))), "sd_dE_across_cases": float(np.std(list(dE.values()))),
          "partial_spearman_expected_vs_best": rho_E, "by_type": by, "per_case_dE": dE,
          "soft_regret_cell_mean": float(np.mean(list(__import__("refimpl.analysis", fromlist=["x"]).cell_means(
              {p.pid: core.soft_regret(p, probs[p.pid]) for p in ev}, ev).values())))}


base = per_case(lambda oi: None, 0, 0.0)
out = {"plain": summarise("plain", base, base), "settings": []}
unemb = lambda oi: steer_lib.unit(W[tok.convert_tokens_to_ids(steer_lib.LETTERS[scoring.ORDERS[oi].index(1)])].float()
                                  - W[tok.convert_tokens_to_ids(steer_lib.LETTERS[scoring.ORDERS[oi].index(4)])].float()).cpu()
for L, f in ((33, 0.5), (36, 0.5), (39, 0.5), (39, 1.0)):
  cheap = summarise(f"cheap per-order L{L} f{f}", per_case(lambda oi: steer_lib.unit(cheap_order[oi, li[L]]), L, f), base)
  # unembedding push at layer 41, fraction chosen to match the mean change in expected offer
  best_u = None
  for fu in (0.02, 0.05, 0.1, 0.2, 0.4):
    u = summarise(f"unembedding push L41 f{fu}", per_case(unemb, 41, fu * 1.0), base)
    if best_u is None or abs(u["mean_dE"] - cheap["mean_dE"]) < abs(best_u["mean_dE"] - cheap["mean_dE"]):
      best_u = u
  ids = [p.pid for p in ev]
  a, b = np.array([cheap["per_case_dE"][i] for i in ids]), np.array([best_u["per_case_dE"][i] for i in ids])
  out["settings"].append({"cheap": cheap, "matched_unembedding_push": best_u,
                          "per_case_dE_corr_cheap_vs_push": float(np.corrcoef(a, b)[0, 1]) if a.std() > 0 and b.std() > 0 else None})
  print(f"{cheap['name']}: dE {cheap['mean_dE']:+.3f} (sd across cases {cheap['sd_dE_across_cases']:.3f}); partial rho(expected, best) {cheap['partial_spearman_expected_vs_best']:+.2f}; "
        f"hard regret by type { {k: round(v['mean_hard_regret'], 2) for k, v in cheap['by_type'].items()} }; "
        f"matched push {best_u['name']}: dE {best_u['mean_dE']:+.3f}, per-case correlation {out['settings'][-1]['per_case_dE_corr_cheap_vs_push']}", flush=True)
print("plain: partial rho", out["plain"]["partial_spearman_expected_vs_best"], "hard regret by type",
      {k: round(v["mean_hard_regret"], 2) for k, v in out["plain"]["by_type"].items()}, flush=True)
json.dump(out, open(os.path.join(common.ROOT, "demo_out", "steer_content_check.json"), "w"), indent=1, default=float)
print("CONTENT CHECK COMPLETED", flush=True)
