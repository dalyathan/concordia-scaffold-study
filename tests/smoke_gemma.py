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
p = core.Prompt(13, 5, "information", 3)          # pilot variant; never confirmatory
order = core.cyclic_orders()[0]
notes = "Question: What is Maeve's best offer?\nAnswer: She can resell for 5 coins."

# Rendered prompt check: system text folded into the first user turn.
r = lm.render(build_messages(CHOICE_SYSTEM, "X"), True)
assert r.count("<start_of_turn>user") == 3 and r.endswith("<start_of_turn>model\n")
assert CHOICE_SYSTEM + "\n\nQuestion: Is Jake a turtle?" in r
print("render ok")

t = time.time()
probs, hard, store, probs_full = phase3.score_prompt(lm, p, OPENINGS[0], notes, order, capture=True)
print(f"score+capture {time.time()-t:.1f}s (P1 pass + 5 whole-answer passes); "
      "probabilities are not printed (engineering check)")
assert abs(sum(probs.values()) - 1) < 1e-6 and abs(sum(probs_full.values()) - 1) < 1e-6
assert 0 < lm.last_letter_mass <= 1 and len(lm.last_top_nonletter) == 5
assert len(store) == cfg.num_hidden_layers
assert set(store[0]) == {"P1", "P2", "P3", "P4"}
assert store[0]["P1"].shape == (cfg.hidden_size,)
print("capture ok: P1-P4 at", len(store), "layers")

# Positions decode to the intended tokens.
user, _ = phase3.decision_user_turn(p, OPENINGS[0], notes, order)
pre = lm.encode(lm.render(build_messages(CHOICE_SYSTEM, user), True))[0]
pos = phase3.token_positions(lm, pre, p)
for name, i in pos.items():
  print(name, repr(tok.decode(pre[max(0, i-3):i+1])))
assert tok.decode(pre[pos["P2"]]).endswith("(")
assert tok.decode(pre[len(pre)-1]) == "\n"

# P0.2: batched versus sequential whole-answer scoring; and the P1 pass versus
# P1 read from the whole-answer passes (same distribution, different shapes).
t = time.time()
scores, p1, _ = lm.letter_scores(user, phase3.LETTERS, sequential=False)
t_b = time.time() - t
first_prefix_b = dict(lm.last_first_token)
t = time.time()
seq, p1s, _ = lm.letter_scores(user, phase3.LETTERS, sequential=True)
t_s = time.time() - t
first_prefix, first_wholepass = dict(lm.last_first_token), dict(lm.last_first_token_wholepass)
t = time.time()
lm.letter_scores(user, phase3.LETTERS, whole_answer=False)
t_p = time.time() - t
assert lm.last_first_token == first_prefix == first_prefix_b      # P1 pass: mode-independent
deltas = {l: abs(seq[l] - scores[l]) for l in phase3.LETTERS}
d_first = {l: abs(first_prefix[l] - first_wholepass[l]) for l in phase3.LETTERS}
print(f"prompt tokens {p1 + 1}; P1 pass {t_p:.2f}s; whole-answer batched {t_b:.2f}s, "
      f"sequential {t_s:.2f}s (each including the P1 pass)")
md = max(deltas.values())
print(f"P0.2 batched vs sequential whole-answer max |delta| = {md:.3e} nats "
      f"(reference 1e-3: {'within' if md < 1e-3 else 'exceeded'}; bit-identical: {md == 0.0})")
print(f"P1 pass vs P1 read from sequential whole-answer passes: max |delta| = "
      f"{max(d_first.values()):.3e} nats")
same_argmax = max(scores, key=scores.get) == max(seq, key=seq.get)
print("whole-answer argmax identical:", same_argmax)
# P0.2 is reported, not a gate: on GPU, bf16 kernels differ with batch shape.
assert p1 == p1s and same_argmax
print("batched vs sequential ok (same argmax)")
# Determinism: the same scoring twice gives bit-identical scores (P0.7 logic).
again, _, _ = lm.letter_scores(user, phase3.LETTERS)
assert again == seq and lm.last_first_token == first_prefix
print("repeat bit-identical ok")

# P0.9: zero steering vector leaves both scorings bit-identical.
zero = torch.zeros(cfg.hidden_size)
probs0, _, _, full0 = phase3.score_prompt(lm, p, OPENINGS[0], notes, order, steer=(6, zero))
assert all(probs0[k] == probs[k] and full0[k] == probs_full[k] for k in core.PRICES)
print("zero-steer identity ok")

# A large steering vector changes the distribution (P1-pass only, as in 3b tuning).
v = store[6]["P1"].float() * 4.0
probs_s, _, _, none = phase3.score_prompt(lm, p, OPENINGS[0], notes, order, steer=(6, v),
                                          whole_answer=False)
assert none is None
changed = max(abs(probs_s[k] - probs[k]) for k in core.PRICES)
assert changed > 1e-3
print("steering changes the distribution ok")

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
assert resp == "a"
print("sample_choice ok")
print("ALL SMOKE CHECKS PASSED")
