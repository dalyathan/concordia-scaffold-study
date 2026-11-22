# Experiment design: activation recording in the 2024 Concordia haggling setup

This protocol takes the top three agents of the NeurIPS 2024 Concordia Contest and asks, on the contest model (Gemma 2 9B instruction-tuned) and code (Concordia v1.8.9):

1. Facing identical conversations and prices, do they choose better buying offers than the contest's rational baseline?
2. Does the reasoning text they feed the model improve its offers on its own, beyond adding length and beyond simply naming an answer?
3. Can that improvement be reproduced by adding one direction to the model's activations, and does that direction move each offer towards its own optimum rather than shifting all offers alike?

The game is a single buying decision with a stated cost prior and acceptance rule, so every prompt has a known best offer. Outcomes are scored as **regret**, the shortfall from that best offer. Ten confirmatory tests, eleven if the pilot triggers the design extension (section 6), form one Holm family at α = 0.05. Each test ends in one of four pre-registered verdicts:

- **supported**;
- **reversed**, meaning significantly worse in the opposite direction;
- **equivalent**, meaning the effect is within a smallest effect of interest;
- **inconclusive**.

The protocol, code and analysis scripts are hash-committed before any model is run, including the pilot. A tested reference implementation of the harness, conditions, pipeline and analysis is in the REFERENCE.md.

## 1. Questions, outcomes and hypotheses

**1.1 Motivation.** Scaffolds are the main way practitioners improve a fixed model, but whether they work through reasoning or through incidental effects is rarely tested. Incidental effects include control code, extra length, and text that simply names an answer. The contest entries are scaffolds that were evaluated publicly on one fixed model. A game with a known optimum makes their effect measurable, and an activation-level test asks whether the useful part can be moved into the model itself.

**1.2 Game and outcomes.** The buyer has private resale value V and proposes k ∈ {1, …, 5} coins. Its memories state the rules (section 8.3): seller costs C are uniform on 1–5, a seller accepts any offer at or above their cost, and a stated cost is true. The payoff is V − k if accepted and 0 otherwise.

| Prompt type | Payoff of offer k | Best offer (payoff) |
| --- | --- | --- |
| No information about C | Expected over the prior: (V − k) · k / 5 | V = 2: 1 (0.2); 3: 1 or 2 (0.4); 4: 2 (0.8); 5: 2 or 3 (1.2); 6: 3 (1.8) |
| Seller states C | V − k if k ≥ C, else 0 | C < V: k = C (V − C). C ≥ V: any k < C, or k = C when C = V (0) |

- **Regret** = best payoff minus the payoff of the offer; it is 0 at best. Where C ≥ V, regret is k − V for an accepted offer above V, so those cells measure overpaying.
- **Hard regret** uses the chosen offer.
- **Soft regret** uses p(k). In Phase 3 and 3b (primary), p(k) is the model's next-token probability for each option letter at the decision position P1, renormalised over the five letters, with no extra temperature and averaged over five option orders. This is the quantity steering acts on directly. The prompt format is Concordia's own choice format: the user turn ends with `Answer: (` and the assistant's answer is the letter, so the letter is the model's first answer token.
- **Sensitivity.** Whole-answer scoring, as in Concordia's choice calls (letter, end-of-turn, newline), is reported for every Phase 3 and 3b test. Its end-of-turn terms vary by letter and can dominate the score. Phase 2 decisions use whole-answer scoring because that is what the agents' own choice calls do; the native replay (9.4) puts them on the first-token scale.
- **Disagreement rule (fixed now).** Every B, R and K test is also computed with whole-answer p(k). If a test is "supported" on the primary scale but its whole-answer mean effect has the opposite sign, the verdict is reported as "supported (scoring-sensitive)", and the claim is restricted to the first-token readout.
- **Letter mass.** The unrenormalised probability on the five letters is reported per condition, because a small letter mass means the renormalised p(k) describes only part of the model's output. Where the rest goes is reported too: the five most probable non-letter tokens at P1, with their mean probability, per condition. A B or R comparison whose two conditions differ in mean letter mass by more than 0.10 at the cell level, in any cell, is labelled "letter-mass-sensitive"; steering is held to its own coherence rule (10.4). On a 9B smoke-test prompt the two scorings agreed on the top choice in 3 of 5 orders, and the letter mass was 0.46–0.82, mean 0.57 (REFERENCE.md, R3).
- **Calibration.** For a change in conditions, ask whether the per-cell shift in expected offer tracks each cell's best offer once the cell's starting expected offer is held fixed. This is a partial correlation, so offers that merely regress towards a common price do not count (section 10.5).

**1.3 Confirmatory hypotheses** (one-sided, one Holm family of ten tests, or eleven with K2 when the extension is in force; section 11). "Entry" means each of `taehun_cgcal`, `fluffy_fluffyagent_v16submission` and `hgyun_loss_aversion_agent_v3_plus2`, tested separately. N-codes are the Phase 3 text conditions (section 9.2).

| Tests | Phase | Hypothesis | Pass rule |
| --- | --- | --- | --- |
| A1–A3 | 2 | The entry, as a full agent, has lower hard regret than `rational_agent` on identical prompts | One cell-level test |
| B1–B3 | 3 | The entry's reasoning text helps, and helps because it is about this prompt. It gives lower soft regret than each of: no text (N0); the baseline's text (N1); format-matched filler of identical length (N6); and the entry's own text written for a nearby prompt whose best offer differs (N7), which is on-topic and has the same style and similar length | All four comparisons significant (intersection–union) |
| R1–R3 | 3 | The entry's text helps without its price advice. With advice-bearing sentences removed (N8), it still beats no text (N0) and the baseline's text with the same removal applied (N1s) | Both comparisons significant |
| K1 | 3b | Adding the entries' pooled text-induced direction to the baseline prompt lowers soft regret on held-out cells. It must do so more than each of: three separately tuned null directions; a sharpening null that only makes the existing distribution more confident; and 1,000 natural random directions tuned and evaluated on exactly the same budget as a matched copy of the content direction (permutation p) | All six components significant; one p-value (the largest) enters Holm |
| K2 | 3b | That steering is calibrated. On held-out cells with a single best offer, its per-cell offer shifts track each cell's best offer with the cell's starting offer partialled out. They must do so more strongly than five matched controls: a uniform tilt, a pull towards any single fixed price, regression towards the centre, sharpening, and the steered answer-only null | All components significant; one p-value enters Holm. **Confirmatory only when the V = 7, 8 extension is in force** (19 test cells with a single best offer); otherwise K2 is a secondary test (1.5) |

**1.4 Smallest effects of interest.**

- **Regret: 0.05 coins.** The mean best payoff over the 35 cells is 1.25 coins, so this is 4% of it. It is also the regret of offering one coin too much on 1 prompt in 20.
- **K2: a partial-correlation difference of 0.2.** With 12 cells, the 90% interval of a partial-correlation difference is expected to be wider than ±0.2, so K2 can realistically end only "supported", "reversed" or "inconclusive". This is stated now so that "inconclusive" is not over-read.
- **Why K2's family depends on the extension.** K2's tests are exact or permutation tests over cells (10.5). With the 12 unique-best test cells of the 35-cell grid, even steering that puts 96% of each prompt's mass on its best offer cannot pass them at the Holm level: in the unit-tested synthetic case the partial correlation reaches p = 0.006 and the comparison with the flatten control p ≈ 0.28. With the extension's 19 cells the same steering passes every component at p ≤ 0.0012 (`tests/test_design.py`). A confirmatory test that cannot pass whatever the truth only uses up Holm's budget, so K2 is confirmatory with the extension and secondary (Benjamini–Hochberg, 1.5) without it. The rule is fixed now and is applied by `analysis.confirmatory_family`.

The verdicts are:

- **Supported:** the test passes Holm.
- **Reversed:** the opposite-direction test passes Holm at α = 0.01 within its own family of the same tests. By the union bound, which needs no independence between the two families, the probability of any false directional claim across both is at most 0.05 + 0.01 = 0.06.
- **Equivalent:** neither of the above, and the test's equivalence p-value passes a third Holm family at α = 0.05, formed by the tests that are neither supported nor reversed. The equivalence p-value is a two-one-sided-tests (TOST) p from the cell bootstrap: the larger of the bootstrap shares of the effect at or below −bound and at or above +bound (`analysis.bootstrap_equivalence_p`). Unadjusted, it is below 0.05 exactly when the 90% percentile interval lies inside ± the bound; Holm controls the chance of any false "equivalent" across the family.
- **Inconclusive:** none of the above.

**1.5 Secondary questions** (one Benjamini–Hochberg family, q = 0.05; each a one-sided cell-level sign-flip test, as in section 11, unless stated):

- **E1:** Phase 2 under contest sampling (temperature 0.5). For each entry, the mean over 5 draws of D (8.5), tested at cell level on all 35 cells of the E1 subset (8.6).
- **E2:** calibration of each entry's text itself. The K2 partial correlation, computed for Ne versus N1 instead of steered versus unsteered, against the same controls.
- **E3:** K1 on each entry's own content direction (three tests).
- **E4:** the baseline's bid bias: mean expected offer minus mean best offer, under N0 and under N1. Two-sided.
- **E5:** wording (N5 versus own text, two-sided) and length alone (each entry's N6 versus the baseline's N6). Two answer-naming lines are reported descriptively, not tested:
  - N9, which names the entry's own offer: how much of the text's effect a line naming its answer gives;
  - N10, which names the best offer: an upper bound.

  Each entry's own offer equals the best offer at a rate that is reported.
