"""End-to-end smoke test of LocalGemma2 + Phase 3 on a small Gemma 2 model (CPU).

Usage: python -I tests/smoke_gemma.py /path/to/gemma-2-2b-it
Checks: P0.2-style batch-vs-single scoring parity, P0.9 zero-steer identity,
position finding, activation capture, steering effect, greedy determinism.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from refimpl import core, phase3
from refimpl.local_gemma2 import (CHOICE_SYSTEM, LocalGemma2, build_messages,
                                  call_context)

path = sys.argv[1]
torch.manual_seed(0)
tok = AutoTokenizer.from_pretrained(path)
model = AutoModelForCausalLM.from_pretrained(path, torch_dtype=torch.bfloat16,
                                             attn_implementation="eager").eval()
lm = LocalGemma2(model, tok)
cfg = model.config
print("layers", cfg.num_hidden_layers, "hidden", cfg.hidden_size,
      "softcaps", cfg.attn_logit_softcapping, cfg.final_logit_softcapping)

OPENINGS = [f"Opening sentence number {i}." for i in range(5)]  # stand-ins
p = core.Prompt(1, 5, "information", 3)
order = core.cyclic_orders()[0]
notes = "Question: What is Anya's best offer?\nAnswer: She can resell for 5 coins."

# Rendered prompt check: system text folded into the first user turn.
r = lm.render(build_messages(CHOICE_SYSTEM, "X"), True)
assert r.count("<start_of_turn>user") == 3 and r.endswith("<start_of_turn>model\n")
assert CHOICE_SYSTEM + "\n\nQuestion: Is Jake a turtle?" in r
print("render ok")

t = time.time()
probs, hard, store, probs_full = phase3.score_prompt(lm, p, OPENINGS[0], notes, order, capture=True)
print(f"score+capture {time.time()-t:.1f}s  first-token probs={ {k: round(v,3) for k,v in probs.items()} } hard={hard}")
print(f"whole-answer probs={ {k: round(v,3) for k,v in probs_full.items()} }  letter mass at P1={lm.last_letter_mass:.3f}")
assert abs(sum(probs.values()) - 1) < 1e-6
assert len(store) == cfg.num_hidden_layers
assert set(store[0]) == {"P1", "P2", "P3", "P4"}
assert store[0]["P1"].shape == (cfg.hidden_size,)

# Positions decode to the intended tokens.
user, _ = phase3.decision_user_turn(p, OPENINGS[0], notes, order)
pre = lm.encode(lm.render(build_messages(CHOICE_SYSTEM, user), True))[0]
pos = phase3.token_positions(lm, pre, p)
for name, i in pos.items():
  print(name, repr(tok.decode(pre[max(0, i-3):i+1])))
assert tok.decode(pre[pos["P2"]]).endswith("(")
assert tok.decode(pre[len(pre)-1]) == "\n"

# P0.2-style: batched letter scoring equals scoring each sequence alone.
scores, p1, _ = lm.letter_scores(user, phase3.LETTERS)
deltas, alone_all = {}, {}
for l in phase3.LETTERS:
  alone, _, _ = lm.letter_scores(user, [l])
  alone_all[l] = alone[l]
  deltas[l] = abs(alone[l] - scores[l])
print("batch vs single |delta| (nats):", {l: f"{d:.2e}" for l, d in deltas.items()})
assert max(deltas.values()) < 5e-2
assert max(scores, key=scores.get) == max(alone_all, key=alone_all.get)
print("batch vs single ok (same argmax)")
# Determinism: the same batch twice gives bit-identical scores (P0.7 logic).
again, _, _ = lm.letter_scores(user, phase3.LETTERS)
assert again == scores
print("repeat bit-identical ok")

# P0.9: zero steering vector leaves scores identical.
zero = torch.zeros(cfg.hidden_size)
probs0, _, _, full0 = phase3.score_prompt(lm, p, OPENINGS[0], notes, order, steer=(6, zero))
assert all(probs0[k] == probs[k] and full0[k] == probs_full[k] for k in core.PRICES), (probs0, probs)
print("zero-steer identity ok")

# A large steering vector changes the distribution.
v = store[6]["P1"].float() * 4.0
probs_s, _, _, _ = phase3.score_prompt(lm, p, OPENINGS[0], notes, order, steer=(6, v))
print("steered probs", {k: round(x, 3) for k, x in probs_s.items()})
assert any(abs(probs_s[k] - probs[k]) > 1e-3 for k in core.PRICES)

# Greedy sample_text is deterministic and honours terminators.
with call_context(agent="test", pid=p.pid, temperature_override=0.0):
  a = lm.sample_text("Question: What colour is the sky?\nAnswer: The sky is",
                     max_tokens=12, terminators=("\n",))
  b = lm.sample_text("Question: What colour is the sky?\nAnswer: The sky is",
                     max_tokens=12, terminators=("\n",))
print("sample_text:", repr(a))
assert a == b and "\n" not in a

# Choice through the Concordia-facing API.
idx, resp, sc = lm.sample_choice("Question: Is fire hot?\n  (a) Yes\n  (b) No\nAnswer: (",
                                 ["a", "b"])
print("sample_choice:", resp, {k: round(v, 2) for k, v in sc.items()})
print("ALL SMOKE CHECKS PASSED")
