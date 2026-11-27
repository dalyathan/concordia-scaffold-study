# G1 blind review (Sonnet), Llama 3.1 8B replication plan, 2026-11-27

Packet: PROPOSAL.md, REVIEW_BRIEF.md, LLAMA_PLAN.md, LLAMA_PREDICTIONS.md, MODEL_CHECK_llama.md, GEMMA_REFERENCE_TUNE.md, code/.

**Verdict: go-with-changes.** Design mostly sound; within-Llama arms share one code path; controls, protected scorer and frozen rules are good. Several decision rules can fail or pass for reasons unrelated to the hypothesis; the main readout risk is cheap to check before the GPU spend. (Read only; no code run.)

1. First-token readout may be wrong and the 0.5 stop floor is too low. Llama's assistant turn starts fresh after "Answer: ("; it may begin with "(", "a)", "The". Renormalised mass of 0.5-0.8 still gives plausible regrets. Adapters learn the format, so R3 mixes format and content. Fix: probe ~20 tune cases' top-10 first tokens before step 4; plain mass >= 0.9 a precondition for R1/R2; report mass per arm; if low, change framing (e.g. prefill "(") and re-gate.
2. R4 can fail by construction: epoch 0 (plain) is a selection candidate, so if plain beats 0.429 on select_B the cheapest-label run returns plain; same for scrambled. Fix: also report the last-epoch control adapter without selection, or make R4 conditional; note that selecting controls on the true objective favours them.
3. R3 sub-conditions brittle/weak: 4/4 planted on single cases; "every seed below plain" weak; mass >= 0.97 should be paired with plain mass; the interval ignores training-seed variance and the fixed training draw. Fix: planted failures as flagged notes or pre-state which may fail; state the interval as conditional on one training draw.
4. Cross-model comparison confounded (code path, framing, date header, attention, GPU); L1a etc. not clean. Cheap partial fix: harness plain on Gemma tune (~0.1 GPU-h). If skipped, say so and make within-Llama contrasts the headline.
5. R1 threshold arbitrary; if plain ~0.25, R2-R5 have little headroom. Fix: predeclare "headroom-limited" when plain < 0.30; add a relative criterion (share of the plain-to-rule gap closed).
6. Two-point lr sweep with a 0.005 tie rule; fix "no further sweep" now; edge choice is a limitation.
7. Lesson bytes unverified: NotesSolver reads unstripped; a trailing newline would break equality with render_notes. Fix: confirm the test compares full prompts for all four texts.
8. Minor: seeds vary init/order only (fixed training cells); N = 25 runs descriptive; train_lora.py looks correct (checkpointing, train/eval toggling, reload, epoch-0 check); keep step-4 train record before training.

Q2: no code error found that changes results. Q3 (freeze before a test look): arms going to test; adapter/lr from select_B only; seeds individually or mean; primary test split and expectation for test_hard; absolute and relative thresholds; bootstrap spec; mass floors; frozen framing, system sentence, date string, hub commit, texts, label hashes; pin tag and single-look guard; no change after the tune look; parity decision (if skipped, claims limited to within-Llama contrasts).
