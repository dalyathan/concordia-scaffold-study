"""PROTECTED SCORER. Experiment code must not edit this directory.

harness/protected/LOCK.json holds the sha256 of every file here; tests/harness/test_protected.py and
harness.evaluate refuse to run if a hash changed without a DECISIONS.md entry that names the new hash.
Regret = best expected payoff minus the expected payoff of the model's answer distribution (coins; 0 is perfect)."""
from __future__ import annotations

TOL = 1e-12


def best_set(payoffs):
  best = max(payoffs)
  return best, [i for i, x in enumerate(payoffs) if abs(x - best) < TOL]


def soft_regret(payoffs, probs) -> float:
  """probs: probability of each option (same order as payoffs); must sum to ~1."""
  if len(payoffs) != len(probs):
    raise ValueError("payoffs and probs differ in length")
  s = sum(probs)
  if abs(s - 1.0) > 1e-6:
    raise ValueError(f"probabilities sum to {s}, not 1")
  return max(payoffs) - sum(p * x for p, x in zip(probs, payoffs))


def hard_regret(payoffs, probs) -> float:
  """Regret of the single most probable option (first index wins ties)."""
  top = max(range(len(probs)), key=lambda i: (probs[i], -i))
  return max(payoffs) - payoffs[top]


def score_case(payoffs, probs) -> dict:
  best, idx = best_set(payoffs)
  top = max(range(len(probs)), key=lambda i: (probs[i], -i))
  return {"soft_regret": soft_regret(payoffs, probs), "hard_regret": hard_regret(payoffs, probs),
          "top_option": top, "top_is_best": top in idx, "best_payoff": best, "best_options": idx}
