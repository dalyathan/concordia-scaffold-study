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


def projected_cell_sd(d: Mapping[str, float], prompts: Sequence[core.Prompt],
                      n_variants: int = 12) -> dict:
  """SD of cell means of a per-prompt difference d, projected from the variants
  observed (the pilot has 2 per cell) to n_variants per cell.

  Var(cell mean of m variants) = between-cell variance + within-cell variance / m.
  The within-cell variance is the mean over cells of the sample variance of d
  across that cell's variants; the between-cell variance is the variance of the
  observed cell means minus within / m_observed (floored at 0). The projection is
  sqrt(between + within / n_variants)."""
  by = collections.defaultdict(list)
  for p in prompts:
    if p.pid in d:
      by[p.cell].append(d[p.pid])
  cells = sorted(by, key=str)
  m_obs = float(np.mean([len(by[c]) for c in cells]))
  means = np.array([np.mean(by[c]) for c in cells])
  within = float(np.mean([np.var(by[c], ddof=1) for c in cells if len(by[c]) > 1]))
  observed = float(np.var(means, ddof=1))
  between = max(observed - within / m_obs, 0.0)
  return {"n_cells": len(cells), "variants_observed": m_obs, "sd_observed": observed ** 0.5,
          "within_var": within, "between_var": between,
          "sd_projected": (between + within / n_variants) ** 0.5}


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


def bootstrap_t_greater(x: Sequence[float], n: int = 10_000, seed: int = SEED) -> float:
  """Skew-robust sensitivity for a mean > 0: cell bootstrap-t. The studentised
  mean t = mean / (sd / sqrt(k)) is compared with the bootstrap distribution of
  (mean* - mean) / (sd* / sqrt(k)); p = (1 + count(t* >= t)) / (1 + n)."""
  x = np.asarray(x, dtype=float)
  k = len(x)
  sd = x.std(ddof=1)
  if sd == 0:
    return 0.0 if x.mean() > 0 else 1.0
  t = x.mean() / (sd / np.sqrt(k))
  rng = np.random.default_rng(seed)
  b = rng.choice(x, size=(n, k), replace=True)
  sb = b.std(axis=1, ddof=1)
  tb = np.where(sb > 0, (b.mean(axis=1) - x.mean()) / np.where(sb > 0, sb, 1) * np.sqrt(k), 0.0)
  return float((1 + np.sum(tb >= t)) / (1 + n))


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


def bootstrap_equivalence_p(x: Sequence[float], bound: float, n: int = 10_000,
                            seed: int = SEED) -> float:
  """Two one-sided tests (TOST) of |mean| < bound by a cell bootstrap: the larger
  of P*(mean* <= -bound) and P*(mean* >= bound), each (1 + count) / (1 + n). At
  alpha = 0.05 this is equivalent to the 90% percentile interval lying inside
  +-bound; as a p-value it can enter a multiplicity correction."""
  rng = np.random.default_rng(seed)
  x = np.asarray(x, dtype=float)
  means = rng.choice(x, size=(n, len(x)), replace=True).mean(axis=1)
  return float(max((1 + np.sum(means <= -bound)) / (1 + n), (1 + np.sum(means >= bound)) / (1 + n)))


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


CONFIRMATORY_TESTS = ("A1", "A2", "A3", "B1", "B2", "B3", "R1", "R2", "R3", "K1")


def confirmatory_family(extension: bool) -> tuple[str, ...]:
  """The Holm family (Protocol 1.3). K2 is confirmatory only when the V = 7, 8
  extension is in force (19 unique-best test cells); with 12 cells even steering to
  every cell's best offer cannot pass its control comparisons at the Holm level,
  so K2 then moves to the secondary (BH) family."""
  return CONFIRMATORY_TESTS + (("K2",) if extension else ())


