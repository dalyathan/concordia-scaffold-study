(Saved summary of the G3 Sonnet review; verdict: go-with-changes. No error found in scoring/analysis code.)
1 frozen script not committed; lock lacks hashes of gen_lora/gen_notes/refimpl/common and library versions -> commit, record hashes, push lock at once.
2 no guard against stale/pre-existing test outputs; preflight cache could hide a no-op; non-atomic json writes -> assert dir empty, re-score preflight fresh, atomic writes.
3 "beyond shuffled labels" not tested by the rule -> tie to a reported row (c)-a LB>0 on below and no_cost, else drop.
4 a test_same pass may reflect overlap (26/60 current key, 49/60 V+C overlap) -> pre-declare non-overlap condition for the generalisation wording.
5 smoke report came from an older script; edge cases (grid E degenerate intervals) -> rerun fake analysis, n<5 guard.
6 condition 4 on 5-7 below cells unreliable -> descriptive when <8.
7 disclose label-only test statistics seen, stated-cost rule is an oracle on below cells, conditions 2 and 3 both must pass, cond 5 point estimate, write expectation.
Checks passed: scoring path identical to tune, one-adapter-at-a-time with recheck, paired bootstrap, lock logic for crash re-run.
