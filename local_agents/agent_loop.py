"""agent_loop.py — EMBIZ persistent autonomous agent loop (plan -> act -> report).

Runs forever as a systemd user service (embiz-agent-loop.service). It is the
execution half of the autonomous Slack agent system:

  * consumes jobs from the filesystem queue (local_agents/state/queue/pending)
    that the Slack daemon enqueues (responsibility 11 — workflow triggering),
  * PLANS each job with qwen3:8b through the model_router escalation ladder
    (local GPU first; paid APIs only via the audited rung-4 escalation),
  * ACTS by running the repo's LOCAL DETERMINISTIC pipeline tools — these need
    no LLM at all: run_iteration.py, metrics.py, vectorizer.py, digitizer.py
    are pure local CPU compute on the Mint machine,
  * gates completion behind Slack approvals when a job requires a human gate
    (approval request with Block Kit buttons; decision files written by
    slack_daemon.py),
  * REPORTS progress to Slack at every step (responsibility 15), posts QA
    results (14) and decision traces (13), and appends to the repository
    decision_trace.jsonl ledger,
  * performs autonomous idle-period experimentation (run_iteration.py sweeps)
    so the platform never sits idle, per the I-HIVE continuous-learning
    mandate.

Dependencies: stdlib + requests + slack_sdk.
"""

from __future__ import annotations

import datetime
import json
import logging
import os
import signal
import subprocess
import sys
import time
import traceback
from pathlib import Path

from slack_sdk import WebClient

import model_router
from qwen_client import PRIMARY_MODEL, ollama_alive, strip_think

log = logging.getLogger("embiz.agent_loop")

# --------------------------------------------------------------------------
# Paths / config
# --------------------------------------------------------------------------
STATE_DIR = Path(os.environ.get(
    "EMBIZ_STATE_DIR", Path(__file__).resolve().parent / "state"))
QUEUE_PENDING = STATE_DIR / "queue" / "pending"
QUEUE_ACTIVE = STATE_DIR / "queue" / "active"
QUEUE_DONE = STATE_DIR / "queue" / "done"
QUEUE_FAILED = STATE_DIR / "queue" / "failed"
APPROVALS_PENDING = STATE_DIR / "approvals" / "pending"
APPROVALS_DECIDED = STATE_DIR / "approvals" / "decided"
TRANSCRIPT = STATE_DIR / "slack_transcript.jsonl"
HEARTBEAT = STATE_DIR / "agent_heartbeat.json"

REPO_ROOT = Path(os.environ.get(
    "EMBIZ_REPO_ROOT", Path(__file__).resolve().parent.parent))
DECISION_TRACE = REPO_ROOT / "decision_trace.jsonl"

CH_JOBS = os.environ.get("EMBIZ_SLACK_CHANNEL_JOBS", "#embiz-jobs")
CH_QA = os.environ.get("EMBIZ_SLACK_CHANNEL_QA", "#embiz-qa")
CH_ALERTS = os.environ.get("EMBIZ_SLACK_CHANNEL_ALERTS", "#embiz-alerts")

POLL_INTERVAL_S = int(os.environ.get("EMBIZ_QUEUE_POLL_S", "10"))
APPROVAL_TIMEOUT_S = int(os.environ.get("EMBIZ_APPROVAL_TIMEOUT_S", "86400"))
APPROVAL_REMINDER_S = int(os.environ.get("EMBIZ_APPROVAL_REMINDER_S", "3600"))
IDLE_EXPERIMENT_INTERVAL_S = int(
    os.environ.get("EMBIZ_IDLE_EXPERIMENT_INTERVAL_S", "3600"))
IDLE_EXPERIMENTS_ENABLED = os.environ.get("EMBIZ_IDLE_EXPERIMENTS", "1") == "1"
STEP_TIMEOUT_S = int(os.environ.get("EMBIZ_STEP_TIMEOUT_S", "3600"))

# Whitelisted LOCAL deterministic tools (no LLM, no shell interpolation).
# Maps tool name -> argv prefix, run from REPO_ROOT.
TOOL_WHITELIST: dict[str, list[str]] = {
    "run_iteration": [sys.executable, "run_iteration.py"],
    "metrics": [sys.executable, "-c",
                "import metrics, json, sys; "
                "print(json.dumps(metrics.svg_metrics(sys.argv[1]) "
                "if sys.argv[1].endswith('.svg') else metrics.pes_metrics(sys.argv[1])))"],
    "vectorizer": [sys.executable, "vectorizer.py"],
    "digitizer": [sys.executable, "digitizer.py"],
    "production_layout": [sys.executable, "production_layout.py"],
    "git_status": ["git", "status", "--short"],
}

