#!/usr/bin/env python3
"""supervisor.py — owns the closed, never-idle execution loop.

The worker never selects its own next step. It executes one step, then calls:

    python3 engine/supervisor.py --resolve '<STEP>' --classification <SUCCESS|FAILURE>

The supervisor then:
  1. verifies the step's evidence artifact (evidence_verifier),
  2. on a claimed SUCCESS with unverifiable evidence, downgrades to FAILURE,
  3. records the attempt (state_machine) and appends the evidence hash (hash_chain),
  4. resolves the ONLY legal next step via the transition guard,
  5. on FAILURE, routes through the recovery router to the section diagnosis step,
     which will return control to the exact failed step,
  6. writes state/CURRENT_STEP and prints the next step file to open.

This mirrors Temporal (durable history), Step Functions (retry→catch), SCXML
(declared transitions only) and Airflow (observable task lifecycle).
"""
from __future__ import annotations
import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import evidence_verifier as ev  # noqa: E402
import hash_chain as hc  # noqa: E402
import recovery_router as rr  # noqa: E402
import state_machine as sm  # noqa: E402
import transition_guard as tg  # noqa: E402

INDEX = os.path.join(ROOT, "manifest", "steps_index.json")
GEN = os.path.join(HERE, "generate_steps.py")
FIRST_STEP = "#S00-01_TOOLING_INVENTORY"


def ensure_manifest() -> None:
    if not os.path.exists(INDEX):
        subprocess.run([sys.executable, GEN], check=True, cwd=ROOT)


def cmd_init() -> int:
    ensure_manifest()
    idx = tg.load_index()
    if FIRST_STEP not in idx["steps"]:
        print(f"FATAL: manifest missing first step {FIRST_STEP}", file=sys.stderr)
        return 2
    if sm.get_current() is None:
        sm.set_current(FIRST_STEP)
        sm.record_attempt("#BEGIN", "success", {"note": "loop initialized"})
    print(f"initialized. {len(idx['steps'])} steps. current={sm.get_current()}")
    return 0


def cmd_current() -> int:
    ensure_manifest()
    cur = sm.get_current()
    if not cur:
        print("no current step; run --init first", file=sys.stderr)
        return 2
    step = tg.load_index()["steps"][cur]
    print(f"CURRENT_STEP={cur}")
    print(f"OPEN_THIS_FILE={step['file']}")
    return 0


def cmd_resolve(step_id: str, classification: str) -> int:
    ensure_manifest()
    classification = classification.strip().upper()
    sm.record_attempt(step_id, "running", {"classification_claimed": classification})

    evidence_path = os.path.join(ROOT, "evidence", step_id.lstrip("#") + ".json")
    verified, problems = ev.verify(evidence_path)

    # Mandatory visual-fidelity gate: attestation steps must carry the verbatim
    # confirmation sentence backed by REAL passing metrics, or they cannot pass.
    if "VISUAL_FIDELITY" in step_id and os.path.exists(evidence_path):
        try:
            sys.path.insert(0, os.path.join(ROOT, "validators"))
            import fidelity_attestation as fa  # noqa: E402
            ev_obj = json.load(open(evidence_path))
            att_ok, att_probs = fa.verify_attestation(ev_obj)
            if not att_ok:
                verified = False
                problems = (problems or []) + ["visual-fidelity attestation rejected: "
                                               + "; ".join(att_probs)]
        except Exception as exc:  # noqa: BLE001
            verified = False
            problems = (problems or []) + [f"attestation validator error: {exc}"]

    # A claimed SUCCESS with unverifiable evidence is mechanically downgraded.
    effective = classification
    if classification == "SUCCESS" and not verified:
        effective = "FAILURE"
        problems.insert(0, "claimed SUCCESS but evidence failed verification -> downgraded")

    if verified:
        entry = hc.append(step_id, evidence_path, effective)
        chained = entry["chained_hash"]
    else:
        chained = None

    if effective == "SUCCESS":
        idx = tg.load_index()["steps"]
        step_meta = idx.get(step_id, {})
        if step_meta.get("dynamic_return_on_success"):
            # Recovery VERIFY: return to the EXACT failed step (the pipeline never
            # advances from recovery). Read the most recent return_to from the ledger.
            target = _last_return_to()
            if target is None or target not in idx:
                print(json.dumps({"step": step_id, "error": "no return_to recorded"}), file=sys.stderr)
                return 2
            sm.record_attempt(step_id, "success", {"hash": chained, "return_to": target})
            sm.set_current(target)
            print(json.dumps({
                "step": step_id, "classification": "SUCCESS", "evidence_hash": chained,
                "next": target, "open_this_file": idx[target]["file"],
                "note": "recovery verified -> returning to the exact failed step",
            }, indent=2))
            return 0
        route = tg.resolve_next(step_id, "SUCCESS")
        sm.record_attempt(step_id, "success", {"hash": chained, "next": route["next"]})
        sm.set_current(route["next"])
        print(json.dumps({
            "step": step_id, "classification": "SUCCESS", "evidence_hash": chained,
            "next": route["next"], "open_this_file": route["next_file"],
        }, indent=2))
        return 0

    # FAILURE path -------------------------------------------------------------
    fclass = rr.classify(problems)
    n = rr.attempts_for(step_id)
    route = tg.resolve_next(step_id, "FAILURE")  # -> the section recovery step
    sm.record_attempt(step_id, "up_for_retry", {
        "failure_class": fclass, "problems": problems, "attempt": n,
        "recovery": route["next"], "return_to": step_id,
    })
    sm.set_current(route["next"])
    print(json.dumps({
        "step": step_id, "classification": "FAILURE", "failure_class": fclass,
        "problems": problems, "attempt_count": n,
        "recovery": route["next"], "open_this_file": route["next_file"],
        "return_to_after_repair": step_id,
    }, indent=2))
    return 1


def _last_return_to() -> str | None:
    """Most recent `return_to` recorded when a step failed (for recovery return)."""
    path = os.path.join(ROOT, "state", "attempts.jsonl")
    if not os.path.exists(path):
        return None
    found = None
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line).get("detail", {})
            if d.get("return_to"):
                found = d["return_to"]
    return found


def cmd_status() -> int:
    ensure_manifest()
    idx = tg.load_index()
    print(f"steps: {len(idx['steps'])}")
    print(f"current: {sm.get_current()}")
    print("hash_chain: " + ("OK" if hc.verify_chain() else "BROKEN"))
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="EMBIZ instruction-set supervisor")
    p.add_argument("--init", action="store_true")
    p.add_argument("--current", action="store_true")
    p.add_argument("--status", action="store_true")
    p.add_argument("--resolve", metavar="STEP")
    p.add_argument("--classification", metavar="SUCCESS|FAILURE")
    a = p.parse_args()
    if a.init:
        return cmd_init()
    if a.current:
        return cmd_current()
    if a.status:
        return cmd_status()
    if a.resolve:
        if not a.classification:
            print("--resolve requires --classification", file=sys.stderr)
            return 2
        return cmd_resolve(a.resolve, a.classification)
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
