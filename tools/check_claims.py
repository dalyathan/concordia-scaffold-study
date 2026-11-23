#!/usr/bin/env python3
"""Claims checker. CLAIMS.yaml lists each claim made in README.md / reports with its evidence. Fails when
  * a claim has no evidence (kind: none) -- listed as UNBACKED;
  * the claim's `text` is no longer in its file;
  * a number is not in the claim text, or differs from what the evidence gives (rounded to `decimals`);
  * (default) a number in a scanned table section of a file is covered by no claim (a new hand-typed number).
Evidence kinds:
  run_mean   {task, model, solver, split, [metric], [type], [scale]}   mean over all run records (runs/) with that task, model, solver and
                                                                   split (= over seeds) of the metric RE-DERIVED here from each case's
                                                                   payoffs and probs (stored scores are not trusted); `n_records` pins the count
  file_value {path, key (dotted), sha256, [scale]}                a number in a stored JSON file whose sha256 is pinned
  decimals are derived from the number as shown in the text ("0.4" is compared at 1 decimal).
  definition {reason}                                             true by the task's own rules, not a measurement
  none       {reason}
Reads run records directly (JSON); re-derives metrics from the per-case rows, not from the stored summary.

  python tools/check_claims.py [--strict] [--list-unbacked]"""
import json, os, re, sys
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def records():
  out = []
  d = os.path.join(ROOT, "runs")
  for dp, _, fs in os.walk(d):
    out += [json.load(open(os.path.join(dp, f))) for f in sorted(fs) if f.endswith(".json")]
  return out


def case_metric(x, key):
  pay, p = x["payoffs"], x["probs"]
  if key == "soft_regret":
    return max(pay) - sum(a * b for a, b in zip(pay, p))
  top = max(range(len(p)), key=lambda i: (p[i], -i))
  return max(pay) - pay[top]


def run_mean(ev, recs):
  sel = [r for r in recs if r["task"] == ev["task"] and r["model"] == ev["model"] and r["solver"] == ev["solver"] and r["split"] == ev["split"]]
  if not sel:
    raise LookupError(f"no run records for {ev['task']}/{ev['model']}/{ev['solver']}/{ev['split']}")
  if "n_records" in ev and len(sel) != ev["n_records"]:
    raise LookupError(f"expected {ev['n_records']} records, found {len(sel)} (a rerun or a removed seed?)")
  vals = []
  for r in sel:
    rows = [x for x in r["cases"] if not x["planted"] and (not ev.get("type") or x["type"] == ev["type"])]
    vals.append(sum(case_metric(x, ev.get("metric", "soft_regret")) for x in rows) / len(rows))
  return sum(vals) / len(vals), len(sel)


def file_value(ev):
  import hashlib
  raw = open(os.path.join(ROOT, ev["path"]), "rb").read()
  if hashlib.sha256(raw).hexdigest() != ev["sha256"]:
    raise LookupError(f"{ev['path']} changed since the claim was written (sha256 differs)")
  d = json.loads(raw)
  for k in ev["key"].split("."):
    d = d[int(k)] if isinstance(d, list) else d[k]
  return float(d)


def evidence_value(ev, recs):
  if ev["kind"] == "run_mean":
    return run_mean(ev, recs)[0] * ev.get("scale", 1)
  if ev["kind"] == "file_value":
    return file_value(ev) * ev.get("scale", 1)
  raise ValueError(ev["kind"])


NUM = re.compile(r"(?<![\w.])\d+(?:\.\d+)?%?")


def section_spans(text, start_heading, until="\n## "):
  i = text.find(start_heading)
  if i < 0:
    return None
  j = text.find(until, i + len(start_heading))
  return (i, len(text) if j < 0 else j)


def main(argv):
  claims = yaml.safe_load(open(os.path.join(ROOT, "CLAIMS.yaml")))["claims"]
  recs = records()
  problems, unbacked, ok = [], [], 0
  covered = {}      # file -> list of (start, end) spans of claim text
  for c in claims:
    cid = c["id"]
    path = os.path.join(ROOT, c["file"])
    text = open(path).read()
    pos = text.find(c["text"])
    if pos < 0:
      problems.append(f"{cid}: claim text not found in {c['file']} (edited? update CLAIMS.yaml)"); continue
    covered.setdefault(c["file"], []).append((pos, pos + len(c["text"])))
    for n in c.get("numbers", []):
      ev = n["evidence"]
      shown = n["shown"]
      if not re.search(r"(?<![\w.])" + re.escape(shown) + r"(?![\w]|\.\d)", c["text"]):
        problems.append(f"{cid}: number {shown!r} is not in the claim text"); continue
      if ev["kind"] == "none":
        unbacked.append(f"{cid}: {shown} -- {ev['reason']}"); continue
      if ev["kind"] == "definition":
        ok += 1; continue            # a definition of the task, not a measurement; the reason is read by reviewers
      try:
        v = evidence_value(ev, recs)
      except Exception as e:
        problems.append(f"{cid}: evidence for {shown} unreadable: {e}"); continue
      dec = len(shown.rstrip("%").split(".")[1]) if "." in shown else 0
      want = float(shown.rstrip("%"))
      if abs(round(v, dec) - want) > 10 ** -dec / 2 + 1e-12:
        problems.append(f"{cid}: text says {shown} but evidence gives {v:.6f} (rounded {round(v, dec)})")
      else:
        ok += 1
    listed = {n["shown"] for n in c.get("numbers", [])}
    for m in NUM.finditer(c["text"]):
      if m.group() not in listed:
        problems.append(f"{cid}: number {m.group()!r} appears in the claim text but has no evidence entry")
    if not c.get("numbers") and not c.get("qualitative"):
      problems.append(f"{cid}: no numbers and not marked qualitative: add evidence")
  # scan for uncovered numbers in declared sections
  for scan in yaml.safe_load(open(os.path.join(ROOT, "CLAIMS.yaml"))).get("scan", []):
    text = open(os.path.join(ROOT, scan["file"])).read()
    span = section_spans(text, scan["from"])
    if span is None:
      problems.append(f"scan: heading {scan['from']!r} not found in {scan['file']}"); continue
    for m in NUM.finditer(text, *span):
      ctx = text[max(0, m.start() - 8):m.end() + 8]
      if any(re.search(rx, ctx) for rx in scan.get("ignore_contexts", [])):
        continue
      if not any(a <= m.start() < b for a, b in covered.get(scan["file"], [])):
        problems.append(f"uncovered number {m.group()!r} in {scan['file']} at char {m.start()} (no claim): "
                        f"...{text[max(0, m.start() - 30):m.end() + 20]!r}")
  print(f"verified numbers: {ok}; unbacked numbers: {len(unbacked)}; problems: {len(problems)}")
  if "--list-unbacked" in argv or "--strict" in argv:
    for u in unbacked:
      print("UNBACKED", u)
  for p in problems:
    print("FAIL", p)
  fail = bool(problems) or ("--strict" in argv and unbacked)
  return 1 if fail else 0


if __name__ == "__main__":
  sys.exit(main(sys.argv[1:]))
