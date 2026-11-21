"""Formative-memory bank save/load (phase2.save_bank / phase2.load_bank).

Needs Concordia v1.8.9 on PYTHONPATH (skipped otherwise); no model is loaded."""
import datetime
import hashlib
import os
import subprocess
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
pytest.importorskip("concordia")
pytest.importorskip("examples.modular.environment.haggling")

from concordia.associative_memory import blank_memories, importance_function  # noqa: E402
from refimpl import phase2  # noqa: E402


def fake_embed(text):
  h = hashlib.sha256(text.encode()).digest()
  return (np.frombuffer(h * 24, dtype=np.uint8)[:768].astype(np.float32) - 127.5) / 50


def make_bank():
  mem = blank_memories.MemoryFactory(
      model=None, embedder=fake_embed,
      importance=importance_function.ConstantImportanceModel().importance,
      clock_now=lambda: phase2.START).make_blank_memory()
  t0 = datetime.datetime(1880, 3, 1, 9, 30)
  mem.add("Anya was born in a small village.", timestamp=t0, tags=["episode"])
  mem.add("She learnt to\nbargain.", timestamp=t0 + datetime.timedelta(days=400),
          tags=("episode", "childhood"))
  mem.add("Same text, other time.", timestamp=t0)
  mem.add("Same text, other time.", timestamp=t0 + datetime.timedelta(minutes=5))
  mem.add("Anya always drives a hard bargain.", tags=["initial_player_specific_memory"])
  mem.add("Importance differs.", timestamp=t0, importance=0.25)
  return mem


def test_bank_save_and_reload(tmp_path):
  mem = make_bank()
  path = str(tmp_path / "bank.parquet")
  sha = phase2.save_bank(mem, path)
  assert len(sha) == 64 and phase2.save_bank(mem, path) == sha      # deterministic file
  import pyarrow.parquet as pq
  assert tuple(pq.read_table(path).column_names) == phase2.BANK_COLUMNS
  loaded, cfg = phase2.load_bank(path, None, fake_embed, 1)
  a, b = mem.get_data_frame(), loaded.get_data_frame()
  assert list(a.columns) == list(b.columns) and list(a.dtypes) == list(b.dtypes)
  assert len(a) == len(b) == 6
  for col in ("text", "time", "tags", "importance"):
    assert list(a[col]) == list(b[col]), col
  assert all(isinstance(t, tuple) for t in b["tags"])
  for x, y in zip(a["embedding"], b["embedding"]):
    assert x.dtype == y.dtype == np.float32 and np.array_equal(x, y)
  assert loaded._stored_hashes == mem._stored_hashes
  assert cfg.name == "Anya Blossomwood"
  assert cfg.extras == phase2.player_config(1).extras


def test_duplicate_row_ignored_after_load(tmp_path):
  mem = make_bank()
  path = str(tmp_path / "bank.parquet")
  phase2.save_bank(mem, path)
  loaded, _ = phase2.load_bank(path, None, fake_embed, 1)
  n = len(loaded.get_data_frame())
  row = loaded.get_data_frame().iloc[1]
  loaded.add(row["text"], timestamp=row["time"].to_pydatetime(), tags=list(row["tags"]),
             importance=row["importance"])
  assert len(loaded.get_data_frame()) == n                          # duplicate ignored
  loaded.add(row["text"], timestamp=row["time"].to_pydatetime(), tags=list(row["tags"]),
             importance=0.5)
  assert len(loaded.get_data_frame()) == n + 1                      # a new row is added


def test_hashes_recomputed_in_a_fresh_process(tmp_path):
  """String hashes differ across processes: the loader must not reuse stored ones."""
  mem = make_bank()
  path = str(tmp_path / "bank.parquet")
  phase2.save_bank(mem, path)
  code = ("import sys, hashlib, numpy as np; sys.path.insert(0, %r); "
          "from tests.test_banks import fake_embed; from refimpl import phase2; "
          "m, _ = phase2.load_bank(%r, None, fake_embed, 1); r = m.get_data_frame().iloc[0]; "
          "n = len(m.get_data_frame()); "
          "m.add(r['text'], timestamp=r['time'].to_pydatetime(), tags=list(r['tags']), "
          "importance=r['importance']); print(len(m.get_data_frame()) == n)"
          % (os.path.dirname(os.path.dirname(os.path.abspath(__file__))), path))
  env = dict(os.environ, PYTHONHASHSEED="12345")
  out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env)
  assert out.stdout.strip() == "True", out.stderr[-2000:]
