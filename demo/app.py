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
    "method": ("text", "method", "Prompt fix: written rule"),
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
    self.texts = getattr(engine, "texts", None) or {
        "teacher": open(os.path.join(engine.g.OUT, "teacher_method.txt")).read().strip(), "method": __import__("textrows").METHOD}
    self.lora = {}
    peft = getattr(engine, "peft", None)
    if peft is not None:
      base = sum(p.numel() for n, p in peft.named_parameters() if "lora_" not in n)
      for name in engine.runs:
        self.lora[name] = {"params": sum(p.numel() for n, p in peft.named_parameters() if "lora_" in n and f".{name}." in n), "base": base}
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
    return {"setup": title, "offer": c["grid"][top], "best": "/".join(map(str, c["best_offers"])), "right": c["grid"][top] in c["best_offers"],
            "lost": round(lost, 2), "sure": round(max(r.probs), 2), "dist": [[p, round(q, 2)] for p, q in zip(c["grid"], r.probs)]}

  def warmup(self, prompt_text):
    """The turns sent before the case prompt (system text folded into the first user turn; two short examples)."""
    from refimpl.local_gemma2 import CHOICE_SYSTEM, build_messages
    return build_messages(CHOICE_SYSTEM, prompt_text)[:-1]

  def deal(self, c):
    g = self.engine.g
    coins = lambda n: f"{n} coin" + ("" if n == 1 else "s")
    line = g.SELLER_LINES[c["line"]][c["wording"]].format(C=("" if c["C"] is None else coins(c["C"])))
    return {"buyer": c["buyer"], "seller": c["seller"], "V": c["V"], "grid": c["grid"], "C": c["C"], "prior": c["prior"], "line": line,
            "line_kind": c["line"], "wording": c["wording"]}

  def reaction(self, c, offer):
    """What happens to this offer under the game's own payoff rule (refimpl via gen_cases.payoff)."""
    if c["C"] is not None:
      ok = offer >= c["C"]
      return {"accepted": ok, "p_accept": 1.0 if ok else 0.0, "profit": c["V"] - offer if ok else 0}
    lo, hi = c["prior"]
    p = min(1.0, max(0.0, (offer - lo + 1) / (hi - lo + 1)))
    return {"accepted": None, "p_accept": round(p, 2), "profit": c["V"] - offer}

  def run(self, case_label, cond_key, cost, shuffle):
    base = self.engine.cases[CASES[case_label]]
    c = base if cost == "as written" else floor.gen_with_cost(base, None if cost == "says nothing" else int(cost))
    kind, arg, title = CONDITIONS[cond_key]
    plain, sec_p = self.score(c, "plain", None)
    order = list(self.engine.g.orders()[0])
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
    return {"deal": self.deal(c), "rows": rows, "sec": round(sec, 2), "what": what, "cond": cond_key, "shuffled": shuffle,
            "reaction": self.reaction(c, last["offer"]), "best_profit": round(c["best_payoff"], 2),
            "prompt_text": (pt := __import__("gen_notes").render_notes(c, tuple(order), self.texts[arg] if kind == "text" else None)[0]),
            "warmup": [m["content"] for m in self.warmup(pt)], "lora": self.lora.get(arg) if kind == "adapter" else None,
            "adapter": arg if kind == "adapter" else None, "averaged_orders": 1 if shuffle else len(self.engine.g.orders())}


