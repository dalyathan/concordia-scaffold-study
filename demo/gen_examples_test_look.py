"""The ONE test look for the worked-examples arm (GEN_EXAMPLES_TEST_PLAN.md, approved by the owner with the correction that the test sets are
the GENERATED dataset's test_same and test_hard; the original study's sets are never touched).

  python demo/gen_examples_test_look.py --mode preflight   GPU. TUNE cells only: every frozen adapter is reloaded and must reproduce its
                                                          stored tune probabilities; adapter-off must reproduce the saved plain scores;
                                                          hashes, leakage check and the label self-test run. Writes demo/gen/test_preflight.json.
  python demo/gen_examples_test_look.py --mode look        GPU, run ONCE. Needs a passing preflight made by this exact script (sha256),
                                                          writes a lock first, scores test_same and test_hard with plain + 10 frozen adapters,
                                                          then runs the analysis (CPU part) and writes demo_out/gen_examples_test_report.md.
  python demo/gen_examples_test_look.py --mode analyse     CPU. Re-runs only the analysis on the saved test scores (for a crash after scoring).

No adapter, seed, epoch or learning rate is chosen here: the frozen list is built from the stored run files and checked against the sha256
values written in GEN_EXAMPLES_TEST_PLAN.md section 6. Scoring path = gen_lora.score_case (five cyclic orders, first-token letter
probabilities renormalised over the five letters, order- and name-variant-averaged), the same as for tune."""
from __future__ import annotations

import argparse, collections, contextlib, glob, hashlib, json, os, subprocess, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import common
import gen_cases as g

ROOT = common.ROOT
GEN = g.OUT
OUTD = os.path.join(ROOT, "demo_out", "gen_examples_test")
REPORT = os.path.join(ROOT, "demo_out", "gen_examples_test_report.md")
SUMMARY = os.path.join(GEN, "gen_examples_test_summary.json")
PREFLIGHT = os.path.join(GEN, "test_preflight.json")
LOCK = os.path.join(GEN, "test_look_lock.json")
FROZEN_JSON = os.path.join(GEN, "test_frozen_adapters.json")
HASHES = {  # computed before the look (GEN_TEST_PLAN.md section 2)
    "demo/gen/cells.json": "428925050d28a3d0bc23b87551aa837ae0f7daa4465ceb45f5973dbb415bfe86",
    "demo/gen/cases.jsonl": "63e26a25e8a945b68cbcefe1b3433a1b443d7a32da93922e20498d994f7666f0",
    "demo/gen_cases.py": "cc0024b70ee5d53e4dad5966aa312200d9d53fb00248b3826ec4f6b2af01044f",
}
FROZEN_FINGERPRINTS = {"test_same": "0538a2a2bd15e74f66e8bd2fabe1fb7856a457053a33719c28ebc986fae31c40",
                       "test_hard": "c4b08aba9b7b8c367483bb7e0bed9a242b7c322117f1780bf4deda700c55d520"}
# arm name -> (run_id, expected adapter sha256). The sha256 values are those in GEN_EXAMPLES_TEST_PLAN.md section 6.
ADAPTERS = {
    "claude_examples_s0": ("gen_claude_examples_lr1e-04_s0", "74b90cbeaa4c672e571843f3368072e77d24ac06e0f0c908e8011df4b361b243"),
    "claude_examples_s1": ("gen_claude_examples_lr1e-04_s1", "c77a5514ea3edaea0418ba5f0043dfe2bb43608179cc935c63af51be2b6f3bed"),
    "claude_examples_s2": ("gen_claude_examples_lr1e-04_s2", "390def343a67080384aea8953c6b5fed6d0495b0b823aa78e2570a313d0a3ca3"),
    "cheapest_label_s0": ("gen_cheapest_label_lr1e-04_s0", "83aa94c6fc8054c653d1173c77ff94fcad4b2668ea3481f34c01ff37954f25af"),
    "shuffled_claude_s0": ("gen_shuffled_claude_lr1e-04_s0", "9d1f75175de04cfa94f1aca1c0bc91a583e84e526e83705a7882f37a80736e38"),
    "ceiling_s0": ("gen_answer_only_lr1e-04_s0", "07036c98e1042a00be89a27290b053ad9d49418089b3fc06880373264745728c"),
    "teacher_s0": ("gen_teacher_lr1e-04_s0", "e2189c1dd2972d93e8a30083a0d18e34f7f83037515af8942ebf7d6035707163"),
    "teacher_s1": ("gen_teacher_lr1e-04_s1", "e1fb9dc0649278c241cec409dfef1df98e67e90d202e43c459a267136d723011"),
    "teacher_s2": ("gen_teacher_lr1e-04_s2", "4f2d6e962b636f7f253f483bf7bc3f5f01a8e32de716e8e696ad8ab17fb2a082"),
    "method_s0": ("gen_method_original_lr1e-04_s0", "ceba0964a2e412f5420576cf6dde1fb1a7839f83ef0c9d31660c3cb3fb597d82"),
    "method_s1": ("gen_method_original_lr1e-04_s1", "cb9b1d9ab2b192b80bfdb44fd1f6df14987028599bd89ea7a63015063fdd7444"),
    "method_s2": ("gen_method_original_lr1e-04_s2", "501559cc4583b2b8638c5a7497330b93115d07deae55e297726b0f1690b204a7"),
}
FAMILY = {"a": ["claude_examples_s0", "claude_examples_s1", "claude_examples_s2"], "b": ["cheapest_label_s0"], "c": ["shuffled_claude_s0"],
          "ceiling": ["ceiling_s0"], "teacher": ["teacher_s0", "teacher_s1", "teacher_s2"], "method": ["method_s0", "method_s1", "method_s2"]}
