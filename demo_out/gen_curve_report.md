# Learning curve and rules-vs-examples on the 42 TUNE cells (descriptive; read against PREDICTIONS.md)

42 tune cells in 38 decision problems and 19 (V, grid) groups. Intervals: clustered paired bootstrap by (V, grid) (the wider one; used for every 'lower bound > 0' condition) and, in the arm table, also by problem. Soft regret: lower is better. Seeds averaged per arm.

## Soft regret by arm

| Arm | seeds | all [95% by (V, grid)] [95% by problem] | below | at_or_above | no_cost | argmax (hard) regret | letter mass | slope on stated cost (below) | best steps | epoch-0 kept |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| plain |  | 0.657 [0.476, 0.850] [0.451, 0.879] | 1.376 | 0.391 | 0.204 | 0.546 |  | 0.32 [0.05, 0.80] |  |  |
| always-cheapest |  | 0.429 [0.157, 0.822] [0.191, 0.726] | 0.643 | 0.000 | 0.643 |  |  |  |  |  |
| stated-cost rule |  | 0.214 [0.056, 0.481] [0.076, 0.390] | 0.000 | 0.000 | 0.643 |  |  |  |  |  |
| examples-10 | 3 | 0.092 [0.037, 0.174] [0.042, 0.152] | 0.033 | 0.049 | 0.194 | 0.048 | 1.00 | 0.66 [0.42, 0.93] | 500,500,500 | False,False,False |
| examples-25 | 3 | 0.042 [0.013, 0.083] [0.016, 0.072] | 0.015 | 0.019 | 0.091 | 0.019 | 1.00 | 0.75 [0.47, 1.00] | 500,500,400 | False,False,False |
| examples-50 | 3 | 0.040 [0.018, 0.072] [0.020, 0.063] | 0.016 | 0.028 | 0.075 | 0.000 | 1.00 | 0.75 [0.47, 1.00] | 500,400,400 | False,False,False |
| examples-100 | 3 | 0.032 [0.013, 0.061] [0.016, 0.051] | 0.008 | 0.011 | 0.077 | 0.000 | 1.00 | 0.76 [0.49, 1.00] | 400,500,200 | False,False,False |
| rule-soft-25 | 1 | 0.378 [0.224, 0.597] [0.247, 0.536] | 0.566 | 0.134 | 0.434 | 0.257 | 1.00 | 0.27 [-0.05, 0.67] | 50 | False |
| rule-soft-100 (3 seeds) | 3 | 0.376 [0.218, 0.593] [0.240, 0.540] | 0.614 | 0.119 | 0.394 | 0.324 | 1.00 | 0.26 [-0.04, 0.65] | 400,300,200 | False,False,False |
| rule-soft-100 seed 0 | 1 | 0.380 [0.222, 0.599] [0.244, 0.545] | 0.620 | 0.122 | 0.400 | 0.348 | 1.00 | 0.25 [-0.06, 0.66] | 400 | False |
| rule-hard-25 | 1 | 0.343 [0.206, 0.521] [0.226, 0.471] | 0.509 | 0.113 | 0.406 | 0.336 | 1.00 | 0.28 [-0.09, 0.71] | 100 | False |
| rule-hard-100 | 1 | 0.351 [0.214, 0.536] [0.227, 0.490] | 0.518 | 0.102 | 0.433 | 0.303 | 1.00 | 0.34 [0.05, 0.68] | 500 | False |
| cheapest-label-25 | 1 | 0.429 [0.157, 0.822] [0.191, 0.726] | 0.643 | 0.000 | 0.643 | 0.429 | 1.00 | 0.06 [-0.28, 0.61] | 500 | False |

## Comparisons (first minus second; lower bound > 0 means the second is better; (V, grid)-clustered interval, by-type point differences)

