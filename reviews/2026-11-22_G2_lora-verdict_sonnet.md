# G2 LoRA verdict: Sonnet (summary of returned text; verdict: PARTLY justified)
Supported: "pass rule not met, not a failure, no test look". Not supported: "well below shuffled" (shuffled never trained: best epoch 0 = untrained model, mass 0.64); the outcome label contradicts the numbers.
1. Outcome label ("learned train cells, did not transfer") wrong when held-out 0.155 beats plain/neutral; add a branch. Held-out regret < train regret, so no transfer gap.
2. Shuffled control empty (epoch 0 selected; train regret rose to 0.987 when trained). Report at fixed epoch from history; drop shuffled claim.
3. Wrong-rule comparison noisy (6 cells, 1 seed, 1 lr; lower bound -0.003 is a coin flip; seed 0 is the best method seed, seed mean 0.194). Run wrong-rule seeds 1,2 at 1e-4 (~50 min); pre-declare as exploratory/seed-averaged; do not amend the rule post hoc.
4. Alternative: generic push of offers toward ~2 (wrong-rule expected offer 1.94; always-2 0.333) plus mass restoration. Against: neutral reaches mass 1.00 and gains 0.043; slope 0.66 vs 0.03/0.08. "Letter mass 1.00 everywhere" is false for epoch-0 arms.
5. Everything selected on the 6 held-out cells; show fixed epochs 1-4.
6. S1 vs always-2 is a lower-bound criterion, not a code error; S3 trivial; S4 (0.47 vs 0.50) is noise.
7. LR coverage unequal but favours the method; cannot explain the miss.
Freeze before test: licensing (owner waiver or pre-declared extension), primary comparison/test/seed, hyperparameters and seed policy (mean of 3, not best), artefacts by sha256 (no retrain on train+tune), outcome-label table, reading of a null.
Could not verify: bootstrap numbers, core.soft_regret, split file.
