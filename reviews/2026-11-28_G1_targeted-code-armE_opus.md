# G1 review (Opus), targeted training code and arm E. Packet /tmp/gate_G1_02685ec2. 2026-11-28.
**Verdict: go-with-changes for the nine training runs; no-go for arm E as drafted.**
Training code implements the plan (150 cells, 750 steps, select3 patience 2 with epoch 0, run ids with arm and seed, extras from pool3 outside select3, orders_for(cell)); arms share init, permutation, lr, steps, selection set.
1. Arm E locating step does not measure what E needs (A0 has ~no no-cost gain; finds the stated-cost fix). Fix: thresholded recovery, a donor that solves no-cost cells or regret-gradient attribution.
2. Arm E breaks WEIGHT_EDITING_RULES: single seed/single random draw; no LoRA-on-same-examples control; oracle vs Claude targets; "rank-one" undefined; 10-cell dev gate without margin; scrambled targets cannot rule out a generic "go cheaper" shift (add constant mean-R control, vs always-cheapest); exclude last 1-2 layers; perplexity text disjoint from C.
3. Single-look integrity: E and _last not in the freeze; decide now (wait for E or drop it; add _last or declare tune-only).
4. test3_report: per_seed pairs by index not seed id; load() does not filter step or require one record per seed; readout gate only on H1; missing letter mass defaults to 1.0; N_only/not_concluded wordings not in the plan; tests lack N_only, missing seed, E, stray records.
5. train_lora: extra pins self-referential (hard-code committed hashes); orders_sha256 not checked; --limit applied before extras (no smoke of the extras path); oracle-label sensitivity run cannot be launched; select_B names under select3; solver name without seed (note in plan).
6. build_freeze reads best_epoch/version/extra_key from solver_config top level; they are nested under "training" (probable KeyError).
7. Budget stop sums timing.gpu_seconds; confirm records.cost emits it.
8. targeted_train checks only that draws/labels are tracked, not unmodified.
9. Targeting prompt also gave training ranges and pool composition; report accurately.
10. Predictions Q2/Q3 use other definitions (H1 = T-R only; H2 +0.05); score each by its own definition; log.
11. N not exactly V-balanced (30/50 at V 10-15 in N_s0); report achieved distribution; soften wording.
Freeze before the look: E in or out; _last/oracle-label in or out; missing-seed rule; all wordings; readout gate for every rule; record selection by step and seed; descriptive-table code now; prediction scoring; training environment; rules/predictions files in FILES; lock token tied to G3 verdict.
