"""Step 8: write demo/teacher_packet.md (no API call; Claude reads it later)."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
from refimpl import core, phase3

P = common.prompts_by_id()
cases = {c["pid"]: c for c in common.load_cases()}
split = common.load_splits()["case_split"]
build_bad = [p for p in common.cases_in("build") if cases[p.pid]["hard_regret"] > 0][:32]
test_cells = sorted({P[pid].cell for pid, s in split.items() if s == "test"}, key=str)
test_one = [next(p for p in common.cases_in("test") if p.cell == c and p.variant == 15) for c in test_cells]
build_all = [p for p in common.cases_in("build") if len(core.oracle_bids(p)) < 5]

def differing(p):
  last = core.SELLER_LINES[p.line].format(C=p.C)
  return [f"buyer: {p.buyer}; seller: {p.seller}",
          f"resale line: \"{p.buyer} can sell the fruit for {p.V} coins back in her home town.\"",
          f"seller's last line: \"{last}\""]

from refimpl import demo as demo_names
ref = demo_names.DemoPrompt(15, 2, "neutral", None)            # demo variant, never 1-14
user, _ = phase3.decision_user_turn(ref,
                                    "{OPENING}", None, core.cyclic_orders()[0])
scaffold = (user.replace(ref.buyer, "{BUYER}").replace(ref.seller, "{SELLER}")
            .replace("for 2 coins back", "for {V} coins back")
            .replace(core.SELLER_LINES["neutral"], "{SELLER_LAST_LINE}"))
L = ["# Teacher packet: why does Gemma 2 9B misprice fruit?", "",
     "You are reading this offline. A language model (Gemma 2 9B instruction-tuned) answers a "
     "multiple-choice buying decision. It plays a buyer who can resell fruit for V coins; the "
     "seller's farm cost is uniform on 1-5 coins unless the seller states it; a seller accepts "
     "any offer at or above their farm cost. The buyer's payoff is V minus the offer if "
     "accepted, otherwise 0.", "",
     "## The shared prompt (identical for every case except the {placeholders})", "",
     "```text", scaffold, "```", "",
     "The five options are shown in five rotated orders; the model's probabilities below are "
     "averaged over the orders.", "",
     f"## Cases where the model's top offer was not a best offer ({len(build_bad)} cases)", "",
     "Only the lines that differ are shown. The model's offer distribution follows each case.", ""]
for p in build_bad:
  pr = cases[p.pid]["probs"]
  L += [f"### {p.pid}"] + [f"- {x}" for x in differing(p)] + [
        "- model's offer probabilities: " + ", ".join(f"{k} coin{'s' if k != '1' else ''}: {pr[k]:.2f}"
                                                      for k in sorted(pr)), ""]
L += ["## What to send back", "",
      "Reply with one JSON object, and nothing else, with these keys:", "",
      "1. `diagnosis`: what systematic errors the model makes, and why you think it makes them.",
      "2. `method`: one paragraph a buyer could follow to choose the best offer in every case "
      "type. It must contain no numbers from any case.",
      "3. `predictions`: for each test case below (prompt lines only; you see no model output), "
      "your prediction of the model's top offer: `\"too_high\"`, `\"too_low\"` or `\"right\"` "
      "(a best offer).",
      "4. `pairs`: for each build case listed under 'Pairs', a good and a bad reasoning "
      "paragraph written from one template, with the offer each concludes: "
      "`{\"pid\", \"good\", \"good_offer\", \"bad\", \"bad_offer\"}`. Good concludes a best offer; "
      "bad concludes a worse one; keep the two within 10% of each other in length; make about "
      "half the bad offers higher than the best and half lower, with the mean concluded "
      "price of the good and bad sets within 0.25 coins.", "",
      "```json", json.dumps({"diagnosis": "...", "method": "...",
                             "predictions": {test_one[0].pid: "too_high"},
                             "pairs": [{"pid": build_all[0].pid, "good": "...", "good_offer": 1,
                                        "bad": "...", "bad_offer": 2}]}, indent=1), "```", "",
      f"## Test cases for predictions ({len(test_one)}, one variant per test cell)", ""]
for p in test_one:
  L += [f"### {p.pid}"] + [f"- {x}" for x in differing(p)] + [""]
L += [f"## Pairs: build cases ({len(build_all)})", ""]
for p in build_all:
  L += [f"- {p.pid}: " + "; ".join(differing(p)[1:])]
open(os.path.join(common.DEMO_DIR, "teacher_packet.md"), "w").write("\n".join(L) + "\n")
json.dump({"build_bad": [p.pid for p in build_bad], "test_predict": [p.pid for p in test_one],
           "pairs_cases": [p.pid for p in build_all]},
          open(os.path.join(common.DEMO_DIR, "teacher_packet_index.json"), "w"), indent=1)
print(len(build_bad), "build cases with regret;", len(test_one), "test cells;", len(build_all), "pair cases")
