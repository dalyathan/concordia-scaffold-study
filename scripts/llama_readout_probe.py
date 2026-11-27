"""G1 readout probe (before step 4): where does the plain model put its first assistant token? 20 tune cases x 5 orders.

  HF_HUB_OFFLINE=1 PYTHONPATH=concordia:. .venv/bin/python scripts/llama_readout_probe.py [--model llama31_8b]
Writes demo_out/llama/readout_probe.json: per case and order the top-10 first tokens with probabilities, and the mean mass on the bare
answer letters (the readout), on capital letters, on space-prefixed letters, and on "(". Bands frozen in LLAMA_PLAN.md:
mean bare-letter mass >= 0.9 -> interpret; 0.5-0.9 -> caution: stop before step 4 and re-gate a framing change; < 0.5 -> stop."""
import argparse, json, os, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from harness import modelspec
from harness.solvers.hf import Backend
from harness.task import get_task


def main():
  ap = argparse.ArgumentParser(); ap.add_argument("--model", default="llama31_8b"); ap.add_argument("--n", type=int, default=20); a = ap.parse_args()
  import torch
  t0 = time.time()
  spec = modelspec.load(a.model); b = Backend(spec); task = get_task("haggling")
  tok = b.tok
  ids1 = lambda s: (lambda x: x[0] if len(x) == 1 else None)(tok(s, add_special_tokens=False).input_ids)
  groups = {"bare": list(spec.answer_letter_token_ids), "capital": [ids1(l.upper()) for l in spec.answer_letters],
            "space": [ids1(" " + l) for l in spec.answer_letters], "paren": [ids1("(")]}
  groups = {k: [i for i in v if i is not None] for k, v in groups.items()}
  cases = task.cases("tune")[:: max(1, len(task.cases("tune")) // a.n)][:a.n]
  rows, sums = [], {k: 0.0 for k in groups}
  for c in cases:
    for order in task.orders(c):
      text, _ = task.render(c, order)
      prompt = tok.apply_chat_template(b.messages(text), tokenize=False, add_generation_prompt=True, **(spec.chat_template_kwargs or {}))
      x = tok(prompt, return_tensors="pt", add_special_tokens=False).input_ids.to(b.model.device)
      with torch.no_grad():
        p = torch.softmax(b.model(input_ids=x).logits[0, -1].float(), -1)
      top = torch.topk(p, 10)
      m = {k: float(p[v].sum()) for k, v in groups.items()}
      for k in sums: sums[k] += m[k]
      rows.append({"cid": c["cid"], "order": list(order), "mass": m,
                   "top10": [[tok.decode([int(i)]), round(float(q), 5)] for q, i in zip(top.values, top.indices)]})
  n = len(rows)
  mean = {k: v / n for k, v in sums.items()}
  band = "interpret" if mean["bare"] >= 0.9 else ("caution: stop and re-gate a framing change" if mean["bare"] >= 0.5 else "stop")
  out = {"model": spec.name, "revision": b.revision, "n_prompts": n, "mean_mass": mean, "band": band, "groups": groups,
         "gpu_seconds": time.time() - t0, "rows": rows}
  os.makedirs(os.path.join(ROOT, "demo_out", "llama"), exist_ok=True)
  json.dump(out, open(os.path.join(ROOT, "demo_out", "llama", "readout_probe.json"), "w"), indent=1)
  print(json.dumps({k: out[k] for k in ("n_prompts", "mean_mass", "band", "gpu_seconds", "revision")}, indent=1))
  for r in rows[:3]:
    print(r["cid"], r["top10"][:5])


if __name__ == "__main__":
  main()
