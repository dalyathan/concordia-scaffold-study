# QWEN_TEST_PLAN: one look at test2 for Qwen 2.5 7B Instruct (DRAFT, not approved, nothing run)

Status: **draft for G3.** A test look needs (1) G3 with Sonnet + Opus (REVIEW_GATES.md), (2) the owner's explicit go in a message, and (3) the owner's scorer-pin tag (`HARNESS_PIN_REF`). None exists yet. No test case has been opened or scored for Qwen; the test2 cells are described only from their construction report (demo_out/gen_test2_report.md: CPU only, nothing scored). The harness reproduces the stored Gemma scores on the A40 (DECISIONS.md L39). If Llama is also looked at (LLAMA_TEST_PLAN.md), the two looks are planned and reviewed together at one G3, so the number of looks is known in advance.


## Prepared for G3 (2026-11-28)

- **Code items 1-3 written** (CPU tests pass): test2 as locked harness splits with a fingerprint check, and the test2 prompts equal the generator's render for all 480 cases x 5 orders (tests/harness/test_test2_port.py); the one-look guard keyed on (model, split, solver name, seed) as well as the config hash, the evaluation seed tied to the adapter's training seed, and the default runs folder always scanned (harness/evaluate.py, protected; DECISIONS.md X1-X2); the test2 report as its own generator, tools/test2_report.py, rather than a `--split` flag on tools/llama_report.py (it reuses that file's statistics; tested on synthetic records in tests/harness/test_test2_report.py).
- **Look driver:** scripts/test2_look.py (`--freeze`, `--dry`, `--look`). Added beyond the plan: a **preflight** per arm before any test case is scored, which re-scores the arm's 84 tune cases with the reloaded adapter and stops the look if any averaged probability differs from the committed tune record by 1e-3 or more. The adapters are reloaded with fp32 LoRA weights, as harness/train_lora.py reloads its best epoch.
- **Freeze list completed:** demo/gen/test2_freeze_<model>.json holds the six GPU arms (solver, seed, adapter directory, `adapter_model.safetensors` sha256, selected epoch), the tune record and its sha256 for each arm, the sha256 of the harness, driver, report, model YAML and test2 files, the bootstrap settings and the preflight tolerance. The look refuses to start if any of these changed or the git tree is not clean. The `solver_config_sha256` of each look solver needs the loaded model, so it is printed at the preflight, before the arm's first test case; the guard does not depend on it.
- **Test predictions:** TEST2_PREDICTIONS.md, committed alone before G3.
- **Still needed:** G3, then the owner's go and the scorer-pin tag (HARNESS_PIN_REF) created on or after the commit that registers the new harness/evaluate.py hash. If G3 changes any frozen file, the freeze is rewritten and committed before the look.

## Why test2, and what it can show

The tune result (QWEN_RESULTS.md, after G2) is in-family fit: examples-100 reaches 0.063 on tune cells that share values, grids and wording with the training cells (0.041 on tune cases whose decision tuple occurs in training, 0.081 on the others), with early stopping doing real work (one seed diverged after its selected epoch). The open questions are whether this holds on fresh cells from the same ranges (test2_same) and whether it carries outside the training key space (test2_newkey). Both sets were built with a fixed seed (20261201) and locked before any model was scored. test_same and test_hard are not used (Gemma already looked at them).

## What would be scored (frozen before the look)

One look per arm, each in its own process (one adapter per process), on both test2 splits, with exactly the tune configuration: **forced-choice letter after the "Answer: (" assistant prefix**, model pin `a09a35458c702b33eeacc393d103063234e8bc28`, sdpa, bf16, the same system sentence and few-shot turns, the two name variants stored in each test2 cell, five cyclic orders, A40.

| arm | solver | adapter (`adapter_model.safetensors` sha256) | why |
| --- | --- | --- | --- |
| plain | `plain` | none | the failure baseline |
| examples-100 seed 0 (selected, epoch 5) | `lora:claude_examples_n100_lr3e-04` | qwen25_7b_claude_examples_n100_lr3e-04_s0: 69b2bbd88d52dbb0d7be2f2b7b04a93460b324d171f92077f1af8d6dccc85991 | headline, 3-seed mean |
| examples-100 seed 1 (selected, epoch 3) | same | ..._s1: 330d7859aa78e772d23617037ef0b880dba5dc2845ab97e04cad81a89f1a8144 | headline |
| examples-100 seed 2 (selected, epoch 2; diverged later) | same | ..._s2: 7f5848fb2b7061ac1d6ccc5ee83addb7a23392836804d588fd20eff907f331cc | headline; reported per seed too |
| scrambled N=100 (selected) | `lora:shuffled_claude_n100_lr3e-04` | qwen25_7b_shuffled_claude_n100_lr3e-04_s0: 431e005fc83224df8a3452b4c6f3e6fecd66dcc250ef1f8deb68a5606c048709 | the informative control |
| cheapest-label N=100 (selected) | `lora:cheapest_label_n100_lr3e-04` | qwen25_7b_cheapest_label_n100_lr3e-04_s0: befb5bbaabd03ebf519bf449de68c222bacaa8bd608b44ba962164959581b059 | matched-N label control (weak: equals always-cheapest) |
| model-free references | `oracle`, `uniform`, `baseline:cheapest`, `baseline:stated_cost_rule` | none | CPU |

The selected adapters are used, never the `_last` ones, and nothing is retrained (G2: the selection by select_B with patience 2 and epoch 0 a candidate is part of the method; seed 2's `_last` adapter is at uniform). Not scored on test: the prompt arms (their tune gain is not shown to be content-specific; decoy texts were not run), examples-25 (one seed), the lr 1e-4 run, every `_last` adapter. Changing this list after G3 needs a new G3.

**Freeze list (completed and committed before G3; any change after the look invalidates it):**
- the adapter weight hashes above and the `solver_config_sha256` each solver produces (to be printed by a dry run that loads each solver on CPU-side config only, before G3);
- the git commit of the harness, the report generator's test section and the claims checker at G3; the protected scorer and payoff hashes registered in DECISIONS.md; the test2 fingerprints (demo/gen/test2_fingerprints.json);
- bootstrap: PCG64 seed 0, 10,000 resamples, clusters = (V, grid) groups within each slice (number of groups reported; slices without a type are reported as such); intervals exclude seed variance, so the per-seed values are always reported next to the seed mean;
- the planted rule below; the conclusion wording below.

## Code needed before the look (not written; G3 reviews it)

1. **Port test2 into the harness as locked splits.** `harness/tasks/haggling.py` has `locked_splits = ("test_same", "test_hard")`; test2_same and test2_newkey are not in it. Add both, loaded from demo/gen/test2_* with a fingerprint check; a unit test that `evaluate` refuses them without a lock token.
2. **One look per (model, split, arm), not per config hash.** `_prior_look` keys on the solver-config sha, so a changed config could take a second look; key it also on (model, split, solver name), and refuse any second look.
3. **Report section** for test2 (`tools/llama_report.py --model qwen25_7b --split test2_*`), written and frozen before the look, per slice.

## Primary analysis and decision rules (proposed; G3 may change them before the look, nobody after)

- **test2_same (within-distribution):** examples-100 3-seed mean soft regret, overall, by type, and stratified by label key seen / unseen in the 100 training cells. **T1** holds if the mean is at most 0.15, every seed is below plain, and the paired intervals of examples-100 minus plain and minus scrambled N=100 are below 0. Examples-100 minus the stated-cost rule is reported (marginal on tune), not part of T1.
- **test2_newkey (generalisation):** never one pooled number; each pre-declared slice reported (training ranges, new V only, new grid F, new wording 3, grid F plus wording 3, V 13-15). **T2** (primary slice: V 13-15, the clean extension) holds if the examples-100 mean is below plain and below the stated-cost rule with paired intervals below 0; the other slices are descriptive.
- **Planted cases:** the same four on every split, so the no-cost confidence shortfall seen on tune will recur. T1 and T2 are judged **without** the planted condition; planted results are reported per adapter as "top pick correct/incorrect, mass m".
- **Readout:** forced-choice letters throughout; the free-answer agreement on tune probe prompts (plain 0.53; adapters 0.89-0.95) travels with every number; no free-answer scoring on test unless added at G3.
- **Wording fixed now:** if T1 holds and T2 fails: "in-family fit replicates on fresh cells; no evidence of generalisation to new values". If both hold: "generalises to V 13-15 on the forced-choice readout". If T1 fails: "the tune result does not replicate on fresh in-family cells". Gemma and Llama numbers on test2, if any, are confounded description.
- **Test predictions** (ranges and probabilities for T1, T2 and the slice means) are committed in a separate file before the look.

## Process

1. Complete the freeze list (solver config hashes); write the port, the guard change and the report section; CPU tests pass; write the test predictions. Commit.
2. G3 (Sonnet + Opus) on this plan and that code, together with any other model's test plan; triage logged in DECISIONS.md.
3. The owner gives the go in a message and creates the scorer-pin tag; the lock token `G3-OWNER-GO:<date>` and `HARNESS_PIN_REF` are logged in DECISIONS.md.
4. One look: 2 splits x 240 cases x 6 GPU arms, about 0.5 GPU-h on the A40 (about $0.30). Then the report, CLAIMS.yaml, check_claims --strict and recompute, then G2 on the test result.
