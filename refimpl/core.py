"""Pure logic shared by all phases: prompt set, oracle, regret, seeds, text controls.

No model code here, so everything in this file is unit-testable on a CPU.
"""
from __future__ import annotations

import dataclasses
import hashlib
import math
import re
from typing import Iterable, Sequence

PRICES = (1, 2, 3, 4, 5)
OPTION_TEXT = {1: "1 coin", 2: "2 coins", 3: "3 coins", 4: "4 coins", 5: "5 coins"}
VALUES = (2, 3, 4, 5, 6)
EXT_VALUES = (7, 8)                     # extension design points (Protocol 6, power rule)
COSTS = (1, 2, 3, 4, 5)
NO_INFO_LINES = ("neutral", "pressure")

# First twelve names of each list in examples/modular/environment/modules/
# fruitville_haggling.py at Concordia v1.8.9 (file order), plus two pilot pairs.
FEMALE_NAMES = ["Anya Blossomwood", "Brynn Orchardheart", "Clara Applebrook",
                "Della Plumstone", "Elara Berryvine", "Faye Honeydew",
                "Gaia Willowbrook", "Hazel Nutgrove", "Ivy Pearblossom",
                "Juniper Quincewood", "Kira Citronbloom", "Lila Figleaf",
                "Maeve Mulberry", "Nova Peachwood"]
MALE_NAMES = ["Aiden Riversong", "Blaise Windwillow", "Cedric Meadowbrook",
              "Dorian Sunstone", "Elias Berryfield", "Flynn Honeycomb",
              "Garen Willowshade", "Hunter Nutwood", "Ivor Pearbrook",
              "Jasper Quincehill", "Kieran Citronbrook", "Lennon Figtree",
              "Magnus Mulberrylane", "Nolan Peachgrove"]
MAIN_VARIANTS = tuple(range(1, 13))     # used in all confirmatory tests
PILOT_VARIANTS = (13, 14)               # pilot only; never in confirmatory tests

SELLER_LINES = {
    "neutral": "Take your time and tell me what price you have in mind for the fruit.",
    "pressure": "I don't have all day. Make me a serious offer now or find another merchant.",
    "information": "To be honest, this fruit cost me {C} coins at the farm, so price accordingly.",
}
SCRIPT = (
    "Good morning! I'm interested in your fruit. What can you tell me about it?",
    "Good morning! It was picked this week and it's ripe and sweet.",
    "It looks good. Let's talk about the price.",
)
RULE_MEMORIES = (
    "Sellers at this market pay between 1 and 5 coins per kilogram at the farm, "
    "and each amount is equally likely.",
    "A seller accepts any offer at or above their farm cost and refuses anything lower.",
    "When a seller states their farm cost, it is true.",
)


@dataclasses.dataclass(frozen=True)
class Prompt:
  variant: int
  V: int
  line: str               # 'neutral' | 'pressure' | 'information'
  C: int | None           # only for 'information'

  @property
  def buyer(self) -> str:
    return FEMALE_NAMES[self.variant - 1]

  @property
  def seller(self) -> str:
    return MALE_NAMES[self.variant - 1]

  @property
  def opening_index(self) -> int:       # 0-based index into VISUAL_SCENE_OPENINGS
    return (self.variant - 1) % 5

  @property
  def cell(self) -> tuple:
    return (self.V, self.line) if self.C is None else (self.V, "C", self.C)

  @property
  def pid(self) -> str:
    c = "" if self.C is None else f"-C{self.C}"
    return f"v{self.variant:02d}-V{self.V}-{self.line}{c}"


def prompt_set(variants: Iterable[int] = MAIN_VARIANTS,
               values: Iterable[int] = VALUES) -> list[Prompt]:
  out = []
  for v in variants:
    for V in values:
      for line in NO_INFO_LINES:
        out.append(Prompt(v, V, line, None))
      for C in COSTS:
        out.append(Prompt(v, V, "information", C))
  return out


def all_cells(values: Iterable[int] = VALUES) -> list[tuple]:
  return sorted({p.cell for p in prompt_set([1], values)}, key=str)


def steering_cell_split(cell: tuple) -> str:
  """Disjoint cell split for steering: 'dev' or 'test'.

  No-information cells: V odd (3, 5, 7) -> dev; V even (2, 4, 6, 8) -> test.
  Information cells: V + C odd -> dev; even -> test.
  """
  if cell[1] != "C":
    return "dev" if cell[0] % 2 == 1 else "test"
  V, _, C = cell
  return "dev" if (V + C) % 2 == 1 else "test"


# ----------------------------------------------------------------- payoffs
def payoff(p: Prompt, k: int) -> float:
  """Expected payoff of bid k (no-info: over the uniform cost prior)."""
  if p.C is None:
    return (p.V - k) * k / 5.0            # P(C <= k) = k/5 for C uniform on 1..5
  return float(p.V - k) if k >= p.C else 0.0


