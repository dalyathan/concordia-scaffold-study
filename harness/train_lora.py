"""LoRA on worked-example labels, model-agnostic (any harness/models/*.yaml), scored only through harness.evaluate (protected scorer).

  python -m harness.train_lora --model <config> --arm claude_examples|cheapest_label|shuffled_claude --n-cells 100|25|50|10 \
      --lr 1e-4 --seed 0 [--limit K] [--plain-train-record runs/.../plain-train-....json]

Recipe = the pre-refactor generated-dataset recipe (demo/gen_lora.py, GEN_CURVE_PLAN.md), unchanged except for the code path:
  training set  demo/gen/lora_train_cells.json (100 train cells, one fixed name variant and three fixed option orders each);
                N < 100 uses the nested subsets of demo/gen/curve_subsets.json;
  labels        claude_examples: Claude's frozen worked-solution positions (demo/gen/claude_labels.json, sha256 pinned);
                cheapest_label: always grid position 0 (the cheapest price); shuffled_claude: Claude's labels permuted within
                case type (same derangement search, numpy PCG64 seed 20261127); every label set's sha256 must equal the one the
                earlier runs recorded;
  target        one-hot on the letter that shows the labelled grid position, per (case, order);
  loss          cross-entropy of the first assistant token over the five letters, using their FULL-VOCABULARY log-probs;
  adapter       LoRA rank 4, alpha 8, dropout 0, the config's lora_target_modules, fp32 adapter weights, AdamW (wd 0),
                one optimizer step per case (its three orders accumulated), gradient checkpointing;
  steps         at most 500 optimizer steps: N = 100 -> 5 epochs; N < 100 -> ceil(500 / N) epochs;
  selection     split select_B (42 train cells outside the training set, name variant 0, five orders) scored at epoch 0 and at the
                steps of SCHEDULE; patience 2 scorings; the best scoring (lowest soft regret, epoch 0 = the plain model included) is kept;
  verdict       the tune split is scored ONCE, with the best adapter, by harness.evaluate -> one run record (planted cases included).
Checks (a failed check stops the run): the training forward path equals the scoring path at zero adapter (< 1e-2 nats);
epoch-0 select_B probabilities equal the plain train record's for those cases (< 1e-3) when --plain-train-record is given;
the reloaded best adapter reproduces its select_B score (< 1e-3)."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import time

from harness import modelspec, records
from harness.evaluate import evaluate
from harness.solvers.hf import Backend, _HFSolver, file_sha
from harness.task import get_task

ROOT = records.ROOT
GEN = os.path.join(ROOT, "demo", "gen")
TRAIN_CELLS = os.path.join(GEN, "lora_train_cells.json")
CURVE = os.path.join(GEN, "curve_subsets.json")
LABELS = os.path.join(GEN, "claude_labels.json")
PINNED = {  # sha256 of the input files and of the label sets, as used and recorded by the earlier runs
    "lora_train_cells.json": "9596560f9028a04cb5f53b486fe2ef206b305e873bf044d0309bf75c5c5d67a4",
    "curve_subsets.json": "e5025b2a5e9970a4ae75968fea39f8b97c54a77e8fd65065c51d456588a9a29d",
    "claude_labels.json": "0b6f0febaa1d32302bf275bab823893db481d0386e1eccb36e52a1cbb7f95839",
    "labels:claude_examples": "a24e9238a89996ccb38cec5249492bb9b22b9e8416095d175ee9e91cec4652a6",
    "labels:cheapest_label": "b22c9f734dd9770ae7976ce93a14b3e4f39803dd58f7532ebe79ce20e01bcf26",
    "labels:shuffled_claude": "b263b077cd347249efef88b82c6c2d77953fd9c0910776ceba43b75d9b696aa6",
}
ARMS = ("claude_examples", "cheapest_label", "shuffled_claude")
TYPES = ("below", "at_or_above", "no_cost")
SCHEDULE = {10: (2, 5, 10, 20, 30, 40, 50), 25: (2, 4, 8, 12, 16, 20), 50: (1, 2, 4, 6, 8, 10), 100: (1, 2, 3, 4, 5)}
ADAPTERS = os.path.join(ROOT, "demo_out", "adapters_harness")


def _sha_file(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()


def _sha_obj(o): return hashlib.sha256(json.dumps(o, sort_keys=True).encode()).hexdigest()


def shuffled_labels(claude, cid_type):
  """Copy of demo/gen_lora.shuffled_labels (the fewest-agreement derangement within type among 20000 draws)."""
  import numpy as np
  rng = np.random.Generator(np.random.PCG64(20261127))
  out = {}
  for typ in TYPES:
    ids = sorted(cid for cid in claude if cid_type[cid] == typ)
    n = len(ids)
    own = np.array([claude[c] for c in ids])
    best = None
    for _ in range(20000):
      perm = rng.permutation(n)
      if any(perm[i] == i for i in range(n)):
        continue
      agree = int((own[perm] == own).sum())
      if best is None or agree < best[0]:
        best = (agree, perm)
    for i, cid in enumerate(ids):
      out[cid] = claude[ids[best[1][i]]]
  return out


def build_labels(arm, cases_by_id, full_ids):
  for f in ("lora_train_cells.json", "curve_subsets.json", "claude_labels.json"):
    assert _sha_file(os.path.join(GEN, f)) == PINNED[f], f"{f} changed"
  assert all(cases_by_id[c]["grid"][0] == min(cases_by_id[c]["grid"]) for c in full_ids), "position 0 must be the cheapest price"
  cl = json.load(open(LABELS))["labels"]
  assert set(cl) == set(full_ids) and len(full_ids) == 100
  claude = {k: v["position"] for k, v in cl.items()}
  if arm == "claude_examples":
    lab = claude
  elif arm == "cheapest_label":
    lab = {k: 0 for k in claude}
  else:
    lab = shuffled_labels(claude, {c: cases_by_id[c]["type"] for c in full_ids})
  assert _sha_obj(lab) == PINNED["labels:" + arm], f"{arm} labels differ from the earlier runs' labels"
  return lab, claude


class _LiveAdapter(_HFSolver):
  """Scores with the adapter currently in training (the PEFT model wraps the backend's model in place)."""
  name = "lora"
  uses_adapter = True
  def __init__(self, backend, adapter_dir, train_info, label):
    super().__init__(backend); self.dir = adapter_dir; self.info = train_info
    self.name = "lora:" + label          # one solver name per arm, N and lr (seeds share it), so check_claims' run_mean pools seeds only
  def _extra(self):
    sd = os.path.join(self.dir, "adapter_model.safetensors")
    return {"adapter_dir": os.path.relpath(self.dir, ROOT), "adapter_sha256": file_sha(self.dir) if os.path.isdir(self.dir) else None,
            "adapter_weights_sha256": _sha_file(sd) if os.path.exists(sd) else None, "trained_in_process": True, **self.info}


def main(argv=None):
  ap = argparse.ArgumentParser()
  ap.add_argument("--model", required=True); ap.add_argument("--arm", required=True, choices=ARMS)
  ap.add_argument("--n-cells", type=int, default=100, choices=sorted(SCHEDULE)); ap.add_argument("--lr", type=float, default=1e-4)
  ap.add_argument("--seed", type=int, default=0); ap.add_argument("--rank", type=int, default=4); ap.add_argument("--patience", type=int, default=2)
  ap.add_argument("--max-steps", type=int, default=500); ap.add_argument("--limit", type=int, default=0, help="smoke: this many training cases")
  ap.add_argument("--plain-train-record"); ap.add_argument("--runs", default=records.RUNS)
  ap.add_argument("--device", default="cuda", help="cpu only for the tiny-model smoke test (tests/harness/test_train_lora_smoke.py)")
  ap.add_argument("--spec-path", help="smoke test: a model config file outside harness/models")
  a = ap.parse_args(argv)
  if not a.limit and not a.plain_train_record:
    ap.error("--plain-train-record is required (the epoch-0 check is a frozen stop rule); only --limit smoke runs may omit it")
  import numpy as np
  import torch
  t_start = time.time()
  spec = modelspec.load(a.spec_path or a.model)
  task = get_task("haggling")
  _, allcases = task.build_all()
  by_id = {c["cid"]: c for c in allcases}
  tspec = json.load(open(TRAIN_CELLS))
  subset = set(json.load(open(CURVE))["subsets"][str(a.n_cells)]) if a.n_cells < 100 else set(tspec)
  assert subset <= set(tspec) and len(subset) == a.n_cells
  full_ids = [f"{k}-n{v['name_variant']}" for k, v in tspec.items()]
  labels, claude = build_labels(a.arm, by_id, full_ids)
  train = [by_id[f"{k}-n{v['name_variant']}"] for k, v in tspec.items() if k in subset]
  if a.limit:
    train = train[:a.limit]
  assert all(c["split"] == "train" for c in train)
  sel_cells = {c["cell"] for c in task.cases("select_B")}
  assert not sel_cells & set(tspec), "selection set overlaps the training cells"
  epochs = 5 if a.n_cells == 100 else math.ceil(a.max_steps / a.n_cells)
  eval_epochs = set(SCHEDULE[a.n_cells])
  assert max(eval_epochs) == epochs
  rid = f"{spec.name}_{a.arm}_n{a.n_cells}_lr{a.lr:.0e}_s{a.seed}" + ("_smoke" if a.limit else "")
  save_dir = os.path.join(ADAPTERS, rid)
  if os.path.exists(save_dir) and not a.limit:
    raise SystemExit(f"{save_dir} exists; adapters are never overwritten")
  os.makedirs(save_dir, exist_ok=True)
  sub_ids = [c["cid"] for c in train]
  label_info = {"arm": a.arm, "labels_sha256": _sha_obj(labels), "n_cells": a.n_cells, "lr": a.lr, "seed": a.seed, "rank": a.rank,
                "label_share_cheapest_subset": float(np.mean([labels[c] == 0 for c in sub_ids])),
                "label_agreement_with_claude_subset": float(np.mean([labels[c] == claude[c] for c in sub_ids]))}

  b = Backend(spec, device=a.device)
  model, tok = b.model, b.tok
  letter_ix = torch.tensor(list(spec.answer_letter_token_ids))
  orders = list(task.orders(train[0]))
  examples = []
  for c in train:
    for oi in tspec[c["cell"]]["orders"]:
      text, l2o = task.render(c, orders[oi])
      prompt = b.render_prompt(text)
      ids = tok(prompt, return_tensors="pt", add_special_tokens=False).input_ids[0]
      tgt = [0.0] * 5
      tgt[spec.answer_letters.index(next(l for l, o in l2o.items() if o == labels[c["cid"]]))] = 1.0
      examples.append({"cid": c["cid"], "ids": ids, "target": torch.tensor(tgt), "text": text})
  by_case = {}
  for ex in examples:
    by_case.setdefault(ex["cid"], []).append(ex)

  from peft import LoraConfig, get_peft_model
  torch.manual_seed(a.seed)
  cfg = LoraConfig(r=a.rank, lora_alpha=2 * a.rank, lora_dropout=0.0, bias="none", target_modules=list(spec.lora_target_modules), task_type="CAUSAL_LM")
  peft_model = get_peft_model(model, cfg)
  for _, prm in peft_model.named_parameters():
    if prm.requires_grad:
      prm.data = prm.data.float()
  params = [p for p in peft_model.parameters() if p.requires_grad]
  n_train = sum(p.numel() for p in params)
  b.peft = peft_model
  model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
  cap = getattr(model.config, "final_logit_softcapping", None)
  opt = torch.optim.AdamW(params, lr=a.lr, weight_decay=0.0)

  def letter_lp(ids):
    hidden = model.model(input_ids=ids[None].to(model.device), use_cache=False).last_hidden_state[:, -1]
    logits = model.lm_head(hidden).float()
    if cap:
      logits = torch.tanh(logits / cap) * cap
    return torch.log_softmax(logits, dim=-1)[0, letter_ix.to(logits.device)]

  # training path == scoring path at the zero adapter
  model.eval()
  worst = 0.0
  with torch.no_grad():
    for ex in [by_case[c][0] for c in list(by_case)[:3]]:        # first order of three different cases
      lp = letter_lp(ex["ids"]).cpu().numpy()
      ref, _ = b.next_letter_logprobs(ex["text"])
      worst = max(worst, float(np.max(np.abs(lp - np.array([ref[l] for l in spec.answer_letters])))))
  assert worst < 1e-2, f"training forward path differs from the scoring path by {worst} nats"
  print(f"{rid}: {len(train)} cases, {len(examples)} examples, {n_train} trainable parameters; path check {worst:.1e} nats", flush=True)

  info = {"training": label_info}
  live = _LiveAdapter(b, save_dir, info, f"{a.arm}_n{a.n_cells}_lr{a.lr:.0e}")

  def score_select():
    model.eval()
    r = evaluate(task, live, "select_B", a.seed, spec, write=False, planted=False)
    model.train()
    probs = {x["cid"]: x["probs"] for x in r["cases"]}
    return r["summary"], r["letter_mass"]["mean"], probs

  history = []
  s0, m0, p0 = score_select()
  if a.plain_train_record:
    pr = {x["cid"]: x["probs"] for x in json.load(open(a.plain_train_record))["cases"]}
    dev = max(abs(u - v) for cid, p in p0.items() for u, v in zip(p, pr[cid]))
    assert dev < 1e-3, f"epoch-0 select_B scoring differs from the plain train record by {dev}"
    info["training"]["epoch0_vs_plain_train_record_max_abs_prob"] = dev
  history.append({"epoch": 0, "step": 0, "train_loss": None, "select_B": s0, "letter_mass": m0})
  print(f"epoch 0 (plain): select_B soft regret {s0['soft_regret_mean']:.4f}, mass {m0:.3f}", flush=True)
  best = {"epoch": 0, "soft": s0["soft_regret_mean"], "probs": p0}
  peft_model.save_pretrained(save_dir)
  bad = 0
  rng = np.random.Generator(np.random.PCG64(a.seed))
  cids = [c["cid"] for c in train]
  control = True   # every arm trains to the last epoch and is also scored unselected (G1); selection stops at the frozen rule
  stopped_at = None
  t_train = 0.0
  model.train()
  for epoch in range(1, epochs + 1):
    t0 = time.time(); losses = []
    for i in rng.permutation(len(cids)):
      opt.zero_grad(set_to_none=True)
      exs = by_case[cids[i]]
      for ex in exs:
        loss = -(ex["target"].to(model.device) * letter_lp(ex["ids"])).sum() / len(exs)
        loss.backward(); losses.append(float(loss) * len(exs))
      opt.step()
    t_train += time.time() - t0
    if epoch not in eval_epochs:
      continue
    s, m, p = score_select()
    history.append({"epoch": epoch, "step": epoch * len(cids), "train_loss": float(np.mean(losses)), "select_B": s, "letter_mass": m,
                    "sec_training_epoch": time.time() - t0})
    print(f"epoch {epoch} (step {epoch * len(cids)}): loss {np.mean(losses):.4f}; select_B soft {s['soft_regret_mean']:.4f} (mass {m:.3f}); "
          f"{time.time() - t0:.0f}s", flush=True)
    if stopped_at is not None:
      continue                                    # control arms only: training goes on to the last epoch; selection is closed
    if s["soft_regret_mean"] < best["soft"] - 1e-9:
      best = {"epoch": epoch, "soft": s["soft_regret_mean"], "probs": p}
      peft_model.save_pretrained(save_dir); bad = 0
    else:
      bad += 1
      if bad >= a.patience:
        stopped_at = epoch
        print(f"early stop after epoch {epoch} (best epoch {best['epoch']})", flush=True)
        if not control:
          break
  if control:
    # G1 (2026-11-27): a control whose selection keeps epoch 0 would just be the plain model, so every control is also scored as its
    # last-epoch adapter with no selection (LLAMA_PLAN.md: R3/R4 use this version when best_is_epoch_zero is true)
    peft_model.save_pretrained(save_dir + "_last")
    last_epoch = epoch
  from safetensors.torch import load_file
  from peft.utils import set_peft_model_state_dict
  last_rec = None
  if control:
    info_last = {"training": {**label_info, "version": "last epoch, no selection", "last_epoch": last_epoch, "early_stop_epoch": stopped_at,
                              "history": history, "train_cases": cids, "trainable_parameters": n_train}}
    live_last = _LiveAdapter(b, save_dir + "_last", info_last, f"{a.arm}_n{a.n_cells}_lr{a.lr:.0e}_last")
    model.eval()
    last_rec = evaluate(task, live_last, "tune", a.seed, spec, config={"run": rid + "_last", "training": info_last["training"]}, directory=a.runs,
                        write=not a.limit)
    print("last-epoch record:", last_rec.get("_written_to"), f"tune {last_rec['summary']['soft_regret_mean']:.4f}", flush=True)
  rr = set_peft_model_state_dict(peft_model, load_file(os.path.join(save_dir, "adapter_model.safetensors")))
  assert not getattr(rr, "unexpected_keys", None), "best-adapter reload: unexpected keys"
  s_re, _, p_re = score_select()
  assert abs(s_re["soft_regret_mean"] - best["soft"]) < 1e-3, f"reloaded best adapter scores {s_re['soft_regret_mean']}, expected {best['soft']}"
  info["training"].update({"best_epoch": best["epoch"], "best_step": best["epoch"] * len(cids), "best_is_epoch_zero": best["epoch"] == 0,
                           "select_B_best_soft_regret": best["soft"], "select_B_reload_soft_regret": s_re["soft_regret_mean"],
                           "epochs_max": epochs, "early_stop_epoch": stopped_at, "control_arm": control,
                           "version": "selected on select_B (early stopping, epoch 0 a candidate)", "eval_epochs": sorted(eval_epochs), "patience": a.patience, "optimizer_steps_per_epoch": len(cids),
                           "trainable_parameters": n_train, "path_check_max_nats": worst, "history": history, "sec_training_total": t_train,
                           "train_cases": cids, "recipe": "demo/gen_lora.py recipe; see harness/train_lora.py docstring"})
  model.eval()
  gpu_s = time.time() - t_start
  t1 = time.time()
  rec = evaluate(task, live, "tune", a.seed, spec, config={"run": rid, "training": info["training"]}, write=not a.limit,
                 directory=a.runs, gpu_seconds=None)
  if not a.limit:
    # gpu time of the whole run (load + targets + training + selection + tune scoring) is recorded in the config and the summary file
    rec_path = rec["_written_to"]
    d = json.load(open(rec_path))
    total = gpu_s + (time.time() - t1)
    d["timing"] = {"wall_seconds": total, **records.cost(total), "tune_scoring_seconds": time.time() - t1}
    with open(rec_path, "w") as f:
      json.dump(d, f, indent=1, sort_keys=True)
    print("record:", rec_path)
  print(f"TRAIN_LORA {rid} DONE: best epoch {best['epoch']}, select_B {best['soft']:.4f}, tune {rec['summary']['soft_regret_mean']:.4f}, "
        f"planted {rec['planted']['n_ok']}/{rec['planted']['n']}, mass {rec['letter_mass']['mean']:.3f}, {time.time() - t_start:.0f}s", flush=True)


if __name__ == "__main__":
  main()
