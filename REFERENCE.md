# Reference implementation

This document holds the reference implementation of the harness, condition builders, pipeline driver and analysis described in PROTOCOL.md, with its test results. Where the two disagree, PROTOCOL.md is authoritative and the disagreement is a bug to report.

## R1. Overview

### Layout

| File | What it does | Protocol sections |
|---|---|---|
| `refimpl/core.py` | Prompt set (420 prompts, 35 cells; extension V = 7, 8), best offers, regret, unique-best cells, cell split, seeds, reasoning text S and S\_reason (with answer stems), text utilities | 1.2, 4, 6, 8.1, 8.4, 10.1 |
| `refimpl/local_gemma2.py` | `LocalGemma2`: local stand-in for `together_ai.Gemma2` (system texts, few-shots, trimming, whole-answer and first-token letter scoring). Choice scoring is sequential (one candidate per pass) and fixed. Also: hook support, the letter-mass coherence measure, the generation-cache reset, and per-call seeding only inside a call context | 1.2, 4, 10.4 |
| `refimpl/determinism.py` | Sequential executor, seeded `default_rng`, deterministic torch | 4 |
| `refimpl/runtime.py` | Loads 9B (or 2B) from the pinned snapshot: bfloat16, eager attention, `low_cpu_mem_usage`, `device_map={"": 0}`. Loads all-mpnet-base-v2 on the CPU. Reports the environment | 3 |
| `refimpl/phase2.py` | Formative memories; player config; saving and loading memory banks (de-duplication hashes recomputed at load). Builds an agent as `haggling.py` does, seeds the decision, feeds it the script, and returns offer, regret, S, S\_reason and every model call | 8 |
| `refimpl/phase3.py` | Fixed decision prompt, token positions P1–P4, activation capture, steering hook; returns first-token and whole-answer p(k) | 9.1, 9.6, 10.3 |
| `refimpl/conditions.py` | The 28 Phase 3 conditions, the N7 donor rule, advice removal (including bare numbers and currency marks), format-matched filler, paraphrase retries, leakage-audit prompt | 9.2 |
| `refimpl/steering.py` | Layer and α grid, rescaling, (layer, α) tuning with a "no steering" option | 10.2, 10.4 |
| `refimpl/pipeline.py` | Run driver: Phase 2 and E1 with the exclusion rule; paraphrases; Phase 3 scoring and activation storage; native replay; leakage audit and its flag; pilot power rule; named directions (robust to dropped paraphrases); letter-span projection (E6); matched content copy; 1,000 random directions; tuning and test evaluation (`run_phase3b`) | 6, 8–10, 12 |
| `refimpl/analysis.py` | Sign-flip tests (exact for n ≤ 20), Wilcoxon (sensitivity), IUT, reverse rule, Holm (0.05 and 0.01), BH, bootstrap, verdicts, power simulation, A/B/R assembly, K1 (six components, including sharpening and the matched random permutation p), K2 (unique-best cells, partial correlation, five controls, bootstrap p = (1 + count)/(1 + n)), K1/K2 assembly, fidelity (E9) | 6, 9.3, 10.5, 11 |
| `tests/test_core.py`, `tests/test_design.py`, `tests/test_banks.py` | 30 unit tests (check P0.10) | 6 |
| `tests/smoke_gemma.py` | Phase 3 path on a real Gemma 2 checkpoint (P0.2, P0.7 and P0.9 logic) | 6 |
| `tests/scoring_orders.py` | Letter mass and first-token versus whole-answer top-choice agreement across the five option orders on one prompt (prints no probabilities or regret) | 1.2 |
| `tests/smoke_phase2.py` | One Concordia `rational_agent` decision through the Phase 2 harness on a pilot prompt, run twice; prints only call counts, retrieval flags and hashes (P0.6 and P0.7 logic) | 6 |
| `scripts/download_models.py` | Downloads the pinned revisions and checks every weight shard against the Hub's LFS SHA-256 | 3, P0.1 |
| `scripts/nonet.sh` | Runs a command with no network, as the unprivileged user, without `HF_TOKEN` | 5 |
| `scripts/check_phase3_memory.py`, `scripts/check_phase2_agents.py` | 9B engineering checks: Phase 3 peak memory and time per pass; one Phase 2 decision per agent, recording no outcome | 6 (P0.6, P0.11) |
| `scripts/generate_banks.py` | Generates and saves the 14 formative-memory banks, with a save-and-reload equality check | 6, 8.3 |
| `scripts/make_registration.py` | Writes the registration record (hashes, revisions, hardware) | 11 |
| `scripts/build_reference.py` | Builds this document with verbatim code listings | — |

### Environment

The code runs on the stack pinned in Protocol section 3:

- Python 3.11, torch 2.4.1, transformers 4.44.2, numpy 1.26.4, scipy 1.14.1, pandas 2.0.3, frozen in `requirements.lock` (CPU torch, 159 packages);
- for GPU runs, the same lock with `torch==2.4.1` from PyPI (CUDA 12.1 build), its `nvidia-*` packages and `pyarrow==17.0.0`, frozen in `requirements.gpu.lock` (173 packages);
- Concordia v1.8.9 (commit `3643ac0466f748b8055b61feb0b7908411f73d84`) on `PYTHONPATH`;
- the directory containing `agent_py_files/` (from the supplementary zip) on `PYTHONPATH`.

It uses no API newer than transformers 4.44.2. Every process that imports agent code runs without network and without `HF_TOKEN`, with `HF_HUB_OFFLINE=1`, `CUBLAS_WORKSPACE_CONFIG=:4096:8` and `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` (`scripts/nonet.sh`).

### How to run

```
python scripts/download_models.py                  # needs HF_TOKEN; verifies shard hashes
unset HF_TOKEN; export HF_HUB_OFFLINE=1
PYTHONPATH=concordia:agents_zip:. python -m pytest -q tests/
scripts/nonet.sh python tests/smoke_gemma.py 9b --device cuda
scripts/nonet.sh python tests/scoring_orders.py 9b --device cuda
scripts/nonet.sh python tests/smoke_phase2.py 2b --device cuda
scripts/nonet.sh python scripts/check_phase3_memory.py --notes-tokens 200 3000 3900
scripts/nonet.sh python scripts/check_phase2_agents.py
scripts/nonet.sh python scripts/generate_banks.py
```

`9b`, `2b` and `embedder` resolve to the snapshot directories of the pinned revisions under `./models`.

The full study calls these, in the order of Protocol section 12:

1. `pipeline.run_phase2` (memories loaded with `phase2.load_bank`), then again with `temperature=0.5, draws=range(5)` for E1;
2. `run_paraphrases`, `run_phase3`, `run_native_replay` and `run_leakage_audit`, passing `values=core.VALUES + core.EXT_VALUES` if the extension is triggered;
3. `run_phase3b`;
4. `analysis.abr_tests`, `analysis.k_tests` and `analysis.confirmatory_verdicts`.

The pilot uses `run_phase3(..., only=("N0", "N1"))` and `pilot_power_rule`.

`steering.LAYERS` (6–30) assumes 9B's 42 layers.

### Design notes

