# HARDWARE_PARITY.md: AWS A10G → RunPod A40 (Nov 24, 2026)

**Question.** Does the move from the AWS A10G to the RunPod A40 change any stored number? The demo startup check failed on the A40: adapter "teacher" was 7.8e-4 from its stored A10G tune probabilities on the 2 check cases, examples 7.7e-6; adapter-off still matched plain bit for bit.

**What was done.**
- `demo/hw_parity.py` rescored on the A40, with the stored code (`gen_lora.score_case`, adapters loaded as `demo/floor.py` loads them):
  - the 42 generated tune cells (84 cases: both name variants, five orders) for plain and all 33 gen adapters with a run file;
  - for the 18 original-dataset adapters with a run file, their own 24 stored tune cases (build and tuning cells; `scoring.score`, as `demo/lora.py` scored them). They have no stored A10G probabilities on the gen cells.
- The three `_smoke` adapter folders have no run file and were skipped. `demo_out/lora/teacher_*.json` are teacher-target caches, not adapter runs, and were skipped.
- **Scope:** plain-prompt first-token probabilities on tune cases only. Not rescored: text/notes rows, steering, selection set B, train cells, distillation targets, and free-text answers. Hard regret is not reported here, but 13 top-answer changes are counted.
- No test split was opened (the script asserts the split).
- `demo/hw_parity_report.py` compares with the stored A10G per-case probabilities: `demo_out/gen_plain_scores.jsonl`, `tune_probs_best` in each run file, and `history[0].tune_probs` for original-dataset plain. Per-case A40 probabilities are in `demo_out/hw_parity/A40_probs.json`; the summary is in `demo_out/hw_parity/summary.json`.
- The regret code was checked: recomputing each run's A10G soft regret from its stored probabilities equals the stored value within 1e-9 for all 51 runs.
- GPU time: 57 min of scoring, one process. Projected at 55 min from the plain pass, so gate G1 was not run (under 1 h, already-reviewed scoring code); the actual run took slightly over 1 h with model loads.
- Follow-up checks after gate G2 (`demo/hw_parity_checks.py`, `demo_out/hw_parity/checks.json`, a few GPU minutes); results in the Cause bullet below.

## Hardware and software

| | A10G (stored numbers) | A40 (this rescore) |
| --- | --- | --- |
| GPU | NVIDIA A10G (AWS g5.2xlarge), Ampere GA102, sm_86 | NVIDIA A40 (RunPod), Ampere GA102, sm_86, 84 SMs, 48 GB |
| Driver | not recorded | 595.112.07 (nvidia-smi reports CUDA 13.2) |
| torch / CUDA runtime / cuDNN / cuBLAS | 2.4.1+cu121 (recorded in `demo_out/test_dryrun_raw.json`), same lock file | 2.4.1+cu121 / 12.1 / 9.1.0 / 12.1.3.1 |
| transformers / peft | 4.44.2 / 0.12.0 | 4.44.2 / 0.12.0 |
| Model | Gemma 2 9B-it @ 11c9b309, bf16, eager attention | same (shard hashes checked by setup_pod.sh) |

## Results

**Summary.**

- **Original dataset:** every case is bit-identical, for plain and for all 18 adapters (max abs difference 0.0).
- **Generated dataset:** probabilities differ.
  - Overall tune soft regret changes by at most 0.00355 coins, in plain, the three `gen_neutral` seeds (whose best epoch 0 means a zero adapter) and `gen_teacher_lr1e-03_s0` (also an epoch-0 run). Every other gen arm changes by less than 0.0035.
  - **No arm reaches 0.005.**
  - By type, two changes exceed 0.005: −0.0071 (`gen_claude_examples_n10_lr1e-04_s1`, at_or_above) and +0.0054 (plain, below).
  - The largest per-cell change is 0.070: `gen_rule_hard_n25_lr1e-04_s0`, cell V9-gC-information-C5-p2_6-w0.
  - The order-averaged top answer changes in 13 of 2,856 case-arm pairs.
