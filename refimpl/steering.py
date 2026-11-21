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
