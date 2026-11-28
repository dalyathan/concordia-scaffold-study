# Teaching Gemma to haggle

Can a small open model be made a better negotiator by changing it internally, with a stronger model (Claude) as the teacher? This repository tests that on **Gemma 2 9B-it** in a one-shot buying decision taken from the 2024 Concordia haggling game. The best offer can be calculated exactly, so every answer gets an exact score: **regret**, the profit the buyer left on the table compared with the best possible offer, in coins. Zero is perfect.

The live numbers are in **[RESULTS_LEDGER.md](RESULTS_LEDGER.md)** (one row per method ever tried, dead ends included) and the running log is **[DEMO_STATUS.md](DEMO_STATUS.md)**. This page holds the settled findings, the problem tree with what is solved, and the history of how we got here.

## Results at a glance

Losses are mean regret in coins per decision; lower is better. "Locked test" means a set of cases that was fingerprinted before any model saw it and scored exactly once, under a rule written in advance.

| Question | Answer | Key numbers |
| --- | --- | --- |
| Does plain Gemma fail? | Yes. It ignores the cost the seller states and offers about 2 coins almost regardless. | Not optimal in 55% of decisions; its offer moves 0.12 coins per coin of stated cost (should be 1) |
| Does one sentence in the prompt fix it? | Mostly. Same-length neutral text, a wrong rule and "only your profit matters" do nothing. | Held-out loss 0.58 → 0.17 |
| Can a steering vector do what the sentence does? | No. Vectors that move offers are only a push toward one answer letter. Patching shows why: the sentence's effect differs case by case and appears only in the last third of the network. | Best coherent move about 0.2 coins; still worse than "always offer 2" |
| Can the sentence be trained into the weights (LoRA)? | Yes, on the fixed cells. | Locked test: 0.26, same as the sentence in the prompt (0.26); plain 0.53; outcome **SUPPORT** |
| Does Claude's own written lesson train in? | It improves with feedback, but trained in it mostly becomes an "offer the cheapest" knob and hurts cases with no stated cost. | Tuning: 0.38 vs plain 0.66; **not passed** |
| Do Claude's worked solutions train in? | Yes, and Gemma's offer now follows the stated cost, including on harder unseen cases. | Locked tests: same-range 0.04 (plain 0.69), harder 0.17 (plain 1.30); both **passed** |
| Does the fix reach Gemma's written answers? | No. The add-ons fix the multiple-choice pick, not what Gemma says in words. | Written offer agrees with its own pick on about a third of cases |

Two limits to state with every result: Claude's "worked solutions" were the correct answers (it solved the game with a script), so they show that a teacher who can solve a task can produce data that fixes a student, not that Claude taught beyond that. And every fix so far lives in the multiple-choice channel, not in free text.

## The problem tree and what is solved

Root: make Gemma 2 9B a better negotiator by changing it internally, with Claude as the teacher. Revised on November 23 after the results.

| | Branch | Question | Status |
| --- | --- | --- | --- |
| A | Measure | Can each decision be scored, and is the failure real? | ✅ Solved |
| A4 | | Do the multiple-choice pick and the written answer agree? | ❌ Open: they mostly don't |
| B | Where a fix can live | Prompt, activations or weights? | ✅ Answered: prompt yes, activations no (mechanism known), weights yes |
| C1 | What to train on | Rules, worked examples or answers? | 🟡 Examples won; comparison not yet clean |
| C2 | | Soft or hard training targets? | 🔄 Running |
| C3 | | How many examples are needed? | 🔄 Running (learning curve at 10, 25, 50, 100) |
| D1 | What the teacher adds | With few examples, do a teacher's examples or explanations beat plain answers? | ❌ Open |
| D2 | | Does a teacher that sees the student's internals fix it better? | ❌ Open: the novel experiment |
| D3 | | Does teaching work on a task with no calculable answer (multi-round haggle)? | ❌ Open |
| E1 | Real behaviour | Does the fix reach written answers? | ❌ Open: first priority |
| E2 | | Multi-round negotiation | ❌ Open |
| E3 | | The seller role and side effects | ❌ Open |
| F | Transfer | New values, price grids and wording | ✅ Passed |
| F | | Other models (Llama 3.1 8B) | 🟡 Tune results after G2 (Nov 28, branch `llama`; Sonnet + Opus "partly justified", wording fixed): on the forced-choice letter, plain Llama is close to uniform guessing (1.18 vs 1.26); written paragraphs help but a wrong rule helps as much; LoRA on Claude's examples reaches 0.048 and beats the scrambled control, yet the frozen rule says "not replicated" because every adapter fails the planted no-cost case, as Gemma's adapters also do (Nov 28). In-family tune only; test2 plan drafted (LLAMA_TEST_PLAN.md), waiting for G3 and the owner |
| G | Infrastructure | Pluggable models and tasks, and numbers that can't be made up | 🟡 Built and unit-tested on CPU (Nov 23, branch `refactor`); full suite run on a fresh clone with Concordia pinned (128 pass, 1 skip, 1 old test needs the GPU machine's `logs/`); a G2 blind review done (partly justified, fixes applied). Nov 27-28 (branch `llama`): Llama access granted and checked; the HF solvers and the model-agnostic LoRA trainer (harness/train_lora.py) ran on the A40 for the full tune study (3.2 GPU-h, run records, planted cases, claims checked); Nov 28: Gemma parity run on the A40 FAILED its per-case tolerance (up to 1.7e-2 vs 1e-3; mean regret within 0.001); cause located: the harness reads Gemma 2 logits after a bf16 final soft-cap, while the stored code soft-caps in float32 (reproduced to 1e-8); fix proposed, not made; the owner's scorer pin tag still open (REFACTOR_STATUS.md) |

