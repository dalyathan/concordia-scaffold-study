"""JOB A (NEXT_JOBS.md): harness-vs-stored parity for Gemma 2 9B on the tune split, plus planted cases for the stored examples adapters.

  HF_HUB_OFFLINE=1 HF_HUB_CACHE=models CUBLAS_WORKSPACE_CONFIG=:4096:8 HARNESS_PROVIDER=runpod HARNESS_GPU_USD_PER_HOUR=0.60 \
    PYTHONPATH=concordia:. .venv/bin/python scripts/gemma_parity.py [--compare-only]
Runs (one process each, via python -m harness.run; skipped if a record with the same solver/adapter exists): plain, then lora with each of the
nine adapters in ADAPTERS. Then compares each new record with its A40 reference (where one exists) and its A10G reference using the frozen
tools/parity_check.compare. Writes demo_out/gemma_parity.json, or with --at-head (only records made at the current commit) demo_out/gemma_parity_after_fix.json. Decisions: DECISIONS.md L31-L34."""
import glob, json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "tools"))
import parity_check  # noqa: E402  (frozen tolerances)

RUNS = os.path.join(ROOT, "runs", "haggling", "gemma2_9b")
LEG = lambda n: os.path.join(RUNS, n + ".json")
A40 = json.load(open(os.path.join(ROOT, "demo_out", "hw_parity", "A40_probs.json")))["gen"]
ADAPTERS = [(f"gen_{arm}_lr1e-04_s{s}", s, f"legacy-{short}-tune-s{s}-preflight", a40rec)
            for arm, short in (("claude_examples", "claude_examples"), ("teacher", "teacher"), ("method_original", "method"))
            for s in (0, 1, 2)
            for a40rec in [f"legacy-gemma-claude_examples_n100-tune-s{s}-a40" if arm == "claude_examples" else None]]


HEAD = None   # --at-head: only records made at the current git commit (the readout fix, DECISIONS.md L38)


def new_records():
  out = []
  for p in sorted(glob.glob(os.path.join(RUNS, "*.json"))):
    if os.path.basename(p).startswith("legacy-"):
      continue
    r = json.load(open(p)); r["_path"] = os.path.relpath(p, ROOT)
    if HEAD and (r.get("git") or {}).get("commit") != HEAD:
      continue
    out.append(r)
  return out


def find(solver, adapter=None):
  for r in new_records():
    if r["solver"] == solver and r["split"] == "tune" and (adapter is None or os.path.basename((r.get("solver_config") or {}).get("adapter_dir", "").rstrip("/")) == adapter):
      return r
  return None


def run(solver, seed=0, kw=None):
  cmd = [sys.executable, "-m", "harness.run", "--task", "haggling", "--solver", solver, "--model", "gemma2_9b", "--split", "tune", "--seed", str(seed)]
  if kw:
    cmd += ["--kw", json.dumps(kw)]
  print("RUN", " ".join(cmd[2:]), flush=True)
  subprocess.run(cmd, cwd=ROOT, check=True)


def a40_ref(name, new):
  """A record-shaped reference from A40_probs.json (soft regret recomputed with the new record's payoffs for the same cid)."""
  pay = {x["cid"]: x["payoffs"] for x in new["cases"] if not x["planted"]}
  cases = [{"cid": cid, "planted": False, "probs": v["probs"],
            "score": {"soft_regret": max(pay[cid]) - sum(a * b for a, b in zip(pay[cid], v["probs"]))}} for cid, v in A40[name].items() if cid in pay]
  return {"cases": cases}


def main():
  global HEAD
  out_name = "gemma_parity.json"
  if "--at-head" in sys.argv:
    HEAD = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    out_name = "gemma_parity_after_fix.json"
  if "--compare-only" not in sys.argv:
    if not find("plain"):
      run("plain")
    for name, seed, _, _ in ADAPTERS:
      if not find("lora", name):
        run("lora", seed, {"adapter_dir": f"demo_out/adapters/{name}"})
  out = {"tolerances": {"max_abs_prob": parity_check.MAX_ABS_PROB, "max_abs_regret": parity_check.MAX_ABS_REGRET}, "rows": []}
  jobs = [("plain", None, "legacy-plain-tune-s0", "legacy-gemma-plain-tune-s0-a40")] + [(n, n, a10, a40) for n, _, a10, a40 in ADAPTERS]
  for label, adapter, a10g_name, a40_name in jobs:
    new = find("plain") if adapter is None else find("lora", adapter)
    if new is None:
      out["rows"].append({"arm": label, "status": "not run"}); continue
    row = {"arm": label, "record": new["_path"], "gpu_seconds": (new.get("timing") or {}).get("gpu_seconds"),
           "planted": {x["cid"]: {"ok": x.get("planted_ok"), "mass_on_expected": x.get("planted_mass_on_expected"), "top_option": x["score"]["top_option"]}
                       for x in new["cases"] if x["planted"]}}
    if a40_name:
      ok, rep = parity_check.compare(new, json.load(open(LEG(a40_name)))); ref_src = a40_name
    else:
      ok, rep = parity_check.compare(new, {**a40_ref(adapter, new), "planted": new["planted"], "letter_mass": new["letter_mass"]}); ref_src = f"A40_probs.json:{adapter}"
    row["A40"] = {"ref": ref_src, "tool_verdict": ok, **rep}
    ok10, rep10 = parity_check.compare(new, json.load(open(LEG(a10g_name))))
    row["A10G"] = {"ref": a10g_name, "tool_verdict": ok10, **rep10}
    for k in ("A40", "A10G"):
      r = row[k]
      r["readout_parity"] = (not r["missing_in_new"] and not r["extra_in_new"] and r["max_abs_prob_diff"] <= parity_check.MAX_ABS_PROB
                             and r["regret_diff"] <= parity_check.MAX_ABS_REGRET and bool(r["letter_mass_ok"]))
    out["rows"].append(row)
    print(f"{label:34s} A40 maxdp {row['A40']['max_abs_prob_diff']:.2e} dreg {row['A40']['regret_diff']:.4f} readout {row['A40']['readout_parity']} | "
          f"A10G maxdp {row['A10G']['max_abs_prob_diff']:.2e} dreg {row['A10G']['regret_diff']:.4f} | planted {sum(v['ok'] for v in row['planted'].values())}/4",
          flush=True)
  out["readout_parity_all_A40"] = all(r.get("A40", {}).get("readout_parity") for r in out["rows"])
  out["git_commit_filter"] = HEAD
  json.dump(out, open(os.path.join(ROOT, "demo_out", out_name), "w"), indent=1)
  print("READOUT PARITY vs A40:", "PASS" if out["readout_parity_all_A40"] else "FAIL")


if __name__ == "__main__":
  main()
