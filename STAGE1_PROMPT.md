# Stage 1 instructions for Claude Code

You are working in ~/concordia-scaffold-study on an AWS g5.2xlarge: one NVIDIA A10G (24 GB), 8 vCPUs and 32 GB RAM. PROTOCOL.md is the authoritative experiment protocol, and refimpl/ and tests/ are its reference implementation.

This is **Stage 1, a development run**. Its job is to get everything working on the real 9B model, generate the formative-memory banks and prepare the registration package.

Ground rules:

- Do not run the pilot or any confirmatory phase.
- Do not compute, print or save any offer, regret, S text or calls log for any agent.
- Do not ask me questions. Make reasonable choices, log them in STAGE1_REPORT.md, and stop when done.
- Run anything longer than about 5 minutes with `nohup … > logs/<name>.log 2>&1 &`, then poll the log.
- Never modify files in agent_py_files/. If an agent raises an error, log it and continue.

## 1. Environment

1. Install Python 3.11 with uv. Create .venv and install requirements.lock, but take `torch==2.4.1` from PyPI (the CUDA 12.1 build with its nvidia-* packages) instead of the CPU build. Add `pyarrow==17.0.0`; newer pyarrow fails with numpy 1.26.4.
2. Before any Python runs, set these in the shell: `CUBLAS_WORKSPACE_CONFIG=:4096:8` and `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`.
3. Clone google-deepmind/concordia into ./concordia and check out commit 3643ac0466f748b8055b61feb0b7908411f73d84. Use it through `PYTHONPATH`; do not pip-install it.
4. Download the NeurIPS supplementary zip linked in PROTOCOL.md section 3 into ./agents_zip/.
   - Check its size is 4,537,615 bytes and its SHA-256 is e9ffb65167d776fd4beae14ee65cd3b44ec9c489870698c203f7acdefc199582. Stop if either differs.
   - Unzip it there, so that ./agents_zip/agent_py_files is importable.
   - Take `basic_agent` and `rational_agent` from Concordia (`concordia.factory.agent.*`); they are byte-identical to the zip's copies.
5. Using the `HF_TOKEN` environment variable (never print it or write it to disk), download into ./models/:
   - google/gemma-2-9b-it at revision 11c9b309abf73637e4b6f9a3fa1e92e615547819;
   - google/gemma-2-2b-it at revision 299a8560bedf22ed1c72a8a11e7dce4a7f9f51f8;
   - sentence-transformers/all-mpnet-base-v2 at revision e8c3b32edf5434bc2275fc9bab85f82640a19130.

   Check every weight shard's SHA-256 against the LFS hashes the Hugging Face API lists at that revision (9B has four shards; fix "both shards" in P0.1).
6. Then run `unset HF_TOKEN` and `export HF_HUB_OFFLINE=1`. Every process that imports agent_py_files must run without network, for example by prefixing it with `unshare -rn`. Check first that the GPU is still visible inside it. If `unshare` is unavailable, log that and use `docker run --network none --gpus all` instead.

## 2. Loading (write refimpl/runtime.py)

- Load 9B with `AutoModelForCausalLM.from_pretrained(path, revision=…, torch_dtype=torch.bfloat16, attn_implementation="eager", device_map={"": 0})`.
- Load the embedder with `SentenceTransformer(path, revision=…, device="cpu")` and call it as `lambda t: model.encode(t, show_progress_bar=False)`. It runs on the CPU because the embeddings go into the hashed memory banks.
- Make the test scripts accept `--device cuda` and use this loader.

## 3. Code fixes (then run all unit tests; all must pass)

1. **N7 donor.** N7 is the entry's S from a donor prompt with the same variant and seller line, whose set of best offers does not overlap this prompt's set.
   - Choose the donor cell nearest in (V, C) by Manhattan distance among cells with a disjoint optimal set. No-information cells use C = 0 and only no-information donors.
   - Break ties by the smaller V, then the smaller C.
   - Cell (V=5, C=5) has every offer optimal, so no disjoint donor exists. For it, use the donor with the smallest overlap under the same rule, and exclude it from the disjointness test.
   - Unit tests: 34 of 35 cells (48 of 49 with V = 7, 8) have a disjoint donor; the choice is deterministic.
   - In PROTOCOL.md 1.3, 9.2 and 9.3, describe N7 as "the entry's own text written for a nearby prompt whose best offer differs". For information cells the donor's stated cost can differ. Remove "differs only in the valuation".