- **Repeatability on each GPU:**
  - A40: the teacher adapter repeats bit for bit in the same session, and plain repeats bit for bit in a fresh process (84/84 cases).
  - A10G: the stored plain file (`gen_score.py`) and the four epoch-0 training runs (`gen_lora.py`, separate processes) are equal per case, bit for bit.
  - So neither set of numbers is run-to-run noise.
- **Cause: consistent with GPU kernel selection by matrix size; not fully identified.**
  - Every gen tune case whose five prompts are all 590–601 tokens long (6 of 84: 2 at_or_above and 4 no_cost, variants V2, V4, V5, V8) matches the A10G bit for bit. Every case whose prompts are 603–649 tokens (78 of 84) differs. No case has 602 tokens.
  - The original-dataset prompts are 592–601 tokens: all identical.
  - The model, the lock file versions and the scoring code are the same. No scoring code changed after `demo_out/gen_plain_scores.jsonl` was made (git log).
  - On the A40 the torch profiler shows an extra CUTLASS bf16 GEMM kernel (`cutlass_80_tensorop_bf16_s16816gemm_bf16_128x256_32x3_tn_align8`) at 603 tokens that is not used at 601 tokens. Which kernels the A10G used cannot be checked now, and its driver was not recorded, so a driver difference is not excluded.
  - Why the shifts can be large: activations are bf16 through every layer, and `refimpl/local_gemma2.py` also computes `lm_head` in bf16 before the float32 soft-cap and log-softmax. A small upstream difference can therefore move a logit by a whole bf16 step (0.125 near 20). Shifts are of order 1e-2 where probabilities are not saturated, and much smaller where they are (`gen_cheapest_label` rows: 1.8e-6 and 2.2e-4).

Columns:
- **dp:** absolute probability difference per case and price, over all cases.
- **Δ:** A40 − A10G, in coins of cell-mean tune soft regret.
- **Largest cell Δ:** the per-cell soft-regret change with the largest magnitude.
- **3-dp flips:** values whose 3-decimal rounding changes.