PAGE = """<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Haggle Lab</title><style>
:root{--bg:#0f1115;--panel:#171a21;--line:#262a33;--text:#e8eaed;--muted:#9aa0a6;--me:#2563eb;--them:#2a2f3a;--good:#22c55e;--bad:#f87171}
*{box-sizing:border-box} body{margin:0;background:var(--bg);color:var(--text);font:15px/1.45 -apple-system,Segoe UI,Helvetica,Arial,sans-serif}
.app{max-width:780px;margin:0 auto;min-height:100vh;display:flex;flex-direction:column}
header{padding:14px 16px;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap;position:sticky;top:0;background:var(--bg);z-index:5}
h1{font-size:19px;margin:0} .sub{color:var(--muted);font-size:13px} .sub.fake{color:var(--bad);font-weight:600}
.score{display:flex;gap:6px;flex-wrap:wrap} .pill{background:var(--panel);border:1px solid var(--line);border-radius:999px;padding:4px 10px;font-size:13px;color:var(--muted)} .pill b{color:var(--text)}
#chat{flex:1;padding:16px;display:flex;flex-direction:column;gap:10px}
.sys{align-self:center;text-align:center;color:var(--muted);font-size:13px;background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:6px 12px;max-width:92%}
.sys b{color:var(--text)}
.msg{display:flex;gap:8px;align-items:flex-end;max-width:86%} .msg.them{align-self:flex-start} .msg.me{align-self:flex-end;flex-direction:row-reverse}
.av{width:32px;height:32px;border-radius:50%;display:grid;place-items:center;font-weight:700;font-size:13px;flex:none}
.them .av{background:#f59e0b;color:#111} .me .av{background:var(--me);color:#fff}
.bub{padding:9px 13px;border-radius:18px} .them .bub{background:var(--them);border-bottom-left-radius:6px} .me .bub{background:var(--me);border-bottom-right-radius:6px;color:#fff}
.who{font-size:12px;color:var(--muted);margin:0 4px 3px} .me .who{text-align:right}
.big{font-size:18px} .brain{display:inline-block;font-size:11px;background:rgba(255,255,255,.18);border-radius:6px;padding:1px 6px;margin-bottom:4px}
.chips{display:flex;gap:4px;margin-top:6px;flex-wrap:wrap} .chip{font-size:12px;border-radius:8px;padding:2px 7px;background:rgba(255,255,255,.12)} .chip.pick{background:#fff;color:var(--me);font-weight:700} .chip.best{outline:2px solid var(--good)}
.verdict{font-size:13px;margin:4px 6px 0;color:var(--muted)} .me .verdict{text-align:right} .ok{color:var(--good);font-weight:700} .no{color:var(--bad);font-weight:700}
.typing .bub{opacity:.75} .dots span{animation:b 1s infinite;display:inline-block} .dots span:nth-child(2){animation-delay:.15s} .dots span:nth-child(3){animation-delay:.3s} @keyframes b{50%{transform:translateY(-4px)}}
footer{position:sticky;bottom:0;background:var(--panel);border-top:1px solid var(--line);padding:10px 12px 12px}
.row{display:flex;gap:6px;flex-wrap:wrap;align-items:center;margin:4px 0} .lab{font-size:12px;color:var(--muted);width:100%;margin-top:4px}
button{font:inherit;font-size:14px;border-radius:999px;border:1px solid var(--line);background:#20242c;color:var(--text);padding:7px 12px;cursor:pointer}
button.on{background:var(--text);color:#111;border-color:var(--text)} button.go{background:var(--me);border-color:var(--me);color:#fff;font-weight:600}
button:disabled{opacity:.45;cursor:default}
@media(max-width:560px){button{font-size:13px;padding:5px 10px} footer{padding:6px 10px 8px} .lab{margin-top:2px} .msg{max-width:94%}}
</style></head><body><div class="app">
<header><div><h1>Haggle Lab</h1><div class="sub WHERECLASS">WHERE</div></div>
<div class="score"><span class="pill">offers <b id="n">0</b></span><span class="pill">right <b id="k">0</b></span><span class="pill">coins lost <b id="lost">0.00</b></span></div></header>
<div id="chat"></div>
<footer>
<div class="lab">Deal</div><div class="row" id="cases">CASES</div>
<div class="lab">What the seller says the farm charged</div><div class="row" id="costs">COSTS</div>
<div class="lab">Make an offer with...</div>
<div class="row"><button class="go" data-c="plain">Base model</button><button class="go" data-c="method">+ written rule</button><button class="go" data-c="teacher">+ Claude's lesson</button></div>
<div class="row"><button class="go" data-c="examples">LoRA: Claude's worked examples</button><button class="go" data-c="lesson_adapter">LoRA: Claude's lesson</button><button id="shuffle">Shuffle the options, same brain</button></div>
</footer></div>
<script>
const BRAIN={plain:"Base model",method:"Prompt fix: written rule",teacher:"Prompt fix: Claude's lesson",examples:"LoRA adapter: Claude's worked examples",lesson_adapter:"LoRA adapter: Claude's lesson"};
let st={case:document.querySelector("#cases button").dataset.v,cost:"as written",cond:"plain",dealKey:"",n:0,k:0,lost:0};
const chat=document.getElementById("chat");
const esc=t=>String(t).replace(/[&<>"]/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[m]));
const ini=n=>n.split(" ").map(w=>w[0]).join("").slice(0,2);
function add(html){chat.insertAdjacentHTML("beforeend",html);window.scrollTo(0,document.body.scrollHeight);return chat.lastElementChild}
function sel(group,v){document.querySelectorAll(`#${group} button`).forEach(b=>b.classList.toggle("on",b.dataset.v===v))}
function newDeal(d){
  add(`<div class="sys">New deal. <b>${esc(d.buyer.split(" ")[0])}</b> (our buyer) can resell for <b>${d.V} coins</b>. Prices on offer: <b>${d.grid.join(" · ")}</b>.`+
      (d.C===null?` The farm's cost is somewhere from ${d.prior[0]} to ${d.prior[1]}.`:"")+`</div>`);
  add(`<div class="msg them"><div class="av">${ini(d.seller)}</div><div><div class="who">${esc(d.seller)} · seller</div><div class="bub">${esc(d.line)}</div></div></div>`);
}
async function offer(cond,shuffle=false){
  st.cond=cond; document.querySelectorAll("button").forEach(b=>b.disabled=true);
  const typing=add(`<div class="msg me typing"><div class="av">AI</div><div><div class="who">Our buyer · Gemma 2 9B</div><div class="bub"><span class="dots"><span>.</span><span>.</span><span>.</span></span></div></div></div>`);
  try{
    const r=await (await fetch("run",{method:"POST",body:JSON.stringify({case:st.case,cost:st.cost,cond,shuffle})})).json();
    typing.remove();
    if(r.error){add(`<div class="sys">Error: ${esc(r.error)}</div>`);return}
    const d=r.deal, key=st.case+"|"+st.cost;
    if(key!==st.dealKey){st.dealKey=key;newDeal(d)}
    const x=r.rows[r.rows.length-1], best=x.best.split("/").map(Number);
    const chips=x.dist.map(([p,q])=>`<span class="chip ${p===x.offer?"pick":""} ${best.includes(p)?"best":""}">${p}: ${Math.round(q*100)}%</span>`).join("");
    add(`<div class="msg me"><div class="av">AI</div><div><div class="who">Our buyer · Gemma 2 9B</div><div class="bub"><div class="brain">${esc(BRAIN[cond])}${shuffle?" · options shuffled":""}</div><div class="big">I'll offer <b>${x.offer} coins</b>.</div><div class="chips">${chips}</div></div>`+
        `<div class="verdict">${x.right?'<span class="ok">✓ best price</span>':`<span class="no">✗ ${x.lost.toFixed(2)} coins lost</span> (best: ${x.best})`} · ${Math.round(x.sure*100)}% sure · ${r.sec.toFixed(2)} s</div></div></div>`);
    const re=r.reaction;
    if(re.accepted===true) add(`<div class="msg them"><div class="av">${ini(d.seller)}</div><div><div class="bub">Deal! ${x.offer} coins it is.</div></div></div>`);
    else if(re.accepted===false) add(`<div class="msg them"><div class="av">${ini(d.seller)}</div><div><div class="bub">No. That's below what I paid.</div></div></div>`);
    else add(`<div class="sys">The seller's cost is hidden, so an offer of ${x.offer} is accepted ${Math.round(re.p_accept*100)}% of the time.</div>`);
    st.n++; if(x.right) st.k++; st.lost+=x.lost;
    document.getElementById("n").textContent=st.n; document.getElementById("k").textContent=st.k; document.getElementById("lost").textContent=st.lost.toFixed(2);
  }finally{document.querySelectorAll("button").forEach(b=>b.disabled=false)}
}
document.querySelectorAll("button[data-c]").forEach(b=>b.onclick=()=>offer(b.dataset.c));
document.getElementById("shuffle").onclick=()=>offer(st.cond,true);
document.querySelectorAll("#cases button").forEach(b=>b.onclick=()=>{st.case=b.dataset.v;sel("cases",st.case);offer("plain")});
document.querySelectorAll("#costs button").forEach(b=>b.onclick=()=>{st.cost=b.dataset.v;sel("costs",st.cost);offer(st.cond)});
sel("cases",st.case); sel("costs",st.cost); offer("plain");
</script></body></html>"""


