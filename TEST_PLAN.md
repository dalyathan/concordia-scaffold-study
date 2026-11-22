# TEST_PLAN.md — APPROVED by the owner with the answers in section 8 (nothing has been run on test cases yet)

Status: approved by the owner (Nov 22) with answers (1) yes to the test look, (2) neutral seed 2 run on tuning cells first then frozen, (3) no extra shift-to-2 control, (4) threshold 0.10 kept. Nothing here is a result. A look at the test cases needs (a) this plan approved by you in a message, (b) gate G3 (Sonnet + Opus) on the approved text, (c) your explicit "go". The frozen LoRA rule was not passed on the development cells; so a test look is a new, separate, pre-registered question and the owner must decide that it is worth spending the one look.

## 1. Question and claim to be tested
Does a rank-4 LoRA distilled from the method-text teacher lower first-token soft regret on unseen cells compared with plain, neutral-distil, wrong-rule-distil and always-2? (Exploratory development evidence: held-out tune cells, selected-on; method 0.194 vs wrong-rule 0.404, neutral 0.531, always-2 0.333, plain 0.577.)

## 2. Test cells (variants 1-14 excluded; only name variants 15-18; no train or tune cell)
`demo/splits.json` split "test": 72 cases = 18 cells x 4 variants (15-18), case-id list sha256 prefix c232e47c86ae089d.
Cells (V, line, C): (2,C2) (2,C4) (2,neutral) (2,pressure) (3,C1) (3,C3) (3,C5) (4,C2) (4,C4) (4,neutral) (4,pressure) (5,C1) (5,C3) (5,C5) (6,C2) (6,C4) (6,neutral) (6,pressure). Of these, cells with stated cost below resale (C<V): (3,C1) (4,C2) (5,C1) (5,C3) (6,C2) (6,C4) = 6 cells; with C>=V: (2,C2) (2,C4) (3,C3) (3,C5) (4,C4) (5,C5) = 6 cells; no stated cost: 6 cells. Unit of analysis = cell (n = 18). The live demo case v15-V3-information-C1 is a test case and is included. Test plain soft regret (earlier): 0.534.

## 3. Adapters (frozen by hash; no re-selection of lr or epoch on test data)
Each at the best epoch saved by early stopping on the held-out tune cells (that rule has no test analogue and is not re-run). Same scoring code, five cyclic orders, first-token letters renormalised.
| Run | best epoch | adapter sha256 |
| --- | --- | --- |
| method lr 1e-4 s0 | 2 | 074552fd0ccb3b4289e55cec30f18416b82f3ef23705c1f01f9b6a8beaaca3c8 |
| method lr 1e-4 s1 | 2 | 6fb73ed23b05e4ee1e03b0d54e2ad7a23fee98caae0a6873df48a4e03591c712 |
| method lr 1e-4 s2 | 4 | b5297b15ab2b91d84dfcfb80046e578920491d1a298e811af1557206c6b7ea0e |
| wrong-rule lr 1e-3 s0 | 5 | 15fbe9f650d4ee6f6f7550acc4fab707a9d4e353bb1b57017c01b2764ca37090 |
| wrong-rule lr 1e-3 s1 | 5 | 1b71d2cb378b19cea54a18a7f29dfe08eedaa05bcf1735a74e7dfbcafa3ad665 |
| wrong-rule lr 1e-3 s2 | 2 | 33234ecfc2b0a7dbae9abf5e06bfc9198014f6ae1e93d5dcd9c8a6b9083a706a |
| neutral lr 1e-4 s0 | 1 | 8ca8b754ea0c216671dfe08157ce8c968febd51c4182df65a97716e010188966 |
| neutral lr 1e-4 s1 | 3 | 1f5adbe997a5ba52f99f691cc11ec47ff918394a9d5c346bc22871675b2e9e0c |
Neutral seed 2 (lr 1e-4) was run on tuning cells and is frozen: best epoch 3, sha256 d3f49c7b1e50708521372d4c05bf33c8cfaaafcb2629843771b2c09135f8ce0b, held-out tune soft regret 0.516. Neutral now has 3 seeds. The machine-readable frozen list is demo/test_frozen_adapters.json (verified by sha256 before scoring). Reference rows computed without adapters: plain, always-2, and the in-prompt method text (an upper reference, not a comparator to beat).
Seed policy: arm value = mean of all seeds' per-case probabilities (3 for each of method, wrong-rule and neutral); no best-seed selection; per-seed values reported alongside.
Adapter files are gitignored; before the look verify each sha256 and that adapter-off scoring reproduces plain bit for bit (safety checks 1-3, demo_out/lora_checks.json).

## 4. Primary comparison (one, declared in advance)
Cell-mean soft regret. D = mean over test cells of [soft regret(wrong-rule arm) - soft regret(method arm)]. Paired cell bootstrap, 10,000 resamples, numpy PCG64 seed 0, 95% percentile interval. **Primary claim holds only if D >= 0.10 and the lower bound > 0 and the same holds against neutral-distil and plain, and method is not worse than always-2 (lower bound of always-2 minus method > 0 required for any claim of "beats always-2").** Always-2 is a required comparator because the wrong-rule control behaves like a shift to 2 on the development cells.

