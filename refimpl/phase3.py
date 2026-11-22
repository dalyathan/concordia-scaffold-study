"""Phase 3 / 3b: fixed decision prompt, activation capture and steering."""
from __future__ import annotations

import string
from typing import Sequence

import torch

from . import core
from .local_gemma2 import (CHOICE_SYSTEM, LocalGemma2, build_messages,
                           ensure_prompt_not_too_long)

LETTERS = list(string.ascii_lowercase[:5])


def instructions_text(buyer: str) -> str:
  """v1.8.9 concordia/components/agent/instructions.py, name substituted."""
  n = buyer
  return (f"The instructions for how to play the role of {n} are as follows. This is "
          f"a social science experiment studying how well you play the role of a "
          f"character named {n}. The experiment is structured as a tabletop "
          "roleplaying game (like dungeons and dragons). However, in this case it "
          "is a serious social science experiment and simulation. The goal is to be "
          f"realistic. It is important to play the role of a person like {n} as "
          "accurately as possible, i.e., by responding in ways that you think it is "
          f"likely a person like {n} would respond, and taking into account all "
          f"information about {n} that you have. Always use third-person limited "
          "perspective.")


SHARED_MEMORY_1 = "Fruits are sold by weight."
SHARED_MEMORY_2 = ("The price of one kilogram of fruit is, on average, 3 coins. 1 coin "
                   "is really cheap and 5 coins is really expensive. The smallest value "
                   "of transaction is 1 coin, all prices have to be in multiples of 1 "
                   "coin. No fractional values are allowed.")


def premise(p: core.Prompt, opening: str) -> str:
  return (f"{opening} {p.buyer} is trying to buy some fruit from {p.seller}. They are "
          f"negotiating a price. {p.buyer} can sell the fruit for {p.V} coins back "
          "in her home town.")


def utterances(p: core.Prompt, fmt: str = '{speaker} -- "{text}"') -> list[str]:
  last = core.SELLER_LINES[p.line].format(C=p.C)
  turns = [(p.buyer, core.SCRIPT[0]), (p.seller, core.SCRIPT[1]),
           (p.buyer, core.SCRIPT[2]), (p.seller, last)]
  return [fmt.format(speaker=s, text=t) for s, t in turns]


def decision_user_turn(p: core.Prompt, opening: str, notes: str | None,
                       order: Sequence[int], utter_fmt: str = '{speaker} -- "{text}"'
                       ) -> tuple[str, dict[str, int]]:
  lines = [instructions_text(p.buyer), "", "Memories:", SHARED_MEMORY_1, SHARED_MEMORY_2,
           *core.RULE_MEMORIES, f"{p.buyer} always drives a hard bargain.", "",
           "Observations:", premise(p, opening), *utterances(p, utter_fmt),
           f"{p.buyer} is ready to make an offer.", ""]
  text = "\n".join(lines) + "\n"
  if notes is not None:
    text += "Notes:\n" + notes + "\n\n"
  text += f"Question: What price would {p.buyer} propose?:\n"
  letter_to_price = {}
  for l, k in zip(LETTERS, order):
    text += f"  ({l}) {core.OPTION_TEXT[k]}\n"
    letter_to_price[l] = k
  text += "Answer: ("
  return text, letter_to_price


def token_positions(lm: LocalGemma2, prefix_ids: torch.Tensor, p: core.Prompt,
                    utter_fmt: str = '{speaker} -- "{text}"') -> dict[str, int]:
  """P2-P4 via offset mapping on the decoded prefix (P1 comes from letter_scores)."""
  text = lm.tok.decode(prefix_ids)
  enc = lm.tok(text, add_special_tokens=False, return_offsets_mapping=True)
  assert enc.input_ids == prefix_ids.tolist(), "offset re-tokenisation drift"
  spans = enc.offset_mapping

  def last_token_ending_at(char_end: int) -> int:
    idx = [i for i, (a, b) in enumerate(spans) if a < char_end <= b]
    assert idx, "no token covers position"
    return idx[-1]

  ans = text.rfind("Answer: (") + len("Answer: (")
  u4 = utterances(p, utter_fmt)[3]
  u4_end = text.rfind(u4) + len(u4)
  val = f"{p.V} coins back"
  v_end = text.rfind(val) + len(val)
  assert text.count(u4) >= 1 and text.count(val) >= 1
  return {"P2": last_token_ending_at(ans), "P3": last_token_ending_at(u4_end),
          "P4": last_token_ending_at(v_end)}


