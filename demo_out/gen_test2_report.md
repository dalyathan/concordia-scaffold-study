# test2 sets: fresh locked test cells (CPU only, nothing scored)

seed 20261201; two name variants per cell; extension: grid F (8, 10, 12, 14, 16), resale values 10-15, seller wording index 3 (reserved for test2).

ties dropped while sampling (candidate cells where every offer ties): {'below': 1635, 'at_or_above': 1517}; original-study-space candidates excluded: 144
availability for test2_newkey (cells not used, not tie, pair not in the 300 train cells): {"below": {"in_range_available": 120, "extension_available": 2645}, "at_or_above": {"in_range_available": 5, "extension_available": 255}, "no_cost": {"in_range_available": 11, "extension_available": 710}}

## test2_same: 120 cells, 240 cases

| type | cells | single best offer | in training ranges | extension |
| --- | --- | --- | --- | --- |
| below | 40 | 40 (100%) | 40 | 0 |
| at_or_above | 40 | 7 (18%) | 40 | 0 |
| no_cost | 40 | 21 (52%) | 40 | 0 |
| all | 120 | 68 (57%) | 120 | 0 |

V values: {2: 14, 3: 24, 4: 22, 5: 13, 6: 15, 7: 13, 8: 9, 9: 10}; grids: {'B': 44, 'A': 27, 'C': 49}; wordings: {0: 61, 1: 59}

Cells sharing a label key with training (counts of cells; by type below / at_or_above / no_cost):

| key | vs the 300 train cells | vs the 100 LoRA training cells |
| --- | --- | --- |
| current key (V, grid, C or prior) | 25 / 36 / 19 (total 80) | 14 / 28 / 2 (total 44) |
| stricter (V, C) key, C = none for no-cost cells | 36 / 36 / 40 (total 112) | 25 / 36 / 40 (total 101) |
| pair (V, C or cost range) | 36 / 36 / 39 (total 111) | 25 / 36 / 21 (total 82) |

## test2_newkey: 120 cells, 240 cases

| type | cells | single best offer | in training ranges | extension |
| --- | --- | --- | --- | --- |
| below | 40 | 40 (100%) | 20 | 20 |
| at_or_above | 40 | 0 (0%) | 5 | 35 |
| no_cost | 40 | 36 (90%) | 11 | 29 |
| all | 120 | 76 (63%) | 36 | 84 |

V values: {2: 11, 6: 8, 7: 7, 8: 4, 9: 6, 10: 12, 11: 20, 12: 11, 13: 16, 14: 17, 15: 8}; grids: {'B': 23, 'C': 31, 'A': 12, 'F': 54}; wordings: {0: 43, 1: 47, 3: 30}

Cells sharing a label key with training (counts of cells; by type below / at_or_above / no_cost):

| key | vs the 300 train cells | vs the 100 LoRA training cells |
| --- | --- | --- |
| current key (V, grid, C or prior) | 0 / 0 / 0 (total 0) | 0 / 0 / 0 (total 0) |
| stricter (V, C) key, C = none for no-cost cells | 0 / 0 / 11 (total 11) | 0 / 0 / 11 (total 11) |
| pair (V, C or cost range) | 0 / 0 / 0 (total 0) | 0 / 0 / 0 (total 0) |

