"""Steering checks a-c before closing rung 4 (see DEMO_STATUS.md, section 3).

Vectors are built from the 11 train cells (44 cases) and scored on 12 held-out tune
cases (variants 15 and 18 of the six held-out tune cells); never on test cells.
Strength = fraction of the mean plain P1 residual norm at that layer (train cases,
all orders). Stages (each saved to demo_out/steer_checks.json; --resume skips done
stages): collect, a, b, c, controls, extras.

  a  per-order cheap vectors (cheap = P1 with paragraph(case, 1) minus with
     paragraph(case, 4)), each option order steered with its own vector; layers
     12-39 every 3; fractions 0.1, 0.25, 0.5, 1.0
  b  order-averaged cheap and sentence (method text minus neutral text); layers
     27-39 every 3; the same fractions
  c  patch each held-out case's P1 residual from the method-text run into the
     plain run, one layer at a time (all 42 layers), per order
  controls  negated vector and 3 random unit directions at the best setting of each
     of (a), (b-cheap), (b-sentence)
  extras  top-10 P1 tokens under steering (4 cases) and steered free text (4 cases)
"""
import argparse, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import torch
import common, pairs_template, scoring, steer_lib, textrows
from refimpl import core, runtime
from refimpl.local_gemma2 import LocalGemma2

ap = argparse.ArgumentParser()
ap.add_argument("--resume", action="store_true")
args = ap.parse_args()
OUT = os.path.join(common.ROOT, "demo_out", "steer_checks.json")
ACTS = os.path.join(common.ROOT, "demo_out", "steer_acts_train.pt")
res = json.load(open(OUT)) if (args.resume and os.path.exists(OUT)) else {}
T0 = time.time()
def log(m): print(f"[{time.time() - T0:6.0f}s] {m}", flush=True)
def save(): json.dump(res, open(OUT, "w"), indent=1, default=float)

model, tok = runtime.load_gemma("9b", "cuda")
lm = LocalGemma2(model, tok)
R = steer_lib.Runner(lm)
train, ev = steer_lib.lora_cases("lora_train"), steer_lib.eval_cases()
assert len(train) == 44 and len(ev) == 12
assert all(common.load_splits()["case_split"][p.pid] != "test" for p in train + ev)
LAYERS = list(range(12, 40, 3))                     # 12, 15, ..., 39
LAYERS_B = [27, 30, 33, 36, 39]
FRACS = (0.1, 0.25, 0.5, 1.0)
N_LAYERS = len(R.layers)

# ------------------------------------------------------------ plain baseline
plain_runs = {(p.pid, oi): R.run(p, oi)[:2] for p in ev for oi in range(5)}
plain_m, plain = steer_lib.aggregate(ev, plain_runs)
res["plain_eval12"] = {**plain_m, "cases": [p.pid for p in ev]}
log(f"plain on 12 held-out tune cases: soft regret {plain_m['soft_regret']:.3f}, expected {plain_m['expected']:.3f}, mass {plain_m['mass']:.2f}")

# ------------------------------------------------------------------- collect
if os.path.exists(ACTS):
  acts = torch.load(ACTS)
else:
  acts = {}
  names = {"plain": None, "cheap1": "c1", "cheap4": "c4", "method": "m", "neutral": "n"}
  notes = lambda p: {"plain": None, "cheap1": pairs_template.paragraph(p, 1), "cheap4": pairs_template.paragraph(p, 4),
                     "method": textrows.METHOD, "neutral": textrows.row_text("neutral", p)}
  for i, p in enumerate(train):
    nt = notes(p)
    for name in names:
      per = []
      for oi in range(5):
        _, st = R.with_capture(p, oi, LAYERS, notes=nt[name])
        per.append(torch.stack([st[L] for L in LAYERS]))
      acts.setdefault(name, {})[p.pid] = torch.stack(per)            # [5, layers, d]
    if (i + 1) % 11 == 0:
      log(f"collect: {i + 1}/{len(train)} train cases")
  torch.save(acts, ACTS)
