# GEN_PLAN.md — LoRA arms on the generated dataset (written before training)

## Question
Can a method paragraph written by Claude from Gemma's own failures (the "teacher method", frozen in demo/gen/teacher_method.txt, sha256 d4010305b297188598d0fb87186ed8fdb2ef0c98446dec70240a7f74f46c3499) be distilled into rank-4 LoRA weights so that plain-prompt Gemma 2 9B-it makes better offers on unseen generated cells? Evidence comes from the TUNE cells only; test_same and test_hard are not touched, and nothing here is a test result.

## Data (all from demo/gen/, CPU-generated; only train and tune cells are read)
- Training set: 100 of the 300 train cells (34 below-resale, 33 at-or-above, 33 no-cost; demo/gen/lora_train_cells.json), one fixed name variant per cell, three fixed option orders per case = 300 examples per arm. Reduced from the 300 cells for the 8-hour budget (a pass costs about 1 s; the full set would take about 1 hour per epoch).
- Tune set (42 cells x 2 name variants, five orders): early stopping uses the 42 variant-0 cases; at the best epoch all 84 cases are scored and saved. Selection is on tune, so tune numbers are selected-on.
- Reference rows on tune (no training): plain, the teacher text in the prompt, the original method text in the prompt, neutral text, wrong rule (step B), always-cheapest and the stated-cost rule (computed from labels).

## Arms (five; targets over the five option letters)
1. **teacher-distil:** the model's own first-token letter distribution with the teacher paragraph as the Notes block, computed before training.
2. **our-method-distil:** same with the earlier method paragraph (textrows.METHOD). 3. **neutral-distil:** same with 150 tokens of market-scene text. 4. **wrong-rule-distil:** same with "Offer half the stated cost."
5. **answer-trained ceiling:** uniform over the letters of the case's best offers (supervised, not a method).
Training uses the full-vocabulary letter loss (cross-entropy of the answer letter against the target using the letters' full-vocabulary log-probs, so letter mass is protected), rank 4, alpha 8, q/k/v/o, fp32 adapter weights, AdamW, one optimizer step per case, gradient checkpointing, at most 5 epochs, early stopping on tune (patience 2). Same code path for all arms (demo/gen_lora.py).

## Seeds and learning rate
lr grid {1e-4, 3e-4, 1e-3} at seed 0 chosen on tune by lowest monitor soft regret (ties to the lower lr); 3 seeds per arm at the chosen lr, subject to the budget ladder below. Every arm is compared at its own chosen lr when it has a grid, else at the teacher's chosen lr.

## Budget: 8 GPU-hours (est. 0.6 h per run: 4.5 epochs x about 400 s plus 360 s load, targets and evaluation; re-measured by the chain)
Ladder, first plan that fits (demo/gen_chain.py --plan): L0 full 23 runs (13.8 h); L1 controls and ceiling at the teacher's lr only 17 runs (10.2 h); L2 also our-method at the teacher's lr only 15 runs (9.0 h); **L3 neutral and wrong-rule get 2 seeds instead of 3: 13 runs (7.8 h)** <- chosen at the placeholder epoch time; L4 our-method 2 seeds. Order: teacher grid; seed 0 of the other arms; teacher seeds 1-2; our-method seeds; control seeds. The grid for controls was dropped first, as instructed (logged).

## Pass rule (on TUNE cells, frozen now)
Per-cell tune soft regret (mean of the two name variants, then mean over an arm's seeds). Teacher-distil PASSES if its mean over cells is below plain, neutral-distil and wrong-rule-distil and, for each of the three, the lower 95% bound of the paired cell bootstrap of (control - teacher) (10,000 resamples, seed 0, 42 cells) is above 0, with letter mass at least 0.9 x plain. Reported alongside (not part of the rule): teacher vs our-method-distil; all arms against always-cheapest and the stated-cost rule; the answer-trained ceiling; by case type (below / at-or-above / no-cost); slope of the expected offer on the stated cost (below cells); train-sample regret; per-seed values; the in-prompt teacher text as the upper reference. The same rule must also be met by seeds 1-2 only (seed 0 chose the lr) before any claim of a pass is written. A pass on tune is not a test result; the test look is a separate plan (GEN_TEST_PLAN.md).

## Safety
Epoch 0 scoring is asserted to equal the saved plain scores on the tune monitor cases (1e-3); adapter-off scoring equality and adapter reload were verified earlier by demo/lora_checks.py on the same PEFT path (not re-verified for this dataset: noted). Adapters are gitignored; hashes are recorded in the run JSONs (committed after every run). Old adapters are not used; test cells are not read. Gates: G1 (Sonnet + Opus, over 3 GPU-hours) on this plan; G2 (Sonnet + Opus) before any verdict.
