"""Write/verify harness/protected/LOCK.json. `--write` is for use ONLY with a DECISIONS.md entry naming the new hashes."""
import hashlib, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDIR = os.path.join(ROOT, "harness", "protected")
LOCK = os.path.join(PDIR, "LOCK.json")


# Besides harness/protected/**: the code that averages options, chooses what is looked at, and checks the results.
EXTRA = ("harness/evaluate.py", "harness/task.py", "tools/recompute.py", "tools/check_claims.py", "tools/lock_protected.py")


def hashes():
  out = {}
  for dp, _, fs in os.walk(PDIR):
    for f in sorted(fs):
      if f.endswith(".py"):
        p = os.path.join(dp, f)
        out[os.path.relpath(p, ROOT)] = hashlib.sha256(open(p, "rb").read()).hexdigest()
  for f in EXTRA:
    p = os.path.join(ROOT, f)
    if os.path.exists(p):
      out[f] = hashlib.sha256(open(p, "rb").read()).hexdigest()
  return dict(sorted(out.items()))


def decision_lines():
  p = os.path.join(ROOT, "DECISIONS.md")
  return open(p).read().splitlines() if os.path.exists(p) else []


def unexplained():
  """Protected files whose CURRENT sha256 is not registered in DECISIONS.md as a line `PROTECTED <path> sha256 <hash>`.
  (LOCK.json is only a convenience copy: editing it does not help, DECISIONS.md is the authority.)"""
  newest = {}
  for l in decision_lines():           # the LAST registration of each path wins: going back to an older hash needs a new line
    m = re.match(r"PROTECTED (\S+) sha256 ([0-9a-f]{64})\s*$", l.strip())
    if m:
      newest[m.group(1)] = m.group(2)
  return [(f, h) for f, h in hashes().items() if newest.get(f) != h]


def pin_mismatches(ref):
  """Protected files that differ from their content at git ref `ref` (a tag the OWNER created and protects on the remote).
  Returns [] when all equal; raises if the ref cannot be read (an unreadable pin is a failure, not a pass)."""
  import subprocess
  bad = []
  for f, h in hashes().items():
    try:
      blob = subprocess.check_output(["git", "-C", ROOT, "show", f"{ref}:{f}"], stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
      raise RuntimeError(f"cannot read {f} at {ref}: {e.stderr.decode()[:120]}")
    if hashlib.sha256(blob).hexdigest() != h:
      bad.append((f, h))
  return bad


if __name__ == "__main__":
  if "--write" in sys.argv:
    json.dump(hashes(), open(LOCK, "w"), indent=1)
    print("Paste into DECISIONS.md with the reason for the change:")
    for f, h in hashes().items():
      print(f"PROTECTED {f} sha256 {h}")
  elif "--pin" in sys.argv:
    ref = sys.argv[sys.argv.index("--pin") + 1]
    bad = pin_mismatches(ref); print("PIN OK" if not bad else f"differs from {ref}: {bad}"); sys.exit(1 if bad else 0)
  else:
    bad = unexplained(); print("OK" if not bad else bad); sys.exit(1 if bad else 0)
