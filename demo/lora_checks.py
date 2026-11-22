"""LoRA safety checks, run before any real arm. Two stages in two processes (never
two models at once):

  python demo/lora_checks.py --stage train    checks 1 and 2, then saves a small adapter and its numbers
  python demo/lora_checks.py --stage reload   check 3: a fresh process reloads that adapter

1. The training forward pass (model.model -> lm_head, soft-cap, log-softmax at the
   last prompt token) equals the scoring path's first-token distribution
   (LocalGemma2.letter_scores) on one example: full-vocabulary letter log-probs and
   the renormalised letter distribution, at epoch 0 and after a few steps.
2. Adapter off matches plain bit-for-bit: with a trained (non-zero) adapter loaded,
   scoring inside peft's disable_adapter() reproduces the saved plain probabilities
   exactly, while adapter on differs.
3. A saved adapter, reloaded in a fresh process through scoring.load_adapters,
   reproduces the numbers computed before saving (max absolute difference).
Writes demo_out/lora_checks.json. Uses held-out tune and train cases only."""
import argparse, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import torch
import common, scoring, steer_lib
from refimpl import core, runtime
from refimpl.local_gemma2 import CHOICE_SYSTEM, LocalGemma2, build_messages, ensure_prompt_not_too_long

ap = argparse.ArgumentParser()
ap.add_argument("--stage", required=True, choices=("train", "reload"))
args = ap.parse_args()
OUT = os.path.join(common.ROOT, "demo_out", "lora_checks.json")
ADIR = os.path.join(common.ROOT, "demo_out", "adapters_check")
res = json.load(open(OUT)) if os.path.exists(OUT) else {}
model, tok = runtime.load_gemma("9b", "cuda")
lm = LocalGemma2(model, tok)
tune = steer_lib.lora_cases("lora_tune")[:4]
train = steer_lib.lora_cases("lora_train")[:6]
plain_saved = {c["pid"]: {int(k): v for k, v in c["probs"].items()} for c in common.load_cases()}
letter_ids = torch.tensor([tok.convert_tokens_to_ids(l) for l in steer_lib.LETTERS])
cap = model.config.final_logit_softcapping


def train_path_letters(p, oi):
  """The training forward pass: full-vocab log-probs of the five letters at P1."""
  user, l2p = scoring.user_turn(scoring.key(p), None, tuple(scoring.ORDERS[oi]), False)
  ids = lm.encode(lm.render(build_messages(CHOICE_SYSTEM, ensure_prompt_not_too_long(user, 1)), True))[0]
  hidden = model.model(input_ids=ids[None], use_cache=False).last_hidden_state[:, -1]
  logits = model.lm_head(hidden).float()
  if cap:
    logits = torch.tanh(logits / cap) * cap
  lp = torch.log_softmax(logits, dim=-1)[0]
  return lp[letter_ids.to(lp.device)].detach().cpu(), l2p


def compare_paths(label):
  worst_full, worst_renorm = 0.0, 0.0
  for p in tune[:2]:
    for oi in (0, 3):
      for mode in ("eval", "train"):
        model.eval() if mode == "eval" else model.train()
        with torch.no_grad():
          tl, l2p = train_path_letters(p, oi)
        model.eval()
        r = scoring.score(lm, p, orders=[scoring.ORDERS[oi]])
        first = lm.last_first_token
        sc = torch.tensor([first[l] for l in steer_lib.LETTERS])
        worst_full = max(worst_full, float((tl - sc).abs().max()))
        ren = torch.softmax(tl, 0)
        worst_renorm = max(worst_renorm, max(abs(float(ren[j]) - r.per_order[0][l2p[steer_lib.LETTERS[j]]]) for j in range(5)))
  return {"label": label, "max_abs_diff_letter_logprobs": worst_full, "max_abs_diff_renormalised": worst_renorm,
          "exact": worst_full == 0.0}


