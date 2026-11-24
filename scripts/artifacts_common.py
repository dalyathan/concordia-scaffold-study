"""Shared list of the files that git cannot hold (gitignored, not re-creatable cheaply) and the manifest check.
The HF repo mirrors these paths exactly; the repo id comes from ARTIFACT_REPO (default dalyathan/concordia-scaffold-artifacts)."""
import hashlib, json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_ID = os.environ.get("ARTIFACT_REPO", "dalyathan/concordia-scaffold-artifacts")
# directories and files, relative to the repo root
INCLUDE_DIRS = ["demo_out/adapters", "demo_out/adapters_check", "demo_out/dead_ends", "logs", "agents_zip", "banks"]
INCLUDE_FILES = ["demo_out/acts_rows.pt", "demo_out/p1_acts.pt", "demo_out/steer_acts_train.pt", "demo_out/vectors.pt", "demo_out/tune_partial.jsonl"]
SKIP_PARTS = ("__pycache__", ".pytest_cache")


def sha256(path):
  h = hashlib.sha256()
  with open(path, "rb") as f:
    for chunk in iter(lambda: f.read(1 << 24), b""):
      h.update(chunk)
  return h.hexdigest()


def files():
  out = []
  for d in INCLUDE_DIRS:
    for dp, dn, fn in os.walk(os.path.join(ROOT, d)):
      dn[:] = [x for x in dn if x not in SKIP_PARTS]
      out += [os.path.relpath(os.path.join(dp, f), ROOT) for f in fn]
  out += [f for f in INCLUDE_FILES if os.path.exists(os.path.join(ROOT, f))]
  return sorted(set(out))


def check_tree(base, manifest_path=None):
  """compare files under `base` with the manifest -> (matched, mismatched, missing) lists"""
  m = json.load(open(manifest_path or os.path.join(ROOT, "artifacts_manifest.json")))
  matched, bad, missing = [], [], []
  for e in m["files"]:
    p = os.path.join(base, e["path"])
    if not os.path.exists(p):
      missing.append(e["path"])
    elif os.path.getsize(p) != e["bytes"] or sha256(p) != e["sha256"]:
      bad.append(e["path"])
    else:
      matched.append(e["path"])
  return matched, bad, missing
