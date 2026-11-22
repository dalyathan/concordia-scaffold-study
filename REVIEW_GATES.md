# Review gates

Blind review by two fresh reviewers is part of the process. It applies to every task in this repository, including when a message says "be economical" or "no review rounds": those words mean no review beyond these gates.

## When

- **G1, before a big run or a new method.** Before launching any GPU job expected to take more than 1 hour, and before the first run of any new method, rung or training arm.
- **G2, before a conclusion.** After results arrive and before writing a verdict as a conclusion in DEMO_STATUS.md, or putting a result into the demo.
- **G3, before the test set.** Before any intervention is scored on test cases. G3 also needs an explicit go from the owner in a message; a review can never grant it.

Skip G1 for jobs under 1 hour that use an already-reviewed method. Run at most two gates per message unless the message says otherwise.

## How

1. **Build the packet.** Make a new, empty folder `/tmp/gate_<gate>_<random>/`. Copy in only:
   - `PROPOSAL.md`: three or four sentences of project context; then exactly what is about to be done or concluded, with its decision rules and numbers;
   - `REVIEW_BRIEF.md`: the questions (template below);
   - the files needed to judge it: the relevant DEMO_STATUS.md sections, RESULTS_LEDGER.md, the relevant code, and small result summaries.

   Put nothing else in: no earlier reviews, no review log, no chat, no git log, no names of people, and nothing that says this is a round, an iteration or a revision. Before sending, search the packet for "round", "iteration", "reviewer said", "previous review", "revision" and remove them.
2. **Run the reviewers.** Who reviews depends on the gate: **G1 uses Sonnet alone**, unless the step will use more than 3 GPU hours, then Sonnet and Opus; **G2 and G3 always use Sonnet and Opus**. Spawn `gate-reviewer-sonnet` (and `gate-reviewer-opus` where required) as new subagents, in parallel, and never resume an earlier one. The Fable reviewer is no longer used. Give each only: "Read /tmp/gate_<...>/REVIEW_BRIEF.md and follow it."
   - If those agent types are not available in this session, spawn general-purpose subagents with model sonnet (and model opus where required) instead. Paste the instructions from `.claude/agents/gate-reviewer-*.md` as their prompt, plus the packet path.
   - If the Opus reviewer cannot start at all, run a second fresh Sonnet reviewer instead and log that.
3. **Save the reviews** to `reviews/<date>_<gate>_<topic>_{sonnet,opus}.md`. They never go into a later packet.
4. **Act by rule**, and log every point as applied, deferred or rejected, with the reason:
   - Both reviewers say no-go: do not run it. Fix and re-gate once. If it is still no-go, log it and move to the next task.
   - A problem raised by both, or marked most severe by either, whose fix takes under 30 minutes of work or under 1 GPU hour: fix it before proceeding.
   - Anything else: list it under "Open review points" in DEMO_STATUS.md and proceed.
   - Never weaken a control, touch the test set, or break a time limit because a review suggested it.
   - Re-review at most once per gate.
5. **Record the gate** in RESULTS_LEDGER.md notes or DEMO_STATUS.md: gate, topic, both verdicts, what changed.

## REVIEW_BRIEF.md template

```
Read PROPOSAL.md first, then the other files in this folder. Answer in at most 900 words.

1. [G1] Is the proposed step well designed? Look for flaws in setup, targets, controls,
   evaluation and decision rules, and for anything that would make a positive result
   misleading or a negative result uninformative. What should change before running it?
   [G2] Is the stated conclusion justified by the evidence? What alternative explanations
   remain, and what is the cheapest check that would rule out each?
2. Any errors you can find in the code that affect the result.
3. What must be decided or frozen before the single look at the held-out test cases?

Format: verdict first (go / go-with-changes / no-go for G1; justified / partly / not
justified for G2), then numbered problems ranked by severity, each with a concrete fix.
Mark anything you could not verify. Do not modify any file.
```