TEST_SPLITS = ("test_same", "test_hard")
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
SELF = os.path.abspath(__file__)


def load_data():
  cells = {c["cell"]: c for c in json.load(open(os.path.join(GEN, "cells.json")))["cells"]}
  cases = [json.loads(l) for l in open(os.path.join(GEN, "cases.jsonl"))]
  return cells, cases


def frozen_adapters():
  out = {}
  for name, (rid, want) in ADAPTERS.items():
    r = json.load(open(os.path.join(ROOT, "demo_out", "gen_lora", rid + ".json")))
    d = os.path.join(ROOT, r["adapter_dir"])
    got = sha(os.path.join(d, "adapter_model.safetensors"))
    assert got == r["adapter_sha256"], f"{name}: adapter file differs from the stored run result"
    assert want is None or got == want, f"{name}: adapter sha256 differs from the plan"
    assert r["lr"] == 1e-4 and r["arm"] in ("claude_examples", "cheapest_label", "shuffled_claude", "answer_only", "teacher", "method_original")
    out[name] = {"run_id": rid, "dir": d, "sha256": got, "best_epoch": r["best_epoch"], "stored_tune": r["tune_probs_best"]}
  return out


def verify_hashes(cells, cases):
  for p, h in HASHES.items():
    if h:
      assert sha(os.path.join(ROOT, p)) == h, f"hash mismatch for {p}"
  import gen_lora
  assert sha(os.path.join(GEN, "claude_labels.json")) == gen_lora.FROZEN_LABELS, "claude_labels.json differs from the frozen hash"
  fp = g.fingerprints(list(cells.values()), cases)
  for k, h in FROZEN_FINGERPRINTS.items():
    assert fp[k]["sha256"] == h, f"fingerprint mismatch for {k}"
    assert fp[k]["n_cells"] == {"test_same": 60, "test_hard": 62}[k]
  assert all(c["grid"][0] == min(c["grid"]) for c in cells.values()), "grid position 0 must be the cheapest price"
  return fp


# ------------------------------------------------------------------------------------------------ scoring
def make_scorer():
  import torch
  from peft import PeftModel
  from refimpl import runtime
  from refimpl.local_gemma2 import LocalGemma2
  import gen_lora
  model, tok = runtime.load_gemma("9b", "cuda")
  lm = LocalGemma2(model, tok)
  return lm, gen_lora.score_case


def score_set(lm, score_case, cases, label, peft=None, adapter=None):
  """-> {cid: (probs list, mass)}"""
  ctx = contextlib.nullcontext()
  if peft is not None:
    if adapter is None:
      ctx = peft.disable_adapter()
    else:
      peft.set_adapter(adapter)
  out = {}
  t0 = time.time()
  with ctx:
    for i, c in enumerate(cases):
      p, _, m = score_case(lm, c)
      out[c["cid"]] = ([float(x) for x in p], float(m))
      if i % 40 == 0:
        print(f"  {label}: {i}/{len(cases)} {time.time() - t0:.0f}s", flush=True)
  return out


