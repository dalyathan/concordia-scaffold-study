"""Run records: one JSON file per (model, task, solver, seed) run, holding everything needed to regenerate every reported number."""
from __future__ import annotations

import datetime
import hashlib
import json
import os
import platform
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNS = os.path.join(ROOT, "runs")
SCHEMA = 1


def sha256_file(path) -> str:
  return hashlib.sha256(open(path, "rb").read()).hexdigest()


def git_info() -> dict:
  def g(*a):
    try:
      return subprocess.check_output(["git", "-C", ROOT, *a], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
      return None
  return {"commit": g("rev-parse", "HEAD"), "branch": g("rev-parse", "--abbrev-ref", "HEAD"),
          "dirty": bool(g("status", "--porcelain", "--untracked-files=no"))}


def environment() -> dict:
  env = {"python": sys.version.split()[0], "platform": platform.platform(), "machine": platform.machine(),
         "provider": os.environ.get("HARNESS_PROVIDER", "unspecified"), "packages": {}}
  for pkg in ("torch", "transformers", "peft", "numpy", "yaml"):
    try:
      env["packages"][pkg] = __import__(pkg).__version__
    except Exception:
      pass
  try:
    env["gpu"] = subprocess.check_output(["nvidia-smi", "--query-gpu=name,driver_version,memory.total", "--format=csv,noheader"],
                                         text=True, stderr=subprocess.DEVNULL, timeout=10).strip()
  except Exception:
    env["gpu"] = None
  return env


def cost(gpu_seconds: float) -> dict:
  """Approximate cost = GPU seconds x HARNESS_GPU_USD_PER_HOUR (set per provider; nothing assumes AWS). None if not set."""
  rate = os.environ.get("HARNESS_GPU_USD_PER_HOUR")
  return {"gpu_seconds": gpu_seconds, "usd_per_gpu_hour": float(rate) if rate else None,
          "approx_usd": round(gpu_seconds / 3600 * float(rate), 4) if rate else None,
          "note": "approximate; rate is typed by whoever launches the run"}


def write(record: dict, directory: str = RUNS) -> str:
  d = os.path.join(directory, record["task"], record["model"] or "none")
  os.makedirs(d, exist_ok=True)
  path = os.path.join(d, f"{record['run_id']}.json")
  if os.path.exists(path):
    raise FileExistsError(path)
  with open(path, "w") as f:
    json.dump(record, f, indent=1, sort_keys=True)
  return path


def load_all(directory: str = RUNS) -> list[dict]:
  out = []
  for dp, _, fs in os.walk(directory):
    for f in sorted(fs):
      if f.endswith(".json"):
        r = json.load(open(os.path.join(dp, f)))
        r["_path"] = os.path.relpath(os.path.join(dp, f), ROOT)
        out.append(r)
  return sorted(out, key=lambda r: r["_path"])


def new_run_id(task, model, solver, split, seed) -> str:
  stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
  return f"{solver.replace(':', '_')}-{split}-s{seed}-{stamp}"
