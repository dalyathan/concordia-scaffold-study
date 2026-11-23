# Worked-examples arms: the one test look (generated test_same and test_hard)

script sha256 52ea926f2a8a787820ae332e8f5cc1df8156fa471843227190f75bb26ac27c10; adapters per demo/gen/test_frozen_adapters.json; conditions as frozen in GEN_EXAMPLES_TEST_PLAN.md; paired cell bootstrap 10,000 resamples, numpy default_rng(0), two-sided 95% percentile; no adapter, seed, epoch or lr was chosen on test data. The development verdict on tune was PASSED (soft regret 0.032 vs plain 0.657).

## test_same: 60 cells (below 20, at_or_above 20, no_cost 20)

| Arm | all [95%] | below | at_or_above | no_cost | cheapest-option mass by type |
| --- | --- | --- | --- | --- | --- |
| plain | 0.694 [0.504, 0.905] | 1.528 | 0.257 | 0.297 | 0.09 / 0.08 / 0.10 |
| always-cheapest | 0.764 [0.423, 1.150] | 1.550 | 0.000 | 0.742 | 1.00 / 1.00 / 1.00 |
| stated-cost rule | 0.247 [0.099, 0.419] | 0.000 | 0.000 | 0.742 | 0.55 / 1.00 / 1.00 |
| (a) claude-examples (3 seeds) | 0.044 [0.023, 0.070] | 0.016 | 0.004 | 0.112 | 0.55 / 0.92 / 0.38 |
| (b) cheapest-label | 0.764 [0.423, 1.150] | 1.550 | 0.000 | 0.742 | 1.00 / 1.00 / 1.00 |
| (c) shuffled-Claude | 0.935 [0.629, 1.287] | 1.956 | 0.103 | 0.746 | 0.66 / 0.90 / 0.64 |
| answer-trained ceiling lr 1e-4 | 0.027 [0.013, 0.045] | 0.004 | 0.027 | 0.049 | 0.55 / 0.39 / 0.34 |
| teacher-distil (3 seeds; reported only) | 0.368 [0.229, 0.544] | 0.604 | 0.055 | 0.445 | 0.36 / 0.40 / 0.46 |
| our-method-distil (3 seeds; reported only) | 0.396 [0.268, 0.547] | 0.557 | 0.148 | 0.483 | 0.31 / 0.29 / 0.31 |

letter mass: plain 0.80, (a) 1.00

Frozen rule (six conditions):
- 1. plain - a: +0.650 [+0.459, +0.861], lower bound > 0: **yes**
- 2. (b) - a: +0.720 [+0.387, +1.099], lower bound > 0: **yes**
- 3. always-cheapest - a: +0.720 [+0.387, +1.099], lower bound > 0: **yes**
- 4. plain - a on below cells (20): +1.512 [+1.196, +1.891], lower bound > 0: **yes**
- 5. type means (a) minus plain: below -1.512, at_or_above -0.253, no_cost -0.185 (each <= +0.05): **yes**
- 6. letter mass 1.00 vs 0.9 x plain 0.72: **yes**

**Outcome for test_same: PASSED**

Reported, outside the rule:
- plain - stated-cost rule: +0.447 [+0.186, +0.724], lower bound > 0: **yes**
- stated-cost rule - a: +0.203 [+0.075, +0.353], lower bound > 0: **yes**
- plain - answer-trained ceiling lr 1e-4: +0.668 [+0.476, +0.880], lower bound > 0: **yes**
- answer-trained ceiling lr 1e-4 - a: -0.018 [-0.040, +0.005], lower bound > 0: **no**
- plain - teacher-distil (3 seeds; reported only): +0.326 [+0.177, +0.485], lower bound > 0: **yes**
- teacher-distil (3 seeds; reported only) - a: +0.324 [+0.196, +0.488], lower bound > 0: **yes**
- plain - our-method-distil (3 seeds; reported only): +0.298 [+0.135, +0.474], lower bound > 0: **yes**
- our-method-distil (3 seeds; reported only) - a: +0.352 [+0.236, +0.490], lower bound > 0: **yes**
- (b) - a on below cells: +1.534 [+0.686, +2.484], lower bound > 0: **yes**
- (c) - a on below cells: +1.940 [+1.260, +2.721], lower bound > 0: **yes**
- (b) - a on no_cost cells: +0.630 [+0.295, +1.016], lower bound > 0: **yes**
- (c) - a on no_cost cells: +0.634 [+0.406, +0.896], lower bound > 0: **yes**
- per-seed: plain - claude_examples_s0: +0.665 [+0.474, +0.875], lower bound > 0: **yes**
- per-seed: (b) - claude_examples_s0: +0.735 [+0.401, +1.118], lower bound > 0: **yes**
- per-seed: always-cheapest - claude_examples_s0: +0.735 [+0.401, +1.118], lower bound > 0: **yes**
- per-seed: plain - claude_examples_s1: +0.668 [+0.475, +0.880], lower bound > 0: **yes**
- per-seed: (b) - claude_examples_s1: +0.738 [+0.403, +1.122], lower bound > 0: **yes**
- per-seed: always-cheapest - claude_examples_s1: +0.738 [+0.403, +1.122], lower bound > 0: **yes**
- per-seed: plain - claude_examples_s2: +0.616 [+0.426, +0.829], lower bound > 0: **yes**
- per-seed: (b) - claude_examples_s2: +0.686 [+0.359, +1.061], lower bound > 0: **yes**
- per-seed: always-cheapest - claude_examples_s2: +0.686 [+0.359, +1.061], lower bound > 0: **yes**
- wording check: (c) - a on below cells: +1.940 [+1.260, +2.721], lower bound > 0: **yes**
- wording check: (c) - a on no_cost cells: +0.634 [+0.406, +0.896], lower bound > 0: **yes**
- wording check: plain - a on the 34 cells whose current label key is not in the 100 training cells: +0.869 [+0.581, +1.194], lower bound > 0: **yes**
- WORDING FLAGS (fixed in the plan): 'beyond shuffled labels' allowed: **yes**; 'generalises to cells with new label keys' allowed: **yes** (else a pass is worded as holding on the same generator, largely on repeated parameter combinations)
- by type, (a) minus ceiling: below +0.013, at_or_above -0.023, no_cost +0.063
- per-run soft regret (a): claude_examples_s0 0.029; claude_examples_s1 0.026; claude_examples_s2 0.078
- per-run soft regret (b): cheapest_label_s0 0.764
- per-run soft regret (c): shuffled_claude_s0 0.935
- per-run soft regret (ceiling): ceiling_s0 0.027
- per-run soft regret (teacher): teacher_s0 0.373; teacher_s1 0.349; teacher_s2 0.383
- per-run soft regret (method): method_s0 0.419; method_s1 0.389; method_s2 0.380
- slope of the expected offer on the stated cost, below cells: (a) 0.68 [0.29, 0.81], plain 0.21 (0 of 10000 resamples dropped for a single stated cost), oracle 0.69
- overlap with the 100 training cells, current key: 26 overlapping, 34 not; non-overlapping: plain - a +0.869 [+0.581, +1.194], (b) - a +1.209 [+0.661, +1.840]
- overlap with the 100 training cells, V and C only: 49 overlapping, 11 not; non-overlapping: plain - a +1.720 [+1.145, +2.345], (b) - a +2.257 [+0.896, +3.705]