2. **Advice-removal rule.** Make PROTOCOL.md 9.2 list exactly the regexes and word lists in conditions.py, including the bare-number, currency-mark and option-label rules.
3. **K1 power.** It is 0.81 SD everywhere (fix the 0.83 in section 10.5).
4. **Seeding.** `LocalGemma2._seed` applies per-call seeding only when a call context is set (Phases 2–3), so Phase 1 sampling follows the launcher seed.
5. **K2 bootstrap.** In `analysis.calibration_test`, compute the bootstrap p-values as (1 + count) / (1 + n).
6. **Order.** In PROTOCOL.md section 6 (Order), add that engineering checks that record no outcome may precede registration.
7. **Scoring on this GPU.**
   - Batch-of-five eager attention on long prompts does not fit in 24 GB.
   - Give `LocalGemma2.letter_scores` a fixed `sequential=True` mode that always scores the five letter sequences one at a time. It must never depend on whether memory runs out.
   - Capture activations and apply steering in every pass. Hooks must see the same P1 in each pass.
   - Update PROTOCOL.md sections 4, 9.6 and 12, and the criteria for P0.2 and P0.7 (P0.2 becomes "batched versus sequential on short prompts, reported").

## 4. 9B engineering checks (no outcomes)

1. Run tests/smoke_gemma.py on 9B, both batched and sequential on its short prompt. Report the batch-versus-sequential difference against P0.2's 10⁻³ nats.
2. Run scoring_orders.py on 9B with the probability and regret prints removed. Report only mean letter mass and first-token versus whole-answer top-choice agreement.
3. Build a worst-case Phase 3 prompt: a 3,000-token Notes block of filler, about 4,500 tokens in total. Score it sequentially, unsteered and steered at layer 18. Record the peak GPU memory (`torch.cuda.max_memory_allocated`) and the time per pass.
4. Run one Phase 2 decision for each of the five agents: `rational_agent`, `basic_agent` and the three entries.
   - Use pilot prompt v13-V5-information-C3, real all-mpnet-base-v2 embeddings and a temporary blank memory.
   - Record only:
     - whether it raised an exception;
     - the number of model calls;
     - whether S is non-empty;
     - whether each rule memory reached the prompts;
     - the longest prompt in tokens;
     - wall time.
   - Run each agent twice, and confirm byte-identical S by comparing SHA-256 values only.

## 5. Formative memories

1. Generate the 14 banks (variants 1–14) with `phase2.formative_memory` on 9B, greedy, under the determinism patches.
2. Save each bank as parquet with columns text, time, tags, importance and embedding, and record each file's SHA-256.
3. Write a loader in refimpl/phase2.py. It rebuilds the memory and the player config as `phase2.formative_memory` derives them.
   - It recomputes `_stored_hashes` as `hash((text, time, tuple(tags), importance))`, converting tags back to tuples, because Python's string hashes change between processes.
   - Unit tests:
     - a saved bank round-trips;
     - re-adding a duplicate row is ignored.

## 6. Registration package (do not publish)

1. Create a .gitignore excluding .venv/, concordia/, agents_zip/, models/, logs/ and *.parquet, then git-commit the code.
2. In registration/, write:
   - that commit hash;
   - the SHA-256 of every code file, requirements.gpu.lock and each memory bank;
   - the model and embedder revisions;
   - the GPU, driver, `torch.version.cuda` and cuDNN versions.

   Commit that in a second commit.
3. Record this A10G as the **bank-generation and development hardware**. Leave the confirmatory hardware line marked "to be decided", because PROTOCOL.md section 3 specifies a 48 GB GPU.
4. Save `uv pip freeze` as requirements.gpu.lock at this point, after every install.

## 7. Report

Write STAGE1_REPORT.md. It must cover:

- every check, passed or failed;
- measured times per Phase 2 decision and per Phase 3 pass (short and worst case, steered and unsteered), with a revised GPU-day estimate for every phase on this GPU and on a 48 GB L40S;
- whether the full study is feasible on this A10G with sequential scoring;
- every deviation from PROTOCOL.md, with reasons;
- anything that blocks Stage 2.

Then stop.
