# G3 GEN2_TEST_PLAN, Opus (go-with-changes)
1. Earlier test look not disclosed as an input; state its outcome, report side by side.
2. Novelty flags tangled with case type: 38 of 40 newkey at_or_above cells are grid F; at_or_above best is cheapest (zero regret for always-cheapest and the stated-cost rule); on below cells the stated-cost rule is the oracle and ignores V; V matters only on no_cost cells. Report slices by type; "new resale values" wording only from no_cost cells with novel V (>= 8 cells and clusters); use mutually exclusive slices; add a vs stated-cost rule by type.
3. Curve claim not gated; +-0.05 margin about equals a's expected regret; add relative criterion (ex25 - a) <= 0.1 x (plain - a), require set PASSED, freeze the seed-and-cluster bootstrap, add key_in_subset25/10 strata.
4. Overlap with tune, selection set B, test_same, test_hard not reported: add flags and strata.
5. Slice-size rule should require 8 cells and 8 (V, grid) clusters; say which rule seed is used for hard vs soft; multiplicity (8 comparisons, 2 curve claims) uncorrected: say so or Holm.
6. test2_same new-key clause: for examples-25 use its own subset.
7. Latent duplicate-cell risk in draw_stratified with cap 2: assert unique cell ids and cids.
8. Docstring contradicts code (cap 2 for at_or_above).
9. Up to 20 per type in range became 13/2/3; no-novelty slice is 18 cells, mostly below.
10-12. Counts consistent where checked; steps for three runs missing from the table; assert test2 names not in first dataset and pools of 72.
Freeze before look: script with install(), rendered-prompt fingerprints through score_case, gen_test2.py hash, new lock and output dir, leakage check for test2_*, run-id assertions loosened for _n25_ and rule_hard, tune_probs_best for all adapters, GPU estimate and stop time; analysis estimator, relative margin and gating, per-type slice rules, overlap strata; disclosure; plan and script sha256.
