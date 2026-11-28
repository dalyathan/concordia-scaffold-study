# G1 review (Opus), targeted vs random extra examples (Qwen). Packet /tmp/gate_G1_f0a60abd. 2026-11-28.
**Verdict: go-with-changes.**
1. Intervals ignore training-seed and cell-draw variance (one fixed draw per arm shared by seeds). Fix: per-seed draws; two-level bootstrap or all-seeds direction condition; consider 5 seeds.
2. H1 mostly measures no-cost data share (R ~18 no-cost of 50), not targeting; T vs N is the targeting test. Fix: make T-N co-primary; reword H1-only result.
3. H2 wording wrong ("harm not excluded"), pooling unspecified; apply to N.
4. train_lora traps: run id / solver name collide across arms (overwrite stop, pooled by run_mean); epochs ceil(500/150)=4; SCHEDULE lacks 150; asserts (split train, 100 ids, label pins) must be relaxed with separate pins; orders for extra cells unspecified; gen_test2.install() needed; lr explicit.
5. Label noise differs by arm; compute oracle agreement by arm; freeze handling.
6. gen_test3: original_study_cell not excluded; planted problems unchecked; fingerprints lack rendered prompts and renderer files; names can repeat within test3.
7. select_B early stopping can disfavour novel-range extras; freeze selected adapter primary, epoch-0 rule, report best epoch and _last.
8. Stratum "(V, grid) present in extras".
9. Give the targeting Claude per-seed failure values.
Freeze before the look: analysis script hash, bootstrap design, co-primary structure and wording, adapter version and epoch-0 rule, failed-run rule, hashes of extras/labels/orders/adapters, averaging order, references, readout gate, H2 pooling, preflight, owner go.
