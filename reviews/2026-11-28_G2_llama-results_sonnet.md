# G2 review (Sonnet), Llama results, 2026-11-28

**Verdict: partly justified.** The LoRA contrasts (R3 secondary, R4, R5) are sound for in-family tune cells and the multiple-choice letter readout. The R1 wording ("fails as Gemma did", "barely tracks cost") and the R2 mechanism ("pushing toward lower offers") are not supported by the numbers in the packet. I read all files but could not execute anything. The run records, protected payoff and scorer code, claude_labels.json and the tests were not in the packet.

1. **R1 and R2 mechanism claims go beyond the data.**
   - Plain (1.184) is almost the uniform-random reference (1.260). The gap is 0.076, and it is just as small within each type (below 1.83 vs 1.87, at-or-above 1.28 vs 1.33, no-cost 0.45 vs 0.58). After order averaging, Llama's picks carry almost no price information. Gemma's plain regret (0.657) was well below uniform. "Fails as Gemma did" meets the frozen R1 rule mechanically, but the failure is probably a different kind: Gemma offered too little, while Llama's error may be near-chance or too high.
   - The direction of Llama's error is never measured. In below-cost cells an offer under the stated cost is rejected, so "pushing toward lower offers" is implausible as stated. The wrong rule's biggest gain is on at-or-above cells (1.28 to 0.44). That could be a lower-offer effect, but it could equally be that any short anchoring sentence helps a near-random chooser, or that it reduces the letter-d bias (plain top-letter share 0.39 vs 0.28-0.30 in the arms).
   - "Offer barely tracks stated cost (slope 0.26)" has interval [-0.11, 0.74]. That includes both 0 and the rule's 0.76, and the report's own prediction scoring marks L1c UNCLEAR.
   - Fix: compute the signed offer error (expected price minus best price) per arm and type from the existing records; no GPU is needed. Then drop the mechanism sentence or test it with a "double the stated cost" rule and a length-matched one-sentence neutral control. State R1 as "plain is close to uniform on every type", and drop the slope claim.
2. **R3 wording and the planted no-cost case.**
   - Reporting "not replicated" under the frozen rule is correct; do not relabel it as a pass.
   - Two things cut against the "near-tie, so harmless" framing. Seeds 0 and 1 have the wrong top option (3 and 1), and seed 1 puts 0.13 on the best option, below the uniform 0.20. The 0.9 bar is badly calibrated for a near-tie, but this is still one case, so it neither clears nor condemns the adapters.
   - Gemma's adapters were never held to planted checks, so the failure is not a replication difference.
   - Cheapest check: top-option accuracy and hard regret on the no-cost tune cells, and on the training no-cost cells, for each adapter. Also check whether Claude's labels on the no-cost training cells are payoff-optimal (not verifiable from the packet).
   - The proposed wording needs three additions: "multiple-choice letter readout", "one fixed training draw and label set", and the per-seed range (0.024-0.082). It should also say that one of the four planted cases failed in all three seeds, with its masses.
3. **Readout validity.**
   - The prefixed letter agrees with Llama's free answer only 0.53 of the time. The free answer is consistent across orders in 6/20 cases, and the prefixed argmax in 3/20. The check was relaxed post hoc (L18).
   - The adapters are trained and scored on the same letter readout. So "teaches Llama to haggle" is unsupported; only "teaches the letter readout" is.
   - Cheapest check: greedy free-text offers from plain and the three examples-100 adapters on the 42 tune cells, parsed and scored (minutes of GPU).
4. **Tune is near-duplicate of train in decision-relevant features.**
   - Decisions depend on V, grid and stated cost. Tune cells differ from training cells mainly in prior, wording and names, and were chosen from the same small feature space. The plan admits "in-family".
   - So 0.048 largely measures recall of the labelled mapping; examples-25 reaching about the same value is consistent with that.
   - Check: the share of tune cells whose (V, grid, C, type) tuple occurs in the 100 training cells, and regret split by seen and unseen tuples.
5. **Statistical limits.**
   - There are 19 clusters. Intervals are conditional on one training draw and one label set, and there are three seeds.
   - Examples-100 minus examples-25 has interval [-0.097, 0.002], and the seed spread alone is 0.058, so R5 "within 0.05" cannot be resolved.
   - The lr choice (select_B 0.053 vs 0.072) is smaller than the seed-to-seed spread of select_B (0.043-0.079). It is noise, but harmless: 3e-4 gives tune 0.069.
   - The cheapest-label adapters collapse exactly onto always-cheapest, so beating them is a weak test. The informative comparators are scrambled (0.659) and the stated-cost rule (0.214). Examples-100 minus rule is -0.167 [-0.400, -0.029], which is marginal.
6. **Gemma comparison.** Keep it as description only and do not quote deltas such as "+0.527". Parity was skipped, and framing, prefix, attention and GPU all differ.
7. **Code.**
   - No bug found that moves the headline numbers.
   - Checked and consistent: the letter-to-option mapping in evaluate.py; training targets matching scoring; linearity of soft regret, which justifies seed averaging; shared bootstrap indices in paired differences; the reload assertion; and the planted-case payoffs against the arithmetic in the comments.
   - Minor issues:
     - `if not control: break` is dead code, because control is always True.
     - `_prior_look` keys on the solver-config hash (which includes the adapter hash), so a retrained adapter gets a fresh "single look".
     - L1d is scored on the unprefixed framing while everything else uses the prefix.
   - Not verified: pin enforcement, the protected payoff and scorer, the label files, and the run records.

**Freeze before the single test look:**
- The solver list (three examples-100 seeds, controls, examples-25), each adapter's sha, and selected versus last-epoch adapters.
- The headline split and the claim: test_hard is the only generalisation test.
- The pass criteria per split, including how planted cases are handled (decided before any look).
- The lr, the prefix and the readout.
- The test comparators: plain, the stated-cost rule, scrambled and cheapest-label.
- The cluster definition per test slice; test_hard has no at-or-above cells in hard_V.
- How the seed spread is reported.
- The R1 and R2 wording after the signed-offer analysis; the Gemma comparison stays description-only; the free-answer limitation travels with every test number.
- G3, the owner's go, the lock token, and HARNESS_PIN_REF.
