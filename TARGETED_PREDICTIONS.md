# TARGETED_PREDICTIONS: Claude-targeted vs random extra examples (Qwen 2.5 7B first), written 2026-11-28 before any plan, data or run

Committed alone, before TARGETED_PLAN.md, before the new pool and test set exist, and before any GPU step. Inputs: tune results and the one test2 look (QWEN_TEST2_RESULTS.md, LLAMA_TEST2_RESULTS.md), where the examples-100 adapters do worst on deals with no stated cost (test2_same no-cost 0.14 Qwen / 0.12 Llama; test2_newkey no-cost 0.75 Qwen) and fail the planted no-cost case in every seed.

Setup being predicted (details fixed in TARGETED_PLAN.md): Qwen, retrained from scratch on the same 100 Claude-labelled cells plus 50 extra cells, three seeds per arm, same recipe and number of epochs. Arm T: 50 extra cells chosen by Claude from a failure map of the examples-100 adapters on build cells. Arm R: 50 extra cells drawn at random from the same pool. A0: the existing examples-100 adapters. Scored once on a new locked test set (test3) that is about half no-stated-cost deals. Soft regret in coins, forced-choice letter, 3-seed means.

| id | quantity | predicted | probability |
| --- | --- | --- | --- |
| Q1 | test3 no-cost cells: T minus R | -0.40 to 0.00 (point estimate) | 0.7 |
| Q2 | H1 holds (T minus R on no-cost: mean < 0, 95% interval below 0, permutation p < 0.05) | - | 0.55 |
| Q3 | H2 holds (T minus R on the other cells: upper 95% bound <= +0.05) | - | 0.75 |
| Q4 | H3 holds (T beats the stated-cost rule on test3 no-cost cells by the same three conditions) | - | 0.4 |
| Q5 | R minus A0 on test3 no-cost cells below 0 (more random data helps a little) | - | 0.65 |
| Q6 | T passes the planted no-cost case (mass >= 0.9) in at least 2 of 3 seeds | - | 0.4 |
| Q7 | A0 test3 no-cost mean | 0.15-0.70 | 0.7 |
| Q8 | T test3 no-cost mean | 0.05-0.45 | 0.7 |

Why: the failure is concentrated (no-cost deals, especially at higher resale values), so 50 extra examples aimed there should move it more than 50 spread over all types (about a third of random cells are no-cost). The risk is that the no-cost failure is about how the model uses the cost range at all, which more examples of any kind fix about equally, or that targeted cells crowd out the other types (Q3).
