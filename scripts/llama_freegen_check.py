"""G1 check of the assistant-prefix readout: does the letter forced after "Answer: (" match what plain Llama picks when it answers freely?

  HF_HUB_OFFLINE=1 PYTHONPATH=concordia:. .venv/bin/python scripts/llama_freegen_check.py
Same 20 train cases outside the LoRA training cells and select_B as the probe (scripts/llama_readout_probe.py --split train_other), 5 orders.
Per prompt: greedy generation (64 new tokens) WITHOUT the prefix; the option it names is parsed (the first "(x)" / "x)" letter of a shown
option, else the first shown price "N coin(s)"); compared with the argmax letter of the prefixed first-token readout.
Frozen threshold (LLAMA_PLAN.md): agreement on parsed prompts >= 0.7 and parse rate >= 0.5 -> proceed; otherwise stop before step 4.
No regret is computed. Writes demo_out/llama/freegen_check.json.
--adapter DIR (added at G2, descriptive only, no threshold): the same check with a trained LoRA adapter loaded on top of the model;
writes demo_out/llama/freegen_check_<adapter name>.json.
G1 (Qwen, 2026-11-28): generation is explicitly plain greedy (repetition_penalty=1.0; a model's generation_config may set another, Qwen 2.5
ships 1.05; Llama 3.1's default is 1.0, so the Llama numbers are unaffected) and the effective settings are written to the JSON; agreement is
also reported on letter-parsed answers only. For any model other than llama31_8b the check is descriptive: no thresholds, no pass field,
exit 0 (QWEN_PLAN.md)."""
import json, os, re, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from harness import modelspec
from harness.solvers.hf import Backend
from harness.task import get_task

THRESH_AGREE, THRESH_PARSE = 0.7, 0.5     # the frozen Llama rule (llama31_8b only)
GEN = {"repetition_penalty": 1.0}           # plain greedy whatever the model's generation_config says


def parse(text, l2price):
  m = re.search(r"\(([a-e])\)|(?<![A-Za-z])([a-e])\)", text)
  if m:
    return (m.group(1) or m.group(2)), "letter"
  for pm in re.finditer(r"(\d+)\s*coins?", text):
    k = int(pm.group(1)); hits = [l for l, p in l2price.items() if p == k]
    if hits:
      return hits[0], "price"
  return None, None


def main():
  import argparse, torch
  ap = argparse.ArgumentParser(); ap.add_argument("--adapter"); ap.add_argument("--model", default="llama31_8b"); a = ap.parse_args()
  t0 = time.time()
  spec = modelspec.load(a.model); b = Backend(spec); task = get_task("haggling"); tok = b.tok
  if a.adapter:
    from peft import PeftModel
    b.model = PeftModel.from_pretrained(b.model, a.adapter); b.model.eval()
  used = set(json.load(open(os.path.join(ROOT, "demo", "gen", "lora_train_cells.json")))) | {c["cell"] for c in task.cases("select_B")}
  pool = [c for c in task.cases("train") if c["cell"] not in used]
  cases = pool[:: max(1, len(pool) // 20)][:20]
  rows = []
  for c in cases:
    for order in task.orders(c):
      text, l2o = task.render(c, order)
      l2price = {l: c["grid"][o] for l, o in l2o.items()}
      lp, _ = b.next_letter_logprobs(text)                      # prefixed readout (the config's prefix)
      forced = max(lp, key=lp.get)
      prompt = b.render_prompt(text, prefix="")
      x = tok(prompt, return_tensors="pt", add_special_tokens=False).input_ids.to(b.model.device)
      with torch.no_grad():
        g = b.model.generate(x, max_new_tokens=64, do_sample=False, pad_token_id=tok.eos_token_id, **GEN)
      reply = tok.decode(g[0, x.shape[1]:], skip_special_tokens=True)
      free, how = parse(reply, l2price)
      rows.append({"cid": c["cid"], "order": list(order), "forced": forced, "free": free, "parsed_by": how,
                   "agree": None if free is None else free == forced, "reply": reply})
  parsed = [r for r in rows if r["free"] is not None]
  agree = sum(r["agree"] for r in parsed) / len(parsed) if parsed else 0.0
  rate = len(parsed) / len(rows)
  descriptive = a.model != "llama31_8b"
  ok = agree >= THRESH_AGREE and rate >= THRESH_PARSE
  lp_rows = [r for r in parsed if r["parsed_by"] == "letter"]
  out = {"n_prompts": len(rows), "parse_rate": rate, "agreement_on_parsed": agree,
         "agreement_on_letter_parsed": (sum(r["agree"] for r in lp_rows) / len(lp_rows)) if lp_rows else None, "n_letter_parsed": len(lp_rows),
         "generation": {"do_sample": False, "max_new_tokens": 64, **GEN}, "adapter": a.adapter, "gpu_seconds": time.time() - t0, "rows": rows}
  if not descriptive:
    out.update({"thresholds": {"agree": THRESH_AGREE, "parse": THRESH_PARSE}, "pass": ok})
  odir = os.path.join(ROOT, "demo_out", "llama" if a.model == "llama31_8b" else a.model.split("_")[0][:4])   # demo_out/llama, demo_out/qwen
  os.makedirs(odir, exist_ok=True)
  name = "freegen_check.json" if not a.adapter else f"freegen_check_{os.path.basename(a.adapter.rstrip('/'))}.json"
  out["model"] = a.model
  json.dump(out, open(os.path.join(odir, name), "w"), indent=1)
  print(json.dumps({k: out.get(k) for k in ("n_prompts", "parse_rate", "agreement_on_parsed", "agreement_on_letter_parsed", "pass", "gpu_seconds")}, indent=1))
  for r in rows[:4]:
    print(r["forced"], r["free"], repr(r["reply"][:120]))
  return 0 if (ok or descriptive) else 2


if __name__ == "__main__":
  sys.exit(main())