Pruned: baking the vector into a bias (convenience, not knowledge), steering side effects (moot), reasoning pairs for steering, and the contest winners' reasoning (it belongs to the separate pre-registered study below).

## History

**Nov 20–21: the harness.** Reworked the Concordia haggling game into one buying decision with an exact best offer. Moved from CPU to one NVIDIA A10G on AWS; repeated scoring is bit-identical. Baseline on 140 cases: plain Gemma loses money in 55% of decisions.

**Nov 21: is the failure real, and what does a sentence buy?** The failure is about pricing, not answer position (position explains about 15% of choices). One method sentence cuts losses by 58% on tuning cases; matched control texts do nothing. Blind review gates were added to the process (see below).

**Nov 21–22: steering.** Three tuning runs were stopped and redesigned: the first was mis-scaled, the second too weak, and a dose scan showed the positive control failed. A final-layer patch proved the steering code was correct. Vectors built per answer order did move offers at layers 33–39, but only as a push toward one answer letter. Patching located the sentence's effect: case-specific and late. Steering was closed for this failure.

**Nov 22: training the sentence in.** The first loss function let the adapter dodge the answer format (letter mass fell to 1%); it was caught after one epoch and replaced. Training on the correct answers reached zero held-out loss. The distilled sentence missed its development pass rule by 0.003 against the wrong-rule control; follow-up runs matched seeds and learning rates. One look at the locked test set: **SUPPORT**. Free-text answers got worse.

**Nov 22: a larger generated dataset and Claude as teacher.** A generator built 300 training and 42 tuning cells plus two locked test sets (same-range, and harder: new resale values, price grids and seller wording). A blind Claude wrote a lesson from Gemma's mistakes; one round of feedback improved it (loss 0.43 → 0.25 on its feedback cells), a second round made it worse and was rejected by a rule set in advance. Trained in, the lesson became an "offer cheap" knob and did harm on no-cost cases: **not passed**.

**Nov 23: worked examples.** A blind Claude solved the 100 training cases (by script, all correct). Trained on those, Gemma reached 0.03 on tuning cells and its offer followed the stated cost (slope 0.76, as good as the best play). One look at both generated test sets: **passed** on both, and on each harder slice.

**Nov 23: the demo and what's next.** The stage tool now switches the trained add-ons on and off live; a precision bug in loading several adapters was found and fixed; free text was checked and ruled out as stage evidence; every beat is recorded for replay. Two new locked test sets of 120 cells each were generated for the next experiments. A learning-curve experiment (rules vs examples at matched data, soft vs hard targets) is running, with its predictions committed before the runs.

**Nov 23: related setups (branch `refactor`).** Before refactoring the code to take any model or task, a fresh agent with no project history surveyed similar setups: evaluation harnesses (lm-evaluation-harness, Inspect, HELM), provenance tools (DVC, MLflow, Hydra) and 14 papers, each opened on its arXiv page to check title and first author. A first attempt could fetch no pages, and its unchecked output was discarded. Main lessons: structure each condition as an interchangeable "solver"; generate every reported number from stored per-case records; hash-lock all inputs; keep the scorer out of the experiment code's reach. No paper was found comparing prompt, lesson, steering and LoRA across several small models. See RELATED_SETUPS.md.

