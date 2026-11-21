"""Stage 1 check 4.4: one Phase 2 decision per agent on 9B, twice each.

Pilot prompt v13-V5-information-C3, real all-mpnet-base-v2 embeddings, and a
temporary blank memory bank (plus the player-specific memory, as
phase2.formative_memory adds it). Records only: exception or not, number of
model calls, whether S is non-empty, whether each rule memory reached the prompts,
the longest rendered prompt in tokens, wall time, and SHA-256 equality of S across
the two runs. No offer, regret, S text or calls log is printed or saved."""
import argparse, hashlib, json, os, random, sys, time, traceback
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import torch
from concordia.associative_memory import blank_memories, importance_function
from examples.modular.environment import haggling
from examples.modular.environment.modules import fruitville_haggling as fv
from refimpl import core, phase2, runtime
from refimpl.local_gemma2 import CHOICE_SYSTEM, TEXT_SYSTEM, LocalGemma2, build_messages

AGENTS = ("concordia.factory.agent.rational_agent", "concordia.factory.agent.basic_agent",
          "agent_py_files.taehun_cgcal", "agent_py_files.fluffy_fluffyagent_v16submission",
          "agent_py_files.hgyun_loss_aversion_agent_v3_plus2")
ap = argparse.ArgumentParser()
ap.add_argument("--agents", nargs="*", default=list(AGENTS))
ap.add_argument("--out", default="logs/check_phase2_agents.json")
args = ap.parse_args()

model, tok = runtime.load_gemma("9b", "cuda")
lm = LocalGemma2(model, tok, sequential=True)
embed, _ = runtime.load_embedder("embedder")
p = core.Prompt(13, 5, "information", 3)
assert p.pid == "v13-V5-information-C3"
random.seed(1000 + p.variant)
cfg = haggling.configure_player(p.buyer, "female", fv.YEAR, True, random.Random(1000 + p.variant))
mem = blank_memories.MemoryFactory(
    model=lm, embedder=embed,
    importance=importance_function.ConstantImportanceModel().importance,
    clock_now=lambda: phase2.SETUP).make_blank_memory()
for extra in cfg.extras["player_specific_memories"]:
  mem.add(extra, tags=["initial_player_specific_memory"])

def rendered_tokens(c):
  sysm = TEXT_SYSTEM if c["kind"] == "text" else CHOICE_SYSTEM
  return len(lm.encode(lm.render(build_messages(sysm, c["prompt"]), True))[0])

# Numbers-only generation log: prompt tokens and requested new tokens per call.
gen_log = []
_orig_generate = lm.model.generate
def _logged_generate(ids, **kw):
  gen_log.append({"prompt_tokens": int(ids.shape[1]), "max_new_tokens": kw.get("max_new_tokens")})
  torch.cuda.reset_peak_memory_stats()
  out = _orig_generate(ids, **kw)
  gen_log[-1]["new_tokens"] = int(out.shape[1] - ids.shape[1])
  gen_log[-1]["peak_GiB"] = round(torch.cuda.max_memory_allocated() / 2**30, 2)
  return out
lm.model.generate = _logged_generate

results = json.load(open(args.out)) if os.path.exists(args.out) else {}
for a in args.agents:
  runs = []
  for rep in (0, 1):
    torch.cuda.reset_peak_memory_stats()
    gen_log.clear()
    t = time.perf_counter()
    try:
      r = phase2.run_decision(lm, embed, a, p, mem, cfg, list(fv.VISUAL_SCENE_OPENINGS))
      runs.append({"exception": None, "wall_s": round(time.perf_counter() - t, 1),
                   "n_model_calls": len(r["calls"]),
                   "n_text_calls": sum(c["kind"] == "text" for c in r["calls"]),
                   "n_choice_calls": sum(c["kind"] == "choice" for c in r["calls"]),
                   "S_nonempty": bool(r["S"]),
                   "rule_memories_in_prompts": r["rule_memories_in_prompts"],
                   "longest_prompt_tokens": max(rendered_tokens(c) for c in r["calls"]),
                   "peak_gpu_GiB": round(torch.cuda.max_memory_allocated() / 2**30, 2),
                   "S_sha256": hashlib.sha256(r["S"].encode()).hexdigest()})
      del r
    except Exception as e:  # noqa: BLE001 - logged, run continues
      runs.append({"exception": repr(e)[:500], "traceback": traceback.format_exc()[-2000:],
                   "wall_s": round(time.perf_counter() - t, 1)})
    finally:
      # Release memory held by a failed call (left-over generation cache, frames).
      import gc
      if hasattr(lm.model, "_cache"):
        del lm.model._cache
      gc.collect(); torch.cuda.empty_cache()
    runs[-1]["generate_calls"] = list(gen_log)
  ok = all(x["exception"] is None for x in runs)
  results[a] = {"runs": runs, "S_identical_sha256": ok and runs[0]["S_sha256"] == runs[1]["S_sha256"]}
  printable = {k: v for k, v in results[a].items()}
  print(a, json.dumps(printable, indent=1), flush=True)
  json.dump(results, open(args.out, "w"), indent=1)
