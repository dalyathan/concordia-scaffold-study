# TEST2_PREDICTIONS: predictions for the one test2 look, Llama 3.1 8B and Qwen 2.5 7B (written 2026-11-28, before any test2 score of either model)

Committed alone, before G3 and before the look. Inputs: tune results only (LLAMA_RESULTS.md, QWEN_RESULTS.md, after G2) and Gemma's earlier look at test_same / test_hard (DEMO_STATUS.md). No test2 case of any model has been scored. The look's rules (T1, T2) and wording are in LLAMA_TEST_PLAN.md, QWEN_TEST_PLAN.md and tools/test2_report.py. These predictions are scored after the look; they change nothing in the rules.

Units: soft regret in coins, forced-choice letter, examples-100 = the 3-seed mean of the selected adapters.

## Basis
- Tune, examples-100: Llama 0.048 (seen decision tuples 0.032, unseen 0.060); Qwen 0.063 (seeds 0.032 / 0.055 / 0.104; seen 0.041, unseen 0.081).
- Tune, examples-100 minus plain: Llama -1.14 [-1.32, -0.91]; Qwen -1.60 [-1.89, -1.24]. Minus scrambled: Llama -0.61; Qwen -0.81. Minus the stated-cost rule: Llama -0.17 [-0.40, -0.03]; Qwen -0.15 [-0.38, -0.01].
- test2_same draws fresh cells from the training ranges; 48 of its 120 cells share a label key with the 100 LoRA cells (fewer than on tune), so its mean should sit near the tune "unseen" value.
- Gemma's earlier look: examples-100 0.171 on test_hard overall, 0.414 on its new-resale-value slice (V 10-12; plain 2.54), against 0.504 for the stated-cost rule overall. The V 13-15 slice of test2_newkey is further out than Gemma's V 10-12, and it is small (33 cells, 66 cases, 12 groups), so its intervals will be wide.

## Predictions

| id | model | quantity | predicted range | probability |
| --- | --- | --- | --- | --- |
| P1 | Llama | test2_same examples-100 mean | 0.03-0.15 | 0.8 |
| P2 | Qwen | test2_same examples-100 mean | 0.04-0.18 | 0.75 |
| P3 | Llama | T1 holds | - | 0.8 |
| P4 | Qwen | T1 holds (the seed-2 adapter is the main risk to "mean <= 0.15") | - | 0.7 |
| P5 | both | test2_same: key-unseen stratum worse than key-seen stratum for examples-100 | - | 0.75 per model |
| P6 | Llama | V 13-15 slice: examples-100 mean | 0.10-0.80 | 0.7 |
| P7 | Qwen | V 13-15 slice: examples-100 mean | 0.10-0.90 | 0.7 |
| P8 | both | V 13-15 slice: examples-100 below plain with the paired interval below 0 | - | 0.85 per model |
| P9 | Llama | T2 holds (also below the stated-cost rule with the interval below 0) | - | 0.35 |
| P10 | Qwen | T2 holds | - | 0.3 |
| P11 | both | new wording 3 slice: examples-100 within 0.10 of its training-ranges slice | - | 0.7 per model |
| P12 | both | every examples-100 adapter fails the planted no-cost case on both splits (mass < 0.9), as on tune | - | 0.85 per model |
| P13 | both | scrambled N=100 mean on test2_same at least 0.3 worse than examples-100 | - | 0.9 per model |

Expected conclusion wording, per model: "in-family fit replicates on fresh cells; no evidence of generalisation to new values" (Llama about 0.5, Qwen about 0.45); "generalises to V 13-15 on the forced-choice readout" (Llama 0.3, Qwen 0.25); "the tune result does not replicate on fresh in-family cells" (Llama 0.2, Qwen 0.3).
