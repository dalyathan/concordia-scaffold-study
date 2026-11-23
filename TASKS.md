# Adding a task

A task is a Python class in `harness/tasks/<name>.py` that exposes `TASK = <Class>`. Nothing in shared code names a task or a model.
The toy `harness/tasks/parity.py` (CPU only, 60 lines) is the template; `harness/tasks/haggling.py` is the full example.

## The interface (`harness/task.py`)

| member | meaning |
| --- | --- |
| `name`, `splits`, `locked_splits` | split names; locked splits are refused by `evaluate()` without a lock token (G3 plus an owner go) |
| `cases(split)` | list of case dicts, each with `cid`, `split`, `type`. Build train / tune / locked-test from a fixed seed and disjoint cells |
| `n_options(case)`, `orders(case)` | number of options and the option orders the readout averages over |
| `render(case, order)` | `(prompt text ending right before the answer letter, {letter: option index})` |
| `payoffs(case)` | expected payoff of each option, **delegating to `harness/protected/payoffs/<name>.py`** |
| `reference(case)` | reference solver: `{"best_options": [...], "best_payoff": x}` |
| `case_type(case)` | the type used for per-type reporting |
| `planted_cases()`, `planted_expected()` | known-answer cases (see below) |

## Steps

1. Write `harness/protected/payoffs/<name>.py` with `payoffs(case)`. This directory is protected: after writing it, run
   `python -m tools.lock_protected --write`, paste the printed `PROTECTED <path> sha256 <hash>` lines into `DECISIONS.md` with a
   one-line reason. `tests/harness/test_protected.py` and `evaluate()` fail without them.
2. Write `harness/tasks/<name>.py` (copy `parity.py`). Keep generators seeded and pure; if existing case files must be reproduced,
   compare sha256 as `tests/harness/test_haggling_port.py` does.
3. Register it in `harness/task.py` (`TASKS = {...}`).
4. Add an independent payoff rule for it to `tools/recompute.py` (a separate copy on purpose: the recompute must not import project code).
5. Plant at least two known-answer cases whose best option you can verify by hand; they are scored in every evaluation and reported
   in their own column (`planted ok`), never in the mean. A solver that fails them is flagged in the record.
6. Smoke test on CPU: `python -m harness.run --task <name> --solver oracle --split tune` must give regret 0 and `planted.all_ok = true`;
   `--solver uniform` must give the chance-level regret. Add the two asserts to `tests/harness/`.

## Solvers (conditions)

`harness/solver.py`: a solver has `name`, `describe()` (stored in the run record) and `letter_probs(task, case, order)`.
CPU solvers (`constant`, `uniform`, `oracle`, `random`) are in `harness/solvers/cpu.py`. Model solvers are in `harness/solvers/hf.py`:
`plain`, `lesson` (a text file placed before the case; its sha256 is recorded), `steering` (vector file, layer, scale) and `lora`
(an adapter directory; its hash is recorded). They read every model fact from the model's YAML config (`harness/models/<name>.yaml`).
To add a model: copy a YAML file, then run `python tools/model_checks.py --models <name> --write` (needs the tokenizer files;
gated repos need `HF_TOKEN`).

## Running and reporting

    python -m harness.run --task haggling --solver plain --model gemma2_9b --split tune     # GPU box
    python tools/recompute.py runs/            # independent recompute from the per-case rows
    python tools/make_report.py                # RESULTS_GENERATED.md
    python tools/check_claims.py               # README numbers against CLAIMS.yaml
    python -m pytest -q tests/harness
