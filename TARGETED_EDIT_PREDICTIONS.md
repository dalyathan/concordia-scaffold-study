# TARGETED_EDIT_PREDICTIONS: arm E (A0 + a direct weight edit chosen by Claude for no-stated-cost deals), written 2026-11-28 before any locating run or edit

Committed alone, before the arm-E section of TARGETED_PLAN.md is reviewed and before any GPU step. Inputs: the same as TARGETED_PREDICTIONS.md, plus the earlier steering and patching results (the decision is made late and varies by case; steering vectors failed). Soft regret in coins on test3, forced-choice letter.

| id | quantity | predicted | probability |
| --- | --- | --- | --- |
| E1 | The locating step finds a single layer whose patch from the adapter into plain Qwen recovers at least half of the adapter's gain on no-cost probe cells | - | 0.35 |
| E2 | The fix is spread over 3 or more layers (no single layer recovers half) | - | 0.6 |
| E3 | Within the 5-attempt budget, an edit passes its development checks (beats its same-size random-direction control on select3 no-cost cells and keeps letter mass >= 0.90) | - | 0.4 |
| E4 | On test3 no-cost cells, E minus A0 is below 0 with the interval below 0 | - | 0.3 |
| E5 | On test3 no-cost cells, E beats T (the targeted LoRA arm) | - | 0.15 |
| E6 | E does no harm elsewhere (H2-style bound +0.10 against A0) | - | 0.6 |

Why: MEMIT-style edits work for facts stored in middle-layer MLPs; this decision draws on several numbers and is made late, so a small closed-form edit is likelier to help partly than fully, and less likely than retraining to beat targeted LoRA. A clean failure is still informative.
