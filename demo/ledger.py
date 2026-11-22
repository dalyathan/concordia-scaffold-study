"""Results ledger: rebuilds RESULTS_LEDGER.md and demo_out/ledger.json from the saved
results of demo steps 2-7 and any LoRA results. Reads files only (CPU); safe to run
while a GPU job is running.

  python demo/ledger.py

One row per method or arm ever tried, dead ends included. Soft regret is the mean
over cells of the per-case soft regret (order-averaged first-token p(k)); intervals
are 95% cell-bootstrap intervals (2,000 resamples, seed 0) where per-case results
were saved. "In-sample" means the method's setting was chosen or fitted on the same
cases it is scored on. Rungs: 1 plain readout, 2 model-free baselines, 3 text in the
prompt, 4 steering vectors, 5 LoRA adapters.
"""
from __future__ import annotations

import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np

import common
from refimpl import analysis, core

OUT = os.path.join(common.ROOT, "demo_out")
P = common.prompts_by_id()
SPLIT = common.load_splits()["case_split"]


def rel(path):
  return os.path.relpath(path, common.ROOT)


def jl(path):
  return [json.loads(l) for l in open(path)] if os.path.exists(path) else []


def cell_stats(per_case: dict) -> tuple[float, tuple | None]:
  """Mean over cells and a 95% cell-bootstrap interval."""
  cells = analysis.cell_means(per_case, [P[k] for k in per_case])
  x = np.array(list(cells.values()), dtype=float)
  if len(x) < 3:
    return float(x.mean()), None
  rng = np.random.default_rng(0)
  m = rng.choice(x, size=(2000, len(x)), replace=True).mean(1)
  return float(x.mean()), (float(np.quantile(m, 0.025)), float(np.quantile(m, 0.975)))


def soft_from_probs(probs_by_pid: dict) -> dict:
  return {pid: core.soft_regret(P[pid], {int(k): v for k, v in pr.items()}) for pid, pr in probs_by_pid.items()}


ROWS: list[dict] = []


def add(beat, rung, method, split, in_sample, regret, ci, plain, control, control_regret,
        wall, verdict, source, note="", lower_is_better=True):
  change = None if regret is None or plain is None else regret - plain
  beats = "n/a"
  if regret is not None and control_regret is not None:
    beats = "yes" if regret < control_regret - 1e-9 else "no"
  assert len(verdict.split()) <= 12, verdict
  ROWS.append({"beat": beat, "rung": rung, "method": method, "split": split, "in_sample": in_sample,
               "soft_regret": regret, "ci": ci, "change_vs_plain": change, "control": control,
               "control_regret": control_regret, "beats_control": beats, "wall_time": wall,
               "verdict": verdict, "source": source, "note": note})


def fmt_wall(sec):
  if sec is None:
    return "—"
  return f"{sec / 60:.0f} min" if sec < 5400 else f"{sec / 3600:.1f} h"


# ------------------------------------------------------------ rung 1: plain
cases = {c["pid"]: c for c in common.load_cases()}
plain_case_soft = {pid: c["soft_regret"] for pid, c in cases.items()}
plain_by = {}
for sp in ("build", "tuning", "test"):
  ids = {pid: v for pid, v in plain_case_soft.items() if SPLIT[pid] == sp}
  plain_by[sp] = cell_stats(ids)
all_plain = cell_stats(plain_case_soft)
plain_wall = sum(c["sec"] for c in cases.values())
add("failure-is-real", 1, "plain Gemma 2 9B, no notes", "all 140", "no", all_plain[0], all_plain[1],
    all_plain[0], "—", None, plain_wall,
    "fails in 55% of cases; ignores stated cost", rel(common.CASES))
for sp in ("build", "tuning", "test"):
  add("failure-is-real", 1, "plain Gemma 2 9B, no notes", sp, "no", plain_by[sp][0], plain_by[sp][1],
      plain_by[sp][0], "—", None, None, "the reference row for this split", rel(common.CASES))
PLAIN_T = plain_by["tuning"][0]

