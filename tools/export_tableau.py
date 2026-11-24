"""export_tableau.py: tidy CSV tables of the generated-case results, for Tableau / Power BI / pandas.

  python tools/export_tableau.py            # writes exports/tableau/*.csv and exports/tableau/DATA_DICTIONARY.md

Train and tune cases only. The locked test sets (test_same, test_hard, test2_*) are never read, so nothing found by browsing
these tables can leak into a test claim. Every number comes from result files already in the repo; nothing is re-scored.
"""
from __future__ import annotations

import csv
import glob
import hashlib
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEN = os.path.join(ROOT, "demo", "gen")
OUT_DIR = os.path.join(ROOT, "exports", "tableau")
ALLOWED_SPLITS = {"train", "tune"}

PROMPT_SETUPS = {  # gen_text_rows.jsonl 'row' -> label
    "method_original": "Prompt: written rule",
    "teacher": "Prompt: Claude's lesson",
    "teacher_v1": "Prompt: Claude's lesson (first draft)",
    "neutral": "Prompt: neutral text (control)",
    "wrong_rule": "Prompt: wrong rule (control)",
}
ARM_LABELS = {
    "claude_examples": "LoRA: Claude's worked examples",
    "teacher": "LoRA: Claude's lesson (distilled)",
    "method_original": "LoRA: written rule (distilled)",
    "neutral": "LoRA: neutral text (control)",
    "wrong_rule": "LoRA: wrong rule (control)",
    "answer_only": "LoRA: answers only (ceiling)",
    "cheapest_label": "LoRA: always-cheapest labels (control)",
    "shuffled_claude": "LoRA: scrambled answers (control)",
    "rule_hard": "LoRA: lesson's top answer as hard label",
}


def sha(path):
  return hashlib.sha256(open(path, "rb").read()).hexdigest()


def load_cases():
  cells = {c["cell"]: c for c in json.load(open(os.path.join(GEN, "cells.json")))["cells"]}
  cases = {}
  for l in open(os.path.join(GEN, "cases.jsonl")):
    c = json.loads(l)
    if c["split"] not in ALLOWED_SPLITS:
      continue
    c.update({k: cells[c["cell"]][k] for k in ("payoffs", "best_payoff", "best_offers")})
    cases[c["cid"]] = c
  return cases


def score(c, probs):
  top = max(range(len(probs)), key=lambda i: (probs[i], -i))          # ties go to the cheaper price (as floor.gen_top)
  expected = sum(p * x for p, x in zip(probs, c["payoffs"]))
  return {"offer": c["grid"][top], "offer_position": top + 1, "right": int(c["grid"][top] in c["best_offers"]),
          "coins_lost": round(c["best_payoff"] - c["payoffs"][top], 6), "expected_coins_lost": round(c["best_payoff"] - expected, 6),
          "confidence": round(max(probs), 6), "expected_offer": round(sum(p * x for p, x in zip(probs, c["grid"])), 6),
          **{f"p_option{i + 1}": round(p, 6) for i, p in enumerate(probs)}}


