"""Stage 1 step 6: write registration/ (hashes, revisions, hardware). Does not publish.

Usage: python scripts/make_registration.py <code commit hash>"""
import glob, hashlib, json, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import torch
from refimpl import runtime

commit = sys.argv[1]
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(root)

def sha(path):
  with open(path, "rb") as f:
    return hashlib.sha256(f.read()).hexdigest()

tracked = subprocess.run(["git", "ls-tree", "-r", "--name-only", commit], capture_output=True,
                         text=True, check=True).stdout.split()
code = sorted(f for f in tracked if f.endswith((".py", ".sh")) or f in
              ("PROTOCOL.md", "requirements.lock", "requirements.gpu.lock", ".gitignore"))
for f in code:   # hashes are of the committed bytes
  blob = subprocess.run(["git", "show", f"{commit}:{f}"], capture_output=True, check=True).stdout
  assert hashlib.sha256(blob).hexdigest() == sha(f), f"{f} differs from commit {commit}"
manifest = json.load(open("banks/manifest.json"))
banks = {m["file"]: m["sha256"] for _, m in sorted(manifest.items(), key=lambda kv: int(kv[0]))}
for f, h in banks.items():
  assert sha(os.path.join("banks", f)) == h, f
smi = subprocess.run(["nvidia-smi", "--query-gpu=name,driver_version,memory.total",
                      "--format=csv,noheader"], capture_output=True, text=True).stdout.strip()
gpu_name, driver, mem_total = [x.strip() for x in smi.split(",")]
model_hashes = json.load(open("logs/model_hashes.json"))
reg = {
  "code_commit": commit,
  "code_sha256": {f: sha(f) for f in code},
  "requirements.gpu.lock_sha256": sha("requirements.gpu.lock"),
  "memory_banks_sha256": banks,
  "models": {k: {"repo": r, "revision": v,
                 "weight_sha256": {n: x["sha256"] for n, x in model_hashes[r]["shards"].items()}}
             for k, (r, v) in runtime.PINS.items()},
  "concordia": {"tag": "v1.8.9", "commit": "3643ac0466f748b8055b61feb0b7908411f73d84"},
  "agent_zip": {"bytes": 4537615,
                "sha256": "e9ffb65167d776fd4beae14ee65cd3b44ec9c489870698c203f7acdefc199582"},
  "bank_generation_and_development_hardware": {
      "gpu": gpu_name, "gpu_memory": mem_total, "driver": driver,
      "torch": torch.__version__, "torch.version.cuda": torch.version.cuda,
      "cudnn": torch.backends.cudnn.version(), "instance": "AWS g5.xlarge (4 vCPUs, 16 GB RAM)"},
  "confirmatory_hardware": "to be decided (PROTOCOL.md section 3 specifies one 48 GB GPU)",
}
os.makedirs("registration", exist_ok=True)
json.dump(reg, open("registration/registration.json", "w"), indent=1, sort_keys=True)
lines = ["# Registration record (not published)", "",
         f"- Code commit: `{commit}`",
         f"- Concordia: v1.8.9, commit `{reg['concordia']['commit']}`",
         f"- Agent zip: {reg['agent_zip']['bytes']:,} bytes, SHA-256 `{reg['agent_zip']['sha256']}`", ""]
lines += ["## Models", ""]
for k, m in reg["models"].items():
  lines.append(f"- {m['repo']} at revision `{m['revision']}`")
  for n, h in m["weight_sha256"].items():
    lines.append(f"  - `{n}`: `{h}`")
lines += ["", "## Hardware", "",
          f"- **Bank-generation and development hardware:** {gpu_name} ({mem_total}), driver {driver}, "
          f"torch {torch.__version__}, CUDA (torch.version.cuda) {torch.version.cuda}, "
          f"cuDNN {torch.backends.cudnn.version()}; AWS g5.xlarge (4 vCPUs, 16 GB RAM).",
          "- **Confirmatory hardware:** to be decided. PROTOCOL.md section 3 specifies one 48 GB GPU; "
          "exact repeatability (P0.7) is required on that configuration only.", "",
          "## Memory banks (SHA-256)", ""]
lines += [f"- `{f}`: `{h}`" for f, h in banks.items()]
lines += ["", f"## requirements.gpu.lock", "", f"- `{reg['requirements.gpu.lock_sha256']}`", "",
          "## Code files (SHA-256 at the code commit)", ""]
lines += [f"- `{f}`: `{h}`" for f, h in reg["code_sha256"].items()]
open("registration/REGISTRATION.md", "w").write("\n".join(lines) + "\n")
print("\n".join(lines))
