# Stage 1 report: development run on one A10G

Date: 2026-11-21. Instance: AWS **g5.xlarge** (one NVIDIA A10G, 24 GB; 4 vCPUs; 16 GB system RAM), not the g5.2xlarge that STAGE1_PROMPT.md assumes, on instruction. No pilot or confirmatory phase was run. No offer, regret, S text or calls log was computed for output, printed or saved for any agent: the agent checks record only exceptions, call counts, retrieval flags, prompt lengths, timings, memory and SHA-256 values of S.

**Summary.**

- Everything in STAGE1_PROMPT.md was completed. The 9B model loads directly to the GPU within 16 GB of system RAM (peak RSS 5.6 GB), so the instance did not need to change.
- All 30 unit tests pass. All 9B smoke checks pass.
- All 14 formative-memory banks were generated and round-trip exactly.
- Phase 3 scoring fits the A10G: sequential scoring of a 4,497-token prompt peaks at 20.56 GiB.
- **Two findings need a decision before Stage 2:**
  1. `hgyun_loss_aversion_agent_v3_plus2` runs out of GPU memory in a Phase 2 decision on the A10G. transformers 4.44.2 computes float32 logits for the whole prompt during generation prefill.
  2. Batched and sequential scoring differ by up to 0.32 nats on the GPU, far above P0.2's 10⁻³.
- Phase 3b with five sequential passes per scoring would take about 27–43 A10G-days.

## 1. Environment

| Check | Result |
| --- | --- |
| Python 3.11 via uv; `.venv` from `requirements.lock` with `torch==2.4.1` from PyPI and `pyarrow==17.0.0` | **Pass.** uv 0.13.6, CPython 3.11.18. torch 2.4.1 (CUDA 12.1 build, `torch.version.cuda` 12.1), cuDNN 9.1.0.70 (`nvidia-cudnn-cu12==9.1.0.70`), transformers 4.44.2, numpy 1.26.4, pyarrow 17.0.0. `uv pip freeze` saved as `requirements.gpu.lock` (173 packages) after the last install |
| `CUBLAS_WORKSPACE_CONFIG=:4096:8`, `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` | **Pass.** Set for every Python process (`scripts/nonet.sh` sets both) |
| Concordia clone at `3643ac0466f748b8055b61feb0b7908411f73d84` | **Pass.** HEAD is tag v1.8.9 (25 Nov 2024). Used via `PYTHONPATH` only; not pip-installed |
| Supplementary zip | **Pass.** 4,537,615 bytes; SHA-256 `e9ffb651…199582` matches. Unzipped in `./agents_zip/`, so `agent_py_files` imports |
| `basic_agent`, `rational_agent` byte-identical to Concordia's | **Pass** (`cmp`) |
| Model downloads at pinned revisions; every weight shard's SHA-256 against the Hub's LFS hashes | **Pass.** gemma-2-9b-it (4 shards), gemma-2-2b-it (2 shards) and all-mpnet-base-v2 (`model.safetensors`) all match (`logs/model_hashes.json`). Downloaded with `HF_TOKEN` read from the environment, never printed or written |
| P0.1 model config | **Pass.** 42 layers, hidden 3,584, 16 query / 8 key-value heads, head dimension 256, sliding window 4,096, soft-caps 50 and 30, vocabulary 256,000 |
| `unset HF_TOKEN`, `HF_HUB_OFFLINE=1`, no network for agent processes | **Pass, with a deviation.** `unshare -rn` fails on this host (`write failed /proc/self/uid_map: Operation not permitted`, because `kernel.apparmor_restrict_unprivileged_userns=1`). Instead of Docker, `scripts/nonet.sh` runs `sudo unshare -n` and then drops straight back to the `ubuntu` user with `setpriv`, under `env -i` (no `HF_TOKEN`), with `HF_HUB_OFFLINE=1` and `TRANSFORMERS_OFFLINE=1`. Verified inside the sandbox: the user is `ubuntu`, `HF_TOKEN` is absent, `curl https://huggingface.co` fails, only `lo` exists, and CUDA sees the A10G and runs a matmul. Every 9B process (smoke tests, agent checks, bank generation) ran through it |

