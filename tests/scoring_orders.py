"""First-token versus whole-answer scoring across the five option orders (one prompt)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from refimpl import core, phase3
from refimpl.local_gemma2 import LocalGemma2

path = sys.argv[1]
tok = AutoTokenizer.from_pretrained(path)
model = AutoModelForCausalLM.from_pretrained(path, torch_dtype=torch.bfloat16,
                                             attn_implementation="eager").eval()
lm = LocalGemma2(model, tok)
p = core.Prompt(1, 5, "information", 3)
notes = "Question: What is Anya's best offer?\nAnswer: She can resell for 5 coins."
acc_f, acc_w = {k: 0.0 for k in core.PRICES}, {k: 0.0 for k in core.PRICES}
for i, order in enumerate(core.cyclic_orders()):
  pf, hard, _, pw = phase3.score_prompt(lm, p, "Opening sentence number 0.", notes, order)
  top_f, top_w = max(pf, key=pf.get), max(pw, key=pw.get)
  print(f"order {i} {order}: first-token top={top_f} ({pf[top_f]:.2f}, letter "
        f"{'abcde'[order.index(top_f)]}); whole-answer top={top_w} ({pw[top_w]:.2f}, letter "
        f"{'abcde'[order.index(top_w)]}); letter mass {lm.last_letter_mass:.2f}")
  for k in core.PRICES:
    acc_f[k] += pf[k] / 5; acc_w[k] += pw[k] / 5
print("order-averaged first-token:", {k: round(v, 3) for k, v in acc_f.items()},
      "soft regret", round(core.soft_regret(p, acc_f), 3))
print("order-averaged whole-answer:", {k: round(v, 3) for k, v in acc_w.items()},
      "soft regret", round(core.soft_regret(p, acc_w), 3))