def run_scoring(split_names, mode):
  cells, cases = load_data()
  fp = verify_hashes(cells, cases)
  fr = frozen_adapters()
  use = [c for c in cases if c["split"] in split_names]
  assert use and all(c["split"] in split_names for c in use)
  if mode == "preflight":
    assert set(split_names) == {"tune"}
  else:
    assert set(split_names) <= set(TEST_SPLITS)
  lm, score_case = make_scorer()
  from peft import PeftModel
  names = list(ADAPTERS)
  peft = PeftModel.from_pretrained(lm.model, fr[names[0]]["dir"], adapter_name=names[0])
  for n in names[1:]:
    peft.load_adapter(fr[n]["dir"], adapter_name=n)
  peft.eval()
  for _, prm in peft.named_parameters():
    if "lora_" in _ and prm.dtype != __import__("torch").float32:
      prm.data = prm.data.float()
  os.makedirs(OUTD, exist_ok=True)
  tag = "tune_preflight" if mode == "preflight" else "test"
  res = {}
  for arm in ["plain"] + names:
    f = os.path.join(OUTD, f"{tag}_{arm}.json")
    if os.path.exists(f):
      res[arm] = json.load(open(f)); print(f"  {arm}: reuse {f}", flush=True); continue
    sc = score_set(lm, score_case, use, arm, peft, None if arm == "plain" else arm)
    json.dump(sc, open(f, "w"))
    res[arm] = sc
  return res, fr, cells, cases


def preflight():
  res, fr, cells, cases = run_scoring(("tune",), "preflight")
  plain_saved = {r["cid"]: r for r in map(json.loads, open(os.path.join(ROOT, "demo_out", "gen_plain_scores.jsonl")))}
  worst = {}
  worst["plain"] = max(abs(a - b) for cid, (p, _) in res["plain"].items() for a, b in zip(p, plain_saved[cid]["probs"]))
  for n, f in fr.items():
    worst[n] = max(abs(a - b) for cid, (p, _) in res[n].items() for a, b in zip(p, f["stored_tune"][cid]))
  ok = worst["plain"] < 1e-3 and all(v < 1e-3 for k, v in worst.items() if k != "plain")
  leak = leakage_check(cells, cases)
  selftest()
  st = {"ok": bool(ok and not leak), "max_abs_diff": worst, "leakage_files": leak, "script_sha256": sha(SELF), "adapters": {k: {x: v[x] for x in ("run_id", "sha256", "best_epoch")} for k, v in fr.items()},
        "time": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())}
  json.dump(st, open(PREFLIGHT, "w"), indent=1)
  json.dump({k: {x: v[x] for x in ("run_id", "sha256", "best_epoch")} for k, v in fr.items()}, open(FROZEN_JSON, "w"), indent=1)
  print("PREFLIGHT", "OK" if st["ok"] else "FAILED", json.dumps(worst), flush=True)
  assert st["ok"], "preflight failed"


def leakage_check(cells, cases):
  """No existing output under demo_out/ or demo/gen/ may contain a test case or cell id (other than the case/cell/fingerprint files)."""
  ids = {c["cid"] for c in cases if c["split"] in TEST_SPLITS} | {c["cell"] for c in cases if c["split"] in TEST_SPLITS}
  skip = {"cases.jsonl", "cells.json", "fingerprints.json", "fingerprints_v2.json"}
  bad = []
  for root in (os.path.join(ROOT, "demo_out"), GEN):
    for dp, dn, fn in os.walk(root):
      if "adapters" in dp.split(os.sep) or "gen_examples_test" in dp:
        continue
      for f in fn:
        if f in skip or not f.endswith((".json", ".jsonl", ".md", ".txt", ".log")) or f.startswith("gen_examples_test") or f.startswith("test_"):
          continue
        p = os.path.join(dp, f)
        try:
          txt = open(p, errors="ignore").read()
        except OSError:
          continue
        if any(i in txt for i in ids):
          bad.append(os.path.relpath(p, ROOT))
  return bad


# ------------------------------------------------------------------------------------------------ analysis
def boot(d):
  v = np.asarray(d, float)
  b = np.random.default_rng(0).choice(v, size=(10000, len(v)), replace=True).mean(1)
  return float(v.mean()), float(np.quantile(b, .025)), float(np.quantile(b, .975))


fmt = lambda b: f"{b[0]:+.3f} [{b[1]:+.3f}, {b[2]:+.3f}]"


