"""Follow-up steering checks (items raised by the review of the steering verdict).
Same cases and vectors as steer_checks.py: vectors from the 11 train cells, scored on
the 12 held-out tune cases. Never test cells. Writes demo_out/steer_followup.json.

  P0  cosine of each per-order vector with unit(W_U[letter of 1] - W_U[letter of 4])
  P1  wrong-order control: order oi steered with the vector of order (oi+1) mod 5
  P2  per-order SENTENCE vectors (the analogue of check a), layers 27-39
  P3  actual-delta steering (diagnostic, uses the evaluated cases' own method-text
      run): delta = P1(method run) - P1(plain run), added at scale 1: per case and
      order; averaged over orders within a case; averaged over cases within an order
  P4  the positive control as TEXT: paragraph(case, 1) and paragraph(case, 4) as notes
  P5  free text on all 12 cases: order-averaged cheap vector at two settings, with
      the negated vector and a random direction of the same norm
  P6  negated per-order cheap at coherent strengths
  P7  per-case changes in expected offer for: per-order cheap, method text, patches at
      layers 33 and 36, and the final-layer push (interpolated to the same mean); their
      correlations with the push and with headroom (plain expected offer - 1)"""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import torch
import common, pairs_template, scoring, steer_lib, textrows
from refimpl import analysis, core, runtime
from refimpl.local_gemma2 import LocalGemma2

T0 = time.time()
def log(m): print(f"[{time.time() - T0:6.0f}s] {m}", flush=True)
model, tok = runtime.load_gemma("9b", "cuda")
lm = LocalGemma2(model, tok)
R = steer_lib.Runner(lm)
ev, train = steer_lib.eval_cases(), steer_lib.lora_cases("lora_train")
assert all(common.load_splits()["case_split"][p.pid] != "test" for p in ev + train)
acts = torch.load(os.path.join(common.ROOT, "demo_out", "steer_acts_train.pt"))
LAYERS = list(range(12, 40, 3)); li = {L: i for i, L in enumerate(LAYERS)}
resid = {L: float(torch.stack([acts["plain"][p.pid][:, li[L]].norm(dim=-1).mean() for p in train]).mean()) for L in LAYERS}
resid[41] = json.load(open(os.path.join(common.ROOT, "demo_out", "steer_verify_hooks.json")))["resid_norm_layer41"]
cheap_order = torch.stack([acts["cheap1"][p.pid] - acts["cheap4"][p.pid] for p in train]).mean(0)       # [5, layers, d]
sent_order = torch.stack([acts["method"][p.pid] - acts["neutral"][p.pid] for p in train]).mean(0)        # [5, layers, d]
cheap_avg, sent_avg = cheap_order.mean(0), sent_order.mean(0)
W = lm.model.lm_head.weight
LET = steer_lib.LETTERS
def unemb(oi):
  o = scoring.ORDERS[oi]
  return steer_lib.unit(W[tok.convert_tokens_to_ids(LET[o.index(1)])].float() - W[tok.convert_tokens_to_ids(LET[o.index(4)])].float()).cpu()
U = [unemb(oi) for oi in range(5)]
unit = steer_lib.unit
out = {"cases": [p.pid for p in ev]}


def evaluate(vec_fn, L, notes_fn=None):
  """vec_fn(p, oi) -> absolute steering vector or None. Returns per-case order-averaged probs and mass."""
  probs, mass = {}, {}
  for p in ev:
    ps, ms = [], []
    for oi in range(5):
      v = vec_fn(p, oi) if vec_fn else None
      pr, m, *_ = R.run(p, oi, notes_fn(p) if notes_fn else None, R.steer(L, v) if v is not None else None)
      ps.append(pr); ms.append(m)
    probs[p.pid] = {k: float(np.mean([d[k] for d in ps])) for k in core.PRICES}
    mass[p.pid] = float(np.mean(ms))
  return probs, mass