- **E6:** K1 with the content direction's component in the span of the letter unembedding rows (a–e) projected out (section 10.6).
- **E7:** B and R recomputed on S\_reason (N2r–N4r), the reasoning text with memory-summary calls removed.
- **E8:** per-entry heterogeneity in Phase 3: a sign-flip test on the cell-level difference between the best and worst entry's Ne. If significant, E3, the per-entry directions, are the primary reading of 3b.
- **E9:** fidelity of steering. This is the share of the text effect that steering reproduces on test cells: the mean cell difference (N1 − steered N1) divided by the mean cell difference (N1 − mean of N2–N4), with a 95% bootstrap interval. Descriptive.

**1.6 Reading the results.** Phases 3 and 3b run whatever A shows, because they ask what the text does inside one model.

| Result | Reading |
| --- | --- |
| A supported, B supported | The entry's advantage is at least partly carried by its text; R says whether beyond the answer |
| A supported, B not supported | Evidence the advantage is outside the transplanted text (control code, native template or retrieval). Interpret alongside the native replay (section 9.4) |
| A not supported, B supported | The text helps when isolated, but the full agent does not convert it into better choices |
| K1 and K2 supported | One mid-layer direction reproduces part of the effect (E9 says how much) and moves offers towards each prompt's own optimum |
| B not supported, K1 supported | The direction lowers regret, but since the text itself does not, K1 cannot be read as "reproducing the text's effect". It is reported as a steering result only |
| K1 supported, K2 not | The direction mainly shifts or concentrates offers without regard to each cell's optimum |
| K1 supported, E6 not | The effect may be largely a direct push on the answer letters rather than a change upstream of the readout |
| K1 not supported | No single mean-difference direction at the tested layers reproduces the effect; other mechanisms are not ruled out |
| Any test reversed | The entry, or its text, makes offers worse than the comparison |

"Not supported" is always split into reversed, equivalent or inconclusive (1.4).

**Inferential target.** The 35 cells are fixed design points, not a sample from a population of games. Confirmatory claims are about the average effect over this pre-specified grid, with name and opening variation averaged out within each cell. The crossed mixed model (section 11) adds a generalisation over name and opening variants.

**1.7 Agent choice.** The three entries are fixed by their final contest rank, which was earned across all scenarios, not haggling alone. Nothing is selected on results here.

## 2. Design at a glance

Each phase removes one confound left by the previous one. A naive comparison of agents' activations is confounded twice: agents send different prompt text, so activations differ trivially, and model-generated seller speech makes games diverge after the first turn.

| Phase | Purpose | Varies | Held fixed | Output |
| --- | --- | --- | --- | --- |
| 0 | Validate the harness; baseline-only pilot | — | Everything | Pass/fail log; pilot estimates (variants 13–14, baseline quantities only) |
| 1 | Show native behaviour (descriptive) | Focal agent | Scenarios, seeds, contest sampling | Scores per simulation |
| 2 | Remove conversation drift | Agent (5) | Identical scripted conversation and memories; greedy decoding | Hard regret (A1–A3); each agent's reasoning text S |
| 3 | Remove template differences | Inserted text (28 conditions) | One fixed decision prompt | Soft regret (B, R); activations |
| 3b | Test causation | Direction added to the baseline prompt | Everything else | Regret change and calibration under steering (K1, K2) |

## 3. Pinned inputs

