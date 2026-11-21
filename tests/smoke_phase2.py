"""Phase 2 harness smoke test: Concordia v1.8.9's rational_agent (byte-identical to
the contest zip's copy) makes one scripted decision through LocalGemma2.

Usage: PYTHONPATH=<concordia v1.8.9>:<ref> python tests/smoke_phase2.py <2b|9b|gemma dir>
       [--device cpu|cuda]
A hash-based stand-in embedder is used here; real runs use all-mpnet-base-v2.
Prints no offer, regret or S text: only call counts, retrieval flags, whether S is
non-empty and SHA-256 values for the determinism check.
"""
import argparse
import hashlib
import sys
import time

import numpy as np

from examples.modular.environment.modules import fruitville_haggling as fv
from refimpl import core, phase2, runtime

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


ap = argparse.ArgumentParser()
ap.add_argument("model")
ap.add_argument("--device", default="cpu", choices=("cpu", "cuda"))
args = ap.parse_args()
model, tok = runtime.load_gemma(args.model, args.device)
lm = LocalGemma2(model, tok, sequential=True)

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

p = core.Prompt(13, 5, "information", 3)          # pilot variant: never confirmatory
sha = lambda x: hashlib.sha256(str(x).encode()).hexdigest()
t = time.time()
res = phase2.run_decision(lm, embedder, "concordia.factory.agent.rational_agent", p,
                          mem, cfg, list(fv.VISUAL_SCENE_OPENINGS))
print(f"decision in {time.time()-t:.0f}s")
print("model calls during episode:", len(res["calls"]))
print("rule memories seen in act() prompts:", res["rule_memories_in_prompts"])
print("S non-empty:", bool(res["S"]), " sha256(S):", sha(res["S"])[:16])
assert res["k"] in core.PRICES and res["S"]
# Determinism: rerun gives the same offer and the same S (compared by hash only).
res2 = phase2.run_decision(lm, embedder, "concordia.factory.agent.rational_agent", p,
                           mem, cfg, list(fv.VISUAL_SCENE_OPENINGS))
same = sha((res["k"], res["S"])) == sha((res2["k"], res2["S"]))
if not same:
  for i, (c1, c2) in enumerate(zip(res["calls"], res2["calls"])):
    if sha(c1) != sha(c2):
      print("first differing call index:", i, c1["kind"])
      break
assert same, "not deterministic"
print("PHASE 2 SMOKE TEST PASSED (deterministic rerun identical)")
