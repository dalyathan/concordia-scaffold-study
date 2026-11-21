## R3. Test results

All results below come from one NVIDIA A10G (24 GB; driver 595.112.07) on an AWS g5.xlarge (4 vCPUs, 16 GB RAM). The stack is the pinned GPU stack: Python 3.11.18, torch 2.4.1 with CUDA 12.1 and cuDNN 9.1.0.70, transformers 4.44.2 (`requirements.gpu.lock`). Models were loaded from their pinned revisions, and every weight shard's SHA-256 matched the Hub's LFS hash first:

- gemma-2-9b-it: 4 shards;
- gemma-2-2b-it: 2 shards;
- all-mpnet-base-v2: `model.safetensors`.

Every model process ran with no network and without `HF_TOKEN`. No offer, regret, S text or calls log of any agent was printed or saved. The agent checks use pilot prompts only.

### Unit tests (P0.10): 30 passed

`tests/test_core.py` covers:

- prompt and cell counts, including the 49-cell extension and its 24/25 split;
- the hand-computed best-offer table, including C = V and C > V;
- non-negative regret;
- the disjoint 17/18 split;
- seeds, and per-call seeding applied only inside a call context (the global generators are untouched without one);
- S entries, with the prompt's answer stem;
- softmax and cyclic orders;
- Holm and IUT;
- the direction of the sign-flip and Wilcoxon tests.

`tests/test_design.py` covers:

- **Advice removal.** These go: per-option profit lines, "3 coins: 2" lists, option labels, multi-price sentences, "offer 2", "a price of 3 seems fair" and "$2". These stay: single-price facts, "the average price is 3 coins" and "2 kg".
- **Conditions.** Exact-length Q/A filler; the 28-condition set, including a dropped paraphrase; the audit prompt.
- **N7 donors.**
  - 34 of 35 cells (48 of 49 with V = 7, 8) have a disjoint donor; the exception is cell (5, 5), whose donor is (5, 4).
  - Donors keep the variant and line; no-information prompts get only no-information donors.
  - Each donor is the nearest disjoint cell under the tie rule, checked by brute force.
  - The choice is deterministic.
- **Tuner.** It returns "no steering" when every setting hurts or none is coherent.
- **Sign-flip test.** Exact for 18 cells, Monte Carlo for 36.
- **Families and verdicts.** BH, the reverse rule, all four verdicts through the two Holm families, and the monotonicity of the power simulation.
- **A/B/R assembly**, including orientation.
- **K1.** It is one p-value and fails when the sharpening null does better.
- **K2.** It uses only the 12 unique-best cells; pulling to a fixed price, flattening and sharpening do not pass, and steering to each prompt's best offer does.
- **K1/K2 assembly and the fidelity measure.**

`tests/test_banks.py` covers memory banks:

- Save and reload reproduce columns, dtypes, every row (tags as tuples, embeddings bit-exact), the de-duplication hashes and the player config.
- Re-adding a duplicate row is ignored, while a row differing only in importance is added.
- The duplicate check also holds in a fresh process with a different `PYTHONHASHSEED`.

### Model configuration (P0.1): matches

`config.json` at the pinned 9B revision: 42 layers, hidden size 3,584, 16 query and 8 key-value heads, head dimension 256, sliding window 4,096, soft-caps 50 and 30, vocabulary 256,000.

**Loading.** 9B loads with `low_cpu_mem_usage=True` and `device_map={"": 0}`. Peak resident memory was 5.6 GB, and loading took about 2.3 minutes, limited by disk reads. The weights occupy 17.21 GiB on the GPU.

### `smoke_gemma.py` on 9B (Phase 3 path; P0.2, P0.7 and P0.9 logic): passed

The prompt is a smoke prompt with a made-up one-line note and placeholder openings, not any agent's text.

```
layers 42 hidden 3584 softcaps 50.0 30.0
render ok
score+capture 2.1s  [probabilities omitted here]
P2 '\nAnswer: ('
P3 ' so price accordingly."'
P4 ' 5 coins back'
prompt tokens 590; batched 1.19s, sequential 1.35s
batched vs sequential whole-answer |delta| (nats): {'a': '3.21e-01', 'b': '6.33e-02', 'c': '8.60e-02', 'd': '6.44e-02', 'e': '2.14e-01'}
batched vs sequential first-token |delta| (nats): {'a': '5.32e-02', 'b': '2.36e-02', 'c': '1.40e-01', 'd': '3.25e-02', 'e': '2.36e-02'}
P0.2 max |delta| = 3.210e-01 nats; criterion 1e-3: EXCEEDED; bit-identical: False
argmax identical (whole-answer, first-token): True True
batched vs sequential ok (same argmax)
repeat bit-identical ok
zero-steer identity ok
sample_text: 'blue. '
ALL SMOKE CHECKS PASSED
```

What this shows:

- The prompt is rendered with the system text folded into the first user turn.
- Activations are captured at all 42 layers at P1–P4, and P2–P4 decode to the intended text.
- Scoring the same prompt twice is bit-identical (P0.7 logic).
- A zero steering vector leaves both scorings bit-identical (P0.9), and a large vector moves the distribution.
- Greedy sampling is repeatable and stops at terminators.
- **Batched and sequential scoring are not bit-identical on this GPU:** up to 0.32 nats (whole-answer) and 0.14 nats (first-token), though with the same argmax. On a CPU the same comparison had been identical to the last bit.

  A diagnostic on 2B compared the final hidden state at P1 between batch sizes 5 and 1. It differs by up to 0.81, on a scale of 96. Unembedding in float32 leaves 0.18 nats, so the difference is not just bf16 logit rounding: GPU kernels chosen for different batch shapes accumulate floating-point error differently, and the error compounds over the layers.

  This is why the scoring mode is fixed (sequential) for every run, and why P0.2 is reported rather than used as a gate.

