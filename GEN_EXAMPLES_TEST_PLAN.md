# GEN_EXAMPLES_TEST_PLAN.md (approved by the owner on Nov 23 with one correction; the owner's go is conditional on gate G3 not saying no-go)

Owner correction (verbatim in substance): the test sets are the GENERATED dataset's test_same (60 cells) and test_hard (62 cells: hard_V 20, hard_grid 21, hard_wording 21, each slice reported separately) from demo/gen/cells.json. The earlier "never touch test_same / test_hard" referred to these same generated sets before this approval; it did not mean the original study. test_same and test_hard are judged separately. Reported-only rows outside the rule are added: the teacher-distil adapters (lr 1e-4, seeds 0-2) and our-method-distil (seeds 0-2). The original study's test cells, old adapters, name variants 1-14 and agent_py_files remain untouched.

## 1. What is scored
The existing adapters only, no retraining, no new seeds, no choice of lr, epoch or seed after the look. Each at its saved best epoch (early stopping on selection set B), name = run id, sha256 of adapter_model.safetensors (the script refuses any mismatch; the machine-readable list is demo/gen/test_frozen_adapters.json):
| Run | best epoch | adapter sha256 |
| --- | --- | --- |
| claude_examples lr 1e-4 s0 | 4 | 74b90cbeaa4c672e571843f3368072e77d24ac06e0f0c908e8011df4b361b243 |
| claude_examples lr 1e-4 s1 | 5 | c77a5514ea3edaea0418ba5f0043dfe2bb43608179cc935c63af51be2b6f3bed |
| claude_examples lr 1e-4 s2 | 2 | 390def343a67080384aea8953c6b5fed6d0495b0b823aa78e2570a313d0a3ca3 |
| cheapest_label lr 1e-4 s0 (b) | 5 | 83aa94c6fc8054c653d1173c77ff94fcad4b2668ea3481f34c01ff37954f25af |
| shuffled_claude lr 1e-4 s0 (c) | 2 | 9d1f75175de04cfa94f1aca1c0bc91a583e84e526e83705a7882f37a80736e38 |
| answer-trained ceiling lr 1e-4 s0 (reference) | 5 | 07036c98e1042a00be89a27290b053ad9d49418089b3fc06880373264745728c |
| teacher-distil lr 1e-4 s0 (reported only) | 4 | e2189c1dd2972d93e8a30083a0d18e34f7f83037515af8942ebf7d6035707163 |
| teacher-distil lr 1e-4 s1 | 3 | e1fb9dc0649278c241cec409dfef1df98e67e90d202e43c459a267136d723011 |
| teacher-distil lr 1e-4 s2 | 2 | 4f2d6e962b636f7f253f483bf7bc3f5f01a8e32de716e8e696ad8ab17fb2a082 |
| our-method-distil lr 1e-4 s0 (reported only) | 3 | ceba0964a2e412f5420576cf6dde1fb1a7839f83ef0c9d31660c3cb3fb597d82 |
| our-method-distil lr 1e-4 s1 | 3 | cb9b1d9ab2b192b80bfdb44fd1f6df14987028599bd89ea7a63015063fdd7444 |
| our-method-distil lr 1e-4 s2 | 2 | 501559cc4583b2b8638c5a7497330b93115d07deae55e297726b0f1690b204a7 |
Arm value = mean over its seeds of per-case probabilities (no best-seed selection); per-run values are printed. Reference rows without adapters: plain (adapter off), always-cheapest, stated-cost rule (stated cost when given and below V, else cheapest; computed from the labels).
Before the look (preflight, tune cells only): each adapter reloaded through PEFT must reproduce its stored tune probabilities and adapter-off must reproduce the saved plain scores (max abs diff < 1e-3), else stop. The preflight also recomputes the hashes of cells.json, cases.jsonl, gen_cases.py, the claude label file and the rendered-prompt fingerprints of test_same and test_hard (values in GEN_TEST_PLAN.md section 2), asserts grid position 0 is the cheapest price on every cell, and checks that no existing output under demo_out/ or demo/gen/ contains a test case or cell id.

