"""Model-backed solvers (GPU). WRITTEN BUT NOT RUN in the refactor session (the GPU was busy); see REFACTOR_STATUS.md.

Everything model-specific comes from a ModelSpec; no model name appears here. Readout: first-token probability of each answer
letter right after the rendered prompt (the same readout as the pre-refactor code in refimpl/), renormalised over the letters, with the
unrenormalised letter mass reported. torch / transformers / peft are imported lazily so the module imports on a CPU box."""
from __future__ import annotations

import hashlib
import os

from harness import modelspec

# Same chat framing as the pre-refactor code (refimpl/: CHOICE_SYSTEM + two few-shot turns), so a 9B
# plain readout can be compared with the stored numbers (GPU check listed in REFACTOR_STATUS.md).
SYSTEM = "You always continue sentences provided by the user and you never repeat what the user already said."
FEW_SHOT = [("Question: Is Jake a turtle?\nAnswer: Jake is ", "not a turtle."),
            ("Question: What is Priya doing right now?\nAnswer: Priya is currently ", "sleeping.")]


def _sha(b: bytes) -> str: return hashlib.sha256(b).hexdigest()


def file_sha(path: str) -> str:
  h = hashlib.sha256()
  if os.path.isdir(path):
    for dp, _, fs in sorted(os.walk(path)):
      for f in sorted(fs):
        h.update(f.encode()); h.update(open(os.path.join(dp, f), "rb").read())
  else:
    h.update(open(path, "rb").read())
  return h.hexdigest()


class Backend:
  """One loaded model + tokenizer, shared by solvers (adapters are switched on it, not reloaded)."""
  def __init__(self, spec: modelspec.ModelSpec, device="cuda", revision=None):
    import torch
    revision = revision or spec.revision
    from transformers import AutoModelForCausalLM, AutoTokenizer
    if spec.answer_letter_token_ids is None or "tokenizer" not in spec.verified:
      raise RuntimeError(f"{spec.name}: answer_letter_token_ids not filled and verified; run tools/model_checks.py --write first")
    if revision is None and not os.environ.get("HARNESS_ALLOW_UNPINNED"):
      raise RuntimeError(f"{spec.name}: pass a pinned hub revision (commit hash) or set HARNESS_ALLOW_UNPINNED=1 (then the record says so)")
    self.spec, self.torch = spec, torch
    kw = {"revision": revision} if revision else {}
    self.tok = AutoTokenizer.from_pretrained(spec.hf_id, **kw)
    self.model = AutoModelForCausalLM.from_pretrained(
        spec.hf_id, torch_dtype=getattr(torch, spec.dtype), attn_implementation=spec.attn_implementation,
        low_cpu_mem_usage=True, device_map={"": 0} if device == "cuda" else None, **kw).eval()
    self.layers = self._resolve(spec.layer_module.rsplit(".{i}", 1)[0])
    self.revision = revision or getattr(self.model.config, "_commit_hash", None)
    self.pinned = revision is not None
    self.peft = None

  def _resolve(self, dotted):
    obj = self.model
    for part in dotted.split("."):
      obj = getattr(obj, part)
    return obj

  def messages(self, user: str, lesson: str | None = None):
    text = user if lesson is None else lesson.rstrip() + "\n\n" + user
    msgs = [{"role": "system", "content": SYSTEM}] if self.spec.system_role else []
    for i, (u, a) in enumerate(FEW_SHOT):
      msgs += [{"role": "user", "content": (SYSTEM + "\n\n" + u) if (i == 0 and not self.spec.system_role) else u},
               {"role": "assistant", "content": a}]
    return msgs + [{"role": "user", "content": text}]

  def next_letter_logprobs(self, user: str, lesson=None, hooks=()):
    torch = self.torch
    prompt = self.tok.apply_chat_template(self.messages(user, lesson), tokenize=False, add_generation_prompt=True)
    ids = self.tok(prompt, return_tensors="pt", add_special_tokens=False).input_ids.to(self.model.device)
    handles = [h(ids.shape[1] - 1) for h in hooks]
    try:
      with torch.no_grad():
        logits = self.model(input_ids=ids).logits[0, -1].float()
    finally:
      for h in handles: h.remove()
    lp = torch.log_softmax(logits, dim=-1)
    return {l: float(lp[i]) for l, i in zip(self.spec.answer_letters, self.spec.answer_letter_token_ids)}, prompt


