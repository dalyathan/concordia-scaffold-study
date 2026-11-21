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
               para, openings: Sequence[str], out: str, only: Sequence[str] | None = None):
  """Scores every condition (or only those in `only`, e.g. the pilot's N0/N1) in
  the five cyclic orders and stores activations."""
  orders = core.cyclic_orders()
  for p in prompts:
    conds = conditions.build_conditions(p, S, S_reason, offers, para, openings, lm.tok)
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


def run_leakage_audit(lm: LocalGemma2, prompts, S, S_reason, offers, para, openings, out: str):
  """Score the audit question for every N8 and N1s text (Protocol 9.2)."""
  for p in prompts:
    conds = conditions.build_conditions(p, S, S_reason, offers, para, openings, lm.tok)
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
