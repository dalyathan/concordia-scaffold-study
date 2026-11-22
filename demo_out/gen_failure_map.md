# Failure map of plain Gemma 2 9B-it on generated TRAIN and TUNE cells (the test sets were not scored)

342 cells (300 train, 42 tune), 2 name variants each, five orders. Soft regret = best expected payoff minus the model's expected payoff (order-averaged first-token probabilities). Cell-clustered bootstrap (10,000, seed 0). Baselines use the same labels: uniform over the five offers, always-cheapest, and a stated-cost rule (cheapest grid price >= C if C < V, else cheapest).

## train

Overall: soft regret 0.652 [0.573, 0.731], hard regret 0.576 [0.496, 0.659], mass on best set 0.45 (chance 0.34), letter mass 0.81; baselines: uniform 1.204, always-cheapest 0.573, stated-cost rule 0.157.

### train: by type

| type | cells | soft regret [95%] | mass on best set (chance) | top in best set | letter mass | always-cheapest | stated-cost rule | uniform |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| at_or_above | 100 | 0.298 [0.216, 0.383] | 0.79 (0.52) | 0.80 | 0.87 | 0.000 | 0.000 | 1.054 |
| below | 100 | 1.436 [1.326, 1.552] | 0.07 (0.20) | 0.07 | 0.80 | 1.250 | 0.000 | 1.888 |
| no_cost | 100 | 0.221 [0.184, 0.263] | 0.49 (0.29) | 0.50 | 0.75 | 0.470 | 0.470 | 0.669 |

### train: by resale-value band

| Vband | cells | soft regret [95%] | mass on best set (chance) | top in best set | letter mass | always-cheapest | stated-cost rule | uniform |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2-3 | 94 | 0.534 [0.437, 0.634] | 0.52 (0.32) | 0.49 | 0.86 | 0.022 | 0.001 | 1.460 |
| 4-5 | 104 | 0.375 [0.279, 0.477] | 0.62 (0.43) | 0.69 | 0.83 | 0.178 | 0.043 | 0.934 |
| 6-7 | 56 | 0.992 [0.798, 1.188] | 0.20 (0.25) | 0.20 | 0.76 | 1.044 | 0.223 | 1.242 |
| 8-9 | 46 | 1.102 [0.829, 1.387] | 0.23 (0.26) | 0.17 | 0.71 | 2.019 | 0.649 | 1.242 |

### train: by price grid

| grid | cells | soft regret [95%] | mass on best set (chance) | top in best set | letter mass | always-cheapest | stated-cost rule | uniform |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | 84 | 0.631 [0.470, 0.804] | 0.50 (0.36) | 0.50 | 0.76 | 0.988 | 0.321 | 0.977 |
| B | 98 | 0.679 [0.526, 0.834] | 0.43 (0.35) | 0.39 | 0.81 | 0.591 | 0.162 | 1.114 |
| C | 118 | 0.643 [0.544, 0.747] | 0.44 (0.30) | 0.48 | 0.84 | 0.263 | 0.035 | 1.439 |

### train: by wording

| wording | cells | soft regret [95%] | mass on best set (chance) | top in best set | letter mass | always-cheapest | stated-cost rule | uniform |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 160 | 0.690 [0.585, 0.798] | 0.43 (0.34) | 0.44 | 0.81 | 0.529 | 0.148 | 1.226 |
| 1 | 140 | 0.607 [0.490, 0.729] | 0.47 (0.34) | 0.47 | 0.80 | 0.623 | 0.166 | 1.179 |

### train: by seller line (collinear with type)

| line | cells | soft regret [95%] | mass on best set (chance) | top in best set | letter mass | always-cheapest | stated-cost rule | uniform |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| information | 200 | 0.867 [0.761, 0.974] | 0.43 (0.36) | 0.43 | 0.84 | 0.625 | 0.000 | 1.471 |
| neutral | 49 | 0.213 [0.157, 0.281] | 0.49 (0.29) | 0.45 | 0.77 | 0.400 | 0.400 | 0.658 |
| pressure | 51 | 0.229 [0.181, 0.280] | 0.49 (0.29) | 0.55 | 0.73 | 0.536 | 0.536 | 0.680 |

