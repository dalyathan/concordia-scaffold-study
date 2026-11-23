# Results ledger

Rebuilt by `python demo/ledger.py` from saved results (do not edit by hand). Soft regret is in coins: the mean over cells of each case's soft regret, using first-token probabilities averaged over the five option orders. Intervals are 95% cell-bootstrap intervals where per-case results were saved. Rungs: 1 plain readout, 2 model-free baselines, 3 text in the prompt, 4 steering vectors, 5 LoRA adapters. In-sample = the setting was chosen or fitted on the cases it is scored on.

| # | Beat | Rung | Method | Split | In-sample | Soft regret [95% CI] | Change vs plain | Matched control | Control regret | Beats control? | Wall time | Verdict | Source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | failure-is-real | 1 | plain Gemma 2 9B, no notes | all 140 | no | 0.618 [0.41, 0.82] | +0.000 | — | — | n/a | 3 min | fails in 55% of cases; ignores stated cost | `demo_out/cases.jsonl` |
| 2 | failure-is-real | 1 | plain Gemma 2 9B, no notes | build | no | 0.699 [0.39, 1.03] | +0.000 | — | — | n/a | — | the reference row for this split | `demo_out/cases.jsonl` |
| 3 | failure-is-real | 1 | plain Gemma 2 9B, no notes | tuning | no | 0.714 [0.43, 1.01] | +0.000 | — | — | n/a | — | the reference row for this split | `demo_out/cases.jsonl` |
| 4 | failure-is-real | 1 | plain Gemma 2 9B, no notes | test | no | 0.534 [0.27, 0.84] | +0.000 | — | — | n/a | — | the reference row for this split | `demo_out/cases.jsonl` |
| 5 | failure-is-real | 1 | plain, reworded scaffold (same facts) | all 140 | no | 0.642 [0.44, 0.85] | +0.024 | plain, original wording | 0.618 | no | — | failure survives rewording; half the picks change | `demo_out/reworded_cases.jsonl` |
| 6 | failure-is-real | 1 | greedy free-text answer (hard regret) | all 140 | no | 0.540 [0.30, 0.79] | -0.081 | first-token top offer (hard regret) | 0.621 | yes | 2 min | free text agrees with first token 54%; similar regret | `demo_out/say.jsonl` |
| 7 | one-sentence | 2 | constant shift (tilt, beta -0.85) | tuning | yes | 0.669 | -0.046 | plain | 0.714 | yes | — | small gain; no model knowledge needed | `demo/baselines.json` |
| 8 | one-sentence | 2 | always offer 1 (attractor, lam 1) | tuning | no | 0.635 | -0.079 | plain | 0.714 | yes | — | beats plain Gemma without any model | `demo/baselines.json` |
| 9 | one-sentence | 2 | always offer 2 (attractor, lam 1) | tuning | yes | 0.529 | -0.185 | plain | 0.714 | yes | — | beats plain Gemma without any model | `demo/baselines.json` |
| 10 | one-sentence | 2 | always offer 3 (attractor, lam 1) | tuning | no | 0.694 | -0.020 | plain | 0.714 | yes | — | beats plain Gemma without any model | `demo/baselines.json` |
| 11 | one-sentence | 2 | always offer 4 (attractor, lam 1) | tuning | no | 1.306 | +0.591 | plain | 0.714 | no | — | worse than plain | `demo/baselines.json` |
| 12 | one-sentence | 2 | always offer 5 (attractor, lam 1) | tuning | no | 2.306 | +1.591 | plain | 0.714 | no | — | worse than plain | `demo/baselines.json` |
| 13 | one-sentence | 2 | shrink to the middle (flatten, lam 0.00) | tuning | yes | 0.714 | +0.000 | plain | 0.714 | no | — | never helps; best lam is zero | `demo/baselines.json` |
| 14 | one-sentence | 3 | method paragraph (no numbers) | tuning | no | 0.303 [0.11, 0.56] | -0.411 | neutral | 0.688 | yes | 1 min | cuts regret 58%; content, not length, helps | `demo_out/text_rows_tuning.jsonl` |
| 15 | one-sentence | 3 | same-length neutral text | tuning | no | 0.688 [0.40, 1.00] | -0.026 | plain | 0.714 | yes | 1 min | length alone does nothing | `demo_out/text_rows_tuning.jsonl` |
| 16 | one-sentence | 3 | wrong rule: offer half the stated cost | tuning | no | 0.688 [0.35, 1.10] | -0.026 | neutral | 0.688 | no | 1 min | no better than neutral text | `demo_out/text_rows_tuning.jsonl` |
| 17 | one-sentence | 3 | disposition: only your own profit matters | tuning | no | 0.747 [0.44, 1.08] | +0.033 | neutral | 0.688 | no | 1 min | slightly worse than plain | `demo_out/text_rows_tuning.jsonl` |
| 18 | one-sentence | 3 | acceptance rule restated | tuning | no | 0.702 [0.43, 0.99] | -0.013 | neutral | 0.688 | no | 1 min | restating the rule alone does nothing | `demo_out/text_rows_tuning.jsonl` |
| 19 | one-sentence | 3 | template reasoning naming the best offer | tuning | no | 0.001 [0.00, 0.00] | -0.714 | answer-only | 0.013 | yes | 1 min | names the answer; near-zero regret (leaky) | `demo_out/text_rows_tuning.jsonl` |
| 20 | one-sentence | 3 | answer only (UPPER BOUND) | tuning | no | 0.013 [0.00, 0.04] | -0.702 | plain | 0.714 | yes | 1 min | upper bound: text naming the answer | `demo_out/text_rows_tuning.jsonl` |
| 21 | inside-the-model | 4 | tune job v1: alpha x raw vector (mis-scaled) | tuning | yes | — | — | random directions (matched) | — | n/a | 9 min | dead end: unequal norms; stopped before any result | `logs/demo_tune_job_v1.log` |
| 22 | inside-the-model | 4 | tune job v2: template, best of 10 points (fractions 0.02-0.20) | tuning | yes | 0.714 [0.43, 1.01] | -0.001 | random directions (matched) | — | n/a | 10 min | dead end: sanity check showed under 0.01-coin moves | `demo_out/tune_partial_v2.jsonl` |
| 23 | inside-the-model | 4 | sanity: offer_lower, layer 18, fractions 0.10/0.20 | tuning (4 cases) | no | — | — | its negation | — | n/a | — | right sign, but moves offers at most 0.007 coins | `demo_out/tune_sanity.json` |
| 24 | inside-the-model | 4 | dose scan: offer_lower, P1 on, best coherent setting (L24, f 0.25) | tuning (8 cases) | yes | 0.826 | -0.014 | plain (8 cases) | 0.839 | yes | 3 min | moves offer -0.049 coins; negligible | `demo_out/dose_scan.json` |
| 25 | inside-the-model | 4 | dose scan: offer_lower, P3 on, best coherent setting | tuning (8 cases) | yes | — | — | plain (8 cases) | 0.839 | n/a | 3 min | no coherent setting: letter mass collapses | `demo_out/dose_scan.json` |
| 26 | inside-the-model | 4 | dose scan: cheap, P1 on, best coherent setting (L24, f 0.1) | tuning (8 cases) | yes | 0.823 | -0.016 | plain (8 cases) | 0.839 | yes | 3 min | moves offer -0.037 coins; negligible | `demo_out/dose_scan.json` |
| 27 | inside-the-model | 4 | dose scan: cheap, P3 on, best coherent setting | tuning (8 cases) | yes | — | — | plain (8 cases) | 0.839 | n/a | 3 min | no coherent setting: letter mass collapses | `demo_out/dose_scan.json` |
| 28 | inside-the-model | 4 | dose scan: sentence, P1 on, best coherent setting (L24, f 0.1) | tuning (8 cases) | yes | 0.838 | -0.002 | plain (8 cases) | 0.839 | yes | 3 min | moves offer -0.005 coins; negligible | `demo_out/dose_scan.json` |
| 29 | inside-the-model | 4 | dose scan: sentence, P3 on, best coherent setting (L24, f 0.25) | tuning (8 cases) | yes | 0.831 | -0.009 | plain (8 cases) | 0.839 | yes | 3 min | moves offer -0.071 coins; negligible | `demo_out/dose_scan.json` |
| 30 | inside-the-model | 4 | tune job v3 (PAUSED, partial): template, full budget, best point so far | tuning | yes | 0.712 [0.43, 1.01] | -0.003 | plain | 0.714 | yes | — | partial result; job paused (resume later) | `demo_out/tune_partial.jsonl` |
| 31 | inside-the-model | 4 | steering check a: per-order cheap, best coherent (L39, f 1.0) | held-out tune cases (12) | yes | 0.407 | -0.166 | best constant shift (fit on train cells) | 0.508 | yes | 44 min | letter push: order-specific; not better than always-2 | `demo_out/steer_checks.json` |
| 32 | inside-the-model | 4 | steering check b: order-averaged cheap, best coherent (L27, f 0.25) | held-out tune cases (12) | yes | 0.560 | -0.013 | 3 random directions (same setting) | 0.578 | yes | — | moves offer -0.20 coins; negligible | `demo_out/steer_checks.json` |
| 33 | inside-the-model | 4 | steering check b: order-averaged sentence, best coherent (L33, f 1.0) | held-out tune cases (12) | yes | 0.606 | +0.032 | 3 random directions (same setting) | 0.579 | no | — | moves offer -0.07 coins; negligible | `demo_out/steer_checks.json` |
| 34 | inside-the-model | 4 | patch method-text P1 residual into plain at layer 33 (diagnostic) | held-out tune cases (12) | yes | 0.341 | -0.233 | method text in the prompt | 0.184 | no | — | diagnostic: shows where the text's effect arrives | `demo_out/steer_checks.json` |
| 35 | inside-the-model | 4 | patch method-text P1 residual into plain at layer 39 (diagnostic) | held-out tune cases (12) | yes | 0.203 | -0.370 | method text in the prompt | 0.184 | no | — | diagnostic: shows where the text's effect arrives | `demo_out/steer_checks.json` |
| 36 | inside-the-model | 4 | per-order sentence vector (method - neutral), L36, f 1.0 | held-out tune cases (12) | yes | 0.427 | -0.146 | wrong-order vector, same setting | 1.279 | yes | 20 min | letter push, like per-order cheap | `demo_out/steer_followup.json` |
| 37 | inside-the-model | 5 | LoRA answer_only, lr 1e-04, seed 0 | held-out tune cells (6) | yes | 0.002 [0.00, 0.00] | -0.575 | shuffled arm (same lr, seed) | 0.577 | yes | 47 min | best epoch 8; beats plain | `demo_out/lora/answer_only_lr1e-04_s0.json` |
| 38 | inside-the-model | 5 | LoRA answer_only, lr 3e-04, seed 0 | held-out tune cells (6) | yes | 0.000 [0.00, 0.00] | -0.577 | plain (held-out cells) | 0.577 | yes | 47 min | best epoch 7; beats plain | `demo_out/lora/answer_only_lr3e-04_s0.json` |
| 39 | inside-the-model | 5 | LoRA method, lr 1e-03, seed 0 | held-out tune cells (6) | yes | 0.420 [0.16, 0.70] | -0.156 | neutral-distil (same lr, seed) | 0.577 | yes | 37 min | best epoch 4; beats plain | `demo_out/lora/method_lr1e-03_s0.json` |
| 40 | inside-the-model | 5 | LoRA method, lr 1e-04, seed 0 | held-out tune cells (6) | yes | 0.155 [0.07, 0.26] | -0.422 | neutral-distil (same lr, seed) | 0.534 | yes | 26 min | best epoch 2; beats plain | `demo_out/lora/method_lr1e-04_s0.json` |
| 41 | inside-the-model | 5 | LoRA method, lr 1e-04, seed 1 | held-out tune cells (6) | yes | 0.217 [0.09, 0.41] | -0.360 | neutral-distil (same lr, seed) | 0.527 | yes | 24 min | best epoch 2; beats plain | `demo_out/lora/method_lr1e-04_s1.json` |
| 42 | inside-the-model | 5 | LoRA method, lr 1e-04, seed 2 | held-out tune cells (6) | yes | 0.210 [0.07, 0.42] | -0.367 | neutral-distil (same lr, seed) | 0.516 | yes | 35 min | best epoch 4; beats plain | `demo_out/lora/method_lr1e-04_s2.json` |
| 43 | inside-the-model | 5 | LoRA method, lr 3e-04, seed 0 | held-out tune cells (6) | yes | 0.231 [0.10, 0.43] | -0.345 | neutral-distil (same lr, seed) | 0.577 | yes | 30 min | best epoch 3; beats plain | `demo_out/lora/method_lr3e-04_s0.json` |
| 44 | inside-the-model | 5 | LoRA neutral, lr 1e-03, seed 0 | held-out tune cells (6) | yes | 0.577 [0.20, 0.96] | +0.000 | plain (held-out cells) | 0.577 | no | 13 min | best epoch 0; no clear gain over plain | `demo_out/lora/neutral_lr1e-03_s0.json` |
| 45 | inside-the-model | 5 | LoRA neutral, lr 1e-04, seed 0 | held-out tune cells (6) | yes | 0.534 [0.17, 0.91] | -0.043 | plain (held-out cells) | 0.577 | yes | 21 min | best epoch 1; no clear gain over plain | `demo_out/lora/neutral_lr1e-04_s0.json` |
| 46 | inside-the-model | 5 | LoRA neutral, lr 1e-04, seed 1 | held-out tune cells (6) | yes | 0.527 [0.16, 0.91] | -0.049 | plain (held-out cells) | 0.577 | yes | 29 min | best epoch 3; no clear gain over plain | `demo_out/lora/neutral_lr1e-04_s1.json` |
| 47 | inside-the-model | 5 | LoRA neutral, lr 1e-04, seed 2 | held-out tune cells (6) | yes | 0.516 [0.17, 0.88] | -0.060 | plain (held-out cells) | 0.577 | yes | 29 min | best epoch 3; beats plain | `demo_out/lora/neutral_lr1e-04_s2.json` |
| 48 | inside-the-model | 5 | LoRA neutral, lr 3e-04, seed 0 | held-out tune cells (6) | yes | 0.577 [0.20, 0.96] | +0.000 | plain (held-out cells) | 0.577 | no | 13 min | best epoch 0; no clear gain over plain | `demo_out/lora/neutral_lr3e-04_s0.json` |
| 49 | inside-the-model | 5 | LoRA shuffled0, lr 1e-04, seed 0 | held-out tune cells (6) | yes | 0.577 [0.20, 0.96] | +0.000 | plain (held-out cells) | 0.577 | no | 13 min | best epoch 0; no clear gain over plain | `demo_out/lora/shuffled0_lr1e-04_s0.json` |
| 50 | inside-the-model | 5 | LoRA wrong_rule, lr 1e-03, seed 0 | held-out tune cells (6) | yes | 0.430 [0.10, 0.76] | -0.147 | plain (held-out cells) | 0.577 | yes | 42 min | best epoch 5; beats plain | `demo_out/lora/wrong_rule_lr1e-03_s0.json` |
| 51 | inside-the-model | 5 | LoRA wrong_rule, lr 1e-03, seed 1 | held-out tune cells (6) | yes | 0.354 [0.04, 0.67] | -0.223 | plain (held-out cells) | 0.577 | yes | 42 min | best epoch 5; beats plain | `demo_out/lora/wrong_rule_lr1e-03_s1.json` |
| 52 | inside-the-model | 5 | LoRA wrong_rule, lr 1e-03, seed 2 | held-out tune cells (6) | yes | 0.428 [0.08, 0.77] | -0.148 | plain (held-out cells) | 0.577 | yes | 24 min | best epoch 2; beats plain | `demo_out/lora/wrong_rule_lr1e-03_s2.json` |
| 53 | inside-the-model | 5 | LoRA wrong_rule, lr 1e-04, seed 0 | held-out tune cells (6) | yes | 0.448 [0.12, 0.78] | -0.129 | plain (held-out cells) | 0.577 | yes | 26 min | best epoch 2; beats plain | `demo_out/lora/wrong_rule_lr1e-04_s0.json` |
| 54 | inside-the-model | 5 | LoRA wrong_rule, lr 3e-04, seed 0 | held-out tune cells (6) | yes | 0.473 [0.14, 0.80] | -0.103 | plain (held-out cells) | 0.577 | yes | 46 min | best epoch 6; beats plain | `demo_out/lora/wrong_rule_lr3e-04_s0.json` |
| 55 | inside-the-model | 5 | LoRA answer_only, renormalised-only loss, lr 3e-4 (stopped after 1 epoch) | held-out tune cells (6) | yes | 0.204 | -0.373 | plain (held-out cells) | 0.577 | yes | 7 min | dead end: letter mass collapsed to 0.01 | `logs/demo_lora_answer_only_renorm_loss_dead_end.log` |
| 56 | inside-the-model | 5 | generated-data LoRA answer_only, lr 3e-04, seed 0 | tune cells (42, generated) | yes | 0.118 | -0.539 | plain (tune cells) | 0.657 | yes | 38 min | beats plain on tune | `demo_out/gen_lora/gen_answer_only_lr3e-04_s0.json` |
| 57 | inside-the-model | 5 | generated-data LoRA teacher, lr 1e-03, seed 0 | tune cells (42, generated) | yes | 0.657 | +0.000 | plain (tune cells) | 0.657 | no | 20 min | no improvement (epoch 0) | `demo_out/gen_lora/gen_teacher_lr1e-03_s0.json` |
| 58 | inside-the-model | 5 | generated-data LoRA teacher, lr 1e-04, seed 0 | tune cells (42, generated) | yes | 0.380 | -0.277 | plain (tune cells) | 0.657 | yes | 40 min | beats plain on tune | `demo_out/gen_lora/gen_teacher_lr1e-04_s0.json` |
| 59 | inside-the-model | 5 | generated-data LoRA teacher, lr 3e-04, seed 0 | tune cells (42, generated) | yes | 0.384 | -0.273 | plain (tune cells) | 0.657 | yes | 40 min | beats plain on tune | `demo_out/gen_lora/gen_teacher_lr3e-04_s0.json` |
| 60 | inside-the-model | 5 | LoRA method distillation, 3 seeds, TEST LOOK (72 cases, 18 test cells) | test cells (18) | no | 0.263 | -0.271 | wrong-rule distil (3 seeds) | 0.482 | yes | — | test label: SUPPORT | `demo_out/test_look.json` |
| 61 | take-home | 0 | steercheck toy problem (a vector that should work) | toy (40 cases) | yes | 0.066 [0.04, 0.08] | -0.734 | its negation | 0.800 | yes | — | steercheck detects a working vector and its controls | `demo/steercheck.py` |

