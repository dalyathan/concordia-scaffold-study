"""Import stored per-case probabilities of earlier GPU runs as run records (no model is run; labelled `legacy_import`).
Sources: demo_out/gen_plain_scores.jsonl (plain, train+tune), demo_out/gen_examples_test/{test,tune_preflight}_*.json.
Only results that already exist are read; no locked split is newly evaluated.

  python tools/import_legacy.py [--out runs]"""
import argparse, collections, glob, hashlib, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from harness import modelspec, records
from harness.protected import scorer
from harness.tasks.haggling import HagglingTask


def build_record(task, cases_by_id, solver_name, split_label, probs_by_cid, source_files, seed, extra, masses=None):
  rows = []
  for cid, probs in sorted(probs_by_cid.items()):
    case = cases_by_id[cid]
    pay = task.payoffs(case)
    rows.append({"cid": cid, "inputs": case, "type": task.case_type(case), "planted": False, "split": case["split"], "payoffs": pay,
                 "probs": probs, "per_order_probs": None, "letter_mass": [masses[cid]] if masses else None, "prompt_sha256": None,
                 "score": scorer.score_case(pay, probs), "per_order_soft_regret": None})
  by = collections.defaultdict(list)
  for r in rows: by[r["type"]].append(r["score"]["soft_regret"])
  m = lambda x: sum(x) / len(x) if x else None
  spec = modelspec.load("gemma2_9b")
  return {"schema": records.SCHEMA, "run_id": f"legacy-{solver_name}-{split_label}-s{seed}", "model": spec.name, "model_config": None,
          "task": "haggling", "split": split_label, "solver": f"legacy:{solver_name}",
          "solver_config": {"solver": solver_name, "legacy_import": True, **extra}, "seed": seed,
          "config": {"note": "per-case probabilities produced by the pre-refactor GPU code (g5.2xlarge A10G, Gemma 2 9B-it); imported, not re-run"},
          "git": {**records.git_info(), "note": "commit of the importer; the run itself predates it"}, "environment": {"provider": "aws (historic)"},
          "input_hashes": {"source_files_sha256": {f: records.sha256_file(os.path.join(ROOT, f)) for f in source_files},
                           "cases_sha256": hashlib.sha256(json.dumps([c["inputs"] for c in rows], sort_keys=True).encode()).hexdigest()},
          "timing": {"wall_seconds": None, "gpu_seconds": None, "approx_usd": None, "note": "not recorded in the legacy files"},
          "summary": {"n_cases": len(rows), "soft_regret_mean": m([r["score"]["soft_regret"] for r in rows]),
                      "hard_regret_mean": m([r["score"]["hard_regret"] for r in rows]),
                      "by_type": {k: {"n": len(v), "soft_regret_mean": m(v)} for k, v in sorted(by.items())}},
          "planted": {"n": 0, "n_ok": 0, "all_ok": None, "failed": [], "note": "legacy imports had no planted cases"}, "cases": rows}


def main():
  ap = argparse.ArgumentParser(); ap.add_argument("--out", default=records.RUNS); a = ap.parse_args()
  task = HagglingTask(); _, cases = task.build_all()
  by_id = {c["cid"]: c for c in cases}
  n = 0
  src = "demo_out/gen_plain_scores.jsonl"
  per = collections.defaultdict(dict); ms = collections.defaultdict(dict)
  for l in open(os.path.join(ROOT, src)):
    d = json.loads(l); per[d["split"]][d["cid"]] = d["probs"]; ms[d["split"]][d["cid"]] = d.get("mass")
  for split, probs in per.items():
    records.write(build_record(task, by_id, "plain", split, probs, [src], 0, {}, ms[split]), a.out); n += 1
  for f in sorted(glob.glob(os.path.join(ROOT, "demo_out/gen_examples_test/*.json"))):
    base = os.path.basename(f)[:-5]
    kind, rest = base.split("_", 1)
    if kind not in ("test", "tune"):
      continue
    if base == "tune_preflight_plain":
      continue            # same plain tune scores as gen_plain_scores.jsonl (imported above)
    d = json.load(open(f))
    if rest.startswith("preflight_"):
      rest = rest[len("preflight_"):]
    seed = 0
    if "_s" in rest and rest.rsplit("_s", 1)[1].isdigit():
      rest, seed = rest.rsplit("_s", 1); seed = int(seed)
    for split in sorted({c["split"] for c in by_id.values() if c["cid"] in d}):
      probs = {cid: v[0] for cid, v in d.items() if cid in by_id and by_id[cid]["split"] == split}
      mass = {cid: v[1] for cid, v in d.items() if cid in by_id and by_id[cid]["split"] == split}
      rec = build_record(task, by_id, rest, split, probs, [os.path.relpath(f, ROOT)], seed, {"file": os.path.basename(f)}, mass)
      rec["run_id"] = f"legacy-{rest}-{split}-s{seed}" + ("-preflight" if base.startswith("tune_preflight") else "")
      records.write(rec, a.out); n += 1
  print("records written:", n)


if __name__ == "__main__":
  main()
