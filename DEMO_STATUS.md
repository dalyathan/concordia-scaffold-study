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

- The first run used six cases of which two pairs became identical prompts once the cost was overridden (same variant and V). A rerun with six distinct prompts is queued (`logs/demo_step2_dial.log`); the results below are from the first run, de-duplicated.
- Gemma offers **2 coins almost whatever the stated cost**: cost 1 → 2 (overpay); cost 3 → 2 (refused); cost 4 → 2 (refused when V > 4). When the stated cost is 2, it offers *more* (3–4).

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

## Step 7: tuning job (tuning cases only) — launched, running

`demo/tune_job.py`, using `steercheck.run_controls`.

- **Grid** (29 points ≤ 30): no steering, plus layers 6, 9, 12, 15, 18, 21, 24 (the first 7 of `steering.LAYERS`) × `steering.ALPHAS` (0.5, 1, 2, 4). α multiplies the vector.
- **Full budget** (five orders): template, offer_lower, sentence, and the negated template.
- **Matched budget** (one order per case, `cyclic_orders()[(variant − 1) mod 5]`): template, 20 random directions and 5 Gaussian directions, all rescaled to the template's norm at each layer.
  - Random directions: differences of plain P1 activations between two tuning cases from different cells, with pairs drawn using PCG64 seed 11.
  - Gaussian directions: PCG64 seed 12.
- **Tuning rule:** the setting with the lowest mean cell soft regret among coherent settings, where coherent means mean letter mass ≥ 0.9 × plain. "No steering" is always an option.
- **Analysis.** The unit of analysis is the cell (17 tuning cells). Intervals: 2,000 bootstrap resamples of cells. Tuning and evaluation use the same tuning cases, so results are in-sample and labelled so. No test case is touched.
- **Estimate** (20 passes timed first, `logs/demo_tune_estimate.log`): 0.294 s per pass × 45,560 passes (19,040 full budget, 24,752 matched, the rest evaluations) = **3.7 hours**.
- **Started:** 04:23, under nohup in tmux session `tune`.

Check command:

```bash
grep -v "Loading\|Warn\|warn\|torch.load" logs/demo_tune_job.log | tail -40   # progress and, at the end, the table
python demo/steercheck.py --results demo_out/tune_results.json                  # the table once finished
```
