# MIGRATION.md: AWS (A10G) to a RunPod pod (written Nov 24; nothing on the AWS machine was stopped or deleted)

## 1. Inventory of everything not in git (git status --ignored, measured Nov 24)
Untracked but not ignored files: none. Ignored items (32 entries) grouped:

| Group | Paths | Size | Status | Re-creation if dropped |
| --- | --- | --- | --- | --- |
| Adapters | demo_out/adapters/ (54 adapter folders, 162 files); demo_out/adapters_check/ (17 MB); demo_out/dead_ends/ (17 MB, a rejected adapter) | 925 MB + 17 MB + 17 MB | **to back up** (HF repo; see section 4) | Not cheaply: each is 20-60 min of GPU time; the 51 with a run file are verified by sha256 |
| Logs | logs/ (123 files: chain logs, floor logs, model_hashes.json, check outputs) | 680 KB | **to back up** | Not re-creatable (they record the runs) |
| Activation caches | demo_out/acts_rows.pt, p1_acts.pt, steer_acts_train.pt, vectors.pt | 226 MB | **to back up** | Re-creatable by the steering scripts (GPU, about 1 h) but kept |
| Partial scores | demo_out/tune_partial.jsonl | 132 KB | **to back up** | Superseded; kept |
| Contest agents | agents_zip/ | 11 MB | **to back up** | From the original contest download only |
| Banks | banks/formative_v01..v14.parquet | 0.9 MB | **to back up** | scripts/generate_banks.py from the manifest (CPU) |
| Model weights | models/ (Gemma 2 9B-it 18 GB, Gemma 2 2B-it 4.9 GB, all-mpnet-base-v2 0.4 GB, pinned revisions) | 23.6 GB | **dropped** (not backed up) | scripts/download_models.py at the pinned revisions with shard sha256 checks (needs HF_TOKEN with the Gemma licence accepted). Pins: 9B 11c9b309abf73637e4b6f9a3fa1e92e615547819, 2B 299a8560bedf22ed1c72a8a11e7dce4a7f9f51f8, mpnet e8c3b32edf5434bc2275fc9bab85f82640a19130 |
| Python env | .venv/ (Python 3.11.18, torch 2.4.1, transformers 4.44.2, peft 0.12.0) | 5.9 GB | **dropped** | requirements.gpu.lock (exact versions) via scripts/setup_pod.sh |
| Concordia | concordia/ (clean checkout, no local changes) | 73 MB | **dropped** | git clone at 3643ac0466f748b8055b61feb0b7908411f73d84 |
| Caches | .pytest_cache/, __pycache__/ (demo, refimpl, tests); ~/.cache/huggingface (token metadata only, 0.8 MB) | 2 MB | **dropped** | Regenerated automatically |
Outside the repo on this machine: ~/.claude (184 MB, Claude Code session transcripts and memory, private conversation content) is **not backed up** here and is not needed to run anything; the HF token and the GitHub login are secrets and are never copied (the pod gets them as secrets).

## 2. Git state (Nov 24)
Branches: demo (all recent work; pushed), main (4 commits ahead of origin/main: the Stage 1 and reference-rebuild commits; they were already contained in origin/demo, so nothing new became public; pushed), stage1-wip (pushed, nothing ahead), refactor (exists only on origin; no local branch, no local work; head 6636d4b). The check below was run after the final commit: git status clean and `git log origin/<b>..<b>` empty for demo, main and stage1-wip. Result recorded in section 7.

## 3. Pod choice (RunPod)
- GPU: Ampere with 48 GB, preferably **A40 or RTX A6000** (same architecture family as the A10G, so scoring numbers stay comparable; 48 GB leaves room for 9B plus LoRA training at fp32 adapters without checkpoint changes). Avoid Hopper/Ada cards for the parity check: first-token probabilities must match the A10G run within the stored tolerances (max abs 1e-3), and different kernels can move them; if parity fails on another architecture, say so and do not mix numbers.
- Storage: a **100 GB network volume** mounted at /workspace (models 24 GB, venv 6 GB, adapters 1 GB, caches); WORKDIR and HF_HOME point there so a restarted pod keeps everything.
- Secrets: **HF_TOKEN as a pod secret** (read access to the private artifact repo and to google/gemma-2-9b-it with the licence accepted); for pushing from the pod, a GitHub token as a second secret (GH_TOKEN) used with `gh auth setup-git`. Never put either in a file in the repo.
- Image: any CUDA 12.x image with python3.11, git and curl (the lock pins torch 2.4.1, which brings its own CUDA 12.1 runtime).