**Loading 9B with 16 GB of RAM.** `refimpl/runtime.py` loads with `torch_dtype=bfloat16`, `attn_implementation="eager"`, `low_cpu_mem_usage=True` and `device_map={"": 0}`. Shards are memory-mapped and moved to the GPU tensor by tensor. Peak resident memory was 5.6 GB (`/usr/bin/time -v`), and system RAM "used" stayed near 1.9 GB, the rest being reclaimable page cache. A load takes about 2.3 minutes, limited by disk reads: the page cache cannot hold all 18.5 GB. Each process loaded one language model. The CPU embedder (all-mpnet-base-v2, 0.4 GB) sits beside the GPU-resident 9B in the Phase 2 and bank-generation processes, as Phase 2 requires. **Loading did not fail for lack of system RAM.**

## 2. Loading code

`refimpl/runtime.py` (new) provides:

- `load_gemma(name_or_path, device)`, which resolves `9b`, `2b` or `embedder` to the snapshot directory of the pinned revision under `./models` and passes that revision;
- `load_lm`;
- `load_embedder`: `SentenceTransformer(path, revision=…, device="cpu")`, called as `lambda t: model.encode(t, show_progress_bar=False)`;
- `env_report`.

`tests/smoke_gemma.py`, `tests/scoring_orders.py` and `tests/smoke_phase2.py` accept `--device cpu|cuda` and use this loader.

## 3. Code fixes

All unit tests pass: **30 passed** (`tests/test_core.py` 12, `tests/test_design.py` 15, `tests/test_banks.py` 3).

1. **N7 donor.** `conditions.n7_donor(p, values)` replaces `v_prime`:
   - The donor has the same variant and seller line, and the nearest (V, C) cell by Manhattan distance among cells whose best-offer set is disjoint from this prompt's.
   - No-information cells use C = 0 and only no-information donors.
   - Ties go to the smaller V, then the smaller C.
   - Cell (5, 5) takes the smallest-overlap donor under the same rule, which is (5, 4).

   `build_conditions`, `run_phase3` and `run_leakage_audit` take the V grid in use (`values`), so the donor set follows the extension if it is triggered. The unit test checks 34 of 35 cells (48 of 49 with V = 7, 8) disjoint, the exception (5, 5), the nearest-donor rule against brute force, and determinism. PROTOCOL.md 1.3, 9.2 (with a donor-rule paragraph) and 9.3 now describe N7 as "the entry's own text written for a nearby prompt whose best offer differs". 9.2 notes that for information cells the donor's stated cost can differ. "Differs only in the valuation" is removed.
2. **Advice-removal rule.** PROTOCOL.md 9.2 now lists every pattern exactly as in `conditions.py` and `core.py`: the sentence split, coin amounts, bare numbers, currency marks, option labels, decision verbs, the full evaluative list (including "fair", "reasonable", "good", …, "open", "opening"), the attached-number rule, the option-label trigger, and how kept sentences are joined.
3. **K1 power.** 10.5 now reads 0.81 SD, matching section 11.
4. **Seeding.** `LocalGemma2._seed` returns without seeding unless a call context is set (`local_gemma2.context_is_set()`, using a `NO_CONTEXT` sentinel), so Phase 1 sampling follows the launcher seed. Unit-tested.
5. **K2 bootstrap.** `analysis.calibration_test` computes bootstrap p-values as (1 + count) / (1 + n) in both directions.
6. **Order.** PROTOCOL.md section 6 (Order) states that engineering checks that record no outcome may precede registration, and lists what they may record.
7. **Scoring on this GPU.**
   - `LocalGemma2(…, sequential=True)` is the default. `letter_scores(…, sequential=None)` scores the five letter sequences one per forward pass (batch size 1), always; it never depends on free memory.
   - Hooks are registered once around all five passes, so capture and steering run in every pass with the same P1.
   - Batched mode (`sequential=False`) remains only for the P0.2 comparison.
   - PROTOCOL.md sections 4, 9.6, 12 and the P0.2 and P0.7 criteria are updated. 10.3 also said "batched", so it was updated too.
   - P0.2 is now "batched versus sequential on short prompts, reported".

