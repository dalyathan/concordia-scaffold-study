# Post-hoc descriptive checks (G2 reviewer requests; tune cells; do not change the frozen verdict)

## Mass on the cheapest option (position 0), mean over cells, by type; and soft regret

| Arm | cheapest mass below | at_or_above | no_cost | soft regret all |
| --- | --- | --- | --- | --- |
| plain | 0.04 | 0.12 | 0.08 | 0.657 |
| teacher-distil | 0.50 | 0.52 | 0.51 | 0.376 |
| method-distil | 0.56 | 0.37 | 0.36 | 0.373 |
| wrong-rule-distil (1 seed) | 0.20 | 0.32 | 0.20 | 0.589 |
| ceiling lr 3e-4 | 0.74 | 0.45 | 0.31 | 0.118 |
| ceiling lr 1e-4 | 0.71 | 0.52 | 0.31 | 0.026 |

## Teacher-distil vs always-cheapest (cheapest regret minus teacher regret; positive = teacher better), paired cell bootstrap

- all (42 cells): +0.053 [-0.098, +0.222]
- below (14 cells): +0.029 [-0.329, +0.460]
- at_or_above (14 cells): -0.119 [-0.282, -0.028]
- no_cost (14 cells): +0.249 [+0.086, +0.435]

## Gain over plain by overlap of (V, grid, C or prior) with the 100 training cells (16 overlapping, 26 not)

- teacher-distil, overlapping: plain minus arm +0.417 [+0.169, +0.700]
- teacher-distil, non-overlapping: plain minus arm +0.198 [+0.010, +0.392]
- method-distil, overlapping: plain minus arm +0.354 [+0.075, +0.678]
- method-distil, non-overlapping: plain minus arm +0.241 [+0.020, +0.473]
- teacher text in the prompt, overlapping: plain minus text +0.405 [+0.145, +0.709]
- teacher text in the prompt, non-overlapping: plain minus text +0.182 [-0.002, +0.370]

## Ceiling at both learning rates (tune soft regret)

- ceiling lr 3e-4: 0.118
- ceiling lr 1e-4: 0.026

## Neutral-distil selection-set soft regret by epoch (set B; plain = epoch 0)

- seed 0: 0.584, 0.608, 0.660
- seed 1: 0.584, 0.830, 0.653
- seed 2: 0.584, 0.634, 0.598