def main():
  os.makedirs(OUT_DIR, exist_ok=True)
  cases = load_cases()
  train100 = set(json.load(open(os.path.join(GEN, "lora_train_cells.json"))))
  select_b = set(json.load(open(os.path.join(GEN, "lora_select_cells_B.json"))))
  sources = {}

  # 1. cases
  with open(os.path.join(OUT_DIR, "cases.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["case_id", "cell_id", "split", "case_type", "resale_value", "price_list", "option1", "option2", "option3", "option4", "option5",
                "seller_line", "stated_cost", "cost_range_low", "cost_range_high", "wording", "name_variant", "best_offers", "best_payoff",
                "in_training_set_100", "in_selection_set"])
    for c in cases.values():
      w.writerow([c["cid"], c["cell"], c["split"], c["type"], c["V"], c["grid_name"], *c["grid"], c["line"], "" if c["C"] is None else c["C"],
                  c["prior"][0], c["prior"][1], c["wording"], c["name_variant"], "/".join(map(str, c["best_offers"])), c["best_payoff"],
                  int(c["cell"] in train100), int(c["cell"] in select_b)])
  sources["cases"] = ["demo/gen/cases.jsonl", "demo/gen/cells.json", "demo/gen/lora_train_cells.json", "demo/gen/lora_select_cells_B.json"]

  # 2. results: one row per case x setup x seed
  head = ["case_id", "split", "family", "setup", "run_id", "seed", "n_training_examples", "learning_rate", "offer", "offer_position", "right",
          "coins_lost", "expected_coins_lost", "confidence", "expected_offer", "p_option1", "p_option2", "p_option3", "p_option4", "p_option5",
          "letter_mass"]
  n_rows = 0
  with open(os.path.join(OUT_DIR, "results.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=head)
    w.writeheader()
    for l in open(os.path.join(ROOT, "demo_out", "gen_plain_scores.jsonl")):
      r = json.loads(l)
      if r["split"] in ALLOWED_SPLITS:
        w.writerow({"case_id": r["cid"], "split": r["split"], "family": "base", "setup": "Base model", "run_id": "", "seed": "",
                    "n_training_examples": 0, "learning_rate": "", "letter_mass": round(r["mass"], 6), **score(cases[r["cid"]], r["probs"])}); n_rows += 1
    for l in open(os.path.join(ROOT, "demo_out", "gen_text_rows.jsonl")):
      r = json.loads(l)
      if r["split"] in ALLOWED_SPLITS:
        w.writerow({"case_id": r["cid"], "split": r["split"], "family": "prompt", "setup": PROMPT_SETUPS[r["row"]], "run_id": "", "seed": "",
                    "n_training_examples": 0, "learning_rate": "", "letter_mass": round(r["mass"], 6), **score(cases[r["cid"]], r["probs"])}); n_rows += 1
    for path in sorted(glob.glob(os.path.join(ROOT, "demo_out", "gen_lora", "*.json"))):
      run = json.load(open(path))
      m = re.search(r"_n(\d+)_lr", run["run_id"])
      for cid, probs in run["tune_probs_best"].items():
        if cid not in cases:
          continue
        w.writerow({"case_id": cid, "split": cases[cid]["split"], "family": "lora", "setup": ARM_LABELS.get(run["arm"], run["arm"]), "run_id": run["run_id"],
                    "seed": run["seed"], "n_training_examples": int(m.group(1)) if m else 100, "learning_rate": run["lr"],
                    "letter_mass": round(run["tune_mass_best"][cid], 6), **score(cases[cid], probs)}); n_rows += 1
  sources["results"] = ["demo_out/gen_plain_scores.jsonl", "demo_out/gen_text_rows.jsonl", "demo_out/gen_lora/*.json (tune_probs_best)"]

  # 3. training history (per scoring point, selection set B)
  with open(os.path.join(OUT_DIR, "training_history.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["run_id", "setup", "seed", "n_training_examples", "learning_rate", "epoch", "optimizer_step", "train_loss",
                "selection_expected_coins_lost", "selection_below", "selection_at_or_above", "selection_no_cost", "selection_offer_slope_on_cost",
                "selection_letter_mass", "best_epoch"])
    for path in sorted(glob.glob(os.path.join(ROOT, "demo_out", "gen_lora", "*.json"))):
      run = json.load(open(path))
      m = re.search(r"_n(\d+)_lr", run["run_id"])
      for h in run["history"]:
        t = h["tune"]
        w.writerow([run["run_id"], ARM_LABELS.get(run["arm"], run["arm"]), run["seed"], int(m.group(1)) if m else 100, run["lr"], h["epoch"],
                    h.get("step", 0), "" if h["train_loss"] is None else round(h["train_loss"], 6), round(t["soft_regret"], 6),
                    *[round(t["soft_by_type"][k], 6) for k in ("below", "at_or_above", "no_cost")],
                    "" if t.get("slope_stated_cost_below") is None else round(t["slope_stated_cost_below"], 6), round(t["mass"], 6),
                    int(h["epoch"] == run["best_epoch"])])
  sources["training_history"] = ["demo_out/gen_lora/*.json (history; its 'tune' key is selection set B)"]

  # 4. base model per option order (position bias)
  with open(os.path.join(OUT_DIR, "base_per_order.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["case_id", "split", "order_index", "price", "probability"])
    for l in open(os.path.join(ROOT, "demo_out", "gen_plain_scores.jsonl")):
      r = json.loads(l)
      if r["split"] not in ALLOWED_SPLITS:
        continue
      c = cases[r["cid"]]
      for k, probs in enumerate(r["per_order"]):
        for price, p in zip(c["grid"], probs):
          w.writerow([r["cid"], r["split"], k, price, round(p, 6)])
  sources["base_per_order"] = ["demo_out/gen_plain_scores.jsonl (per_order)"]

  manifest = {"tables": {}, "excluded_splits": "test_same, test_hard, test2_same, test2_newkey (never read)"}
  for name in ("cases", "results", "training_history", "base_per_order"):
    p = os.path.join(OUT_DIR, name + ".csv")
    manifest["tables"][name] = {"rows": sum(1 for _ in open(p)) - 1, "sha256": sha(p), "sources": sources[name]}
  json.dump(manifest, open(os.path.join(OUT_DIR, "manifest.json"), "w"), indent=1)
  print(json.dumps(manifest, indent=1))


if __name__ == "__main__":
  main()