Also updated, beyond the prompt's list:

- P0.1 now says "all four weight shards".
- P0.10 lists the 30 tests.
- Section 3 records the A10G as bank-generation and development hardware, with confirmatory hardware to be decided.
- `tests/smoke_phase2.py` and `tests/scoring_orders.py` no longer print offers, probabilities, regret or S. `smoke_phase2.py` uses pilot variant 13.

## 4. 9B engineering checks (no outcomes)

### 4.1 `tests/smoke_gemma.py` on 9B (`--device cuda`)

**All smoke checks pass:**

- rendering;
- position finding: P2 `(`, P3 the end of the seller line, P4 "5 coins back";
- activation capture over 42 layers;
- repeat scoring bit-identical;
- P0.9 zero-steer identity (bit-identical);
- a large steering vector changes the distribution;
- greedy `sample_text` deterministic and honouring terminators;
- `sample_choice`.

**Batched versus sequential on the short prompt (590 prefix tokens), against P0.2's 10⁻³ nats:**

| | Max absolute difference (nats) | Argmax identical |
| --- | --- | --- |
| Whole-answer score | 0.321 (letter a); others 0.063–0.214 | yes |
| First-token log-probability at P1 | 0.140 (letter c); others 0.024–0.053 | yes |

**This fails the old 10⁻³ criterion by a factor of about 300.** The CPU smoke tests were bit-identical across batch shapes; the GPU is not.

A diagnostic on 2B, same prompt type, compared the final hidden state at P1 between batch size 5 and batch size 1. It differs by up to 0.81, on a scale of 96 (about 1%). The cause is bf16 GEMM and attention kernels chosen by batch shape, compounded over the layers. Unembedding in float32 does not remove the difference (0.18 nats remain), so it is not just bf16 logit rounding.

Consequences:

- Within one fixed mode, scoring is deterministic: repeats are bit-identical.
- Across modes or batch shapes, the numerical noise floor is about 0.1–0.3 nats per letter.
- This supports the protocol's decision to fix the scoring mode. It also sets an expectation for cross-hardware replication (section 13, "Numerics").

Batched took 1.19 s and sequential 1.35 s for the five letters.

### 4.2 `tests/scoring_orders.py` on 9B (probability and regret prints removed)

- Mean letter mass at P1 over the five orders: **0.570** (range 0.457–0.816).
- First-token and whole-answer top choices agree in **3 of 5** orders.

### 4.3 Worst-case Phase 3 prompt (sequential scoring, activation capture on, 42 layers)

Pilot prompt v13-V5-neutral, order 1, with `conditions.qa_filler` Notes. Steering: the prompt's own layer-18 P1 activation, added at layer 18. Peak memory is `torch.cuda.max_memory_allocated()`. Weights take 17.21 GiB; the card offers 22.06 GiB to PyTorch.

| Notes block | Tokens per sequence | Mode | Peak GPU memory | Time per pass | Time per scoring (5 passes) | Repeats bit-identical |
| --- | --- | --- | --- | --- | --- | --- |
| 200 tokens (short) | 797 | unsteered | 17.39 GiB | 0.383 s | 1.92 s | yes |
| 200 tokens (short) | 797 | steered L18 | 17.39 GiB | 0.384 s | 1.92 s | yes |
| **3,000 tokens (cap)** | **3,597** | unsteered | **19.40 GiB** | **2.323 s** | 11.6 s | yes |
| **3,000 tokens (cap)** | **3,597** | steered L18 | **19.40 GiB** | **2.323 s** | 11.6 s | yes |
| 3,900 tokens | 4,497 | unsteered | 20.56 GiB | 3.194 s | 16.0 s | yes |
| 3,900 tokens | 4,497 | steered L18 | 20.56 GiB | 3.194 s | 16.0 s | yes |

A 3,000-token Notes block gives 3,597 tokens in total, not about 4,500: the fixed prompt without Notes is only about 600 tokens. Because PROTOCOL.md section 12 quotes "up to about 4,500 tokens", a 3,900-token block (4,497 tokens) was also measured. Both fit, the largest with 1.5 GiB to spare. Steering adds no measurable time or memory.

### 4.4 One Phase 2 decision per agent

