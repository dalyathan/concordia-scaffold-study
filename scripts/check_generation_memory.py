"""Peak GPU memory of sample_text (greedy, with last-position prefill
unembedding) for long synthetic prompts, max_tokens 1,000 (cache sized for 1,000
new tokens); generation stops at the first period. No agent is involved."""
import argparse, gc, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import torch
from examples.modular.environment.modules import fruitville_haggling as fv
from refimpl import conditions, runtime
from refimpl.local_gemma2 import LocalGemma2, TEXT_SYSTEM, build_messages, call_context

ap = argparse.ArgumentParser()
ap.add_argument("--lengths", nargs="*", type=int, default=[2424, 4000, 5000, 6000])
ap.add_argument("--max-tokens", type=int, default=1000)
ap.add_argument("--out", default="logs/check_generation_memory.json")
args = ap.parse_args()
model, tok = runtime.load_gemma("9b", "cuda")
lm = LocalGemma2(model, tok)
res = []
for n in args.lengths:
  text = conditions.qa_filler(list(fv.VISUAL_SCENE_OPENINGS), n, tok) + "\nQuestion: What is the weather like?\nAnswer:"
  ids = lm.encode(lm.render(build_messages(TEXT_SYSTEM, text), True))
  torch.cuda.empty_cache(); torch.cuda.reset_peak_memory_stats()
  t = time.perf_counter()
  try:
    with call_context(agent="memcheck", pid=f"len{n}", temperature_override=0.0):
      lm.sample_text(text, max_tokens=args.max_tokens, terminators=(".",))
    ok, err = True, None
  except torch.OutOfMemoryError as e:
    ok, err = False, "OutOfMemoryError"
  res.append({"prompt_tokens": int(ids.shape[1]), "max_new_tokens": args.max_tokens, "ok": ok, "error": err,
              "peak_GiB": round(torch.cuda.max_memory_allocated() / 2**30, 2),
              "wall_s": round(time.perf_counter() - t, 1)})
  print(res[-1], flush=True)
  if hasattr(lm.model, "_cache"):
    del lm.model._cache
  gc.collect(); torch.cuda.empty_cache()
json.dump(res, open(args.out, "w"), indent=1)
