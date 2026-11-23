# Worked-examples arms on the 42 TUNE cells (labels sha256 0b6f0feb...; selection on set B; tune scored once per run)

claude_examples lr chosen on selection set B: 1e-04 (selection soft regret {0.0001: 0.027019775898123804, 0.0003: 0.1706110221676228}); seeds completed: [0, 1, 2]; best epochs [4, 5, 2]; epoch-0 flags [False, False, False]

## Soft regret on tune cells (cell means, seeds averaged), by type

| Arm | all [95%] | below | at_or_above | no_cost | letter mass | cheapest-option mass below / at_or_above / no_cost | best epochs |
| --- | --- | --- | --- | --- | --- | --- | --- |
| plain | 0.657 [0.463, 0.865] | 1.376 | 0.391 | 0.204 | 0.81 | 0.04 / 0.12 / 0.08 |  |
| always-cheapest | 0.429 [0.195, 0.719] | 0.643 | 0.000 | 0.643 | nan | 1.00 / 1.00 / 1.00 |  |
| claude_examples (a) | 0.032 [0.016, 0.051] | 0.008 | 0.011 | 0.077 | 1.00 | 0.71 / 0.96 / 0.35 | 4,5,2 |
| cheapest_label (b) | 0.429 [0.195, 0.719] | 0.643 | 0.000 | 0.643 | 1.00 | 1.00 / 1.00 / 1.00 | 5 |
| shuffled_claude (c) | 0.695 [0.477, 0.950] | 1.338 | 0.164 | 0.581 | 1.00 | 0.49 / 0.86 / 0.73 | 2 |
| answer-trained ceiling lr 1e-04 | 0.026 [0.009, 0.054] | 0.002 | 0.053 | 0.022 | 1.00 | 0.71 / 0.52 / 0.31 | 5 |
| answer-trained ceiling lr 3e-04 | 0.118 [0.062, 0.190] | 0.133 | 0.149 | 0.073 | 1.00 | 0.74 / 0.45 / 0.31 | 4 |
| teacher-distil (earlier, 3 seeds) | 0.376 [0.242, 0.535] | 0.614 | 0.119 | 0.394 | 1.00 | 0.50 / 0.52 / 0.51 | 4,3,2 |

## Pass rule (GEN_EXAMPLES_PLAN.md, frozen): paired cell bootstrap, 10,000 resamples, seed 0, two-sided 95% percentile (lower = 2.5th percentile)

- 1. plain - a: +0.625 [+0.430, +0.836], lower bound > 0: **yes**
- 2. (b) - a: +0.397 [+0.171, +0.676], lower bound > 0: **yes**
- 3. always-cheapest - a: +0.397 [+0.171, +0.676], lower bound > 0: **yes**
- 4. plain - a on below cells (14): +1.368 [+1.140, +1.656], lower bound > 0: **yes**
- 5. type means (a) minus plain: below -1.368, at_or_above -0.380, no_cost -0.127 (each <= +0.05): **yes**
- 6. letter mass 1.00 vs 0.9 x plain 0.73: **yes**

**Owner's pass rule: PASSED** (mean over completed seeds [0, 1, 2])

## Tags (not part of the rule; they decide how a pass may be worded)

- T1a plain - a on the 26 non-overlapping cells: +0.668 [+0.416, +0.953], lower bound > 0: **yes**
- T1b (b) - a on the 26 non-overlapping cells: +0.577 [+0.224, +0.989], lower bound > 0: **yes**
- T2 plain - a (seeds 1-2): +0.616 [+0.420, +0.827], lower bound > 0: **yes**
- T2 (b) - a (seeds 1-2): +0.387 [+0.164, +0.665], lower bound > 0: **yes**
- T2 always-cheapest - a (seeds 1-2): +0.387 [+0.164, +0.665], lower bound > 0: **yes**
- T2 plain - a below (seeds 1-2): +1.366 [+1.138, +1.651], lower bound > 0: **yes**
- T3 (b) - a seed 0 (equal footing): +0.415 [+0.184, +0.700], lower bound > 0: **yes**
- T4 (b) - a on below cells: +0.635 [+0.068, +1.343], lower bound > 0: **yes**
- T4 (b) - a on no_cost cells: +0.566 [+0.258, +0.927], lower bound > 0: **yes**
- T4 (c) - a on below cells (differing labels): +1.330 [+0.967, +1.832], lower bound > 0: **yes**
- T4 (c) - a on no_cost cells (differing labels): +0.505 [+0.299, +0.759], lower bound > 0: **yes**
- T5 (a) minus ceiling at lr 1e-04: +0.006 [-0.019, +0.028]; mean <= 0.05: **yes**
- (a) vs earlier teacher-distil: teacher-distil minus (a) +0.344 [+0.218, +0.496]

## Slope of the expected offer on the stated cost over the 14 below cells (OLS; bootstrap interval over cells)

- plain: 0.32 [0.04, 0.71]
- always-cheapest: 0.06 [-0.32, 0.49]
- claude_examples (a): 0.76 [0.42, 0.99]
- cheapest_label (b): 0.06 [-0.32, 0.49]
- shuffled_claude (c): -0.16 [-0.57, 0.36]
- answer-trained ceiling lr 1e-04: 0.76 [0.43, 1.00]
- answer-trained ceiling lr 3e-04: 0.69 [0.39, 0.91]
- teacher-distil (earlier, 3 seeds): 0.26 [-0.11, 0.63]
- oracle (first best price): 0.76

## By label-key overlap with the 100 training cells (16 overlapping, 26 not): soft regret

| Arm | overlapping | non-overlapping |
| --- | --- | --- |
| plain | 0.564 | 0.714 |
| always-cheapest | 0.112 | 0.623 |
| claude_examples (a) | 0.009 | 0.046 |
| cheapest_label (b) | 0.113 | 0.623 |
| shuffled_claude (c) | 0.418 | 0.865 |
| answer-trained ceiling lr 1e-04 | 0.018 | 0.031 |
| answer-trained ceiling lr 3e-04 | 0.062 | 0.153 |
| teacher-distil (earlier, 3 seeds) | 0.147 | 0.516 |

## Per-run tune soft regret

- gen_cheapest_label_lr1e-04_s0: 0.429 (best epoch 5, selection 0.314, 2257 s)
- gen_claude_examples_lr1e-04_s0: 0.013 (best epoch 4, selection 0.027, 2257 s)
- gen_claude_examples_lr1e-04_s1: 0.026 (best epoch 5, selection 0.027, 2258 s)
- gen_claude_examples_lr1e-04_s2: 0.057 (best epoch 2, selection 0.067, 1866 s)
- gen_claude_examples_lr3e-04_s0: 0.119 (best epoch 1, selection 0.171, 1474 s)
- gen_shuffled_claude_lr1e-04_s0: 0.695 (best epoch 2, selection 0.574, 1867 s)
