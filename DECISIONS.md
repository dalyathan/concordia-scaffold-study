# DECISIONS (refactor branch)

Every choice made without asking, newest last. Protected scorer hashes are listed in the section at the end.

## Protected scorer registrations
Initial registration (refactor, 2026-11-23): scorer and payoff rules ported verbatim from demo/gen_cases.py payoff(); new generic regret code.

PROTECTED harness/protected/__init__.py sha256 e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
PROTECTED harness/protected/payoffs/__init__.py sha256 e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
PROTECTED harness/protected/payoffs/haggling.py sha256 a0423b3a0a2908c6494e8e2e1f2c55e35c6c17eb934122f06cf7455bc95a13e2
PROTECTED harness/protected/payoffs/parity.py sha256 1f1ea76ad4f5744a4b5d5b9adbc74c7bf99eb31e4bc7f9d518936062a6cb3f21
PROTECTED harness/protected/scorer.py sha256 3b6141e7cd16ed0c4cab1c058653427f673ecdfbc9fb9436716e4ebb16084265


## Choices (refactor, 2026-11-23)

1. **New package, no edits to the old code.** Everything is under `harness/` and `tools/`; `demo/`, `refimpl/` and `tests/*.py` are untouched. The
   learning-curve job on the GPU imports them and `demo/gen/test_look_lock.json` fingerprints them, so editing them would invalidate that record.
   Cost: the old scripts still contain Gemma names; migration is by the new package, not by rewriting the old one.
2. **Config format YAML, one file per model** (`harness/models/*.yaml`), loaded by `harness/modelspec.py`. Layer count, hidden size, dtype and
   attention mode were typed from the published model cards (not verified for the gated repos, see MODEL_CHECKS.md).
3. **Answer-letter token ids are never typed.** They stay `null` until `tools/model_checks.py --write` reads them from the tokenizer, in the rendered
   prompt context (the first token of the assistant turn, after the rendered prompt), which is what the readout uses. A solver refuses to load a model with `null` ids.
4. **Gated models are NOT CHECKED.** No `HF_TOKEN` is available and licences (Gemma, Llama, Mistral) are the owner's to accept. A tokenizer read from a
   third-party mirror was considered and rejected as a workaround of the gate. The tool reports them as NOT CHECKED, never as passing.