rw = {r["pid"]: r for r in jl(os.path.join(OUT, "reworded_cases.jsonl"))}
if rw:
  m, ci = cell_stats({pid: r["soft_regret"] for pid, r in rw.items()})
  add("failure-is-real", 1, "plain, reworded scaffold (same facts)", "all 140", "no", m, ci, all_plain[0],
      "plain, original wording", all_plain[0], None,
      "failure survives rewording; half the picks change", rel(os.path.join(OUT, "reworded_cases.jsonl")))
say = jl(os.path.join(OUT, "say.jsonl"))
if say:
  hard = {s["pid"]: core.hard_regret(P[s["pid"]], s["offer"]) for s in say if s["offer"] is not None}
  m, ci = cell_stats(hard)
  ph = cell_stats({pid: c["hard_regret"] for pid, c in cases.items()})[0]
  add("failure-is-real", 1, "greedy free-text answer (hard regret)", "all 140", "no", m, ci, ph,
      "first-token top offer (hard regret)", ph, sum(s["sec"] for s in say),
      "free text agrees with first token 54%; similar regret", rel(os.path.join(OUT, "say.jsonl")),
      note="hard regret, not soft")

# ------------------------------------------------------- rung 2: baselines
bl_path = os.path.join(common.DEMO_DIR, "baselines.json")
if os.path.exists(bl_path):
  bl = json.load(open(bl_path))
  add("one-sentence", 2, f"constant shift (tilt, beta {bl['constant_shift']['beta']:+.2f})", "tuning", "yes",
      bl["constant_shift"]["soft"], None, PLAIN_T, "plain", PLAIN_T, None,
      "small gain; no model knowledge needed", rel(bl_path))
  for k, d in bl["constant_offer"].items():
    add("one-sentence", 2, f"always offer {k} (attractor, lam 1)", "tuning", "yes" if k == "2" else "no",
        d["soft"], None, PLAIN_T, "plain", PLAIN_T, None,
        "beats plain Gemma without any model" if d["soft"] < PLAIN_T else "worse than plain",
        rel(bl_path))
  add("one-sentence", 2, f"shrink to the middle (flatten, lam {bl['shrink_to_middle']['lam']:.2f})",
      "tuning", "yes", bl["shrink_to_middle"]["soft"], None, PLAIN_T, "plain", PLAIN_T, None,
      "never helps; best lam is zero", rel(bl_path))
ALWAYS2 = bl["constant_offer"]["2"]["soft"] if os.path.exists(bl_path) else None

# ----------------------------------------------------------- rung 3: text
tr = jl(os.path.join(OUT, "text_rows_tuning.jsonl"))
if tr:
  by_row = {}
  for r in tr:
    by_row.setdefault(r["row"], {})[r["pid"]] = r
  stats = {row: cell_stats({pid: r["soft_regret"] for pid, r in d.items()}) for row, d in by_row.items()}
  wall = {row: sum(r["sec"] for r in d.values()) for row, d in by_row.items()}
  spec = {
      "method": ("method paragraph (no numbers)", "neutral", "cuts regret 58%; content, not length, helps"),
      "neutral": ("same-length neutral text", "plain", "length alone does nothing"),
      "wrong_rule": ("wrong rule: offer half the stated cost", "neutral", "no better than neutral text"),
      "disposition": ("disposition: only your own profit matters", "neutral", "slightly worse than plain"),
      "acceptance_rule": ("acceptance rule restated", "neutral", "restating the rule alone does nothing"),
      "template": ("template reasoning naming the best offer", "answer_only", "names the answer; near-zero regret (leaky)"),
      "answer_only": ("answer only (UPPER BOUND)", "plain", "upper bound: text naming the answer"),
  }
  src = rel(os.path.join(OUT, "text_rows_tuning.jsonl"))
  for row, (name, ctrl, verdict) in spec.items():
    if row in stats:
      add("one-sentence", 3, name, "tuning", "no", stats[row][0], stats[row][1], PLAIN_T,
          ctrl.replace("_", "-"), stats[ctrl][0] if ctrl in stats else None, wall[row], verdict, src,
          note="names the best offer" if row in ("template", "answer_only") else "")

