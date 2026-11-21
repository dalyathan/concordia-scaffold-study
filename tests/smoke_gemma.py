"""End-to-end smoke test of LocalGemma2 + Phase 3 on a Gemma 2 model.

Usage: python tests/smoke_gemma.py <2b|9b|model dir> [--device cpu|cuda]
Checks: P0.2-style batched-vs-sequential scoring parity, P0.9 zero-steer identity,
position finding, activation capture, steering effect, greedy determinism.
"""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import torch

from refimpl import core, phase3, runtime
from refimpl.local_gemma2 import (CHOICE_SYSTEM, LocalGemma2, build_messages,
                                  call_context)

ap = argparse.ArgumentParser()
ap.add_argument("model")
ap.add_argument("--device", default="cpu", choices=("cpu", "cuda"))
args = ap.parse_args()
torch.manual_seed(0)
model, tok = runtime.load_gemma(args.model, args.device)
lm = LocalGemma2(model, tok, sequential=True)
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

# P0.2: batched letter scoring versus sequential (one letter per pass).
t = time.time()
scores, p1, _ = lm.letter_scores(user, phase3.LETTERS, sequential=False)
t_b = time.time() - t
first_b, mass_b = dict(lm.last_first_token), lm.last_letter_mass
t = time.time()
seq, p1s, _ = lm.letter_scores(user, phase3.LETTERS, sequential=True)
t_s = time.time() - t
first_s = dict(lm.last_first_token)
deltas = {l: abs(seq[l] - scores[l]) for l in phase3.LETTERS}
deltas_first = {l: abs(first_s[l] - first_b[l]) for l in phase3.LETTERS}
print(f"prompt tokens {p1 + 1}; batched {t_b:.2f}s, sequential {t_s:.2f}s")
print("batched vs sequential whole-answer |delta| (nats):", {l: f"{d:.2e}" for l, d in deltas.items()})
print("batched vs sequential first-token |delta| (nats):", {l: f"{d:.2e}" for l, d in deltas_first.items()})
md = max(max(deltas.values()), max(deltas_first.values()))
print(f"P0.2 max |delta| = {md:.3e} nats; criterion 1e-3: {'within' if md < 1e-3 else 'EXCEEDED'}; "
      f"bit-identical: {md == 0.0}")
same_argmax = max(scores, key=scores.get) == max(seq, key=seq.get)
same_first = max(first_b, key=first_b.get) == max(first_s, key=first_s.get)
print("argmax identical (whole-answer, first-token):", same_argmax, same_first)
# P0.2 is reported, not a gate: on GPU, bf16 kernels differ with batch shape, so
# the two modes are not bit-identical. Only argmax agreement is asserted here.
assert p1 == p1s and same_argmax and same_first
print("batched vs sequential ok (same argmax)")
scores = seq  # the registered mode from here on
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
