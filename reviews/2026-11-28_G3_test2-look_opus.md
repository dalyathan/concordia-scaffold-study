# G3 review (Opus), test2 look for Llama and Qwen. Packet /tmp/gate_G3_8d9e11af. 2026-11-28.

**Verdict: go-with-changes.**

1. The look stops itself: run_one's git-clean check fails once reference/arm records exist (runs/ tracked); no resume after a crash mid-arm. Fix: subprocesses check only that frozen files are committed and unchanged, ignore runs/, skip a split whose record exists; CPU test of the --look path; re-freeze.
2. Statistics not frozen: llama_report.py, cpu.py, records.py, lock_protected.py, plans, predictions; test2_report never re-checks hashes. Fix: add to the freeze; report refuses on hash mismatch; record G3 commit/tag in DECISIONS.md.
3. T1 differs: LLAMA_TEST_PLAN includes the stated-cost-rule interval; code/Qwen plan/proposal do not; stale Llama plan text. Fix: one version (code's); edit plan.
4. T2 wording misdescribes the likely outcome (beats plain, not the rule -> "no evidence of generalisation"). Fix: split T2a (beats plain) / T2b (beats rule) with wording for every combination, incl. T1 fails & T2 holds, and untestable.
5. No letter-mass rule on test. Fix: report mean/min per arm and slice; "not concluded" if any arm in a rule has mean mass < 0.9.
6. V 13-15 interval on 12 clusters (anti-conservative). Fix: also require group sign-flip permutation p < 0.05, or a frozen sensitivity check.
7. Prediction scoring method not fixed. Fix: freeze it, ideally as code; P11 compares slices with different type mixes.
8. Lock token self-asserted. Fix: check it against a DECISIONS.md entry in the pin commit, or make the token the tag.
9. Smaller: preflight should assert re-scored cids equal stored ones; hash adapter_config.json / whole adapter dir; references must be exactly one, with token; update plan text on solver_config_sha256.

Before the look: T1 aligned; T2a/T2b and wording; mass rule; permutation check; prediction scoring; extra hashes and report self-check; driver fixes, re-freeze, G3 commit/token/pin in DECISIONS.md; commit each record after it is written.

Not verified by the reviewer: .gitignore, records.write, lock_protected, protected payoff/scorer, cpu.py, test2_cells.json flags, train_lora reload path, peft behaviour; llama_report.py lines 598-818.
