# Reference implementation

This document holds the reference implementation of the harness, condition builders, pipeline driver and analysis described in PROTOCOL.md, with its test results. Where the two disagree, PROTOCOL.md is authoritative and the disagreement is a bug to report.

## R1. Overview

### Layout

| File | What it does | Protocol sections |
|---|---|---|
| `refimpl/core.py` | Prompt set (420 prompts, 35 cells; extension V = 7, 8), best offers, regret, unique-best cells, cell split, seeds, reasoning text S and S\_reason (with answer stems), text utilities | 1.2, 4, 6, 8.1, 8.4, 10.1 |
| `refimpl/local_gemma2.py` | `LocalGemma2`: local stand-in for `together_ai.Gemma2` (system texts, few-shots, trimming, whole-answer and first-token letter scoring). Choice scoring is sequential (one candidate per pass) and fixed. Also: hook support, the letter-mass coherence measure, the generation-cache reset, and per-call seeding only inside a call context | 1.2, 4, 10.4 |
| `refimpl/determinism.py` | Sequential executor, seeded `default_rng`, deterministic torch | 4 |
| `refimpl/runtime.py` | Loads 9B (or 2B) from the pinned snapshot: bfloat16, eager attention, `low_cpu_mem_usage`, `device_map={"": 0}`. Loads all-mpnet-base-v2 on the CPU. Reports the environment | 3 |
| `refimpl/phase2.py` | Formative memories; player config; saving and loading memory banks (de-duplication hashes recomputed at load). Builds an agent as `haggling.py` does, seeds the decision, feeds it the script, and returns offer, regret, S, S\_reason and every model call | 8 |
| `refimpl/phase3.py` | Fixed decision prompt, token positions P1–P4, activation capture, steering hook; returns first-token and whole-answer p(k) | 9.1, 9.6, 10.3 |
| `refimpl/conditions.py` | The 28 Phase 3 conditions, the N7 donor rule, advice removal (including bare numbers and currency marks), format-matched filler, paraphrase retries, leakage-audit prompt | 9.2 |
| `refimpl/steering.py` | Layer and α grid, rescaling, (layer, α) tuning with a "no steering" option | 10.2, 10.4 |
| `refimpl/pipeline.py` | Run driver: Phase 2 and E1 with the exclusion rule; paraphrases; Phase 3 scoring and activation storage; native replay; leakage audit and its flag; pilot power rule; named directions (robust to dropped paraphrases); letter-span projection (E6); matched content copy; 1,000 random directions; tuning and test evaluation (`run_phase3b`) | 6, 8–10, 12 |
| `refimpl/analysis.py` | Sign-flip tests (exact for n ≤ 20), Wilcoxon (sensitivity), IUT, reverse rule, Holm (0.05 and 0.01), BH, bootstrap, verdicts, power simulation, A/B/R assembly, K1 (six components, including sharpening and the matched random permutation p), K2 (unique-best cells, partial correlation, five controls, bootstrap p = (1 + count)/(1 + n)), K1/K2 assembly, fidelity (E9) | 6, 9.3, 10.5, 11 |
| `tests/test_core.py`, `tests/test_design.py`, `tests/test_banks.py` | 30 unit tests (check P0.10) | 6 |
| `tests/smoke_gemma.py` | Phase 3 path on a real Gemma 2 checkpoint (P0.2, P0.7 and P0.9 logic) | 6 |
| `tests/scoring_orders.py` | Letter mass and first-token versus whole-answer top-choice agreement across the five option orders on one prompt (prints no probabilities or regret) | 1.2 |
| `tests/smoke_phase2.py` | One Concordia `rational_agent` decision through the Phase 2 harness on a pilot prompt, run twice; prints only call counts, retrieval flags and hashes (P0.6 and P0.7 logic) | 6 |
| `scripts/download_models.py` | Downloads the pinned revisions and checks every weight shard against the Hub's LFS SHA-256 | 3, P0.1 |
| `scripts/nonet.sh` | Runs a command with no network, as the unprivileged user, without `HF_TOKEN` | 5 |
| `scripts/check_phase3_memory.py`, `scripts/check_phase2_agents.py` | 9B engineering checks: Phase 3 peak memory and time per pass; one Phase 2 decision per agent, recording no outcome | 6 (P0.6, P0.11) |
| `scripts/generate_banks.py` | Generates and saves the 14 formative-memory banks, with a save-and-reload equality check | 6, 8.3 |
| `scripts/make_registration.py` | Writes the registration record (hashes, revisions, hardware) | 11 |
| `scripts/build_reference.py` | Builds this document with verbatim code listings | — |

### Environment

The code runs on the stack pinned in Protocol section 3:

