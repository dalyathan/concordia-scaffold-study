# EXPLORATORY analyses (CPU, saved results; the frozen verdict 'not passed' stands)

Seeds used: [0]. Arms at their own seed-0 chosen lr: method 1e-04 (seeds [0], grid {'1e-04': 0.15510958211242618, '3e-04': 0.2314509565809123, '1e-03': 0.42031721063070454}), neutral 1e-04 (seeds [0], grid {'1e-04': 0.5336067130642781, '3e-04': 0.5767025445125867, '1e-03': 0.5767025445125867}), wrong_rule 1e-04 (seeds [0], grid {'1e-04': 0.4476209046324473}).
Held-out cells are selected-on (lr, epoch). Bootstrap: paired over the 6 held-out cells, 10,000 resamples, seed 0.

## A. Soft regret on held-out cells (arm mean over seeds), difference control − method

| Control | Control soft regret | Method soft regret | Difference [95% interval] | Cells method better |
| --- | --- | --- | --- | --- |
| plain | 0.577 | 0.155 | +0.422 [+0.051, +0.820] | 5 of 6 |
| neutral | 0.534 | 0.155 | +0.378 [+0.043, +0.758] | 5 of 6 |
| wrong_rule | 0.448 | 0.155 | +0.293 [-0.003, +0.605] | 3 of 6 |

## B. (a) Slope of expected offer on stated cost, cells with C < V (3 cells: [(3, 'C', 2), (5, 'C', 4), (6, 'C', 1)])

| Arm | Slope | Method − arm [95% interval] | resamples dropped (one distinct C) |
| --- | --- | --- | --- |
| method | 0.661 | | |
| plain | 0.053 | +0.609 [+0.604, +0.611] | 1097 of 10000 |
| neutral | 0.076 | +0.585 [+0.571, +0.621] | 1097 of 10000 |
| wrong_rule | 0.031 | +0.631 [+0.410, +1.184] | 1097 of 10000 |

With 3 cost cells (and 4 name variants each that are not independent) this interval is fragile; read it as descriptive.

## B. (b) Per-cell table (arm mean over seeds)

| Cell | Line | Best offer(s) | Expected offer: plain | method | neutral | wrong-rule | Soft regret: plain | method | neutral | wrong-rule | Method beats wrong-rule? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| (3, 'C', 2) | information | [2] | 2.47 | 1.98 | 2.50 | 1.65 | 0.998 | 0.029 | 0.737 | 0.627 | yes |
| (3, 'C', 4) | information | [1, 2, 3] | 2.02 | 2.19 | 2.19 | 2.00 | 0.002 | 0.170 | 0.009 | 0.002 | NO |
| (3, 'neutral') | neutral | [1, 2] | 1.98 | 1.56 | 2.08 | 1.89 | 0.020 | 0.019 | 0.050 | 0.013 | NO |
| (5, 'C', 4) | information | [4] | 2.44 | 3.18 | 2.55 | 2.02 | 0.994 | 0.410 | 0.965 | 0.999 | yes |
| (5, 'pressure') | pressure | [2, 3] | 3.15 | 1.92 | 2.84 | 2.07 | 0.199 | 0.143 | 0.146 | 0.035 | NO |
| (6, 'C', 1) | information | [1] | 2.25 | 1.16 | 2.29 | 2.01 | 1.249 | 0.159 | 1.295 | 1.010 | yes |

## B. (c) Held-out soft regret at fixed epochs (all saved runs, seed 0; history holds aggregates only, so no per-cell interval is possible)

| Run | ep0 (plain) | ep1 | ep2 | ep3 | ep4 | slope ep1 | ep2 | ep3 | ep4 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| method 1e-04 | 0.577 | 0.315 | 0.155 | 0.254 | 0.240 | 0.217 | 0.661 | 0.390 | 0.301 |
| method 3e-04 | 0.577 | 0.405 | 0.387 | 0.231 | 0.289 | 0.079 | 0.203 | 0.444 | 0.246 |
| method 1e-03 | 0.577 | 0.492 | 0.457 | 0.509 | 0.420 | 0.002 | 0.004 | -0.002 | 0.003 |
| neutral 1e-04 | 0.577 | 0.534 | 0.559 | 0.584 | — | 0.076 | 0.043 | 0.037 | — |
| neutral 3e-04 | 0.577 | 0.627 | 0.646 | — | — | -0.070 | -0.035 | — | — |
| neutral 1e-03 | 0.577 | 0.885 | 0.754 | — | — | -0.033 | 0.003 | — | — |
| wrong_rule 1e-04 | 0.577 | 0.462 | 0.448 | 0.460 | 0.458 | 0.031 | 0.031 | 0.046 | 0.035 |

## B. (d) Free-text hard regret, method vs plain (cell bootstrap)

plain 0.500, method 0.467; difference plain − method +0.033 [-0.150, +0.250], method better in 1 of 6 cells.