| Data | Arm | max abs dp | mean abs dp | soft A10G | soft A40 | Δ soft | Δ below | Δ at/above | Δ no-cost | largest cell Δ | argmax changes | 3-dp flips |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gen | plain | 5.8e-02 | 5.6e-03 | 0.6572 | 0.6608 | +3.5e-03 | +5.4e-03 | +3.6e-03 | +1.7e-03 | +5.9e-02 | 0 | overall,below,at_or_above,no_cost |
| gen | gen_answer_only_lr1e-04_s0 | 2.1e-02 | 1.6e-03 | 0.0258 | 0.0271 | +1.3e-03 | -9.4e-06 | +3.8e-03 | +4.0e-05 | +3.8e-02 | 0 | overall,at_or_above |
| gen | gen_answer_only_lr3e-04_s0 | 1.0e-02 | 9.6e-04 | 0.1184 | 0.1187 | +2.9e-04 | +8.4e-05 | +4.8e-04 | +3.1e-04 | -6.1e-03 | 0 | overall,no_cost |
| gen | gen_cheapest_label_lr1e-04_s0 | 1.8e-06 | 2.1e-07 | 0.4286 | 0.4286 | +3.3e-07 | +6.2e-07 | +3.8e-07 | -1.8e-08 | +4.3e-06 | 0 | - |
| gen | gen_cheapest_label_n25_lr1e-04_s0 | 2.2e-04 | 1.8e-06 | 0.4286 | 0.4286 | +1.2e-06 | +3.8e-06 | -2.5e-07 | +8.2e-08 | +6.1e-05 | 0 | - |
| gen | gen_claude_examples_lr1e-04_s0 | 4.9e-02 | 1.1e-03 | 0.0131 | 0.0131 | +1.7e-05 | +5.5e-05 | -2.7e-06 | -4.0e-07 | -1.1e-03 | 2 | - |
| gen | gen_claude_examples_lr1e-04_s1 | 1.9e-02 | 7.0e-04 | 0.0264 | 0.0265 | +1.1e-04 | +1.8e-05 | -2.4e-04 | +5.5e-04 | -3.4e-03 | 0 | - |
| gen | gen_claude_examples_lr1e-04_s2 | 2.1e-02 | 1.2e-03 | 0.0567 | 0.0576 | +8.7e-04 | +4.1e-04 | +1.6e-03 | +6.1e-04 | +2.2e-02 | 0 | overall,at_or_above |
| gen | gen_claude_examples_lr3e-04_s0 | 4.2e-02 | 1.3e-03 | 0.1194 | 0.1191 | -2.9e-04 | -6.4e-04 | +2.0e-04 | -4.4e-04 | -9.1e-03 | 1 | below,at_or_above |
| gen | gen_claude_examples_n10_lr1e-04_s0 | 3.2e-02 | 1.5e-03 | 0.0711 | 0.0712 | +5.6e-05 | +3.6e-04 | -1.6e-04 | -2.8e-05 | +9.5e-03 | 1 | - |
| gen | gen_claude_examples_n10_lr1e-04_s1 | 7.3e-02 | 2.0e-03 | 0.1513 | 0.1479 | -3.4e-03 | -5.1e-05 | -7.1e-03 | -2.9e-03 | -6.7e-02 | 2 | overall,at_or_above,no_cost |
| gen | gen_claude_examples_n10_lr1e-04_s2 | 2.6e-02 | 8.8e-04 | 0.0537 | 0.0538 | +8.2e-05 | -5.4e-04 | -6.5e-05 | +8.5e-04 | -4.5e-03 | 0 | below,no_cost |
| gen | gen_claude_examples_n25_lr1e-04_s0 | 3.2e-02 | 5.5e-04 | 0.0430 | 0.0427 | -3.1e-04 | -6.2e-05 | -6.1e-04 | -2.4e-04 | -1.2e-02 | 0 | no_cost |
| gen | gen_claude_examples_n25_lr1e-04_s1 | 2.2e-02 | 4.6e-04 | 0.0366 | 0.0371 | +4.8e-04 | -3.9e-05 | +1.6e-03 | -1.4e-04 | +2.3e-02 | 0 | at_or_above |
| gen | gen_claude_examples_n25_lr1e-04_s2 | 5.0e-02 | 7.4e-04 | 0.0453 | 0.0447 | -6.0e-04 | +4.6e-04 | -3.1e-03 | +8.3e-04 | -4.6e-02 | 0 | at_or_above,no_cost |
| gen | gen_claude_examples_n50_lr1e-04_s0 | 1.5e-02 | 5.9e-04 | 0.0144 | 0.0145 | +1.3e-04 | -5.5e-04 | +1.3e-03 | -3.4e-04 | +1.8e-02 | 0 | overall,at_or_above |
| gen | gen_claude_examples_n50_lr1e-04_s1 | 4.0e-02 | 1.7e-03 | 0.0279 | 0.0284 | +4.3e-04 | +2.6e-04 | -5.9e-05 | +1.1e-03 | +8.0e-03 | 1 | no_cost |
| gen | gen_claude_examples_n50_lr1e-04_s2 | 1.3e-02 | 7.7e-04 | 0.0768 | 0.0767 | -5.5e-05 | +1.7e-04 | -6.7e-04 | +3.4e-04 | -6.8e-03 | 0 | - |
| gen | gen_method_original_lr1e-04_s0 | 1.2e-02 | 1.4e-03 | 0.4024 | 0.4015 | -9.2e-04 | -3.4e-03 | -6.2e-04 | +1.2e-03 | -4.1e-02 | 1 | below,no_cost |
| gen | gen_method_original_lr1e-04_s1 | 2.4e-02 | 1.5e-03 | 0.3665 | 0.3660 | -5.4e-04 | -2.6e-03 | +9.3e-04 | +5.0e-05 | -3.7e-02 | 0 | overall,below,at_or_above,no_cost |
| gen | gen_method_original_lr1e-04_s2 | 2.3e-02 | 2.1e-03 | 0.3497 | 0.3487 | -9.8e-04 | -2.8e-03 | -3.5e-04 | +1.9e-04 | -3.0e-02 | 0 | overall,below,at_or_above |
| gen | gen_neutral_lr1e-04_s0 | 5.8e-02 | 5.6e-03 | 0.6572 | 0.6608 | +3.5e-03 | +5.4e-03 | +3.6e-03 | +1.7e-03 | +5.9e-02 | 0 | overall,below,at_or_above,no_cost |
| gen | gen_neutral_lr1e-04_s1 | 5.8e-02 | 5.6e-03 | 0.6572 | 0.6608 | +3.5e-03 | +5.4e-03 | +3.6e-03 | +1.7e-03 | +5.9e-02 | 0 | overall,below,at_or_above,no_cost |
| gen | gen_neutral_lr1e-04_s2 | 5.8e-02 | 5.6e-03 | 0.6572 | 0.6608 | +3.5e-03 | +5.4e-03 | +3.6e-03 | +1.7e-03 | +5.9e-02 | 0 | overall,below,at_or_above,no_cost |
| gen | gen_rule_hard_lr1e-04_s0 | 2.3e-02 | 2.1e-03 | 0.3511 | 0.3508 | -2.2e-04 | +3.0e-04 | -1.1e-03 | +1.6e-04 | +2.0e-02 | 0 | below,at_or_above |
| gen | gen_rule_hard_n25_lr1e-04_s0 | 5.2e-02 | 4.2e-03 | 0.3426 | 0.3431 | +5.2e-04 | +4.6e-03 | -1.4e-03 | -1.6e-03 | +7.0e-02 | 2 | below,at_or_above,no_cost |
| gen | gen_shuffled_claude_lr1e-04_s0 | 1.5e-02 | 1.4e-03 | 0.6946 | 0.6954 | +8.6e-04 | +2.8e-03 | -1.6e-04 | -3.0e-05 | +1.2e-02 | 0 | below |
| gen | gen_teacher_lr1e-03_s0 | 5.8e-02 | 5.6e-03 | 0.6572 | 0.6608 | +3.5e-03 | +5.4e-03 | +3.6e-03 | +1.7e-03 | +5.9e-02 | 0 | overall,below,at_or_above,no_cost |
| gen | gen_teacher_lr1e-04_s0 | 1.7e-02 | 2.2e-03 | 0.3804 | 0.3792 | -1.2e-03 | -4.8e-03 | +1.2e-04 | +9.4e-04 | -1.7e-02 | 0 | overall,below,no_cost |
| gen | gen_teacher_lr1e-04_s1 | 1.9e-02 | 1.9e-03 | 0.3516 | 0.3517 | +4.4e-05 | -1.9e-04 | +1.6e-04 | +1.6e-04 | +7.5e-03 | 0 | below |
| gen | gen_teacher_lr1e-04_s2 | 2.8e-02 | 2.3e-03 | 0.3950 | 0.3943 | -7.4e-04 | -1.8e-03 | -8.7e-04 | +5.0e-04 | -1.8e-02 | 0 | overall,below,at_or_above,no_cost |
| gen | gen_teacher_lr3e-04_s0 | 7.0e-03 | 1.2e-03 | 0.3838 | 0.3837 | -1.1e-04 | -1.4e-03 | +4.9e-04 | +5.4e-04 | -7.8e-03 | 1 | below,at_or_above,no_cost |
| gen | gen_teacher_n25_lr1e-04_s0 | 2.7e-02 | 2.7e-03 | 0.3780 | 0.3773 | -6.6e-04 | +1.6e-03 | -3.9e-03 | +2.5e-04 | -3.6e-02 | 2 | overall,below,at_or_above |
| gen | gen_wrong_rule_lr1e-04_s0 | 2.2e-02 | 1.8e-03 | 0.5894 | 0.5891 | -2.6e-04 | -1.5e-03 | +9.4e-04 | -2.0e-04 | +1.2e-02 | 0 | below,at_or_above |
| orig | plain | 0.0e+00 | 0.0e+00 | 0.5767 | 0.5767 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | 0 | - |
| orig | answer_only_lr1e-04_s0 | 0.0e+00 | 0.0e+00 | 0.0015 | 0.0015 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | 0 | - |
| orig | answer_only_lr3e-04_s0 | 0.0e+00 | 0.0e+00 | 0.0002 | 0.0002 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | 0 | - |
| orig | method_lr1e-03_s0 | 0.0e+00 | 0.0e+00 | 0.4203 | 0.4203 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | 0 | - |
| orig | method_lr1e-04_s0 | 0.0e+00 | 0.0e+00 | 0.1551 | 0.1551 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | 0 | - |
| orig | method_lr1e-04_s1 | 0.0e+00 | 0.0e+00 | 0.2167 | 0.2167 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | 0 | - |
| orig | method_lr1e-04_s2 | 0.0e+00 | 0.0e+00 | 0.2095 | 0.2095 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | 0 | - |
| orig | method_lr3e-04_s0 | 0.0e+00 | 0.0e+00 | 0.2315 | 0.2315 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | 0 | - |
| orig | neutral_lr1e-03_s0 | 0.0e+00 | 0.0e+00 | 0.5767 | 0.5767 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | 0 | - |
| orig | neutral_lr1e-04_s0 | 0.0e+00 | 0.0e+00 | 0.5336 | 0.5336 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | 0 | - |
| orig | neutral_lr1e-04_s1 | 0.0e+00 | 0.0e+00 | 0.5274 | 0.5274 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | 0 | - |
| orig | neutral_lr1e-04_s2 | 0.0e+00 | 0.0e+00 | 0.5164 | 0.5164 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | 0 | - |
| orig | neutral_lr3e-04_s0 | 0.0e+00 | 0.0e+00 | 0.5767 | 0.5767 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | 0 | - |
| orig | shuffled0_lr1e-04_s0 | 0.0e+00 | 0.0e+00 | 0.5767 | 0.5767 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | 0 | - |
| orig | wrong_rule_lr1e-03_s0 | 0.0e+00 | 0.0e+00 | 0.4301 | 0.4301 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | 0 | - |
| orig | wrong_rule_lr1e-03_s1 | 0.0e+00 | 0.0e+00 | 0.3542 | 0.3542 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | 0 | - |
| orig | wrong_rule_lr1e-03_s2 | 0.0e+00 | 0.0e+00 | 0.4284 | 0.4284 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | 0 | - |
| orig | wrong_rule_lr1e-04_s0 | 0.0e+00 | 0.0e+00 | 0.4476 | 0.4476 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | 0 | - |
| orig | wrong_rule_lr3e-04_s0 | 0.0e+00 | 0.0e+00 | 0.4735 | 0.4735 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | 0 | - |

