# G1 blind review (Opus), Llama 3.1 8B replication plan, 2026-11-27

**Verdict: go-with-changes.** Rules compare Llama arms with Llama controls; tune only for the verdict; selection and lr on select_B; no test split reachable. Checked and correct: target letter mapping matches gen_lora.py; case-mean equals cell-mean; planted expectations follow from the payoffs; steps/schedules/epochs match; shuffle copy sha-pinned; Gemma numbers match.

1. (Blocking, flagged unverified) Revision pin not applied: packet hf.py passes `hub_commit=` to from_pretrained, which transformers does not know; self.hub_commit records the requested hash, not the loaded one. Fix: pass revision=, assert model.config._commit_hash (and tokenizer's) equals the pin, record the actual hash.
2. Readout floor too loose: show the first assistant token is on ids 64..68 rather than "(", "A", " a"; floor 0.5 vs L1d 0.90; training raises mass, so adapter gains may partly be readout. Fix: log top-10 first tokens and mass on capital/space variants on plain tune; pre-register a caution/re-gate band 0.5-0.9; report mass per arm.
3. Early stopping can turn a control into plain. Fix: report best_is_epoch_zero for every control; if true, also score it at a fixed epoch (the examples run's best or the last); state which version R3/R4 use.
4. Cheapest-label at N = 25 compared with examples at N = 100 in R3. Fix: add cheapest_label N = 100 for R3, keep N = 25 for L4f.
5. Parity skip affects every Gemma-vs-Llama statement; partial fix: harness plain on Gemma tune on the A40 vs the A40 rescore (0.661). If kept skipped, label cross-model statements; keep within-Llama verdicts.
6. Lesson identity only enforced outside the packet: gen_lora used .strip(); NotesSolver uses raw read() plus "\n\n". Fix: assert lesson sha in NotesSolver (teacher = f41ae9...), strip or assert no trailing whitespace.
7. Bootstrap over about 20 or fewer (V, grid) clusters undercovers; R3 treats the 3-seed mean as fixed. Fix: report the cluster count; count seeds below plain; do not upgrade UNCLEAR in prose.
8. Minor: notes arms on train feed no rule (drop or say why); train_lora rewrites `timing` in a written record (use a side file); R2 two paragraphs without a multiplicity note; report Claude-label agreement with the oracle per type.

Freeze before a test look: adapters (lr, seeds, weight sha256), lesson shas, the loaded model commit and chat_template_kwargs, harness commit and owner pin tag, parity status and wording, the report script and its sha, bootstrap set-up, primary metric, R1-R5 unchanged, the list of test splits, control handling. Tighten _prior_look: it keys on describe() incl. adapter_dir, so a copied adapter directory allows a second look at the same weights; key on (model, split, adapter-weights sha / lesson sha).

Could not verify: lesson bytes and tests; g.orders() == haggling.orders(); Gemma's headline lr 1e-4; uniform baseline; anything needing the model.
