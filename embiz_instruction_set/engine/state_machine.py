#!/usr/bin/env python3
"""state_machine.py — reads/writes the durable execution state.

state/CURRENT_STEP     : the single step id the worker is authorized to run now.
state/attempts.jsonl   : append-only ledger of every attempt (Airflow-style states).
state/hash_chain.jsonl : append-only evidence hash chain (see hash_chain.py).
"""
from __future__ import annotations
import json
import os
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CURRENT = os.path.join(ROOT, "state", "CURRENT_STEP")
ATTEMPTS = os.path.join(ROOT, "state", "attempts.jsonl")


def set_current(step_id: str) -> None:
    os.makedirs(os.path.dirname(CURRENT), exist_ok=True)
    with open(CURRENT, "w", encoding="utf-8") as f:
        f.write(step_id.strip() + "\n")


def get_current() -> str | None:
    if not os.path.exists(CURRENT):
        return None
    return open(CURRENT, "r", encoding="utf-8").read().strip() or None


def record_attempt(step_id: str, state: str, detail: dict) -> None:
    os.makedirs(os.path.dirname(ATTEMPTS), exist_ok=True)
    entry = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "step": step_id,
        "state": state,  # queued|running|success|failed|up_for_retry|recovering
        "detail": detail,
    }
    with open(ATTEMPTS, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