### train: by stated cost relative to the grid (information cells and no-cost)

| crel | cells | soft regret [95%] | mass on best set (chance) | top in best set | letter mass | always-cheapest | stated-cost rule | uniform |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| C below grid min | 41 | 1.070 [0.981, 1.164] | 0.12 (0.20) | 0.12 | 0.82 | 0.000 | 0.000 | 2.000 |
| C on grid | 159 | 0.814 [0.686, 0.945] | 0.51 (0.40) | 0.52 | 0.84 | 0.786 | 0.000 | 1.335 |
| no stated cost | 100 | 0.221 [0.184, 0.263] | 0.49 (0.29) | 0.50 | 0.75 | 0.470 | 0.470 | 0.669 |

### train: type = below, by V band

| Vband | cells | soft regret [95%] | mass on best set (chance) | top in best set | letter mass | always-cheapest | stated-cost rule | uniform |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2-3 | 17 | 1.074 [0.928, 1.224] | 0.18 (0.20) | 0.12 | 0.83 | 0.118 | 0.000 | 1.929 |
| 4-5 | 28 | 1.121 [0.989, 1.256] | 0.12 (0.20) | 0.18 | 0.83 | 0.500 | 0.000 | 1.843 |
| 6-7 | 34 | 1.532 [1.386, 1.679] | 0.01 (0.20) | 0.00 | 0.79 | 1.353 | 0.000 | 1.782 |
| 8-9 | 21 | 1.993 [1.704, 2.329] | 0.02 (0.20) | 0.00 | 0.76 | 3.000 | 0.000 | 2.086 |

### train: type = at_or_above, by V band

| Vband | cells | soft regret [95%] | mass on best set (chance) | top in best set | letter mass | always-cheapest | stated-cost rule | uniform |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2-3 | 52 | 0.506 [0.377, 0.642] | 0.65 (0.38) | 0.63 | 0.88 | 0.000 | 0.000 | 1.504 |
| 4-5 | 47 | 0.074 [0.027, 0.131] | 0.94 (0.66) | 0.98 | 0.86 | 0.000 | 0.000 | 0.574 |
| 6-7 | 1 | 0.001 [0.001, 0.001] | 1.00 (0.80) | 1.00 | 0.87 | 0.000 | 0.000 | 0.200 |

### train: type = no_cost, by V band

| Vband | cells | soft regret [95%] | mass on best set (chance) | top in best set | letter mass | always-cheapest | stated-cost rule | uniform |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2-3 | 25 | 0.226 [0.163, 0.295] | 0.47 (0.26) | 0.44 | 0.83 | 0.004 | 0.004 | 1.051 |
| 4-5 | 29 | 0.143 [0.098, 0.192] | 0.59 (0.29) | 0.72 | 0.80 | 0.156 | 0.156 | 0.639 |
| 6-7 | 21 | 0.166 [0.126, 0.211] | 0.48 (0.30) | 0.48 | 0.70 | 0.594 | 0.594 | 0.417 |
| 8-9 | 25 | 0.353 [0.251, 0.474] | 0.40 (0.31) | 0.32 | 0.66 | 1.195 | 1.195 | 0.533 |

### train: by number of best offers

| n_best | cells | soft regret [95%] | mass on best set (chance) | top in best set | letter mass | always-cheapest | stated-cost rule | uniform |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 174 | 1.030 [0.925, 1.135] | 0.17 (0.20) | 0.17 | 0.80 | 0.862 | 0.144 | 1.574 |
| 2 | 71 | 0.222 [0.172, 0.276] | 0.72 (0.40) | 0.73 | 0.79 | 0.309 | 0.309 | 0.813 |
| 3 | 33 | 0.016 [0.008, 0.025] | 0.99 (0.60) | 1.00 | 0.88 | 0.000 | 0.000 | 0.725 |
| 4 | 22 | 0.002 [0.002, 0.002] | 1.00 (0.80) | 1.00 | 0.83 | 0.000 | 0.000 | 0.255 |

