# LLAMA_PLAN: Llama 3.1 8B replication of the Gemma haggling study (branch `llama`, written 2026-11-27 before any Llama GPU run)

Model: `meta-llama/Llama-3.1-8B-Instruct` at revision 0e9e39f2 (harness/models/llama31_8b.yaml, MODEL_CHECKS.md: PASS). Task: the generated haggling dataset (harness/tasks/haggling.py, byte-identical to demo/gen), five cyclic option orders, both name variants (never the name variants 1-14), first-token letter readout. Splits used: **train and tune only**, plus `select_B` (42 train cells outside the 100 training cells, name variant 0) for LoRA early stopping and the lr choice. test_same, test_hard, test2_same and test2_newkey are never opened. Predictions were committed before any Llama code: LLAMA_PREDICTIONS.md (copied unchanged from branch demo, sha256 49a30f9f...).

**Limitation stated in every results file: harness not yet checked against stored Gemma scores** (owner decision, DECISIONS.md L1). Gemma comparison numbers come from imported records of the pre-refactor code; Llama numbers from the harness solvers.

## Step 4: failure map and prompt arms (GPU, `scripts/llama_step4.py`)

| arm | solver | splits |
| --- | --- | --- |
| oracle, uniform, always-cheapest, stated-cost rule | CPU (`oracle`, `uniform`, `baseline` cheapest / stated_cost_rule) | train, tune |
| plain | `plain` | train, tune |
| written rule (our method paragraph) | `notes` harness/lessons/method_original.txt | train, tune |
| Claude's lesson (frozen teacher paragraph) | `notes` harness/lessons/teacher.txt | train, tune |
| same-length neutral text (control) | `notes` harness/lessons/neutral.txt | train, tune |
| wrong rule "Offer half the stated cost." (control) | `notes` harness/lessons/wrong_rule.txt | train, tune |

Texts are byte-equal to the Gemma text rows (tests/harness/test_lessons.py) and inserted at the same place (a `Notes:` block before the question; test_llama_additions.py compares with demo/gen_notes.render_notes). One seed (scoring is deterministic). The stated-cost rule is the cheapest listed price at or above a stated cost below resale, else the cheapest (tune: 0.214, always-cheapest 0.429, both reproduced by a CPU test).

## Step 5: LoRA on Claude's worked examples (GPU, `harness/train_lora.py`, tune only for the verdict)

Recipe = the Gemma generated-dataset recipe (demo/gen_lora.py, GEN_CURVE_PLAN.md): one-hot target on the letter showing Claude's labelled grid position; cross-entropy over the five letters' full-vocabulary log-probs at the first assistant token; LoRA rank 4, alpha 8, dropout 0, q/k/v/o, fp32 adapter weights, AdamW (wd 0); one optimizer step per case (three fixed orders accumulated); gradient checkpointing; at most 500 optimizer steps (N = 100: 5 epochs, scored every epoch; N = 25: 20 epochs, scored at epochs 2, 4, 8, 12, 16, 20); early stopping, patience 2 scorings, on `select_B` soft regret, with epoch 0 (= plain) a candidate; the 42 tune cells are scored once, with the best adapter, by `harness.evaluate` (protected scorer, planted cases) into a run record. Label sets are checked by sha256 against the ones the Gemma runs recorded.

| run | N cells | seeds | lr | purpose |
| --- | --- | --- | --- | --- |
| examples | 100 | 0 | 1e-4 and 3e-4 | lr sweep on select_B (the Gemma choice procedure) |
| examples | 100 | 1, 2 | chosen | 3 seeds at N = 100 |
| examples | 25 | 0 | chosen | one point on the curve (L4b, L4c partly) |
| cheapest-label control | 25 | 0 | chosen | "a student trained to answer cheap" (L4f; Gemma N = 25 and N = 100 records exist) |
| scrambled-answer control | 100 | 0 | chosen | Claude's labels permuted within case type (Gemma `shuffled_claude`, same labels) |

**lr choice (frozen):** the lr whose examples-100 seed-0 run has the lower best select_B soft regret; if the two are within 0.005, 1e-4 (the Gemma value). The un-chosen run's tune record is reported as the sweep, never as the headline.

## Metrics, per run and per case type (below / at_or_above / no_cost), from run records only (`tools/llama_report.py`)

