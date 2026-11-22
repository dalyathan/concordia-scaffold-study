# G2 exploratory reading: Sonnet (summary of returned text; verdict: PARTLY justified)
Numbers match tables. Mechanism sentence ("stated-cost-tracking effect wrong-rule only partly reproduces") not supported (3 cost cells, post hoc split). Both SUPPORT branches fail (loss elsewhere -0.076 > 0.05); NOT SEPARATED not met either; say so.
1. Wrong-rule control not content-free (wrong-rule text in prompt does nothing, distilled arm 0.577->0.40; offers near 2 with slope ~0): partly a shift-to-2. Report always-2 and method gain over always-2 with interval.
2. Selection on held-out cells not symmetric (method trajectory noisy, min-over-epochs flatters it); fixed-epoch seeds 1,2; the per-cell fixed-epoch section printed empty.
3. Seed separation weaker than it reads (3 vs 3; seeds share the 6 cells); say "consistent across seeds on these cells".
4. Slope/cell split post hoc, 3 points; remove from headline; (5,C4) expected offer 2.72 vs best 4.
5. Train-cell evidence unused (wrong-rule gain smaller on train than held-out).
6. Free text unchanged, agreement falls: limitation.
7. Neutral 2 seeds; epoch 0 can be returned.
Freeze: new pre-registered rule, comparators incl. always-2, adapters by sha256, epoch rule, cell-type prediction, free-text endpoint, power, G3 + owner go.