### train: cells where the best payoff is <= 0 (arbitrary labels)

| best_le_0 | cells | soft regret [95%] | mass on best set (chance) | top in best set | letter mass | always-cheapest | stated-cost rule | uniform |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| False | 175 | 0.882 [0.769, 1.000] | 0.28 (0.24) | 0.30 | 0.77 | 0.983 | 0.268 | 1.258 |
| True | 125 | 0.329 [0.258, 0.403] | 0.70 (0.46) | 0.68 | 0.87 | 0.000 | 0.000 | 1.128 |

### train: stated cost inside the stated prior range

| C_in_prior | cells | soft regret [95%] | mass on best set (chance) | top in best set | letter mass | always-cheapest | stated-cost rule | uniform |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| False | 33 | 1.107 [0.925, 1.285] | 0.19 (0.25) | 0.18 | 0.79 | 0.303 | 0.000 | 1.782 |
| True | 167 | 0.819 [0.702, 0.942] | 0.48 (0.38) | 0.49 | 0.85 | 0.689 | 0.000 | 1.410 |

Position of the model's top offer in the grid (0 = cheapest): {0: 26, 1: 175, 2: 51, 3: 43, 4: 5}; best-offer positions in the labels (first best): {0: 198, 1: 37, 2: 33, 3: 23, 4: 9}

## tune

Overall: soft regret 0.657 [0.465, 0.862], hard regret 0.498 [0.319, 0.693], mass on best set 0.45 (chance 0.33), letter mass 0.81; baselines: uniform 1.260, always-cheapest 0.429, stated-cost rule 0.214.

### tune: by type

| type | cells | soft regret [95%] | mass on best set (chance) | top in best set | letter mass | always-cheapest | stated-cost rule | uniform |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| at_or_above | 14 | 0.391 [0.170, 0.656] | 0.74 (0.44) | 0.79 | 0.85 | 0.000 | 0.000 | 1.329 |
| below | 14 | 1.376 [1.144, 1.674] | 0.06 (0.20) | 0.07 | 0.81 | 0.643 | 0.000 | 1.871 |
| no_cost | 14 | 0.204 [0.113, 0.309] | 0.55 (0.34) | 0.57 | 0.76 | 0.643 | 0.643 | 0.580 |

### tune: by resale-value band

| Vband | cells | soft regret [95%] | mass on best set (chance) | top in best set | letter mass | always-cheapest | stated-cost rule | uniform |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2-3 | 12 | 0.478 [0.192, 0.784] | 0.64 (0.38) | 0.67 | 0.86 | 0.000 | 0.000 | 1.493 |
| 4-5 | 16 | 0.644 [0.364, 0.949] | 0.43 (0.33) | 0.50 | 0.83 | 0.087 | 0.025 | 1.267 |
| 6-7 | 9 | 0.780 [0.365, 1.203] | 0.29 (0.27) | 0.33 | 0.81 | 0.667 | 0.222 | 1.133 |
| 8-9 | 5 | 0.908 [0.302, 1.925] | 0.33 (0.32) | 0.20 | 0.63 | 2.120 | 1.320 | 0.904 |

### tune: by price grid

| grid | cells | soft regret [95%] | mass on best set (chance) | top in best set | letter mass | always-cheapest | stated-cost rule | uniform |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | 11 | 0.499 [0.230, 0.790] | 0.53 (0.38) | 0.55 | 0.74 | 0.891 | 0.527 | 0.902 |
| B | 14 | 0.554 [0.251, 0.885] | 0.48 (0.37) | 0.43 | 0.82 | 0.171 | 0.171 | 1.209 |
| C | 17 | 0.845 [0.515, 1.220] | 0.37 (0.26) | 0.47 | 0.84 | 0.341 | 0.047 | 1.534 |

