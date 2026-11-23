"""PROTECTED payoff rule of the haggling task (ported verbatim from demo/gen_cases.py; unit-tested equal to refimpl.core)."""


def payoff(V, grid, C, prior, k) -> float:
  """Expected payoff of offer k. Stated cost C: V - k if k >= C else 0. No cost: the farm cost is uniform on the
  integers prior[0]..prior[1], so P(accept) = clamp((k - lo + 1) / (hi - lo + 1), 0, 1)."""
  if C is not None:
    return float(V - k) if k >= C else 0.0
  lo, hi = prior
  return (V - k) * min(1.0, max(0.0, (k - lo + 1) / (hi - lo + 1)))


def payoffs(case) -> list:
  return [payoff(case["V"], case["grid"], case["C"], case["prior"], k) for k in case["grid"]]
