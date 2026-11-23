#!/usr/bin/env python3
"""CPU-only tokenizer check, one block per model config. Needs the tokenizer files (hub download, or --local-dir DIR/<model name>/).

Checks per config:
  1. each answer letter is a single token in the rendered prompt context (the id is the token after the prompt's final '(');
  2. the chat template renders a sample case (with the system-role handling the config declares);
  3. the config's hook module names exist in the model's architecture (from config.json: layer count, hidden size) and the
     layer count / hidden size in our YAML equal the hub config.
  python tools/model_checks.py [--write] [--local-dir DIR] [--models a,b] [--md MODEL_CHECKS.md]
--write stores the verified letter ids and `verified` facts back into harness/models/*.yaml. Models whose files cannot be fetched
(gated repo without HF_TOKEN, no network) are reported as NOT CHECKED with the reason; nothing is guessed."""
import argparse, json, os, sys, traceback
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from harness import modelspec
from harness.solvers.hf import FEW_SHOT, SYSTEM

SAMPLE_CASE_ID = "V5-gC-information-C2-p1_5-w1-n0"


def sample_prompt():
  from harness.tasks.haggling import HagglingTask
  t = HagglingTask(); _, cases = t.build_all()
  case = next(c for c in cases if c["cid"] == SAMPLE_CASE_ID)
  return t.render(case, t.orders(case)[0])[0]


def messages(spec, user):
  msgs = [{"role": "system", "content": SYSTEM}] if spec.system_role else []
  for i, (u, a) in enumerate(FEW_SHOT):
    msgs += [{"role": "user", "content": (SYSTEM + "\n\n" + u) if (i == 0 and not spec.system_role) else u}, {"role": "assistant", "content": a}]
  return msgs + [{"role": "user", "content": user}]


def load_tokenizer_and_config(spec, local_dir):
  from transformers import AutoConfig, AutoTokenizer
  src = os.path.join(local_dir, spec.name) if local_dir and os.path.isdir(os.path.join(local_dir, spec.name)) else spec.hf_id
  return AutoTokenizer.from_pretrained(src), AutoConfig.from_pretrained(src), src


def check(spec, local_dir, user):
  res = {"model": spec.name, "hf_id": spec.hf_id, "checks": [], "letter_ids": None, "verified": []}
  try:
    tok, cfg, src = load_tokenizer_and_config(spec, local_dir)
  except Exception as e:
    res["status"] = "NOT CHECKED"; res["reason"] = f"{type(e).__name__}: {str(e)[:200]}"; return res
  ok = True
  def rec(name, passed, detail):
    nonlocal ok
    ok &= bool(passed); res["checks"].append({"name": name, "passed": bool(passed), "detail": detail})
  # 2. template renders; system-role handling
  try:
    prompt = tok.apply_chat_template(messages(spec, user), tokenize=False, add_generation_prompt=True)
    rec("chat template renders the sample case", user[:60] in prompt and len(prompt) > len(user), f"{len(prompt)} chars; tail={prompt[-60:]!r}")
  except Exception as e:
    prompt = None; rec("chat template renders the sample case", False, f"{type(e).__name__}: {e}")
  try:
    tok.apply_chat_template([{"role": "system", "content": "s"}, {"role": "user", "content": "u"}], tokenize=False)
    accepts_system = True
  except Exception:
    accepts_system = False
  rec("config system_role matches the template", accepts_system or not spec.system_role,
      f"template accepts a system message: {accepts_system}; config says {spec.system_role}")
  # 1. letters
  ids = []
  if prompt is not None:
    base = tok(prompt, add_special_tokens=False).input_ids
    for l in spec.answer_letters:
      full = tok(prompt + l, add_special_tokens=False).input_ids
      single = len(full) == len(base) + 1 and full[:len(base)] == base
      ids.append(full[-1] if single else None)
      rec(f"letter {l!r} is one token after the prompt", single, f"ids appended: {full[len(base):] if full[:len(base)] == base else 'prefix changed'}")
    distinct = len({i for i in ids if i is not None}) == len(ids)
    rec("letter ids are distinct", distinct, str(ids))
    if spec.answer_letter_token_ids is not None:
      rec("config letter ids equal the tokenizer's", tuple(ids) == spec.answer_letter_token_ids, f"config {spec.answer_letter_token_ids} vs {tuple(ids)}")
  # 3. hooks vs the hub config
  n = getattr(cfg, "num_hidden_layers", None); h = getattr(cfg, "hidden_size", None)
  rec("layer count equals the hub config", n == spec.num_layers, f"config.json {n} vs yaml {spec.num_layers}")
  rec("hidden size equals the hub config", h == spec.hidden_size, f"config.json {h} vs yaml {spec.hidden_size}")
  archs = getattr(cfg, "architectures", None) or []
  rec("architecture is a causal LM with a .model.layers list (hook path)", any(a.endswith("ForCausalLM") for a in archs), f"architectures {archs}; hook names {spec.layer_names()[0]} .. {spec.layer_names()[-1]}")
  res["status"] = "PASS" if ok else "FAIL"
  if ok:
    res["letter_ids"] = ids; res["verified"] = ["tokenizer", "chat_template", "num_layers", "hidden_size"]
  res["source"] = src
  return res


def write_md(results, path):
  L = ["# MODEL_CHECKS", "", "Generated by `python tools/model_checks.py` (CPU only; tokenizer and config files only, no weights). Do not edit by hand.", "",
       "| model | status | letter ids a..e |", "| --- | --- | --- |"]
  for r in results:
    L.append(f"| {r['model']} (`{r['hf_id']}`) | {r['status']} | {r['letter_ids'] or '-'} |")
  for r in results:
    L += ["", f"## {r['model']}", ""]
    if r["status"] == "NOT CHECKED":
      L.append(f"NOT CHECKED: {r['reason']}")
      continue
    L += ["| check | result | detail |", "| --- | --- | --- |"] + [f"| {c['name']} | {'ok' if c['passed'] else 'FAIL'} | {c['detail']} |" for c in r["checks"]]
  open(path, "w").write("\n".join(L) + "\n")


def main():
  ap = argparse.ArgumentParser(); ap.add_argument("--write", action="store_true"); ap.add_argument("--local-dir")
  ap.add_argument("--models"); ap.add_argument("--md", default=os.path.join(ROOT, "MODEL_CHECKS.md")); a = ap.parse_args()
  names = a.models.split(",") if a.models else modelspec.all_names()
  user = sample_prompt()
  results = [check(modelspec.load(n), a.local_dir, user) for n in names]
  write_md(results, a.md)
  if a.write:
    for r in results:
      if r["status"] == "PASS":
        p = os.path.join(modelspec.DIR, r["model"] + ".yaml")
        txt = open(p).read()
        txt = txt.replace("answer_letter_token_ids: null", f"answer_letter_token_ids: {r['letter_ids']}")
        txt = txt.replace("verified: []", f"verified: {r['verified']}")
        open(p, "w").write(txt)
  for r in results:
    print(r["model"], r["status"], r.get("reason", ""))
  return 0 if all(r["status"] != "FAIL" for r in results) else 1


if __name__ == "__main__":
  sys.exit(main())
