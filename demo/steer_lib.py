"""Helpers for the steering checks: exact capture and patching at P1, per-order
scoring with arbitrary hooks, the top-10 P1 tokens, and last-position steering for
free-text generation. Everything here runs on one loaded LocalGemma2."""
from __future__ import annotations

import json
import math
import os

import numpy as np
import torch

import common
import scoring
from refimpl import analysis, core, phase3
from refimpl.local_gemma2 import CHOICE_SYSTEM, build_messages, ensure_prompt_not_too_long

ORDERS = scoring.ORDERS
LETTERS = phase3.LETTERS


def lora_cases(split_name: str):
  sp = json.load(open(os.path.join(common.DEMO_DIR, "splits_lora.json")))["case_split"]
  P = common.prompts_by_id()
  return [P[pid] for pid, s in sp.items() if s == split_name]


def eval_cases():
  """12 held-out tune cases: variants 15 and 18 of the six held-out tune cells."""
  return [p for p in lora_cases("lora_tune") if p.variant in (15, 18)]


class Runner:
  def __init__(self, lm):
    self.lm = lm
    self.tok = lm.tok
    self.layers = lm.model.model.layers
    self.letter_ids = [lm.tok.convert_tokens_to_ids(l) for l in LETTERS]

  # ----------------------------------------------------------- one scoring
  def user(self, p, oi, notes=None):
    return scoring.user_turn(scoring.key(p), notes, tuple(ORDERS[oi]), False)

  def p1(self, user):
    return scoring._p1_index(self.lm, user)

  def run(self, p, oi, notes=None, hooks_fn=None):
    """One P1 pass. hooks_fn(p1) -> list of hook factories. Returns
    (probs {price: p}, letter mass, first-token log-probs {letter: lp}, l2p, p1)."""
    user, l2p = self.user(p, oi, notes)
    p1 = self.p1(user)
    hooks = hooks_fn(p1) if hooks_fn else []
    _, p1c, _ = self.lm.letter_scores(user, LETTERS, hooks=hooks, whole_answer=False)
    assert p1c == p1
    first = dict(self.lm.last_first_token)
    return core.softmax_scores(first, l2p), self.lm.last_letter_mass, first, l2p, p1

  # --------------------------------------------------------------- hooks
  def capture(self, layers, store):
    """Factories storing the exact (bf16 -> float32) residual at P1 after each layer."""
    def mk(L):
      def hook(mod, inp, out):
        hs = out[0] if isinstance(out, tuple) else out
        store[L] = hs[0, self._p1].detach().float().cpu()
      return lambda: self.layers[L].register_forward_hook(hook)
    return [mk(L) for L in layers]

  def with_capture(self, p, oi, layers, notes=None, extra=None):
    store: dict = {}
    def hooks_fn(p1):
      self._p1 = p1
      return self.capture(layers, store) + (extra(p1) if extra else [])
    out = self.run(p, oi, notes, hooks_fn)
    return out, store

  def patch(self, L, vec):
    def fn(p1):
      def hook(mod, inp, out):
        hs = out[0] if isinstance(out, tuple) else out
        hs[:, p1, :] = vec.to(hs.dtype).to(hs.device)
        return (hs, *out[1:]) if isinstance(out, tuple) else hs
      return [lambda: self.layers[L].register_forward_hook(hook)]
    return fn

  def steer(self, L, vec):
    def fn(p1):
      return [phase3.steering_hook(self.lm, L, vec, lambda: p1)]
    return fn

  # ----------------------------------------------------------- top tokens
  def top10(self, p, oi, hooks_fn=None, notes=None):
    user, _ = self.user(p, oi, notes)
    p1 = self.p1(user)
    trimmed = ensure_prompt_not_too_long(user, 1)
    ids = self.lm.encode(self.lm.render(build_messages(CHOICE_SYSTEM, trimmed), True))[0]
    handles = [h() for h in (hooks_fn(p1) if hooks_fn else [])]
    try:
      with torch.no_grad():
        hidden = self.lm.model.model(input_ids=ids[None], use_cache=False).last_hidden_state
        logits = self.lm.model.lm_head(hidden[:, -1:]).float()
    finally:
      for h in handles:
        h.remove()
    cap = self.lm.model.config.final_logit_softcapping
    logits = torch.tanh(logits / cap) * cap
    lp = torch.log_softmax(logits, dim=-1)[0, 0]
    top = torch.topk(lp, 10)
    return [(self.tok.decode([int(i)]), round(math.exp(float(v)), 4)) for v, i in zip(top.values, top.indices)]

  # ------------------------------------------------------ free-text steering
  def say_steered(self, p, L, vec):
    """Greedy free text with `vec` added at the last position of the prefill and of
    every decoding step (the 'readout position onward')."""
    def hook(mod, inp, out):
      hs = out[0] if isinstance(out, tuple) else out
      hs[:, -1, :] = hs[:, -1, :] + vec.to(hs.dtype).to(hs.device)
      return (hs, *out[1:]) if isinstance(out, tuple) else hs
    h = self.layers[L].register_forward_hook(hook)
    try:
      return scoring.say(self.lm, p)
    finally:
      h.remove()


# ------------------------------------------------------------------ metrics
def aggregate(cases, res, plain=None):
  """res: {(pid, oi): (probs, mass)} over the five orders. Returns order-averaged
  per-case results and summary metrics (cell-mean renormalised soft regret, change
  in expected offer against `plain`, letter mass relative to `plain`)."""
  per = {}
  for p in cases:
    ps = [res[(p.pid, oi)][0] for oi in range(5)]
    avg = {k: float(np.mean([d[k] for d in ps])) for k in core.PRICES}
    per[p.pid] = {"probs": avg, "mass": float(np.mean([res[(p.pid, oi)][1] for oi in range(5)])),
                  "expected": core.expected_bid(avg)}
  soft = {p.pid: core.soft_regret(p, per[p.pid]["probs"]) for p in cases}
  out = {"soft_regret": float(np.mean(list(analysis.cell_means(soft, cases).values()))),
         "expected": float(np.mean([v["expected"] for v in per.values()])),
         "mass": float(np.mean([v["mass"] for v in per.values()]))}
  if plain is not None:
    out["d_expected"] = float(np.mean([per[p.pid]["expected"] - plain[p.pid]["expected"] for p in cases]))
    out["mass_ratio"] = out["mass"] / float(np.mean([plain[p.pid]["mass"] for p in cases]))
  return out, per


def unit(v):
  v = v.float()
  return v / v.norm()
