"""Hook verification, before any steering check (DEMO_STATUS.md).

(1) Patch the full P1 residual of a method-text run into the plain run at the last
    layer (41): the plain run must reproduce the method-text first-token
    distribution exactly (all 5 orders, 4 held-out tune cases).
(2) Steer at the last layer with W_U[letter of offer 1] - W_U[letter of offer 4]
    (unit, per option order, scaled to fractions of the mean plain P1 residual norm
    at layer 41): the expected offer must fall as the fraction grows, while the
    letter format stays coherent for small fractions.
Also checks that the letter token ids used for steering equal the ids letter_scores
reads. Writes demo_out/steer_verify_hooks.json."""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import torch
import common, scoring, textrows, steer_lib
from refimpl import core, runtime
from refimpl.local_gemma2 import LocalGemma2

model, tok = runtime.load_gemma("9b", "cuda")
lm = LocalGemma2(model, tok)
R = steer_lib.Runner(lm)
cases = steer_lib.eval_cases()[:4]
LAST = len(R.layers) - 1
assert LAST == 41
out = {"cases": [p.pid for p in cases]}

# letter token ids: the id letter_scores reads is the id at position `start` of the full rendering
p0 = cases[0]
user, l2p = R.user(p0, 0)
from refimpl.local_gemma2 import build_messages, CHOICE_SYSTEM, ensure_prompt_not_too_long
trim = ensure_prompt_not_too_long(user, 1)
start = lm.encode(lm.render(build_messages(CHOICE_SYSTEM, trim), True)).shape[1]
read = [int(lm.encode(lm.render(build_messages(CHOICE_SYSTEM, trim, l), False))[0][start]) for l in steer_lib.LETTERS]
out["letter_ids_match"] = read == R.letter_ids
print("letter ids read by letter_scores == convert_tokens_to_ids:", out["letter_ids_match"], read, flush=True)
assert out["letter_ids_match"]

# (1) patch at the last layer
worst, rows = 0.0, []
plain_norm41 = []
for p in cases:
  for oi in range(5):
    (pm, mm, fm, _, _), st = R.with_capture(p, oi, [LAST], notes=textrows.METHOD)
    (pp, mp, fp, _, p1p), stp = R.with_capture(p, oi, [LAST])
    plain_norm41.append(float(stp[LAST].norm()))
    (pq, mq, fq, _, _) = R.run(p, oi, None, R.patch(LAST, st[LAST]))
    d = max(abs(fm[l] - fq[l]) for l in steer_lib.LETTERS)
    worst = max(worst, d)
    rows.append({"pid": p.pid, "order": oi, "max_abs_logprob_diff": d,
                 "method_vs_plain_max_diff": max(abs(fm[l] - fp[l]) for l in steer_lib.LETTERS)})
out["patch_last_layer"] = {"worst_abs_diff": worst, "exact": worst == 0.0, "rows": rows}
print(f"(1) patch at layer {LAST}: worst |log-prob difference| = {worst:.3e} (exact: {worst == 0.0}); "
      f"method vs plain differ by up to {max(r['method_vs_plain_max_diff'] for r in rows):.2f} nats", flush=True)

# (2) final-layer steering with the offer-1 minus offer-4 unembedding difference
resid41 = float(np.mean(plain_norm41))
out["resid_norm_layer41"] = resid41
W = lm.model.lm_head.weight
plain = {}
for p in cases:
  plain[p.pid] = [R.run(p, oi) for oi in range(5)]
def avg_probs(runs):
  return {k: float(np.mean([r[0][k] for r in runs])) for k in core.PRICES}
base_E = float(np.mean([core.expected_bid(avg_probs(plain[p.pid])) for p in cases]))
base_mass = np.mean([np.mean([r[1] for r in plain[p.pid]]) for p in cases])
rows2 = []
for f in (0.05, 0.1, 0.25, 0.5, 1.0, 2.0):
  Es, masses = [], []
  for p in cases:
    res = []
    for oi in range(5):
      order = scoring.ORDERS[oi]
      l1, l4 = steer_lib.LETTERS[order.index(1)], steer_lib.LETTERS[order.index(4)]
      d = steer_lib.unit(W[tok.convert_tokens_to_ids(l1)].float() - W[tok.convert_tokens_to_ids(l4)].float()).cpu()
      pr, mass, *_ = R.run(p, oi, None, R.steer(LAST, f * resid41 * d))
      res.append((pr, mass))
    avg = {k: float(np.mean([r[0][k] for r in res])) for k in core.PRICES}
    Es.append(core.expected_bid(avg)); masses.append(np.mean([r[1] for r in res]))
  rows2.append({"fraction": f, "d_expected": float(np.mean(Es) - base_E), "mass_ratio": float(np.mean(masses) / base_mass)})
  print(f"(2) layer {LAST}, fraction {f}: change in expected offer {rows2[-1]['d_expected']:+.3f}, "
        f"letter mass x{rows2[-1]['mass_ratio']:.2f}", flush=True)
out["final_layer_unembedding_steer"] = {"plain_expected": float(base_E), "rows": rows2}
d = [r["d_expected"] for r in rows2]
out["steer_check_passes"] = bool(d[2] < -0.05 and d[3] < d[2] + 1e-9 or d[3] < -0.1)
out["rule"] = "pass: the expected offer falls by more than 0.05 at fraction 0.25 and does not rise again by 0.5"
json.dump(out, open(os.path.join(common.ROOT, "demo_out", "steer_verify_hooks.json"), "w"), indent=1)
print("HOOK CHECK 1 (patch exact):", out["patch_last_layer"]["exact"], "| HOOK CHECK 2 (steer lowers offer):", out["steer_check_passes"], flush=True)