## 2. Test sets and scoring
test_same (60 cells x 2 name variants = 120 cases) and test_hard (62 cells x 2 = 124 cases; slices hard_V, hard_grid with its grid-D part and the 6-cell grid-E part reported separately, hard_wording), from demo/gen/cells.json; counts fixed now. Scoring path = gen_lora.score_case (five cyclic orders, first-token letter probabilities renormalised over the five letters, averaged over orders and name variants), identical to tune.

## 3. Decision rule (frozen; the six conditions of the tune rule, applied separately to each set and slice; no pooling of test_same with test_hard)
(a) = mean over the three claude_examples seeds. A set PASSES if all hold: (1) plain - (a) lower bound > 0; (2) (b) - (a) lower bound > 0; (3) always-cheapest - (a) lower bound > 0; (4) plain - (a) on its below cells lower bound > 0 (not applicable if the set has none); (5) no case type present has (a) worse than plain by more than 0.05 (type-mean point estimate); (6) letter mass of (a) >= 0.9 x plain. Paired cell bootstrap over the set's cells, 10,000 resamples, numpy default_rng(0), two-sided 95% percentile; lower bound = 2.5th percentile. Outcome per set: PASSED or NOT PASSED, with the list of failed conditions; slices are exploratory and uncorrected, test_same and test_hard are the two primary results, and a slice with fewer than 8 cells (grid E, 6 cells) is labelled "descriptive only". Conditions 2 and 3 are in effect one test on tune ((b) = always-cheapest); both are kept.
Reported, outside the rule: stated-cost rule minus (a); ceiling minus (a) and (a) minus ceiling by type; teacher-distil and our-method-distil: plain minus each, each minus (a); (b) - a and (c) - a on below and no-cost cells; per-run soft regret of every adapter; slope of the expected offer on the stated cost (below cells; bootstrap over cells); cheapest-option mass by type; overlap strata of the label key with the 100 training cells (current key and the stricter V+C key, counts computed in the script from labels only).

## 4. Allowed wording
Pass on a set: "single-label oracle-equivalent supervision at 100 cells lowers soft regret on that set of the same generator, beyond offering cheap and beyond shuffled labels; Claude's labels equal the script-solved oracle up to a tie rule, so nothing is claimed about teaching." Fail: report the numbers and say the tune result did not carry to that set (or not on the listed conditions). For hard slices, passing is described only as transfer to unseen resale values, grids or wordings, one slice at a time. No equality-with-ceiling claim (one ceiling seed); no "examples beat instructions" (teacher-distil and our-method-distil are different target types); the teacher-distil and our-method-distil rows are reported, not tested against a rule.

## 5. Locked before the look and limits
Scoring code, prompts, the analysis (all in demo/gen_examples_test_look.py), this plan, the adapters above. One look: the script writes demo/gen/test_look_lock.json first and refuses a second look; it needs a passing preflight made by the same script sha256. After the lock: a crash is handled by an identical, hash-verified re-run of the same script (only unfinished arms are re-scored; no partial output is read before completion); any code change after the lock voids the look; an analysis bug found afterwards is reported as a deviation with both outputs. Stop time: Nov 25 23:00 CST. Limits: seeds 1-2 of the ceiling do not exist; the bootstrap resamples cells only (tune and test cells share values of V, grid and prior, so intervals are optimistic; no clustering); tune has been reused across arms; the lr grid and the expectation of a pass were set after the ceiling's tune results were known; selection set B chose lr independently; (c) has one seed and cannot shuffle at-or-above cells (all labels cheapest); one training draw; test-cell label keys overlap with training cells (reported, not removed).

## 6. Record (filled after approval)
Script demo/gen_examples_test_look.py sha256, preflight result, G3 verdicts and the look's outcome are recorded in DEMO_STATUS.md and in demo/gen/test_preflight.json / test_look_lock.json.