BASE_P, BASE_M = evaluate(None, 0)
BASE_E = {p.pid: core.expected_bid(BASE_P[p.pid]) for p in ev}
def summ(probs, mass):
  dE = {p.pid: core.expected_bid(probs[p.pid]) - BASE_E[p.pid] for p in ev}
  soft = {p.pid: core.soft_regret(p, probs[p.pid]) for p in ev}
  hard = {p.pid: core.hard_regret(p, max(core.PRICES, key=lambda k: (probs[p.pid][k], -k))) for p in ev}
  cm = lambda d: float(np.mean(list(analysis.cell_means(d, ev).values())))
  return {"d_expected": float(np.mean(list(dE.values()))), "soft_regret": cm(soft), "hard_regret": cm(hard),
          "mass_ratio": float(np.mean(list(mass.values())) / np.mean(list(BASE_M.values()))), "per_case_dE": dE}
out["plain"] = {"soft_regret": summ(BASE_P, BASE_M)["soft_regret"], "expected": float(np.mean(list(BASE_E.values()))),
                "mass": float(np.mean(list(BASE_M.values())))}
log("plain done")

# ----------------------------------------------------------------------- P0
out["P0_cosine_with_unembedding_diff"] = {
    "cheap": {L: [float(torch.nn.functional.cosine_similarity(cheap_order[oi, li[L]], U[oi], dim=0)) for oi in range(5)] for L in (27, 33, 36, 39)},
    "sentence": {L: [float(torch.nn.functional.cosine_similarity(sent_order[oi, li[L]], U[oi], dim=0)) for oi in range(5)] for L in (27, 33, 36, 39)}}
log("P0 done")

# ----------------------------------------------------------------------- P1 wrong order
SET = ((27, 0.25), (33, 0.5), (36, 0.5), (39, 0.5), (39, 1.0))
out["P1_wrong_order"] = []
for L, f in SET:
  same = summ(*evaluate(lambda p, oi: f * resid[L] * unit(cheap_order[oi, li[L]]), L))
  wrong = summ(*evaluate(lambda p, oi: f * resid[L] * unit(cheap_order[(oi + 1) % 5, li[L]]), L))
  out["P1_wrong_order"].append({"layer": L, "fraction": f, "same_order": {k: v for k, v in same.items() if k != "per_case_dE"},
                                "next_order_vector": {k: v for k, v in wrong.items() if k != "per_case_dE"}, "_same_per_case": same["per_case_dE"]})
  log(f"P1 L{L} f{f}: own-order dE {same['d_expected']:+.3f}, wrong-order dE {wrong['d_expected']:+.3f} (mass x{wrong['mass_ratio']:.2f})")

# ----------------------------------------------------------------------- P2 per-order sentence
out["P2_sentence_per_order"] = []
for L in (27, 30, 33, 36, 39):
  for f in (0.25, 0.5, 1.0):
    s = summ(*evaluate(lambda p, oi: f * resid[L] * unit(sent_order[oi, li[L]]), L))
    out["P2_sentence_per_order"].append({"layer": L, "fraction": f, **{k: v for k, v in s.items() if k != "per_case_dE"}})
  best = min((r for r in out["P2_sentence_per_order"] if r["layer"] == L), key=lambda r: r["soft_regret"])
  log(f"P2 sentence per-order L{L}: lowest regret {best['soft_regret']:.3f} at f{best['fraction']} (dE {best['d_expected']:+.3f}, mass x{best['mass_ratio']:.2f})")

# ----------------------------------------------------------------------- P3 actual delta; P7 patches
DL = (27, 30, 33, 36, 39)
delta, st_method = {}, {}
for p in ev:
  for oi in range(5):
    _, stp = R.with_capture(p, oi, list(range(42)), notes=None)
    _, stm = R.with_capture(p, oi, list(range(42)), notes=textrows.METHOD)
    st_method[(p.pid, oi)] = {L: stm[L] for L in (33, 36)}
    delta[(p.pid, oi)] = {L: stm[L] - stp[L] for L in DL}