def selftest():
  b = boot([0.1, 0.2, 0.15, 0.3, 0.25, 0.2]); assert b[1] > 0
  b = boot([-0.1, 0.2, -0.15, 0.3, -0.25, 0.2]); assert b[1] < 0 < b[2]
  assert abs(boot([1.0] * 5)[0] - 1.0) < 1e-12


def analyse(res=None, report=None, summary_path=None):
  cells, cases = load_data()
  tr = json.load(open(os.path.join(GEN, "lora_train_cells.json")))
  if res is None:
    res = {}
    for f in glob.glob(os.path.join(OUTD, "test_*.json")):
      res[os.path.basename(f)[5:-5]] = json.load(open(f))
  by_cell = {}
  for c in cases:
    if c["split"] in TEST_SPLITS:
      by_cell.setdefault(c["cell"], []).append(c["cid"])
  sets = {"test_same": sorted(k for k in by_cell if cells[k]["split"] == "test_same"),
          "test_hard": sorted(k for k in by_cell if cells[k]["split"] == "test_hard")}
  for sl in ("hard_V", "hard_grid", "hard_wording"):
    sets[f"test_hard/{sl}"] = sorted(k for k in by_cell if cells[k]["slice"] == sl)
  sets["test_hard/hard_grid D"] = sorted(k for k in sets["test_hard/hard_grid"] if cells[k]["grid_name"] == "D")
  sets["test_hard/hard_grid E (descriptive only, <8 cells)"] = sorted(k for k in sets["test_hard/hard_grid"] if cells[k]["grid_name"] == "E")
  assert len(sets["test_same"]) == 60 and len(sets["test_hard"]) == 62
  cell_p = lambda arm, k: np.mean([res[arm][cid][0] for cid in by_cell[k]], 0)
  cell_m = lambda arm, k: float(np.mean([res[arm][cid][1] for cid in by_cell[k]]))
  fam_p = lambda fam, k: np.mean([cell_p(a, k) for a in FAMILY[fam]], 0)
  soft = lambda P, k: cells[k]["best_payoff"] - float(np.dot(P, cells[k]["payoffs"]))
  key = lambda k: (cells[k]["V"], cells[k]["grid_name"], cells[k]["C"], None if cells[k]["C"] is not None else tuple(cells[k]["prior"]))
  key2 = lambda k: (cells[k]["V"], cells[k]["C"])
  trk, trk2 = {key(k) for k in tr}, {key2(k) for k in tr}
  rule_pos = lambda k: (next((i for i, x in enumerate(cells[k]["grid"]) if x >= cells[k]["C"]), 4) if cells[k]["C"] is not None and cells[k]["C"] < cells[k]["V"] else 0)
  L = ["# Worked-examples arms: the one test look (generated test_same and test_hard)", "",
       f"script sha256 {sha(SELF)}; adapters per demo/gen/test_frozen_adapters.json; conditions as frozen in GEN_EXAMPLES_TEST_PLAN.md; paired cell bootstrap 10,000 resamples, numpy default_rng(0), two-sided 95% percentile; "
       "no adapter, seed, epoch or lr was chosen on test data. The development verdict on tune was PASSED (soft regret 0.032 vs plain 0.657).", ""]
  summary = {"script_sha256": sha(SELF), "sets": {}}
  TP = {"plain": lambda k: cell_p("plain", k), "always-cheapest": lambda k: np.eye(5)[0],
        "stated-cost rule": lambda k: np.eye(5)[rule_pos(k)], "(a) claude-examples (3 seeds)": lambda k: fam_p("a", k),
        "(b) cheapest-label": lambda k: fam_p("b", k), "(c) shuffled-Claude": lambda k: fam_p("c", k), "answer-trained ceiling lr 1e-4": lambda k: fam_p("ceiling", k),
        "teacher-distil (3 seeds; reported only)": lambda k: fam_p("teacher", k), "our-method-distil (3 seeds; reported only)": lambda k: fam_p("method", k)}
  for sname, ks in sets.items():
    types = [t for t in g.TYPES if any(cells[k]["type"] == t for k in ks)]
    S = {n: {k: soft(f(k), k) for k in ks} for n, f in TP.items()}
    byt = lambda d, t, kk=None: float(np.mean([d[k] for k in (kk or ks) if cells[k]["type"] == t]))
    plain_mass = float(np.mean([cell_m("plain", k) for k in ks]))
    a_mass = float(np.mean([np.mean([cell_m(a, k) for a in FAMILY["a"]]) for k in ks]))
    L += [f"## {sname}: {len(ks)} cells (" + ", ".join("%s %d" % (t, sum(1 for k in ks if cells[k]["type"] == t)) for t in types) + ")", "",
          "| Arm | all [95%] | " + " | ".join(types) + " | cheapest-option mass by type |", "| --- | --- | " + " | ".join("---" for _ in types) + " | --- |"]
    for n, f in TP.items():
      b = boot(list(S[n].values()))
      L.append(f"| {n} | {b[0]:.3f} [{b[1]:.3f}, {b[2]:.3f}] | " + " | ".join(f"{byt(S[n], t):.3f}" for t in types) + " | " + " / ".join(f"{np.mean([f(k)[0] for k in ks if cells[k]['type'] == t]):.2f}" for t in types) + " |")
    L += ["", f"letter mass: plain {plain_mass:.2f}, (a) {a_mass:.2f}", ""]
    sc = {}
    def cond(name, d, kk=None):
      kk = kk or ks
      b = boot([d[k] for k in kk]); sc[name] = b
      L.append(f"- {name}: {fmt(b)}, lower bound > 0: **{'yes' if b[1] > 0 else 'no'}**")
      return b[1] > 0
    L.append("Frozen rule (six conditions):")
    sA, sP, sB, sCh = S["(a) claude-examples (3 seeds)"], S["plain"], S["(b) cheapest-label"], S["always-cheapest"]
    c1 = cond("1. plain - a", {k: sP[k] - sA[k] for k in ks})
    c2 = cond("2. (b) - a", {k: sB[k] - sA[k] for k in ks})
    c3 = cond("3. always-cheapest - a", {k: sCh[k] - sA[k] for k in ks})
    bl = [k for k in ks if cells[k]["type"] == "below"]
    c4 = cond(f"4. plain - a on below cells ({len(bl)})", {k: sP[k] - sA[k] for k in bl}, bl) if bl else None
    d5 = {t: byt(sA, t) - byt(sP, t) for t in types}
    c5 = all(v <= 0.05 for v in d5.values())
    L.append("- 5. type means (a) minus plain: " + ", ".join(f"{t} {v:+.3f}" for t, v in d5.items()) + f" (each <= +0.05): **{'yes' if c5 else 'no'}**")
    c6 = a_mass >= 0.9 * plain_mass
    L.append(f"- 6. letter mass {a_mass:.2f} vs 0.9 x plain {0.9 * plain_mass:.2f}: **{'yes' if c6 else 'no'}**")
    conds = [c1, c2, c3, c4 if c4 is not None else True, c5, c6]
    small = len(ks) < 8
    outcome = ("DESCRIPTIVE ONLY (fewer than 8 cells); " if small else "") + ("PASSED" if all(conds) else "NOT PASSED")
    failed = [i + 1 for i, v in enumerate(conds) if not v]
    L += ["", f"**Outcome for {sname}: {outcome}**" + (f" (failed conditions: {failed})" if failed else "") + ("; condition 4 not applicable (no below cells)" if c4 is None else ""), ""]
    L.append("Reported, outside the rule:")
    for nm in ("stated-cost rule", "answer-trained ceiling lr 1e-4", "teacher-distil (3 seeds; reported only)", "our-method-distil (3 seeds; reported only)"):
      cond(f"plain - {nm}", {k: sP[k] - S[nm][k] for k in ks})
      cond(f"{nm} - a", {k: S[nm][k] - sA[k] for k in ks})
    sC = S["(c) shuffled-Claude"]
    for t in ("below", "no_cost"):
      kk = [k for k in ks if cells[k]["type"] == t]
      if kk:
        cond(f"(b) - a on {t} cells", {k: sB[k] - sA[k] for k in kk}, kk)
        cond(f"(c) - a on {t} cells", {k: sC[k] - sA[k] for k in kk}, kk)
    L.append("- by type, (a) minus ceiling: " + ", ".join(f"{t} {byt(sA, t) - byt(S['answer-trained ceiling lr 1e-4'], t):+.3f}" for t in types))
    for fam in ("a", "b", "c", "ceiling", "teacher", "method"):
      per = []
      for a in FAMILY[fam]:
        v = float(np.mean([soft(cell_p(a, k), k) for k in ks])); per.append(f"{a} {v:.3f}")
      L.append(f"- per-run soft regret ({fam}): " + "; ".join(per))
    bk = [k for k in ks if cells[k]["type"] == "below" and cells[k]["C"] is not None]
    if len({cells[k]["C"] for k in bk}) >= 2:
      sl = lambda f, kk: float(np.polyfit([cells[k]["C"] for k in kk], [float(np.dot(f(k), cells[k]["grid"])) for k in kk], 1)[0])
      rng = np.random.default_rng(0); bs = []
      for _ in range(10000):
        ii = rng.choice(len(bk), len(bk)); kk = [bk[i] for i in ii]
        if len({cells[k]["C"] for k in kk}) >= 2:
          bs.append(sl(TP["(a) claude-examples (3 seeds)"], kk))
      L.append(f"- slope of the expected offer on the stated cost, below cells: (a) {sl(TP['(a) claude-examples (3 seeds)'], bk):.2f} [{np.quantile(bs, .025):.2f}, {np.quantile(bs, .975):.2f}], plain {sl(TP['plain'], bk):.2f}, oracle {sl(lambda k: np.eye(5)[cells[k]['best_positions'][0]], bk):.2f}")
    for nm, kf, tk in (("current key", key, trk), ("V and C only", key2, trk2)):
      ov = [k for k in ks if kf(k) in tk]; nov = [k for k in ks if kf(k) not in tk]
      L.append(f"- overlap with the 100 training cells, {nm}: {len(ov)} overlapping, {len(nov)} not" +
               ("; non-overlapping: plain - a " + fmt(boot([sP[k] - sA[k] for k in nov])) + ", (b) - a " + fmt(boot([sB[k] - sA[k] for k in nov])) if len(nov) >= 5 else "; too few non-overlapping cells for an interval"))
    L.append("")
    summary["sets"][sname] = {"n_cells": len(ks), "outcome": outcome, "failed_conditions": failed, "conditions": {k: list(v) for k, v in sc.items()},
                              "soft_regret": {n: float(np.mean(list(S[n].values()))) for n in S}}
  open(report or REPORT, "w").write("\n".join(L) + "\n")
  json.dump(summary, open(summary_path or SUMMARY, "w"), indent=1)
  print("\n".join(L[-40:]), flush=True)
  print("outcomes:", {k: v["outcome"] for k, v in summary["sets"].items()}, flush=True)


