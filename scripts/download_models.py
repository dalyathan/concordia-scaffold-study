"""Download the pinned models into ./models (HF cache layout) and verify every
weight shard's SHA-256 against the LFS hashes listed by the Hub at that revision.
Reads HF_TOKEN from the environment; never prints or stores it."""
import hashlib, json, os, sys
from huggingface_hub import HfApi, snapshot_download

PINS = [("google/gemma-2-9b-it", "11c9b309abf73637e4b6f9a3fa1e92e615547819", None),
        ("google/gemma-2-2b-it", "299a8560bedf22ed1c72a8a11e7dce4a7f9f51f8", None),
        ("sentence-transformers/all-mpnet-base-v2", "e8c3b32edf5434bc2275fc9bab85f82640a19130",
         ["onnx/*", "openvino/*", "pytorch_model.bin", "*.h5", "*.ot", "*.msgpack"])]
WEIGHT_SUFFIXES = (".safetensors", ".bin")
token = os.environ["HF_TOKEN"]
api = HfApi(token=token)
report = {}
for repo, rev, ignore in PINS:
  info = api.model_info(repo, revision=rev, files_metadata=True)
  assert info.sha == rev, (repo, info.sha)
  path = snapshot_download(repo, revision=rev, cache_dir="models", token=token,
                           ignore_patterns=(ignore or []) + ["transformers/*"])
  res = {}
  for s in info.siblings:
    if not s.rfilename.endswith(WEIGHT_SUFFIXES) or not os.path.exists(os.path.join(path, s.rfilename)):
      continue
    h = hashlib.sha256()
    with open(os.path.join(path, s.rfilename), "rb") as f:
      for chunk in iter(lambda: f.read(1 << 24), b""):
        h.update(chunk)
    ok = h.hexdigest() == s.lfs.sha256
    res[s.rfilename] = {"sha256": h.hexdigest(), "lfs_sha256": s.lfs.sha256, "match": ok}
    print(repo, s.rfilename, "OK" if ok else "MISMATCH", flush=True)
  report[repo] = {"revision": rev, "path": path, "shards": res}
os.makedirs("logs", exist_ok=True)
with open("logs/model_hashes.json", "w") as f:
  json.dump(report, f, indent=1)
bad = [(r, n) for r, v in report.items() for n, x in v["shards"].items() if not x["match"]]
print("ALL SHARD HASHES MATCH" if not bad else f"MISMATCHES: {bad}")
sys.exit(1 if bad else 0)
