#!/usr/bin/env python3
"""fidelity_attestation.py — enforce the MANDATORY visual-fidelity attestation.

A vectorized SVG may not be posited as finished, and a stitch plan / PES may not
be created from an SVG, until the agent has (a) run fidelity_compare.py to obtain
REAL metrics that pass thresholds, AND (b) stated the mandated confirmation
sentence naming the actual artifact filename(s) and the customer source image.

This validator rejects the evidence unless BOTH hold. It is called by the
attestation gate steps (S05 end, S06 start, S08 end) and closes the door on a
worker "confirming" fidelity it never measured.
"""
from __future__ import annotations
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "engine"))

# The required clause. The agent fills in <FILES> but MUST keep this wording.
REQUIRED_CLAUSE = ("preserve consistent silhouette, proportions, recognizable "
                   "artistic intent, and relative scale with the customer source image")
LEAD = "I HAVE REVIEWED"


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


def verify_attestation(evidence: dict) -> tuple[bool, list[str]]:
    problems: list[str] = []
    att = _norm(evidence.get("attestation", ""))
    if not att:
        return False, ["no attestation sentence present"]
    if LEAD not in att.upper():
        problems.append("attestation must begin with the mandated lead 'I HAVE REVIEWED'")
    if REQUIRED_CLAUSE.lower() not in att.lower():
        problems.append("attestation is missing the mandated fidelity clause (verbatim)")

    # Must name the real artifact filenames it reviewed.
    named = evidence.get("attested_files", [])
    if not named:
        problems.append("attested_files list is empty (must name the real .svg / .pes reviewed)")
    for fn in named:
        if os.path.basename(fn) not in att:
            problems.append(f"attestation does not name the artifact it claims to review: {fn}")

    # Must carry REAL computed metrics that pass thresholds.
    metrics = evidence.get("fidelity_metrics")
    if not isinstance(metrics, dict):
        problems.append("fidelity_metrics missing — attestation must be backed by computed metrics")
    else:
        try:
            import fidelity_compare as fc  # noqa: E402
            ok, fails = fc.passes(metrics)
            if not ok:
                problems.append("fidelity metrics did not pass thresholds: " + "; ".join(fails))
        except Exception as e:  # noqa: BLE001
            problems.append(f"could not evaluate fidelity metrics: {e}")

    return (len(problems) == 0), problems


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: fidelity_attestation.py evidence/<STEP>.json")
        sys.exit(2)
    ev = json.load(open(sys.argv[1]))
    ok, probs = verify_attestation(ev)
    print(json.dumps({"attestation_ok": ok, "problems": probs}, indent=2))
    sys.exit(0 if ok else 1)
