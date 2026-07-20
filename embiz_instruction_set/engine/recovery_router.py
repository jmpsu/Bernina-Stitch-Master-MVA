#!/usr/bin/env python3
"""recovery_router.py — classifies a failure and returns it to the failed step.

Step Functions-style: after bounded retries, a FAILURE is caught and routed into
the section's recovery diagnosis step. The recovery branch always terminates by
returning to the EXACT step id that failed (recorded as `return_to`), so the
pipeline never advances on a repair — only a genuine SUCCESS on the origin step
advances. Failure classes mirror typed error names.
"""
from __future__ import annotations
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ATTEMPTS = os.path.join(ROOT, "state", "attempts.jsonl")

FAILURE_CLASSES = {
    "EVIDENCE_MISSING": "Evidence artifact absent or unhashed.",
    "EVIDENCE_PLACEHOLDER": "Placeholder/stub present where real work required.",
    "PREDICATE_UNMET": "One or more acceptance predicates false.",
    "COMMAND_ERROR": "A declared command exited non-zero / raised.",
    "TIMEOUT": "Action exceeded its allotted time.",
    "ROUTE_VIOLATION": "Attempted to route to a non-declared destination.",
    "DEPENDENCY_MISSING": "A required tool/dependency is not installed/verified.",
    "SCHEMA_INVALID": "Artifact failed its JSON schema.",
    "UNKNOWN": "Unclassified failure; requires prescribed external research.",
}


def attempts_for(step_id: str) -> int:
    if not os.path.exists(ATTEMPTS):
        return 0
    n = 0
    with open(ATTEMPTS, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and json.loads(line).get("step") == step_id:
                n += 1
    return n


def classify(problems: list[str]) -> str:
    joined = " ".join(problems).lower()
    if "missing" in joined and "evidence" in joined:
        return "EVIDENCE_MISSING"
    if "placeholder" in joined:
        return "EVIDENCE_PLACEHOLDER"
    if "predicate" in joined:
        return "PREDICATE_UNMET"
    if "schema" in joined:
        return "SCHEMA_INVALID"
    if "route" in joined:
        return "ROUTE_VIOLATION"
    if "depend" in joined or "install" in joined:
        return "DEPENDENCY_MISSING"
    return "UNKNOWN"
