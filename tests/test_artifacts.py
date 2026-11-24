import json, os, shutil, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
import artifacts_common as A


def test_check_tree_counts_match_mismatch_missing():
  d = tempfile.mkdtemp(); src = tempfile.mkdtemp()
  for n, t in (("a.txt", "one"), ("b.txt", "two"), ("c.txt", "three")):
    open(os.path.join(src, n), "w").write(t)
  man = {"files": [{"path": n, "bytes": os.path.getsize(os.path.join(src, n)), "sha256": A.sha256(os.path.join(src, n))} for n in ("a.txt", "b.txt", "c.txt")]}
  mp = os.path.join(d, "m.json"); json.dump(man, open(mp, "w"))
  shutil.copy(os.path.join(src, "a.txt"), d)
  open(os.path.join(d, "b.txt"), "w").write("twX")      # same size, different content
  ok, bad, missing = A.check_tree(d, mp)
  assert (ok, bad, missing) == (["a.txt"], ["b.txt"], ["c.txt"])


def test_file_list_has_no_duplicates_and_skips_caches():
  fs = A.files()
  assert len(fs) == len(set(fs)) and not any("__pycache__" in f for f in fs)
