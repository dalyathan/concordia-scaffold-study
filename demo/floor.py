"""floor.py: the stage tool for the demo (projector: <= 80 columns, <= 25 lines per
screen, colour only on the regret value: red above 0, green at 0).

  python demo/floor.py --serve [--model 9b|2b]   load once, read commands from stdin
  python demo/floor.py --map                     print the plain failure map
  python demo/floor.py --replay <log>            replay a saved session

Commands (--serve):
  case <id>          score a demo case (plain): prompt lines, bars, offer, regret
  cost <n|none>      re-score the current case with only the stated cost changed
  shuffle            re-score under a new option order; did the pick change?
  plain | text <name> | steer <config.json> | adapter <on|off>
                     switch the condition; plain and current side by side
  say                greedy-generate Gemma's answer text for the current case
  table              the results table (every row kept, including failures)
  dial <cases.json>  batch in a background thread; 'dial show' prints results
  help | quit
Every --serve session writes a replayable log to logs/floor_<time>.jsonl.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import re
import shlex
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402
from refimpl import core, demo  # noqa: E402

WIDTH, SCREEN = 80, 25
RED, GREEN, RESET = "\033[31m", "\033[32m", "\033[0m"
COMMANDS = {"case": 1, "cost": 1, "shuffle": 0, "plain": 0, "text": 1, "steer": 1,
            "adapter": 1, "say": 0, "table": 0, "dial": 1, "help": 0, "quit": 0}


class CommandError(ValueError):
  pass


def parse_command(line: str) -> tuple[str, list[str]]:
  """'case v15-V3-information-C1' -> ('case', ['v15-V3-information-C1']).
  Raises CommandError for unknown commands or wrong arguments."""
  parts = shlex.split(line.strip())
  if not parts:
    raise CommandError("empty command")
  cmd, args = parts[0].lower(), parts[1:]
  if cmd not in COMMANDS:
    raise CommandError(f"unknown command '{cmd}' (try: help)")
  if cmd == "dial" and args == ["show"]:
    return "dial", ["show"]
  if len(args) != COMMANDS[cmd]:
    raise CommandError(f"'{cmd}' takes {COMMANDS[cmd]} argument(s)")
  if cmd == "case":
    try:
      demo.DemoPrompt(*_pid_parts(args[0]))
    except (ValueError, KeyError) as e:
      raise CommandError(f"bad case id: {e}") from None
  if cmd == "cost" and args[0] != "none" and args[0] not in "12345":
    raise CommandError("cost takes 1-5 or none")
  if cmd == "adapter" and args[0] not in ("on", "off"):
    raise CommandError("adapter takes on or off")
  return cmd, args


_PID = re.compile(r"^v(\d+)-V(\d+)-(neutral|pressure|information)(?:-C(\d))?$")


def _pid_parts(pid: str) -> tuple:
  m = _PID.match(pid)
  if not m:
    raise ValueError(f"not a case id: {pid}")
  v, V, line, C = m.groups()
  if (line == "information") != (C is not None):
    raise ValueError(f"not a case id: {pid}")
  return int(v), int(V), line, (int(C) if C else None)


def regret_text(x: float, colour: bool = True) -> str:
  s = f"{x:.2f}"
  if not colour:
    return s
  return (RED if x > 1e-9 else GREEN) + s + RESET


def bars(probs: dict, width: int = 30, label: str = "") -> list[str]:
  out = [label] if label else []
  for k in core.PRICES:
    n = int(round(probs[k] * width))
    out.append(f"{k} coin{'s' if k > 1 else ' '} {'#' * n:<{width}} {probs[k]:4.2f}")
  return out


_ANSI = re.compile(r"\033\[\d+m")


def visible_len(s: str) -> int:
  return len(_ANSI.sub("", s))


def cut(s: str, width: int) -> str:
  """Truncate to `width` visible characters, keeping colour codes intact."""
  out, n, i = [], 0, 0
  while i < len(s) and n < width:
    m = _ANSI.match(s, i)
    if m:
      out.append(m.group()); i = m.end(); continue
    out.append(s[i]); n += 1; i += 1
  res = "".join(out)
  return res + (RESET if "\033[3" in res and not res.endswith(RESET) and RESET not in res[res.rfind("\033[3"):] else "")


def fit(lines: list[str]) -> list[str]:
  return [cut(l, WIDTH) for l in lines]


def side_by_side(a: list[str], b: list[str], gap: int = 2) -> list[str]:
  w = (WIDTH - gap) // 2
  n = max(len(a), len(b))
  a, b = a + [""] * (n - len(a)), b + [""] * (n - len(b))
  out = []
  for x, y in zip(a, b):
    x = cut(x, w)
    out.append(x + " " * (w - visible_len(x) + gap) + cut(y, w))
  return out


def prompt_lines(p: core.Prompt) -> list[str]:
  """Last prompt lines with cost and resale marked >>...<< (no colour)."""
  from refimpl import phase3
  last = core.SELLER_LINES[p.line].format(C=p.C)
  if p.C is not None:
    last = last.replace(f"cost me {p.C} coins", f"cost me >>{p.C} coins<<")
  resale = f"{p.buyer} can sell the fruit for >>{p.V} coins<< back home."
  import textwrap
  return (textwrap.wrap(resale, WIDTH)
          + textwrap.wrap(f'{p.seller} -- "{last}"', WIDTH)
          + [f"{p.buyer} is ready to make an offer."])


class Floor:
  """Session state and command handlers. `engine` scores; injectable for tests."""

  def __init__(self, engine, log_path: str | None = None, colour: bool = True):
    self.engine, self.colour = engine, colour
    self.p: demo.DemoPrompt | None = None
    self.condition = ("plain", None)
    self.rows: list[dict] = []
    self.dial_results: list[dict] = []
    self.dial_thread: threading.Thread | None = None
    self.rng = random.Random(0)
    self.log = open(log_path, "a") if log_path else None
    self.lock = threading.Lock()

  # -------------------------------------------------------------- helpers
  def _need_case(self):
    if self.p is None:
      raise CommandError("no current case (use: case <id>)")

  def _row(self, what: str, p, r, ok: bool = True, note: str = ""):
    hr = core.hard_regret(p, r.top) if ok else None
    row = {"n": len(self.rows) + 1, "case": p.pid, "condition": what,
           "offer": r.top if ok else None, "best": core.oracle_bids(p), "regret": hr,
           "sec": round(r.sec, 2) if ok else None, "ok": ok, "note": note}
    self.rows.append(row)
    return row

  def _panel(self, p, r, title: str) -> list[str]:
    hr = core.hard_regret(p, r.top)
    return bars(r.probs, 20, title) + [
        f"offer {r.top}  best {','.join(map(str, core.oracle_bids(p)))}",
        f"regret {regret_text(hr, self.colour)}  ({r.sec:.1f}s)"]

  def _score(self, p, condition=None, orders=None):
    with self.lock:
      return self.engine.score(p, condition or ("plain", None), orders)

  # ------------------------------------------------------------- commands
  def run(self, line: str) -> list[str]:
    t0 = time.perf_counter()
    try:
      cmd, args = parse_command(line)
      out = getattr(self, f"cmd_{cmd}")(*args)
    except CommandError as e:
      out = [f"error: {e}"]
    except Exception as e:  # noqa: BLE001 - a failure is shown and kept, never fatal
      out = [f"failed: {type(e).__name__}: {str(e)[:60]}"]
      if self.p is not None:
        self.rows.append({"n": len(self.rows) + 1, "case": self.p.pid, "condition": line.strip(),
                          "offer": None, "best": core.oracle_bids(self.p), "regret": None,
                          "sec": None, "ok": False, "note": type(e).__name__})
    out = fit(out + [f"[{time.perf_counter() - t0:.2f}s]"])
    if self.log:
      plain = [re.sub(r"\033\[\d+m", "", l) for l in out]
      self.log.write(json.dumps({"cmd": line.strip(), "out": plain}) + "\n")
      self.log.flush()
    return out

  def cmd_help(self):
    doc = __doc__.splitlines()
    start = next(i for i, l in enumerate(doc) if l.startswith("Commands"))
    end = next(i for i, l in enumerate(doc) if l.startswith("Every --serve"))
    return doc[start:end]

  def cmd_quit(self):
    raise SystemExit(0)

  def cmd_case(self, pid):
    self.p = demo.DemoPrompt(*_pid_parts(pid))
    self.condition = ("plain", None)
    r = self._score(self.p)
    self._row("plain", self.p, r)
    head = f"{self.p.pid}  [{common.case_type(self.p)}]"
    return [head] + prompt_lines(self.p) + [""] + self._panel(self.p, r, "plain")

  def cmd_cost(self, n):
    self._need_case()
    import scoring
    q = scoring.with_cost(self.p, None if n == "none" else int(n))
    r = self._score(q, self.condition)
    self._row(f"cost {n}", q, r)
    return [f"{self.p.pid} with stated cost {n}"] + prompt_lines(q)[-2:] + [""] + \
        self._panel(q, r, f"{self.condition[0]}, cost {n}")

  def cmd_shuffle(self):
    self._need_case()
    base = self._score(self.p, self.condition)
    order = list(core.PRICES)
    while tuple(order) in [tuple(o) for o in core.cyclic_orders()]:
      self.rng.shuffle(order)
    r = self._score(self.p, self.condition, [order])
    self._row(f"shuffle {''.join(map(str, order))}", self.p, r)
    changed = r.top != base.top
    return [f"order (a)-(e) = {order}",
            f"pick under this order: {r.top}; order-averaged pick: {base.top}",
            "PICK CHANGED" if changed else "pick unchanged"] + [""] + \
        self._panel(self.p, r, "this order")

  def _switch(self, condition):
    self._need_case()
    self.condition = condition
    plain = self._score(self.p)
    if condition[0] == "plain":
      return [f"{self.p.pid}: plain"] + self._panel(self.p, plain, "plain")
    r = self._score(self.p, condition)
    name = condition[0] + (f" {condition[1]}" if isinstance(condition[1], str) else "")
    self._row(name, self.p, r)
    return [f"{self.p.pid}: plain vs {name}"] + side_by_side(
        self._panel(self.p, plain, "plain"), self._panel(self.p, r, name[:30]))

  def cmd_plain(self):
    return self._switch(("plain", None))

  def cmd_text(self, name):
    return self._switch(("text", name))

  def cmd_steer(self, path):
    return self._switch(("steer", path))

  def cmd_adapter(self, state):
    self._need_case()
    if state == "on":
      return ["no adapter yet"]
    self.condition = ("plain", None)
    return ["adapter off (plain)"]

  def cmd_say(self):
    self._need_case()
    with self.lock:
      text, k = self.engine.say(self.p)
    import textwrap
    return textwrap.wrap(f"{self.p.buyer} would propose {text.strip()}", WIDTH) + \
        [f"parsed offer: {k}   best: {core.oracle_bids(self.p)}"]

  def cmd_table(self):
    import steercheck
    return steercheck.format_session_table(self.rows, colour=self.colour, max_lines=SCREEN - 2)

  def cmd_dial(self, arg):
    if arg == "show":
      return self._dial_show()
    spec = json.load(open(arg))
    items = spec["cases"] if isinstance(spec, dict) else spec
    if self.dial_thread and self.dial_thread.is_alive():
      raise CommandError("a dial is already running")
    self.dial_results = []
    cond = self.condition
    def work():
      import scoring
      for it in items:
        pid = it if isinstance(it, str) else it["pid"]
        p = demo.DemoPrompt(*_pid_parts(pid))
        if isinstance(it, dict) and "cost" in it:
          p = scoring.with_cost(p, it["cost"])
        try:
          # One order per lock acquisition (about 0.3 s on 9B), so a live command
          # waits for at most one pass, not a whole five-order case.
          per = [self._score(p, cond, [o]).probs for o in core.cyclic_orders()]
          probs = {k: sum(d[k] for d in per) / len(per) for k in core.PRICES}
          top = max(core.PRICES, key=lambda k: (probs[k], -k))
          self.dial_results.append({"p": p, "probs": probs, "top": top})
        except Exception as e:  # noqa: BLE001
          self.dial_results.append({"p": p, "error": repr(e)})
    self.dial_thread = threading.Thread(target=work, daemon=True)
    self.dial_thread.start()
    return [f"dial started: {len(items)} cases under {cond[0]} (dial show)"]

  def _dial_show(self):
    from refimpl import analysis
    done = [d for d in self.dial_results if "probs" in d]
    running = self.dial_thread is not None and self.dial_thread.is_alive()
    if not done:
      return ["dial: no results yet" + (" (running)" if running else "")]
    beta = best_shift([d["probs"] for d in done], [d["p"] for d in done])
    out = [f"dial: {len(done)} done{' (running)' if running else ''}; "
           f"best constant shift beta={beta:+.2f}",
           "case                       offer best   1 2 3 4 5   shift-fit"]
    for d in done[:SCREEN - 4]:
      p = d["p"]
      best = core.oracle_bids(p)
      t = analysis.tilt(d["probs"], beta)
      ft = max(core.PRICES, key=lambda k: (t[k], -k))
      axis = " ".join("B" if k in best and k == d["top"] else "o" if k == d["top"]
                      else "b" if k in best else "." for k in core.PRICES)
      out.append(f"{p.pid:<26} {d['top']:>5} {','.join(map(str, best)):<6} {axis}   {ft}")
    return out


def best_shift(dists, prompts, grid=None) -> float:
  """Constant shift (analysis.tilt) with the beta minimising mean soft regret."""
  import numpy as np
  from refimpl import analysis
  grid = grid if grid is not None else np.round(np.arange(-6, 6.01, 0.05), 2)
  def loss(b):
    return float(np.mean([core.soft_regret(p, analysis.tilt(d, b)) for d, p in zip(dists, prompts)]))
  return float(min(grid, key=lambda b: (loss(b), abs(b))))


class ModelEngine:
  """Live scoring on a loaded model, with result caching."""

  def __init__(self, model_name: str):
    import scoring
    from refimpl import runtime
    from refimpl.local_gemma2 import LocalGemma2
    model, tok = runtime.load_gemma(model_name, "cuda")
    self.lm = LocalGemma2(model, tok)
    self.scoring = scoring
    self.cache: dict = {}
    self.vectors: dict = {}
    self.rows_def = None

  def _notes(self, p, name):
    import textrows
    return textrows.row_text(name, p)

  def score(self, p, condition, orders=None):
    orders = orders or self.scoring.ORDERS
    kind, arg = condition
    notes, steer = None, None
    if kind == "text":
      notes = self._notes(p, arg)
    elif kind == "steer":
      steer = self._steer(arg)
    key = (self.scoring.key(p), kind, arg, tuple(map(tuple, orders)))
    if key not in self.cache:
      self.cache[key] = self.scoring.score(self.lm, p, notes=notes, orders=orders, steer=steer)
    return self.cache[key]

  def _steer(self, path):
    """config: {"name", "layer", "alpha", "vectors"?} for a saved vector (default
    demo_out/vectors.pt), or {"random_seed", "norm", "layer", "alpha"} for a seeded
    Gaussian direction of the given norm (works on any model size)."""
    import torch
    cfg = json.load(open(path))
    if "random_seed" in cfg:
      d = self.lm.model.config.hidden_size
      g = torch.Generator().manual_seed(int(cfg["random_seed"]))
      v = torch.randn(d, generator=g)
      return int(cfg["layer"]), float(cfg["alpha"]) * float(cfg["norm"]) * v / v.norm()
    vpath = os.path.join(common.ROOT, cfg.get("vectors", "demo_out/vectors.pt"))
    if vpath not in self.vectors:
      self.vectors[vpath] = torch.load(vpath)
    v = self.vectors[vpath][cfg["name"]][int(cfg["layer"])]
    return int(cfg["layer"]), float(cfg["alpha"]) * v.float()

  def say(self, p):
    return self.scoring.say(self.lm, p)


def print_map():
  import collections
  import numpy as np
  cases = common.load_cases()
  split = common.load_splits()["case_split"]
  lines = ["PLAIN GEMMA FAILURE MAP (140 demo cases, no notes)",
           "group                       n  hard  soft  wrong  high  low"]
  def row(name, cs):
    hr = [c["hard_regret"] for c in cs]
    return (f"{name:<24}{len(cs):>4}  {np.mean(hr):4.2f}  {np.mean([c['soft_regret'] for c in cs]):4.2f}"
            f"  {np.mean([h > 0 for h in hr]):4.0%}  {sum(c['direction'] == 'too_high' for c in cs):>4}"
            f"  {sum(c['direction'] == 'too_low' for c in cs):>3}")
  lines.append(row("all", cases))
  for t in ("cost below resale", "cost at or above resale", "no cost"):
    lines.append(row(t, [c for c in cases if common.case_type(c) == t]))
  for V in range(2, 7):
    lines.append(row(f"V = {V}", [c for c in cases if c["V"] == V]))
  for C in range(1, 6):
    lines.append(row(f"stated cost {C}", [c for c in cases if c["C"] == C]))
  for s in ("build", "tuning", "test"):
    lines.append(row(f"split {s}", [c for c in cases if split[c["pid"]] == s]))
  print("\n".join(fit(lines[:SCREEN])))


def replay(path):
  print("RECORDED RUN".center(WIDTH, "="))
  for l in open(path):
    rec = json.loads(l)
    print(f"> {rec['cmd']}")
    print("\n".join(rec["out"]))


def main():
  ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
  ap.add_argument("--serve", action="store_true")
  ap.add_argument("--map", action="store_true")
  ap.add_argument("--replay")
  ap.add_argument("--model", default="9b", choices=("9b", "2b"))
  ap.add_argument("--no-colour", action="store_true")
  args = ap.parse_args()
  if args.map:
    return print_map()
  if args.replay:
    return replay(args.replay)
  if not args.serve:
    ap.print_help()
    return
  os.makedirs(os.path.join(common.ROOT, "logs"), exist_ok=True)
  log = os.path.join(common.ROOT, "logs", f"floor_{time.strftime('%Y%m%d_%H%M%S')}_{args.model}.jsonl")
  t = time.time()
  engine = ModelEngine(args.model)
  floor = Floor(engine, log, colour=not args.no_colour)
  print(f"floor: {args.model} loaded in {time.time() - t:.0f}s; log {os.path.relpath(log, common.ROOT)}")
  for line in sys.stdin:
    if not line.strip():
      continue
    print(f"> {line.strip()}")
    try:
      print("\n".join(floor.run(line)), flush=True)
    except SystemExit:
      break


if __name__ == "__main__":
  main()