## test_hard: 62 cells (below 24, at_or_above 14, no_cost 24)

| Arm | all [95%] | below | at_or_above | no_cost | cheapest-option mass by type |
| --- | --- | --- | --- | --- | --- |
| plain | 1.297 [0.930, 1.722] | 2.438 | 0.557 | 0.588 | 0.08 / 0.14 / 0.04 |
| always-cheapest | 1.520 [0.939, 2.166] | 2.625 | 0.000 | 1.302 | 1.00 / 1.00 / 1.00 |
| stated-cost rule | 0.504 [0.279, 0.759] | 0.000 | 0.000 | 1.302 | 0.50 / 1.00 / 1.00 |
| (a) claude-examples (3 seeds) | 0.171 [0.094, 0.264] | 0.042 | 0.006 | 0.397 | 0.51 / 0.88 / 0.16 |
| (b) cheapest-label | 1.520 [0.939, 2.166] | 2.625 | 0.000 | 1.302 | 1.00 / 1.00 / 1.00 |
| (c) shuffled-Claude | 1.663 [1.142, 2.260] | 2.986 | 0.287 | 1.144 | 0.70 / 0.78 / 0.67 |
| answer-trained ceiling lr 1e-4 | 0.090 [0.055, 0.132] | 0.004 | 0.077 | 0.184 | 0.51 / 0.60 / 0.14 |
| teacher-distil (3 seeds; reported only) | 0.959 [0.631, 1.342] | 1.472 | 0.180 | 0.900 | 0.42 / 0.57 / 0.42 |
| our-method-distil (3 seeds; reported only) | 0.868 [0.601, 1.180] | 1.126 | 0.333 | 0.922 | 0.37 / 0.36 / 0.31 |

letter mass: plain 0.77, (a) 1.00

Frozen rule (six conditions):
- 1. plain - a: +1.126 [+0.753, +1.559], lower bound > 0: **yes**
- 2. (b) - a: +1.349 [+0.788, +1.982], lower bound > 0: **yes**
- 3. always-cheapest - a: +1.349 [+0.788, +1.982], lower bound > 0: **yes**
- 4. plain - a on below cells (24): +2.397 [+1.671, +3.205], lower bound > 0: **yes**
- 5. type means (a) minus plain: below -2.397, at_or_above -0.551, no_cost -0.191 (each <= +0.05): **yes**
- 6. letter mass 1.00 vs 0.9 x plain 0.70: **yes**

**Outcome for test_hard: PASSED**

Reported, outside the rule:
- plain - stated-cost rule: +0.793 [+0.341, +1.297], lower bound > 0: **yes**
- stated-cost rule - a: +0.333 [+0.178, +0.506], lower bound > 0: **yes**
- plain - answer-trained ceiling lr 1e-4: +1.207 [+0.837, +1.637], lower bound > 0: **yes**
- answer-trained ceiling lr 1e-4 - a: -0.081 [-0.140, -0.030], lower bound > 0: **no**
- plain - teacher-distil (3 seeds; reported only): +0.338 [+0.147, +0.542], lower bound > 0: **yes**
- teacher-distil (3 seeds; reported only) - a: +0.788 [+0.485, +1.154], lower bound > 0: **yes**
- plain - our-method-distil (3 seeds; reported only): +0.429 [+0.196, +0.678], lower bound > 0: **yes**
- our-method-distil (3 seeds; reported only) - a: +0.697 [+0.462, +0.983], lower bound > 0: **yes**
- (b) - a on below cells: +2.583 [+1.261, +4.042], lower bound > 0: **yes**
- (c) - a on below cells: +2.944 [+1.774, +4.232], lower bound > 0: **yes**
- (b) - a on no_cost cells: +0.906 [+0.608, +1.224], lower bound > 0: **yes**
- (c) - a on no_cost cells: +0.747 [+0.571, +0.939], lower bound > 0: **yes**
- per-seed: plain - claude_examples_s0: +1.183 [+0.811, +1.614], lower bound > 0: **yes**
- per-seed: (b) - claude_examples_s0: +1.406 [+0.834, +2.044], lower bound > 0: **yes**
- per-seed: always-cheapest - claude_examples_s0: +1.406 [+0.834, +2.044], lower bound > 0: **yes**
- per-seed: plain - claude_examples_s1: +1.142 [+0.763, +1.579], lower bound > 0: **yes**
- per-seed: (b) - claude_examples_s1: +1.365 [+0.797, +2.003], lower bound > 0: **yes**
- per-seed: always-cheapest - claude_examples_s1: +1.365 [+0.797, +2.003], lower bound > 0: **yes**
- per-seed: plain - claude_examples_s2: +1.054 [+0.687, +1.479], lower bound > 0: **yes**
- per-seed: (b) - claude_examples_s2: +1.277 [+0.725, +1.905], lower bound > 0: **yes**
- per-seed: always-cheapest - claude_examples_s2: +1.277 [+0.725, +1.905], lower bound > 0: **yes**
- wording check: (c) - a on below cells: +2.944 [+1.774, +4.232], lower bound > 0: **yes**
- wording check: (c) - a on no_cost cells: +0.747 [+0.571, +0.939], lower bound > 0: **yes**
- wording check: plain - a on the 53 cells whose current label key is not in the 100 training cells: +1.165 [+0.734, +1.653], lower bound > 0: **yes**
- WORDING FLAGS (fixed in the plan): 'beyond shuffled labels' allowed: **yes**; 'generalises to cells with new label keys' allowed: **yes** (else a pass is worded as holding on the same generator, largely on repeated parameter combinations)
- by type, (a) minus ceiling: below +0.037, at_or_above -0.071, no_cost +0.213
- per-run soft regret (a): claude_examples_s0 0.114; claude_examples_s1 0.156; claude_examples_s2 0.243
- per-run soft regret (b): cheapest_label_s0 1.520
- per-run soft regret (c): shuffled_claude_s0 1.663
- per-run soft regret (ceiling): ceiling_s0 0.090
- per-run soft regret (teacher): teacher_s0 0.963; teacher_s1 0.964; teacher_s2 0.950
- per-run soft regret (method): method_s0 0.903; method_s1 0.831; method_s2 0.870
- slope of the expected offer on the stated cost, below cells: (a) 0.60 [0.41, 0.78], plain 0.21 (0 of 10000 resamples dropped for a single stated cost), oracle 0.52
- overlap with the 100 training cells, current key: 9 overlapping, 53 not; non-overlapping: plain - a +1.165 [+0.734, +1.653], (b) - a +1.529 [+0.872, +2.248]
- overlap with the 100 training cells, V and C only: 37 overlapping, 25 not; non-overlapping: plain - a +1.839 [+1.028, +2.714], (b) - a +2.848 [+1.648, +4.102]