# ------------------------------------------------------ rung 4: steering
v1 = os.path.join(common.ROOT, "logs", "demo_tune_job_v1.log")
if os.path.exists(v1):
  add("inside-the-model", 4, "tune job v1: alpha x raw vector (mis-scaled)", "tuning", "yes", None, None,
      PLAIN_T, "random directions (matched)", None, 9 * 60,
      "dead end: unequal norms; stopped before any result", rel(v1),
      note="wall time from DEMO_STATUS (killed after about 9 minutes)")
v2 = os.path.join(OUT, "tune_partial_v2.jsonl")
if os.path.exists(v2):
  pts = jl(v2)
  best = None
  for r in pts:
    m = cell_stats(soft_from_probs({pid: pr for pid, (pr, _) in r["results"].items()}))
    if best is None or m[0] < best[0][0]:
      best = (m, r["key"])
  add("inside-the-model", 4, f"tune job v2: template, best of {len(pts)} points (fractions 0.02-0.20)",
      "tuning", "yes", best[0][0], best[0][1], PLAIN_T, "random directions (matched)", None, 10 * 60,
      "dead end: sanity check showed under 0.01-coin moves", rel(v2),
      note=f"best point {best[1]}; wall time from DEMO_STATUS (killed after about 10 minutes)")
san = os.path.join(OUT, "tune_sanity.json")
if os.path.exists(san):
  s = json.load(open(san))
  mx = max(abs(r["mean_change_in_expected_offer"]) for r in s["rows"])
  add("inside-the-model", 4, "sanity: offer_lower, layer 18, fractions 0.10/0.20", "tuning (4 cases)", "no",
      None, None, None, "its negation", None, None,
      f"right sign, but moves offers at most {mx:.3f} coins", rel(san), note="change in expected offer only")
ds_path = os.path.join(OUT, "dose_scan.json")
if os.path.exists(ds_path):
  ds = json.load(open(ds_path))
  plain8 = ds["plain"]["soft_regret"]
  m = re.findall(r"\[\s*(\d+)s\]", open(os.path.join(common.ROOT, "logs", "demo_dose_scan.log")).read())
  ds_wall = float(m[-1]) if m else None
  for v in ds["vectors"]:
    for mode in ds["modes"]:
      rows = [r for r in ds["rows"] if r["vector"] == v and r["mode"] == mode]
      coh = [r for r in rows if r["mass_ratio"] >= 0.9]
      b = min(coh, key=lambda r: r["soft_regret"]) if coh else None
      label = f"dose scan: {v}, {'P1' if mode == 'p1' else 'P3'} on, best coherent setting"
      if b is None:
        add("inside-the-model", 4, label, "tuning (8 cases)", "yes", None, None, plain8, "plain (8 cases)",
            plain8, ds_wall / 6 if ds_wall else None, "no coherent setting: letter mass collapses",
            rel(ds_path), note="no per-case results saved: no interval")
      else:
        add("inside-the-model", 4, label + f" (L{b['layer']}, f {b['fraction']})", "tuning (8 cases)", "yes",
            b["soft_regret"], None, plain8, "plain (8 cases)", plain8, ds_wall / 6 if ds_wall else None,
            f"moves offer {b['d_expected']:+.3f} coins; negligible" if abs(b["d_expected"]) < 0.1
            else f"moves offer {b['d_expected']:+.2f} coins", rel(ds_path),
            note="no per-case results saved: no interval")
  if ds_wall and ds_wall > 0:
    pass
