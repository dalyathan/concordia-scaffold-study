"""Failure map of the demo baseline run (demo_out/cases.jsonl -> markdown tables).

Mean hard regret (of the top offer) and soft regret by resale value V, by seller
line, by stated cost C (information cases), by case type, and overall; the share of
cases with non-zero hard regret; and the direction of wrong top offers (above every
best offer = too much; below every best offer = too little), plus the mean of
(expected offer - mean best offer)."""
import argparse, collections, json
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("--cases", default="demo_out/cases.jsonl")
ap.add_argument("--out", default="demo_out/failure_map.md")
args = ap.parse_args()
cases = [json.loads(l) for l in open(args.cases)]

def kind(c):
  if c["C"] is None:
    return "no information"
  return "stated cost C < V" if c["C"] < c["V"] else "stated cost C >= V"

def table(title, key, order=None):
  groups = collections.defaultdict(list)
  for c in cases:
    groups[key(c)].append(c)
  keys = order or sorted(groups, key=lambda k: (str(type(k)), k))
  rows = [f"### {title}", "",
          "| Group | Cases | Mean hard regret | Mean soft regret | Non-zero hard regret | Too much | Too little | Mean (expected − best offer) |",
          "| --- | --- | --- | --- | --- | --- | --- | --- |"]
  for k in keys:
    g = groups.get(k, [])
    if not g:
      continue
    hr = np.array([c["hard_regret"] for c in g]); sr = np.array([c["soft_regret"] for c in g])
    hi = sum(c["direction"] == "too_high" for c in g); lo = sum(c["direction"] == "too_low" for c in g)
    bias = np.mean([c["expected_offer"] - np.mean(c["best_offers"]) for c in g])
    rows.append(f"| {k} | {len(g)} | {hr.mean():.3f} | {sr.mean():.3f} | {np.mean(hr > 1e-9):.0%} "
                f"| {hi} | {lo} | {bias:+.2f} |")
  return "\n".join(rows) + "\n"

out = ["# Demo failure map (plain Gemma, no Notes, 140 demo cases)", "",
       "Hard regret is that of the top offer (argmax of p(k) averaged over the five option orders); "
       "soft regret uses the averaged p(k). Too much / too little: top offer above every best offer / "
       "below every best offer. Regret is in coins.", ""]
out.append(table("Overall", lambda c: "all cases"))
out.append(table("By resale value V", lambda c: f"V = {c['V']}", [f"V = {v}" for v in range(2, 7)]))
out.append(table("By seller line", lambda c: c["line"], ["neutral", "pressure", "information"]))
out.append(table("By stated cost C (information cases)",
                 lambda c: f"C = {c['C']}" if c["C"] is not None else None,
                 [f"C = {k}" for k in range(1, 6)]))
out.append(table("By case type", kind, ["no information", "stated cost C < V", "stated cost C >= V"]))
out.append(table("By V and seller line", lambda c: f"V = {c['V']}, {c['line']}",
                 [f"V = {v}, {l}" for v in range(2, 7) for l in ("neutral", "pressure", "information")]))
nz = np.mean([c["hard_regret"] > 1e-9 for c in cases])
hi = sum(c["direction"] == "too_high" for c in cases); lo = sum(c["direction"] == "too_low" for c in cases)
top = collections.Counter(c["top_offer"] for c in cases)
summary = {"n_cases": len(cases), "share_nonzero_hard_regret": float(nz),
           "at_least_30pct_nonzero": bool(nz >= 0.30), "too_high": hi, "too_low": lo,
           "mean_hard_regret": float(np.mean([c["hard_regret"] for c in cases])),
           "mean_soft_regret": float(np.mean([c["soft_regret"] for c in cases])),
           "top_offer_counts": {str(k): top[k] for k in sorted(top)},
           "mean_letter_mass": float(np.mean([c["letter_mass"] for c in cases])),
           "order_consistent_top_offer": float(np.mean([len(set(c["top_offer_by_order"])) == 1 for c in cases]))}
out += ["### Summary", "", "```json", json.dumps(summary, indent=1), "```", ""]
open(args.out, "w").write("\n".join(out))
json.dump(summary, open(args.out.replace(".md", ".json"), "w"), indent=1)
print("\n".join(out))