## 4. Backup of what git cannot hold
Destination: private HF model repo `dalyathan/concordia-scaffold-artifacts` (paths mirrored exactly). Manifest: artifacts_manifest.json (path, bytes, sha256 of every file; 392 files, 1,252,998,217 bytes), committed to demo. Scripts: scripts/make_artifacts_manifest.py, scripts/backup_to_hf.py (create the private repo and upload; idempotent), scripts/verify_backup.py (download into a temporary directory, compare every sha256 to the manifest, compare each adapter with the sha256 in its run file, print counts, delete the temporary copy only if all match).
**Status: the upload did not happen.** The HF_TOKEN on this machine is read-only (whoami reports role "read"); creating the repo returned `403 Forbidden: You don't have the rights to create a model under the namespace "dalyathan"`. No other credential was tried and no other destination was used (a private GitHub repo or a cloud bucket would be a different service than the one chosen, so that is left to the owner).
What was verified locally instead: the manifest matches the files on disk (392 of 392), and 51 adapters match the sha256 stored in their run files (0 mismatched, 0 missing); `python scripts/verify_backup.py --local .` prints "ALL MATCH". Verification of the remote copy (step 4 of the request) was not possible.
To finish: put a write-enabled token in HF_TOKEN (a fine-grained token with "write" on your own namespace, or a classic write token), then on this machine
`.venv/bin/python scripts/make_artifacts_manifest.py && .venv/bin/python scripts/backup_to_hf.py && .venv/bin/python scripts/verify_backup.py`
(re-run the manifest first if any log has grown; the upload script refuses files that changed after the manifest). Commit the refreshed manifest.

## 5. Pod setup
`HF_TOKEN=... BRANCH=demo bash scripts/setup_pod.sh` (also copy it from the repo: `curl -fsSL https://raw.githubusercontent.com/dalyathan/concordia-scaffold-study/demo/scripts/setup_pod.sh -o setup_pod.sh`). It clones the repo and the branch, clones concordia at the pinned commit, builds the venv from requirements.gpu.lock and asserts torch 2.4.1 / transformers 4.44.2 / peft 0.12.0 / CUDA, downloads the artifact repo and checks every sha256 against artifacts_manifest.json, downloads the pinned models with shard-hash checks, and runs the demo tool's adapter startup check (adapter off == plain bit for bit; adapters reproduce stored tune probabilities) and requires "startup checks passed". Nothing in it assumes AWS (no instance metadata, no ubuntu user, no fixed paths). It has been syntax-checked (`bash -n`) but not run here, because it would need the pod, a write-enabled artifact repo and about 30 GB of downloads.

## 6. Order of jobs on the pod (do not run on AWS)
1. `scripts/setup_pod.sh` (includes the adapter manifest check).
2. Demo adapter check: `PYTHONPATH=concordia:. .venv/bin/python demo/floor.py --serve --dataset gen` and look for "startup checks passed" (already part of step 1; repeat after any restart).
3. Gemma parity check on the refactor branch: `git checkout refactor`, then `python -m harness.run --task haggling --solver plain --model gemma2_9b --split tune`, `python tools/parity_check.py <the new record> --legacy runs/haggling/gemma2_9b/legacy-plain-tune-s0.json`, then the adapter variants as written in tools/parity_check.py. Exit 0 required before any new number comes from the harness. If parity fails, stop and report; do not continue with new numbers.
4. GEN2 test look (GEN2_TEST_PLAN.md) only after: the owner's explicit go, the look script written with its sha256 in the plan, and gate G3 on plan plus script. The look runs once from demo, using the adapters in demo_out/adapters verified in step 1.

## 7. Final report
**Safe to stop AWS: NO.**
Reason: the adapters (0.96 GB, 51 of them with run-file hashes), logs, activation caches and agents_zip exist only on this machine. The upload to the private HF repo failed with 403 because the HF_TOKEN here is read-only, and no other destination was used. Everything else is safe: all code, results and plans are in git (demo, main and stage1-wip pushed; refactor is on origin), and models, venv and concordia are re-creatable from pins.
To make it "yes": run the three commands in section 4 with a write-enabled HF_TOKEN; `verify_backup.py` must print "ALL MATCH" (files matched 392 of 392, adapters 51 of 51) and delete its temporary copy. Counts so far: remote check not possible (files 392 in the manifest, matched 0 remotely, mismatched 0, missing 392); local check: matched 392, mismatched 0, missing 0; adapters vs run files: matched 51, mismatched 0, missing 0.
Branch state at the end of this step: see the commit that contains this file; checks run: `git status` clean and `git log origin/<b>..<b>` empty for demo, main, stage1-wip.
