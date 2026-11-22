"""steercheck: one control table for candidate steering vectors (or any intervention).

Model-agnostic. You supply
  score(case, steer, orders) -> (probs, letter_mass)    probs: {option: probability};
                                                        steer: None or (layer, vector)
  best(case) -> set of best options;  value(case, option) -> payoff;  cell(case) -> id
  candidate vectors {name: {layer: vector}} (negated copies are added automatically)
and get, on the cases given (cell = unit of analysis, cell-bootstrap intervals):
  plain; each vector and its negation tuned at full budget; the first vector tuned at
  matched budget beside the reference directions (random, Gaussian) tuned the same way,
  with its rank among them; the best constant shift (a tilt exp(beta * option));
  the partial Spearman correlation of each vector's per-cell shift in expected option
  with the best option, given the plain expected option.

  python demo/steercheck.py --results demo_out/tune_results.json   print a saved table
  python demo/steercheck.py --toy                                  run the toy example
"""
from __future__ import annotations

import argparse
import json
import math
from typing import Callable, Mapping, Sequence

import numpy as np

RED, GREEN, RESET = "\033[31m", "\033[32m", "\033[0m"


# ---------------------------------------------------------------- helpers
def expected(probs: Mapping) -> float:
  return float(sum(float(k) * v for k, v in probs.items()))


def soft_regret(probs: Mapping, case, best, value) -> float:
  top = max(value(case, b) for b in best(case))
  return top - sum(v * value(case, k) for k, v in probs.items())


def tilt(probs: Mapping, beta: float) -> dict:
  w = {k: v * math.exp(beta * float(k)) for k, v in probs.items()}
  z = sum(w.values())
  return {k: x / z for k, x in w.items()}


def cell_means(values: Mapping, cell_of: Mapping) -> dict:
  acc: dict = {}
  for key, v in values.items():
    acc.setdefault(cell_of[key], []).append(v)
  return {c: float(np.mean(v)) for c, v in acc.items()}


def cell_bootstrap(per_cell: Mapping, n: int = 2000, seed: int = 0) -> tuple[float, float]:
  x = np.array(list(per_cell.values()), dtype=float)
  rng = np.random.default_rng(seed)
  m = rng.choice(x, size=(n, len(x)), replace=True).mean(1)
  return float(np.quantile(m, 0.025)), float(np.quantile(m, 0.975))


def partial_spearman(x, y, z, n_perm: int = 10_000, seed: int = 11) -> tuple[float, float]:
  """Partial Spearman of x and y given z, with a one-sided permutation p (> 0)."""
  from scipy import stats
  rz = stats.rankdata(z)
  Z = np.column_stack([np.ones_like(rz), rz])
  res = lambda v: stats.rankdata(v) - Z @ np.linalg.lstsq(Z, stats.rankdata(v), rcond=None)[0]
  ex, ey = res(np.asarray(x, float)), res(np.asarray(y, float))
  if ex.std() == 0 or ey.std() == 0:
    return 0.0, 1.0
  r = float(np.corrcoef(ex, ey)[0, 1])
  rng = np.random.default_rng(seed)
  null = np.array([np.corrcoef(rng.permutation(ex), ey)[0, 1] for _ in range(n_perm)])
  return r, float((1 + np.sum(null >= r - 1e-12)) / (1 + n_perm))


# ----------------------------------------------------------------- tuning
class MemoryCheckpoint:
  """Per-grid-point results: (name, budget, layer, alpha) -> {case key: (probs, mass)}.
  Subclass and override put() to persist (see demo/tune_job.py: JSONL, one line per
  finished point, so an interruption loses at most the point being computed)."""

  def __init__(self):
    self.data: dict = {}

  def get(self, key):
    return self.data.get(key)

  def put(self, key, value):
    self.data[key] = value


def _point(score, cases, vec, layer, alpha, orders_for, checkpoint, name, budget, case_key):
  key = (name, budget, layer, float(alpha))
  if checkpoint is not None:
    hit = checkpoint.get(key)
    if hit is not None:
      return {c: hit[case_key(c)] for c in cases}
  out = {c: score(c, (layer, alpha * vec[layer]), orders_for(c)) for c in cases}
  if checkpoint is not None:
    checkpoint.put(key, {case_key(c): out[c] for c in cases})
  return out


