#!/usr/bin/env bash
# Rung 5 chain: waits for the tuning job (tmux session "tune") to end, then a 2B GPU
# smoke test of demo/lora.py, then the three 9B arms in turn. No agent code imported.
cd "$(dirname "$0")/.."
while tmux has-session -t tune 2>/dev/null; do sleep 60; done
export HF_HUB_OFFLINE=1 CUBLAS_WORKSPACE_CONFIG=:4096:8 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
.venv/bin/python demo/lora.py --arm template --model 2b --limit 2 --max-epochs 1 --out /tmp/claude-1000/-home-ubuntu-concordia-scaffold-study/95f682ba-988d-4c17-8b03-23ef2c0ab043/scratchpad/lora_smoke > logs/demo_lora_smoke_gpu.log 2>&1 || exit 1
for arm in answer_only template shuffled; do
  .venv/bin/python demo/lora.py --arm $arm > logs/demo_lora_$arm.log 2>&1
done
echo "LORA CHAIN DONE" >> logs/demo_lora_answer_only.log