class _HFSolver:
  name = "hf"
  def __init__(self, backend: Backend): self.b = backend
  def _extra(self): return {}
  def hooks(self, case): return ()
  def lesson(self): return None
  def describe(self):
    return {"solver": self.name, "model": self.b.spec.name, "hf_id": self.b.spec.hf_id, "revision": self.b.revision, "revision_pinned": self.b.pinned,
            "dtype": self.b.spec.dtype, "attn": self.b.spec.attn_implementation, **self._extra()}

  uses_adapter = False
  def letter_probs(self, task, case, order):
    import contextlib, math
    text, l2o = task.render(case, order)
    peft = getattr(self.b, "peft", None)
    ctx = self.b.peft.disable_adapter() if (peft is not None and not self.uses_adapter) else contextlib.nullcontext()
    with ctx:
      lp, prompt = self.b.next_letter_logprobs(text, self.lesson(), self.hooks(case))
    letters = list(l2o)
    mass = sum(math.exp(lp[l]) for l in letters)
    return {"probs": {l: math.exp(lp[l]) / mass for l in letters}, "mass": mass,
            "prompt_sha256": _sha(prompt.encode())}


class PlainSolver(_HFSolver):
  name = "plain"


class LessonSolver(_HFSolver):
  """A written lesson placed before the case (fixed text; its hash is recorded)."""
  name = "lesson"
  def __init__(self, backend, lesson_path: str):
    super().__init__(backend); self.path = lesson_path; self.text = open(lesson_path).read()
  def lesson(self): return self.text
  def _extra(self): return {"lesson_path": self.path, "lesson_sha256": _sha(self.text.encode())}


class SteeringSolver(_HFSolver):
  """Adds `scale * vector` to the residual stream output of decoder layer `layer` at the last prompt position."""
  name = "steering"
  def __init__(self, backend, vector_path: str, layer: int, scale: float):
    super().__init__(backend)
    self.vec = backend.torch.load(vector_path, map_location="cpu"); self.vpath, self.layer, self.scale = vector_path, layer, scale
    assert self.vec.shape[-1] == backend.spec.hidden_size, f"steering vector size {tuple(self.vec.shape)} != hidden size {backend.spec.hidden_size}"
    assert 0 <= layer < backend.spec.num_layers
  def hooks(self, case):
    def mk(pos):
      def hook(mod, inp, out):
        hs = out[0] if isinstance(out, tuple) else out
        hs[:, pos, :] = hs[:, pos, :] + (self.scale * self.vec).to(hs.dtype).to(hs.device)
        return (hs, *out[1:]) if isinstance(out, tuple) else hs
      return self.b.layers[self.layer].register_forward_hook(hook)
    return (mk,)
  def _extra(self): return {"vector_path": self.vpath, "vector_sha256": file_sha(self.vpath), "layer": self.layer, "scale": self.scale}


class LoRASolver(_HFSolver):
  """A saved PEFT adapter (directory). Adapters are never moved or deleted by the harness. PEFT injects the LoRA layers into the
  shared model in place, so every other solver on this Backend runs under `disable_adapter()` (see _HFSolver.letter_probs)."""
  name = "lora"
  uses_adapter = True
  def __init__(self, backend, adapter_dir: str):
    super().__init__(backend)
    from peft import PeftModel
    self.dir = adapter_dir
    self.peft = PeftModel.from_pretrained(backend.model, adapter_dir).eval()
    backend.peft = self.peft
  def _extra(self): return {"adapter_dir": self.dir, "adapter_sha256": file_sha(self.dir)}
