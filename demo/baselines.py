"""Step 6: offline baselines fitted on the tuning cases (plain distributions only):
constant shift (analysis.tilt, best beta), constant offer (analysis.attractor,
lam = 1, each price), shrink to the middle (analysis.flatten, best lam).
Writes demo/baselines.json."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import common
from refimpl import analysis, core

P = common.prompts_by_id()
cases = {c["pid"]: c for c in common.load_cases()}
tuning = common.cases_in("tuning")
base = {p.pid: {int(k): v for k, v in cases[p.pid]["probs"].items()} for p in tuning}


def summarise(fn):
  """Mean over cells of soft regret, and of hard regret of the top offer."""
  soft, hard = {}, {}
  for p in tuning:
    d = fn(base[p.pid])
    top = max(core.PRICES, key=lambda k: (d[k], -k))
    soft[p.pid], hard[p.pid] = core.soft_regret(p, d), core.hard_regret(p, top)
  cm = lambda x: float(np.mean(list(analysis.cell_means(x, tuning).values())))
  by = {}
  for t in ("cost below resale", "cost at or above resale", "no cost"):
    ids = [p for p in tuning if common.case_type(p) == t]
    by[t] = float(np.mean([soft[p.pid] for p in ids]))
  return {"soft": cm(soft), "hard": cm(hard), "soft_by_type": by}


out = {"plain": summarise(lambda d: d)}
betas = np.round(np.arange(-6, 6.001, 0.05), 2)
b = min(betas, key=lambda x: (summarise(lambda d: analysis.tilt(d, x))["soft"], abs(x)))
out["constant_shift"] = {"beta": float(b), **summarise(lambda d: analysis.tilt(d, b))}
out["constant_offer"] = {str(k): summarise(lambda d, k=k: analysis.attractor(d, k, 1.0)) for k in core.PRICES}
kbest = min(core.PRICES, key=lambda k: out["constant_offer"][str(k)]["soft"])
out["constant_offer_best"] = {"offer": kbest, **out["constant_offer"][str(kbest)]}
lams = np.round(np.arange(0, 1.0001, 0.02), 2)
lb = min(lams, key=lambda x: (summarise(lambda d: analysis.flatten(d, x))["soft"], x))
out["shrink_to_middle"] = {"lam": float(lb), **summarise(lambda d: analysis.flatten(d, lb))}
json.dump(out, open(os.path.join(common.DEMO_DIR, "baselines.json"), "w"), indent=1)
print("| Baseline (fitted on tuning cases) | Parameter | Soft regret (cell mean) | Hard regret | cost < resale | cost ≥ resale | no cost |")
print("| --- | --- | --- | --- | --- | --- | --- |")
def line(name, par, d):
  bt = d["soft_by_type"]
  print(f"| {name} | {par} | {d['soft']:.3f} | {d['hard']:.3f} | {bt['cost below resale']:.3f} | "
        f"{bt['cost at or above resale']:.3f} | {bt['no cost']:.3f} |")
line("plain", "—", out["plain"])
line("constant shift (tilt)", f"beta = {out['constant_shift']['beta']:+.2f}", out["constant_shift"])
for k in core.PRICES:
  line(f"constant offer {k}", "lam = 1", out["constant_offer"][str(k)])
line("shrink to the middle (flatten)", f"lam = {out['shrink_to_middle']['lam']:.2f}", out["shrink_to_middle"])
