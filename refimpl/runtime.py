"""Model and embedder loading for GPU runs (Protocol section 3).

Models live in ./models in the Hugging Face cache layout (scripts/download_models.py),
so each path is the snapshot directory of its pinned revision. Every process that
imports agent code runs with HF_HUB_OFFLINE=1 and no network.

The 9B model is loaded with low_cpu_mem_usage=True and device_map={"": 0}: shards are
memory-mapped and moved to the GPU tensor by tensor, so the weights never sit in
system RAM in full (the bank-generation machine has 16 GB of RAM). Only one language
model is loaded per process.
"""
from __future__ import annotations

import os

import torch

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(REPO_ROOT, "models")

GEMMA_9B = ("google/gemma-2-9b-it", "11c9b309abf73637e4b6f9a3fa1e92e615547819")
GEMMA_2B = ("google/gemma-2-2b-it", "299a8560bedf22ed1c72a8a11e7dce4a7f9f51f8")
EMBEDDER = ("sentence-transformers/all-mpnet-base-v2", "e8c3b32edf5434bc2275fc9bab85f82640a19130")
PINS = {"9b": GEMMA_9B, "2b": GEMMA_2B, "embedder": EMBEDDER}


def snapshot_path(repo: str, revision: str, models_dir: str = MODELS_DIR) -> str:
  path = os.path.join(models_dir, "models--" + repo.replace("/", "--"), "snapshots", revision)
  if not os.path.isdir(path):
    raise FileNotFoundError(f"{repo}@{revision} not found under {models_dir}")
  return path


def resolve(name_or_path: str) -> tuple[str, str | None]:
  """'9b' / '2b' / 'embedder' -> (snapshot path, revision); a path -> (path, None)."""
  if name_or_path in PINS:
    repo, rev = PINS[name_or_path]
    return snapshot_path(repo, rev), rev
  for repo, rev in PINS.values():
    if os.path.abspath(name_or_path) == os.path.abspath(snapshot_path_or_none(repo, rev) or ""):
      return name_or_path, rev
  return name_or_path, None


def snapshot_path_or_none(repo, rev):
  try:
    return snapshot_path(repo, rev)
  except FileNotFoundError:
    return None


def load_gemma(name_or_path: str = "9b", device: str = "cuda"):
  """Returns (model, tokenizer). device='cuda': bfloat16, eager attention,
  low_cpu_mem_usage, device_map={"": 0} (straight to GPU 0). device='cpu': the
  CPU smoke-test configuration."""
  from transformers import AutoModelForCausalLM, AutoTokenizer
  path, rev = resolve(name_or_path)
  kw = dict(revision=rev) if rev else {}
  tok = AutoTokenizer.from_pretrained(path, **kw)
  if device == "cuda":
    model = AutoModelForCausalLM.from_pretrained(
        path, torch_dtype=torch.bfloat16, attn_implementation="eager",
        low_cpu_mem_usage=True, device_map={"": 0}, **kw)
  elif device == "cpu":
    model = AutoModelForCausalLM.from_pretrained(
        path, torch_dtype=torch.bfloat16, attn_implementation="eager",
        low_cpu_mem_usage=True, **kw)
  else:
    raise ValueError(device)
  return model.eval(), tok


def load_lm(name_or_path: str = "9b", device: str = "cuda", sequential: bool = True, **kw):
  from .local_gemma2 import LocalGemma2
  model, tok = load_gemma(name_or_path, device)
  return LocalGemma2(model, tok, sequential=sequential, **kw)


def load_embedder(name_or_path: str = "embedder"):
  """all-mpnet-base-v2 on the CPU (its vectors go into the hashed memory banks).
  Returns (callable text -> vector, SentenceTransformer)."""
  from sentence_transformers import SentenceTransformer
  path, rev = resolve(name_or_path)
  kw = dict(revision=rev) if rev else {}
  model = SentenceTransformer(path, device="cpu", **kw)
  return (lambda t: model.encode(t, show_progress_bar=False)), model


def env_report() -> dict:
  import transformers
  out = {"torch": torch.__version__, "torch.version.cuda": torch.version.cuda,
         "cudnn": torch.backends.cudnn.version(), "transformers": transformers.__version__,
         "CUBLAS_WORKSPACE_CONFIG": os.environ.get("CUBLAS_WORKSPACE_CONFIG"),
         "PYTORCH_CUDA_ALLOC_CONF": os.environ.get("PYTORCH_CUDA_ALLOC_CONF"),
         "HF_HUB_OFFLINE": os.environ.get("HF_HUB_OFFLINE")}
  if torch.cuda.is_available():
    out["gpu"] = torch.cuda.get_device_name(0)
    out["gpu_total_bytes"] = torch.cuda.get_device_properties(0).total_memory
  return out
