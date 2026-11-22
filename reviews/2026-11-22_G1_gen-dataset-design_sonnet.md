# G1 generated dataset design: Sonnet (summary of returned text; verdict: GO-WITH-CHANGES)
Scoring train/tune is fine to start; declare label/slice issues before reading the failure map.
1. at_or_above is a weak, confounded label (best set = every offer below C; low V relative to grid after tie rejection): report expected-payoff regret and mass on best set, per-cell chance baseline, always-cheapest and stated-cost heuristics, by type with V stratified.
2. Cells with best payoff <= 0 / P=0 ties are arbitrary: add best_payoff<=0 and n_best fields; report as stratum.
3. hard_V differs from train on more than V (always-profitable regime, truncated C, no at_or_above): describe as such; compare with a matched always-profitable train subset (V 8-9 on grid A).
4. hard_grid mixes axes; E is barely OOD: report D and E separately.
5. Effective n overstated (labels depend on V, grid, C, and prior only for no-cost; train/test_same label-key overlap): log overlap, cell-level bootstrap, minimum detectable effect.
6. Stated prior inconsistent with stated cost/grid: add C_in_prior flag.
7. Fingerprint weak (order-0 prompt + cid only): also hash test cell entries with labels, generator sha256, refimpl/core sha; freeze quotas (single RNG stream).
8. Leakage to earlier artifacts: flag grid A prior (1,5) cells that equal old train/tune (V,line,C); old adapters must not be scored on this set.
9. hard_wording rests on one paraphrase per line; report wording effects per line.
10. Line collinear with type; do not present as separate factors.
11. Reusability: consider a reserve test set; pre-register one primary metric/comparison per use.
Code: no label bug found; tests weak (core equivalence only on grid A/prior (1,5); no brute-force check, no balance test for test_hard, split tests read cached files).
Freeze before test use: primary metric (regret, mass on best set), order aggregation, handling of best_payoff<=0 cells, bootstrap + minimum detectable effect, generator/library hashes, reserve set, primary comparisons, old adapters excluded.