## Three best methods (tuning split; excluding rows that name the answer)

1. method paragraph (no numbers): soft regret 0.303 (-0.411 vs plain).
2. always offer 2 (attractor, lam 1): soft regret 0.529 (-0.185 vs plain).
3. always offer 1 (attractor, lam 1): soft regret 0.635 (-0.079 vs plain).

## Three that failed

1. tune job v1: alpha x raw vector (mis-scaled): dead end: unequal norms; stopped before any result.
2. tune job v2: template, best of 10 points (fractions 0.02-0.20): dead end: sanity check showed under 0.01-coin moves.
3. dose scan: cheap, P1 on, best coherent setting (L24, f 0.1): moves offer -0.037 coins; negligible.

## Slow runs (over 30 minutes) that gave no signal

- none so far.

## Row notes

- Row 6: hard regret, not soft
- Row 19: names the best offer
- Row 20: names the best offer
- Row 21: wall time from DEMO_STATUS (killed after about 9 minutes)
- Row 22: best point ['template', 'full', 9, 0.05]; wall time from DEMO_STATUS (killed after about 10 minutes)
- Row 23: change in expected offer only
- Row 24: no per-case results saved: no interval
- Row 25: no per-case results saved: no interval
- Row 26: no per-case results saved: no interval
- Row 27: no per-case results saved: no interval
- Row 28: no per-case results saved: no interval
- Row 29: no per-case results saved: no interval
- Row 30: 21 grid points done; best so far ['template', 'full', 18, 0.25]; coherence not applied
- Row 31: always-2 scores 0.333 on these cases; negation raises the offer; random directions do nothing; no interval (12 cases = 6 cells)
- Row 32: order-averaged mean-difference vector at P1; no interval (12 cases = 6 cells)
- Row 33: order-averaged mean-difference vector at P1; no interval (12 cases = 6 cells)
- Row 34: uses the evaluated cases' own method-text run; not a deployable method; no interval (12 cases = 6 cells)
- Row 35: uses the evaluated cases' own method-text run; not a deployable method; no interval (12 cases = 6 cells)
- Row 36: no interval (12 cases = 6 cells)
- Row 37: train-cell soft regret 0.001; selected-on the held-out cells
- Row 38: train-cell soft regret 0.000; selected-on the held-out cells
- Row 39: train-cell soft regret 0.720; selected-on the held-out cells
- Row 40: train-cell soft regret 0.363; selected-on the held-out cells
- Row 41: train-cell soft regret 0.451; selected-on the held-out cells
- Row 42: train-cell soft regret 0.394; selected-on the held-out cells
- Row 43: train-cell soft regret 0.414; selected-on the held-out cells
- Row 44: train-cell soft regret 0.778; selected-on the held-out cells
- Row 45: train-cell soft regret 0.740; selected-on the held-out cells
- Row 46: train-cell soft regret 0.767; selected-on the held-out cells
- Row 47: train-cell soft regret 0.775; selected-on the held-out cells
- Row 48: train-cell soft regret 0.778; selected-on the held-out cells
- Row 49: train-cell soft regret 0.778; selected-on the held-out cells
- Row 50: train-cell soft regret 0.754; selected-on the held-out cells
- Row 51: train-cell soft regret 0.656; selected-on the held-out cells
- Row 52: train-cell soft regret 0.733; selected-on the held-out cells
- Row 53: train-cell soft regret 0.816; selected-on the held-out cells
- Row 54: train-cell soft regret 0.815; selected-on the held-out cells
- Row 55: regret looks good only because it is read after renormalising over a collapsed 1% of the mass; replaced by the full-vocabulary letter loss
- Row 56: best epoch 4; selection-set soft regret 0.120
- Row 57: best epoch 0; selection-set soft regret 0.584
- Row 58: best epoch 4; selection-set soft regret 0.360
- Row 59: best epoch 3; selection-set soft regret 0.375
- Row 60: frozen development verdict: NOT PASSED. Control minus method, paired cell bootstrap: plain +0.271 [+0.054, +0.514]; neutral +0.286 [+0.064, +0.536]; wrong-rule +0.219 [+0.048, +0.399]; always-2 +0.115 [-0.066, +0.317] (always-2 0.378); free-text hard regret worse: plain 0.439, method 0.736
- Row 61: toy regret is on the toy's own scale
