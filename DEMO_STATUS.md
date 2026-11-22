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
