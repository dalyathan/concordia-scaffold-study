# Rules for Claude editing model weights

These rules apply whenever Claude chooses or computes a change to a model's weights directly: a MEMIT/ROME-style edit, a hand-chosen rank-one update, pruning, or any edit not learned by the frozen LoRA recipe. LoRA training on examples follows its own plans; the general rules (1-4, 10-12) apply to it too. REVIEW_GATES.md still applies in full.

The aim is that an edit Claude makes can be believed: it was planned before it was seen to work, it touches only what it says it touches, it can be undone, and it is measured by the same protected scorer, against controls, on cases it was never shaped on.

## Do

1. **Write the edit down before making it.** Commit a short edit card first. It holds:
   - the target behaviour as input → output on build cells (train, probe or pool; never tune or test);
   - where the edit will go and why;
   - its size budget;
   - the predicted effect on the target cells and on the preservation set;
   - the stop rule.
   - Predictions are committed before any edit is applied, as for every other experiment here.
2. **Locate before you edit.** Choose layers and modules from evidence on build cells: activation patching, attribution, or the failure map. Record the evidence behind each choice, including the sites considered and rejected.
3. **Start with the smallest edit.** Begin with one layer and a rank-one change. Widen only along a ladder fixed in the edit card (more layers, then higher rank). Every rung counts as an attempt.
4. **Keep every edit as a separate, reversible file.** Save the weight delta (or the edited matrices) as its own file with a sha256, next to the pinned base model revision. Loading the base without the delta must reproduce the plain model bit for bit, which is the same check as "adapter off == plain".
5. **Fix a size budget in advance.** Set a cap on the edit's norm relative to the weights it changes, and report the edit's actual size. An edit that needs more than its budget has failed, not "needs tuning".
6. **Measure side effects on a fixed preservation set.** Check these every time:
   - the other case types;
   - unrelated text (perplexity on a fixed held-out sample);
   - first-token letter mass;
   - agreement between the forced-choice letter and the free answer;
   - the planted known-answer cases.
7. **Compare against controls of the same size.** At minimum:
   - a random-direction edit with the same norm at the same sites;
   - the same edit computed from scrambled targets;
   - the LoRA adapter trained on the same examples.

   An edit that does no better than its random-direction control has not been shown to work.
8. **Score only through the harness.** Use the protected scorer, the frozen readout (five orders, the config's prefix), run records, and CLAIMS.yaml with recompute. Never hand-copy a number.
9. **Say who decided what.** In every report, separate what Claude chose (target, sites, size) from what a formula computed (the least-squares solution, the gradient). "Claude edited the weights" is said only of choices Claude made.
10. **Count and log every attempt,** failures included. Each one goes in RESULTS_LEDGER.md as a row, with its edit card and outcome. A dead end is a result.
11. **Gate as usual.** G1 before the first edit of a new kind (sites, method or target), G2 before any conclusion, G3 and the owner's go before any test look.
12. **Re-measure after every edit.** If edits are stacked, score the combined model as a new arm, with its own controls and preservation set.

## Don't

1. **Never use tune or test cells to choose sites, targets or size.** Tune is for the development check named in the plan; test is for the one locked look.
2. **Never edit the readout itself.** That covers:
   - the answer-letter rows of the embedding or the unembedding (lm_head);
   - the final norm;
   - the tokenizer;
   - the chat template;
   - the logit soft-cap.

   An edit there can move the forced-choice letter without changing the decision, which games the scorer. Editing the protected scorer, the payoffs or the case files is out of the question.
3. **Never edit the downloaded model in place.** The base files keep their pinned hashes. Any edit lives in a delta file.
4. **Never hand-set individual weights to fix particular cases.** Changing numbers until named cases come out right is fitting, not editing. Every edit comes from a stated rule and a stated procedure applied to a set of build cells.
5. **Never exceed the attempt budget.** Set a number of attempts per target in the edit card (for example 5). Going past it, or quietly starting over with a "new" target, needs a new G1.
6. **Never accept an edit that breaks the readout,** whatever its regret:
   - mean letter mass below 0.90 on any case type;
   - free-answer agreement down by more than 0.10 from the unedited model;
   - a new planted-case failure.
7. **Never report a single seed or a single edit as a method.** Where the procedure has randomness (sampled keys, the random-direction control), run it with at least three seeds and report each one.
8. **Never carry an edit across models without redoing the locating step.** Sites found on Qwen are a hypothesis for Llama or Gemma, not an answer.
9. **Never let an edit card be written after the result.** If the plan changes after a result is seen, the change is logged as post-hoc in DECISIONS.md and the claim is narrowed to match.

## What a finished edit report contains

- The edit card, committed before the edit.
- The locating evidence.
- The delta file with its hash and size.
- The target and preservation results against the controls.
- The attempt count.
- The split between Claude's choices and computed steps.
- The gate verdicts.