tr_path = os.path.join(OUT, "tune_results.json")
tp_path = os.path.join(OUT, "tune_partial.jsonl")
if os.path.exists(tr_path):
  res = json.load(open(tr_path))
  log = os.path.join(common.ROOT, "logs", "demo_tune_job.log")
  m = re.findall(r"TUNE JOB COMPLETED in (\d+)s", open(log).read()) if os.path.exists(log) else []
  wall = float(m[-1]) if m else None
  rank = res.get("summary", {}).get("matched_rank_p")
  refs = [r for r in res["rows"] if r["budget"] == "matched" and r["name"].split()[0] in ("random", "gauss")]
  ref_best = min((r["soft_regret"] for r in refs), default=None)
  for r in res["rows"]:
    if r in refs or r["name"] == "plain":
      continue
    setting = "no steering chosen" if r["layer"] is None and r["budget"] != "offline" else \
        (f"L{r['layer']}, f {r['alpha']}" if r["layer"] is not None else "")
    is_neg = r["name"].startswith("-")
    if r["budget"] == "matched":
      ctrl, creg = "20 random + 5 Gaussian (matched; best)", ref_best
    elif is_neg:
      ctrl, creg = "the un-negated vector", next((x["soft_regret"] for x in res["rows"]
                                                  if x["name"] == r["name"][1:] and x["budget"] == "full"), None)
    elif r["budget"] == "offline":
      ctrl, creg = "plain", PLAIN_T
    else:
      ctrl, creg = "its negation" if any(x["name"] == "-" + r["name"] for x in res["rows"]) else "plain", \
          next((x["soft_regret"] for x in res["rows"] if x["name"] == "-" + r["name"]), PLAIN_T)
    red = PLAIN_T - r["soft_regret"]
    verdict = ("no coherent setting beat plain; kept no steering" if r["layer"] is None and r["budget"] != "offline"
               else f"reduces regret {red:+.2f}" if red > 0.05 else "no useful change")
    if r["budget"] == "matched" and rank is not None:
      verdict = f"rank among references p = {rank:.2f}"
    add("inside-the-model", 4, f"tune job v3: {r['name']} ({r['budget']} budget{', ' + setting if setting else ''})",
        "tuning", "yes", r["soft_regret"], tuple(r["soft_regret_ci"]), PLAIN_T, ctrl, creg,
        wall, verdict, rel(tr_path), note=res.get("note", ""))
  if refs:
    add("inside-the-model", 4, f"tune job v3: {len(refs)} random/Gaussian directions (matched; best)",
        "tuning", "yes", ref_best, None, PLAIN_T, "plain", PLAIN_T, wall,
        "reference set for the matched rank", rel(tr_path))
elif os.path.exists(tp_path):
  pts = jl(tp_path)
  by = {}
  for r in pts:
    name, budget = r["key"][0], r["key"][1]
    m = cell_stats(soft_from_probs({pid: pr for pid, (pr, _) in r["results"].items()}))
    if (name, budget) not in by or m[0] < by[(name, budget)][0][0]:
      by[(name, budget)] = (m, r["key"])
  for (name, budget), (m, key) in by.items():
    add("inside-the-model", 4, f"tune job v3 (PAUSED, partial): {name}, {budget} budget, best point so far",
        "tuning", "yes", m[0], m[1], PLAIN_T, "plain", PLAIN_T, None,
        "partial result; job paused (resume later)", rel(tp_path),
        note=f"{len(pts)} grid points done; best so far {key}; coherence not applied")

# Steering checks a-c and the follow-up (12 held-out tune cases, vectors from the train cells).
sc_path = os.path.join(OUT, "steer_checks.json")
fu_path = os.path.join(OUT, "steer_followup.json")
if os.path.exists(sc_path):
  sc = json.load(open(sc_path))
  p12 = sc["plain_eval12"]["soft_regret"]
  const_shift_12 = 0.508          # best constant shift fitted on the train cells, scored on these 12 cases
  HO = "held-out tune cases (12)"
  def sadd(method, regret, ctrl, creg, verdict, source, note, wall=None):
    add("inside-the-model", 4, method, HO, "yes", regret, None, p12, ctrl, creg, wall, verdict, source,
        note=note + "; no interval (12 cases = 6 cells)")
  a_best = min((r for r in sc["a"] if r["mass_ratio"] >= 0.9), key=lambda r: r["soft_regret"])
  sadd(f"steering check a: per-order cheap, best coherent (L{a_best['layer']}, f {a_best['fraction']})", a_best["soft_regret"],
       "best constant shift (fit on train cells)", const_shift_12, "letter push: order-specific; not better than always-2",
       rel(sc_path), "always-2 scores 0.333 on these cases; negation raises the offer; random directions do nothing", 2645)
  for name, key in (("cheap", "b_cheap"), ("sentence", "b_sentence")):
    c = sc["controls"][key]
    rnd = float(np.mean([x["soft_regret"] for x in c["random"]]))
    b = c["best"]
    sadd(f"steering check b: order-averaged {name}, best coherent (L{b['layer']}, f {b['fraction']})", b["soft_regret"],
         "3 random directions (same setting)", rnd, f"moves offer {b['d_expected']:+.2f} coins; negligible",
         rel(sc_path), "order-averaged mean-difference vector at P1")
  for L in (33, 39):
    x = next(r for r in sc["c"]["patched"] if r["layer"] == L)
    sadd(f"patch method-text P1 residual into plain at layer {L} (diagnostic)", x["soft_regret"],
         "method text in the prompt", sc["c"]["method_text"]["soft_regret"],
         "diagnostic: shows where the text's effect arrives", rel(sc_path),
         "uses the evaluated cases' own method-text run; not a deployable method")