### tune: by wording

| wording | cells | soft regret [95%] | mass on best set (chance) | top in best set | letter mass | always-cheapest | stated-cost rule | uniform |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 18 | 0.777 [0.432, 1.157] | 0.47 (0.32) | 0.50 | 0.81 | 0.478 | 0.089 | 1.378 |
| 1 | 24 | 0.568 [0.366, 0.783] | 0.44 (0.33) | 0.46 | 0.81 | 0.392 | 0.308 | 1.171 |

### tune: by seller line (collinear with type)

| line | cells | soft regret [95%] | mass on best set (chance) | top in best set | letter mass | always-cheapest | stated-cost rule | uniform |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| information | 28 | 0.884 [0.633, 1.146] | 0.40 (0.32) | 0.43 | 0.83 | 0.321 | 0.000 | 1.600 |
| neutral | 10 | 0.207 [0.086, 0.351] | 0.63 (0.36) | 0.60 | 0.75 | 0.660 | 0.660 | 0.580 |
| pressure | 4 | 0.198 [0.111, 0.268] | 0.37 (0.30) | 0.50 | 0.79 | 0.600 | 0.600 | 0.580 |

### tune: by stated cost relative to the grid (information cells and no-cost)

| crel | cells | soft regret [95%] | mass on best set (chance) | top in best set | letter mass | always-cheapest | stated-cost rule | uniform |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| C below grid min | 3 | 1.035 [0.929, 1.147] | 0.05 (0.20) | 0.00 | 0.83 | 0.000 | 0.000 | 2.000 |
| C on grid | 25 | 0.866 [0.584, 1.159] | 0.44 (0.34) | 0.48 | 0.83 | 0.360 | 0.000 | 1.552 |
| no stated cost | 14 | 0.204 [0.113, 0.309] | 0.55 (0.34) | 0.57 | 0.76 | 0.643 | 0.643 | 0.580 |

### tune: type = below, by V band

| Vband | cells | soft regret [95%] | mass on best set (chance) | top in best set | letter mass | always-cheapest | stated-cost rule | uniform |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2-3 | 1 | 1.010 [1.010, 1.010] | 0.00 (0.20) | 0.00 | 0.91 | 0.000 | 0.000 | 2.000 |
| 4-5 | 7 | 1.256 [1.045, 1.503] | 0.11 (0.20) | 0.14 | 0.82 | 0.143 | 0.000 | 1.914 |
| 6-7 | 5 | 1.315 [1.084, 1.610] | 0.01 (0.20) | 0.00 | 0.81 | 0.800 | 0.000 | 1.720 |
| 8-9 | 1 | 2.896 [2.896, 2.896] | 0.01 (0.20) | 0.00 | 0.68 | 4.000 | 0.000 | 2.200 |

### tune: type = at_or_above, by V band

| Vband | cells | soft regret [95%] | mass on best set (chance) | top in best set | letter mass | always-cheapest | stated-cost rule | uniform |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2-3 | 10 | 0.472 [0.166, 0.815] | 0.67 (0.38) | 0.70 | 0.86 | 0.000 | 0.000 | 1.560 |
| 4-5 | 4 | 0.190 [0.002, 0.377] | 0.90 (0.60) | 1.00 | 0.84 | 0.000 | 0.000 | 0.750 |

### tune: type = no_cost, by V band

| Vband | cells | soft regret [95%] | mass on best set (chance) | top in best set | letter mass | always-cheapest | stated-cost rule | uniform |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2-3 | 1 | 0.007 [0.007, 0.007] | 0.99 (0.60) | 1.00 | 0.81 | 0.000 | 0.000 | 0.320 |
| 4-5 | 5 | 0.152 [0.039, 0.285] | 0.51 (0.28) | 0.60 | 0.83 | 0.080 | 0.080 | 0.775 |
| 6-7 | 4 | 0.112 [0.075, 0.186] | 0.64 (0.35) | 0.75 | 0.80 | 0.500 | 0.500 | 0.400 |
| 8-9 | 4 | 0.411 [0.273, 0.582] | 0.41 (0.35) | 0.25 | 0.62 | 1.650 | 1.650 | 0.580 |

