"""THE TEST LOOK (TEST_PLAN.md). Two separated steps:

  python demo/test_look.py --dry-run     GPU: the same pipeline on the 24 held-out TUNE cases (no test case touched);
                                         writes demo_out/test_dryrun_raw.json / .json / .md
  python demo/test_look.py --execute     GPU: validate everything, THEN write demo_out/test_look.lock, then score and save
                                         raw results (demo_out/test_look_raw.json) and run the analysis. Needs demo/test_go.json.
  python demo/test_look.py --analyze [--tag test_look|test_dryrun]
                                         CPU only: recompute statistics, label and report from the raw file; never loads the model.

Rerun policy: a failure before the lock is written (validation, model load, plain re-scoring) burns nothing and may be
rerun; once the lock exists the look has started, raw results are saved as each run finishes, and only --analyze may be
repeated. Frozen inputs: demo/test_frozen_adapters.json (sha256 of each adapter and its config). Arm value = mean of the
seeds' per-case probabilities. Statistics: unit = cell, paired bootstrap, 10,000 resamples, numpy PCG64 seed 0, 95%
percentile interval (approximate at n = 18 skewed cells). Outcome labels: TEST_PLAN.md sections 6 and 9."""
import argparse, hashlib, json, os, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import common, scoring, steer_lib, textrows
from refimpl import core

N, SEED, THRESH = 10000, 0, 0.10
ROOT = common.ROOT
DEMO = common.DEMO_DIR
CASE_HASH_PREFIX = "c232e47c86ae089d"
DEV_VERDICT = "frozen development verdict: NOT PASSED (owner's rule, wrong-rule lower bound -0.003); this test look is a separate exploratory-derived question"


def sha(path):
  return hashlib.sha256(open(path, "rb").read()).hexdigest()


def cell_vals(cases, per_case):
  cells = sorted({p.cell for p in cases}, key=str)
  return cells, {c: float(np.mean([per_case[p.pid] for p in cases if p.cell == c])) for c in cells}


def boot(d, n=N):
  d = np.asarray(d, float)
  b = np.random.default_rng(SEED).choice(d, size=(n, len(d)), replace=True).mean(1)
  return [float(d.mean()), float(np.quantile(b, .025)), float(np.quantile(b, .975)), int((d > 0).sum())]


def label(r):
  """Outcome label (TEST_PLAN.md sections 6, 9). Base label from the comparators; text names the conditions that failed.
  SUPPORT: for wrong-rule, neutral and plain: D >= 0.10 and lower bound > 0, and mean(always-2 - method) >= 0.
  PARTIAL: lower bound > 0 vs plain and vs neutral, SUPPORT not met.   PLAIN-ONLY: lower bound > 0 vs plain only.
  NOT SHOWN: lower bound vs plain <= 0.   HARM flag appended (upper bound of plain - method < 0 over >= 3 C>=V cells)."""
  d = r["diff"]
  ok = lambda k: d[k][0] >= THRESH and d[k][1] > 0
  beats2 = d["always2"][1] > 0
  if ok("wrong_rule") and ok("neutral") and ok("plain") and d["always2"][0] >= 0:
    base = f"SUPPORT (beats always-2 with lower bound > 0: {'yes' if beats2 else 'no'})"
  elif d["plain"][1] > 0 and d["neutral"][1] > 0:
    failed = [k for k in ("wrong_rule", "neutral", "plain") if not ok(k)] + ([] if d["always2"][0] >= 0 else ["always2 (method worse in mean)"])
    base = "PARTIAL: lower bound > 0 vs plain and neutral; SUPPORT not met because: " + ", ".join(failed)
  elif d["plain"][1] > 0:
    base = "PLAIN-ONLY: separated from plain but not from neutral-distil (lower bound <= 0 vs neutral)"
  else:
    base = "NOT SHOWN: lower bound vs plain <= 0 (read as 'not shown here')"
  h = r["harm_C_ge_V"]
  return base + (" | HARM flag: method worse than plain on the cells with stated cost >= resale value (upper bound < 0)" if h is not None and h[2] < 0 else "")


