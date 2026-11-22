"""Markdown tables from demo_out/steer_checks.json -> demo_out/steer_checks.md (CPU)."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

res = json.load(open(os.path.join(common.ROOT, "demo_out", "steer_checks.json")))
pl = res["plain_eval12"]
L = [f"# Steering checks a-c (12 held-out tune cases; vectors built from the 11 train cells)", "",
     f"Plain on the 12 cases: soft regret {pl['soft_regret']:.3f}, expected offer {pl['expected']:.3f}, letter mass {pl['mass']:.2f}. "
     "Each entry: change in expected offer / renormalised soft regret / letter mass relative to plain. **Bold** = coherent (mass >= 0.9 x plain).", ""]
def grid(rows, title, key=None):
  rs = [r for r in rows if key is None or r["vector"] == key]
  fr = sorted({r["fraction"] for r in rs}); ls = sorted({r["layer"] for r in rs})
  L.extend([f"## {title}", "", "| Layer | " + " | ".join(f"f = {f}" for f in fr) + " |", "| --- | " + " | ".join("---" for _ in fr) + " |"])
  for l in ls:
    cells = []
    for f in fr:
      r = next(x for x in rs if x["layer"] == l and x["fraction"] == f)
      s = f"{r['d_expected']:+.3f} / {r['soft_regret']:.2f} / {r['mass_ratio']:.2f}"
      cells.append(f"**{s}**" if r["mass_ratio"] >= 0.9 else s)
    L.append(f"| {l} | " + " | ".join(cells) + " |")
  L.append("")
if "a" in res: grid(res["a"], "(a) Per-order cheap vectors, each order steered with its own")
if "b" in res:
  grid(res["b"], "(b) Order-averaged cheap, layers 27-39", "cheap")
  grid(res["b"], "(b) Order-averaged sentence (method minus neutral), layers 27-39", "sentence")
if "c" in res:
  c = res["c"]; m = c["method_text"]
  L += ["## (c) Upper bound: patch the method-text P1 residual into the plain run, one layer at a time", "",
        f"Plain {pl['soft_regret']:.3f}; method text in the prompt {m['soft_regret']:.3f} (mass x{m['mass_ratio']:.2f}). "
        f"Layer-41 patch reproduces the method-text distribution exactly: worst difference {c['last_layer_exact_diff']}.", "",
        "| Layer | Soft regret | Change in expected offer | Letter mass vs plain |", "| --- | --- | --- | --- |"]
  for r in c["patched"]:
    if r["layer"] % 3 == 0 or r["layer"] >= 38:
      L.append(f"| {r['layer']} | {r['soft_regret']:.3f} | {r['d_expected']:+.3f} | {r['mass_ratio']:.2f} |")
  L.append("")
if "controls" in res:
  L += ["## Controls at each check's best setting (largest decrease among coherent settings)", "",
        "| Check | Best setting | Vector: dE / regret / mass | Negated: dE / regret / mass | 3 random directions: dE |", "| --- | --- | --- | --- | --- |"]
  for k, v in res["controls"].items():
    b, n = v["best"], v["negated"]
    L.append(f"| {k} | L{b['layer']} f{b['fraction']}{'' if b['coherent'] else ' (incoherent)'} | {b['d_expected']:+.3f} / {b['soft_regret']:.2f} / {b['mass_ratio']:.2f} | "
             f"{n['d_expected']:+.3f} / {n['soft_regret']:.2f} / {n['mass_ratio']:.2f} | " + ", ".join(f"{r['d_expected']:+.3f}" for r in v["random"]) + " |")
  L.append("")
if "extras" in res:
  ex = res["extras"]
  L += ["## Top-10 P1 tokens (option order 0, one case) and steered free text", ""]
  t0 = ex["top10"][0]
  for t in ex["top10"][:3]:
    L.append(f"- {t['pid']}, {t['setting']}: plain {t['plain']}  ->  steered {t['steered']}")
  L += ["", f"Steered `say` ({ex['say_setting']}):", "", "| Case | Best | Plain says | Steered says |", "| --- | --- | --- | --- |"]
  for s in ex["say"]:
    L.append(f"| {s['pid']} | {s['best_offers']} | {s['plain'][0].strip()[:40]} ({s['plain'][1]}) | {s['steered'][0].strip()[:40]} ({s['steered'][1]}) |")
open(os.path.join(common.ROOT, "demo_out", "steer_checks.md"), "w").write("\n".join(L) + "\n")
print("\n".join(L))
