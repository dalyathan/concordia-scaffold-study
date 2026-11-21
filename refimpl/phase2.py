"""Phase 2 harness: build one agent exactly as v1.8.9 haggling.py does, feed it the
scripted conversation, and collect its decision and reasoning text S.

Requires Concordia v1.8.9 on the path and the agent files from the supplementary
zip importable as modules (e.g. `agent_py_files.taehun_cgcal`).
"""
from __future__ import annotations

import datetime
import importlib
import random

import numpy as np
import torch

from concordia.associative_memory import blank_memories, formative_memories, importance_function
from concordia.clocks import game_clock
from concordia.typing import entity as entity_lib

from examples.modular.environment import haggling
from examples.modular.environment.modules import fruitville_haggling as fv

from . import core, phase3
from .determinism import deterministic_execution, reset_decision_counter
from .local_gemma2 import LocalGemma2, call_context

START = datetime.datetime(year=fv.YEAR, month=fv.MONTH, day=fv.DAY)   # 1895-09-12 00:00
SETUP = START - datetime.timedelta(days=1)
DECISION_SPEC = entity_lib.choice_action_spec(
    call_to_action="What price would {name} propose?:",
    options=tuple(core.OPTION_TEXT[k] for k in core.PRICES), tag="choice")


def formative_memory(lm: LocalGemma2, embedder, variant: int):
  """Generated once per variant (greedy) and stored; reused for every agent."""
  name = core.FEMALE_NAMES[variant - 1]
  random.seed(1000 + variant)                 # get_trait() uses the global RNG
  cfg = haggling.configure_player(name, "female", fv.YEAR, True,
                                  random.Random(1000 + variant))
  clock = game_clock.MultiIntervalClock(start=START,
                                        step_sizes=[haggling.MAJOR_TIME_STEP,
                                                    haggling.MINOR_TIME_STEP])
  blank = blank_memories.MemoryFactory(
      model=lm, embedder=embedder,
      importance=importance_function.ConstantImportanceModel().importance,
      clock_now=clock.now)
  shared, _ = haggling.get_shared_memories_and_context(fv.SCENARIO_PREMISE)
  factory = formative_memories.FormativeMemoryFactory(
      model=lm, shared_memories=shared,
      blank_memory_factory_call=blank.make_blank_memory, current_date=START)
  with call_context(agent="formative", pid=f"variant{variant}", temperature_override=0.0):
    with deterministic_execution():
      mem = factory.make_memories(cfg)
  for extra in cfg.extras["player_specific_memories"]:   # as _make_player_memories
    mem.add(extra, tags=["initial_player_specific_memory"])
  # Release: mem.get_data_frame() (text, time, tags, importance, embedding) as parquet.
  return mem, cfg


def run_decision(lm: LocalGemma2, embedder, agent_module: str, p: core.Prompt,
                 formative_mem, cfg, openings: list[str],
                 utter_fmt: str = '{speaker} -- "{text}"', draw: int = 0,
                 temperature: float = 0.0) -> dict:
  mod = importlib.import_module(agent_module)
  clock = game_clock.MultiIntervalClock(start=SETUP,
                                        step_sizes=[haggling.MAJOR_TIME_STEP,
                                                    haggling.MINOR_TIME_STEP])
  # Identical starting memories on this run's clock. AssociativeMemory holds a
  # threading.Lock, so it cannot be deep-copied: make a blank bank and copy rows.
  memory = blank_memories.MemoryFactory(
      model=lm, embedder=embedder,
      importance=importance_function.ConstantImportanceModel().importance,
      clock_now=clock.now).make_blank_memory()
  memory._memory_bank = formative_mem.get_data_frame()        # a copy
  memory._stored_hashes = set(formative_mem._stored_hashes)
  agent = mod.build_agent(config=cfg, model=lm, memory=memory, clock=clock,
                          update_time_interval=haggling.MAJOR_TIME_STEP)
  calls = []
  lm.log = lambda rec: calls.append(rec)
  with call_context(agent=agent_module, pid=p.pid, draw=draw,
                    temperature_override=temperature):
    with deterministic_execution():
      reset_decision_counter()
      # AssociativeMemory.retrieve_random(_with_importance) calls
      # DataFrame.sample(random_state=None), i.e. numpy's global RNG, and add()
      # calls it before any model call has re-seeded that RNG. Seed the global
      # generators at the start of every decision so that state is fixed.
      s0 = core.call_seed("decision-start", agent_module, p.pid, draw)
      random.seed(s0)
      np.random.seed(s0 % (2**32))
      torch.manual_seed(s0)
      # Setup-time observations, as haggling.py's _init_premise_memories does.
      for text in [fv.SCENARIO_PREMISE, phase3.SHARED_MEMORY_1, phase3.SHARED_MEMORY_2,
                   *core.RULE_MEMORIES]:
        agent.observe(text)
      clock.set(START)
      agent.observe(phase3.premise(p, openings[p.opening_index]))
      for u in phase3.utterances(p, utter_fmt):
        clock.advance()
        agent.observe(u)
      agent.observe(f"{p.buyer} is ready to make an offer.")
      act_from = len(calls)
      choice_text = agent.act(DECISION_SPEC)
  act_calls = calls[act_from:]
  k = next(k for k, t in core.OPTION_TEXT.items() if t == choice_text)
  text_calls = [(c["prompt"], c["output"]) for c in act_calls if c["kind"] == "text"]
  S = core.build_S(text_calls)
  S_reason = core.build_S(text_calls, reasoning_only=True)
  rule_seen = {i: any(r in c["prompt"] for c in act_calls) for i, r in
               enumerate(core.RULE_MEMORIES)}
  return {"pid": p.pid, "agent": agent_module, "draw": draw, "k": k,
          "hard_regret": core.hard_regret(p, k), "S": S, "S_reason": S_reason,
          "calls": calls,
          "rule_memories_in_prompts": rule_seen}
