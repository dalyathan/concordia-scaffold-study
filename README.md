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
| C1 | What to train on | Rules, worked examples or answers? | 🟡 Examples beat rule-trained students by about 0.3 at N = 25 and 100 (tune, Nov 24, G2 partly justified); the gap is oracle labels vs the paragraph's own behaviour, not shown to be about content alone |
| C2 | | Soft or hard training targets? | 🟡 With the paragraph as content, hard vs soft differ by about 0.03, inside seed noise (single seeds); no examples-soft arm yet |
| C3 | | How many examples are needed? | 🟡 25 cells reach within 0.05 of 100 (0.042 vs 0.032 on tune, one subset draw); 10 is borderline (0.092, seed spread 0.054–0.151) |
| C4 | | Where does the trained model still fail, and does targeted data fix it? | 🟡 Lead from exploring tune results (Nov 24, not a claim): the worked-examples adapter loses 0.008–0.011 coins per decision when a cost is stated but 0.077 when it is hidden, rising with resale value (0.21 at resale 8); all 9 of its hidden-cost errors are offers that are too low. Targeted-data experiment designed, not run |
| D1 | What the teacher adds | With few examples, do a teacher's examples or explanations beat plain answers? | ❌ Open |
| D2 | | Does a teacher that sees the student's internals fix it better? | ❌ Open: the novel experiment |
| D3 | | Does teaching work on a task with no calculable answer (multi-round haggle)? | ❌ Open |
| E1 | Real behaviour | Does the fix reach written answers? | ❌ Open: first priority |
| E2 | | Multi-round negotiation | ❌ Open |
| E3 | | The seller role and side effects | ❌ Open |
| F | Transfer | New values, price grids and wording | ✅ Passed |
| F | | Other models (Llama 3.1 8B) | 🟡 Predictions written (LLAMA_PREDICTIONS.md, Nov 24); no Llama code yet |
| G | Infrastructure | Move from AWS to a RunPod pod without losing artifacts | ✅ Backup in the private HF repo verified (392/392 files, 51/51 adapters, Nov 24); pod set up on a RunPod A40 (Nov 24) |
| G2 | | Do the numbers reproduce on the A40? | 🟡 Not bit for bit on the generated dataset: tune soft regret moves ≤ 0.004 overall (≤ 0.007 per type) and some 3-decimal numbers change (plain 0.657 → 0.661); no reported ordering changes; original dataset identical; likely a size-dependent GPU kernel choice (HARDWARE_PARITY.md, G2 partly justified, Nov 24). Demo startup check still fails on the A40 (tolerance policy left to the owner) |

Pruned: baking the vector into a bias (convenience, not knowledge), steering side effects (moot), reasoning pairs for steering, and the contest winners' reasoning (it belongs to the separate pre-registered study below).

## History

**Nov 20–21: the harness.** Reworked the Concordia haggling game into one buying decision with an exact best offer. Moved from CPU to one NVIDIA A10G on AWS; repeated scoring is bit-identical. Baseline on 140 cases: plain Gemma loses money in 55% of decisions.

**Nov 21: is the failure real, and what does a sentence buy?** The failure is about pricing, not answer position (position explains about 15% of choices). One method sentence cuts losses by 58% on tuning cases; matched control texts do nothing. Blind review gates were added to the process (see below).

**Nov 21–22: steering.** Three tuning runs were stopped and redesigned: the first was mis-scaled, the second too weak, and a dose scan showed the positive control failed. A final-layer patch proved the steering code was correct. Vectors built per answer order did move offers at layers 33–39, but only as a push toward one answer letter. Patching located the sentence's effect: case-specific and late. Steering was closed for this failure.

**Nov 22: training the sentence in.** The first loss function let the adapter dodge the answer format (letter mass fell to 1%); it was caught after one epoch and replaced. Training on the correct answers reached zero held-out loss. The distilled sentence missed its development pass rule by 0.003 against the wrong-rule control; follow-up runs matched seeds and learning rates. One look at the locked test set: **SUPPORT**. Free-text answers got worse.

**Nov 22: a larger generated dataset and Claude as teacher.** A generator built 300 training and 42 tuning cells plus two locked test sets (same-range, and harder: new resale values, price grids and seller wording). A blind Claude wrote a lesson from Gemma's mistakes; one round of feedback improved it (loss 0.43 → 0.25 on its feedback cells), a second round made it worse and was rejected by a rule set in advance. Trained in, the lesson became an "offer cheap" knob and did harm on no-cost cases: **not passed**.

**Nov 23: worked examples.** A blind Claude solved the 100 training cases (by script, all correct). Trained on those, Gemma reached 0.03 on tuning cells and its offer followed the stated cost (slope 0.76, as good as the best play). One look at both generated test sets: **passed** on both, and on each harder slice.

