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
    self.last_first_token_wholepass: dict[str, float] = {}
    self.last_top_nonletter: list[tuple[str, float]] = []
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

  @contextlib.contextmanager
  def _last_position_unembedding(self):
    """During generate(), unembed only the last position.

    transformers 4.44.2's Gemma2ForCausalLM.forward unembeds every prompt position
    in the prefill step and copies the logits to float32 (about 1.5-2 GB per 1,000
    prompt tokens), although generation uses only the last position. A forward
    pre-hook on lm_head slices its input to the last position, so prefill memory
    no longer grows with the vocabulary. Decoding steps already have one position
    and are unchanged. Active only inside sample_text; letter_scores unembeds its
    own positions and never runs under this hook."""
    def pre(module, args):
      h = args[0]
      return (h[:, -1:, :],) if h.dim() == 3 and h.shape[1] > 1 else None
    handle = self.model.lm_head.register_forward_pre_hook(pre)
    try:
      yield
    finally:
      handle.remove()

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
    with torch.no_grad(), self._last_position_unembedding():
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
                    hooks: Sequence = (), sequential: bool | None = None,
                    whole_answer: bool = True
                    ) -> tuple[dict[str, float] | None, int, torch.Tensor]:
    """First-token and whole-answer letter scores.

    Returns (scores, p1_index, prefix_ids). p1_index is the position of the last
    prefix token (the newline after '<start_of_turn>model').

    P1 pass. The prefix alone is run once; its last position gives the next-token
    distribution at P1, from which last_first_token (each letter's first-token
    log-probability, the Phase 3 primary) and last_letter_mass are read. Hooks see
    this pass, so activations at P1-P4 are captured and steering at P1 applied here.

    Whole-answer passes (whole_answer=True). Each letter is appended as the whole
    assistant answer (letter, <end_of_turn>, newline) and scored by the summed
    log-probability of those tokens, Concordia's choice rule. All letters are
    single tokens, so the sequences have equal length. sequential=True (the
    default, self.sequential) scores them one per pass, batch size 1, always;
    sequential=False scores them in one batch (P0.2 comparison only). Hooks are
    registered for these passes too, so steering applies from P1 onwards in each.
    With whole_answer=False only the P1 pass runs and scores is None (Phase 3b
    tuning, which uses only the first-token distribution and the letter mass).
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
    cap = getattr(self.model.config, "final_logit_softcapping", None)

    def unembed(hidden_slice):
      # Only the needed positions are unembedded (no [seq, 256k] logits; works on
      # transformers 4.44.2). Soft-cap and log-softmax in float32.
      logits = self.model.lm_head(hidden_slice).float()
      if cap:
        logits = torch.tanh(logits / cap) * cap
      return torch.log_softmax(logits, dim=-1)

    groups = []
    if whole_answer:
      groups = [batch[b:b + 1] for b in range(len(seqs))] if sequential else [batch]
    logps = []
    handles = [h() for h in hooks]
    try:
      with torch.no_grad():
        hidden = self.model.model(input_ids=prefix_ids[None], use_cache=False).last_hidden_state
        logp1 = unembed(hidden[:, -1:])[0, 0]                         # P1 distribution
        del hidden
        for g in groups:
          hidden = self.model.model(input_ids=g, use_cache=False).last_hidden_state
          logps.append(unembed(hidden[:, start - 1:-1]))
          del hidden
    finally:
      for h in handles:
        h.remove()
    letter_ids = [int(batch[b, start]) for b in range(len(letters))]
    first = {l: float(logp1[i]) for l, i in zip(letters, letter_ids)}
    # Coherence measure (Protocol 10.4): next-token probability mass on the letters.
    self.last_letter_mass = float(sum(np.exp(v) for v in first.values()))
    self.last_first_token = first           # Phase 3 primary outcome
    # Where the rest of the P1 mass goes: the five most probable non-letter tokens.
    top = torch.topk(logp1, len(letters) + 5)
    self.last_top_nonletter = [(self.tok.decode([int(i)]), float(np.exp(float(v))))
                               for v, i in zip(top.values, top.indices)
                               if int(i) not in letter_ids][:5]
    if not whole_answer:
      self.last_first_token_wholepass = {}
      return None, start - 1, prefix_ids
    logp = torch.cat(logps, 0)
    # Diagnostic only: P1 read from the whole-answer passes (same quantity,
    # different tensor shapes, so it can differ in the last bits; see P0.2).
    self.last_first_token_wholepass = {l: float(logp[b, 0, letter_ids[b]])
                                       for b, l in enumerate(letters)}
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