Pilot prompt v13-V5-information-C3, real all-mpnet-base-v2 embeddings (CPU). Memory: a temporary blank bank plus the player-specific memory ("… always drives a hard bargain."), as `phase2.formative_memory` adds it. Greedy, determinism patches, no network. Each agent ran twice (`scripts/check_phase2_agents.py`, `logs/check_phase2_agents.run1.json`).

| Agent | Exception | Model calls (text + choice) | S non-empty | Rule memories 1/2/3 reached prompts | Longest prompt (tokens) | Wall time per decision | Peak GPU | S identical across the two runs (SHA-256) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `rational_agent` | none | 6 (5 + 1) | yes | yes / yes / yes | 1,419 | 56.2 s, 54.3 s | 20.07 GiB | **yes** |
| `basic_agent` | none | 12 (10 + 2) | yes | yes / yes / yes | 1,836 | 86.3 s, 85.9 s | 20.87 GiB | **yes** |
| `taehun_cgcal` | none | 7 (5 + 2) | yes | yes / yes / yes | 701 | 10.1 s, 10.1 s | 18.49 GiB | **yes** |
| `fluffy_fluffyagent_v16submission` | none | 5 (4 + 1) | yes | yes / yes / yes | 3,331 | 168.8 s, 168.4 s | 21.17 GiB | **yes** |
| `hgyun_loss_aversion_agent_v3_plus2` | **CUDA out of memory** (both runs) | — | — | — | ≥ 2,424 (the call that failed) | 121.6 s to failure | > 22 GiB | — |

**`hgyun` diagnosis** (a numbers-only rerun, `logs/check_phase2_hgyun_diag.json`):

- Its seventh generation call has a 2,424-token prompt and `max_new_tokens` 1,000.
- It fails allocating 2.31 GiB, which is exactly 2,424 × 256,000 × 4 bytes. In transformers 4.44.2, `Gemma2ForCausalLM.forward` unembeds **every prompt position** during `generate`'s prefill: bf16 logits, bf16 soft-cap temporaries, then a float32 copy. That adds roughly 1.5–2 GB per 1,000 prompt tokens on top of the 17.2 GiB of weights. `num_logits_to_keep` does not exist in this version.
- The agent then retries. Memory held by the failed attempt pushed later peaks up (21.48 GiB for a 925-token prompt that first took 19.19 GiB), and the retry failed again.
- In the second run of the original check, memory from the first failure was never released, so it failed at its first call. The check script now releases the cache and runs `gc` after an exception.
- Phase 3 scoring is unaffected: it unembeds only three positions.

As instructed, the error was logged and the run continued. This blocks Phase 2 (and very likely Phase 1, whose native prompts reach about 7,000 tokens) on a 24 GB GPU. See section 8.

## 5. Formative memories

`scripts/generate_banks.py` generated the 14 banks (variants 1–14) with `phase2.formative_memory` on 9B, greedy, under the determinism patches and in the no-network sandbox, with all-mpnet-base-v2 embeddings on the CPU.

- Each bank is saved as `banks/formative_vNN.parquet` with columns text, time, tags, importance and embedding (float32 lists). The SHA-256 values are in `banks/manifest.json` and `registration/`.
- Each bank was reloaded in the same process with the new loader and compared with the live memory: columns, dtypes, every row (text, time, tags as tuples, importance, embedding bit-exact), the de-duplication hashes and the player config all match.

