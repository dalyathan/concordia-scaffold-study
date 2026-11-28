# LLAMA_TEST_PLAN: one look at test2 for Llama 3.1 8B (frozen at G3; not run)

Status: **G3 done (Sonnet + Opus, go-with-changes; changes applied, DECISIONS.md X4).** A test look needs (1) G3 with Sonnet + Opus (REVIEW_GATES.md), (2) the owner's explicit go in a message, and (3) the owner's scorer-pin tag (`HARNESS_PIN_REF`). The owner's go and the pin tag do not exist yet. The harness reproduces the stored Gemma scores on the A40 after the soft-cap readout fix (DECISIONS.md L38-L39). No test case has been opened or scored for Llama. The test2 cells are described here only from their construction report (demo_out/gen_test2_report.md: CPU only, nothing scored).


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

## Code items (written before G3; see "Prepared for G3" above)

1. **Port test2 into the harness as locked splits.** `harness/tasks/haggling.py` has `locked_splits = ("test_same", "test_hard")`; test2_same and test2_newkey are not in it. Add both to `locked_splits` and load them from demo/gen/test2_*, with a fingerprint check against demo/gen/test2_fingerprints.json; add a unit test that `evaluate` refuses them without a lock token. The cells are loaded only inside the locked look.
2. **One look per adapter, not per config hash.** `_prior_look` keys on the solver-config sha, so a retrained adapter with a different hash would get a fresh look. Key it also on (model, split, arm, N, lr), so that any second Llama look at the same arm on the same split is refused, whatever the adapter.
3. **Report section** for test2 in `tools/llama_report.py`, written and frozen before the look, per slice as below.

## Decision rules (frozen at G3, 2026-11-28; identical for Llama and Qwen; implemented in tools/test2_report.py)

Each model gets its own verdict; the models are never pooled. "Fails" means the frozen test did not show the effect, not that it is absent.

- **Readout rule.** Every arm a rule uses (examples-100 seeds and plain; for T1 also scrambled N=100) must have mean first-token letter mass >= 0.90 on the cases the rule uses. Otherwise that rule is "not concluded (readout)". Mean and minimum mass are reported per arm, split and slice.
- **T1 (test2_same, within-distribution).** Holds if the examples-100 3-seed mean is at most 0.15, every seed's mean is below plain, and the paired 95% intervals of examples-100 minus plain and minus scrambled N=100 lie entirely below 0. Examples-100 minus the stated-cost rule is reported and is **not** part of T1, so T1 can hold with a mean above the rule. Reported beside it: by type, and stratified by label key seen / unseen in the 100 LoRA cells.
- **test2_newkey (generalisation).** Never one pooled number. Each pre-declared slice is reported (training ranges, new V only, new grid F, new wording 3, grid F plus wording 3, V 13-15), with the number of (V, grid) groups, per-seed means, both paired intervals and the group sign-flip permutation p.
- **T2a (V 13-15 slice, beats plain).** The examples-100 mean is below plain, the paired interval lies entirely below 0, and the permutation p is below 0.05.
- **T2b (V 13-15 slice, beats the stated-cost rule).** The same against the model-free stated-cost rule. On this slice the rule's regret comes only from the no-cost cells, so T2b is decided there. The slice is not a pure V extension: its at-or-above cells use grid F, and some cells carry the new wording. The report prints its composition (cells by type, grid F, wording 3) next to T2. With 12 groups the percentile intervals undercover; the permutation condition is there for that reason. Per-seed T2 checks are descriptive.
- **Planted cases:** reported per adapter (top pick correct or not, mass on the expected options); not part of any rule.
- **Readout limitation travels with every number:** forced-choice letters; the free-answer agreement on tune probe prompts is quoted in the report.
- **Wording** (two parts, fixed now):
  - **T1:** holds "in-family fit replicates on fresh cells"; fails "the tune result does not replicate on fresh in-family cells"; not concluded "in-family replication is not concluded".
  - **T2a and T2b both hold:** "on the V 13-15 cells (which also carry grid F or the new seller wording in part) the examples-100 adapters beat both plain and the model-free stated-cost rule".
  - **T2a only:** "on the V 13-15 cells they improve on plain but are not shown to beat the model-free stated-cost rule".
  - **T2b only:** "on the V 13-15 cells they beat the stated-cost rule but an improvement over plain is not shown".
  - **Neither:** "on the V 13-15 cells an improvement over plain is not shown".
  - **Not concluded:** "on the V 13-15 cells the comparison is not concluded".
- **Incomplete look and resume.** A frozen arm with no record makes the rules that need it "not concluded". After a crash, rerunning the look scores only (arm, split) pairs without a record; that is not a second look. A failed preflight stops the look and scores nothing for that arm.
- **Predictions** (TEST2_PREDICTIONS.md) are scored by the code in tools/test2_report.py. Each one is a yes/no event with its stated probability; a range prediction's event is "the point estimate lies in the range". The report lists the outcomes and the Brier score.
- Gemma numbers on test2, if any, come from a different scoring script and are description only.

## Process

1. Fill in the freeze list; write the port and the report section; CPU tests pass. Commit.
2. G3 (Sonnet + Opus) on this plan and that code; triage and log it in DECISIONS.md.
3. The owner gives the go in a message and creates the scorer-pin tag; the lock token `G3-OWNER-GO:<date>` and `HARNESS_PIN_REF` are logged in DECISIONS.md.
4. One look: about 2 x 240 cases x 6 GPU arms, roughly 0.5 GPU-h on the A40 (about $0.30). Then the report, CLAIMS.yaml, check_claims --strict and recompute, then G2 on the test result.
