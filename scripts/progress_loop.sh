#!/usr/bin/env bash
# CPU-only: every 15 minutes commit and push demo_out/lora_progress.jsonl if it changed.
cd "$(dirname "$0")/.."
while true; do
  if [ -n "$(git status --porcelain demo_out/lora_progress.jsonl)" ]; then
    git add demo_out/lora_progress.jsonl
    git commit -q -m "progress" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01SjA2UwPwxQicQ6boGHZXU2" -- demo_out/lora_progress.jsonl
    git -c credential.helper= -c credential.helper='!gh auth git-credential' push -q origin demo 2>&1 | tail -1
  fi
  sleep 900
done
