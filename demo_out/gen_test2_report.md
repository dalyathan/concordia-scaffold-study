# test2 sets: fresh locked test cells (CPU only, nothing scored)

seed 20261201; two name variants per cell; extension: grid F (8, 10, 12, 14, 16), resale values 10-15, seller wording index 3 (reserved for test2).

(counts of candidate evaluations, summed over the enumerations, not distinct cells: all-tie candidates dropped {'below': 1710, 'at_or_above': 1991}; original-study-space candidates excluded 256); no cell in either set is a tie
availability for test2_newkey (cells not used, not tie, pair not in the 300 train cells): {"below": {"in_range_pairs_available_cells": 119, "in_range_problems_available": 13, "extension_available_cells": 2799, "extension_problems_available": 196}, "at_or_above": {"in_range_pairs_available_cells": 7, "in_range_problems_available": 1, "extension_available_cells": 425, "extension_problems_available": 29}, "no_cost": {"in_range_pairs_available_cells": 11, "in_range_problems_available": 3, "extension_available_cells": 722, "extension_problems_available": 124}}

## test2_same: 120 cells, 240 cases

| type | cells | single best offer | in training ranges | extension |
| --- | --- | --- | --- | --- |
| below | 40 | 40 (100%) | 40 | 0 |
| at_or_above | 40 | 7 (18%) | 40 | 0 |
| no_cost | 40 | 24 (60%) | 40 | 0 |
| all | 120 | 71 (59%) | 120 | 0 |

V values: {2: 15, 3: 17, 4: 23, 5: 17, 6: 16, 7: 10, 8: 8, 9: 14}; grids: {'B': 45, 'A': 33, 'C': 42}; wordings: {0: 65, 1: 55}

Cells sharing a label key with training (counts of cells; by type below / at_or_above / no_cost):

| key | vs the 300 train cells | vs the 100 LoRA training cells |
| --- | --- | --- |
| current key (V, grid, C or prior) | 22 / 38 / 23 (total 83) | 11 / 30 / 7 (total 48) |
| stricter (V, C) key, C = none for no-cost cells | 35 / 38 / 40 (total 113) | 23 / 38 / 40 (total 101) |
| pair (V, C or cost range) | 35 / 38 / 39 (total 112) | 23 / 38 / 24 (total 85) |

Effective size and trivial references (label-only, nothing scored; soft regret = best payoff minus expected payoff of the policy; one value per cell, mean over cells):

| type | cells | distinct problems (V, grid, C or prior) | distinct pairs | best = cheapest price | mean best-set size | uniform-random regret | always-cheapest regret | stated-cost-rule regret | median margin best-second |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| below | 40 | 40 | 23 | 19 | 1.00 | 1.83 | 1.23 | 0.00 | 1.00 |
| at_or_above | 40 | 24 | 13 | 40 | 2.85 | 0.85 | 0.00 | 0.00 | 0.00 |
| no_cost | 40 | 40 | 30 | 15 | 1.40 | 0.72 | 0.52 | 0.52 | 0.11 |

Slices (pre-declared; never report one pooled number for test2_newkey):

| slice | below | at_or_above | no_cost |
| --- | --- | --- | --- |
| training ranges (no novelty) | 40 | 40 | 40 |
| new V only (>=10, grids A-C, wordings 0-1) | 0 | 0 | 0 |
| new grid F (any V, wordings 0-1) | 0 | 0 | 0 |
| new wording 3 (any V, grids A-C) | 0 | 0 | 0 |
| new grid F and new wording 3 | 0 | 0 | 0 |
| V 13-15 (the clean extension: V 10-12 also occur in test_hard) | 0 | 0 | 0 |
| label key (V, grid, C or prior) seen in the 100 LoRA cells | 11 | 30 | 7 |
| label key seen in the 300 train cells | 22 | 38 | 23 |

## test2_newkey: 120 cells, 240 cases

| type | cells | single best offer | in training ranges | extension |
| --- | --- | --- | --- | --- |
| below | 40 | 38 (95%) | 13 | 27 |
| at_or_above | 40 | 18 (45%) | 2 | 38 |
| no_cost | 40 | 38 (95%) | 3 | 37 |
| all | 120 | 94 (78%) | 18 | 102 |

V values: {2: 4, 6: 10, 7: 8, 8: 9, 9: 14, 10: 18, 11: 15, 12: 9, 13: 10, 14: 14, 15: 9}; grids: {'C': 13, 'B': 19, 'A': 15, 'F': 73}; wordings: {1: 38, 0: 32, 3: 50}

Cells sharing a label key with training (counts of cells; by type below / at_or_above / no_cost):

| key | vs the 300 train cells | vs the 100 LoRA training cells |
| --- | --- | --- |
| current key (V, grid, C or prior) | 0 / 0 / 0 (total 0) | 0 / 0 / 0 (total 0) |
| stricter (V, C) key, C = none for no-cost cells | 0 / 0 / 4 (total 4) | 0 / 0 / 4 (total 4) |
| pair (V, C or cost range) | 0 / 0 / 0 (total 0) | 0 / 0 / 0 (total 0) |

Effective size and trivial references (label-only, nothing scored; soft regret = best payoff minus expected payoff of the policy; one value per cell, mean over cells):

| type | cells | distinct problems (V, grid, C or prior) | distinct pairs | best = cheapest price | mean best-set size | uniform-random regret | always-cheapest regret | stated-cost-rule regret | median margin best-second |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| below | 40 | 40 | 25 | 20 | 1.10 | 3.23 | 2.48 | 0.00 | 1.50 |
| at_or_above | 40 | 24 | 23 | 40 | 2.00 | 2.57 | 0.00 | 0.00 | 0.00 |
| no_cost | 40 | 40 | 28 | 22 | 1.05 | 2.67 | 1.70 | 1.70 | 1.00 |

Slices (pre-declared; never report one pooled number for test2_newkey):

| slice | below | at_or_above | no_cost |
| --- | --- | --- | --- |
| training ranges (no novelty) | 13 | 2 | 3 |
| new V only (>=10, grids A-C, wordings 0-1) | 6 | 0 | 9 |
| new grid F (any V, wordings 0-1) | 8 | 19 | 10 |
| new wording 3 (any V, grids A-C) | 5 | 0 | 9 |
| new grid F and new wording 3 | 8 | 19 | 9 |
| V 13-15 (the clean extension: V 10-12 also occur in test_hard) | 10 | 7 | 16 |
| label key (V, grid, C or prior) seen in the 100 LoRA cells | 0 | 0 | 0 |
| label key seen in the 300 train cells | 0 | 0 | 0 |

Notes: (1) the (V, C) row with C = none is vacuous for no-cost cells (every no-cost cell at a trained V matches). (2) test2_same is a within-distribution check and partly overlaps training problems; report it stratified by key seen / unseen. (3) For at-or-above cells every offer below the stated cost is best (best payoff 0), so that type tests avoiding overpayment, not finding one best offer; headline soft regret, never pooled hit rate. (4) Below-cost cells whose best offer is the cheapest price are solved by always offering the cheapest price; the references above must be beaten. (5) V below the smallest grid price forces a negative best payoff (the model cannot decline to trade).
