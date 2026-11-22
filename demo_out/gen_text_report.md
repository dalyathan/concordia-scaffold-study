# Text rows on generated train and tune cells (plain Gemma 2 9B-it, five orders; test sets not scored)

Notes block inserted before the question. Rows: plain (no notes), original method paragraph (earlier work), teacher method (Claude Opus, frozen), same-length neutral text, wrong rule; teacher_v1 = the first paragraph, teacher = the frozen winner of the closed loop (selected on 42 loop cells, so optimistic there) ("Offer half the stated cost."). Soft regret = best expected payoff minus the model's; cell means (two name variants), cell-bootstrap 95% intervals (10,000, seed 0). 'diff' = plain minus row (positive = row better).

## train (300 cells)

| Row | all types | below | at_or_above | no_cost | slope of expected offer on stated cost (below cells) | letter mass | diff vs plain, all types [95%] |
| --- | --- | --- | --- | --- | --- | --- | --- |
| plain | 0.652 [0.573, 0.731] | 1.436 [1.326, 1.552] | 0.298 [0.216, 0.383] | 0.221 [0.184, 0.263] | 0.26 | 0.81 | +0.000 [+0.000, +0.000] |
| method_original | 0.368 [0.312, 0.428] | 0.633 [0.511, 0.767] | 0.134 [0.087, 0.187] | 0.336 [0.258, 0.427] | 0.26 | 0.91 | +0.284 [+0.215, +0.352] |
| teacher_v1 | 0.485 [0.419, 0.553] | 1.050 [0.930, 1.181] | 0.150 [0.097, 0.208] | 0.256 [0.207, 0.311] | 0.19 | 0.85 | +0.166 [+0.124, +0.209] |
| teacher | 0.330 [0.278, 0.383] | 0.612 [0.508, 0.725] | 0.080 [0.043, 0.124] | 0.298 [0.225, 0.378] | 0.27 | 0.92 | +0.322 [+0.259, +0.385] |
| neutral | 0.682 [0.596, 0.768] | 1.511 [1.383, 1.650] | 0.286 [0.202, 0.373] | 0.248 [0.204, 0.298] | 0.20 | 0.85 | -0.030 [-0.050, -0.012] |
| wrong_rule | 0.652 [0.553, 0.755] | 1.478 [1.274, 1.697] | 0.186 [0.124, 0.252] | 0.292 [0.234, 0.358] | 0.08 | 0.68 | -0.001 [-0.054, +0.050] |
| always-cheapest | 0.573 | 1.250 | 0.000 | 0.470 | | | |
| stated-cost rule | 0.157 | 0.000 | 0.000 | 0.470 | | | |

## tune (42 cells)

| Row | all types | below | at_or_above | no_cost | slope of expected offer on stated cost (below cells) | letter mass | diff vs plain, all types [95%] |
| --- | --- | --- | --- | --- | --- | --- | --- |
| plain | 0.657 [0.465, 0.862] | 1.376 [1.144, 1.674] | 0.391 [0.170, 0.656] | 0.204 [0.113, 0.309] | 0.32 | 0.81 | +0.000 [+0.000, +0.000] |
| method_original | 0.369 [0.207, 0.571] | 0.542 [0.179, 1.053] | 0.174 [0.044, 0.364] | 0.391 [0.180, 0.637] | 0.27 | 0.91 | +0.288 [+0.108, +0.487] |
| teacher_v1 | 0.517 [0.343, 0.725] | 1.102 [0.781, 1.517] | 0.188 [0.040, 0.394] | 0.262 [0.138, 0.412] | 0.15 | 0.86 | +0.140 [+0.049, +0.245] |
| teacher | 0.390 [0.243, 0.565] | 0.673 [0.377, 1.073] | 0.107 [0.017, 0.270] | 0.390 [0.196, 0.619] | 0.24 | 0.92 | +0.267 [+0.115, +0.437] |
| neutral | 0.735 [0.514, 0.977] | 1.515 [1.206, 1.912] | 0.400 [0.127, 0.739] | 0.289 [0.158, 0.440] | 0.27 | 0.85 | -0.078 [-0.141, -0.015] |
| wrong_rule | 0.618 [0.405, 0.874] | 1.325 [0.930, 1.858] | 0.244 [0.078, 0.443] | 0.285 [0.140, 0.459] | 0.10 | 0.67 | +0.039 [-0.084, +0.150] |
| always-cheapest | 0.429 | 0.643 | 0.000 | 0.643 | | | |
| stated-cost rule | 0.214 | 0.000 | 0.000 | 0.643 | | | |

## LoRA selection set B (42 train cells not used by the loop, the packet or LoRA training)

| Row | soft regret [95%] | below | at_or_above | no_cost |
| --- | --- | --- | --- | --- |
| plain | 0.584 [0.446, 0.730] | 1.004 | 0.508 | 0.240 |
| method_original | 0.395 [0.262, 0.546] | 0.497 | 0.263 | 0.426 |
| teacher_v1 | 0.490 [0.351, 0.635] | 0.904 | 0.264 | 0.303 |
| teacher | 0.342 [0.216, 0.487] | 0.431 | 0.224 | 0.370 |
| neutral | 0.651 [0.499, 0.811] | 1.136 | 0.505 | 0.313 |
| wrong_rule | 0.519 [0.369, 0.678] | 0.918 | 0.314 | 0.325 |

## loop set A (42 cells the winner was selected on: optimistic)

| Row | soft regret [95%] | below | at_or_above | no_cost |
| --- | --- | --- | --- | --- |
| plain | 0.571 [0.401, 0.748] | 1.211 | 0.326 | 0.174 |
| method_original | 0.287 [0.192, 0.388] | 0.453 | 0.179 | 0.229 |
| teacher_v1 | 0.431 [0.297, 0.574] | 0.903 | 0.197 | 0.194 |
| teacher | 0.245 [0.161, 0.334] | 0.483 | 0.070 | 0.181 |
| neutral | 0.541 [0.368, 0.723] | 1.214 | 0.260 | 0.147 |
| wrong_rule | 0.420 [0.296, 0.550] | 0.843 | 0.207 | 0.211 |