log("collect done")
li = {L: i for i, L in enumerate(LAYERS)}
resid = {L: float(torch.stack([acts["plain"][p.pid][:, li[L]].norm(dim=-1).mean() for p in train]).mean()) for L in LAYERS}
cheap_diff = torch.stack([acts["cheap1"][p.pid] - acts["cheap4"][p.pid] for p in train])     # [n, 5, layers, d]
cheap_order = cheap_diff.mean(0)                                                              # [5, layers, d]
cheap_avg = cheap_order.mean(0)                                                               # [layers, d]
sent_avg = torch.stack([acts["method"][p.pid] - acts["neutral"][p.pid] for p in train]).mean(0).mean(0)
vec_stats = {"cheap_norm_frac": {L: float(cheap_avg[li[L]].norm() / resid[L]) for L in LAYERS},
             "sentence_norm_frac": {L: float(sent_avg[li[L]].norm() / resid[L]) for L in LAYERS},
             "cheap_cos_between_orders": {L: float(np.mean([float(torch.nn.functional.cosine_similarity(
                 cheap_order[a, li[L]], cheap_order[b, li[L]], dim=0)) for a in range(5) for b in range(a)])) for L in LAYERS},
             "resid_norm": resid}
res["vector_stats"] = vec_stats
save()


def steer_eval(vec_fn, L, f, cases=ev):
  """vec_fn(oi) -> unit direction [d] (cpu float32); strength f * resid[L]."""
  runs = {}
  for p in cases:
    for oi in range(5):
      v = f * resid[L] * vec_fn(oi)
      runs[(p.pid, oi)] = R.run(p, oi, None, R.steer(L, v))[:2]
  return steer_lib.aggregate(cases, runs, plain)[0]


def table(name, rows):
  log(f"{name}: " + "; ".join(f"L{r['layer']} f{r['fraction']}: dE {r['d_expected']:+.3f} regret {r['soft_regret']:.2f} mass x{r['mass_ratio']:.2f}"
                              for r in sorted(rows, key=lambda r: r["d_expected"])[:3]) + "  (3 largest decreases)")


# -------------------------------------------------------------------- stage a
if "a" not in res:
  rows = []
  for L in LAYERS:
    for f in FRACS:
      m = steer_eval(lambda oi: steer_lib.unit(cheap_order[oi, li[L]]), L, f)
      rows.append({"layer": L, "fraction": f, **m})
    log(f"a: layer {L} done")
  res["a"] = rows; save(); table("a (per-order cheap)", rows)

# -------------------------------------------------------------------- stage b
if "b" not in res:
  rows = []
  for name, vec in (("cheap", cheap_avg), ("sentence", sent_avg)):
    for L in LAYERS_B:
      for f in FRACS:
        m = steer_eval(lambda oi: steer_lib.unit(vec[li[L]]), L, f)
        rows.append({"vector": name, "layer": L, "fraction": f, **m})
    log(f"b: {name} done")
  res["b"] = rows; save()
  for name in ("cheap", "sentence"):
    table(f"b ({name}, order-averaged)", [r for r in rows if r["vector"] == name])

# -------------------------------------------------------------------- stage c
if "c" not in res:
  rows = []
  per_layer = {L: {} for L in range(N_LAYERS)}
  method_runs = {}
  exact = 0.0
  for p in ev:
    for oi in range(5):
      (pm, mm, fm, _, _), st = R.with_capture(p, oi, list(range(N_LAYERS)), notes=textrows.METHOD)
      method_runs[(p.pid, oi)] = (pm, mm)
      for L in range(N_LAYERS):
        out = R.run(p, oi, None, R.patch(L, st[L]))
        per_layer[L][(p.pid, oi)] = out[:2]
        if L == N_LAYERS - 1:
          exact = max(exact, max(abs(out[2][l] - fm[l]) for l in steer_lib.LETTERS))
    log(f"c: {p.pid} done")
  method_m, _ = steer_lib.aggregate(ev, method_runs, plain)
  for L in range(N_LAYERS):
    m, _ = steer_lib.aggregate(ev, per_layer[L], plain)
    rows.append({"layer": L, **m})
  res["c"] = {"method_text": method_m, "patched": rows, "last_layer_exact_diff": exact}
  save()
  log("c (patching): soft regret by layer (plain {:.2f}, method text {:.2f}): ".format(plain_m["soft_regret"], method_m["soft_regret"])
      + " ".join(f"{r['layer']}:{r['soft_regret']:.2f}" for r in rows if r["layer"] % 3 == 0 or r["layer"] == 41))