| Input | Pin |
| --- | --- |
| Concordia | [v1.8.9](https://github.com/google-deepmind/concordia/tree/v1.8.9), commit `3643ac0466f748b8055b61feb0b7908411f73d84` |
| Contest agent code | [NeurIPS supplementary zip](https://proceedings.neurips.cc/paper_files/paper/2025/file/d0251bbbc0288f241b878775ba1735dc-Supplemental-Datasets_and_Benchmarks_Track.zip), 4,537,615 bytes, SHA-256 `e9ffb65167d776fd4beae14ee65cd3b44ec9c489870698c203f7acdefc199582`. Its `rational_agent.py` is byte-identical to Concordia's own `concordia/factory/agent/rational_agent.py` |
| Model | [`google/gemma-2-9b-it`](https://huggingface.co/google/gemma-2-9b-it) (gated; accept the licence), loaded in bfloat16 with `attn_implementation="eager"`, which Gemma 2's logit soft-capping needs. Loaded with `revision="11c9b309abf73637e4b6f9a3fa1e92e615547819"`, the repository's latest commit (27 August 2024, unchanged since). At load, P0.1 checks each weight shard's SHA-256 against the LFS hashes listed at that commit |
| Expected architecture (check P0.1) | 42 layers, hidden size 3,584, 16 query and 8 key-value heads, head dimension 256, alternating local (4,096-token window) and global attention, soft-caps 50 (attention) and 30 (final), vocabulary 256,000 ([Gemma 2 report](https://arxiv.org/abs/2408.00118)) |
| Memory embedder | `sentence-transformers/all-mpnet-base-v2` (the v1.8.9 launcher default), `revision="e8c3b32edf5434bc2275fc9bab85f82640a19130"` |
| Smoke-test model | `google/gemma-2-2b-it`, `revision="299a8560bedf22ed1c72a8a11e7dce4a7f9f51f8"`: same architecture family, used only for CPU tests of the code |
| Python | 3.11; torch 2.4.1, transformers 4.44.2, accelerate 0.34.2, sentence-transformers 3.0.1, numpy 1.26.4, scipy 1.14.1, pandas 2.0.3 (Concordia requires ≤ 2.0.3), plus Concordia's and its examples' other requirements, frozen in `requirements.lock` (159 packages, shipped with the code). The lock was resolved with the CPU build of torch 2.4.1 for the CPU tests. The GPU runs install the same lock with `torch==2.4.1` from PyPI (the CUDA 12.1 build), the `nvidia-*` packages it pulls in and `pyarrow==17.0.0` (for the memory banks), frozen as `requirements.gpu.lock` (173 packages). The reference implementation's unit tests and 9B smoke tests pass on exactly this GPU stack (REFERENCE.md, R3) |
| R (sensitivity models only) | R 4.4.1, lme4 1.1-35, lmerTest 3.1-3 |
| Sparse autoencoders (exploratory) | [`google/gemma-scope-9b-it-res`](https://huggingface.co/google/gemma-scope-9b-it-res), layers 9, 20 and 31, width 16k |
| Hardware | Confirmatory runs: one 48 GB GPU of a model named in the registration file (for example an NVIDIA L40S), with CUDA and driver versions recorded there; to be decided at registration. Exact repeatability (check P0.7) is required on that configuration only. The formative-memory banks were generated, and the development checks run, on one NVIDIA A10G (24 GB), recorded in the registration file as the bank-generation and development hardware |

## 4. Model serving

The contest called Gemma through Together AI with `concordia/language_model/together_ai.py:Gemma2`. Here a local class, `LocalGemma2` (`refimpl/local_gemma2.py`), implements the same v1.8.9 `LanguageModel` interface. All phases use it.

- **Free text (`sample_text`).** The message list is copied from `Gemma2.sample_text`: the system text (verbatim in the code), two few-shot exchanges ("Is Jake a turtle?" / "not a turtle."; "What is Priya doing right now?" / "sleeping."), then the prompt. Gemma's template has no system role, so the system text is prepended to the first user turn, separated by a blank line. The list is rendered with the pinned tokenizer's chat template.
- **Sampling.** Phase 1 uses the caller's temperature (Concordia default 0.5) with top-p 1 and top-k off. Phases 2–3 use temperature 0 (greedy) for every call. Max new tokens is min(caller's value, 5,000). Generation stops at the end-of-turn token or at the first caller terminator, and the text is cut before that terminator.
- **Trimming.** `ensure_prompt_not_too_long` is copied from v1.8.9: a 7,000-token budget at 4 characters per token, keeping the first 2,000 characters and the end. If the rendered input plus new tokens exceeds 8,192, it re-trims at 1 character per token.
- **Choices (`sample_choice`).** Concordia's `multiple_choice_question` shuffles options, labels them (a), (b)… and ends the prompt with `Answer: (`.
  - Each label letter is appended as the whole assistant answer, under the choice system text and the same few-shots.
  - Its score is the summed log-probability of every token after the last `<start_of_turn>model\n`: the letter, `<end_of_turn>` and newline, as Together's echoed log-probabilities were.
  - The choice is the argmax, with ties going to the first option.
  - Letters are single tokens, so all candidates have equal length. They are scored **sequentially**: one candidate per forward pass, batch size 1 (`LocalGemma2.letter_scores`, `sequential=True`). This mode is fixed for every run and every GPU; it never depends on free memory. Batched eager attention over five long prompts does not fit in 24 GB, and a fixed mode keeps shapes, and therefore rounding, identical everywhere.
  - **P1 pass.** The first-token distribution at P1 (the Phase 3 primary and the letter mass) is read from one further pass over the prefix alone. It is mathematically the same distribution as at P1 in each of the five answer passes, and one fixed pass gives one value instead of five that can differ in the last bits. Phase 3b tuning, which needs only this distribution, runs the P1 pass alone.
  - Only the positions that predict answer tokens are unembedded. The final soft-cap (30) and the log-softmax are computed in float32.
  - A batched mode (all candidates in one pass) is kept only for check P0.2, which reports the batched-versus-sequential difference on short prompts.
- **Prefill unembedding in generation.** transformers 4.44.2's Gemma 2 forward unembeds every prompt position during generation's prefill and copies the logits to float32, about 1.5–2 GB per 1,000 prompt tokens, although only the last position is used. On a 24 GB GPU that ran out of memory from about 2,400 prompt tokens. `sample_text` therefore registers a pre-hook on the unembedding during `generate` that passes it only the last position (`LocalGemma2._last_position_unembedding`). The sampled tokens depend only on that position, so this is the same computation with a smaller matrix product; it is part of the registered code, and its peak memory is reported in REFERENCE.md, R3.
- **Determinism (Phases 2–3; `refimpl/determinism.py`).**
  - Thread pools are replaced by a sequential executor, which also covers Concordia's `concurrency` helpers.
  - Each call is seeded from SHA-256 over the UTF-8 encoding of (prompt, agent, prompt ID, draw index), joined by U+001F; the first 8 bytes are read big-endian. This seeds `random`, the legacy `numpy.random` and torch.
  - Unseeded `numpy.random.default_rng()` calls get a seed from the call context plus a counter that resets at each decision.
  - At the start of every decision, `random`, the legacy `numpy.random` and torch are seeded from the same hash over ("decision-start", agent, prompt ID, draw). `AssociativeMemory.add` samples memories with pandas `DataFrame.sample(random_state=None)`, which uses numpy's global state, before any model call has re-seeded it.
  - Before every generation, the model's stored generation cache is deleted. transformers 4.44.2 otherwise reuses Gemma 2's cache whenever an earlier call left a large enough one, so attention shapes, and therefore floating-point rounding, would depend on call history. On the pinned stack this flipped a greedy token between two otherwise identical runs (REFERENCE.md, R3).
  - `torch.use_deterministic_algorithms(True)` and `CUBLAS_WORKSPACE_CONFIG=:4096:8` are set.

Together's handling of the system message and its sampling defaults are unknown; check P0.3 measures the system-message effect.

## 5. Agents

Five agents are imported from the zip's `agent_py_files/`, unmodified. The only setup is putting the directory that contains `agent_py_files/` on `PYTHONPATH`, so they import as `agent_py_files.<name>`. Each module's own `build_agent(config, model, memory, clock, update_time_interval)` is called, exactly as `haggling.py` calls it. `rational_agent` is imported from Concordia (`concordia.factory.agent.rational_agent`), whose copy is byte-identical. A static audit of the three entry files found no network, subprocess, `eval`/`exec` or file-writing calls; `fluffy`'s file writes are commented out. The agents still run inside a container without network access.

| File | Role | Final contest rank | Where the offer is decided |
| --- | --- | --- | --- |
| `rational_agent.py` | Baseline | — | Option and best-option questions, then a final multiple-choice call |
| `basic_agent.py` | Second baseline (exploratory only) | — | Self, situation and person questions, then a final multiple-choice call |
| `taehun_cgcal.py` (Taehun Cha) | Entry | 1st | Asks whether payoffs are numeric. If yes, asks the model for each option's expected profit and picks the highest **in Python** (ties by `np.random.choice`); otherwise a final multiple-choice call |
| `fluffy_fluffyagent_v16submission.py` (Avinaash Anand K) | Entry | 2nd | Four long reasoning components, then a final multiple-choice call |
| `hgyun_loss_aversion_agent_v3_plus2.py` (Hyeonggeun Yun) | Entry | 3rd | Rational-style components plus a loss-evaluation component, then a final multiple-choice call |

Ranks are from the contest's final cross-play among the top six ([contest paper](https://arxiv.org/abs/2512.03318)). Because `taehun_cgcal` can decide in code, this protocol never compares agents' activations at "the final choice call". Phase 2 compares behaviour; Phase 3 compares text inside one shared decision call.

## 6. Phase 0: checks and pilot

Every check must pass, or have its deviation logged, before Phase 1 and Phase 2 start. Registration comes first (see Order below). Native pilot simulations use seeds 101–103.

| Check | Procedure | Pass criterion |
| --- | --- | --- |
| P0.1 Model config | Compare `config.json` at the pinned revision with section 3; check all four weight shards' SHA-256 against the LFS hashes at that commit | All values and hashes match |
| P0.2 Choice scoring | Batched versus sequential scoring on short prompts: on 50 captured short choice prompts, score the five letters in one batch and one per pass (the registered mode) | Reported: maximum absolute difference in nats against 10⁻³, and argmax agreement. Not a gate, because all runs use sequential scoring |
| P0.3 System folding | On 200 captured choice calls, argmax with the system text folded versus omitted | Report agreement. Below 90%: run Phase 1 both ways and report both, "folded" primary |
| P0.4 Observation format | Log every string a player receives through `observe()` in 3 native `haggling_0` runs | Expected utterance format `{speaker} -- "{utterance}"`. If different, the captured format is used and logged |
| P0.5 Seeds | `haggling.py` line 622 reads `self._rng = random.Random(sampled_settings.random_seed)`, and `random_seed` defaults to 42 (line 109). Replace line 622 with `self._rng = random.Random(sampled_settings.random_seed if seed is None else seed)` (the launcher already passes `seed=args.seed + repetition_idx`). Run two seeds | Sampled names, values and costs differ |
| P0.6 Agent smoke test | All five agents, real formative memories, all-mpnet-base-v2, 9B on the registered GPU: one native `haggling_1` game and one Phase 2 prompt each | No exceptions; each agent's S is non-empty |
| P0.7 Determinism | Rerun 40 Phase 2 decisions (8 per agent) and 100 Phase 3 prompts | Offers and reasoning texts byte-identical; scores bit-identical (the scorer always runs sequentially, batch size 1, with fixed shapes) |
| P0.8 Sequential execution | Log the thread of every model call in 10 decisions | One thread, submission order |
| P0.9 Steering hook | Add a zero vector through the hook on 50 prompts | Probabilities bit-identical to unhooked scoring |
| P0.10 Unit tests | `tests/test_core.py`, `tests/test_design.py`, `tests/test_banks.py` and `tests/test_report.py` (38 tests): prompt counts and extension cells, best-offer table, regret, cell split, seeds, per-call seeding only inside a call context, S entries with stems, removal rules, filler, condition set, the pilot's conditions read only baseline data, N7 donors (34 of 35 cells, 48 of 49 with the extension, disjoint; deterministic), audit prompt, memory-bank save-and-reload equality and duplicate rejection (hashes recomputed in a fresh process), the no-steering tuner option, sign-flip, bootstrap-t, Holm, IUT, BH, reverse rule, verdicts, the family rule and TOST equivalence, power simulation and the projected cell SD, A/B/R assembly, K1 including the sharpening null, K2 (unique-best cells; exact swap test; attractor, flatten and sharpening do not pass; oracle steering passes with 19 cells and cannot beat flatten with 12), and a synthetic end-to-end run of the registered analysis including the exclusion rule | All pass |
| P0.11 Runtime and memory | Time and peak memory for 5 prompts × 5 agents (Phase 2) and 50 prompts (Phase 3) | Used for scheduling only |

**Order.**

1. The 14 formative-memory banks are generated (section 8.3). This produces no outcome.
2. This document, the code, the analysis scripts, the lock file and the SHA-256 of each memory bank are registered (hash-committed), and the banks are published.
3. The Phase 0 checks and the pilot then run.

Engineering checks that record no outcome may precede registration: environment and hash checks, unit tests, scoring parity, memory and timing measurements, and agent runs that record only whether they raised an exception, call counts, retrieval flags, prompt lengths, timings and hashes of S (never an offer, a regret, S itself or a calls log). They are reported with the registration.

The pilot's decision rules are fixed here, and the pilot never computes an entry's outcome.

**Pilot (P0.12).** The pilot uses the 70 prompts of pilot variants 13–14: buyers Maeve Mulberry and Nova Peachwood, sellers Magnus Mulberrylane and Nolan Peachgrove, openings 3 and 4.

- **What runs.** All five agents run Phase 2, because their runtimes and S lengths are needed. Only `rational_agent` is scored in Phase 3, under N0 and N1.
- **What is computed.** The analysis script for the pilot reads only these fields:
  - runtimes;
  - the token length of each S and how often the 3,000-token cap binds;
  - the rule-memory retrieval log;
  - for `rational_agent` alone: hard regret, N0 and N1 soft regret per cell (first-token and whole-answer), the letter mass, and the cell-level spread of N1 − N0.

  Entries' offers and regrets are written to a sealed file that is not opened until Phase 3b ends.
- **Power rule (fixed now; `pipeline.pilot_power_rule`, `analysis.projected_cell_sd`, `analysis.power_simulation`).**
  - **SD projected to 12 variants.** The pilot has 2 variants per cell, the confirmatory design 12, so 2-variant cell means carry six times the within-cell variance. The sd used is sqrt(between + within/12), where within is the mean over cells of the variance of N1 − N0 across the cell's variants and between is the variance of the pilot's cell means minus within/2 (floored at 0). Using the raw 2-variant sd would bias the rule towards extending.
  - **Simulation.** Cell differences are drawn from Normal(0.05, sd). There are 35 cells and 2,000 simulated data sets, each tested by the one-sided sign-flip test with 2,000 sign patterns at α = 0.05/11, with numpy seed 20261121. Power at 18 cells (K1) is reported with the same sd.
  - If power is at least 80%, the 35-cell design stands.
  - Otherwise the **extension** below is added before Phase 2, for every agent and test.
  - **If power is still below 80% with 49 cells**, nothing further is added. The study runs as registered, and the four-way verdicts report underpowered tests as "inconclusive" rather than as negative.
  - **Proxy.** N1 − N0 is the only contrast the baseline-only pilot can measure. It stands in for every contrast; the per-family power actually achieved is reported with the results.
- **Extension (fixed now).** New design points, not re-worded copies of existing ones: resale values V = 7 and V = 8, with the same seller lines, costs, script and 12 variants. This adds 14 cells, for 49 in total, and 168 prompts.
  - Best offers: no information, V = 7 gives 3 or 4 (2.4) and V = 8 gives 4 (3.2); stated cost C < V gives k = C.
  - The split rule extends unchanged: no-information cells with V odd go to development; information cells with V + C odd go to development. That gives development 24 cells and test 25.
  - Cell means stay the unit, because the new cells differ in the payoff-relevant variable.
  - **Why V = 7, 8 rather than harder cells.** 10 of the 14 new cells state a cost below V, where the best offer can be read off. Those cells are easy, but they are not filler: they test whether text and steering keep a model on the stated cost when the resale value is high, and they raise K2's unique-best test cells from 12 to 19. New seller lines or noisy cost statements would change the game itself, not add design points of the same game, so they are not used. The cell-type sensitivity analyses (section 11) report easy and hard cells separately.
- **Ceiling rule (fixed now).** Cells where the pilot's N1 soft regret is below 0.05 coins are listed as "near-ceiling". The confirmatory set is unchanged. A pre-specified secondary analysis repeats every confirmatory test on the remaining cells.

Pilot data never enter a confirmatory test.

## 7. Phase 1: native rerun (descriptive)

This phase shows how the five agents behave in the contest's own haggling scenarios before any controls. It has no hypothesis, and no later step depends on it.

- **Scenarios:** `haggling_0` (resident: focal copies trade with each other and with rational agents, in both roles; values 5–6, costs 1–2, 2 games per pair) and `haggling_1` (visitor: one focal agent with a seller who always accepts). Both are unmodified except for the P0.5 seed patch.
- **Runs:** `launch_concordia_challenge_evaluation.py --embedder all-mpnet-base-v2 --seed 1 --num_repetitions_per_scenario 20`, once per agent, with `LocalGemma2` at contest sampling. That is 200 simulations.
- **Reported, per agent and scenario** (95% bootstrap intervals over simulations): the launcher's focal per-capita score; buyer-role score; deal rate; the rate of accepted prices above the buyer's value; and the entries' rank order beside the contest's.

## 8. Phase 2: identical conversations

Every agent decides after exactly the same memories and the same fully scripted conversation, so the only difference is the agent (`refimpl/phase2.py`).

**8.1 Prompt set: 420 unique prompts in 35 cells** (`core.prompt_set`):

| Type | Factors | Prompts |
| --- | --- | --- |
| No information about C | V ∈ {2, …, 6} × seller line ∈ {neutral, pressure} × 12 variants | 120 (10 cells) |
| Seller states C | V ∈ {2, …, 6} × C ∈ {1, …, 5} × 12 variants | 300 (25 cells) |

**Variants.** Variant i uses buyer `FEMALE_NAMES[i−1]`, seller `MALE_NAMES[i−1]` and opening `VISUAL_SCENE_OPENINGS[(i−1) mod 5]` from v1.8.9's `fruitville_haggling.py`. Variants 1–12 are listed below; 13–14 are the pilot. Openings are numbered 1–5 in file order.

| i | Buyer | Seller | Opening | i | Buyer | Seller | Opening |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Anya Blossomwood | Aiden Riversong | 1 | 7 | Gaia Willowbrook | Garen Willowshade | 2 |
| 2 | Brynn Orchardheart | Blaise Windwillow | 2 | 8 | Hazel Nutgrove | Hunter Nutwood | 3 |
| 3 | Clara Applebrook | Cedric Meadowbrook | 3 | 9 | Ivy Pearblossom | Ivor Pearbrook | 4 |
| 4 | Della Plumstone | Dorian Sunstone | 4 | 10 | Juniper Quincewood | Jasper Quincehill | 5 |
| 5 | Elara Berryvine | Elias Berryfield | 5 | 11 | Kira Citronbloom | Kieran Citronbrook | 1 |
| 6 | Faye Honeydew | Flynn Honeycomb | 1 | 12 | Lila Figleaf | Lennon Figtree | 2 |

**8.2 Script.** Two exchanges, buyer first:

1. Buyer: "Good morning! I'm interested in your fruit. What can you tell me about it?"
2. Seller: "Good morning! It was picked this week and it's ripe and sweet."
3. Buyer: "It looks good. Let's talk about the price."
4. Seller:
   - neutral: "Take your time and tell me what price you have in mind for the fruit."
   - pressure: "I don't have all day. Make me a serious offer now or find another merchant."
   - information: "To be honest, this fruit cost me {C} coins at the farm, so price accordingly."

**8.3 Agent state** (identical across agents for a given prompt):

1. **Configuration:** `haggling.configure_player(buyer, "female", 1895, True, random.Random(1000 + i))`, with Python's global `random` seeded to 1000 + i first, because `get_trait` uses it.
2. **Formative memories:** generated once per variant by v1.8.9's `FormativeMemoryFactory.make_memories`, built as in `haggling.py`, with `LocalGemma2` greedy. "{buyer} always drives a hard bargain." is added as `haggling.py` does. Generation is not bit-reproducible across hardware. The 14 banks are therefore generated before registration and published with it, with their SHA-256 in the registration file (section 6, Order), and every phase and every replication loads them rather than regenerating. `AssociativeMemory` holds a thread lock and cannot be deep-copied. So each decision builds a fresh memory on its own clock and copies the stored bank's rows (text, time, tags, importance, embedding) and content hashes into it (`phase2.run_decision`).
3. **Setup observations** (clock at 11 Sept 1895, 00:00, the day before the start):
   - the scenario premise;
   - "Fruits are sold by weight.";
   - "The price of one kilogram of fruit is, on average, 3 coins. 1 coin is really cheap and 5 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed.";
   - the three rule sentences: "Sellers at this market pay between 1 and 5 coins per kilogram at the farm, and each amount is equally likely." "A seller accepts any offer at or above their farm cost and refuses anything lower." "When a seller states their farm cost, it is true."
4. **Scene** (clock at 12 Sept 1895, 00:00, advanced by one clock step (5 minutes, the major step) before each utterance):
   - the premise "{opening} {buyer} is trying to buy some fruit from {seller}. They are negotiating a price. {buyer} can sell the fruit for {V} coins back in her home town.";
   - the four utterances;
   - "{buyer} is ready to make an offer."
5. **Decision:** `act()` with the v1.8.9 action spec "What price would {name} propose?:" and options "1 coin" to "5 coins", greedy, under the determinism patches.

That is 5 agents × 420 = **2,100 decisions**.

**8.4 Recorded per decision:**

- the offer and its hard regret;
- every model call (prompt, output) in order;
- whether each rule sentence appeared in any prompt during `act()` (retrieval log);
- the **reasoning text S**: one entry per `sample_text` call during `act()`, in call order, separated by blank lines (`core.build_S`).
  - Each entry is "Question: " plus the call's last prompt line beginning "Question:" (or its last non-empty line if there is none).
  - Then comes "Answer: ", plus the answer stem the prompt itself ends with (for example "Anya would"), plus the completion. The entry therefore reads as the model saw it.
  - Multiple-choice sub-calls are logged but are not part of S.
- **S\_reason**: S without entries whose question starts "Summarize", "Summarise", "Select the subset", "Recall" or "What is the current" (memory-retrieval and observation-summary calls). It is used only in E7.

**8.5 A1–A3.** Per prompt, D = regret of `rational_agent` minus regret of the entry, so positive means the entry is better. Tested at cell level (section 11).

**8.6 E1 robustness.** 110 prompts (the no-information prompts of variants 1–6 and the information prompts of variants 1–2; all 35 cells) are rerun at temperature 0.5. Each agent gets 5 draws, with draw index 0–4 in the seed: 5 agents × 110 × 5 = **2,750 sampled decisions**. Each entry's draw-averaged D is tested at cell level (E1), with a 95% interval.

## 9. Phase 3: text transplant and activations

Each agent's Phase 2 reasoning text is inserted into one fixed decision prompt, so differences come only from the inserted text (`refimpl/phase3.py`).

**9.1 Fixed decision prompt.** The user turn, scored as a multiple-choice call (section 4):

```text
{INSTRUCTIONS}

Memories:
Fruits are sold by weight.
The price of one kilogram of fruit is, on average, 3 coins. 1 coin is really cheap and 5 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed.
Sellers at this market pay between 1 and 5 coins per kilogram at the farm, and each amount is equally likely.
A seller accepts any offer at or above their farm cost and refuses anything lower.
When a seller states their farm cost, it is true.
{buyer} always drives a hard bargain.

Observations:
{opening} {buyer} is trying to buy some fruit from {seller}. They are negotiating a price. {buyer} can sell the fruit for {V} coins back in her home town.
{buyer} -- "Good morning! I'm interested in your fruit. What can you tell me about it?"
{seller} -- "Good morning! It was picked this week and it's ripe and sweet."
{buyer} -- "It looks good. Let's talk about the price."
{seller} -- "{seller line}"
{buyer} is ready to make an offer.

{NOTES}Question: What price would {buyer} propose?:
  (a) {option}
  (b) {option}
  (c) {option}
  (d) {option}
  (e) {option}
Answer: (
```

- `{INSTRUCTIONS}` is the v1.8.9 `Instructions` text with the buyer's name, verbatim in `phase3.instructions_text`.
- `{NOTES}` is "Notes:", a newline, the inserted text and a blank line; it is empty in N0.
- The inserted text is capped at 3,000 tokens (first and last 1,500 kept, joined by a line "..."), identically in every condition. How often the cap binds is reported.
- Options are the five prices in five cyclic orders ("1 coin" first, "2 coins" first, and so on). Soft regret averages p(k) over the orders. Hard regret averages each order's argmax.

**9.2 Conditions** (28 per prompt, all 420 prompts; `conditions.build_conditions`):

| Code | Inserted text | Purpose |
| --- | --- | --- |
| N0 | None | The model alone |
| N1 | `rational_agent`'s S | Baseline text |
| N1s | N1 with the N8 removal rule applied | Symmetric comparison for R |
| N2, N3, N4 | S of `taehun_cgcal`, `fluffy_fluffyagent_v16submission`, `hgyun_loss_aversion_agent_v3_plus2` | Entry text |
| N2r–N4r | Each entry's S\_reason (8.4) | E7: reasoning without memory summaries |
| N5 (×4) | Each agent's S paraphrased | Wording control |
| N6 (×4) | Filler in the same format as S, with the same token count as each agent's S. Blocks of "Question: What does the market look like?" / "Answer: {opening}" cycle through the five scene openings, joined by blank lines and cut to the exact count (`conditions.qa_filler`) | Length and format control |
| N7 (×3) | The entry's own text written for a nearby prompt whose best offer differs: its S from a donor prompt with the same variant and seller line whose set of best offers does not overlap this prompt's (`conditions.n7_donor`; rule below) | Specificity: on-topic text for a prompt with a different answer |
| N8 (×3) | Each entry's S with advice-bearing sentences removed (rule below) | Text without price advice |
| N9 (×4) | Only "{buyer} should offer {k} coins." ("coin" when k = 1), with k that agent's own Phase 2 offer | Answer only |
| N10 | The same line with k the best offer (the smallest if several) | E5: answer-naming upper bound |

**N7 donor rule** (`conditions.n7_donor`). Among the cells of the grid in use (35, or 49 with the extension) with the same seller line whose set of best offers is disjoint from this prompt's, the donor is the cell nearest in (V, C) by Manhattan distance; no-information cells use C = 0 and take only no-information donors. Ties go to the smaller V, then the smaller C. The donor prompt has the same variant. For information cells the donor's stated cost can differ from this prompt's, as well as its V. Cell (V = 5, C = 5) has every offer optimal, so no donor is disjoint: it uses the donor with the smallest overlap under the same rule (V = 5, C = 4), and it is the only exception (34 of 35 cells, 48 of 49 with the extension, have a disjoint donor; unit-tested).

**What N7 controls for, and why not a same-cell donor.** B asks whether the entry's text helps *because it is about this prompt*. N7 holds the agent, variant, names, seller line, style and approximate length fixed and changes only the payoff-relevant facts the text was written for, so that its best offer differs. Its stated values (V, and for information cells possibly C) therefore conflict with the prompt's own; that conflict is the manipulation, not a side effect: text that helps because it carries this prompt's valuation must beat text carrying another prompt's valuation. A same-cell donor from another variant (same V, C and best offer, different names) would carry the same valuation and answer, so beating it would test name-specific wording, not specificity of content, and the hypothesis would be expected to fail it. Two descriptive checks accompany N7: the share of N7 texts containing a number that conflicts with the prompt's V or C, and the share of N7 texts whose agent's Phase 2 offer for the donor prompt equals this prompt's best offer.

That is 28 × 5 orders × 420 = **58,800** scored prompts. Token counts use the pinned tokenizer without special tokens.

**Paraphrases.** Each paraphrase is a `sample_text` call through `LocalGemma2` with `max_tokens` 3,000 and the prompt "Rewrite the following notes in different words. Keep every fact and number exactly.", a blank line, then the text. The first attempt is greedy. If the sorted list of digit strings (`core.numeral_multiset`) differs from the original's, up to three retries are sampled at temperature 0.7 with draw indices 1–3. If all fail, that prompt is dropped from wording contrasts only, and drop-outs are reported per agent.

**Advice removal** (`conditions.remove_recommendations_strict`). The text is split at sentence ends (after `.`, `!` or `?` followed by whitespace) and at newlines. A sentence is removed if it mentions a price or an option label **and** any of the following:

- a decision verb;
- an evaluative or payoff word;
- an option label;
- a number attached to the price (as in "3 coins: 2" or "3 coins → 1.2");
- two or more different prices.

A sentence mentions a price if it contains a coin amount ("3 coins", "three coins"), a bare number 1–5 after a decision verb, "price" or a preposition ("offer 2", "a price of 3", "for 4"; not when followed by "kg", "kilogram", "%" or "per"), or a currency mark ("$2"). Prices are compared as digits, so "three coins" and "3 coins" are the same price. This catches per-option profit estimates (the top entry's main output) as well as explicit recommendations. Single-price statements of fact, such as the resale value, a stated cost or the average price, survive. The patterns, exactly as in `conditions.py` and `core.py` (all case-insensitive):

```text
sentence split:  (?<=[.!?])\s+|\n+
coin amount:     \b([1-5])\s*coins?\b|\b(one|two|three|four|five)\s+coins?\b
bare number:     \b(?:offer|offers|offering|propose|proposes|proposing|bid|bids|bidding|pay|pays|paying|price|prices|priced|at|for)\s+(?:of\s+|is\s+|around\s+|about\s+)?([1-5])\b(?!\s*(?:kg|kilogram|%|per))
currency mark:   [$€£¢]\s?([1-5])\b
option label:    \(\s*[a-e]\s*\)|\boption\s+[a-e1-5]\b
decision verb:   \b(?:offer|offers|propose|proposes|bid|bids|pay|pays|choose|chooses|go with|settle on|counter)\b
evaluative:      \b(?:profit|profits|gain|gains|payoff|payoffs|expected|earn|earns|earning|surplus|return|returns|optimal|best|better|worse|worth|maximi[sz]e|maximi[sz]es|recommend|recommended|should|ideal|fair|reasonable|good|acceptable|sensible|appropriate|aim|aims|target|targets|go for|start|starting|open|opening)\b
attached number: \b[1-5]\s*coins?\b[^.\n]*?(?:[:=]|->|→)\s*-?\d
```

Kept sentences are stripped and joined with single spaces.

**Leakage audit** (reported with R; not a test). For every N8 and N1s text, the model is asked under the choice scoring of section 4: "Based only on these notes, which price do they favour?", with options (a)–(e) for the five prices and (f) "The notes do not favour any price". The audit reports two rates: how often the answer is a price, and how often it equals the agent's own Phase 2 offer.

- **Calibration.** The same rates are computed for the baseline's N1s against the baseline's own offer. That gives the level of "favouring" expected from stripped text that carries no extra advice.
- **Flag** (`pipeline.leakage_flags`). If an entry's own-offer rate exceeds the baseline's by more than 10 percentage points, its R result cannot be "supported": a passing R is reported as "inconclusive (possibly carried by implied advice)". Reversed and equivalent verdicts are unaffected.
- **What the rule removed.** For every agent, the mean token count of S and of its stripped text (N8 or N1s), and the share of sentences removed, are reported, so that a difference in how much the rule strips from entry and baseline text is visible. N8 and N1s are not length-matched to each other: matching would require adding filler to stripped text, which would itself be a new condition. R is therefore read with these counts beside it.
- **What the rule cannot catch.** Advice that names no price ("offer exactly what the seller paid") survives. The audit is the check on this; the model that answers it is the decision model, so it measures what that model can still read from the text, which is the quantity that matters for R.

The 10-point margin is fixed now. It is about three standard errors of a difference of two rates on 420 prompts each, near rates of 0.3 (standard error 0.032).

**9.3 Tests.** All differences are oriented so that positive favours the entry's own text (N2, N3 or N4, written Ne), and are tested at cell level (section 11):

- **B\_e:** soft regret under N0, under N1, under the entry's N6 and under the entry's N7 (the entry's own text written for a nearby prompt whose best offer differs), each minus soft regret under Ne. Four tests; the largest p-value is used (intersection–union).
- **R\_e:** N0 minus the entry's N8, and N1s minus the entry's N8. The larger p-value is used. Both texts in the second comparison have had the same removal applied, so N8 cannot win merely because the baseline's text contains bad advice.

A line naming the entry's own offer (N9) is not part of R. Requiring the text to beat its own answer would penalise entries whose answers are good. N9 and N10 are reported descriptively (E5).

`analysis.abr_tests` assembles A, B and R. `analysis.confirmatory_verdicts` applies both Holm families and the verdict rules.

**9.4 Native replay** (`pipeline.run_native_replay`). Wherever an agent's Phase 2 decision ended in a multiple-choice call over the five prices, that exact final prompt is re-scored, giving both its whole-answer argmax and its first-token argmax. This puts Phase 2's native prompts on Phase 3's scale.

- **Which decisions qualify** (`pipeline.final_price_choice`). The last model call made during `act()` must be a choice call whose prompt lists all five price options. `taehun_cgcal` decides in Python whenever the model answers that payoffs are numeric; its last call is then a yes/no choice, not a price choice, and the decision does not qualify. The number of qualifying decisions is reported per agent.
- **Criterion (fixed now; `pipeline.native_replay_labels`).** If an entry's first-token argmax agrees with its Phase 2 choice on fewer than 80% of its qualifying prompts, its B and R results are labelled "transplant-sensitive". The first-token scale then does not reproduce that agent's own decisions.

**9.5 E-family contrasts in Phase 3:**

- **E5:** wording (each N5 minus its own text) and length alone (each entry's N6 minus the baseline's N6), tested; N9 and N10 minus Ne, descriptive.
- **E2:** calibration of each entry's text versus N1, with the K2 statistic and controls.
- **E7:** B and R with N2r–N4r in place of N2–N4.
- **E8:** heterogeneity across entries.

**9.6 Activations.** Forward hooks on each decoder layer's output, i = 0…41: the residual stream after the block and before the final norm, which is Gemma Scope's site. Activations are captured in the P1 pass (section 4), the pass whose first-token distribution is the primary outcome and the pass Phase 3b steers; all capture positions are at or before P1. Steering hooks fire in every pass (10.3). Stored in float16, with computation in bfloat16.

| Position | Definition | Stored |
| --- | --- | --- |
| P1 | Last prefix token: the newline after `<start_of_turn>model` | Mean over the 5 orders |
| P2 | The `(` ending `Answer: (` | Mean over the 5 orders |
| P3 | Last token of the final seller line | Order 1 |
| P4 | Last token of "{V} coins back" | Order 1 |

P2–P4 are found from the tokenizer's offset mapping on the decoded prefix: the last token whose character span covers the end of the target string, with an assertion that re-tokenising reproduces the same ids (`phase3.token_positions`).

## 10. Phase 3b: steering

If the entries' text improves offers through a direction in activation space, adding that direction to the baseline prompt (N1) should lower regret. It should do so more than directions encoding only wording, length or a named answer. And to show it carries valuation, it should move each cell's offer towards that cell's own optimum, not shift all offers alike.

**10.1 Disjoint cells.** Cells are split, not just variants (`core.steering_cell_split`):

- **Development (17 cells):** no-information cells with V odd (3, 5), and information cells with V + C odd.
- **Test (18 cells):** no-information cells with V even (2, 4, 6), and information cells with V + C even.

With the extension (section 6), V = 7 and 8 follow the same rule: development 24 cells, test 25. Development and test cells share V and C values but never the same (V, C) pair or (V, line) pair. "Held-out" means held-out cells of one grid, not held-out conditions.

Development uses all 12 variants of its cells (204 prompts); test uses all 12 variants of its cells (216 prompts). No test prompt, and no text generated for one, is used in fitting or tuning.

**10.2 Directions** (development set). h\_L is the layer-L activation at P1 under a condition, averaged over the five orders and then over prompts; "entries" means the mean of the three entries.

| Direction | Definition |
| --- | --- |
| Content | h\_L(entries' own text, N2–N4) − h\_L(N1) |
| Wording null | h\_L(entries' paraphrases, N5) − h\_L(entries' own text) |
| Length null | h\_L(entries' length filler, N6) − h\_L(baseline's length filler, N6) |
| Answer-only null | h\_L(entries' answer lines, N9) − h\_L(baseline's answer line, N9) |
| Natural random (1,000) | The difference between the N1 activations of two development prompts from different cells, at the same layer. Pairs are drawn once with numpy PCG64 seed 11 and reused at every layer (`pipeline.random_directions_at`) |

Every null is rescaled to the content direction's Euclidean norm at the same layer. α then multiplies the rescaled vector. Each named null's natural norm (before rescaling) is reported beside the content norm, and so is the number of directions, named or random, whose tuning fell back to "no steering" (α = 0).

**What the random set is.** The 1,000 natural directions are not exchangeable with the content direction: they are activation differences between real prompts from different cells, so they carry valuation and cost information and can themselves lower regret. Component 6 is therefore a rank of the content direction within a reference distribution of informative, same-norm directions, not a permutation test of exchangeable units, and it is conservative. For calibration, 200 isotropic Gaussian directions (one draw each from PCG64 seed 12, reused at every layer and rescaled to the content norm; `pipeline.isotropic_directions_at`) are tuned and evaluated on the same matched budget, and the matched content copy's rank among them is reported; it is not a component of K1.

**10.3 Intervention** (`phase3.steering_hook`). α · direction is added to layer L's output at P1 and every later position (letter, `<end_of_turn>`, newline), in every scoring pass, exactly as unsteered runs are scored: in the P1 pass (where it changes the first-token distribution, the primary outcome) and in each of the five sequential whole-answer passes when those run. The hook sees the same P1 in every pass. Earlier positions are untouched, and causal attention means they are unaffected anyway. Check P0.9 confirms that a zero vector gives bit-identical probabilities.

**10.4 Tuning** (development only):

- **Grid:** L ∈ {6, 9, …, 30} × α ∈ {0.5, 1, 2, 4}: 9 layers, 36 settings. Every direction, random ones included, is tuned over the same 36 settings.
- **Coherence:** the mean next-token probability on the letters a–e at P1 (`LocalGemma2.last_letter_mass`), averaged over the tuning prompts and orders, must stay at least 90% of the same mean unsteered (a ratio of means).
- **Passes.** Tuning uses only the first-token distribution and the letter mass, both from the P1 pass, so tuning runs the P1 pass alone (`whole_answer=False`). Test evaluation of the named directions also runs the whole-answer passes, for the whole-answer sensitivity analysis.
- **Choice:** each direction gets its own best setting, by largest mean soft-regret reduction among coherent settings (`steering.tune`). Ties go to the smaller α, then the earlier layer. "No steering" is always an option. If no coherent setting reduces regret on development, the direction is applied with α = 0, so its effect is exactly zero. The same rule applies to every direction.
- **Tuning data.** Every comparison is like for like:
  - Content and the three named nulls are tuned on all 204 development prompts × 5 orders, and tested on 216 test prompts × 5 orders.
  - For the random comparison only, a **matched copy of the content direction** and each of the 1,000 random directions are tuned identically. Each uses variant 1 of every development cell (17 prompts) with one order, over the same 36 settings. Each is tested on the 216 test prompts with one order per prompt, rotating with the variant (`pipeline.single_order`).

  The matched copy is what component 6 below compares with the random directions. The noisier 17-prompt tuning therefore affects content and random directions alike.
- Everything is frozen before the test set is touched.
- **Direct logit effects.** Excluding late layers does not stop a vector from travelling in the residual stream to the unembedding. The content direction's cosine with each letter's unembedding row (a–e) is reported at the tuned layer. E6 reruns the K1 test with the direction's component in the span of those five rows projected out, then rescaled to the original norm.

**10.5 Tests** (216 test prompts, 18 test cells):

**K1** (`analysis.k1_test`, assembled by `analysis.k_tests`; `pipeline.run_phase3b` produces its inputs) has six components, each a one-sided p-value:

1. **Δ:** N1 soft regret minus content-steered N1 soft regret, cell-level sign-flip test (section 11).
2. **Δ minus the wording null's own steered Δ**, same test.
3. **Δ minus the length null's own steered Δ**, same test.
4. **Δ minus the answer-only null's own steered Δ**, same test.
5. **Sharpening null.** Each unsteered N1 distribution (the order-averaged p(k) of the prompt) is raised to a power γ and renormalised: the same mode, but more confident. γ ∈ {1.25, 1.5, 2, 3, 4, 6, 8} is chosen on development by largest mean soft-regret reduction, or γ = 1 if none reduces it (`analysis.tune_sharpen`). The component tests Δ minus the sharpened Δ, so K1 cannot pass merely because steering makes the model more confident in its existing choice.
6. **Random-direction reference rank:** (1 + number of random directions whose mean Δ ≥ the matched content copy's mean Δ) / 1,001. The smallest attainable value is 1/1,001 ≈ 0.001, below the strictest Holm threshold of 0.05/11 ≈ 0.0045. Passing requires the matched copy to beat at least 996 of the 1,000 informative random directions, each tuned under the same noisy 17-prompt budget; this is a demanding criterion by design.

K1's p-value is the largest of the six (intersection–union). It enters Holm as one test, so every component is held to K1's Holm level. K1 tests the pooled direction of the three entries. E3 tests each entry's own direction, and E8 decides which reading is primary (section 1.5).

**K2** (`analysis.calibration_test`) uses only the test cells whose best offer is a single price (`core.has_unique_best`). For information cells with C ≥ V, any offer below C is optimal, so there is no target. That leaves 12 of the 18 test cells: 6 no-information and 6 with C < V. For each cell it takes:

- s, the steering shift (mean expected offer, steered minus unsteered);
- o, the best offer;
- b, the unsteered expected offer.

The statistic is the **partial Spearman correlation of s and o controlling for b**: ranks, then residuals on b's rank, then Pearson. This removes the coupling in the old "needed correction" measure (o − b), which shares a −b term with any shift that depends on the starting point.

Controls, each applied to the unsteered distributions:

- **tilt:** exp(βk), with β matched to the mean signed shift;
- **attractor:** (1 − λ)p + λ·δ\_k\* for each fixed price k\* = 1…5, with λ matched to the mean absolute shift. The k\* with the highest partial correlation is used, which favours the control.
- **flatten:** (1 − λ)p + λ·uniform, with λ matched to the mean absolute shift;
- **sharpening:** the tuned γ from K1, applied to the unsteered distributions;
- **answer-only null:** the steered answer-only direction.

K2's components are:

- **the partial correlation is positive:** a permutation test (`analysis.partial_spearman_perm`). The residuals of s's ranks (on b's rank) are permuted across cells, 100,000 Monte Carlo permutations, PCG64 seed 11, p = (1 + count) / 100,001. Ties in o (best offers take few values) are handled by average ranks, and the permutation distribution accounts for them;
- **it exceeds each control's partial correlation:** an exact paired swap test (`analysis.paired_swap_test`). Under the null that a cell's steered and control shifts are exchangeable, all 2ⁿ within-cell swaps are equally likely (4,096 with 12 cells, 524,288 with 19); p is the share of swaps whose difference in partial correlation is at least the observed one.

Both tests are exact or Monte Carlo-exact for the small number of cells, replacing a t-test and a percentile bootstrap that are not calibrated at n = 12. The 90% interval used for K2's equivalence verdict is a cell bootstrap (10,000 resamples, seed 11) of the difference against the strongest control, with its TOST p-value (1.4).

K2's p-value is the largest of these. Its reverse p-value is the Bonferroni minimum over the opposite-direction components (section 11). Unit tests confirm that steering which only pulls towards a fixed price, only flattens, or only sharpens does not pass, and that steering towards each prompt's own optimum does. K2 is also computed for every random direction and its distribution is reported; this is secondary.

**Power caveat.** K1 rests on 18 test cells, which detect about 0.81 SD at the strictest Holm level, and K2 on 12. The extension, if triggered, raises these to 25 and 19 (K2's unique-best test cells with V = 7, 8 added: (7, C = 1, 3, 5), (8, C = 2, 4), and V = 8 neutral and pressure). Without the extension K2 is secondary (1.3, 1.4). An "inconclusive" steering result is a real possibility, and the verdicts are designed to report it as such.

**10.6 Secondary and exploratory:**

- E3: each entry's own content direction (h\_L(Ne) − h\_L(N1)), tuned and tested through the same procedure, with its own matched copy. Its K1 components reuse the pooled named nulls, the sharpening null and the random directions, whose test results do not depend on the content direction (`pipeline.run_phase3b`).
- E6: K1 with the letter-unembedding component projected out of the content direction (10.4), tuned and tested like E3.
- The full price distribution under steering, per cell.
- Ablation: removing the unit content direction from N2–N4 runs.
- Exploratory (labelled):
  - ridge probes for V at P4 and P1, with grouped cross-validation and shuffled-label nulls;
  - Gemma Scope features at layers 9, 20 and 31 that differ between entry text and N1, against a permutation null;
  - pressure versus neutral activations at P3.

## 11. Statistical plan

The analysis code is `refimpl/analysis.py`.

**Registration.** Before Phase 0 and the pilot, register these with a public timestamp:

- this document;
- the model, embedder and smoke-model revisions (section 3);
- the lock file;
- the commit and SHA-256 of the harness and analysis code.

There are no interim analyses. The pilot's only effect is through the power rule and ceiling rule in section 6, both fixed now.

**Unit.** Under greedy decoding, prompts in one cell differ only in names and opening, so they are not independent. Each per-prompt difference D (positive favours the hypothesis) is averaged within its cell over the 12 variants. Tests use those cell means: 35 cells for A, B and R (49 with the extension), 18 test cells for K1 (25) and 12 for K2 (19).

**Primary test: one-sided sign-flip permutation test of the mean cell difference** (`analysis.signflip_greater`).

- **Null and validity.** The null is the sharp null of no effect: within every prompt, the two conditions (or agents) being compared are exchangeable, so swapping their labels leaves the joint distribution of the outcomes unchanged. That makes every prompt's difference D, and therefore every cell mean of D, symmetric about 0 whatever the distribution of regret levels, including the one-sided regret of cells with C ≥ V and the near-zero regret of easy cells. The sign-flip test is exact for this null. Cells are fixed design points; the randomness the test relies on is the label exchangeability under the null, not sampling of cells.
- **What a rejection means.** The one-sided test uses the mean, not ranks, so a rejection is read as a positive average effect over the grid's cells, the claim the protocol makes. Skew under the alternative does not affect the test's validity, only its power.
- **Skew-robust sensitivity.** A cell bootstrap-t test (studentised mean, 10,000 resamples, seed 20261121; `analysis.bootstrap_t_greater`) is reported beside every sign-flip test, with the Wilcoxon test below.
- **Computation.** Exact enumeration of all 2ⁿ sign patterns when there are 20 cells or fewer. Otherwise 100,000 Monte Carlo patterns with numpy seed 20261121, p = (1 + count) / 100,001.
- **Sensitivity.** The Wilcoxon signed-rank test (Pratt zeros) is reported for every test.

Multi-part hypotheses (B, R, K1, K2) use the largest component p-value. This is an intersection–union test: it needs no adjustment within the hypothesis, and every component is held to the hypothesis's Holm level. K1's random component is a reference-distribution rank, and K2's components are a permutation test and exact paired swap tests (section 10.5).

**Family** (`analysis.confirmatory_family`). A1–A3, B1–B3, R1–R3 and K1 form ten tests; K2 is the eleventh when the extension is in force (1.3). Holm–Bonferroni at α = 0.05 (`analysis.holm`). Ordered from the smallest p-value, the thresholds are 0.05/m, 0.05/(m − 1), …, 0.05/1, with m = 10 or 11. Without the extension K2 joins the secondary family.

- **Reverse family.** The opposite-direction p-values of the same tests form a separate Holm family at α = 0.01, used only to award "reversed".
  - Single tests use `analysis.signflip_less`.
  - Multi-part tests use the Bonferroni-corrected minimum over their components' opposite-direction p-values (`analysis.reverse_p`). The permutation and bootstrap components use their lower tails.
  - By the union bound, which needs no independence, the chance of any false directional claim across both families is at most 0.05 + 0.01.
- **Equivalence family.** The TOST p-values of the tests that are neither supported nor reversed form a third Holm family at α = 0.05, used only to award "equivalent" (1.4).
- **Secondary tests** (E1–E9, section 1.5, and K2 when the extension is not in force) form one Benjamini–Hochberg family at q = 0.05 (`analysis.benjamini_hochberg`).
- **Exploratory analyses** carry no claims.

**Verdicts** (`analysis.verdict`, applied by `analysis.confirmatory_verdicts`).

- **Supported:** the test passes Holm.
- **Reversed:** it does not pass, and its opposite-direction test passes the reverse family.
- **Equivalent:** neither, and its TOST p-value passes the equivalence family: the cell bootstrap of the mean cell difference lies within ±0.05 coins with Holm-adjusted confidence. Multi-part tests use the component with the largest p-value. For K2 the bound is a partial-correlation difference of ±0.2, against the strongest control.
- **Inconclusive:** none of the above.

**Power.** At the strictest Holm level (α ≈ 0.0045) with 80% power, a mean test (normal approximation, which the sign-flip test approaches) detects about (2.61 + 0.84)/√n standard deviations of the cell means:

- 35 cells: 0.58;
- 18 cells (K1): 0.81;
- 12 cells (K2 without the extension, secondary): 1.00; 19 cells (K2 with it): 0.79.

Whether that reaches the 0.05-coin bound depends on the spread of cell means.

- The pilot estimates that spread from baseline-only quantities.
- The pre-registered power rule (section 6) adds the V = 7, 8 extension if simulated power is below 80%.
- Averaging more name variants within a cell cannot add power at the cell level; only more cells can. That is why the extension adds new design points rather than re-worded copies of existing cells.
- A simulation-based power report for the final design is published with the results.

**Effect sizes.** For every test: the mean cell difference with a 95% bootstrap interval (10,000 resamples of cells), the matched-pairs rank-biserial correlation, and the standardised mean.

**Sensitivity analyses** (every confirmatory test):

- A mixed model on prompt-level D with crossed random intercepts for cell and variant, `lmer(D ~ 1 + (1|cell) + (1|variant))` (REML, Satterthwaite, one-sided on the intercept).
- The cell-level Wilcoxon signed-rank test, and a prompt-level Wilcoxon test.
- Separate cell-level tests for no-information cells, information cells with C < V (15 cells, where the stated cost gives the answer directly) and information cells with C ≥ V.
- Every confirmatory test repeated on the cells not flagged near-ceiling by the pilot (section 6).
- For B, R and K: hard regret, and whole-answer soft regret (section 1.2).

If the primary test and the mixed model disagree at α = 0.05, the result is reported as fragile.

**Exclusions.** An agent that fails on a prompt is retried once with the same seed. If it still fails, that prompt is dropped for every agent and condition. Exclusions are reported. If more than 10% of an agent's prompts are excluded, its tests are labelled inconclusive.

**Deviations.** Any change after registration is logged with its date, reason and affected analyses, and both versions of each result are reported.

## 12. Compute and run order

**Memory** (bfloat16):

- Weights: about 9.2 billion parameters × 2 bytes ≈ 18.5 GB.
- KV cache: 42 layers × 2 × 8 heads × 256 × 2 bytes ≈ 344 KB per token, about 2.4 GB at 7,000 tokens.
- Phase 3 scores five equal-length sequences of up to about 4,500 tokens, one per forward pass (batch size 1), with eager attention. Batching the five does not fit in 24 GB.

A 48 GB GPU is specified for the confirmatory runs; sequential scoring also fits a 24 GB A10G (peak memory measured in Stage 1 and recorded with the registration). P0.11 records peak memory on the registered GPU.

**Storage.** P1 and P2 are stored averaged over the 5 orders, and P3 and P4 once, all in float16: 4 positions × 42 layers × 3,584 × 2 bytes ≈ 1.2 MB per prompt and condition. 420 × 28 × 1.2 MB ≈ **14 GB** (about 16 GB with the V = 7, 8 extension).

**Runtime** (planning figures from the Stage 1 measurements on one A10G, replaced by P0.11 on the registered GPU). Measured on the A10G: one sequential scoring pass takes 0.38 s at 800 tokens, 2.32 s at 3,600 and 3.19 s at 4,500 (steered or not); a Phase 2 decision with a blank memory took 10 s (`taehun_cgcal`) to 169 s (`fluffy`). L40S figures are scaled by published bandwidth and bf16 throughput ratios (about 1.4× for generation, 2–3× for scoring), not measured.

| Phase | Workload | A10G (24 GB) | L40S (48 GB) |
| --- | --- | --- | --- |
| 1 | 200 native simulations | 4–9 GPU-days, if long prompts fit (see note) | 3–6 GPU-days |
| 2 | 2,100 greedy decisions plus 2,750 sampled ones (E1), 5–25 model calls each | 6–9 GPU-days, if long prompts fit (see note) | 4–6 GPU-days |
| 3 | 58,800 scorings (5 sequential passes each) plus 1,680 paraphrases, the native replay and the leakage audit | 4–6 GPU-days | 2–3 GPU-days |
| 3b | Tuning: 4 named directions × 36 settings × 204 prompts × 5 orders (147k scorings), plus the matched content copy and 1,000 random directions × 36 × 17 (613k). Test: 4 named × 216 × 5 orders, plus 1,001 × 216 × 1 order (221k). About 1M scorings of N1 prompts (about 1,000–1,500 tokens), five passes each | 27–43 GPU-days | 11–17 GPU-days |

Note: on transformers 4.44.2, `generate` computes float32 logits over the whole prompt during prefill (about 1 GB per 1,000 prompt tokens, plus bfloat16 copies). On the A10G this runs out of memory from about 2,400 prompt tokens (`hgyun_loss_aversion_agent_v3_plus2` in Stage 1). Phases 1–2 therefore need the 48 GB GPU, or a registered change to prefill unembedding, before they can run on a 24 GB GPU.

**Order** (`refimpl/pipeline.py` runs steps 5–8 for Phases 2–3b):

1. Formative-memory banks generated (no outcomes).
2. Registration (hash commit) and publication of the banks.
3. Phase 0 checks.
4. Pilot: `run_phase2(..., sealed=True)` on the 70 pilot prompts, `seal_file` (its SHA-256 is published), `run_phase3(..., only=("N0", "N1"))`, then `pilot_power_rule`; the power and ceiling rules are applied.
5. Phases 1 and 2 (`run_phase2`, then E1), which are independent.
6. Phase 3 (`run_paraphrases`, `run_phase3`, `run_native_replay`, `run_leakage_audit`).
7. Phase 3b (`run_phase3b`, which also produces E3, E6 and the isotropic reference).
8. Analysis with the registered code (`refimpl/report.py`): `exclusions`, `phase3_tables`, `confirmatory` (with the leakage, native-replay, exclusion, disagreement and letter-mass rules), `secondary`, `sensitivity`, and `mixed_model_table` with `analysis/mixed_model.R`.

The whole chain from step 4 to step 8 has been run end to end on a small model and off-grid prompts (`scripts/dry_run_pipeline.py`; REFERENCE.md, R3).

## 13. Deviations, threats and release

**Declared deviations from the contest:**

| Deviation | Phases | Reason |
| --- | --- | --- |
| Local serving instead of the Together AI API; system text folded into the first user turn | All | Activations are needed; Gemma's template has no system role (effect measured by P0.3) |
| Top-p and top-k off | 1 | Provider defaults unknown |
| One-line seed patch in `haggling.py` | 1 | It hard-codes seed 42, so repetitions would be identical |
| Greedy decoding, sequential execution | 2–3 | Exact pairing and repeatability; E1 checks sampling |
| Scripted conversation, single decision, threshold seller, three added rule memories, wider V and C | 2–3 | Removes drift and defines a best offer; the contest's own ranges are kept in Phase 1 |
| Inserted text capped at 3,000 tokens | 3 | Keeps prompts within budget; the binding rate is reported |

**Threats to validity:**

- **Scope.** One model, a single five-price decision, and three entries. Results do not establish anything about other models, multi-turn negotiation, or why the entries won the contest.
- **A simplified game.** Some cells are easy (a stated cost below V gives the answer directly). Cell-type sensitivity analyses report easy and hard cells separately, and the pilot flags ceiling risk.
- **Role-play versus optimisation.** The decision prompt asks what the buyer would propose, and the "hard bargain" and 3-coin memories may anchor offers. The baseline bid bias (E4) is reported, and every comparison is within the same prompt.
- **Retrieval.** In Phase 2, agents' memory retrieval may not surface the rule sentences. This is logged per agent (8.4) and is part of what A measures.
- **Transplant.** In Phase 3 text sits outside its native template. The native replay (9.4) measures this, with a fixed 80% agreement criterion.
- **Implicit advice.** The removal rule can miss advice that is only implied. That would make the N8 comparisons in R easier to pass, not harder, so a passed R may still partly reflect implied advice. The leakage audit (9.2) measures how much remains, and N9 and N10 bound how much naming an answer alone can do.
- **What S contains.** S includes memory-summary calls as well as deliberation. E7 repeats B and R on S\_reason, the deliberation alone.
- **Linear, mid-layer steering only.** A null K1 does not rule out other mechanisms.
- **Held-out means held-out cells of one grid.** Development and test cells share V and C values (never the same pair), so K1 and K2 test generalisation to new combinations within the grid, not to new values or games. Holding out whole V levels would leave too few cells on each side of a 5 × 7 grid for any test. Claims are limited to "on this grid".
- **Pooling the entries.** K1's content direction is the mean of the three entries' text effects. If they differ, the pooled direction can mix mechanisms. The reading rule is fixed now and uses no pilot data: if E8 (heterogeneity) is significant, the per-entry directions (E3) are the primary reading of Phase 3b and K1 is reported as the pooled summary.
- **One model, one game.** A second model or a "maximise profit" instruction arm would test generality and the role-play framing directly; both are outside this study's budget and are left to replication. E4 reports the baseline's bid bias so the role-play anchoring is visible.
- **Numerics.** Exact repeatability holds only on the registered GPU model, driver and lock file, with the fixed sequential scoring mode. Replications on other hardware or library versions should expect numerical differences of the size seen between batch shapes on one GPU: on the 9B smoke prompt, batched and sequential letter scores differed by up to 0.32 nats with the same argmax (REFERENCE.md, R3). Conclusions should rest on the cell-level tests, not on matching individual probabilities.
- **Licence.** The agent archive has no licence. Agent files are not redistributed; patches are published as diffs against the archive's SHA-256.

**Release, at registration:**

- the reference implementation as a public repository, with the unit tests, smoke tests and lock file;
- the P0.5 seed patch (one line, given in section 6);
- the 14 formative-memory banks (text, time, tags, importance, embedding) with their SHA-256;
- the SHA-256 of the sealed pilot file of entries' outcomes.

**Release, after the runs:**

- all prompts, formative memories, reasoning texts and paraphrases (JSON);
- every model call and score;
- activations (about 14 GB) and directions;
- the deviation log.

## Sources

- [Smith et al., the NeurIPS 2024 Concordia Contest report (arXiv 2512.03318)](https://arxiv.org/abs/2512.03318); [NeurIPS 2025 Datasets and Benchmarks proceedings page](https://proceedings.neurips.cc/paper_files/paper/2025/hash/d0251bbbc0288f241b878775ba1735dc-Abstract-Datasets_and_Benchmarks_Track.html)
- [Contest agent code (supplementary zip)](https://proceedings.neurips.cc/paper_files/paper/2025/file/d0251bbbc0288f241b878775ba1735dc-Supplemental-Datasets_and_Benchmarks_Track.zip)
- [Concordia v1.8.9](https://github.com/google-deepmind/concordia/tree/v1.8.9)
- [Gemma 2 technical report (arXiv 2408.00118)](https://arxiv.org/abs/2408.00118); [google/gemma-2-9b-it](https://huggingface.co/google/gemma-2-9b-it)
- [Gemma Scope (arXiv 2408.05147)](https://arxiv.org/abs/2408.05147); [google/gemma-scope-9b-it-res](https://huggingface.co/google/gemma-scope-9b-it-res)
- [sentence-transformers/all-mpnet-base-v2](https://huggingface.co/sentence-transformers/all-mpnet-base-v2)
