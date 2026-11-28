"""Back up the gitignored Llama artifacts of branch `llama` to the private HF repo dalyathan/concordia-scaffold-artifacts under llama/,
then download them into a fresh temporary directory and verify every file.

  HF_HUB_ENABLE_HF_TRANSFER=0 PYTHONPATH=. .venv/bin/python scripts/backup_llama_artifacts.py
Files: every file under demo_out/adapters_harness/ (all step-5 adapters, including *_last) and every gitignored logs/llama_* file; plus any
Llama run record or demo_out/llama probe file that git does not track (none expected: they are committed). HF_TOKEN is read by
huggingface_hub from the environment and never printed. Writes llama_artifacts_manifest.json (repo path, local path, bytes, sha256 per file)
and uploads it as llama/llama_artifacts_manifest.json. Verification: (1) each downloaded file's sha256 against the manifest; (2) each run
record's adapter_weights_sha256 (adapter_model.safetensors) and adapter_sha256 (directory hash, harness.solvers.hf.file_sha) against the
downloaded adapter. Exit 0 only if nothing is mismatched or missing."""
import glob, hashlib, json, os, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
REPO = "dalyathan/concordia-scaffold-artifacts"
# --model qwen25_7b: the same backup for Qwen (prefix qwen/, qwen_artifacts_manifest.json, its adapters, logs and records). Default: Llama.
MODEL = sys.argv[sys.argv.index("--model") + 1] if "--model" in sys.argv else "llama31_8b"
TAG = {"llama31_8b": "llama", "qwen25_7b": "qwen"}[MODEL]
PREFIX = TAG + "/"
MANIFEST = os.path.join(ROOT, f"{TAG}_artifacts_manifest.json")


def sha(p):
  h = hashlib.sha256()
  with open(p, "rb") as f:
    for b in iter(lambda: f.read(1 << 20), b""):
      h.update(b)
  return h.hexdigest()


def untracked(paths):
  """paths git does not hold (ignored or untracked)"""
  tracked = set(subprocess.run(["git", "ls-files", "-z", "--", *paths], cwd=ROOT, capture_output=True, text=True).stdout.split("\0"))
  return [p for p in paths if p not in tracked]


def collect():
  files = sorted(os.path.relpath(p, ROOT) for p in glob.glob(os.path.join(ROOT, "demo_out", "adapters_harness", MODEL + "_*", "**", "*"), recursive=True) if os.path.isfile(p))
  logs = glob.glob(os.path.join(ROOT, "logs", TAG + "_*")) + glob.glob(os.path.join(ROOT, "logs", MODEL + "_*"))
  files += untracked(sorted(os.path.relpath(p, ROOT) for p in logs if os.path.isfile(p)))
  files += untracked(sorted(os.path.relpath(p, ROOT) for p in glob.glob(os.path.join(ROOT, "runs", "haggling", MODEL, "*.json"))))
  files += untracked(sorted(os.path.relpath(p, ROOT) for p in glob.glob(os.path.join(ROOT, "demo_out", TAG, "*")) if os.path.isfile(p)))
  return sorted(set(files))


def main():
  from huggingface_hub import CommitOperationAdd, HfApi, snapshot_download
  from harness.solvers.hf import file_sha
  api = HfApi()
  files = collect()
  entries = [{"repo_path": PREFIX + f, "local_path": f, "bytes": os.path.getsize(os.path.join(ROOT, f)), "sha256": sha(os.path.join(ROOT, f))} for f in files]
  man = {"repo": REPO, "prefix": PREFIX, "branch": TAG, "model": MODEL, "n_files": len(entries), "total_bytes": sum(e["bytes"] for e in entries), "files": entries}
  json.dump(man, open(MANIFEST, "w"), indent=1)
  ops = [CommitOperationAdd(path_in_repo=e["repo_path"], path_or_fileobj=os.path.join(ROOT, e["local_path"])) for e in entries]
  ops.append(CommitOperationAdd(path_in_repo=PREFIX + os.path.basename(MANIFEST), path_or_fileobj=MANIFEST))
  c = api.create_commit(repo_id=REPO, repo_type="model", operations=ops, commit_message=f"{TAG}: {len(entries)} artifacts (adapters_harness, logs) from branch {TAG}")
  print(f"uploaded {len(entries)} files + manifest, {man['total_bytes']} bytes; hub commit {c.oid}", flush=True)

  tmp = tempfile.mkdtemp(prefix=TAG + "_verify_")
  snapshot_download(REPO, repo_type="model", revision=c.oid, allow_patterns=[PREFIX + "*"], local_dir=tmp)
  matched, mismatched, missing = [], [], []
  for e in entries:
    p = os.path.join(tmp, e["repo_path"])
    if not os.path.exists(p):
      missing.append(e["repo_path"])
    elif sha(p) == e["sha256"] and os.path.getsize(p) == e["bytes"]:
      matched.append(e["repo_path"])
    else:
      mismatched.append(e["repo_path"])
  # run-record adapter hashes against the downloaded copies
  rec_ok, rec_bad, rec_missing = 0, [], []
  for rp in sorted(glob.glob(os.path.join(ROOT, "runs", "haggling", MODEL, "lora_*.json"))):
    sc = json.load(open(rp)).get("solver_config") or {}
    d = os.path.join(tmp, PREFIX + sc["adapter_dir"])
    w = os.path.join(d, "adapter_model.safetensors")
    if not os.path.exists(w):
      rec_missing.append(os.path.basename(rp)); continue
    good = sha(w) == sc.get("adapter_weights_sha256") and (sc.get("adapter_sha256") is None or file_sha(d) == sc["adapter_sha256"])
    if good:
      rec_ok += 1
    else:
      rec_bad.append(os.path.basename(rp))
  out = {"files": len(entries), "matched": len(matched), "mismatched": len(mismatched), "missing": len(missing),
         "run_records_checked": rec_ok + len(rec_bad) + len(rec_missing), "run_record_adapter_hash_matched": rec_ok,
         "run_record_adapter_hash_mismatched": rec_bad, "run_record_adapter_missing": rec_missing, "hub_commit": c.oid, "verify_dir": tmp,
         "mismatched_files": mismatched, "missing_files": missing}
  print(json.dumps(out, indent=1))
  return 0 if not (mismatched or missing or rec_bad or rec_missing) else 1


if __name__ == "__main__":
  sys.exit(main())
