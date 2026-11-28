# TARGETED_PLAN: does aiming extra examples at the model's failures beat the same number of random ones? (Qwen 2.5 7B first)

Status: **G1 done (Sonnet + Opus, both go-with-changes; changes applied, DECISIONS.md T1).** Predictions were committed alone first (TARGETED_PREDICTIONS.md, c1f1795). Nothing has been trained or scored for this plan. The training and look code is still to be written and tested on CPU (end of this file). The test3 look needs G3 and the owner's go.

## Why

On the one test2 look (QWEN_TEST2_RESULTS.md, LLAMA_TEST2_RESULTS.md), the adapters trained on 100 of Claude's worked examples keep their tune performance on fresh in-range cells, but they do worst on deals where the seller states no cost:
- no-cost soft regret 0.14 (Qwen) in range and 0.75 on new-key cells;
- every adapter fails the planted no-cost case.

The contribution tested here is a **failure-driven loop**: Claude reads where the trained model still loses money, on build cells only, and chooses where the next examples go. The comparisons are against the same number of random examples, and against random examples of the failing type. A win against both shows that aiming the data matters, not just how much of the failing type there is.

## Data (built, CPU only; demo/gen_test3.py, seed 20261203; tests/test_gen_test3.py)

Every cell poses a decision problem ((V, grid, stated cost) or (V, grid, cost range)) that occurs in no earlier cell (train, tune, test_same, test_hard, test2) and in no planted case. The original study's cell space (grid A, cost range 1-5, V 2-6) is excluded, as for test2. test3 and the pool share no problem. Resale values are 2-15, grids A-F, wordings 0-3 and the five cost ranges. All-tie cells are dropped. Buyer and seller names are built from name parts never used before. The fingerprints include a hash of every rendered prompt in all five orders and of the renderer files.

- **test3 (LOCKED):** 120 cells (60 no_cost, 30 below, 30 at_or_above), one per problem, V-balanced, two name variants (240 cases). No model has seen it.
- **pool (build):** every remaining problem, one cell each, name variant 0: 549 cells (199 no_cost, 329 below, 21 at_or_above).
- **probe (build, in the pool):** 90 cells (45 no_cost, 30 below, 15 at_or_above), V-balanced, for the failure map.
- **select3 (build, in the pool, not in the probe):** 30 cells (10 no_cost, 14 below, 6 at_or_above), V-balanced over 2-15 and grids A-F. This is the early-stopping set of the new arms, chosen because select_B covers only V 2-9 and grids A-C. It is never an extra training cell.

## Steps

1. **Failure map (GPU, about 0.25 h).** Score the three selected Qwen examples-100 adapters (A0; adapter hashes as frozen for test2) and plain Qwen on the 90 probe cells with the tune readout. Record per-cell soft regret, per seed and as the seed mean. These are run records on an unlocked build split `probe3`.
2. **Claude targets (no GPU).**
   - A fresh Claude instance with no project history gets only the failure table: probe cell features (type, V, grid, cost range or stated cost, line, wording), A0's per-seed and seed-mean regret, and the number of seeds with regret above 0.1. It gets nothing about test3 beyond "a held-out set exists", and no tune or test numbers.
   - It writes a targeting rule as a JSON filter with weights over cell features, plus two sentences of reasoning.
   - The rule, the prompt and the reply are committed verbatim before any draw. If fewer than 50 pool cells (outside select3) match, Claude gets one second attempt.
3. **Draws (no GPU; one draw per training seed, so the cell draw is a source of variance in the analysis).** For each seed s = 0, 1, 2, an arm takes 50 pool cells outside select3, one per problem:
   - **T_s (targeted):** sampled from the rule's weighted distribution with seed 100 + s;
   - **R_s (random):** uniform over the pool with seed 200 + s;
   - **N_s (no-cost random, V-balanced):** V-balanced draw of no-cost cells, like test3, with seed 300 + s. N controls for "more no-cost data" and for V coverage.

   The three fixed option orders of each extra cell are a seeded function of the cell alone (seed 20261204), so they are the same in every arm that uses the cell. Per-arm counts by type, V band (2-9, 10-15), grid and wording are reported.
4. **Labels (no GPU).**
   - The union of all drawn cells goes to a fresh Claude instance in one request. It uses the original worked-example packet format (demo/gen/examples_packet.md), with the cells shuffled and no arm membership shown. Its positions are the labels.
   - Before training, label agreement with the payoff-optimal offer under the lowest-price tie rule is computed by arm and type and reported. On the original 100 cells the agreement is 100%. Labels are used as given, because Claude is the teacher.
   - If an arm's no-cost agreement is 5 points or more below another arm's, an oracle-label run of that arm (seed 0) is added as a descriptive sensitivity check.