### tune: by number of best offers

| n_best | cells | soft regret [95%] | mass on best set (chance) | top in best set | letter mass | always-cheapest | stated-cost rule | uniform |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 22 | 1.096 [0.850, 1.365] | 0.11 (0.20) | 0.14 | 0.82 | 0.527 | 0.118 | 1.667 |
| 2 | 15 | 0.231 [0.119, 0.355] | 0.76 (0.40) | 0.80 | 0.80 | 0.427 | 0.427 | 0.915 |
| 3 | 3 | 0.010 [0.007, 0.014] | 0.99 (0.60) | 1.00 | 0.78 | 0.000 | 0.000 | 0.640 |
| 4 | 2 | 0.002 [0.001, 0.003] | 1.00 (0.80) | 1.00 | 0.82 | 0.000 | 0.000 | 0.300 |

### tune: cells where the best payoff is <= 0 (arbitrary labels)

| best_le_0 | cells | soft regret [95%] | mass on best set (chance) | top in best set | letter mass | always-cheapest | stated-cost rule | uniform |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| False | 27 | 0.819 [0.568, 1.093] | 0.28 (0.26) | 0.30 | 0.78 | 0.667 | 0.333 | 1.259 |
| True | 15 | 0.365 [0.148, 0.622] | 0.75 (0.45) | 0.80 | 0.85 | 0.000 | 0.000 | 1.261 |

### tune: stated cost inside the stated prior range

| C_in_prior | cells | soft regret [95%] | mass on best set (chance) | top in best set | letter mass | always-cheapest | stated-cost rule | uniform |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| False | 3 | 0.916 [0.003, 1.815] | 0.38 (0.40) | 0.33 | 0.81 | 0.000 | 0.000 | 1.467 |
| True | 25 | 0.880 [0.619, 1.159] | 0.40 (0.31) | 0.44 | 0.83 | 0.360 | 0.000 | 1.616 |

Position of the model's top offer in the grid (0 = cheapest): {0: 2, 1: 33, 2: 4, 3: 3}; best-offer positions in the labels (first best): {0: 29, 1: 5, 2: 4, 3: 3, 4: 1}

## Train analogues of the hard slices (for reading the test-hard slices later)

### train: always-profitable regime (V >= largest price of the grid)

| type | cells | soft regret [95%] | mass on best set (chance) | top in best set | letter mass | always-cheapest | stated-cost rule | uniform |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| below | 52 | 1.769 [1.612, 1.934] | 0.02 (0.20) | 0.00 | 0.77 | 2.154 | 0.000 | 1.881 |
| no_cost | 52 | 0.249 [0.190, 0.319] | 0.44 (0.31) | 0.40 | 0.67 | 0.881 | 0.881 | 0.433 |

### train: V 8-9 on grid A

| type | cells | soft regret [95%] | mass on best set (chance) | top in best set | letter mass | always-cheapest | stated-cost rule | uniform |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| below | 4 | 2.428 [1.781, 3.097] | 0.04 (0.20) | 0.00 | 0.73 | 5.500 | 0.000 | 2.800 |
| no_cost | 7 | 0.665 [0.438, 0.915] | 0.23 (0.26) | 0.14 | 0.57 | 2.129 | 2.129 | 0.843 |

Label-key overlap (V, grid, C or prior) of tune cells with train cells: 30 of 42 (cells whose label is identical to a train cell's).

For the locked test sets (labels only, no scoring): test_same cells with a label key identical to a train cell: 43 of 60; test_hard: 18 of 62.

Cells at grid A, prior (1,5), V 2-6 (same game structure as the old cells; old test cells excluded by construction; old train/tune cells possible): train: 8, tune: 0, test_same: 0, test_hard: 0. Old adapters and old rule-teacher data must not be scored on this set.

