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
