# Predictions for Qwen 2.5 7B Instruct (written 2026-11-28 from the Gemma 2 9B and Llama 3.1 8B tune results; committed before any Qwen code or run)

Task: the same generated haggling dataset, rendering, five cyclic option orders and the stored name variants, the same 42 tune cells (84 cases) and selection set B, first-token letter scoring through the harness (readout parity with the stored Gemma scores passed on the A40, DECISIONS.md L39). Model: `Qwen/Qwen2.5-7B-Instruct` (instruct; if only another variant is usable, that is logged and every statement below is void). Soft regret in coins, lower is better; tune only; no test split is opened. Scoring is mechanical, as for Llama: HELD if the observed value is inside the range (or the direction and threshold hold), FAILED if outside, UNCLEAR if the 95% cluster-bootstrap interval over (V, grid) groups straddles a range edge; probability statements get a Brier term only. If the readout needs the "Answer: (" assistant prefix (decided on train cases only, by the format-only rule fixed in QWEN_PLAN.md), every statement except Q1d is scored under the prefixed readout, and Q1d is scored on the unprefixed one.

## References (tune; soft regret)

| | Gemma 2 9B | Llama 3.1 8B | uniform guessing |
| --- | --- | --- | --- |
| plain (below / at or above / no cost) | 0.657 (1.376 / 0.391 / 0.204) | 1.184 (1.828 / 1.278 / 0.446) | 1.260 (1.871 / 1.329 / 0.580) |
| written rule (method paragraph) / Claude's lesson / neutral / wrong rule | 0.369 / 0.390 / 0.735 / 0.618 | 0.773 / 0.930 / 1.158 / 0.611 | |
| examples-100 (3 seeds) / examples-25 | 0.032 / 0.043 | 0.048 / 0.086 | |
| cheapest-label N=25, N=100 / scrambled N=100 | 0.429, 0.429 / 0.695 | 0.429, 0.429 / 0.659 | |
| slope of offer on stated cost, below cells: plain / examples-100 | 0.32 / 0.76 | 0.26 / 0.74 | 0 |
| first-token letter mass (unprefixed) | >= 0.99 | 0.487 (0.998 with "Answer: (") | |
| top-letter share (position bias) | - | 0.391 | 0.20 |
| free answer agrees with the forced letter: plain / after examples-100 | about 1/3 (written offer vs pick) | 0.53 / 0.90-0.95 | 0.20 |
| planted no-cost case, examples-100 adapters (mass on the best offer; bar 0.9) | 0.20 / 0.29 / 0.57 | 0.40 / 0.13 / 0.36 | |
| stated-cost rule / always-cheapest | 0.214 / 0.429 | | |

## Q1. Plain failure pattern
- **Q1a** plain soft regret on tune: 0.45-1.10 (point 0.75): between Gemma and Llama.
- **Q1b** by type: below 0.80-1.80 (point 1.20); at or above 0.20-1.20 (point 0.60); no cost 0.08-0.50 (point 0.28). Below is the worst type, and at least 2x the no-cost regret.
- **Q1c** slope of the expected offer on stated cost (below cells): at most 0.50 (point 0.30). Qwen also largely ignores the stated cost.
- **Q1d** unprefixed first-token letter mass: P(>= 0.95) = 0.5. With the prefix, if it is needed: >= 0.95 (probability 0.9).
- **Q1e** top-letter share above 0.30: probability 0.5.
- **Q1f** plain beats uniform guessing by at least 0.10 overall (plain <= 1.16): probability 0.65.

## Q2. Prompt arms (difference to plain, negative = better)
- **Q2a** written rule (our method paragraph): -0.10 to -0.50 (point -0.30).
- **Q2b** Claude's lesson (teacher paragraph): -0.05 to -0.45 (point -0.20); the lesson helps less than the written rule (probability 0.65).
- **Q2c** neutral text: |difference| <= 0.10.
- **Q2d** the wrong rule helps (wrong minus plain < 0, interval below 0): probability 0.6.
- **Q2e** wrong rule vs written rule: (wrong minus written) in [-0.25, +0.35] (point +0.10); the wrong rule is at least as good as the written rule (difference <= 0): probability 0.35.
- **Q2f** neither paragraph's regret gets below 0.30: probability 0.7.

## Q3. LoRA on Claude's worked examples (the Llama recipe; lr by the same rule)
- **Q3a** examples-100 (3-seed mean): 0.01-0.10 (point 0.04); every seed below plain (probability 0.95).
- **Q3b** examples-25 (one seed): 0.02-0.15 (point 0.07); within 0.05 of examples-100: probability 0.75.
- **Q3c** cheapest-label N=25 and N=100: each within 0.05 of always-cheapest (0.429): probability 0.9.
- **Q3d** scrambled N=100: 0.45-1.00 (point 0.68), and at least 0.15 worse than examples-100 (probability 0.9).
- **Q3e** slope of the offer on stated cost, examples-100: at least 0.50 (point 0.72).
- **Q3f** letter mass of every trained adapter at least 0.97 (under the readout used).
- **Q3g** the lr rule picks 1e-4: probability 0.6.

## Q4. Planted known-answer cases (4 cases; pass = top option acceptable and >= 0.9 mass on acceptable options)
- **Q4a** plain passes at most 2 of 4: probability 0.85.
- **Q4b** examples-100 adapters fail planted no-cost in at least 2 of 3 seeds: probability 0.8.
- **Q4c** examples-100 adapters pass the other three planted cases in every seed: probability 0.7.

## Q5. Free-answer agreement (the forced letter vs Qwen's own greedy free answer, 20 train cases outside training and selection x 5 orders, same parser as for Llama)
- **Q5a** plain: 0.35-0.80 (point 0.55).
- **Q5b** after examples-100 (each seed): at least 0.85 (probability 0.75).

## Known reasons these may fail
Qwen 2.5 is strong at arithmetic for its size, so plain could be well below Llama and near Gemma or better; then Q1 and Q2 shift down together and are reported as failed, not re-fit. Its chat template always has a system message; its tokenizer may merge "(a" or " a" differently, which changes the first-token readout and possibly the need for the prefix. The recipe (lr, steps, rank) was chosen on Gemma; one training subset draw; three seeds.
