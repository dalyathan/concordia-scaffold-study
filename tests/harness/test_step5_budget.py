"""G1 (Qwen): the step-5 driver's GPU budget stop must see LoRA training time (timing.gpu_seconds in the trainer's records) and count a
`_last` record's scoring once (it is inside its run's record)."""
import glob, json, os, runpy, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_gpu_hours_counts_training_once(monkeypatch):
  recs = [json.load(open(p)) for p in glob.glob(os.path.join(ROOT, "runs", "haggling", "llama31_8b", "lora_*.json"))]
  if not recs:
    import pytest; pytest.skip("no Llama LoRA records")
  main = [r for r in recs if not r["solver"].endswith("_last")]
  assert all((r.get("timing") or {}).get("gpu_seconds", 0) > 300 for r in main), "a training record carries no training GPU time"
  monkeypatch.setattr(sys, "argv", ["llama_step5.py", "--model", "llama31_8b"])
  g = runpy.run_path(os.path.join(ROOT, "scripts", "llama_step5.py"), run_name="not_main")
  all_recs = [json.load(open(p)) for p in glob.glob(os.path.join(ROOT, "runs", "haggling", "llama31_8b", "*.json"))]
  want = sum((r.get("timing") or {}).get("gpu_seconds") or 0 for r in all_recs if not r["solver"].endswith("_last")) / 3600
  assert abs(g["gpu_hours"]() - want) < 1e-9 and g["gpu_hours"]() > 2.0
  assert g["BUDGET_STOP_H"] == 8.0