| Variant | Buyer | File | Rows | Model calls | Wall time | Peak GPU | Round trip | SHA-256 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Anya Blossomwood | `formative_v01.parquet` | 13 | 2 | 147 s | 20.1 GiB | exact | `036088e9e1950a5290e860564893b0e19c23835f51bc605d225890dd69d3d151` |
| 2 | Brynn Orchardheart | `formative_v02.parquet` | 13 | 2 | 141 s | 20.17 GiB | exact | `5ac0a0ceac0b0fbcb303c79893e30ba76c2f56a525cfc7f9ef2913b0dd134483` |
| 3 | Clara Applebrook | `formative_v03.parquet` | 13 | 2 | 136 s | 20.23 GiB | exact | `3e65402bcf2bd7649493f647e09eacf08911594e2412885bc13787f8969536f0` |
| 4 | Della Plumstone | `formative_v04.parquet` | 13 | 2 | 144 s | 20.22 GiB | exact | `95e2c03f2f767a507bb4371412721ee31fe92554ad7a0018f1c68bdacedff206` |
| 5 | Elara Berryvine | `formative_v05.parquet` | 13 | 2 | 157 s | 20.17 GiB | exact | `dd61cd28ee13fd4cc079f32f9bcc719f170eceb53564a020dd4b648d2e34e43e` |
| 6 | Faye Honeydew | `formative_v06.parquet` | 13 | 2 | 149 s | 20.2 GiB | exact | `97f9cde9bdd78a348d3e133014c42247b8acb2a20bca47c5bb91c81d076b58b6` |
| 7 | Gaia Willowbrook | `formative_v07.parquet` | 13 | 2 | 150 s | 20.26 GiB | exact | `4be541713b55ac9cce041f332503f1bff8ba0262151fffe9a04b20d428768708` |
| 8 | Hazel Nutgrove | `formative_v08.parquet` | 13 | 2 | 132 s | 20.19 GiB | exact | `1c28950e1341b60248bc914cd0d02ce29a30fcf5c527ac8032cf68d5f6efed21` |
| 9 | Ivy Pearblossom | `formative_v09.parquet` | 13 | 2 | 142 s | 20.2 GiB | exact | `f76a332b54b7a5bf77ea780cce4361fcebbf7fdaad85e6f6ab4602e214b701bd` |
| 10 | Juniper Quincewood | `formative_v10.parquet` | 13 | 2 | 142 s | 20.17 GiB | exact | `6c9440eb2e2d09a93b72080e6bffd7346152d46cda46eb755341f65fac436ce6` |
| 11 | Kira Citronbloom | `formative_v11.parquet` | 13 | 2 | 150 s | 20.26 GiB | exact | `ca1d3cae5be2606276288aa7b3fb1af965e67a66c4bb0f8a465a4a1ed3ce9286` |
| 12 | Lila Figleaf | `formative_v12.parquet` | 13 | 2 | 156 s | 20.21 GiB | exact | `d65838a2ffeadacf7c9e92ad13a3d269734c3dd550e88accda2114458b74afaa` |
| 13 | Maeve Mulberry | `formative_v13.parquet` | 13 | 2 | 132 s | 20.14 GiB | exact | `32d084fa109e14b2a3d4a7a31bf16983058ecf24407f3befb68d16684d12eca0` |
| 14 | Nova Peachwood | `formative_v14.parquet` | 13 | 2 | 153 s | 20.28 GiB | exact | `ac22fe3bd9fd92c44be8fedc0fd27ddba5e653c6b854061766d707b522d9e66a` |

Every bank has 13 rows. By tag, in variants 1 and 4: 7 `episode`, 1 `info`, 1 `initial_player_specific_memory` and 4 untagged (shared memories and context). One Concordia warning was printed, during variant 4: "Number of generated formative episodes (8) does not match number of formative ages (7)". Concordia pairs episodes with ages using `zip`, so the eighth episode is dropped, as it would be upstream. Total generation time: 34 minutes, with 5.6 GB peak RSS and a peak GPU allocation of 20.3 GiB.


**Loader** (`refimpl/phase2.py`):

- `player_config(variant)` derives the config exactly as `formative_memory` does, and `formative_memory` now calls it.
- `save_bank(mem, path)` writes the parquet with an explicit schema and returns its SHA-256.
- `load_bank(path, lm, embedder, variant)` re-adds the rows in their saved order through `AssociativeMemory.add`, with the stored embeddings (the embedder is not re-run). The frame therefore has the original columns, dtypes and order. Tags are converted back to tuples.
- `_stored_hashes` is recomputed as `hash((text, time, tuple(tags), importance))` in the loading process.

Unit tests (`tests/test_banks.py`):

- a saved bank round-trips;
- re-adding a duplicate row is ignored, while a row differing only in importance is added;
- the duplicate check also holds in a fresh process with a different `PYTHONHASHSEED`.

## 6. Registration package (not published)