if os.path.exists(fu_path):
  fu = json.load(open(fu_path))
  p12 = fu["plain"]["soft_regret"]
  x = next(r for r in fu["P2_sentence_per_order"] if r["layer"] == 36 and r["fraction"] == 1.0)
  add("inside-the-model", 4, "per-order sentence vector (method - neutral), L36, f 1.0", "held-out tune cases (12)", "yes",
      x["soft_regret"], None, p12, "wrong-order vector, same setting",
      next(r for r in fu["P1_wrong_order"] if r["layer"] == 36)["next_order_vector"]["soft_regret"], 1173,
      "letter push, like per-order cheap", rel(fu_path), note="no interval (12 cases = 6 cells)")

# ------------------------------------------------------------- rung 5: LoRA
# Runs are saved in demo_out/lora/<run_id>.json (held-out tune cells: the split the
# arms are early-stopped on, so their numbers are selected-on / in-sample).
lora_runs = []
for path in sorted(glob.glob(os.path.join(OUT, "lora", "*.json"))):
  if path.endswith("_smoke.json") or os.path.basename(path).startswith("teacher_"):
    continue
  lora_runs.append((json.load(open(path)), path))
if lora_runs:
  split_f = os.path.join(common.DEMO_DIR, "splits_lora.json")
  ho_ids = [pid for pid, sp in json.load(open(split_f))["case_split"].items() if sp == "lora_tune"]
  plain_ho = cell_stats({pid: plain_case_soft[pid] for pid in ho_ids})[0]
  by_id = {r["run_id"]: r for r, _ in lora_runs}
  for r, path in lora_runs:
    m, ci = cell_stats(soft_from_probs(r["tune_probs_best"]))
    arm = r["arm"]
    twin = {"method": "neutral", "answer_only": "shuffled0"}.get(arm)
    ctrl_id = r["run_id"].replace(arm + ("%d" % r["perm"] if arm == "shuffled" else ""), twin) if twin else None
    ctrl = by_id.get(ctrl_id) if ctrl_id else None
    if ctrl:
      cm = cell_stats(soft_from_probs(ctrl["tune_probs_best"]))[0]
      cname, creg = {"method": "neutral-distil", "answer_only": "shuffled arm"}[arm] + " (same lr, seed)", cm
    else:
      cname, creg = "plain (held-out cells)", plain_ho
    leaky = arm == "template"
    verdict = ("leaky upper bound: teacher names the best offer" if leaky else
               f"best epoch {r['best_epoch']}; " + ("beats plain" if m < plain_ho - 0.05 else "no clear gain over plain"))
    add("inside-the-model", 5, f"LoRA {arm}{r['perm'] if arm == 'shuffled' else ''}, lr {r['lr']:.0e}, seed {r['seed']}"
        + (f", rank {r['rank']}" if r["rank"] != 4 else ""), "held-out tune cells (6)", "yes", m, ci, plain_ho,
        cname, creg, r.get("wall_s"), verdict[:90], rel(path),
        note=f"train-cell soft regret {r['train_best']['soft_regret']:.3f}; selected-on the held-out cells"
        + ("; LEAKY" if leaky else ""))