- **Sequential letter scoring.** The five answer sequences share a prefix and differ only in the letter token. Each is scored in its own forward pass through the decoder stack (`model.model`, no cache, batch size 1). The mode is fixed, so shapes, and therefore rounding, never depend on free memory. Only the positions that predict answer tokens go through the unembedding; the final soft-cap (30) and the log-softmax are computed in float32. A batched mode exists only for check P0.2.
- **Two scorings from the same passes.** The first-token log-probability of each letter at P1 (the Phase 3 primary) and the whole-answer score (letter, end-of-turn and newline, Concordia's rule) come from the same five passes.
- **Coherence.** Every pass shares P1, so pass b's first-position log-probability of its own letter is the probability of letter b. Their sum is the letter mass, which the tuning coherence rule uses and every condition reports.
- **Hooks in every pass.** Capture and steering hooks are registered once around the five passes, so they fire in each, at the same P1. Captured positions are at or before P1 and identical across passes.
- **Generation cache.** transformers 4.44.2 keeps Gemma 2's generation cache on the model and reuses it when large enough. That makes floating-point rounding depend on earlier calls, so `sample_text` deletes it before each call.
- **Seeding scope.** Per-call seeds apply only inside `call_context(...)` (Phases 2–3). Without a context (Phase 1), nothing is re-seeded and sampling follows the launcher's seed.
- **Memory banks.** A bank is saved as parquet (text, time, tags, importance, embedding). Loading re-adds the rows in order through `AssociativeMemory.add` with the stored embeddings, so the frame's columns, dtypes and order match the original. It also recomputes `_stored_hashes` as `hash((text, time, tuple(tags), importance))`, because Python's string hashes change between processes.
- **Memory copy.** `AssociativeMemory` holds a `threading.Lock` and cannot be deep-copied. Each Phase 2 run makes a blank memory on its own clock and copies the stored bank's rows and hashes into it. The decision then starts by seeding the global generators, because memory sampling uses numpy's global state.
- **Positions.** P1 is the last prefix token. P2–P4 come from the tokenizer's offset mapping on the decoded prefix, with an assertion that re-tokenising gives the same ids.
- **Steering** adds α·v to the chosen layer's output from P1 onwards, in each of the five passes.
- **Agent code** from the zip is imported only by the pipeline and the check scripts, always without network. A static audit found no network, subprocess, `eval`/`exec` or file-writing calls in the three entry files.

## R2. Code

Every file below is listed verbatim (generated by `scripts/build_reference.py`).

### `refimpl/core.py`

````python
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
````

### `refimpl/local_gemma2.py`

````python
"""LocalGemma2: a local stand-in for concordia/language_model/together_ai.py:Gemma2.

Reproduces that class's message lists, prompt trimming and choice scoring with a
local Transformers model, so internal activations are accessible. The trimming
function is copied from Concordia v1.8.9 (Apache 2.0) so behaviour matches.
"""
from __future__ import annotations

import contextlib
import contextvars
import dataclasses
from typing import Callable, Collection, Sequence

import numpy as np
import torch

try:  # Concordia is needed only when the class is used inside agents.
  from concordia.language_model import language_model as _lm
  _Base = _lm.LanguageModel
except ImportError:  # pragma: no cover - allows unit tests without Concordia
  _Base = object

from . import core

TEXT_SYSTEM = (
    "You always continue sentences provided by the user and you never repeat "
    "what the user has already said. All responses must end with a period. Try "
    "not to use lists, but if you must, then always delimit list items using "
    "either semicolons or single newline characters ('\\n'), never delimit list "
    "items with double carriage returns ('\\n\\n')."
)
CHOICE_SYSTEM = ("You always continue sentences provided by the user and you never "
                 "repeat what the user already said.")
FEW_SHOT = [
    ("Question: Is Jake a turtle?\nAnswer: Jake is ", "not a turtle."),
    ("Question: What is Priya doing right now?\nAnswer: Priya is currently ",
     "sleeping."),
]
MAX_ALLOWED_TOKENS = 7000
NUM_INITIAL_TOKENS = 500
GUESS_CHARS_PER_TOKEN = 4
DEFAULT_NUM_RESPONSE_TOKENS = 5000
CONTEXT_LIMIT = 8192


def ensure_prompt_not_too_long(prompt: str, num_response_tokens: int,
                               guess_chars_per_token: int = GUESS_CHARS_PER_TOKEN
                               ) -> str:
  """Copied from together_ai._ensure_prompt_not_too_long (v1.8.9)."""
  num_initial_chars = NUM_INITIAL_TOKENS * guess_chars_per_token
  max_prompt_tokens = MAX_ALLOWED_TOKENS - num_response_tokens
  if max_prompt_tokens <= 0:
    raise ValueError(f"Cannot reserve {num_response_tokens} of "
                     f"{MAX_ALLOWED_TOKENS} tokens.")
  max_prompt_chars = max_prompt_tokens * guess_chars_per_token
  if len(prompt) <= max_prompt_chars:
    return prompt
  if max_prompt_chars > num_initial_chars:
    num_final_chars = max_prompt_chars - num_initial_chars
    return prompt[:num_initial_chars] + prompt[-num_final_chars:]
  return prompt[-max_prompt_chars:]


def build_messages(system: str, user_prompt: str, assistant: str | None = None
                   ) -> list[dict]:
  """Gemma has no system role: the system text is folded into the first user turn."""
  msgs = []
  for i, (u, a) in enumerate(FEW_SHOT):
    msgs.append({"role": "user", "content": (system + "\n\n" + u) if i == 0 else u})
    msgs.append({"role": "assistant", "content": a})
  msgs.append({"role": "user", "content": user_prompt})
  if assistant is not None:
    msgs.append({"role": "assistant", "content": assistant})
  return msgs


# Call context: set by the harness so seeds and logs know who is calling.
@dataclasses.dataclass
class CallContext:
  agent: str = ""
  pid: str = ""
  draw: int = 0
  temperature_override: float | None = None   # 0.0 in Phases 2-3


# The default is a sentinel: "no call context set" (Phase 1, native runs). Only
# calls made inside call_context(...) (Phases 2-3) get per-call seeds.
NO_CONTEXT = CallContext()
CONTEXT: contextvars.ContextVar[CallContext] = contextvars.ContextVar(
    "call_context", default=NO_CONTEXT)


def context_is_set() -> bool:
  return CONTEXT.get() is not NO_CONTEXT


@contextlib.contextmanager
def call_context(**kw):
  token = CONTEXT.set(CallContext(**kw))
  try:
    yield
  finally:
    CONTEXT.reset(token)


class _StopOnStrings:
  def __init__(self, tokenizer, stops: Collection[str], start: int):
    self.tok, self.stops, self.start = tokenizer, [s for s in stops if s], start

  def __call__(self, input_ids, scores, **kw) -> bool:
    if not self.stops:
      return False
    text = self.tok.decode(input_ids[0, self.start:], skip_special_tokens=True)
    return any(s in text for s in self.stops)


class LocalGemma2(_Base):
  """Drop-in LanguageModel for Concordia v1.8.9 agents and game masters."""

  def __init__(self, model, tokenizer, *, log: Callable[[dict], None] | None = None,
               sequential: bool = True):
    # Choice scoring mode, fixed for the whole run (Protocol section 4). True: the
    # letter sequences are always scored one at a time (batch size 1), on every
    # GPU and whatever the free memory. False (batched) is kept only for the P0.2
    # comparison on short prompts.
    self.sequential = sequential
    self.max_new_cap: int | None = None
    self.last_letter_mass: float = float("nan")
    self.last_first_token: dict[str, float] = {}
    self.model, self.tok = model, tokenizer
    self.device = next(model.parameters()).device
    self.log = log or (lambda rec: None)
    eot = tokenizer.convert_tokens_to_ids("<end_of_turn>")
    self.eos_ids = [i for i in {tokenizer.eos_token_id, eot} if isinstance(i, int) and i >= 0]

  # ---------------------------------------------------------------- utils
  def render(self, msgs: list[dict], add_generation_prompt: bool) -> str:
    return self.tok.apply_chat_template(msgs, tokenize=False,
                                        add_generation_prompt=add_generation_prompt)

  def encode(self, text: str) -> torch.Tensor:
    ids = self.tok(text, add_special_tokens=False, return_tensors="pt").input_ids
    return ids.to(self.device)

  def _seed(self, prompt: str) -> int | None:
    """Per-call seeding, applied only when a call context is set (Phases 2-3).
    Without one (Phase 1) nothing is re-seeded, so sampling follows the
    launcher's seed."""
    if not context_is_set():
      return None
    ctx = CONTEXT.get()
    s = core.call_seed(prompt, ctx.agent, ctx.pid, ctx.draw)
    import random
    random.seed(s)
    np.random.seed(s % (2**32))
    torch.manual_seed(s)
    return s

  # ---------------------------------------------------------- sample_text
  def sample_text(self, prompt: str, *, max_tokens: int = 256,
                  terminators: Collection[str] = (), temperature: float = 0.5,
                  timeout: float = 60, seed: int | None = None) -> str:
    del timeout, seed  # seeds are derived from the call context instead
    ctx = CONTEXT.get()
    if ctx.temperature_override is not None:
      temperature = ctx.temperature_override
    original = prompt
    max_new = min(max_tokens, DEFAULT_NUM_RESPONSE_TOKENS)
    if self.max_new_cap is not None:   # smoke tests on CPU only; None in real runs
      max_new = min(max_new, self.max_new_cap)
    prompt = ensure_prompt_not_too_long(original, max_tokens)
    ids = self.encode(self.render(build_messages(TEXT_SYSTEM, prompt), True))
    if ids.shape[1] + max_new > CONTEXT_LIMIT:  # mirrors the API-error retry
      prompt = ensure_prompt_not_too_long(original, max_tokens, guess_chars_per_token=1)
      ids = self.encode(self.render(build_messages(TEXT_SYSTEM, prompt), True))
    self._seed(original)
    gen_kw = dict(max_new_tokens=max_new, eos_token_id=self.eos_ids,
                  pad_token_id=self.tok.pad_token_id or self.eos_ids[0],
                  stopping_criteria=[_StopOnStrings(self.tok, terminators, ids.shape[1])])
    if temperature and temperature > 0:
      gen_kw.update(do_sample=True, temperature=float(temperature), top_p=1.0, top_k=0)
    else:
      gen_kw.update(do_sample=False)
    # transformers 4.44 keeps Gemma 2's HybridCache on the model (`_cache`) and
    # reuses it when large enough, so attention shapes - and floating-point
    # rounding - would depend on earlier calls. Drop it so every call allocates a
    # cache sized by its own input only (history-independent, P0.7).
    if hasattr(self.model, "_cache"):
      del self.model._cache
    with torch.no_grad():
      out = self.model.generate(ids, attention_mask=torch.ones_like(ids), **gen_kw)
    text = self.tok.decode(out[0, ids.shape[1]:], skip_special_tokens=True)
    cut = [text.find(s) for s in terminators if s and s in text]
    if cut:
      text = text[:min(cut)]
    self.log({"kind": "text", "agent": ctx.agent, "pid": ctx.pid,
              "prompt": original, "output": text})
    return text

  # -------------------------------------------------------- choice scoring
  def letter_scores(self, user_prompt: str, letters: Sequence[str],
                    hooks: Sequence = (), sequential: bool | None = None
                    ) -> tuple[dict[str, float], int, torch.Tensor]:
    """Total log-probability of each letter as the whole assistant answer.

    Returns (scores, p1_index, prefix_ids). p1_index is the position of the last
    prefix token (the newline after '<start_of_turn>model').

    All letters are single tokens, so the candidate sequences have equal length.
    sequential=True (the default, self.sequential) scores them one per forward
    pass, always with batch size 1; it never depends on free memory. Hooks are
    registered for every pass, so activations are captured and steering applied
    in each pass; P1 is the same position in each. sequential=False scores all
    candidates in one batch (P0.2 comparison only).
    """
    if sequential is None:
      sequential = self.sequential
    trimmed = ensure_prompt_not_too_long(user_prompt, max(len(l) for l in letters))
    prefix = self.render(build_messages(CHOICE_SYSTEM, trimmed), True)
    prefix_ids = self.encode(prefix)[0]
    seqs = []
    for l in letters:
      full = self.render(build_messages(CHOICE_SYSTEM, trimmed, l), False)
      ids = self.encode(full)[0]
      assert torch.equal(ids[:len(prefix_ids)], prefix_ids), "prefix tokenisation drift"
      seqs.append(ids)
    n = {len(s) for s in seqs}
    assert len(n) == 1, "letters must tokenise to equal lengths"
    batch = torch.stack(seqs)
    start = len(prefix_ids)
    groups = [batch[b:b + 1] for b in range(len(seqs))] if sequential else [batch]
    cap = getattr(self.model.config, "final_logit_softcapping", None)
    logps = []
    handles = [h() for h in hooks]
    try:
      with torch.no_grad():
        for g in groups:
          # Run the decoder stack (hooks fire here), then unembed only the
          # positions that predict answer tokens: start-1 .. len-2. This avoids
          # materialising [batch, seq, 256k] logits and works on transformers
          # 4.44.2 (no logits_to_keep). The final-logit soft-cap is applied in
          # float32.
          hidden = self.model.model(input_ids=g, use_cache=False).last_hidden_state  # after final norm
          logits = self.model.lm_head(hidden[:, start - 1:-1]).float()
          del hidden
          if cap:
            logits = torch.tanh(logits / cap) * cap
          logps.append(torch.log_softmax(logits, dim=-1))
          del logits
    finally:
      for h in handles:
        h.remove()
    logp = torch.cat(logps, 0)
    # Coherence measure (Protocol 10.4): next-token probability mass on the letters
    # at P1. Every row shares P1, so row b gives the probability of letter b.
    first = {l: float(logp[b, 0, batch[b, start]]) for b, l in enumerate(letters)}
    self.last_letter_mass = float(sum(np.exp(v) for v in first.values()))
    # First-token log-probability of each letter at P1 (Phase 3 primary outcome).
    self.last_first_token = first
    scores = {}
    for b, l in enumerate(letters):
      tgt = batch[b, start:].to(logp.device)
      lp = logp[b].gather(-1, tgt[:, None]).squeeze(-1)
      scores[l] = float(lp.sum())
    return scores, start - 1, prefix_ids

  def sample_choice(self, prompt: str, responses: Sequence[str], *,
                    seed: int | None = None) -> tuple[int, str, dict[str, float]]:
    del seed
    self._seed(prompt)
    scores, _, _ = self.letter_scores(prompt, list(responses))
    arr = np.array([scores[r] for r in responses])
    idx = int(np.argmax(arr))           # ties -> first, as np.argmax
    ctx = CONTEXT.get()
    self.log({"kind": "choice", "agent": ctx.agent, "pid": ctx.pid,
              "prompt": prompt, "scores": scores, "choice": responses[idx]})
    return idx, responses[idx], dict(scores)
````

### `refimpl/determinism.py`

````python
"""Patches that make Phases 2-3 deterministic (Protocol section 4, "Determinism")."""
from __future__ import annotations

import concurrent.futures
import contextlib
import os

import numpy as np
import torch

from . import core
from .local_gemma2 import CONTEXT


class _SequentialExecutor(concurrent.futures.Executor):
  """Runs every submitted task immediately, in submission order, on this thread."""

  def __init__(self, *args, **kwargs):
    pass

  def submit(self, fn, /, *args, **kwargs):
    fut = concurrent.futures.Future()
    try:
      fut.set_result(fn(*args, **kwargs))
    except BaseException as e:  # noqa: BLE001 - propagate through the future
      fut.set_exception(e)
    return fut

  def map(self, fn, *iterables, timeout=None, chunksize=1):
    return [fn(*a) for a in zip(*iterables)]

  def shutdown(self, wait=True, *, cancel_futures=False):
    pass


_ORIGINAL_DEFAULT_RNG = np.random.default_rng
_RNG_COUNTER = {"n": 0}


def _seeded_default_rng(seed=None):
  """default_rng(): unseeded calls get a seed from the current call context.

  The counter resets at each agent decision (reset_decision_counter), so the k-th
  unseeded generator within a decision always gets the same seed.
  """
  if seed is not None:
    return _ORIGINAL_DEFAULT_RNG(seed)
  ctx = CONTEXT.get()
  _RNG_COUNTER["n"] += 1
  s = core.call_seed(f"default_rng#{_RNG_COUNTER['n']}", ctx.agent, ctx.pid, ctx.draw)
  return _ORIGINAL_DEFAULT_RNG(np.random.PCG64(s))


def reset_decision_counter():
  _RNG_COUNTER["n"] = 0


@contextlib.contextmanager
def deterministic_execution():
  """Apply all Phase 2-3 patches for the duration of the block."""
  os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
  torch.use_deterministic_algorithms(True)
  saved_pool = concurrent.futures.ThreadPoolExecutor
  saved_rng = np.random.default_rng
  concurrent.futures.ThreadPoolExecutor = _SequentialExecutor
  np.random.default_rng = _seeded_default_rng
  # concordia.utils.concurrency (run_tasks, map_parallel, ...) creates its pools via
  # concurrent.futures.ThreadPoolExecutor at call time, so this one patch covers it.
  try:
    yield
  finally:
    concurrent.futures.ThreadPoolExecutor = saved_pool
    np.random.default_rng = saved_rng
````

### `refimpl/runtime.py`

````python
"""Model and embedder loading for GPU runs (Protocol section 3).

Models live in ./models in the Hugging Face cache layout (scripts/download_models.py),
so each path is the snapshot directory of its pinned revision. Every process that
imports agent code runs with HF_HUB_OFFLINE=1 and no network.

The 9B model is loaded with low_cpu_mem_usage=True and device_map={"": 0}: shards are
memory-mapped and moved to the GPU tensor by tensor, so the weights never sit in
system RAM in full (the bank-generation machine has 16 GB of RAM). Only one language
model is loaded per process.
"""
from __future__ import annotations

import os

import torch

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(REPO_ROOT, "models")

GEMMA_9B = ("google/gemma-2-9b-it", "11c9b309abf73637e4b6f9a3fa1e92e615547819")
GEMMA_2B = ("google/gemma-2-2b-it", "299a8560bedf22ed1c72a8a11e7dce4a7f9f51f8")
EMBEDDER = ("sentence-transformers/all-mpnet-base-v2", "e8c3b32edf5434bc2275fc9bab85f82640a19130")
PINS = {"9b": GEMMA_9B, "2b": GEMMA_2B, "embedder": EMBEDDER}


def snapshot_path(repo: str, revision: str, models_dir: str = MODELS_DIR) -> str:
  path = os.path.join(models_dir, "models--" + repo.replace("/", "--"), "snapshots", revision)
  if not os.path.isdir(path):
    raise FileNotFoundError(f"{repo}@{revision} not found under {models_dir}")
  return path


def resolve(name_or_path: str) -> tuple[str, str | None]:
  """'9b' / '2b' / 'embedder' -> (snapshot path, revision); a path -> (path, None)."""
  if name_or_path in PINS:
    repo, rev = PINS[name_or_path]
    return snapshot_path(repo, rev), rev
  for repo, rev in PINS.values():
    if os.path.abspath(name_or_path) == os.path.abspath(snapshot_path_or_none(repo, rev) or ""):
      return name_or_path, rev
  return name_or_path, None


def snapshot_path_or_none(repo, rev):
  try:
    return snapshot_path(repo, rev)
  except FileNotFoundError:
    return None


def load_gemma(name_or_path: str = "9b", device: str = "cuda"):
  """Returns (model, tokenizer). device='cuda': bfloat16, eager attention,
  low_cpu_mem_usage, device_map={"": 0} (straight to GPU 0). device='cpu': the
  CPU smoke-test configuration."""
  from transformers import AutoModelForCausalLM, AutoTokenizer
  path, rev = resolve(name_or_path)
  kw = dict(revision=rev) if rev else {}
  tok = AutoTokenizer.from_pretrained(path, **kw)
  if device == "cuda":
    model = AutoModelForCausalLM.from_pretrained(
        path, torch_dtype=torch.bfloat16, attn_implementation="eager",
        low_cpu_mem_usage=True, device_map={"": 0}, **kw)
  elif device == "cpu":
    model = AutoModelForCausalLM.from_pretrained(
        path, torch_dtype=torch.bfloat16, attn_implementation="eager",
        low_cpu_mem_usage=True, **kw)
  else:
    raise ValueError(device)
  return model.eval(), tok


def load_lm(name_or_path: str = "9b", device: str = "cuda", sequential: bool = True, **kw):
  from .local_gemma2 import LocalGemma2
  model, tok = load_gemma(name_or_path, device)
  return LocalGemma2(model, tok, sequential=sequential, **kw)


def load_embedder(name_or_path: str = "embedder"):
  """all-mpnet-base-v2 on the CPU (its vectors go into the hashed memory banks).
  Returns (callable text -> vector, SentenceTransformer)."""
  from sentence_transformers import SentenceTransformer
  path, rev = resolve(name_or_path)
  kw = dict(revision=rev) if rev else {}
  model = SentenceTransformer(path, device="cpu", **kw)
  return (lambda t: model.encode(t, show_progress_bar=False)), model


def env_report() -> dict:
  import transformers
  out = {"torch": torch.__version__, "torch.version.cuda": torch.version.cuda,
         "cudnn": torch.backends.cudnn.version(), "transformers": transformers.__version__,
         "CUBLAS_WORKSPACE_CONFIG": os.environ.get("CUBLAS_WORKSPACE_CONFIG"),
         "PYTORCH_CUDA_ALLOC_CONF": os.environ.get("PYTORCH_CUDA_ALLOC_CONF"),
         "HF_HUB_OFFLINE": os.environ.get("HF_HUB_OFFLINE")}
  if torch.cuda.is_available():
    out["gpu"] = torch.cuda.get_device_name(0)
    out["gpu_total_bytes"] = torch.cuda.get_device_properties(0).total_memory
  return out
````

### `refimpl/phase2.py`

````python
"""Phase 2 harness: build one agent exactly as v1.8.9 haggling.py does, feed it the
scripted conversation, and collect its decision and reasoning text S.

Requires Concordia v1.8.9 on the path and the agent files from the supplementary
zip importable as modules (e.g. `agent_py_files.taehun_cgcal`).
"""
from __future__ import annotations

import datetime
import importlib
import random

import numpy as np
import torch

from concordia.associative_memory import blank_memories, formative_memories, importance_function
from concordia.clocks import game_clock
from concordia.typing import entity as entity_lib

from examples.modular.environment import haggling
from examples.modular.environment.modules import fruitville_haggling as fv

from . import core, phase3
from .determinism import deterministic_execution, reset_decision_counter
from .local_gemma2 import LocalGemma2, call_context

START = datetime.datetime(year=fv.YEAR, month=fv.MONTH, day=fv.DAY)   # 1895-09-12 00:00
SETUP = START - datetime.timedelta(days=1)
DECISION_SPEC = entity_lib.choice_action_spec(
    call_to_action="What price would {name} propose?:",
    options=tuple(core.OPTION_TEXT[k] for k in core.PRICES), tag="choice")


def formative_memory(lm: LocalGemma2, embedder, variant: int):
  """Generated once per variant (greedy) and stored; reused for every agent."""
  cfg = player_config(variant)                # seeds the global RNG first (get_trait)
  clock = game_clock.MultiIntervalClock(start=START,
                                        step_sizes=[haggling.MAJOR_TIME_STEP,
                                                    haggling.MINOR_TIME_STEP])
  blank = blank_memories.MemoryFactory(
      model=lm, embedder=embedder,
      importance=importance_function.ConstantImportanceModel().importance,
      clock_now=clock.now)
  shared, _ = haggling.get_shared_memories_and_context(fv.SCENARIO_PREMISE)
  factory = formative_memories.FormativeMemoryFactory(
      model=lm, shared_memories=shared,
      blank_memory_factory_call=blank.make_blank_memory, current_date=START)
  with call_context(agent="formative", pid=f"variant{variant}", temperature_override=0.0):
    with deterministic_execution():
      mem = factory.make_memories(cfg)
  for extra in cfg.extras["player_specific_memories"]:   # as _make_player_memories
    mem.add(extra, tags=["initial_player_specific_memory"])
  # Release: mem.get_data_frame() (text, time, tags, importance, embedding) as parquet.
  return mem, cfg


def run_decision(lm: LocalGemma2, embedder, agent_module: str, p: core.Prompt,
                 formative_mem, cfg, openings: list[str],
                 utter_fmt: str = '{speaker} -- "{text}"', draw: int = 0,
                 temperature: float = 0.0) -> dict:
  mod = importlib.import_module(agent_module)
  clock = game_clock.MultiIntervalClock(start=SETUP,
                                        step_sizes=[haggling.MAJOR_TIME_STEP,
                                                    haggling.MINOR_TIME_STEP])
  # Identical starting memories on this run's clock. AssociativeMemory holds a
  # threading.Lock, so it cannot be deep-copied: make a blank bank and copy rows.
  memory = blank_memories.MemoryFactory(
      model=lm, embedder=embedder,
      importance=importance_function.ConstantImportanceModel().importance,
      clock_now=clock.now).make_blank_memory()
  memory._memory_bank = formative_mem.get_data_frame()        # a copy
  memory._stored_hashes = set(formative_mem._stored_hashes)
  agent = mod.build_agent(config=cfg, model=lm, memory=memory, clock=clock,
                          update_time_interval=haggling.MAJOR_TIME_STEP)
  calls = []
  lm.log = lambda rec: calls.append(rec)
  with call_context(agent=agent_module, pid=p.pid, draw=draw,
                    temperature_override=temperature):
    with deterministic_execution():
      reset_decision_counter()
      # AssociativeMemory.retrieve_random(_with_importance) calls
      # DataFrame.sample(random_state=None), i.e. numpy's global RNG, and add()
      # calls it before any model call has re-seeded that RNG. Seed the global
      # generators at the start of every decision so that state is fixed.
      s0 = core.call_seed("decision-start", agent_module, p.pid, draw)
      random.seed(s0)
      np.random.seed(s0 % (2**32))
      torch.manual_seed(s0)
      # Setup-time observations, as haggling.py's _init_premise_memories does.
      for text in [fv.SCENARIO_PREMISE, phase3.SHARED_MEMORY_1, phase3.SHARED_MEMORY_2,
                   *core.RULE_MEMORIES]:
        agent.observe(text)
      clock.set(START)
      agent.observe(phase3.premise(p, openings[p.opening_index]))
      for u in phase3.utterances(p, utter_fmt):
        clock.advance()
        agent.observe(u)
      agent.observe(f"{p.buyer} is ready to make an offer.")
      act_from = len(calls)
      choice_text = agent.act(DECISION_SPEC)
  act_calls = calls[act_from:]
  k = next(k for k, t in core.OPTION_TEXT.items() if t == choice_text)
  text_calls = [(c["prompt"], c["output"]) for c in act_calls if c["kind"] == "text"]
  S = core.build_S(text_calls)
  S_reason = core.build_S(text_calls, reasoning_only=True)
  rule_seen = {i: any(r in c["prompt"] for c in act_calls) for i, r in
               enumerate(core.RULE_MEMORIES)}
  return {"pid": p.pid, "agent": agent_module, "draw": draw, "k": k,
          "hard_regret": core.hard_regret(p, k), "S": S, "S_reason": S_reason,
          "calls": calls,
          "rule_memories_in_prompts": rule_seen}


# ------------------------------------------------------- formative-memory banks
BANK_COLUMNS = ("text", "time", "tags", "importance", "embedding")


def player_config(variant: int):
  """The player config exactly as formative_memory() derives it (global random
  seeded first, because get_trait() uses it)."""
  name = core.FEMALE_NAMES[variant - 1]
  random.seed(1000 + variant)
  return haggling.configure_player(name, "female", fv.YEAR, True,
                                   random.Random(1000 + variant))


def save_bank(mem, path: str) -> str:
  """Writes mem's rows (text, time, tags, importance, embedding) as parquet and
  returns the file's SHA-256."""
  import hashlib
  import pyarrow as pa
  import pyarrow.parquet as pq
  df = mem.get_data_frame()
  schema = pa.schema([("text", pa.string()), ("time", pa.timestamp("ns")),
                      ("tags", pa.list_(pa.string())), ("importance", pa.float64()),
                      ("embedding", pa.list_(pa.float32()))])
  table = pa.table({
      "text": [str(t) for t in df["text"]],
      "time": [pd_timestamp(t) for t in df["time"]],
      "tags": [list(t) for t in df["tags"]],
      "importance": [float(x) for x in df["importance"]],
      "embedding": [np.asarray(e, dtype=np.float32) for e in df["embedding"]]},
      schema=schema)
  pq.write_table(table, path)
  with open(path, "rb") as f:
    return hashlib.sha256(f.read()).hexdigest()


def pd_timestamp(t):
  import pandas as pd
  return pd.Timestamp(t)


def bank_hash(text: str, time, tags, importance) -> int:
  """AssociativeMemory.add's de-duplication hash. Python string hashes change
  between processes, so this is always recomputed at load, never stored."""
  return hash((text, time, tuple(tags), importance))


def load_bank(path: str, lm, embedder, variant: int):
  """Rebuilds (memory, cfg) as formative_memory() returned them, from a saved bank.

  Rows are re-added in their saved order through AssociativeMemory.add, with the
  stored embedding (the embedder is not re-run) and the stored time, tags (as a
  tuple) and importance, so the frame has the same columns, dtypes and order as
  the original. _stored_hashes is recomputed in this process."""
  import pyarrow.parquet as pq
  table = pq.read_table(path)
  assert tuple(table.column_names) == BANK_COLUMNS, table.column_names
  rows = table.to_pylist()
  stored = {}
  for r in rows:
    e = np.asarray(r["embedding"], dtype=np.float32)
    prev = stored.setdefault(r["text"], e)
    assert np.array_equal(prev, e), "one text with two embeddings"
  clock = game_clock.MultiIntervalClock(start=START,
                                        step_sizes=[haggling.MAJOR_TIME_STEP,
                                                    haggling.MINOR_TIME_STEP])
  mem = blank_memories.MemoryFactory(
      model=lm, embedder=lambda t: stored[t].copy(),
      importance=importance_function.ConstantImportanceModel().importance,
      clock_now=clock.now).make_blank_memory()
  for r in rows:
    t = r["time"]
    t = t.to_pydatetime() if hasattr(t, "to_pydatetime") else t
    mem.add(r["text"], timestamp=t, tags=tuple(r["tags"]), importance=float(r["importance"]))
  assert len(mem.get_data_frame()) == len(rows), "duplicate rows in bank"
  expected = {bank_hash(r["text"], (r["time"].to_pydatetime() if hasattr(r["time"], "to_pydatetime")
                                    else r["time"]), r["tags"], float(r["importance"]))
              for r in rows}
  mem._stored_hashes = expected
  mem._embedder = embedder          # real embedder for anything added later
  return mem, player_config(variant)
````

### `refimpl/phase3.py`

````python
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
  the block, before the final norm) at given positions, batch item 0."""
  layers = lm.model.model.layers
  factories = []
  for i, layer in enumerate(layers):
    def make(i=i, layer=layer):
      def hook(mod, inp, out):
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
                 steer: tuple[int, torch.Tensor] | None = None):
  """Returns (probs, hard, store, probs_full).

  probs: p(k) from the first-token letter log-probabilities at P1, renormalised
  over the five letters (the Phase 3 primary outcome). hard: its argmax (ties to
  the earlier letter). probs_full: p(k) from whole-answer scores (letter,
  <end_of_turn>, newline; sensitivity analysis). store: activations if capture."""
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
  scores, p1_check, _ = lm.letter_scores(user, LETTERS, hooks=hooks)
  assert p1_check == p1
  first = lm.last_first_token
  probs = core.softmax_scores(first, l2p)
  probs_full = core.softmax_scores(scores, l2p)
  hard = l2p[max(LETTERS, key=lambda l: (first[l], -LETTERS.index(l)))]
  return probs, hard, store, probs_full
````

### `refimpl/conditions.py`

````python
"""Phase 3 condition builders (Protocol section 9.2): the inserted text per condition."""
from __future__ import annotations

import re
from typing import Callable, Mapping, Sequence

from . import core

BASELINE = "concordia.factory.agent.rational_agent"
ENTRIES = ("agent_py_files.taehun_cgcal",
           "agent_py_files.fluffy_fluffyagent_v16submission",
           "agent_py_files.hgyun_loss_aversion_agent_v3_plus2")
AGENTS = (BASELINE, *ENTRIES)
ENTRY_CODE = dict(zip(ENTRIES, ("N2", "N3", "N4")))

# ------------------------------------------------------------ strict removal
_EVAL = re.compile(r"\b(?:profit|profits|gain|gains|payoff|payoffs|expected|earn|earns|"
                   r"earning|surplus|return|returns|optimal|best|better|worse|worth|"
                   r"maximi[sz]e|maximi[sz]es|recommend|recommended|should|ideal|fair|reasonable|"
                   r"good|acceptable|sensible|appropriate|aim|aims|target|targets|"
                   r"go for|start|starting|open|opening)\b", re.I)
_PRICE_ALL = re.compile(r"\b([1-5])\s*coins?\b|\b(one|two|three|four|five)\s+coins?\b", re.I)
_OPTION = re.compile(r"\(\s*[a-e]\s*\)|\boption\s+[a-e1-5]\b", re.I)
# Bare price numbers: after a decision verb or 'price', or with a currency mark.
_BARE = re.compile(r"\b(?:offer|offers|offering|propose|proposes|proposing|bid|bids|"
                   r"bidding|pay|pays|paying|price|prices|priced|at|for)\s+(?:of\s+|is\s+|"
                   r"around\s+|about\s+)?([1-5])\b(?!\s*(?:kg|kilogram|%|per))|"
                   r"[$€£¢]\s?([1-5])\b", re.I)
_NUM_AFTER_PRICE = re.compile(r"\b[1-5]\s*coins?\b[^.\n]*?(?:[:=]|->|→)\s*-?\d", re.I)
_WORDNUM = {"one": "1", "two": "2", "three": "3", "four": "4", "five": "5"}


def _prices(sent: str) -> set[str]:
  found = {(a or _WORDNUM[b.lower()]) for a, b in _PRICE_ALL.findall(sent)}
  found |= {(a or b) for a, b in _BARE.findall(sent)}
  return found


def remove_recommendations_strict(text: str) -> str:
  """N8 rule. A sentence is removed if it mentions a price - '3 coins', 'three
  coins', a bare 1-5 after a decision verb or 'price'/'at'/'for' ('offer 2', 'a price
  of 3'), or a currency mark - or an option label, and any of: a decision verb,
  an evaluative/payoff word, a number attached to the price ('3 coins: 2'), or two
  or more different prices. Single-price statements of facts (resale value,
  stated cost, average price) survive."""
  sents = [s for s in core._SENT_SPLIT.split(text) if s and s.strip()]
  keep = []
  for s in sents:
    has_price = bool(_prices(s)) or bool(_OPTION.search(s))
    drop = has_price and (core._VERB.search(s) or _EVAL.search(s) or _OPTION.search(s)
                          or _NUM_AFTER_PRICE.search(s) or len(_prices(s)) >= 2)
    if not drop:
      keep.append(s.strip())
  return " ".join(keep)


# ------------------------------------------------------------------ fillers
FILLER_QUESTION = "What does the market look like?"


def qa_filler(openings: Sequence[str], n_tokens: int, tokenizer) -> str:
  """N6: neutral filler in the same 'Question:/Answer:' format as S, cycling the
  five scene openings, cut to exactly n_tokens tokens."""
  if n_tokens <= 0:
    return ""
  blocks, ids, i = [], [], 0
  while len(ids) < n_tokens:
    blocks.append(f"Question: {FILLER_QUESTION}\nAnswer: {openings[i % len(openings)]}")
    ids = tokenizer.encode("\n\n".join(blocks), add_special_tokens=False)
    i += 1
  text = tokenizer.decode(ids[:n_tokens])
  while len(tokenizer.encode(text, add_special_tokens=False)) > n_tokens:
    text = text[:-1]
  return text


def n_tokens(text: str, tokenizer) -> int:
  return len(tokenizer.encode(text, add_special_tokens=False))


# --------------------------------------------------------------- paraphrase
PARAPHRASE_INSTRUCTION = ("Rewrite the following notes in different words. "
                          "Keep every fact and number exactly.")


def paraphrase(sample_text: Callable[..., str], call_context, text: str, agent: str,
               pid: str) -> str | None:
  """Greedy first; up to three retries at temperature 0.7 (draws 1-3). None if all
  attempts change the multiset of numerals."""
  prompt = PARAPHRASE_INSTRUCTION + "\n\n" + text
  target = core.numeral_multiset(text)
  for draw, temp in ((0, 0.0), (1, 0.7), (2, 0.7), (3, 0.7)):
    with call_context(agent=f"paraphrase:{agent}", pid=pid, draw=draw,
                      temperature_override=temp):
      out = sample_text(prompt, max_tokens=3000)
    if core.numeral_multiset(out) == target:
      return out
  return None


# ----------------------------------------------------------------- builder
def _donor_key(p: core.Prompt, q: core.Prompt) -> tuple:
  """Manhattan distance in (V, C), then smaller V, then smaller C. No-information
  prompts use C = 0."""
  c_p, c_q = p.C or 0, q.C or 0
  return (abs(p.V - q.V) + abs(c_p - c_q), q.V, c_q)


def n7_donor(p: core.Prompt, values: Sequence[int] = core.VALUES) -> core.Prompt:
  """N7 donor: the prompt with the same variant and seller line whose set of best
  offers does not overlap p's, nearest in (V, C) (_donor_key). No-information
  prompts take only no-information donors with the same line. Where no donor is
  disjoint (only cell V = 5, C = 5, where every offer is best), the donor with the
  smallest overlap is used, under the same distance and tie rule."""
  if p.C is None:
    cands = [core.Prompt(p.variant, V, p.line, None) for V in values]
  else:
    cands = [core.Prompt(p.variant, V, p.line, C) for V in values for C in core.COSTS]
  cands = [q for q in cands if q.cell != p.cell]
  best = set(core.oracle_bids(p))
  overlap = {q: len(best & set(core.oracle_bids(q))) for q in cands}
  return min(cands, key=lambda q: (overlap[q], *_donor_key(p, q)))


def has_disjoint_donor(p: core.Prompt, values: Sequence[int] = core.VALUES) -> bool:
  q = n7_donor(p, values)
  return not set(core.oracle_bids(p)) & set(core.oracle_bids(q))


def oracle_offer(p: core.Prompt) -> int:
  return min(core.oracle_bids(p))


def build_conditions(p: core.Prompt, S: Mapping[str, Mapping[str, str]],
                     S_reason: Mapping[str, Mapping[str, str]],
                     offers: Mapping[str, Mapping[str, int]],
                     paraphrases: Mapping[str, Mapping[str, str | None]],
                     openings: Sequence[str], tokenizer,
                     values: Sequence[int] = core.VALUES) -> dict[str, str | None]:
  """All 28 conditions for prompt p. Dicts are keyed [agent][pid]. Returns
  code -> inserted text (None = no Notes block). Texts are capped (core.cap_tokens).
  values: the V grid in use (core.VALUES, or VALUES + EXT_VALUES with the
  extension); it fixes the N7 donor set."""
  pid, vp = p.pid, n7_donor(p, values).pid
  out: dict[str, str | None] = {"N0": None}
  out["N1"] = S[BASELINE][pid]
  out["N1s"] = remove_recommendations_strict(S[BASELINE][pid])
  out["N10"] = core.answer_only(p.buyer, oracle_offer(p))
  for a in AGENTS:
    tag = a.rsplit(".", 1)[-1]
    if a in ENTRY_CODE:
      c = ENTRY_CODE[a]
      out[c] = S[a][pid]
      out[c + "r"] = S_reason[a][pid]
      out[f"N7:{tag}"] = S[a][vp]
      out[f"N8:{tag}"] = remove_recommendations_strict(S[a][pid])
    if paraphrases[a].get(pid) is not None:              # failed paraphrase: key absent,
      out[f"N5:{tag}"] = paraphrases[a][pid]             # dropped from wording contrasts
    out[f"N6:{tag}"] = qa_filler(openings, n_tokens(S[a][pid], tokenizer), tokenizer)
    out[f"N9:{tag}"] = core.answer_only(p.buyer, offers[a][pid])
  capped = {}
  for k, v in out.items():
    capped[k] = None if v is None else core.cap_tokens(v, tokenizer)[0]
  return capped


CONDITION_COUNT = 1 + 1 + 1 + 1 + 3 * 4 + 4 * 3   # = 28


# ------------------------------------------------------------ leakage audit
AUDIT_LETTERS = ("a", "b", "c", "d", "e", "f")


def audit_prompt(notes: str) -> tuple[str, dict[str, int | None]]:
  """Leakage audit for N8 / N1s texts (Protocol 9.2): does the stripped text still
  favour a price? Scored with LocalGemma2.letter_scores(prompt, AUDIT_LETTERS);
  the argmax letter maps to a price, or None for 'no price favoured'."""
  lines = ["Notes:", notes, "",
           "Question: Based only on these notes, which price do they favour?"]
  mapping: dict[str, int | None] = {}
  for l, k in zip(AUDIT_LETTERS, core.PRICES):
    lines.append(f"  ({l}) {core.OPTION_TEXT[k]}")
    mapping[l] = k
  lines.append("  (f) The notes do not favour any price")
  mapping["f"] = None
  return "\n".join(lines) + "\nAnswer: (", mapping
````

### `refimpl/steering.py`

````python
"""Phase 3b helpers: grid, rescaling, (layer, alpha) tuning (Protocol 10.2, 10.4)."""
from __future__ import annotations

from typing import Callable, Mapping, Sequence

import torch

LAYERS = tuple(range(6, 31, 3))          # 6, 9, ..., 30
ALPHAS = (0.5, 1.0, 2.0, 4.0)


def mean_activation(acts: Mapping[str, torch.Tensor], pids: Sequence[str]) -> torch.Tensor:
  """acts: pid -> P1 activation (already averaged over the five orders)."""
  return torch.stack([acts[p].float() for p in pids]).mean(0)


def rescale(v: torch.Tensor, norm: float) -> torch.Tensor:
  n = float(v.norm())
  return v * (norm / n) if n > 0 else v


def tune(evaluate: Callable[[int, float], tuple[float, float]],
         layers: Sequence[int] = LAYERS, alphas: Sequence[float] = ALPHAS):
  """Pick the best coherent (layer, alpha); 'no steering' is always an option.

  evaluate(layer, alpha) -> (mean soft-regret reduction on the tuning prompts,
  letter-mass ratio). Coherent if ratio >= 0.9. Ties: smaller alpha, then earlier
  layer. Returns (layer, alpha, reduction), or None when no coherent setting
  reduces regret (reduction <= 0): the direction is then applied with alpha = 0,
  i.e. its effect is exactly zero. The same rule applies to every direction.
  """
  best = None
  for alpha in sorted(alphas):
    for layer in sorted(layers):
      red, ratio = evaluate(layer, alpha)
      if ratio < 0.9 or red <= 0:
        continue
      if best is None or red > best[2] + 1e-12:
        best = (layer, alpha, red)
  return best
````

### `refimpl/pipeline.py`

````python
"""Run driver for Phases 2, 3 and 3b and the pilot (Protocol sections 6 and 8-12).

