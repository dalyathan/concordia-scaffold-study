"""Demo scoring engine: order-averaged first-token p(k) for a demo case, with
optional stated-cost override, Notes block, reworded scaffold, steering vector
and P1 activation capture. Shared by floor.py, the step scripts and steercheck."""
from __future__ import annotations

import dataclasses
import functools
import re
import time
from typing import Sequence

import numpy as np
import torch

import common  # noqa: F401  (sets sys.path)
from examples.modular.environment.modules import fruitville_haggling as fv
from refimpl import core, demo, phase3
from refimpl.local_gemma2 import CHOICE_SYSTEM, LocalGemma2, build_messages, call_context

OPENINGS = list(fv.VISUAL_SCENE_OPENINGS)
ORDERS = core.cyclic_orders()


# ------------------------------------------------------------ prompt variants
def with_cost(p: demo.DemoPrompt, cost) -> demo.DemoPrompt:
  """Change only the stated cost: an integer gives the 'information' seller line
  with that cost; None gives the neutral line (no cost stated)."""
  if cost is None:
    return demo.DemoPrompt(p.variant, p.V, "neutral", None)
  return demo.DemoPrompt(p.variant, p.V, "information", int(cost))


REWORD_SELLER = {
    "neutral": "No rush. Tell me what price you would like to pay for the fruit.",
    "pressure": "I'm busy. Give me a serious offer right now or go to another merchant.",
    "information": "Honestly, I paid {C} coins for this fruit at the farm, so set your price with that in mind.",
}


def reworded_user_turn(p: core.Prompt, opening: str, notes: str | None,
                       order: Sequence[int]) -> tuple[str, dict[str, int]]:
  """The decision prompt with every sentence reworded, same facts (step 2)."""
  n, s = p.buyer, p.seller
  last = REWORD_SELLER[p.line].format(C=p.C)
  lines = [
      f"Here is how to play {n}. This social-science experiment tests how well you can "
      f"portray a character called {n}. It is set up like a tabletop role-playing game "
      "such as Dungeons and Dragons, but it is a serious simulation whose aim is realism. "
      f"Portray {n} as faithfully as you can: answer the way a person like {n} probably "
      f"would, using everything you know about {n}. Always write in the third-person "
      "limited perspective.",
      "", f"What {n} remembers:",
      "Fruit is priced by weight.",
      "On average a kilogram of fruit costs 3 coins; 1 coin is very cheap and 5 coins is "
      "very expensive. Prices are whole numbers of coins, with 1 coin the smallest amount; "
      "fractions are not allowed.",
      "At this market, what a seller paid the farm for a kilogram is anywhere from 1 to 5 "
      "coins, with every amount equally likely.",
      "A seller agrees to any offer that is at least their farm cost and turns down any "
      "lower offer.",
      "If a seller says what they paid at the farm, it is the truth.",
      f"{n} is known for driving a hard bargain.",
      "", "What has happened:",
      f"{opening} {n} wants to buy fruit from {s}, and the two are agreeing on a price. "
      f"Back in her home town, {n} can resell the fruit for {p.V} coins.",
      f'{n} -- "Hello! Your fruit caught my eye. What can you tell me about it?"',
      f'{s} -- "Hello! It was harvested this week; it\'s ripe and sweet."',
      f'{n} -- "It looks nice. Let\'s discuss the price."',
      f'{s} -- "{last}"',
      f"{n} is about to make an offer.", ""]
  text = "\n".join(lines) + "\n"
  if notes is not None:
    text += "Notes:\n" + notes + "\n\n"
  text += f"Question: What price would {n} offer?:\n"
  l2p = {}
  for l, k in zip(phase3.LETTERS, order):
    text += f"  ({l}) {core.OPTION_TEXT[k]}\n"
    l2p[l] = k
  return text + "Answer: (", l2p


@functools.lru_cache(maxsize=4096)
def user_turn(pid_key: tuple, notes: str | None, order: tuple, reword: bool):
  p = demo.DemoPrompt(*pid_key)
  opening = OPENINGS[p.opening_index]
  if reword:
    return reworded_user_turn(p, opening, notes, order)
  return phase3.decision_user_turn(p, opening, notes, order)


