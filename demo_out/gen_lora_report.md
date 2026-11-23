# Generated-dataset LoRA arms on the 42 TUNE cells (selection on 42 separate train cells; tune scored once per run)

Chosen lr: teacher 1e-04 (lowest selection-set soft regret at seed 0); other arms at their own grid if complete, else the teacher's lr (answer-trained ceiling 3e-4). neutral: 3 run(s) kept epoch 0 (no improvement; flagged and not counted as arms)

## Arms: soft regret on tune cells (mean over cells, seeds averaged), by type

| Arm | lr | seeds | all [95%] | below | at_or_above | no_cost | letter mass | slope on stated cost (below) | best epochs | s/epoch |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| plain |  |  | 0.657 [0.465, 0.862] | 1.376 | 0.391 | 0.204 | 0.81 |  |  |  |
| always-cheapest |  |  | 0.429 [0.195, 0.719] | 0.643 | 0.000 | 0.643 |  |  |  |  |
| stated-cost rule |  |  | 0.214 [0.076, 0.386] | 0.000 | 0.000 | 0.643 |  |  |  |  |
| teacher text in prompt |  |  | 0.390 [0.243, 0.565] | 0.673 | 0.107 | 0.390 |  |  |  |  |
| method_original text in prompt |  |  | 0.369 [0.207, 0.571] | 0.542 | 0.174 | 0.391 |  |  |  |  |
| teacher-distil | 1e-04 | 0,1,2 | 0.376 [0.242, 0.535] | 0.614 | 0.119 | 0.394 | 1.00 | 0.26 | 4,3,2 | 392 |
| method_original-distil | 1e-04 | 0,1,2 | 0.373 [0.236, 0.541] | 0.486 | 0.244 | 0.388 | 1.00 | 0.33 | 3,3,2 | 392 |
| wrong_rule-distil | 1e-04 | 0 | 0.589 [0.378, 0.847] | 1.281 | 0.209 | 0.278 | 1.00 | 0.12 | 5 | 392 |
| answer-trained ceiling | 3e-04 | 0 | 0.118 [0.062, 0.190] | 0.133 | 0.149 | 0.073 | 1.00 | 0.69 | 4 | 392 |

## Pass rule (GEN_PLAN.md, frozen): control minus teacher, paired cell bootstrap

| Comparison | mean diff [95%] | cells where teacher better | lower bound > 0 |
| --- | --- | --- | --- |
| plain | +0.282 [+0.127, +0.447] | 26 of 42 | yes |
| neutral-distil | not run | | |
| wrong-rule-distil | +0.214 [+0.074, +0.367] | 23 of 42 | yes |
| our-method-distil (not in rule) | -0.003 [-0.058, +0.052] | 19 of 42 | no |
| always-cheapest (not in rule) | +0.053 [-0.098, +0.222] | 13 of 42 | no |
| stated-cost rule (not in rule) | -0.161 [-0.343, -0.005] | 9 of 42 | no |

1. beats plain, neutral-distil and wrong-rule-distil with lower bound > 0: **no**
2. effect floor, improvement over plain >= 0.15: +0.282 -> **yes**
3. below cells: improvement over plain +0.762 [+0.530, +1.013], better in 14 of 14 cells (need lower bound > 0 and >= 60%) -> **yes**
4. no harm (teacher minus plain <= +0.05): at_or_above -0.272, no_cost +0.190 -> **no**
5. letter mass 1.00 vs 0.9 x plain 0.73 -> **yes**

**Pass rule (all seeds): NOT PASSED** (seeds [0, 1, 2]; replication on seeds 1-2 only below)

Replication, teacher seeds 1-2 only vs all available control seeds:

- vs plain: +0.284 [+0.130, +0.448], teacher better in 26 of 42 cells
- vs wrong-rule-distil: +0.216 [+0.077, +0.369], teacher better in 24 of 42 cells

## By overlap of the cell's label key (V, grid, C or prior) with the 100 training cells: 16 overlapping, 26 not

| Arm | overlapping cells | non-overlapping cells |
| --- | --- | --- |
| plain | 0.564 | 0.714 |
| teacher | 0.147 | 0.516 |
| method_original | 0.210 | 0.473 |
| wrong_rule | 0.370 | 0.724 |
| answer_only | 0.062 | 0.153 |

## Per-seed tune soft regret (cell means)

- gen_answer_only_lr1e-04_s0: 0.026 (best epoch 5, selection set 0.054)
- gen_answer_only_lr3e-04_s0: 0.118 (best epoch 4, selection set 0.120)
- gen_method_original_lr1e-04_s0: 0.402 (best epoch 3, selection set 0.403)
- gen_method_original_lr1e-04_s1: 0.367 (best epoch 3, selection set 0.383)
- gen_method_original_lr1e-04_s2: 0.350 (best epoch 2, selection set 0.394)
- gen_neutral_lr1e-04_s0: 0.657 (best epoch 0, selection set 0.584)
- gen_neutral_lr1e-04_s1: 0.657 (best epoch 0, selection set 0.584)
- gen_neutral_lr1e-04_s2: 0.657 (best epoch 0, selection set 0.584)
- gen_teacher_lr1e-03_s0: 0.657 (best epoch 0, selection set 0.584)
- gen_teacher_lr1e-04_s0: 0.380 (best epoch 4, selection set 0.360)
- gen_teacher_lr1e-04_s1: 0.352 (best epoch 3, selection set 0.329)
- gen_teacher_lr1e-04_s2: 0.395 (best epoch 2, selection set 0.372)
- gen_teacher_lr3e-04_s0: 0.384 (best epoch 3, selection set 0.375)
- gen_wrong_rule_lr1e-04_s0: 0.589 (best epoch 5, selection set 0.510)