- rule-soft-25 - examples-25: +0.336 [+0.198, +0.535]; problem-clustered +0.336 [+0.214, +0.487]; by type below +0.551, at_or_above +0.116, no_cost +0.342
- rule-hard-25 - examples-25: +0.301 [+0.182, +0.456]; problem-clustered +0.301 [+0.194, +0.418]; by type below +0.494, at_or_above +0.094, no_cost +0.315
- rule-soft-100 (3 seeds) - examples-100: +0.344 [+0.198, +0.543]; problem-clustered +0.344 [+0.217, +0.501]; by type below +0.606, at_or_above +0.108, no_cost +0.317
- rule-hard-100 - examples-100: +0.319 [+0.195, +0.484]; problem-clustered +0.319 [+0.207, +0.447]; by type below +0.510, at_or_above +0.091, no_cost +0.356
- rule-soft-100 seed 0 - examples-100: +0.348 [+0.202, +0.548]; problem-clustered +0.348 [+0.221, +0.505]; by type below +0.612, at_or_above +0.111, no_cost +0.323
- rule-hard-25 - rule-soft-25: -0.035 [-0.106, +0.018]; problem-clustered -0.035 [-0.101, +0.018]; by type below -0.057, at_or_above -0.022, no_cost -0.027
- rule-hard-100 - rule-soft-100 seed 0: -0.029 [-0.096, +0.017]; problem-clustered -0.029 [-0.083, +0.013]; by type below -0.101, at_or_above -0.020, no_cost +0.033
- cheapest-label-25 - examples-25: +0.387 [+0.126, +0.764]; problem-clustered +0.387 [+0.158, +0.681]; by type below +0.628, at_or_above -0.019, no_cost +0.551
- examples-10 - examples-100: +0.060 [+0.020, +0.115]; problem-clustered +0.060 [+0.022, +0.106]; by type below +0.024, at_or_above +0.038, no_cost +0.117
- examples-25 - examples-100: +0.010 [-0.009, +0.029]; problem-clustered +0.010 [-0.008, +0.029]; by type below +0.007, at_or_above +0.007, no_cost +0.015
- examples-50 - examples-100: +0.008 [-0.005, +0.023]; problem-clustered +0.008 [-0.004, +0.022]; by type below +0.008, at_or_above +0.017, no_cost -0.001
- plain - examples-10: +0.565 [+0.364, +0.766]; problem-clustered +0.565 [+0.340, +0.804]; by type below +1.344, at_or_above +0.342, no_cost +0.010
- plain - examples-25: +0.616 [+0.428, +0.813]; problem-clustered +0.616 [+0.403, +0.844]; by type below +1.362, at_or_above +0.372, no_cost +0.113
- plain - examples-50: +0.618 [+0.434, +0.809]; problem-clustered +0.618 [+0.407, +0.843]; by type below +1.361, at_or_above +0.363, no_cost +0.129

## What the training subsets cover (CPU, from the subset lists)

| N | distinct training problems | tune cells whose problem is in the subset | examples-N regret covered / uncovered | share of cheapest Claude labels | rule-soft target: soft / argmax regret on the subset | always-cheapest regret on the subset |
| --- | --- | --- | --- | --- | --- | --- |
| 10 | 10 | 3 of 42 | 0.000 / 0.099 | 0.70 | 0.20 / 0.08 | 0.32 |
| 25 | 25 | 9 of 42 | 0.008 / 0.051 | 0.64 | 0.21 / 0.10 | 0.42 |
| 50 | 47 | 12 of 42 | 0.013 / 0.050 | 0.62 | 0.29 / 0.16 | 0.65 |
| 100 | 79 | 16 of 42 | 0.009 / 0.046 | 0.65 | 0.31 / 0.24 | 0.60 |

Claude labels have regret 0 on every training cell by construction; the in-prompt teacher paragraph's own regret (order-averaged) is shown above, so a rule student cannot be expected to beat it by much.
- rule-hard-25: share of training cases whose argmax price differs across their three orders 0.56; share of cheapest target prices 0.60
- rule-hard-100: share of training cases whose argmax price differs across their three orders 0.60; share of cheapest target prices 0.64

## Seed spread (max - min of per-run tune soft regret) and per-run values

