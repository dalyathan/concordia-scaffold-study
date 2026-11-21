"""Phase 2 harness smoke test: Concordia v1.8.9's rational_agent (byte-identical to
the contest zip's copy) makes one scripted decision through LocalGemma2.

Usage: PYTHONPATH=<concordia v1.8.9>:<ref> python tests/smoke_phase2.py <gemma dir>
A hash-based stand-in embedder is used here; real runs use all-mpnet-base-v2.
"""
import hashlib
import sys
import time

import numpy as np
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from examples.modular.environment.modules import fruitville_haggling as fv
from refimpl import core, phase2

# Environment shim for this CPU box only (Python 3.13 + pandas>2.0.3, whereas
# Concordia v1.8.9 pins pandas<=2.0.3 on Python 3.11): newer pandas leaves the
# memory bank's 'time' column as object dtype after concat into an empty frame.
# Applied only when pandas is newer than the pinned 2.0.3.
import pandas as pd
if tuple(int(x) for x in pd.__version__.split(".")[:2]) > (2, 0):
  from concordia.associative_memory import associative_memory as _am
  _orig = _am.AssociativeMemory._pd_to_text
  def _pd_to_text(self, data, *a, **kw):
    data = data.copy(); data["time"] = pd.to_datetime(data["time"])
    return _orig(self, data, *a, **kw)
  _am.AssociativeMemory._pd_to_text = _pd_to_text
  print("pandas shim applied (pandas", pd.__version__, ")")
from refimpl.local_gemma2 import LocalGemma2


def embedder(text: str) -> np.ndarray:            # deterministic stand-in
  h = hashlib.sha256(text.encode()).digest()
  v = np.frombuffer(h * 12, dtype=np.uint8)[:384].astype(np.float32) - 127.5
  return v / np.linalg.norm(v)


path = sys.argv[1]
tok = AutoTokenizer.from_pretrained(path)
model = AutoModelForCausalLM.from_pretrained(path, torch_dtype=torch.bfloat16,
                                             attn_implementation="eager").eval()
lm = LocalGemma2(model, tok)

# CPU smoke test: formative-memory generation (upstream Concordia, ~5,000-token
# backstory) is skipped; the agent starts from a blank memory bank with the
# player-specific memories added, and generations are capped at 64 tokens.
lm.max_new_cap = 64
import random
from concordia.associative_memory import blank_memories, importance_function
from examples.modular.environment import haggling
random.seed(1001)
cfg = haggling.configure_player(core.FEMALE_NAMES[0], "female", fv.YEAR, True,
                                random.Random(1001))
mem = blank_memories.MemoryFactory(
    model=lm, embedder=embedder,
    importance=importance_function.ConstantImportanceModel().importance,
    clock_now=lambda: phase2.SETUP).make_blank_memory()
for extra in cfg.extras["player_specific_memories"]:
  mem.add(extra, tags=["initial_player_specific_memory"])

p = core.Prompt(1, 5, "information", 3)
t = time.time()
res = phase2.run_decision(lm, embedder, "concordia.factory.agent.rational_agent", p,
                          mem, cfg, list(fv.VISUAL_SCENE_OPENINGS))
print(f"decision in {time.time()-t:.0f}s: offer={res['k']} hard_regret={res['hard_regret']}")
print("model calls during episode:", len(res["calls"]))
print("rule memories seen in act() prompts:", res["rule_memories_in_prompts"])
print("S (first 600 chars):\n", res["S"][:600])
assert res["k"] in core.PRICES and res["S"]
# Determinism: rerun gives the same offer and the same S.
res2 = phase2.run_decision(lm, embedder, "concordia.factory.agent.rational_agent", p,
                           mem, cfg, list(fv.VISUAL_SCENE_OPENINGS))
if not (res2["k"] == res["k"] and res2["S"] == res["S"]):
  import difflib
  print("offers:", res["k"], res2["k"])
  for i, (c1, c2) in enumerate(zip(res["calls"], res2["calls"])):
    if c1 != c2:
      print("first differing call:", i, c1["kind"])
      for key in ("prompt", "output", "scores"):
        if c1.get(key) != c2.get(key):
          a, b = str(c1.get(key)), str(c2.get(key))
          j = next((n for n in range(min(len(a), len(b))) if a[n] != b[n]), min(len(a), len(b)))
          print(" key", key, "differs at char", j)
          print("  run1:", repr(a[max(0, j-150):j+150]))
          print("  run2:", repr(b[max(0, j-150):j+150]))
      break
assert res2["k"] == res["k"] and res2["S"] == res["S"], "not deterministic"
print("PHASE 2 SMOKE TEST PASSED (deterministic rerun identical)")