_web: WebClient | None = None
_stop = False


def _utcnow() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _append_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def post(channel: str, text: str, blocks: list | None = None) -> str | None:
    """Slack post with transcript logging (shares the daemon's transcript)."""
    if _web is None:
        log.info("[no-slack] %s: %s", channel, text)
        return None
    try:
        resp = _web.chat_postMessage(channel=channel, text=text, blocks=blocks)
        _append_jsonl(TRANSCRIPT, {
            "timestamp": _utcnow(), "direction": "outbound",
            "kind": "agent_loop_message",
            "payload": {"channel": channel, "text": text, "ts": resp.get("ts")},
        })
        return resp.get("ts")
    except Exception as exc:  # noqa: BLE001
        log.error("slack post failed: %s", exc)
        return None


def trace(decision: str, objective: str, extra: dict | None = None,
          slack: bool = True) -> None:
    """Append to decision_trace.jsonl and mirror to Slack (responsibility 13)."""
    entry = {"timestamp": _utcnow(), "artifact": "decision_trace",
             "agent": "agent_loop", "decision": decision,
             "objective": objective}
    if extra:
        entry.update(extra)
    _append_jsonl(DECISION_TRACE, entry)
    if slack:
        post(CH_JOBS, f":brain: DECISION [agent_loop] {decision}: {objective}")


def report_error(source: str, exc: BaseException) -> None:
    tb = "".join(traceback.format_exception(exc)).strip().splitlines()
    post(CH_ALERTS, f":rotating_light: agent_loop ERROR in `{source}`:\n"
                    f"```{chr(10).join(tb[-6:])}```")


# --------------------------------------------------------------------------
# Planning (qwen3:8b via the escalation ladder)
# --------------------------------------------------------------------------
PLAN_SYSTEM = (
    "You are the EMBIZ orchestrator on a local machine. Plan the requested job "
    "as a short JSON list of steps. Each step is an object: "
    '{"action": "run_tool"|"reason"|"needs_approval", "tool": <one of '
    f"{sorted(TOOL_WHITELIST)}>, " '"args": [strings], "description": "..."}. '
    "The pipeline tools are deterministic local Python needing no LLM. Use "
    '"reason" steps only for analysis/report text. Add one "needs_approval" '
    "step before anything production-facing (exports, customer messages). "
    "Respond ONLY with the JSON array."
)


def plan_job(job: dict) -> list[dict]:
    prompt = (f"Job {job['id']}: {job['description']}\n"
              f"Params: {json.dumps(job.get('params', {}))}\n"
              "Produce the JSON step list now.")
    try:
        text = model_router.route("plan", prompt, system=PLAN_SYSTEM)
        text = strip_think(text)
        start, end = text.find("["), text.rfind("]")
        steps = json.loads(text[start:end + 1]) if start != -1 else []
        steps = [s for s in steps if isinstance(s, dict) and s.get("action")]
        if steps:
            return steps
    except Exception as exc:  # noqa: BLE001
        log.warning("planning failed for %s (%s); using fallback plan",
                    job["id"], exc)
    # Deterministic fallback: measure the corpus and report. Always safe.
    return [
        {"action": "run_tool", "tool": "run_iteration", "args": [],
         "description": "fallback: run one measurement iteration"},
        {"action": "reason", "args": [],
         "description": f"summarize the outcome of job {job['id']}"},
    ]


# --------------------------------------------------------------------------
# Acting
# --------------------------------------------------------------------------
def run_tool(tool: str, args: list[str]) -> tuple[bool, str]:
    """Run a whitelisted local deterministic tool. Returns (ok, output_tail)."""
    if tool not in TOOL_WHITELIST:
        return False, f"tool {tool!r} is not whitelisted"
    argv = TOOL_WHITELIST[tool] + [str(a) for a in args]
    try:
        proc = subprocess.run(
            argv, cwd=REPO_ROOT, capture_output=True, text=True,
            timeout=STEP_TIMEOUT_S,
        )
        tail = (proc.stdout + proc.stderr)[-1500:]
        return proc.returncode == 0, tail
    except subprocess.TimeoutExpired:
        return False, f"tool {tool} timed out after {STEP_TIMEOUT_S}s"
    except OSError as exc:
        return False, f"tool {tool} failed to start: {exc}"


