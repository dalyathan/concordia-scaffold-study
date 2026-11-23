#!/usr/bin/env python3
"""Claims checker. CLAIMS.yaml lists each claim made in README.md / reports with its evidence. Fails when
  * a claim has no evidence (kind: none) -- listed as UNBACKED;
  * the claim's `text` is no longer in its file;
  * a number is not in the claim text, or differs from what the evidence gives (rounded to `decimals`);
  * (default) a number in a scanned table section of a file is covered by no claim (a new hand-typed number).
Evidence kinds:
  run_mean   {solver, split, metric, [type], decimals, [scale]}   mean over all run records (runs/) with that solver and split
                                                                   (= over seeds) of the record's per-case recomputed metric
  file_value {path, key (dotted), decimals, [scale]}              a number in a stored JSON file
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


def run_mean(ev, recs):
  sel = [r for r in recs if r["solver"] == ev["solver"] and r["split"] == ev["split"]]
  if not sel:
    raise LookupError(f"no run records for solver={ev['solver']} split={ev['split']}")
  vals = []
  for r in sel:
    rows = [x for x in r["cases"] if not x["planted"] and (not ev.get("type") or x["type"] == ev["type"])]
    key = ev.get("metric", "soft_regret")
    vals.append(sum(x["score"][key] for x in rows) / len(rows))
  return sum(vals) / len(vals), len(sel)


def file_value(ev):
  d = json.load(open(os.path.join(ROOT, ev["path"])))
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
      if shown not in c["text"]:
        problems.append(f"{cid}: number {shown!r} is not in the claim text"); continue
      if ev["kind"] == "none":
        unbacked.append(f"{cid}: {shown} -- {ev['reason']}"); continue
      try:
        v = evidence_value(ev, recs)
      except Exception as e:
        problems.append(f"{cid}: evidence for {shown} unreadable: {e}"); continue
      dec = ev["decimals"]
      want = float(shown.rstrip("%"))
      if abs(round(v, dec) - want) > 10 ** -dec / 2 + 1e-12:
        problems.append(f"{cid}: text says {shown} but evidence gives {v:.6f} (rounded {round(v, dec)})")
      else:
        ok += 1
    if not c.get("numbers") and not c.get("qualitative"):
      problems.append(f"{cid}: no numbers and not marked qualitative: add evidence")
  # scan for uncovered numbers in declared sections
  for scan in yaml.safe_load(open(os.path.join(ROOT, "CLAIMS.yaml"))).get("scan", []):
    text = open(os.path.join(ROOT, scan["file"])).read()
    span = section_spans(text, scan["from"])
    if span is None:
      problems.append(f"scan: heading {scan['from']!r} not found in {scan['file']}"); continue
    for m in NUM.finditer(text, *span):
      if m.group() in scan.get("ignore", []):
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
