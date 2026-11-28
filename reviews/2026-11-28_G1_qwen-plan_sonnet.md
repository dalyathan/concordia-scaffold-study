# G1 review (Sonnet), Qwen plan, 2026-11-28

**Verdict: go-with-changes.** The design is sound as a tune-only replication; the readout rule fixed in advance and the mechanical prediction scoring are real improvements. The changes are small, but three should be made before the GPU run. Read: all packet files. Not verified: harness/records.py, evaluate.py and tools/llama_report.py (not in the packet); nothing could be run.

1. **The 0.95 readout rule rests on a mean over ~100 prompts from 20 cases.**
   - The probe takes a stride sample, so the 20 cases may not be balanced across case types, and a mean of 0.95 can hide a type or order where mass is 0.6.
   - The probe prints only the Llama bands (0.9 and 0.5) and the mean, so the 0.95 comparison is manual.
   - Fix: freeze, before running, that the rule is mean >= 0.95 AND the minimum per-type mean >= 0.90, or state that it is the mean only and that minima are reported but not used. Log the case-type counts of the 20 cases. Add a `--threshold 0.95` printout.
2. **Possible "(a" merge in the prefixed readout.**
   - Qwen's pre-tokenizer may tokenise "Answer: (a" naturally as "(a", one token. The model check was run with an empty prefix and tests appended ids, not natural tokenisation.
   - If the prefix is used, the rerun should also test whether prefix+letter tokenises naturally as prefix tokens followed by the letter id. If not, say the readout is off-distribution, as it is for Llama.
   - Mass >= 0.95 does not show the model "means" the letter, so the free-answer agreement must appear next to every plain and arm claim.
3. **The GPU budget stop may not work (not verified).**
   - train_lora overwrites the main record's timing with `{"wall_seconds", **records.cost(total), "tune_scoring_seconds"}`, while gpu_hours() sums `timing["gpu_seconds"]`. If records.cost() has no `gpu_seconds` key, LoRA runs count as 0 h.
   - Conversely, gpu_hours() double-counts `_last` scoring (conservative), although the plan says "counted once".
   - Fix: check records.cost before running, or add a test; have the driver skip `_last` records or fix the plan wording.
4. **The step-4 stop uses a different threshold from the readout rule.**
   - The probe rule is 0.95 on train, but the step-4 code stop and the R1/R2 condition use plain tune mass 0.9. This is permitted but inconsistent.
   - Fix: say so, or use 0.95 in both places. Also state that Q1d is scored on the train probe, since no unprefixed tune mass exists for Qwen.
5. **The wrong-rule control cannot answer the content question.**
   - It is one short sentence, not length-matched, and it matched or beat the paragraphs on Llama. A third model with the same control adds little.
   - Option: add a length-matched wrong or irrelevant paragraph (prompt arms only, ~0.1 GPU-h). Otherwise state up front that the content question is expected to stay unresolved.
6. **The planted no-cost failure is now a design question.**
   - Both model families fail it in every adapter and Qwen is predicted to fail (Q4b 0.8), so R3 reads "not replicated" almost by construction.
   - Fix: decide before the run whether this is a model failure or a defect of the planted case or its training coverage, e.g. whether any training label covers a no-cost case with the planted pattern. Keep the secondary R3, and do not read a third identical failure as strong evidence about models.
7. **Free-answer check details.**
   - llama_freegen_check.py still carries the Llama thresholds (0.7/0.5), prints `pass` and exits 2 on fail; descriptive use must not treat exit 2 as a stop. Remove the thresholds or ignore the exit code.
   - The adapter variant loads with PeftModel.from_pretrained, while training and scoring used set_peft_model_state_dict with fp32 adapter weights, so dtype handling may differ. Compare forced-letter regret on this path with the tune record (not verified).
   - The adapter free answer is generated without the prefix it was trained with; note this as off-distribution.
8. **Minor design points.**
   - The two-point lr sweep with the 0.005 default will likely pick 1e-4; it is already reported as a limitation.
   - About 20 (V, grid) groups means percentile intervals undercover; repeat this in QWEN_RESULTS.
   - Adapters may beat the stated-cost rule because tune shares values and grids with training, so keep the seen/unseen split prominent.
   - Restate the Llama clause "plain < 0.30 -> R2-R5 headroom-limited" in R1.
   - "Every seed below plain" is nearly trivial; use the paired interval as the test.
   - The prediction ranges are wide; the Brier terms and the predictions-before-code order partly offset this.

**Checked and fine:**
- step-4 job construction;
- step-5 solver names matching the trainer's lr format;
- the lr rule as frozen;
- hf.py leaving non-soft-capped models on the unchanged path;
- the trainer's path, epoch-0 and reload checks;
- the label sha pins and the select_B/training overlap assertion;
- test splits refused by step 4;
- the prefix applied consistently in training, scoring and the plain train record.

**Freeze before the single test look:**
- the model, the commit pin and the prefix decision, with the probe JSON sha;
- which models are tested (looks multiply);
- the primary and secondary test splits, one look each;
- the adapters (selected or `_last`, lr, seeds), the headline arm and the controls, with no re-tuning after the look;
- the metric, scorer path, hardware and bootstrap;
- pass thresholds against the rule, always-cheapest, uniform and plain, and what "generalises" means;
- how planted cases count;
- a committed test-prediction file;
- G3 and the owner's go;
- no name variants 1-14 and no agent_py_files.