log("P3 deltas captured")
out["P3_actual_delta"] = []
for L in DL:
  own = summ(*evaluate(lambda p, oi: delta[(p.pid, oi)][L], L))
  case_avg = summ(*evaluate(lambda p, oi: torch.stack([delta[(p.pid, o)][L] for o in range(5)]).mean(0), L))
  order_avg = summ(*evaluate(lambda p, oi: torch.stack([delta[(q.pid, oi)][L] for q in ev]).mean(0), L))
  out["P3_actual_delta"].append({"layer": L, "own_case_and_order": {k: v for k, v in own.items() if k != "per_case_dE"},
                                 "averaged_over_orders_within_case": {k: v for k, v in case_avg.items() if k != "per_case_dE"},
                                 "averaged_over_cases_within_order": {k: v for k, v in order_avg.items() if k != "per_case_dE"}})
  log(f"P3 L{L}: own dE {own['d_expected']:+.3f} regret {own['soft_regret']:.3f}; case-avg {case_avg['d_expected']:+.3f}; order-avg {order_avg['d_expected']:+.3f}")

# ----------------------------------------------------------------------- P4 text as notes
out["P4_cheap_text"] = {}
for k in (1, 4):
  s = summ(*evaluate(None, 0, notes_fn=lambda p, k=k: pairs_template.paragraph(p, k)))
  out["P4_cheap_text"][f"paragraph concluding {k}"] = {kk: v for kk, v in s.items() if kk != "per_case_dE"}
method_s = summ(*evaluate(None, 0, notes_fn=lambda p: textrows.METHOD))
out["P4_cheap_text"]["method paragraph"] = {kk: v for kk, v in method_s.items() if kk != "per_case_dE"}
log(f"P4: text 'concluding 1' dE {out['P4_cheap_text']['paragraph concluding 1']['d_expected']:+.3f}, 'concluding 4' dE {out['P4_cheap_text']['paragraph concluding 4']['d_expected']:+.3f}")

# ----------------------------------------------------------------------- P6 negated at coherent strengths
out["P6_negated_per_order"] = []
for L, f in ((39, 0.25), (39, 0.5), (33, 0.5), (27, 0.1), (27, 0.25)):
  s = summ(*evaluate(lambda p, oi: -f * resid[L] * unit(cheap_order[oi, li[L]]), L))
  out["P6_negated_per_order"].append({"layer": L, "fraction": f, **{k: v for k, v in s.items() if k != "per_case_dE"}})
  log(f"P6 negated per-order L{L} f{f}: dE {s['d_expected']:+.3f} mass x{s['mass_ratio']:.2f}")

# ----------------------------------------------------------------------- P7 per-case comparison
grid_f = (0.01, 0.02, 0.03, 0.05, 0.07, 0.1, 0.15, 0.2, 0.3)
push = {f: summ(*evaluate(lambda p, oi: f * resid[41] * U[oi], 41)) for f in grid_f}
log("P7 push grid done")
def push_matched(target_mean):
  """per-case dE of the final-layer push interpolated to the target mean change"""
  fs = sorted(grid_f, key=lambda f: push[f]["d_expected"], reverse=True)     # from small |dE| to large
  for a, b in zip(fs, fs[1:]):
    da, db = push[a]["d_expected"], push[b]["d_expected"]
    if da >= target_mean >= db:
      w = (da - target_mean) / (da - db) if da != db else 0.0
      return {pid: (1 - w) * push[a]["per_case_dE"][pid] + w * push[b]["per_case_dE"][pid] for pid in push[a]["per_case_dE"]}
  return push[fs[-1]]["per_case_dE"]
items = {}
for L, f in ((33, 0.5), (36, 0.5), (39, 0.5)):
  items[f"cheap per-order L{L} f{f}"] = summ(*evaluate(lambda p, oi: f * resid[L] * unit(cheap_order[oi, li[L]]), L))
