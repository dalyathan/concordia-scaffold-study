# G3 review (Sonnet), test2 look for Llama and Qwen. Packet /tmp/gate_G3_8d9e11af. 2026-11-28.

**Verdict: go-with-changes.**

1. git-clean check in each arm process fails once reference/arm records exist (runs/ is tracked) -> half-written look. Fix: clean check in the parent only; arm processes check frozen-file hashes.
2. No resume rule for a crash mid-arm; report needs exactly one record per arm/seed/split; no wording for a missing arm. Fix: freeze a --splits option, a resume rule (scoring a split with no record is not a second look; failed preflight scores nothing), and "T1 untestable" wording.
3. Statistics code not frozen: llama_report.py (imported by test2_report.py), cpu.py, records.py, task.py, package versions. Fix: add to the freeze.
4. T2 wording overclaims: V 13-15 cells also carry grid F (at-or-above must) and mostly wording 3; versus the rule, T2 is decided by the no-cost cells. Fix: reword; report overlap counts and per-type breakdown beside T2.
5. T2 low power, 12 clusters, percentile bootstrap undercovers; seed variance excluded. Fix: per-seed T2 check (descriptive), "T2 fails" = "not shown"; optional permutation p.
6. T1: "every seed below plain" trivial; T1 can hold with mean above the stated-cost rule; Llama plan still lists the rule inside T1, code/Qwen plan do not. Fix: align; state rule comparison is not decisive.
7. No letter-mass gate. Fix: report mean/min mass per arm and slice; below 0.9 on a slice = readout invalid.
8. check() too light: step tag, equal cases_sha256, exactly 6x2 records, model pin, missing labels dropped silently, duplicate references hidden by rs[:1]. Fix: assert these.
9. Preflight tolerance 1e-3 loose vs 3.3e-16 parity. Fix: tighten (e.g. 1e-5) or keep and record the max diff.
10. Minor: single-seed controls selected on select_B; state per-model verdicts, no pooling.

Before the look: fix the clean check and re-freeze; hash the extra files and versions; resume rule and untestable wording; align T1; reword T2 and report overlap; letter-mass gate; stronger check(); per-model verdicts; owner records the freeze commit; full dry run with a dummy token on a scratch runs folder.

Not verified by the reviewer: test2_cells.json, tests/, protected scorer and payoffs, .gitignore, lock_protected, records.py.
