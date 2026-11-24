"""app.py: a clickable web page for the stage demo (generated cases, display only). Standard library only: no extra packages,
so the locked GPU environment is not touched.

  PYTHONPATH=concordia:. .venv/bin/python demo/app.py            # loads Gemma 2 9B + three LoRA adapters (GPU); http://localhost:7860
  PYTHONPATH=concordia:. python demo/app.py --fake               # no model: random scores, to try the page on a laptop

Buttons call the same engine as demo/floor.py (GenEngine): the same cases, prompts, adapters, readout and scoring code.
Every click is appended to logs/app_<time>.jsonl. Nothing here draws a test-set conclusion; the cases are the runbook's
three live cases, chosen by the fixed rule in demo/gen/demo_live_cases.json.
"""
from __future__ import annotations

import argparse
import html
import json
import os
import random
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402
import floor  # noqa: E402

LIVE = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "gen", "demo_live_cases.json")))
CASES = {
    "Seller states a cost below resale": LIVE["main"],
    "Seller states no cost": LIVE["backup_no_cost"],
    "Seller's cost is above resale": LIVE["backup_at_or_above"],
}
COSTS = ["as written", "1", "2", "3", "4", "says nothing"]
CONDITIONS = {
    "plain": ("plain", None, "Base model"),
    "method": ("text", "method", "Prompt fix: one-sentence rule"),
    "teacher": ("text", "teacher", "Prompt fix: Claude's lesson"),
    "examples": ("adapter", "examples", "LoRA adapter: Claude's worked examples"),
    "lesson_adapter": ("adapter", "teacher", "LoRA adapter: Claude's lesson"),
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

  def row(self, title, c, r):
    top = floor.gen_top(r.probs)
    lost = floor.gen_hard_regret(c, top)
    return {"setup": title, "offer": c["grid"][top], "best": "/".join(map(str, c["best_offers"])), "right": lost == 0,
            "lost": round(lost, 2), "sure": round(max(r.probs), 2), "dist": [[p, round(q, 2)] for p, q in zip(c["grid"], r.probs)]}

  def prompt(self, c):
    text = html.escape(" ".join(floor.gen_prompt_lines(c))).replace("&gt;&gt;", "<b>").replace("&lt;&lt;", "</b>")
    at = text.find(html.escape(c["seller"]))
    return {"facts": text[:at].strip(), "seller": text[at:].strip()}

  def run(self, case_label, cond_key, cost, shuffle):
    base = self.engine.cases[CASES[case_label]]
    c = base if cost == "as written" else floor.gen_with_cost(base, None if cost == "says nothing" else int(cost))
    kind, arg, title = CONDITIONS[cond_key]
    plain, sec_p = self.score(c, "plain", None)
    if shuffle:
      order = list(range(5))
      while tuple(order) in [tuple(o) for o in self.engine.g.orders()]:
        random.shuffle(order)
      r, sec = self.score(c, kind, arg, [tuple(order)])
      title = f"{title} (options shuffled: {', '.join(str(c['grid'][i]) for i in order)})"
    else:
      r, sec = (plain, sec_p) if cond_key == "plain" else self.score(c, kind, arg)
    what = title + ("" if cost == "as written" else f" | seller cost: {cost}")
    rows = [self.row(title, c, r)] if cond_key == "plain" and not shuffle else [self.row("Base model", c, plain), self.row(title, c, r)]
    last = rows[-1]
    self.log.write(json.dumps({"t": time.time(), "case": c["cid"], "what": what, "probs": r.probs, **last}) + "\n")
    self.log.flush()
    return {"prompt": self.prompt(c), "rows": rows, "sec": round(sec, 2), "what": what}


PAGE = """<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Teaching a small open model to haggle</title><style>
body{font:16px/1.45 -apple-system,Segoe UI,Helvetica,Arial,sans-serif;max-width:900px;margin:24px auto;padding:0 16px;color:#202124}
h1{font-size:26px;margin:0 0 8px} .note{color:#5f6368} .fake{color:#d93025;font-weight:600}
fieldset{border:1px solid #dadce0;border-radius:8px;margin:14px 0;padding:8px 12px} legend{color:#5f6368;font-size:14px}
label{display:inline-block;margin:4px 12px 4px 0} .case{background:#f8f9fa;border-radius:8px;padding:12px 14px;margin:14px 0}
.seller{border-left:3px solid #dadce0;padding-left:10px;margin-top:8px} .grp{margin:12px 0 4px;font-weight:600}
button{font:inherit;padding:10px 14px;margin:4px 6px 4px 0;border-radius:8px;border:1px solid #dadce0;background:#fff;cursor:pointer}
button.primary{background:#1a73e8;color:#fff;border-color:#1a73e8} button:disabled{opacity:.5}
#head{font-size:20px;margin:18px 0 8px} table{border-collapse:collapse;width:100%;margin:6px 0} th,td{text-align:left;padding:6px 8px;border-bottom:1px solid #eee}
.no{color:#d93025;font-weight:600} .yes{color:#188038;font-weight:600} #log td{font-size:13px;color:#5f6368}
</style></head><body>
<h1>Teaching a small open model to haggle</h1>
<p>Gemma 2 9B is the buyer. It can resell the item for the amount shown and must pick one of five prices. The seller accepts any offer
at or above their cost. The best price can be calculated, so every answer is scored: <b>right</b> or not, and <b>coins lost</b>
compared with the best price.</p><p class="WHERECLASS">WHERE</p>
<fieldset><legend>Case</legend>CASES</fieldset>
<fieldset><legend>What the seller says the farm charged</legend>COSTS</fieldset>
<div class="case" id="prompt"></div>
<div><button data-c="plain">Base model</button><button id="shuffle">Shuffle the options</button></div>
<div class="grp">Prompt fixes</div>
<div><button data-c="method">Add the one-sentence rule</button><button data-c="teacher">Add Claude's lesson</button></div>
<div class="grp">LoRA adapters <span class="note">(no prompt change)</span></div>
<div><button data-c="examples" class="primary">Adapter ON: Claude's worked examples</button><button data-c="lesson_adapter">Adapter ON: Claude's lesson</button><button data-c="plain">Adapter OFF</button></div>
<div id="head"></div><table id="res"></table><div id="dist" class="note"></div>
<h3>Every click, newest first</h3><table id="log"></table>
<script>
let cond="plain";
const val=n=>document.querySelector(`input[name=${n}]:checked`).value;
async function go(c,shuffle=false){
  cond=c; document.querySelectorAll("button").forEach(b=>b.disabled=true); document.getElementById("head").textContent="Scoring...";
  try{
    const r=await (await fetch("run",{method:"POST",body:JSON.stringify({case:val("case"),cost:val("cost"),cond:c,shuffle})})).json();
    if(r.error){document.getElementById("head").textContent="Error: "+r.error;return}
    document.getElementById("prompt").innerHTML=r.prompt.facts+'<div class="seller">'+r.prompt.seller+"</div>";
    const last=r.rows[r.rows.length-1];
    document.getElementById("head").innerHTML=`Gemma offers <b>${last.offer}</b>: `+(last.right?'<span class="yes">the best price</span>':`<span class="no">loses ${last.lost.toFixed(2)} coins</span> vs the best price`)+` <span class="note">(${r.sec.toFixed(2)} s)</span>`;
    document.getElementById("res").innerHTML="<tr><th>Setup</th><th>Offer</th><th>Best</th><th>Right?</th><th>Coins lost</th><th>Sure</th></tr>"+
      r.rows.map(x=>`<tr><td>${x.setup}</td><td><b>${x.offer}</b></td><td>${x.best}</td><td class="${x.right?"yes":"no"}">${x.right?"yes":"no"}</td><td>${x.lost.toFixed(2)}</td><td>${Math.round(x.sure*100)}%</td></tr>`).join("");
    document.getElementById("dist").textContent="How sure it is about each price: "+last.dist.map(([p,q])=>`${p}: ${Math.round(q*100)}%`).join(" · ");
    const log=document.getElementById("log");
    log.insertAdjacentHTML("afterbegin",`<tr><td>${r.what}</td><td>offer ${last.offer}</td><td class="${last.right?"yes":"no"}">${last.right?"right":"lost "+last.lost.toFixed(2)}</td><td>sure ${Math.round(last.sure*100)}%</td></tr>`);
  }finally{document.querySelectorAll("button").forEach(b=>b.disabled=false)}
}
document.querySelectorAll("button[data-c]").forEach(b=>b.onclick=()=>go(b.dataset.c));
document.getElementById("shuffle").onclick=()=>go(cond,true);
document.querySelectorAll("input").forEach(i=>i.onchange=()=>go(cond));
go("plain");
</script></body></html>"""


def radios(name, options):
  return "".join(f'<label><input type="radio" name="{name}" value="{html.escape(o)}"{" checked" if i == 0 else ""}> {html.escape(o)}</label>'
                 for i, o in enumerate(options))


def serve(app, where, fake, port):
  page = (PAGE.replace("CASES", radios("case", list(CASES))).replace("COSTS", radios("cost", COSTS))
          .replace("WHERECLASS", "fake" if fake else "note").replace("WHERE", html.escape(where))).encode()

  class H(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype):
      self.send_response(code); self.send_header("Content-Type", ctype); self.send_header("Content-Length", str(len(body)))
      self.end_headers(); self.wfile.write(body)

    def do_GET(self):
      self._send(200, page, "text/html; charset=utf-8") if self.path in ("/", "/index.html") else self._send(404, b"not found", "text/plain")

    def do_POST(self):
      if self.path.rstrip("/") != "/run":
        return self._send(404, b"not found", "text/plain")
      try:
        q = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
        if q["case"] not in CASES or q["cost"] not in COSTS or q["cond"] not in CONDITIONS:
          raise ValueError("bad request")
        out = app.run(q["case"], q["cond"], q["cost"], bool(q.get("shuffle")))
      except Exception as e:  # noqa: BLE001
        out = {"error": f"{type(e).__name__}: {str(e)[:120]}"}
      self._send(200, json.dumps(out).encode(), "application/json")

    def log_message(self, *a):
      pass

  print(f"serving on http://localhost:{port}  ({where})", flush=True)
  ThreadingHTTPServer(("0.0.0.0", port), H).serve_forever()


def main():
  ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
  ap.add_argument("--fake", action="store_true", help="no model: random scores (to try the page without a GPU)")
  ap.add_argument("--port", type=int, default=7860)
  args = ap.parse_args()
  if args.fake:
    engine, where = FakeEngine(), "FAKE SCORES: no model loaded. This only shows the page layout."
  else:
    engine = floor.GenEngine("9b")
    import torch
    where = f"Running live: Gemma 2 9B with three LoRA adapters on {torch.cuda.get_device_name(0)}."
  serve(App(engine, args.fake), where, args.fake, args.port)


if __name__ == "__main__":
  main()
