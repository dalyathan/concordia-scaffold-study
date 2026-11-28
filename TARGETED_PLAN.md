# TARGETED_PLAN: does aiming extra examples at the model's failures beat the same number of random ones? (Qwen 2.5 7B first; DRAFT for G1)

Predictions were committed alone first (TARGETED_PREDICTIONS.md, c1f1795). Nothing has been trained or scored for this plan.

## Why

On the one test2 look (QWEN_TEST2_RESULTS.md, LLAMA_TEST2_RESULTS.md), the adapters trained on 100 of Claude's worked examples keep their tune performance on fresh in-range cells, but they do worst on deals where the seller states no cost:
- no-cost soft regret 0.14 (Qwen) on in-range cells and 0.75 on the new-key cells;
- every adapter fails the planted no-cost case;
- on V 13-15 they are not shown to beat the model-free stated-cost rule, whose regret there comes only from no-cost cells.

The new contribution would be a **failure-driven loop**: Claude reads where the trained model still loses money (on build cells only) and chooses where the next examples go. The test is against the same number of randomly chosen examples, so a win shows that aiming the data matters, not just having more of it.

## Data (built, CPU only; demo/gen_test3.py, seed 20261203; tests/test_gen_test3.py)

Every cell poses a decision problem ((V, grid, stated cost) or (V, grid, cost range)) that occurs in no earlier cell (train, tune, test_same, test_hard, test2), and test3 and the pool share none. Resale values are 2-15, grids A-F, wordings 0-3 and the five cost ranges. All-tie cells are dropped. Buyer and seller names are new.

- **test3 (LOCKED):** 120 cells (60 no_cost, 30 below, 30 at_or_above), one per problem, V-balanced, two name variants (240 cases). The fingerprints are in demo/gen/test3_fingerprints.json. No model has seen it. It enters the harness as a locked split (fingerprint check, lock token, owner pin, one look per arm) by the same code path as test2.
- **pool (build):** every remaining problem, one cell each, name variant 0: 552 cells (202 no_cost, 329 below, 21 at_or_above). The extra training cells come from here.
- **probe (build, part of the pool):** 90 cells (45 no_cost, 30 below, 15 at_or_above), V-balanced, for the failure map.

## Steps

1. **Failure map (GPU, about 0.25 h).** Score the three selected Qwen examples-100 adapters (A0, frozen hashes as in demo/gen/test2_freeze_qwen25_7b.json) and plain Qwen on the 90 probe cells with the tune readout. Record per-cell soft regret, seed mean and per seed, as run records on a new unlocked split `probe3`.
2. **Claude targets (no GPU).**
   - A fresh Claude instance with no project history gets only the failure table: probe cell features (type, V, grid, cost range or stated cost, line, wording) and the A0 seed-mean regret. It gets nothing about test3 beyond "a held-out set exists", and no tune or test numbers.
   - It writes a targeting rule as a JSON filter with weights over cell features, plus two sentences of reasoning.
   - A script draws **50 pool cells** from the cells that match, one per problem, proportional to the weights (seed 1, PCG64).
   - If fewer than 50 match, Claude gets one second attempt. The rule and the drawn cells are committed before any training.
3. **Labels for the extra cells (no GPU).**
   - The cells of every arm are put to a fresh Claude instance in the same worked-example packet format as the original 100 (demo/gen/examples_packet.md), and its chosen positions are the labels. On the original 100, Claude's labels equal the payoff-optimal offer with the lowest-price tie rule in 100 of 100 cells.
   - Any new label that differs from that is reported and kept. Claude is the teacher.
   - All arms use labels from the same request, so the arms differ only in which cells were chosen.
