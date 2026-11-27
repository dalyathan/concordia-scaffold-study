# Predictions for Llama 3.1 8B (written Nov 24 from the Gemma 2 9B results; committed before any Llama code)

Task: the same generated dataset, rendering, five option orders and two name variants (never variants 1-14), the same first-token letter scoring, the same 42 tune cells and selection set B. Model: Llama 3.1 8B Instruct (the instruct variant; if only the base model is available that is logged and every statement below is void for that model). Soft regret in coins, lower is better; "tune" only; no test set (test2_same, test2_newkey or earlier) is used for any of this. Each statement has a number and a direction; scoring is mechanical: HELD if the observed value is inside the range (or the direction and threshold hold), FAILED if outside, UNCLEAR if the 95% interval (bootstrap over (V, grid) groups) straddles a range edge. Probability statements get a Brier term only.

## What the Gemma results give as the reference (tune cells)
Plain 0.657 (below-resale cells 1.376, at-or-above 0.391, no-cost 0.204; slope of offer on stated cost 0.32); neutral text 0.735; our paragraph in the prompt (method_original) 0.369 (-0.29); the teacher paragraph in the prompt 0.390 (-0.27); steering failed (a push toward one answer letter, effects within the noise of random directions); examples learning curve 0.092, 0.042, 0.040, 0.032 at N = 10, 25, 50, 100; rule-trained students 0.34-0.38; always-cheapest 0.429; stated-cost rule 0.214. Gemma letter mass at the first token is >= 0.99.

## L1. Plain failure pattern
- L1a: plain soft regret on tune is 0.50-0.95 (point 0.72). Direction: worse than or similar to Gemma (0.657).
- L1b: the failure is concentrated where a cost is stated below resale: regret on below-resale cells is at least 2.5x the regret on no-cost cells, and at least 0.9.
- L1c: slope of the mean offer on stated cost (below-resale cells) is at most 0.45 (Gemma 0.32); direction: Llama also ignores the cost.
- L1d: first-token letter mass over the five letters is at least 0.90 (Gemma >= 0.99); probability 0.7 that it is >= 0.98.
- L1e: position bias is larger than Gemma's: the share of probability on the most favoured letter, averaged over cells and orders, is above 0.30 (uniform is 0.20). Probability 0.6.

## L2. In-prompt gains (same paragraphs, same cells; difference to plain, negative = better)
- L2a: our paragraph (method_original): -0.10 to -0.40 (point -0.22); direction: smaller gain than Gemma's -0.29 (probability 0.6).
- L2b: the teacher paragraph (frozen, teacher_method.txt): -0.08 to -0.38 (point -0.20); |teacher - our paragraph| <= 0.12 (probability 0.7).
- L2c: the same-length neutral text changes regret by no more than +-0.10.
- L2d: neither paragraph gets within 0.15 of the stated-cost rule (0.214) or of examples-trained adapters; i.e. the paragraph's own regret stays above 0.30. Probability 0.8.

## L3. Steering
- L3a: probability 0.80 that steering fails again, defined as: the best coherent order-averaged sentence vector (all layers and scales tried under the earlier steering protocol, selected on selection set B) improves tune soft regret by less than 0.10 versus plain, or does not beat a random direction of equal norm by more than 0.05.
- L3b: where steering moves the answer it does so mostly by pushing one letter: the per-order sentence vector's gain is at least 3x larger on the cells where the targeted letter is the best offer than on the others (direction only; probability 0.65).

## L4. Examples learning curve (same recipe: rank 4, alpha 8, q/k/v/o, lr 1e-4 unless the learning-rate sweep on selection set B at N = 100 says otherwise, 500 optimizer steps, early stopping on set B; Claude's frozen labels; 3 seeds; same nested subsets)
- L4a: examples-100 soft regret 0.02-0.15 (point 0.06).
- L4b: examples-25: 0.04-0.25 (point 0.11). examples-10: 0.12-0.50 (point 0.28). examples-50: 0.03-0.18 (point 0.08).
- L4c: the curve is monotone down with 0.03 tolerance from N = 50 to 100, and Llama needs at least as many cells as Gemma: the smallest N within 0.05 of examples-100 is >= 25 (probability 0.85) and <= 50 (probability 0.6).
- L4d: slope of the offer on stated cost for examples-100 at least 0.5 (Gemma 0.76); for examples-10 below 0.55 (probability 0.65).
- L4e: rule-trained students (teacher-distil, N = 100) stay above 0.20 and worse than examples-100 by at least 0.15 (probability 0.8).
- L4f: the cheapest-label control at N = 25 lands within 0.05 of always-cheapest (0.429).
- L4g: letter mass of every trained adapter at least 0.97.

## Known reasons these may fail
Different tokenizer and chat template change the first-token letter reading (a letter may be preceded by a space or period token); the Gemma recipe's lr and step count were chosen on Gemma; one subset draw; Llama could already be stronger at arithmetic than Gemma (plain well below 0.5), in which case L1a, L2 and L4 ranges shift down together and are reported as such, not re-fit.
