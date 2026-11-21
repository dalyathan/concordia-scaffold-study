"""Stage 1 step 5: generate the 14 formative-memory banks (variants 1-14) with
phase2.formative_memory on 9B (greedy, determinism patches), save each as parquet
(text, time, tags, importance, embedding) and record its SHA-256. Resumable:
existing banks are skipped. Banks contain no outcome."""
import argparse, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import torch
from refimpl import phase2, runtime
from refimpl.local_gemma2 import LocalGemma2

ap = argparse.ArgumentParser()
ap.add_argument("--variants", nargs="*", type=int, default=list(range(1, 15)))
ap.add_argument("--out", default="banks")
args = ap.parse_args()
os.makedirs(args.out, exist_ok=True)
manifest_path = os.path.join(args.out, "manifest.json")
manifest = json.load(open(manifest_path)) if os.path.exists(manifest_path) else {}
model, tok = runtime.load_gemma("9b", "cuda")
n_calls = {"n": 0}
lm = LocalGemma2(model, tok, sequential=True, log=lambda rec: n_calls.__setitem__("n", n_calls["n"] + 1))
embed, _ = runtime.load_embedder("embedder")
for v in args.variants:
  path = os.path.join(args.out, f"formative_v{v:02d}.parquet")
  if os.path.exists(path) and str(v) in manifest:
    print(f"variant {v}: exists, skipped", flush=True)
    continue
  n_calls["n"] = 0
  torch.cuda.reset_peak_memory_stats()
  t = time.perf_counter()
  mem, cfg = phase2.formative_memory(lm, embed, v)
  sha = phase2.save_bank(mem, path)
  # Round-trip check against the live memory (same process, so hashes comparable).
  import numpy as np
  loaded, cfg2 = phase2.load_bank(path, lm, embed, v)
  a, b = mem.get_data_frame(), loaded.get_data_frame()
  rt = (list(a.columns) == list(b.columns) and list(a.dtypes) == list(b.dtypes)
        and all(list(a[c]) == list(b[c]) for c in ("text", "time", "tags", "importance"))
        and all(np.array_equal(x, y) for x, y in zip(a["embedding"], b["embedding"]))
        and loaded._stored_hashes == mem._stored_hashes and cfg2.extras == cfg.extras)
  assert rt, f"variant {v}: bank round trip failed"
  manifest[str(v)] = {"file": os.path.basename(path), "sha256": sha,
                      "rows": len(mem.get_data_frame()), "buyer": cfg.name,
                      "model_calls": n_calls["n"], "wall_s": round(time.perf_counter() - t, 1),
                      "peak_gpu_GiB": round(torch.cuda.max_memory_allocated() / 2**30, 2),
                      "round_trip_ok": rt}
  json.dump(manifest, open(manifest_path, "w"), indent=1, sort_keys=True)
  print(f"variant {v}:", json.dumps(manifest[str(v)]), flush=True)
print("done")
