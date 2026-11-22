"""Stage 1 check 4.3: peak GPU memory and time per sequential scoring pass on 9B,
for a short Phase 3 prompt and a worst-case one (3,000-token Notes filler, about
4,500 tokens in all), unsteered and steered at layer 18, with activation capture
as in Phase 3. Pilot variant 13 only. Prints no probabilities, offers or regret."""
import argparse, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import torch
from examples.modular.environment.modules import fruitville_haggling as fv
from refimpl import conditions, core, phase3, runtime
from refimpl.local_gemma2 import CHOICE_SYSTEM, LocalGemma2, build_messages

ap = argparse.ArgumentParser()
ap.add_argument("--model", default="9b")
ap.add_argument("--reps", type=int, default=3)
ap.add_argument("--out", default="logs/check_phase3_memory.json")
ap.add_argument("--notes-tokens", nargs="*", type=int, default=[200, 3000])
args = ap.parse_args()
model, tok = runtime.load_gemma(args.model, "cuda")
lm = LocalGemma2(model, tok, sequential=True)
openings = list(fv.VISUAL_SCENE_OPENINGS)
p = core.Prompt(13, 5, "neutral", None)
opening = openings[p.opening_index]
order = core.cyclic_orders()[0]
cases = {f"{n}-token notes": conditions.qa_filler(openings, n, tok) for n in args.notes_tokens}
LAYER = 18
results = {"model": args.model, "gpu": torch.cuda.get_device_name(0), "cases": {}}
for name, notes in cases.items():
  user, _ = phase3.decision_user_turn(p, opening, notes, order)
  n_tok = len(lm.encode(lm.render(build_messages(CHOICE_SYSTEM, user, "a"), False))[0])
  # Steering vector: the prompt's own layer-18 P1 activation (realistic norm).
  _, _, store, _ = phase3.score_prompt(lm, p, opening, notes, order, capture=True)
  vec = store[LAYER]["P1"].float()
  rec = {"tokens_per_sequence": n_tok, "notes_tokens": conditions.n_tokens(notes, tok)}
  for mode, steer in (("unsteered", None), ("steered L18", (LAYER, vec))):
    torch.cuda.synchronize(); torch.cuda.reset_peak_memory_stats()
    times, outs = [], []
    for _ in range(args.reps):
      t = time.perf_counter()
      probs, _, _, full = phase3.score_prompt(lm, p, opening, notes, order, capture=True,
                                              steer=steer)
      torch.cuda.synchronize()
      times.append(time.perf_counter() - t)
      outs.append(json.dumps([probs, full, lm.last_letter_mass]))
    rec[mode] = {"peak_gpu_bytes": torch.cuda.max_memory_allocated(),
                 "peak_gpu_GiB": round(torch.cuda.max_memory_allocated() / 2**30, 2),
                 "sec_per_scoring_6_passes": [round(x, 3) for x in times],  # P1 pass + 5 whole-answer passes
                 "sec_per_pass_mean": round(sum(times) / len(times) / 6, 3),
                 "repeat_bit_identical": len(set(outs)) == 1}
  results["cases"][name] = rec
  print(name, json.dumps(rec, indent=1), flush=True)
results["weights_GiB"] = round(sum(x.numel() * x.element_size() for x in model.parameters()) / 2**30, 2)
os.makedirs(os.path.dirname(args.out), exist_ok=True)
json.dump(results, open(args.out, "w"), indent=1)
print("weights GiB", results["weights_GiB"])
