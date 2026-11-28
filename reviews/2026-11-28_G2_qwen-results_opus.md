# G2 review (Opus), Qwen results, 2026-11-28

**Verdict: partly justified.** The mechanical verdicts (R1 met, R2 helps but content not shown, R3 not replicated, R4/R5 pass) match the tables and the code. Four things need fixing: the training collapse at the chosen lr is left out; the R5 claim is stronger than the seed spread allows; the planted wording hides that the top pick is right; the list of failed predictions is incomplete.

1. **A seed collapses at lr 3e-4, and the proposal does not mention it.**
   - `claude_examples_n100_lr3e-04_s2_last` scores 1.259, which is uniform guessing (1.260): slope 0.06, planted 0/4, mass 0.999. Early stopping at epoch 2 (select_B 0.132) hid this.
   - On tune, seed 0 is 0.030 at 1e-4 and 0.032 at 3e-4, so the two are equal; the select_B gap that picked 3e-4 (0.059 vs 0.020) does not show up on tune.
   - So 3e-4 looks close to unstable, and the R3-secondary result depends on selection rescuing a diverging run.
   - Fix: say so in conclusion 3 and the limitations. CPU check: print seed 2's select_B and train loss at epochs 1-5 and confirm a divergence, not a scoring fault.
2. **R5 ignores seed variance.**
   - "Interval inside +-0.05" is a case bootstrap on fixed seeds. The examples-100 seeds span 0.032-0.104 (0.072, wider than the band) and examples-25 has one seed.
   - The same holds for the examples-100 interval: averaging seeds per case leaves seed variance out.
   - Fix: reword to "examples-25 (one seed) falls within the examples-100 seed range", drop the interval as support, and say that intervals exclude seed variance.
3. **The planted "failure" is a confidence shortfall: the top pick is correct.**
   - All three seeds have top option 2 = the expected offer; the case fails only on mass (0.44-0.71) in a near-tie (1.6 vs 1.8), so its soft regret is about 0.1 or less.
   - Fix: say "top pick correct, mass below the 0.9 bar". The frozen "not replicated" stands.
4. **"Content not shown" in R2 is slightly too strong.**
   - The paired-interval logic is right, but the slope of offer on stated cost is a content-specific signal pointing the other way: written rule 0.334 [0.055, 0.743], lesson 0.239, wrong rule 0.110 [-0.059, 0.450], plain 0.094.
   - CPU checks: a paired cluster-bootstrap slope difference (written minus wrong rule); a content-free "push lower" baseline (shift plain's distribution one grid step cheaper and score it).
5. **R1 could come from the readout.**
   - Agreement with the free answer is 0.53, and the plain:noprefix train score rests on 0.009 mass (weak support). The signed error (+1.64 vs uniform +0.86) points to a real high-price bias, not position bias.
   - CPU checks: regret of the 100 stored free-answer replies against the forced choice and uniform on the same prompts; the unprefixed probe's merged "(a"-"(e" tokens as a letter distribution against the prefixed one.
   - Wording: "its forced-choice expected offer".
6. **Examples-100 minus the stated-cost rule** (-0.151 [-0.382, -0.011]) is the weakest support; with 19 clusters, call it marginal.
7. **The prediction summary is incomplete:** Q1b below and Q1b at_or_above also FAILED (four failed in all).
8. **Minor:**
   - three_model_table reads Llama's controls by solver name, without the control() fallback to `_last` (values look like trained adapters; not verified).
   - The R2-controls text "helps at least as much as either paragraph" is triggered by wrong-minus-plain < 0; it happens to be true here.
   - Checked and correct: regret, bootstrap, sign-flip p, slope, position bias, the seen/unseen regex, prediction precedence, Brier terms, trainer selection/`_last`/reload, the readout path.

**Not verifiable from the packet:** the run records, the protected scorer and payoffs, the Gemma planted masses, the Llama records, the label check, CLAIMS.yaml, the parity.

**Freeze before the test look:**
1. Exact solver configs by hash (`_prior_look` blocks only an identical solver_config_sha256): prefix, commit a09a3545, the three selected examples-100 adapters at 3e-4 by sha (selected, not `_last`; note seed 2's collapse), examples-25, scrambled, plain, the prompt arms.
2. Splits: the plan names test2_same and test2_newkey, but HagglingTask has only test_same and test_hard; settle which exist and are looked at; hard slices separately (hard_V has no at_or_above).
3. Primary endpoint and comparators with thresholds; whether seed variance enters the intervals; the undercoverage.
4. How planted cases count, and the wording when the top pick is right but mass is below 0.9.
5. Written test predictions committed first.
6. Pins and approval: the frozen report and claims sha, HARNESS_PIN_REF, G3 (Sonnet + Opus) and the owner's go.