- gen_claude_examples_n10_lr1e-04_s0: tune 0.071 (by type below 0.072, at_or_above 0.001, no_cost 0.141); selection set B 0.050; slope 0.58; best step 500; 7 epochs run; 2205 s
- gen_claude_examples_n10_lr1e-04_s1: tune 0.151 (by type below 0.015, at_or_above 0.131, no_cost 0.308); selection set B 0.165; slope 0.68; best step 500; 7 epochs run; 2204 s
- gen_claude_examples_n10_lr1e-04_s2: tune 0.054 (by type below 0.012, at_or_above 0.017, no_cost 0.133); selection set B 0.056; slope 0.73; best step 500; 7 epochs run; 2205 s
  - examples-10: seed spread 0.098
- gen_claude_examples_n25_lr1e-04_s0: tune 0.043 (by type below 0.029, at_or_above 0.015, no_cost 0.085); selection set B 0.093; slope 0.73; best step 500; 6 epochs run; 2135 s
- gen_claude_examples_n25_lr1e-04_s1: tune 0.037 (by type below 0.013, at_or_above 0.011, no_cost 0.085); selection set B 0.048; slope 0.75; best step 500; 6 epochs run; 2136 s
- gen_claude_examples_n25_lr1e-04_s2: tune 0.045 (by type below 0.003, at_or_above 0.029, no_cost 0.104); selection set B 0.050; slope 0.76; best step 400; 6 epochs run; 2134 s
  - examples-25: seed spread 0.009
- gen_claude_examples_n50_lr1e-04_s0: tune 0.014 (by type below 0.004, at_or_above 0.019, no_cost 0.020); selection set B 0.016; slope 0.76; best step 500; 6 epochs run; 2138 s
- gen_claude_examples_n50_lr1e-04_s1: tune 0.028 (by type below 0.020, at_or_above 0.000, no_cost 0.064); selection set B 0.043; slope 0.74; best step 400; 6 epochs run; 2138 s
- gen_claude_examples_n50_lr1e-04_s2: tune 0.077 (by type below 0.023, at_or_above 0.064, no_cost 0.143); selection set B 0.105; slope 0.74; best step 400; 6 epochs run; 2138 s
  - examples-50: seed spread 0.062
- gen_claude_examples_lr1e-04_s0: tune 0.013 (by type below 0.003, at_or_above 0.000, no_cost 0.036); selection set B 0.027; slope 0.76; best step 400; 5 epochs run; 2257 s
- gen_claude_examples_lr1e-04_s1: tune 0.026 (by type below 0.001, at_or_above 0.020, no_cost 0.058); selection set B 0.027; slope 0.76; best step 500; 5 epochs run; 2258 s
- gen_claude_examples_lr1e-04_s2: tune 0.057 (by type below 0.020, at_or_above 0.013, no_cost 0.137); selection set B 0.067; slope 0.75; best step 200; 4 epochs run; 1866 s
  - examples-100: seed spread 0.044
- gen_teacher_n25_lr1e-04_s0: tune 0.378 (by type below 0.566, at_or_above 0.134, no_cost 0.434); selection set B 0.346; slope 0.27; best step 50; 3 epochs run; 1082 s
- gen_teacher_lr1e-04_s0: tune 0.380 (by type below 0.620, at_or_above 0.122, no_cost 0.400); selection set B 0.360; slope 0.25; best step 400; 5 epochs run; 2371 s
- gen_teacher_lr1e-04_s1: tune 0.352 (by type below 0.538, at_or_above 0.099, no_cost 0.418); selection set B 0.329; slope 0.29; best step 300; 5 epochs run; 2371 s
- gen_teacher_lr1e-04_s2: tune 0.395 (by type below 0.685, at_or_above 0.136, no_cost 0.364); selection set B 0.372; slope 0.24; best step 200; 4 epochs run; 1979 s
  - rule-soft-100 (3 seeds): seed spread 0.043
- gen_teacher_lr1e-04_s0: tune 0.380 (by type below 0.620, at_or_above 0.122, no_cost 0.400); selection set B 0.360; slope 0.25; best step 400; 5 epochs run; 2371 s
- gen_rule_hard_n25_lr1e-04_s0: tune 0.343 (by type below 0.509, at_or_above 0.113, no_cost 0.406); selection set B 0.319; slope 0.28; best step 100; 4 epochs run; 1442 s
- gen_rule_hard_lr1e-04_s0: tune 0.351 (by type below 0.518, at_or_above 0.102, no_cost 0.433); selection set B 0.319; slope 0.34; best step 500; 5 epochs run; 2370 s
- gen_cheapest_label_n25_lr1e-04_s0: tune 0.429 (by type below 0.643, at_or_above 0.000, no_cost 0.643); selection set B 0.314; slope 0.06; best step 500; 6 epochs run; 2135 s

