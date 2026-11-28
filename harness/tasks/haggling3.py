"""The haggling task with the targeted experiment's sets (TARGETED_PLAN.md; demo/gen_test3.py), in a separate module so the files frozen
for the test2 look (harness/tasks/haggling.py, harness/task.py) stay byte-identical. Same task name ("haggling"), prompts, payoffs,
orders and planted cases; it only adds splits:

  test3    LOCKED: 120 cells x 2 name variants; harness.evaluate refuses it without the lock token and the owner pin
  pool3    build: 549 cells, name variant 0 (the extra training cells of arms T, R and N come from here, outside select3)
  probe3   build: the 90 pool cells of the failure map
  select3  build: the 30 pool cells of the new arms' early stopping (never an extra training cell)

Cases are read from the committed files only after their sha256 equals demo/gen/test3_fingerprints.json; nothing is rebuilt."""
from __future__ import annotations

import hashlib
import json
import os

from harness.tasks.haggling import GEN_DIR, HagglingTask

FILES = {"test3": ("test3_cases.jsonl", "test3_cells.json"), "pool3": ("pool3_cases.jsonl", "pool3_cells.json")}
COUNTS = {"test3": 240, "pool3": 549, "probe3": 90, "select3": 30}


class Haggling3Task(HagglingTask):
  splits = HagglingTask.splits + ("test3", "pool3", "probe3", "select3")
  locked_splits = HagglingTask.locked_splits + ("test3",)
  FINGERPRINTS = os.path.join(GEN_DIR, "test3_fingerprints.json")

  def _load(self, name):
    fp = json.load(open(self.FINGERPRINTS))["files"]
    out = {}
    for f in FILES[name]:
      raw = open(os.path.join(GEN_DIR, f), "rb").read()
      want = fp[f"demo/gen/{f}"]
      if hashlib.sha256(raw).hexdigest() != want:
        raise RuntimeError(f"demo/gen/{f} differs from its locked fingerprint {want}")
      out[f] = raw
    cases = [json.loads(l) for l in out[FILES[name][0]].decode().splitlines() if l.strip()]
    cells = {c["cell"]: c for c in json.loads(out[FILES[name][1]])["cells"]}
    return cases, cells

  def cases(self, split: str) -> list[dict]:
    if split not in ("test3", "pool3", "probe3", "select3"):
      return super().cases(split)
    cases, cells = self._load("test3" if split == "test3" else "pool3")
    if split in ("probe3", "select3"):
      cases = [c for c in cases if cells[c["cell"]][split[:-1] if split == "probe3" else "select3"]]
    out = [{**c, "split": split} if split in ("probe3", "select3") else c for c in cases]
    if len(out) != COUNTS[split]:
      raise RuntimeError(f"{split}: expected {COUNTS[split]} cases, found {len(out)}")
    return out

  def cell(self, cell_id: str) -> dict:
    """The stored cell (labels, flags) of a test3 or pool3 cell."""
    for name in ("pool3", "test3"):
      cells = self._load(name)[1]
      if cell_id in cells:
        return cells[cell_id]
    raise KeyError(cell_id)


TASK = Haggling3Task
