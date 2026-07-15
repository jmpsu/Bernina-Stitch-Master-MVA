#!/usr/bin/env python3
"""Regression framework (BRD "Regression Framework" / "Failure Analysis").

Compares consecutive E2E pass summaries (reports/e2e/pass_NN.json) metric by
metric, appends verdicts to reports/regression_history.jsonl, and raises a
persistent alert for any regression beyond tolerance. Improvements are
recorded in the reward ledger direction; regressions become learning
opportunities, not discarded information.
"""

import datetime
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "local_agents"))

E2E = REPO / "reports" / "e2e"
HISTORY = REPO / "reports" / "regression_history.jsonl"

METRICS = ["mean_ssim", "mean_composite", "density_pass_rate",
           "dual_size_rate", "companion_rate", "completed"]
TOLERANCE = 0.02  # relative drop beyond this is a regression


def main() -> int:
    passes = sorted(E2E.glob("pass_*.json"))
    if len(passes) < 2:
        print("need at least two passes to compare")
        return 0
    prev = json.loads(passes[-2].read_text(encoding="utf-8"))
    cur = json.loads(passes[-1].read_text(encoding="utf-8"))
    now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    regressions = []
    with HISTORY.open("a", encoding="utf-8") as f:
        for m in METRICS:
            p, c = prev.get(m), cur.get(m)
            if p is None or c is None:
                continue
            drop = (p - c) / p if p else 0.0
            verdict = ("REGRESSION" if drop > TOLERANCE
                       else "improved" if c > p else "stable")
            rec = {"timestamp": now, "metric": m,
                   "previous": p, "current": c,
                   "previous_pass": prev["pass"], "current_pass": cur["pass"],
                   "verdict": verdict}
            f.write(json.dumps(rec) + "\n")
            print(f"{m:20s} {p} -> {c}  {verdict}")
            if verdict == "REGRESSION":
                regressions.append(rec)
    if regressions:
        from agent_bus import alert_event
        for r in regressions:
            alert_event("michaela", "regression",
                        f"{r['metric']} regressed {r['previous']} -> "
                        f"{r['current']} (pass {r['previous_pass']} -> "
                        f"{r['current_pass']})")
    return 1 if regressions else 0


if __name__ == "__main__":
    sys.exit(main())
