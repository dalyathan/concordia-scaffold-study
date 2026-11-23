# GEN_TEST_PLAN.md - PROPOSAL for the owner (nothing here has been run on test_same or test_hard)

Status: proposal written Nov 23 after the development verdict. A look needs (a) your approval of this text, (b) the scoring script written, committed and hashed here after your approval, (c) gate G3 (Sonnet + Opus) on the approved text and script, (d) your explicit "go". Variants 1-14, the old test cells and old adapters are not used.

## 0. What the development evidence says (so you can decide whether the one look is worth spending)
The frozen development rule (GEN_PLAN.md) was NOT PASSED on tune. Teacher-distil: tune soft regret 0.376 (3 seeds) vs plain 0.657, always-cheapest 0.429, stated-cost rule 0.214; it fails the no-harm criterion on no-cost cells (+0.190 vs plain, a fault already in the in-prompt paragraph) and puts about half its probability on the cheapest option in every case type (plain 0.04-0.12). It is not separated from our hand-written paragraph's distillation (-0.003 [-0.058, +0.052]) or from always-cheapest (+0.053 [-0.098, +0.222]). So a test look is a new, separate, pre-registered question, and the likely outcome is a partial or harm label, not a support. Decisions for you are in section 9.

## 1. Question and claims
Q1 (primary): on cells like the training cells (test_same), does the frozen teacher-distil adapter lower soft regret relative to plain, neutral-distil and wrong-rule-distil, without harm on at-or-above and no-cost cells?
Q2 (primary, second comparison): is teacher-distil different from our-method-distil?
Q3 (descriptive per slice): on test_hard slices (resale values, price grids and wordings never seen in training), does the gain over plain survive? Each slice is its own result; nothing is pooled with test_same.
No claim about mechanism (tracking the stated cost) is made or tested beyond the reported slope and cheapest-option mass.