**Nov 23: the demo and what's next.** The stage tool now switches the trained add-ons on and off live; a precision bug in loading several adapters was found and fixed; free text was checked and ruled out as stage evidence; every beat is recorded for replay. Two new locked test sets of 120 cells each were generated for the next experiments. A learning-curve experiment (rules vs examples at matched data, soft vs hard targets) is running, with its predictions committed before the runs.

**Nov 24: hardware parity, A10G → A40.** The demo's startup check failed on the new RunPod A40, so every stored tune number was rescored there (plain and 51 adapters, 57 GPU-minutes). The original dataset reproduced bit for bit. The generated dataset did not: prompts of 603 tokens or more appear to take a different GPU kernel path (seen on the A40; the A10G side cannot be checked now), and with bf16 logits a tiny difference can move a probability by a few percent. Tune soft regret moved at most 0.004 per arm (0.007 per type), no comparison changed sign, but some three-decimal numbers changed (plain 0.657 → 0.661). Rule: A10G and A40 generated-dataset numbers are not mixed. Review (G2): partly justified; wording tightened and determinism on both GPUs checked.

**Nov 24: where the trained model still fails (exploration).** Every train and tune result was exported to tidy tables for Tableau (`exports/tableau/`, built by `tools/export_tableau.py`; 6,876 scored decisions across 39 setups; the locked test sets are never read). Browsing them showed the worked-examples adapter (100 examples, 3 seeds) is nearly perfect when the seller states a cost (0.008 below resale, 0.011 at or above) but loses 0.077 coins per decision when the cost is hidden, concentrated at resale values 6–9 (0.05–0.21). All 9 of its 84 hidden-cost errors under-offer, and the training set has few such cases (15 of 33 hidden-cost training cells at resale 6–9, 3 at resale 8). These are tune numbers with 2–3 situations per resale value, so they are a lead, not a finding. Next, written before any run: a fresh locked evaluation set weighted towards hidden-cost cases, then targeted data (+30 hidden-cost, high-resale cases) against the same amount of random data at equal training steps, with predictions and a G1 review first.

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
| `demo/app.py` | Clickable web demo (standard library only): a Marketplace-style chat beside the exact context Gemma reads, with the prompt fixes, LoRA adapters (10/25/50/100 examples) and controls; `--fake` runs without a GPU |
| `demo/walkthrough.ipynb` | CPU-only walkthrough of the recorded results |
| `tools/export_tableau.py`, `exports/tableau/` | Tidy CSVs of train and tune results for Tableau or pandas, with a data dictionary and manifest |
| `demo_out/` | Saved results and reports |
| [RESULTS_LEDGER.md](RESULTS_LEDGER.md) | Every method tried, its control, and a one-line verdict |
| [DEMO_STATUS.md](DEMO_STATUS.md) | Running log of every step and choice |
| `reviews/` | Blind reviews from each gate |
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

**Nov 23–24: learning curve and rules vs examples.** Thirteen runs (7.4 GPU-hours) on nested subsets of the 100 training cells. Worked examples: 0.092 at 10 cells, 0.042 at 25, 0.040 at 50, 0.032 at 100 (tune; plain 0.657). Students distilled from the in-prompt rule paragraph stayed at 0.34–0.38 whether the target was soft or its argmax, about 0.3 worse than examples at the same size; a control trained to answer cheap equalled always-cheap. Review said the claim is oracle labels vs the paragraph's behaviour, and that 25 vs 10 rests on one subset draw and three seeds. 23 of 26 mechanical predictions held; examples needed fewer cells than predicted.

**Nov 24: migration prep.** Inventory of everything outside git (adapters 0.96 GB, logs, activation caches; models, venv and concordia are re-creatable), a manifest with sha256 for 392 files, a pod setup script that pins torch 2.4.1 / transformers 4.44.2 / peft 0.12.0 and reruns the adapter startup check, and a job order for the pod (setup, adapter check, Gemma parity, then the test look). The first upload attempt failed because the token on the machine was read-only; the repo was then filled from outside and re-verified here (392 of 392 files, 51 of 51 adapters). See MIGRATION.md.

`PROTOCOL.md`, `refimpl/` and `registration/` also hold a separate pre-registered study: do the reasoning texts of the top three NeurIPS 2024 Concordia contest agents lower regret in this decision, and can an activation direction reproduce the effect? The work above never uses that study's cases (name variants 1 to 14), never imports the contest agents' code, and does not edit its protocol. Contest agent code is not redistributed here.

## Talk

Planned live demo of this work: AI Tinkerers × Walmart, Dallas–Fort Worth Demo Night, December 2, 2026.
