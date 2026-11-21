# Review-and-improve loop

Run this after Stage 1 has finished (STAGE1_REPORT.md exists). Do not ask me questions; make reasonable choices and log them.

## Goal

Improve PROTOCOL.md, the code in refimpl/ and tests/, and the evidence in REFERENCE.md until a fresh blind Sonnet reviewer scores the work **Overall ≥ 8** and a fresh blind Fable reviewer scores it **Overall ≥ 9**.

## Each round

1. **Build the review packet.** Create a new empty folder outside the repository, `/tmp/review_packet_<random>/`. Copy in only these files:
   - PROTOCOL.md;
   - REFERENCE.md, regenerated so its code listings match the current refimpl/ and tests/ exactly;
   - STAGE1_REPORT.md.

   Nothing else goes in: no review history, no notes, no git log, and nothing that says this is a round or a revision. Before sending it, check the packet's text for words like "round", "iteration", "reviewer", "previous version" or "v6", and remove them.
2. **Run the reviewers.** Spawn the `blind-reviewer-sonnet` and `blind-reviewer-fable` subagents, in parallel, as **new** subagents. Never resume one from an earlier round. Give each only this message: "Review the documents in /tmp/review_packet_<random>/". Add no other context.
3. **Record the scores.** Append both score tables and the dated weakness lists to `~/review_log/rounds.md`. This file is outside the repository and never goes into a packet.
4. **Stop if the targets are met.** If Sonnet's Overall ≥ 8 and Fable's Overall ≥ 9, stop and go to "Finish".
5. **Revise.** Fix the weaknesses both reviewers raised, most severe first. Wherever a weakness can be settled by measurement on this GPU, measure it rather than argue it: timing, memory, letter mass, an agent running, a determinism check. Then:
   - update PROTOCOL.md, the code and the tests;
   - run all unit tests, which must pass;
   - rerun any smoke check affected;
   - record measured results in REFERENCE.md;
   - commit with a message describing the changes.

## Rules that always hold

- Never run the pilot or any confirmatory phase.
- Never compute, print or save an offer, regret, S text or calls log for any agent on a confirmatory prompt. Engineering checks use pilot variants 13–14 or off-grid prompts, and report only pass/fail, counts, timings and memory.
- Keep the agent sandbox from Stage 1: no network and no `HF_TOKEN` for any process that imports agent_py_files.
- Never weaken a test or control just to raise a score. If a reviewer's fix would make the design worse, keep the design, explain why in PROTOCOL.md, and log the disagreement in rounds.md.

## When to stop without meeting the targets

- after 6 rounds; or
- if the Overall scores have not improved for 2 rounds in a row; or
- if every remaining weakness needs something outside this instance's reach, such as a different model, more data, or a design change only I should decide.

## Finish

1. Regenerate the registration package exactly as in STAGE1_PROMPT.md step 6. The code and memory-bank hashes must match the final commit.
2. Write `REVIEW_SUMMARY.md` in the repository. It contains:
   - the score table for every round (Sonnet and Fable);
   - what changed each round;
   - which weaknesses remain and why;
   - whether the targets were met.
3. Commit, and stop. Do not push.