def get_cases(tag):
  P = common.prompts_by_id()
  if tag == "test_look":
    sp = json.load(open(os.path.join(DEMO, "splits.json")))["case_split"]
    ids = sorted(i for i, s in sp.items() if s == "test")
    assert len(ids) == 72 and hashlib.sha256("\n".join(ids).encode()).hexdigest()[:16] == CASE_HASH_PREFIX, "test case list differs from the plan"
    cases = [P[i] for i in ids]
    assert all(p.variant in (15, 16, 17, 18) for p in cases) and len({p.cell for p in cases}) == 18
    lo = json.load(open(os.path.join(DEMO, "splits_lora.json")))["case_split"]
    dev = {P[i].cell for i in lo}
    assert not ({p.cell for p in cases} & dev), "test cells overlap train/tune cells"
    return cases
  return steer_lib.lora_cases("lora_tune")


def analyze(tag):
  cases = get_cases(tag)
  P = common.prompts_by_id()
  raw = json.load(open(os.path.join(ROOT, "demo_out", f"{tag}_raw.json")))
  frozen = json.load(open(os.path.join(DEMO, "test_frozen_adapters.json")))
  plain_saved = {c["pid"]: {int(k): v for k, v in c["probs"].items()} for c in common.load_cases()}
  mass_saved = {c["pid"]: float(c["letter_mass"]) for c in common.load_cases()}
  per = {rid: {pid: {int(k): v for k, v in pr.items()} for pid, pr in d.items()} for rid, d in raw["per"].items()}
  text_probs = {pid: {int(k): v for k, v in pr.items()} for pid, pr in raw["text_probs"].items()}
  arm = {A: {p.pid: {k: float(np.mean([per[r][p.pid][k] for r in runs])) for k in core.PRICES} for p in cases} for A, runs in frozen.items()}
  arm["plain"] = {p.pid: plain_saved[p.pid] for p in cases}
  arm["always2"] = {p.pid: {k: float(k == 2) for k in core.PRICES} for p in cases}
  arm["method_text_in_prompt"] = text_probs
  soft = {k: {p.pid: core.soft_regret(p, v[p.pid]) for p in cases} for k, v in arm.items()}
  cv = {}
  for k in soft:
    cells, cv[k] = cell_vals(cases, soft[k])
  first = {c: [p for p in cases if p.cell == c][0] for c in cells}
  res = {"tag": tag, "n_cases": len(cases), "n_cells": len(cells), "cells": [str(c) for c in cells], "dev_verdict": DEV_VERDICT,
         "arm_soft_regret": {k: float(np.mean(list(v.values()))) for k, v in cv.items()}, "diff": {}}
  for k in ("plain", "neutral", "wrong_rule", "always2"):
    res["diff"][k] = boot([cv[k][c] - cv["method"][c] for c in cells])                 # control - method
  lt = [c for c in cells if first[c].C is not None and first[c].C < first[c].V]
  ge = [c for c in cells if first[c].C is not None and first[c].C >= first[c].V]
  nn = [c for c in cells if first[c].C is None]
  res["split"] = {n: {k: float(np.mean([cv[k][c] - cv["method"][c] for c in cs])) for k in ("plain", "neutral", "wrong_rule", "always2")} if cs else None
                  for n, cs in (("C<V", lt), ("C>=V", ge), ("no cost", nn))}
  res["stratum_C<V_interval"] = {k: boot([cv[k][c] - cv["method"][c] for c in lt]) for k in ("plain", "neutral", "wrong_rule", "always2")} if len(lt) >= 3 else None
  res["harm_C_ge_V"] = boot([cv["plain"][c] - cv["method"][c] for c in ge]) if len(ge) >= 3 else None
  res["loo_wrong_rule"] = {str(c): float(np.mean([cv["wrong_rule"][x] - cv["method"][x] for x in cells if x != c])) for c in cells}
  exp = {k: {c: float(np.mean([core.expected_bid(arm[k][p.pid]) for p in cases if p.cell == c])) for c in cells} for k in arm}
  xs = [first[c].C for c in lt]
  res["slope_C<V_descriptive"] = {k: (float(np.polyfit(xs, [exp[k][c] for c in lt], 1)[0]) if len(set(xs)) > 1 else None) for k in exp}
  best = {c: core.oracle_bid_point(first[c]) for c in cells}
  res["C<V_cells_where_method_offer_closer_to_best_than_plain"] = [int(sum(abs(exp["method"][c] - best[c]) < abs(exp["plain"][c] - best[c]) for c in lt)), len(lt)]
  res["per_seed_soft_regret"] = {rid: float(np.mean(list(cell_vals(cases, {p.pid: core.soft_regret(p, per[rid][p.pid]) for p in cases})[1].values()))) for rid in per}
  mm = {rid: {pid: float(v) for pid, v in raw["mass"][rid].items()} for rid in frozen["method"]}
  res["mass_ratio_method"] = float(np.mean([np.mean([mm[r][p.pid] for r in frozen["method"]]) for p in cases]) / np.mean([mass_saved[p.pid] for p in cases]))
  # free text: unparsable answers are dropped (as in lora.py); parse-failure rate reported
  say = raw["say"]
  def hr(key):
    return {p.pid: core.hard_regret(p, say[key][p.pid][1]) for p in cases if say[key][p.pid][1] is not None}
  def cm(d):
    return float(np.mean(list(analysis_cell_means(d, cases).values())))
  from refimpl import analysis
  analysis_cell_means = analysis.cell_means
  plain_hr = hr("plain")
  seeds_hr = [hr(r) for r in frozen["method"]]
  res["free_text_hard_regret"] = {"plain": cm(plain_hr), "method_seeds": [cm(h) for h in seeds_hr],
                                  "method_mean": float(np.mean([cm(h) for h in seeds_hr])),
                                  "parse_failure_rate": {k: float(np.mean([v[p.pid][1] is None for p in cases])) for k, v in say.items()}}
  res["adapter_off_check_max_abs_diff"] = raw["adapter_off_check_max_abs_diff"]
  res["label"] = label(res)
  out = os.path.join(ROOT, "demo_out", tag)
  json.dump(res, open(out + ".json", "w"), indent=1, default=float)
  fmt = lambda v, n=len(cells): f"{v[0]:+.3f} [{v[1]:+.3f}, {v[2]:+.3f}], {v[3]} of {n} cells"
  L = [f"# {tag}: {len(cases)} cases, {len(cells)} cells ({'TEST LOOK' if tag == 'test_look' else 'DRY RUN on held-out TUNE cases, not a result'})", "",
       f"**Outcome label: {res['label']}**", "", DEV_VERDICT, "",
       "| Arm | Soft regret |", "| --- | --- |"] + [f"| {k} | {v:.3f} |" for k, v in res["arm_soft_regret"].items()]
  L += ["", "Comparator table: difference control - method (paired cell bootstrap 10,000, seed 0; threshold D >= 0.10 and lower bound > 0 for wrong-rule, neutral, plain):", "",
        "| Control | D [95% interval], cells better | D >= 0.10 | lower bound > 0 |", "| --- | --- | --- | --- |"]
  for k, v in res["diff"].items():
    L.append(f"| {k} | {fmt(v)} | {'yes' if v[0] >= THRESH else 'no'} | {'yes' if v[1] > 0 else 'no'} |")
  L += ["", "Split of the difference by cell type (descriptive): " + "; ".join(f"{n}: " + (", ".join(f"{k} {v:+.3f}" for k, v in d.items()) if d else "no cells") for n, d in res["split"].items()), ""]
  if res["stratum_C<V_interval"]:
    L += ["Declared secondary, C<V stratum (cells: " + str(len(lt)) + "), control - method: " + "; ".join(f"{k} {fmt(v, len(lt))}" for k, v in res["stratum_C<V_interval"].items()), ""]
  L += [f"Harm check (plain - method over C>=V cells): {res['harm_C_ge_V']}", f"Leave-one-cell-out (wrong-rule - method): {res['loo_wrong_rule']}",
        f"Slope of expected offer on stated cost, C<V cells (descriptive): {res['slope_C<V_descriptive']}",
        f"C<V cells where the method's expected offer is closer to the best offer than plain's: {res['C<V_cells_where_method_offer_closer_to_best_than_plain']}",
        f"Per-run soft regret: {res['per_seed_soft_regret']}", f"Letter mass method / plain: {res['mass_ratio_method']:.2f}",
        f"Free-text hard regret (descriptive): {res['free_text_hard_regret']}", f"Adapter-off check max abs diff vs saved plain (all cases): {res['adapter_off_check_max_abs_diff']:.2e}"]
  open(out + ".md", "w").write("\n".join(L) + "\n")
  print("\n".join(L))