**Nov 23: the refactor (branch `refactor`).** Built `harness/` next to the old code (which was left untouched, because the running GPU job uses it): one YAML config per model (five models), a task interface with haggling ported (it reproduces `cells.json`, `cases.jsonl` and `fingerprints.json` byte for byte) and a toy second task, every condition as an interchangeable solver, run records for every run, a protected scorer whose hash must be registered in DECISIONS.md, planted known-answer cases in every evaluation, an independent stdlib-only recompute, generated result tables, and CLAIMS.yaml with a checker that fails on unbacked, mismatched or new hand-typed numbers. The 40 earlier per-case result files were imported as run records and the README numbers they back were re-derived: all fifteen now reproduce from stored results (the older fixed-cell test look was imported per case too), none differ; one is a definition, not a measurement. Tokenizer checks passed for four of five models (Llama 3.1 8B needs licence access); revisions are pinned in every config. All 16 checkable arXiv citations in the related-setups survey matched title and first author on arxiv.org. The model-backed solvers are written but have never run on a GPU.

**Nov 23: a packaging bug caught on a fresh clone (branch `refactor`).** The five model configs in `harness/models/` had never been committed: `.gitignore` ignored every folder called `models/` (meant for downloaded weights), so a fresh clone failed the config test while the working copy passed. Fixed with a `!harness/models/` exception (weight folders are still ignored), the five YAML files committed, and the whole suite run on a fresh clone with Concordia at the pinned commit: 128 passed, 1 skipped by design, and 1 failure that is not from this branch (`tests/test_ledger.py` reads `logs/demo_dose_scan.log`, a gitignored folder that exists only on the GPU machine). The old tests also needed `torch`, `scipy` and Concordia's own dependencies installed, and torch 2.4.1 has no wheel for Python 3.13, so a newer torch (CPU import only) was used.

**Nov 27: Llama 3.1 8B, stopped at the readout (branch `llama`; a dead end for now).** Through the new harness, with the Gemma parity check skipped by the owner, Llama 3.1 8B passed the tokenizer check (single-token answer letters, a fixed date in its template) and the replication plan passed review gate G1 with changes. A readout probe then showed that with the Gemma chat framing Llama's first answer token is mostly the initial of the buyer's name, so only about half the probability sits on the answer letters, below the frozen floor. Opening the assistant turn with "Answer: (", chosen on train cases, puts 0.998 on the letters; a second G1 accepted that with changes and added a check that the forced letter matches what Llama names when it answers freely. It did not (0.53 agreement against a frozen 0.7; chance 0.2), although the unprefixed readout agrees even less (0.49) and the free answers themselves change with option order in most cases. By the frozen rule nothing further ran: no Llama regret, no LoRA. About 0.15 GPU-hours used. Code for every remaining step is ready and smoke-tested; the owner decides whether to restate the threshold or change the framing. The push to GitHub failed at the time (the token lacked write access); it works since Nov 27. The owner then restated the check as format-only (post-hoc) and the run resumed (see the next entry).