def key(p: core.Prompt) -> tuple:
  return (p.variant, p.V, p.line, p.C)


# ---------------------------------------------------------------- scoring
@dataclasses.dataclass
class Result:
  probs: dict            # k -> order-averaged first-token p(k)
  per_order: list        # list of dicts k -> p(k)
  logp_letters: list     # per order: letter -> first-token log-prob (unrenormalised)
  orders: list
  mass: float
  acts: torch.Tensor | None   # [layers, hidden] float32, P1 averaged over orders
  sec: float

  @property
  def top(self) -> int:
    return max(core.PRICES, key=lambda k: (self.probs[k], -k))

  def expected(self) -> float:
    return core.expected_bid(self.probs)


def score(lm: LocalGemma2, p: core.Prompt, notes: str | None = None,
          orders: Sequence[Sequence[int]] = ORDERS, steer: tuple | None = None,
          capture: bool = False, reword: bool = False) -> Result:
  """Order-averaged first-token p(k) from the P1 pass. steer = (layer, vector)."""
  t0 = time.perf_counter()
  per, logs, masses, acts = [], [], [], []
  for order in orders:
    user, l2p = user_turn(key(p), notes, tuple(order), reword)
    hooks, store = [], {}
    p1 = {}
    def pos():
      return {"P1": p1["i"]}
    if capture:
      hooks += phase3.capture_hooks(lm, store, pos)
    if steer is not None:
      hooks.append(phase3.steering_hook(lm, steer[0], steer[1], lambda: p1["i"]))
    p1["i"] = _p1_index(lm, user)
    _, p1_check, _ = lm.letter_scores(user, phase3.LETTERS, hooks=hooks, whole_answer=False)
    assert p1_check == p1["i"]
    first = dict(lm.last_first_token)
    per.append(core.softmax_scores(first, l2p))
    logs.append(first)
    masses.append(lm.last_letter_mass)
    if capture:
      acts.append(torch.stack([store[L]["P1"].float() for L in sorted(store)]))
  probs = {k: float(np.mean([d[k] for d in per])) for k in core.PRICES}
  return Result(probs, per, logs, [list(o) for o in orders], float(np.mean(masses)),
                torch.stack(acts).mean(0) if capture else None, time.perf_counter() - t0)


def _p1_index(lm, user: str) -> int:
  """Position of P1 (last prefix token), cached per user turn on the wrapper."""
  cache = lm.__dict__.setdefault("_p1_cache", {})
  if user not in cache:
    from refimpl.local_gemma2 import ensure_prompt_not_too_long
    trimmed = ensure_prompt_not_too_long(user, 1)
    cache[user] = lm.encode(lm.render(build_messages(CHOICE_SYSTEM, trimmed), True)).shape[1] - 1
  return cache[user]


# ------------------------------------------------------------- generation
_NUM = re.compile(r"\b([1-5])\b|\b(one|two|three|four|five)\b", re.I)
_WORD = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5}


def say(lm: LocalGemma2, p: core.Prompt, max_tokens: int = 16) -> tuple[str, int | None]:
  """Greedy free-text answer: the decision prompt without the option list, ending
  'Answer: {buyer} would propose'. Returns (text, parsed offer or None)."""
  user, _ = phase3.decision_user_turn(p, OPENINGS[p.opening_index], None, ORDERS[0])
  stem = user[:user.index("Question:")]
  prompt = (stem + f"Question: What price would {p.buyer} propose?\n"
            f"Answer: {p.buyer} would propose")
  with call_context(agent="demo-say", pid=p.pid, temperature_override=0.0):
    text = lm.sample_text(prompt, max_tokens=max_tokens, terminators=("\n",))
  m = _NUM.search(text)
  k = None if m is None else (int(m.group(1)) if m.group(1) else _WORD[m.group(2).lower()])
  return text, k


def regret(p: core.Prompt, r: Result) -> tuple[float, float]:
  return core.hard_regret(p, r.top), core.soft_regret(p, r.probs)
