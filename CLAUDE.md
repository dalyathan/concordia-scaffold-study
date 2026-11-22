# Working rules for this repository

- Follow REVIEW_GATES.md: blind Sonnet and Fable reviews at gates G1 (before a big run or new method), G2 (before a conclusion) and G3 (before the test set). This holds even when a message says "be economical" or "no review rounds".
- Never use name variants 1-14 for the demo, never import agent_py_files, and do not edit PROTOCOL.md unless a message explicitly asks.
- Interventions run on build and tuning cases only. Test cases need G3 and an explicit go from the owner.
- Do not ask questions in unattended runs: log choices in DEMO_STATUS.md, commit and push after each step.