**Nov 28: Llama 3.1 8B on the tune cells (branch `llama`).** After the owner restated the readout check as format-only (post-hoc; the forced letter agrees with Llama's free answer on only about half the prompts), the frozen plan ran: 3.2 GPU-hours, about $2. Plain Llama turned out close to random guessing on the forced-choice letter (1.18 vs 1.26 for uniform), offering too much on every case type. Both written paragraphs lowered regret, but a one-sentence wrong rule lowered it as much, so the prompt result shows a generic push rather than use of the content. LoRA on 100 of Claude's worked examples brought regret to 0.048 (3 seeds; Gemma 0.032) and beat the scrambled-answer control. After training, the adapters' free answers matched their forced letters on 90-95% of probe prompts. Every adapter failed one planted known-answer case (no cost), so the frozen rule reads "not replicated"; Gemma's adapters were never held to that check. Review gate G2 (Sonnet + Opus) judged the first wording "partly justified", and the conclusions were narrowed: near-uniform rather than "fails like Gemma", generic prompt effect, in-family fit only. A plan for one look at the fresh test2 cells is drafted and waits for G3 and the owner.

**Nov 28: Gemma parity check of the harness (branch `llama`; failed, located).** By the owner's request the new harness scored plain Gemma 2 9B and nine stored adapters on the tune cells, on the A40, to check it reproduces the stored numbers. Mean regret agreed within 0.001 for every arm, but per-case probabilities differed by up to 1.7e-2, far outside the frozen 1e-3. A diagnostic found the whole difference in the last step: the prompts are byte-identical, and reading the same model the old way (soft-cap in float32 on the last position) reproduces the stored numbers to 1e-8, while the harness takes transformers' logits, which soft-cap in bf16. The issue is Gemma-specific (Llama has no soft-cap). As a by-product, Gemma's examples-100 adapters turned out to fail the same planted no-cost case as Llama's, so that Llama 'not replicated' verdict is shared, not new. About 0.35 GPU-hours. The fix is proposed, not made; the Qwen replication waits, as instructed.

## How the work is kept honest

- **Cells, not cases.** A cell is one combination of resale value, price list, seller line and stated cost. Training, tuning and test never share a cell.
- **A control for every claim.** Same-length neutral text, a wrong rule, random directions tuned on the same budget, shuffled labels, "always the cheapest" labels, and model-free baselines such as "always offer 2".
- **Order-averaged readout.** Every answer is scored under all five rotations of the option order.
- **Blind review gates** ([REVIEW_GATES.md](REVIEW_GATES.md)). Before a big run, before a conclusion and before any test set, fresh reviewer agents read only a packet of the relevant files and judge the plan or the result. Their reviews are in [reviews/](reviews/).
- **Rules before results.** Pass rules, decision rules and predictions are committed before the runs they judge. Each locked test set is looked at once.

## Repository map

| Path | What it is |
| --- | --- |
| `demo/floor.py`, [DEMO_RUNBOOK.md](DEMO_RUNBOOK.md) | Stage tool: score a case, change the stated cost, shuffle options, switch the prompt text or a trained add-on on and off; the runbook gives every command and fallback |
| `demo/gen_cases.py`, `demo/gen/` | Case generator, frozen cell lists, locked test sets and their fingerprints, Claude's lessons and labels |
| `demo/gen_lora.py` and its chains | LoRA training arms and controls on the generated data |
| `demo/` (other files) | The fixed-cell ladder: splits, failure checks, text rows, steering vectors and checks, the first LoRA runs |
| `demo/steercheck.py`, [README_DEMO.md](README_DEMO.md) | A reusable recipe for testing whether a steering vector beats a prompt and a constant |
| `demo_out/` | Saved results and reports |
| [RESULTS_LEDGER.md](RESULTS_LEDGER.md) | Every method tried, its control, and a one-line verdict |
| [DEMO_STATUS.md](DEMO_STATUS.md) | Running log of every step and choice |
| `reviews/` | Blind reviews from each gate |
| `harness/`, `tools/`, [TASKS.md](TASKS.md), [MODEL_CHECKS.md](MODEL_CHECKS.md) | Refactor (branch `refactor`): model configs, task interface, solvers, run records, protected scorer, claim and citation checkers; `runs/` holds the run records, [RESULTS_GENERATED.md](RESULTS_GENERATED.md) is generated from them, [CLAIMS.yaml](CLAIMS.yaml) ties README numbers to evidence, [DECISIONS.md](DECISIONS.md) logs choices |
| `refimpl/`, `tests/` | Core game, scoring, best-offer calculation and statistics, with unit tests |
| [PROTOCOL.md](PROTOCOL.md), `registration/` | The separate pre-registered study (see below) |

## Reproducing

Hardware: one 24 GB GPU (an NVIDIA A10G on AWS g5.2xlarge was used). Each case takes about 1.5 seconds on Gemma 2 9B; one LoRA run takes about 40 minutes.

1. Python 3.11 and the pinned packages in `requirements.gpu.lock` (torch 2.4.1, transformers 4.44.2), plus `peft==0.12.0`.
2. Clone [google-deepmind/concordia](https://github.com/google-deepmind/concordia) into `./concordia` at commit `3643ac0466f748b8055b61feb0b7908411f73d84` and use it through `PYTHONPATH`.
3. Accept the Gemma licence on Hugging Face, then run `HF_TOKEN=… python scripts/download_models.py`, which downloads pinned revisions into `./models` and checks every weight file's SHA-256.
4. Set `CUBLAS_WORKSPACE_CONFIG=:4096:8` and `HF_HUB_OFFLINE=1`.
5. Run the tests with `PYTHONPATH=concordia:. python -m pytest -q tests/`, then follow [DEMO_RUNBOOK.md](DEMO_RUNBOOK.md) or [README_DEMO.md](README_DEMO.md).

## The pre-registered study

`PROTOCOL.md`, `refimpl/` and `registration/` also hold a separate pre-registered study: do the reasoning texts of the top three NeurIPS 2024 Concordia contest agents lower regret in this decision, and can an activation direction reproduce the effect? The work above never uses that study's cases (name variants 1 to 14), never imports the contest agents' code, and does not edit its protocol. Contest agent code is not redistributed here.

## Talk

Planned live demo of this work: AI Tinkerers × Walmart, Dallas–Fort Worth Demo Night, December 2, 2026.
