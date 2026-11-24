"""app.py: a clickable web version of the stage demo (generated cases, display only).

  PYTHONPATH=concordia:. .venv/bin/python demo/app.py              # loads Gemma 2 9B + three LoRA add-ons (GPU)
  PYTHONPATH=concordia:. python demo/app.py --fake                 # no model: random scores, to try the page on a laptop

Buttons call the same engine as demo/floor.py (GenEngine): the same cases, prompts, adapters, readout and regret code.
Every click is appended to logs/app_<time>.jsonl. Nothing here draws a test-set conclusion; the cases are the runbook's
three live cases, chosen by the fixed rule in demo/gen/demo_live_cases.json.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402
import floor  # noqa: E402

import gradio as gr  # noqa: E402
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

GREY, RED, GREEN = "#9aa0a6", "#d93025", "#188038"
LIVE = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "gen", "demo_live_cases.json")))
CASES = {
    "Seller states a cost below resale": LIVE["main"],
    "Seller states no cost": LIVE["backup_no_cost"],
    "Seller's cost is above resale": LIVE["backup_at_or_above"],
}
CONDITIONS = {
    "plain": ("plain", None, "Plain Gemma"),
    "method": ("text", "method", "+ method sentence in the prompt"),
    "teacher": ("text", "teacher", "+ Claude's lesson in the prompt"),
    "examples": ("adapter", "examples", "Add-on ON: trained on Claude's examples"),
    "lesson_adapter": ("adapter", "teacher", "Add-on ON: trained on Claude's lesson"),
}


class FakeEngine:
  """Same cases as GenEngine, random probabilities. For trying the page without a GPU; the header says so."""

  def __init__(self):
    import gen_cases as g
    self.g = g
    self.cases = {}
    for l in open(os.path.join(g.OUT, "cases.jsonl")):
      c = json.loads(l); self.cases[c["cid"]] = c
    cells = {c["cell"]: c for c in json.load(open(os.path.join(g.OUT, "cells.json")))["cells"]}
    for c in self.cases.values():
      c.update({k: cells[c["cell"]][k] for k in ("payoffs", "best_payoff", "best_offers", "best_positions")})
    self.runs = {"examples": "(fake)", "teacher": "(fake)", "method": "(fake)"}

  def score(self, c, condition, orders=None):
    rng = random.Random(hash((c["cid"], condition, str(orders))))
    w = [rng.random() ** 3 for _ in c["grid"]]
    return floor.GenResult([x / sum(w) for x in w], 1.0, 0.01)


class App:
  def __init__(self, engine, fake):
    self.engine, self.fake = engine, fake
    self.lock = threading.Lock()
    os.makedirs(os.path.join(common.ROOT, "logs"), exist_ok=True)
    self.log = open(os.path.join(common.ROOT, "logs", f"app_{time.strftime('%Y%m%d_%H%M%S')}{'_fake' if fake else ''}.jsonl"), "a")

  def score(self, c, kind, arg, orders=None):
    with self.lock:
      t0 = time.perf_counter()
      r = self.engine.score(c, (kind, arg), orders)
      return r, time.perf_counter() - t0

  def summary(self, c, r):
    top = floor.gen_top(r.probs)
    return dict(offer=c["grid"][top], best=c["best_offers"], regret=floor.gen_hard_regret(c, top), soft=floor.gen_soft_regret(c, r.probs))

  def figure(self, panels):
    fig, axes = plt.subplots(1, len(panels), figsize=(5.2 * len(panels), 3.4), sharey=True, squeeze=False)
    for ax, (title, c, r) in zip(axes[0], panels):
      s = self.summary(c, r)
      colors = [GREEN if p in s["best"] else (RED if p == s["offer"] else GREY) for p in c["grid"]]
      ax.bar([str(p) for p in c["grid"]], r.probs, color=colors)
      ax.set_ylim(0, 1.05); ax.set_xlabel("price offered (coins)")
      ax.spines[["top", "right"]].set_visible(False)
      ax.set_title(f"{title}\npicks {s['offer']} (best {'/'.join(map(str, s['best']))}), expected regret {s['soft']:.2f}", fontsize=11)
    axes[0][0].set_ylabel("probability")
    fig.tight_layout()
    return fig

  def prompt_md(self, c):
    lines = floor.gen_prompt_lines(c)
    text = " ".join(lines).replace(">>", "**").replace("<<", "**")
    seller_at = text.find(c["seller"])
    return f"{text[:seller_at].strip()}\n\n> {text[seller_at:].strip()}"

  def record(self, what, c, r, sec):
    s = self.summary(c, r)
    row = [what, s["offer"], "/".join(map(str, s["best"])), round(s["regret"], 2), round(s["soft"], 2), round(sec, 2)]
    self.log.write(json.dumps({"t": time.time(), "case": c["cid"], "what": what, "probs": r.probs, **s}) + "\n")
    self.log.flush()
    return row

  def run(self, case_label, cond_key, cost, shuffle, history):
    base = self.engine.cases[CASES[case_label]]
    c = base if cost == "as written" else floor.gen_with_cost(base, None if cost == "says nothing" else int(cost))
    kind, arg, title = CONDITIONS[cond_key]
    plain, sec_p = self.score(c, "plain", None)
    if shuffle:
      order = list(range(5))
      while tuple(order) in [tuple(o) for o in self.engine.g.orders()]:
        random.shuffle(order)
      r, sec = self.score(c, kind, arg, [tuple(order)])
      title = f"{title}, options shuffled"
      what = f"{CONDITIONS[cond_key][2]} | shuffled {[c['grid'][i] for i in order]}"
    else:
      r, sec = (plain, sec_p) if cond_key == "plain" else self.score(c, kind, arg)
      what = CONDITIONS[cond_key][2]
    if cost != "as written":
      what += f" | seller cost: {cost}"
    panels = [(title, c, r)] if cond_key == "plain" and not shuffle else [("Plain Gemma", c, plain), (title, c, r)]
    s = self.summary(c, r)
    verdict = "best offer" if s["regret"] == 0 else f"leaves {s['regret']:.2f} coins on the table"
    result = f"### Gemma offers **{s['offer']}** ({verdict}). Scored in {sec:.2f} s."
    history = [self.record(what, c, r, sec)] + (history or [])
    return self.prompt_md(c), self.figure(panels), result, history


def build(app, header):
  with gr.Blocks(title="Teaching a small open model to haggle") as ui:
    gr.Markdown(header)
    history = gr.State([])
    case = gr.Radio(list(CASES), value=list(CASES)[0], label="Case")
    cost = gr.Radio(["as written", "1", "2", "3", "4", "says nothing"], value="as written", label="What the seller says the farm charged")
    prompt = gr.Markdown()
    with gr.Row():
      b_plain = gr.Button("Plain Gemma", variant="secondary")
      b_shuffle = gr.Button("Shuffle the options")
    gr.Markdown("**Fixes**")
    with gr.Row():
      b_method = gr.Button("Add the method sentence")
      b_teacher = gr.Button("Add Claude's lesson")
      b_ex = gr.Button("Add-on ON: Claude's examples", variant="primary")
      b_lesson = gr.Button("Add-on ON: Claude's lesson")
      b_off = gr.Button("Add-on OFF")
    result = gr.Markdown()
    plot = gr.Plot()
    table = gr.Dataframe(headers=["what", "offer", "best", "regret", "expected regret", "seconds"], label="Every click, newest first",
                         interactive=False, wrap=True)
    last = gr.State("plain")

    def go(cond_key, shuffle=False):
      def f(case_label, cost_v, hist):
        p, fig, res, hist = app.run(case_label, cond_key, cost_v, shuffle, hist)
        return p, fig, res, hist, hist, cond_key
      return f

    io = dict(inputs=[case, cost, history], outputs=[prompt, plot, result, history, table, last])
    b_plain.click(go("plain"), **io)
    b_off.click(go("plain"), **io)
    b_method.click(go("method"), **io)
    b_teacher.click(go("teacher"), **io)
    b_ex.click(go("examples"), **io)
    b_lesson.click(go("lesson_adapter"), **io)
    b_shuffle.click(lambda c, k, h, last_key: go(last_key, True)(c, k, h), inputs=[case, cost, history, last],
                    outputs=[prompt, plot, result, history, table, last])
    for ctl in (case, cost):
      ctl.change(lambda c, k, h, last_key: go(last_key)(c, k, h), inputs=[case, cost, history, last],
                 outputs=[prompt, plot, result, history, table, last])
    ui.load(go("plain"), **io)
  return ui


def main():
  ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
  ap.add_argument("--fake", action="store_true", help="no model: random scores (to try the page without a GPU)")
  ap.add_argument("--port", type=int, default=7860)
  ap.add_argument("--share", action="store_true", help="also open a temporary public gradio.live link")
  args = ap.parse_args()
  if args.fake:
    engine, where = FakeEngine(), "**FAKE SCORES: no model loaded.** This only shows the page layout."
  else:
    engine = floor.GenEngine("9b")
    import torch
    where = f"Running live: Gemma 2 9B with three LoRA add-ons on {torch.cuda.get_device_name(0)}."
  header = (
      "# Teaching a small open model to haggle\n"
      "Gemma 2 9B is the buyer. It can resell the item for the amount shown and picks one of five prices. The seller accepts any offer "
      "at or above their cost. **Regret** is the coins left on the table compared with the best offer; zero is perfect. "
      "Green bar: best offer. Red bar: Gemma's pick.\n\n" + where)
  build(App(engine, args.fake), header).queue(default_concurrency_limit=1).launch(server_name="0.0.0.0", server_port=args.port,
                                                                                share=args.share)


if __name__ == "__main__":
  main()