def request_approval(job: dict, description: str) -> str:
    """Post an approval request with buttons; block until decided (or timeout).

    The Slack daemon records the human's decision into approvals/decided/.
    Approval may arrive via button, reaction, or /embiz approve|reject.
    Returns 'approved', 'rejected', or 'timeout'.
    """
    job_id = job["id"]
    blocks = [
        {"type": "section",
         "text": {"type": "mrkdwn",
                  "text": f":raised_hand: *Approval required — {job_id}*\n"
                          f"{description}\nJob: {job['description']}"}},
        {"type": "actions", "elements": [
            {"type": "button", "action_id": "embiz_approve",
             "text": {"type": "plain_text", "text": "Approve"},
             "style": "primary", "value": job_id},
            {"type": "button", "action_id": "embiz_reject",
             "text": {"type": "plain_text", "text": "Reject"},
             "style": "danger", "value": job_id},
        ]},
    ]
    ts = post(CH_JOBS, f"Approval required for {job_id}: {description} "
                       f"(react :white_check_mark:/:x:, use the buttons, or "
                       f"`/embiz approve {job_id}`)", blocks=blocks)
    APPROVALS_PENDING.mkdir(parents=True, exist_ok=True)
    (APPROVALS_PENDING / f"{job_id}.json").write_text(json.dumps({
        "job_id": job_id, "slack_ts": ts, "description": description,
        "requested": _utcnow(),
    }, indent=2), encoding="utf-8")

    decided = APPROVALS_DECIDED / f"{job_id}.json"
    waited = 0
    while waited < APPROVAL_TIMEOUT_S and not _stop:
        if decided.exists():
            try:
                decision = json.loads(decided.read_text(encoding="utf-8"))
                return decision.get("decision", "rejected")
            except (OSError, ValueError):
                return "rejected"
        time.sleep(POLL_INTERVAL_S)
        waited += POLL_INTERVAL_S
        if waited % APPROVAL_REMINDER_S < POLL_INTERVAL_S:
            post(CH_JOBS, f":hourglass: Still awaiting approval for *{job_id}* "
                          f"({waited // 3600}h elapsed).")
    return "timeout"


def execute_job(job: dict) -> None:
    job_id = job["id"]
    post(CH_JOBS, f":rocket: *{job_id}* started — {job['description']}")
    steps = plan_job(job)
    trace("plan-created", f"{job_id}: {len(steps)} steps", {
        "job_id": job_id,
        "plan": [s.get("description", s.get("tool", "?")) for s in steps],
    })

    evidence: list[dict] = []
    for i, step in enumerate(steps, 1):
        if _stop:
            raise RuntimeError("shutdown requested mid-job")
        desc = step.get("description", step.get("tool", step["action"]))
        post(CH_JOBS, f":gear: *{job_id}* step {i}/{len(steps)}: {desc}")

        if step["action"] == "run_tool":
            ok, output = run_tool(step.get("tool", ""), step.get("args", []))
            evidence.append({"step": i, "tool": step.get("tool"),
                             "ok": ok, "output_tail": output})
            if step.get("tool") == "run_iteration":
                # QA visibility: iteration output carries OVERALL_SCORE.
                passed = ok and "OVERALL_SCORE" in output
                post(CH_QA, f"{':white_check_mark:' if ok else ':x:'} QA "
                            f"*{job_id}* step {i} ({desc})\n```{output[-800:]}```")
            if not ok:
                raise RuntimeError(f"step {i} failed: {output[-400:]}")

        elif step["action"] == "reason":
            summary = model_router.route(
                "summarize",
                f"Job {job_id} ({job['description']}). Evidence so far:\n"
                f"{json.dumps(evidence)[-6000:]}\n\nTask: {desc}. "
                f"Write a short factual report.")
            evidence.append({"step": i, "reason": summary})
            post(CH_JOBS, f":memo: *{job_id}* step {i} report:\n{summary}")

        elif step["action"] == "needs_approval":
            decision = request_approval(job, desc)
            evidence.append({"step": i, "approval": decision})
            if decision != "approved":
                raise RuntimeError(f"human gate returned {decision!r} at step {i}")

        else:
            evidence.append({"step": i, "skipped": step["action"]})

    job.update({"state": "done", "finished": _utcnow(), "evidence": evidence})
    QUEUE_DONE.mkdir(parents=True, exist_ok=True)
    (QUEUE_DONE / f"{job_id}.json").write_text(
        json.dumps(job, indent=2), encoding="utf-8")
    (QUEUE_ACTIVE / f"{job_id}.json").unlink(missing_ok=True)
    trace("job-complete", f"{job_id} completed with {len(evidence)} evidence items",
          {"job_id": job_id})
    post(CH_JOBS, f":checkered_flag: *{job_id}* DONE — evidence retained in "
                  f"queue/done/{job_id}.json")


