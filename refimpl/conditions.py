"""Phase 3 condition builders (Protocol section 9.2): the inserted text per condition."""
from __future__ import annotations

import re
from typing import Callable, Collection, Mapping, Sequence

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
                     values: Sequence[int] = core.VALUES,
                     only: Collection[str] | None = None) -> dict[str, str | None]:
  """All 28 conditions for prompt p, or only the codes in `only`. Dicts are keyed
  [agent][pid]. Returns code -> inserted text (None = no Notes block). Texts are
  capped (core.cap_tokens). values: the V grid in use (core.VALUES, or VALUES +
  EXT_VALUES with the extension); it fixes the N7 donor set.

  Each condition reads only the data it needs, so the pilot
  (only=("N0", "N1")) needs nothing but the baseline's S: no entry's S, offer or
  paraphrase is read (Protocol 6, sealed pilot file)."""
  pid = p.pid
  want = (lambda code: True) if only is None else (lambda code: code in only)
  out: dict[str, str | None] = {}
  if want("N0"):
    out["N0"] = None
  if want("N1"):
    out["N1"] = S[BASELINE][pid]
  if want("N1s"):
    out["N1s"] = remove_recommendations_strict(S[BASELINE][pid])
  if want("N10"):
    out["N10"] = core.answer_only(p.buyer, oracle_offer(p))
  for a in AGENTS:
    tag = a.rsplit(".", 1)[-1]
    if a in ENTRY_CODE:
      c = ENTRY_CODE[a]
      if want(c):
        out[c] = S[a][pid]
      if want(c + "r"):
        out[c + "r"] = S_reason[a][pid]
      if want(f"N7:{tag}"):
        out[f"N7:{tag}"] = S[a][n7_donor(p, values).pid]
      if want(f"N8:{tag}"):
        out[f"N8:{tag}"] = remove_recommendations_strict(S[a][pid])
    if want(f"N5:{tag}") and paraphrases[a].get(pid) is not None:  # failed paraphrase: key
      out[f"N5:{tag}"] = paraphrases[a][pid]                      # absent, dropped from wording contrasts
    if want(f"N6:{tag}"):
      out[f"N6:{tag}"] = qa_filler(openings, n_tokens(S[a][pid], tokenizer), tokenizer)
    if want(f"N9:{tag}"):
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