## test_hard/hard_V: 20 cells (below 10, no_cost 10)

| Arm | all [95%] | below | no_cost | cheapest-option mass by type |
| --- | --- | --- | --- | --- |
| plain | 2.536 [1.662, 3.465] | 4.027 | 1.044 | 0.02 / 0.07 |
| always-cheapest | 3.981 [2.702, 5.330] | 5.800 | 2.161 | 1.00 / 1.00 |
| stated-cost rule | 1.081 [0.521, 1.706] | 0.000 | 2.161 | 0.20 / 1.00 |
| (a) claude-examples (3 seeds) | 0.414 [0.216, 0.640] | 0.074 | 0.753 | 0.18 / 0.04 |
| (b) cheapest-label | 3.981 [2.702, 5.330] | 5.800 | 2.161 | 1.00 / 1.00 |
| (c) shuffled-Claude | 3.792 [2.558, 5.095] | 5.854 | 1.731 | 0.83 / 0.65 |
| answer-trained ceiling lr 1e-4 | 0.173 [0.081, 0.275] | 0.004 | 0.342 | 0.20 / 0.00 |
| teacher-distil (3 seeds; reported only) | 2.323 [1.536, 3.133] | 3.074 | 1.573 | 0.23 / 0.41 |
| our-method-distil (3 seeds; reported only) | 1.884 [1.255, 2.543] | 2.161 | 1.607 | 0.17 / 0.33 |

letter mass: plain 0.69, (a) 1.00

Frozen rule (six conditions):
- 1. plain - a: +2.122 [+1.159, +3.158], lower bound > 0: **yes**
- 2. (b) - a: +3.567 [+2.230, +4.993], lower bound > 0: **yes**
- 3. always-cheapest - a: +3.567 [+2.230, +4.993], lower bound > 0: **yes**
- 4. plain - a on below cells (10): +3.953 [+2.752, +5.165], lower bound > 0: **yes**
- 5. type means (a) minus plain: below -3.953, no_cost -0.291 (each <= +0.05): **yes**
- 6. letter mass 1.00 vs 0.9 x plain 0.62: **yes**

**Outcome for test_hard/hard_V: PASSED**

