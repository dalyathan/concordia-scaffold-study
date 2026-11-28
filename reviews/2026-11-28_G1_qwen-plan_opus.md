# G1 review (Opus), Qwen plan, 2026-11-28

**Verdict: go-with-changes.** The design copies the reviewed Llama plan closely, and the readout rule is now fixed before any data, which is an improvement. No error was found that would corrupt the regret numbers. The changes are small and should be made before the first GPU call. The estimate (3.6 GPU-h) is over 3 h, so G1 needs Sonnet + Opus.

1. **The free-answer check still applies the Llama stop rule.**
   - llama_freegen_check.py keeps THRESH_AGREE/THRESH_PARSE = 0.7/0.5, writes "pass", returns exit 2 on fail, and its docstring calls the threshold frozen. The Qwen plan says descriptive only, so `set -e` or a reader could treat it as a failed gate.
   - Fix: for qwen25_7b drop the thresholds, the pass field and the nonzero exit, and update the docstring.
2. **Greedy decoding may not be plain greedy** (not verified).
   - `generate(do_sample=False)` takes its other settings from the model's generation_config. Qwen2.5-Instruct ships repetition_penalty=1.05 and Llama 3.1 does not. That penalty would push the free answer away from letters and prices already in the prompt, biasing Q5 and making Llama-vs-Qwen agreement not comparable.
   - Fix: pass repetition_penalty=1.0 and neutral top_k/top_p/temperature explicitly; record the generation config in the output; report agreement on letter-parsed answers separately (the price fallback takes the first price mentioned, which can be the stated cost).
3. **The readout decision is applied by hand, and the code prints the wrong band.**
   - The probe labels "interpret" at a mean of 0.9 or more, while the rule is 0.95; only the mean is reported.
   - Fix: add --threshold 0.95, compute the prefix decision in code and write it to the JSON, and also report the per-case minimum and the share of prompts below 0.9.
4. **Some decision paths are not specified in advance.**
   - (a) If the train probe is >= 0.95 with no prefix but plain tune mass is below 0.9 (the step-4 stop), the plan must say "stop and report; no switch to the prefix", or the tune cells would choose the framing.
   - (b) Q1d does not say which value is scored.
   - (c) The scoring rule overlaps: the point can be inside the range while the interval straddles an edge, and no precedence is given.
   - (d) Items with both a range and a probability (Q3a, Q3b, Q3d) need a rule for scoring each part.
   - Fix: write these into the plan before the probe runs.
5. **The 5 h budget stop could not be verified.**
   - gpu_hours() sums timing.gpu_seconds, which training records get from records.cost (not in the packet). The `_last` tune scoring is counted twice (conservative).
   - Fix: confirm the key, ideally with a unit test on a stored Llama training record.
6. **The report generator, and so the mechanical prediction scoring, is not reviewed.**
   - Fix: generalise it before the runs, show that it regenerates the Llama results bit-identically, map the Q-ids, and freeze it by commit hash before any Qwen record exists.
7. **Scientific scope (wording).**
   - R3 will very likely read "not replicated" from the single planted no-cost case (Q4b 0.8), so the informative content is in the labelled secondary.
   - Cheapest-label collapses onto always-cheapest, so scrambled-100 and the stated-cost rule (0.214) are the real comparisons; show them next to each other in the headline.
   - Near-zero regret on tune is in-family fit only.
   - The three-model table is confounded by framing; if Qwen ends up unprefixed while Llama is prefixed, say so in the caption.
8. **Minor.**
   - Step 4 logs to logs/llama_step4.jsonl for every model.
   - The hf.py docstring still says "WRITTEN BUT NOT RUN".
   - The step-4 docstring says the floor is 0.5 while the code uses 0.9.
   - A crash after the `_last` record but before the main record would hit "adapters are never overwritten" on restart; log a manual cleanup rule in advance.

**Checked:**
- the yaml pin and letter ids against the model check (all rows pass, real system role);
- Qwen takes the unchanged readout path;
- the output directory resolves to demo_out/qwen;
- the lr rule and the 5.0 h default stop;
- the trainer keeps its path, epoch-0 and reload checks, the sha-pinned labels and the train-to-last-epoch rule.

**Not verified:** harness.evaluate, records, task, the report generator, lesson-text byte equality, and Qwen's generation_config. **Code errors that affect results:** items 1, 2, 3 and possibly 5; none affects soft regret.

**Freeze before the single test look:**
- the prefix choice and commit pin;
- the harness and report commit hashes;
- the adapters (lr, seeds, selected vs `_last`, headline, sha256s), the arms and controls;
- the exact test splits, name variants and orders;
- test versions of R1-R5 with thresholds, the interval method, multiplicity across splits and arms, and how planted cases count;
- separately committed test predictions with HELD/UNCLEAR precedence;
- the hardware (A40);
- no tune-driven change after G3, the owner's go, and what "generalisation" means against in-family.
