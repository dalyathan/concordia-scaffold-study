**Verdict: partly justified.**

- Numbers 1 and 3 hold with qualifications (problems 2 to 5). I recomputed all seven arm means in HARDWARE_PARITY.md from summary.json and they match.
- The cause attribution in number 2 is plausible but not proven (problem 1).
- The claim "arm gaps 0.01–0.6" is wrong for two comparisons (problem 2).

I could not open demo_out, the A40 probabilities file, the token lengths, the git log or the A10G logs, so none of those are verified.

**Problems, ranked by severity**

1. **The "hardware, not code" attribution rests on a confounded length split.**
   - The evidence is that 6 of 84 gen cases (590–601 tokens) match bit for bit, 78 differ, and the original dataset (592–601 tokens) is identical.
   - Length is confounded with dataset and template: the original and gen prompt formats differ, and the 6 matching gen cases may share a type or wording.
   - No token count appears between 601 and 603, so a "threshold" sits in an empty interval.
   - The kernel was not identified, and the A10G driver was not recorded.
   - A same-session A40 repeat shows only in-process determinism. Different cuBLAS workspace or heuristic state across processes is not excluded.
   - **A10G cross-process control (partial evidence from the folder):** in summary.json the A10G values for plain, which came from gen_score.py, equal those for the neutral and teacher_lr1e-03 epoch-0 runs from gen_lora.py. Overall soft regret is identical to all digits (0.657241610819068). That supports A10G cross-process determinism on long prompts, but the write-up never uses it. Per-case equality is unchecked.
   - **Cheapest fixes:**
     - Use that control explicitly.
     - Rerun plain gen tune in a fresh A40 process and compare bit for bit.
     - Tabulate the 6 matching cases by type and variant.
   - The conclusion survives either way, because the two quantities that matter are the size of the effect and the fact that the code is unchanged. Say "consistent with hardware or driver kernel selection" instead of "Cause: hardware".

2. **"No conclusion changes, arm gaps 0.01–0.6" is not supported by the table.**
   - Examples-25 vs examples-50 differ by 0.0019 on A10G (0.0416 vs 0.0397) and 0.0016 on A40.
   - Teacher lr1e-4 vs method_original differ by 0.0028 on A10G (0.3757 vs 0.3729) and 0.0030 on A40.
   - These gaps are the same size as the per-run A40 shifts. The shifts reach 0.0012 for teacher and 0.0034 for examples-n10_s1. Per-type shifts reach 0.007.
   - The orderings are unchanged, so no conclusion flips, but the sentence is false as written.
   - **Fix:** state the noise floor (about ±0.003 overall per arm, ±0.007 per type, ±0.07 per cell). List every pairwise comparison in the reports with a gap under about 0.01, and say that those were never resolved beyond hardware noise and seed spread.

3. **The decision rule is ill-posed and the verdict wording mixes two things.**
   - The 3-decimal clause fails for any non-bit-identical result. The count "28 of 34 rows flip" mostly measures rounding boundaries, so it is uninformative.
   - Item 1 says "NOT hardware-only", while item 2 attributes the cause to hardware. A reader will read these as contradictory.
   - The 0.005 threshold is applied to the overall regret only. Per type, plain "below" moves +0.0054 and examples-n10_s1 "at_or_above" moves −0.0071. Both exceed 0.005, and the reports state per-type numbers.
   - **Fix:** record two separate findings. The cause is hardware or kernel selection, with the code unchanged. The effect is below 0.005 overall, but not below 0.005 per type, and not bit-compatible.
   - Keep the literal rule outcome as logged, but do not name it "hardware-only".

4. **The startup tolerance is left broken without a decision.**
   - Step 3 of the request was cut off, so the demo cannot start on the A40.
   - You already have A40 per-case probabilities and an in-session repeat that is bit-identical.
   - **Fix:** store A40 reference probabilities for the check cases, check against them at 1e-6 on the A40, and keep the A10G references for the A10G. First confirm cross-process A40 reproducibility (problem 1).
   - Do not raise FLOOR_ADAPTER_TOL globally. A value around 1e-4 would also have passed some arms that are really different.

5. **Verification gaps in the report code (minor).**
   - The "recomputed regret equals stored within 1e-9" assertion is skipped for plain: `stored_summ.get("plain")` is None, and the same holds for original-dataset plain.
   - Plain is covered only indirectly, through the identical neutral A10G value. The headline 0.657 → 0.661 depends on this.
   - The gen plain reference is the 84 tune rows of gen_plain_scores.jsonl, and the check against the stored per-case `soft_regret` field was not done. It is a one-line addition.
   - The hw_parity.py assertion that the plain text equals the render with no notes is good.
   - I found no code error that changes the table. Argmax changes sum to 13 and the 28 flip rows tally correctly.

6. **Neither GPU is a reference.** The bf16 lm_head step quantisation (0.125 near 20) means each result is one of two roundings. Optionally, score about 10 long cases in fp32 to show that both are within noise of the truth. This is not needed for the decision.

**What to decide or freeze before the single test look**

- **Hardware and stack.**
  - All test numbers will be A40, because the A10G is gone. Freeze the GPU, driver, container, torch/cu121/cuBLAS versions and batch-1 sequential scoring.
  - Reaffirm the rule "no mixing". Rescore plain and every comparator on the A40 in the same session as the test, on the tune cases too, so that every tune-vs-test comparison is A40 vs A40.
  - The A10G tune numbers must not be the reference for the test comparison.
- **Candidates.**
  - Freeze the arms, seeds, adapter hashes (the sha256 values already recorded) and the examples seed picked by `pick_examples_run`.
  - Freeze the plain and neutral controls.
- **Metric and decision thresholds, in A40 terms.**
  - Freeze cell-mean soft regret, hard regret and the type breakdown.
  - Add a minimum difference that exceeds the numeric noise floor (at least 0.01, or a seed-spread criterion). Comparisons below it are reported as unresolved.
  - Freeze the rounding precision (use 2 decimals, or give the noise).
- **Test-prompt lengths.** Check the length distribution of the test_same and test_hard prompts before looking. If they are longer than 649 tokens, the kernel regime is untested, so repeat the A40 determinism check at those lengths on tune-like prompts.
- **Startup check.** Freeze the A40 reference probabilities and the tolerance (problem 4). Write the verdict wording from problem 3.
- **Process.** G3 sign-off and the owner's explicit go are still required under CLAUDE.md. The README node for this step should stay at 🟡 until problems 1 and 2 are addressed.