def validate(tag, frozen):
  for arm, runs in frozen.items():
    for rid, v in runs.items():
      d = os.path.join(scoring.ADAPTER_DIR, rid)
      assert sha(os.path.join(d, "adapter_model.safetensors")) == v["sha256"], f"adapter {rid} hash mismatch"
      assert sha(os.path.join(d, "adapter_config.json")) == v["config_sha256"], f"adapter config {rid} hash mismatch"
  info = {}
  if tag == "test_look":
    plan = open(os.path.join(ROOT, "TEST_PLAN.md")).read()
    assert sha(os.path.abspath(__file__)) in plan, "this script's sha256 is not the one recorded in TEST_PLAN.md"
    assert subprocess.run(["git", "diff", "--quiet", "HEAD", "--", "demo", "refimpl", "TEST_PLAN.md"], cwd=ROOT).returncode == 0, "uncommitted changes in demo/ refimpl/ TEST_PLAN.md"
    go = json.load(open(os.path.join(DEMO, "test_go.json")))
    assert go.get("go") is True and go.get("section_9_approved") is True and go.get("script_sha256") == sha(os.path.abspath(__file__)), "test_go.json does not authorise this script"
    info["commit"] = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
  import torch, transformers, peft
  info.update({"script_sha256": sha(os.path.abspath(__file__)), "torch": torch.__version__, "transformers": transformers.__version__, "peft": peft.__version__,
               "gpu": torch.cuda.get_device_name(0),
               "files": {f: sha(os.path.join(ROOT, f)) for f in ("demo/scoring.py", "demo/textrows.py", "demo/common.py", "demo/steer_lib.py", "refimpl/core.py", "demo/splits.json", "demo/test_frozen_adapters.json", os.path.relpath(common.CASES, ROOT))}})
  return info


