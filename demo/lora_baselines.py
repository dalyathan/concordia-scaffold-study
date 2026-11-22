"""Baselines on the LoRA split (CPU; saved results only): plain, method text,
neutral text, wrong-rule text and always-2, on the train cells and on the held-out
tune cells, with cell-bootstrap intervals and per-case-type means.
Writes demo_out/lora_baselines.json."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import common
from refimpl import analysis, core

OUT = os.path.join(common.ROOT, "demo_out")
P = common.prompts_by_id()
sp = json.load(open(os.path.join(common.DEMO_DIR, "splits_lora.json")))["case_split"]
plain = {c["pid"]: {int(k): v for k, v in c["probs"].items()} for c in common.load_cases()}
rows = {}
for f in ("text_rows_tuning.jsonl", "text_rows_build.jsonl"):
  for l in open(os.path.join(OUT, f)):
    r = json.loads(l)
    rows.setdefault(r["row"], {})[r["pid"]] = {int(k): v for k, v in r["probs"].items()}
const2 = {pid: {k: float(k == 2) for k in core.PRICES} for pid in plain}
sources = {"plain": plain, "method text": rows["method"], "neutral text": rows["neutral"],
           "wrong-rule text": rows["wrong_rule"], "always-2": const2}
mass_src = {}
for f in ("text_rows_tuning.jsonl", "text_rows_build.jsonl"):
  for l in open(os.path.join(OUT, f)):
    r = json.loads(l); mass_src.setdefault(r["row"], {})[r["pid"]] = r["mass"]
mass_src["plain"] = {c["pid"]: c["letter_mass"] for c in common.load_cases()}


def stats(src, ids, mass=None):
  cases = [P[i] for i in ids]
  soft = {i: core.soft_regret(P[i], src[i]) for i in ids}
  hard = {i: core.hard_regret(P[i], max(core.PRICES, key=lambda k: (src[i][k], -k))) for i in ids}
  cm = analysis.cell_means(soft, cases)
  x = np.array(list(cm.values()))
  rng = np.random.default_rng(0)
  b = rng.choice(x, size=(2000, len(x)), replace=True).mean(1)
  by = {}
  for t in ("cost below resale", "cost at or above resale", "no cost"):
    ii = [i for i in ids if common.case_type(P[i]) == t]
    by[t] = float(np.mean([soft[i] for i in ii])) if ii else None
  return {"soft_regret": float(x.mean()), "ci": [float(np.quantile(b, .025)), float(np.quantile(b, .975))],
          "hard_regret": float(np.mean(list(analysis.cell_means(hard, cases).values()))),
          "by_type": by, "letter_mass": float(np.mean([mass[i] for i in ids])) if mass else None,
          "n_cases": len(ids), "n_cells": len(cm)}


out = {}
for split in ("lora_train", "lora_tune"):
  ids = [pid for pid, s in sp.items() if s == split]
  out[split] = {}
  for name, src in sources.items():
    key = {"method text": "method", "neutral text": "neutral", "wrong-rule text": "wrong_rule"}.get(name, name)
    out[split][name] = stats(src, ids, mass_src.get(key))
json.dump(out, open(os.path.join(OUT, "lora_baselines.json"), "w"), indent=1)
for split in out:
  print(split)
  print("| Baseline | Soft regret [95% CI] | Hard regret | cost < resale | cost ≥ resale | no cost | Letter mass |")
  for n, d in out[split].items():
    bt = d["by_type"]
    print(f"| {n} | {d['soft_regret']:.3f} [{d['ci'][0]:.2f}, {d['ci'][1]:.2f}] | {d['hard_regret']:.3f} | "
          f"{bt['cost below resale']:.3f} | {bt['cost at or above resale']:.3f} | {bt['no cost']:.3f} | "
          f"{'—' if d['letter_mass'] is None else format(d['letter_mass'], '.2f')} |")
