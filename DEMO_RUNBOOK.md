# DEMO_RUNBOOK.md - Dec 2 stage demo (generated cases; display only)

**Rule for the stage:** everything on screen is a display of single cases. No test-set conclusion is drawn from these cases (the test look was made once and is reported in DEMO_STATUS.md; the live case is a test_same cell chosen by a fixed rule, see below). Do not run `say` as evidence (stage rule below).

## Setup (before the room fills)
```
cd /home/ubuntu/concordia-scaffold-study
PYTHONPATH=concordia:. .venv/bin/python demo/floor.py --serve --dataset gen
```
Loads in about 20 s and prints "startup checks passed: adapter off == plain bit for bit; adapters {...} reproduce stored tune probabilities". If that line is missing or an assertion fires, do NOT go live: use the replays below. Adapters (loaded once, switched with set_adapter): `examples` = claude_examples lr 1e-4 seed 1 (the seed with the lowest selection-set-B soft regret, 0.0269 vs 0.0270 and 0.0666; chosen on set B, not on test), `teacher` = teacher-distil lr 1e-4 seed 0, `method` = method_original-distil lr 1e-4 seed 0. Warm-up: type each beat once before the audience arrives (each new scoring takes 1.4-1.9 s; repeats are cached and take 0.00 s).

Live cases (fixed rule in demo/gen_demo_choose.py, result demo/gen/demo_live_cases.json; first test_same cell in file order that qualifies):
- MAIN `V3-gB-information-C2-p1_10-w1-n0` (stated cost 2 below resale 3; prices 2 3 4 5 6): plain soft regret 1.47 >= 1 coin, examples top offer = best offer (2).
- BACKUP no-cost `V9-gB-neutral-p3_7-w0-n0`: no cell reached plain regret 1 coin, so the declared fallback was used (largest plain soft regret among cells where the examples top offer is best: 0.83).
- BACKUP at-or-above `V3-gC-information-C4-p1_5-w0-n0` (cost 4 >= resale 3): plain soft regret 1.19.

## The four beats (type the commands; every command prints its time and takes under 2 s on the 9B)
Each beat has a script: `demo/beats/beatN.txt`, recorded as `demo/replays/beatN.jsonl`.

**Beat 1 - plain Gemma fails** (about 90 s)
```
case V3-gB-information-C2-p1_10-w1-n0
shuffle
cost 1
cost none
table
```
Expect: plain offers 4, best is 2, regret 2.00 (soft 1.47; bars 0.13 / 0.35 / 0.43 / 0.09 / 0.00). `shuffle`: pick changes to 3 under the new order ("PICK CHANGED", regret 1.00, 0.3 s). `cost 1`: offer 2, regret 0.00 (soft 0.56); `cost none`: offer 2, regret 0.00 (soft 0.17). Say: the stated cost is on the page, the answer moves with the option order.

**Beat 2 - the method as text** (about 60 s)
```
case V3-gB-information-C2-p1_10-w1-n0
text method
plain
text teacher
plain
```
Expect: with the method paragraph in the prompt: offer 2, regret 0.00, soft 0.00 (1.9 s); with the teacher paragraph: offer 2, soft 0.04. `plain` returns to offer 4.

**Beat 3 - the same, moved into the weights: adapter on and off** (about 2 min)
```
case V3-gB-information-C2-p1_10-w1-n0
adapter examples
adapter off
adapter teacher
adapter method
adapter examples
cost none
cost 1
table
```
Expect: examples adapter: offer 2, probability 1.00 on 2, regret 0.00, soft 0.00; `adapter off`: back to plain exactly (offer 4, regret 2.00; asserted bit-for-bit at startup); teacher adapter soft 0.20 (0.81 on 2); method adapter soft 0.01. `cost none` and `cost 1` under the examples adapter: offer 2, regret 0.00. The table lists every row (plain, three adapters, cost rows).

**Beat 4 - it is not just this case** (about 90 s)
```
case V9-gB-neutral-p3_7-w0-n0
adapter examples
case V3-gC-information-C4-p1_5-w0-n0
adapter examples
case V3-gB-information-C2-p1_10-w1-n0
adapter examples
table
```
Expect: no-cost backup: plain offers 3 (best 5 or 6, regret 1.20, soft 0.83), examples offers 5 (regret 0.00, soft 0.19). At-or-above backup: plain offer 3 is a best offer (regret 0.00) but soft regret 1.19; examples soft 0.00 (all mass on 3). Do not say "it always works": the honest lines are in DEMO_STATUS.md (test look: test_same and test_hard both passed the frozen rule; one training draw, one seed per control; labels equal the script-solved oracle up to a tie rule, so this is not "Claude taught it").

## `say` (free text): do not show it as evidence
Check on 30 tune cells (demo_out/gen_say_check.json, written by demo/gen_say_check.py): the free-text offer agrees with the first-token pick on only 9 / 11 / 10 of 30 cases (plain / examples / teacher), and many free-text answers are off the price list (21 / 16 / 21 of 30 on-grid). Stage rule: say is NOT safe to show; if asked, run it on plain only, call it "a different channel that the adapters were not trained on".

## Failure fallbacks
- **GPU down / CUDA error / startup check fails:** replay the beats on the CPU; the screen starts with the banner RECORDED RUN:
  `.venv/bin/python demo/floor.py --replay demo/replays/beat1.jsonl` (then beat2, beat3, beat4). Say it is a recording. No GPU or network needed.
- **Model slow (a command over 5 s, or loading over 2 min):** do not wait. If it happens at a beat boundary, switch that beat to its replay; if the model is already loaded, repeats are cached (0.00 s), so re-type the beat's earlier commands. Stop the session with `quit` and restart only between beats.
- **Wi-Fi down:** nothing here needs the network (model, adapters and cases are local). Present from the local repo; open `DEMO_STATUS.md` and the replays from disk. Do not run git push/pull on stage.
- **A command prints `failed:` or `error:`:** it is logged as a row and the session continues (never fatal). Re-type the command; if it fails twice, replay the beat.
- **Session log:** every live session writes logs/floor_<time>_9b_gen.jsonl; replay it afterwards with `--replay`.