- soft regret (headline; order-averaged probabilities), hard regret, per type;
- 95% intervals: cluster bootstrap over (V, grid) groups, 10,000 resamples, numpy PCG64 seed 0; paired differences resample the same groups for both arms;
- slope of the expected offer on the stated cost over the 14 below cells (least squares; bootstrap interval as above);
- first-token letter mass (unrenormalised) mean and minimum; harness floor 0.5;
- position bias: the largest entry of the mean letter-probability vector over all cases and orders (uniform 0.20);
- planted cases: n passed / 4 (reported in their own column, never in the mean);
- examples arms: 3-seed mean and every seed; best step, whether epoch 0 was kept; GPU seconds and approximate USD.

## Decision rules (frozen before the runs)

- **Stop rules.** Plain tune letter mass < 0.5 -> stop: the readout is wrong; fix it and re-gate (no number is interpreted). The oracle must pass 4/4 planted cases on every split (pipeline check) and always-cheapest must fail `planted-high` (negative control); otherwise stop. A trainer check failing (training path vs scoring path >= 1e-2 nats; epoch-0 select_B vs the plain train record >= 1e-3; reload >= 1e-3) stops the run. Cumulative GPU time >= 8 h stops new runs (budget 10 h).
- **R1 plain fails like Gemma** if plain tune soft regret >= 0.30, its paired 95% interval against the stated-cost rule is above 0, and the below type has the largest per-type regret. Otherwise "fails differently" (reported per type) or "does not fail" (soft regret < 0.30).
- **R2 a paragraph helps** if the paired interval of (paragraph - plain) is below 0 and the paired interval of (paragraph - neutral) is below 0. **Controls inert** if |neutral - plain| <= 0.10 and the wrong rule does not help (interval of wrong_rule - plain not below 0).
- **R3 worked examples train in on Llama** only if all hold: examples-100 3-seed mean <= 0.15; every seed below plain; paired intervals of (examples-100 seed-mean - X) below 0 for X = plain, cheapest-label, scrambled; mean letter mass of each adapter >= 0.97; each examples-100 adapter passes 4/4 planted. Any failure -> "not replicated", naming which condition failed.
- **R4 controls behave**: cheapest-label within 0.05 of always-cheapest (0.429); scrambled at least 0.15 worse than the examples-100 mean. If a control fails, R3 is reported but not called a replication.
- **R5 data size** (descriptive, one seed): examples-25 within 0.05 of the examples-100 mean or not.
- **Predictions** in LLAMA_PREDICTIONS.md are scored mechanically as written there (HELD / FAILED / UNCLEAR when the interval straddles an edge), and as **not testable** when this plan does not run the arm (steering L3, rule-trained students L4e, N = 10 and 50 in L4b/L4c/L4d).
- No conclusion is written before G2 (Sonnet + Opus).

## Changes from the Gemma recipe, with reasons

1. **Code path.** Harness solvers (`harness/solvers/hf.py`: first token only, no prompt trimming, PEFT on the shared model) instead of `refimpl.local_gemma2`. Reason: the owner's instruction to run through the harness. Risk: unknown readout difference; the parity check is skipped by owner decision, so Gemma-vs-Llama differences may include it.
2. **Chat framing.** The same system sentence and two few-shot turns, but Llama gets a real system message (its template supports one) where Gemma's template folds it into the first user turn; Llama's template also always adds "Cutting Knowledge Date: December 2023 / Today Date: 26 Jul 2024" to the system header. date_string is fixed so prompts never change by day.
3. **Attention and logits.** sdpa attention, no logit soft-capping (Gemma needed eager attention and soft-capping). Reason: model architecture.
4. **Hardware.** RunPod A40 (Gemma's runs: AWS A10G; an A40 rescore of the Gemma adapters and plain exists and is shown next to the A10G numbers where available; the Gemma prompt rows exist only on the A10G).
5. **Epoch-0 check.** Gemma checked epoch-0 selection scores against its stored plain file; Llama checks them against the step-4 plain train record.
6. **Not run:** the train-side monitor sample (never used for selection), steering, rule-trained students, N = 10 and 50, a second subset draw. Reason: the owner's step list and the budget.
7. **Cheapest-label control at N = 25** (the prediction L4f is stated at N = 25); the scrambled control at N = 100 (Gemma's only scrambled run).

## Budget (estimates; actuals per run in the records and LLAMA_RESULTS.md)

Step 4: about 17,000 forward passes, est. 0.5-0.8 GPU-h. Step 5: 7 training runs, est. 15-30 min each on the A40 (Gemma: about 37 min each on the A10G), 2-3.5 GPU-h. Total est. 3-4.5 GPU-h (about $2-3), cap 10 GPU-h.
