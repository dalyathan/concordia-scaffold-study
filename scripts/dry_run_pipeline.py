"""End-to-end dry run of the pipeline glue on a small model and off-grid prompts.

Exercises, in order: run_phase2 (all five agents, sealed pilot path, released
variant-13 bank), load_phase2, run_native_replay and native_replay_labels;
run_paraphrases, run_phase3 (the pilot's N0/N1 path and all 28 conditions with
activations), run_leakage_audit and leakage_flags, pilot_power_rule; run_phase3b
(named directions, matched copy, random and isotropic directions, E3, E6); then
analysis.k_tests and report. Prompts: variant 13 with V = 9, 10 only (no phase
uses them); Phase 3 uses synthetic S texts. Writes to --out (outside the
repository) and prints only stage names, counts and timings."""
import argparse, json, os, random, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
import torch
from examples.modular.environment.modules import fruitville_haggling as fv
from refimpl import analysis, conditions, core, phase2, pipeline, report, runtime
from refimpl.local_gemma2 import LocalGemma2

ap = argparse.ArgumentParser()
ap.add_argument("--model", default="2b")
ap.add_argument("--out", required=True)
args = ap.parse_args()
os.makedirs(f"{args.out}/records", exist_ok=True)
T0 = time.time()
def stage(name, **kw):
  print(f"[{time.time() - T0:7.1f}s] {name}", json.dumps(kw, default=str), flush=True)

model, tok = runtime.load_gemma(args.model, "cuda")
lm = LocalGemma2(model, tok)
lm.max_new_cap = 96                     # dry run only: short generations
embed, _ = runtime.load_embedder("embedder")
openings = list(fv.VISUAL_SCENE_OPENINGS)
VALUES = (9, 10)
prompts = core.prompt_set([13], VALUES)
assert all(p.V not in core.VALUES + core.EXT_VALUES for p in prompts)
stage("loaded", prompts=len(prompts))

# Phase 2: all five agents on two off-grid prompts, pilot-style sealing.
mem, cfg = phase2.load_bank("banks/formative_v13.parquet", lm, embed, 13)
p2_prompts = [core.Prompt(13, 9, "information", 3), core.Prompt(13, 10, "neutral", None)]
agents = (conditions.BASELINE, "concordia.factory.agent.basic_agent", *conditions.ENTRIES)
pipeline.run_phase2(lm, embed, p2_prompts, {13: (mem, cfg)}, openings, args.out,
                    agents=agents, sealed=True)
recs = pipeline._read_jsonl(f"{args.out}/records/phase2.jsonl")
sealed = pipeline._read_jsonl(f"{args.out}/records/sealed_phase2.jsonl")
assert all(set(r) <= {"agent", "pid", "draw", "attempt", "wall_s", "error", "n_calls", "S_tokens",
                      "S_capped", "rule_seen", "sealed"} for r in recs if r["agent"] != conditions.BASELINE)
stage("phase2 (sealed)", open_records=len(recs), sealed_records=len(sealed),
      errors=sum("error" in r for r in recs), sealed_sha256=pipeline.seal_file(args.out)[:16])
# Native replay runs on an unsealed file (here: the sealed records, dry run only).
os.replace(f"{args.out}/records/phase2.jsonl", f"{args.out}/records/phase2_open.jsonl")
with open(f"{args.out}/records/phase2.jsonl", "w") as f:
  for r in sealed + [r for r in recs if r["agent"] == conditions.BASELINE]:
    f.write(json.dumps(r) + "\n")
pipeline.run_native_replay(lm, args.out)
nr = pipeline._read_jsonl(f"{args.out}/records/native_replay.jsonl")
stage("native replay", records=len(nr), price_choice=sum(r["ended_in_price_choice"] for r in nr),
      labels=len(pipeline.native_replay_labels(args.out)))

# Phase 3 inputs: synthetic S texts for every agent and prompt.
rng = random.Random(0)
S = {a: {p.pid: f"Question: What does {p.buyer} know?\nAnswer: She can resell for {p.V} coins. "
           f"Offering {rng.randint(1, 5)} coins gives a profit of {rng.randint(0, 5)} coins. "
           f"The market is busy." for p in prompts} for a in conditions.AGENTS}
offers = {a: {p.pid: rng.randint(1, 5) for p in prompts} for a in conditions.AGENTS}
para = pipeline.run_paraphrases(lm, {a: dict(list(v.items())[:2]) for a, v in S.items()}, args.out)
para = {a: {p.pid: (para[a].get(p.pid) or S[a][p.pid]) for p in prompts} for a in conditions.AGENTS}
stage("paraphrases", n=sum(len(v) for v in para.values()))
pilot_out = f"{args.out}/pilot"
os.makedirs(f"{pilot_out}/records", exist_ok=True)
pipeline.run_phase3(lm, prompts, {conditions.BASELINE: S[conditions.BASELINE]}, {}, {}, {},
                    openings, pilot_out, only=("N0", "N1"), values=VALUES)
rule = pipeline.pilot_power_rule(pilot_out, prompts)
stage("pilot path (N0, N1 from baseline data only) and power rule",
      keys=sorted(rule)[:4], n_cells=rule["n_cells"])
pipeline.run_phase3(lm, prompts, S, S, offers, para, openings, args.out, values=VALUES)
p3 = pipeline._read_jsonl(f"{args.out}/records/phase3.jsonl")
stage("phase3", records=len(p3), conditions=len({r["cond"] for r in p3}),
      acts=sum(len(fs) for _, _, fs in os.walk(f"{args.out}/acts")))
pipeline.run_leakage_audit(lm, prompts, S, S, offers, para, openings, args.out, values=VALUES)
stage("leakage audit", flags=pipeline.leakage_flags(args.out, offers))

# Phase 3b on the off-grid split, two layers, tiny random sets.
dev = [p for p in prompts if core.steering_cell_split(p.cell) == "dev"]
test = [p for p in prompts if core.steering_cell_split(p.cell) == "test"]
notes_n1 = {p.pid: S[conditions.BASELINE][p.pid] for p in prompts}
res = pipeline.run_phase3b(lm, args.out, dev, test, notes_n1, openings, n_random=4,
                           n_isotropic=2, layers=(6, 9))
stage("phase3b", dev=len(dev), test=len(test), keys=sorted(res), fallbacks=res["fallbacks"])
k = analysis.k_tests(test, **res["K"], n_boot=200)
k_e6 = analysis.k_tests(test, **res["E6"], n_boot=200)
k_e3 = {t: analysis.k_tests(test, **v, n_boot=200) for t, v in res["E3"].items()}
stage("k_tests", K1_components=sorted(k["K1"]["components"]), K2_cells=k["K2"]["n_cells"],
      E3=len(k_e3))
tables = report.phase3_tables(p3, prompts)
regret = {a: {p.pid: core.hard_regret(p, offers[a][p.pid]) for p in prompts} for a in conditions.AGENTS}
conf = report.confirmatory(prompts, tables, regret, k, extension=False)
sec = report.secondary(prompts, test, tables, k_per_entry=k_e3, k_e6=k_e6,
                       phase2_regret=regret, steered_content=res["K"]["named"]["content"])
stage("report", family=conf["family"], secondary=len(sec["p"]), missing=sec["missing"])
print("DRY RUN COMPLETED")
