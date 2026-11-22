# G2 LoRA verdict: Opus (summary of returned text; verdict: PARTLY justified)
Decision right (rule not met, no test look); proposed text overstates.
1. Outcome label wrong, and "matched" is one-sided in code (trs <= 0.428+0.05) while documented as within 0.05; seed 0 is 0.065 below teacher. Make code and docstring agree; add label "transfers vs plain/neutral; not separated from wrong-rule".
2. Effect is in first-token letter probabilities, not free text (hard regret 0.50->0.47; say agreement 0.58->0.38). S4 passes on 0.03 with no interval. Say so; bootstrap free-text regret per cell.
3. Wrong-rule had less coverage (1e-4, seed 0) than method (3 lrs, 3 seeds); bias favours the method; lower bound -0.003 is within bootstrap noise; do not re-roll the seed. Robustness run: wrong-rule 3e-4, 1e-3 + seeds 1,2 (~1.7 GPU-h, G1 Sonnet alone). 12 runs used ~5.5 of 10 h; planner assumed 6.5 epochs/run, early stopping gave ~4.4, so L4 would have fit; log it.
4. Shuffled control = untrained model (adapter hash equals neutral 1e-3/3e-4 epoch 0); "well below shuffled" and S1-vs-shuffled add nothing; "mass 1.00 everywhere" false.
5. Alternative: generic push to offer ~2 on cells that reward 2 (wrong-rule distil helps 0.448 though wrong-rule text did nothing). Separator is slope 0.66 vs 0.03, with no interval. CPU check: cell-bootstrap of slope difference; per-cell table of the 3 cells where method loses/ties.
6. S1 vs always-2 is not a code bug; save per-cell differences.
7. Add "selected-on" to wording.
Unverified: per-cell numbers behind intervals, METHOD_TEXT_TRAIN 0.428, held-out size (12 vs 24 cases).
Freeze: adapters by hash and epoch, the rule/unit/bootstrap (10,000, seed 0), comparators and criteria, corrected label table, exact test-cell list (variants 1-14 excluded), G3 Sonnet+Opus plus explicit owner go.
