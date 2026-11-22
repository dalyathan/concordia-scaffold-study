"""Step 1: split the 140 demo cases by cell and fix the live case (no rescoring)."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402
from refimpl import core  # noqa: E402

prompts = common.prompts_by_id()
cases = {c["pid"]: c for c in common.load_cases()}
split = {pid: common.case_split(p) for pid, p in prompts.items()}
live = next(pid for pid, p in prompts.items()
            if split[pid] == "test" and p.C is not None and p.C < p.V
            and cases[pid]["hard_regret"] > 0)
cells = {s: sorted({str(prompts[pid].cell) for pid in split if split[pid] == s})
         for s in ("build", "tuning", "test")}
out = {"rule": "core.steering_cell_split; dev cells: variants 15-16 build, 17-18 tuning; "
               "test cells: all four variants test",
       "counts": {s: sum(v == s for v in split.values()) for s in ("build", "tuning", "test")},
       "cells": cells, "live_case": live,
       "live_case_rule": "first test case (demo_prompts order) with a stated cost below "
                         "resale and non-zero plain hard regret",
       "case_split": split}
json.dump(out, open(common.SPLITS, "w"), indent=1)
print(json.dumps({k: v for k, v in out.items() if k != "case_split" and k != "cells"}, indent=1))
print({s: len(c) for s, c in cells.items()})