5. **Training (GPU, about 3.8 h).** Qwen is trained from scratch with the examples recipe (harness/train_lora.py: rank 4, lr 3e-4 as chosen for Qwen in QWEN_RESULTS.md, fp32 adapters, one optimizer step per case over three fixed orders).
   - Training set: the same 100 Claude-labelled cells plus the seed's 50 extra cells; 5 epochs = 750 optimizer steps (`--max-steps 750`).
   - Early stopping is scored on **select3**, with patience 2 and epoch 0 a candidate.
   - Arms T, R and N, seeds 0-2. A0 (the existing examples-100 adapters) is the reference and is not retrained; A0 comparisons are descriptive only (100 cells and 500 steps against 150 and 750).
   - **The selected adapter is primary.** The last-epoch adapter is scored descriptively.
   - A run that selects epoch 0 is included as is (it is plain Qwen). A run that diverges or crashes is included or reported as missing, never rerun or replaced.
   - The tune split is scored once per run.
6. **Development check (tune only; descriptive; cannot change the rules).** Per arm: tune soft regret overall and on no-cost cells, planted cases, letter mass, best epoch, the training-path and reload checks.
7. **G3, the owner's go, then the one test3 look** for every T, R and N adapter, A0, plain and the four model-free references. Preflight on tune as for test2 (scripts/test2_look.py generalised to `--split test3`). Then G2 on the result.

## Decision rules (fixed now)

**Statistics.**
- Arm values are per-case means over the three seeds. Name variants and orders are averaged inside each case, as for test2.
- Intervals come from a **two-level bootstrap**: resample the three seeds of each arm with replacement, then resample (V, grid) groups, both within the slice; PCG64 seed 0, 10,000 resamples.
- p-values come from a group sign-flip permutation test on the seed-mean differences (10,000 flips).
- Readout gate: a rule is "not concluded (readout)" if any adapter it uses has mean first-token letter mass below 0.90 on the cases the rule uses.

**H1 (primary, two parts, both required; test3 no-cost cases).** For each of T minus R and T minus N:
- the mean is below 0;
- the two-level 95% interval lies entirely below 0;
- the permutation p is below 0.05;
- **every seed's** T_s minus R_s (respectively N_s) mean is below 0.

**H2 (no harm; test3 below and at-or-above cases pooled).** The upper two-level 95% bound of T minus R is at most +0.10, and the same for T minus N. With 60 cells this check has low power: a pass rules out large harm only, and a fail means "harm not excluded".

**H3 (secondary).** T beats always-cheapest on test3 no-cost cells (by the same three pooled conditions). On no-cost cells the stated-cost rule is always-cheapest. The same check is reported for R, N and A0, so the result is read relative to them.

**Descriptive.**
- R minus A0 and T minus A0;
- per seed;
- per V band and grid;
- the stratum "(V, grid) of the test cell present among the arm's extra cells: yes / no";
- planted no-cost mass per adapter;
- last-epoch adapters;
- tune numbers.

All of these are published whatever the outcome.

**Wording.**
- **H1 both parts hold:** "examples aimed by Claude at the model's failures fix them better than the same number of random examples, and better than random examples of the failing type".
- **T beats R but not N:** "adding examples of the failing type helps; Claude's aiming was not shown to add to that".
- **Neither:** "aiming the extra examples was not shown to beat random ones".
- **H2:** "no large harm elsewhere" if it holds; "harm elsewhere not excluded" if it fails.
- "Not shown" means the frozen test did not establish it, not that it is absent.

## Guards against a misleading result

- **The targeting Claude sees only the probe failure table, not test3.** N controls for "more no-cost data" and for V coverage, because it is V-balanced like test3.
- **Equal set size and steps** (150 cells, 750 steps) for T, R and N. Orders are a function of the cell.
- **Labels:** one request, with arm membership hidden; accuracy by arm is reported before training.
- **Selection:** select3 matches test3's ranges and is the same set for every arm.
- **Probe cells may be in an arm's extras:** allowed, because they are build data. test3 shares no problem with the pool.
- **Single model:** Qwen first. Llama and Gemma repeat the same plan only if G2 on the Qwen result says it is worth it.

## Budget

About 4.5 GPU-hours on an A40, about $2.7:
- failure map 0.25 h;
- nine training runs at about 25 min each;
- a possible oracle-label sensitivity run;
- the look, 0.4 h.

Five seeds per arm, which both reviewers mentioned as an option, would add about 2.5 h. It is deferred: the per-seed direction condition and the two-level bootstrap carry the seed variance instead.

## Code to write before the GPU steps (CPU-tested)

- **Harness:** `test3` as a locked split, and `probe3` and `select3` as build splits, all with a fingerprint check and render equal to the generator. Pool cases need gen_test2's grid F and wording 3; the harness already renders them.
- **train_lora.py**, without weakening the existing pins:
  - `--extra-cells <file> --extra-labels <file> --select select3 --max-steps 750`;
  - the run id and solver name carry the arm and seed (`claude_examples_n150_T_s0` etc.), so arms never share a name and never pool;
  - the extra cells' pins are separate (cells, labels, orders sha256);
  - the extra cells must come from pool3 outside select3;
  - SCHEDULE gains 150 (epochs 1-5);
  - the existing 100-cell assertions are kept for the original cells;
  - lr is passed explicitly.
- **Scripts:** the failure-map script, the targeting prompt and draw script, the labelling-packet builder and label checker, and the test3 report (the rules above, the two-level bootstrap and the per-seed condition) with its tests on synthetic records.
- **Freeze file** for the look, as for test2: adapter hashes, extra-cell, label and order hashes, code hashes and package versions.
