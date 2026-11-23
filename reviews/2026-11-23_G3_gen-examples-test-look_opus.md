(Saved summary of the G3 Opus review; verdict: go-with-changes. Rule, controls and scoring path sound.)
1 lock does not cover scoring code (gen_lora, gen_notes, common, refimpl modules), adapter_config hashes, library versions -> hash and assert.
2 stale test outputs could be reused; leakage check skips the output dir -> assert empty when creating the lock; on re-run validate case ids and record file sha256; analyse needs lock status scored/complete and all 13 files.
3 frozen state not committed; plan lacks the script sha; docstring points to section 6 not 1.
4 "beyond shuffled labels" clause not backed by a condition -> allow only if (c)-a LB>0 on both below and no_cost.
5 smoke report from an older script version and showed real label-only test statistics (always-cheapest 0.000 on grid E, 3.98 on hard_V) -> disclose, rerun fake analysis with the frozen script.
6 overlap not tied to wording -> fix the rule now.
7 slices: Holm or transfer wording only if test_hard passes overall; cond 4 descriptive <8 below cells; add (b) minus each (a) seed and per-seed conditions 1-3; state primary sets not corrected against each other.
8 minor: assert slice counts and 2 cases per cell; assert run arm/seed match name; report dropped slope resamples; enforce stop time; "DESCRIPTIVE ONLY; PASSED" -> "not evaluated"; rule_pos assumes ascending grid.
