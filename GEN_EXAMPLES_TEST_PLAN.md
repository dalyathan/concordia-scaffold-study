# GEN_EXAMPLES_TEST_PLAN.md (for owner approval; NOTHING has been scored on any test set; needs G3 and an explicit go)

## What would be scored
The existing adapters only, no retraining, no new seeds, no choice of lr, epoch or seed after the test look: claude_examples lr 1e-4 seeds 0, 1, 2; cheapest_label s0; shuffled_claude s0; answer-trained ceiling lr 1e-4 s0 (reference); plain model; baselines always-cheapest and stated-cost rule (computed). Adapters identified by adapter_sha256 in demo_out/gen_lora/*.json; before the look, re-score tune from each reloaded adapter and require it to reproduce the stored tune numbers (|diff| < 1e-3), otherwise stop.

## Test sets
The generated-dataset test cells only (split names to be taken from demo/gen/cells.json, whichever of them the owner names in the go message). Never test_same, test_hard (original study), old test cells, old adapters or name variants 1-14. Same scoring path as tune (five cyclic orders, letter renormalisation, the same name variants as the stored plain scores); assertion grid[0] == min(grid) on every scored cell.

## Decision rule (frozen now; same six conditions as the tune rule, applied to the test cells)
(a) = mean over the three seeds. Pass if all hold: (1) plain - (a) lower bound > 0; (2) (b) - (a) lower bound > 0; (3) always-cheapest - (a) lower bound > 0; (4) plain - (a) on below cells lower bound > 0; (5) no case type worse than plain by more than 0.05; (6) letter mass >= 0.9 x plain. Paired cell bootstrap, 10,000 resamples, PCG64 seed 0, two-sided 95% percentile. If the owner names two test sets, each is judged separately, with no pooling and no correction beyond reporting both.
Reported, not in the rule: stated-cost rule minus (a); (c) minus (a) on below and no-cost cells per seed; the (a) minus ceiling difference by type; slope on stated cost; results split by label-key overlap with the 100 training cells (current key and the stricter V+C key, counts computed before scoring); per-seed spread next to every interval.

## Allowed wording
Pass: "single-label oracle-equivalent supervision at 100 cells lowers soft regret on held-out cells of the same generator, beyond offering cheap and beyond shuffled labels; Claude's labels equal the script-solved oracle up to a tie rule, so nothing beyond that is claimed about teaching." Fail: report the numbers and say the tune result did not carry to the test cells. No equality-with-ceiling claim (one ceiling seed).

## Not allowed / open
No claim about unseen cell types, no "examples beat instructions". Open: ceiling seeds 1-2 (1.2 GPU-h) before any equality statement; cluster-by-(V, grid) bootstrap; test-cell overlap with training keys reported before scoring.
