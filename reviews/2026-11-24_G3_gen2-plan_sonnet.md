# G3 GEN2_TEST_PLAN, Sonnet (go-with-changes)
1. test2_newkey mostly tests novelty beyond training ranges (in-range cells about 18: 13 below, 2 at_or_above, 3 no_cost); 13 cells have V below the cheapest price (forced loss, cheapest best); reword the pass; add in-range, forced-loss and grid-F V>=9 slices; print always-cheapest regret per slice.
2. Pass rule ignores seed variance; plain-minus-a is weak. Require conditions per seed or under seed-and-cluster; add absolute bar (a <= 25% of plain and below the stated-cost rule).
3. Raw coin thresholds; V=15 cells dominate; 0.05 margin post-tune: add scale-free sensitivity; say margin is post-tune.
4. Clustering underspecified; slices with few clusters (V>=13: 12 (V,grid) clusters); the two sets share decision problems (7), so not independent replications; report with duplicates collapsed.
5. Earlier looks (examples-100, cheapest-label-100, rule-soft-100 on test_same/test_hard) not disclosed; expectations written afterwards.
6. Multiplicity: name primary claims, others descriptive; Holm or both-sets rule for the curve claim.
7. Slice wording too permissive; also require always-cheapest minus a > 0 and the absolute bar.
8. Docstring of gen_test2.py contradicts code (cap 2 for at_or_above; in-range counts); plan untracked; fingerprints do not cover gen_lora.py.
Freeze before look: plan commit and hash, script sha, install() and fingerprints recomputed, bootstrap estimator, minimum clusters, absolute bars, scale-free sensitivity, new slices, reference regrets by slice, cross-set shared problems, primary claims, split-verdict wording, lock mechanics, duplicate-collapsed reporting.
