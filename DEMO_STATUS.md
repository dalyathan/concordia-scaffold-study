# Demo status

Date: 2026-11-22. Instance after the restart: AWS g5.2xlarge (one NVIDIA A10G, 24 GB; 8 vCPUs; 30 GiB RAM shown by `free -g`). Branch `demo`, built on `stage1-wip`.

**Summary.**

- Gemma 2 9B works end to end through the scoring and steering path on the A10G.
- Every check in step 3 passed. The worst-case prompt (about 4,500 tokens) fits, with a peak of 20.56 GiB.
- The 140-case demo baseline ran on 9B in 3.4 minutes.
- Plain Gemma has non-zero regret in **55%** of cases, above the 30% bar.
- Its failures concentrate where the seller states a cost below the resale value (97% wrong).
- Wrong offers are too high twice as often as too low (52 vs 25).
- Nothing blocks the demo.

## 1. Tidy-up (logged choices)

**What finished before the restart:**

- Stage 1 (committed earlier);
- the scoring-noise check (`logs/check_scoring_noise.json`, finished 10:50);
- the bank-based agent check;
- the generation-memory check.

**What did not run:** the queued generation-ceiling probe, the 9B smoke rerun and the scoring-orders rerun had not started when the instance stopped. They left no output files, so there was nothing partial to delete. `scripts/dry_run_pipeline.py` was written but never run.

**Disk** (80% used, 30 GB free):

| Path | Size |
| --- | --- |
| `~/.cache/uv` | 28 GB |
| repository (`models/` 23 GB, `.venv` 5.9 GB) | 29 GB |
| `~/.vscode-server` | 3.7 GB |
| `~/.cache/warp_test_tmp` | 3.8 GB |
| `~/research` | 2.6 GB |

- The Hugging Face cache is empty, because the models were downloaded only into `./models`. There are therefore no duplicate model downloads to delete.
- `uv cache prune` removed only unreferenced entries: 11,921 files, 22.6 MiB.
- The rest of the uv cache is referenced by installed environments. It and the other projects' caches were left alone, because they may belong to other work and the remaining 30 GB is ample (this demo writes 42 MB).
- Nothing else was deleted.

## 2. Saving the work

- All work in progress was committed as `24cb876` and pushed to the new branch **`origin/stage1-wip`**. Plain `git push` had no HTTPS credentials, so the push used `gh`'s stored login as a one-off credential helper; git config was not changed.
- The demo is committed on branch **`demo`**, from `stage1-wip`.

## 3. Gemma 2 9B through the scoring and steering path

Loading: `device_map={"": 0}`, `low_cpu_mem_usage=True`, bf16, eager attention, one model per process. No process imported `agent_py_files`.

`tests/smoke_gemma.py 9b --device cuda` scores the five answer sequences one at a time (`sequential=True`). Results (`logs/demo_smoke_gemma_9b.log`):

| Check | Result |
| --- | --- |
| Model config (42 layers, hidden 3,584, soft-caps 50/30) | **pass** |
| Positions P2 `(`, P3 end of seller line, P4 "5 coins back"; capture at all 42 layers | **pass** |
| Same prompt scored twice: identical scores and first-token probabilities, hence identical offers | **pass** (bit-identical) |
| Zero steering vector at layer 6: probabilities unchanged | **pass** (bit-identical, first-token and whole-answer) |
| Large steering vector (4 × the layer-6 P1 activation): probabilities change | **pass** |
| Greedy `sample_text` repeatable, stops at terminator; `sample_choice` | **pass** |
| Batched versus sequential whole-answer scores (reported, not a gate) | max difference 0.34 nats, same argmax |
| First-token distribution: P1 pass versus P1 read from the answer passes | max difference 0.046 nats |
| Wall time including the load; peak resident memory | 2 min 39 s; 5.6 GB |

**Worst-case prompt** (`scripts/check_phase3_memory.py --notes-tokens 3900`, pilot-variant prompt with 3,900 tokens of filler Notes, 4,497 tokens per sequence; one scoring = one P1 pass plus five sequential whole-answer passes, with capture at all layers):

| Mode | Peak GPU memory | Seconds per scoring (6 passes) | Seconds per pass | Repeat bit-identical |
| --- | --- | --- | --- | --- |
| Unsteered | 20.56 GiB (of 22.06) | 19.02 | 3.17 | yes |
| Steered at layer 18 | 20.56 GiB | 19.02 | 3.17 | yes |

Weights take 17.21 GiB. Steering adds no measurable time or memory.

**A related finding from before the restart** (`logs/check_scoring_noise.json`, off-grid prompts only):

- Different numerical routes to the same quantity differ by up to 0.08 coins of soft regret in two-variant cell means, and 0.02 coins on average per prompt. The routes are: the P1 pass versus P1 read from sequential or batched answer passes, and sequential versus batched whole-answer scoring.
- Within one fixed route, results are bit-identical.
- This matters for small effects in the registered study, not for this demo, whose regrets are an order of magnitude larger.

## 4. Skipped, as instructed

- formative-memory banks;
- Phase 2 agent runs;
- the registration package;
- further protocol edits.

## 5. Demo baseline run

**Cases.** Name variants 15–18, 35 cells each, 140 cases (`refimpl/demo.py`).

- The loader (`demo.demo_prompts`, `demo.DemoPrompt`) raises an error for any variant 1–14. This is unit-tested (`tests/test_demo.py`).
- `core.FEMALE_NAMES` stops at 14, so the demo names come from Concordia v1.8.9's `fruitville_haggling.py` lists (20 names each), at file positions not used by variants 1–14.
- Variants 15–17 take positions 15–17: Opal Apricot / Orion Apricotwood, Sasha Grapevine / Peregrine Grapehill, Quinn Cherryblossom / Quentin Cherrybrook.
- **Choice:** variant 18 takes position 19 (Sage Honeycomb / Silas Honeybrook), not 18. Position 18 would make buyer "Rowan Cranberry" and seller "Rowan Cranberryfield" share a first name in the dialogue.
- Openings follow the experiment's rule, `(variant − 1) mod 5`.

**Scoring** (`scripts/run_demo.py`):

- Plain Gemma 2 9B with no Notes block, through `phase3.score_prompt` over the five cyclic option orders.
- First-token probabilities from the P1 pass alone (`whole_answer=False`), which is all the demo needs.
- Activations are captured at every layer.

**Saved per case** (`demo_out/cases.jsonl`, committed):

- p(k) averaged over the orders;
- the **top offer**: argmax of the averaged p(k), ties to the lower price (a logged choice);
- the expected offer;
- the best offer(s) from `core.oracle_bids`;
- hard regret of the top offer, and soft regret of the averaged p(k);
- whether the top offer is too high or too low;
- the letter mass;
- each order's own top offer.

**Activations:** decision-token (P1) activations at all 42 layers, averaged over the orders, float16, `demo_out/p1_acts.pt` (42 MB; `{pid: [42, 3584]}`; not committed, because `*.pt` is git-ignored). Run log: `logs/demo_run.log`.

**Run:** 9B, 140 cases, 1.45 s per case (5 P1 passes of about 590 tokens), 3.4 minutes in total, peak 17.33 GiB. It ran with nohup inside tmux, and progress was checked only through its log.

### Failure map

The full tables, including V × seller line, are in `demo_out/failure_map.md`.

- Regret is in coins.
- "Too much" means the top offer is above every best offer; "too little" means below every best offer.
- The last column is the expected offer minus the mean best offer.

**Overall**

| Cases | Mean hard regret | Mean soft regret | Non-zero hard regret | Too much | Too little | Mean (expected − best) |
| --- | --- | --- | --- | --- | --- | --- |
| 140 | 0.621 | 0.618 | **55%** | 52 | 25 | +0.32 |

**By resale value V**

| V | Cases | Mean hard regret | Mean soft regret | Non-zero | Too much | Too little | Expected − best |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | 28 | 0.343 | 0.366 | 25% | 7 | 0 | +0.60 |
| 3 | 28 | 0.250 | 0.293 | 21% | 5 | 1 | +0.34 |
| 4 | 28 | 0.443 | 0.462 | 50% | 10 | 4 | +0.25 |
| 5 | 28 | 0.871 | 0.792 | 79% | 16 | 6 | +0.40 |
| 6 | 28 | 1.200 | 1.177 | 100% | 14 | 14 | +0.03 |

**By seller line**

| Line | Cases | Mean hard regret | Mean soft regret | Non-zero | Too much | Too little | Expected − best |
| --- | --- | --- | --- | --- | --- | --- | --- |
| neutral | 20 | 0.100 | 0.120 | 35% | 4 | 3 | +0.32 |
| pressure | 20 | 0.200 | 0.156 | 55% | 10 | 1 | +0.54 |
| information (stated cost) | 100 | 0.810 | 0.810 | 59% | 38 | 21 | +0.28 |

**By stated cost C** (information cases)

| C | Cases | Mean hard regret | Mean soft regret | Non-zero | Too much | Too little | Expected − best |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 20 | 1.150 | 1.195 | 100% | 20 | 0 | +1.19 |
| 2 | 20 | 1.200 | 1.146 | 75% | 14 | 1 | +0.99 |
| 3 | 20 | 0.900 | 0.916 | 60% | 4 | 8 | −0.09 |
| 4 | 20 | 0.600 | 0.592 | 40% | 0 | 8 | −0.53 |
| 5 | 20 | 0.200 | 0.202 | 20% | 0 | 4 | −0.18 |

**By case type**

| Type | Cases | Mean hard regret | Mean soft regret | Non-zero | Too much | Too little |
| --- | --- | --- | --- | --- | --- | --- |
| no information about cost | 40 | 0.150 | 0.138 | 45% | 14 | 4 |
| stated cost C < V | 60 | 1.333 | 1.307 | **97%** | 37 | 21 |
| stated cost C ≥ V | 40 | 0.025 | 0.064 | 2% | 1 | 0 |

**Reading the map.**

- **Is regret non-zero in at least 30% of cases? Yes: 77 of 140 cases (55%).**
- **Gemma mostly offers too much.** Of the 77 wrong top offers, 52 are above every best offer and 25 below. The expected offer exceeds the best offer by 0.32 coins on average.
- The worst cases are a **stated cost below the resale value**, where the answer is simply "offer the stated cost". Here plain Gemma is wrong 97% of the time:
  - With a low stated cost (C = 1, 2) it overpays. It anchors on 2–4 coins: 2 coins is the top offer in 76 of 140 cases overall.
  - With C = 3, 4 it often offers *below* the stated cost, an offer the seller refuses, so the whole margin V − C is lost.
- Regret rises with V because the margins at stake grow. Every V = 6 case is wrong.
- When the stated cost is at or above V, almost any low offer is optimal, so regret is near zero.
- Under pressure, Gemma overbids more often than with the neutral line (55% vs 35% non-zero).

**Other observations.**

- The mean letter mass at P1 is 0.64.
- The top offer is the same in all five option orders in only 33% of cases, a clear option-order effect. This is why averaging over orders matters.

## 6. Blocking issues

- **Nothing blocks the demo.**
- **For later work:**
  - `scripts/dry_run_pipeline.py` has not been run.
  - `REFERENCE.md` on `stage1-wip` was not rebuilt after the last code changes (`scripts/build_reference.py`).
  - Generation on 24 GB still runs out of memory for prompts of about 4,100 tokens or more, which matters for native Phase 1 games. Phase 2 prompts seen so far reach 2,947 tokens and fit.

---

# Demo plan, part 2 (2026-11-22)

Rules followed throughout:

- No name variant 1–14 is used; `agent_py_files` is never imported; PROTOCOL.md is not edited.
- First-token probabilities are averaged over the five option orders.
- Interventions run on tuning cases only; test cases get plain scoring only.

## Step 1: split by cell — done

- **Rule** (`demo/common.py::case_split`, written by `demo/make_splits.py` to `demo/splits.json`):
  - development cells (`core.steering_cell_split == "dev"`, 17): variants 15–16 are **build** (34 cases), 17–18 are **tuning** (34);
  - test cells (18): all four variants are **test** (72).
  - The saved results were reused; nothing was rescored.
- **Live case: `v15-V3-information-C1`** (V = 3, stated cost 1; the first test case in `demo.demo_prompts()` order with a stated cost below resale and non-zero plain hard regret).
- **Failure map per split** (`scripts/demo_failure_map.py --split <name>` → `demo_out/failure_map_{build,tuning,test}.md`):

| Split | Cases | Mean hard regret | Mean soft regret | Non-zero hard regret | Too much | Too little |
| --- | --- | --- | --- | --- | --- | --- |
| build | 34 | 0.729 | 0.699 | 56% | 10 | 9 |
| tuning | 34 | 0.694 | 0.714 | 62% | 15 | 6 |
| test | 72 | 0.536 | 0.534 | 51% | 27 | 10 |

In the test split, stated cost below resale is non-zero in 24 of 24 cases (mean hard regret 1.417), no cost in 50%, and cost at or above resale in 4%.

## Step 2: is the failure real? (plain model only) — done

The GPU job is `demo/step2_run.py` (`logs/demo_step2.log`); the analysis is `demo/step2_report.py` (→ `demo/step2.json`). Rescoring all 140 cases reproduced the saved order-averaged probabilities exactly (max difference 0).

**Regression of the order-averaged expected offer** (all 140 cases, plain):

| Case type | n | Slope on stated cost (ideal 1) | Slope on resale value | Intercept | R² |
| --- | --- | --- | --- | --- | --- |
| cost below resale | 60 | **0.12** | 0.14 | 1.73 | 0.23 |
| cost at or above resale | 40 | **0.21** | 0.21 | 0.89 | 0.49 |
| no cost | 40 | — | 0.40 | 0.85 | — |

**The failure is real.** Gemma's expected offer moves only 0.12 coins per coin of stated cost, where it should move one-for-one. It barely uses the stated cost.

**Variance split** (choice):

- **Method.** Per case, a Latin-square ANOVA on the 5 orders × 5 positions of first-token log-probabilities, renormalised over the letters. Treatment = price, columns = option position, rows = order (removed).
- **Result.** Pooled over cases, of the variance not due to the order: **price content 74.7%, option position 14.6%**, residual 10.7%.
- The median case's price share is 77%. Position dominates the price in 10 of 140 cases.
- **Choice:** the saved run kept only order-averaged probabilities, so the per-order scores came from the rescore, which is identical.

**Greedy generation** (`scoring.say`):

- **Format.** The decision prompt without the option list, ending "Answer: {buyer} would propose"; text system, greedy, `max_tokens` 16. The first number 1–5 or number word is parsed.
- **Result.** All 140 parsed. The free-text offer agrees with the first-token top choice in **76 of 140 (54%)**. The mean regret of the free-text offer is 0.54 (first-token: 0.62). 0.86 s per case.
- **Choice:** the free-text format tests whether the multiple-choice readout reflects what the model says unprompted by options. Generating after "Answer: (" would only re-read the same first-token distribution.

**Cost dial** (`demo/dial_cost.json`): six build cases, only the stated cost changed to 1, 2, 3, 4 and none; "none" uses the neutral seller line (a logged choice).

- The first run's case list had two pairs that became identical prompts once the cost was overridden (same variant and V). It was rerun with six distinct prompts: distinct (variant, V), V + C odd so all are development cells (`demo/step2_run.py --only-dial`, `logs/demo_step2_dial.log`).

Each cell shows the top offer (E = expected offer; best = best offer(s)):

| Case | cost 1 | cost 2 | cost 3 | cost 4 | none |
| --- | --- | --- | --- | --- | --- |
| v15-V3-information-C2 | 2 (E 2.01; best 1) | 1 (E 2.35; best 2) | 2 (E 2.00; best 1,2,3) | 2 (E 2.01; best 1,2,3) | 2 (E 1.90; best 1,2) |
| v15-V4-information-C1 | 2 (E 2.06; best 1) | 3 (E 2.98; best 2) | 2 (E 2.01; best 3) | 2 (E 2.36; best 1,2,3,4) | 2 (E 2.25; best 2) |
| v15-V5-information-C2 | 2 (E 2.07; best 1) | 4 (E 3.48; best 2) | 2 (E 2.53; best 3) | 2 (E 2.37; best 4) | 2 (E 2.51; best 2,3) |
| v15-V6-information-C1 | 2 (E 2.15; best 1) | 4 (E 3.38; best 2) | 2 (E 2.56; best 3) | 2 (E 2.32; best 4) | 2 (E 2.64; best 3) |
| v16-V4-information-C3 | 2 (E 2.02; best 1) | 3 (E 2.92; best 2) | 2 (E 2.01; best 3) | 2 (E 2.31; best 1,2,3,4) | 2 (E 2.25; best 2) |
| v16-V6-information-C3 | 2 (E 2.05; best 1) | 4 (E 3.46; best 2) | 2 (E 2.77; best 3) | 2 (E 2.20; best 4) | 2 (E 2.92; best 3) |

Gemma offers **2 coins at every stated cost except 2**:

- cost 1: it overpays;
- cost 3 or 4 with V above the cost: it offers below the cost, so the seller refuses;
- **stated cost 2: it bids above the cost** (3–4 coins, 1 in the V = 3 case).

The dial makes the slope-0.12 finding concrete: the stated cost barely moves the offer, except that a stated 2 pushes it up, away from 2.

**Reworded scaffold** (`scoring.reworded_user_turn`: every sentence reworded, same facts, same options; plain, all 140 cases):

| Split | Case type | n | Reworded hard | Reworded soft | Original hard | Original soft | Same top offer |
| --- | --- | --- | --- | --- | --- | --- | --- |
| build | all | 34 | 0.647 | 0.715 | 0.729 | 0.699 | 41% |
| tuning | all | 34 | 0.676 | 0.703 | 0.694 | 0.714 | 56% |
| test | all | 72 | 0.636 | 0.579 | 0.536 | 0.534 | 57% |
| all | cost below resale | 60 | 1.350 | 1.293 | 1.333 | 1.307 | 55% |
| all | cost at or above resale | 40 | 0.100 | 0.144 | 0.025 | 0.064 | 50% |
| all | no cost | 40 | 0.145 | 0.164 | 0.150 | 0.138 | 52% |
| all | all | 140 | 0.649 | 0.642 | 0.621 | 0.618 | 53% |

Rewording leaves the failure intact: overall regret is 0.649 versus 0.621, and cost below resale stays the worst. But it changes the top offer in about half the cases. The aggregate failure is robust; individual picks are fragile.

## Step 3: `demo/floor.py`, the stage tool — done

- **Modes and commands.** `--serve [--model 9b|2b]` loads once and reads commands from stdin: `case`, `cost`, `shuffle`, `plain`, `text`, `steer`, `adapter`, `say`, `table`, `dial <cases.json>` / `dial show`, `help`, `quit`. `--map` prints the failure map; `--replay <log>` replays a session under a "RECORDED RUN" banner.
- **Logging.** Every `--serve` session writes `logs/floor_<time>_<model>.jsonl`.
- **Projector limits.** Output is cut to 80 visible columns, and every command's screen stays within 25 lines. Colour (ANSI) appears only on the regret value: red above 0, green at 0. Cost and resale are marked `>>…<<` instead of coloured.
- **Speed.** Prompt rendering, tokenisation, the P1 index and every scored result are cached.
- **Concurrency.** One model lock serialises the background `dial` thread and the live commands, because steering hooks are global to the model.
- **Command parser** (`floor.parse_command`): rejects unknown commands, wrong arguments and any case id from variants 1–14.
- **`steer <config.json>`** accepts `{"name", "layer", "alpha"[, "vectors"]}` for a saved vector (`demo_out/vectors.pt`), or `{"random_seed", "norm", "layer", "alpha"}` for a seeded Gaussian direction. The second form works on any model size; it was added so 2B could be checked before the step 5 vectors existed.
- **`adapter on`** prints "no adapter yet".

