"""One YAML config per model (harness/models/*.yaml). Shared code reads model facts only through ModelSpec.

Fields marked `null` in `answer_letter_token_ids` are filled by `python tools/model_checks.py --write` from the real tokenizer;
they are never typed by hand. `verified` records which facts were checked against the hub config/tokenizer."""
from __future__ import annotations

import dataclasses
import glob
import os

import yaml

DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
REQUIRED = ("name", "hf_id", "dtype", "attn_implementation", "chat_template", "system_role", "answer_letters",
            "answer_letter_token_ids", "num_layers", "hidden_size", "layer_module", "final_norm_module", "lora_target_modules")


@dataclasses.dataclass(frozen=True)
class ModelSpec:
  name: str
  hf_id: str
  dtype: str
  attn_implementation: str
  chat_template: str           # family tag; the template text itself comes from the tokenizer
  system_role: bool            # False: the system text is folded into the first user turn
  answer_letters: tuple
  answer_letter_token_ids: tuple | None
  num_layers: int
  hidden_size: int
  layer_module: str            # dotted path of the decoder layer list, "{i}" is the layer index
  final_norm_module: str
  lora_target_modules: tuple
  generation_end_tokens: tuple = ()
  verified: tuple = ()
  revision: str | None = None   # hub commit hash of the weights and tokenizer; Backend refuses to load without one
  notes: str = ""

  def layer_names(self) -> list[str]:
    return [self.layer_module.format(i=i) for i in range(self.num_layers)]


def load(name_or_path: str) -> ModelSpec:
  path = name_or_path if os.path.exists(name_or_path) else os.path.join(DIR, name_or_path + ".yaml")
  d = yaml.safe_load(open(path))
  missing = [k for k in REQUIRED if k not in d]
  if missing:
    raise ValueError(f"{path}: missing fields {missing}")
  for k in ("answer_letters", "lora_target_modules", "generation_end_tokens", "verified"):
    if k in d and d[k] is not None:
      d[k] = tuple(d[k])
  if d["answer_letter_token_ids"] is not None:
    d["answer_letter_token_ids"] = tuple(d["answer_letter_token_ids"])
  if "{i}" not in d["layer_module"]:
    raise ValueError(f"{path}: layer_module must contain {{i}}")
  return ModelSpec(**{k: v for k, v in d.items() if k in {f.name for f in dataclasses.fields(ModelSpec)}})


def all_names() -> list[str]:
  return sorted(os.path.splitext(os.path.basename(p))[0] for p in glob.glob(os.path.join(DIR, "*.yaml")))
