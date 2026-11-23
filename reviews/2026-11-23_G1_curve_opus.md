(Saved summary of the G1 Opus review of GEN_CURVE_PLAN.md / PREDICTIONS.md; verdict: go-with-changes.)
1 train and tune cells may share decision problems; N does not count distinct problems -> count distinct problems per subset, covered / uncovered tune cells per N.
2 content-vs-kind reading (P4) largely fixed by construction (paragraph argmax hard regret 0.41 > rule-soft 0.376; Claude labels = oracle) -> report each target's own regret, argmax (hard) regret of every run, reword P4 as match-or-beat the target policy; a real 2x2 needs examples-soft (about 0.6 GPU-h).
3 scoring rule too lenient (FAILED only outside by more than the range width; point predictions have no direction; probabilities not scorable) -> HELD inside the range, FAILED outside, UNCLEAR only for CI-straddled thresholds; Brier for probabilities; mechanical scoring in the report script.
4 provenance: code uncommitted; code_sha only in label_info; paragraph sha not asserted; report does not assert configs of loaded runs (incl. reused N=100) -> commit, record code sha and git head in every run, assert, check configs.
5 intervals ignore seed and subset variance; single-seed arms -> seed spread of rule-soft-100 as a yardstick; fix the ratio's denominator guard and which rule-soft-100 version.
6 budget estimate omits reload re-scoring and target building (about 7.8 h of 8); a cut lands on N=50 -> pre-declare partial-N=50 scoring or run examples-50 s0 earlier.
7 cheap-offer confound: all at_or_above labels are position 0 -> report share of cheapest labels per subset; below-type regret and stated-cost slope co-primary.
8 constant steps at N=10: first check at 100 steps = 10 epochs -> score set B at steps 25 / 50 too.
9 lr 1e-4 provenance -> state in the limits.
Freeze: hashes of all inputs and reused runs, run list/order, predictions and scoring rule, comparisons, library versions.
