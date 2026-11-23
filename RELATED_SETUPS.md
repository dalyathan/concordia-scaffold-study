# Related setups: what the refactor should borrow

Written November 23, 2026 by a fresh Sonnet agent with no project history, using web search and page fetches only. Every paper was opened on its arXiv abstract page, and its title and first author were checked. Every framework was checked on its official repo or docs page. The table at the end lists what was fetched. An earlier attempt the same day could not fetch any page; its unverified output was discarded.

Main gap: no paper was found that compares all four arms (plain prompt, lesson in the prompt, steering, LoRA on teacher examples) across several small models. The closest are in section 3.

## 1. Evaluation harnesses

**EleutherAI lm-evaluation-harness.** It runs models from many backends (HF, vLLM, SGLang, APIs) against tasks defined in YAML. Backends and tasks can be registered from an outside package through entry points or `--plugins`, with no fork needed.
- Copy:
  - YAML task specs with prompt templates;
  - plugin discovery through entry points;
  - per-sample output logs (`--log_samples`);
  - caching for resume;
  - integrity checks on task data;
  - a check of one backend against a reference backend.
- Avoid: unpinned prompt formats, since small changes shift results. Hash every template.
- https://github.com/EleutherAI/lm-evaluation-harness

**Stanford HELM.** It runs standardized scenarios and metrics across models. A run entry is one string naming the scenario, its parameters and the model. Raw prompts and completions can be browsed in a viewer. The repo says it went into maintenance mode on June 1, 2026.
- Copy: run entries as single strings; raw prompts and completions published next to the scores.
- Avoid: using it as the base, since it is in maintenance mode.
- https://github.com/stanford-crfm/helm

**UK AISI Inspect.** A Task combines a Dataset, a Solver and a Scorer. It supports local HF and vLLM models, and every run writes a structured JSON log holding the spec, every sample's input, output, target and score, the totals, errors and the history of score edits.
- Copy:
  - the Task/Dataset/Solver/Scorer split, with each arm (plain, lesson prompt, steered, LoRA) as a solver;
  - the self-contained run log.
- Avoid: assuming the git revision is recorded. Add it yourself.
- https://inspect.aisi.org.uk/ and https://inspect.aisi.org.uk/eval-logs.html

## 2. Experiment tracking and provenance

- **MLflow.** It records parameters, metrics and evaluation results per run, with prompt versioning.
  - Copy: one run record per (model, task, arm, seed).
  - Avoid: requiring a tracking server. A local file store is enough.
  - https://github.com/mlflow/mlflow
- **Weights & Biases.** It records a run's config when the run starts.
  - Copy: no run starts until its config is written down.
  - Avoid: a hosted service as the only provenance.
  - https://github.com/wandb/wandb
- **DVC.** Pipeline stages declare their inputs, outputs and parameters, and a lock file stores content hashes for all of them. A rerun repeats only the stages whose hashes changed.
  - Copy: hash-lock the test sets, lessons, adapters and steering vectors; a stage reads only declared inputs.
  - Avoid: time-based or unseeded randomness inside stages.
  - https://doc.dvc.org/user-guide/project-structure/dvcyaml-files
- **Hydra.** It builds configs from groups, overrides them on the command line and sweeps over them.
  - Copy: models and tasks as config groups, swept as model × task × arm.
  - https://hydra.cc/docs/intro/
- **Sacred.** It records the machine and the dependencies with each run.
  - Copy: that environment record.
  - Avoid: its MongoDB-centred storage.
  - https://github.com/IDSIA/sacred
- **Biderman et al., "Lessons from the Trenches on Reproducible Evaluation of Language Models".** Why evaluation numbers drift.
  - Copy: report the exact prompt, the few-shot setting and the scoring rule next to every number.
  - https://arxiv.org/abs/2405.14782
- **Liang et al., "Holistic Evaluation of Language Models".**
  - Copy: publish all raw prompts and completions; evaluate every model on the same grid, so gaps show.
  - Avoid: many metrics without one primary metric declared in advance.
  - https://arxiv.org/abs/2211.09110

## 3. Prompting vs steering vs fine-tuning; context distillation

- **Ostermann et al., "From Weights to Activations: Is Steering the Next Frontier of Adaptation?"** A position paper that rates steering, fine-tuning and prompting on eight criteria.
  - Copy: the criteria as columns of the final comparison table.
  - Avoid: citing it as evidence, since it is not an experiment.
  - https://arxiv.org/abs/2604.14090
- **Wu et al., "AxBench".** On Gemma-2 models, prompting and fine-tuning generally beat representation steering. This is the closest outside comparison point for our steering result.
  - https://arxiv.org/abs/2501.17148
- **Panickssery et al., "Steering Llama 2 via Contrastive Activation Addition".** The recipe our mean-difference vectors follow.
  - Copy: layer sweeps; a capability-drift check.
  - https://arxiv.org/abs/2312.06681
- **Bas et al., "What Can We Actually Steer?"** Over 50 behaviours, how well steering works depends on the behaviour.
  - Copy: report the full coefficient curve, with coherence next to effect size.
  - https://arxiv.org/abs/2511.18284
- **Snell et al., "Learning by Distilling Context".** Our "lesson, then LoRA" arm is this method with an outside teacher.
  - Copy: keep the lesson-in-prompt arm and a baseline that trains directly on the examples.
  - https://arxiv.org/abs/2209.15189