def tune(score, cases, vec: Mapping, grid: Sequence[tuple], orders_for: Callable,
         best, value, cell_of, base: Mapping, coherence: float = 0.9, checkpoint=None,
         name: str = "", budget: str = "", case_key: Callable = str) -> dict:
  """Best coherent (layer, alpha) by mean cell soft regret; 'no steering' always an
  option (ties: no steering, then smaller alpha, then earlier layer). Coherent: mean
  letter mass at least `coherence` x the plain mean. base: case -> (probs, mass)."""
  plain_reg = np.mean(list(cell_means({c: soft_regret(base[c][0], c, best, value) for c in cases},
                                      cell_of).values()))
  plain_mass = np.mean([base[c][1] for c in cases])
  best_setting = {"layer": None, "alpha": 0.0, "mean_cell_regret": float(plain_reg), "mass_ratio": 1.0}
  tried = []
  for layer, alpha in grid:
    if layer is None or alpha == 0:
      continue
    out = _point(score, cases, vec, layer, alpha, orders_for, checkpoint, name, budget, case_key)
    reg = float(np.mean(list(cell_means({c: soft_regret(out[c][0], c, best, value) for c in cases},
                                        cell_of).values())))
    ratio = float(np.mean([out[c][1] for c in cases]) / plain_mass) if plain_mass > 0 else 0.0
    tried.append({"layer": layer, "alpha": alpha, "mean_cell_regret": reg, "mass_ratio": ratio})
    if ratio >= coherence and reg < best_setting["mean_cell_regret"] - 1e-12:
      best_setting = tried[-1]
  return {"chosen": best_setting, "tried": tried}


def evaluate(score, cases, vec, setting, orders_for, checkpoint=None, name="", budget="",
             case_key: Callable = str):
  if setting["layer"] is None:
    return None
  return _point(score, cases, vec, setting["layer"], setting["alpha"], orders_for, checkpoint,
                name, budget, case_key)


