"""Diagnostic for a failed Gemma parity check (JOB A; does not change the verdict): where does the harness readout differ from the stored
pre-refactor readout on the same GPU (A40)?

  HF_HUB_OFFLINE=1 HF_HUB_CACHE=models PYTHONPATH=concordia:. .venv/bin/python scripts/gemma_parity_diag.py
Prompts are byte-identical (checked separately: 420/420). On the plain model and the 84 tune cases x 5 orders, three readouts of the same
loaded model are compared with the A40 reference (demo_out/hw_parity/A40_probs.json, plain):
  H  harness:          model(input_ids).logits[-1] (HF Gemma2: lm_head over all positions, soft-cap in bf16, then float)
  L  legacy-style:     model.model(use_cache=False) hidden -> lm_head on the last position only -> float -> soft-cap in float32 (refimpl)
  M  mixed:            harness forward, but lm_head on the last hidden state and the soft-cap in float32
Order-averaged probabilities over the 5 letters are renormalised exactly as harness.evaluate does. Writes demo_out/gemma_parity_diag.json."""
import json, os, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def main():
  import numpy as np, torch
  from harness import modelspec
  from harness.solvers.hf import Backend
  from harness.task import get_task
  t0 = time.time()
  spec = modelspec.load("gemma2_9b"); b = Backend(spec); task = get_task("haggling"); m = b.model; tok = b.tok
  cap = m.config.final_logit_softcapping
  ref = json.load(open(os.path.join(ROOT, "demo_out", "hw_parity", "A40_probs.json")))["gen"]["plain"]
  ids_l = list(spec.answer_letter_token_ids)

  def letters(logits_f32):
    lp = torch.log_softmax(logits_f32, -1)
    p = torch.exp(lp[ids_l]).double().cpu().numpy()
    return p

  def capf(x):
    return torch.tanh(x / cap) * cap

  out = {k: [] for k in "HLM"}
  for c in task.cases("tune"):
    acc = {k: np.zeros(5) for k in "HLM"}
    orders = task.orders(c)
    for o in orders:
      text, l2o = task.render(c, o)
      x = tok(b.render_prompt(text), return_tensors="pt", add_special_tokens=False).input_ids.to(m.device)
      with torch.no_grad():
        H = letters(m(input_ids=x).logits[0, -1].float())
        hid = m.model(input_ids=x, use_cache=False).last_hidden_state[:, -1:]
        L = letters(capf(m.lm_head(hid).float())[0, 0])
        hid2 = m.model(input_ids=x).last_hidden_state[:, -1:]
        M = letters(capf(m.lm_head(hid2).float())[0, 0])
      for k, p in (("H", H), ("L", L), ("M", M)):
        q = p / p.sum()
        for letter_idx, letter in enumerate(spec.answer_letters):
          acc[k][l2o[letter]] += q[letter_idx] / len(orders)
    for k in "HLM":
      out[k].append((c["cid"], acc[k]))
  res = {}
  for k in "HLM":
    d = [float(np.max(np.abs(np.array(p) - np.array(ref[cid]["probs"])))) for cid, p in out[k]]
    res[k] = {"max_abs_dp_vs_A40": max(d), "n_cases_over_1e-3": int(sum(v > 1e-3 for v in d)), "median_abs_dp": float(np.median(d)), "n": len(d)}
  res["gpu_seconds"] = time.time() - t0
  json.dump(res, open(os.path.join(ROOT, "demo_out", "gemma_parity_diag.json"), "w"), indent=1)
  print(json.dumps(res, indent=1))


if __name__ == "__main__":
  main()
