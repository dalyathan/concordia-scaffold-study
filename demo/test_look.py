"""THE TEST LOOK (TEST_PLAN.md). Scores the frozen adapters on the 72 test cases, once.

  python demo/test_look.py --dry-run     same pipeline on the 24 held-out TUNE cases (no test case is touched);
                                         writes demo_out/test_dryrun.* only
  python demo/test_look.py --execute     the test look; refuses to run unless demo_out/test_look.lock is absent
                                         (it is created first, so a second run is impossible) and demo/test_go.json
                                         (written by the owner's go) exists

Frozen inputs: demo/test_frozen_adapters.json (arm -> run id -> sha256, epoch; verified against the files).
Arm value = mean of the seeds' per-case probabilities. Statistics: unit = cell, paired bootstrap, 10,000
resamples, numpy PCG64 seed 0, 95% percentile interval. Outcome label from TEST_PLAN.md section 6 (see label())."""
import argparse, hashlib, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import common, scoring, steer_lib, textrows
from refimpl import core, runtime
from refimpl.local_gemma2 import LocalGemma2

N, SEED, THRESH = 10000, 0, 0.10
ARMS = ("method", "wrong_rule", "neutral")
ROOT = common.ROOT


def cell_values(cases, per_case):
  cells = sorted({p.cell for p in cases}, key=str)
  return cells, {c: float(np.mean([per_case[p.pid] for p in cases if p.cell == c])) for c in cells}


def boot(d, n=N):
  d = np.asarray(d, float)
  b = np.random.default_rng(SEED).choice(d, size=(n, len(d)), replace=True).mean(1)
  return float(d.mean()), float(np.quantile(b, .025)), float(np.quantile(b, .975)), int((d > 0).sum())


def label(r):
  """Outcome label, TEST_PLAN.md section 6. Clarifications fixed before the look: 'not worse than always-2' = mean
  (always-2 - method) >= 0; 'beats always-2' (reported separately) = lower bound > 0. The base label is SUPPORT,
  PARTIAL or NOT SHOWN; a HARM flag (upper bound of plain - method < 0 over the cells with stated cost >= resale
  value, needing at least 3 such cells) is appended to it and reported."""
  ok = lambda k: r["diff"][k][0] >= THRESH and r["diff"][k][1] > 0
  if ok("wrong_rule") and ok("neutral") and ok("plain") and r["diff"]["always2"][0] >= 0:
    base = "SUPPORT"
  elif r["diff"]["plain"][1] > 0 and r["diff"]["neutral"][1] > 0:
    base = "PARTIAL: improves on plain and neutral, not separated from wrong-rule / always-2"
  else:
    base = "NOT SHOWN: lower bound vs plain <= 0 (read as 'not shown here')"
  h = r["harm_C_ge_V"]
  return base + (" | HARM flag: method worse than plain on the cells with stated cost >= resale value (upper bound < 0)" if h is not None and h[2] < 0 else "")


