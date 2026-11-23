(Saved summary of the G1 Sonnet review of GEN_CURVE_PLAN.md / PREDICTIONS.md; verdict: go-with-changes. No code error that invalidates the runs.)
1 subset draw not replicated: N effect confounded with the draw; intervals exclude draw variance -> state; (optional second draw / per-seed draws).
2 tune bootstrap near a plain cell bootstrap (38 problems / 42 cells); dependence by V, grid -> also cluster by (V, grid); score "lower bound > 0" conditions on the wider interval.
3 P2 ignores noise and bundles three probabilistic statements -> split into binary predictions with probabilities, define "within 0.05".
4 P1 monotonicity (50 -> 100) a coin flip -> require 10 > 25 > 50 and a tolerance of 0.02 for 50 -> 100.
5 P4 over-reads the design (content vs label quality; per-order argmax targets noisy; closed-share ratio unstable) -> log argmax disagreement, interval on the ratio, say the 2x2 cell is missing.
6 N=50 last: a cut loses the point P2 depends on -> run examples-50 s0 earlier.
7 lr 1e-4 and 500 steps come from N=100 -> declared limit.
8 smaller: P6 number for cheapest-label slope; lower ends of ranges cannot fail; within-generator only.
Code: label_info over all 100 cases not the subset; report NaN printed as "no"; closed share uses 3-seed mean vs single seed; per-seed values missing; unused RNG_IDX; docstring; chain pushes tune results each run (peeking); subsets sha not pinned; commit all code, freeze hashes, no edits after the first run.
