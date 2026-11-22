# EXPLORATORY analyses (CPU, saved results; the frozen verdict 'not passed' stands)

Seeds used: [0, 1, 2]. Arms at their own seed-0 chosen lr: method 1e-04 (seeds [0, 1, 2], grid {'1e-04': 0.15510958211242618, '3e-04': 0.2314509565809123, '1e-03': 0.42031721063070454}), neutral 1e-04 (seeds [0, 1], grid {'1e-04': 0.5336067130642781, '3e-04': 0.5767025445125867, '1e-03': 0.5767025445125867}), wrong_rule 1e-03 (seeds [0, 1, 2], grid {'1e-04': 0.4476209046324473, '3e-04': 0.47348023562915326, '1e-03': 0.4301475138665957}).
Held-out cells are selected-on (lr, epoch). Bootstrap: paired over the 6 held-out cells, 10,000 resamples, seed 0.

## A. Soft regret on held-out cells (arm mean over seeds), difference control − method

| Control | Control soft regret | Method soft regret | Difference [95% interval] | Cells method better |
| --- | --- | --- | --- | --- |
| plain | 0.577 | 0.194 | +0.383 [+0.034, +0.760] | 5 of 6 |
| neutral | 0.531 | 0.194 | +0.337 [+0.021, +0.703] | 4 of 6 |
| wrong_rule | 0.404 | 0.194 | +0.210 [-0.032, +0.502] | 4 of 6 |

### A2. Same difference split by cell type (descriptive, no interval): C<V cells [(3, 'C', 2), (5, 'C', 4), (6, 'C', 1)] vs other cells [(3, 'C', 4), (3, 'neutral'), (5, 'pressure')]

| Control | mean diff (control − method) on C<V cells | on other cells |
| --- | --- | --- |
| plain | +0.789 | -0.023 |
| neutral | +0.710 | -0.037 |
| wrong_rule | +0.497 | -0.076 |

### A3. Per-seed held-out soft regret at each arm's chosen lr (seed 0 is the seed that chose the lr)

| Arm | seed 0 | seed 1 | seed 2 |
| --- | --- | --- | --- |
| method 1e-04 | 0.155 (best ep 2) | 0.217 (best ep 2) | 0.210 (best ep 4) |
| neutral 1e-04 | 0.534 (best ep 1) | 0.527 (best ep 3) | — |
| wrong_rule 1e-03 | 0.430 (best ep 5) | 0.354 (best ep 5) | 0.428 (best ep 2) |


## B. (a) Slope of expected offer on stated cost, cells with C < V (3 cells: [(3, 'C', 2), (5, 'C', 4), (6, 'C', 1)])

| Arm | Slope | Method − arm [95% interval] | resamples dropped (one distinct C) |
| --- | --- | --- | --- |
| method | 0.499 | | |
| plain | 0.053 | +0.446 [+0.418, +0.518] | 1097 of 10000 |
| neutral | 0.066 | +0.433 [+0.357, +0.622] | 1097 of 10000 |
| wrong_rule | -0.010 | +0.509 [+0.457, +0.640] | 1097 of 10000 |

POST HOC choice (seed-0 slopes were seen before the rule was written). With 3 cost cells the bootstrap has about 7 distinct outcomes and is conditioned on dropping 1/9 of resamples; the interval is arithmetic on 3 points, NOT a sampling interval. Descriptive only.

## B. (b) Per-cell table (arm mean over seeds)

| Cell | Line | Best offer(s) | Expected offer: plain | method | neutral | wrong-rule | Soft regret: plain | method | neutral | wrong-rule | Method beats wrong-rule? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| (3, 'C', 2) | information | [2] | 2.47 | 1.91 | 2.38 | 2.09 | 0.998 | 0.097 | 0.767 | 0.376 | yes |
| (3, 'C', 4) | information | [1, 2, 3] | 2.02 | 2.05 | 2.16 | 1.98 | 0.002 | 0.121 | 0.008 | 0.005 | NO |
| (3, 'neutral') | neutral | [1, 2] | 1.98 | 1.51 | 2.05 | 1.97 | 0.020 | 0.015 | 0.039 | 0.024 | yes |
| (5, 'C', 4) | information | [4] | 2.44 | 2.72 | 2.47 | 1.98 | 0.994 | 0.603 | 0.975 | 0.998 | yes |
| (5, 'pressure') | pressure | [2, 3] | 3.15 | 1.86 | 2.74 | 1.99 | 0.199 | 0.153 | 0.132 | 0.031 | NO |
| (6, 'C', 1) | information | [1] | 2.25 | 1.17 | 2.26 | 1.99 | 1.249 | 0.174 | 1.262 | 0.992 | yes |

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
| wrong_rule 3e-04 | 0.577 | 0.511 | 0.484 | 0.482 | 0.474 | 0.007 | 0.027 | 0.005 | 0.014 |
| wrong_rule 1e-03 | 0.577 | 0.470 | 0.523 | 0.468 | 0.467 | -0.000 | -0.009 | -0.002 | -0.006 |

### Fixed-epoch per-cell soft regret difference (control − method), runs that logged per-epoch probabilities


## B. (d) Free-text hard regret, method vs plain (cell bootstrap)

plain 0.500, method 0.492; difference plain − method +0.008 [-0.183, +0.208], method better in 1 of 6 cells.


## C. G2 additions (exploratory)

- always-2 − method: +0.140 [-0.110, +0.451], method better in 2 of 6 cells (always-2 mean 0.333).
- leave-one-cell-out mean of (wrong_rule − method): without (3, 'C', 2): +0.197, without (3, 'C', 4): +0.276, without (3, 'neutral'): +0.251, without (5, 'C', 4): +0.174, without (5, 'pressure'): +0.277, without (6, 'C', 1): +0.089
- leave-one-cell-out mean of (neutral − method): without (3, 'C', 2): +0.270, without (3, 'C', 4): +0.427, without (3, 'neutral'): +0.399, without (5, 'C', 4): +0.330, without (5, 'pressure'): +0.408, without (6, 'C', 1): +0.186
- train cells (11, fitted; each arm fits its own teacher): plain 0.778, method 0.403, neutral 0.753, wrong_rule 0.715
- train cells wrong-rule − method: +0.312 [+0.057, +0.590] over 11 cells
- fixed-epoch per-cell section above is empty because the method runs predate the per-epoch probability logging (only wrong-rule 3e-4/1e-3 and neutral seed 1 have it).