Reported, outside the rule:
- plain - stated-cost rule: +1.455 [+0.201, +2.756], lower bound > 0: **yes**
- stated-cost rule - a: +0.667 [+0.298, +1.087], lower bound > 0: **yes**
- plain - answer-trained ceiling lr 1e-4: +2.363 [+1.441, +3.335], lower bound > 0: **yes**
- answer-trained ceiling lr 1e-4 - a: -0.241 [-0.378, -0.123], lower bound > 0: **no**
- plain - teacher-distil (3 seeds; reported only): +0.212 [-0.189, +0.657], lower bound > 0: **no**
- teacher-distil (3 seeds; reported only) - a: +1.910 [+1.098, +2.776], lower bound > 0: **yes**
- plain - our-method-distil (3 seeds; reported only): +0.651 [+0.079, +1.250], lower bound > 0: **yes**
- our-method-distil (3 seeds; reported only) - a: +1.471 [+0.865, +2.135], lower bound > 0: **yes**
- (b) - a on below cells: +5.725 [+3.605, +7.538], lower bound > 0: **yes**
- (c) - a on below cells: +5.779 [+3.987, +7.331], lower bound > 0: **yes**
- (b) - a on no_cost cells: +1.408 [+0.990, +1.858], lower bound > 0: **yes**
- (c) - a on no_cost cells: +0.978 [+0.673, +1.301], lower bound > 0: **yes**
- per-seed: plain - claude_examples_s0: +2.254 [+1.312, +3.255], lower bound > 0: **yes**
- per-seed: (b) - claude_examples_s0: +3.699 [+2.374, +5.095], lower bound > 0: **yes**
- per-seed: always-cheapest - claude_examples_s0: +3.699 [+2.374, +5.095], lower bound > 0: **yes**
- per-seed: plain - claude_examples_s1: +2.139 [+1.155, +3.196], lower bound > 0: **yes**
- per-seed: (b) - claude_examples_s1: +3.584 [+2.243, +5.020], lower bound > 0: **yes**
- per-seed: always-cheapest - claude_examples_s1: +3.584 [+2.243, +5.020], lower bound > 0: **yes**
- per-seed: plain - claude_examples_s2: +1.972 [+1.003, +3.015], lower bound > 0: **yes**
- per-seed: (b) - claude_examples_s2: +3.417 [+2.063, +4.858], lower bound > 0: **yes**
- per-seed: always-cheapest - claude_examples_s2: +3.417 [+2.063, +4.858], lower bound > 0: **yes**
- wording check: (c) - a on below cells: +5.779 [+3.987, +7.331], lower bound > 0: **yes**
- wording check: (c) - a on no_cost cells: +0.978 [+0.673, +1.301], lower bound > 0: **yes**
- wording check: plain - a on the 20 cells whose current label key is not in the 100 training cells: +2.122 [+1.159, +3.158], lower bound > 0: **yes**
- WORDING FLAGS (fixed in the plan): 'beyond shuffled labels' allowed: **yes**; 'generalises to cells with new label keys' allowed: **yes** (else a pass is worded as holding on the same generator, largely on repeated parameter combinations); 'transfer to unseen V / grid / wording' allowed only if test_hard as a whole passed (test_hard: PASSED) and this slice passed
- by type, (a) minus ceiling: below +0.070, no_cost +0.411
- per-run soft regret (a): claude_examples_s0 0.282; claude_examples_s1 0.396; claude_examples_s2 0.563
- per-run soft regret (b): cheapest_label_s0 3.981
- per-run soft regret (c): shuffled_claude_s0 3.792
- per-run soft regret (ceiling): ceiling_s0 0.173
- per-run soft regret (teacher): teacher_s0 2.340; teacher_s1 2.408; teacher_s2 2.223
- per-run soft regret (method): method_s0 1.970; method_s1 1.799; method_s2 1.884
- slope of the expected offer on the stated cost, below cells: (a) 0.86 [0.65, 1.00], plain -0.09 (1 of 10000 resamples dropped for a single stated cost), oracle 0.90
- overlap with the 100 training cells, current key: 0 overlapping, 20 not; non-overlapping: plain - a +2.122 [+1.159, +3.158], (b) - a +3.567 [+2.230, +4.993]
- overlap with the 100 training cells, V and C only: 0 overlapping, 20 not; non-overlapping: plain - a +2.122 [+1.159, +3.158], (b) - a +3.567 [+2.230, +4.993]

## test_hard/hard_grid: 21 cells (below 7, at_or_above 7, no_cost 7)

| Arm | all [95%] | below | at_or_above | no_cost | cheapest-option mass by type |
| --- | --- | --- | --- | --- | --- |
| plain | 0.646 [0.313, 1.035] | 1.308 | 0.469 | 0.162 | 0.11 / 0.17 / 0.01 |
| always-cheapest | 0.234 [0.021, 0.564] | 0.429 | 0.000 | 0.273 | 1.00 / 1.00 / 1.00 |
| stated-cost rule | 0.091 [0.000, 0.199] | 0.000 | 0.000 | 0.273 | 0.57 / 1.00 / 1.00 |
| (a) claude-examples (3 seeds) | 0.029 [0.010, 0.053] | 0.005 | 0.007 | 0.075 | 0.67 / 0.86 / 0.29 |
| (b) cheapest-label | 0.234 [0.021, 0.564] | 0.429 | 0.000 | 0.273 | 1.00 / 1.00 / 1.00 |
| (c) shuffled-Claude | 0.488 [0.272, 0.793] | 0.835 | 0.146 | 0.484 | 0.77 / 0.91 / 0.71 |
| answer-trained ceiling lr 1e-4 | 0.059 [0.030, 0.093] | 0.005 | 0.102 | 0.069 | 0.59 / 0.51 / 0.30 |
| teacher-distil (3 seeds; reported only) | 0.197 [0.115, 0.291] | 0.254 | 0.146 | 0.191 | 0.49 / 0.51 / 0.49 |
| our-method-distil (3 seeds; reported only) | 0.293 [0.133, 0.480] | 0.393 | 0.343 | 0.141 | 0.39 / 0.25 / 0.33 |

letter mass: plain 0.85, (a) 1.00

