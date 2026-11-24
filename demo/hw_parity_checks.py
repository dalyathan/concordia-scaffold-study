"""Follow-up checks for HARDWARE_PARITY.md (G2 points). Tune cases only; one GPU process, a few minutes.

  PYTHONPATH=concordia:. .venv/bin/python demo/hw_parity_checks.py
1. fresh-process A40 rescore of plain on the 84 gen tune cases, compared bit for bit with demo_out/hw_parity/A40_probs.json;
2. A10G cross-process control: stored plain (gen_score.py) vs the epoch-0 gen runs (gen_lora.py), per case;
3. the gen tune cases that matched the A10G bit for bit, by type and variant, with token lengths;
4. stored per-case plain soft_regret recomputed from stored probabilities;
5. GEMM/attention kernel names for one gen prompt of <= 601 tokens and one of >= 603 tokens (torch profiler).
Writes demo_out/hw_parity/checks.json.
"""
import collections, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import torch
import common
import gen_cases as g
import gen_lora
from refimpl import phase3, runtime
from refimpl.local_gemma2 import CHOICE_SYSTEM, LocalGemma2, build_messages, ensure_prompt_not_too_long

OUT = os.path.join(common.ROOT, "demo_out", "hw_parity")


def main():
  cells = {c["cell"]: c for c in json.load(open(os.path.join(g.OUT, "cells.json")))["cells"]}
  tune = [c for c in map(json.loads, open(os.path.join(g.OUT, "cases.jsonl"))) if c["split"] == "tune"]
  assert len(tune) == 84 and all(c["split"] == "tune" for c in tune)
  a40 = json.load(open(os.path.join(OUT, "A40_probs.json")))
  ref = {r["cid"]: r for r in map(json.loads, open(os.path.join(common.ROOT, "demo_out", "gen_plain_scores.jsonl"))) if r["split"] == "tune"}
  res = {}
  # 2. A10G cross-process control
  ep0 = {}
  for f in sorted(os.listdir(os.path.join(common.ROOT, "demo_out", "gen_lora"))):
    r = json.load(open(os.path.join(common.ROOT, "demo_out", "gen_lora", f)))
    if r["best_epoch"] == 0:
      ep0[r["run_id"]] = all(r["tune_probs_best"][k] == ref[k]["probs"] for k in ref)
  res["a10g_epoch0_runs_equal_stored_plain_per_case_bitwise"] = ep0
  # 4. stored plain soft_regret
  res["stored_plain_soft_regret_max_abs_err"] = max(abs(cells[r["cell"]]["best_payoff"] - float(np.dot(r["probs"], cells[r["cell"]]["payoffs"])) - r["soft_regret"]) for r in ref.values())
  model, tok = runtime.load_gemma("9b", "cuda")
  lm = LocalGemma2(model, tok)
  ntok = lambda user: int(lm.encode(lm.render(build_messages(CHOICE_SYSTEM, ensure_prompt_not_too_long(user, 1)), True))[0].shape[0])
  # 3. matching cases
  rows = []
  for c in tune:
    lens = [ntok(g.render(c, o)[0]) for o in g.orders()]
    rows.append({"cid": c["cid"], "type": c["type"], "variant": c["cid"].split("-")[0], "len_min": min(lens), "len_max": max(lens),
                 "a40_equals_a10g": a40["gen"]["plain"][c["cid"]]["probs"] == ref[c["cid"]]["probs"]})
  res["cases"] = rows
  m = [r for r in rows if r["a40_equals_a10g"]]
  d = [r for r in rows if not r["a40_equals_a10g"]]
  res["matching_by_type"] = dict(collections.Counter(r["type"] for r in m))
  res["matching_len_range"] = [min(r["len_min"] for r in m), max(r["len_max"] for r in m)]
  res["differing_len_range"] = [min(r["len_min"] for r in d), max(r["len_max"] for r in d)]
  res["all_case_lengths_sorted"] = sorted({r["len_min"] for r in rows} | {r["len_max"] for r in rows})
  # 1. fresh-process rescore of plain
  same = 0
  for c in tune:
    p, _, _ = gen_lora.score_case(lm, c)
    same += [float(x) for x in p] == a40["gen"]["plain"][c["cid"]]["probs"]
  res["fresh_process_plain_bitwise_equal_cases"] = f"{same}/84"
  # 5. kernel names around the length split
  short = min(m, key=lambda r: -r["len_max"])
  long_ = min(d, key=lambda r: r["len_min"])
  kern = {}
  for tag, r in (("short", short), ("long", long_)):
    c = next(x for x in tune if x["cid"] == r["cid"])
    user = g.render(c, g.orders()[0])[0]
    with torch.profiler.profile(activities=[torch.profiler.ProfilerActivity.CUDA]) as prof:
      lm.letter_scores(user, phase3.LETTERS, whole_answer=False)
    names = collections.Counter(e.name for e in prof.events() if e.device_type == torch.autograd.DeviceType.CUDA)
    kern[tag] = {"cid": r["cid"], "tokens": ntok(user), "kernels": dict(names)}
  only_s = sorted(set(kern["short"]["kernels"]) - set(kern["long"]["kernels"]))
  only_l = sorted(set(kern["long"]["kernels"]) - set(kern["short"]["kernels"]))
  res["kernels"] = {"short": {k: kern["short"][k] for k in ("cid", "tokens")}, "long": {k: kern["long"][k] for k in ("cid", "tokens")},
                    "only_in_short": only_s, "only_in_long": only_l}
  json.dump(res, open(os.path.join(OUT, "checks.json"), "w"), indent=1)
  print(json.dumps({k: v for k, v in res.items() if k not in ("cases",)}, indent=1))


if __name__ == "__main__":
  main()
