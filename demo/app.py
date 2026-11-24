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
    self.texts = getattr(engine, "texts", None) or {
        "teacher": open(os.path.join(engine.g.OUT, "teacher_method.txt")).read().strip(), "method": __import__("textrows").METHOD}
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
            "prompt_text": __import__("gen_notes").render_notes(c, tuple(order), self.texts[arg] if kind == "text" else None)[0],
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
<div class="row"><button class="go" data-c="plain">Base model</button><button class="go" data-c="method">+ one-sentence rule</button><button class="go" data-c="teacher">+ Claude's lesson</button></div>
<div class="row"><button class="go" data-c="examples">LoRA: Claude's worked examples</button><button class="go" data-c="lesson_adapter">LoRA: Claude's lesson</button><button id="shuffle">Shuffle the options, same brain</button></div>
</footer></div>
<script>
const BRAIN={plain:"Base model",method:"Prompt fix: one-sentence rule",teacher:"Prompt fix: Claude's lesson",examples:"LoRA adapter: Claude's worked examples",lesson_adapter:"LoRA adapter: Claude's lesson"};
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


MARKET = """<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Marketplace haggle: live LoRA demo</title><style>
*{box-sizing:border-box} body{margin:0;font:15px/1.45 -apple-system,Segoe UI,Helvetica,Arial,sans-serif;background:#e9ebee;color:#1c1e21}
.wrap{display:grid;grid-template-columns:minmax(0,1fr) 400px;gap:16px;max-width:1240px;margin:0 auto;padding:16px}
@media(max-width:900px){.wrap{grid-template-columns:1fr}}
.card{background:#fff;border-radius:12px;box-shadow:0 1px 2px rgba(0,0,0,.15);overflow:hidden}
.listing{display:flex;gap:14px;padding:14px;border-bottom:1px solid #e4e6eb;align-items:center}
.thumb{width:84px;height:84px;border-radius:10px;background:linear-gradient(135deg,#dbeafe,#fef3c7);display:grid;place-items:center;font-size:44px;flex:none}
.lt{font-size:18px;font-weight:700} .lm{color:#65676b;font-size:13px} .tag{display:inline-block;background:#e7f3ff;color:#1b74e4;border-radius:6px;padding:1px 7px;font-size:12px;font-weight:600;margin-top:4px}
#chat{height:560px;overflow-y:auto;padding:14px;display:flex;flex-direction:column;gap:8px;background:#fff}
.sys{align-self:center;color:#65676b;font-size:12.5px;text-align:center;max-width:90%;padding:4px 10px}
.sys b{color:#1c1e21}
.m{display:flex;gap:8px;align-items:flex-end;max-width:80%} .m.s{align-self:flex-start} .m.b{align-self:flex-end;flex-direction:row-reverse}
.av{width:28px;height:28px;border-radius:50%;display:grid;place-items:center;font-size:12px;font-weight:700;color:#fff;flex:none}
.s .av{background:#e4a11b} .b .av{background:#1b74e4}
.bub{padding:8px 12px;border-radius:18px;font-size:15px} .s .bub{background:#e4e6eb} .b .bub{background:#1b74e4;color:#fff}
.meta{font-size:11.5px;color:#65676b;margin:2px 10px 0} .b .meta{text-align:right}
.ok{color:#1a7f37;font-weight:700} .no{color:#d1242f;font-weight:700}
.typing .bub{opacity:.7} .dots span{animation:bo 1s infinite;display:inline-block} .dots span:nth-child(2){animation-delay:.15s} .dots span:nth-child(3){animation-delay:.3s} @keyframes bo{50%{transform:translateY(-3px)}}
.dev{background:#0f1115;color:#e8eaed;padding:14px;border-radius:12px;font-size:14px;align-self:start;position:sticky;top:16px}
.dev h2{font-size:15px;margin:0 0 2px} .dev .sub{color:#9aa0a6;font-size:12px} .dev .sub.fake{color:#f87171;font-weight:700}
.lab{color:#9aa0a6;font-size:12px;margin:12px 0 5px;text-transform:uppercase;letter-spacing:.04em}
.btns{display:flex;flex-wrap:wrap;gap:6px}
button{font:inherit;font-size:13px;border-radius:8px;border:1px solid #2c313a;background:#1b1f27;color:#e8eaed;padding:6px 10px;cursor:pointer}
button.on{background:#e8eaed;color:#111;border-color:#e8eaed} button.brain{border-color:#1b74e4} button.brain.on{background:#1b74e4;color:#fff;border-color:#1b74e4}
button:disabled{opacity:.45;cursor:default}
table{width:100%;border-collapse:collapse;font-size:13px} td{padding:4px 2px;border-bottom:1px solid #262a33} td:last-child{text-align:right}
.probs{display:flex;gap:4px;flex-wrap:wrap;margin-top:6px} .p{font-size:12px;border-radius:6px;padding:2px 6px;background:#1b1f27;border:1px solid #2c313a} .p.pick{background:#1b74e4;border-color:#1b74e4} .p.best{outline:2px solid #22c55e}
details{margin-top:10px} summary{cursor:pointer;color:#9aa0a6;font-size:12px} pre{white-space:pre-wrap;font-size:11px;line-height:1.35;background:#000;color:#cfd3d8;padding:8px;border-radius:8px;max-height:260px;overflow:auto}
.note{color:#9aa0a6;font-size:12px;margin-top:8px}
</style></head><body><div class="wrap">
<div class="card"><div class="listing"><div class="thumb">&#x1F6B2;</div><div><div class="lt">Road bike, good condition</div>
<div class="lm" id="lm"></div><span class="tag">AI buyer: Gemma 2 9B</span></div></div><div id="chat"></div></div>
<div class="dev"><h2>Under the hood</h2><div class="sub WHERECLASS">WHERE</div>
<div class="lab">Buyer's brain</div><div class="btns">
<button class="brain" data-c="plain">Base model</button><button class="brain" data-c="method">+ one-sentence rule</button><button class="brain" data-c="teacher">+ Claude's lesson</button>
<button class="brain" data-c="examples">LoRA: Claude's worked examples</button><button class="brain" data-c="lesson_adapter">LoRA: Claude's lesson</button>
<button id="again">Ask again, options shuffled</button></div>
<div class="lab">Deal</div><div class="btns" id="cases">CASES</div>
<div class="lab">Seller says they paid</div><div class="btns" id="costs">COSTS</div>
<div class="lab">Last offer, scored</div><table id="score"><tr><td colspan="2" class="note">Make an offer to see the score.</td></tr></table><div class="probs" id="probs"></div>
<div class="lab">This session</div><table id="tally"></table>
<details><summary>What Gemma actually reads (unchanged from the experiments)</summary><pre id="prompt"></pre></details>
<div class="note">The chat is a reskin for the audience: <b>$10 = 1 coin</b> and the bike is the fruit in the original game. The model's input, the adapters and the scoring are exactly the ones tested. The best offer is calculated from the game's rules, so every offer gets an exact score.</div>
</div></div>
<script>
const D=10, BRAIN={plain:"Base model",method:"+ one-sentence rule",teacher:"+ Claude's lesson",examples:"LoRA: worked examples",lesson_adapter:"LoRA: Claude's lesson"};
const LINES=SELLERLINES;
let st={case:document.querySelector("#cases button").dataset.v,cost:"as written",cond:"plain",key:"",tally:{}};
const chat=document.getElementById("chat"), $=x=>"$"+x*D, money=v=>"$"+(+(v*D).toFixed(2));
const esc=t=>String(t).replace(/[&<>"]/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[m]));
function add(h){chat.insertAdjacentHTML("beforeend",h);chat.scrollTop=chat.scrollHeight;return chat.lastElementChild}
function mark(){document.querySelectorAll("#cases button").forEach(b=>b.classList.toggle("on",b.dataset.v===st.case));
  document.querySelectorAll("#costs button").forEach(b=>b.classList.toggle("on",b.dataset.v===st.cost));
  document.querySelectorAll("button.brain").forEach(b=>b.classList.toggle("on",b.dataset.c===st.cond))}
function sellerSays(d){let t=LINES[d.line_kind][d.wording]; return t.replace("{C}",d.C===null?"":$(d.C))}
function newDeal(d){
  const first=d.seller.split(" ")[0];
  document.getElementById("lm").textContent=`Listed by ${first} · Plano, TX · offers in $${D} steps: ${d.grid.map($).join(", ")}`;
  add(`<div class="sys">You can flip this bike for <b>${$(d.V)}</b>.`+(d.C===null?` ${esc(first)} paid somewhere from ${$(d.prior[0])} to ${$(d.prior[1])}.`:"")+`</div>`);
  add(`<div class="m s"><div class="av">${esc(first[0])}</div><div><div class="bub">Hi! Yes, it's still available.</div></div></div>`);
  add(`<div class="m s"><div class="av">${esc(first[0])}</div><div><div class="bub">${esc(sellerSays(d))}</div></div></div>`);
}
async function offer(cond,shuffle=false){
  st.cond=cond; mark(); document.querySelectorAll("button").forEach(b=>b.disabled=true);
  const ty=add(`<div class="m b typing"><div class="av">AI</div><div><div class="bub"><span class="dots"><span>.</span><span>.</span><span>.</span></span></div></div></div>`);
  try{
    const r=await (await fetch("run",{method:"POST",body:JSON.stringify({case:st.case,cost:st.cost,cond,shuffle})})).json();
    ty.remove(); if(r.error){add(`<div class="sys">Error: ${esc(r.error)}</div>`);return}
    const d=r.deal, key=st.case+"|"+st.cost; if(key!==st.key){st.key=key;newDeal(d)}
    const x=r.rows[r.rows.length-1], best=x.best.split("/").map(Number), first=d.seller.split(" ")[0];
    add(`<div class="m b"><div class="av">AI</div><div><div class="bub">I can do <b>${$(x.offer)}</b>.</div><div class="meta">${esc(BRAIN[cond])}${shuffle?" · shuffled":""} · `+
        (x.right?'<span class="ok">best offer</span>':`<span class="no">leaves ${money(x.lost)} on the table</span>`)+`</div></div></div>`);
    const re=r.reaction;
    if(re.accepted===true) add(`<div class="m s"><div class="av">${esc(first[0])}</div><div><div class="bub">Deal! ${$(x.offer)} it is. When can you pick it up?</div></div></div>`);
    else if(re.accepted===false) add(`<div class="m s"><div class="av">${esc(first[0])}</div><div><div class="bub">Sorry, I paid more than that.</div></div></div>`);
    else add(`<div class="sys">${esc(first)}'s floor is hidden: an offer of ${$(x.offer)} gets accepted ${Math.round(re.p_accept*100)}% of the time.</div>`);
    document.getElementById("score").innerHTML=`<tr><td>Brain</td><td>${esc(BRAIN[cond])}${shuffle?" (shuffled)":""}</td></tr><tr><td>Offer</td><td><b>${$(x.offer)}</b></td></tr>`+
      `<tr><td>Best offer (calculated)</td><td>${best.map($).join(" or ")}</td></tr><tr><td>Right?</td><td class="${x.right?"ok":"no"}">${x.right?"yes":"no"}</td></tr>`+
      `<tr><td>Money left on the table</td><td>${money(x.lost)}</td></tr><tr><td>Confidence</td><td>${Math.round(x.sure*100)}%</td></tr>`+
      `<tr><td>Model time</td><td>${r.sec.toFixed(2)} s${r.averaged_orders>1?` (avg of ${r.averaged_orders} option orders)`:""}</td></tr>`;
    document.getElementById("probs").innerHTML=x.dist.map(([p,q])=>`<span class="p ${p===x.offer?"pick":""} ${best.includes(p)?"best":""}">${$(p)}: ${Math.round(q*100)}%</span>`).join("");
    document.getElementById("prompt").textContent=r.prompt_text;
    const t=st.tally[cond]=st.tally[cond]||{n:0,k:0,lost:0}; t.n++; if(x.right)t.k++; t.lost+=x.lost*D;
    document.getElementById("tally").innerHTML="<tr><td><b>Brain</b></td><td><b>right / offers · avg $ lost</b></td></tr>"+Object.entries(st.tally).map(([c,v])=>`<tr><td>${esc(BRAIN[c])}</td><td>${v.k}/${v.n} · $${(v.lost/v.n).toFixed(1)}</td></tr>`).join("");
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
