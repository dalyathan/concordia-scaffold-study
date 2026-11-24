# DECISIONS.md (demo branch; the refactor branch keeps its own DECISIONS.md)

## Nov 24: migration off AWS
- Scope: back up and tidy only; nothing on the AWS machine was stopped, deleted or moved; the progress loop and tmux sessions were left alone.
- Branch main was 4 commits ahead of origin/main. They were already in origin/demo (public), so pushing main publishes nothing new; pushed. refactor exists only on origin (no local work).
- The HF_TOKEN on this machine is read-only: repo creation returned 403. I did not try other credentials or create a private repo elsewhere (GitHub, bucket): the owner chose the HF repo, and sending the artifacts to a different service is the owner's decision. Prepared instead: artifacts_manifest.json (392 files), scripts/backup_to_hf.py, scripts/verify_backup.py; manifest and the 51 adapter sha256 values verified locally. Result: "safe to stop AWS: no" until the upload is run with a write token and verified.
- Dropped (re-creatable): models/ (pinned downloads), .venv (lock), concordia/ (pinned clone), caches. Not backed up: ~/.claude session data (private, not needed to run).
- Backed up (when the upload runs): adapters, adapters_check, dead_ends, logs, activation caches, tune_partial, agents_zip, banks.
- setup_pod.sh requires "startup checks passed" from the demo tool and asserts exact torch/transformers/peft versions; Ampere 48 GB (A40/RTX A6000) preferred for parity with the A10G.

- Nov 24 05:34 UTC: the HF artifact repo was found private with 394 files; I re-ran scripts/verify_backup.py (392/392 matched, 51/51 adapters matched, 0 mismatched, 0 missing, copy deleted) and changed the migration verdict to "safe to stop AWS: yes".
