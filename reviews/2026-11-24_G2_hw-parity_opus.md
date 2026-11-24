**Verdict: partly justified.** Conclusion 1 (not hardware-only under the rule) holds and would hold under any reasonable reading of the rule. Conclusion 2 (the cause is the hardware) is plausible but not shown. Conclusion 3 ("no earlier conclusion changes") is stated more strongly than the evidence allows.

I recomputed against summary.json: the 7 seed-averaged arm means, the 28 of 34 gen rows with 3-decimal changes, the 13 of 2,856 top-answer changes, and the 33 + 18 = 51 arm count. All match. The neutral and teacher_lr1e-03 epoch-0 rows equal the stored plain numbers exactly. That shows the A10G was consistent across processes. The A40 plain run was made before PEFT was loaded, so the gen difference does not come from adapter loading. I could not see the run JSONs, gen_plain_scores.jsonl, scoring.py, lora.py, the reports or the git log, so the claims that depend on them are unverified.

**Problems, most severe first**

1. **"No earlier conclusion changes (arm gaps 0.01–0.6)" is wrong as stated.** From the table's own numbers:
   - examples-25 vs examples-50 differ by 0.0019 on the A10G and 0.0016 on the A40.
   - method_original vs teacher lr1e-4 differ by about 0.003 on both GPUs.
   - Single runs are closer still: rule_hard_s0 0.3511 vs teacher_s1 0.3516.
   - These are all inside the largest hardware shift: 0.0035 overall, 0.0071 by type, 0.07 per cell.

   The orderings do survive on the A40 (I checked those above). But no list of the conclusions that were checked is given.
   *Fix:* list every reported comparison (arm vs arm, curve ordering, per-type claims, and any hard-regret or top-answer claims). Recompute each from A40_probs.json and report its gap next to the hardware shift. Better still, compare the hardware shift with the seed spread: examples-10 seeds run from 0.054 to 0.151, which makes the hardware shift negligible.

2. **The scope is narrower than the wording.** Only plain-prompt tune cases were rescored. Not covered:
   - text/notes conditions and steering;
   - selection set B (which drove the lr choice, early stopping and `pick_examples_run`);
   - train-cell scores and the distillation targets;
   - hard regret.

   "Nothing on the original dataset changes" holds only because those prompts are 592–601 tokens. A notes paragraph pushes them past the 603-token point where differences start, so original-dataset text-arm numbers are probably not reproducible either.
   *Fix:* say the scope explicitly. Cheapest check (about 1 GPU-minute): rescore one text arm on the 24 original tune cases.

3. **"Cause: hardware" is not separated from an environment difference at the time the gen numbers were made.** For the A10G, the driver is not recorded and no pip freeze exists. The torch version comes from one unrelated file. peft was missing from the lock until ed4ef98, though that cannot explain the plain result. A cuBLAS heuristic difference from any library or driver mismatch would also give a length threshold. Matching original-dataset numbers made at some other time does not rule this out.
   *Cheapest checks:*
   - confirm the lock at each run file's `git_head` (torch 2.4.1+cu121, transformers 4.44.2);
   - on the A40, profile one 601-token and one 603-token prompt (torch profiler or `CUBLASLT_LOG_LEVEL=2`). If the GEMM kernel switches between them, that supports "kernel choice by size".

   Until then, write "consistent with hardware; not identified".

4. **The demo cannot start on the A40 as left.** The tolerance of 1e-6 fails for every gen adapter: examples is at 7.7e-6, teacher at 7.8e-4 on the 2 check cases. The floor.py comment ("set FLOOR_ADAPTER_TOL (e.g. 1e-4)") would also fail.
   *Fix:* keep 1e-6 but check against references for the current GPU (A40_probs.json, which repeats bit for bit), keyed by `torch.cuda.get_device_name`. Fail loudly on an unknown GPU. Correct the comment.

5. **Rule application.** The rule's first condition was applied to overall soft regret only. Per type, the change reaches 0.0071 (n10_s1 at_or_above) and 0.0054 (plain, below), both above 0.005. Say this. The verdict does not change. "≤ 0.0035" is actually 0.00355.

6. **The explanation of the mechanism is overstated.** Hidden states are bf16 through every layer, not only at lm_head. Differences are also not "either exactly 0 or of order 1e-2": the cheapest_label rows show 1.8e-6 and 2.2e-4, because the probabilities are saturated. Soften the wording.

7. **teacher_* original-dataset run files are excluded silently** (hw_parity.py line 85 and the report). Explain why, or include them.

**Code.** I found no error that changes the reported numbers:
- the regret formula matches `summarize`, and stored values are re-checked within 1e-9;
- the stored plain scores (`g.render`) and the rescore (`render_notes(None)`) are asserted to use the same prompt text;
- the adapter loading re-copies the fp32 weights, and the 18 original-dataset adapters match bit for bit, which supports the loading path;
- the original-dataset plain reference comes from the first run file, but the spread across run files is 0.

I could not verify `scoring.score` or `steer_lib.lora_cases`.

**What to freeze before the single test look**

- **One hardware platform.** Score everything on the A40, including plain and every comparator, and never mix it with A10G numbers. Record GPU name, SM count, driver, a pip freeze, cuBLAS/cuDNN versions, eager attention and batch size 1.
- **A tripwire.** In the same process, just before opening the test set, rescore a fixed set of tune cases. They must equal A40_probs.json bit for bit, or the run aborts.
- **The arms and adapters**, by run id and sha256. Keep the existing A10G-based selections (lr, best epoch, examples seed). Do not reselect from A40 rescoring.
- **The metric:** cell-mean soft regret, five orders, both name variants. Also the reporting precision and the analysis script hash.
- **A minimum effect to interpret.** Set it above both the hardware shift (about 0.004 overall, 0.007 by type) and the seed spread. Fix it in advance, together with the decision rules for each comparison.
- **The demo reference and tolerance policy** (item 4), and how README/report numbers are labelled by hardware.