**Choices:**

- `shuffle` draws a random non-cyclic order (seeded) and compares that order's pick with the order-averaged pick.
- `say` uses the step 2 free-text format.
- `text` rows come from `demo/textrows.py`.
- `dial show` lists offer against best offer per case, with the best constant shift (`analysis.tilt`, beta grid ±6) fitted on the dial's cases beside it.
- `table` comes from `steercheck.format_session_table`.

**Check session** (`demo/configs/floor_check.txt`):

- `case`, `cost`, `shuffle` and `say` on the live test case;
- `text`, `steer`, `adapter` and `dial` on tuning cases only;
- a bad command;
- a registered case id, which is refused.

| Command | 9B seconds | 2B seconds |
| --- | --- | --- |
| model load (warm page cache) | 5 | 42 (cold) |
| `case` (5 orders) | 1.74 | 0.81 |
| `cost 3` / `cost none` | 1.39 / 1.38 | 0.46 / 0.46 |
| `shuffle` (one order) | 0.28 | 0.09 |
| `say` | under 2 | 0.91 |
| `text method` (plain + text, side by side) | under 3 | 1.01 |
| `steer` (random direction, layer 12) | 4.15 | 1.37 |
| `dial show`, `table`, `plain` (cached) | ≤ 0.7 | ≤ 0.25 |

Every live command returned in under 5 seconds on 9B, and both models work (`logs/demo_floor_check_{9b,2b}.log`).

Fixed after the first check:

- truncation and padding now count visible columns, so ANSI codes no longer cut the `table` seconds column or misalign the side-by-side panels;
- `help` lines fit 80 columns;
- `say` spacing.

A confirming 9B rerun is queued after the GPU jobs (`logs/demo_floor_check_9b_r2.log`).

**Process note:** the step 2 commit already contained the in-progress files for later steps (`floor.py`, `steercheck.py`, `textrows.py`, `pairs_template.py`, `direction.py`, `step4_run.py`). They were written while the GPU ran and are completed and reported in their own steps.

## Step 4: text rows (tuning cases only) — done

- **Job.** `demo/step4_run.py` (`logs/demo_step4.log`, 7 minutes, 34 tuning cases × 8 rows × 5 orders); report `demo/step4_report.py` → `demo/step4.json`. Row texts are frozen in **`demo/text_rows.json`**.
- **Method paragraph** (`textrows.METHOD`): one fixed text with no digits. Its rule, executed literally (`textrows.method_offer`), gives a best offer (`core.oracle_bids`) in all 49 cells (V = 2–8, all three case types). The check passed before the text was frozen.
- **Rows:**
  - same-length neutral = `conditions.qa_filler` cut to the method's token count;
  - template reasoning = `pairs_template.paragraph(case, smallest best offer)`;
  - answer-only = `core.answer_only(buyer, smallest best offer)`, an **upper bound**.
  - Rows are inserted as the Notes block. Case means are used; each tuning cell has exactly two cases, so these equal cell means.

| Row | Soft regret: cost < resale | cost ≥ resale | no cost | all | Hard regret (all) | Non-zero (all) | Letter mass |
| --- | --- | --- | --- | --- | --- | --- | --- |
| plain | 1.256 | 0.085 | 0.125 | 0.714 | 0.694 | 62% | 0.63 |
| method | 0.494 | 0.101 | 0.075 | **0.303** | 0.288 | 21% | 0.89 |
| same-length neutral | 1.246 | 0.033 | 0.087 | 0.688 | 0.600 | 50% | 0.54 |
| wrong rule ("Offer half the stated cost.") | 1.285 | 0.006 | 0.030 | 0.688 | 0.765 | 53% | 0.69 |
| disposition ("Only your own profit matters.") | 1.322 | 0.103 | 0.098 | 0.747 | 0.659 | 50% | 0.50 |
| acceptance rule | 1.206 | 0.093 | 0.176 | 0.702 | 0.635 | 59% | 0.52 |
| template reasoning (names the best offer) | 0.001 | 0.001 | 0.000 | 0.001 | 0.000 | 0% | 0.97 |
| answer-only (**UPPER BOUND**) | 0.024 | 0.000 | 0.000 | 0.013 | 0.000 | 0% | 0.92 |

**Prompt ceiling for a fixed text:** the method paragraph cuts soft regret by 58% (0.714 → 0.303). Almost all of the gain is in the cost-below-resale cases (1.256 → 0.494), and the letter mass rises to 0.89.

The controls show that the content does the work:

- neutral text of the same length: 0.688;
- the wrong rule: 0.688;
- the bare acceptance rule: 0.702;
- the disposition: slightly worse than plain (0.747).

Text that states the answer for the case takes regret to about 0, which is the ceiling a vector would have to approach.

## Step 5: pairs and directions (no Claude) — done

**Template pairs** (`demo/pairs_template.py` → `demo/pairs_template.json`):

- 34 build cases, none skipped. No build cell has every offer optimal; that cell, V = 5 and C = 5, is a test cell.
- One template for all case types; only the facts and the concluded offer vary, and the arithmetic for the concluded offer is stated truthfully.
- Good concludes a best offer. Bad concludes the offer just above or below the best set, chosen greedily to balance direction and mean price.

| Check | Result |
| --- | --- |
| token lengths within 10% | **pass** (ratio 1.00 for every pair) |
| bad above / below | **18 / 16** |
| mean concluded price, good / bad | **2.65 / 2.59** (within 0.25: pass) |
| offer-lower pairs (positive control): 34 pairs, A one coin below B, same template | **pass** (lengths ratio 1.00) |

**Directions** (`demo/direction.py`, `logs/demo_step5.log`) → `demo_out/vectors.pt` and `demo/directions.json`:

- P1 activation at every layer, averaged over the five orders, with the paragraph as the Notes block.
- template = mean(good − bad) and offer_lower = mean(A − B), on build cases.
- sentence = mean(method − neutral), on the step 4 tuning activations.
- Each also with the option-letter span removed (`pipeline.project_out_letters`, which rescales to the original norm).

| Vector | Pairs | Norm / mean residual norm, layers 6, 12, 18, 24 | Mean pairwise cosine of per-case differences, same layers | cos(vector, letter-projected vector), same layers |
| --- | --- | --- | --- | --- |
| template | 34 | 0.003, 0.003, 0.006, 0.027 | 0.189, 0.085, 0.053, 0.131 | 0.999, 0.999, 1.000, 0.998 |
| offer_lower | 34 | 0.002, 0.003, 0.010, 0.030 | 0.075, 0.162, 0.256, 0.238 | 0.998, 0.999, 1.000, 1.000 |
| sentence | 34 | 0.094, 0.153, 0.284, 0.290 | 0.996, 0.992, 0.995, 0.981 | 1.000, 0.999, 1.000, 0.997 |

**Reading:**

- **Template.** The vector is tiny: 0.3–2.7% of the residual norm at the tuning layers. Its per-case differences barely agree (cosine 0.05–0.19). The good-minus-bad difference is mostly case-specific, so the mean direction is weak.
- **Offer-lower.** The positive control is as small, but more consistent (cosine up to 0.27).
- **Sentence.** Large and almost identical across cases, because the same text is inserted every time.
- **Letter span.** The option-letter unembedding span is a negligible part of every vector (cosine with the projected version ≥ 0.997).

## Step 6: offline baselines (fitted on tuning cases) — done

`demo/baselines.py` → `demo/baselines.json`. These are fitted on the plain distributions of the 34 tuning cases. Means are over cells. Grids: beta −6 to 6 in steps of 0.05; lam 0 to 1 in steps of 0.02. Ties go to the smaller |beta| or lam.

| Baseline | Parameter | Soft regret | Hard regret | cost < resale | cost ≥ resale | no cost |
| --- | --- | --- | --- | --- | --- | --- |
| plain | — | 0.714 | 0.694 | 1.256 | 0.085 | 0.125 |
| constant shift (`analysis.tilt`) | best beta = −0.85 | 0.669 | 0.676 | 1.225 | 0.012 | 0.076 |
| constant offer 1 (`analysis.attractor`, lam = 1) | — | 0.635 | 0.635 | 1.111 | 0.000 | 0.200 |
| **constant offer 2** | — | **0.529** | 0.529 | 1.000 | 0.000 | 0.000 |
| constant offer 3 | — | 0.694 | 0.694 | 1.111 | 0.250 | 0.200 |
| constant offer 4 | — | 1.306 | 1.306 | 1.778 | 0.750 | 0.800 |
| constant offer 5 | — | 2.306 | 2.306 | 2.556 | 2.250 | 1.800 |
| shrink to the middle (`analysis.flatten`) | best lam = 0.00 | 0.714 | 0.694 | 1.256 | 0.085 | 0.125 |

**"Always offer 2 coins" beats plain Gemma** on the tuning cases (0.529 vs 0.714), and so does the best constant shift (0.669). Shrinking towards uniform never helps, so its best lam is 0. A steering vector has to beat these model-free baselines before its gain means anything. The method paragraph (0.303, step 4) does.

## Step 7: tuning job (tuning cases only) — relaunched with strength as a fraction of the residual norm, running

**Why the first launch was stopped.** It used α ∈ {0.5, 1, 2, 4} as a multiplier of each raw vector. The template and offer_lower vectors are only 0.3–2.7% of the residual norm at the tuning layers (step 5), so even α = 4 barely moved them. The sentence vector is 9–29% of the residual norm, so at α = 4 it exceeded 100%. The directions were therefore not compared at equal strength.

- The first job was killed after about 9 minutes, before its first tuning finished.
- Its log is kept as `logs/demo_tune_job_v1.log` (model load only; no results).

**Changes** (`demo/tune_job.py`, `demo/steercheck.py`):

- **Strength = fraction of the mean plain P1 residual norm at that layer.** The norm is the mean over the 34 tuning cases of |h_L| at P1, from `demo_out/p1_acts.pt`; at layer 18 it is 220.7.
- **Equal norm for every direction.** Every direction is normalised to unit length, then multiplied by that norm: template, offer_lower, sentence, the negated template, the 20 random directions and the 5 Gaussian directions. The grid value is then the fraction, so all directions are compared at equal norm.
- **Grid** (29 points, the same for every vector): no steering, plus layers 6, 9, 12, 15, 18, 21, 24 × fractions 0.02, 0.05, 0.10, 0.20.
- **Unchanged:**
  - budgets: full = five orders; matched = one order per case, rotating with the variant;
  - references: random = differences of plain P1 activations between tuning cases from different cells, PCG64 seed 11; Gaussian = seed 12;
  - tuning rule: lowest mean cell soft regret among coherent settings (letter mass ≥ 0.9 × plain), with "no steering" always an option;
  - cell bootstrap, 2,000 resamples;
  - tuning cases only, in-sample.
- **Checkpoint.**
  - Each finished (vector, budget, layer, fraction) point, with every case's order-averaged p(k) and letter mass, is appended to **`demo_out/tune_partial.jsonl`**, flushed and fsynced.
  - `--resume` loads that file and skips the points already there; the chosen setting's evaluation reuses the cached point.
  - A reboot loses at most the grid point being computed, plus about 1 minute to recompute the plain baselines.
  - Without `--resume`, an existing checkpoint file stops the job instead of being overwritten (a logged choice).
  - The launch command passes `--resume`, which behaves as a fresh start when no file exists, so the same command restarts the job.
  - Unit-tested: `test_steercheck_checkpoint_resume_skips_done_points`.
  - `demo_out/tune_partial.jsonl` is git-ignored, because it changes constantly while the job runs; it lives on local disk, which survives a reboot.

**Sanity check before launch** (`demo/tune_job.py --sanity`, `logs/demo_tune_sanity.log`, `demo_out/tune_sanity.json`): 4 tuning cases (v17-V2-information-C1, C3, C5, v17-V3-neutral), offer_lower at layer 18.

| Direction | Fraction | Mean change in expected offer | Should | As expected | Per case |
| --- | --- | --- | --- | --- | --- |
| offer_lower | 0.10 | −0.004 | lower | yes | +0.008, −0.009, −0.013, −0.001 |
| −offer_lower | 0.10 | +0.003 | raise | yes | +0.002, +0.012, −0.003, +0.002 |
| offer_lower | 0.20 | −0.007 | lower | yes | +0.001, −0.010, −0.010, −0.008 |
| −offer_lower | 0.20 | +0.003 | raise | yes | 0.000, +0.010, 0.000, +0.003 |

The signs are right, but the effect is very small: under 0.01 coins even at 20% of the residual norm, and one case moves the wrong way at 0.10. The positive control barely moves the offer at layer 18. The job was launched as instructed.

**Launch.** 04:32, tmux session `tune`, under nohup, with `--resume`. Same pass count as before: about 45,560 passes at about 0.29 s, so **about 3.7 hours**.

**Check commands:**

```bash
grep -v "Loading\|Warn\|warn\|torch.load" logs/demo_tune_job.log | tail -40    # progress; at the end, the table
wc -l demo_out/tune_partial.jsonl                                               # grid points done (840 tuned points in all: 4 x 28 full budget + 26 x 28 matched)
python demo/steercheck.py --results demo_out/tune_results.json                   # the table once finished
```

**Resume after an interruption** (skips finished points):

```bash
tmux new-session -d -s tune "nohup scripts/nonet.sh .venv/bin/python demo/tune_job.py --resume >> logs/demo_tune_job.log 2>&1"
```

## Step 8: teacher packet — done (no API call)

`demo/make_teacher_packet.py` → **`demo/teacher_packet.md`** and `demo/teacher_packet_index.json`.

**What the packet contains:**

