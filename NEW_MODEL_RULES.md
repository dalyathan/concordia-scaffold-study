# Rules for adding a model or starting a new experiment (lessons from Gemma, Llama, Qwen and the targeted runs)

Each rule below exists because skipping it cost us time or a clean result once. They apply to every new model (Mistral, Gemma 2B, a larger model) and every new experiment, on top of CLAUDE.md, REVIEW_GATES.md and WEIGHT_EDITING_RULES.md. The lesson behind each rule is in brackets.

## Before any GPU time

1. **Check the access tokens first.** At the start of a session, confirm that the GitHub token can push and the Hugging Face token has write access and the model's licence. Tokens go in files (/root/.gh_token, /root/.hf_token) that the user types in, never in chat. [Read-only tokens blocked two backups and a push.]
2. **Make storage survive a stopped pod.** Use a network volume, or push records after every step and back up adapters to the HF artifact repo as each run finishes, with a manifest of sha256 values. Never let the only copy live on a container disk. ["Stop" wiped the disk; three evenings went to restoring.]
3. **Check the lock file on the working branch.** It must contain every package the code imports (peft included). Pin the setup in a script like scripts/pod_test2_look.sh and run its version check first. [The qwen branch's lock lacked peft; a pod run stopped at setup.]
4. **Use one GPU type for everything that feeds a comparison: the A40.** Record the GPU in every run record (the harness does). A number from another GPU type is compared on means only, and the comparison is labelled. [A10G and A40 per-case probabilities differ by up to 6e-2; Gemma's old numbers needed a parity check.]
5. **Run a parity check for the code path.** When code that produced earlier numbers changes, rescore stored cases with the new code and compare per case before any new comparison. [Gemma's bf16 soft-cap readout went unnoticed until the parity check.]

## Before any data from the new model

6. **Use only the harness.** A new model is a YAML file in harness/models plus `tools/model_checks.py`, never model-specific scoring code. [The Gemma-only code had to be ported and re-checked.]
7. **Fix the readout rule in the plan before scoring anything:** the assistant prefix (if the first token is not a bare letter), the letter-mass floor and the planted known-answer cases. Never change a readout threshold after seeing data; if it must change, log it as post-hoc and narrow the claim. [Llama's readout check was restated after the data.]
8. **Commit predictions alone, first.** Then the plan, then the data, then runs. Each prediction is scored by its own definition, even if the plan's rule later changes.
9. **Run the full control set on every model, from the start:**
   - plain;
   - the written rule;
   - Claude's lesson;
   - neutral text;
   - **the wrong rule**;
   - scrambled labels;
   - cheapest labels;
   - the model-free references.

   [The wrong rule turned out to be the most telling control; on Gemma it came late.]
10. **Score the written answers too.** Measure free-answer agreement with the forced-choice letter, and the free-answer regret, for plain and the headline adapters, as a descriptive check on every model. [For a long time forced choice was the only readout.]

## Training data and runs

11. **Check training-set coverage before training.** Tabulate cells by case type × resale-value band × grid × wording. Any slice the test sets will probe that has fewer than about 10 training cells is either filled before training or named as a limitation in the plan. [High-value no-cost deals were thin in the 100 cells; that is exactly the weak spot found later.]
12. **Use three seeds, select early, keep the last epoch tune-only.**
    - Select on a set that covers the test ranges.
    - The last-epoch adapter is scored on tune only.
    - Runs that crash or diverge are reported, never rerun.

    [One Qwen seed and one targeted run collapsed after their best epoch.]
13. **Pin every training input:** cells, labels, orders and rule, by committed-file hashes in code, not by hashes stored inside the same file. [Self-referential pins would have passed an edited file.]

## Held-out tests

14. **Never edit a file that an earlier look froze by hash.** Put new splits and tools in new modules that import the frozen ones. [Editing them would have broken the published test2 reports' checks.]
15. **Write and test the report before the look.** That includes the descriptive tables, the prediction scoring, the rule for missing seeds and the readout gate on every rule, all on synthetic records. Freeze it in the look's freeze file.
16. **One look per arm,** enforced by the harness guard. Anything not scored in that look (a late arm, a last-epoch adapter) stays out of the test set for good, or gets its own new held-out set.

## Tests and tools

17. **Tests write only to scratch folders.** Every test that runs evaluate() or a builder passes a temp directory explicitly, and a guard fails the test if it leaves a file in runs/ or demo/gen. [Twice a test wrote synthetic records or tables into the real folders.]
18. **Check reports across machines by their markdown.** JSON floats can differ in the last digit between machines (numpy summation order).
19. **Decide whether to keep an idle pod by cost.** An idle A40 costs about $0.60/h. A fresh setup costs about 20-30 minutes plus the risk that no A40 is free. Keep the pod through short gaps; stop it, after the backup is verified, for gaps of several hours.
