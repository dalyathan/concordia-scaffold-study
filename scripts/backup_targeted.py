"""Back up the targeted experiment's adapters (demo_out/adapters_harness/<model>_claude_examples_n150_*) and its gitignored logs to the
private HF artifact repo under targeted/, write targeted_artifacts_manifest.json (repo path, local path, bytes, sha256 per file), then
download everything into a fresh temporary folder and verify every sha256 and every run record's adapter weights hash.
HF_TOKEN is read from the environment and never printed. Exit 0 only if nothing is missing or mismatched.

  HF_TOKEN=$(cat /root/.hf_token) .venv/bin/python scripts/backup_targeted.py [--model qwen25_7b]"""
from __future__ import annotations

import glob
import hashlib
import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO, PREFIX = "dalyathan/concordia-scaffold-artifacts", "targeted/"
MODEL = sys.argv[sys.argv.index("--model") + 1] if "--model" in sys.argv else "qwen25_7b"
MANIFEST = os.path.join(ROOT, "targeted_artifacts_manifest.json")


def sha(p):
  return hashlib.sha256(open(p, "rb").read()).hexdigest()


def main():
  from huggingface_hub import CommitOperationAdd, HfApi, snapshot_download
  files = sorted(os.path.relpath(p, ROOT) for p in glob.glob(os.path.join(ROOT, "demo_out", "adapters_harness", f"{MODEL}_claude_examples_n150_*", "**", "*"),
                                                              recursive=True) if os.path.isfile(p))
  files += sorted(os.path.relpath(p, ROOT) for p in glob.glob(os.path.join(ROOT, "logs", "*targeted*")) if os.path.isfile(p))
  if not files:
    raise SystemExit("no targeted adapters found")
  entries = [{"repo_path": PREFIX + f, "local_path": f, "bytes": os.path.getsize(os.path.join(ROOT, f)), "sha256": sha(os.path.join(ROOT, f))} for f in files]
  api = HfApi(token=os.environ["HF_TOKEN"])
  ops = [CommitOperationAdd(path_in_repo=e["repo_path"], path_or_fileobj=os.path.join(ROOT, e["local_path"])) for e in entries]
  man = {"repo": REPO, "prefix": PREFIX, "model": MODEL, "n_files": len(entries), "total_bytes": sum(e["bytes"] for e in entries), "files": entries}
  ops.append(CommitOperationAdd(path_in_repo=PREFIX + "targeted_artifacts_manifest.json", path_or_fileobj=json.dumps(man, indent=1).encode()))
  c = api.create_commit(repo_id=REPO, repo_type="model", operations=ops, commit_message=f"targeted: {len(entries)} files ({MODEL} n150 adapters, logs)")
  print(f"uploaded {len(entries)} files, {man['total_bytes']} bytes; hub commit {c.oid}", flush=True)
  tmp = tempfile.mkdtemp(prefix="verify_targeted_")
  snapshot_download(REPO, repo_type="model", revision=c.oid, allow_patterns=[PREFIX + "*"], local_dir=tmp, token=os.environ["HF_TOKEN"])
  bad = [e["local_path"] for e in entries if not os.path.exists(os.path.join(tmp, e["repo_path"])) or sha(os.path.join(tmp, e["repo_path"])) != e["sha256"]]
  rec_bad, n_rec = [], 0
  for p in glob.glob(os.path.join(ROOT, "runs", "haggling", MODEL, "lora_claude_examples_n150_*-tune-*.json")):
    r = json.load(open(p)); sc = r["solver_config"]
    w = os.path.join(tmp, PREFIX + sc["adapter_dir"], "adapter_model.safetensors"); n_rec += 1
    if not os.path.exists(w) or sha(w) != sc["adapter_weights_sha256"]:
      rec_bad.append(os.path.relpath(p, ROOT))
  man["upload_status"] = (f"uploaded and verified: hub commit {c.oid}; {len(entries) - len(bad)}/{len(entries)} files sha256-matched after download; "
                          f"{n_rec - len(rec_bad)}/{n_rec} run-record adapter hashes matched")
  json.dump(man, open(MANIFEST, "w"), indent=1)
  print(man["upload_status"])
  if bad or rec_bad:
    raise SystemExit(f"MISMATCH: files {bad[:5]}, records {rec_bad[:5]}")
  print("BACKUP VERIFIED")


if __name__ == "__main__":
  main()
