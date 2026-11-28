# LLAMA_TEST_PLAN: one look at test2 for Llama 3.1 8B (DRAFT, not approved, nothing run)

Status: **draft for G3.** A test look needs (1) G3 with Sonnet + Opus (REVIEW_GATES.md), (2) the owner's explicit go in a message, and (3) the owner's scorer-pin tag (`HARNESS_PIN_REF`). None exists yet. The parity check of the harness against stored Gemma scores was skipped by the owner, so every Gemma-vs-Llama number stays code-path-confounded, on test as on tune. No test case has been opened or scored for Llama. The test2 cells are described here only from their construction report (demo_out/gen_test2_report.md: CPU only, nothing scored).


## Prepared for G3 (2026-11-28)

- **Code items 1-3 written** (CPU tests pass): test2 as locked harness splits with a fingerprint check, and the test2 prompts equal the generator's render for all 480 cases x 5 orders (tests/harness/test_test2_port.py); the one-look guard keyed on (model, split, solver name, seed) as well as the config hash, the evaluation seed tied to the adapter's training seed, and the default runs folder always scanned (harness/evaluate.py, protected; DECISIONS.md X1-X2); the test2 report as its own generator, tools/test2_report.py, rather than a `--split` flag on tools/llama_report.py (it reuses that file's statistics; tested on synthetic records in tests/harness/test_test2_report.py).
- **Look driver:** scripts/test2_look.py (`--freeze`, `--dry`, `--look`). Added beyond the plan: a **preflight** per arm before any test case is scored, which re-scores the arm's 84 tune cases with the reloaded adapter and stops the look if any averaged probability differs from the committed tune record by 1e-3 or more. The adapters are reloaded with fp32 LoRA weights, as harness/train_lora.py reloads its best epoch.
- **Freeze list completed:** demo/gen/test2_freeze_<model>.json holds the six GPU arms (solver, seed, adapter directory, `adapter_model.safetensors` sha256, selected epoch), the tune record and its sha256 for each arm, the sha256 of the harness, driver, report, model YAML and test2 files, the bootstrap settings and the preflight tolerance. The look refuses to start if any of these changed or the git tree is not clean. The `solver_config_sha256` of each look solver needs the loaded model, so it is printed at the preflight, before the arm's first test case; the guard does not depend on it.
- **Test predictions:** TEST2_PREDICTIONS.md, committed alone before G3.
- **Still needed:** G3, then the owner's go and the scorer-pin tag (HARNESS_PIN_REF) created on or after the commit that registers the new harness/evaluate.py hash. If G3 changes any frozen file, the freeze is rewritten and committed before the look.

## Why test2, and what it can show

The tune result (LLAMA_RESULTS.md, after G2) is in-family fit: examples-100 reaches 0.048 soft regret on tune cells that share values, grids and wording with the training cells. The open questions are whether this holds on fresh cells from the same ranges (test2_same), and whether it carries to cells outside the training key space (test2_newkey). Both sets were built with a fixed seed (20261201) and locked before any model was scored. test_same and test_hard are not used: Gemma already looked at them.

## What would be scored (frozen before the look)

One look per arm, each a separate process (one adapter per process), on both test2 splits. Every arm uses the **forced-choice letter after "Answer: ("**, the model pin `0e9e39f249a16976918f6564b8830bc894c89659`, date_string "26 Jul 2024", sdpa, and the two name variants stored in each test2 cell (as for tune).

| arm | solver | adapter | why |
| --- | --- | --- | --- |
| plain | `plain` | none | the failure baseline |
| examples-100 seed 0, 1, 2 (selected) | `lora:claude_examples_n100_lr1e-04` | demo_out/adapters_harness/llama31_8b_claude_examples_n100_lr1e-04_s{0,1,2} | the headline; 3-seed mean of per-case soft regret |
| scrambled N=100 (selected) | `lora:shuffled_claude_n100_lr1e-04` | ..._shuffled_claude_n100_lr1e-04_s0 | the informative control |
| cheapest-label N=100 (selected) | `lora:cheapest_label_n100_lr1e-04` | ..._cheapest_label_n100_lr1e-04_s0 | matched-N label control (weak: it equals always-cheapest) |
| model-free references | `oracle`, `uniform`, `baseline:cheapest`, `baseline:stated_cost_rule` | none | CPU |

Not scored on test: the prompt arms (their tune result is not content-specific), examples-25 (one seed), the lr 3e-4 run, and every `_last` adapter. Changing this list after G3 needs a new G3.

**Freeze list (to be filled in and committed before G3; a change after the look invalidates it):**
- the sha256 of each adapter's `adapter_model.safetensors` (to be computed and pasted here) and the `solver_config_sha256` each solver produces;
- the sha256 of `tools/llama_report.py` (the test section), `harness/evaluate.py`, the protected scorer and payoff files (already registered in DECISIONS.md), and the test2 fingerprints (demo/gen/test2_fingerprints.json);
- the bootstrap seed (PCG64 0), 10,000 resamples, clusters = (V, grid) groups within each slice (the number of groups is reported per slice; some slices have none of a type);
- the planted rule (below).

## Code needed before the look (not written; G3 reviews it)

1. **Port test2 into the harness as locked splits.** `harness/tasks/haggling.py` has `locked_splits = ("test_same", "test_hard")`; test2_same and test2_newkey are not in it. Add both to `locked_splits` and load them from demo/gen/test2_*, with a fingerprint check against demo/gen/test2_fingerprints.json; add a unit test that `evaluate` refuses them without a lock token. The cells are loaded only inside the locked look.
2. **One look per adapter, not per config hash.** `_prior_look` keys on the solver-config sha, so a retrained adapter with a different hash would get a fresh look. Key it also on (model, split, arm, N, lr), so that any second Llama look at the same arm on the same split is refused, whatever the adapter.
3. **Report section** for test2 in `tools/llama_report.py`, written and frozen before the look, per slice as below.

## Primary analysis and decision rules (proposed; G3 may change them before the look, nobody after)

- **test2_same (within-distribution check):** examples-100 3-seed mean soft regret, reported overall and by type and stratified by label key seen / unseen in the 100 training cells. **T1** holds if the mean is at most 0.15, every seed is below plain, and the paired intervals of examples-100 minus plain, minus scrambled N=100 and minus the stated-cost rule are all below 0.
- **test2_newkey (generalisation):** never one pooled number. Report each pre-declared slice: training ranges, new V only, new grid F, new wording 3, grid F plus wording 3, V 13-15. **T2** (primary slice: V 13-15, the clean extension) holds if the examples-100 mean is below plain and below the stated-cost rule with paired intervals below 0. The other slices are descriptive.
- **Planted cases:** they are the same four on every split, so the no-cost failure seen on tune will recur. Decided now: T1 and T2 are judged **without** the planted condition, and the planted result is reported next to them per adapter ("planted-X failed at mass m"). The tune verdict R3 stays "not replicated" by its own frozen rule whatever test shows.
- **Readout limitation travels with every number:** forced-choice letters; the plain model's letter agrees with its free answer on about half the probe prompts, and the examples-100 adapters' on most (LLAMA_RESULTS.md).
- Gemma's numbers on test2, if any exist, are reported as confounded description only.

## Process

1. Fill in the freeze list; write the port and the report section; CPU tests pass. Commit.
2. G3 (Sonnet + Opus) on this plan and that code; triage and log it in DECISIONS.md.
3. The owner gives the go in a message and creates the scorer-pin tag; the lock token `G3-OWNER-GO:<date>` and `HARNESS_PIN_REF` are logged in DECISIONS.md.
4. One look: about 2 x 240 cases x 6 GPU arms, roughly 0.5 GPU-h on the A40 (about $0.30). Then the report, CLAIMS.yaml, check_claims --strict and recompute, then G2 on the test result.
