# Teaching Gemma to haggle

Can a small open model be made a better negotiator by changing it internally, with a stronger model as the teacher? This repository tests that on **Gemma 2 9B-it** in a one-shot buying decision from the 2024 Concordia haggling game, where the best offer is computable, so every answer gets an exact score: the profit it leaves on the table (regret).

The work climbs a ladder. Each rung is a complete result on its own, with its controls:

1. **Measure the failure.** Score every decision against the best offer.
2. **Fix it with text.** How much does one sentence in the prompt buy?
3. **Fix it with activation steering.** Can a vector added to the model's activations do what the sentence does?
4. **Fix it in the weights.** Can LoRA training move the sentence's effect into the model, so it works with no sentence?

The full, current numbers are in **[RESULTS_LEDGER.md](RESULTS_LEDGER.md)** (one row per method ever tried, dead ends included) and the running log is **[DEMO_STATUS.md](DEMO_STATUS.md)**.

## What we have found so far

**The failure is real.** Plain Gemma leaves money on the table in 55% of decisions. When the seller states a cost below resale value, it is wrong 97% of the time. Its offer moves only 0.12 coins per coin of stated cost (it should move 1): it mostly offers 2 coins whatever the cost.

**One sentence fixes most of it.** A fixed method paragraph with no numbers cuts regret by 58% on tuning cases (0.71 → 0.30 coins) and by 70% on held-out cells (0.58 → 0.17). Controls do nothing: same-length neutral text, a wrong rule, "only your profit matters" and the bare acceptance rule all leave Gemma where it was. "Always offer 2 coins", which uses no model at all, also beats plain Gemma (0.53), so every fix is compared with it too.

**Steering does not reproduce the sentence.**

- Mean-difference vectors at the decision token, averaged over answer orders (layers 12 to 39), never moved the offer by more than about 0.2 coins while the answer format held.
- Vectors built separately for each answer order do move offers at layers 33 to 39, by up to 1.3 coins. But they behave like a push toward one answer letter: the next order's vector pushes the other way, they match a plain push toward the "1 coin" letter almost exactly, and they still do worse than "always offer 2".
- Patching shows why. The sentence's effect appears only in the last third of the network (none by layer 24, about half by layer 33, all by layer 41) and is specific to each case, so it cancels when averaged into one direction.

The steering hook itself is verified: an exact patch at the last layer reproduces the sentence's output.

**LoRA: in progress.** Safety checks pass (the training path equals the scoring path; an adapter switched off equals plain Gemma exactly). The main test distils the method sentence into the weights and compares it with matched controls (neutral-text and wrong-rule distillation, shuffled labels) on held-out cells, under a pass rule written before training.

All numbers so far are on build and tuning cells. **The test set (18 cells, 72 cases) is locked** and gets one look after every setting is frozen.

## How the work is kept honest

- **Cells, not cases.** A cell is one combination of resale value, seller line and stated cost. Training, tuning and test never share a cell.
- **A control for every claim.** Same-length neutral text, a wrong rule, random directions tuned on the same budget, negated vectors, shuffled labels and model-free baselines.
- **Order-averaged readout.** Every answer is scored under all five rotations of the option order, because position alone changes the top answer in two thirds of cases.
- **Blind review gates** ([REVIEW_GATES.md](REVIEW_GATES.md)). Before a big run, before a conclusion and before the test set, fresh reviewer agents read only a packet of the relevant files and judge the plan or the result. Their reviews are kept in [reviews/](reviews/).
- **Rules written before results.** Pass rules and decision rules are committed before the runs they judge.

## Repository map

| Path | What it is |
| --- | --- |
| `demo/` | The ladder: splits, failure checks, text rows, steering vectors and checks, LoRA, the stage tool |
| `demo/floor.py` | Live tool: score a case, change the stated cost, shuffle options, switch text, steering or adapter on and off |
| `demo/steercheck.py`, [README_DEMO.md](README_DEMO.md) | A reusable five-step recipe for testing whether a steering vector beats a prompt and a constant |
| `demo_out/` | Saved results (per-case scores, scans, LoRA progress) |
| [RESULTS_LEDGER.md](RESULTS_LEDGER.md) | Every method tried, its control, and a one-line verdict |
| [DEMO_STATUS.md](DEMO_STATUS.md) | Running log of every step and choice |
| `reviews/` | Blind reviews from each gate |
| `refimpl/`, `tests/` | Core game, scoring, oracle and statistics, with unit tests |
| [PROTOCOL.md](PROTOCOL.md), `registration/` | A separate, pre-registered study of the top three NeurIPS 2024 Concordia contest agents (see below) |

## Reproducing

Hardware: one 24 GB GPU (an NVIDIA A10G on AWS g5.2xlarge was used). Each case takes about 1.5 seconds on Gemma 2 9B.

1. Python 3.11 and the pinned packages in `requirements.gpu.lock` (torch 2.4.1, transformers 4.44.2), plus `peft==0.12.0` for the LoRA runs.
2. Clone [google-deepmind/concordia](https://github.com/google-deepmind/concordia) into `./concordia` at commit `3643ac0466f748b8055b61feb0b7908411f73d84` and use it through `PYTHONPATH`.
3. Accept the Gemma licence on Hugging Face, then run `HF_TOKEN=… python scripts/download_models.py`, which downloads pinned revisions into `./models` and checks every weight file's SHA-256.
4. Set `CUBLAS_WORKSPACE_CONFIG=:4096:8` and `HF_HUB_OFFLINE=1`.
5. Run the tests with `PYTHONPATH=concordia:. python -m pytest -q tests/`, then follow [README_DEMO.md](README_DEMO.md) step by step.

Scoring is deterministic: repeated runs give bit-identical results.

## The pre-registered study

`PROTOCOL.md`, `refimpl/` and `registration/` also hold a separate pre-registered study: do the reasoning texts of the top three NeurIPS 2024 Concordia contest agents lower regret in this decision, and can an activation direction reproduce the effect? The demo work never uses that study's cases (name variants 1 to 14), never imports the contest agents' code, and does not edit its protocol. Contest agent code is not redistributed here; it is downloaded from the NeurIPS supplementary archive and verified by SHA-256.

## Talk

Planned live demo of this work: AI Tinkerers × Walmart, Dallas–Fort Worth Demo Night, December 2, 2026.
