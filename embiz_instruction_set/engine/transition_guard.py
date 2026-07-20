#!/usr/bin/env python3
"""transition_guard.py — enforces that only declared routes are legal (SCXML-style).

Given a step id and a proposed classification, resolves the ONLY permitted next
step from the manifest. If the worker (or anything else) tries to route somewhere
that is not the declared SUCCESS or FAILURE target, the guard refuses. This closes
the "agent picks its own direction" failure mode mechanically.
"""
from __future__ import annotations
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
INDEX = os.path.join(ROOT, "manifest", "steps_index.json")


def load_index() -> dict:
    with open(INDEX, "r", encoding="utf-8") as f:
        return json.load(f)


def resolve_next(step_id: str, classification: str) -> dict:
    idx = load_index()
    steps = idx["steps"]
    if step_id not in steps:
        raise KeyError(f"unknown step id: {step_id}")
    step = steps[step_id]
    classification = classification.strip().upper()
    if classification not in ("SUCCESS", "FAILURE"):
        raise ValueError(f"classification must be SUCCESS or FAILURE, got {classification!r}")
    target = step["on_success"] if classification == "SUCCESS" else step["on_failure"]
    if target not in steps:
        raise KeyError(f"declared route {target} is not a known step (manifest invalid)")
    return {
        "from": step_id,
        "classification": classification,
        "next": target,
        "next_file": steps[target]["file"],
    }


def max_attempts(step_id: str) -> int:
    return load_index()["steps"][step_id].get("max_attempts", 3)
