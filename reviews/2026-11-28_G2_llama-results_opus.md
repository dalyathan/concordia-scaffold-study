# G2 review (Opus), Llama results, 2026-11-28

**Verdict: partly justified.** The numbers in the report match llama_report.json, and every mechanical verdict follows from the frozen rules (R1-R5 and the prediction scoring). Three conclusions read more into the data than it shows: R1 ("fails as Gemma did"), the mechanism sentence in R2, and the near-tie framing in R3.

1. **R1: plain Llama is close to uniform guessing, and the failure pattern does not match Gemma's.**
   - Plain tune regret is 1.184; uniform is 1.260. Per type: below 1.83 vs 1.87, at-or-above 1.28 vs 1.33, no-cost 0.45 vs 0.58.
   - Uniform guessing would also meet every R1 condition (>=0.30, interval vs the rule above 0, below is the worst type), so the frozen rule cannot tell "fails like Gemma" apart from "ignores the content".
   - The readout is driven by letter position: 39% of the probability sits on letter d. In the diagnostic, the prefixed pick names the same price in all five orders in only 3 of 20 cases.
   - The direction of the error also differs. Llama's at-or-above regret is 1.28 against Gemma's 0.39. Regret there comes from offering at or above the cost, so Llama mostly offers too much; "offers too little, as Gemma did" is not supported.
   - Fix: state "R1 criteria met; plain Llama is near uniform" and drop "as Gemma did". Cheapest check, CPU only on existing records: the mean signed error (expected offer minus best offer) per type, for plain Llama, the Gemma plain record and uniform.
2. **Readout validity limits every conclusion.**
   - The scored pick agrees with Llama's own free answer on 0.53 of the probe prompts. The 0.7 bar was dropped after the result was seen (L18).
   - Every claim is therefore about the forced-choice letter after "Answer: (", not about the offers Llama would make.
   - The LoRA adapters were trained directly on this readout, so "teaches the model to make good offers" is untested.
   - Fix: say "forced-choice letter" in every conclusion. Cheap check: rerun the free-answer agreement check on the three examples-100 adapters (same 20 train cases, about 20 GPU seconds each).
3. **R2: the mechanism sentence is unmeasured, and the comparison with the wrong rule is untested.**
   - "Pushing Llama toward lower offers" was never measured.
   - An alternative explanation fits equally well: the three texts that help all cut position bias (top-letter share 0.39 down to 0.28-0.30), while the neutral text does not (0.393).
   - The wrong rule also helps no-cost cells (0.446 to 0.269), where "half the stated cost" does not apply, so the model is not following it literally.
   - "Lowers it more" is a gap between point estimates only. No paired interval was computed for method minus wrong rule (0.773 vs 0.611) or teacher minus wrong rule.
   - Fix: add those two paired intervals; report the expected offer per type and arm; add a letter-prior-calibrated regret per arm. Then reword to "the wrong rule helps at least as much; the paragraphs' gain may be generic".
4. **R3: the frozen verdict "not replicated" is correctly applied, but the framing needs two changes.**
   - (a) The planted check was never applied to Gemma's adapters, so "not replicated" partly reflects a stricter bar for Llama, not a shown difference between models. Cheap check: rescore the existing A40 Gemma adapters on the four planted cases. If not run, state this asymmetry next to the verdict.
   - (b) Do not use "near-tie" to soften the result. Seed 1 puts only 0.13 on the best offer and its top choice is offer 2. That fits the adapters' tune no-cost regret (0.056-0.169), the weakest type in every seed.
   - The secondary result (mean 0.048; intervals vs plain, cheapest-label N=100 and scrambled N=100 all below 0) is supported as labelled. It is conditional on one training subset, and seeds 1 and 2 selected their final epoch. That plus the lower lr edge means the lr and step-count effects are unresolved.
5. **R5 is weak.** One seed (0.086) is compared with a 3-seed mean. It is worse than every examples-100 seed (0.024-0.082), and the paired interval is [-0.097, 0.002]. "Within 0.05" holds as frozen, but say examples-25 is about 1.8 times higher. The unselected last epoch of examples-25 (0.057, 4/4 planted) shows how much noise selection adds.
6. **Code issues (none changes a verdict).**
   - The GPU total double-counts about 0.15 h. train_lora.py sets gpu_s = time.time() - t_start after the `_last` tune evaluation, which already wrote its own wall time. The real total is about 3.23 h, not 3.38 h.
   - perm_p can return 0 and the table prints "p 0.000" (teacher). Use (k+1)/(B+1).
   - slope() uses 2,000 resamples; the plan says 10,000.
   - The L2b Brier note says "|teacher - rule|" but computes |teacher - method paragraph|, which is easily read as the stated-cost rule.
   - Checked and correct: the lr rule, the control-version logic, cid matching across seeds, exclusion of planted cases from means, the prediction edge logic (L1a, L1c, L2a, L4a, L4b, L4d), and every Brier term.

**Not verified:** the run records themselves, the protected payoff module (planted payoffs checked by hand: 1, 1.6, 1.8, 1.6, 1), CLAIMS.yaml and check_claims, lock_protected, the step and free-answer scripts, the Gemma records, and the label and input sha256 values. The packet's `commit_pin` keyword spelling in hf.py is taken as the stated packet artefact.

**Freeze before the single test look:**
1. Scope: which splits and slices, the primary comparison, and how multiple slices are handled (hard_V has no at-or-above cells).
2. Exact solver configs. `_prior_look` blocks only a repeat with an identical config hash, so pre-register each solver_config sha256. Pin the adapter weights, lr, prefix, chat-template date, commit pin, report code and bootstrap seeds.
3. Test decision rules: thresholds, the comparators (plain, cheapest-label N=100, scrambled N=100, stated-cost rule), and whether the planted condition counts. The planted cases are the same on every split, so the no-cost failure will recur; decide in advance whether R3-on-test is primary with or without it.
4. Readout: whether the adapter free-answer check runs before the look, and the wording the test result carries either way.
5. Final tune wording for R1 and R2, settled before the test.
6. Test predictions, if any, committed first under the prefixed framing.
7. G3 (Sonnet + Opus), the `G3-OWNER-GO:` token and HARNESS_PIN_REF, all logged in DECISIONS.
