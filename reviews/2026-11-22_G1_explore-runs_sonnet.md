# G1 exploratory runs: Sonnet (summary of returned text; verdict: GO-WITH-CHANGES)
Cost under 3 GPU-h so Sonnet alone is the right level.
1. Slope on 3 cells is statistically empty (best offer = C in each; 1097/10000 resamples degenerate; ~7 distinct outcomes; plain interval [0.604,0.611] is arithmetic). Demote to descriptive; split soft-regret difference into C<V cells and others.
2. Primary outcome picked after seeing step-1 slopes: label post hoc; forking paths.
3. No decision rule written; pre-write what outcomes mean.
4. Winner's curse: seed 0 chose lr and is the best method seed; report seeds 1-2 only as main readout; fixed-epoch readout; log per-epoch probs in new runs.
5. Wrong-rule control weak (train regret 0.816 vs plain 0.778; slope 0.03); report in-prompt regret of wrong-rule/neutral text and student-teacher KL; gain sits only in the 3 C<V cells (method worse on (3,C4): 0.170 vs 0.002).
6. If hard stop triggers neutral could have 1 seed; pre-specify fallback.
7. Effective n stays 6 cells; seeds measure training noise only; within-family generalisation.
8. Confirm neutral chosen lr is a real trained adapter (it is: 1e-4, best epoch 1).
Code: slope definition matches lora.py; bootstrap drop is the artifact in 1, not a bug. Freeze before test: adapter sha256/lr/epoch/seed, test cell list, one primary metric and threshold, owner decides whether tune-set exploratory evidence can license the look, procedure, null wording, locked scoring code.
