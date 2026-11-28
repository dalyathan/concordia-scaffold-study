# G1 review (Sonnet), targeted vs random extra examples (Qwen). Packet /tmp/gate_G1_f0a60abd. 2026-11-28.
**Verdict: go-with-changes.**
1. H1 tests composition, not targeting. Fix: primary = H1 AND H4 (T<R and T<N); else word as "more no-cost data helps"; add a V-balanced no-cost random control.
2. Uncertainty ignores seed and draw variance; per-seed draws for R and N; all seeds same direction; two-level bootstrap or 5 seeds.
3. Checkpoint choice not frozen; select_B is in-range only. Fix: name selected/last primary; a selector from pool cells matching test3 ranges; epoch-0 rule.
4. H2 (+0.05) unpowered; N has no extra below/at-or-above cells. Fix: margin from seed spread; report T-A0, R-A0.
5. Label accuracy by arm not pre-registered; labeller should not see arm membership; shuffled.
6. A0 comparisons confounded (500 vs 750 steps): descriptive only.
7. H3: on no-cost cells the stated-cost rule is always-cheapest; reword; run for R and A0.
Code: fingerprints lack rendered prompts; name pools share parts; train_lora extension traps (n_cells/SCHEDULE, 100-id asserts and pins, split train, orders per cell arm-independent, epochs, lr).
Freeze before the look: look code tested; hashes of rule, prompt, draws, labels, orders; adapter choice and selector; diverged-run rule; label accuracy report; conjunction rule; H2 margin and H3 wording; readout gate scope; tables published regardless.