# Dead end: LoRA with a renormalised-only loss (letter mass collapsed in one epoch).
dead = os.path.join(common.ROOT, "logs", "demo_lora_answer_only_renorm_loss_dead_end.log")
if os.path.exists(dead):
  m = re.search(r"epoch 1: .*?held-out tune soft ([0-9.]+) \(mass ([0-9.]+)\).*?(\d+)s/epoch", open(dead).read())
  if m:
    ho_ids = [pid for pid, sp in json.load(open(os.path.join(common.DEMO_DIR, "splits_lora.json")))["case_split"].items()
              if sp == "lora_tune"]
    plain_ho = cell_stats({pid: plain_case_soft[pid] for pid in ho_ids})[0]
    add("inside-the-model", 5, "LoRA answer_only, renormalised-only loss, lr 3e-4 (stopped after 1 epoch)",
        "held-out tune cells (6)", "yes", float(m.group(1)), None, plain_ho, "plain (held-out cells)", plain_ho,
        float(m.group(3)) + 120, f"dead end: letter mass collapsed to {m.group(2)}", rel(dead),
        note="regret looks good only because it is read after renormalising over a collapsed 1% of the mass; "
             "replaced by the full-vocabulary letter loss")

# The single test look (TEST_PLAN.md); the frozen development verdict stays "not passed".
tl = os.path.join(common.ROOT, "demo_out", "test_look.json")
if os.path.exists(tl):
  t = json.load(open(tl))
  d = t["diff"]
  add("inside-the-model", 5, "LoRA method distillation, 3 seeds, TEST LOOK (72 cases, 18 test cells)", "test cells (18)", "no",
      t["arm_soft_regret"]["method"], None, t["arm_soft_regret"]["plain"], "wrong-rule distil (3 seeds)", t["arm_soft_regret"]["wrong_rule"],
      None, "test label: " + t["label"].split(" (")[0].split(":")[0], rel(tl),
      note=("frozen development verdict: NOT PASSED. Control minus method, paired cell bootstrap: "
            f"plain {d['plain'][0]:+.3f} [{d['plain'][1]:+.3f}, {d['plain'][2]:+.3f}]; neutral {d['neutral'][0]:+.3f} [{d['neutral'][1]:+.3f}, {d['neutral'][2]:+.3f}]; "
            f"wrong-rule {d['wrong_rule'][0]:+.3f} [{d['wrong_rule'][1]:+.3f}, {d['wrong_rule'][2]:+.3f}]; always-2 {d['always2'][0]:+.3f} [{d['always2'][1]:+.3f}, {d['always2'][2]:+.3f}] "
            f"(always-2 {t['arm_soft_regret']['always2']:.3f}); free-text hard regret worse: plain {t['free_text_hard_regret']['plain']:.3f}, method {t['free_text_hard_regret']['method_mean']:.3f}"))

# ------------------------------------------------------------ take-home
try:
  import steercheck
  toy = steercheck.toy()
  rows = {(x["name"], x["budget"]): x for x in toy["rows"]}
  add("take-home", 0, "steercheck toy problem (a vector that should work)", "toy (40 cases)", "yes",
      rows[("toy", "full")]["soft_regret"], tuple(rows[("toy", "full")]["soft_regret_ci"]),
      rows[("plain", "full")]["soft_regret"], "its negation", rows[("-toy", "full")]["soft_regret"], None,
      "steercheck detects a working vector and its controls", "demo/steercheck.py",
      note="toy regret is on the toy's own scale")
except Exception as e:  # noqa: BLE001
  print("toy skipped:", e)


# ------------------------------------------------------------------ write
def f3(x):
  return "—" if x is None else f"{x:.3f}"


