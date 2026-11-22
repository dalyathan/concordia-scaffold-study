# G3 test plan: Opus (summary of returned text; verdict: GO-WITH-CHANGES; do not run the script at its first hash)
1. Dry run did not use the frozen script (old label, one C>=V cell): rerun with the final script, record the new sha256.
2. Look cannot be re-analysed (only aggregates saved): save per-case/per-order probabilities, masses, free-text outputs; separate GPU scoring from CPU analysis.
3. Lock too early; a crash after scoring would lose the look: validate first, lock before first adapter scores a test case, save raw results as each run finishes.
4. Labels can state false things (plain separated but neutral not has no label; PARTIAL text): define the missing label, build text from failed criteria, unit-test every branch.
5. Section 9 changes the approved rules and only the executor wrote it; a G3 review is not owner consent: get explicit owner approval tied to the commit and script hash.
6. Frozen inputs unchecked: case-id hash, cell list, disjointness, script sha, git commit/clean tree, test_go.json content, adapter_config hash, scoring/core/textrows/common/cases hashes.
7. Plain checked on 4 of 72 cases: re-score plain with adapters off on all 72.
8. Free-text: unparsable scored 1.0 vs dropped in lora.py: use the development rule, report parse-failure rate.
9. Missing outputs: cells moving toward best offer; development verdict line.
10. Expected D ~0.11 near the threshold (3 of 6 tune cells C<V vs 6 of 18 test cells): NOT SHOWN/PARTIAL likely; optionally declare C<V interval as a secondary.
11. Minor: tolerance ~0.003 for loaded adapters; commit and push lock and outputs right after; confirm live case never scored with an intervention.
Verified correct: scoring path, adapter switching, always-2 and seed-averaging arms, difference signs, bootstrap, HARM sign.
