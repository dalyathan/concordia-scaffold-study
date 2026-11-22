"""Choose the tuning grid from demo_out/dose_scan.json by a fixed rule; write
demo/tune_grid.json.

Position mode: the one where the positive control "cheap" lowers the expected offer
most at any coherent setting (letter mass >= 0.9 x plain). Ties go to "p1".
Fractions: in that mode, f_min = the smallest scanned fraction at which cheap lowers
the expected offer by >= 0.25 coins while coherent (at any scanned layer; L* = that
layer, ties to the larger decrease); f_max = the largest scanned fraction at which
cheap at L* stays coherent. Four roughly geometric values from f_min to f_max
(rounded to two significant figures). If f_max = f_min, four geometric values from
f_min / 4 to f_min. If cheap never lowers the offer by 0.25 while coherent: 0.25,
0.5, 1.0, 2.0, and the positive control is recorded as failed. Layers stay 6-24
(7 layers): 7 x 4 + no steering = 29 points."""
import json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

COHERENT, TARGET = 0.9, 0.25
scan = json.load(open(os.path.join(common.ROOT, "demo_out", "dose_scan.json")))
cheap = [r for r in scan["rows"] if r["vector"] == "cheap"]
coh = [r for r in cheap if r["mass_ratio"] >= COHERENT]
best_by_mode = {m: max((-r["d_expected"] for r in coh if r["mode"] == m), default=float("-inf"))
                for m in scan["modes"]}
mode = max(scan["modes"], key=lambda m: (best_by_mode[m], m == "p1"))
hits = [r for r in coh if r["mode"] == mode and -r["d_expected"] >= TARGET]
sig2 = lambda x: float(f"{x:.2g}")
if hits:
  first = min(hits, key=lambda r: (r["fraction"], r["d_expected"]))
  L, f_min = first["layer"], first["fraction"]
  f_max = max(r["fraction"] for r in coh if r["mode"] == mode and r["layer"] == L)
  lo, hi = (f_min, f_max) if f_max > f_min else (f_min / 4, f_min)
  fractions = [sig2(lo * (hi / lo) ** (i / 3)) for i in range(4)]
  ok, note = True, (f"cheap lowers the expected offer by {-first['d_expected']:.2f} coins at layer {L}, "
                    f"fraction {f_min} (mass ratio {first['mass_ratio']:.2f}); largest coherent fraction "
                    f"at layer {L}: {f_max}")
else:
  L, f_min, f_max = None, None, None
  fractions = [0.25, 0.5, 1.0, 2.0]
  ok, note = False, ("POSITIVE CONTROL FAILED: cheap never lowered the expected offer by 0.25 coins "
                     "while coherent in either position mode; default fractions used")
layers = [6, 9, 12, 15, 18, 21, 24]
grid = {"mode": mode, "fractions": fractions, "layers": layers, "n_points": 1 + len(layers) * len(fractions),
        "positive_control_ok": ok, "note": note, "best_cheap_decrease_by_mode": best_by_mode,
        "reference_layer": L, "f_min": f_min, "f_max": f_max,
        "rule": __doc__.split("\n\n", 1)[1].strip()}
assert grid["n_points"] <= 30
json.dump(grid, open(os.path.join(common.DEMO_DIR, "tune_grid.json"), "w"), indent=1)
print(json.dumps({k: v for k, v in grid.items() if k != "rule"}, indent=1))