def confirmatory_verdicts(tests: Mapping[str, dict]) -> dict[str, str]:
  """tests: name -> {'p', 'p_reverse', and 'effect_cells' or 'p_equiv', 'sesoi'?}.

  Holm at 0.05 for the confirmatory direction, a separate Holm at 0.01 for the
  reverse direction, and a third Holm at 0.05 over the equivalence (TOST) p-values
  of the tests that are neither supported nor reversed. A test without an
  equivalence p-value can only be supported, reversed or inconclusive."""
  passed = holm({k: v["p"] for k, v in tests.items()}, ALPHA)
  passed_r = holm({k: v["p_reverse"] for k, v in tests.items()}, ALPHA_REVERSE)
  p_eq = {}
  for k, v in tests.items():
    if passed[k] or passed_r[k]:
      continue
    if v.get("p_equiv") is not None:
      p_eq[k] = v["p_equiv"]
    elif v.get("effect_cells") is not None:
      p_eq[k] = bootstrap_equivalence_p(v["effect_cells"], v.get("sesoi", SESOI_REGRET))
  passed_eq = holm(p_eq, ALPHA) if p_eq else {}
  out = {}
  for k in tests:
    if passed[k]:
      out[k] = "supported"
    elif passed_r[k]:
      out[k] = "reversed"
    elif passed_eq.get(k):
      out[k] = "equivalent"
    else:
      out[k] = "inconclusive"
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


def _rank_residuals(v, rz):
  rv = stats.rankdata(np.asarray(v, dtype=float))
  Z = np.column_stack([np.ones_like(rz), rz])
  return rv - Z @ np.linalg.lstsq(Z, rv, rcond=None)[0]


def _corr_rows(E, ey):
  """Pearson correlation of each row of E with ey (0 where a row is constant)."""
  E = E - E.mean(axis=-1, keepdims=True)
  e = ey - ey.mean()
  num = E @ e
  den = np.sqrt((E * E).sum(axis=-1) * (e @ e))
  return np.where(den > 0, num / np.where(den > 0, den, 1.0), 0.0)


def partial_spearman_perm(x, y, z, n_perm: int = 100_000, seed: int = SEED
                          ) -> tuple[float, float, float]:
  """Partial Spearman correlation of x and y given z, with a permutation p-value.

  Ranks (average ranks for ties); x's and y's ranks are residualised on z's rank;
  the statistic is the Pearson correlation of the residuals. Null distribution:
  the residuals of x are permuted across cells (Kennedy's method for partial
  correlation), n_perm Monte Carlo permutations from PCG64(seed). Returns (rho,
  p for rho > 0, p for rho < 0), each (1 + count) / (1 + n_perm)."""
  rz = stats.rankdata(np.asarray(z, dtype=float))
  ex, ey = _rank_residuals(x, rz), _rank_residuals(y, rz)
  if ex.std() == 0 or ey.std() == 0:
    return 0.0, 1.0, 1.0
  r = float(_corr_rows(ex[None, :], ey)[0])
  rng = np.random.Generator(np.random.PCG64(seed))
  perm = np.argsort(rng.random((n_perm, len(ex))), axis=1)
  null = _corr_rows(ex[perm], ey)
  return (r, float((1 + np.sum(null >= r - 1e-12)) / (1 + n_perm)),
          float((1 + np.sum(null <= r + 1e-12)) / (1 + n_perm)))