def main():
  ap = argparse.ArgumentParser()
  ap.add_argument("--dry-run", action="store_true")
  ap.add_argument("--execute", action="store_true")
  a = ap.parse_args()
  assert a.dry_run != a.execute, "choose exactly one of --dry-run / --execute"
  frozen = json.load(open(os.path.join(common.DEMO_DIR, "test_frozen_adapters.json")))
  P = common.prompts_by_id()
  if a.execute:
    lock = os.path.join(ROOT, "demo_out", "test_look.lock")
    if os.path.exists(lock):
      raise SystemExit("the test look has already been started; it runs exactly once")
    if not os.path.exists(os.path.join(common.DEMO_DIR, "test_go.json")):
      raise SystemExit("demo/test_go.json (the owner's go) is missing")
    open(lock, "w").write(time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    cases = [P[i] for i, s in json.load(open(os.path.join(common.DEMO_DIR, "splits.json")))["case_split"].items() if s == "test"]
    assert len(cases) == 72 and all(p.variant in (15, 16, 17, 18) for p in cases)
    tag = "test_look"
  else:
    cases = steer_lib.lora_cases("lora_tune")
    tag = "test_dryrun"
  # verify the frozen adapters
  for arm, runs in frozen.items():
    for rid, v in runs.items():
      h = hashlib.sha256(open(os.path.join(scoring.ADAPTER_DIR, rid, "adapter_model.safetensors"), "rb").read()).hexdigest()
      assert h == v["sha256"], f"adapter {rid} hash mismatch"
  names = [rid for runs in frozen.values() for rid in runs]
  model, tok = runtime.load_gemma("9b", "cuda")
  lm = LocalGemma2(model, tok)
  peft = scoring.load_adapters(lm, names)
  plain_saved = {c["pid"]: {int(k): v for k, v in c["probs"].items()} for c in common.load_cases()}
  mass_saved = {c["pid"]: float(c["letter_mass"]) for c in common.load_cases()}
  # adapter-off check on 4 cases against the saved plain probabilities
  chk = []
  with scoring.adapter_context(peft, None):
    for p in cases[:4]:
      r = scoring.score(lm, p)
      chk.append(max(abs(r.probs[k] - plain_saved[p.pid][k]) for k in core.PRICES))
  assert max(chk) < 1e-4, f"adapter off does not reproduce plain: {chk}"
  per = {}      # run -> {pid: probs}
  mass = {}
  say = {}
  for rid in names:
    with scoring.adapter_context(peft, rid):
      rs = {p.pid: scoring.score(lm, p) for p in cases}
      per[rid] = {k: {int(kk): float(vv) for kk, vv in r.probs.items()} for k, r in rs.items()}
      mass[rid] = {k: float(r.mass) for k, r in rs.items()}
      if rid in frozen["method"]:
        say[rid] = {p.pid: scoring.say(lm, p)[1] for p in cases}
    print("scored", rid, flush=True)
  with scoring.adapter_context(peft, None):
    textrs = {p.pid: scoring.score(lm, p, notes=textrows.METHOD) for p in cases}
    say["plain"] = {p.pid: scoring.say(lm, p)[1] for p in cases}
  text_probs = {k: {int(kk): float(vv) for kk, vv in r.probs.items()} for k, r in textrs.items()}
  # arm values (mean of seeds' probabilities)
  arm = {}
  for A, runs in frozen.items():
    arm[A] = {p.pid: {k: float(np.mean([per[r][p.pid][k] for r in runs])) for k in core.PRICES} for p in cases}
  arm["plain"] = {p.pid: plain_saved[p.pid] for p in cases}
  arm["always2"] = {p.pid: {k: float(k == 2) for k in core.PRICES} for p in cases}
  arm["method_text_in_prompt"] = text_probs
  soft = {k: {p.pid: core.soft_regret(p, v[p.pid]) for p in cases} for k, v in arm.items()}
  cells, cv = None, {}
  for k in soft:
    cells, cv[k] = cell_values(cases, soft[k])
  res = {"tag": tag, "n_cases": len(cases), "n_cells": len(cells), "cells": [str(c) for c in cells],
         "arm_soft_regret": {k: float(np.mean(list(v.values()))) for k, v in cv.items()}, "diff": {}}
  for k in ("plain", "neutral", "wrong_rule", "always2"):
    res["diff"][k] = list(boot([cv[k][c] - cv["method"][c] for c in cells]))      # control - method
  by = lambda sel: [c for c in cells if sel(P[[p.pid for p in cases if p.cell == c][0]])]
  lt = by(lambda p: p.C is not None and p.C < p.V)
  ge = by(lambda p: p.C is not None and p.C >= p.V)
  nn = by(lambda p: p.C is None)
  res["split"] = {n: {k: float(np.mean([cv[k][c] - cv["method"][c] for c in cs])) for k in ("plain", "neutral", "wrong_rule", "always2")}
                  for n, cs in (("C<V", lt), ("C>=V", ge), ("no cost", nn))}
  res["harm_C_ge_V"] = list(boot([cv["plain"][c] - cv["method"][c] for c in ge])) if len(ge) >= 3 else None
  res["loo_wrong_rule"] = {str(c): float(np.mean([cv["wrong_rule"][x] - cv["method"][x] for x in cells if x != c])) for c in cells}
  exp = {k: {c: float(np.mean([core.expected_bid(arm[k][p.pid]) for p in cases if p.cell == c])) for c in cells} for k in arm}
  sl = lambda e: float(np.polyfit([P[[p.pid for p in cases if p.cell == c][0]].C for c in lt], [e[c] for c in lt], 1)[0]) if len({P[[p.pid for p in cases if p.cell == c][0]].C for c in lt}) > 1 else None
  res["slope_C<V_descriptive"] = {k: sl(exp[k]) for k in exp}
  res["per_seed_soft_regret"] = {rid: float(np.mean(list(cell_values(cases, {p.pid: core.soft_regret(p, per[rid][p.pid]) for p in cases})[1].values()))) for rid in names}
  res["mass_ratio_method"] = float(np.mean([np.mean([mass[r][p.pid] for r in frozen["method"]]) for p in cases]) / np.mean([mass_saved[p.pid] for p in cases]))
  hr = {k: {p.pid: (core.hard_regret(p, v[p.pid]) if v[p.pid] is not None else 1.0) for p in cases} for k, v in say.items() if k in ("plain", *frozen["method"])}
  ms = {p.pid: float(np.mean([hr[r][p.pid] for r in frozen["method"]])) for p in cases}
  res["free_text_hard_regret"] = {"plain": float(np.mean(list(cell_values(cases, hr["plain"])[1].values()))), "method": float(np.mean(list(cell_values(cases, ms)[1].values())))}
  res["adapter_off_check_max_abs_diff"] = float(max(chk))
  res["label"] = label(res)
  out = os.path.join(ROOT, "demo_out", tag)
  json.dump(res, open(out + ".json", "w"), indent=1, default=float)
  L = [f"# {tag}: {len(cases)} cases, {len(cells)} cells ({'TEST LOOK' if a.execute else 'DRY RUN on held-out TUNE cases, not a result'})", "",
       f"**Outcome label: {res['label']}**", "", "| Arm | Soft regret |", "| --- | --- |"]
  L += [f"| {k} | {v:.3f} |" for k, v in res["arm_soft_regret"].items()]
  L += ["", "Difference control - method, paired cell bootstrap (10,000, seed 0): mean [95% interval], cells where method better", ""]
  L += [f"- {k}: {v[0]:+.3f} [{v[1]:+.3f}, {v[2]:+.3f}], {v[3]} of {len(cells)}" for k, v in res["diff"].items()]
  L += ["", "Split of the difference by cell type (descriptive):", ""] + [f"- {n}: " + ", ".join(f"{k} {v:+.3f}" for k, v in d.items()) for n, d in res["split"].items()]
  if res["harm_C_ge_V"]:
    L += ["", f"Method vs plain on C>=V cells (harm check): {res['harm_C_ge_V'][0]:+.3f} [{res['harm_C_ge_V'][1]:+.3f}, {res['harm_C_ge_V'][2]:+.3f}] (plain - method)"]
  L += ["", f"Leave-one-cell-out (wrong-rule - method): {res['loo_wrong_rule']}", "", f"Slope of expected offer on stated cost, C<V cells (descriptive): {res['slope_C<V_descriptive']}",
        "", f"Per-seed soft regret: {res['per_seed_soft_regret']}", "", f"Letter mass method / plain: {res['mass_ratio_method']:.2f}; free-text hard regret: {res['free_text_hard_regret']}",
        f"Adapter-off check max abs diff vs saved plain: {res['adapter_off_check_max_abs_diff']:.2e}"]
  open(out + ".md", "w").write("\n".join(L) + "\n")
  print("\n".join(L))


if __name__ == "__main__":
  main()
