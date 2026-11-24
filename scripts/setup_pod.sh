#!/usr/bin/env bash
# Set up a fresh GPU pod (RunPod or any Linux box with an NVIDIA GPU, git, python3.11, curl) for this repo. Nothing here assumes AWS.
#   HF_TOKEN=<token>  [BRANCH=demo] [WORKDIR=/workspace] [ARTIFACT_REPO=dalyathan/concordia-scaffold-artifacts] bash setup_pod.sh
# HF_TOKEN needs read access to the artifact repo and to google/gemma-2-9b-it (licence accepted). It is read from the environment and never printed.
# Steps: clone repo + branch; clone concordia at the pinned commit; venv with the exact locked versions; adapters from the private HF repo,
# every sha256 checked against artifacts_manifest.json; Gemma 2 9B-it (and the other pinned models) at their pinned revisions with shard hashes
# checked; then the demo tool's adapter startup check (adapter off == plain bit for bit; each adapter reproduces its stored tune probabilities).
set -euo pipefail
: "${HF_TOKEN:?set HF_TOKEN (a pod secret) before running}"
BRANCH="${BRANCH:-demo}"
WORKDIR="${WORKDIR:-/workspace}"
REPO_URL="${REPO_URL:-https://github.com/dalyathan/concordia-scaffold-study.git}"
CONCORDIA_COMMIT=3643ac0466f748b8055b61feb0b7908411f73d84
export ARTIFACT_REPO="${ARTIFACT_REPO:-dalyathan/concordia-scaffold-artifacts}"
export HF_HOME="${HF_HOME:-$WORKDIR/.hf_home}"   # keep caches on the network volume
mkdir -p "$WORKDIR" && cd "$WORKDIR"

echo "== 0. machine"
command -v nvidia-smi >/dev/null && nvidia-smi --query-gpu=name,memory.total --format=csv,noheader || { echo "no NVIDIA GPU visible"; exit 1; }
PY=$(command -v python3.11 || true); [ -n "$PY" ] || { echo "python3.11 not found (install it, e.g. apt-get install -y python3.11 python3.11-venv)"; exit 1; }
df -h "$WORKDIR" | tail -1

echo "== 1. repo ($BRANCH)"
[ -d concordia-scaffold-study/.git ] || git clone "$REPO_URL" concordia-scaffold-study
cd concordia-scaffold-study
git fetch -q origin && git checkout -q "$BRANCH" && git pull -q --ff-only origin "$BRANCH"
git log --oneline -1

echo "== 2. concordia at the pinned commit"
[ -d concordia/.git ] || git clone -q https://github.com/google-deepmind/concordia.git concordia
git -C concordia fetch -q origin "$CONCORDIA_COMMIT" 2>/dev/null || true
git -C concordia checkout -q "$CONCORDIA_COMMIT"
[ "$(git -C concordia rev-parse HEAD)" = "$CONCORDIA_COMMIT" ] || { echo "concordia pin mismatch"; exit 1; }

echo "== 3. venv with the locked versions"
[ -x .venv/bin/python ] || "$PY" -m venv .venv
.venv/bin/python -m pip install -q --upgrade pip
# torch 2.4.1 comes from the CUDA 12.1 wheel index; the rest of the lock is pinned exactly
.venv/bin/pip install -q --extra-index-url https://download.pytorch.org/whl/cu121 -r requirements.gpu.lock
.venv/bin/python - <<'PYEOF'
import torch, transformers, peft
assert torch.__version__.startswith("2.4.1"), torch.__version__
assert transformers.__version__ == "4.44.2" and peft.__version__ == "0.12.0", (transformers.__version__, peft.__version__)
assert torch.cuda.is_available(), "CUDA not available to torch"
print("torch", torch.__version__, "transformers", transformers.__version__, "peft", peft.__version__, "|", torch.cuda.get_device_name(0))
PYEOF

echo "== 4. adapters and other backed-up files from the private HF repo"
# Some pod images set HF_HUB_ENABLE_HF_TRANSFER=1; turn it off unless hf_transfer is installed in the venv (download speed only, no effect on results)
.venv/bin/python -c "import hf_transfer" 2>/dev/null || export HF_HUB_ENABLE_HF_TRANSFER=0
.venv/bin/python - <<'PYEOF'
import os
from huggingface_hub import snapshot_download
snapshot_download(os.environ["ARTIFACT_REPO"], repo_type="model", local_dir=".", token=os.environ["HF_TOKEN"])
PYEOF
.venv/bin/python - <<'PYEOF'
import sys
sys.path.insert(0, "scripts")
import artifacts_common as A
ok, bad, missing = A.check_tree(A.ROOT)
print(f"manifest: matched {len(ok)}, mismatched {len(bad)}, missing {len(missing)}")
sys.exit(0 if not bad and not missing else 1)
PYEOF
rm -rf .cache 2>/dev/null || true   # local_dir download leaves a small .cache folder

echo "== 5. models at the pinned revisions (shard sha256 checked against the Hub)"
.venv/bin/python scripts/download_models.py

echo "== 6. demo tool adapter startup check (loads Gemma 9B once; no test data)"
printf 'help\nquit\n' > /tmp/pod_startup_script.txt
PYTHONPATH=concordia:. .venv/bin/python demo/floor.py --serve --dataset gen --no-colour --script /tmp/pod_startup_script.txt --log /tmp/pod_startup_floor.jsonl | tee /tmp/pod_startup_check.txt
grep -q "startup checks passed" /tmp/pod_startup_check.txt && echo "SETUP OK" || { echo "startup check did not report success"; exit 1; }