# ------------------------------------------------------------------- controls
def best_setting(rows, key=None):
  rs = [r for r in rows if key is None or r["vector"] == key]
  coh = [r for r in rs if r["mass_ratio"] >= 0.9]
  pool, coherent = (coh, True) if coh else (rs, False)
  b = min(pool, key=lambda r: r["d_expected"])
  return {**b, "coherent": coherent}


if "controls" not in res:
  rng = np.random.Generator(np.random.PCG64(7))
  rand = [steer_lib.unit(torch.from_numpy(rng.standard_normal(cheap_avg.shape[1]).astype(np.float32))) for _ in range(3)]
  ctl = {}
  for name, rows, vec_fn in (
      ("a", res["a"], lambda L, sign: (lambda oi: sign * steer_lib.unit(cheap_order[oi, li[L]]))),
      ("b_cheap", [r for r in res["b"] if r["vector"] == "cheap"], lambda L, sign: (lambda oi: sign * steer_lib.unit(cheap_avg[li[L]]))),
      ("b_sentence", [r for r in res["b"] if r["vector"] == "sentence"], lambda L, sign: (lambda oi: sign * steer_lib.unit(sent_avg[li[L]])))):
    b = best_setting(rows)
    L, f = b["layer"], b["fraction"]
    ctl[name] = {"best": b, "negated": steer_eval(vec_fn(L, -1.0), L, f),
                 "random": [steer_eval(lambda oi, v=v: v, L, f) for v in rand]}
    log(f"controls {name}: best L{L} f{f} dE {b['d_expected']:+.3f}; negated dE {ctl[name]['negated']['d_expected']:+.3f}; "
        f"random dE {[round(r['d_expected'], 3) for r in ctl[name]['random']]}")
  res["controls"] = ctl; save()

# --------------------------------------------------------------------- extras
if "extras" not in res:
  four = ev[:4]
  ex = {"top10": [], "say": []}
  overall = [res["controls"][k]["best"] for k in ("a", "b_cheap", "b_sentence")]
  best_all = min(overall, key=lambda r: r["d_expected"])
  L, f = best_all["layer"], best_all["fraction"]
  vname = "cheap" if best_all is not res["controls"]["b_sentence"]["best"] else "sentence"
  vec = steer_lib.unit((sent_avg if vname == "sentence" else cheap_avg)[li[L]])
  ex["say_setting"] = {"vector": vname + " (order-averaged)", "layer": L, "fraction": f}
  for p in four:
    plain_say = scoring.say(lm, p)
    steered_say = R.say_steered(p, L, f * resid[L] * vec)
    ex["say"].append({"pid": p.pid, "best_offers": core.oracle_bids(p), "plain": list(plain_say), "steered": list(steered_say)})
    for name, key in (("a", "a"), ("b_cheap", "b_cheap"), ("b_sentence", "b_sentence")):
      b = res["controls"][key]["best"]
      Lb, fb = b["layer"], b["fraction"]
      if key == "a":
        fn = lambda p1, oi=0, Lb=Lb, fb=fb: R.steer(Lb, fb * resid[Lb] * steer_lib.unit(cheap_order[0, li[Lb]]))(p1)
      else:
        v = steer_lib.unit((sent_avg if key == "b_sentence" else cheap_avg)[li[Lb]])
        fn = R.steer(Lb, fb * resid[Lb] * v)
      ex["top10"].append({"pid": p.pid, "setting": f"{key} L{Lb} f{fb}", "order": 0,
                          "plain": R.top10(p, 0), "steered": R.top10(p, 0, fn)})
  res["extras"] = ex; save()
  log("extras done")

log("STEER CHECKS COMPLETED")
