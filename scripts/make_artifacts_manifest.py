"""Write artifacts_manifest.json: path, bytes, sha256 of every file that goes to the private HF artifact repo. CPU only."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import artifacts_common as A
rows = [{"path": p, "bytes": os.path.getsize(os.path.join(A.ROOT, p)), "sha256": A.sha256(os.path.join(A.ROOT, p))} for p in A.files()]
json.dump({"repo": A.REPO_ID, "n_files": len(rows), "total_bytes": sum(r["bytes"] for r in rows), "files": rows}, open(os.path.join(A.ROOT, "artifacts_manifest.json"), "w"), indent=1)
print(len(rows), "files,", sum(r["bytes"] for r in rows), "bytes")