## Predictions scored mechanically (rule at the top of PREDICTIONS.md)

- P1a: **FAILED** - examples-10 = 0.092 (range 0.15..0.5)
- P1b: **FAILED** - examples-25 = 0.042 (range 0.05..0.18)
- P1c: **HELD** - examples-50 = 0.040 (range 0.03..0.09)
- P1m: **HELD** - means 0.092 > 0.042 > 0.040; 50 - 100 = +0.008
- P2a: **FAILED** - examples-25 mean 0.042 > 0.082: no (stated p = 0.65; Brier term 0.423)
- P2b: **HELD** - examples-50 mean 0.040 <= 0.082: yes (stated p = 0.8; Brier term 0.040)
- P2c: **HELD** - examples-10 mean 0.092 > 0.082: yes (stated p = 0.9; Brier term 0.010)
- P3a: **HELD** - rule-soft-25 - examples-25 = +0.336 [+0.198, +0.535] (range 0.2..0.5)
- P3b: **HELD** - rule-hard-25 - examples-25 = +0.301 [+0.182, +0.456] (range 0.15..0.45)
- P3c: **HELD** - rule-soft-100 (3 seeds) - examples-100 = +0.344 [+0.198, +0.543] (range 0.2..0.5)
- P3d: **HELD** - rule-hard-100 - examples-100 = +0.319 [+0.195, +0.484] (range 0.22..0.5)
- P4a: **HELD** - rule-soft-25 = 0.378 (range 0.33..0.55)
- P4b: **HELD** - rule-hard-25 = 0.343 (range 0.3..0.55)
- P4c: **HELD** - rule-hard-100 = 0.351 (range 0.3..0.5)
- P4d N=25: **HELD** - |rule-hard-25 - rule-soft-25| = 0.035 (limit 0.08; seed spread of rule-soft-100: 0.04340647142481524)
- P4e N=25: **HELD** - closed share 0.11 (denominator 0.336)
- P4f N=25: **HELD** - rule-hard-25 argmax regret 0.336 (>= 0.25)
- P4d N=100: **HELD** - |rule-hard-100 - rule-soft-100 seed 0| = 0.029 (limit 0.08; seed spread of rule-soft-100: 0.04340647142481524)
- P4e N=100: **HELD** - closed share 0.08 (denominator 0.348)
- P4f N=100: **HELD** - rule-hard-100 argmax regret 0.303 (>= 0.25)
- P5a: **HELD** - cheapest-label-25 = 0.429 (range 0.4..0.46)
- P5b: **HELD** - cheapest-label-25 - examples-25 = +0.387 [+0.126, +0.764] (range 0.0..9.9)
- P6a: **HELD** - slope examples-50 = 0.747 (range 0.55..0.8)
- P6b: **HELD** - slope examples-25 = 0.745 (range 0.3..0.75)
- P6c: **FAILED** - slope examples-10 = 0.663 (range 0.0..0.55)
- P6e: **HELD** - slope cheapest-label-25 = 0.062 (range -0.15..0.2)
- P6d: **HELD** - rule-arm slopes {'rule-soft-25': 0.27, 'rule-hard-25': 0.28, 'rule-soft-100 (3 seeds)': 0.26, 'rule-hard-100': 0.34} (each < 0.40)
- P7: **HELD** - minimum letter mass 0.998
- P8a: **HELD** - epoch-0 kept flags for examples N >= 25: [False, False, False, False, False, False, False, False, False]
- P8b: **FAILED** - examples-10 epoch-0 kept flags [False, False, False] (stated p = 0.15; Brier term 0.022)
- Brier score of the probability statements (P2a-c, P8b): 0.124 over 4 statements
- Tally: HELD 25, FAILED 5, UNCLEAR 0
