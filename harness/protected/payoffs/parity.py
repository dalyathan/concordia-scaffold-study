"""PROTECTED payoff rule of the toy 'parity' smoke task: pick the option whose value equals the target mod m."""


def payoffs(case) -> list:
  return [1.0 if (v % case["modulus"]) == case["target"] else 0.0 for v in case["options"]]