5. **Network.** I asked the environment tool to allow huggingface.co and arxiv.org (the Default environment's allowlist was empty); that was needed for
   parts 3 and 14 and is the only environment change I made.
6. **Protected scorer = `harness/protected/` (generic regret) + `harness/protected/payoffs/<task>.py` (payoff rules).** Authority is DECISIONS.md:
   a line `PROTECTED <path> sha256 <hash>` must exist for every file's current hash (editing `LOCK.json` alone does not help; it is only a convenience copy).
   Adding a task therefore needs a DECISIONS entry for its payoff file, on purpose.
7. **Haggling payoffs ported verbatim** from `demo/gen_cases.py`. The Concordia opening texts are read from the pinned clone by AST instead of importing
   Concordia (its imports need packages not installed here); output is byte-identical (cells.json, cases.jsonl, fingerprints.json).
   `fingerprints_v2.json` embeds hashes of the old generator files, so it is not reproduced by design (test skipped, reason in the test).
8. **test2_same / test2_newkey not ported.** Their generator monkeypatches `demo/gen_cases.py`; porting it would duplicate 320 lines for locked sets that are
   not to be re-evaluated. Left in `demo/`; listed in REFACTOR_STATUS.md.
9. **Legacy results are imported, not re-run** (`tools/import_legacy.py`): per-case probabilities in `demo_out/` become run records labelled `legacy:<arm>`
   with source-file hashes. No locked split is newly evaluated; the test-set files imported are the already-looked results. They have no planted cases, no GPU time.
10. **Readout of the new HF solvers equals the old one in design** (first-token letter probabilities, renormalised, five cyclic orders, same chat framing),
    but it has not been run. Until a GPU parity check passes (REFACTOR_STATUS.md, item 1) the new solvers must not be used for headline numbers.
11. **Cost** is `gpu_seconds x $HARNESS_GPU_USD_PER_HOUR`; nothing assumes AWS. Provider is read from `HARNESS_PROVIDER`.
12. **Hand-typed number audit** covers README "Results at a glance" (scanned by the checker) and was spot-checked for the History section; see REFACTOR_STATUS.md.
13. **No G1 gate run.** This step runs no GPU job and no new method on data; reviews are by the tests listed in REFACTOR_STATUS.md. A G2-style blind review of
    the claims machinery is listed as the owner's next step because a review costs tokens and the instruction file asks for G2 only before a conclusion.

## Blind review triage (G2, 2026-11-23; reviews/2026-11-23_G2_refactor_{sonnet,opus}.md)

Both reviewers: **partly justified** (no no-go). Applied = fixed on this branch; Deferred = listed in REFACTOR_STATUS.md; Rejected = with reason.

| # | Point (raised by) | Action |
| --- | --- | --- |
| Locked guard is a string; "once" not enforced; unrecorded looks; no token in record (both) | **Applied**: locked splits force `write=True`, store the token, refuse a repeat look with the same solver config (hash of `describe()`), unknown split name is an error. **Deferred**: owner-written ledger of looks, token as HMAC over case-set hash, check against frozen fingerprints (needs an owner process) |
| test_same / test_hard already seen; no fresh locked split (both) | **Deferred to owner**: a new single look needs a fresh set or an explicit re-look statement. test2 sets exist but are not ported/imported |
| Planted cases weak (both) | **Applied**: new `planted-high` case (answer 5 coins; "always offer 2" fails it); a planted case passes only with >= 0.9 probability on the acceptable options, so ties no longer pass (uniform fails 4 of 4). **Deferred**: move `planted_expected` into protected code; separate pipeline check vs model sanity |
| `check_claims.run_mean` ignores task/model/config (both) | **Applied**: evidence needs task, model, solver, split and recomputes from payoffs and probs (stored scores not trusted); optional `n_records`. **Deferred**: record paths with sha256, config-hash filter; `make_report` still groups by solver without config |
| Claim checker gaps (both) | **Applied**: decimals derived from the shown string; every number in a claim's text must be listed; regex (not substring) matching; `file_value` evidence is sha256-pinned; bare-number ignore list replaced by context patterns; a test pins the unbacked set at exactly the known five. **Deferred**: scanning the problem tree and History; numbers written as words; `--strict` cannot pass until the five are backed |
| Recompute weak (both) | **Applied**: checks probs = mean of per_order_probs, length mismatch, hard regret, by_type, duplicate ids; a pytest runs it over `runs/`. **Deferred**: store raw letter probabilities and the letter map so option-order handling can be recomputed; frozen case-id hash and expected counts |
| Scorer lock is self-attested (both) | **Deferred to owner**: pin hashes in an owner-held file or CI; add evaluate.py to the protected set; newest-hash-only rule. Review `git log -p harness/protected DECISIONS.md` at each gate |
| Model misconfiguration (both) | **Applied**: `Backend` refuses ids not verified by the tokenizer check and an unpinned revision (override `HARNESS_ALLOW_UNPINNED=1`, recorded); letter-mass floor 0.5 recorded as `letter_mass.ok`; LoRA solver no longer leaks the adapter into other solvers on the same backend (`disable_adapter`); steering vector shape and layer asserted. **Deferred**: revision values per config; Llama date string; >5 options; re-deriving ids at load |
| Letter-id check measures first reply token, not the token after "(" (Sonnet) | **Checked, confirmed in design**: the readout is the first token of the assistant turn (as in the old code), and `model_checks` measures that same position; the DECISIONS wording in item 3 was loose. Corrected here: "the token after the rendered prompt, at the assistant turn start". The Qwen ids 64..68 are for that position |
| Headline LoRA numbers (0.26/0.53) not tied to per-case records (Sonnet) | **Confirmed, expected**: they come from `demo_out/test_look.json`, the older fixed-cell study (18 cells, 72 cases), not the generated sets; now hash-pinned. Per-case import of that set is **deferred** |
| Generator default wrote into demo/gen (Opus) | **Applied**: needs an explicit scratch dir and refuses demo/gen |
| Doc cites non-existent `test_report_fresh.py` (both) | **Applied** (now `test_claims_and_report.py`) |
| git dirty ignores untracked; gpu seconds exclude load; vacuous assertion; citation matching lenient (both) | **Deferred** (minor) |
| Regret of the order-averaged distribution hides position bias (Sonnet) | **Deferred**: `per_order_soft_regret` is already stored; a report column is to be added |

Protected files were not changed by these fixes (hash check still OK).
