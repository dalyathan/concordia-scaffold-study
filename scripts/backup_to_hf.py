"""Create the PRIVATE model repo (default dalyathan/concordia-scaffold-artifacts) and upload every file in artifacts_manifest.json.
Needs a token with WRITE access in HF_TOKEN (never printed). Safe to re-run (uploads are idempotent).
Then run: python scripts/verify_backup.py"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import artifacts_common as A
from huggingface_hub import HfApi, CommitOperationAdd
import json
tok = os.environ["HF_TOKEN"]
api = HfApi(token=tok)
api.create_repo(A.REPO_ID, repo_type="model", private=True, exist_ok=True)
m = json.load(open(os.path.join(A.ROOT, "artifacts_manifest.json")))
for e in m["files"]:       # the manifest must still describe the files on disk
  assert A.sha256(os.path.join(A.ROOT, e["path"])) == e["sha256"], f"changed since the manifest: {e['path']}"
batch, size = [], 0
def flush():
  global batch, size
  if batch:
    api.create_commit(A.REPO_ID, repo_type="model", operations=batch, commit_message="artifacts backup")
    print("committed", len(batch), "files", flush=True)
  batch, size = [], 0
for e in m["files"]:
  batch.append(CommitOperationAdd(path_in_repo=e["path"], path_or_fileobj=os.path.join(A.ROOT, e["path"]))); size += e["bytes"]
  if size > 400e6 or len(batch) >= 100:
    flush()
flush()
api.upload_file(path_or_fileobj=os.path.join(A.ROOT, "artifacts_manifest.json"), path_in_repo="artifacts_manifest.json", repo_id=A.REPO_ID, repo_type="model")
info = api.model_info(A.REPO_ID); print("private:", info.private, "files on hub:", len(info.siblings))
