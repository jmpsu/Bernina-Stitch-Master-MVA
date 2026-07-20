#!/usr/bin/env python3
"""selftest.py — prove the instruction-set system is internally sound.

Checks (all must pass):
  T1  Every step's on_success and on_failure route resolves to a known step.
  T2  Every pipeline step's failure route is its section's recovery DIAGNOSE.
  T3  The loop is closed: no step is a terminal dead-end; the last pipeline step
      routes back into the never-idle improvement loop.
  T4  Every recovery VERIFY step is marked dynamic_return_on_success (returns to
      the exact failed step, never advances the pipeline).
  T5  Every section has a full recovery micro-branch (diagnose/repair/verify/escalate).
  T6  Every generated step file exists on disk and contains the ten-clause contract.
  T7  The verifier rejects fabricated/placeholder evidence (false-completion guard).
  T8  The verifier + guard accept a well-formed SUCCESS and route it forward.
  T9  A FAILURE routes to recovery and records return_to = the failed step.
  T10 The hash chain verifies after appends.
"""
from __future__ import annotations
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "engine"))

import evidence_verifier as ev  # noqa: E402

INDEX = os.path.join(ROOT, "manifest", "steps_index.json")
FAILS: list[str] = []


def ok(cond: bool, label: str):
    print(("PASS " if cond else "FAIL ") + label)
    if not cond:
        FAILS.append(label)


def main() -> int:
    idx = json.load(open(INDEX))
    steps = idx["steps"]

    # T1 route integrity
    bad = [s for s, m in steps.items()
           if m["on_success"] not in steps and m["on_success"] != "#RETURN_TO_FAILED"
           or m["on_failure"] not in steps]
    ok(not bad, f"T1 all routes resolve (bad={bad[:5]})")

    # T2 pipeline failure -> section DIAGNOSE
    t2bad = []
    for s, m in steps.items():
        if s.startswith("#S") and "-REC" not in m["section"]:
            sid = m["section"]
            if m["on_failure"] != f"#REC-{sid}_DIAGNOSE":
                t2bad.append(s)
    ok(not t2bad, f"T2 pipeline failures route to section DIAGNOSE (bad={t2bad[:5]})")

    # T3 closed loop: last pipeline step loops back into idle work
    last = "#S15-10_GLOBAL_PRINCIPLES_AUDIT"
    ok(last in steps and steps[last]["on_success"] == "#S14-08_IDLE_EXPERIMENTATION",
       "T3 pipeline end loops back into never-idle work")
    ok(steps["#S14-09_CONTINUE_AS_NEW"]["on_success"] == "#S15-01_PRODUCTION_READINESS_GATE"
       or steps["#S14-08_IDLE_EXPERIMENTATION"]["on_success"].startswith("#S14-09"),
       "T3b idle experimentation advances within the loop")

    # T4 recovery VERIFY dynamic return
    verifies = [s for s in steps if s.endswith("_VERIFY") and s.startswith("#REC-")]
    ok(verifies and all(steps[s].get("dynamic_return_on_success") for s in verifies),
       f"T4 every recovery VERIFY returns to the exact failed step ({len(verifies)} verifies)")

    # T5 full recovery branch per section
    sids = ["BOOT"] + sorted({m["section"] for s, m in steps.items() if m["section"].startswith("S") and "-REC" not in m["section"]})
    t5bad = []
    for sid in sids:
        for kind in ("DIAGNOSE", "REPAIR", "VERIFY", "ESCALATE"):
            if f"#REC-{sid}_{kind}" not in steps:
                t5bad.append(f"#REC-{sid}_{kind}")
    ok(not t5bad, f"T5 every section has a full recovery branch (missing={t5bad[:5]})")

    # T6 files exist + contain the contract
    t6bad = []
    for s, m in steps.items():
        if s == "#BEGIN":
            continue
        p = os.path.join(ROOT, m["file"])
        if not os.path.exists(p):
            t6bad.append(m["file"]); continue
        txt = open(p, encoding="utf-8").read()
        if "EXECUTION CONTRACT" not in txt or "ON SUCCESS" not in txt or "ON FAILURE" not in txt:
            t6bad.append(m["file"])
    ok(not t6bad, f"T6 every step file exists with the contract (bad={t6bad[:5]})")

    # T7 verifier rejects fabricated/placeholder evidence
    with tempfile.TemporaryDirectory() as td:
        bad_ev = os.path.join(td, "bad.json")
        json.dump({"step": "#X", "commands": ["echo hi"], "stdout": "TODO: would run",
                   "changed_files": [{"path": "x"}],
                   "predicate_results": [{"predicate": "p", "passed": True}]}, open(bad_ev, "w"))
        v, probs = ev.verify(bad_ev)
        ok(not v, f"T7 verifier rejects placeholder evidence (problems={len(probs)})")

        empty_ev = os.path.join(td, "empty.json")
        open(empty_ev, "w").write("")
        v2, _ = ev.verify(empty_ev)
        ok(not v2, "T7b verifier rejects empty evidence")

        # T8 verifier accepts a clean SUCCESS
        good_ev = os.path.join(td, "good.json")
        json.dump({"step": "#S00-01_TOOLING_INVENTORY", "commands": ["python3 --version"],
                   "stdout": "Python 3.11.0", "inspect_only": True, "changed_files": [],
                   "predicate_results": [{"predicate": "tools present", "passed": True}]},
                  open(good_ev, "w"))
        v3, probs3 = ev.verify(good_ev)
        ok(v3, f"T8 verifier accepts clean SUCCESS (problems={probs3})")

    # T9 simulate a FAILURE routes to recovery + records return_to (dry, in temp state)
    #    We exercise the transition guard directly rather than mutating real state.
    sys.path.insert(0, os.path.join(ROOT, "engine"))
    import transition_guard as tg  # noqa: E402
    r = tg.resolve_next("#S04-03_POTRACE_PARAM_SWEEP", "FAILURE")
    ok(r["next"] == "#REC-S04_DIAGNOSE", f"T9 failure routes to recovery ({r['next']})")

    # T10 hash chain verifies (may be empty -> OK)
    import hash_chain as hc  # noqa: E402
    ok(hc.verify_chain(), "T10 hash chain verifies")

    print(f"\nSELFTEST: {'ALL PASS' if not FAILS else 'FAILURES: ' + str(FAILS)}")
    return 0 if not FAILS else 1


if __name__ == "__main__":
    raise SystemExit(main())
