# G2 review (Sonnet), Qwen results, 2026-11-28

**Verdict: partly justified.** Read: proposal, results, plan, predictions, decisions excerpt, code. Not re-run; run records, claims checker and dataset scripts were not in the packet; numbers checked for internal consistency only.

1. **Conclusion 3 omits an instability; "near zero" rests on early stopping.**
   - The seed-2 last-epoch adapter (`_last`) scores 1.259, equal to uniform (1.260), with planted 0/4 and slope 0.06. That is the signature of a fixed-letter adapter, since order-averaging turns a fixed letter into a uniform spread.
   - Seed 2 is good (0.104) only because select_B stopped it at epoch 2. Seed 1 stopped at epoch 3 and seed 0 at the last epoch, so 3e-4 is probably at or past the edge of stability.
   - The two-point lr sweep chose the upper lr on seed 0 alone.
   - The seed range (0.032-0.104) makes the three-model ranking of examples-100 meaningless.
   - Fix: state that "near zero" holds only with select_B early stopping and report the `_last` collapse. Report per-epoch select_B for all seeds (in the record histories). Optionally run seed 2 at 1e-4. Freeze the stopping rule for a test look.
2. **Conclusion 2 overstates.**
   - The wrong rule is not shown to beat the written rule: [-0.060, 0.458] includes 0. It does beat the lesson (0.622 [0.202, 0.933]). Use "at least as much as".
   - The mechanism is unresolved: the wrong rule's slope on stated cost is 0.11 [-0.06, 0.45]. Literal rule-following would give about 0.5, so this looks like a generic push lower (plain signed error +1.64, wrong rule -0.06).
   - Length is confounded: one sentence against paragraphs.
   - Cheapest check (about 0.02 GPU-h per arm on tune): decoys "offer double the stated cost", "offer the highest price" and a length-matched wrong paragraph.
3. **Conclusion 1 is about a forced readout.**
   - Agreement with the free answer is 0.53, so "worse than uniform" is about the prefix-forced letter, not what Qwen would write. Do not extend "the picks are systematically wrong" to Qwen's behaviour as a buyer.
   - Support: the train split shows the same direction (1.534 vs 1.204).
   - Read the signed error +1.64 against uniform's +0.86, a grid-asymmetry baseline; plain's excess is about +0.8.
   - Cheapest check: score parsed free answers as regret on tune for plain and the adapters.
4. **R3 and the planted case.**
   - "Not replicated" is correct and the proposed sentence is agreed.
   - A 0.9 bar on a near-tie is harsh, and the top option is the acceptable one. The failure is shared by all three models, so it is not informative about Qwen.
   - The pre-run label and coverage check could not be verified (label file not in the packet).
   - Seen/unseen (0.041 vs 0.081; 36 of 84 tune cases seen) points to limited generalisation, so keep "in-family".
   - Cheapest check: no-cost cells with V 6 and grid A at other priors.
5. **Interval strength.**
   - The intervals come from about 19 clusters and undercover.
   - "Beats the stated-cost rule" (-0.151 [-0.382, -0.011]) is borderline: say "comparable to or slightly better than". The adapter slope (0.743) is close to the rule's (0.76), so the adapters approximate the rule, with better no-cost behaviour.
   - Cheapest-label is a degenerate control; scrambled is the informative one, and is also selected on select_B.
   - The one-training-draw caveats stand.
6. **Conclusion 5:** confounded by prefix, system role, date header and the recipe being tuned on Gemma, as the report states. Drop any ranking of the adapter numbers.
7. **Code:** no error changes the headline.
   - Checked: the training path matches the scoring path, the loss uses full-vocabulary log-probs with the target from the label's letter, and planted_ok and mass are as described.
   - Caveats: the path-check tolerance (1e-2 nats) is loose for bf16; the assistant prefix repeats "Answer: (" that ends the user turn (consistent across models, a quirk).
   - Not read: the report generator, scorer and probe scripts.

**Predictions:** the scoring follows the stated precedence. UNCLEAR where the point is inside but the interval touches an edge (Q3a, Q3e) should not be reported as a hit; Q2b is UNCLEAR with its point outside the range, by the rule.

**Freeze before the test look:**
- lr 3e-4, select_B early stopping (patience 2, epoch 0 a candidate), the three trained seeds, no retraining;
- selected or `_last`, and the aggregate (3-seed mean plus per-seed values);
- the split or splits and the per-slice analysis, with descriptive comparisons named in advance;
- the criteria and how planted counts;
- the comparators and the interval method;
- the readout prefix, and no tuning on test;
- whether prompt arms are tested at all (if so, decoys on tune first);
- the conclusion wording written before the look.
