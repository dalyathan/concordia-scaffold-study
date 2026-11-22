# G3 test plan: Sonnet (summary of returned text; verdict: GO-WITH-CHANGES)
1. Lock written before anything can fail; nothing saved until the end: validate first, lock just before scoring, dump per-case results; declare rerun policy.
2. Final script never run end to end; dry-run output stale (old HARM label; one C>=V cell): rerun, unit-test label().
3. Label strings can mislead (PARTIAL text when only D<0.10; NOT SHOWN text when plain passes but neutral fails; SUPPORT with mean-only always-2): conditional texts, comparator table, "beats always-2" in headline.
4. Low power: expected D ~0.12 near threshold; state what a null means; declare the C<V stratum interval as secondary (not primary).
5. Weak data-selection assertions: assert case-id hash, 18-cell list, disjointness from train/tune.
6. Frozen code surface incomplete: record commit, sha256 of scoring/textrows/common/core/splits/cases, adapter_config, library versions, GPU.
7. Nine adapters in one PeftModel: record tolerance (dry run differs from training log by ~1e-3).
8. Seed variance not in interval; percentile bootstrap anti-conservative at n=18: state limits.
9. Minor: unparsable free-text imputed 1.0 (undocumented), secondary 3 not implemented, slope confounded with V, confirm live case never scored with an adapter.
Could not verify: core/common/splits contents, hashes, test_go.json.
