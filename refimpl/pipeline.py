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
               draws: Sequence[int] = (0,), fname: str = "phase2.jsonl",
               sealed: bool = False):
  """formative: variant -> (memory, cfg), loaded from the released banks
  (phase2.load_bank). Exclusion rule: one retry with the same seed, then the
  failure is recorded. E1: temperature=0.5, draws=range(5), fname='phase2_e1.jsonl'.

  sealed=True (the pilot, Protocol 6): for every agent except the baseline, the
  full record (offer, regret, S, calls) goes only to records/sealed_<fname>, and
  the open record keeps only what the pilot analysis may read: wall time, call
  count, S token length and whether the 3,000-token cap binds, and the retrieval
  log. seal_file() then gives the sealed file's SHA-256 for publication."""
  import time
  for a in agents:
    for draw in draws:
      for p in prompts:
        mem, cfg = formative[p.variant]
        rec = None
        for attempt in (0, 1):
          t0 = time.perf_counter()
          try:
            r = phase2.run_decision(lm, embedder, a, p, mem, cfg, list(openings),
                                    draw=draw, temperature=temperature)
            rec = {"agent": a, "pid": p.pid, "draw": draw, "k": r["k"],
                   "hard_regret": r["hard_regret"], "S": r["S"], "S_reason": r["S_reason"],
                   "rule_seen": r["rule_memories_in_prompts"], "calls": r["calls"],
                   "act_from": r["act_from"], "attempt": attempt,
                   "wall_s": time.perf_counter() - t0, "n_calls": len(r["calls"]),
                   "S_tokens": conditions.n_tokens(r["S"], lm.tok),
                   "S_capped": core.cap_tokens(r["S"], lm.tok)[1]}
            break
          except Exception as e:  # noqa: BLE001 - recorded, then excluded
            rec = {"agent": a, "pid": p.pid, "draw": draw, "error": repr(e),
                   "attempt": attempt, "wall_s": time.perf_counter() - t0}
        if sealed and a != conditions.BASELINE:
          _jsonl(f"{out}/records/sealed_{fname}", rec)
          rec = {k: rec[k] for k in ("agent", "pid", "draw", "attempt", "wall_s", "error",
                                      "n_calls", "S_tokens", "S_capped", "rule_seen")
                 if k in rec}
          rec["sealed"] = True
        _jsonl(f"{out}/records/{fname}", rec)


def seal_file(out: str, fname: str = "phase2.jsonl") -> str:
  """SHA-256 of the sealed pilot file, published at registration time of the
  confirmatory phases; the file itself is not opened until Phase 3b ends."""
  import hashlib
  with open(f"{out}/records/sealed_{fname}", "rb") as f:
    return hashlib.sha256(f.read()).hexdigest()


