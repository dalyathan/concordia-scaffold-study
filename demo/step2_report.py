"""Step 2 analysis (CPU): writes demo/step2.json and prints markdown tables."""
import collections, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import common
from refimpl import core

P = common.prompts_by_id()
cases = {c["pid"]: c for c in common.load_cases()}
split = common.load_splits()["case_split"]
out = os.path.join(common.ROOT, "demo_out")
res = {}

# 1. Regression of the order-averaged expected offer, by case type.
reg = {}
for t in ("cost below resale", "cost at or above resale", "no cost"):
  cs = [c for c in cases.values() if common.case_type(c) == t]
  y = np.array([c["expected_offer"] for c in cs])
  if t == "no cost":
    X = np.column_stack([np.ones(len(cs)), [c["V"] for c in cs]])
    b = np.linalg.lstsq(X, y, rcond=None)[0]
    reg[t] = {"n": len(cs), "intercept": b[0], "slope_V": b[1], "slope_cost": None}
  else:
    X = np.column_stack([np.ones(len(cs)), [c["C"] for c in cs], [c["V"] for c in cs]])
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    yhat = X @ b
    r2 = 1 - np.sum((y - yhat) ** 2) / np.sum((y - y.mean()) ** 2)
    reg[t] = {"n": len(cs), "intercept": b[0], "slope_cost": b[1], "slope_V": b[2], "r2": r2}
res["regression"] = reg

# 2. Variance split: Latin-square ANOVA per case on letter log-probs renormalised
# over the five letters. Row = order, column = option position, treatment = price.
ss = collections.Counter()
per_case = {}
for l in open(f"{out}/plain_per_order.jsonl"):
  r = json.loads(l)
  M = np.zeros((5, 5)); price = np.zeros((5, 5), int)
  for o, (order, lp) in enumerate(zip(r["orders"], r["logp_letters"])):
    v = np.array([lp[x] for x in "abcde"])
    v = v - np.log(np.exp(v - v.max()).sum()) - v.max()          # renormalise over letters
    M[o] = v; price[o] = order
  g = M.mean()
  ss_order = 5 * np.sum((M.mean(1) - g) ** 2)
  ss_pos = 5 * np.sum((M.mean(0) - g) ** 2)
  pm = np.array([M[price == k].mean() for k in core.PRICES])
  ss_price = 5 * np.sum((pm - g) ** 2)
  ss_tot = np.sum((M - g) ** 2)
  ss_res = ss_tot - ss_order - ss_pos - ss_price
  ss.update({"price": ss_price, "position": ss_pos, "order": ss_order, "residual": ss_res})
  per_case[r["pid"]] = ss_price / max(ss_price + ss_pos + ss_res, 1e-12)
tot = ss["price"] + ss["position"] + ss["residual"]
res["variance_split"] = {"share_price": ss["price"] / tot, "share_position": ss["position"] / tot,
                         "share_residual": ss["residual"] / tot,
                         "median_case_share_price": float(np.median(list(per_case.values()))),
                         "cases_position_dominant": int(sum(v < 0.5 for v in per_case.values()))}

# 3. Greedy free text versus first-token top choice.
say = [json.loads(l) for l in open(f"{out}/say.jsonl")]
parsed = [s for s in say if s["offer"] is not None]
agree = [s["offer"] == cases[s["pid"]]["top_offer"] for s in parsed]
res["say"] = {"n": len(say), "parsed": len(parsed), "agree_with_top": int(sum(agree)),
              "agreement": float(np.mean(agree)) if agree else None,
              "regret_of_said_offer_mean": float(np.mean([core.hard_regret(P[s["pid"]], s["offer"]) for s in parsed])),
              "sec_mean": float(np.mean([s["sec"] for s in say]))}

# 4. Cost dial summary.
dial = json.load(open(os.path.join(common.DEMO_DIR, "dial_cost.json")))
res["dial"] = [{"pid": c["pid"], **{s: (d["top"], round(d["expected"], 2), d["best"]) for s, d in c["dial"].items()}}
               for c in dial["cases"]]

# 5. Reworded baseline by split and case type.
rw = {json.loads(l)["pid"]: json.loads(l) for l in open(f"{out}/reworded_cases.jsonl")}
tab = {}
for sp in ("build", "tuning", "test", "all"):
  for t in ("cost below resale", "cost at or above resale", "no cost", "all"):
    ids = [pid for pid in rw if (sp == "all" or split[pid] == sp)
           and (t == "all" or common.case_type(cases[pid]) == t)]
    tab[f"{sp}|{t}"] = {"n": len(ids),
                        "reworded_hard": float(np.mean([rw[i]["hard_regret"] for i in ids])),
                        "reworded_soft": float(np.mean([rw[i]["soft_regret"] for i in ids])),
                        "original_hard": float(np.mean([cases[i]["hard_regret"] for i in ids])),
                        "original_soft": float(np.mean([cases[i]["soft_regret"] for i in ids])),
                        "same_top": float(np.mean([rw[i]["top"] == cases[i]["top_offer"] for i in ids]))}
res["reworded"] = tab
json.dump(res, open(os.path.join(common.DEMO_DIR, "step2.json"), "w"), indent=1, default=float)
print(json.dumps(res, indent=1, default=lambda x: round(float(x), 3)))