- `.gitignore` excludes `.venv/`, `concordia/`, `agents_zip/`, `models/`, `logs/` and `*.parquet`. It also keeps the existing `__pycache__/` and `.pytest_cache/` entries. The bank manifest (`banks/manifest.json`, hashes only) is committed; the parquet files are not.
- The code was committed first, as commit `24b614aa29c3786dace92955f93c2317bf44581a`. `registration/registration.json` and `registration/REGISTRATION.md` then record:
  - that commit hash;
  - the SHA-256 of every code file (all `.py` and `.sh`, PROTOCOL.md, both lock files, `.gitignore`), checked against the committed bytes;
  - the SHA-256 of `requirements.gpu.lock` and of each memory bank;
  - the model and embedder revisions with their weight-shard hashes;
  - the Concordia commit and the zip hash;
  - the GPU (NVIDIA A10G, 23,028 MiB), driver 595.112.07, `torch.version.cuda` 12.1 and cuDNN 90100.
- The second commit holds the registration files, `banks/manifest.json` and this report.
- The A10G is recorded as the **bank-generation and development hardware**. The confirmatory hardware line reads "to be decided", because PROTOCOL.md section 3 specifies a 48 GB GPU.
- `requirements.gpu.lock` is `uv pip freeze` after every install (173 packages: the 159 of `requirements.lock` with CUDA torch, plus the `nvidia-*` packages, `triton` and `pyarrow`).

## 7. Runtime and feasibility

**Measured on this A10G:**

- **Phase 3 pass times, sequential, steered = unsteered:** 0.38 s at 800 tokens, 2.32 s at 3,600, 3.19 s at 4,500. A quadratic through the three points gives about 0.48 s at 1,000 tokens, 0.76 s at 1,500 and 1.07 s at 2,000. One scoring is five passes.
- **Phase 2 decisions with a blank memory:** 10 s (`taehun`), 55 s (`rational`), 86 s (`basic`), 169 s (`fluffy`). `hgyun` was at least 122 s before failing. The mean over the five agents is about 100 s. Real formative memories add retrieved text to prompts, but decoding dominates, so planning uses 1–1.5× that figure.
- **Bank generation:** about 2.4 minutes per variant (2 calls).

**Revised estimates.** L40S figures are scaled, not measured: about 1.4× faster for generation (memory bandwidth 864 vs 600 GB/s) and 2–3× for compute-bound scoring.

