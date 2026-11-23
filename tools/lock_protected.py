"""Write/verify harness/protected/LOCK.json. `--write` is for use ONLY with a DECISIONS.md entry naming the new hashes."""
import hashlib, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDIR = os.path.join(ROOT, "harness", "protected")
LOCK = os.path.join(PDIR, "LOCK.json")


def hashes():
  out = {}
  for dp, _, fs in os.walk(PDIR):
    for f in sorted(fs):
      if f.endswith(".py"):
        p = os.path.join(dp, f)
        out[os.path.relpath(p, ROOT)] = hashlib.sha256(open(p, "rb").read()).hexdigest()
  return dict(sorted(out.items()))


def decision_lines():
  p = os.path.join(ROOT, "DECISIONS.md")
  return open(p).read().splitlines() if os.path.exists(p) else []


def unexplained():
  """Protected files whose CURRENT sha256 is not registered in DECISIONS.md as a line `PROTECTED <path> sha256 <hash>`.
  (LOCK.json is only a convenience copy: editing it does not help, DECISIONS.md is the authority.)"""
  lines = decision_lines()
  return [(f, h) for f, h in hashes().items() if f"PROTECTED {f} sha256 {h}" not in "\n".join(lines)]


if __name__ == "__main__":
  if "--write" in sys.argv:
    json.dump(hashes(), open(LOCK, "w"), indent=1)
    print("Paste into DECISIONS.md with the reason for the change:")
    for f, h in hashes().items():
      print(f"PROTECTED {f} sha256 {h}")
  else:
    bad = unexplained(); print("OK" if not bad else bad); sys.exit(1 if bad else 0)
