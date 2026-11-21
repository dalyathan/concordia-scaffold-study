"""First-token versus whole-answer scoring across the five option orders (one prompt)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from refimpl import core, phase3
from refimpl.local_gemma2 import LocalGemma2

import argparse
from refimpl import runtime
ap = argparse.ArgumentParser()
ap.add_argument("model")
ap.add_argument("--device", default="cpu", choices=("cpu", "cuda"))
args = ap.parse_args()
model, tok = runtime.load_gemma(args.model, args.device)
lm = LocalGemma2(model, tok, sequential=True)
p = core.Prompt(1, 5, "information", 3)
notes = "Question: What is Anya's best offer?\nAnswer: She can resell for 5 coins."
# Reports only the mean letter mass and first-token versus whole-answer top-choice
# agreement (no probabilities, offers or regret are printed).
masses, agree = [], 0
for i, order in enumerate(core.cyclic_orders()):
  pf, _, _, pw = phase3.score_prompt(lm, p, "Opening sentence number 0.", notes, order)
  masses.append(lm.last_letter_mass)
  agree += max(pf, key=pf.get) == max(pw, key=pw.get)
print(f"mean letter mass {sum(masses) / len(masses):.3f} "
      f"(range {min(masses):.3f}-{max(masses):.3f}); first-token vs whole-answer "
      f"top choice agree in {agree} of 5 orders")