MARKET = r"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Haggle: what Gemma sees, and what changes</title><style>
*{box-sizing:border-box} body{margin:0;font:15px/1.45 -apple-system,Segoe UI,Helvetica,Arial,sans-serif;background:#e9ebee;color:#1c1e21}
.top{background:#0f1115;color:#e8eaed;padding:10px 16px;position:sticky;top:0;z-index:5}
.top h1{font-size:17px;margin:0;display:inline} .top .sub{color:#9aa0a6;font-size:12px;margin-left:8px} .top .sub.fake{color:#f87171;font-weight:700}
.bar{display:flex;flex-wrap:wrap;gap:6px 14px;align-items:center;margin-top:8px} .grp{display:flex;gap:5px;flex-wrap:wrap;align-items:center}
.gl{color:#9aa0a6;font-size:11px;text-transform:uppercase;letter-spacing:.05em;margin-right:2px}
button{font:inherit;font-size:13px;border-radius:8px;border:1px solid #2c313a;background:#1b1f27;color:#e8eaed;padding:5px 9px;cursor:pointer}
button.on{background:#e8eaed;color:#111;border-color:#e8eaed} button.brain{border-color:#3b82f6} button.brain.on{background:#3b82f6;color:#fff}
button:disabled{opacity:.45;cursor:default}
.wrap{display:grid;grid-template-columns:minmax(300px,0.8fr) minmax(0,1.2fr);gap:14px;max-width:1400px;margin:0 auto;padding:14px}
@media(max-width:960px){.wrap{grid-template-columns:1fr}}
.card{background:#fff;border-radius:12px;box-shadow:0 1px 2px rgba(0,0,0,.15);overflow:hidden}
.listing{display:flex;gap:12px;padding:12px;border-bottom:1px solid #e4e6eb;align-items:center}
.thumb{width:64px;height:64px;border-radius:10px;background:linear-gradient(135deg,#dbeafe,#fef3c7);display:grid;place-items:center;font-size:34px;flex:none}
.lt{font-size:16px;font-weight:700} .lm{color:#65676b;font-size:12.5px}
#chat{height:calc(100vh - 230px);min-height:420px;overflow-y:auto;padding:12px;display:flex;flex-direction:column;gap:7px}
.sys{align-self:center;color:#65676b;font-size:12.5px;text-align:center;max-width:92%;padding:3px 8px} .sys b{color:#1c1e21}
.m{display:flex;gap:7px;align-items:flex-end;max-width:85%} .m.s{align-self:flex-start} .m.b{align-self:flex-end;flex-direction:row-reverse}
.av{width:26px;height:26px;border-radius:50%;display:grid;place-items:center;font-size:11px;font-weight:700;color:#fff;flex:none}
.s .av{background:#e4a11b} .b .av{background:#1b74e4}
.bub{padding:7px 11px;border-radius:17px} .s .bub{background:#e4e6eb} .b .bub{background:#1b74e4;color:#fff}
.meta{font-size:11.5px;color:#65676b;margin:2px 8px 0} .b .meta{text-align:right}
.ok{color:#1a7f37;font-weight:700} .no{color:#d1242f;font-weight:700}
.dots span{animation:bo 1s infinite;display:inline-block} .dots span:nth-child(2){animation-delay:.15s} .dots span:nth-child(3){animation-delay:.3s} @keyframes bo{50%{transform:translateY(-3px)}}
.ctx{display:flex;flex-direction:column;height:calc(100vh - 116px);min-height:520px}
.ch{padding:12px 14px;border-bottom:1px solid #e4e6eb} .ch h2{font-size:15px;margin:0}
.chg{margin-top:6px;border-radius:8px;padding:7px 10px;font-size:13.5px} .chg.none{background:#f0f2f5;color:#65676b} .chg.text{background:#dcfce7;color:#14532d} .chg.lora{background:#ede9fe;color:#3b0764}
.cb{flex:1;overflow-y:auto;padding:10px 14px;position:relative}
.turn{margin:8px 0} .role{font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:#65676b;margin-bottom:3px}
pre{white-space:pre-wrap;font:12.5px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace;margin:0;background:#f7f8fa;border:1px solid #e4e6eb;border-radius:8px;padding:9px 11px}
mark{border-radius:3px;padding:0 2px} mark.fact{background:#fef3c7} mark.add{background:#bbf7d0;display:block;padding:4px 6px;border-left:3px solid #16a34a}
mark.opt{background:transparent} mark.pick{background:#1b74e4;color:#fff} mark.best{outline:2px solid #16a34a}
.read{margin-top:8px;font-size:13px} .read .p{display:inline-block;font:12px ui-monospace,Menlo,monospace;border-radius:6px;padding:2px 6px;margin:2px;background:#f0f2f5} .read .p.pick{background:#1b74e4;color:#fff} .read .p.best{outline:2px solid #16a34a}
.foot{padding:8px 14px;border-top:1px solid #e4e6eb;font-size:12.5px;color:#65676b} .foot table{width:100%;border-collapse:collapse} .foot td{padding:2px 4px}
details summary{cursor:pointer;color:#65676b;font-size:12.5px}
</style></head><body>
<div class="top"><h1>What Gemma sees, and what changes</h1><span class="sub WHERECLASS">WHERE</span>
<div class="bar">
<div class="grp"><span class="gl">Brain</span><button class="brain" data-c="plain">Base model</button><button class="brain" data-c="method">+ written rule</button><button class="brain" data-c="teacher">+ Claude's lesson</button><button class="brain" data-c="examples">LoRA: worked examples</button><button class="brain" data-c="lesson_adapter">LoRA: Claude's lesson</button><button id="again">Shuffle options</button></div>
<div class="grp"><span class="gl">Deal</span><span id="cases">CASES</span></div>
<div class="grp"><span class="gl">Seller paid</span><span id="costs">COSTS</span></div>
</div></div>
<div class="wrap">
<div class="card"><div class="listing"><div class="thumb">&#x1F6B2;</div><div><div class="lt">Road bike, good condition</div><div class="lm" id="lm"></div></div></div><div id="chat"></div></div>
<div class="card ctx"><div class="ch"><h2 id="ctitle">Context sent to Gemma</h2><div id="chg" class="chg none">Make an offer to see the context.</div></div>
<div class="cb">
<details class="turn"><summary>Warm-up turns sent first (system text + 2 tiny examples), same for every brain</summary><div id="warm"></div></details>
<div class="turn"><div class="role">User turn: the case (this is the market Gemma actually reads)</div><pre id="prompt"></pre></div>
<div class="turn"><div class="role">What we read back</div><div class="read" id="read"></div></div>
</div>
<div class="foot"><table id="tally"></table><div>The chat on the left is a reskin for the audience ($10 = 1 coin, bike = fruit). The context on the right is the real input, unchanged from the experiments.</div></div>
</div></div>
<script>
const D=10, BRAIN={plain:"Base model",method:"+ written rule",teacher:"+ Claude's lesson",examples:"LoRA: worked examples",lesson_adapter:"LoRA: Claude's lesson"};
const LINES=SELLERLINES;
let st={case:document.querySelector("#cases button").dataset.v,cost:"as written",cond:"plain",key:"",tally:{}};
const chat=document.getElementById("chat"), $=x=>"$"+x*D, money=v=>"$"+(+(v*D).toFixed(2));
const esc=t=>String(t).replace(/[&<>"]/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[m]));
function add(h){chat.insertAdjacentHTML("beforeend",h);chat.scrollTop=chat.scrollHeight;return chat.lastElementChild}
function mark(){document.querySelectorAll("#cases button").forEach(b=>b.classList.toggle("on",b.dataset.v===st.case));
  document.querySelectorAll("#costs button").forEach(b=>b.classList.toggle("on",b.dataset.v===st.cost));
  document.querySelectorAll("button.brain").forEach(b=>b.classList.toggle("on",b.dataset.c===st.cond))}
function newDeal(d){
  const f=d.seller.split(" ")[0], t=LINES[d.line_kind][d.wording].replace("{C}",d.C===null?"":$(d.C));
  document.getElementById("lm").textContent=`Listed by ${f} · Plano, TX · offers in $${D} steps: ${d.grid.map($).join(", ")}`;
  add(`<div class="sys">New deal. You can flip this bike for <b>${$(d.V)}</b>.`+(d.C===null?` ${esc(f)} paid somewhere from ${$(d.prior[0])} to ${$(d.prior[1])}.`:"")+`</div>`);
  add(`<div class="m b"><div class="av">AI</div><div><div class="bub">Hi! Is the bike still available? What can you tell me about it?</div></div></div>`);
  add(`<div class="m s"><div class="av">${esc(f[0])}</div><div><div class="bub">Yes! Rode it one season, new tires, runs great.</div></div></div>`);
  add(`<div class="m b"><div class="av">AI</div><div><div class="bub">Looks good. Let's talk price.</div></div></div>`);
  add(`<div class="m s"><div class="av">${esc(f[0])}</div><div><div class="bub">${esc(t)}</div></div></div>`);
}
function showContext(r,x,cond,shuffle){
  const d=r.deal, best=x.best.split("/").map(Number);
  document.getElementById("ctitle").textContent="Context sent to Gemma: "+BRAIN[cond]+(shuffle?" (options shuffled)":"");
  const chg=document.getElementById("chg");
  const m=r.prompt_text.match(/Notes:\n([\s\S]*?)\n\nQuestion:/);
  if(r.lora){chg.className="chg lora";chg.innerHTML=`<b>Context: identical to the base model.</b> The change is inside the model: a LoRA adapter with ${(r.lora.params/1e6).toFixed(1)} million trained numbers, ${(100*r.lora.params/r.lora.base).toFixed(2)}% of Gemma's ${(r.lora.base/1e9).toFixed(1)} billion.`}
  else if(cond==="examples"||cond==="lesson_adapter"){chg.className="chg lora";chg.innerHTML="<b>Context: identical to the base model.</b> The change is inside the model: a small rank-4 LoRA adapter."}
  else if(m){chg.className="chg text";chg.innerHTML=`<b>Context: base + ${m[1].split(/\s+/).length} words added</b> (green below). Same model weights.`}
  else {chg.className="chg none";chg.innerHTML="<b>Context: the base case.</b> No notes, no adapter."}
  let h=esc(r.prompt_text);
  if(m){const mm=esc(m[1]); h=h.replace(mm,`<mark class="add">${mm}</mark>`)}
  const fact=t=>{const e=esc(t); h=h.replace(e,`<mark class="fact">${e}</mark>`)};
  fact(d.line); const rs=h.match(/can sell the fruit for \d+ coins back in her home town\./); if(rs) fact(rs[0].replace(/&amp;/g,"&"));
  const pr=h.match(/Sellers at this market pay between \d+ and \d+ coins per kilogram at the farm[^\n]*/); if(pr) fact(pr[0]);
  h=h.replace(/^  \(([a-eA-E])\) (\d+) coins$/gm,(all,l,p)=>`<mark class="opt ${+p===x.offer?"pick":""} ${best.includes(+p)?"best":""}">  (${l}) ${p} coins</mark>`);
  document.getElementById("prompt").innerHTML=h;
  const cb=document.querySelector(".cb"), tgt=document.querySelector("#prompt mark.add")||document.querySelector("#prompt mark.pick");
  if(tgt) cb.scrollTo({top:tgt.offsetTop-cb.offsetTop-cb.clientHeight/3,behavior:"smooth"});
  document.getElementById("warm").innerHTML=r.warmup.map((t,i)=>`<div class="role">${i%2?"Assistant":"User"}</div><pre>${esc(t)}</pre>`).join("");
  document.getElementById("read").innerHTML=`Gemma's probability for each option's letter as the next token, averaged over ${r.averaged_orders} option order${r.averaged_orders>1?"s":""} (no free text is generated):<br>`+
    x.dist.map(([p,q])=>`<span class="p ${p===x.offer?"pick":""} ${best.includes(p)?"best":""}">${p} coins: ${Math.round(q*100)}%</span>`).join("")+
    `<br>Pick: <b>${x.offer} coins</b> · best (calculated): ${x.best} · `+(x.right?'<span class="ok">right</span>':`<span class="no">${x.lost.toFixed(2)} coins left on the table</span>`);
}
async function offer(cond,shuffle=false){
  st.cond=cond; mark(); document.querySelectorAll("button").forEach(b=>b.disabled=true);
  const ty=add(`<div class="m b"><div class="av">AI</div><div><div class="bub"><span class="dots"><span>.</span><span>.</span><span>.</span></span></div></div></div>`);
  try{
    const r=await (await fetch("run",{method:"POST",body:JSON.stringify({case:st.case,cost:st.cost,cond,shuffle})})).json();
    ty.remove(); if(r.error){add(`<div class="sys">Error: ${esc(r.error)}</div>`);return}
    const d=r.deal, key=st.case+"|"+st.cost; if(key!==st.key){st.key=key;newDeal(d)}
    const x=r.rows[r.rows.length-1], f=d.seller.split(" ")[0];
    add(`<div class="m b"><div class="av">AI</div><div><div class="bub">I can do <b>${$(x.offer)}</b>.</div><div class="meta">${esc(BRAIN[cond])}${shuffle?" · shuffled":""} · `+
        (x.right?'<span class="ok">best offer</span>':`<span class="no">leaves ${money(x.lost)} on the table</span>`)+`</div></div></div>`);
    const re=r.reaction;
    if(re.accepted===true) add(`<div class="m s"><div class="av">${esc(f[0])}</div><div><div class="bub">Deal! ${$(x.offer)} it is. When can you pick it up?</div></div></div>`);
    else if(re.accepted===false) add(`<div class="m s"><div class="av">${esc(f[0])}</div><div><div class="bub">Sorry, I paid more than that.</div></div></div>`);
    else add(`<div class="sys">${esc(f)}'s floor is hidden: an offer of ${$(x.offer)} gets accepted ${Math.round(re.p_accept*100)}% of the time.</div>`);
    showContext(r,x,cond,shuffle);
    const t=st.tally[cond]=st.tally[cond]||{n:0,k:0,lost:0}; t.n++; if(x.right)t.k++; t.lost+=x.lost*D;
    document.getElementById("tally").innerHTML="<tr><td><b>This session</b></td><td><b>right / offers</b></td><td><b>avg $ left on the table</b></td></tr>"+
      Object.entries(st.tally).map(([c,v])=>`<tr><td>${esc(BRAIN[c])}</td><td>${v.k}/${v.n}</td><td>$${(v.lost/v.n).toFixed(1)}</td></tr>`).join("");
  }finally{document.querySelectorAll("button").forEach(b=>b.disabled=false)}
}
document.querySelectorAll("button.brain").forEach(b=>b.onclick=()=>offer(b.dataset.c));
document.getElementById("again").onclick=()=>offer(st.cond,true);
document.querySelectorAll("#cases button").forEach(b=>b.onclick=()=>{st.case=b.dataset.v;offer("plain")});
document.querySelectorAll("#costs button").forEach(b=>b.onclick=()=>{st.cost=b.dataset.v;offer(st.cond)});
mark(); offer("plain");
</script></body></html>"""

SELLER_SKIN = {  # display only: the same line type and wording index as the case, retold as a bike sale in dollars
    "neutral": ["Go ahead, tell me what you're thinking of paying for it.", "No rush. What would you like to offer?",
                "Whenever you're ready, tell me what you'd pay."],
    "pressure": ["I've got other people asking. Give me a real offer now or I'll move on.",
                 "I'm busy, so send your best offer right now or I'll go to the next person.",
                 "Time is money. Make a serious offer now or I'll sell it to someone else."],
    "information": ["I'll be straight with you: I paid {C} for it, so keep that in mind.", "Between us, I paid {C} for it. Let that guide your offer.",
                    "Full disclosure, I paid {C} for it. Name your price with that in mind."],
}
COST_LABELS = {"as written": "as written", "1": "$10", "2": "$20", "3": "$30", "4": "$40", "says nothing": "says nothing"}


def radios(name, options):
  return "".join(f'<button data-v="{html.escape(o)}">{html.escape(o)}</button>' for o in options)


def serve(app, where, fake, port):
  page = (PAGE.replace("CASES", radios("case", list(CASES))).replace("COSTS", radios("cost", COSTS))
          .replace("WHERECLASS", "fake" if fake else "").replace("WHERE", html.escape(where))).encode()
  market = (MARKET.replace("CASES", radios("case", list(CASES))).replace("COSTS", "".join(
      f'<button data-v="{html.escape(k)}">{html.escape(v)}</button>' for k, v in COST_LABELS.items()))
            .replace("SELLERLINES", json.dumps(SELLER_SKIN)).replace("WHERECLASS", "fake" if fake else "")
            .replace("WHERE", html.escape(where))).encode()

  class H(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype):
      self.send_response(code); self.send_header("Content-Type", ctype); self.send_header("Content-Length", str(len(body)))
      self.end_headers(); self.wfile.write(body)

    def do_GET(self):
      pages = {"/": market, "/market": market, "/chat": page}
      self._send(200, pages[self.path], "text/html; charset=utf-8") if self.path in pages else self._send(404, b"not found", "text/plain")

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

  print(f"serving on http://localhost:{port}  (Marketplace page; plain chat at /chat)  ({where})", flush=True)
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