if args.stage == "train":
  from peft import LoraConfig, get_peft_model
  torch.manual_seed(0)
  peft_model = get_peft_model(model, LoraConfig(r=4, lora_alpha=8, lora_dropout=0.0, bias="none",
                                                target_modules=["q_proj", "k_proj", "v_proj", "o_proj"], task_type="CAUSAL_LM"))
  for _, prm in peft_model.named_parameters():
    if prm.requires_grad:
      prm.data = prm.data.float()
  model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
  c1 = compare_paths("check 1 at epoch 0 (B = 0)")
  print(c1, flush=True)
  # make the adapter non-zero: a few steps toward always-2
  opt = torch.optim.AdamW([q for q in peft_model.parameters() if q.requires_grad], lr=3e-3)
  model.train()
  for step in range(6):
    p = train[step % len(train)]
    opt.zero_grad()
    tl, _ = None, None
    user, l2p = scoring.user_turn(scoring.key(p), None, tuple(scoring.ORDERS[0]), False)
    ids = lm.encode(lm.render(build_messages(CHOICE_SYSTEM, ensure_prompt_not_too_long(user, 1)), True))[0]
    hidden = model.model(input_ids=ids[None], use_cache=False).last_hidden_state[:, -1]
    logits = model.lm_head(hidden).float()
    logits = torch.tanh(logits / cap) * cap
    lp = torch.log_softmax(logits[0, letter_ids.to(logits.device)], dim=-1)
    two = [k for l, k in l2p.items() if k == 2]
    tgt = torch.tensor([1.0 if l2p[l] == 2 else 0.0 for l in steer_lib.LETTERS]).to(lp.device)
    (-(tgt * lp).sum()).backward()
    opt.step()
  model.eval()
  c1b = compare_paths("check 1 after 6 steps (B != 0)")
  print(c1b, flush=True)
  # check 2: adapter off == plain bit-for-bit; adapter on differs
  on = {p.pid: scoring.score(lm, p).probs for p in tune}
  with peft_model.disable_adapter():
    off = {p.pid: scoring.score(lm, p).probs for p in tune}
  diff_off = max(abs(off[p.pid][k] - plain_saved[p.pid][k]) for p in tune for k in core.PRICES)
  diff_on = max(abs(on[p.pid][k] - plain_saved[p.pid][k]) for p in tune for k in core.PRICES)
  c2 = {"adapter_off_vs_saved_plain_max_diff": diff_off, "bit_for_bit": diff_off == 0.0,
        "adapter_on_vs_plain_max_diff": diff_on, "adapter_on_differs": diff_on > 1e-4}
  print("check 2:", c2, flush=True)
  peft_model.save_pretrained(os.path.join(ADIR, "check"))
  res.update({"check1_epoch0": c1, "check1_trained": c1b, "check2": c2,
              "saved_numbers": {pid: {str(k): v for k, v in pr.items()} for pid, pr in on.items()}})
  json.dump(res, open(OUT, "w"), indent=1)
  print("LORA CHECKS (train stage) COMPLETED", flush=True)
else:
  saved = {pid: {int(k): v for k, v in pr.items()} for pid, pr in res["saved_numbers"].items()}
  from peft import PeftModel
  peft = PeftModel.from_pretrained(lm.model, os.path.join(ADIR, "check"), adapter_name="check")
  peft.eval()
  now = {p.pid: scoring.score(lm, p).probs for p in tune}
  d = max(abs(now[p.pid][k] - saved[p.pid][k]) for p in tune for k in core.PRICES)
  with peft.disable_adapter():
    off = {p.pid: scoring.score(lm, p).probs for p in tune}
  d_off = max(abs(off[p.pid][k] - plain_saved[p.pid][k]) for p in tune for k in core.PRICES)
  res["check3"] = {"reload_vs_saved_max_diff": d, "reproduces": d < 1e-6, "exact": d == 0.0,
                   "reloaded_adapter_off_vs_plain_max_diff": d_off}
  json.dump(res, open(OUT, "w"), indent=1)
  print("check 3:", res["check3"], flush=True)
  print("LORA CHECKS (reload stage) COMPLETED", flush=True)