def lists():
  usable = [r for r in ROWS if r["split"] == "tuning" and r["soft_regret"] is not None
            and "names the best offer" not in r["note"] and "partial" not in r["method"]]
  best = sorted(usable, key=lambda r: r["change_vs_plain"])[:3]
  # Failed = interventions meant to help (rung >= 3; not the controls, not rows that
  # name the answer, not running jobs) whose result is missing or no useful change
  # (< 0.05 coins better than plain). Order: dead-end steering runs, then the failed
  # positive control, then by change vs plain (worst first).
  controls = ("same-length neutral", "wrong rule", "answer only", "sanity:")
  failed = [r for r in ROWS if r["rung"] >= 3 and "names the best offer" not in r["note"]
            and not r["method"].startswith(controls) and "PAUSED" not in r["method"]
            and (r["soft_regret"] is None or r["change_vs_plain"] > -0.05)]
  def prio(r):
    m = r["method"]
    order = 0 if "tune job v1" in m else 1 if "tune job v2" in m else 2 if ("cheap" in m and "P1" in m) else 3
    return (order, -(r["change_vs_plain"] if r["change_vs_plain"] is not None else 0.0))
  failed = sorted(failed, key=prio)
  slow = [r for r in ROWS if r["wall_time"] and r["wall_time"] > 1800 and (
      r["change_vs_plain"] is None or abs(r["change_vs_plain"]) < 0.05)]
  return best, failed[:3], slow


def main():
  best, failed, slow = lists()
  L = ["# Results ledger", "",
       "Rebuilt by `python demo/ledger.py` from saved results (do not edit by hand). Soft regret is "
       "in coins: the mean over cells of each case's soft regret, using first-token probabilities "
       "averaged over the five option orders. Intervals are 95% cell-bootstrap intervals where "
       "per-case results were saved. Rungs: 1 plain readout, 2 model-free baselines, 3 text in the "
       "prompt, 4 steering vectors, 5 LoRA adapters. In-sample = the setting was chosen or fitted "
       "on the cases it is scored on.", "",
       "| # | Beat | Rung | Method | Split | In-sample | Soft regret [95% CI] | Change vs plain | "
       "Matched control | Control regret | Beats control? | Wall time | Verdict | Source |",
       "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
  for i, r in enumerate(ROWS, 1):
    reg = f3(r["soft_regret"]) + (f" [{r['ci'][0]:.2f}, {r['ci'][1]:.2f}]" if r["ci"] else "")
    ch = "—" if r["change_vs_plain"] is None else f"{r['change_vs_plain']:+.3f}"
    L.append(f"| {i} | {r['beat']} | {r['rung']} | {r['method']} | {r['split']} | {r['in_sample']} | {reg} | "
             f"{ch} | {r['control']} | {f3(r['control_regret'])} | {r['beats_control']} | "
             f"{fmt_wall(r['wall_time'])} | {r['verdict']} | `{r['source']}` |")
  L += ["", "## Three best methods (tuning split; excluding rows that name the answer)", ""]
  L += [f"{i}. {r['method']}: soft regret {f3(r['soft_regret'])} ({r['change_vs_plain']:+.3f} vs plain)."
        for i, r in enumerate(best, 1)]
  L += ["", "## Three that failed", ""]
  L += [f"{i}. {r['method']}: {r['verdict']}." for i, r in enumerate(failed, 1)]
  L += ["", "## Slow runs (over 30 minutes) that gave no signal", ""]
  L += ([f"- {r['method']}: {fmt_wall(r['wall_time'])}; {r['verdict']}." for r in slow] or ["- none so far."])
  notes = [(i, r["note"]) for i, r in enumerate(ROWS, 1) if r["note"]]
  if notes:
    L += ["", "## Row notes", ""] + [f"- Row {i}: {n}" for i, n in notes]
  open(os.path.join(common.ROOT, "RESULTS_LEDGER.md"), "w").write("\n".join(L) + "\n")
  json.dump({"rows": ROWS, "best": [r["method"] for r in best], "failed": [r["method"] for r in failed],
             "slow_no_signal": [r["method"] for r in slow]},
            open(os.path.join(OUT, "ledger.json"), "w"), indent=1, default=float)
  print(f"ledger: {len(ROWS)} rows -> RESULTS_LEDGER.md, demo_out/ledger.json")


if __name__ == "__main__":
  main()