- Python 3.11, torch 2.4.1, transformers 4.44.2, numpy 1.26.4, scipy 1.14.1, pandas 2.0.3, frozen in `requirements.lock` (CPU torch, 159 packages);
- for GPU runs, the same lock with `torch==2.4.1` from PyPI (CUDA 12.1 build), its `nvidia-*` packages and `pyarrow==17.0.0`, frozen in `requirements.gpu.lock` (173 packages);
- Concordia v1.8.9 (commit `3643ac0466f748b8055b61feb0b7908411f73d84`) on `PYTHONPATH`;
- the directory containing `agent_py_files/` (from the supplementary zip) on `PYTHONPATH`.

It uses no API newer than transformers 4.44.2. Every process that imports agent code runs without network and without `HF_TOKEN`, with `HF_HUB_OFFLINE=1`, `CUBLAS_WORKSPACE_CONFIG=:4096:8` and `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` (`scripts/nonet.sh`).

### How to run

```
python scripts/download_models.py                  # needs HF_TOKEN; verifies shard hashes
unset HF_TOKEN; export HF_HUB_OFFLINE=1
PYTHONPATH=concordia:agents_zip:. python -m pytest -q tests/
scripts/nonet.sh python tests/smoke_gemma.py 9b --device cuda
scripts/nonet.sh python tests/scoring_orders.py 9b --device cuda
scripts/nonet.sh python tests/smoke_phase2.py 2b --device cuda
scripts/nonet.sh python scripts/check_phase3_memory.py --notes-tokens 200 3000 3900
scripts/nonet.sh python scripts/check_phase2_agents.py
scripts/nonet.sh python scripts/generate_banks.py
```

`9b`, `2b` and `embedder` resolve to the snapshot directories of the pinned revisions under `./models`.

The full study calls these, in the order of Protocol section 12:

1. `pipeline.run_phase2` (memories loaded with `phase2.load_bank`), then again with `temperature=0.5, draws=range(5)` for E1;
2. `run_paraphrases`, `run_phase3`, `run_native_replay` and `run_leakage_audit`, passing `values=core.VALUES + core.EXT_VALUES` if the extension is triggered;
3. `run_phase3b`;
4. `analysis.abr_tests`, `analysis.k_tests` and `analysis.confirmatory_verdicts`.

The pilot uses `run_phase3(..., only=("N0", "N1"))` and `pilot_power_rule`.

`steering.LAYERS` (6–30) assumes 9B's 42 layers.

### Design notes

- **Sequential letter scoring.** The five answer sequences share a prefix and differ only in the letter token. Each is scored in its own forward pass through the decoder stack (`model.model`, no cache, batch size 1). The mode is fixed, so shapes, and therefore rounding, never depend on free memory. Only the positions that predict answer tokens go through the unembedding; the final soft-cap (30) and the log-softmax are computed in float32. A batched mode exists only for check P0.2.
- **Two scorings from the same passes.** The first-token log-probability of each letter at P1 (the Phase 3 primary) and the whole-answer score (letter, end-of-turn and newline, Concordia's rule) come from the same five passes.
- **Coherence.** Every pass shares P1, so pass b's first-position log-probability of its own letter is the probability of letter b. Their sum is the letter mass, which the tuning coherence rule uses and every condition reports.
- **Hooks in every pass.** Capture and steering hooks are registered once around the five passes, so they fire in each, at the same P1. Captured positions are at or before P1 and identical across passes.
- **Generation cache.** transformers 4.44.2 keeps Gemma 2's generation cache on the model and reuses it when large enough. That makes floating-point rounding depend on earlier calls, so `sample_text` deletes it before each call.
- **Seeding scope.** Per-call seeds apply only inside `call_context(...)` (Phases 2–3). Without a context (Phase 1), nothing is re-seeded and sampling follows the launcher's seed.
- **Memory banks.** A bank is saved as parquet (text, time, tags, importance, embedding). Loading re-adds the rows in order through `AssociativeMemory.add` with the stored embeddings, so the frame's columns, dtypes and order match the original. It also recomputes `_stored_hashes` as `hash((text, time, tuple(tags), importance))`, because Python's string hashes change between processes.
- **Memory copy.** `AssociativeMemory` holds a `threading.Lock` and cannot be deep-copied. Each Phase 2 run makes a blank memory on its own clock and copies the stored bank's rows and hashes into it. The decision then starts by seeding the global generators, because memory sampling uses numpy's global state.
- **Positions.** P1 is the last prefix token. P2–P4 come from the tokenizer's offset mapping on the decoded prefix, with an assertion that re-tokenising gives the same ids.
- **Steering** adds α·v to the chosen layer's output from P1 onwards, in each of the five passes.
- **Agent code** from the zip is imported only by the pipeline and the check scripts, always without network. A static audit found no network, subprocess, `eval`/`exec` or file-writing calls in the three entry files.

