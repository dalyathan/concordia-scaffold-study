# G1 blind review (Sonnet), Llama plan with the assistant-prefix framing, 2026-11-27 (packet /tmp/gate_G1_32380fc1)

**Verdict: go-with-changes.** No code bug that changes a result; main risks are a framing confound and decision-rule gaps.

1. The "Answer: (" prefix is an unmeasured intervention and hides a falsified prediction: L1d (mass >= 0.90) and L4g were written for the unprefixed readout; L1d would have FAILED as written (0.487). The prefix also repeats text (the system prompt says never repeat) and the few-shot turns lack it. Fix: score L1d/L4g as FAILED or not testable for the native framing and report 0.487; on train cases only, run plain without the prefix (renormalised) as a sensitivity row (~1,000 passes; no tune regret); state that R1 is conditional on this framing.
2. Mass bands vs stop rules mismatch: the 0.998 is from train cases; step 4 stops only below 0.5 while R1 needs >= 0.9. Fix: stop step 4 below 0.9 after plain tune (it already runs first).
3. R3/R4 show only in-family fit (tune shares grids, V, templates, phrasing; only names disjoint). Fix: word R3 as "trains in on in-family cells", not generalisation.
4. Intervals shaky for close R2 calls (about 24 groups). Fix: add a BCa/studentised interval or a sign-flip permutation test on group-level paired differences; require an R2 call to have the interval below 0 and a point effect of at least 0.10; define "seed-mean" in R3 (mean of probabilities then regret, vs mean of per-case regrets).
5. lr sweep / seed-0 reuse; the 0.005 tie band is noise; early stopping is "best of up to 5 epochs". Fix: say so; if on an edge, the lr effect is unresolved; no extension.
6. Controls weaker than they look: the wrong rule is one short sentence (a weak null) vs 600+ character paragraphs; one seed per control; R4 thresholds single-run. Fix: a length-matched wrong paragraph, or label the wrong-rule result weak; report R4 as descriptive.
7. Planted 4/4 is strict (planted-nocost needs >= 0.9 on a near-tie). Fix: keep the rule, pre-state that a planted-only failure is reported as "planted-X failed at mass m" with the other R3 conditions reported.
8. Cross-model comparison also confounded by the system role and the date header; put "framing-confounded" in every cross-model sentence; offer the owner the Gemma harness run again at the final report.
9. Smaller: R1's "below has the largest per-type regret" is uninformative when types are close (use the paired difference); bootstrap conditional on one training draw.

Code: no result-changing error in train_lora.py, hf.py, evaluate.py (tokenisation match, full-vocabulary loss, epoch-0 selection and reload, control last-epoch scoring before reload, planted=False in selection). The path check runs in eval mode only (low risk). Could not verify the pinned hashes, baselines, probe JSONs, or that the real code passes `revision`.

Freeze before the test look: framing (prefix, date_string, commit pin, template) as hashed configs; adapters (selected epoch), arms and baselines; interval method and per-claim thresholds; hard-split slices named (hard_V has no at_or_above); scorer hash and pin tag; G3 and the owner's go; test_hard read only as generalisation; the Gemma comparison stays labelled confounded.
