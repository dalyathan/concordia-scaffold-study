"""Download the artifact repo into a temporary directory, check every sha256 against artifacts_manifest.json, check each adapter against the
sha256 stored in its run file (demo_out/gen_lora/*.json, demo_out/lora/*.json), print counts, and delete the copy only if everything matches.
Usage: python scripts/verify_backup.py [--local DIR]   (--local checks an existing tree instead of downloading; never deletes it)"""
import glob, json, os, shutil, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import artifacts_common as A
local = sys.argv[sys.argv.index("--local") + 1] if "--local" in sys.argv else None
if local:
  base = local
else:
  from huggingface_hub import snapshot_download
  base = snapshot_download(A.REPO_ID, repo_type="model", local_dir=tempfile.mkdtemp(prefix="artifact_check_", dir="/tmp"), token=os.environ["HF_TOKEN"])
matched, bad, missing = A.check_tree(base)
print(f"manifest check: files {len(matched) + len(bad) + len(missing)}, matched {len(matched)}, mismatched {len(bad)}, missing {len(missing)}")
# adapters against the values stored in the run files
a_ok = a_bad = a_missing = 0
for f in sorted(glob.glob(os.path.join(A.ROOT, "demo_out", "gen_lora", "*.json")) + glob.glob(os.path.join(A.ROOT, "demo_out", "lora", "*.json"))):
  if f.endswith("_smoke.json"):
    continue
  r = json.load(open(f))
  d, want = r.get("adapter_dir"), r.get("adapter_sha256")
  if not d or not want:
    continue
  p = os.path.join(base, d, "adapter_model.safetensors")
  if not os.path.exists(p):
    a_missing += 1; print("adapter missing:", d)
  elif A.sha256(p) == want:
    a_ok += 1
  else:
    a_bad += 1; print("adapter MISMATCH:", d)
print(f"adapters vs run files: matched {a_ok}, mismatched {a_bad}, missing {a_missing}")
ok = not bad and not missing and not a_bad and not a_missing
print("ALL MATCH" if ok else "PROBLEMS FOUND")
if ok and not local:
  shutil.rmtree(base); print("temporary copy deleted")
sys.exit(0 if ok else 1)
