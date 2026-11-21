#!/usr/bin/env bash
# Run a command with no network: a fresh network namespace (loopback only), then
# drop straight back to the calling user. Used instead of `unshare -rn` because
# this host restricts unprivileged user namespaces
# (kernel.apparmor_restrict_unprivileged_userns=1). HF_TOKEN is never passed in.
set -euo pipefail
U=$(id -u); G=$(id -g); ROOT="$(cd "$(dirname "$0")/.." && pwd)"
exec sudo -n unshare -n -- setpriv --reuid="$U" --regid="$G" --init-groups -- \
  env -i HOME="$HOME" USER="$USER" PATH="$PATH" LANG=C.UTF-8 \
  HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  CUBLAS_WORKSPACE_CONFIG=:4096:8 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True \
  PYTHONPATH="$ROOT/concordia:$ROOT/agents_zip:$ROOT" \
  bash -c 'cd "$0" && ip link set lo up 2>/dev/null; exec "$@"' "$ROOT" "$@"