Frozen rule (six conditions):
- 1. plain - a: +0.617 [+0.281, +1.011], lower bound > 0: **yes**
- 2. (b) - a: +0.205 [+0.007, +0.528], lower bound > 0: **yes**
- 3. always-cheapest - a: +0.205 [+0.007, +0.528], lower bound > 0: **yes**
- 4. plain - a on below cells (7) [descriptive: fewer than 8 below cells, not part of this set's outcome]: +1.303 [+0.631, +2.060], lower bound > 0: **yes**
- 5. type means (a) minus plain: below -1.303, at_or_above -0.462, no_cost -0.087 (each <= +0.05): **yes**
- 6. letter mass 1.00 vs 0.9 x plain 0.77: **yes**

**Outcome for test_hard/hard_grid: PASSED (condition 4 descriptive: fewer than 8 below cells)**

Reported, outside the rule:
- plain - stated-cost rule: +0.555 [+0.189, +0.974], lower bound > 0: **yes**
- stated-cost rule - a: +0.062 [-0.011, +0.154], lower bound > 0: **no**
- plain - answer-trained ceiling lr 1e-4: +0.587 [+0.257, +0.977], lower bound > 0: **yes**
- answer-trained ceiling lr 1e-4 - a: +0.030 [+0.003, +0.063], lower bound > 0: **yes**
- plain - teacher-distil (3 seeds; reported only): +0.449 [+0.166, +0.792], lower bound > 0: **yes**
- teacher-distil (3 seeds; reported only) - a: +0.168 [+0.089, +0.262], lower bound > 0: **yes**
- plain - our-method-distil (3 seeds; reported only): +0.354 [+0.111, +0.683], lower bound > 0: **yes**
- our-method-distil (3 seeds; reported only) - a: +0.264 [+0.102, +0.454], lower bound > 0: **yes**
- (b) - a on below cells: +0.424 [-0.006, +1.281], lower bound > 0: **no**
- (c) - a on below cells: +0.831 [+0.290, +1.612], lower bound > 0: **yes**
- (b) - a on no_cost cells: +0.199 [-0.006, +0.419], lower bound > 0: **no**
- (c) - a on no_cost cells: +0.409 [+0.311, +0.519], lower bound > 0: **yes**
- per-seed: plain - claude_examples_s0: +0.624 [+0.288, +1.016], lower bound > 0: **yes**
- per-seed: (b) - claude_examples_s0: +0.212 [+0.007, +0.541], lower bound > 0: **yes**
- per-seed: always-cheapest - claude_examples_s0: +0.212 [+0.007, +0.541], lower bound > 0: **yes**
- per-seed: plain - claude_examples_s1: +0.623 [+0.288, +1.017], lower bound > 0: **yes**
- per-seed: (b) - claude_examples_s1: +0.211 [+0.015, +0.533], lower bound > 0: **yes**
- per-seed: always-cheapest - claude_examples_s1: +0.211 [+0.015, +0.533], lower bound > 0: **yes**
- per-seed: plain - claude_examples_s2: +0.605 [+0.269, +1.000], lower bound > 0: **yes**
- per-seed: (b) - claude_examples_s2: +0.193 [-0.003, +0.515], lower bound > 0: **no**
- per-seed: always-cheapest - claude_examples_s2: +0.193 [-0.003, +0.515], lower bound > 0: **no**
- wording check: (c) - a on below cells: +0.831 [+0.290, +1.612], lower bound > 0: **yes**
- wording check: (c) - a on no_cost cells: +0.409 [+0.311, +0.519], lower bound > 0: **yes**
- wording check: plain - a on the 21 cells whose current label key is not in the 100 training cells: +0.617 [+0.281, +1.011], lower bound > 0: **yes**
- WORDING FLAGS (fixed in the plan): 'beyond shuffled labels' allowed: **yes**; 'generalises to cells with new label keys' allowed: **yes** (else a pass is worded as holding on the same generator, largely on repeated parameter combinations); 'transfer to unseen V / grid / wording' allowed only if test_hard as a whole passed (test_hard: PASSED) and this slice passed
- by type, (a) minus ceiling: below -0.001, at_or_above -0.095, no_cost +0.006
- per-run soft regret (a): claude_examples_s0 0.022; claude_examples_s1 0.023; claude_examples_s2 0.041
- per-run soft regret (b): cheapest_label_s0 0.234
- per-run soft regret (c): shuffled_claude_s0 0.488
- per-run soft regret (ceiling): ceiling_s0 0.059
- per-run soft regret (teacher): teacher_s0 0.190; teacher_s1 0.158; teacher_s2 0.243
- per-run soft regret (method): method_s0 0.297; method_s1 0.273; method_s2 0.308
- slope of the expected offer on the stated cost, below cells: (a) 0.31 [-0.27, 0.66], plain 0.29 (7 of 10000 resamples dropped for a single stated cost), oracle 0.06
- overlap with the 100 training cells, current key: 0 overlapping, 21 not; non-overlapping: plain - a +0.617 [+0.281, +1.011], (b) - a +0.205 [+0.007, +0.528]
- overlap with the 100 training cells, V and C only: 17 overlapping, 4 not; too few non-overlapping cells for an interval

## test_hard/hard_wording: 21 cells (below 7, at_or_above 7, no_cost 7)

| Arm | all [95%] | below | at_or_above | no_cost | cheapest-option mass by type |
| --- | --- | --- | --- | --- | --- |
| plain | 0.769 [0.494, 1.059] | 1.298 | 0.646 | 0.363 | 0.15 / 0.11 / 0.02 |
| always-cheapest | 0.463 [0.162, 0.813] | 0.286 | 0.000 | 1.105 | 1.00 / 1.00 / 1.00 |
| stated-cost rule | 0.368 [0.105, 0.692] | 0.000 | 0.000 | 1.105 | 0.86 / 1.00 / 1.00 |
| (a) claude-examples (3 seeds) | 0.082 [0.027, 0.169] | 0.031 | 0.005 | 0.210 | 0.84 / 0.91 / 0.19 |
| (b) cheapest-label | 0.464 [0.162, 0.813] | 0.286 | 0.000 | 1.105 | 1.00 / 1.00 / 1.00 |
| (c) shuffled-Claude | 0.810 [0.582, 1.054] | 1.039 | 0.427 | 0.965 | 0.45 / 0.66 / 0.67 |
| answer-trained ceiling lr 1e-4 | 0.043 [0.010, 0.084] | 0.004 | 0.052 | 0.073 | 0.85 / 0.68 / 0.16 |
| teacher-distil (3 seeds; reported only) | 0.421 [0.261, 0.623] | 0.403 | 0.214 | 0.646 | 0.63 / 0.63 / 0.38 |
| our-method-distil (3 seeds; reported only) | 0.475 [0.293, 0.695] | 0.381 | 0.323 | 0.723 | 0.61 / 0.46 / 0.26 |

letter mass: plain 0.78, (a) 1.00

Frozen rule (six conditions):
- 1. plain - a: +0.687 [+0.413, +0.982], lower bound > 0: **yes**
- 2. (b) - a: +0.382 [+0.128, +0.675], lower bound > 0: **yes**
- 3. always-cheapest - a: +0.382 [+0.128, +0.675], lower bound > 0: **yes**
- 4. plain - a on below cells (7) [descriptive: fewer than 8 below cells, not part of this set's outcome]: +1.266 [+0.892, +1.666], lower bound > 0: **yes**
- 5. type means (a) minus plain: below -1.266, at_or_above -0.641, no_cost -0.153 (each <= +0.05): **yes**
- 6. letter mass 1.00 vs 0.9 x plain 0.70: **yes**

**Outcome for test_hard/hard_wording: PASSED (condition 4 descriptive: fewer than 8 below cells)**

Reported, outside the rule:
- plain - stated-cost rule: +0.401 [-0.048, +0.834], lower bound > 0: **no**
- stated-cost rule - a: +0.286 [+0.071, +0.540], lower bound > 0: **yes**
- plain - answer-trained ceiling lr 1e-4: +0.726 [+0.459, +1.007], lower bound > 0: **yes**
- answer-trained ceiling lr 1e-4 - a: -0.039 [-0.103, +0.017], lower bound > 0: **no**
- plain - teacher-distil (3 seeds; reported only): +0.348 [+0.065, +0.640], lower bound > 0: **yes**
- teacher-distil (3 seeds; reported only) - a: +0.339 [+0.225, +0.470], lower bound > 0: **yes**
- plain - our-method-distil (3 seeds; reported only): +0.294 [-0.023, +0.623], lower bound > 0: **no**
- our-method-distil (3 seeds; reported only) - a: +0.393 [+0.249, +0.547], lower bound > 0: **yes**
- (b) - a on below cells: +0.254 [-0.058, +0.826], lower bound > 0: **no**
- (c) - a on below cells: +1.007 [+0.750, +1.351], lower bound > 0: **yes**
- (b) - a on no_cost cells: +0.895 [+0.436, +1.326], lower bound > 0: **yes**
- (c) - a on no_cost cells: +0.755 [+0.482, +1.030], lower bound > 0: **yes**
- per-seed: plain - claude_examples_s0: +0.722 [+0.447, +1.010], lower bound > 0: **yes**
- per-seed: (b) - claude_examples_s0: +0.417 [+0.146, +0.730], lower bound > 0: **yes**
- per-seed: always-cheapest - claude_examples_s0: +0.417 [+0.145, +0.730], lower bound > 0: **yes**
- per-seed: plain - claude_examples_s1: +0.710 [+0.434, +1.004], lower bound > 0: **yes**
- per-seed: (b) - claude_examples_s1: +0.405 [+0.142, +0.711], lower bound > 0: **yes**
- per-seed: always-cheapest - claude_examples_s1: +0.405 [+0.142, +0.711], lower bound > 0: **yes**
- per-seed: plain - claude_examples_s2: +0.629 [+0.350, +0.930], lower bound > 0: **yes**
- per-seed: (b) - claude_examples_s2: +0.323 [+0.087, +0.592], lower bound > 0: **yes**
- per-seed: always-cheapest - claude_examples_s2: +0.323 [+0.087, +0.592], lower bound > 0: **yes**
- wording check: (c) - a on below cells: +1.007 [+0.750, +1.351], lower bound > 0: **yes**
- wording check: (c) - a on no_cost cells: +0.755 [+0.482, +1.030], lower bound > 0: **yes**
- wording check: plain - a on the 12 cells whose current label key is not in the 100 training cells: +0.528 [+0.236, +0.864], lower bound > 0: **yes**
- WORDING FLAGS (fixed in the plan): 'beyond shuffled labels' allowed: **yes**; 'generalises to cells with new label keys' allowed: **yes** (else a pass is worded as holding on the same generator, largely on repeated parameter combinations); 'transfer to unseen V / grid / wording' allowed only if test_hard as a whole passed (test_hard: PASSED) and this slice passed
- by type, (a) minus ceiling: below +0.028, at_or_above -0.047, no_cost +0.137
- per-run soft regret (a): claude_examples_s0 0.047; claude_examples_s1 0.059; claude_examples_s2 0.140
- per-run soft regret (b): cheapest_label_s0 0.464
- per-run soft regret (c): shuffled_claude_s0 0.810
- per-run soft regret (ceiling): ceiling_s0 0.043
- per-run soft regret (teacher): teacher_s0 0.424; teacher_s1 0.395; teacher_s2 0.445
- per-run soft regret (method): method_s0 0.493; method_s1 0.466; method_s2 0.467
- slope of the expected offer on the stated cost, below cells: (a) 0.69 [0.29, 0.93], plain 0.43 (211 of 10000 resamples dropped for a single stated cost), oracle 0.69
- overlap with the 100 training cells, current key: 9 overlapping, 12 not; non-overlapping: plain - a +0.528 [+0.236, +0.864], (b) - a +0.449 [+0.097, +0.845]
- overlap with the 100 training cells, V and C only: 20 overlapping, 1 not; too few non-overlapping cells for an interval

## test_hard/hard_grid D: 15 cells (below 5, at_or_above 4, no_cost 6)

| Arm | all [95%] | below | at_or_above | no_cost | cheapest-option mass by type |
| --- | --- | --- | --- | --- | --- |
| plain | 0.710 [0.264, 1.236] | 1.541 | 0.505 | 0.156 | 0.00 / 0.00 / 0.00 |
| always-cheapest | 0.327 [0.044, 0.781] | 0.600 | 0.000 | 0.319 | 1.00 / 1.00 / 1.00 |
| stated-cost rule | 0.127 [0.000, 0.270] | 0.000 | 0.000 | 0.319 | 0.40 / 1.00 / 1.00 |
| (a) claude-examples (3 seeds) | 0.037 [0.010, 0.068] | 0.006 | 0.002 | 0.086 | 0.54 / 0.76 / 0.18 |
| (b) cheapest-label | 0.327 [0.044, 0.781] | 0.600 | 0.000 | 0.319 | 1.00 / 1.00 / 1.00 |
| (c) shuffled-Claude | 0.530 [0.251, 0.939] | 0.879 | 0.114 | 0.517 | 0.88 / 0.92 / 0.71 |
| answer-trained ceiling lr 1e-4 | 0.057 [0.026, 0.090] | 0.004 | 0.089 | 0.079 | 0.44 / 0.41 / 0.19 |
| teacher-distil (3 seeds; reported only) | 0.223 [0.113, 0.349] | 0.290 | 0.166 | 0.206 | 0.35 / 0.34 / 0.46 |
| our-method-distil (3 seeds; reported only) | 0.300 [0.092, 0.554] | 0.468 | 0.332 | 0.138 | 0.20 / 0.14 / 0.33 |

letter mass: plain 0.84, (a) 1.00

Frozen rule (six conditions):
- 1. plain - a: +0.673 [+0.219, +1.205], lower bound > 0: **yes**
- 2. (b) - a: +0.290 [+0.018, +0.738], lower bound > 0: **yes**
- 3. always-cheapest - a: +0.290 [+0.018, +0.738], lower bound > 0: **yes**
- 4. plain - a on below cells (5) [descriptive: fewer than 8 below cells, not part of this set's outcome]: +1.535 [+0.670, +2.400], lower bound > 0: **yes**
- 5. type means (a) minus plain: below -1.535, at_or_above -0.502, no_cost -0.069 (each <= +0.05): **yes**
- 6. letter mass 1.00 vs 0.9 x plain 0.76: **yes**

**Outcome for test_hard/hard_grid D: PASSED (condition 4 descriptive: fewer than 8 below cells)**

Reported, outside the rule:
- plain - stated-cost rule: +0.583 [+0.080, +1.155], lower bound > 0: **yes**
- stated-cost rule - a: +0.090 [-0.012, +0.214], lower bound > 0: **no**
- plain - answer-trained ceiling lr 1e-4: +0.654 [+0.203, +1.182], lower bound > 0: **yes**
- answer-trained ceiling lr 1e-4 - a: +0.020 [-0.006, +0.052], lower bound > 0: **no**
- plain - teacher-distil (3 seeds; reported only): +0.487 [+0.107, +0.966], lower bound > 0: **yes**
- teacher-distil (3 seeds; reported only) - a: +0.186 [+0.080, +0.314], lower bound > 0: **yes**
- plain - our-method-distil (3 seeds; reported only): +0.410 [+0.103, +0.852], lower bound > 0: **yes**
- our-method-distil (3 seeds; reported only) - a: +0.263 [+0.040, +0.521], lower bound > 0: **yes**
- (b) - a on below cells: +0.594 [-0.008, +1.795], lower bound > 0: **no**
- (c) - a on below cells: +0.873 [+0.158, +1.927], lower bound > 0: **yes**
- (b) - a on no_cost cells: +0.232 [+0.005, +0.466], lower bound > 0: **yes**
- (c) - a on no_cost cells: +0.430 [+0.321, +0.552], lower bound > 0: **yes**
- per-seed: plain - claude_examples_s0: +0.680 [+0.225, +1.210], lower bound > 0: **yes**
- per-seed: (b) - claude_examples_s0: +0.297 [+0.013, +0.748], lower bound > 0: **yes**
- per-seed: always-cheapest - claude_examples_s0: +0.297 [+0.013, +0.748], lower bound > 0: **yes**
- per-seed: plain - claude_examples_s1: +0.679 [+0.219, +1.215], lower bound > 0: **yes**
- per-seed: (b) - claude_examples_s1: +0.296 [+0.023, +0.733], lower bound > 0: **yes**
- per-seed: always-cheapest - claude_examples_s1: +0.296 [+0.023, +0.733], lower bound > 0: **yes**
- per-seed: plain - claude_examples_s2: +0.662 [+0.207, +1.194], lower bound > 0: **yes**
- per-seed: (b) - claude_examples_s2: +0.279 [+0.009, +0.722], lower bound > 0: **yes**
- per-seed: always-cheapest - claude_examples_s2: +0.279 [+0.009, +0.722], lower bound > 0: **yes**
- wording check: (c) - a on below cells: +0.873 [+0.158, +1.927], lower bound > 0: **yes**
- wording check: (c) - a on no_cost cells: +0.430 [+0.321, +0.552], lower bound > 0: **yes**
- wording check: plain - a on the 15 cells whose current label key is not in the 100 training cells: +0.673 [+0.219, +1.205], lower bound > 0: **yes**
- WORDING FLAGS (fixed in the plan): 'beyond shuffled labels' allowed: **yes**; 'generalises to cells with new label keys' allowed: **yes** (else a pass is worded as holding on the same generator, largely on repeated parameter combinations); 'transfer to unseen V / grid / wording' allowed only if test_hard as a whole passed (test_hard: PASSED) and this slice passed
- by type, (a) minus ceiling: below +0.001, at_or_above -0.086, no_cost +0.008
- per-run soft regret (a): claude_examples_s0 0.031; claude_examples_s1 0.032; claude_examples_s2 0.048
- per-run soft regret (b): cheapest_label_s0 0.327
- per-run soft regret (c): shuffled_claude_s0 0.530
- per-run soft regret (ceiling): ceiling_s0 0.057
- per-run soft regret (teacher): teacher_s0 0.216; teacher_s1 0.179; teacher_s2 0.274
- per-run soft regret (method): method_s0 0.307; method_s1 0.289; method_s2 0.304
- slope of the expected offer on the stated cost, below cells: (a) 0.37 [-0.70, 0.66], plain 0.29 (226 of 10000 resamples dropped for a single stated cost), oracle 0.10
- overlap with the 100 training cells, current key: 0 overlapping, 15 not; non-overlapping: plain - a +0.673 [+0.219, +1.205], (b) - a +0.290 [+0.018, +0.738]
- overlap with the 100 training cells, V and C only: 12 overlapping, 3 not; too few non-overlapping cells for an interval

## test_hard/hard_grid E (descriptive only, <8 cells): 6 cells (below 2, at_or_above 3, no_cost 1)

| Arm | all [95%] | below | at_or_above | no_cost | cheapest-option mass by type |
| --- | --- | --- | --- | --- | --- |
| plain | 0.486 [0.199, 0.790] | 0.726 | 0.422 | 0.199 | 0.37 / 0.38 / 0.04 |
| always-cheapest | 0.000 [0.000, 0.000] | 0.000 | 0.000 | 0.000 | 1.00 / 1.00 / 1.00 |
| stated-cost rule | 0.000 [0.000, 0.000] | 0.000 | 0.000 | 0.000 | 1.00 / 1.00 / 1.00 |
| (a) claude-examples (3 seeds) | 0.008 [0.002, 0.016] | 0.002 | 0.014 | 0.004 | 1.00 / 0.99 / 0.99 |
| (b) cheapest-label | 0.000 [0.000, 0.000] | 0.000 | 0.000 | 0.000 | 1.00 / 1.00 / 1.00 |
| (c) shuffled-Claude | 0.384 [0.167, 0.652] | 0.726 | 0.189 | 0.287 | 0.50 / 0.90 / 0.69 |
| answer-trained ceiling lr 1e-4 | 0.064 [0.005, 0.151] | 0.007 | 0.120 | 0.011 | 0.99 / 0.66 / 0.95 |
| teacher-distil (3 seeds; reported only) | 0.131 [0.074, 0.173] | 0.163 | 0.119 | 0.101 | 0.86 / 0.73 / 0.72 |
| our-method-distil (3 seeds; reported only) | 0.274 [0.097, 0.458] | 0.206 | 0.357 | 0.160 | 0.88 / 0.40 / 0.37 |

letter mass: plain 0.88, (a) 1.00

Frozen rule (six conditions):
- 1. plain - a: +0.477 [+0.190, +0.781], lower bound > 0: **yes**
- 2. (b) - a: -0.008 [-0.016, -0.002], lower bound > 0: **no**
- 3. always-cheapest - a: -0.008 [-0.016, -0.002], lower bound > 0: **no**
- 4. plain - a on below cells (2) [descriptive: fewer than 8 below cells, not part of this set's outcome]: only 2 cells, no interval computed
- 5. type means (a) minus plain: below -0.724, at_or_above -0.407, no_cost -0.195 (each <= +0.05): **yes**
- 6. letter mass 1.00 vs 0.9 x plain 0.79: **yes**

**Outcome for test_hard/hard_grid E (descriptive only, <8 cells): DESCRIPTIVE ONLY: fewer than 8 cells, no PASSED/NOT PASSED label (conditions failing: [2, 3])** (failed conditions: [2, 3]); condition 4 not applicable (no below cells)

Reported, outside the rule:
- plain - stated-cost rule: +0.486 [+0.199, +0.790], lower bound > 0: **yes**
- stated-cost rule - a: -0.008 [-0.016, -0.002], lower bound > 0: **no**
- plain - answer-trained ceiling lr 1e-4: +0.421 [+0.169, +0.715], lower bound > 0: **yes**
- answer-trained ceiling lr 1e-4 - a: +0.056 [+0.003, +0.137], lower bound > 0: **yes**
- plain - teacher-distil (3 seeds; reported only): +0.355 [+0.095, +0.628], lower bound > 0: **yes**
- teacher-distil (3 seeds; reported only) - a: +0.122 [+0.071, +0.161], lower bound > 0: **yes**
- plain - our-method-distil (3 seeds; reported only): +0.212 [-0.038, +0.564], lower bound > 0: **no**
- our-method-distil (3 seeds; reported only) - a: +0.265 [+0.096, +0.441], lower bound > 0: **yes**
- (b) - a on below cells: only 2 cells, no interval computed
- (c) - a on below cells: only 2 cells, no interval computed
- (b) - a on no_cost cells: only 1 cells, no interval computed
- (c) - a on no_cost cells: only 1 cells, no interval computed
- per-seed: plain - claude_examples_s0: +0.485 [+0.198, +0.789], lower bound > 0: **yes**
- per-seed: (b) - claude_examples_s0: -0.001 [-0.002, -0.000], lower bound > 0: **no**
- per-seed: always-cheapest - claude_examples_s0: -0.001 [-0.002, -0.000], lower bound > 0: **no**
- per-seed: plain - claude_examples_s1: +0.484 [+0.196, +0.788], lower bound > 0: **yes**
- per-seed: (b) - claude_examples_s1: -0.002 [-0.006, -0.000], lower bound > 0: **no**
- per-seed: always-cheapest - claude_examples_s1: -0.002 [-0.006, -0.000], lower bound > 0: **no**
- per-seed: plain - claude_examples_s2: +0.464 [+0.178, +0.767], lower bound > 0: **yes**
- per-seed: (b) - claude_examples_s2: -0.022 [-0.039, -0.004], lower bound > 0: **no**
- per-seed: always-cheapest - claude_examples_s2: -0.022 [-0.039, -0.004], lower bound > 0: **no**
- wording check: (c) - a on below cells: only 2 cells, no interval computed
- wording check: (c) - a on no_cost cells: only 1 cells, no interval computed
- WORDING FLAGS (fixed in the plan): 'beyond shuffled labels' allowed: **no**; 'generalises to cells with new label keys' allowed: **no** (else a pass is worded as holding on the same generator, largely on repeated parameter combinations); 'transfer to unseen V / grid / wording' allowed only if test_hard as a whole passed (test_hard: PASSED) and this slice passed
- by type, (a) minus ceiling: below -0.005, at_or_above -0.106, no_cost -0.008
- per-run soft regret (a): claude_examples_s0 0.001; claude_examples_s1 0.002; claude_examples_s2 0.022
- per-run soft regret (b): cheapest_label_s0 0.000
- per-run soft regret (c): shuffled_claude_s0 0.384
- per-run soft regret (ceiling): ceiling_s0 0.064
- per-run soft regret (teacher): teacher_s0 0.123; teacher_s1 0.103; teacher_s2 0.166
- per-run soft regret (method): method_s0 0.271; method_s1 0.231; method_s2 0.319
- slope of the expected offer on the stated cost, below cells: (a) 0.00 [0.00, 0.00], plain 0.29 (4881 of 10000 resamples dropped for a single stated cost), oracle 0.00
- overlap with the 100 training cells, current key: 0 overlapping, 6 not; non-overlapping: plain - a +0.477 [+0.190, +0.781], (b) - a -0.008 [-0.016, -0.002]
- overlap with the 100 training cells, V and C only: 5 overlapping, 1 not; too few non-overlapping cells for an interval

