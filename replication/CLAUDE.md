# Replicating "Claude as teacher" for small open-weight models: instructions for a Claude instance

You are a Claude instance asked to replicate, check or extend this study. Read this file first. It says what was claimed, which files are the results, how to rerun each step, and the rules that keep the replication honest. Run commands from the repository root (the folder above this one).

## The claim you are checking

Small open-weight models (Gemma 2 9B, Llama 3.1 8B, Qwen 2.5 7B) make a poor one-shot buying decision in a haggling game: pick one of five prices to offer a seller, given a resale value, the price scale, the range of farm costs and the seller's last line. The cost is the soft regret in coins against the exact best offer.

- **Teaching through the prompt helps, but not reliably for the right reason.** For Llama and Qwen a deliberately wrong rule helps about as much as Claude's paragraph (tune: Llama 0.61 against 0.77-0.93, Qwen 0.52 against 0.75-1.14). For Gemma the written rule helps more than the wrong rule (0.37 against 0.62).
- **Steering vectors fail.** Activation patching shows the decision is made late and differs from case to case.
- **Training works.** A rank-4 LoRA adapter trained on 100 of Claude's worked examples fixes the decision. Regret falls from 0.66 (Gemma), 1.18 (Llama) and 1.67 (Qwen) coins to 0.03-0.06 on tune cases, and stays near 0.06-0.07 on fresh held-out cases for Llama and Qwen.
- **The controls show the gain comes from Claude's correct answers.** Scrambled labels and always-cheapest labels do not produce it.
- **Remaining weak spot:** deals where the seller states no cost, especially at new resale values. There the adapters beat the untrained model but are not shown to beat a simple stated-cost rule.

The repository's own README, "The problem tree and what is solved", gives the current status of every claim with dates.

## What counts as a result (check these, not prose)

1. **Run records** (`runs/haggling/<model>/*.json`). One per (solver, split, seed). Each holds every case's inputs, per-order probabilities, payoffs and scores, the git commit, package versions, the GPU, the solver config with its hash, and the adapter's weight hash. Every number in a report comes from these.
2. **CLAIMS.yaml and `tools/check_claims.py --strict`.** These tie each number in the README and results files to the records it comes from. A hand-typed number fails the check.
3. **`tools/recompute.py runs/`.** An independent recompute from the raw per-case outputs, standard library only, with its own copy of the payoff rule. It must agree with every record.
4. **The protected scorer** (`harness/protected/`, plus `harness/evaluate.py`, `harness/task.py`, `tools/recompute.py`, `tools/check_claims.py`, `tools/lock_protected.py`). Their hashes are registered in DECISIONS.md and pinned by the owner's git tag `scorer-pin-1`. `python tools/lock_protected.py --pin scorer-pin-1` must print `PIN OK`.
5. **Locked test sets with fingerprints:**
   - `demo/gen/fingerprints*.json` (test_same, test_hard);
   - `demo/gen/test2_fingerprints.json` (test2_same, test2_newkey);
   - `demo/gen/test3_fingerprints.json` (test3, unused so far).

   The harness refuses a locked split without a lock token and the pin, and refuses a second look at the same (model, split, arm, seed).
6. **Pre-registration:**
   - `*_PREDICTIONS.md`, each committed alone before its plan and data;
   - `*_PLAN.md` and `*_TEST_PLAN.md`, with the decision rules and wording fixed before the results;
   - `reviews/`, blind reviews at each gate (REVIEW_GATES.md);
   - `DECISIONS.md`, every choice and deviation, including post-hoc ones, labelled as such.
7. **Generated results files:** QWEN_RESULTS.md, LLAMA_RESULTS.md, QWEN_TEST2_RESULTS.md and LLAMA_TEST2_RESULTS.md, written by `tools/llama_report.py` and `tools/test2_report.py` from records only. Run each with `--check` to see that it matches the records.
8. **Adapters:** `demo_out/adapters_harness/<model>_<arm>_n<N>_lr<lr>_s<seed>/`, backed up to the Hugging Face model repo `dalyathan/concordia-scaffold-artifacts` under `llama/` and `qwen/`. Every file's sha256 is in `llama_artifacts_manifest.json` and `qwen_artifacts_manifest.json`. (That repo is private; ask the owner for access or a public copy.)

A replication **succeeds** if your records reproduce these within the tolerance noted below, the controls behave the same way, and your conclusions follow the frozen wording. It **fails informatively** if you followed the frozen recipe and got something else: report that as a result.

## How Claude was used as the teacher

1. **Worked examples (the method that works).** Claude received `demo/gen/examples_packet.md`: the rules of the game in plain words and 100 cases, each with the resale value, the five listed prices, the price scale, the farm cost line and the seller's last line. Claude answered with one JSON object choosing an offer per case.
   - The reply is kept verbatim in `demo/gen/examples_reply.json`.
   - `demo/gen_examples_score.py check|freeze` scores it against the exact payoff rule and freezes `demo/gen/claude_labels.json` (sha256 pinned in `harness/train_lora.py`).
   - Claude's 100 choices equal the payoff-optimal offer, with the lowest price on ties, in 100 of 100 cases.
   - To redo this with your own Claude, give a fresh instance the same packet with no other context. Freeze its reply before training, and report any label that differs from the payoff rule rather than correcting it.
2. **Written lessons (control and comparison).** Claude's teacher paragraph is `demo/gen/teacher_reply.json`; the written-rule and wrong-rule texts are in `harness/lessons/`. They are scored as notes in the prompt (solver `notes:<name>`).
3. **Targeted examples (in progress).** Claude reads a failure table on build cells and picks extra training cells. See TARGETED_PLAN.md before running anything from it.

## Environment (what the published runs used)