def fail_job(job: dict, exc: BaseException) -> None:
    job_id = job["id"]
    job.update({"state": "failed", "finished": _utcnow(), "error": str(exc)})
    QUEUE_FAILED.mkdir(parents=True, exist_ok=True)
    (QUEUE_FAILED / f"{job_id}.json").write_text(
        json.dumps(job, indent=2), encoding="utf-8")
    (QUEUE_ACTIVE / f"{job_id}.json").unlink(missing_ok=True)
    trace("job-failed", f"{job_id}: {exc}", {"job_id": job_id}, slack=False)
    post(CH_JOBS, f":x: *{job_id}* FAILED — {exc}")
    report_error(f"execute_job({job_id})", exc)


def claim_next_job() -> dict | None:
    """Atomically claim the oldest pending job via rename."""
    if not QUEUE_PENDING.exists():
        return None
    for f in sorted(QUEUE_PENDING.glob("*.json")):
        target = QUEUE_ACTIVE / f.name
        try:
            QUEUE_ACTIVE.mkdir(parents=True, exist_ok=True)
            f.rename(target)  # atomic on same filesystem
        except OSError:
            continue  # another worker claimed it
        try:
            job = json.loads(target.read_text(encoding="utf-8"))
            job["state"] = "active"
            return job
        except (OSError, ValueError) as exc:
            log.error("corrupt job file %s: %s", f.name, exc)
            target.rename(QUEUE_FAILED / f.name)
    return None


# --------------------------------------------------------------------------
# Idle-period autonomous experimentation (I-HIVE continuous learning)
# --------------------------------------------------------------------------
def idle_experiment() -> None:
    """Free local CPU work: one measurement/learning iteration + Slack summary."""
    ok, output = run_tool("run_iteration", [])
    line = next((ln for ln in reversed(output.splitlines())
                 if "OVERALL_SCORE" in ln), output[-200:])
    post(CH_QA, f":test_tube: Idle experiment iteration "
                f"({'ok' if ok else 'FAILED'}): {line.strip()[:300]}")
    trace("idle-experiment", f"autonomous idle iteration ({'ok' if ok else 'failed'})",
          slack=False)


# --------------------------------------------------------------------------
# Main loop
# --------------------------------------------------------------------------
def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s")

    global _web
    token = os.environ.get("SLACK_BOT_TOKEN")
    if token:
        _web = WebClient(token=token)
    else:
        log.warning("SLACK_BOT_TOKEN unset — running headless (log-only).")

    def _sig(*_):
        global _stop
        _stop = True
    signal.signal(signal.SIGTERM, _sig)
    signal.signal(signal.SIGINT, _sig)

    for d in (QUEUE_PENDING, QUEUE_ACTIVE, QUEUE_DONE, QUEUE_FAILED,
              APPROVALS_PENDING, APPROVALS_DECIDED):
        d.mkdir(parents=True, exist_ok=True)

    # Recover jobs orphaned in active/ by a previous crash: re-queue them.
    for f in QUEUE_ACTIVE.glob("*.json"):
        f.rename(QUEUE_PENDING / f.name)
        log.info("re-queued orphaned job %s", f.stem)

    post(CH_ALERTS,
         f":robot_face: EMBIZ agent loop online (local {PRIMARY_MODEL} via "
         f"escalation ladder; Ollama {'up' if ollama_alive() else 'DOWN'}; "
         f"deterministic pipeline tools: {', '.join(sorted(TOOL_WHITELIST))}).")

    last_idle = time.time()
    while not _stop:
        HEARTBEAT.write_text(json.dumps(
            {"timestamp": _utcnow(), "pid": os.getpid()}), encoding="utf-8")
        job = None
        try:
            job = claim_next_job()
            if job:
                execute_job(job)
                last_idle = time.time()  # production work resets idle timer
            else:
                if (IDLE_EXPERIMENTS_ENABLED
                        and time.time() - last_idle > IDLE_EXPERIMENT_INTERVAL_S):
                    idle_experiment()
                    last_idle = time.time()
                time.sleep(POLL_INTERVAL_S)
        except Exception as exc:  # noqa: BLE001 — the loop must never die
            if job:
                fail_job(job, exc)
            else:
                log.error("loop error: %s", exc, exc_info=True)
                report_error("agent_loop.main", exc)
                time.sleep(POLL_INTERVAL_S)

    post(CH_ALERTS, ":zzz: EMBIZ agent loop shutting down (signal).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
