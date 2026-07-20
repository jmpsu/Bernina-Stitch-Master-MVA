#!/usr/bin/env python3
"""evidence_verifier.py — independent verifier that rejects false completion.

Rejects an evidence artifact (forcing FAILURE regardless of the worker's claim)
when it is missing, empty, malformed, contains placeholder tokens where real work
was required, omits captured command output, or omits the changed-file list. This
is the component that makes "unsupported completion claims shall never be accepted"
(BRD) mechanically true rather than aspirational.
"""
from __future__ import annotations
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

PLACEHOLDER_PATTERNS = [
    r"\bTODO\b", r"\bFIXME\b", r"\bPLACEHOLDER\b", r"\bNotImplemented\b",
    r"\bstub\b", r"\bfake output\b", r"\bwould (?:run|print|produce)\b",
    r"\bshould (?:work|pass)\b", r"\.\.\.\s*$", r"<INSERT[^>]*>",
]

REQUIRED_KEYS = ["step", "commands", "stdout", "changed_files", "predicate_results"]


def verify(evidence_path: str, require_real: bool = True) -> tuple[bool, list[str]]:
    problems: list[str] = []
    if not os.path.exists(evidence_path):
        return False, [f"evidence missing: {evidence_path}"]
    raw = open(evidence_path, "r", encoding="utf-8").read().strip()
    if not raw:
        return False, ["evidence file is empty"]
    try:
        data = json.loads(raw)
    except Exception as exc:  # noqa: BLE001
        return False, [f"evidence is not valid JSON: {exc}"]

    for key in REQUIRED_KEYS:
        if key not in data:
            problems.append(f"missing required key: {key}")

    if isinstance(data.get("commands"), list) and not data["commands"]:
        problems.append("commands list is empty (no action was run)")
    if isinstance(data.get("stdout"), str) and not data["stdout"].strip():
        problems.append("stdout is empty (no real command output captured)")
    if isinstance(data.get("changed_files"), list) and not data["changed_files"]:
        # allowed for pure-inspection steps that declare inspect_only=true
        if not data.get("inspect_only"):
            problems.append("changed_files empty and step is not inspect_only")

    if require_real and not data.get("inspect_only"):
        blob = raw
        for pat in PLACEHOLDER_PATTERNS:
            if re.search(pat, blob, flags=re.IGNORECASE | re.MULTILINE):
                problems.append(f"placeholder token present: /{pat}/")

    preds = data.get("predicate_results", [])
    if isinstance(preds, list) and preds:
        if any((p.get("passed") is not True) for p in preds if isinstance(p, dict)):
            problems.append("one or more acceptance predicates did not pass")
    else:
        problems.append("predicate_results missing or empty")

    return (len(problems) == 0), problems


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: evidence_verifier.py evidence/<STEP>.json")
        sys.exit(2)
    ok, probs = verify(sys.argv[1])
    print(json.dumps({"verified": ok, "problems": probs}, indent=2))
    sys.exit(0 if ok else 1)
