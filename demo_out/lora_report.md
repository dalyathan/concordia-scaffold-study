# LoRA results (held-out tune cells: selected-on, not independent evidence)

## Arms (seed 0, chosen learning rate)

| Arm | lr | Best epoch (of run) | Held-out soft regret | Train soft regret (best / min) | Held-out mass | Fidelity KL (train / held-out) | Say agreement (plain → arm) | Say hard regret (plain → arm) | Slope on stated cost | s/epoch |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| method | 1e-04 | 2 (4) | 0.155 | 0.363 / 0.363 | 1.00 (plain 0.64) | 0.111 / 0.291 | 0.58 → 0.38 | 0.50 → 0.47 | 0.66 | 316 |
| neutral | 1e-04 | 1 (3) | 0.534 | 0.740 / 0.740 | 1.00 (plain 0.64) | 0.201 / 0.171 | 0.58 → 0.62 | 0.50 → 0.50 | 0.08 | 316 |
| wrong_rule | 1e-04 | 2 (4) | 0.448 | 0.816 / 0.778 | 1.00 (plain 0.64) | 0.095 / 0.135 | 0.58 → 0.83 | 0.50 → 0.52 | 0.03 | 316 |
| answer_only | 3e-04 | 7 (8) | 0.000 | 0.000 / 0.000 | 1.00 (plain 0.64) | — / — | 0.58 → 0.67 | 0.50 → 0.07 | 1.00 | 317 |
| shuffled (best of 1) | 1e-04 | 0 (2) | 0.577 | 0.778 / 0.778 | 0.64 (plain 0.64) | — / — | 0.58 → 0.58 | 0.50 → 0.50 | 0.05 | 316 |

Reference on the same cells: plain 0.577; method text (prompt) 0.171; always-2 0.333.

## Pass rule (owner's rule, frozen)

| Comparison (control − method, per held-out cell) | Mean | 95% interval | Cells where method is better | Lower bound > 0 |
| --- | --- | --- | --- | --- |
| plain | +0.422 | [+0.051, +0.820] | 5 of 6 | yes |
| neutral-distil | +0.378 | [+0.043, +0.758] | 5 of 6 | yes |
| wrong-rule-distil | +0.293 | [-0.003, +0.605] | 3 of 6 | no |

**Owner's rule: NOT PASSED**

## Strict criteria (reported separately)

| Criterion | Met |
| --- | --- |
| S1 vs always-2 | no |
| S1 vs best shuffled | yes |
| S2 effect floor (>= 50% of the plain-to-method-text gap) | yes |
| S3 mass >= 0.9 x plain | yes |
| S4 free-text hard regret below plain | yes |
| S5 slope on stated cost >= 0.25 | yes |

**Strict pass: NO.**

## Method seeds (same learning rate)

| Seed | Held-out soft regret | Best epoch | vs plain: lower bound > 0 |
| --- | --- | --- | --- |
| 0 | 0.155 | 2 | yes |
| 1 | 0.217 | 2 | yes |
| 2 | 0.210 | 4 | yes |

## Outcome (method arm, seed 0)

- Train-cell soft regret at the best epoch 0.363; method text on the train cells 0.428; teacher matched: yes.
- Outcome: **learned the train cells, did not transfer**.
- All held-out numbers are selected-on; with 6 cells a null is read only as "not shown here".

