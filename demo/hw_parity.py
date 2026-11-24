"""Hardware parity: rescore stored tune probabilities on the current GPU with the stored code and compare with the A10G numbers.

Gen dataset: the 42 tune cells (84 cases = both name variants, five orders) for plain and for every gen adapter with a run file
(demo_out/gen_lora/*.json), scored with gen_lora.score_case; adapters loaded exactly as demo/floor.py GenEngine loads them
(PEFT load, then the fp32 weights re-copied from the safetensors file). Stored A10G references: demo_out/gen_plain_scores.jsonl
(plain) and tune_probs_best in each run file.
Original dataset: the 24 lora_tune cases (build/tuning cells only) for every original adapter with a run file (demo_out/lora/*.json),
scored with scoring.score as demo/lora.py did; plain reference = history[0].tune_probs in the run files that stored it.
TUNE ONLY: refuses any test split. Writes demo_out/hw_parity/<gpu>_probs.json (resumable per arm).

  PYTHONPATH=concordia:. .venv/bin/python demo/hw_parity.py
"""
import glob, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import torch
import common
import gen_cases as g
import gen_lora
import scoring
import steer_lib
from refimpl import core, phase3, runtime
from refimpl.local_gemma2 import LocalGemma2

OUTDIR = os.path.join(common.ROOT, "demo_out", "hw_parity")


def gen_tune_cases():
  cases = [json.loads(l) for l in open(os.path.join(g.OUT, "cases.jsonl"))]
  tune = [c for c in cases if c["split"] == "tune"]
  assert len(tune) == 84 and len({c["cell"] for c in tune}) == 42 and all(c["split"] == "tune" for c in tune)
  return tune


def orig_tune_cases():
  tune = steer_lib.lora_cases("lora_tune")
  split = common.load_splits()["case_split"]
  assert all(split[p.pid] in ("build", "tuning") for p in tune), "refusing a non-development case"
  return tune


def main():
  os.makedirs(OUTDIR, exist_ok=True)
  gpu = torch.cuda.get_device_name(0).replace("NVIDIA ", "").replace(" ", "_")
  out_path = os.path.join(OUTDIR, f"{gpu}_probs.json")
  res = json.load(open(out_path)) if os.path.exists(out_path) else {"gpu": torch.cuda.get_device_name(0), "gen": {}, "orig": {}, "sec": {}}
  save = lambda: json.dump(res, open(out_path + ".tmp", "w")) or os.replace(out_path + ".tmp", out_path)
  gtune, otune = gen_tune_cases(), orig_tune_cases()
  model, tok = runtime.load_gemma("9b", "cuda")
  lm = LocalGemma2(model, tok)

  def score_gen(tag):
    t0 = time.time()
    out = {}
    for c in gtune:
      p, _, m = gen_lora.score_case(lm, c)
      out[c["cid"]] = {"probs": [float(x) for x in p], "mass": m}
    res["sec"][tag] = time.time() - t0
    return out

  def score_orig(tag):
    t0 = time.time()
    out = {}
    for p in otune:
      r = scoring.score(lm, p)
      out[p.pid] = {"probs": {str(k): float(v) for k, v in r.probs.items()}, "mass": float(r.mass)}
    res["sec"][tag] = time.time() - t0
    return out

  # plain, gen route of gen_score.py (g.render) must be the same text as score_case with no notes
  import gen_notes
  for c in gtune:
    for o in g.orders():
      assert gen_notes.render_notes(c, o, None)[0] == g.render(c, o)[0]
  if "plain" not in res["gen"]:
    res["gen"]["plain"] = score_gen("gen:plain"); save()
  if "plain" not in res["orig"]:
    res["orig"]["plain"] = score_orig("orig:plain"); save()
  print("plain done", flush=True)

  from peft import PeftModel
  from peft.utils import set_peft_model_state_dict
  from safetensors.torch import load_file
  gen_runs = sorted(glob.glob(os.path.join(common.ROOT, "demo_out", "gen_lora", "*.json")))
  orig_runs = sorted(f for f in glob.glob(os.path.join(common.ROOT, "demo_out", "lora", "*.json")) if not os.path.basename(f).startswith("teacher_"))
  jobs = [("gen", f) for f in gen_runs] + [("orig", f) for f in orig_runs]
  runs = [(kind, json.load(open(f))) for kind, f in jobs]
  first = runs[0][1]
  peft = PeftModel.from_pretrained(model, os.path.join(common.ROOT, first["adapter_dir"]), adapter_name="anchor")
  set_peft_model_state_dict(peft, load_file(os.path.join(common.ROOT, first["adapter_dir"], "adapter_model.safetensors")), adapter_name="anchor")
  peft.eval()
  with peft.disable_adapter():                     # adapter off == plain, bit for bit (as in floor.py)
    for c in gtune[:2]:
      assert [float(x) for x in gen_lora.score_case(lm, c)[0]] == res["gen"]["plain"][c["cid"]]["probs"], "adapter off != plain"
  for kind, r in runs:
    rid = r["run_id"]
    if rid in res[kind]:
      continue
    d = os.path.join(common.ROOT, r["adapter_dir"])
    import hashlib
    assert hashlib.sha256(open(os.path.join(d, "adapter_model.safetensors"), "rb").read()).hexdigest() == r["adapter_sha256"], rid
    peft.load_adapter(d, adapter_name="cur")
    rr = set_peft_model_state_dict(peft, load_file(os.path.join(d, "adapter_model.safetensors")), adapter_name="cur")
    assert not getattr(rr, "unexpected_keys", None), rid
    peft.set_adapter("cur")
    peft.eval()
    with torch.no_grad():
      res[kind][rid] = score_gen(f"{kind}:{rid}") if kind == "gen" else score_orig(f"{kind}:{rid}")
    peft.set_adapter("anchor")
    peft.delete_adapter("cur")
    save()
    print(kind, rid, f"{res['sec'][f'{kind}:{rid}']:.0f}s", flush=True)
  # within-session repeat of the adapter named in the startup failure
  rep = "gen_teacher_lr1e-04_s0"
  if "repeat:" + rep not in res["gen"]:
    r = json.load(open(os.path.join(common.ROOT, "demo_out", "gen_lora", rep + ".json")))
    d = os.path.join(common.ROOT, r["adapter_dir"])
    peft.load_adapter(d, adapter_name="cur")
    set_peft_model_state_dict(peft, load_file(os.path.join(d, "adapter_model.safetensors")), adapter_name="cur")
    peft.set_adapter("cur"); peft.eval()
    with torch.no_grad():
      res["gen"]["repeat:" + rep] = score_gen("repeat")
    save()
  print("HW PARITY DONE", flush=True)


if __name__ == "__main__":
  main()
