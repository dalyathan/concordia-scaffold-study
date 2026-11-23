# G2 gen LoRA verdict, Sonnet (verdict: partly justified; summary of the reply)
1. Neutral control mislabelled: runs with best epoch 0 are dropped, so rule 1 shows "not run"; three neutral runs equal plain by construction; rule 4 alone is the sufficient reason for NOT PASSED. Fix: relabel; optionally neutral at a fixed epoch.
2. "Offers lower" not separated from "offers cheap": teacher-distil is not distinguishable from always-cheapest (+0.053 [-0.098,+0.222]); wrong-rule has 1 seed, stopped at the epoch cap. Checks: mass on the cheapest option by type; a distilled "offer the cheapest" control.
3. Rule 4 failure comes from the paragraph (in-prompt no-cost 0.390 vs plain 0.204; distillation reproduces it), not from distillation. Do not edit the paragraph and retest on the same tune cells.
4. Ceiling lr chosen post hoc: 1e-4 run (0.026; selection 0.054) is better than the reported 3e-4 (0.118).
5. Unequal control coverage; neutral seeds 1-2 were scheduled before wrong-rule seeds 1-2 and used ~40 min on epoch-0 clones.
6. Replication on seeds 1-2 covers only the rule-1 comparisons, not rules 2-5; rule 5 not per type.
7. Overlap: gain is 0.417 on 16 overlapping vs about 0.2 on 26 non-overlapping cells; give an interval.
8. Minor: "equals our-method" needs a margin; lr grid coarse at the low end; docstring names the old selection file.
Freeze before a test plan: whether to test at all after a failed tune run and which claim; exact adapters by sha256; control definitions (neutral at fixed epoch, wrong-rule 3 seeds); primary test set and multiplicity; ceiling lr; overlap stratum; bootstrap settings.
