# QWEN_PLAN: Qwen 2.5 7B Instruct replication of the haggling study (branch `qwen`, written 2026-11-28 before any Qwen GPU run)

Model: `Qwen/Qwen2.5-7B-Instruct` at revision a09a3545 (harness/models/qwen25_7b.yaml; MODEL_CHECKS.md: PASS on 2026-11-28, single-token letters ids 64-68, real system role, no final logit soft-cap). Task: the generated haggling dataset (harness/tasks/haggling.py), five cyclic option orders, the stored name variants, first-token letter readout through the harness. Splits used: **train and tune only**, plus `select_B` (42 train cells outside the 100 training cells) for LoRA early stopping and the lr choice. test_same, test_hard, test2_same and test2_newkey are never opened. Predictions were committed alone before any Qwen code: QWEN_PREDICTIONS.md (commit 7e3d2f9).

**Code check.** The harness readout reproduces the stored Gemma scores on the A40 (per case <= 3.3e-16 after the soft-cap readout fix; DECISIONS.md L38-L39). Qwen has no final soft-cap, so it takes the unchanged readout path, the same one Llama used (Llama records bit-identical under the fixed code).

The plan is the Llama plan (LLAMA_PLAN.md, frozen there), with the same arms, recipe, rules and report, plus the changes listed at the end. Every analysis added at the Llama G2 review is part of the report from the start.

## Readout check (fixed in advance; owner instruction)

1. `scripts/llama_readout_probe.py --model qwen25_7b --split train_other` (20 train cases outside the 100 LoRA training cells and select_B, x 5 orders; mass only, no regret): mean letter mass on the five bare letters at the first assistant token, **without** an assistant prefix.
2. If that mass is >= 0.95: no prefix. If it is below 0.95: the assistant prefix **"Answer: ("** (the Llama one, the only candidate) is set in harness/models/qwen25_7b.yaml and the probe is rerun on the same train cases; mass >= 0.95 passes. If it is still below 0.95: **stop** before step 4 and report (no other framing is tried without a new G1).
3. The tune cells are not used to choose the framing. If a prefix is used, the model check is rerun with it (letters single tokens after the prefix).
4. **Free-answer agreement** (scripts/llama_freegen_check.py, model-agnostic): the greedy free answer without the prefix vs the forced letter's argmax, on the same 20 train cases; **descriptive only, no threshold**. Rerun with each examples-100 adapter after step 5.
5. Step 4 then also applies the Llama floor: R1 and R2 are concluded only if plain tune letter mass >= 0.9 (code stop below 0.9).

## Step 4: failure map and prompt arms (GPU, `scripts/llama_step4.py --model qwen25_7b`, train and tune)

