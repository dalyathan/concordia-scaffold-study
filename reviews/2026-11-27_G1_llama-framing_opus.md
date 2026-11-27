# G1 blind review (Opus), Llama plan with the assistant-prefix framing, 2026-11-27 (packet /tmp/gate_G1_32380fc1)

**Verdict: go-with-changes.** Trainer compared line by line with gen_lora.py: loss, accumulation, early stopping and reload match. Nine fixes, none a redesign.

1. L1d becomes circular under the prefix (the prefix was chosen because mass was 0.487). Fix: freeze now that L1d (and its 0.98 Brier term) is scored on the no-prefix framing as FAILED with READOUT_PROBE.md as evidence; report the prefixed mass separately; state that every other prediction is scored under a framing changed after the predictions were written.
2. Mass shows the readout is a letter, not that it is Llama's choice; the forced "Answer: (" repeats the user's line against the system sentence and few-shot turns. Fix (minutes): on the same 20 train_other cases generate greedily without the prefix, parse the option named, report agreement with the prefixed argmax; freeze a threshold (e.g. >= 0.7); if it fails, stop and re-gate.
3. Stop rules not enforced in code: step 4 stops only at the 0.5 floor; oracle 4/4 and cheapest-fails-planted-high only logged; --plain-train-record optional; no step-5 driver (lr choice, seeds, 8 h stop by hand). Fix: asserts with exit 2; require --plain-train-record unless --limit; script step 5 with the lr rule in code.
4. Mass band covers plain only; a Notes block could lower an arm's mass. Fix: conclude R2 for an arm only if that arm's tune mass >= 0.9; same for neutral and wrong_rule.
5. lr tie-break default: gen_lora.py defaults to 3e-4; check which lr the Gemma headline used; two-point sweep: pre-register an exploratory third lr or state the limitation.
6. Planted 4/4 is a criterion Gemma never faced (planted-nocost 1.8 vs 1.6). Fix: keep it, also report R3 without planted as a labelled secondary.
7. A selected examples run can silently be plain. Fix: score the last-trained examples adapter too.
8. Robustness: lesson paths relative to cwd, logs/ must exist; the path check covers 3 orders of one case (Gemma: 3 cases).
9. Intervals undercover with about 24 groups; keep the seed-level counts as the main R3 evidence.

Checked and correct: target mapping, epoch-0 comparison, control order, baseline rules, bf16 lm_head on both paths, prefix tokenisation, splits refused. Could not verify: records.py, lock_protected, tests, label/input hashes, whether Gemma adapters pass planted, set_peft_model_state_dict naming (the reload assert would catch it).

Freeze before the test look: framing by hash; adapters (lr, weights sha256, selected or last); arms and test splits (the harness locks only test_same and test_hard; test2_same and test2_newkey are not in this task's locked_splits: confirm where they are locked); statistics and rules; one look keyed on adapter-weights sha256 (_LiveAdapter and LoRASolver describe the same adapter differently); pin tag and G3 token; one adapter per process (a second LoRASolver wraps the model again).
