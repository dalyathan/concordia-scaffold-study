"""LoRA split: the 17 development cells -> 11 train cells and 6 held-out tune cells,
all four variants each, balanced by case type (hand-picked before any LoRA result;
see DEMO_STATUS.md). Test cells are untouched. Writes demo/splits_lora.json."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
from refimpl import core

TUNE_CELLS = [(3, "C", 2), (5, "C", 4), (6, "C", 1), (3, "C", 4), (3, "neutral"), (5, "pressure")]
dev = [p for p in common.prompts_by_id().values() if core.steering_cell_split(p.cell) == "dev"]
cells = sorted({p.cell for p in dev}, key=str)
assert all(c in cells for c in TUNE_CELLS) and len(cells) == 17
train_cells = [c for c in cells if c not in TUNE_CELLS]
split = {p.pid: ("lora_tune" if p.cell in TUNE_CELLS else "lora_train") for p in dev}
by_type = lambda cs: {t: sum(common.case_type(next(p for p in dev if p.cell == c)) == t for c in cs)
                      for t in ("cost below resale", "cost at or above resale", "no cost")}
out = {"rule": "17 development cells: 6 held-out tune cells (hand-picked, balanced by case type: 3 cost "
               "below resale with best offers 2, 4, 1; 1 cost at or above resale; 2 no cost, one per "
               "seller line) and 11 train cells; all four variants (15-18) of each cell",
       "train_cells": [str(c) for c in train_cells], "tune_cells": [str(c) for c in TUNE_CELLS],
       "types_train": by_type(train_cells), "types_tune": by_type(TUNE_CELLS),
       "counts": {"lora_train": sum(v == "lora_train" for v in split.values()),
                  "lora_tune": sum(v == "lora_tune" for v in split.values())},
       "case_split": split}
json.dump(out, open(os.path.join(common.DEMO_DIR, "splits_lora.json"), "w"), indent=1)
print(json.dumps({k: v for k, v in out.items() if k != "case_split"}, indent=1))
