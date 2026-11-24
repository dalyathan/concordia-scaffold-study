# Follow-up after gate G2 (post hoc, CPU, tune cells only)

## A. Tune cells whose decision problem is not in the N = 100 training subset (26 cells of 42)

| Arm | soft regret [95% by (V, grid)] on these cells |
| --- | --- |
| plain | 0.714 [0.485, 1.003] |
| always-cheapest | 0.623 [0.200, 1.174] |
| stated-cost rule | 0.315 [0.074, 0.681] |
| examples-10 | 0.137 [0.054, 0.241] |
| examples-25 | 0.055 [0.012, 0.108] |
| examples-50 | 0.050 [0.020, 0.092] |
| examples-100 | 0.046 [0.018, 0.085] |
| rule-soft-25 | 0.519 [0.295, 0.810] |
| rule-soft-100 (3 seeds) | 0.516 [0.291, 0.813] |
| rule-hard-25 | 0.484 [0.298, 0.707] |
| rule-hard-100 | 0.472 [0.275, 0.731] |
| cheapest-label-25 | 0.623 [0.200, 1.174] |

Comparisons on these cells (first minus second):

- examples-10 - examples-100: +0.091 [+0.032, +0.160]
- examples-25 - examples-100: +0.009 [-0.015, +0.032]
- examples-50 - examples-100: +0.004 [-0.012, +0.026]
- rule-soft-25 - examples-25: +0.464 [+0.263, +0.735]
- rule-hard-25 - examples-25: +0.428 [+0.265, +0.624]
- rule-soft-100 (3 seeds) - examples-100: +0.470 [+0.263, +0.747]
- rule-hard-100 - examples-100: +0.426 [+0.250, +0.658]
- rule-hard-25 - rule-soft-25: -0.036 [-0.145, +0.048]
- rule-hard-100 - rule-soft-100 seed 0: -0.048 [-0.143, +0.024]

## B. Seed-and-cluster bootstrap and per-seed counts (examples-N minus examples-100)

Per-seed tune soft regret and whether it is within 0.05 of the examples-100 3-seed mean (0.032):

- examples-10: seeds 0.071, 0.151, 0.054; within 0.05 of examples-100 mean: 2 of 3
- examples-25: seeds 0.043, 0.037, 0.045; within 0.05 of examples-100 mean: 3 of 3
- examples-50: seeds 0.014, 0.028, 0.077; within 0.05 of examples-100 mean: 3 of 3
- examples-100: seeds 0.013, 0.026, 0.057; within 0.05 of examples-100 mean: 3 of 3

- examples-10 - examples-100, seeds resampled with clusters: +0.060 [+0.000, +0.156]; share of resamples with difference <= 0.05: 0.44
- examples-25 - examples-100, seeds resampled with clusters: +0.010 [-0.020, +0.044]; share of resamples with difference <= 0.05: 0.99
- examples-50 - examples-100, seeds resampled with clusters: +0.008 [-0.036, +0.055]; share of resamples with difference <= 0.05: 0.97

## C. Corrected tally (probability statements scored by Brier only, as PREDICTIONS.md says)

HELD 23, FAILED 3 (P1a, P1b, P6c), UNCLEAR 0; Brier statements P2a-c, P8b listed separately (mean 0.124 over 4).

## D. Hard vs soft targets

- N = 25: hard - soft -0.035 [-0.106, +0.018]; rule-soft-100 seed spread 0.043 (single seeds: difference is noise-sized); the interval allows hard targets to have closed up to 31% of the soft-to-examples gap (0.336); point estimate 11%.
- N = 100: hard - soft -0.029 [-0.096, +0.017]; rule-soft-100 seed spread 0.043 (single seeds: difference is noise-sized); the interval allows hard targets to have closed up to 28% of the soft-to-examples gap (0.348); point estimate 8%.