items["method text (prompt)"] = method_s
for L in (33, 36):
  pr, ms = {}, {}
  for p in ev:
    ps, mm = [], []
    for oi in range(5):
      r = R.run(p, oi, None, R.patch(L, st_method[(p.pid, oi)][L]))
      ps.append(r[0]); mm.append(r[1])
    pr[p.pid] = {k: float(np.mean([d[k] for d in ps])) for k in core.PRICES}; ms[p.pid] = float(np.mean(mm))
  items[f"patch method residual at L{L}"] = summ(pr, ms)
ids = [p.pid for p in ev]
headroom = np.array([BASE_E[i] - 1.0 for i in ids])
corr = lambda a, b: float(np.corrcoef(a, b)[0, 1]) if np.std(a) > 0 and np.std(b) > 0 else None
out["P7_per_case"] = {}
for name, s in items.items():
  d = np.array([s["per_case_dE"][i] for i in ids])
  pm = push_matched(s["d_expected"])
  out["P7_per_case"][name] = {"mean_dE": s["d_expected"], "corr_with_matched_push": corr(d, np.array([pm[i] for i in ids])),
                              "corr_with_headroom": corr(d, -headroom), "per_case_dE": {i: float(x) for i, x in zip(ids, d)}}
  log(f"P7 {name}: mean dE {s['d_expected']:+.3f}; corr with matched final-layer push {out['P7_per_case'][name]['corr_with_matched_push']:.3f}; corr with headroom {out['P7_per_case'][name]['corr_with_headroom']:.3f}")
json.dump(out, open(os.path.join(common.ROOT, "demo_out", "steer_followup.json"), "w"), indent=1, default=float)

# ----------------------------------------------------------------------- P5 free text on all 12 cases
rng = np.random.Generator(np.random.PCG64(5))
rvec = unit(torch.from_numpy(rng.standard_normal(cheap_avg.shape[1]).astype(np.float32)))
say_plain = {p.pid: scoring.say(lm, p) for p in ev}
out["P5_free_text"] = {"plain": {i: list(v) for i, v in say_plain.items()}, "settings": []}
for L, f in ((27, 0.25), (39, 1.0)):
  v = f * resid[L] * unit(cheap_avg[li[L]])
  row = {"layer": L, "fraction": f}
  for name, vec in (("steered", v), ("negated", -v), ("random", f * resid[L] * rvec)):
    res = {p.pid: R.say_steered(p, L, vec) for p in ev}
    moved = [res[i][1] != say_plain[i][1] for i in ids if res[i][1] is not None and say_plain[i][1] is not None]
    d = [res[i][1] - say_plain[i][1] for i in ids if res[i][1] is not None and say_plain[i][1] is not None]
    by = {}
    for t in ("cost below resale", "cost at or above resale", "no cost"):
      sel = [p.pid for p in ev if common.case_type(p) == t and res[p.pid][1] is not None]
      by[t] = {"n": len(sel), "hard_regret": float(np.mean([core.hard_regret(next(q for q in ev if q.pid == i), res[i][1]) for i in sel])) if sel else None}
    row[name] = {"offers": {i: res[i][1] for i in ids}, "share_moved": float(np.mean(moved)), "mean_change": float(np.mean(d)), "by_type": by}
  out["P5_free_text"]["settings"].append(row)
  log(f"P5 free text L{L} f{f}: share moved {row['steered']['share_moved']:.2f} (mean change {row['steered']['mean_change']:+.2f}); "
      f"negated {row['negated']['share_moved']:.2f} ({row['negated']['mean_change']:+.2f}); random {row['random']['share_moved']:.2f} ({row['random']['mean_change']:+.2f})")
out["P5_free_text"]["plain_hard_regret_by_type"] = {t: float(np.mean([core.hard_regret(p, say_plain[p.pid][1]) for p in ev if common.case_type(p) == t and say_plain[p.pid][1] is not None])) for t in ("cost below resale", "cost at or above resale", "no cost")}
json.dump(out, open(os.path.join(common.ROOT, "demo_out", "steer_followup.json"), "w"), indent=1, default=float)
log("STEER FOLLOWUP COMPLETED")