def run_controls(score, cases: Sequence, best, value, cell, vectors: Mapping[str, Mapping],
                 grid: Sequence[tuple], full_orders: Callable, matched_orders: Callable,
                 reference: Mapping[str, Mapping] = {}, n_boot: int = 2000,
                 log: Callable = print, negate: Sequence[str] | None = None,
                 checkpoint=None, case_key: Callable = str) -> dict:
  """The whole control table. vectors: full-budget candidates (the first is also run
  at matched budget); reference: directions tuned only at matched budget (random,
  Gaussian), against which the matched first vector is ranked."""
  cell_of = {c: cell(c) for c in cases}
  base_full = {c: score(c, None, full_orders(c)) for c in cases}
  base_matched = {c: score(c, None, matched_orders(c)) for c in cases}
  rows, detail = [], {}
  def row(name, budget, base, out, setting):
    probs = {c: (out[c][0] if out else base[c][0]) for c in cases}
    reg = {c: soft_regret(probs[c], c, best, value) for c in cases}
    reg0 = {c: soft_regret(base[c][0], c, best, value) for c in cases}
    hard = {}
    for c in cases:
      top = max(probs[c], key=lambda k: (probs[c][k], -float(k)))
      hard[c] = max(value(c, b) for b in best(c)) - value(c, top)
    red_cells = cell_means({c: reg0[c] - reg[c] for c in cases}, cell_of)
    cells_reg = cell_means(reg, cell_of)
    # Partial Spearman on cells with a single best option.
    ub = [c for c in cases if len(best(c)) == 1]
    s = cell_means({c: expected(probs[c]) - expected(base[c][0]) for c in ub}, cell_of)
    o = cell_means({c: float(next(iter(best(c)))) for c in ub}, cell_of)
    b = cell_means({c: expected(base[c][0]) for c in ub}, cell_of)
    ks = sorted(s)
    rho, p_rho = (partial_spearman([s[k] for k in ks], [o[k] for k in ks], [b[k] for k in ks])
                  if out and len(ks) >= 4 else (float("nan"), float("nan")))
    r = {"name": name, "budget": budget,
         "layer": setting.get("layer") if setting else None,
         "alpha": setting.get("alpha") if setting else None,
         "soft_regret": float(np.mean(list(cells_reg.values()))),
         "soft_regret_ci": cell_bootstrap(cells_reg, n_boot),
         "reduction": float(np.mean(list(red_cells.values()))),
         "reduction_ci": cell_bootstrap(red_cells, n_boot),
         "hard_regret": float(np.mean(list(cell_means(hard, cell_of).values()))),
         "mass_ratio": setting.get("mass_ratio", 1.0) if setting else 1.0,
         "partial_spearman": rho, "partial_spearman_p": p_rho, "n_cells": len(cells_reg)}
    rows.append(r)
    return r
  row("plain", "full", base_full, None, None)
  negate = list(vectors) if negate is None else list(negate)
  for name, vec in vectors.items():
    for sign, nm in ((1.0, name), (-1.0, f"-{name}")):
      if sign < 0 and name not in negate:
        continue
      v = {L: sign * x for L, x in vec.items()}
      ck = dict(checkpoint=checkpoint, name=nm, budget="full", case_key=case_key)
      t = tune(score, cases, v, grid, full_orders, best, value, cell_of, base_full, **ck)
      detail[nm] = t
      row(nm, "full", base_full, evaluate(score, cases, v, t["chosen"], full_orders, **ck),
          t["chosen"])
      log(f"tuned {nm}: {t['chosen']}")
  first = next(iter(vectors))
  ck = dict(checkpoint=checkpoint, name=first, budget="matched", case_key=case_key)
  t = tune(score, cases, vectors[first], grid, matched_orders, best, value, cell_of, base_matched, **ck)
  detail[f"{first}@matched"] = t
  m = row(f"{first}", "matched", base_matched,
          evaluate(score, cases, vectors[first], t["chosen"], matched_orders, **ck), t["chosen"])
  ref_red = {}
  for name, vec in reference.items():
    ck = dict(checkpoint=checkpoint, name=name, budget="matched", case_key=case_key)
    t = tune(score, cases, vec, grid, matched_orders, best, value, cell_of, base_matched, **ck)
    detail[name] = t
    rr = row(name, "matched", base_matched,
             evaluate(score, cases, vec, t["chosen"], matched_orders, **ck), t["chosen"])
    ref_red[name] = rr["reduction"]
    log(f"tuned reference {name}: {t['chosen']}")
  # Best constant shift (no model), fitted on the same cases.
  betas = np.round(np.arange(-6, 6.001, 0.05), 2)
  def shift_loss(bt):
    return np.mean(list(cell_means({c: soft_regret(tilt(base_full[c][0], bt), c, best, value)
                                    for c in cases}, cell_of).values()))
  beta = float(min(betas, key=lambda bt: (shift_loss(bt), abs(bt))))
  shifted = {c: (tilt(base_full[c][0], beta), base_full[c][1]) for c in cases}
  row(f"const shift b={beta:+.2f}", "offline", base_full, shifted, {"layer": None})
  summary = {}
  if ref_red:
    summary["matched_rank_p"] = (1 + sum(v >= m["reduction"] for v in ref_red.values())) / (1 + len(ref_red))
    summary["n_reference"] = len(ref_red)
  return {"rows": rows, "summary": summary, "detail": detail,
          "note": "settings tuned and evaluated on the same cases (in-sample)"}


# ------------------------------------------------------------------ tables
def _reg(x, colour):
  if x is None:
    return "  -  "
  s = f"{x:5.2f}"
  return ((RED if x > 1e-9 else GREEN) + s + RESET) if colour else s