4. **Training (GPU, about 3.7 h).** All arms are trained from scratch on Qwen with the frozen examples recipe (harness/train_lora.py: rank 4, lr 3e-4, fp32 adapters, one optimizer step per case over three fixed orders, select_B early stopping with patience 2 and epoch 0 a candidate). The training set is the same 100 Claude-labelled cells plus 50 extra cells, so every arm runs 5 epochs = 750 steps. Three seeds per arm:
   - **T (targeted):** the 50 cells Claude's rule picked;
   - **R (random):** 50 pool cells drawn uniformly at random, one per problem (seed 2), with no failure information;
   - **N (no-cost random):** 50 pool no-cost cells drawn uniformly at random (seed 3). This separates Claude's targeting from simply "more no-cost data";
   - **A0:** the existing examples-100 adapters, not retrained (the reference).

   The tune split is scored once per run, as before, with the selected and the last-epoch adapter.
5. **Development check (tune only, before G3).**
   - Per-arm tune soft regret overall and on no-cost cells.
   - Planted cases.
   - Letter mass.
   - The training-path and reload checks of train_lora.

   These numbers are descriptive and cannot change the rules below.
6. **G3, the owner's go, then the one look at test3** for T, R, N, A0, plain and the four model-free references, with a preflight on tune exactly as for test2 (scripts/test2_look.py generalised to `--split test3`). After that, G2 on the result.

## Decision rules (fixed now; per-case seed means; 95% cluster bootstrap over (V, grid) groups, PCG64 seed 0, 10,000 resamples; group sign-flip permutation p, 10,000 flips)

- **Readout rule:** every arm a rule uses must have mean letter mass >= 0.90 on the cases it uses; otherwise that rule is "not concluded (readout)".
- **H1 (primary; targeting beats random):** on the test3 no-cost cases, T minus R has a mean below 0, a 95% interval entirely below 0 and a permutation p below 0.05.
- **H2 (no harm):** on the test3 below and at-or-above cases, the upper 95% bound of T minus R is at most +0.05.
- **H3 (secondary; beats the rule):** on test3 no-cost cases, T minus the stated-cost rule has a mean below 0, an interval below 0 and p < 0.05.
- **H4 (secondary; Claude's targeting beyond "more no-cost data"):** H1's three conditions for T minus N on the no-cost cases.
- **Descriptive:**
  - R minus A0 and T minus A0;
  - per seed;
  - per V band (2-9, 10-15) and grid;
  - planted no-cost mass per adapter;
  - tune numbers.
- **Wording:**
  - H1 holds: "examples aimed by Claude at the model's failures fix them better than the same number of random examples".
  - H1 holds and H4 fails: add "but no better than more examples of the failing type".
  - H1 fails: "aiming the extra examples was not shown to beat random ones".
  - "Not shown" means the frozen test did not establish it, not that it is absent.
  - If H2 fails, the wording says the targeted arm got worse elsewhere.

## What could make a result misleading, and the guard

- **Claude knows the test is no-cost heavy.** The targeting Claude sees only the probe failure table, not test3. The failure map, not the test, decides where the examples go. N controls for "the test is no-cost heavy, so add no-cost examples".
- **Arm size and steps:** equal (150 cells, 750 steps) for T, R and N.
- **Label noise between arms:** one labelling request covers every arm's cells.
- **Selection on select_B (in-range cells) may favour R:** the rule is the same for every arm and frozen.
- **Probe cells may be in T's training set:** allowed, because they are build data. test3 shares no problem with the pool.
- **Single model:** Qwen first. Llama and Gemma repeat the same plan only if G2 on the Qwen result says it is worth it.

## Budget

About 4.3 GPU-hours on an A40 (failure map 0.25 h, nine training runs at about 25 min each, look 0.4 h), about $2.6. That is over 3 GPU-hours, so G1 uses Sonnet and Opus.

## Code still to write (CPU, before the GPU steps; reviewed at G1 as described, checked by tests)

- **Harness:** test3 as a locked split and `probe3` / `pool3` as build splits (fingerprint check, render equals the generator).
- **train_lora.py:** `--extra-cells <file> --extra-labels <file>` (pinned sha256, extra cells must come from pool3, total 150).
- **Scripts:** the failure-map script, the targeting draw script, the labelling-packet script and the test3 report (rules above). scripts/test2_look.py generalised to test3.