Seed-averaged arm means (as quoted in the reports), A10G → A40:

| Arm | A10G | A40 | Changes at 3 decimals |
| --- | --- | --- | --- |
| examples-100 (3 seeds) | 0.0321 | 0.0324 | no (0.032) |
| examples-50 | 0.0397 | 0.0399 | no (0.040) |
| examples-25 | 0.0416 | 0.0415 | no (0.042) |
| examples-10 | 0.0920 | 0.0910 | **yes: 0.092 → 0.091** |
| method_original (3 seeds) | 0.3729 | 0.3721 | **yes: 0.373 → 0.372** |
| teacher lr 1e-4 (3 seeds) | 0.3757 | 0.3751 | **yes: 0.376 → 0.375** |
| plain (= neutral, epoch 0) | 0.6572 | 0.6608 | **yes: 0.657 → 0.661** |

Reported comparisons (seed means where the reports use them; A10G gap → A40 gap; every sign is the same on both GPUs):

| Comparison | A10G | A40 |
| --- | --- | --- |
| examples-10 − examples-25 | +0.0504 | +0.0495 |
| examples-25 − examples-50 | **+0.0020** | **+0.0016** |
| examples-50 − examples-100 | +0.0076 | +0.0075 |
| examples-25 − examples-100 (the "within 0.05" claim) | +0.0096 | +0.0091 |
| rule-soft-25 − examples-25 | +0.3363 | +0.3358 |
| rule-soft-100 (teacher) − examples-100 | +0.3436 | +0.3427 |
| rule-hard-25 − rule-soft-25 | −0.0353 | −0.0342 |
| rule-hard-100 − rule-soft-100 (3-seed mean) | −0.0246 | −0.0242 |
| rule-soft-100 (teacher) − method_original | **+0.0028** | **+0.0030** |
| cheapest-25 − examples-25 | +0.3870 | +0.3871 |
| plain − rule-soft-100 | +0.2815 | +0.2857 |
| wrong_rule − rule-soft-100 | +0.2137 | +0.2141 |