## 2. Test cells (locked before any model scored them; fingerprints committed in demo/gen/fingerprints_v2.json)
- test_same: 60 cells (20 below, 20 at_or_above, 20 no_cost) x 2 name variants (n0, n1) = 120 cases; list sha256 0538a2a2... (full value is in fingerprints_v2.json).
- test_hard: 62 cells x 2 = 124 cases; slices reported separately: hard_V (20 cells: 10 below, 10 no_cost; no at_or_above cells exist at unseen V, all-tie cells excluded), hard_grid (21 cells, 7 per type; grids D and E reported as two sub-slices), hard_wording (21 cells, wording 2; 7 per type). List sha256 prefixes: test_hard c4b08aba, hard_V 9c3090a6, hard_grid e8b156e6, hard_wording d7276494.
- Unit of analysis = cell (mean of the two name variants, then mean over an arm's seeds). Cells are disjoint from train, tune, loop set A, selection set B and the 50 packet cells (asserted by gen_cases fingerprints and re-asserted by the test script).
- Before scoring, the script computes (labels only, no model) for every test cell whether its label key (V, grid, C or prior) coincides with one of the 100 LoRA training cells; the overlapping and non-overlapping strata of test_same are both reported (declared secondary).
- Pre-test integrity: recompute fingerprints_v2 and compare; hash of cells.json (428925050d28...), cases.jsonl (63e26a25...), gen_cases.py (cc0024b7...), the teacher paragraph (f41ae9b3...).

## 3. Frozen adapters (no re-selection of lr, epoch or seed on test data)
Each at its saved best epoch (early stopping on selection set B). Adapter files are gitignored; sha256 verified before scoring; adapter-off scoring must reproduce the saved plain probabilities (max abs diff < 1e-4 on the tune cases) before the lock is written.
| Arm | lr | seed | best epoch | adapter sha256 |
| --- | --- | --- | --- | --- |
| teacher-distil | 1e-4 | 0 | 4 | e2189c1dd2972d93e8a30083a0d18e34f7f83037515af8942ebf7d6035707163 |
| teacher-distil | 1e-4 | 1 | 3 | e1fb9dc0649278c241cec409dfef1df98e67e90d202e43c459a267136d723011 |
| teacher-distil | 1e-4 | 2 | 2 | 4f2d6e962b636f7f253f483bf7bc3f5f01a8e32de716e8e696ad8ab17fb2a082 |
| our-method-distil | 1e-4 | 0 | 3 | ceba0964a2e412f5420576cf6dde1fb1a7839f83ef0c9d31660c3cb3fb597d82 |
| our-method-distil | 1e-4 | 1 | 3 | cb9b1d9ab2b192b80bfdb44fd1f6df14987028599bd89ea7a63015063fdd7444 |
| our-method-distil | 1e-4 | 2 | 2 | 501559cc4583b2b8638c5a7497330b93115d07deae55e297726b0f1690b204a7 |
| wrong-rule-distil | 1e-4 | 0 | 5 | b9f52e461587dc40c11ddff532c0abbae42d810ca6d849f8a4f9d868d8151a46 |
| answer-trained ceiling (reference only) | 1e-4 | 0 | 5 | 07036c98e1042a00be89a27290b053ad9d49418089b3fc06880373264745728c |
| answer-trained ceiling (reference only, pre-declared rate) | 3e-4 | 0 | 4 | b2ca52de544b0b8b8d077ba356211359394a4f9bbb53e571470e05bbdea3818b |
Neutral-distil: all three tune runs kept epoch 0, i.e. the neutral arm is the plain model; see decision D1 (fixed-epoch neutral runs). Wrong-rule has one seed; see decision D2. Seed policy: an arm's value = mean over its seeds of per-case probabilities; no best-seed selection; per-seed values are reported next to every arm. Reference rows without adapters: plain, always-cheapest, stated-cost rule (computed from the labels), and the in-prompt teacher and original paragraphs (upper references, not comparators to beat). The machine-readable frozen list will be demo/gen/test_frozen_adapters.json, written with the script.

## 4. Primary comparisons (test_same only; one declared set, no pooling with test_hard)
Metric: cell-mean soft regret (first-token letter probabilities, five cyclic orders). Differences are control minus teacher-distil (positive = teacher better). Paired cell bootstrap, 10,000 resamples, numpy PCG64 seed 0, 95% percentile interval; counts of cells where the teacher is better are reported.
P1 vs plain; P2 vs wrong-rule-distil; P3 vs neutral-distil (as fixed by D1); P4 vs our-method-distil (two-sided).
Secondary comparators, always reported: always-cheapest and the stated-cost rule (overall and by type), with the same bootstrap. Everything else (by-type tables, overlap strata, slope on stated cost with bootstrap interval over below cells, probability mass on the cheapest option by type, letter mass per type, per-seed values, in-prompt text rows, the ceilings) is descriptive.

## 5. Outcome labels (written before the look; every case gets exactly one label per set)
test_same label (primary), computed in this order:
- **HARM-FLAG** is appended (not an override) when teacher-distil minus plain on at_or_above or on no_cost cells exceeds +0.05 (point estimate; at least 5 cells of the type). Expected from development for no-cost cells.
- **SUPPORT:** P1 lower bound > 0 and improvement >= 0.15; P2 and P3 lower bounds > 0; no HARM-FLAG; letter mass >= 0.9 x plain overall and in each type. A tag follows: "beats always-cheapest" (lower bound > 0 overall), "not separated from always-cheapest" (interval contains 0), or "worse than always-cheapest" (upper bound < 0).
- **PARTIAL:** P1 holds (lower bound > 0, improvement >= 0.15) but SUPPORT fails; the failed conditions are listed (e.g. "HARM-FLAG on no_cost", "not separated from wrong-rule").
- **NOT SHOWN:** P1 lower bound <= 0 (read only as "not shown on these 60 cells"; no second look, no re-tuning, no new arm).
- **WORSE:** P1 upper bound < 0.
P4 label (teacher vs our method, in every case): TEACHER-BETTER (lower bound > 0), OURS-BETTER (upper bound < 0), EQUIVALENT (whole interval within +-0.10), INCONCLUSIVE otherwise.
Each test_hard slice (hard_V, hard_grid D, hard_grid E, hard_grid all, hard_wording) gets one label from the teacher-vs-plain difference: TRANSFERS (lower bound > 0), NOT SHOWN (interval contains 0), WORSE (upper bound < 0), with n cells and by-type values; for hard_V the label covers only below and no_cost cells. A slice with fewer than 8 cells is labelled descriptive-only. The frozen development verdict "NOT PASSED" is printed next to every test result.

## 6. Pre-registered expectation and power
On tune, teacher-distil minus plain: below +0.76, at_or_above -0.27, no_cost +0.19 (harm). I therefore expect test_same to come out PARTIAL with HARM-FLAG on no_cost, and a result against always-cheapest near zero; a SUPPORT would be a surprise. With 20 cells per type and 60 overall the interval on P1 is expected to be about +-0.15 wide; per-slice intervals at 7-10 cells per type will be wide and are descriptive.

## 7. Locked before the look
Scoring code and prompts (gen_cases.render, gen_score/gen_lora scoring path, orders), the analysis script, the frozen adapter list, this plan, the commit hash and the script sha256 (recorded in section 10 after approval); no edits to PROTOCOL.md; no name variants 1-14; no agent_py_files; adapters only on test cases; no re-run after the lock, only `--analyze`; stop time rule (all work before Nov 25 23:00 CST). One run, one report. Failure before the lock may be re-run; after the lock only analyse.

## 8. Limits stated now
Controls: wrong-rule has one seed and teacher has three (the bootstrap resamples cells only; seed spread is shown per run); no lr grid for controls (declared in GEN_PLAN); the paragraph and all lr/epoch choices were made on non-test cells only but tune was seen after the paragraph was frozen, and the paragraph was not revised after the tune verdict; the teacher paragraph's no-cost branch is known to hurt; the in-prompt rows and the cheapest-mass check are post-hoc descriptive. Overlap of label keys between test and training cells is reported, not removed.

## 9. Decisions for the owner (defaults used if you answer only "approved")
D1. Neutral control: the neutral-distil arm equals plain (best epoch 0 on all three seeds; at epochs 1-2 it is worse than plain on the selection set). Option A (default, no GPU): treat neutral as plain, declare it, P3 = P1. Option B (about 1.3 GPU hours on train/tune cells only, before any test look): run three neutral seeds for a fixed 3 epochs (the teacher's median best epoch), freeze them and use them as the neutral arm.
D2. Wrong-rule seeds 1-2 (about 1.4 GPU hours, train/tune only): default no; with only one wrong-rule seed P2 is reported with that caveat. Choose yes if you want P2 on equal seed count.
D3. Should the one look be spent at all, given NOT PASSED on tune? Default: yes, as a descriptive pre-registered look.
D4. Ceiling rate for the reference row: both rates are scored and reported; neither is a comparator.

## 10. After approval (to be filled in)
Script demo/gen_test_look.py sha256: not yet written. Frozen adapter file: demo/gen/test_frozen_adapters.json (not yet written). G3 (Sonnet + Opus) on the approved text and script: before the go. Explicit go from the owner: not given.
