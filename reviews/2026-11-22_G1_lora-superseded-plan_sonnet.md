# G1 review, Sonnet: superseded LoRA plan (answer_only / template / shuffled; build and tuning share cells)

Status: for the superseded plan. Not part of any later packet.

**Verdict: go-with-changes.** The code looks sound. The design as written would give a positive result that is nearly guaranteed and uninformative, and a negative result that could just mean undertraining.

Not verified: `refimpl` and `splits.json` were not in the packet. Read in full: `lora.py`, `scoring.py`, `common.py`, `pairs_template.py`, `summary.json`. Nothing was run.

1. **Build and tuning are the same 17 cells**, differing only in name variant. A LoRA can reach near-zero tuning regret by memorising a 17-entry cell-to-offer table; early stopping on the same cells rewards that. "answer_only beats always-2 and plain" is almost guaranteed, and the shuffled arm does not rule out lookup. Dev cells have V+C odd and test cells V+C even, so a later test claim is interpolation. Fix: split by cell; train on about 12 dev cells, early-stop and decide on the other 5 (or 3-fold cell cross-validation); report train and held-out-cell regret separately; apply "works" to held-out cells only.
2. **The template arm is a near-duplicate of answer_only.** The teacher paragraph names the best offer (tuning regret 0.001). No arm distils the method paragraph, which "matches the text" is defined against. Fix: add an arm whose teacher is the method paragraph; keep template only as a labelled upper bound.
3. **The shuffled arm is not a clean null.** Permuting best-sets across 34 cases leaves many labels correct or overlapping; best-sets are shared across cells. Fix: compute overlap and regret of the shuffled targets; use a permutation mapping each case to a disjoint best-set from another cell; at least 3 permutations.
4. **Single seed plus selection bias.** Early stopping picks the best of up to 9 evaluations on the compared cases, so every arm is at most 0.714 by construction; intervals are anti-conservative and ignore seed variance. Fix: at least 3 seeds; compare on held-out cells; margin must exceed seed spread.
5. **A negative result is uninformative as written** (rank 4, lr 1e-4, at most 272 steps, no check that the model can fit the training data). Fix: precondition that answer_only train soft regret falls below about 0.1, else "undertrained"; pre-register one fallback setting.
6. **The decision rule is ambiguous, and the metric is dominated by one case type** (9 of 17 tuning cells are cost-below-resale). The letter-only loss pushes letter mass up, a format effect. Fix: one unambiguous rule; per-type regret; letter-mass floor; free-text and reworded-scaffold checks.
7. **Code: nothing found that clearly changes the result**, one thing unverified: `letter_ids` come from `convert_tokens_to_ids` and the assertion only checks positivity. Fix: assert they equal the ids `letter_scores` uses; check epoch 0 reproduces plain exactly; check the training loss's letter log-probabilities match `lm.last_first_token` on one example.

Freeze before the single test look: adapter checkpoints and hashes chosen on held-out dev cells only; comparators (plain, always-k fixed from dev, method paragraph, shuffled); metric, weighting, margin, bootstrap, mass floor; an exclusion rule; what counts as a lookup result; a statement that the test is interpolation; no step run a second time after the single look.