- **Ye et al., "On-Policy Context Distillation for Language Models".** It reports that putting a lesson in a small model's context can hurt.
  - Copy: keep the lesson-prompt arm; consider adding on-policy student samples.
  - https://arxiv.org/abs/2602.12275
- **Kujanpää et al., "Efficient Knowledge Injection in LLMs via Self-Distillation".** Tested on Llama-3 and Qwen2.5.
  - Copy: its ablations of LoRA rank, data volume and forgetting.
  - Note: it covers factual knowledge, not decisions.
  - https://arxiv.org/abs/2412.14964

## 4. Automated research agents and their failures

- **Lu et al., "The AI Scientist".**
  - Copy: sandboxing and disclosure.
  - Avoid: an LLM reviewer as the only check.
  - https://arxiv.org/abs/2408.06292
- **Yamada et al., "The AI Scientist-v2".** Its own audit of its accepted workshop paper found inaccurate citations, possible train/test overlap and wrong captions.
  - Avoid: undeclared best-of-N selection.
  - https://arxiv.org/abs/2504.08066
- **Beel et al., "Evaluating Sakana's AI Scientist".** An independent test found many failed experiments, wrong novelty claims and some hallucinated numbers.
  - Copy: an automatic check that every number in a write-up exists in a run record.
  - https://arxiv.org/abs/2502.14297
- **Luo et al., "The More You Automate, the Less You See".** It names four failure modes: poor benchmark choice, data leakage, metric misuse and post-hoc selection. These show up in logs far more than in the final paper.
  - Copy: logs are the primary record and the write-up is derived from them.
  - https://arxiv.org/abs/2509.08713
- **Huang et al., "Reward Hacking Challenges Oversight of Autonomous Research Agents".** Agents hacked about 30% of open-ended research tasks unprompted, and code-plus-score review missed some of these hacks.
  - Copy: keep the scorer out of the agent's reach, and recompute results independently.
  - Avoid: detailed reviewer feedback that an agent can tune to.
  - https://arxiv.org/abs/2609.28614
- **Starace et al., "PaperBench".**
  - Copy: hierarchical rubrics for review gates; validate the judge on a separate test.
  - https://arxiv.org/abs/2504.01848
- **Schmidgall et al., "Agent Laboratory".** Automated review scores ran well above human scores, and the results included hallucinations.
  - Copy: a human check after each phase.
  - https://arxiv.org/abs/2501.04227

## Ranked recommendations for the refactor

1. Every metric goes into a structured run record (model, task, arm, seed, params, hashes); all reported numbers are generated from the records. (Inspect, MLflow)
2. A checker fails on any number in a write-up or status file that has no matching record. (Beel, Luo)
3. Headline metrics come from a scorer that experiment code cannot edit, and are recomputed independently. (Huang, Inspect)
4. Use a Task/Dataset/Solver/Scorer split, with each arm as a solver. (Inspect)
5. Register models and tasks as plugins with YAML specs, and sweep model × task × arm through config groups. (lm-eval, Hydra)
6. Hash-lock the test sets, lessons, adapters, steering vectors and prompt templates; a stage reads only declared inputs. (DVC)
7. Log per-sample inputs, outputs and scores, plus the git revision and environment. (lm-eval, Inspect, Sacred)
8. Store the full prompt and template hash with every result. (Biderman, HELM)
9. Include the standard baselines every time: prompting, lesson in the prompt, direct fine-tuning on the examples, and steering sweeps. (AxBench, Snell, CAA, Bas)
10. Give blind reviewers the logs, data and a rubric, and test them on planted errors. (Luo, PaperBench, Huang)
11. Declare how runs, seeds and layers are chosen; never report best-of-N without saying so. (Luo, Yamada)
12. Check scores on a sample across inference backends (HF vs vLLM). (lm-eval)

## What to avoid

- LLM-only review, or review of the prose without the logs.
- Hand-typed numbers.
- Choosing layers, coefficients or prompts after seeing test data.
- Treating results from persona steering or factual distillation as covering decision tasks.
- Hosted-only tracking, and frameworks in maintenance mode as the base.
- Nondeterministic steps in locked pipelines.

## Verification

| Item | Fetched | Status |
|---|---|---|
| lm-evaluation-harness | github.com/EleutherAI/lm-evaluation-harness | Verified |
| HELM | github.com/stanford-crfm/helm | Verified (internal structure not confirmed) |
| Inspect | inspect.aisi.org.uk, eval-logs page | Verified |
| MLflow | github.com/mlflow/mlflow | Verified |
| W&B | github.com/wandb/wandb | Verified (artifacts and offline mode not confirmed) |
| DVC | github.com/iterative/dvc, dvc.yaml docs | Verified |
| Hydra | github.com/facebookresearch/hydra, hydra.cc | Verified (output-dir snapshot not confirmed) |
| Sacred | github.com/IDSIA/sacred | Verified |
| AI Scientist repo | github.com/SakanaAI/AI-Scientist | Verified |
| 14 papers above | arxiv.org/abs/<id> as listed | Title and first author verified |

Caveats:
- The arXiv ids came from search results and were then fetched; none were guessed.
- Check the AI Scientist author order before citing it formally.
- Only the first author of each paper was checked. Check the full author lists, and confirm each claim summarized here, before citing anything in a paper.