def run(tag):
  from refimpl import runtime
  from refimpl.local_gemma2 import LocalGemma2
  lock = os.path.join(ROOT, "demo_out", "test_look.lock")
  if tag == "test_look" and os.path.exists(lock):
    raise SystemExit("the test look has already been started; it runs exactly once (only --analyze may be repeated)")
  frozen = json.load(open(os.path.join(DEMO, "test_frozen_adapters.json")))
  cases = get_cases(tag)
  info = validate(tag, frozen)
  names = [rid for runs in frozen.values() for rid in runs]
  model, tok = runtime.load_gemma("9b", "cuda")
  lm = LocalGemma2(model, tok)
  peft = scoring.load_adapters(lm, names)
  plain_saved = {c["pid"]: {int(k): v for k, v in c["probs"].items()} for c in common.load_cases()}
  with scoring.adapter_context(peft, None):                      # plain re-scored on all cases with adapters off
    chk = [max(abs(scoring.score(lm, p).probs[k] - plain_saved[p.pid][k]) for k in core.PRICES) for p in cases]
  assert max(chk) < 1e-4, f"adapter off does not reproduce plain on all cases: max {max(chk)}"
  if tag == "test_look":
    open(lock, "w").write(json.dumps({"started": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), **info}, indent=1))   # the look starts here
  rawp = os.path.join(ROOT, "demo_out", f"{tag}_raw.json")
  raw = {"info": info, "adapter_off_check_max_abs_diff": float(max(chk)), "per": {}, "per_order": {}, "mass": {}, "say": {}, "text_probs": {}}
  save = lambda: json.dump(raw, open(rawp, "w"), default=float)
  for rid in names:
    with scoring.adapter_context(peft, rid):
      rs = {p.pid: scoring.score(lm, p) for p in cases}
      raw["per"][rid] = {k: {str(kk): float(vv) for kk, vv in r.probs.items()} for k, r in rs.items()}
      raw["per_order"][rid] = {k: [{str(kk): float(vv) for kk, vv in o.items()} for o in r.per_order] for k, r in rs.items()}
      raw["mass"][rid] = {k: float(r.mass) for k, r in rs.items()}
      if rid in frozen["method"]:
        raw["say"][rid] = {p.pid: list(scoring.say(lm, p)) for p in cases}
    save()
    print("scored", rid, flush=True)
  with scoring.adapter_context(peft, None):
    raw["text_probs"] = {p.pid: {str(k): float(v) for k, v in scoring.score(lm, p, notes=textrows.METHOD).probs.items()} for p in cases}
    raw["say"]["plain"] = {p.pid: list(scoring.say(lm, p)) for p in cases}
  save()
  print("raw saved", flush=True)


if __name__ == "__main__":
  ap = argparse.ArgumentParser()
  g = ap.add_mutually_exclusive_group(required=True)
  g.add_argument("--dry-run", action="store_true")
  g.add_argument("--execute", action="store_true")
  g.add_argument("--analyze", action="store_true")
  ap.add_argument("--tag", default="test_look")
  a = ap.parse_args()
  if a.analyze:
    analyze(a.tag)
  else:
    tag = "test_look" if a.execute else "test_dryrun"
    run(tag)
    analyze(tag)