References (oracle, uniform, always-cheapest, stated-cost rule; CPU, already on file for tune and train), plain, the four prompt arms as `notes` (written rule = method_original, Claude's lesson = teacher, same-length neutral text, wrong rule "Offer half the stated cost."), and, only if a prefix is used, `plain:noprefix` on train (sensitivity; feeds no rule). Texts byte-equal to the Gemma rows.

## Step 5: LoRA on Claude's worked examples (GPU, `harness/train_lora.py`, driver `scripts/llama_step5.py --model qwen25_7b`)

The Llama recipe unchanged: rank 4, alpha 8, dropout 0, q/k/v/o, fp32 adapter weights, AdamW, CE over the five letters' full-vocabulary log-probs at the first assistant token, one optimizer step per case (three fixed orders), at most 500 steps (N = 100: 5 epochs; N = 25: 20 epochs scored at 2, 4, 8, 12, 16, 20), early stopping on select_B (patience 2, epoch 0 a candidate), every arm also trained to the last epoch and scored unselected (`_last`), label sets sha-pinned, path check, epoch-0 check against the step-4 plain train record, reload check.

| run | N | seeds | lr |
| --- | --- | --- | --- |
| examples | 100 | 0 | 1e-4 and 3e-4 (sweep on select_B) |
| examples | 100 | 1, 2 | chosen |
| examples | 25 | 0 | chosen |
| cheapest-label | 25 and 100 | 0 | chosen |
| scrambled answers | 100 | 0 | chosen |

**lr rule (as for Llama):** the lr with the lower examples-100 seed-0 best select_B soft regret; within 0.005: 1e-4. No further lr is tried; an edge choice is reported as a limitation.

## Metrics and report (`tools/llama_report.py --model qwen25_7b`, generalised; QWEN_RESULTS.md)

Everything the Llama report gives (soft and hard regret per type, cluster-bootstrap intervals over (V, grid) groups, 10,000 resamples, PCG64 seed 0; slope of the offer on stated cost with 10,000 resamples; letter mass; top-letter share; planted cases with masses; per-seed values; GPU and USD per record, `_last` scoring counted once), plus from the start: plain minus uniform per type; each paragraph minus the wrong rule (paired interval, permutation p as (k+1)/(B+1)); the signed offer error per arm and type; regret on tune cases whose decision tuple is seen vs unseen among the 100 training cells; free-answer agreement before and after LoRA; a three-model table on the same tune cells: Gemma (imported stored records, A10G and A40 columns; the harness reproduces the A40 column) and Llama and Qwen (harness, A40), labelled confounded by model-specific framing.

## Decision rules (as frozen for Llama, with the Llama G2 wording)

- **R1** plain fails if plain tune soft regret >= 0.30, its paired interval against the stated-cost rule is above 0 and the below type is worst; **reported together with plain minus uniform**: if that interval includes 0 or plain is within 0.10 of uniform, the wording is "close to uniform guessing", not "fails like Gemma".
- **R2** a paragraph helps if (paragraph - plain) has interval below 0 and point <= -0.10, (paragraph - neutral) interval below 0, and arm mass >= 0.9. Controls inert if |neutral - plain| <= 0.10 and the wrong rule does not help. If the wrong rule helps as much as a paragraph (paragraph minus wrong rule interval includes 0 or is above 0), the results say the gain is not shown to come from the paragraph's content.
- **R3** worked examples train in on Qwen, on in-family cells, only if: examples-100 3-seed mean <= 0.15; every seed below plain; paired intervals of examples-100 minus plain, minus cheapest-label N = 100 and minus scrambled N = 100 below 0; each adapter's letter mass >= 0.97; each examples-100 adapter passes 4/4 planted. A planted failure is reported as "planted-X failed at mass m", R3 is also given without the planted condition (labelled secondary), and next to it the Gemma and Llama examples adapters' planted results on the same cases (both failed planted no-cost).
- **R4** cheapest-label N = 25 and N = 100 within 0.05 of always-cheapest; scrambled at least 0.15 worse than examples-100.
- **R5** examples-25 within 0.05 of the examples-100 mean (descriptive; one seed; the interval is reported).
- **Predictions** in QWEN_PREDICTIONS.md scored mechanically (HELD / FAILED / UNCLEAR / probability with a Brier term / not testable).
- **Stops (code):** plain tune mass < 0.9; oracle failing a planted case or always-cheapest passing planted-high; any trainer check failing; no new run once the Qwen records' GPU time reaches 5 h (budget 6 h).
- No conclusion before G2 (Sonnet + Opus).

## Changes from the Llama plan, with reasons

1. **Readout rule fixed in advance** (owner): format-only, mass >= 0.95 on train cases, "Answer: (" only if the unprefixed mass is below that; free-answer agreement descriptive. Reason: the Llama check was restated post hoc; fixing it before the data removes that forking path.
2. **Model-specific framing:** Qwen's chat template has a real system role (the same system sentence is passed; Qwen's default "You are Qwen..." system prompt is therefore not used) and no date header. sdpa attention, no soft-cap.
3. **Code:** the Llama scripts are generalised by a `--model` argument (step 4 already has one; step 5 driver, free-answer check and report gain one); outputs for Qwen go to QWEN_RESULTS.md and demo_out/qwen/. No change to the harness scorer, evaluator, task or trainer.
4. **Budget:** 6 GPU-h (owner), stop for new runs at 5 h.
5. **Not run** (as for Llama): steering, rule-trained students, N = 10 and 50, a second subset draw.

## Budget (estimates)

Readout probe and free-answer check: about 0.15 GPU-h; step 4 about 0.85 GPU-h; step 5: 8 runs at about 0.3 GPU-h; adapter free-answer checks about 0.15 GPU-h. Total about 3.6 GPU-h (about $2.20 at $0.60/h), cap 6 GPU-h.