## 5. Secondary outcomes (declared now; descriptive unless stated)
1. Differences vs plain, neutral, always-2 separately, with the same bootstrap.
2. Split of D by cell type (C<V, C>=V, no stated cost) with no interval, plus leave-one-cell-out D (n = 18).
3. Slope of the expected offer on the stated cost over the 6 C<V test cells (descriptive; 6 cells), and the number of cells where the method's expected offer moves toward the best offer.
4. Letter mass >= 0.9 x plain (format check); free-text hard regret on a 4-case-per-cell sample, method vs plain (descriptive).
5. Per-seed values of every arm.

## 6. Outcome table (written before the look; covers every case)
- **SUPPORT:** primary claim holds (section 4).
- **PARTIAL:** lower bound > 0 vs plain and neutral but not vs wrong-rule or always-2: "improves on plain, not separated from a shift-to-2".
- **NOT SHOWN:** lower bound vs plain <= 0. Read only as "not shown here" (n = 18 cells, one look); not as evidence of absence. No second look, no re-tuning, no new arm on these cells.
- **HARM:** method worse than plain with upper bound < 0 on the C>=V cells (where the rule should not help): reported as a harm finding.
In every case report the frozen development verdict ("not passed") next to the test result.

## 7. Locked before the look
Scoring code, prompts, orders and analysis script (explore_cpu.py extended by a test-mode script written and committed before the look; commit hash recorded here at approval); no edits to PROTOCOL.md; variants 1-14 and agent_py_files untouched; no intervention other than the adapters above on test cases; G3 Sonnet + Opus before the run; stop time rule (all work before Nov 24 23:00 CST). One run, one report.

## 8. Owner's answers (Nov 22)
(1) Yes to the test look. (2) Run neutral seed 2 on tuning cells first, then freeze it: done. (3) No extra shift-to-2 control; always-2 is already a required comparator. (4) Keep the 0.10 threshold.

## 9. Clarifications written by the executor after gate G3 (need the owner's explicit approval, tied to the script hash; see section 10)
Gate G3 (Sonnet + Opus, both go-with-changes) found defects in the first script; all were fixed and the script re-run as a dry run on tune cells. Changes to the approved plan's wording:
- **Always-2.** "Not worse than always-2" (section 4) = mean(always-2 soft regret - method soft regret) >= 0. "Beats always-2" (lower bound > 0) is reported in the SUPPORT headline and is not required.
- **Labels (section 6), built from the comparator table.** SUPPORT: D >= 0.10 and lower bound > 0 against wrong-rule, neutral and plain, and always-2 not better in mean. PARTIAL: lower bound > 0 vs plain and neutral, SUPPORT not met (the label lists the failed conditions). **PLAIN-ONLY (new):** lower bound > 0 vs plain but not vs neutral. NOT SHOWN: lower bound vs plain <= 0. HARM is an appended flag, not an override (upper bound of plain - method < 0 over the C>=V test cells, needing at least 3 such cells). The label is printed next to the full comparator table and the frozen development verdict "not passed".
- **Declared secondary:** the C<V stratum (6 test cells) difference control - method with a bootstrap interval; the count of C<V cells where the method's expected offer is closer to the best offer than plain's. Descriptive: split by cell type, leave-one-cell-out, slope on stated cost (pools V; confounded), free-text hard regret on all 72 cases (greedy, unparsable answers dropped as in development, parse-failure rate reported).
- **Power warning.** On development cells the method's advantage over wrong-rule was about +0.50 on C<V cells and about -0.1 elsewhere; re-weighting to the test mix (6 of 18 cells C<V) gives an expected D of about 0.11, near the 0.10 threshold, with a wide interval. PARTIAL or NOT SHOWN are likely outcomes even if the effect is real; a NOT SHOWN is read only as "not shown here".
- **Limits stated:** the bootstrap resamples cells only (inference about these adapters on new cells, not about the training procedure; seed spread is reported per run); percentile intervals at n = 18 skewed cells are approximate; every arm's lr and epoch was chosen on the same 6 development cells; plain test soft regret 0.534 was seen before; loaded adapters reproduce training-time held-out values to about 0.003 (dry run), recorded as the expected tolerance. The live demo case (v15-V3-information-C1) was never scored with any adapter or vector (floor.py refuses interventions on test cases); this look is the first intervention on it.
- **Execution.** `demo/test_look.py --execute` validates first (adapter safetensors and config sha256, the 72-case id list hash, the 18-cell list, disjointness from train/tune cells, this script's sha256 recorded below, clean git tree for demo/ refimpl/ TEST_PLAN.md, test_go.json), loads the model, re-scores plain with adapters off on all 72 cases and asserts max abs diff < 1e-4 against the saved plain probabilities, only then writes demo_out/test_look.lock (commit, script hash, versions, GPU, hashes of scoring.py, textrows.py, common.py, steer_lib.py, core.py, splits.json, cases file, frozen list), then scores each adapter and writes raw results to demo_out/test_look_raw.json after each. Statistics come from `--analyze`, which reads the raw file only and may be re-run. A failure before the lock may be rerun; after the lock only `--analyze`. Variants 1-14 are loaded by common but never scored.
- Test-mode script: demo/test_look.py, sha256 f0f33b83893f984eb5faebc7d32cbf0c194ec5d6d89e4ca463426b351564b042.

## 10. The owner's go
Not yet given. `demo/test_go.json` must be created from the owner's explicit message and contain {"go": true, "section_9_approved": true, "script_sha256": "<the hash above>"}; the script refuses to run without it.