def load_phase2(out: str, fname: str = "phase2.jsonl"):
  """Returns S, S_reason, offers, regret (agent -> pid -> value) and the excluded
  pids (dropped for every agent and condition)."""
  S, S_reason, offers, regret, failed = {}, {}, {}, {}, set()
  for r in _read_jsonl(f"{out}/records/{fname}"):
    if "error" in r:
      if r["attempt"] == 1:
        failed.add(r["pid"])
      continue
    if r.get("sealed"):
      continue                     # pilot: entries' outcomes are in the sealed file
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
                                        values, only=only)
    opening = openings[p.opening_index]
    for code, notes in conds.items():
      acc = {}
      for oi, order in enumerate(orders):
        probs, hard, store, probs_full = phase3.score_prompt(lm, p, opening, notes, order,
                                                             capture=True)
        _jsonl(f"{out}/records/phase3.jsonl",
               {"pid": p.pid, "cond": code, "order": oi, "probs": probs, "hard": hard,
                "probs_full": probs_full, "letter_mass": lm.last_letter_mass,
                "top_nonletter": lm.last_top_nonletter,
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


def final_price_choice(calls: Sequence[dict], act_from: int) -> dict | None:
  """The call that decided the offer, if the decision ended in a multiple-choice
  call over the five prices: the last model call made during act() must be a
  choice call whose prompt lists all five price options. Otherwise (for example
  taehun_cgcal choosing in Python after a yes/no choice call) None."""
  act_calls = list(calls[act_from:])
  if not act_calls:
    return None
  c = act_calls[-1]
  if c["kind"] != "choice" or len(c["scores"]) != len(core.PRICES):
    return None
  if not all(core.OPTION_TEXT[k] in c["prompt"] for k in core.PRICES):
    return None
  return c


def run_native_replay(lm: LocalGemma2, out: str):
  """Re-score each Phase 2 decision's final price choice prompt (Protocol 9.4).
  Decisions that did not end in a price choice call are recorded as such and
  excluded from the agreement rate."""
  for r in _read_jsonl(f"{out}/records/phase2.jsonl"):
    if "error" in r:
      continue
    c = final_price_choice(r["calls"], r["act_from"])
    if c is None:
      _jsonl(f"{out}/records/native_replay.jsonl",
             {"agent": r["agent"], "pid": r["pid"], "ended_in_price_choice": False})
      continue
    letters = list(c["scores"])
    scores, _, _ = lm.letter_scores(c["prompt"], letters)
    first = dict(lm.last_first_token)
    _jsonl(f"{out}/records/native_replay.jsonl",
           {"agent": r["agent"], "pid": r["pid"], "ended_in_price_choice": True,
            "phase2_choice": c["choice"],
            "replay_choice": max(letters, key=lambda l: (scores[l], -letters.index(l))),
            "replay_first_token_choice": max(letters, key=lambda l: (first[l], -letters.index(l))),
            "first_token": first})


def native_replay_labels(out: str, threshold: float = 0.80) -> dict[str, dict]:
  """Per entry: share of price-choice decisions whose first-token argmax equals
  the Phase 2 choice; below threshold -> 'transplant-sensitive' (Protocol 9.4)."""
  recs = [r for r in _read_jsonl(f"{out}/records/native_replay.jsonl")
          if r.get("ended_in_price_choice")]
  res = {}
  for a in conditions.ENTRIES:
    rs = [r for r in recs if r["agent"] == a]
    rate = float(np.mean([r["replay_first_token_choice"] == r["phase2_choice"] for r in rs])) if rs else float("nan")
    res[a] = {"n": len(rs), "agreement": rate,
              "transplant_sensitive": bool(rs) and rate < threshold}
  return res


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
def pilot_power_rule(out: str, prompts: Sequence[core.Prompt],
                     n_variants: int = 12) -> dict:
  """Baseline-only pilot quantities and the registered power rule (Protocol 6).

  The SD of N1 - N0 cell means is projected from the pilot's 2 variants per cell
  to the 12 of the confirmatory design (analysis.projected_cell_sd), because
  2-variant cell means carry more within-cell noise. Power is simulated for the
  number of cells in the pilot's grid (35), and reported for 18 cells (K1)."""
  soft = soft_regret_table(out, prompts)
  n0 = {p.pid: soft[(p.pid, "N0")] for p in prompts if (p.pid, "N0") in soft}
  n1 = {p.pid: soft[(p.pid, "N1")] for p in prompts if (p.pid, "N1") in soft}
  d = {pid: n1[pid] - n0[pid] for pid in n1 if pid in n0}
  proj = analysis.projected_cell_sd(d, prompts, n_variants)
  sd = proj["sd_projected"]
  n_cells = proj["n_cells"]
  power = analysis.power_simulation(sd, n_cells=n_cells)
  power_k1 = analysis.power_simulation(sd, n_cells=18)
  n1_cells = analysis.cell_means(n1, prompts)
  near = sorted([c for c, v in n1_cells.items() if v < analysis.SESOI_REGRET], key=str)
  return {"sd_projected": sd, **proj, "power": power, "power_18_cells": power_k1,
          "extend": power < 0.80, "near_ceiling_cells": near}


# ---------------------------------------------------------------- Phase 3b
def _p1(out: str, pid: str, cond: str, layer: int) -> torch.Tensor:
  return torch.load(f"{out}/acts/{pid}/{cond.replace(':', '_')}.pt")[layer]["P1"].float()


def _has(out: str, pid: str, cond: str) -> bool:
  return os.path.exists(f"{out}/acts/{pid}/{cond.replace(':', '_')}.pt")


def named_directions(out: str, dev: Sequence[core.Prompt], layer: int,
                     entries: Sequence[str] = conditions.ENTRIES) -> dict:
  """Content and the three named nulls at one layer (Protocol 10.2), pooled over
  `entries` (all three for K1; one for E3). A prompt enters a contrast only if
  every condition in that contrast exists for it (a dropped paraphrase removes the
  prompt from the wording contrast only). Also returns each null's natural norm."""
  tags = [a.rsplit(".", 1)[-1] for a in entries]
  base_tag = conditions.BASELINE.rsplit(".", 1)[-1]
  ent = [conditions.ENTRY_CODE[a] for a in entries]
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
  return {"content": content, **{k: steering.rescale(v, norm) for k, v in nulls.items()},
          "natural_norms": {"content": norm, **{k: float(v.norm()) for k, v in nulls.items()}}}


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
                   layer: int | None, vec: torch.Tensor | None, orders,
                   whole_answer: bool = False, full_out: dict | None = None):
  """(soft regret, mean letter mass at P1, mean p(k)) over the given orders, from
  the first-token distribution at P1; layer=None scores unsteered.

  whole_answer=False (tuning): only the P1 pass runs. whole_answer=True (test
  evaluation): the whole-answer passes also run, and full_out (if given) receives
  the order-averaged whole-answer p(k) under "probs_full" (K sensitivity)."""
  regs, mass, dists, fulls = [], [], [], []
  for order in orders:
    steer = None if layer is None else (layer, vec)
    probs, _, _, full = phase3.score_prompt(lm, p, opening, notes, order, steer=steer,
                                            whole_answer=whole_answer)
    regs.append(core.soft_regret(p, probs)); dists.append(probs)
    mass.append(lm.last_letter_mass)
    if full is not None:
      fulls.append(full)
  mean_p = {k: float(np.mean([d[k] for d in dists])) for k in core.PRICES}
  if full_out is not None and fulls:
    full_out["probs_full"] = {k: float(np.mean([d[k] for d in fulls])) for k in core.PRICES}
  return float(np.mean(regs)), float(np.mean(mass)), mean_p


def all_orders(p: core.Prompt):
  return core.cyclic_orders()


def single_order(p: core.Prompt):
  """One order per prompt, rotating with the variant (random-direction budget)."""
  return [core.cyclic_orders()[(p.variant - 1) % 5]]


def tuning_subset(dev: Sequence[core.Prompt]) -> list[core.Prompt]:
  """The lowest variant of each development cell: variant 1, so 17 prompts (24 with
  the extension)."""
  first = {}
  for p in dev:
    if p.cell not in first or p.variant < first[p.cell].variant:
      first[p.cell] = p
  return [p for p in dev if first[p.cell] is p]


def make_evaluate(lm, prompts, notes_n1, openings, direction_at: Callable[[int], torch.Tensor],
                  orders_for, cache: dict | None = None):
  """evaluate(layer, alpha) -> (mean soft-regret reduction, letter-mass ratio).

  The ratio is the mean steered letter mass over the tuning prompts divided by
  the mean unsteered letter mass (a ratio of means, Protocol 10.4)."""
  base = {} if cache is None else cache          # unsteered results are deterministic,
  def unsteered(p):                                # so one cache serves every direction
    key = (p.pid, tuple(orders_for(p)), False)
    if key not in base:
      base[key] = steered_regret(lm, p, notes_n1[p.pid], openings[p.opening_index],
                                 None, None, orders_for(p))
    return base[key]
  def evaluate(layer, alpha):
    vec = alpha * direction_at(layer)
    red, m_steer, m_base = [], [], []
    for p in prompts:
      r0, m0, _ = unsteered(p)
      r, m, _ = steered_regret(lm, p, notes_n1[p.pid], openings[p.opening_index],
                               layer, vec, orders_for(p))
      red.append(r0 - r); m_steer.append(m); m_base.append(m0)
    base_mass = float(np.mean(m_base))
    return float(np.mean(red)), (float(np.mean(m_steer)) / base_mass if base_mass > 0 else 0.0)
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


def isotropic_directions_at(d_model: int, content_norm_at: Callable[[int], float],
                           n: int = 200, seed: int = 12) -> list[Callable[[int], torch.Tensor]]:
  """n isotropic Gaussian directions (one draw each from PCG64(seed), reused at
  every layer), rescaled to the content norm at each layer. A reported
  calibration reference for K1's random component, not a component (10.2)."""
  rng = np.random.Generator(np.random.PCG64(seed))
  vs = [torch.from_numpy(rng.standard_normal(d_model).astype(np.float32)) for _ in range(n)]
  return [lambda L, v=v: steering.rescale(v, content_norm_at(L)) for v in vs]


NAMED = ("content", "wording", "length", "answer")


def run_phase3b(lm, out: str, dev, test, notes_n1, openings, n_random: int = 1000,
                n_isotropic: int = 200, layers: Sequence[int] = steering.LAYERS,
                secondary: bool = True):
  """Tune and evaluate every direction (Protocol 10.4-10.6).

  Returns {"K": k_tests input for K1/K2, "E6": the same with the letter-span
  projected content direction, "E3": {entry tag: the same with that entry's own
  content direction}, "isotropic_rank": the matched content copy's rank among the
  isotropic directions, "fallbacks": how many tunings chose no steering,
  "natural_norms": per layer}. E6 and E3 reuse the named nulls' and the random
  directions' test results; only their content direction and its matched copy are
  tuned anew. Tuning runs the P1 pass only; test evaluation of the named directions
  also runs the whole-answer passes (K sensitivity)."""
  dirs = {L: named_directions(out, dev, L) for L in layers}
  at = {name: (lambda L, n=name: dirs[L][n]) for name in NAMED}
  sub = tuning_subset(dev)
  cache = {}                         # unsteered scorings, shared by every direction
  def tune_all(fn):
    return steering.tune(make_evaluate(lm, dev, notes_n1, openings, fn, all_orders, cache),
                         layers=layers)
  def tune_matched(fn):
    return steering.tune(make_evaluate(lm, sub, notes_n1, openings, fn, single_order, cache),
                         layers=layers)
  whole = {}                         # whole-answer p(k) on test prompts (K sensitivity)
  def unsteered_test(p, orders_for, wa):
    key = ("test", p.pid, tuple(orders_for(p)), wa)
    if key not in cache:
      f0 = {}
      r0, _, p0 = steered_regret(lm, p, notes_n1[p.pid], openings[p.opening_index],
                                 None, None, orders_for(p), whole_answer=wa, full_out=f0)
      cache[key] = (r0, p0, f0)
    return cache[key]
  def evaluate_on_test(setting, direction_at, orders_for, name=None):
    res = {}
    wa = name is not None             # whole-answer passes only for the named directions
    for p in test:
      f1 = {}
      r0, p0, f0 = unsteered_test(p, orders_for, wa)
      if setting is None:
        res[p.pid] = (r0, r0, p0, p0)
        f1 = f0
      else:
        L, alpha, _ = setting
        r1, _, p1 = steered_regret(lm, p, notes_n1[p.pid], openings[p.opening_index],
                                   L, alpha * direction_at(L), orders_for(p),
                                   whole_answer=wa, full_out=f1)
        res[p.pid] = (r0, r1, p0, p1)
      if wa:
        whole.setdefault(name, {})[p.pid] = (f0.get("probs_full"), f1.get("probs_full"))
    return res
  # Named directions: all dev prompts, all orders.
  tuned = {n: tune_all(fn) for n, fn in at.items()}
  named = {n: evaluate_on_test(tuned[n], at[n], all_orders, name=n) for n in at}
  # Matched budget for the random comparison: content and each random direction
  # tuned on 17 prompts x 1 order, evaluated on the single rotating order.
  content_matched = tune_matched(at["content"])
  matched = evaluate_on_test(content_matched, at["content"], single_order)
  norm_at = lambda L: float(dirs[L]["content"].norm())
  rands = random_directions_at(out, dev, norm_at, n_random)
  rand_tuned = [tune_matched(fn) for fn in rands]
  random_single = [evaluate_on_test(st, fn, single_order) for st, fn in zip(rand_tuned, rands)]
  # Sharpening null: gamma tuned on the dev prompts' unsteered N1 distributions.
  dev_base = {}
  for p in dev:
    key = (p.pid, tuple(all_orders(p)), False)
    if key not in cache:
      cache[key] = steered_regret(lm, p, notes_n1[p.pid], openings[p.opening_index],
                                  None, None, all_orders(p))
    dev_base[p.pid] = cache[key][2]
  gamma = analysis.tune_sharpen(dev, dev_base)
  K = {"named": named, "content_matched": matched, "random_single": random_single, "gamma": gamma}
  settings = {"named": tuned, "content_matched": content_matched, "random": rand_tuned,
              "gamma": gamma}
  result = {"K": K}
  def variant(content_at, key):
    st, stm = tune_all(content_at), tune_matched(content_at)
    settings[key] = {"content": st, "content_matched": stm}
    nm = dict(named)
    nm["content"] = evaluate_on_test(st, content_at, all_orders, name=f"{key}:content")
    return {"named": nm, "content_matched": evaluate_on_test(stm, content_at, single_order),
            "random_single": random_single, "gamma": gamma}
  if secondary:
    proj = {L: project_out_letters(lm, dirs[L]["content"]) for L in layers}
    result["E6"] = variant(lambda L: proj[L], "E6")
    result["E3"] = {}
    for a in conditions.ENTRIES:
      tag = a.rsplit(".", 1)[-1]
      own = {L: named_directions(out, dev, L, [a])["content"] for L in layers}
      result["E3"][tag] = variant(lambda L, own=own: own[L], f"E3:{tag}")
  iso = isotropic_directions_at(int(dirs[layers[0]]["content"].numel()), norm_at, n_isotropic)
  iso_tuned = [tune_matched(fn) for fn in iso]
  iso_means = [float(np.mean([v[0] - v[1] for v in evaluate_on_test(st, fn, single_order).values()]))
               for st, fn in zip(iso_tuned, iso)]
  matched_mean = float(np.mean([v[0] - v[1] for v in matched.values()]))
  result["isotropic_rank"] = analysis.permutation_p(matched_mean, iso_means)
  all_settings = list(tuned.values()) + rand_tuned + iso_tuned + [content_matched]
  result["fallbacks"] = {"named": sorted(n for n, st in tuned.items() if st is None),
                         "random": sum(st is None for st in rand_tuned),
                         "isotropic": sum(st is None for st in iso_tuned),
                         "total": sum(st is None for st in all_settings)}
  result["natural_norms"] = {L: dirs[L]["natural_norms"] for L in layers}
  settings["isotropic"] = iso_tuned
  with open(f"{out}/records/steer_settings.json", "w") as f:
    json.dump(settings, f, default=str)
  with open(f"{out}/records/steer_test_whole_answer.json", "w") as f:
    json.dump(whole, f)
  return result