def look():
  pf = json.load(open(PREFLIGHT))
  assert pf["ok"] and pf["script_sha256"] == sha(SELF), "preflight missing, failed, or made by a different script"
  if os.path.exists(LOCK):
    lk = json.load(open(LOCK))
    assert lk["script_sha256"] == sha(SELF), "lock exists for a different script: the look is void"
    assert lk["status"] != "complete", "the look has already been made"
    print("RE-RUN after an interrupted look (identical hash-verified script); partial outputs are re-scored where missing", flush=True)
  else:
    lk = {"script_sha256": sha(SELF), "status": "started", "time": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()), "git_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()}
  json.dump(lk, open(LOCK, "w"), indent=1)
  res, fr, cells, cases = run_scoring(TEST_SPLITS, "look")
  lk["status"] = "scored"; json.dump(lk, open(LOCK, "w"), indent=1)
  analyse(res)
  lk["status"] = "complete"; json.dump(lk, open(LOCK, "w"), indent=1)
  print("TEST LOOK COMPLETE", flush=True)


if __name__ == "__main__":
  ap = argparse.ArgumentParser()
  ap.add_argument("--mode", required=True, choices=("preflight", "look", "analyse", "analyse-fake"))
  ap.add_argument("--out", default="/tmp/fake_analysis")
  a = ap.parse_args()
  if a.mode == "analyse-fake":      # smoke test of the analysis code on RANDOM probabilities; touches no real output, scores nothing
    cells_, cases_ = load_data(); rg = np.random.default_rng(1); fake = {}
    for arm in ["plain"] + list(ADAPTERS):
      fake[arm] = {c["cid"]: (list(rg.dirichlet(np.ones(5))), 0.9) for c in cases_ if c["split"] in TEST_SPLITS}
    os.makedirs(a.out, exist_ok=True)
    analyse(fake, os.path.join(a.out, "fake_report.md"), os.path.join(a.out, "fake_summary.json"))
  else:
    {"preflight": preflight, "look": look, "analyse": analyse}[a.mode]()