Every record is written to disk, so the analysis can be rerun without the model:

  records/phase2.jsonl        (agent, prompt): offer, regret, S, S_reason, calls
  records/phase2_e1.jsonl     E1 sampled decisions (temperature 0.5, draws 0-4)
  records/paraphrases.json    agent -> pid -> paraphrase or null
  records/phase3.jsonl        (prompt, condition, order): first-token p(k), whole-answer p(k)
  records/native_replay.jsonl Phase 2 final choice prompts re-scored
  records/leakage.jsonl       leakage audit of N8 / N1s texts
  acts/<pid>/<cond>.pt        activations {layer: {P1..P4}}, P1/P2 averaged over orders
  records/steer_*.json        tuned settings and test evaluations
"""
from __future__ import annotations

import json
import os
from typing import Callable, Mapping, Sequence

import numpy as np
import torch

from . import analysis, conditions, core, phase2, phase3, steering
from .local_gemma2 import CHOICE_SYSTEM, LocalGemma2, build_messages, call_context


def _jsonl(path: str, rec: dict):
  os.makedirs(os.path.dirname(path), exist_ok=True)
  with open(path, "a") as f:
    f.write(json.dumps(rec, default=str) + "\n")


def _read_jsonl(path: str) -> list[dict]:
  with open(path) as f:
    return [json.loads(l) for l in f]


# ------------------------------------------------------------------ Phase 2
def run_phase2(lm: LocalGemma2, embedder, prompts: Sequence[core.Prompt],
               formative: Mapping[int, tuple], openings: Sequence[str], out: str,
               agents: Sequence[str] = conditions.AGENTS, temperature: float = 0.0,
               draws: Sequence[int] = (0,), fname: str = "phase2.jsonl"):
  """formative: variant -> (memory, cfg), loaded from the released banks.
  Exclusion rule: one retry with the same seed, then the failure is recorded.
  E1: temperature=0.5, draws=range(5), fname='phase2_e1.jsonl'."""
  for a in agents:
    for draw in draws:
      for p in prompts:
        mem, cfg = formative[p.variant]
        rec = None
        for attempt in (0, 1):
          try:
            r = phase2.run_decision(lm, embedder, a, p, mem, cfg, list(openings),
                                    draw=draw, temperature=temperature)
            rec = {"agent": a, "pid": p.pid, "draw": draw, "k": r["k"],
                   "hard_regret": r["hard_regret"], "S": r["S"], "S_reason": r["S_reason"],
                   "rule_seen": r["rule_memories_in_prompts"], "calls": r["calls"],
                   "attempt": attempt}
            break
          except Exception as e:  # noqa: BLE001 - recorded, then excluded
            rec = {"agent": a, "pid": p.pid, "draw": draw, "error": repr(e),
                   "attempt": attempt}
        _jsonl(f"{out}/records/{fname}", rec)


def load_phase2(out: str, fname: str = "phase2.jsonl"):
  """Returns S, S_reason, offers, regret (agent -> pid -> value) and the excluded
  pids (dropped for every agent and condition)."""
  S, S_reason, offers, regret, failed = {}, {}, {}, {}, set()
  for r in _read_jsonl(f"{out}/records/{fname}"):
    if "error" in r:
      if r["attempt"] == 1:
        failed.add(r["pid"])
      continue
    for d, key in ((S, "S"), (S_reason, "S_reason"), (offers, "k"), (regret, "hard_regret")):
      d.setdefault(r["agent"], {})[r["pid"]] = r[key]
  return S, S_reason, offers, regret, failed


def run_paraphrases(lm: LocalGemma2, S: Mapping[str, Mapping[str, str]], out: str):
  para = {a: {pid: conditions.paraphrase(lm.sample_text, call_context, text, a, pid)
              for pid, text in by.items()} for a, by in S.items()}
  os.makedirs(f"{out}/records", exist_ok=True)
  with open(f"{out}/records/paraphrases.json", "w") as f:
    json.dump(para, f)
  return para


# ------------------------------------------------------------------ Phase 3
def run_phase3(lm: LocalGemma2, prompts: Sequence[core.Prompt], S, S_reason, offers,
               para, openings: Sequence[str], out: str, only: Sequence[str] | None = None,
               values: Sequence[int] = core.VALUES):
  """Scores every condition (or only those in `only`, e.g. the pilot's N0/N1) in
  the five cyclic orders and stores activations. values: the V grid in use
  (core.VALUES + core.EXT_VALUES with the extension); it fixes the N7 donors."""
  orders = core.cyclic_orders()
  for p in prompts:
    conds = conditions.build_conditions(p, S, S_reason, offers, para, openings, lm.tok,
                                        values)
    if only is not None:
      conds = {k: v for k, v in conds.items() if k in only}
    opening = openings[p.opening_index]
    for code, notes in conds.items():
      acc = {}
      for oi, order in enumerate(orders):
        probs, hard, store, probs_full = phase3.score_prompt(lm, p, opening, notes, order,
                                                             capture=True)
        _jsonl(f"{out}/records/phase3.jsonl",
               {"pid": p.pid, "cond": code, "order": oi, "probs": probs, "hard": hard,
                "probs_full": probs_full, "letter_mass": lm.last_letter_mass,
                "capped": notes is not None and core.cap_tokens(notes, lm.tok)[1]})
        for L, pos in store.items():
          for name in ("P1", "P2"):
            acc.setdefault(L, {}).setdefault(name, []).append(pos[name].float())
          if oi == 0:
            acc[L]["P3"], acc[L]["P4"] = pos["P3"], pos["P4"]
      acts = {L: {k: (torch.stack(v).mean(0) if isinstance(v, list) else v).half()
                  for k, v in d.items()} for L, d in acc.items()}
      os.makedirs(f"{out}/acts/{p.pid}", exist_ok=True)
      torch.save(acts, f"{out}/acts/{p.pid}/{code.replace(':', '_')}.pt")


def soft_regret_table(out: str, prompts: Sequence[core.Prompt], key: str = "probs") -> dict:
  """(pid, cond) -> soft regret averaged over orders. key='probs' (primary,
  first token) or 'probs_full' (sensitivity, whole answer)."""
  by = {}
  for r in _read_jsonl(f"{out}/records/phase3.jsonl"):
    by.setdefault((r["pid"], r["cond"]), []).append({int(k): v for k, v in r[key].items()})
  P = {p.pid: p for p in prompts}
  return {k: float(np.mean([core.soft_regret(P[k[0]], pr) for pr in v]))
          for k, v in by.items() if k[0] in P}


def run_native_replay(lm: LocalGemma2, out: str):
  """Re-score each Phase 2 decision's final multiple-choice prompt (Protocol 9.4)."""
  for r in _read_jsonl(f"{out}/records/phase2.jsonl"):
    if "error" in r:
      continue
    final = [c for c in r["calls"] if c["kind"] == "choice"]
    if not final:
      continue
    c = final[-1]
    letters = list(c["scores"])
    scores, _, _ = lm.letter_scores(c["prompt"], letters)
    _jsonl(f"{out}/records/native_replay.jsonl",
           {"agent": r["agent"], "pid": r["pid"], "phase2_choice": c["choice"],
            "replay_choice": max(letters, key=lambda l: (scores[l], -letters.index(l))),
            "first_token": lm.last_first_token})


def run_leakage_audit(lm: LocalGemma2, prompts, S, S_reason, offers, para, openings, out: str,
                      values: Sequence[int] = core.VALUES):
  """Score the audit question for every N8 and N1s text (Protocol 9.2)."""
  for p in prompts:
    conds = conditions.build_conditions(p, S, S_reason, offers, para, openings, lm.tok,
                                        values)
    for code, text in conds.items():
      if not (code.startswith("N8:") or code == "N1s") or not text:
        continue
      prompt, mapping = conditions.audit_prompt(text)
      scores, _, _ = lm.letter_scores(prompt, list(conditions.AUDIT_LETTERS))
      _jsonl(f"{out}/records/leakage.jsonl",
             {"pid": p.pid, "cond": code,
              "favoured": mapping[max(scores, key=scores.get)]})


def leakage_flags(out: str, offers) -> dict[str, dict]:
  """Per entry: rate at which its N8 text 'favours' its own Phase 2 offer, versus
  the same rate for the baseline's N1s and own offer. Flag if the entry's rate
  exceeds the baseline's by more than 10 percentage points (Protocol 9.2)."""
  recs = _read_jsonl(f"{out}/records/leakage.jsonl")
  base = conditions.BASELINE
  def rate(cond, agent):
    rs = [r for r in recs if r["cond"] == cond]
    return float(np.mean([r["favoured"] == offers[agent].get(r["pid"]) for r in rs])) if rs else 0.0
  b = rate("N1s", base)
  out_ = {}
  for a in conditions.ENTRIES:
    tag = a.rsplit(".", 1)[-1]
    e = rate(f"N8:{tag}", a)
    out_[tag] = {"rate": e, "baseline_rate": b, "flag": e - b > 0.10}
  return out_


# ------------------------------------------------------------------ pilot
def pilot_power_rule(out: str, prompts: Sequence[core.Prompt]) -> dict:
  """Baseline-only pilot quantities and the registered power rule (Protocol 6)."""
  soft = soft_regret_table(out, prompts)
  n0 = {p.pid: soft[(p.pid, "N0")] for p in prompts if (p.pid, "N0") in soft}
  n1 = {p.pid: soft[(p.pid, "N1")] for p in prompts if (p.pid, "N1") in soft}
  diffs = analysis.cell_diffs(n1, n0, prompts)
  sd = float(np.std(diffs, ddof=1))
  power = analysis.power_simulation(sd, n_cells=35)
  n1_cells = analysis.cell_means(n1, prompts)
  near = sorted([c for c, v in n1_cells.items() if v < analysis.SESOI_REGRET], key=str)
  return {"sd": sd, "power_35": power, "extend": power < 0.80,
          "near_ceiling_cells": near}


# ---------------------------------------------------------------- Phase 3b
def _p1(out: str, pid: str, cond: str, layer: int) -> torch.Tensor:
  return torch.load(f"{out}/acts/{pid}/{cond.replace(':', '_')}.pt")[layer]["P1"].float()


def _has(out: str, pid: str, cond: str) -> bool:
  return os.path.exists(f"{out}/acts/{pid}/{cond.replace(':', '_')}.pt")


def named_directions(out: str, dev: Sequence[core.Prompt], layer: int) -> dict:
  """Content and the three named nulls at one layer (Protocol 10.2). A prompt
  enters a contrast only if every condition in that contrast exists for it
  (a dropped paraphrase removes the prompt from the wording contrast only)."""
  tags = [a.rsplit(".", 1)[-1] for a in conditions.ENTRIES]
  base_tag = conditions.BASELINE.rsplit(".", 1)[-1]
  ent = ["N2", "N3", "N4"]
  def contrast(a_conds, b_conds):
    ps = [p for p in dev if all(_has(out, p.pid, c) for c in a_conds + b_conds)]
    ma = torch.stack([_p1(out, p.pid, c, layer) for p in ps for c in a_conds]).mean(0)
    mb = torch.stack([_p1(out, p.pid, c, layer) for p in ps for c in b_conds]).mean(0)
    return ma - mb
  content = contrast(ent, ["N1"])
  norm = float(content.norm())
  nulls = {"wording": contrast([f"N5:{t}" for t in tags], ent),
           "length": contrast([f"N6:{t}" for t in tags], [f"N6:{base_tag}"]),
           "answer": contrast([f"N9:{t}" for t in tags], [f"N9:{base_tag}"])}
  return {"content": content, **{k: steering.rescale(v, norm) for k, v in nulls.items()}}


def project_out_letters(lm: LocalGemma2, v: torch.Tensor) -> torch.Tensor:
  """E6: remove v's component in the span of the a-e unembedding rows, then
  rescale to the original norm."""
  ids = [lm.tok.convert_tokens_to_ids(l) for l in "abcde"]
  W = lm.model.lm_head.weight[ids].float().cpu()        # 5 x d (on CPU, like v)
  Q, _ = torch.linalg.qr(W.T)                           # d x 5, orthonormal
  x = v.float().cpu()
  r = x - Q @ (Q.T @ x)
  return steering.rescale(r, float(x.norm()))


def steered_regret(lm: LocalGemma2, p: core.Prompt, notes: str, opening: str,
                   layer: int | None, vec: torch.Tensor | None, orders):
  """(soft regret, mean letter mass at P1, mean p(k)) over the given orders;
  layer=None scores unsteered."""
  regs, mass, dists = [], [], []
  for order in orders:
    steer = None if layer is None else (layer, vec)
    probs, _, _, _ = phase3.score_prompt(lm, p, opening, notes, order, steer=steer)
    regs.append(core.soft_regret(p, probs)); dists.append(probs)
    mass.append(lm.last_letter_mass)
  mean_p = {k: float(np.mean([d[k] for d in dists])) for k in core.PRICES}
  return float(np.mean(regs)), float(np.mean(mass)), mean_p


def all_orders(p: core.Prompt):
  return core.cyclic_orders()


def single_order(p: core.Prompt):
  """One order per prompt, rotating with the variant (random-direction budget)."""
  return [core.cyclic_orders()[(p.variant - 1) % 5]]


def tuning_subset(dev: Sequence[core.Prompt]) -> list[core.Prompt]:
  """Variant 1 of each development cell (17 prompts)."""
  return [p for p in dev if p.variant == 1]


def make_evaluate(lm, prompts, notes_n1, openings, direction_at: Callable[[int], torch.Tensor],
                  orders_for):
  """evaluate(layer, alpha) -> (mean soft-regret reduction, letter-mass ratio)."""
  base = {}
  def unsteered(p):
    if p.pid not in base:
      base[p.pid] = steered_regret(lm, p, notes_n1[p.pid], openings[p.opening_index],
                                   None, None, orders_for(p))
    return base[p.pid]
  def evaluate(layer, alpha):
    vec = alpha * direction_at(layer)
    red, ratio = [], []
    for p in prompts:
      r0, m0, _ = unsteered(p)
      r, m, _ = steered_regret(lm, p, notes_n1[p.pid], openings[p.opening_index],
                               layer, vec, orders_for(p))
      red.append(r0 - r); ratio.append(m / m0 if m0 > 0 else 0.0)
    return float(np.mean(red)), float(np.mean(ratio))
  return evaluate


def random_directions_at(out: str, dev: Sequence[core.Prompt],
                         content_norm_at: Callable[[int], float], n: int = 1000,
                         seed: int = 11) -> list[Callable[[int], torch.Tensor]]:
  """n natural random directions: N1-activation differences between two dev
  prompts from different cells (pairs drawn once with PCG64(seed), reused at every
  layer), rescaled to the content norm at that layer."""
  rng = np.random.Generator(np.random.PCG64(seed))
  pairs = []
  while len(pairs) < n:
    i, j = rng.integers(0, len(dev), 2)
    if dev[i].cell != dev[j].cell:
      pairs.append((dev[i].pid, dev[j].pid))
  def make(a, b):
    return lambda L: steering.rescale(_p1(out, a, "N1", L) - _p1(out, b, "N1", L),
                                      content_norm_at(L))
  return [make(a, b) for a, b in pairs]


def run_phase3b(lm, out: str, dev, test, notes_n1, openings, n_random: int = 1000):
  """Tune and evaluate every direction (Protocol 10.4-10.5); returns k_tests input."""
  dirs = {L: named_directions(out, dev, L) for L in steering.LAYERS}
  at = {name: (lambda L, n=name: dirs[L][n]) for name in ("content", "wording", "length", "answer")}
  # Named directions: all dev prompts, all orders.
  tuned = {n: steering.tune(make_evaluate(lm, dev, notes_n1, openings, fn, all_orders))
           for n, fn in at.items()}
  # Matched budget for the random comparison: content and each random direction
  # tuned on 17 prompts x 1 order, evaluated on the single rotating order.
  sub = tuning_subset(dev)
  content_matched = steering.tune(make_evaluate(lm, sub, notes_n1, openings,
                                                at["content"], single_order))
  rands = random_directions_at(out, dev, lambda L: float(dirs[L]["content"].norm()), n_random)
  rand_tuned = [steering.tune(make_evaluate(lm, sub, notes_n1, openings, fn, single_order))
                for fn in rands]
  def evaluate_on_test(setting, direction_at, orders_for):
    res = {}
    for p in test:
      r0, _, p0 = steered_regret(lm, p, notes_n1[p.pid], openings[p.opening_index],
                                 None, None, orders_for(p))
      if setting is None:
        res[p.pid] = (r0, r0, p0, p0)
        continue
      L, alpha, _ = setting
      r1, _, p1 = steered_regret(lm, p, notes_n1[p.pid], openings[p.opening_index],
                                 L, alpha * direction_at(L), orders_for(p))
      res[p.pid] = (r0, r1, p0, p1)
    return res
  named = {n: evaluate_on_test(tuned[n], at[n], all_orders) for n in at}
  matched = evaluate_on_test(content_matched, at["content"], single_order)
  random_single = [evaluate_on_test(s, fn, single_order) for s, fn in zip(rand_tuned, rands)]
  # Sharpening null: gamma tuned on the dev prompts' unsteered N1 distributions.
  dev_base = {p.pid: steered_regret(lm, p, notes_n1[p.pid], openings[p.opening_index],
                                    None, None, all_orders(p))[2] for p in dev}
  gamma = analysis.tune_sharpen(dev, dev_base)
  with open(f"{out}/records/steer_settings.json", "w") as f:
    json.dump({"named": tuned, "content_matched": content_matched,
               "random": rand_tuned, "gamma": gamma}, f, default=str)
  return {"named": named, "content_matched": matched, "random_single": random_single,
          "gamma": gamma}
````

### `refimpl/analysis.py`

````python
"""Confirmatory statistics (Protocol sections 10.5 and 11).

Primary test: one-sided sign-flip permutation test of the mean cell difference.
Multi-part hypotheses: intersection-union (largest component p). Family: Holm,
alpha 0.05 (confirmatory direction) and 0.01 (reverse family). Secondary: BH.
"""
from __future__ import annotations

import collections
import itertools
from typing import Callable, Mapping, Sequence

import numpy as np
from scipy import stats

from . import core

ALPHA, ALPHA_REVERSE = 0.05, 0.01
SESOI_REGRET, SESOI_K2 = 0.05, 0.2
SEED = 20261121


# ------------------------------------------------------------------ basics
def cell_means(values: Mapping[str, float], prompts: Sequence[core.Prompt]
               ) -> dict[tuple, float]:
  """Average a per-prompt quantity within each cell (over its variants)."""
  acc = collections.defaultdict(list)
  for p in prompts:
    if p.pid in values:
      acc[p.cell].append(values[p.pid])
  return {c: float(np.mean(v)) for c, v in acc.items()}


def cell_diffs(a: Mapping[str, float], b: Mapping[str, float],
               prompts: Sequence[core.Prompt]) -> list[float]:
  """Cell means of a - b over prompts present in both, cells in sorted order."""
  d = {p.pid: a[p.pid] - b[p.pid] for p in prompts if p.pid in a and p.pid in b}
  m = cell_means(d, prompts)
  return [m[c] for c in sorted(m, key=str)]


def signflip_greater(x: Sequence[float], n_mc: int = 100_000, seed: int = SEED) -> float:
  """One-sided sign-flip permutation p-value for mean(x) > 0.

  Exact enumeration of all 2^n sign patterns for n <= 20; otherwise Monte Carlo
  with n_mc patterns, p = (1 + #{mean* >= mean}) / (1 + n_mc)."""
  x = np.asarray(x, dtype=float)
  n, obs = len(x), float(np.mean(x))
  if n == 0 or np.allclose(x, 0):
    return 1.0
  if n <= 20:
    signs = np.array(list(itertools.product((1.0, -1.0), repeat=n)))
    null = (signs * x).mean(axis=1)
    return float(np.mean(null >= obs - 1e-12))
  rng = np.random.default_rng(seed)
  signs = rng.choice((1.0, -1.0), size=(n_mc, n))
  null = (signs * x).mean(axis=1)
  return float((1 + np.sum(null >= obs - 1e-12)) / (1 + n_mc))


def signflip_less(x: Sequence[float], **kw) -> float:
  return signflip_greater([-v for v in x], **kw)


def wilcoxon_greater(x: Sequence[float]) -> float:
  """Sensitivity analysis: one-sided Wilcoxon signed-rank, zeros by Pratt."""
  x = np.asarray(x, dtype=float)
  if np.allclose(x, 0):
    return 1.0
  return float(stats.wilcoxon(x, zero_method="pratt", alternative="greater",
                              correction=True).pvalue)


def iut(*pvalues: float) -> float:
  """Intersection-union test: every component null must be rejected."""
  return max(pvalues)


def reverse_p(*component_reverse_pvalues: float) -> float:
  """Reverse direction of a multi-part test: Bonferroni over its components (any
  one component significantly in the wrong direction)."""
  m = len(component_reverse_pvalues)
  return min(1.0, m * min(component_reverse_pvalues))


def holm(pvalues: Mapping[str, float], alpha: float = ALPHA) -> dict[str, bool]:
  order = sorted(pvalues, key=pvalues.get)
  m, out, stop = len(order), {}, False
  for i, k in enumerate(order):
    if not stop and pvalues[k] <= alpha / (m - i):
      out[k] = True
    else:
      stop, out[k] = True, False
  return out


def benjamini_hochberg(pvalues: Mapping[str, float], q: float = 0.05) -> dict[str, bool]:
  keys = sorted(pvalues, key=pvalues.get)
  m, k_max = len(keys), 0
  for i, k in enumerate(keys, start=1):
    if pvalues[k] <= q * i / m:
      k_max = i
  return {k: (i < k_max) for i, k in enumerate(keys)}


def bootstrap_ci(x: Sequence[float], level: float = 0.95, n: int = 10_000,
                 seed: int = SEED) -> tuple[float, float]:
  rng = np.random.default_rng(seed)
  x = np.asarray(x, dtype=float)
  means = rng.choice(x, size=(n, len(x)), replace=True).mean(axis=1)
  lo, hi = np.quantile(means, [(1 - level) / 2, 1 - (1 - level) / 2])
  return float(lo), float(hi)


def verdict(passed: bool, passed_reverse: bool, interval: tuple[float, float] | None,
            sesoi: float) -> str:
  """'supported' | 'reversed' | 'equivalent' | 'inconclusive'.
  interval: 90% bootstrap interval of the effect (None = equivalence not assessed)."""
  if passed:
    return "supported"
  if passed_reverse:
    return "reversed"
  if interval is not None and -sesoi < interval[0] and interval[1] < sesoi:
    return "equivalent"
  return "inconclusive"


def permutation_p(content_stat: float, null_stats: Sequence[float]) -> float:
  null = np.asarray(null_stats, dtype=float)
  return float((1 + np.sum(null >= content_stat)) / (1 + len(null)))


def permutation_p_less(content_stat: float, null_stats: Sequence[float]) -> float:
  null = np.asarray(null_stats, dtype=float)
  return float((1 + np.sum(null <= content_stat)) / (1 + len(null)))


# ------------------------------------------------------------- A, B and R
def abr_tests(prompts: Sequence[core.Prompt], soft: Mapping[tuple, float],
              phase2_regret: Mapping[str, Mapping[str, float]], baseline: str,
              entries: Mapping[str, str]) -> dict:
  """A_e, B_e and R_e for every entry.

  soft: (pid, condition) -> Phase 3 soft regret (orders averaged).
  phase2_regret: agent -> pid -> Phase 2 hard regret.
  entries: agent -> (code, tag), e.g. {'agent_py_files.taehun_cgcal': ('N2', 'taehun_cgcal')}.
  Every difference is oriented so that positive favours the entry.
  """
  def col(cond):
    return {p.pid: soft[(p.pid, cond)] for p in prompts if (p.pid, cond) in soft}
  base_tag = baseline.rsplit(".", 1)[-1]
  out = {}
  for agent, (code, tag) in entries.items():
    A = cell_diffs(phase2_regret[baseline], phase2_regret[agent], prompts)
    ne = col(code)
    B = {"N0": cell_diffs(col("N0"), ne, prompts),
         "N1": cell_diffs(col("N1"), ne, prompts),
         "N6": cell_diffs(col(f"N6:{tag}"), ne, prompts),
         "N7": cell_diffs(col(f"N7:{tag}"), ne, prompts)}
    n8 = col(f"N8:{tag}")
    R = {"N0": cell_diffs(col("N0"), n8, prompts),
         "N1s": cell_diffs(col("N1s"), n8, prompts)}
    def pack(parts):
      if isinstance(parts, dict):
        p = {k: signflip_greater(v) for k, v in parts.items()}
        r = {k: signflip_less(v) for k, v in parts.items()}
        worst = max(p, key=p.get)
        return {"p": iut(*p.values()), "p_reverse": reverse_p(*r.values()),
                "components": p, "effect_cells": parts[worst]}
      return {"p": signflip_greater(parts), "p_reverse": signflip_less(parts),
              "effect_cells": parts}
    out[f"A:{tag}"] = pack(A)
    out[f"B:{tag}"] = pack(B)
    out[f"R:{tag}"] = pack(R)
    out[f"descr:N9-Ne:{tag}"] = float(np.mean(cell_diffs(col(f"N9:{tag}"), ne, prompts)))
    out[f"descr:N10-Ne:{tag}"] = float(np.mean(cell_diffs(col("N10"), ne, prompts)))
  return out


def confirmatory_verdicts(tests: Mapping[str, dict]) -> dict[str, str]:
  """tests: name -> {'p', 'p_reverse', 'effect_cells' or 'interval', 'sesoi'?}.
  Holm at 0.05 for the confirmatory direction, separate Holm at 0.01 for the reverse."""
  passed = holm({k: v["p"] for k, v in tests.items()}, ALPHA)
  passed_r = holm({k: v["p_reverse"] for k, v in tests.items()}, ALPHA_REVERSE)
  out = {}
  for k, v in tests.items():
    if "interval" in v:
      interval = v["interval"]
    elif v.get("effect_cells") is not None:
      interval = bootstrap_ci(v["effect_cells"], level=0.90)
    else:
      interval = None
    out[k] = verdict(passed[k], passed_r[k], interval, v.get("sesoi", SESOI_REGRET))
  return out


# ------------------------------------------------------------------ power
def power_simulation(sd: float, n_cells: int, effect: float = SESOI_REGRET,
                     alpha: float = ALPHA / 11, n_sim: int = 2000, n_flip: int = 2000,
                     seed: int = SEED) -> float:
  """Power of the one-sided sign-flip test at the strictest Holm level, cell
  differences ~ Normal(effect, sd). Monte Carlo over n_sim data sets, each tested
  with n_flip sign patterns (p resolution 1/2001 < 0.05/11)."""
  rng = np.random.default_rng(seed)
  hits = 0
  for _ in range(n_sim):
    x = rng.normal(effect, sd, n_cells)
    signs = rng.choice((1.0, -1.0), size=(n_flip, n_cells))
    p = (1 + np.sum((signs * x).mean(axis=1) >= x.mean())) / (1 + n_flip)
    hits += p <= alpha
  return hits / n_sim


# ---------------------------------------------------------------- K1
def sharpen(probs: Mapping[int, float], gamma: float) -> dict[int, float]:
  """Sharpening null: p(k)^gamma, renormalised (more confident, same mode)."""
  w = {k: probs[k] ** gamma for k in core.PRICES}
  z = sum(w.values())
  return {k: w[k] / z for k in core.PRICES}


GAMMAS = (1.25, 1.5, 2.0, 3.0, 4.0, 6.0, 8.0)


def tune_sharpen(prompts: Sequence[core.Prompt], base: Mapping[str, Mapping[int, float]],
                 gammas: Sequence[float] = GAMMAS) -> float:
  """gamma with the largest mean soft-regret reduction on development prompts;
  1.0 (no change) if none reduces regret."""
  def red(g):
    return float(np.mean([core.soft_regret(p, base[p.pid]) -
                          core.soft_regret(p, sharpen(base[p.pid], g)) for p in prompts]))
  best = max(gammas, key=red)
  return best if red(best) > 0 else 1.0


def k1_test(delta_cells: Sequence[float], null_delta_cells: Mapping[str, Sequence[float]],
            content_mean_matched: float, random_means: Sequence[float]) -> dict:
  """K1 as one intersection-union p-value.

  delta_cells: per test cell, N1 soft regret minus content-steered soft regret.
  null_delta_cells: per named null (wording, length, answer, sharpen), the same quantity.
  content_mean_matched: mean Delta of the content direction tuned and evaluated
  exactly like each random direction (17 prompts x 1 order; single rotating order).
  random_means: mean Delta for each of the random directions."""
  d = np.asarray(delta_cells, dtype=float)
  comps = {"delta": signflip_greater(d)}
  rev = {"delta": signflip_less(d)}
  for name, nd in null_delta_cells.items():
    diff = d - np.asarray(nd, dtype=float)
    comps[f"vs_{name}"] = signflip_greater(diff)
    rev[f"vs_{name}"] = signflip_less(diff)
  comps["vs_random"] = permutation_p(content_mean_matched, random_means)
  rev["vs_random"] = permutation_p_less(content_mean_matched, random_means)
  worst = max(comps, key=comps.get)
  effect = d if worst in ("delta", "vs_random") else d - np.asarray(
      null_delta_cells[worst[3:]], dtype=float)
  return {"components": comps, "p": iut(*comps.values()),
          "p_reverse": reverse_p(*rev.values()), "effect_cells": list(effect),
          "min_attainable_random_p": 1.0 / (1 + len(random_means))}


# ---------------------------------------------------------------- K2
def tilt(probs: Mapping[int, float], beta: float) -> dict[int, float]:
  w = {k: probs[k] * np.exp(beta * k) for k in core.PRICES}
  z = sum(w.values())
  return {k: w[k] / z for k in core.PRICES}


def attractor(probs: Mapping[int, float], k_star: int, lam: float) -> dict[int, float]:
  return {k: (1 - lam) * probs[k] + (lam if k == k_star else 0.0) for k in core.PRICES}


def flatten(probs: Mapping[int, float], lam: float) -> dict[int, float]:
  return {k: (1 - lam) * probs[k] + lam / 5.0 for k in core.PRICES}


def _brentq_or_bound(f: Callable[[float], float], a: float, b: float) -> float:
  from scipy.optimize import brentq
  if f(a) * f(b) > 0:
    return a if abs(f(a)) < abs(f(b)) else b
  return float(brentq(f, a, b))


def matched_beta(base: Mapping[str, Mapping[int, float]], target_shift: float) -> float:
  def mean_shift(b):
    return float(np.mean([core.expected_bid(tilt(base[pid], b)) -
                          core.expected_bid(base[pid]) for pid in base]))
  return _brentq_or_bound(lambda b: mean_shift(b) - target_shift, -20, 20)


def _match_lambda(base, fn, target_abs_shift: float) -> float:
  def mean_abs(lam):
    return float(np.mean([abs(core.expected_bid(fn(base[pid], lam)) -
                              core.expected_bid(base[pid])) for pid in base]))
  if mean_abs(1.0) <= target_abs_shift:
    return 1.0
  return _brentq_or_bound(lambda l: mean_abs(l) - target_abs_shift, 0.0, 1.0)


def partial_spearman(x, y, z) -> tuple[float, float, float]:
  """Spearman correlation of x and y controlling for z (ranks, residualise on z's
  rank, Pearson). Returns (rho, p for rho > 0, p for rho < 0), t with n - 3 df."""
  rx, ry, rz = (stats.rankdata(np.asarray(v, dtype=float)) for v in (x, y, z))
  Z = np.column_stack([np.ones_like(rz), rz])
  ex = rx - Z @ np.linalg.lstsq(Z, rx, rcond=None)[0]
  ey = ry - Z @ np.linalg.lstsq(Z, ry, rcond=None)[0]
  if ex.std() == 0 or ey.std() == 0:
    return 0.0, 1.0, 1.0
  r = float(np.corrcoef(ex, ey)[0, 1])
  n = len(x)
  t = r * np.sqrt((n - 3) / max(1e-12, 1 - r * r))
  return r, float(stats.t.sf(t, n - 3)), float(stats.t.cdf(t, n - 3))


def calibration_test(prompts: Sequence[core.Prompt],
                     base: Mapping[str, Mapping[int, float]],
                     steered: Mapping[str, Mapping[int, float]],
                     extra_nulls: Mapping[str, Mapping[str, Mapping[int, float]]] = {},
                     n_boot: int = 10_000, seed: int = 11) -> dict:
  """K2 on the test cells whose best offer is a single price (core.has_unique_best).

  Statistic: partial Spearman correlation, across cells, of the steering shift s
  with the best offer o, controlling for the unsteered expected offer b. Passes
  if it is > 0 and exceeds, by a paired bootstrap over cells, the partial
  correlation of every control: tilt (matched mean signed shift), attractor
  towards each fixed price (the strongest of the five is used; matched mean
  absolute shift), flatten (matched mean absolute shift), and extra_nulls."""
  pids = [p for p in prompts if p.pid in base and p.pid in steered and core.has_unique_best(p)]
  B = {p.pid: base[p.pid] for p in pids}
  def shifts(dists):
    return {p.pid: core.expected_bid(dists[p.pid]) - core.expected_bid(B[p.pid]) for p in pids}
  s = shifts(steered)
  mean_shift = float(np.mean(list(s.values())))
  mean_abs = float(np.mean(np.abs(list(s.values()))))
  controls = {"tilt": {pid: tilt(B[pid], matched_beta(B, mean_shift)) for pid in B}}
  lam_f = _match_lambda(B, flatten, mean_abs)
  controls["flatten"] = {pid: flatten(B[pid], lam_f) for pid in B}
  for k_star in core.PRICES:
    fn = lambda pr, l, k=k_star: attractor(pr, k, l)
    lam = _match_lambda(B, fn, mean_abs)
    controls[f"attractor{k_star}"] = {pid: fn(B[pid], lam) for pid in B}
  controls.update(extra_nulls)
  cells = sorted({p.cell for p in pids}, key=str)
  def by_cell(d):
    m = cell_means(d, pids)
    return np.array([m[c] for c in cells])
  z = by_cell({pid: core.expected_bid(B[pid]) for pid in B})
  o = by_cell({p.pid: float(core.oracle_bids(p)[0]) for p in pids})
  a = by_cell(s)
  ctrl = {k: by_cell(shifts(v)) for k, v in controls.items()}
  rho, p_rho, p_rho_neg = partial_spearman(a, o, z)
  ctrl_rho = {k: partial_spearman(v, o, z)[0] for k, v in ctrl.items()}
  best_att = max((k for k in ctrl if k.startswith("attractor")), key=ctrl_rho.get)
  used = [k for k in ctrl if not k.startswith("attractor")] + [best_att]
  rng = np.random.default_rng(seed)
  diffs = {k: [] for k in used}
  for _ in range(n_boot):
    idx = rng.integers(0, len(cells), len(cells))
    r_a = partial_spearman(a[idx], o[idx], z[idx])[0]
    for k in used:
      diffs[k].append(r_a - partial_spearman(ctrl[k][idx], o[idx], z[idx])[0])
  # Bootstrap p-values as (1 + count) / (1 + n), so none is exactly zero.
  p_vs = {k: float((1 + np.sum(np.asarray(v) <= 0)) / (1 + n_boot)) for k, v in diffs.items()}
  p_vs_rev = {k: float((1 + np.sum(np.asarray(v) >= 0)) / (1 + n_boot)) for k, v in diffs.items()}
  strongest = max(used, key=ctrl_rho.get)               # equivalence vs strongest control
  lo, hi = np.quantile(diffs[strongest], [0.05, 0.95])
  return {"n_cells": len(cells), "rho_partial": rho, "p_rho": p_rho,
          "control_rho": {k: ctrl_rho[k] for k in used}, "p_vs_controls": p_vs,
          "p": iut(p_rho, *p_vs.values()),
          "p_reverse": reverse_p(p_rho_neg, *p_vs_rev.values()),
          "interval": (float(lo), float(hi)), "sesoi": SESOI_K2}


# ------------------------------------------------------- K1/K2 assembly
def k_tests(test: Sequence[core.Prompt], named: Mapping[str, Mapping[str, tuple]],
            content_matched: Mapping[str, tuple], random_single: Sequence[Mapping[str, tuple]],
            gamma: float, n_boot: int = 10_000) -> dict:
  """Assemble K1 and K2 from evaluation records.

  Each record maps pid -> (unsteered regret, steered regret, unsteered p, steered p).
  named: 'content', 'wording', 'length', 'answer' (tuned on all dev data, all orders).
  content_matched / random_single: content and each random direction tuned on the
  17-prompt, 1-order budget and evaluated on the single rotating order.
  gamma: sharpening exponent tuned on development (tune_sharpen)."""
  def delta_cells(res):
    return cell_diffs({k: v[0] for k, v in res.items()},
                      {k: v[1] for k, v in res.items()}, test)
  P = {p.pid: p for p in test}
  sharp = {pid: (v[0], core.soft_regret(P[pid], sharpen(v[2], gamma)), v[2],
                 sharpen(v[2], gamma)) for pid, v in named["content"].items()}
  nulls = {k: delta_cells(named[k]) for k in ("wording", "length", "answer")}
  nulls["sharpen"] = delta_cells(sharp)
  k1 = k1_test(delta_cells(named["content"]), nulls,
               float(np.mean(delta_cells(content_matched))),
               [float(np.mean(delta_cells(r))) for r in random_single])
  base = {pid: v[2] for pid, v in named["content"].items()}
  k2 = calibration_test(test, base, {pid: v[3] for pid, v in named["content"].items()},
                        {"answer_null": {pid: v[3] for pid, v in named["answer"].items()},
                         "sharpen": {pid: v[3] for pid, v in sharp.items()}},
                        n_boot=n_boot)
  return {"K1": k1, "K2": k2}


def fidelity(test: Sequence[core.Prompt], soft: Mapping[tuple, float],
             steered: Mapping[str, tuple], entry_codes=("N2", "N3", "N4")) -> float:
  """Share of the text effect reproduced by steering, on test cells: mean cell
  (N1 - steered N1) divided by mean cell (N1 - mean of the entries' own text)."""
  n1 = {p.pid: soft[(p.pid, "N1")] for p in test}
  ne = {p.pid: float(np.mean([soft[(p.pid, c)] for c in entry_codes])) for p in test}
  st = {pid: v[1] for pid, v in steered.items()}
  gap = float(np.mean(cell_diffs(n1, ne, test)))
  got = float(np.mean(cell_diffs(n1, st, test)))
  return got / gap if gap != 0 else float("nan")
````

### `tests/scoring_orders.py`

````python
"""First-token versus whole-answer scoring across the five option orders (one prompt)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from refimpl import core, phase3
from refimpl.local_gemma2 import LocalGemma2

import argparse
from refimpl import runtime
ap = argparse.ArgumentParser()
ap.add_argument("model")
ap.add_argument("--device", default="cpu", choices=("cpu", "cuda"))
args = ap.parse_args()
model, tok = runtime.load_gemma(args.model, args.device)
lm = LocalGemma2(model, tok, sequential=True)
p = core.Prompt(1, 5, "information", 3)
notes = "Question: What is Anya's best offer?\nAnswer: She can resell for 5 coins."
# Reports only the mean letter mass and first-token versus whole-answer top-choice
# agreement (no probabilities, offers or regret are printed).
masses, agree = [], 0
for i, order in enumerate(core.cyclic_orders()):
  pf, _, _, pw = phase3.score_prompt(lm, p, "Opening sentence number 0.", notes, order)
  masses.append(lm.last_letter_mass)
  agree += max(pf, key=pf.get) == max(pw, key=pw.get)
print(f"mean letter mass {sum(masses) / len(masses):.3f} "
      f"(range {min(masses):.3f}-{max(masses):.3f}); first-token vs whole-answer "
      f"top choice agree in {agree} of 5 orders")
````

### `tests/smoke_gemma.py`

````python
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

# P0.2 (revised): batched letter scoring versus sequential (one letter per pass).
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
````

### `tests/smoke_phase2.py`

````python
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
````

### `tests/test_banks.py`

````python
"""Formative-memory bank save/load (phase2.save_bank / phase2.load_bank).

Needs Concordia v1.8.9 on PYTHONPATH (skipped otherwise); no model is loaded."""
import datetime
import hashlib
import os
import subprocess
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
pytest.importorskip("concordia")
pytest.importorskip("examples.modular.environment.haggling")

from concordia.associative_memory import blank_memories, importance_function  # noqa: E402
from refimpl import phase2  # noqa: E402


def fake_embed(text):
  h = hashlib.sha256(text.encode()).digest()
  return (np.frombuffer(h * 24, dtype=np.uint8)[:768].astype(np.float32) - 127.5) / 50


def make_bank():
  mem = blank_memories.MemoryFactory(
      model=None, embedder=fake_embed,
      importance=importance_function.ConstantImportanceModel().importance,
      clock_now=lambda: phase2.START).make_blank_memory()
  t0 = datetime.datetime(1880, 3, 1, 9, 30)
  mem.add("Anya was born in a small village.", timestamp=t0, tags=["episode"])
  mem.add("She learnt to\nbargain.", timestamp=t0 + datetime.timedelta(days=400),
          tags=("episode", "childhood"))
  mem.add("Same text, other time.", timestamp=t0)
  mem.add("Same text, other time.", timestamp=t0 + datetime.timedelta(minutes=5))
  mem.add("Anya always drives a hard bargain.", tags=["initial_player_specific_memory"])
  mem.add("Importance differs.", timestamp=t0, importance=0.25)
  return mem


def test_bank_save_and_reload(tmp_path):
  mem = make_bank()
  path = str(tmp_path / "bank.parquet")
  sha = phase2.save_bank(mem, path)
  assert len(sha) == 64 and phase2.save_bank(mem, path) == sha      # deterministic file
  import pyarrow.parquet as pq
  assert tuple(pq.read_table(path).column_names) == phase2.BANK_COLUMNS
  loaded, cfg = phase2.load_bank(path, None, fake_embed, 1)
  a, b = mem.get_data_frame(), loaded.get_data_frame()
  assert list(a.columns) == list(b.columns) and list(a.dtypes) == list(b.dtypes)
  assert len(a) == len(b) == 6
  for col in ("text", "time", "tags", "importance"):
    assert list(a[col]) == list(b[col]), col
  assert all(isinstance(t, tuple) for t in b["tags"])
  for x, y in zip(a["embedding"], b["embedding"]):
    assert x.dtype == y.dtype == np.float32 and np.array_equal(x, y)
  assert loaded._stored_hashes == mem._stored_hashes
  assert cfg.name == "Anya Blossomwood"
  assert cfg.extras == phase2.player_config(1).extras


def test_duplicate_row_ignored_after_load(tmp_path):
  mem = make_bank()
  path = str(tmp_path / "bank.parquet")
  phase2.save_bank(mem, path)
  loaded, _ = phase2.load_bank(path, None, fake_embed, 1)
  n = len(loaded.get_data_frame())
  row = loaded.get_data_frame().iloc[1]
  loaded.add(row["text"], timestamp=row["time"].to_pydatetime(), tags=list(row["tags"]),
             importance=row["importance"])
  assert len(loaded.get_data_frame()) == n                          # duplicate ignored
  loaded.add(row["text"], timestamp=row["time"].to_pydatetime(), tags=list(row["tags"]),
             importance=0.5)
  assert len(loaded.get_data_frame()) == n + 1                      # a new row is added


def test_hashes_recomputed_in_a_fresh_process(tmp_path):
  """String hashes differ across processes: the loader must not reuse stored ones."""
  mem = make_bank()
  path = str(tmp_path / "bank.parquet")
  phase2.save_bank(mem, path)
  code = ("import sys, hashlib, numpy as np; sys.path.insert(0, %r); "
          "from tests.test_banks import fake_embed; from refimpl import phase2; "
          "m, _ = phase2.load_bank(%r, None, fake_embed, 1); r = m.get_data_frame().iloc[0]; "
          "n = len(m.get_data_frame()); "
          "m.add(r['text'], timestamp=r['time'].to_pydatetime(), tags=list(r['tags']), "
          "importance=r['importance']); print(len(m.get_data_frame()) == n)"
          % (os.path.dirname(os.path.dirname(os.path.abspath(__file__))), path))
  env = dict(os.environ, PYTHONHASHSEED="12345")
  out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env)
  assert out.stdout.strip() == "True", out.stderr[-2000:]
````

### `tests/test_core.py`

````python
import math
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from refimpl import core, analysis


def test_prompt_set_counts():
  ps = core.prompt_set()
  assert len(ps) == 420
  assert len({p.pid for p in ps}) == 420
  assert len(core.all_cells()) == 35


def test_oracle_table():
  # Hand-computed values (section 1.2).
  exp = {2: ([1], 0.2), 3: ([1, 2], 0.4), 4: ([2], 0.8), 5: ([2, 3], 1.2), 6: ([3], 1.8)}
  for V, (bids, pay) in exp.items():
    p = core.Prompt(1, V, "neutral", None)
    assert core.oracle_bids(p) == bids
    assert math.isclose(core.oracle_payoff(p), pay)
  p = core.Prompt(1, 5, "information", 3)
  assert core.oracle_bids(p) == [3] and core.oracle_payoff(p) == 2.0
  p = core.Prompt(1, 3, "information", 3)          # C == V: k < C or k == C, payoff 0
  assert core.oracle_bids(p) == [1, 2, 3] and core.oracle_payoff(p) == 0.0
  p = core.Prompt(1, 2, "information", 4)          # C > V
  assert core.oracle_bids(p) == [1, 2, 3]
  assert core.hard_regret(p, 5) == 3.0             # overpay by 3 when accepted


def test_regret_nonnegative_everywhere():
  for p in core.prompt_set([1]):
    for k in core.PRICES:
      assert core.hard_regret(p, k) >= -1e-12


def test_split_is_disjoint_and_sized():
  cells = core.all_cells()
  dev = [c for c in cells if core.steering_cell_split(c) == "dev"]
  test = [c for c in cells if core.steering_cell_split(c) == "test"]
  assert len(dev) == 17 and len(test) == 18 and not set(dev) & set(test)
  ext = core.all_cells(core.VALUES + core.EXT_VALUES)      # extension: V = 7, 8
  assert len(ext) == 49
  assert sum(core.steering_cell_split(c) == "test" for c in ext) == 25


def test_seed_varies_with_draw():
  a = core.call_seed("x", "agent", "pid", 0)
  b = core.call_seed("x", "agent", "pid", 1)
  assert a != b and 0 <= a < 2**64


def test_reasoning_entry():
  e = core.reasoning_entry("Ctx\nQuestion: What would Ann do?\nAnswer: Ann would ",
                           " offer two coins. ")
  assert e == "Question: What would Ann do?\nAnswer: Ann would offer two coins."
  e = core.reasoning_entry("Some context\nLast line here", "x")
  assert e.startswith("Question: Last line here")
  # The prompt's own answer stem is kept, so the entry reads as the model saw it.
  e = core.reasoning_entry("Ctx\nQuestion: What would Ann do?\nAnswer: Ann would ", "offer 2.")
  assert e == "Question: What would Ann do?\nAnswer: Ann would offer 2."
  e = core.reasoning_entry("Question: Summarize the observations.\nAnswer: ", "Ann haggles.")
  assert e == "Question: Summarize the observations.\nAnswer: Ann haggles."
  calls = [("Question: Summarize the observations.\nAnswer: ", "x."),
           ("Question: What would Ann do?\nAnswer: Ann would ", "offer 2.")]
  assert core.build_S(calls, reasoning_only=True) == "Question: What would Ann do?\nAnswer: Ann would offer 2."




def test_softmax_and_expected_bid():
  probs = core.softmax_scores({"a": 0.0, "b": 0.0, "c": -100, "d": -100, "e": -100},
                              {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5})
  assert math.isclose(probs[1], 0.5, abs_tol=1e-9)
  assert math.isclose(core.expected_bid(probs), 1.5, abs_tol=1e-9)


def test_cyclic_orders():
  o = core.cyclic_orders()
  assert o[0] == (1, 2, 3, 4, 5) and o[1] == (2, 3, 4, 5, 1) and len(o) == 5


def test_holm_and_iut():
  h = analysis.holm({"a": 0.001, "b": 0.02, "c": 0.04})
  assert h == {"a": True, "b": True, "c": True}
  h = analysis.holm({"a": 0.001, "b": 0.04, "c": 0.04})
  assert h["a"] and not h["b"] and not h["c"]
  assert analysis.iut(0.01, 0.2) == 0.2


def test_signflip_and_wilcoxon_direction():
  assert analysis.signflip_greater([0.1] * 20 + [0.2] * 15) < 1e-4
  assert analysis.signflip_greater([-0.1] * 18) == 1.0
  assert analysis.signflip_less([-0.1] * 18) < 1e-4


def test_wilcoxon_direction():
  assert analysis.wilcoxon_greater([0.1] * 20 + [0.2] * 15) < 1e-4
  assert analysis.wilcoxon_greater([-0.1] * 35) > 0.99




def test_seed_only_inside_call_context():
  import random
  from refimpl.local_gemma2 import LocalGemma2, call_context, context_is_set
  lm = object.__new__(LocalGemma2)                    # _seed needs no model
  assert not context_is_set()
  random.seed(123); expected = random.random()
  random.seed(123)
  assert lm._seed("prompt") is None                    # Phase 1: launcher seed untouched
  assert random.random() == expected
  with call_context(agent="a", pid="p"):
    assert context_is_set()
    s = lm._seed("prompt")
    assert s == core.call_seed("prompt", "a", "p", 0)
    x = random.random()
    lm._seed("prompt")
    assert random.random() == x                        # Phases 2-3: per-call seed
  with call_context():                                 # an empty context still counts as set
    assert context_is_set()
  assert not context_is_set()
````

### `tests/test_design.py`

````python
"""Unit tests for the condition builders and the confirmatory statistics."""
import math
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

from refimpl import analysis, conditions, core, steering


class WordTok:
  """Whitespace stand-in tokenizer for unit tests (real runs use Gemma's)."""
  def encode(self, text, add_special_tokens=False):
    return text.split(" ")
  def decode(self, ids):
    return " ".join(ids)


# ------------------------------------------------------------- conditions
def test_strict_removal():
  t = ("Anya can sell the fruit for 5 coins. The seller paid 3 coins. "
       "Offering 3 coins gives a profit of 2 coins. 2 coins: 0.4, 3 coins: 1.2. "
       "Option (b) looks best. Prices range from 1 coin to 5 coins. She is careful. "
       "She should offer 2. A price of 3 seems fair. She will pay $2 tops. "
       "The average price is 3 coins. Fruit weighs 2 kg each.")
  out = conditions.remove_recommendations_strict(t)
  for kept in ("sell the fruit for 5 coins", "paid 3 coins", "She is careful",
               "average price is 3 coins", "weighs 2 kg"):
    assert kept in out, kept
  for gone in ("profit", "0.4", "(b)", "range from", "offer 2", "price of 3", "$2"):
    assert gone not in out, gone


def test_qa_filler_exact_length_and_format():
  tok = WordTok()
  f = conditions.qa_filler(["A busy square.", "Stalls everywhere."], 37, tok)
  assert len(tok.encode(f)) == 37 and f.startswith("Question: ")


def test_condition_set():
  p = core.Prompt(1, 5, "information", 3)
  vp = conditions.n7_donor(p)
  S = {a: {p.pid: f"Question: q\nAnswer: text of {a}", vp.pid: "other"} for a in conditions.AGENTS}
  off = {a: {p.pid: 3} for a in conditions.AGENTS}
  para = {a: {p.pid: "para"} for a in conditions.AGENTS}
  c = conditions.build_conditions(p, S, S, off, para, ["Open."], WordTok())
  assert len(c) == conditions.CONDITION_COUNT == 28
  assert c["N0"] is None and c["N10"] == "Anya Blossomwood should offer 3 coins."
  para[conditions.ENTRIES[0]][p.pid] = None
  c = conditions.build_conditions(p, S, S, off, para, ["Open."], WordTok())
  assert len(c) == 27                                    # failed paraphrase dropped


def test_n7_donor_disjoint_and_deterministic():
  for values, n_cells, n_disjoint in ((core.VALUES, 35, 34),
                                      (core.VALUES + core.EXT_VALUES, 49, 48)):
    ps = core.prompt_set([1], values)
    assert len({p.cell for p in ps}) == n_cells
    donors = {p.cell: conditions.n7_donor(p, values) for p in ps}
    disjoint = {c for c, q in donors.items()
                if not set(core.oracle_bids(next(p for p in ps if p.cell == c)))
                & set(core.oracle_bids(q))}
    assert len(disjoint) == n_disjoint
    assert {c for c in donors if c not in disjoint} == {(5, "C", 5)}
    for p in ps:
      q = donors[p.cell]
      # Same variant and line; no-information donors only for no-information prompts.
      assert q.variant == p.variant and q.line == p.line and (q.C is None) == (p.C is None)
      assert q.cell != p.cell and q.V in values
      assert conditions.n7_donor(p, values) == q            # deterministic
      if p.cell != (5, "C", 5):
        # Nearest disjoint donor, ties to smaller V then smaller C.
        cands = [r for r in ps if r.line == p.line and r.cell != p.cell
                 and not set(core.oracle_bids(p)) & set(core.oracle_bids(r))]
        key = lambda r: (abs(p.V - r.V) + abs((p.C or 0) - (r.C or 0)), r.V, r.C or 0)
        assert key(q) == min(key(r) for r in cands)
  # Every-offer-optimal cell: smallest overlap (1), nearest, smaller V -> (V=5, C=4).
  q = conditions.n7_donor(core.Prompt(3, 5, "information", 5))
  assert (q.variant, q.V, q.C) == (3, 5, 4)
  # Spot checks.
  assert conditions.n7_donor(core.Prompt(1, 2, "neutral", None)).V == 4
  assert conditions.n7_donor(core.Prompt(1, 6, "pressure", None)).V == 4
  assert conditions.n7_donor(core.Prompt(1, 5, "information", 3)).cell == (5, "C", 2)


def test_audit_prompt():
  text, m = conditions.audit_prompt("Some notes.")
  assert text.endswith("Answer: (") and "(f) The notes do not favour any price" in text
  assert m["a"] == 1 and m["e"] == 5 and m["f"] is None


# ------------------------------------------------------------------ tuner
def test_tuner_can_choose_no_steering():
  assert steering.tune(lambda L, a: (-0.1, 1.0)) is None          # all settings hurt
  assert steering.tune(lambda L, a: (0.2, 0.5)) is None           # none coherent
  best = steering.tune(lambda L, a: (0.1 * a if L == 9 else 0.0, 1.0))
  assert best[:2] == (9, 4.0)


# ------------------------------------------------------------ basic stats
def test_signflip_exact_and_mc():
  x = [0.05] * 12 + [-0.01] * 6
  p_exact = analysis.signflip_greater(x)                       # n = 18: exact
  p_mc = analysis.signflip_greater(x * 2, n_mc=20_000)         # n = 36: Monte Carlo
  assert 0 < p_exact < 0.01 and 0 < p_mc < 0.01


def test_bh_holm_reverse_and_verdicts():
  r = analysis.benjamini_hochberg({"a": 0.01, "b": 0.02, "c": 0.035, "d": 0.5})
  assert r == {"a": True, "b": True, "c": True, "d": False}
  assert analysis.reverse_p(0.004, 0.5, 0.9) == 0.012
  assert analysis.verdict(False, True, (-0.4, -0.2), 0.05) == "reversed"
  assert analysis.verdict(False, False, (-0.01, 0.02), 0.05) == "equivalent"
  assert analysis.verdict(False, False, None, 0.05) == "inconclusive"
  v = analysis.confirmatory_verdicts({
      "good": {"p": 1e-4, "p_reverse": 1.0, "effect_cells": [0.2] * 35},
      "bad": {"p": 1.0, "p_reverse": 1e-5, "effect_cells": [-0.2] * 35},
      "null": {"p": 0.6, "p_reverse": 0.4, "effect_cells": [0.0, 0.01, -0.01] * 12}})
  assert v == {"good": "supported", "bad": "reversed", "null": "equivalent"}


def test_power_simulation_monotone():
  lo = analysis.power_simulation(sd=0.3, n_cells=35, n_sim=300)
  hi = analysis.power_simulation(sd=0.05, n_cells=35, n_sim=300)
  assert hi > 0.95 and lo < hi


# -------------------------------------------------------------------- A/B/R
def test_abr_tests_orientation():
  ps = core.prompt_set([1, 2])
  base, ent = conditions.BASELINE, conditions.ENTRIES[0]
  tag = ent.rsplit(".", 1)[-1]
  reg = {base: {p.pid: 0.5 for p in ps}, ent: {p.pid: 0.2 for p in ps}}
  soft = {}
  for p in ps:
    for c, v in {"N0": 0.6, "N1": 0.5, "N1s": 0.55, "N2": 0.2, f"N6:{tag}": 0.6, f"N7:{tag}": 0.5,
                 f"N8:{tag}": 0.3, f"N9:{tag}": 0.25, "N10": 0.0}.items():
      soft[(p.pid, c)] = v + 0.01 * (p.variant % 3)
  out = analysis.abr_tests(ps, soft, reg, base, {ent: ("N2", tag)})
  for k in ("A", "B", "R"):
    assert out[f"{k}:{tag}"]["p"] < 1e-4 and out[f"{k}:{tag}"]["p_reverse"] == 1.0


# -------------------------------------------------------------------- K1
def test_k1_single_pvalue_and_sharpen_null():
  d = [0.2] * 18
  r = analysis.k1_test(d, {"wording": [0.0] * 18, "sharpen": [0.05] * 18}, 0.2, [0.0] * 1000)
  assert r["p"] < 0.05 / 11 and r["min_attainable_random_p"] < 0.05 / 11
  r = analysis.k1_test(d, {"wording": [0.0] * 18, "sharpen": [0.3] * 18}, 0.2, [0.0] * 1000)
  assert r["p"] > 0.5                    # mere sharpening does better: fails
  p = {1: 0.1, 2: 0.6, 3: 0.2, 4: 0.05, 5: 0.05}
  s = analysis.sharpen(p, 3.0)
  assert max(s, key=s.get) == 2 and s[2] > p[2]


# -------------------------------------------------------------------- K2
def _base(ps):
  def around(m):
    w = {k: math.exp(-(k - m) ** 2) for k in core.PRICES}
    z = sum(w.values())
    return {k: w[k] / z for k in core.PRICES}
  return {p.pid: around(min(5, p.V - 1) + 0.3 * (p.variant % 3)) for p in ps}


def _test_prompts():
  return [p for p in core.prompt_set([1, 2, 3]) if core.steering_cell_split(p.cell) == "test"]


def test_k2_uses_unique_best_cells_only():
  ps = _test_prompts()
  base = _base(ps)
  r = analysis.calibration_test(ps, base, {k: analysis.flatten(v, 0.5) for k, v in base.items()},
                                n_boot=100)
  assert r["n_cells"] == 12


def test_k2_controls_do_not_pass():
  ps = _test_prompts()
  base = _base(ps)
  for steer in ({pid: analysis.attractor(pr, 2, 0.6) for pid, pr in base.items()},
                {pid: analysis.flatten(pr, 0.6) for pid, pr in base.items()},
                {pid: analysis.sharpen(pr, 3.0) for pid, pr in base.items()}):
    r = analysis.calibration_test(ps, base, steer, n_boot=300)
    assert r["p"] > 0.05, r


def test_k2_oracle_steering_passes():
  ps = _test_prompts()
  base = _base(ps)
  steer = {p.pid: {j: (0.96 if j == core.oracle_bids(p)[0] else 0.01) for j in core.PRICES}
           for p in ps}
  r = analysis.calibration_test(ps, base, steer, n_boot=300)
  assert r["rho_partial"] > 0.5 and r["p"] < 0.05, r


def test_k_tests_assembly_and_fidelity():
  test = [p for p in core.prompt_set([1, 2]) if core.steering_cell_split(p.cell) == "test"]
  flat = {k: 0.2 for k in core.PRICES}
  def toward(p):
    return {j: (0.96 if j == round(core.oracle_bid_point(p)) else 0.01) for j in core.PRICES}
  def res(gain, steer):
    r0 = {p.pid: core.soft_regret(p, flat) for p in test}
    return {p.pid: (r0[p.pid], r0[p.pid] - gain, flat, steer(p)) for p in test}
  named = {"content": res(0.3, toward), "wording": res(0.0, lambda p: flat),
           "length": res(0.0, lambda p: flat), "answer": res(0.0, lambda p: flat)}
  out = analysis.k_tests(test, named, res(0.3, toward),
                         [res(0.0, lambda p: flat) for _ in range(1000)], gamma=1.0, n_boot=200)
  assert out["K1"]["p"] < 0.05 / 11
  assert out["K2"]["rho_partial"] > 0.5
  soft = {}
  for p in test:
    soft[(p.pid, "N1")] = 1.0
    for c in ("N2", "N3", "N4"):
      soft[(p.pid, c)] = 0.4
  half = {p.pid: (1.0, 0.7, flat, flat) for p in test}
  assert abs(analysis.fidelity(test, soft, half) - 0.5) < 1e-9
````

### `scripts/build_reference.py`

````python
"""Builds REFERENCE.md: R1 (docs/reference_R1.md), R2 = verbatim listings of every
file in refimpl/, tests/ and scripts/ plus a requirements excerpt, R3
(docs/reference_R3.md). Run after any code change so the listings match exactly."""
import glob, os
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(root)
FILES = (sorted(glob.glob("refimpl/*.py")) + sorted(glob.glob("tests/*.py"))
         + sorted(glob.glob("scripts/*.py")) + sorted(glob.glob("scripts/*.sh")))
ORDER = ["refimpl/core.py", "refimpl/local_gemma2.py", "refimpl/determinism.py",
         "refimpl/runtime.py", "refimpl/phase2.py", "refimpl/phase3.py",
         "refimpl/conditions.py", "refimpl/steering.py", "refimpl/pipeline.py",
         "refimpl/analysis.py"]
FILES = [f for f in ORDER if f in FILES] + [f for f in FILES if f not in ORDER]
FILES = [f for f in FILES if not f.endswith("__init__.py")]
parts = [open("docs/reference_R1.md").read().rstrip() + "\n\n## R2. Code\n\n"
         "Every file below is listed verbatim (generated by `scripts/build_reference.py`).\n"]
for f in FILES:
  lang = "bash" if f.endswith(".sh") else "python"
  body = open(f).read().rstrip("\n")
  fence = "`" * 4                     # longer than any fence inside the listed files
  assert fence not in body, f
  parts.append(f"\n### `{f}`\n\n{fence}{lang}\n{body}\n{fence}\n")
lock = [l.strip() for l in open("requirements.gpu.lock") if l.split("==")[0] in
        ("accelerate", "immutabledict", "numpy", "pandas", "pyarrow", "safetensors", "scipy",
         "sentence-transformers", "tokenizers", "torch", "transformers", "nvidia-cudnn-cu12")]
n = sum(1 for l in open("requirements.gpu.lock") if l.strip())
parts.append(f"\n### `requirements.gpu.lock` (excerpt; the full file, {n} lines, ships with the code)\n\n```\n"
             + "\n".join(lock) + "\n```\n")
parts.append("\n" + open("docs/reference_R3.md").read().strip() + "\n")
open("REFERENCE.md", "w").write("".join(parts))
print("REFERENCE.md:", sum(len(p) for p in parts), "chars,", len(FILES), "files")
````

### `scripts/check_phase2_agents.py`

````python
"""Stage 1 check 4.4: one Phase 2 decision per agent on 9B, twice each.

Pilot prompt v13-V5-information-C3, real all-mpnet-base-v2 embeddings, and a
temporary blank memory bank (plus the player-specific memory, as
phase2.formative_memory adds it). Records only: exception or not, number of
model calls, whether S is non-empty, whether each rule memory reached the prompts,
the longest rendered prompt in tokens, wall time, and SHA-256 equality of S across
the two runs. No offer, regret, S text or calls log is printed or saved."""
import argparse, hashlib, json, os, random, sys, time, traceback
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import torch
from concordia.associative_memory import blank_memories, importance_function
from examples.modular.environment import haggling
from examples.modular.environment.modules import fruitville_haggling as fv
from refimpl import core, phase2, runtime
from refimpl.local_gemma2 import CHOICE_SYSTEM, TEXT_SYSTEM, LocalGemma2, build_messages

AGENTS = ("concordia.factory.agent.rational_agent", "concordia.factory.agent.basic_agent",
          "agent_py_files.taehun_cgcal", "agent_py_files.fluffy_fluffyagent_v16submission",
          "agent_py_files.hgyun_loss_aversion_agent_v3_plus2")
ap = argparse.ArgumentParser()
ap.add_argument("--agents", nargs="*", default=list(AGENTS))
ap.add_argument("--out", default="logs/check_phase2_agents.json")
args = ap.parse_args()

model, tok = runtime.load_gemma("9b", "cuda")
lm = LocalGemma2(model, tok, sequential=True)
embed, _ = runtime.load_embedder("embedder")
p = core.Prompt(13, 5, "information", 3)
assert p.pid == "v13-V5-information-C3"
random.seed(1000 + p.variant)
cfg = haggling.configure_player(p.buyer, "female", fv.YEAR, True, random.Random(1000 + p.variant))
mem = blank_memories.MemoryFactory(
    model=lm, embedder=embed,
    importance=importance_function.ConstantImportanceModel().importance,
    clock_now=lambda: phase2.SETUP).make_blank_memory()
for extra in cfg.extras["player_specific_memories"]:
  mem.add(extra, tags=["initial_player_specific_memory"])

def rendered_tokens(c):
  sysm = TEXT_SYSTEM if c["kind"] == "text" else CHOICE_SYSTEM
  return len(lm.encode(lm.render(build_messages(sysm, c["prompt"]), True))[0])

# Numbers-only generation log: prompt tokens and requested new tokens per call.
gen_log = []
_orig_generate = lm.model.generate
def _logged_generate(ids, **kw):
  gen_log.append({"prompt_tokens": int(ids.shape[1]), "max_new_tokens": kw.get("max_new_tokens")})
  torch.cuda.reset_peak_memory_stats()
  out = _orig_generate(ids, **kw)
  gen_log[-1]["new_tokens"] = int(out.shape[1] - ids.shape[1])
  gen_log[-1]["peak_GiB"] = round(torch.cuda.max_memory_allocated() / 2**30, 2)
  return out
lm.model.generate = _logged_generate

results = json.load(open(args.out)) if os.path.exists(args.out) else {}
for a in args.agents:
  runs = []
  for rep in (0, 1):
    torch.cuda.reset_peak_memory_stats()
    gen_log.clear()
    t = time.perf_counter()
    try:
      r = phase2.run_decision(lm, embed, a, p, mem, cfg, list(fv.VISUAL_SCENE_OPENINGS))
      runs.append({"exception": None, "wall_s": round(time.perf_counter() - t, 1),
                   "n_model_calls": len(r["calls"]),
                   "n_text_calls": sum(c["kind"] == "text" for c in r["calls"]),
                   "n_choice_calls": sum(c["kind"] == "choice" for c in r["calls"]),
                   "S_nonempty": bool(r["S"]),
                   "rule_memories_in_prompts": r["rule_memories_in_prompts"],
                   "longest_prompt_tokens": max(rendered_tokens(c) for c in r["calls"]),
                   "peak_gpu_GiB": round(torch.cuda.max_memory_allocated() / 2**30, 2),
                   "S_sha256": hashlib.sha256(r["S"].encode()).hexdigest()})
      del r
    except Exception as e:  # noqa: BLE001 - logged, run continues
      runs.append({"exception": repr(e)[:500], "traceback": traceback.format_exc()[-2000:],
                   "wall_s": round(time.perf_counter() - t, 1)})
    finally:
      # Release memory held by a failed call (left-over generation cache, frames).
      import gc
      if hasattr(lm.model, "_cache"):
        del lm.model._cache
      gc.collect(); torch.cuda.empty_cache()
    runs[-1]["generate_calls"] = list(gen_log)
  ok = all(x["exception"] is None for x in runs)
  results[a] = {"runs": runs, "S_identical_sha256": ok and runs[0]["S_sha256"] == runs[1]["S_sha256"]}
  printable = {k: v for k, v in results[a].items()}
  print(a, json.dumps(printable, indent=1), flush=True)
  json.dump(results, open(args.out, "w"), indent=1)
````

### `scripts/check_phase3_memory.py`

````python
"""Stage 1 check 4.3: peak GPU memory and time per sequential scoring pass on 9B,
for a short Phase 3 prompt and a worst-case one (3,000-token Notes filler, about
4,500 tokens in all), unsteered and steered at layer 18, with activation capture
as in Phase 3. Pilot variant 13 only. Prints no probabilities, offers or regret."""
import argparse, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import torch
from examples.modular.environment.modules import fruitville_haggling as fv
from refimpl import conditions, core, phase3, runtime
from refimpl.local_gemma2 import CHOICE_SYSTEM, LocalGemma2, build_messages

ap = argparse.ArgumentParser()
ap.add_argument("--model", default="9b")
ap.add_argument("--reps", type=int, default=3)
ap.add_argument("--out", default="logs/check_phase3_memory.json")
ap.add_argument("--notes-tokens", nargs="*", type=int, default=[200, 3000])
args = ap.parse_args()
model, tok = runtime.load_gemma(args.model, "cuda")
lm = LocalGemma2(model, tok, sequential=True)
openings = list(fv.VISUAL_SCENE_OPENINGS)
p = core.Prompt(13, 5, "neutral", None)
opening = openings[p.opening_index]
order = core.cyclic_orders()[0]
cases = {f"{n}-token notes": conditions.qa_filler(openings, n, tok) for n in args.notes_tokens}
LAYER = 18
results = {"model": args.model, "gpu": torch.cuda.get_device_name(0), "cases": {}}
for name, notes in cases.items():
  user, _ = phase3.decision_user_turn(p, opening, notes, order)
  n_tok = len(lm.encode(lm.render(build_messages(CHOICE_SYSTEM, user, "a"), False))[0])
  # Steering vector: the prompt's own layer-18 P1 activation (realistic norm).
  _, _, store, _ = phase3.score_prompt(lm, p, opening, notes, order, capture=True)
  vec = store[LAYER]["P1"].float()
  rec = {"tokens_per_sequence": n_tok, "notes_tokens": conditions.n_tokens(notes, tok)}
  for mode, steer in (("unsteered", None), ("steered L18", (LAYER, vec))):
    torch.cuda.synchronize(); torch.cuda.reset_peak_memory_stats()
    times, outs = [], []
    for _ in range(args.reps):
      t = time.perf_counter()
      probs, _, _, full = phase3.score_prompt(lm, p, opening, notes, order, capture=True,
                                              steer=steer)
      torch.cuda.synchronize()
      times.append(time.perf_counter() - t)
      outs.append(json.dumps([probs, full, lm.last_letter_mass]))
    rec[mode] = {"peak_gpu_bytes": torch.cuda.max_memory_allocated(),
                 "peak_gpu_GiB": round(torch.cuda.max_memory_allocated() / 2**30, 2),
                 "sec_per_scoring_5_passes": [round(x, 3) for x in times],
                 "sec_per_pass_mean": round(sum(times) / len(times) / 5, 3),
                 "repeat_bit_identical": len(set(outs)) == 1}
  results["cases"][name] = rec
  print(name, json.dumps(rec, indent=1), flush=True)
results["weights_GiB"] = round(sum(x.numel() * x.element_size() for x in model.parameters()) / 2**30, 2)
os.makedirs(os.path.dirname(args.out), exist_ok=True)
json.dump(results, open(args.out, "w"), indent=1)
print("weights GiB", results["weights_GiB"])
````

### `scripts/download_models.py`

````python
"""Download the pinned models into ./models (HF cache layout) and verify every
weight shard's SHA-256 against the LFS hashes listed by the Hub at that revision.
Reads HF_TOKEN from the environment; never prints or stores it."""
import hashlib, json, os, sys
from huggingface_hub import HfApi, snapshot_download

PINS = [("google/gemma-2-9b-it", "11c9b309abf73637e4b6f9a3fa1e92e615547819", None),
        ("google/gemma-2-2b-it", "299a8560bedf22ed1c72a8a11e7dce4a7f9f51f8", None),
        ("sentence-transformers/all-mpnet-base-v2", "e8c3b32edf5434bc2275fc9bab85f82640a19130",
         ["onnx/*", "openvino/*", "pytorch_model.bin", "*.h5", "*.ot", "*.msgpack"])]
WEIGHT_SUFFIXES = (".safetensors", ".bin")
token = os.environ["HF_TOKEN"]
api = HfApi(token=token)
report = {}
for repo, rev, ignore in PINS:
  info = api.model_info(repo, revision=rev, files_metadata=True)
  assert info.sha == rev, (repo, info.sha)
  path = snapshot_download(repo, revision=rev, cache_dir="models", token=token,
                           ignore_patterns=(ignore or []) + ["transformers/*"])
  res = {}
  for s in info.siblings:
    if not s.rfilename.endswith(WEIGHT_SUFFIXES) or not os.path.exists(os.path.join(path, s.rfilename)):
      continue
    h = hashlib.sha256()
    with open(os.path.join(path, s.rfilename), "rb") as f:
      for chunk in iter(lambda: f.read(1 << 24), b""):
        h.update(chunk)
    ok = h.hexdigest() == s.lfs.sha256
    res[s.rfilename] = {"sha256": h.hexdigest(), "lfs_sha256": s.lfs.sha256, "match": ok}
    print(repo, s.rfilename, "OK" if ok else "MISMATCH", flush=True)
  report[repo] = {"revision": rev, "path": path, "shards": res}
os.makedirs("logs", exist_ok=True)
with open("logs/model_hashes.json", "w") as f:
  json.dump(report, f, indent=1)
bad = [(r, n) for r, v in report.items() for n, x in v["shards"].items() if not x["match"]]
print("ALL SHARD HASHES MATCH" if not bad else f"MISMATCHES: {bad}")
sys.exit(1 if bad else 0)
````

### `scripts/generate_banks.py`

````python
"""Stage 1 step 5: generate the 14 formative-memory banks (variants 1-14) with
phase2.formative_memory on 9B (greedy, determinism patches), save each as parquet
(text, time, tags, importance, embedding) and record its SHA-256. Resumable:
existing banks are skipped. Banks contain no outcome."""
import argparse, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import torch
from refimpl import phase2, runtime
from refimpl.local_gemma2 import LocalGemma2

ap = argparse.ArgumentParser()
ap.add_argument("--variants", nargs="*", type=int, default=list(range(1, 15)))
ap.add_argument("--out", default="banks")
args = ap.parse_args()
os.makedirs(args.out, exist_ok=True)
manifest_path = os.path.join(args.out, "manifest.json")
manifest = json.load(open(manifest_path)) if os.path.exists(manifest_path) else {}
model, tok = runtime.load_gemma("9b", "cuda")
n_calls = {"n": 0}
lm = LocalGemma2(model, tok, sequential=True, log=lambda rec: n_calls.__setitem__("n", n_calls["n"] + 1))
embed, _ = runtime.load_embedder("embedder")
for v in args.variants:
  path = os.path.join(args.out, f"formative_v{v:02d}.parquet")
  if os.path.exists(path) and str(v) in manifest:
    print(f"variant {v}: exists, skipped", flush=True)
    continue
  n_calls["n"] = 0
  torch.cuda.reset_peak_memory_stats()
  t = time.perf_counter()
  mem, cfg = phase2.formative_memory(lm, embed, v)
  sha = phase2.save_bank(mem, path)
  # Save-and-reload check against the live memory (same process, so hashes comparable).
  import numpy as np
  loaded, cfg2 = phase2.load_bank(path, lm, embed, v)
  a, b = mem.get_data_frame(), loaded.get_data_frame()
  rt = (list(a.columns) == list(b.columns) and list(a.dtypes) == list(b.dtypes)
        and all(list(a[c]) == list(b[c]) for c in ("text", "time", "tags", "importance"))
        and all(np.array_equal(x, y) for x, y in zip(a["embedding"], b["embedding"]))
        and loaded._stored_hashes == mem._stored_hashes and cfg2.extras == cfg.extras)
  assert rt, f"variant {v}: bank reload differs from the generated memory"
  manifest[str(v)] = {"file": os.path.basename(path), "sha256": sha,
                      "rows": len(mem.get_data_frame()), "buyer": cfg.name,
                      "model_calls": n_calls["n"], "wall_s": round(time.perf_counter() - t, 1),
                      "peak_gpu_GiB": round(torch.cuda.max_memory_allocated() / 2**30, 2),
                      "reload_equal": rt}
  json.dump(manifest, open(manifest_path, "w"), indent=1, sort_keys=True)
  print(f"variant {v}:", json.dumps(manifest[str(v)]), flush=True)
print("done")
````

### `scripts/make_registration.py`

````python
"""Stage 1 step 6: write registration/ (hashes, revisions, hardware). Does not publish.

Usage: python scripts/make_registration.py <code commit hash>"""
import glob, hashlib, json, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import torch
from refimpl import runtime

commit = sys.argv[1]
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(root)

def sha(path):
  with open(path, "rb") as f:
    return hashlib.sha256(f.read()).hexdigest()

tracked = subprocess.run(["git", "ls-tree", "-r", "--name-only", commit], capture_output=True,
                         text=True, check=True).stdout.split()
code = sorted(f for f in tracked if f.endswith((".py", ".sh")) or f in
              ("PROTOCOL.md", "requirements.lock", "requirements.gpu.lock", ".gitignore"))
for f in code:   # hashes are of the committed bytes
  blob = subprocess.run(["git", "show", f"{commit}:{f}"], capture_output=True, check=True).stdout
  assert hashlib.sha256(blob).hexdigest() == sha(f), f"{f} differs from commit {commit}"
manifest = json.load(open("banks/manifest.json"))
banks = {m["file"]: m["sha256"] for _, m in sorted(manifest.items(), key=lambda kv: int(kv[0]))}
for f, h in banks.items():
  assert sha(os.path.join("banks", f)) == h, f
smi = subprocess.run(["nvidia-smi", "--query-gpu=name,driver_version,memory.total",
                      "--format=csv,noheader"], capture_output=True, text=True).stdout.strip()
gpu_name, driver, mem_total = [x.strip() for x in smi.split(",")]
model_hashes = json.load(open("logs/model_hashes.json"))
reg = {
  "code_commit": commit,
  "code_sha256": {f: sha(f) for f in code},
  "requirements.gpu.lock_sha256": sha("requirements.gpu.lock"),
  "memory_banks_sha256": banks,
  "models": {k: {"repo": r, "revision": v,
                 "weight_sha256": {n: x["sha256"] for n, x in model_hashes[r]["shards"].items()}}
             for k, (r, v) in runtime.PINS.items()},
  "concordia": {"tag": "v1.8.9", "commit": "3643ac0466f748b8055b61feb0b7908411f73d84"},
  "agent_zip": {"bytes": 4537615,
                "sha256": "e9ffb65167d776fd4beae14ee65cd3b44ec9c489870698c203f7acdefc199582"},
  "bank_generation_and_development_hardware": {
      "gpu": gpu_name, "gpu_memory": mem_total, "driver": driver,
      "torch": torch.__version__, "torch.version.cuda": torch.version.cuda,
      "cudnn": torch.backends.cudnn.version(), "instance": "AWS g5.xlarge (4 vCPUs, 16 GB RAM)"},
  "confirmatory_hardware": "to be decided (PROTOCOL.md section 3 specifies one 48 GB GPU)",
}
os.makedirs("registration", exist_ok=True)
json.dump(reg, open("registration/registration.json", "w"), indent=1, sort_keys=True)
lines = ["# Registration record (not published)", "",
         f"- Code commit: `{commit}`",
         f"- Concordia: v1.8.9, commit `{reg['concordia']['commit']}`",
         f"- Agent zip: {reg['agent_zip']['bytes']:,} bytes, SHA-256 `{reg['agent_zip']['sha256']}`", ""]
lines += ["## Models", ""]
for k, m in reg["models"].items():
  lines.append(f"- {m['repo']} at revision `{m['revision']}`")
  for n, h in m["weight_sha256"].items():
    lines.append(f"  - `{n}`: `{h}`")
lines += ["", "## Hardware", "",
          f"- **Bank-generation and development hardware:** {gpu_name} ({mem_total}), driver {driver}, "
          f"torch {torch.__version__}, CUDA (torch.version.cuda) {torch.version.cuda}, "
          f"cuDNN {torch.backends.cudnn.version()}; AWS g5.xlarge (4 vCPUs, 16 GB RAM).",
          "- **Confirmatory hardware:** to be decided. PROTOCOL.md section 3 specifies one 48 GB GPU; "
          "exact repeatability (P0.7) is required on that configuration only.", "",
          "## Memory banks (SHA-256)", ""]
lines += [f"- `{f}`: `{h}`" for f, h in banks.items()]
lines += ["", f"## requirements.gpu.lock", "", f"- `{reg['requirements.gpu.lock_sha256']}`", "",
          "## Code files (SHA-256 at the code commit)", ""]
lines += [f"- `{f}`: `{h}`" for f, h in reg["code_sha256"].items()]
open("registration/REGISTRATION.md", "w").write("\n".join(lines) + "\n")
print("\n".join(lines))
````

### `scripts/nonet.sh`

````bash
#!/usr/bin/env bash
# Run a command with no network: a fresh network namespace (loopback only), then
# drop straight back to the calling user. Used instead of `unshare -rn` because
# this host restricts unprivileged user namespaces
# (kernel.apparmor_restrict_unprivileged_userns=1). HF_TOKEN is never passed in.
set -euo pipefail
U=$(id -u); G=$(id -g); ROOT="$(cd "$(dirname "$0")/.." && pwd)"
exec sudo -n unshare -n -- setpriv --reuid="$U" --regid="$G" --init-groups -- \
  env -i HOME="$HOME" USER="$USER" PATH="$PATH" LANG=C.UTF-8 \
  HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  CUBLAS_WORKSPACE_CONFIG=:4096:8 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True \
  PYTHONPATH="$ROOT/concordia:$ROOT/agents_zip:$ROOT" \
  bash -c 'cd "$0" && ip link set lo up 2>/dev/null; exec "$@"' "$ROOT" "$@"
````

### `requirements.gpu.lock` (excerpt; the full file, 173 lines, ships with the code)

```
accelerate==0.34.2
immutabledict==4.3.1
numpy==1.26.4
nvidia-cudnn-cu12==9.1.0.70
pandas==2.0.3
pyarrow==17.0.0
safetensors==0.8.0
scipy==1.14.1
sentence-transformers==3.0.1
tokenizers==0.19.1
torch==2.4.1
transformers==4.44.2
```

## R3. Test results

All results below come from one NVIDIA A10G (24 GB; driver 595.112.07) on an AWS g5.xlarge (4 vCPUs, 16 GB RAM). The stack is the pinned GPU stack: Python 3.11.18, torch 2.4.1 with CUDA 12.1 and cuDNN 9.1.0.70, transformers 4.44.2 (`requirements.gpu.lock`). Models were loaded from their pinned revisions, and every weight shard's SHA-256 matched the Hub's LFS hash first:

- gemma-2-9b-it: 4 shards;
- gemma-2-2b-it: 2 shards;
- all-mpnet-base-v2: `model.safetensors`.

Every model process ran with no network and without `HF_TOKEN`. No offer, regret, S text or calls log of any agent was printed or saved. The agent checks use pilot prompts only.

### Unit tests (P0.10): 30 passed

`tests/test_core.py` covers:

- prompt and cell counts, including the 49-cell extension and its 24/25 split;
- the hand-computed best-offer table, including C = V and C > V;
- non-negative regret;
- the disjoint 17/18 split;
- seeds, and per-call seeding applied only inside a call context (the global generators are untouched without one);
- S entries, with the prompt's answer stem;
- softmax and cyclic orders;
- Holm and IUT;
- the direction of the sign-flip and Wilcoxon tests.

`tests/test_design.py` covers:

- **Advice removal.** These go: per-option profit lines, "3 coins: 2" lists, option labels, multi-price sentences, "offer 2", "a price of 3 seems fair" and "$2". These stay: single-price facts, "the average price is 3 coins" and "2 kg".
- **Conditions.** Exact-length Q/A filler; the 28-condition set, including a dropped paraphrase; the audit prompt.
- **N7 donors.**
  - 34 of 35 cells (48 of 49 with V = 7, 8) have a disjoint donor; the exception is cell (5, 5), whose donor is (5, 4).
  - Donors keep the variant and line; no-information prompts get only no-information donors.
  - Each donor is the nearest disjoint cell under the tie rule, checked by brute force.
  - The choice is deterministic.
- **Tuner.** It returns "no steering" when every setting hurts or none is coherent.
- **Sign-flip test.** Exact for 18 cells, Monte Carlo for 36.
- **Families and verdicts.** BH, the reverse rule, all four verdicts through the two Holm families, and the monotonicity of the power simulation.
- **A/B/R assembly**, including orientation.
- **K1.** It is one p-value and fails when the sharpening null does better.
- **K2.** It uses only the 12 unique-best cells; pulling to a fixed price, flattening and sharpening do not pass, and steering to each prompt's best offer does.
- **K1/K2 assembly and the fidelity measure.**

`tests/test_banks.py` covers memory banks:

- Save and reload reproduce columns, dtypes, every row (tags as tuples, embeddings bit-exact), the de-duplication hashes and the player config.
- Re-adding a duplicate row is ignored, while a row differing only in importance is added.
- The duplicate check also holds in a fresh process with a different `PYTHONHASHSEED`.

### Model configuration (P0.1): matches

`config.json` at the pinned 9B revision: 42 layers, hidden size 3,584, 16 query and 8 key-value heads, head dimension 256, sliding window 4,096, soft-caps 50 and 30, vocabulary 256,000.

**Loading.** 9B loads with `low_cpu_mem_usage=True` and `device_map={"": 0}`. Peak resident memory was 5.6 GB, and loading took about 2.3 minutes, limited by disk reads. The weights occupy 17.21 GiB on the GPU.

### `smoke_gemma.py` on 9B (Phase 3 path; P0.2, P0.7 and P0.9 logic): passed

The prompt is a smoke prompt with a made-up one-line note and placeholder openings, not any agent's text.

```
layers 42 hidden 3584 softcaps 50.0 30.0
render ok
score+capture 2.1s  [probabilities omitted here]
P2 '\nAnswer: ('
P3 ' so price accordingly."'
P4 ' 5 coins back'
prompt tokens 590; batched 1.19s, sequential 1.35s
batched vs sequential whole-answer |delta| (nats): {'a': '3.21e-01', 'b': '6.33e-02', 'c': '8.60e-02', 'd': '6.44e-02', 'e': '2.14e-01'}
batched vs sequential first-token |delta| (nats): {'a': '5.32e-02', 'b': '2.36e-02', 'c': '1.40e-01', 'd': '3.25e-02', 'e': '2.36e-02'}
P0.2 max |delta| = 3.210e-01 nats; criterion 1e-3: EXCEEDED; bit-identical: False
argmax identical (whole-answer, first-token): True True
batched vs sequential ok (same argmax)
repeat bit-identical ok
zero-steer identity ok
sample_text: 'blue. '
ALL SMOKE CHECKS PASSED
```

What this shows:

- The prompt is rendered with the system text folded into the first user turn.
- Activations are captured at all 42 layers at P1–P4, and P2–P4 decode to the intended text.
- Scoring the same prompt twice is bit-identical (P0.7 logic).
- A zero steering vector leaves both scorings bit-identical (P0.9), and a large vector moves the distribution.
- Greedy sampling is repeatable and stops at terminators.
- **Batched and sequential scoring are not bit-identical on this GPU:** up to 0.32 nats (whole-answer) and 0.14 nats (first-token), though with the same argmax. On a CPU the same comparison had been identical to the last bit.

  A diagnostic on 2B compared the final hidden state at P1 between batch sizes 5 and 1. It differs by up to 0.81, on a scale of 96. Unembedding in float32 leaves 0.18 nats, so the difference is not just bf16 logit rounding: GPU kernels chosen for different batch shapes accumulate floating-point error differently, and the error compounds over the layers.

  This is why the scoring mode is fixed (sequential) for every run, and why P0.2 is reported rather than used as a gate.

### `scoring_orders.py` on 9B

Same smoke prompt (V = 5, stated cost 3, a one-line note), five cyclic orders:

```
mean letter mass 0.570 (range 0.457-0.816); first-token vs whole-answer top choice agree in 3 of 5 orders
```

Whole-answer and first-token scoring disagree on the top choice in 2 of 5 orders, and the letter mass is well below 1. These are the reasons the protocol makes first-token scoring primary in Phase 3, reports whole-answer scoring for every test, and reports letter mass per condition.

### Phase 3 memory and time per pass on 9B (P0.11 logic)

Pilot prompt v13-V5-neutral with format-matched filler Notes. Sequential scoring with activation capture at all 42 layers; steering at layer 18 with the prompt's own P1 activation. Peak is `torch.cuda.max_memory_allocated()`. The card offers 22.06 GiB.

| Notes | Tokens per sequence | Peak GPU (unsteered / steered) | Time per pass (unsteered / steered) | Repeats bit-identical |
| --- | --- | --- | --- | --- |
| 200 tokens | 797 | 17.39 / 17.39 GiB | 0.383 / 0.384 s | yes |
| 3,000 tokens (the cap) | 3,597 | 19.40 / 19.40 GiB | 2.323 / 2.323 s | yes |
| 3,900 tokens | 4,497 | 20.56 / 20.56 GiB | 3.194 / 3.194 s | yes |

Every Phase 3 and 3b scoring fits a 24 GB GPU with sequential scoring.

### One Phase 2 decision per agent on 9B (P0.6 logic)

Pilot prompt v13-V5-information-C3, real all-mpnet-base-v2 embeddings. Memory: a temporary blank bank plus the player-specific memory. Each agent ran twice.

| Agent | Exception | Model calls (text + choice) | S non-empty | Rule memories reached prompts | Longest prompt (tokens) | Wall time | S byte-identical across runs |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `rational_agent` | none | 6 (5 + 1) | yes | 3 of 3 | 1,419 | 56 s, 54 s | yes |
| `basic_agent` | none | 12 (10 + 2) | yes | 3 of 3 | 1,836 | 86 s, 86 s | yes |
| `taehun_cgcal` | none | 7 (5 + 2) | yes | 3 of 3 | 701 | 10 s, 10 s | yes |
| `fluffy_fluffyagent_v16submission` | none | 5 (4 + 1) | yes | 3 of 3 | 3,331 | 169 s, 168 s | yes |
| `hgyun_loss_aversion_agent_v3_plus2` | CUDA out of memory | — | — | — | ≥ 2,424 | 122 s to failure | — |

`hgyun` fails in `generate` on a 2,424-token prompt, allocating 2.31 GiB (= 2,424 × 256,000 × 4 bytes). transformers 4.44.2's `Gemma2ForCausalLM.forward` unembeds every prompt position in prefill and copies the logits to float32. On top of 17.2 GiB of weights, that overflows 24 GB from about 2,400 prompt tokens. Phase 3 scoring is unaffected, because it unembeds only the answer positions. Phases 1–2 need the 48 GB GPU of Protocol section 3, or a registered change to prefill unembedding.

### `smoke_phase2.py` on 2B: passed

```
decision in 20s
model calls during episode: 6
rule memories seen in act() prompts: {0: True, 1: True, 2: True}
S non-empty: True  sha256(S): c444e197fab8730a
PHASE 2 SMOKE TEST PASSED (deterministic rerun identical)
```

### Formative-memory banks

The 14 banks (variants 1–14) were generated on 9B, greedy, under the determinism patches, in about 2.4 minutes each.

- Every bank has 13 rows, from 2 model calls.
- In each, the saved file reloads to a memory equal to the live one: rows, dtypes, de-duplication hashes and player config.
- Their SHA-256 values are in the registration record.
- Concordia printed one warning, for variant 4: 8 episodes were generated for 7 formative ages. Concordia pairs episodes with ages using `zip`, so the extra episode is dropped, as it would be upstream.

### Bugs the tests found and fixed

- **Out of memory in scoring.** Full-vocabulary logits for five sequences exhausted memory. The scorer now unembeds only the answer positions.
- **Deep copy fails.** `copy.deepcopy` of an `AssociativeMemory` fails on its thread lock. Its rows are now copied into a fresh memory.
- **Missing answer stem.** S dropped the answer stem each completion continues, so an entry read "Answer: is trying to buy…". The stem is now kept and unit-tested.
- **Unset attention mask.** `generate` warned about it; it is now passed explicitly.
- **Run-history dependence.** transformers 4.44.2 reuses Gemma 2's generation cache across calls when it is large enough. Attention shapes, and therefore rounding, then depend on earlier calls; this flipped a greedy token between two otherwise identical runs. `sample_text` now deletes the cache before each call. Memory sampling in `AssociativeMemory.add` uses numpy's global state, so each decision also starts by seeding the global generators.
- **Memory held after an out-of-memory error.** A failed `generate` left its cache and frames on the GPU, so the next decision failed at once. The agent check now releases the cache and collects garbage after an exception.

### Open issues

- **Phase 2 generation on 24 GB** (above): unresolved; needs the 48 GB GPU or a registered prefill change.
- **The pipeline driver end to end** has not run, because no pilot or confirmatory phase may run before registration. Its statistics are unit-tested (`abr_tests`, `k_tests`, `confirmatory_verdicts`, `power_simulation`). Its model-calling functions are loops over the tested `phase2.run_decision`, `phase3.score_prompt` and `LocalGemma2.letter_scores`.