def capture_hooks(lm: LocalGemma2, store: dict, positions_fn):
  """Hook factories capturing each decoder layer's output (residual stream after
  the block, before the final norm) at given positions, batch item 0.

  letter_scores runs the P1 pass (prefix only) first, then the whole-answer
  passes. Only the first pass is stored, so activations always come from the P1
  pass, the pass Phase 3b steers and reads; later passes leave the store alone."""
  layers = lm.model.model.layers
  factories = []
  for i, layer in enumerate(layers):
    def make(i=i, layer=layer):
      def hook(mod, inp, out):
        if i in store:
          return
        hs = out[0] if isinstance(out, tuple) else out
        pos = positions_fn()
        store[i] = {name: hs[0, j].detach().to(torch.float16).cpu()
                    for name, j in pos.items()}
      return layer.register_forward_hook(hook)
    factories.append(make)
  return factories


def steering_hook(lm: LocalGemma2, layer: int, vec: torch.Tensor, start_pos_fn):
  """Adds vec to layer output at positions >= P1 for every batch item."""
  def make():
    def hook(mod, inp, out):
      hs = out[0] if isinstance(out, tuple) else out
      s = start_pos_fn()
      hs[:, s:, :] = hs[:, s:, :] + vec.to(hs.dtype).to(hs.device)
      return (hs, *out[1:]) if isinstance(out, tuple) else hs
    return lm.model.model.layers[layer].register_forward_hook(hook)
  return make


def score_prompt(lm: LocalGemma2, p: core.Prompt, opening: str, notes: str | None,
                 order: Sequence[int], *, capture: bool = False,
                 steer: tuple[int, torch.Tensor] | None = None,
                 whole_answer: bool = True):
  """Returns (probs, hard, store, probs_full).

  probs: p(k) from the first-token letter log-probabilities at P1 (one pass over
  the prefix), renormalised over the five letters (the Phase 3 primary outcome).
  hard: its argmax (ties to the earlier letter). probs_full: p(k) from
  whole-answer scores (letter, <end_of_turn>, newline; sensitivity analysis), or
  None when whole_answer=False (Phase 3b tuning). store: activations if capture."""
  user, l2p = decision_user_turn(p, opening, notes, order)
  # P1 is the last prefix token; compute it first so hooks can use it.
  trimmed = ensure_prompt_not_too_long(user, 1)  # same trim as letter_scores
  trimmed_prefix = lm.render(build_messages(CHOICE_SYSTEM, trimmed), True)
  pre_ids = lm.encode(trimmed_prefix)[0]
  p1 = len(pre_ids) - 1
  hooks, store = [], {}
  if capture:
    pos = {"P1": p1, **token_positions(lm, pre_ids, p)}
    hooks += capture_hooks(lm, store, lambda: pos)
  if steer is not None:
    hooks.append(steering_hook(lm, steer[0], steer[1], lambda: p1))
  scores, p1_check, _ = lm.letter_scores(user, LETTERS, hooks=hooks, whole_answer=whole_answer)
  assert p1_check == p1
  first = lm.last_first_token
  probs = core.softmax_scores(first, l2p)
  probs_full = core.softmax_scores(scores, l2p) if whole_answer else None
  hard = l2p[max(LETTERS, key=lambda l: (first[l], -LETTERS.index(l)))]
  return probs, hard, store, probs_full