### `scoring_orders.py` on 9B

Same smoke prompt (V = 5, stated cost 3, a one-line note), five cyclic orders:

```
mean letter mass 0.570 (range 0.457-0.816); first-token vs whole-answer top choice agree in 3 of 5 orders
```

Whole-answer and first-token scoring disagree on the top choice in 2 of 5 orders, and the letter mass is well below 1. These are the reasons the protocol makes first-token scoring primary in Phase 3, reports whole-answer scoring for every test, and reports letter mass per condition.

### Phase 3 memory and time per pass on 9B (P0.11 logic)

Pilot prompt v13-V5-neutral with format-matched filler Notes. Sequential scoring with activation capture at all 42 layers; steering at layer 18 with the prompt's own P1 activation. Peak is `torch.cuda.max_memory_allocated()`. The card offers 22.06 GiB.

| Notes | Tokens per sequence | Peak GPU (unsteered / steered) | Time per pass (unsteered / steered) | Repeats bit-identical |
| --- | --- | --- | --- | --- |
| 200 tokens | 797 | 17.39 / 17.39 GiB | 0.383 / 0.384 s | yes |
| 3,000 tokens (the cap) | 3,597 | 19.40 / 19.40 GiB | 2.323 / 2.323 s | yes |
| 3,900 tokens | 4,497 | 20.56 / 20.56 GiB | 3.194 / 3.194 s | yes |

Every Phase 3 and 3b scoring fits a 24 GB GPU with sequential scoring.

### One Phase 2 decision per agent on 9B (P0.6 logic)

Pilot prompt v13-V5-information-C3, real all-mpnet-base-v2 embeddings. Memory: a temporary blank bank plus the player-specific memory. Each agent ran twice.

| Agent | Exception | Model calls (text + choice) | S non-empty | Rule memories reached prompts | Longest prompt (tokens) | Wall time | S byte-identical across runs |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `rational_agent` | none | 6 (5 + 1) | yes | 3 of 3 | 1,419 | 56 s, 54 s | yes |
| `basic_agent` | none | 12 (10 + 2) | yes | 3 of 3 | 1,836 | 86 s, 86 s | yes |
| `taehun_cgcal` | none | 7 (5 + 2) | yes | 3 of 3 | 701 | 10 s, 10 s | yes |
| `fluffy_fluffyagent_v16submission` | none | 5 (4 + 1) | yes | 3 of 3 | 3,331 | 169 s, 168 s | yes |
| `hgyun_loss_aversion_agent_v3_plus2` | CUDA out of memory | — | — | — | ≥ 2,424 | 122 s to failure | — |

`hgyun` fails in `generate` on a 2,424-token prompt, allocating 2.31 GiB (= 2,424 × 256,000 × 4 bytes). transformers 4.44.2's `Gemma2ForCausalLM.forward` unembeds every prompt position in prefill and copies the logits to float32. On top of 17.2 GiB of weights, that overflows 24 GB from about 2,400 prompt tokens. Phase 3 scoring is unaffected, because it unembeds only the answer positions. Phases 1–2 need the 48 GB GPU of Protocol section 3, or a registered change to prefill unembedding.

### `smoke_phase2.py` on 2B: passed

```
decision in 20s
model calls during episode: 6
rule memories seen in act() prompts: {0: True, 1: True, 2: True}
S non-empty: True  sha256(S): c444e197fab8730a
PHASE 2 SMOKE TEST PASSED (deterministic rerun identical)
```

### Formative-memory banks

The 14 banks (variants 1–14) were generated on 9B, greedy, under the determinism patches, in about 2.4 minutes each.

- Every bank has 13 rows, from 2 model calls.
- In each, the saved file reloads to a memory equal to the live one: rows, dtypes, de-duplication hashes and player config.
- Their SHA-256 values are in the registration record.
- Concordia printed one warning, for variant 4: 8 episodes were generated for 7 formative ages. Concordia pairs episodes with ages using `zip`, so the extra episode is dropped, as it would be upstream.

### Bugs the tests found and fixed

- **Out of memory in scoring.** Full-vocabulary logits for five sequences exhausted memory. The scorer now unembeds only the answer positions.
- **Deep copy fails.** `copy.deepcopy` of an `AssociativeMemory` fails on its thread lock. Its rows are now copied into a fresh memory.
- **Missing answer stem.** S dropped the answer stem each completion continues, so an entry read "Answer: is trying to buy…". The stem is now kept and unit-tested.
- **Unset attention mask.** `generate` warned about it; it is now passed explicitly.
- **Run-history dependence.** transformers 4.44.2 reuses Gemma 2's generation cache across calls when it is large enough. Attention shapes, and therefore rounding, then depend on earlier calls; this flipped a greedy token between two otherwise identical runs. `sample_text` now deletes the cache before each call. Memory sampling in `AssociativeMemory.add` uses numpy's global state, so each decision also starts by seeding the global generators.
- **Memory held after an out-of-memory error.** A failed `generate` left its cache and frames on the GPU, so the next decision failed at once. The agent check now releases the cache and collects garbage after an exception.

### Open issues

- **Phase 2 generation on 24 GB** (above): unresolved; needs the 48 GB GPU or a registered prefill change.
- **The pipeline driver end to end** has not run, because no pilot or confirmatory phase may run before registration. Its statistics are unit-tested (`abr_tests`, `k_tests`, `confirmatory_verdicts`, `power_simulation`). Its model-calling functions are loops over the tested `phase2.run_decision`, `phase3.score_prompt` and `LocalGemma2.letter_scores`.
