(Saved summary of the G2 Sonnet review; verdict: PARTLY justified.)
1. Ceiling is one seed; (a) varies 4x across seeds; "tie rule" explanation untested -> say "indistinguishable from ceiling at lr 1e-4 within one-seed noise"; optional ceiling seeds 1-2 (~1.2 GPU-h).
2. Conditions 2 and 3 are the same test (b == always-cheapest); stated-cost rule (0.214) is the stronger comparator and is not tested -> add (a) vs stated-cost (CPU).
3. 16/42 tune cells share label keys with training; clustering by (V, grid) not done; T1 (26 non-overlap) passes.
4. Seeds do not cover the training draw / labels -> state in wording.
5. (c) one seed, at_or_above unshufflable; T4 not in summary JSON tags.
6. Best epoch 5 = cap for several runs; ceiling not necessarily converged.
7. Letter mass condition is near vacuous (full-vocab letter loss).
Code checks: seed averaging, bootstrap, target indexing, derangement, epoch-0 handling, outcome label found correct.
Freeze before test: exact (a) config and the 3 adapters by sha256, handling of conditions 2/3, stated-cost comparison, ceiling seeds, bootstrap unit, overlap reporting, reference arms and seed counts, wording; G3 + owner go needed.