The two bold gaps are about the size of the hardware shift. They were never resolved beyond hardware noise and seed spread: the examples-10 seeds alone run from 0.054 to 0.151, and the README already calls the curve flat from 25 to 100.

## Verdict (after gate G2: Sonnet and Opus, both "partly justified"; points applied below)

Rule: hardware-only if every arm's tune soft regret changes by < 0.005 coins **and** no reported number changes at its stated precision.

**Literal outcome: not hardware-only.** There are two separate findings.

1. **Cause:** consistent with GPU kernel selection by matrix size, with the code, model and library versions unchanged. Both GPUs are deterministic. The A40 kernel switch was seen between 601 and 603 tokens. The A10G side and its driver cannot be checked, so the cause is not fully identified.
2. **Effect:** below 0.005 coins overall in every arm (largest 0.00355), but not below 0.005 per type (0.0071 and 0.0054), and not bit-compatible at reported precision.

Details:

- The first condition **holds** for overall soft regret: the largest change is 0.00355. Per type, two values exceed 0.005 (−0.0071 and +0.0054).
- The second condition **fails**. What changes, at the 3-decimal precision of the reports:
  - plain gen tune soft regret 0.657 → 0.661 (`demo_out/gen_failure_map.md`, `demo_out/gen_curve_report.md`, README);
  - examples-10 0.092 → 0.091 (curve report, README);
  - method_original arm mean 0.373 → 0.372; teacher arm mean 0.376 → 0.375;
  - per-run or per-type 3-decimal values for 28 of 34 gen rows (list in `demo_out/hw_parity/summary.json`, `arms_with_3dp_flips`).
- Nothing on the original dataset changes.

In practice:

- **Do not mix A10G and A40 generated-dataset numbers** in one comparison. Rescore every comparator on the A40 when a new A40 number is compared with an old one.
- **No reported ordering or sign changes** (table above). Two gaps (examples-25 vs -50, teacher vs method_original) are about the size of the hardware shift and should be read as unresolved, as they already were given seed spread. Noise floor from this rescore: about ±0.004 overall per arm, ±0.007 per type, ±0.07 per cell.
- **The startup check cannot pass on the A40 at 1e-6 for gen adapters:** the teacher arm's largest difference over all 84 cases is 1.7e-2. Raising the tolerance would also pass arms that really differ. Both reviewers suggest instead keeping 1e-6 against per-GPU references (A40 references from `A40_probs.json`, which repeat across processes).

`FLOOR_ADAPTER_TOL` and `demo/floor.py` are **unchanged** (default 1e-6). Step 3 of the request applied only if the verdict was hardware-only, and its text was cut off ("set the demo default FLOOR_ADAPTER_TOL from th…"). The per-GPU reference fix is left for the owner (see DEMO_STATUS.md, open review points).