- **GPU:** an NVIDIA A40 (48 GB) on RunPod with a 100 GB container disk. Llama and Qwen were run on the A40 only. Gemma's original results came from an A10G with the pre-refactor code, and the harness reproduces them on the A40 exactly after the float32 soft-cap fix (DECISIONS.md L38-L39). Per-case probabilities differ across GPU types by up to about 6e-2 (HARDWARE_PARITY.md on branch `demo`), so compare like with like, or compare means.
- **Python 3.11 venv with `requirements.gpu.lock`:**
  ```
  uv venv -p 3.11 .venv
  uv pip install --python .venv/bin/python --index-strategy unsafe-best-match \
    --extra-index-url https://download.pytorch.org/whl/cu121 -r requirements.gpu.lock
  ```
  Expect torch 2.4.1+cu121, transformers 4.44.2 and peft 0.12.0. Check that `peft` is in the lock on your branch; an older branch lacked it.
- **Concordia** cloned into `concordia/` at commit `3643ac0466f748b8055b61feb0b7908411f73d84`. Only one file's scene openings are read from it.
- **Model weights** come from the Hugging Face hub at the revisions pinned in `harness/models/<model>.yaml`. The loader refuses an unpinned revision. Llama needs its licence accepted on your account. Some pod images set `HF_HUB_ENABLE_HF_TRANSFER=1`; set it to 0 if `hf_transfer` is not installed.
- **Environment variables for GPU scripts:**
  ```
  CUBLAS_WORKSPACE_CONFIG=:4096:8 HARNESS_PROVIDER=<provider> HARNESS_GPU_USD_PER_HOUR=<rate> PYTHONPATH=concordia:.
  ```
- `scripts/pod_test2_look.sh` is a complete, tested example of a fresh-pod setup: pin check, venv, adapters restored from the hub with hash checks, then the look.

## Rerunning the study, in order

1. **CPU checks first:**
   ```
   python -m pytest -q tests/harness tests/test_gen_test2.py tests/test_gen_test3.py
   python tools/recompute.py runs/
   python tools/check_claims.py --strict
   python tools/lock_protected.py --pin scorer-pin-1
   ```
   All must pass before any GPU time.
2. **Model check (CPU, tokenizer only):** `python tools/model_checks.py --models <model>`. Each answer letter must be one token in context.
3. **Readout rule.** A model whose first assistant token is not a bare letter needs an assistant prefix. Qwen uses `"Answer: ("`, because its unprefixed first token merges "(" with the letter. The rule is fixed in the model's plan before data. Keep the config's `assistant_prefix` as committed.
4. **References and plain model (GPU):** `scripts/llama_step4.py --model <model>`, run on train and tune only. It stops if plain letter mass is below 0.9.
5. **LoRA arms (GPU):** `scripts/llama_step5.py --model <model>`, which runs `harness/train_lora.py` per arm:
   - rank 4, alpha 8, fp32 adapter weights, AdamW;
   - one optimizer step per case over three fixed orders;
   - lr chosen on select_B by the rule in code;
   - early stopping on select_B, patience 2, epoch 0 a candidate;
   - the tune split scored once with the selected adapter.

   The arms are examples-100 (3 seeds), examples-25, cheapest-label N=25 and N=100, and scrambled N=100.
6. **Report:** `python tools/llama_report.py --model <model>`, then `check_claims --strict` and `recompute`.
7. **Held-out look**, only after a blind G3 review and an explicit go from the project owner:
   ```
   HARNESS_PIN_REF=scorer-pin-1 python scripts/test2_look.py --model <model> --look --lock-token G3-OWNER-GO:<date>
   python tools/test2_report.py --model <model>
   ```
   Each adapter is re-scored on tune first and must reproduce its stored tune probabilities (max |dp| < 1e-3; the published looks gave exactly 0). Test2 for Llama and Qwen is already used; a new held-out set (test3) exists for new work.

Approximate cost on an A40 at $0.60/h:
- steps 4-6, about 3-3.5 GPU-hours per model;
- a test look, about 0.5 h per model.

## Numbers to compare against (soft regret in coins, forced-choice letter)

| | Gemma 2 9B | Llama 3.1 8B | Qwen 2.5 7B |
| --- | --- | --- | --- |
| plain, tune | 0.657 (A10G) / 0.661 (A40) | 1.184 | 1.666 |
| examples-100, tune, 3-seed mean | 0.032 | 0.048 | 0.063 |
| wrong rule in the prompt, tune | 0.618 | 0.611 | 0.515 |
| written rule (method paragraph), tune | 0.369 | 0.773 | 0.753 |
| examples-100, test2_same | - | 0.061 | 0.069 |
| stated-cost rule, test2_same | - | 0.174 | 0.174 |
| examples-100, test2_newkey V 13-15 | - | 0.81 | 0.81 |

Take the exact values and intervals from the generated results files, not from this table.

## Rules (the same rules the original work followed)

- **Predictions before plans, plans before data, data before runs.** Commit each prediction file alone.
- **Interventions are trained and tuned on train, select and tune cells only.** A test split is scored once, after a blind review and the owner's explicit go.
- **Never edit the protected scorer, the payoff rule or a test file.** Never hand-type a result number.
- **Never retrain, reseed or reselect after seeing test numbers.** Never rerun a failed or diverged run to get a better one; report it.
- **Separate what Claude chose from what code computed**, in every report.
- **Log every deviation** in DECISIONS.md, marked post-hoc when it is. Log every dead end in RESULTS_LEDGER.md.
- **Direct weight edits** follow WEIGHT_EDITING_RULES.md.
- **Reviews:** follow REVIEW_GATES.md, with blind reviewers who get only a packet folder.