def oracle_payoff(p: Prompt) -> float:
  return max(payoff(p, k) for k in PRICES)


def oracle_bids(p: Prompt) -> list[int]:
  best = oracle_payoff(p)
  return [k for k in PRICES if abs(payoff(p, k) - best) < 1e-12]


def oracle_bid_point(p: Prompt) -> float:
  """Single oracle bid used for calibration: mean of the optimal set."""
  b = oracle_bids(p)
  return sum(b) / len(b)


def has_unique_best(p: Prompt) -> bool:
  """True where the best offer is a single price (K2 uses only these cells)."""
  return len(oracle_bids(p)) == 1


def hard_regret(p: Prompt, k: int) -> float:
  return oracle_payoff(p) - payoff(p, k)


def soft_regret(p: Prompt, probs: dict[int, float]) -> float:
  return oracle_payoff(p) - sum(probs[k] * payoff(p, k) for k in PRICES)


def expected_bid(probs: dict[int, float]) -> float:
  return sum(k * probs[k] for k in PRICES)


def softmax_scores(letter_scores: dict[str, float], letter_to_price: dict[str, int]
                   ) -> dict[int, float]:
  """p(k): softmax over total answer log-probabilities, temperature 1."""
  m = max(letter_scores.values())
  ex = {l: math.exp(s - m) for l, s in letter_scores.items()}
  z = sum(ex.values())
  return {letter_to_price[l]: ex[l] / z for l in ex}


def cyclic_orders() -> list[tuple[int, ...]]:
  """Five option orders: '1 coin' first, '2 coins' first, ..."""
  return [tuple(PRICES[(s + i) % 5] for i in range(5)) for s in range(5)]


# ------------------------------------------------------------------- seeds
def call_seed(prompt_text: str, agent: str, pid: str, draw: int = 0) -> int:
  sep = "\u001f"
  h = hashlib.sha256(sep.join([prompt_text, agent, pid, str(draw)]).encode("utf-8"))
  return int.from_bytes(h.digest()[:8], "big")


# ----------------------------------------------------------- reasoning text
_QUESTION = re.compile(r"^\s*Question:\s*(.*)$")


_ANSWER = re.compile(r"^\s*Answer:\s?(.*)$", re.S)
_SUMMARY_Q = re.compile(r"^\s*(?:Summari[sz]e|Select the subset|Recall|What is the current)", re.I)


def _question_and_stem(call_prompt: str) -> tuple[str, str]:
  lines = [l for l in call_prompt.splitlines() if l.strip()]
  q, q_at = None, -1
  for i in range(len(lines) - 1, -1, -1):
    m = _QUESTION.match(lines[i])
    if m:
      q, q_at = m.group(1).strip(), i
      break
  if q is None:
    return (lines[-1].strip() if lines else ""), ""
  stem = ""
  if q_at < len(lines) - 1:                     # the prompt's own answer stem, if any
    m = _ANSWER.match(lines[-1])
    if m:
      stem = m.group(1).strip()
  return q, stem


def reasoning_entry(call_prompt: str, completion: str) -> str:
  """One S entry: the eliciting question line, then 'Answer:' followed by the
  prompt's own answer stem (e.g. 'Anya would') and the completion, so the entry
  reads as the model saw it."""
  q, stem = _question_and_stem(call_prompt)
  ans = completion.strip()
  ans = f"{stem} {ans}".strip() if stem else ans
  return f"Question: {q}\nAnswer: {ans}"


def is_summary_entry(call_prompt: str) -> bool:
  """Memory-retrieval / observation-summary calls (excluded from S_reason)."""
  return bool(_SUMMARY_Q.match(_question_and_stem(call_prompt)[0]))


def build_S(calls: Sequence[tuple[str, str]], reasoning_only: bool = False) -> str:
  """calls: (prompt, completion) of every sample_text call during act(), in order.
  reasoning_only=True gives S_reason (summary/retrieval calls dropped)."""
  return "\n\n".join(reasoning_entry(p, c) for p, c in calls
                     if not (reasoning_only and is_summary_entry(p)))


# --------------------------------------------------------- text controls
_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")
_VERB = re.compile(r"\b(?:offer|offers|propose|proposes|bid|bids|pay|pays|choose|"
                   r"chooses|go with|settle on|counter)\b", re.I)




_NUMERAL = re.compile(r"\d+(?:\.\d+)?")


def numeral_multiset(text: str) -> list[str]:
  return sorted(_NUMERAL.findall(text))


def answer_only(buyer: str, k: int) -> str:
  return f"{buyer} should offer {k} coin." if k == 1 else f"{buyer} should offer {k} coins."




def cap_tokens(text: str, tokenizer, cap: int = 3000) -> tuple[str, bool]:
  ids = tokenizer.encode(text, add_special_tokens=False)
  if len(ids) <= cap:
    return text, False
  half = cap // 2
  return (tokenizer.decode(ids[:half]) + "\n...\n" + tokenizer.decode(ids[-half:]),
          True)
