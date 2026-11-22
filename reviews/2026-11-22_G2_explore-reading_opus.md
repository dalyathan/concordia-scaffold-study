# G2 exploratory reading: Opus (summary of returned text; verdict: PARTLY justified)
1. Backup SUPPORT clause also failed (loss elsewhere 0.076 > 0.05); NOT SEPARATED not met; rule leaves the in-between case undefined: say so.
2. "Wrong-rule only partly reproduces" is wrong: slope -0.01, offers 1.97-2.09 everywhere = noisy always-2; always-2 scores 0.333; method beats always-2 in only 2 of 6 cells. Name always-2; bootstrap method vs always-2.
3. Headline uses the seed that chose the lr; report seeds 1,2 (0.213 vs 0.391, +0.178 [-0.043,+0.462]).
4. Early stopping favours the method; epoch-4 gap still ~0.23 (aggregates); per-cell section empty because method runs predate logging; call held-out "selected-on".
5. Code version between runs: check diff/metadata (only logging changed; trainable_parameters equal).
6. Seed spread is training noise; cell-level uncertainty dominates; percentile bootstrap at n=6 optimistic.
7. Slope/split post hoc; free text unchanged (answer_only LoRA does move free text, so setup can).
8. Neutral 2 seeds; lrs at grid edges; wrong-rule grid flat.
Freeze: one estimand, adapters/seeds/sha256, aggregation and full outcome table incl. in-between case, secondary measures descriptive, code commit, no variants 1-14/train/tune cells, owner decision whether a test look is warranted.