def paired_swap_test(a, c, o, z, max_exact: int = 20, n_mc: int = 100_000,
                     seed: int = SEED) -> tuple[float, float, float]:
  """Does the steering shift a track o (given z) more than a control shift c?

  Statistic: partial Spearman(a; o | z) - partial Spearman(c; o | z). Paired
  permutation test: under the null that a cell's steered and control shifts are
  exchangeable, every one of the 2^n within-cell swaps of a and c is equally
  likely. Exact enumeration for n <= max_exact cells (K2: 12 or 19); otherwise
  n_mc random swap patterns from PCG64(seed) plus the identity. Returns
  (difference, p for difference > 0, p for < 0), each the share of assignments
  (the identity included) at least as extreme."""
  a, c = np.asarray(a, dtype=float), np.asarray(c, dtype=float)
  rz = stats.rankdata(np.asarray(z, dtype=float))
  ey = _rank_residuals(o, rz)
  n = len(a)
  if n <= max_exact:
    swaps = np.array(list(itertools.product((False, True), repeat=n)))     # 2^n x n
  else:
    rng = np.random.Generator(np.random.PCG64(seed))
    swaps = np.vstack([np.zeros((1, n), bool), rng.random((n_mc, n)) < 0.5])
  A = np.where(swaps, c, a)
  C = np.where(swaps, a, c)
  Z = np.column_stack([np.ones_like(rz), rz])
  H = Z @ np.linalg.pinv(Z)                              # projection onto [1, rank z]
  RA, RC = stats.rankdata(A, axis=1), stats.rankdata(C, axis=1)
  EA, EC = RA - RA @ H.T, RC - RC @ H.T
  d = _corr_rows(EA, ey) - _corr_rows(EC, ey)
  d0 = float(d[0])                                       # first row: no swaps
  return d0, float(np.mean(d >= d0 - 1e-12)), float(np.mean(d <= d0 + 1e-12))


def calibration_test(prompts: Sequence[core.Prompt],
                     base: Mapping[str, Mapping[int, float]],
                     steered: Mapping[str, Mapping[int, float]],
                     extra_nulls: Mapping[str, Mapping[str, Mapping[int, float]]] = {},
                     n_boot: int = 10_000, seed: int = 11, n_perm: int = 100_000) -> dict:
  """K2 on the test cells whose best offer is a single price (core.has_unique_best).

  Statistic: partial Spearman correlation, across cells, of the steering shift s
  with the best offer o, controlling for the unsteered expected offer b. Passes
  if it is > 0 (permutation test, partial_spearman_perm) and exceeds the partial
  correlation of every control (exact paired swap test over cells,
  paired_swap_test): tilt (matched mean signed shift), attractor towards each
  fixed price (the strongest of the five is used; matched mean absolute shift),
  flatten (matched mean absolute shift), and extra_nulls. The 90% interval for the
  equivalence verdict is a cell bootstrap of the difference against the strongest
  control (descriptive; n_boot resamples)."""
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
  rho, p_rho, p_rho_neg = partial_spearman_perm(a, o, z, n_perm=n_perm, seed=seed)
  ctrl_rho = {k: partial_spearman(v, o, z)[0] for k, v in ctrl.items()}
  best_att = max((k for k in ctrl if k.startswith("attractor")), key=ctrl_rho.get)
  used = [k for k in ctrl if not k.startswith("attractor")] + [best_att]
  swap = {k: paired_swap_test(a, ctrl[k], o, z) for k in used}
  p_vs = {k: v[1] for k, v in swap.items()}
  p_vs_rev = {k: v[2] for k, v in swap.items()}
  strongest = max(used, key=ctrl_rho.get)               # equivalence vs strongest control
  rng = np.random.default_rng(seed)
  boot = []
  for _ in range(n_boot):
    idx = rng.integers(0, len(cells), len(cells))
    boot.append(partial_spearman(a[idx], o[idx], z[idx])[0]
                - partial_spearman(ctrl[strongest][idx], o[idx], z[idx])[0])
  lo, hi = np.quantile(boot, [0.05, 0.95])
  boot = np.asarray(boot)
  p_equiv = float(max((1 + np.sum(boot <= -SESOI_K2)) / (1 + n_boot),
                      (1 + np.sum(boot >= SESOI_K2)) / (1 + n_boot)))
  return {"n_cells": len(cells), "rho_partial": rho, "p_rho": p_rho,
          "control_rho": {k: ctrl_rho[k] for k in used}, "p_vs_controls": p_vs,
          "difference_vs_controls": {k: v[0] for k, v in swap.items()},
          "p": iut(p_rho, *p_vs.values()),
          "p_reverse": reverse_p(p_rho_neg, *p_vs_rev.values()),
          "interval": (float(lo), float(hi)), "p_equiv": p_equiv, "sesoi": SESOI_K2}


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