def format_table(result: Mapping, colour: bool = True, width: int = 80,
                 max_reference: int = 4) -> list[str]:
  """The control table, <= 80 columns. Reference rows beyond max_reference are
  summarised by their rank statistic."""
  out = ["row                   budget   L alpha  regret [95% CI]    reduce   rho",
         "-" * 74]
  refs = 0
  for r in result["rows"]:
    is_ref = r["budget"] == "matched" and (r["name"].startswith("random") or r["name"].startswith("gauss"))
    if is_ref:
      refs += 1
      if refs > max_reference:
        continue
    L = "-" if r["layer"] is None else str(r["layer"])
    a = "-" if not r["alpha"] else f"{r['alpha']:g}"
    lo, hi = r["soft_regret_ci"]
    rho = "" if r["partial_spearman"] != r["partial_spearman"] else f"{r['partial_spearman']:+.2f}"
    out.append(f"{r['name'][:21]:<21} {r['budget']:<8} {L:>2} {a:>5}  {_reg(r['soft_regret'], colour)}"
               f" [{lo:4.2f},{hi:4.2f}] {r['reduction']:+6.2f} {rho:>5}")
  s = result.get("summary", {})
  if refs > max_reference:
    out.append(f"... {refs - max_reference} more reference directions")
  if "matched_rank_p" in s:
    out.append(f"matched-budget rank among {s['n_reference']} reference directions: "
               f"p = {s['matched_rank_p']:.3f}")
  out.append(result.get("note", ""))
  return out


def format_session_table(rows: list[dict], colour: bool = True, max_lines: int = 23) -> list[str]:
  """floor.py's results table: every row kept, including failures; newest rows if
  there are too many for one screen (all rows stay in the session log)."""
  head = [" #  case                       condition         offer best  regret   sec"]
  body = []
  for r in rows:
    best = ",".join(map(str, r["best"]))
    offer = "FAIL" if not r["ok"] else str(r["offer"])
    sec = "  -" if r["sec"] is None else f"{r['sec']:5.1f}"
    body.append(f"{r['n']:>2}  {r['case']:<26} {r['condition'][:17]:<17} {offer:>5} {best:<5}"
                f" {_reg(r['regret'], colour)} {sec}")
  if not body:
    return head + ["(no rows yet)"]
  hidden = max(0, len(body) - (max_lines - 1))
  return head + ([f"... {hidden} earlier rows (all kept in the log)"] if hidden else []) + body[hidden:]


# --------------------------------------------------------------------- toy
def toy(seed: int = 0) -> dict:
  """A toy model: options 1-5; the 'model' prefers option 2 whatever the case, and a
  steering vector along dimension 0 pulls it towards each case's best option."""
  rng = np.random.default_rng(seed)
  cases = [(i, int(rng.integers(1, 6))) for i in range(40)]         # (id, best option)
  def score(case, steer, orders):
    _, b = case
    a = 0.0 if steer is None else float(steer[1][0])
    logits = {k: -abs(k - 2) * 1.5 - a * abs(k - b) for k in range(1, 6)}
    m = max(logits.values())
    w = {k: math.exp(v - m) for k, v in logits.items()}
    z = sum(w.values())
    return {k: v / z for k, v in w.items()}, 0.8
  best = lambda c: {c[1]}
  value = lambda c, k: 1.0 if k == c[1] else 0.0
  cell = lambda c: c[1]
  vec = {0: np.array([1.0, 0.0])}
  ref = {f"random {i}": {0: np.array([float(rng.normal()) * 0.1, 1.0])} for i in range(5)}
  grid = [(None, 0.0)] + [(0, a) for a in (0.5, 1.0, 2.0, 4.0)]
  return run_controls(score, cases, best, value, cell, {"toy": vec}, grid,
                      lambda c: [0], lambda c: [0], ref, n_boot=200, log=lambda *a: None)


def main():
  ap = argparse.ArgumentParser(description="steercheck: one control table for steering vectors")
  ap.add_argument("--results", help="a saved run_controls result (JSON) to print")
  ap.add_argument("--toy", action="store_true", help="run the toy example")
  ap.add_argument("--no-colour", action="store_true")
  args = ap.parse_args()
  if args.toy:
    res = toy()
  elif args.results:
    res = json.load(open(args.results))
  else:
    return ap.print_help()
  print("\n".join(format_table(res, colour=not args.no_colour)))


if __name__ == "__main__":
  main()