| Phase | Workload | A10G (24 GB) | L40S (48 GB) |
| --- | --- | --- | --- |
| 1 | 200 native simulations (not measured; scaled from the protocol's planning figure) | 4–9 GPU-days, **but blocked by out-of-memory on long prompts** | 3–6 |
| 2 | 2,100 greedy + 2,750 sampled decisions at about 100–150 s | 6–9 GPU-days, **but blocked by out-of-memory (`hgyun`)** | 4–6 |
| 3 | 58,800 scorings × 5 passes at prompts of about 1,500–2,500 tokens (0.76–1.42 s per pass) = 2.6–4.8 days, plus 1,680 paraphrases (about 1 day), the native replay and the leakage audit | 4–6 GPU-days | 2–3 |
| 3b | About 980k scorings of N1 prompts (about 1,000–1,500 tokens; 0.48–0.76 s per pass) × 5 passes | **27–43 GPU-days** | 11–17 |
| Total | | about 41–67 GPU-days, with Phases 1–2 not runnable as is | about 20–32 |

The protocol's old 3b estimate (2–3 GPU-days) assumed 0.15 s per batched scoring.

**Is the full study feasible on this A10G with sequential scoring?**

- **Phase 3 and 3b memory: yes.** Every Phase 3 and 3b scoring fits; the worst case at 4,497 tokens is 20.56 of 22.06 GiB.
- **Phases 1 and 2: not as implemented.** `generate` on transformers 4.44.2 materialises float32 logits for the whole prompt, which overflows 24 GB from about 2,400 prompt tokens. One of the three entries already fails on a pilot prompt with a blank memory, and real formative memories make prompts longer.
- **Time.** Even with that fixed, Phase 3b dominates at about 1–1.5 A10G-months, because sequential scoring multiplies passes by five.

Two changes would make the A10G practical, and both are design decisions for the investigator:

- unembed only the last prompt position during prefill, for example with a forward hook on `lm_head` or a wrapper that slices `hidden_states[:, -1:]` in prefill;
- for 3b tuning, which uses only the P1 first-token distribution and the letter mass, one pass per scoring instead of five, which would cut 3b roughly five-fold.

Both change numerics relative to the current reference, so they would have to be registered before any outcome is recorded. Neither was made here.

## 8. Deviations from PROTOCOL.md and from STAGE1_PROMPT.md, with reasons

1. **Instance.** g5.xlarge (16 GB RAM, 4 vCPUs) instead of the g5.2xlarge assumed by STAGE1_PROMPT.md, on instruction. 9B loads straight to the GPU, so this had no effect except slower disk-bound loads.
2. **Hardware.** Banks were generated, and all checks run, on a 24 GB A10G, whereas PROTOCOL.md section 3 specifies a 48 GB GPU for runs. The registration records the A10G as bank-generation and development hardware, with confirmatory hardware to be decided. Section 8.3 already states that bank generation is not bit-reproducible across hardware, which is why the banks are published.
3. **Sandbox.** `sudo unshare -n` + `setpriv` instead of `unshare -rn`, because unprivileged user namespaces are blocked by AppArmor. This is equivalent: no network, the unprivileged user, no `HF_TOKEN`.
4. **Choice scoring is sequential** (registered as a protocol change, sections 4, 9.6, 10.3, 12, P0.2, P0.7). P0.2's old 10⁻³ batched-versus-single criterion fails on the GPU (0.32 nats). P0.2 is now reported, not a gate.
5. **Worst-case prompt length.** A 3,000-token Notes block gives a 3,597-token prompt, not about 4,500. Both 3,597 and 4,497 tokens were measured.
6. **Phase 2 check memory.** A blank bank plus the player-specific memory, as instructed ("temporary blank memory"). The real banks did not exist yet at that point.
7. **Test scripts print no outcomes.** `smoke_phase2.py` and `scoring_orders.py` were changed to print no offers, probabilities, regret or S. `smoke_gemma.py` still prints probabilities for its synthetic note on prompt v01-V5-information-C3. That is a model smoke check with a made-up note, not any agent's output. `smoke_gemma.py`'s 5×10⁻² batched-versus-single assertion was replaced by argmax agreement, since P0.2 is no longer a gate.
8. **Models** are stored in the Hugging Face cache layout under `./models` (`models--…/snapshots/<revision>`), so each load path encodes its revision.
9. **`LocalGemma2` signature.** It gains a `sequential` argument (default `True`). `build_conditions`, `run_phase3` and `run_leakage_audit` gain `values` (default `core.VALUES`).
10. **New files:**
    - `refimpl/runtime.py`;
    - `scripts/download_models.py`, `nonet.sh`, `check_phase3_memory.py`, `check_phase2_agents.py`, `generate_banks.py`, `make_registration.py`;
    - `tests/test_banks.py`;
    - `requirements.gpu.lock`.
11. **REFERENCE.md** was not regenerated in Stage 1. Its code listings predate these fixes.

## 9. Blocks for Stage 2

1. **`hgyun` out of memory in Phase 2 on 24 GB** (section 4.4). Either run Phases 1–2 on the specified 48 GB GPU, or register a prefill change (last-position unembedding) before any outcome is recorded.
2. **Confirmatory hardware is undecided.** P0.7's exact repeatability holds only on one configuration. If confirmatory runs use an L40S, every scoring and generation there will differ numerically from this A10G at the 0.1–0.3-nat level seen in 4.1. That is fine for the design, which loads published banks, but it means all phases must run on the same registered GPU.
3. **Phase 3b compute** (27–43 A10G-days; 11–17 L40S-days) is far above the old 2–3-day plan. Consider registering one-pass first-token scoring for 3b tuning.
4. **P0.2 wording.** The 10⁻³ figure is now a reported reference, not a pass criterion. Confirm this is acceptable before registration.
5. **REFERENCE.md** must be regenerated so its listings match the committed code, before registration.