- The shared prompt, once, with placeholders. It is rendered from a demo-variant prompt (variant 15, names replaced), never from variants 1–14.
- Only the differing lines (names, resale line, seller's last line) and Gemma's order-averaged offer distribution for every build case with non-zero regret. There are **19** such cases, under the 32 cap.
- No best offers and no regret anywhere.

**What it asks for**, as one JSON object:

- a diagnosis;
- one method paragraph with no case numbers;
- `too_high` / `too_low` / `right` predictions for one variant (variant 15) of each of the **18 test cells**, shown as prompt lines only;
- good/bad paragraph pairs with their concluded offers for the **34 build cases**, under the step 5 constraints.

**`demo/check_teacher.py <response.json>`:**

- Scores the predictions against plain Gemma's actual top offer on those cases.
- Shows two baselines beside it:
  - the majority class: "right" is 10 of 18, so **56%**;
  - the rule "below about 3 coins it overbids, above it underbids", applied to the smallest best offer: **28%**.
- Checks the pairs with the step 5 checks, plus good = a best offer and bad = not a best offer.
- Flags digits in the method paragraph.
- It was verified on a dummy response built from the step 5 pairs: all pair checks pass.
- The true labels for the 18 cases are right 10, too high 4, too low 4.

## Step 9: take-home — done

**`demo/steercheck.py`** is a model-agnostic function plus CLI.

- **Inputs:** `run_controls(score, cases, best, value, cell, vectors, grid, full_orders, matched_orders, reference, negate=…)`.
- **Output:** one control table. It has these rows:
  - plain;
  - each vector and the requested negations, tuned at full budget;
  - the first vector at matched budget, with its rank among the reference directions (random, Gaussian) tuned the same way;
  - the best constant shift (tilt, beta grid ±6).

  Each row carries:
  - the partial Spearman correlation of the per-cell shift in expected option with the best option, given the plain expected option (permutation p), on cells with one best option;
  - cell-bootstrap intervals for regret and its reduction.
- **CLI:** `--toy` runs the self-contained toy problem; `--results <json>` prints a saved table.
- **Where it is used:** step 7's table comes from `run_controls` / `format_table`, and `floor.py`'s `table` command from `format_session_table`.
- **Choice:** `negate` restricts negated copies to the named vectors, because step 7 asks for the negated template only.

**`README_DEMO.md`** is a five-step recipe with one command per step:

1. build an oracle (`demo/make_splits.py`);
2. read out order-averaged choices (`demo/step2_run.py && demo/step2_report.py`);
3. find the prompt ceiling with neutral and wrong-rule controls (`demo/step4_run.py && demo/step4_report.py`);
4. test the vector with steercheck (`demo/direction.py && demo/tune_job.py && demo/steercheck.py --results …`);
5. state the verdict with six explicit criteria (`demo/floor.py --serve`).

## Step 10: tests and report — done

**Unit tests.** `tests/test_demo_tools.py` (10 tests) and `tests/test_demo.py` (3) cover:

- the split: counts, the cell rule, no cell shared with test, and the saved splits and live case;
- the pair balance checks, including that they detect a skewed set;
- the method paragraph check;
- the offline baselines (tilt, attractor, flatten, best shift);
- steercheck on the toy problem (the vector beats plain with a cell-bootstrap interval above 0, its negation does not help, the table fits 80 columns);
- floor.py's command parser (registered ids refused), its screens with a fake engine (≤ 25 lines, ≤ 80 visible columns), the log (replayable, no colour codes) and colour on regret only.

**All tests:** `PYTHONPATH=concordia:. python -m pytest -q tests/` → **51 passed** (registered-study tests included).

## Status of part 2

| Step | Status |
| --- | --- |
| 1 split, live case `v15-V3-information-C1`, per-split maps | done |
| 2 is the failure real | done: cost slope 0.12; price 75% / position 15% of choice variance; free text agrees 54%; dial; reworded |
| 3 floor.py | done: 9B and 2B checked; every live command under 5 s, except one taken while a dial ran (see below) |
| 4 text rows | done: method 0.303 vs plain 0.714 soft regret; neutral, wrong rule, disposition and acceptance rule ≈ plain |
| 5 pairs and directions | done: checks pass; template vector 0.3–2.7% of residual norm, cosine 0.05–0.19 |
| 6 offline baselines | done: always-2 0.529, best shift 0.669 (beta −0.85), flatten no help |
| 7 tuning job | **running**: third launch 05:02 after a dose scan (positive control failed; grid by rule; about 4 hours; check and resume commands under "Step 7, third launch") |
| 8 teacher packet | done (no API call) |
| 9 steercheck and README_DEMO.md | done |
| 10 tests and report | done |

**Open items:**

- **The step 7 results.** When the relaunched job finishes, `demo_out/tune_results.json` and its table (`python demo/steercheck.py --results demo_out/tune_results.json`) give, on tuning cases (in-sample):
  - each vector's tuned setting, regret and reduction with cell-bootstrap intervals;
  - the negated template;
  - the matched template's rank among the 25 reference directions;
  - the best constant shift;
  - the partial Spearman correlations.

  They are not in this report.
- **One live command over 5 seconds.** In the confirming 9B floor rerun, `text wrong_rule` took 5.54 s: it waited for the model lock while a background `dial` scored a five-order case. The dial thread now takes the lock one order at a time (about 0.3 s), so a live command waits at most one pass. This fix is unit-tested but has not been re-timed on 9B, because the GPU is busy with the tuning job.
- **No intervention has touched a test case.** Only plain scoring and the plain-model analyses (step 2) used test cases.

## Step 7, third launch: dose scan first (2026-11-22)

**Why.** The second launch's sanity check showed offer_lower moving the expected offer by under 0.01 coins even at 0.20 of the residual norm, at P1 only. Its grid would mostly have measured nothing.

### 1. Second tuning job stopped — done

- Killed at 04:42, after 10 of 840 grid points (all template, full budget, layers 6–9).
- Kept as `logs/demo_tune_job_v2.log` and `demo_out/tune_partial_v2.jsonl` (committed).

### 2. Positive control "cheap" — done

**Construction** (`demo/cheap_vector.py`, `logs/demo_cheap_vector.log`, 2 minutes): for each of the 34 build cases, the P1 activation (every layer, averaged over the five orders) with `pairs_template.paragraph(case, 1)` as the Notes block, minus the same with `paragraph(case, 4)`; then the average over cases. It means "say 1 coin, not 4" in absolute terms.

- Saved as `cheap`, and `cheap_proj` with the letter span removed, in `demo_out/vectors.pt`.
- Statistics are in `demo/directions.json`.

| Layer | Norm / mean residual norm | Mean pairwise cosine of per-case differences | cos(vector, letter-projected) |
| --- | --- | --- | --- |
| 6 | 0.003 | 0.196 | 0.998 |
| 12 | 0.005 | 0.429 | 0.999 |
| 18 | 0.023 | 0.713 | 1.000 |
| 24 | 0.065 | 0.625 | 1.000 |

Unlike template (cosine 0.05–0.19) and offer_lower (0.08–0.27), the per-case "1 not 4" differences agree strongly from layer 12 onward. The raw vector is still small, but the scan rescales it to a fixed fraction of the residual norm.

### 3. Dose scan — done

`demo/dose_scan.py` → `demo_out/dose_scan.json` (`logs/demo_dose_scan.log`, 15 minutes).

- **Cases:** 8 tuning cases, every fourth tuning case in order: v17-V2-information-C1, v17-V3-pressure, v17-V4-information-C3, v17-V5-information-C2, v17-V6-information-C5, v18-V3-neutral, v18-V4-information-C1, v18-V5-pressure (taken from `dose_scan.json`). Five orders.
- **Vectors:** offer_lower, cheap and sentence, each unit-normalised and scaled to a fraction of the mean plain P1 residual norm at the layer.
- **Layers and fractions:** layers 12, 18, 24; fractions 0.1, 0.25, 0.5, 1.0, 2.0.
- **Two position modes:**
  - "P1 on": the vector is added at P1 and the positions after it;
  - "P3 on": added at every position from P3 (the last token of the seller's final line) onward, through P1. This was added as `scoring.score(steer_from="p3")`.

Plain on the 8 scan cases: expected offer 2.693, soft regret 0.839, letter mass 0.64. Each entry: change in expected offer / soft regret / letter mass relative to plain. **Bold**: coherent (mass ≥ 0.9 × plain).

| Vector | Mode | Layer | f = 0.1 | f = 0.25 | f = 0.5 | f = 1.0 | f = 2.0 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| offer_lower | P1 on | 12 | **-0.001 / 0.84 / 0.92** | -0.002 / 0.84 / 0.79 | +0.001 / 0.85 / 0.56 | +0.017 / 0.86 / 0.22 | +0.044 / 0.89 / 0.07 |
| offer_lower | P1 on | 18 | **+0.002 / 0.84 / 0.97** | +0.000 / 0.84 / 0.89 | -0.002 / 0.84 / 0.76 | -0.007 / 0.84 / 0.66 | +0.024 / 0.86 / 0.45 |
| offer_lower | P1 on | 24 | **-0.022 / 0.83 / 0.99** | **-0.049 / 0.83 / 0.92** | -0.065 / 0.84 / 0.79 | -0.032 / 0.86 / 0.75 | +0.016 / 0.89 / 0.77 |
| offer_lower | P3 on | 12 | +0.027 / 0.86 / 0.78 | +0.073 / 0.89 / 0.49 | +0.079 / 0.94 / 0.21 | +0.389 / 1.13 / 0.02 | +0.227 / 1.16 / 0.00 |
| offer_lower | P3 on | 18 | -0.022 / 0.83 / 0.84 | -0.060 / 0.81 / 0.51 | -0.081 / 0.84 / 0.16 | +0.126 / 1.03 / 0.01 | +0.436 / 1.25 / 0.02 |
| offer_lower | P3 on | 24 | -0.080 / 0.84 / 0.81 | -0.171 / 0.87 / 0.47 | -0.119 / 1.00 / 0.22 | +0.006 / 1.11 / 0.10 | +0.179 / 1.16 / 0.00 |
| cheap | P1 on | 12 | **-0.001 / 0.84 / 0.93** | -0.001 / 0.84 / 0.83 | +0.001 / 0.85 / 0.65 | +0.017 / 0.86 / 0.37 | +0.052 / 0.89 / 0.07 |
| cheap | P1 on | 18 | **+0.000 / 0.84 / 0.97** | -0.002 / 0.84 / 0.87 | +0.005 / 0.84 / 0.67 | +0.001 / 0.85 / 0.37 | +0.031 / 0.88 / 0.22 |
| cheap | P1 on | 24 | **-0.037 / 0.82 / 0.97** | -0.078 / 0.81 / 0.88 | -0.092 / 0.82 / 0.78 | **-0.041 / 0.84 / 1.07** | +0.005 / 0.88 / 0.78 |
| cheap | P3 on | 12 | +0.008 / 0.85 / 0.80 | +0.011 / 0.85 / 0.54 | -0.060 / 0.84 / 0.25 | +0.063 / 0.90 / 0.06 | +0.154 / 1.14 / 0.00 |
| cheap | P3 on | 18 | -0.015 / 0.82 / 0.80 | +0.001 / 0.82 / 0.38 | +0.066 / 0.87 / 0.06 | +0.109 / 1.05 / 0.00 | +0.329 / 1.22 / 0.00 |
| cheap | P3 on | 24 | -0.170 / 0.80 / 0.77 | -0.361 / 0.79 / 0.39 | -0.346 / 0.88 / 0.19 | +0.091 / 1.11 / 0.02 | +0.183 / 1.14 / 0.00 |
| sentence | P1 on | 12 | **+0.002 / 0.84 / 0.95** | +0.004 / 0.84 / 0.83 | +0.010 / 0.85 / 0.64 | +0.015 / 0.85 / 0.51 | +0.026 / 0.86 / 0.40 |
| sentence | P1 on | 18 | **-0.002 / 0.84 / 0.92** | -0.005 / 0.84 / 0.75 | -0.008 / 0.85 / 0.49 | -0.020 / 0.85 / 0.21 | +0.036 / 0.88 / 0.09 |
| sentence | P1 on | 24 | **-0.005 / 0.84 / 0.95** | -0.012 / 0.83 / 0.83 | -0.012 / 0.84 / 0.55 | +0.010 / 0.85 / 0.17 | +0.027 / 0.88 / 0.10 |
| sentence | P3 on | 12 | -0.015 / 0.84 / 0.88 | -0.009 / 0.87 / 0.70 | +0.040 / 0.91 / 0.37 | +0.113 / 0.98 / 0.00 | +0.287 / 1.18 / 0.00 |
| sentence | P3 on | 18 | **+0.060 / 0.86 / 0.97** | +0.172 / 0.94 / 0.78 | +0.219 / 1.03 / 0.14 | +0.233 / 1.15 / 0.00 | +0.284 / 1.19 / 0.00 |
| sentence | P3 on | 24 | **-0.029 / 0.83 / 1.00** | **-0.071 / 0.83 / 0.93** | -0.093 / 0.85 / 0.70 | +0.109 / 1.03 / 0.19 | +0.254 / 1.17 / 0.01 |

### Steering at this setup cannot move offers

> **Superseded by the steering checks and gate G2 below.** This section's claim holds only for order-averaged vectors at P1 up to layer 24. Per-order vectors at layers 33–39 do move the first-token readout (as a letter push), and free-text offers can be moved too.

**The positive control failed.** `cheap` is the steering-vector form of "say 1 coin, not 4". Its per-case differences agree strongly (cosine 0.71 at layer 18). Yet it never lowered the expected offer by more than **0.04 coins** at any coherent setting, in either position mode.

**Evidence from the scan:**

- **P1 on, best coherent setting:** −0.037 at layer 24, fraction 0.1. At layer 24, fraction 1.0, letter mass is 1.07 × plain but the change is only −0.041.
- **P3 on:** `cheap` does lower the offer, by −0.17 at fraction 0.1 and −0.36 at 0.25 (layer 24), and soft regret falls to 0.79. But the letter mass drops to 0.77 and 0.39 × plain. The model stops answering with a letter before the offer moves much.
- **offer_lower and sentence:** the same pattern. Coherent settings move the offer by at most 0.08 coins (sentence, P3 on, layer 24, fraction 0.25: −0.071 with mass 0.93). Larger strengths collapse the letter mass and *raise* the offer and the regret.
- **Comparison with text.** On the full tuning set, the method paragraph as text cut soft regret from 0.714 to 0.303 (step 4), and the step 2 cost dial shows that changing the prompt's facts moves offers. A mean-difference vector added to the residual stream does neither at any coherent strength.

**Conclusion:** with this model, these layers and these directions, steering cannot move offers by a useful amount without breaking the answer format.

### 4. Grid chosen by rule — done

`demo/choose_grid.py` → `demo/tune_grid.json` (`logs/demo_choose_grid.log`).

- **Position mode: P1 on.** The rule takes the mode where `cheap` lowers the expected offer most while coherent: 0.041 in P1 mode; no coherent setting in P3 mode.
- **Fractions: 0.25, 0.5, 1.0, 2.0, the fallback.** Cheap never reached a 0.25-coin decrease while coherent. **Logged: the positive control failed.**
- **Grid:** layers 6, 9, 12, 15, 18, 21, 24 × those 4 fractions + no steering = **29 points**.

**Interpretations, logged:**

- "Moves the expected offer most" is read as the largest *decrease*, since cheap means "say 1, not 4".
- Coherence is mass ≥ 0.9 × plain on the 8 scan cases.

**Expected consequence:** at P1 on, most settings with fraction ≥ 0.25 were incoherent in the scan, so tuning will mostly keep "no steering" (α = 0) for every direction.

### 5. Third tuning job — launched, running

- **Chain:** started automatically after the scan and the grid choice (`dose_scan.py && choose_grid.py && tune_job.py --resume`, tmux session `tune`). The job started at 05:02.
- **Grid and mode:** from `demo/tune_grid.json` (P1 on; fractions 0.25, 0.5, 1.0, 2.0).
- **Directions:** **cheap** is added to the full-budget vectors (template, offer_lower, sentence, cheap, and the negated template). Equal norm for every direction (unit vector × fraction × mean residual norm), checkpoint, `--resume` and the 20 random + 5 Gaussian matched references are unchanged.
- **Size:** 5 × 28 × 34 × 5 + 26 × 28 × 34 ≈ 48,500 passes, about **4 hours** at 0.29 s per pass. That makes 980 tuned grid points (5 × 28 full budget + 26 × 28 matched).

**Check commands:**

```bash
grep -v "Loading\|Warn\|warn\|torch.load" logs/demo_tune_job.log | tail -40   # progress; at the end, the table
wc -l demo_out/tune_partial.jsonl                                              # grid points done, of 980
python demo/steercheck.py --results demo_out/tune_results.json                  # the table once finished
```

**Resume after an interruption** (skips finished points):

```bash
tmux new-session -d -s tune "nohup scripts/nonet.sh .venv/bin/python demo/tune_job.py --resume >> logs/demo_tune_job.log 2>&1"
```

**Superseded.** Step 7's second-launch section above (grid 0.02–0.20) no longer applies. Its sanity check and partial results are kept as `logs/demo_tune_sanity.log` and `demo_out/tune_partial_v2.jsonl`.

## Ledger

**[RESULTS_LEDGER.md](RESULTS_LEDGER.md)** has one row per method or arm ever tried, dead ends included; the same data is in `demo_out/ledger.json`. `python demo/ledger.py` rebuilds both from saved results. It reads files only, on the CPU.

**Columns:**

- demo beat: failure-is-real, one-sentence, inside-the-model or take-home;
- rung: 1 plain readout, 2 model-free baselines, 3 text, 4 steering, 5 LoRA, 0 take-home tool;
- method;
- split, and whether the result is in-sample;
- mean soft regret, with a cell-bootstrap interval where per-case results were saved;
- change vs plain;
- matched control and its regret;
- beats control?;
- wall time;
- verdict (≤ 12 words);
- source file.

Under the table: the three best methods, the three that failed, and slow runs (over 30 minutes) with no signal.

**Choices:**

- **Soft regret** is the mean over cells of per-case soft regret, the unit used throughout.
- **Free-text row** reports hard regret, labelled as such.
- **Dead ends** come from what they left:
  - tune v1: no result, about 9 minutes;
  - tune v2: the best of its 10 checkpointed points, about 10 minutes;
  - the sanity check: change in expected offer only.
- **Dose-scan rows** use each vector and mode's best coherent setting on the 8 scan cases, against plain on the same 8. They have no interval, because per-case results weren't saved.
- **Third tuning job.** While it runs, its rows come from the partial checkpoint, marked RUNNING. Once `demo_out/tune_results.json` exists, they come from it, including each vector's tuned setting, its negation, the matched rank and the reference set.
- **LoRA rows** come from `demo_out/lora_<arm>.json`, scored on tuning cases, with the shuffled-label arm as the control.
- **"Best"** excludes rows that name the answer (template reasoning, answer-only).
- **"Failed"** lists interventions meant to help (rung ≥ 3, not controls) with no useful change (< 0.05 coins better than plain). Dead-end steering runs come first, then the failed positive control.

**Kept current:** `tune_job.py` and `lora.py` call `ledger.py` when they finish. The running tune job loaded its code before that change, so a CPU-only waiter (tmux session `ledgerwait`, `logs/demo_ledger_after_tune.log`) rebuilds the ledger when the `tune` session ends.

**Test:** `tests/test_ledger.py` checks that the ledger runs on the current files and that every row has a source that exists. **53 tests pass.**

## Rung 5: LoRA — queued (starts when the tuning job ends)

**Script:** `demo/lora.py`. **Training data:** build cases only. **Early stopping:** on tuning cases. Test cases and variants 1–14 are never used.

- **Loss (letter-only):** at P1, the full-vocabulary log-probabilities of the five option letters only, against a target distribution over the letters.
- **Arms:**
  - **answer_only:** the target is uniform over the letters of the case's best offers.
  - **template:** context distillation. The target is the model's own first-token letter distribution with the template reasoning paragraph (`pairs_template.paragraph(case, smallest best offer)`) as Notes, computed before training. The adapter learns to reproduce, on the plain prompt, what the model does when it reads the reasoning. This is the logged reading of "template reasoning" as a LoRA arm.
  - **shuffled:** the answer_only targets with the best-offer sets permuted across build cases (PCG64 seed 0), a label-noise control.
- **Settings:** rank 4, α 8, dropout 0, on q/k/v/o projections, float32 adapter weights, AdamW lr 1e-4, one optimizer step per case (its five orders), seed 0, gradient checkpointing, at most 8 epochs.
- **Early stopping:** on the tuning cases' mean cell soft regret after each epoch, patience 2. Epoch 0 (adapter B = 0) equals plain.
- **Saved:** the best adapter in `demo_out/adapters/<arm>/` (PEFT `save_pretrained`) and results in `demo_out/lora_<arm>.json`. Each run rebuilds the ledger when it finishes.
- **Live loading:** `scoring.load_adapters` loads all saved arms into the running model; `floor.py` `adapter on|off|<arm>` shows plain beside the adapter.

**Dependency:** `peft==0.12.0` was installed into `.venv`. It was the only new package (no upgrades), and it is compatible with transformers 4.44.2 and torch 2.4.1. It is not in `requirements.gpu.lock`, which belongs to the registered study.

**Smoke test:** a CPU smoke test on 2B was stopped after 19 minutes still in its first stage, because bf16 matrix multiplies on this CPU are impractically slow. It was replaced by a 2B GPU smoke test at the start of the chain.

**Chain:** `demo/run_lora_chain.sh`, tmux session `lora`. It waits for the `tune` session to end, runs the 2B GPU smoke test (2 cases, 1 epoch; the arms run only if it succeeds), then the 9B arms answer_only, template and shuffled in turn.

Check commands:

```bash
tail -3 logs/demo_lora_chain.log logs/demo_lora_smoke_gpu.log
grep -h "epoch\|COMPLETED" logs/demo_lora_answer_only.log logs/demo_lora_template.log logs/demo_lora_shuffled.log
```

## Review gates (REVIEW_GATES.md, adopted 05:2x on 2026-11-22)

- **Process.** The owner's `REVIEW_GATES.md` and `CLAUDE.md` arrived on `origin/demo` while work was running; my commits were rebased on top.
- **Earlier work.** Gates apply from that point. The third tuning job (started 05:02) and the dose-scan conclusion predate them. The G2 gate before the final verdict covers the steering conclusion.
- **Gates this message:** G1 for LoRA (a new rung, before the queued chain starts) and G2 before the final conclusion. That is the two-gate limit.
- **G1, LoRA (rung 5):**
  - Packet `/tmp/gate_G1_c939056d/`: proposal with frozen decision rules, brief, status excerpt, ledger, `lora.py` and the code it calls, small summary.
  - The `gate-reviewer-*` agent types are not registered in this session, so fresh general-purpose agents with models sonnet and fable were given the agent files' instructions plus the packet path (the documented fallback).
- **Code change for the packet's word check:** `pairs_template.py` replaced Python's `round()` with `int(x + 0.5)`. Same result here: 0.2 × 34 = 6.8 → 7.

---

# Plan of 2026-11-22, 05:30 UTC (steering checks, held-out split, LoRA with gates)

This follows the owner's second message of the morning and its additions. They supersede the first message's chain, arm order and lr rule.

**Gates:** this message prescribes three gates (G2 steering, G1 LoRA plan, G2 LoRA results), which overrides the two-per-message default.

**The earlier G1 reviews** of the superseded LoRA proposal are saved under `reviews/` when they arrive, marked as being for the superseded plan. They are not put into any later packet.

## 1. Steering job and queued chain stopped — done

- The `tune`, `ledgerwait` and `lora` sessions were stopped. Their processes run under nohup and outlived `tmux kill-session`, so they were killed directly.
- The queued LoRA chain was killed before it could start: its wait loop ended as soon as the `tune` session closed.
- **Kept:** `demo_out/tune_partial.jsonl` (21 points of the third tuning job) for a later `--resume`.

**Earlier G1 reviews** (superseded LoRA plan): saved as `reviews/2026-11-22_G1_lora-superseded-plan_{sonnet,fable}.md`. Both said go-with-changes. Their main points are all covered by this plan: split by cell (no shared cells); a method-distillation arm; a matched neutral control; at least 3 seeds for the key arms; a trainability check before any null is read; train and held-out regret logged separately; secondary `say` and reworded checks; and freezing the comparators before the test look.

## 2. LoRA split on cells — done

`demo/make_splits_lora.py` → **`demo/splits_lora.json`**. The 17 development cells are divided into **11 train cells** (44 cases, all four variants 15–18) and **6 held-out tune cells** (24 cases, all four variants), balanced by case type. The split was hand-picked before any LoRA result. Test cells are untouched.

| Set | Cells | Type counts (below resale / at or above / no cost) |
| --- | --- | --- |
| held-out tune (6) | (3, C 2), (5, C 4), (6, C 1), (3, C 4), (3, neutral), (5, pressure) | 3 / 1 / 2 |
| train (11) | (2, C 1), (2, C 3), (2, C 5), (3, pressure), (4, C 1), (4, C 3), (4, C 5), (5, C 2), (5, neutral), (6, C 3), (6, C 5) | 6 / 3 / 2 |

The held-out cells cover best offers 1, 2 and 4 (cost below resale), a multi-best cell, and both no-cost lines, so they are not a lookup of train cells.

**Baselines on the same cases:** plain is in `demo_out/cases.jsonl`. The step 4 text rows covered only variants 17–18, so `demo/score_rows_dev.py` (`demo_out/text_rows_build.jsonl`) scored method, neutral and wrong-rule on variants 15–16. Always-2 is computed from the labels.

## 3. Steering checks before closing rung 4

### Hook verification — done, both checks pass (`demo/steer_verify_hooks.py`, `demo_out/steer_verify_hooks.json`, `logs/demo_steer_verify_hooks.log`)

Run on 4 held-out tune cases, all five option orders.

| Check | Result |
| --- | --- |
| Letter token ids that `letter_scores` reads equal the ids used for steering (`convert_tokens_to_ids`) | **yes** (235250, 235268, 235260, 235258, 235249) |
| Patch the full P1 residual from a method-text run into the plain run at layer 41; must reproduce the method-text first-token distribution exactly | **exact** (worst difference 0.0 over 20 case-orders; the two runs differ by up to 7.9 nats) |
| Steer at layer 41 with unit(W_U[letter of offer 1] − W_U[letter of offer 4]), per option order, at fractions of the mean plain P1 residual norm at layer 41 | **lowers the offer**: −0.64 coins at fraction 0.05, −1.03 at 0.1, −1.22 at 0.25–2.0; letter mass ×1.14 to ×1.46 up to fraction 0.5 (×0.83 at 1.0) |

The hook is correct. Steering the final layer in the direction that raises "1" over "4" moves the expected offer by about 1.2 coins while the letter format stays coherent. The mechanism is sound, so the earlier null at layers 12–24 is about the vectors, not the code. Pass rule (logged): the expected offer falls by more than 0.05 at fraction 0.25 and does not rise again by 0.5.

**Design of checks a–c** (`demo/steer_checks.py`):

- **Vectors are built from the 11 train cells only** (all four variants, 44 cases), and **scored on 12 held-out tune cases** (variants 15 and 18 of the six held-out cells), so no vector is built from the cells it is scored on.
- **Strength:** a fraction of the mean plain P1 residual norm at that layer (over train cases and orders); fractions 0.1, 0.25, 0.5, 1.0; layers 12 to 39 every 3 (10 layers).
- **Reported:** cell-mean renormalised soft regret, letter mass relative to plain, change in expected offer.
- **Checks:**
  - (a) per-order cheap vectors, each order steered with its own;
  - (b) order-averaged cheap and sentence at layers 27–39;
  - (c) patching each case's P1 residual from the method-text run into the plain run, one layer at a time (all 42 layers).
- **Extras:** the negated vector and 3 random directions at the best settings; the top-10 P1 tokens under steering; steered `say` on 4 cases.
- **Rule for a positive finding:** any setting with a change in expected offer ≤ −0.25 coins and letter mass ≥ 0.9 × plain is written up and recorded for a later grid.

### Baselines on the LoRA split (`demo/lora_baselines.py` → `demo_out/lora_baselines.json`; CPU, saved results)

Mean cell soft regret with 95% cell-bootstrap intervals (all four variants of each cell). Method text was also measured on the train cells, as asked.

| Baseline | Train cells (11): soft regret [95% CI] | Held-out tune cells (6): soft regret [95% CI] | Tune: cost < resale | Tune letter mass |
| --- | --- | --- | --- | --- |
| plain | 0.778 [0.37, 1.19] | 0.577 [0.20, 0.96] | 1.080 | 0.64 |
| method text | 0.428 [0.13, 0.84] | **0.171** [0.03, 0.36] | 0.290 | 0.91 |
| neutral text (same length) | 0.755 [0.33, 1.19] | 0.531 [0.16, 0.92] | 1.012 | 0.58 |
| wrong-rule text | 0.819 [0.30, 1.39] | 0.462 [0.13, 0.79] | 0.902 | 0.70 |
| always-2 | 0.636 [0.18, 1.18] | 0.333 [0.00, 0.67] | 0.667 | — |

The held-out cells are easier for a constant than the train cells: always-2 is already best (or tied) in 4 of the 6, so its 0.333 is a strong reference there. Every LoRA comparison uses these same cases.

## 4. LoRA plan (written before any training)

### Pass rule for the method arm (frozen now)

**The method arm passes if its held-out tune-cell soft regret beats plain and both distillation controls (neutral-distil and wrong-rule-distil), with the lower 95% cell-bootstrap bound of each difference above 0.**

- **Unit:** the 6 held-out tune cells (all four variants each).
- **Per-arm value:** per-cell soft regret, averaged over seeds where an arm has several; each arm at its chosen learning rate.
- **Three differences:** (plain − method), (neutral-distil − method), (wrong-rule-distil − method), per cell.
- **Interval:** 10,000 resamples of cells, seed 0. A difference counts when its 2.5% quantile is above 0.
- **Also reported, never part of the rule:** the shuffled arms, answer_only, constant-2, always-2 and method text.
- **Selection caveat:** the held-out tune cells select the learning rate and the epoch, so these numbers are selected-on and not independent evidence. A fresh look needs the test cells (gate G3).

### Design

- **Data:** train on the 11 train cells (44 cases, 220 examples over five option orders). Early stopping on the 6 held-out tune cells. Test cells and variants 1–14 are never used.
- **Loss (letter-only):** cross-entropy between the target and the student's first-token distribution *renormalised over the five letters*. This is the quantity that soft regret is computed from. Letter mass is therefore not trained and is logged as a side effect. I chose this over a full-vocabulary loss because the earlier plan's reviewers flagged that loss as pushing letter mass up in every arm, a format effect.
- **Arms (targets):**
  - **method:** the model's own first-token letter distribution with the frozen method paragraph as the Notes block, computed before training;
  - **neutral:** the same with the same-length neutral text (matched control);
  - **wrong_rule:** the same with "Offer half the stated cost." (matched control);
  - **answer_only:** uniform over the letters of the case's best offers;
  - **shuffled:** answer_only targets with the best-offer sets permuted over the train *cells* by a derangement that also avoids cells with an identical set. Three derangements (`--perm 0, 1, 2`). The fraction of labels still correct is reported (exactly equal to the true set: 0 by construction; sharing a best offer with the true set: about 36%);
  - **const2:** one-hot on 2 coins;
  - **template:** the model's own distribution with the template paragraph, which names the best offer. A **leaky upper bound**.
- **Settings:** rank 4, α 8, q/k/v/o projections, float32 adapter weights, AdamW, one optimizer step per case (its five orders), gradient checkpointing, at most 8 epochs, patience 2. Learning rate grid {1e-4, 3e-4, 1e-3} for every arm, chosen on the held-out tune cells. Then seeds 0–2 at the chosen rate for method and its two controls (seed 0 is the grid run).
- **Per epoch:** train-cell regret and letter mass, held-out regret and letter mass, seconds. At the best epoch the free-text answer (`scoring.say`) is scored on the held-out cases: agreement with the first-token top offer, against plain's.
- **Trainability check:** answer_only at lr 3e-4 runs first. It passes if its best-epoch **train-cell** soft regret is below 0.15 (plain on the train cells: 0.778). If it fails, the pre-declared fallback (lr 1e-3, rank 16) runs once, and a null from any arm is then read as "undertrained", not as a rung-5 failure.
- **Order:** answer_only trainability check → method, neutral → wrong_rule, answer_only (other rates), shuffled → constant-2, template → seeds 1 and 2.
- **GPU budget:** 10 hours. The reduction rule: controls get 1 seed, then constant-2 is dropped, then template. The estimate comes from the measured seconds per epoch (smoke test) times 6.5 epochs per run.

### Safety checks before the real runs (`demo/lora_checks.py`)

1. The training forward pass equals the scoring path's first-token distribution on one example (epoch 0 and after a few steps).
2. Adapter off matches plain bit-for-bit.
3. A saved adapter reloaded in a fresh process reproduces its numbers.
4. `floor.py` caches are keyed by adapter (unit test).

Also: floor.py refuses every intervention (text, steer, adapter on) on a test case, so no adapter or vector is shown on the live case.

### Freeze rule for the eventual test look

- One script produces every row in one run, with the arms, adapters, comparators and code frozen first.
- Changes are reported against **test plain (0.534)**.
- It needs gate G3 and the owner's explicit go; neither has been given.

### `floor.py` safety changes (before any adapter exists)

- Every intervention (`text`, `steer`, `adapter on|<name>`, and a `dial` run under a non-plain condition) is **refused on a test case**, so no adapter, vector or text is ever shown on the live case. Plain-only commands (`cost`, `shuffle`, `say`, `table`) still work there.
- `adapter` accepts any saved run name (listed from `demo_out/adapters/`); `adapter on` loads the best run named in `demo/lora_summary.json`; `say` follows the current adapter.
- Run ids contain no "." (`method_lr3e-04_s0`), because PEFT adapter names become module-dict keys.
- Caches are keyed by adapter: unit-tested (`test_model_engine_cache_is_keyed_by_adapter`), together with the test-case refusals.

## Gate G1 on the LoRA plan — done: both reviewers **go-with-changes**

Reviews saved as `reviews/2026-11-22_G1_lora-plan_{sonnet,fable}.md` (packet `/tmp/gate_G1_ed994d4f/`, run with the registered `gate-reviewer-*` agents). No training result existed when they ran.

**The owner's pass rule above is unchanged and remains the primary rule.** The reviews showed it can be met by an "offer low" adapter (always-2 scores 0.333 on the held-out cells, better than the plain, neutral-text and wrong-rule comparators). I therefore added **strict criteria, reported separately and never replacing the owner's rule** (`demo/lora_report.py`, committed before any result):

- **S1:** method also beats always-2 and the best shuffled arm, lower bound above 0.
- **S2:** effect floor: it recovers at least 50% of the gap between plain and the in-prompt method text on the held-out cells.
- **S3:** coherence: held-out letter mass at least 0.9 × plain's.
- **S4:** free text: held-out free-text hard regret (`scoring.say`) below plain's.
- **S5:** content: the slope of the expected offer on the stated cost over the held-out cost-below-resale cases is at least 0.25. Measured on the same 12 cases: plain 0.05, method text 0.53, best offer 1.0.

**Review points and what was done:**

| # | Point (who) | Action |
| --- | --- | --- |
| 1 | Pass rule beaten by "offer low": add always-2, shuffled, effect floor, slope (both) | **Applied** as S1, S2, S5. always-2 is computed from the labels; the const2 *training* arm stays optional (owner's reduction order) |
| 2 | Budget plan overruns; silent fallback; unmeasured time (both) | **Applied**: reduction ladder L0–L5 (adds a one-permutation shuffled step and a non-core-arms-at-method's-rate step); seconds per epoch measured from finished runs; model load counted; the driver **refuses to run over budget** (re-planned after the trainability run, and again after the method and neutral grids) |
| 3 | Trainability check read the best-held-out epoch; fallback result unread (both) | **Applied**: uses the **minimum** train regret over epochs; the fallback outcome is read; if the fallback also fails the chain halts as "UNDERTRAINED" (`demo/lora_status.json`) |
| 4 | No coherence floor; free-text not gated (both) | **Applied** as S3 and S4 |
| 5 | 6 cells, lumpy, fragile percentile bootstrap; null uninformative (both) | **Applied**: per-cell differences and a count of cells where method is better are reported beside the interval; a null is read only as "not shown here". The interval stays as the owner's rule |
| 6 | Seed asymmetry (both) | **Applied**: the comparison uses seed 0 of every arm at its chosen rate; method's other seeds are reported separately |
| 7 | Crashed run skipped silently; `chosen_lr` defaults (Fable) | **Applied**: a failed run stops the chain; an incomplete grid is an error |
| 8 | Teacher cache keyed without text (Fable) | **Applied**: key includes a hash of the teacher text |
| 9 | Checks not gated; check 4 missing; pass rule unwritten (both) | **Applied**: the chain refuses to start unless `lora_checks.json` shows checks 1–3 passed and the adapter-cache test passes; the pass-rule script is committed first; its logic is unit-tested on synthetic runs |
| 10 | Check-1 tolerance undefined; rank missing from log names (Sonnet) | **Applied**: tolerances fixed in advance (check 1 ≤ 1e-4, check 2 exact, check 3 ≤ 1e-6); log names include the rank |
| 11 | wrong_rule is not length-matched (both) | **Applied** (wording): wrong_rule (6 tokens) is a *content* control; neutral text is the length-matched one (145 tokens, the same as the method paragraph) |
| 12 | Outcome table (student matches teacher on train × transfers) (Fable) | **Applied** in `lora_report.py`: "matches the teacher on train" = best-epoch train regret within 0.05 of method text's 0.428 |
| 13 | Fidelity to own teacher (both) | **Applied** as a logged KL(teacher‖student) on train and held-out cells for every distillation arm; **not** a gate |
| 14 | Selection makes the rule in-sample (both) | **Applied** (wording): a pass licenses spending the one test look, never evidence |
| 15 | Split chosen with outcome knowledge (Fable) | **Disclosed**: the six held-out cells were hand-picked, balanced by case type and by best offer, *after* the plain failure map on all 140 cases and the step 4 text rows (variants 17–18 of these cells) existed. They were not picked by those results, but the results were visible |
| 16 | Stop distillation arms on teacher cross-entropy rather than held-out regret (Fable) | **Deferred** (open): the owner specified early stopping on held-out tune cells. Fidelity is logged so that a control stuck at plain can be seen |
| 17 | Train cells contain no stated cost 4 and no best offer 4, so held-out cell (5, C 4) tests extrapolation (Sonnet) | **Deferred** (open): the split is frozen; per-cell results show it |

**Open review points:** 16 and 17 above; plus that the const2 *training* arm and the template arm are the first to be dropped by the reduction ladder.

## 3. Steering checks: results, gate G2 and the verdict (2026-11-22)

**Scripts and files.** `demo/steer_checks.py` (checks a–c, controls, extras), `demo/steer_content_check.py`, `demo/steer_followup.py`; results in `demo_out/steer_checks.{json,md}`, `steer_content_check.json`, `steer_followup.json`; logs `logs/demo_steer_*.log`. Vectors are built from the 11 train cells and scored on 12 held-out tune cases (variants 15 and 18 of the six held-out cells). No test case was scored. Reference on those 12 cases: plain soft regret **0.573** (expected offer 2.338, letter mass 0.67); method text in the prompt **0.184**; always-2 **0.333**; best constant shift of the output distribution (fitted on the train cells) **0.508**.

### Checks a–c (full tables: `demo_out/steer_checks.md`)

Each entry: change in expected offer / soft regret / letter mass relative to plain.

| Check | Setting | Result |
| --- | --- | --- |
| (a) per-order cheap | layer 27, f 0.25 | −0.259 / 0.53 / ×1.09 |
| | layer 33, f 1.0 | −1.178 / 0.427 / ×1.06 |
| | layer 36, f 0.5 | −0.841 / 0.471 / ×1.08 |
| | layer 39, f 0.5 | −0.974 / 0.442 / ×1.09 |
| | **layer 39, f 1.0 (best)** | **−1.263 / 0.407 / ×1.20** |
| (b) order-averaged cheap | best coherent: layer 27, f 0.25 | −0.205 / 0.560 / ×1.11 |
| (b) order-averaged sentence | best coherent by change in offer: layer 33, f 1.0 | −0.072 / 0.606 / ×1.35 |
| (c) patch method-run P1 residual into plain | layers 0–24 | no change (0.567–0.575) |
| | 27 / 30 / 33 / 36 / 39 / 41 | 0.526 / 0.495 / 0.341 / 0.253 / 0.203 / 0.184 (layer 41 is exact: difference 0.0) |

- **13 of the 40 settings in (a)** lower the expected offer by at least 0.25 coins with letter mass at least 0.9 × plain (10 with mass at or above plain). So the clause "a check moves the offer by 0.25 coins or more while the format stays coherent" **was met**. It is recorded for a later grid as a *letter push* (below), not as a content result.
- **Controls at (a)'s best setting:** negated vector **+1.629** (soft regret 1.25, mass ×1.20); three random unit directions −0.019, −0.002, +0.024. At coherent strengths the negation raises the offer too: +0.599 (layer 39, f 0.25, mass ×0.95), +1.318 (f 0.5, ×1.01), +1.129 (layer 33, f 0.5, ×0.86).
- **Controls for (b):** cheap negated +0.452 and sentence negated +0.264, but both at *incoherent* strength (letter mass ×0.65 and ×0.03), so those two numbers say little. Random directions: |change| ≤ 0.03.
- **Hook verification** (above) passed first: exact patch at layer 41, and a final-layer unembedding push of −0.64 to −1.22 coins.

### Gate G2 on the steering verdict — both reviewers: **partly justified**

Saved as `reviews/2026-11-22_G2_steering-verdict_{sonnet,fable}.md` (packet `/tmp/gate_G2_ea489d9c/`). The proposed verdict had a wrong number (free text: 2 of 4 cases changed, not 3), over-read the patching, and used evidence that does not discriminate (a 0.99 correlation with the unembedding push). All fixes were under 1 GPU hour, so they were done before this verdict (`demo/steer_followup.py`, 20 minutes):

| Review point | Check and result |
| --- | --- |
| Wrong-order control (both) | Steer option order i with order (i+1)'s vector: at layers 33, 36, 39 (f 0.5) the offer moves **+0.40, +1.10, +1.63** (own order −0.64, −0.84, −0.97); layer 39 f 1.0: +2.39 against −1.26. At layer 27, f 0.25 the wrong-order vector still gives −0.23 (own −0.26): that early effect is **not** order-specific |
| Cosine with the unembedding difference (both) | Per-order cheap vector against unit(W_U[letter of 1] − W_U[letter of 4]): 0.02 (layer 27), 0.09–0.15 (33), 0.24–0.31 (36), 0.33–0.40 (39) |
| Does the 0.99 correlation discriminate? (both) | Yes: per-case effects of per-order cheap correlate **0.991 / 0.995 / 0.997** (layers 33 / 36 / 39) with a final-layer push interpolated to the same mean change, but the **method text** correlates only **0.54**, the patch at layer 33 **0.84** and at layer 36 **0.66**. Correlation with headroom (plain offer − 1): cheap 0.82–0.95, method text 0.40 |
| Per-order sentence vectors (Sonnet) | Layers 33, 36, 39 (f 1.0): −1.04, −1.06, −1.02 with soft regret 0.439, 0.427, 0.426 and mass ×1.4: the same letter-push behaviour as cheap |
| Actual-delta steering (Sonnet) | Delta = method-run minus plain P1 residual of the evaluated cases themselves (diagnostic, not deployable). Own case and order: reproduces the patch (layer 39: −0.547, regret 0.203). **Averaged over orders within a case: ≈ 0 at every layer** (−0.03 to +0.01). Averaged over cases within an order: −0.044 / −0.084 / −0.179 / −0.285 / −0.388 at layers 27–39 but regret stays 0.53–0.57 |
| Positive control as text (Sonnet) | `paragraph(case, 1)` as notes: **−1.321**; `paragraph(case, 4)`: **+1.661**; method paragraph −0.562. The target is real content when given as text |
| Free text on all 12 cases (both) | Order-averaged cheap vector, last-position steering: layer 39, f 1.0 moves **8 of 12** offers (mean −0.67); negated moves 12 of 12 (**+2.33**); random 1 of 12 (+0.08). Layer 27, f 0.25: 2 of 12 (−0.17), negated 7 of 12 (+0.58), random 0. Hard regret on the 6 cost-below-resale cases at layer 39: 0.67 against plain's 1.0 (6 cases, 3 cells) |
| Reporting errors (Fable) | Corrected above: 13 (not "13 or 10") settings; per-order steering at its best (0.407) is **worse than always-2 (0.333)**; the 3-of-4 free-text count is replaced by the 12-case result |
| "Real but weak" (Fable) | Dropped as stated; replaced by the coherent-strength negations above |
| Stats too thin (both) | Stated as descriptive: 12 cases = 6 cells; no interval is claimed for the partial Spearman (+0.10 to +0.21, plain −0.02), which is not used as evidence |

### Verdict (after G2)

**Mean-difference steering at P1 (order-averaged vectors, layers 12–39) did not reproduce the method text's effect on the first-token readout** (best coherent change −0.205 for cheap and −0.072 for sentence, against −0.56 for the text).

1. **The vectors that moved the readout are letter pushes.** Per-order cheap and sentence vectors at layers 33–39 move the expected offer by up to −1.3 coins with coherent letter mass and symmetric negations, but they are specific to the option order (the next order's vector moves the offer the other way), they correlate 0.99 per case with a final-layer push toward the 1-coin letter, and their regret (0.41–0.43) does not beat always-2 (0.333). The method text does not behave like that (per-case correlation 0.54).
2. **Explanation.** The method text's effect at P1 is carried by case- and order-specific signal in the last third of the network: patching the whole P1 residual recovers nothing before layer 24, about half by layer 33 and all by layer 41; the delta averaged over orders cancels to about 0; and a case-independent, order-specific delta reproduces part of the change in the offer (−0.39 of −0.55 at layer 39) but none of the regret gain. A mean-difference direction cannot hold that. **Not tested:** attention (K/V or attention outputs), so "arrives late through attention" is a hypothesis.
3. **Free text.** The order-averaged cheap vector does move free-text offers (8 of 12 at layer 39, f 1.0) with a symmetric negation. Whether it carries case content is not shown: it is a generic "cheaper" shift (cost-below-resale hard regret 0.67 vs 1.0 on 6 cases).
4. **Scope.** P1-only, order-averaged (and per-order) mean-difference vectors, layers 12–39 (6–24 in the earlier scan), fractions up to 1.0 (2.0 earlier); steering from the end of the seller line onward was tried only in the earlier scan at layers 12–24. All on 12 held-out tune cases (6 cells) selected on; test cases were never scored. The negative statement is about *these vectors*, not about steering in general.

**Recorded for a later grid** (positive-finding clause): per-order cheap or sentence vectors at layers 27–39, fractions 0.25–1.0 (first-token readout, a letter push); order-averaged cheap at layer 39, fraction 1.0 for free text.

**Open review points (steering):** the evaluated cases also selected the settings; attention was not patched; free text is 12 cases; whether any steering setting goes to the test cells needs gate G3 and the owner's go.

## 4b. LoRA: loss change, safety checks and launch (2026-11-22, 06:20–06:55 UTC)

**Safety checks — all passed** (`demo/lora_checks.py`, `demo_out/lora_checks.json`, `logs/demo_lora_checks_{train,reload}.log`):

| Check | Result |
| --- | --- |
| 1. Training forward pass = scoring path's first-token distribution (letter log-probs) | **exact** (difference 0.0; renormalised distribution ≤ 9e-8), at epoch 0 and after 6 steps (tolerance 1e-4) |
| 2. Adapter off = plain, bit-for-bit | **exact** (0.0 against the saved plain probabilities); adapter on differs by up to 0.79 |
| 3. Adapter saved, reloaded in a fresh process | **exact** (0.0), and the reloaded adapter switched off equals plain |
| 4. `floor.py` caches keyed by adapter | unit test passes; the chain re-runs it before starting |

**The renormalised-only loss was a mistake and was replaced.** The first trainability run (answer_only, lr 3e-4, loss on the letters renormalised over the five) reached held-out soft regret 0.204 after one epoch, but with **letter mass 0.01** (plain 0.64): the loss does not constrain the answer format, so the adapter simply pushed all probability off the letters while the renormalised remainder looked excellent. It was stopped after epoch 1 (log `logs/demo_lora_answer_only_renorm_loss_dead_end.log`, adapter `demo_out/dead_ends/`, ledger row). The loss is now the ordinary answer-token loss: cross-entropy on the letters' **full-vocabulary** log-probabilities, which equals the renormalised cross-entropy plus −log(letter mass). Every arm is then pushed equally to keep the answer format, so arms differ only in which letter they favour. A smoke test of the method arm (2 cases, 1 epoch) shows mass rising to 0.98 and populates the fidelity, say and slope outputs. This reverts a change I had made in response to the plan review; the reviewers' own concern (format effects) is handled by S3 and by the shared mass term.

**Launch:** tmux session `lora` runs `demo/lora_chain.py` (gates, trainability run, then the plan). The chain refuses to run over the 10-hour budget (re-planned after the trainability run and after the method and neutral grids). The pass-rule script is `demo/lora_report.py` (tested on synthetic runs).

Check commands:

```bash
grep -h "epoch\|COMPLETED\|CHOSEN\|plan" logs/demo_lora_chain.log logs/demo_lora_answer_only_lr3e-04_s0.log | tail -20
ls demo_out/lora/                                   # one JSON per finished run
python demo/lora_report.py                          # tables, pass rule and strict criteria (CPU)
python demo/ledger.py                               # RESULTS_LEDGER.md
```

## Review pair changed (owner's instruction)

`gate-reviewer-opus` added (same instructions as the Fable reviewer). From now: G1 Sonnet alone (Sonnet + Opus if the step uses more than 3 GPU hours); G2 and G3 always Sonnet + Opus; Fable is no longer used. `REVIEW_GATES.md` and `CLAUDE.md` updated. Earlier reviews by Fable stay in `reviews/` unchanged.

## LoRA trainability check passed; chain relaunched

- **answer_only, lr 3e-4, seed 0** (`demo_out/lora/answer_only_lr3e-04_s0.json`): best epoch 7 of 8, **train soft regret 0.000, held-out soft regret 0.000**, letter mass 1.00, 317 s/epoch, 47 minutes. Trainability **passes** (threshold 0.15). It also fits the held-out cells, which it never trained on, so supervision on the answer generalises across cells here. This is the supervised reference, not evidence about the method arm.
- **The chain halted on a ladder gap:** L5 could not take effect before the method rate was known, so the first budget check priced the full grid (10.6 h). Fixed: L5 is priced with one placeholder rate until the method grid finishes, then uses method's chosen rate. The plan estimate is still approximate (runs may use up to 8 epochs, not 6.5); the chain re-plans with measured times after the method and neutral grids.
- Relaunched in tmux `lora` (resumes; the finished run is skipped).

## LoRA verdict (chain finished; gate G2 Sonnet + Opus, both "partly justified")

**Verdict (selected-on held-out cells, 6 cells):** The frozen owner's rule is NOT met: method distil (lr 1e-4, seed 0) held-out soft regret 0.155 beats plain 0.577 (+0.422 [+0.051, +0.820], 5/6 cells) and neutral-distil 0.534 (+0.378 [+0.043, +0.758], 5/6), but not wrong-rule-distil 0.448 (+0.293 [-0.003, +0.605], 3/6; lower bound misses 0 by 0.003). Method seeds 0/1/2: 0.155/0.217/0.210 (lr 3e-4 0.231, 1e-3 0.420); in-prompt method text 0.171, always-2 0.333. Strict: S1 vs always-2 not met (lower-bound criterion), S1 vs shuffled uninformative (the shuffled run never left the untrained model), S2, S3, S5 met, S4 is noise (free text 0.50 -> 0.47). Wrong-rule was run at one lr and one seed. Not a pass, not evidence of failure. Gain is in first-token letter probabilities; free-text answers barely move. **No test look.**

**G2 actions.** Applied: report outcome label fixed (new branch "improves held-out cells over plain and neutral-distil; not separated from wrong-rule-distil"; "matched" documented as one-sided); verdict worded as selected-on; shuffled claim dropped; "letter mass 1.00 everywhere" not used (epoch-0 arms have 0.64). Both reviewers' reviews in reviews/2026-11-22_G2_lora-verdict_*.md.
**Open review points (deferred, not run: owner asked to stop):** wrong-rule seeds 1,2 and lrs 3e-4/1e-3 (about 1.7 GPU-h, needs G1 Sonnet alone; cannot change the frozen verdict, only add exploratory evidence); shuffled at a fixed epoch or derangements 1,2; cell-bootstrap of the slope difference method vs wrong-rule and per-cell table of the 3 cells where method does not win; bootstrap of free-text hard regret; method-vs-control regret at fixed epochs 1-4; save per-cell S1 differences; held-out size (12 vs 24 cases) to be confirmed between LoRA and steering evaluations; planner assumed 6.5 epochs/run vs measured ~4.4, so L4 would have fit (L5 was chosen; runs used ~5.5 of 10 h).
**Before any test look (G3 + owner go):** owner waiver or a pre-declared extension, since the frozen rule licenses it only on a pass; freeze adapters by sha256 and epoch, rule/unit/bootstrap seed, comparators, seed policy (mean of 3), corrected outcome labels, exact test-cell list (variants 1-14 excluded). GPU is idle; steering tune job left paused (no reason to resume).

## EXPLORATORY follow-up to the LoRA verdict (all results below are exploratory; the frozen verdict "not passed" stands)
**Rule written before running (Nov 22):** the exploratory comparison is the mean of 3 seeds per arm, each arm at the learning rate its own seed-0 grid chose, scored on the 6 held-out cells, with a paired cell bootstrap (10,000 resamples, seed 0). Primary exploratory outcome: the slope of the expected offer on the stated cost, method vs wrong-rule. Nothing here can change the frozen verdict. No test cases.

### Exploratory step 1 done (CPU; demo_out/explore_cpu_seeds0.md) and G1 (Sonnet alone; expected 2.5 GPU-h <= 3 h) on the runs: GO-WITH-CHANGES
Applied: (1) slope interval relabelled "descriptive, not a sampling interval" (3 cost cells, ~7 distinct bootstrap outcomes, 1/9 of resamples dropped); the slope as primary outcome is POST HOC (seed-0 slopes were seen before the rule was written); soft regret, per-cell, free-text and slope are co-equal exploratory readouts; added split of the soft-regret difference into C<V cells vs other cells and a per-seed table. (2) Main exploratory readout also reported on seeds 1-2 only (seed 0 chose the lr and is the best method seed). (3) lora.py now logs per-epoch held-out probabilities (`history[].tune_probs`; logging-only change after the method runs; sha1 before badfc3c0) so fixed-epoch per-cell intervals exist for the new runs only. (4) If the 3 h wall-time limit drops a neutral seed, neutral is compared on the seeds it has and flagged unbalanced. Deferred: train-cell in-prompt regret/KL for the controls beyond what the report already shows.
**Pre-written reading (before the runs):** SUPPORT for "method content is distinctive" = method soft regret (3-seed mean and seeds 1-2 mean) below wrong-rule by >= 0.10 with a lower bootstrap bound > 0, AND method better in >= 4 of 6 cells or the gain shown on the C<V cells with no loss elsewhere beyond 0.05, AND method's range over seeds smaller than that difference. NOT SEPARATED = wrong-rule at its best lr/seeds within the method's seed range. Either way the frozen verdict stays "not passed"; an exploratory result on tune cells cannot by itself license a test look (owner decides, in TEST_PLAN.md).
Step-1 facts: method-vs-wrong-rule held-out difference splits +0.679 on the 3 C<V cells and -0.094 on the other 3 (method worse on (3,C4) 0.170 vs 0.002, (3,neutral), (5,pressure)); slopes at best epoch 0.661 vs 0.031 but the method slope across epochs 1-4 is 0.217/0.661/0.390/0.301 (epoch-dependent); free-text hard regret plain 0.500 vs method 0.467, diff +0.033 [-0.150, +0.250], method better in 1 of 6 cells.
**Run chain (tmux `explore`, log logs/demo_lora_explore.log; check: `tail logs/demo_lora_explore.log; ls demo_out/lora | grep wrong_rule`):** wrong_rule 3e-4, 1e-3 (seed 0); wrong_rule seeds 1,2 at its chosen lr; neutral seeds 1,2 at 1e-4; commits and pushes after each run.

## EXPLORATORY results (3 seeds; frozen verdict "not passed" stands; all held-out numbers selected-on; G2 Sonnet + Opus: both "partly justified")
Runs finished (chain log logs/demo_lora_explore.log, 3.05 h): wrong_rule 3e-4 and 1e-3 seed 0 (grid 0.448 / 0.473 / 0.430 -> chosen 1e-3, a flat grid), wrong_rule seeds 1,2 at 1e-3, neutral seed 1 at 1e-4; **neutral seed 2 DROPPED by the pre-set 3 h wall-time limit** (cause independent of outcomes; neutral has 2 seeds). Tables: demo_out/explore_cpu_seeds012.md, _seeds12.md (seeds 1-2 only), _seeds0.md.
**Reading (exploratory, as corrected by G2):**
- Soft regret, 3-seed means on the 6 held-out cells: method 0.194, wrong-rule 0.404, neutral 0.531 (2 seeds), plain 0.577, always-2 0.333. Method minus control differences: plain +0.383 [+0.034, +0.760], neutral +0.337 [+0.021, +0.703], wrong-rule +0.210 [-0.032, +0.502] (better in 4 of 6 cells), always-2 +0.140 [-0.110, +0.451] (better in 2 of 6). Seeds 1-2 only: method 0.213 vs wrong-rule 0.391, +0.178 [-0.043, +0.462]. Per seed: method 0.155/0.217/0.210; wrong-rule 0.430/0.354/0.428.
- Pre-written reading: SUPPORT failed (lower bound < 0; the C<V alternative clause fails too, loss elsewhere 0.076 > 0.05); NOT SEPARATED not met (wrong-rule seeds all above method seeds); the rule leaves this in-between case undefined. Seed spread is training noise; the 6 cells dominate the uncertainty and a percentile bootstrap at n = 6 is optimistic.
- Gain is concentrated: +0.497 vs wrong-rule on the three C<V cells, -0.076 on the other three (method worse on (3,C4) and (5,pressure)); leave-one-cell-out wrong-rule minus method stays +0.089 to +0.277 (smallest without (6,C1)). Method still has regret 0.60 on (5,C4) (expected offer 2.7, best 4).
- Wrong-rule is not content-free: its offers are 1.97-2.09 in every cell (slope -0.01); it behaves like a noisy shift to 2 and wrong-rule text in the prompt does nothing, so "method vs wrong-rule" partly measures cost-tracking vs a shift to 2. Method does not clearly beat always-2. The earlier phrase "wrong-rule only partly reproduces the effect" is withdrawn.
- Slope (descriptive; POST HOC; 3 cells; not a sampling interval): method 0.50 (seeds 1-2: 0.42), wrong-rule -0.01, neutral 0.07, plain 0.05; method's slope is epoch-dependent (0.22/0.66/0.39/0.30 at epochs 1-4, seed 0).
- Fixed epochs (aggregates, seeds 0-2): epoch 3 method 0.254/0.259/0.249 vs wrong-rule 0.468/0.404/0.500; epoch 4 method 0.240/0.232/0.210 vs wrong-rule 0.467/0.418/0.639, so the gap does not depend on epoch selection (per-cell fixed-epoch intervals are not available: method runs predate per-epoch probability logging; only a logging line changed in lora.py, same trainable parameters 4,472,832).
- Train cells (11, fitted, each arm fits its own teacher): plain 0.778, method 0.403, wrong-rule 0.715, neutral 0.753; wrong-rule minus method +0.312 [+0.057, +0.590].
- Free text unchanged (hard regret 0.500 -> 0.492, diff +0.008 [-0.183, +0.208], method better in 1 of 6 cells; agreement with the first token falls): a first-token readout effect, not shown in generated answers.
**Open review points (deferred):** wrong-rule/always-2 offers - build a control that moves offers toward 2 without the rule content (e.g. a distil toward const-2 text) before any claim about content; neutral seed 2; per-cell fixed-epoch intervals (needs logged probabilities for method runs, about 1.6 GPU-h for 3 seeds); each teacher's in-prompt slope on the 6 cells; confirm the method paragraph was frozen before held-out cells were seen (cannot verify from the packet).

## Test look preparation: gate G3 (Sonnet + Opus both GO-WITH-CHANGES) — test set NOT touched
Owner approved TEST_PLAN.md (Nov 22) with answers: test look yes; neutral seed 2 run on tuning cells then frozen (done: best epoch 3, sha256 d3f49c7b..., held-out 0.516); no extra shift-to-2 control; threshold 0.10 kept.
Applied by gate rules (both reviewers raised them; each under 30 minutes): lock now written only after validation and plain re-scoring, raw per-case/per-order results saved after each run, GPU scoring separated from CPU `--analyze`; assertions for case-id hash, 18 cells, disjointness from train/tune, adapter safetensors and config sha256, script sha256 recorded in TEST_PLAN.md, clean git tree, test_go.json content; plain re-scored on all cases with adapters off (dry run: max abs diff 0); free-text unparsable answers dropped (rule as in development) with parse-failure rate; labels rebuilt from a comparator table (new PLAIN-ONLY label; HARM an appended flag); declared secondaries added; unit test of every label branch (tests/test_test_look_label.py). Dry run of the final script on the 24 tune cells (demo_out/test_dryrun.md, NOT a result): label PARTIAL (wrong-rule lower bound < 0). Script sha256 f0f33b83893f984eb5faebc7d32cbf0c194ec5d6d89e4ca463426b351564b042.
**Not applied / needs the owner:** Opus point 5 (section 9 changes the approved wording: always-2 rule, label set incl. PLAIN-ONLY, HARM as flag, secondaries) requires the owner's explicit approval tied to the script hash; demo/test_go.json does not exist, so `--execute` refuses. Power warning recorded in TEST_PLAN.md section 9 (expected D about 0.11 against the 0.10 threshold). Deferred: nothing else. Reviews: reviews/2026-11-22_G3_test-plan_{sonnet,opus}.md.

## TEST LOOK (run once on Nov 22; owner's go; script sha256 f0f33b83893f984eb5faebc7d32cbf0c194ec5d6d89e4ca463426b351564b042; repo commit at lock 473ca213; lock demo_out/test_look.lock, raw demo_out/test_look_raw.json, report demo_out/test_look.md)
**Outcome label (TEST_PLAN.md section 6/9): SUPPORT (beats always-2 with lower bound > 0: no).** Frozen development verdict, next to it: **NOT PASSED** (owner's rule on the 6 development cells, wrong-rule lower bound -0.003). The test look is a separate, pre-registered question; it does not change the development verdict.
72 test cases, 18 test cells (variants 15-18), 3 seeds per arm, adapters verified by sha256, adapter-off scoring reproduced saved plain exactly (max abs diff 0). Soft regret: method 0.263; wrong-rule 0.482; neutral 0.549; plain 0.534; always-2 0.378; method text in the prompt 0.256 (reference).
| Control | Difference control - method [95% cell-bootstrap interval], cells where method better | D >= 0.10 | lower bound > 0 |
| --- | --- | --- | --- |
| plain | +0.271 [+0.054, +0.514], 11 of 18 | yes | yes |
| neutral-distil | +0.286 [+0.064, +0.536], 11 of 18 | yes | yes |
| wrong-rule-distil | +0.219 [+0.048, +0.399], 11 of 18 | yes | yes |
| always-2 | +0.115 [-0.066, +0.317], 6 of 18 | yes | no (not required) |
Descriptive: the difference is carried by the 6 cells with a stated cost below resale (declared secondary, control - method: plain +0.882 [+0.616, +1.162], neutral +0.947, wrong-rule +0.699 [+0.526, +0.859], always-2 +0.502 [+0.089, +0.890]; 6 of 6 cells for plain/neutral/wrong-rule, 4 of 6 for always-2); on the other 12 cells the method is slightly worse (C>=V: plain -0.013, wrong-rule -0.028, always-2 -0.081; no cost: plain -0.056, wrong-rule -0.015, always-2 -0.077). HARM flag not raised (plain - method on C>=V cells -0.013 [-0.195, +0.157]). Method's expected offer moves closer to the best offer than plain in 5 of 6 C<V cells; slope on stated cost 0.53 (method) vs -0.01 (wrong-rule), 0.10 (neutral), 0.18 (plain), 0.42 (method text); descriptive. Per run: method 0.218/0.304/0.267; wrong-rule 0.525/0.424/0.497; neutral 0.541/0.541/0.566. Letter mass method/plain 1.55.
**Caveats to carry with the label:** (1) always-2 (0.378) is not beaten with a lower bound above 0, so the result does not show the method does better than a fixed offer of 2 overall, only that it beats the three declared controls; (2) the benefit sits in the C<V cells, the method is slightly worse elsewhere; (3) **free-text answers got worse, not better**: hard regret plain 0.439, method seeds 0.669/0.667/0.872 (mean 0.736; parse failures 1 of 72 for one seed), so the effect is a first-token/letter readout effect and does not transfer to generated text; (4) 18 cells, bootstrap over cells only, percentile interval approximate at n = 18 skewed cells; seed spread is training noise only; (5) arms' lr and epoch were chosen on the 6 development cells; (6) this is one look: no re-run, re-tune or added arm on the test cells.
Ledger row 56 added (RESULTS_LEDGER.md) beside the frozen development rows. Work stops here per the owner's instruction.

# NEW EXPERIMENT: generated dataset with fresh locked test sets (started Nov 22)
Rules: REVIEW_GATES.md; never name variants 1-14 (old name lists read only to prove disjointness), never the old test cells; no questions; commit and push each step.
## Step 1-3 choices (demo/gen_cases.py, CPU only; data in demo/gen/: cells.json, cases.jsonl, fingerprints.json; tests tests/test_gen_cases.py)
- **Game/template:** same haggling prompt (phase3.instructions_text, same memories, script, question format, five options, `Answer: (`). Changed per case: resale value V; price grid (five prices): A 1-5, B 2-6, C 3-7 (seen), D 2,4,6,8,10 and E 4-8 (hard-only); stated farm-cost prior (uniform integers lo..hi in the rule memory; priors (1,5),(2,6),(3,7),(1,10),(2,10)); the price-scale memory states the grid's mean, cheap/expensive ends and step; stated cost C integer 1..V-1 (below resale) or V..V+2 (at/above); 3 fresh wordings per seller line (none is the original text); invented buyer/seller names (26 first names x 24 surnames per side, disjoint from the old lists); opening scene picked by a hash from the 5 original openings.
- **Labels:** `gen_cases.payoff/label` = core.payoff generalised to any grid and prior (stated cost: V-k if k>=C else 0; no cost: (V-k)*P(cost<=k), cost uniform on the stated integers); unit-tested to equal core.payoff and core.oracle_bids on the whole original game. best_offers, best_positions, unique_best and `all_tie` stored per cell. **All-tie cells are flagged and excluded from every split** (regret would always be 0): 262 candidates rejected; 16 candidates rejected as old test cells (grid 1-5, prior 1-5, (V,line,C) in core.steering_cell_split 'test', whatever the wording).
- **Split (fixed seed 20261122, whole cells, balanced across below / at-or-above / no-cost, no-cost alternating neutral and pressure at random):** train 300 cells (100 per type), tune 42 (14 per type), test-same 60 (20 per type; same V 2-9, grids A-C, wordings 0-1 as train but unseen cells), test-hard 62 in three slices: hard_V 20 cells (V 10-12; seen grids and wordings; **no at-or-above cells: with V >= 10 and seen grids (largest price 7) a stated cost >= V exceeds every price, so all offers tie; balanced between below (10) and no-cost (10) instead**), hard_grid 21 (grids D, E never in train, V 2-9), hard_wording 21 (wording 2, never in train, V and grids seen). Two name variants per cell (cases = 2 x cells). Name pools disjoint across train / tune / test.
- **Fingerprints (sha256 over sorted case ids and the order-0 prompt text of each case):** test_same `0538a2a2bd15e74f66e8bd2fabe1fb7856a457053a33719c28ebc986fae31c40` (60 cells, 120 cases); test_hard `c4b08aba9b7b8c367483bb7e0bed9a242b7c322117f1780bf4deda700c55d520` (62 cells, 124 cases); hard_V `9c3090a6...`, hard_grid `e8b156e6...`, hard_wording `d7276494...` (full values in demo/gen/fingerprints.json; the unit test recomputes them). No model has seen any of these prompts.

## Gate G1 (Sonnet alone; no step over 3 GPU-hours) on the dataset design: GO-WITH-CHANGES (reviews/2026-11-22_G1_gen-dataset-design_sonnet.md)
Applied (test lists unchanged byte for byte, regenerated and compared): `fingerprints_v2.json` now hashes the test cell entries WITH labels and the generator, refimpl/core.py, refimpl/phase3.py and fruitville_haggling.py (fingerprints.json untouched); quotas recorded (single RNG stream: changing a quota changes later splits); brute-force payoff test over the whole grid/prior/V/C space and tests of the hard-slice composition (10 tests pass); failure map built with the reviewer's strata (type x V band, grid, wording, line, stated cost relative to the grid, n_best, best payoff <= 0, C inside the stated prior, baselines, chance mass, train analogues of the hard slices, label-key overlap, old-cell overlap); the old-adapter caveat recorded. Declared limits: hard_V = "V above the grid's largest price, always-profitable regime", has no at-or-above cells and a truncated C range; hard_grid pools D (structure shift: step 2, two-digit option) with E (near-in-distribution, 4-8): report separately; hard_wording is one paraphrase per line; line is collinear with type; the prior is drawn independently of C (flag C_in_prior reported, 33 of 200 train information cells have C outside the prior); labels depend on (V, grid, C) (and the prior only for no-cost), so test_same shares its label key with train for 43 of 60 cells (tune 30 of 42; test_hard 18 of 62): test_same is "new cells, same label structure", not new structure. Deferred: reserve test set; minimum detectable effect; per-wording effects per line; a separate scoring of the cheapest-tie-break reading of at-or-above.
## Step 4: plain Gemma failure map (train and tune only; test sets NOT scored; demo_out/gen_failure_map.md; scores demo_out/gen_plain_scores.jsonl, 684 cases = 342 cells, 5 orders, 1.4 s/case, run `python demo/gen_score.py`, refuses any split but train/tune)
- Overall soft regret train 0.652 [0.573, 0.731], tune 0.657 [0.465, 0.862]; mass on the best set 0.45 (chance 0.34); letter mass 0.81. Baselines on the same labels: uniform 1.204, always-cheapest 0.573, stated-cost rule 0.157 (train).
- **The failure is the stated-cost-below-resale type:** soft regret 1.436 [1.326, 1.552], mass on the best offer 0.07 (below the 0.20 chance level), top offer correct in 7% of cells; the stated-cost rule scores 0. Mean expected offer exceeds the stated cost by 1.28 coins; the slope of expected offer on C is 0.26 (train, below cells); the top offer lands at the second-cheapest position in 48 of 100 cells and at the third in 24, while the correct offer is the cheapest in about two thirds of the labels. It gets worse as V rises (V 2-3 1.07, 4-5 1.12, 6-7 1.53, 8-9 1.99), i.e. with the room to overpay; in the always-profitable regime (V >= largest price) 1.77, in the V 8-9 on grid A analogue 2.43 (4 cells).
- At-or-above cells: 0.298 [0.216, 0.383] (mass on best set 0.79, chance 0.52; always-cheapest regret 0, so the model is partly overpaying even where the cheapest offer is best; V 2-3 0.506, V 4-5 0.074). No-cost cells: 0.221 [0.184, 0.263] (mass on best 0.49 vs chance 0.29; always-cheapest 0.470 and the model beats it at V >= 6, and tends to be worse at V 8-9, 0.353).
- Grid and wording: regret similar across grids A/B/C (0.631/0.679/0.643) and wordings 0/1 (0.690/0.607): no single grid or wording dominates the failure. Cells with C below the grid's cheapest price are the worst information cells (1.070, mass on best 0.12); C on the grid 0.814. Cells with best payoff <= 0 (arbitrary labels) are easy (0.329) and inflate nothing here but should be a separate stratum in later reports.
- Reading: the same failure as in the earlier fixed cells (model does not offer the stated cost), now shown across grids, values 2-9 and two new wordings. The generated set therefore has headroom exactly where an intervention should act (below type, 100 train cells), with a stated-cost rule at 0 as an upper reference.
Commit: data, scripts, map, scores. Stopped per the instruction (no test scoring, no interventions).

# CLAUDE-AS-TEACHER EXPERIMENT on the generated dataset (started Nov 22; stop by Nov 25 23:00 CST)
## A. Teacher (CPU)
- Packet demo/gen/teacher_packet.md built by demo/gen_teacher_packet.py from TRAIN cells only: game rules in words, one prompt example (a train case), and 50 train cells (the 40 highest-regret plus 10 random from the lowest-regret quarter, shuffled, unlabelled) with only the lines that differ (value, price scale, farm-cost limits, seller's last line; buyer name replaced by "The buyer") and Gemma's order-averaged offer distribution. No best offers, regrets, method paragraph or earlier results. The example text "step of 2" grid was removed from the rules because grid D is a test-hard grid; checked the packet contains no grid D/E text, no V >= 10, no held-out wording.
- Teacher: fresh general-purpose subagent, model opus, given /tmp/teacher_32706/teacher_packet.md (a copy of the packet) and "Read this and follow its instructions." Its tool calls only read that file and wrote a scratch file under the scratchpad. Reply saved verbatim in demo/gen/teacher_reply.json (diagnosis + method). Checks passed on the first try: 141 words (<= 150), no digits, no names. No re-ask needed.
- Frozen: demo/gen/teacher_method.txt, sha256 d4010305b297188598d0fb87186ed8fdb2ef0c98446dec70240a7f74f46c3499. Teacher's diagnosis (kept as data): the model ignores the stated cost, anchors on the middle/upper part of the price range, and overbids relative to a low stated cost.
- Neutral control text demo/gen/neutral_text.txt: the five original market-scene openings concatenated and cut at the last full sentence (150 of the teacher's 162 Gemma tokens, 93%; no game content). Wrong rule = the earlier "Offer half the stated cost." sentence; original method = the earlier paragraph (textrows.METHOD), both used only as text rows, not as adapters.

## Gate G1 (Sonnet + Opus; step over 3 GPU-hours) on GEN_PLAN.md and gen_lora.py: both GO-WITH-CHANGES
Both reviewers confirmed the target construction (letter j -> grid position order[j]; answer_only inverse) and the full-vocabulary letter loss. Applied (raised by both or severe, each under 30 minutes): (1) lr choice and early stopping moved to a SELECTION set of 42 train cells outside the 100 training cells (demo/gen/lora_select_cells.json); tune is scored once per run at the best epoch and used for the verdict only; (2) budget now measured per run (mean wall_s; assumed 2400 s before any run), cumulative wall-time guard and ladder re-plan (the earlier 0.6 h per run was several times too low); (3) preconditions and stop rules (in-prompt teacher text must beat plain and neutral on the selection set; halt if all teacher runs keep epoch 0, if the ceiling cannot improve, or if teacher is not better than neutral at seed 0); (4) pass rule strengthened (effect floor 0.15, below-cell improvement with lower bound > 0 and in 60% of cells, no-harm +0.05 on the other types, mass per type, seeds 1-2 replication); (5) assertions: training path equals scoring path at the zero adapter, best-adapter reload has no unexpected keys and reproduces the recorded selection score, dead code removed, best-epoch-0 runs flagged. Declared limits (GEN_PLAN.md): controls get no lr grid (favours teacher; rule also tested on seeds 1-2), seeds do not vary the training cells, wrong-rule text is empty for no-cost cells. Deferred: varying the training subset across seeds; a neutral lr grid if the measured time allows; wrong-rule variant covering all case types. Reviews summarised in reviews/2026-11-22_G1_gen-lora-plan_{sonnet,opus}.md.

## B. Text rows on generated train and tune cells (done; demo_out/gen_text_report.md, scores demo_out/gen_text_rows.jsonl; 4 rows x 684 cases x 5 orders, 78 min; run `python demo/gen_textrows.py`)
Soft regret (cell means, bootstrap 95%), train 300 cells / tune 42 cells. Plain 0.652 / 0.657; **original method paragraph 0.368 / 0.369** (below 0.633, at-or-above 0.134, no-cost 0.336); **teacher method 0.485 / 0.517** (below 1.050, at-or-above 0.150, no-cost 0.256); neutral text 0.682 / 0.735 (slightly harmful); wrong rule 0.652 / 0.618 (letter mass drops to 0.67). Plain minus row (train): original method +0.284 [+0.215, +0.352], teacher +0.166 [+0.124, +0.209], neutral -0.030 [-0.050, -0.012], wrong rule -0.001 [-0.054, +0.050]. Baselines (train): always-cheapest 0.573 (below 1.250, no-cost 0.470), stated-cost rule 0.157. Slope of the expected offer on the stated cost over below cells (train): plain 0.26, original 0.26, teacher 0.19, neutral 0.20, wrong rule 0.08, i.e. none of the texts makes the offer track the cost; both rule texts lower regret mostly by lowering offers. Reading: the teacher's paragraph helps (+0.17) but less than our original paragraph (+0.28); it helps most on at-or-above cells (0.298 -> 0.150) and moves below cells only from 1.436 to 1.050 (the stated-cost rule scores 0); on no-cost cells the original paragraph hurts (0.221 -> 0.336) and the teacher text is neutral-to-slightly-worse (0.256). The distillation ceiling for the teacher arm is therefore its in-prompt row (0.485 train), which is below always-cheapest only by 0.09 on train and well above the stated-cost rule.

## C. LoRA chain launched (tmux `genlora`, log logs/gen_chain.log; per-run logs logs/gen_<arm>_lr<lr>_s<seed>.log; results demo_out/gen_lora/*.json, committed and pushed after every run)
Check: `tail logs/gen_chain.log; ls demo_out/gen_lora; cat demo/gen/gen_chain_status.json`. Smoke test (4 cases, 1 epoch) passed: training path equals scoring path (0.0 nats), epoch 0 equals saved plain, best-adapter reload assertion passed. Started Nov 22 about 22:20 UTC (budget 8 h from there, stop by Nov 25 23:00 CST). Progress loop (tmux `progress`) keeps pushing demo_out/lora_progress.jsonl.

## PAUSE of the gen LoRA chain (owner's instruction, Nov 22 ~22:55 UTC)
Chain (tmux genlora) stopped, no process left, GPU free. No gen LoRA run had finished: the first run (teacher, lr 1e-4, seed 0, paragraph v1 sha d4010305...) was killed during epoch 5; its log is kept (demo_out/gen_teacher_lr1e-04_s0_paused_partial.log: selection-set soft regret per epoch 0 = 0.571 (plain), ..., 0.454, 0.398, 0.457 at epochs 2-4, mass 1.00, 393 s/epoch), the partial adapter is left in demo_out/adapters (gitignored) and no result JSON exists. Measured: 393 s/epoch. Outputs kept. Next: closed teacher loop (G1 Sonnet first), then relaunch the chain unchanged with the frozen winner as the teacher arm; any teacher-arm result made with paragraph v1 would be set aside, not mixed.

## Closed teacher loop: gate G1 (Sonnet alone; CPU plus a few minutes of GPU): GO-WITH-CHANGES (reviews/2026-11-22_G1_teacher-loop_sonnet.md)
Owner's design kept: up to 3 rounds; each round a fresh blind Opus teacher gets the original packet, the current paragraph and Gemma's in-prompt results on the 42 loop cells (per-cell offer distributions and per-type soft regret; no best offers, no tune or test cells); revised paragraph under the same constraints; scored in the prompt on those cells (name variant 0, five orders); keep the best; stop early if a round does not improve by 0.02.
Applied from G1: (1) **contamination:** the 42 cells formerly used as the LoRA selection set are now the LOOP set A (feedback and winner choice). A new LoRA selection set B (demo/gen/lora_select_cells_B.json: 42 train cells, 14 per type, disjoint from the 100 LoRA training cells, from A and from the 50 cells of the original teacher packet; demo/gen/packet_cells.json) is used for the lr choice and early stopping; gen_lora.py and gen_chain.py read B and assert the disjointness; so the teacher arm gets no selection advantage from the loop. (2) **packet overlap:** 5 of the 42 loop cells were also in the original packet; Part 2 displays only the 37 that were not (the 5 are still scored). (3) **decision rule fixed before the loop:** incumbent (start: the v1 paragraph) is replaced by a round's paragraph only if the soft regret on the 42 loop cells improves by at least 0.02 AND by more than one paired standard error; the loop stops at the first round that does not replace the incumbent (ties keep the incumbent) and after round 3; each round receives the running-best paragraph and its results (not simply the previous round). `demo/gen_teacher_loop.py decide` implements it and writes demo/gen/loop/state.json. (4) **same code path:** round 0 re-scored through the same scorer (0.431363 on the loop cells, identical to the earlier text row); overwrite refused; reply and method.txt must match; paragraph checks (no digits, <= 150 words, no 'case' words, no names). (5) **limits declared:** the loop winner's score on the loop cells is optimistic (prompt optimisation with feedback, per-type feedback on 14 cells is noisy); winner, v1 and the hand-written paragraph will be compared on cells not used by the loop (set B, tune) via text rows; the LoRA verdict stays on tune only; every raw reply, packet, paragraph sha256 and per-cell score is kept in demo/gen/loop/. Frozen v1: demo/gen/teacher_method_v1.txt (sha256 d4010305b297188598d0fb87186ed8fdb2ef0c98446dec70240a7f74f46c3499).
### Loop round 1 (Opus teacher fresh and blind; packet demo/gen/loop/round_1_packet.md; reply verbatim demo/gen/loop/round_1_reply.json)
Paragraph (147 words, no digits) sha256 f41ae9b32010fcf2dbf87a7d207393eed31cf6a99294a7ed425abb98abf9b4b9. Its diagnosis: the model adds about a coin on top of a stated cost or skips the cheapest option; it cannot do the acceptance-chance x profit step for no-cost cases; the rewrite says an offer equal to the cost is accepted and replaces the products with a one-step rule (lowest possible farm cost plus resale value, halved and rounded down). Loop-cell soft regret (42 cells, in prompt): v1 0.431 -> **0.245** (improvement 0.186, paired SE 0.043: replaces the incumbent); by type below 0.903 -> 0.483, at-or-above 0.197 -> 0.070, no-cost 0.194 -> 0.181. Incumbent = round 1; continue.
### Loop round 2 and the winner
Round 2 (fresh Opus teacher, given the incumbent = round 1 and its results; reply demo/gen/loop/round_2_reply.json): paragraph 147 words, no digits, sha256 5c04b90d194f336b8f22216913a14fb38509a63a61011956c1ad97b144925f09. Loop-cell soft regret **0.565** vs incumbent 0.245 (worse by 0.320, paired SE 0.063; below 1.005, at-or-above 0.450, no-cost 0.240): not replaced; **the loop stops at the first non-improvement, round 3 is not run** (rule fixed before the loop). The teacher's diagnosis (kept as data) guessed the extra clauses confused the model, but its rewrite, which changed the stated-cost wording to a two-step check and the no-cost target to "halfway between", made things worse.
**Winner: round 1 paragraph, frozen as demo/gen/teacher_method.txt, sha256 f41ae9b32010fcf2dbf87a7d207393eed31cf6a99294a7ed425abb98abf9b4b9** (147 words, no digits). The first paragraph stays as demo/gen/teacher_method_v1.txt (sha256 d4010305...); text rows scored with v1 are renamed teacher_v1 in demo_out/gen_text_rows.jsonl. The winner's loop-cell score (0.245) is optimistic (selected on those cells); honest comparisons are on set B and tune (next: score the winner once on train and tune cells as text row `teacher`, 684 cases).
### Winner scored once on train and tune as text row `teacher` (demo_out/gen_text_report.md; 684 cases, 19 min); old rows kept as `teacher_v1`
Soft regret in the prompt (cell means, bootstrap 95%): train 300 cells plain 0.652, original method 0.368, teacher_v1 0.485, **winner 0.330** [0.278, 0.383] (below 0.612, at-or-above 0.080, no-cost 0.298; slope on stated cost 0.27; letter mass 0.92); tune 42 cells plain 0.657, original 0.369, v1 0.517, **winner 0.390** [0.243, 0.565] (below 0.673, at-or-above 0.107, no-cost 0.390); cells not used by the loop (LoRA selection set B, 42 train cells): plain 0.584, original 0.395, v1 0.490, **winner 0.342**; loop set A (optimistic): winner 0.245, v1 0.431. Plain minus winner on train +0.322 [+0.259, +0.385] (v1 +0.166, original +0.284). Baselines: always-cheapest 0.573 train / 0.429 tune; stated-cost rule 0.157 / 0.214. Reading: the loop turned a paragraph weaker than our hand-written one into one that matches or beats it on cells it was not selected on (set B 0.342 vs 0.395; train 0.330 vs 0.368), mostly on cost-below (1.436 -> 0.612) and at-or-above (0.298 -> 0.080) cells, but it hurts no-cost cells (0.221 -> 0.298 train, 0.204 -> 0.390 tune), as the original paragraph did, and the slope of the expected offer on the stated cost stays 0.27: the model mostly learns "offer low" rather than "offer the cost". The frozen winner is the teacher arm of the chain; the paragraph search used only loop-set cells and train-cell text rows, never tune or test.
## Chain relaunched unchanged with the frozen winner as the teacher arm (tmux `genlora`, log logs/gen_chain.log); preconditions are checked on set B; the earlier killed run used paragraph v1 and left no result.

## C. Gen LoRA chain finished (Nov 23 06:50 UTC; 14 runs, 7.65 h of the 8 h budget; BUDGET GUARD stopped it before wrong-rule seeds 1-2)
Plan chosen after the teacher grid: L2 (controls and ceiling at the teacher's lr; method_original at the teacher's lr). Teacher lr grid: 1e-4 chosen on selection set B (0.360); 3e-4 gave 0.375; 1e-3 stayed at epoch 0 (no improvement). Neutral ran seeds 0-2: all three kept epoch 0 (no improvement over plain), so neutral-distil equals plain and is flagged, not counted as an arm. Wrong-rule ran seed 0 only (budget guard); answer-trained ceiling ran lr 1e-4 and 3e-4 (3e-4 chosen as planned in the report; 1e-4 reached 0.026 on tune, noted as exploratory since the grid choice was made on the selection set).
Report: `PYTHONPATH=concordia:. .venv/bin/python demo/gen_lora_report.py` -> demo_out/gen_lora_report.md, demo/gen/gen_lora_summary.json. Tune soft regret (42 cells, seeds averaged): plain 0.657, teacher-distil 0.376 [0.242, 0.535] (seeds 0.380/0.352/0.395), our-method-distil 0.373, wrong-rule-distil 0.589 (1 seed), ceiling 0.118, always-cheapest 0.429, stated-cost rule 0.214. Frozen pass rule as applied by the script: **NOT PASSED** - criterion 1 fails because neutral-distil is "not run" (all neutral runs kept epoch 0), and criterion 4 (no harm) fails on no-cost cells (+0.190 vs plain). Criteria 2, 3, 5 pass. Teacher beats plain by +0.282 [+0.127, +0.447] and wrong-rule-distil by +0.214 [+0.074, +0.367]; teacher vs our-method-distil -0.003 [-0.058, +0.052] (indistinguishable); teacher is worse than the stated-cost rule (-0.161). Slope on stated cost: teacher 0.26 (plain 0.26ish), ceiling 0.69. Verdict wording waits for G2 (Sonnet + Opus).

## G2 (Sonnet + Opus) on the gen LoRA verdict: both "partly justified" (reviews/2026-11-23_G2_gen-lora-verdict_{sonnet,opus}.md)
Applied: (1) neutral relabelled: "3 runs, best epoch 0 (= plain)", not "not run"; rule 1 is indeterminate for neutral (teacher beats plain and wrong-rule with lower bound > 0), and NOT PASSED rests on rule 4 alone. Neutral at epochs 1-2 on the selection set is worse than plain in all 3 seeds (0.608-0.830 vs 0.584), so the epoch-0 rule is not hiding a format gain. (2) Post-hoc descriptive checks (demo/gen_lora_supp.py -> demo_out/gen_lora_supp.md; labelled post-hoc, tune only): mass on the cheapest option: plain 0.04/0.12/0.08 (below/at-or-above/no-cost), teacher-distil 0.50/0.52/0.51, our-method-distil 0.56/0.37/0.36, wrong-rule 0.20/0.32/0.20, ceiling 0.74/0.45/0.31. Teacher-distil vs always-cheapest (positive = teacher better): all +0.053 [-0.098, +0.222]; below +0.029 [-0.329, +0.460]; at-or-above -0.119 [-0.282, -0.028] (worse); no-cost +0.249 [+0.086, +0.435] (better, because always-cheapest is bad there). (3) Overlap: gain over plain 0.417 [0.169, 0.700] on 16 cells sharing a label key with training, 0.198 [0.010, 0.392] on 26 that do not; the in-prompt teacher text shows the same split (0.405 vs 0.182), so this is mostly difficulty mix, not memorisation by the adapter. (4) Ceiling: both learning rates reported, 3e-4 0.118 (the pre-declared rate), 1e-4 0.026 (lower selection and tune regret); the gap to the ceiling is therefore at least 0.35, i.e. LoRA capacity is not the limit, the teacher paragraph is.
**Verdict (written after G2): frozen pass rule NOT PASSED on tune.** Teacher-distillation lowers tune regret from 0.657 to 0.376 [0.242, 0.535] (3 seeds), mostly by moving about half the probability onto the cheapest option in every case type (plain 0.04-0.12); it beats plain (+0.282 [+0.127, +0.447]) and 1-seed wrong-rule distillation (+0.214 [+0.074, +0.367]); it is not distinguishable from our hand-written paragraph's distillation (-0.003 [-0.058, +0.052]) or from always-cheapest (+0.053 [-0.098, +0.222]), and is worse than the stated-cost rule (-0.161 [-0.343, -0.005]); it harms no-cost cells (+0.190 vs plain), a fault already present in the in-prompt paragraph (0.390 vs plain 0.204) which distillation copies (0.394). Nothing here shows that the adapter learned to track the stated cost; no mechanism claim. Not a pass.
Declared limits (not fixed here because the 8 GPU-hour budget is spent; any extra runs need owner approval): wrong-rule has 1 seed (budget guard; its seeds 1-2 were scheduled after the neutral seeds, which were wasted as epoch-0 clones); neutral is not defined at a fixed epoch; no "distil the cheapest offer" control; replication on seeds 1-2 covers only the rule-1 comparisons; paragraph not revised (tune was seen). Next: GEN_TEST_PLAN.md (proposal for the owner), G3, stop.

## D. GEN_TEST_PLAN.md written (proposal) and gate G3 (Sonnet + Opus): both go-with-changes; all findings applied (reviews/2026-11-23_G3_gen-test-plan_{sonnet,opus}.md)
Changes: ordered label decision lists (every outcome gets one headline label; unit test planned), one sign convention (gain = control minus teacher), stratified bootstrap with shared indices, below-cell and not-worse-than-always-cheapest conditions in SUPPORT, P2 sensitivity with teacher seed 0 only, neutral control dropped under the default (option B / wrong-rule seeds are owner decisions D1, D2; any new run set needs G1 Sonnet), grid E (6 cells) descriptive-only, hashes cited in full from both fingerprint files, leakage check, dry run on tune before the lock, crash/deadline/bug rules. Choices I made without asking: defaults A (no neutral control) and no extra wrong-rule seeds because the 8 GPU-hour budget is spent. **Stopping here: the test script is not written, no test case has been scored. Waiting for the owner's approval of GEN_TEST_PLAN.md and an explicit go.** A second G3 on the approved text and the script is required before the go.

## New arm: Claude teaches by worked examples (owner's message Nov 23)
A. Labels. demo/gen/examples_packet.md (game rules from the original teacher packet + the 100 LoRA training cases with opaque ids c001-c100, shuffled; lines that differ only; builder demo/gen_examples_packet.py; id map demo/gen/examples_id_map.json). Blind Opus general-purpose subagent given only /tmp/examples_teacher/examples_packet.md (a copy, so the repo was not in its path) and "Read this and follow its instructions." Reply verbatim in demo/gen/examples_reply.json; all 100 ids usable, no re-ask. The teacher reported solving the cases by script (expected payoff over the uniform farm-cost prior; stated cost when given) with the lowest tied price as tie rule (40 of 100 cases have tied best prices: 28 at-or-above, 12 no-cost). Scored with demo/gen_examples_score.py (no label corrected): accuracy 1.00, regret 0.000 in all types; 65 of 100 labels are the cheapest price. Frozen demo/gen/claude_labels.json sha256 0b6f0febaa1d32302bf275bab823893db481d0386e1eccb36e52a1cbb7f95839 (demo_out/gen_examples_labels.md).
B. GEN_EXAMPLES_PLAN.md (arms claude_examples, cheapest_label, shuffled_claude in demo/gen_lora.py; chain demo/gen_examples_chain.py; budget 5 GPU-hours measured; pass rule frozen before training). Gate G1 (Sonnet + Opus; step above 3 GPU-hours): both go-with-changes, all applied (reviews/2026-11-23_G1_gen-examples_*.md): question reworded (the labels are the oracle up to a tie rule, so arm (a) is the ceiling with another tie rule and a pass is expected), shuffled control now the fewest-agreement derangement (61 of 100 labels differ; 0 of 33 at-or-above, which cannot be shuffled), tags T1-T5 (non-overlap cells, seeds 1-2, equal footing, per-type control contrasts, non-inferiority to the ceiling), definitions, INCOMPLETE rule, elapsed-time guard, frozen-hash assertion inside gen_lora.py. Smoke tests of all three new arms passed (4 cases, 1 epoch).
C. Chain launched (tmux `exlora`, log logs/gen_examples_chain.log; per-run logs logs/gen_<arm>_lr<lr>_s<seed>.log; results demo_out/gen_lora/gen_<arm>_*.json, committed and pushed after each run). Check: `tail logs/gen_examples_chain.log; ls demo_out/gen_lora | grep -E "claude|cheapest|shuffled"`. Order: claude_examples lr 1e-4 and 3e-4 (seed 0), choose lr on selection set B, cheapest_label s0, claude_examples s1-s2, shuffled_claude s0; estimate 6 x 2400 s = 4.0 h (budget 5 h).

### Worked-examples arm: result and verdict (Nov 23, tune only)
Chain finished 3.33 GPU-h of the 5 h budget (all six runs; log logs/gen_examples_chain.log; report demo_out/gen_examples_report.md; summary demo/gen/gen_examples_summary.json; script demo/gen_examples_report.py). lr chosen on selection set B: 1e-4 (0.027 vs 0.171 at 3e-4). Tune soft regret: plain 0.657, always-cheapest 0.429, (b) cheapest-label 0.429, (c) shuffled-Claude 0.695, **(a) claude-examples 0.032 (seeds 0.013 / 0.026 / 0.057; best epochs 4, 5, 2; none at epoch 0)**, answer-trained ceiling 0.026 (lr 1e-4, one seed) / 0.118 (3e-4), earlier teacher-distil 0.376. Slope on stated cost (14 below cells): (a) 0.76 = oracle 0.76; plain 0.32; (b) 0.06; (c) -0.16.

**Frozen pass rule: PASSED** (all six conditions; lower bounds: plain-a +0.430, (b)-a +0.171, always-cheapest-a +0.171, below cells +1.140; type means all improve; letter mass 1.00 vs 0.73). Tags T1-T5 all hold (non-overlap 26 cells, seeds 1-2 alone, equal footing seed 0, per-type controls, within 0.05 of the ceiling: +0.006 [-0.019, +0.028]).

Gate G2 (Sonnet + Opus, reviews/2026-11-23_G2_gen-examples-verdict_*.md): both "partly justified". **Allowed wording:** single-label supervision that equals the oracle (up to a lowest-tied-price tie rule), at 100 training cells, lowers soft regret on held-out tune cells from the same generator to near the answer-trained ceiling, and this is not just "offer cheap" (b, always-cheapest) and not any labels (c, one seed, below and no-cost cells only). **Not claimed:** that Claude "taught" anything beyond solving the cases by script; transfer to cells unlike the training cells (16 of 42 tune cells share a label key with training; T1 on the 26 others holds; under the stricter key V+C only 5 cells remain, too few); equality with the ceiling (ceiling has one seed; by type (a) - ceiling is below +0.006, at_or_above -0.042, no_cost +0.055); "examples beat instructions" (teacher-distil differs in target type, hard labels vs soft self-distillation). Conditions 2 and 3 are in effect one test ((b) = always-cheapest exactly). Disclosure: the lr grid and the expectation of a pass were set after the ceiling's tune results were known; set B chose lr independently; tune has been reused across arms (no multiplicity correction).
G2 points: applied (report script): grid[0]=min assertion on all cells, T4 into summary tags, T1b no longer short-circuited, T3 selects seed 0, T5 upper bound, per-type difference and per-seed spread shown, post-hoc rows (labelled, not in the rule): stated-cost rule minus (a) +0.182 [+0.060, +0.336] (the rule 0.214 is also the hybrid "stated cost if given, else cheapest"), per-seed (c)-(a) +0.88 to +0.94 with lower bounds > 0.6, stricter-key T1. Deferred (open review points): ceiling seeds 1-2 at lr 1e-4 (~1.2 GPU-h; not run, so no equality claim); clustering the bootstrap by (V, grid); one more training draw; (c) more seeds. Rejected: none.
Ledger regenerated (RESULTS_LEDGER.md). Test plan: GEN_EXAMPLES_TEST_PLAN.md written for the owner's approval; **no test set scored**; waiting for an explicit go.

### Worked-examples test look (Nov 23): approval, script, G3
Owner approved GEN_EXAMPLES_TEST_PLAN.md with the correction that the test sets are the generated test_same (60 cells) and test_hard (62 cells; hard_V 20, hard_grid 21, hard_wording 21), judged separately, plus reported-only rows for teacher-distil (lr 1e-4, seeds 0-2) and our-method-distil (seeds 0-2); go conditional on G3 not saying no-go. Script demo/gen_examples_test_look.py sha256 52ea926f2a8a787820ae332e8f5cc1df8156fa471843227190f75bb26ac27c10; preflight on tune cells (tmux/log logs/gen_examples_test_preflight.log, demo/gen/test_preflight.json): all 12 adapters and plain reproduce stored tune probabilities exactly (an earlier version loading several adapters into one PEFT model was inexact by up to 0.045, so adapters are now loaded one at a time and unloaded, with a clean-model recheck). G3 (Sonnet + Opus, reviews/2026-11-23_G3_gen-examples-test-look_*.md): both go-with-changes; applied: hashes of scoring code and library versions asserted by the look, fresh-output / stale-file guards, atomic writes, per-seed rows, wording flags (shuffled-label clause, overlap, slice transfer), descriptive condition 4 for fewer than 8 below cells, case-count assertions, stop-time check, disclosures and expectation in the plan. Not re-reviewed (at most once per gate; changes were mechanical and the fake-data analysis was re-run on the final script).

### Worked-examples TEST LOOK: result (Nov 23, one look, script sha256 52ea926f...; log logs/gen_examples_test_look.log; report demo_out/gen_examples_test_report.md; summary demo/gen/gen_examples_test_summary.json; lock demo/gen/test_look_lock.json status complete)
Run: tmux `tlook`, ~80 min, plain + 12 frozen adapters scored once on all 244 test cases; no crash, no re-run; no adapter/seed/epoch/lr choice on test. Expectation recorded before the look: test_same like tune (PASS); hard slices open.
**test_same (60 cells): PASSED** (all six conditions). Soft regret: plain 0.694, always-cheapest 0.764, (b) 0.764, (c) 0.935, stated-cost rule 0.247, **(a) 0.044** (seeds 0.029 / 0.026 / 0.078), ceiling 0.027, teacher-distil 0.368, our-method-distil 0.396. plain-a +0.650 [+0.459, +0.861]; (b)-a +0.720 [+0.387, +1.099]; below cells +1.512 [+1.196, +1.891]; type means all improve; letter mass 1.00 vs plain 0.80. Every (a) seed alone also beats plain, (b) and always-cheapest with lower bound > 0. Wording flags: "beyond shuffled labels" allowed ((c)-a +1.94 below, +0.63 no_cost, lower bounds > 0); "generalises to cells with new label keys" allowed (34 non-overlapping cells: plain-a +0.869 [+0.581, +1.194]). Slope on stated cost 0.68 [0.29, 0.81] vs oracle 0.69, plain 0.21. Stated-cost rule minus (a) +0.203 [+0.075, +0.353]. (a) minus ceiling -0.018 [-0.040, +0.005]; no equality claim (one ceiling seed).
**test_hard (62 cells): PASSED** (all six conditions). plain 1.297, always-cheapest 1.520, (b) 1.520, (c) 1.663, stated-cost rule 0.504, **(a) 0.171** (seeds 0.114 / 0.156 / 0.243), ceiling 0.090 ((a) is worse than the ceiling by 0.081 [0.030, 0.140] here), teacher-distil 0.959, our-method-distil 0.868. plain-a +1.126 [+0.753, +1.559]; (b)-a +1.349 [+0.788, +1.982]; below cells +2.397 [+1.671, +3.205]; type means improve; each seed passes alone; wording flags as above (53 non-overlapping cells: plain-a +1.165 [+0.734, +1.653]). Slope 0.60 [0.41, 0.78] vs oracle 0.52.
Slices (exploratory, uncorrected; plain -> (a) regret, plain-a lower bound): hard_V (20 cells) **PASSED**, 2.536 -> 0.414, +1.159; hard_grid (21) PASSED with condition 4 descriptive (7 below cells), 0.646 -> 0.029, +0.281; hard_wording (21) PASSED with condition 4 descriptive, 0.769 -> 0.082, +0.413; hard_grid D (15) PASSED with condition 4 descriptive, 0.710 -> 0.037; hard_grid E (6 cells) descriptive only, no label (conditions 2 and 3 fail on 6 cells, 2 below / 3 at-or-above / 1 no-cost). Since test_hard as a whole and each of hard_V, hard_grid, hard_wording passed, "transfer to unseen resale values, grids and wordings" is the allowed wording for those three slices, one at a time. Teacher-distil and our-method-distil (reported-only rows) beat plain on both sets (test_same +0.326 / +0.298; test_hard +0.338 / +0.429) but are far behind (a) (teacher-distil minus (a) +0.324 test_same, +0.788 test_hard).
**What this supports, and what it does not:** oracle-equivalent single-label supervision from 100 training cells lowers soft regret on the held-out generated test sets, beyond plain, always-cheapest, the cheapest-label control and the shuffled-label control, including cells with new label keys and unseen resale values, grids and wordings. Claude's labels equal the script-solved oracle up to a lowest-price tie rule, so (a) is the answer-trained ceiling with another tie rule; nothing is claimed about teaching, about equality with the ceiling (one ceiling seed; ceiling better on test_hard), or about "examples beat instructions" (different target types). Limits: intervals resample cells only (cells share V, grid, prior values), (b)/(c) one seed, one training draw, tune reused across arms. Ledger regenerated (77 rows). Nothing else was scored; test_same/test_hard are now spent for this arm and any new arm needs its own plan and go.

### Dec 2 demo build (Nov 23; no training, no new experiments, no test-set conclusions)
1. demo/floor.py --serve --dataset gen (classes GenEngine / GenFloor): generated cases of any split, display only (case header shows the split and "display only"); three PEFT adapters loaded once and switched with set_adapter: examples = claude_examples lr 1e-4 seed 1 (chosen by the lowest selection-set-B soft regret: s0 0.02702, s1 0.02691, s2 0.06658; test not used), teacher = teacher-distil seed 0, method = method_original-distil seed 0. Commands: case <id|cell id>, cost <1-12|none>, shuffle, plain, text <method|teacher|neutral>, adapter <examples|teacher|method|off>, say, table, help, quit; each prints its time (1.4-1.9 s for a new scoring on the 9B, 0.00 s cached; shuffle 0.3-0.4 s; say 0.8-0.9 s). Startup assertions (all passed): adapter off equals the pre-load plain scores bit for bit; each adapter reproduces its stored tune probabilities (< 1e-6). Choices: later adapters loaded with load_adapter were found inexact (fp32 weights differ from the files by bf16 rounding; max tune diff up to 0.045 in the test-look preflight), so every adapter's exact fp32 weights are re-copied from its safetensors file after loading; `say` runs on plain or the current adapter (not under text conditions); `steer` and `dial` are not available in gen mode; --script FILE and --log PATH added for recording.
2. Free-text check (demo/gen_say_check.py, demo_out/gen_say_check.json; 30 tune cells: first 10 per type in file order, variant n0; greedy say vs the first-token pick): agreement of the free-text offer with the first-token pick, plain / examples / teacher: 9 / 11 / 10 of 30; free-text offer on the price list: 21 / 16 / 21 of 30; hard regret of the first-token pick over the 30: 0.51 / 0.00 / 0.36; hard regret of the on-grid free-text offers: 0.56 / 0.24 / 0.72 (off-grid offers, e.g. "1 coin and 50 copper", have no comparable regret and are excluded). **Stage rule: `say` is NOT safe to show as evidence of the adapters (it disagrees with the pick on about two thirds of cases and the examples adapter's free text is worse than its pick); show it only on plain if asked, as a different channel.**
3. Live cases (rule fixed before running, demo/gen_demo_choose.py -> demo/gen/demo_live_cases.json; display selection only, no result drawn): main V3-gB-information-C2-p1_10-w1-n0 (below, plain soft regret 1.47, examples top offer = best offer 2); backup no-cost V9-gB-neutral-p3_7-w0-n0 via the declared fallback (no test_same no-cost cell reached plain regret 1 coin; used the largest, 0.83); backup at-or-above V3-gC-information-C4-p1_5-w0-n0 (plain soft regret 1.19). Scanned 2 / 8 / 20 candidates (below / at-or-above / no-cost).
4. Replay logs: demo/beats/beat1-4.txt recorded with --script/--log into demo/replays/beat1-4.jsonl; `floor.py --replay` plays each back with the "RECORDED RUN" banner on the first line (checked for all four). Replays are plain text (colour codes are stripped in logs).
5. DEMO_RUNBOOK.md: four beats with exact commands, expected numbers, timings, fallbacks (GPU down, model slow, Wi-Fi down). Unit tests added in tests/test_demo_tools.py (gen parser, cost relabelling, screens <= 25 lines x 80 columns, time printed, adapter off switch, failing engine, replay banner, seed rule); full suite 74 passed.

### test2 sets: fresh locked test cells (CPU only; nothing scored, no model loaded; Nov 23)
Step 1-2. demo/gen_test2.py (imports demo/gen_cases.py unchanged; new fixed seed 20261201; writes demo/gen/test2_cells.json, test2_cases.jsonl, test2_fingerprints.json, demo_out/gen_test2_report.md; tests tests/test_gen_test2.py, 9 pass). Two sets of 120 cells (40 per type, 2 name variants, 240 cases each): test2_same (training ranges: V 2-9, grids A-C, wordings 0-1) and test2_newkey (pair (V, stated cost or cost range) in none of the 300 train cells, which contain the 100 LoRA cells). Disjoint by cell from each other, from every cell of the first dataset (train, tune, selection A/B, loop and packet cells, LoRA cells, test_same, test_hard) and from the original study's cell space (grid A, prior 1-5, V 2-6 excluded wholesale, 144 candidates). Names from unused pool parts (buyers/sellers [480:552] and [552:624]); none from the first dataset or the old variants 1-14. All-tie cells dropped (below 1635 and at_or_above 1517 candidate evaluations; none in the sets).
Choices (logged): (i) test2_same drew only from the training ranges (enough free cells: 846 / 196 / 346 per type). (ii) test2_newkey: in-range unseen pairs per type were only 120 (below), 5 (at_or_above), 12 (no_cost) before the cap, so at most 20 per type came from the training ranges (5 and 11 for at_or_above and no_cost: all that exist after the exclusions, 20 for below) and the rest from the EXTENSION, as the owner allowed: resale values 10-15 (any resale up to 15), ONE new price grid F = (8, 10, 12, 14, 16) (plus A-C), seller wording index 3 reserved for test2 (never in the first dataset; 30 newkey cells use it; test2_same does not), wordings 0-1 also allowed. Extension cells: below 20, at_or_above 35, no_cost 29 (84 of 120). Anything that renders test2 cases must call gen_test2.install() first (adds grid F and wording 3 to gen_cases in-process; gen_cases.py is not modified, its hash is unchanged). (iii) V-balanced draw (V uniform among values with candidates, then a candidate uniformly), same scheme as gen_cases.build. (iv) "key" definitions in the report: current key (V, grid, C or prior), stricter (V, C) with C = none for no-cost cells (so every no-cost cell at a trained V shares it), and the pair (V, C or cost range) used for the newkey rule.
Counts. test2_same: below 40, at_or_above 40, no_cost 40; single best offer 100% / 18% / 52% (57% overall: at-or-above best offers tie by construction); V 2-9; share a label key with the 300 train cells: current key 25 / 36 / 19 of 40 (80 total), (V, C) key 36 / 36 / 40 (112), pair 36 / 36 / 39; with the 100 LoRA cells: current 14 / 28 / 2 (44), (V, C) 25 / 36 / 40 (101), pair 25 / 36 / 21 (82). test2_newkey: 40 / 40 / 40; single best offer 100% / 0% / 90% (63% overall); 36 in-range + 84 extension cells; current key overlap 0 with train and LoRA cells, pair overlap 0, stricter (V, C) key (no-cost cells at a trained V only) 11 cells.
Fingerprints (rendered prompts of the first name variant order, labels, cell ids): test2_same prompts c858d8c3..., labels 55cac4ea..., test2_newkey prompts ea166c75..., labels d5ea7959...; full values in demo/gen/test2_fingerprints.json together with the sha256 of gen_test2.py, gen_cases.py, cells.json, core.py and phase3.py.

### test2 sets: G1 (Sonnet) and the locked version (Nov 23; supersedes the numbers in the previous test2 entry; nothing scored, no model loaded, no GPU)
Gate G1 (Sonnet alone; step is CPU and under 1 GPU-hour): go-with-changes (reviews/2026-11-23_G1_test2-design_sonnet.md, packet /tmp/gate_G1_test2_AtLK7). Applied (all in demo/gen_test2.py, then regenerated; the earlier cells were never scored or seen by a model): (1) newkey extension stratified over its novelties (new V >= 10, new grid F, new wording 3) instead of changing all at once, per-cell flags novel_V / novel_grid / novel_wording / V_ge_13, and pre-declared slices in the report; (2) one cell per decision problem (V, grid, C or prior) per set; the at-or-above type has only 33 (training ranges) and 28-29 (newkey candidates) distinct problems, so there the cap is 2 cells per problem (test2_same at-or-above: 24 distinct problems in 40 cells; newkey at-or-above 24); distinct problems and pairs are in the report; (3) trivial references computed from labels only (uniform-random, always-cheapest, stated-cost rule regret, best-set size, share where the best offer is the cheapest price, median margin best-second) and the note that at-or-above tests avoiding overpayment, headline soft regret, never a pooled hit rate; (4) test2_same labelled a within-distribution check with strata by label key seen / unseen (key_in_lora100, key_in_train300 per cell); (5) new wording reworded to "I paid {C} for this fruit at the farm" (unambiguous cost); (6) opening scene fixed within a cell (variants differ only in names); (7) the five cyclic orders frozen and ALL five rendered into the fingerprint; (8) V 13-15 flagged as the clean extension (V 10-12 also occur in test_hard); (9) fingerprint adds sha256 of lora_train_cells.json, fruitville_haggling.py, test2_cells.json and test2_cases.jsonl; report notes the vacuous (V, C) row for no-cost, inflated drop counts (now labelled as evaluations). Not applied / recorded: the newkey definition excludes only the 300 train pairs (not pairs of tune, test_same, test_hard): stated; the V distribution is mildly uneven (V-balanced draw, not exactly flat). Tests: tests/test_gen_test2.py, 11 pass (disjointness, no ties, caps, flags, names, determinism, fingerprints record the current script, no CUDA initialised).
Final composition. test2_same (120 cells = 240 cases, training ranges only): 40 / 40 / 40 below / at_or_above / no_cost; single best offer 100% / 18% / 60%; 120 distinct-cell, problems 40 / 24 / 40; label key shared with the 300 train cells 22 / 38 / 23 (83 of 120), with the 100 LoRA cells 11 / 30 / 7 (48); stricter (V, C) key 113 and 101 (vacuous for no-cost). test2_newkey (120 cells = 240 cases): 40 / 40 / 40; in training ranges 13 / 2 / 3 (18) and extension 27 / 38 / 37 (102); single best offer 95% / 45% / 95%; pair and current-key overlap with train and LoRA cells 0 (the stricter (V, C) key matches 4 no-cost cells at a trained V); grids A 15, B 19, C 13, F 73; wordings 0: 32, 1: 38, 3: 50; V 2-15. References from labels (below / at_or_above / no_cost): test2_same always-cheapest regret 1.23 / 0.00 / 0.52, stated-cost rule 0.00 / 0.00 / 0.52; test2_newkey always-cheapest 2.48 / 0.00 / 1.70, stated-cost rule 0.00 / 0.00 / 1.70 (so "offer cheap" is a perfect policy on at-or-above cells of both sets and the stated-cost rule is an oracle on below cells).
Frozen before any scoring (recorded here; the rest is for the test plan and G3, which are not part of this task): sets and fingerprints in demo/gen/test2_fingerprints.json (rendered prompts at all five frozen cyclic orders, labels, cell ids; script, generator, first-dataset cells, core.py, phase3.py, LoRA cell list, haggling module and output files hashed); install() must be called before rendering; the sets are never used for selection, tuning or design; one look only, after a written plan, G3 (Sonnet + Opus) and an explicit owner go. Primary metric to be fixed in that plan: cell-mean soft regret over the two name variants and five orders, reported per type and per slice (never one pooled newkey number), clustered by problem, with the references above.

### Learning curve and rules-vs-examples (owner message Nov 23): plan, G1, freeze (before any run)
Written and committed before any GPU work: GEN_CURVE_PLAN.md (nested type-stratified subsets N = 10, 25, 50, 100 of the 100 LoRA cells, demo/gen_curve.py -> demo/gen/curve_subsets.json; arms examples-N x3 seeds, rule-soft-N and rule-hard-N at N = 25 and 100, cheapest-label-25; lr 1e-4; 500 optimizer steps at every N), PREDICTIONS.md (commit 08f904f, revised after G1 below, still before any run). Gate G1 (Sonnet + Opus; the step is about 8 GPU-hours): both go-with-changes (reviews/2026-11-23_G1_curve_{sonnet,opus}.md). Applied: mechanical prediction scoring rule and split probability statements (Brier) in PREDICTIONS.md and demo/gen_curve_report.py; (V, grid)-clustered bootstrap as the interval for every "lower bound > 0"; argmax (hard) regret per arm; target regrets, distinct training problems, covered/uncovered tune cells and cheapest-label share per subset; rule-hard order-disagreement logged; extra early set-B scorings (step 20 and 50 at N = 10, step 50 at N = 25 and 50); run order with examples-50 seed 0 as the third run; per-run estimate raised to 2300 s (13 runs = 8.3 GPU-hours before early stopping, so a budget cut of the last runs is likely and planned); label metadata computed over the subset; code sha256 and git head in every run result; teacher paragraph sha asserted; report asserts each loaded run's arm, lr, N, training cells and schedule; freeze record demo/gen/curve_freeze.json (inputs, six reused N = 100 runs, code, plan, predictions, library versions) asserted by the chain and the report; no-peeking rule (no change after the first run completes). Declared limits added (lr/steps from N = 100, one subset draw, incomplete 2x2, rule-hard order noise). Not applied: per-seed subset redraws and an examples-soft arm (budget); no second G1 round (a re-review is optional and the changes are mechanical). Smoke tests (2 cases, 20 steps) of rule_hard N=10 and claude_examples N=25 passed; smoke outputs deleted.
Choices: the subsets are one fixed draw (owner's fixed-seed nested request); rule-soft-100 uses the existing teacher-distil seeds 0-2 (seed 0 for equal-footing comparisons with single-seed arms); examples-100 reuses the three existing runs (same procedure at N = 100, verified by the report's config assertions).
Curve chain launched Nov 23 19:42 UTC (tmux `curve`, log logs/gen_curve_chain.log, per-run logs logs/gen_<arm>_n<N>_lr1e-04_s<seed>.log, results demo_out/gen_lora/gen_*_n*_lr1e-04_s*.json plus gen_rule_hard_lr1e-04_s0.json, committed and pushed after each run; status demo/gen/gen_curve_chain_status.json if the budget guard fires). Check: `tail logs/gen_curve_chain.log; ls demo_out/gen_lora | grep -E "_n(10|25|50)_|rule_hard"`. Expected end about 04:00 UTC Nov 24 if all 13 runs fit (the guard cuts the last runs otherwise). Report after the chain: `PYTHONPATH=concordia:. .venv/bin/python demo/gen_curve_report.py`.

### Learning curve and rules-vs-examples: results and G2 (Nov 24)
Chain finished Nov 24 03:05 UTC: all 13 runs, 7.35 GPU-hours (no budget cut). Report: demo_out/gen_curve_report.md (script demo/gen_curve_report.py, unchanged); post-G2 CPU follow-up: demo_out/gen_curve_followup.md (demo/gen_curve_followup.py; post hoc, labelled; tune only). Gate G2 (Sonnet + Opus): both "partly justified" (reviews/2026-11-24_G2_curve_{sonnet,opus}.md). Applied: corrected tally, uncovered-cell curve with intervals, seed-and-cluster bootstrap, per-seed counts, hard-vs-soft bound, rewording below. Not applied (budget/limits): second subset draw at N = 10, examples-soft arm, rule-hard with order-averaged argmax per case; listed as open points.

Conclusions (tune cells, Gemma 2 9B-it, lr 1e-4, 500 steps, one nested subset draw; descriptive):
- Curve (3 seeds): examples-10 0.092, -25 0.042, -50 0.040, -100 0.032 (plain 0.657, always-cheapest 0.429). On the 26 tune cells whose problem is not in the N = 100 training subset: 0.137, 0.055, 0.050, 0.046. N = 25 is the smallest tested size whose estimate is within 0.05 of examples-100 (+0.010, all 3 seeds within 0.05); the curve is flat from 25 to 100 within noise. N = 10 is borderline (2 of 3 seeds within 0.05; seed-and-cluster interval [+0.000, +0.156]; all three seeds were still improving at step 500). Part of the curve is coverage of tune problems by the training subset (3, 9, 12, 16 of 42 cells at N = 10, 25, 50, 100).
- Rules vs examples: with the in-prompt paragraph's behaviour as content, rule-soft and rule-hard sit at 0.34-0.38 (0.43-0.52 on uncovered cells), +0.30 to +0.34 above examples at the same N (lower bounds > +0.18). The comparison is oracle-correct labels vs the paragraph's own behaviour (tune argmax regret 0.41); the rule students track their teacher. Hard vs soft: -0.035 [-0.106, +0.018] at N = 25 and -0.029 [-0.096, +0.017] at N = 100, within the rule-soft-100 seed spread (0.043), single seeds; the intervals allow hard targets to have closed up to 28-31% of the gap (point 8-11%). Not shown: that the kind of target does not matter (no examples-soft arm; rule-hard targets disagree across orders in 56-60% of cases).
- Cheapest-label-25 = always-cheapest (0.429), a weak control since 62-70% of Claude labels are already cheapest.
- Slopes on stated cost: examples N >= 25 about 0.75; examples-10 0.66; rule arms 0.26-0.34 (about plain's 0.32; two intervals include 0).
- Prediction scores (corrected): HELD 23, FAILED 3 (P1a examples-10 and P1b examples-25 better than predicted; P6c examples-10 slope above range), plus Brier statements P2a-c, P8b (mean 0.124; P2a and P8b were wrong). The predictions leaned toward needing more data than the curve did.
Open review points: second subset draw at N = 10/25; examples-soft arm; rule-hard with one order-averaged argmax per case; rule-arm seeds; test-set freeze items (arms, N, seed aggregation, uncovered-problem primary metric, margin with CI rule) go into GEN2_TEST_PLAN.md.

### LLAMA_PREDICTIONS.md and GEN2_TEST_PLAN.md (Nov 24)
LLAMA_PREDICTIONS.md committed before any Llama code (plain pattern, in-prompt gains of our and the teacher paragraph, steering failure, examples learning curve; each with a number and direction). GEN2_TEST_PLAN.md written for the owner's approval (frozen adapters by sha256, test2_same and test2_newkey, primary metric cell-mean soft regret per type and per novelty slice clustered by problem and by (V, grid), pass rule, curve and rules-vs-examples claims, wording). Gate G3 (Sonnet + Opus): both go-with-changes (reviews/2026-11-24_G3_gen2-plan_{sonnet,opus}.md); all points applied in section 7b (earlier look disclosed, mutually exclusive slices by type, per-seed and absolute bars, relative curve margin, estimator, primary claims, overlap strata, look-script requirements). Open: the look script is not written yet (after approval: write, record sha256, G3 on plan + script, one look). Nothing scored on test2_same or test2_newkey. Waiting for the owner's explicit go.
