"""slack_daemon.py — EMBIZ continuously running autonomous Slack daemon.

Socket Mode listener + dispatcher. This is a persistent daemon (systemd user
service embiz-slack-daemon.service), NOT a one-off chatbot session. It owns ALL
fifteen mandatory Slack responsibilities from
EMBIZ_Jupiter_LOCAL_FIRST_Autonomous_Agent_FULL_VERSION.md:

   1. Slack message monitoring           (Socket Mode events_api listener)
   2. Slack command handling             (natural-language @mentions/DMs)
   3. Slack slash command support        (/embiz <subcommand>)
   4. Slack approval handling            (buttons, reactions, /embiz approve)
   5. Slack rejection handling           (buttons, reactions, /embiz reject)
   6. Slack job status updates           (post_job_status)
   7. Slack agent conversations          (qwen3:8b via model_router)
   8. Slack production notifications     (post_production)
   9. Slack error notifications          (post_error; global exception guard)
  10. Slack operational reporting        (scheduled ops report thread)
  11. Slack workflow triggering          (enqueue jobs into filesystem queue)
  12. Slack transcript logging           (state/slack_transcript.jsonl)
  13. Slack-visible decision traces      (post_decision_trace)
  14. Slack-visible QA results           (post_qa_result)
  15. Slack-visible job progress updates (consumed by agent_loop via the same
                                          channels; daemon exposes helpers)

Transport: Socket Mode (SLACK_APP_TOKEN) — outbound-only WebSocket, no public
ingress required on a laptop. Reasoning: qwen3:8b on the local GPU through the
model_router escalation ladder. No paid API is ever called directly from here.

Dependencies: stdlib + requests + slack_sdk.
"""

from __future__ import annotations

import datetime
import json
import logging
import os
import signal
import sys
import threading
import time
import traceback
import uuid
from pathlib import Path

from slack_sdk import WebClient
from slack_sdk.socket_mode import SocketModeClient
from slack_sdk.socket_mode.request import SocketModeRequest
from slack_sdk.socket_mode.response import SocketModeResponse

import model_router
from qwen_client import PRIMARY_MODEL, list_local_models, ollama_alive

log = logging.getLogger("embiz.slack_daemon")

# --------------------------------------------------------------------------
# Paths and configuration (no hardcoded secrets — env only)
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
HEARTBEAT = STATE_DIR / "daemon_heartbeat.json"

REPO_ROOT = Path(os.environ.get(
    "EMBIZ_REPO_ROOT", Path(__file__).resolve().parent.parent))
DECISION_TRACE = REPO_ROOT / "decision_trace.jsonl"

CH_JOBS = os.environ.get("EMBIZ_SLACK_CHANNEL_JOBS", "#embiz-jobs")
CH_QA = os.environ.get("EMBIZ_SLACK_CHANNEL_QA", "#embiz-qa")
CH_ALERTS = os.environ.get("EMBIZ_SLACK_CHANNEL_ALERTS", "#embiz-alerts")
APPROVERS = {u.strip() for u in os.environ.get("EMBIZ_SLACK_APPROVERS", "").split(",") if u.strip()}
REPORT_INTERVAL_S = int(os.environ.get("EMBIZ_REPORT_INTERVAL_S", "21600"))  # 6h

_web: WebClient | None = None
_bot_user_id: str | None = None


def _utcnow() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _append_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def log_transcript(direction: str, kind: str, payload: dict) -> None:
    """Responsibility 12 — durable transcript of every in/outbound message."""
    _append_jsonl(TRANSCRIPT, {
        "timestamp": _utcnow(), "direction": direction, "kind": kind,
        "payload": payload,
    })


# --------------------------------------------------------------------------
# Posting helpers (responsibilities 6, 8, 9, 13, 14, 15)
# --------------------------------------------------------------------------
def post_message(channel: str, text: str, blocks: list | None = None,
                 thread_ts: str | None = None) -> str | None:
    """Post to Slack with transcript logging. Returns message ts (or None)."""
    assert _web is not None
    try:
        resp = _web.chat_postMessage(channel=channel, text=text, blocks=blocks,
                                     thread_ts=thread_ts)
        log_transcript("outbound", "message",
                       {"channel": channel, "text": text, "ts": resp.get("ts")})
        return resp.get("ts")
    except Exception as exc:  # noqa: BLE001 — must never kill the daemon
        log.error("post_message to %s failed: %s", channel, exc)
        log_transcript("outbound", "message_failed",
                       {"channel": channel, "text": text, "error": str(exc)})
        return None


def post_job_status(job_id: str, status: str, detail: str = "") -> None:
    """Responsibility 6 — job status updates."""
    post_message(CH_JOBS, f":package: *{job_id}* status -> `{status}` {detail}")


def post_production(text: str) -> None:
    """Responsibility 8 — production notifications."""
    post_message(CH_JOBS, f":sewing_needle: PRODUCTION: {text}")


def post_error(source: str, exc: BaseException) -> None:
    """Responsibility 9 — error notifications (never silently swallowed)."""
    tb = "".join(traceback.format_exception(exc)).strip().splitlines()
    summary = "\n".join(tb[-6:])
    post_message(CH_ALERTS,
                 f":rotating_light: ERROR in `{source}`:\n```{summary}```")


def post_decision_trace(entry: dict) -> None:
    """Responsibility 13 — Slack-visible decision traces (also to ledger)."""
    entry.setdefault("timestamp", _utcnow())
    entry.setdefault("artifact", "decision_trace")
    _append_jsonl(DECISION_TRACE, entry)
    post_message(CH_JOBS,
                 f":brain: DECISION [{entry.get('agent', 'agent')}] "
                 f"{entry.get('decision', '')}: {entry.get('objective', '')}")


def post_qa_result(job_id: str, passed: bool, evidence: str) -> None:
    """Responsibility 14 — Slack-visible QA results."""
    icon = ":white_check_mark:" if passed else ":x:"
    post_message(CH_QA, f"{icon} QA *{job_id}* -> "
                        f"{'PASS' if passed else 'FAIL'}\n{evidence}")


# --------------------------------------------------------------------------
# Workflow triggering — filesystem job queue (responsibility 11)
# --------------------------------------------------------------------------
def enqueue_job(description: str, requested_by: str, task_type: str = "pipeline",
                params: dict | None = None) -> str:
    job_id = f"JOB-SL-{datetime.datetime.now(datetime.timezone.utc):%Y%m%d-%H%M%S}-{uuid.uuid4().hex[:6]}"
    QUEUE_PENDING.mkdir(parents=True, exist_ok=True)
    job = {
        "id": job_id, "created": _utcnow(), "description": description,
        "requested_by": requested_by, "task_type": task_type,
        "params": params or {}, "state": "pending",
    }
    tmp = QUEUE_PENDING / f".{job_id}.tmp"
    tmp.write_text(json.dumps(job, indent=2), encoding="utf-8")
    tmp.rename(QUEUE_PENDING / f"{job_id}.json")
    post_job_status(job_id, "queued", f"— {description} (by <@{requested_by}>)")
    return job_id


# --------------------------------------------------------------------------
# Approval / rejection handling (responsibilities 4 and 5)
# --------------------------------------------------------------------------
def _authorized(user: str) -> bool:
    if not APPROVERS:
        log.warning("EMBIZ_SLACK_APPROVERS unset — allowing user %s", user)
        return True
    return user in APPROVERS


def record_decision(job_id: str, decision: str, user: str, reason: str = "") -> bool:
    if not _authorized(user):
        post_message(CH_ALERTS,
                     f":lock: <@{user}> attempted `{decision}` on *{job_id}* "
                     f"but is not in the approver allowlist. Ignored.")
        return False
    APPROVALS_DECIDED.mkdir(parents=True, exist_ok=True)
    record = {"job_id": job_id, "decision": decision, "user": user,
              "reason": reason, "timestamp": _utcnow()}
    (APPROVALS_DECIDED / f"{job_id}.json").write_text(
        json.dumps(record, indent=2), encoding="utf-8")
    pending = APPROVALS_PENDING / f"{job_id}.json"
    if pending.exists():
        pending.unlink()
    post_decision_trace({
        "agent": "slack_daemon", "decision": f"human-gate-{decision}",
        "objective": f"{job_id} {decision} by {user}. {reason}".strip(),
    })
    post_job_status(job_id, decision, f"by <@{user}> {reason}")
    return True


def _job_for_approval_ts(ts: str) -> str | None:
    """Map an approval-request message ts back to its job (reaction approvals)."""
    if not APPROVALS_PENDING.exists():
        return None
    for f in APPROVALS_PENDING.glob("*.json"):
        try:
            if json.loads(f.read_text(encoding="utf-8")).get("slack_ts") == ts:
                return f.stem
        except (OSError, ValueError):
            continue
    return None


# --------------------------------------------------------------------------
# Status / reporting helpers (responsibility 10)
# --------------------------------------------------------------------------
def _queue_counts() -> dict:
    return {name: len(list(d.glob("*.json"))) if d.exists() else 0
            for name, d in (("pending", QUEUE_PENDING), ("active", QUEUE_ACTIVE),
                            ("done", QUEUE_DONE), ("failed", QUEUE_FAILED))}


def _paid_usage_total() -> int:
    audit = STATE_DIR / "paid_usage_audit.jsonl"
    if not audit.exists():
        return 0
    return sum(1 for _ in audit.open(encoding="utf-8"))


def build_ops_report() -> str:
    counts = _queue_counts()
    gpu = "up" if ollama_alive() else "DOWN"
    trace_lines = 0
    last_score = "n/a"
    if DECISION_TRACE.exists():
        for line in DECISION_TRACE.open(encoding="utf-8"):
            trace_lines += 1
            try:
                score = json.loads(line).get("overall_score")
                if score is not None:
                    last_score = f"{score:.4f}"
            except ValueError:
                pass
    return (
        f":clipboard: *EMBIZ operational report* ({_utcnow()})\n"
        f"• Queue: pending={counts['pending']} active={counts['active']} "
        f"done={counts['done']} failed={counts['failed']}\n"
        f"• Ollama/{PRIMARY_MODEL}: {gpu} (local GPU, 100% offload target)\n"
        f"• Latest OVERALL_SCORE: {last_score} "
        f"(decision_trace entries: {trace_lines})\n"
        f"• Paid API escalations to date: {_paid_usage_total()} "
        f"(see paid_usage_audit.jsonl)"
    )


def _reporting_thread(stop: threading.Event) -> None:
    """Responsibility 10 — scheduled operational reporting, forever."""
    while not stop.wait(REPORT_INTERVAL_S):
        try:
            post_message(CH_ALERTS, build_ops_report())
        except Exception as exc:  # noqa: BLE001
            log.error("ops report failed: %s", exc)


def _heartbeat_thread(stop: threading.Event) -> None:
    while not stop.wait(60):
        try:
            HEARTBEAT.parent.mkdir(parents=True, exist_ok=True)
            HEARTBEAT.write_text(json.dumps(
                {"timestamp": _utcnow(), "pid": os.getpid()}), encoding="utf-8")
        except OSError as exc:
            log.error("heartbeat write failed: %s", exc)


# --------------------------------------------------------------------------
# Command dispatch (responsibilities 2 and 3)
# --------------------------------------------------------------------------
def handle_command(text: str, user: str, channel: str) -> str:
    """Dispatch a command (from slash command or @mention). Returns reply text."""
    parts = text.strip().split(None, 1)
    cmd = parts[0].lower() if parts else "help"
    arg = parts[1].strip() if len(parts) > 1 else ""

    if cmd in ("status", "health"):
        return build_ops_report()
    if cmd in ("jobs", "queue"):
        counts = _queue_counts()
        pend = sorted(p.stem for p in QUEUE_PENDING.glob("*.json")) if QUEUE_PENDING.exists() else []
        return (f"Queue: {json.dumps(counts)}\n"
                + ("Pending: " + ", ".join(pend[:20]) if pend else "No pending jobs."))
    if cmd == "run":
        if not arg:
            return "Usage: run <task description>"
        job_id = enqueue_job(arg, requested_by=user)
        return f"Queued *{job_id}* — the agent loop will pick it up autonomously."
    if cmd == "approve":
        if not arg:
            return "Usage: approve JOB-ID"
        ok = record_decision(arg.split()[0], "approved", user)
        return f"Approval recorded for {arg.split()[0]}." if ok else "Not authorized."
    if cmd == "reject":
        bits = arg.split(None, 1)
        if not bits:
            return "Usage: reject JOB-ID [reason]"
        ok = record_decision(bits[0], "rejected", user,
                             reason=bits[1] if len(bits) > 1 else "")
        return f"Rejection recorded for {bits[0]}." if ok else "Not authorized."
    if cmd == "models":
        try:
            return "Local Ollama models: " + ", ".join(list_local_models())
        except Exception as exc:  # noqa: BLE001
            return f"Ollama unavailable: {exc}"
    if cmd == "report":
        return build_ops_report()
    if cmd == "ask":
        text = arg or "Introduce yourself briefly."
        return model_router.route("slack_reply", text)
    if cmd == "help":
        return ("Subcommands: status | health | jobs | queue | run <task> | "
                "approve JOB-ID | reject JOB-ID [reason] | ask <question> | "
                "report | models")
    # Free-form: let the local model interpret it (responsibility 2 / 7).
    return model_router.route(
        "slack_reply",
        f"A Slack user said: {text!r}. Reply helpfully as the EMBIZ agent. "
        f"If they are asking to run work, tell them to use "
        f"'/embiz run <task>' or say 'run <task>'.")


# --------------------------------------------------------------------------
# Socket Mode event processing (responsibility 1 and dispatcher)
# --------------------------------------------------------------------------
def process(client: SocketModeClient, req: SocketModeRequest) -> None:
    # Ack immediately — Slack requires ack within 3 seconds.
    client.send_socket_mode_response(
        SocketModeResponse(envelope_id=req.envelope_id))
    try:
        _process_inner(req)
    except Exception as exc:  # noqa: BLE001 — daemon must survive everything
        log.error("event processing failed: %s", exc, exc_info=True)
        post_error("slack_daemon.process", exc)


def _process_inner(req: SocketModeRequest) -> None:
    log_transcript("inbound", req.type, req.payload)

    if req.type == "slash_commands":  # responsibility 3
        p = req.payload
        reply = handle_command(p.get("text", ""), p.get("user_id", "?"),
                               p.get("channel_id", ""))
        post_message(p.get("channel_id", CH_JOBS), reply)
        return

    if req.type == "interactive":  # Block Kit approve/reject buttons (4, 5)
        p = req.payload
        if p.get("type") == "block_actions":
            user = (p.get("user") or {}).get("id", "?")
            for action in p.get("actions", []):
                action_id = action.get("action_id", "")
                value = action.get("value", "")
                if action_id == "embiz_approve":
                    record_decision(value, "approved", user)
                elif action_id == "embiz_reject":
                    record_decision(value, "rejected", user)
        return

    if req.type == "events_api":  # responsibility 1
        event = (req.payload.get("event") or {})
        etype = event.get("type")

        if etype == "reaction_added":  # reaction-based approvals (4, 5)
            ts = (event.get("item") or {}).get("ts", "")
            job_id = _job_for_approval_ts(ts)
            if job_id:
                user = event.get("user", "?")
                if event.get("reaction") in ("white_check_mark", "heavy_check_mark", "+1"):
                    record_decision(job_id, "approved", user)
                elif event.get("reaction") in ("x", "-1", "no_entry"):
                    record_decision(job_id, "rejected", user,
                                    reason="reaction rejection")
            return

        if etype in ("app_mention", "message"):  # responsibilities 2 and 7
            if event.get("bot_id") or event.get("subtype"):
                return  # ignore our own/bot/system messages
            text = event.get("text", "")
            if _bot_user_id:
                text = text.replace(f"<@{_bot_user_id}>", "").strip()
            if etype == "message" and event.get("channel_type") not in ("im",):
                return  # in channels, only respond to explicit mentions
            if not text:
                return
            reply = handle_command(text, event.get("user", "?"),
                                   event.get("channel", CH_JOBS))
            post_message(event.get("channel", CH_JOBS), reply,
                         thread_ts=event.get("thread_ts") or event.get("ts"))


# --------------------------------------------------------------------------
# Main — persistent daemon with reconnect logic
# --------------------------------------------------------------------------
def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s")

    bot_token = os.environ.get("SLACK_BOT_TOKEN")
    app_token = os.environ.get("SLACK_APP_TOKEN")
    if not bot_token or not app_token:
        log.error("SLACK_BOT_TOKEN and SLACK_APP_TOKEN are required "
                  "(Socket Mode). Configure ~/.config/embiz/env.")
        return 2

    global _web, _bot_user_id
    _web = WebClient(token=bot_token)
    _bot_user_id = _web.auth_test().get("user_id")

    for d in (QUEUE_PENDING, QUEUE_ACTIVE, QUEUE_DONE, QUEUE_FAILED,
              APPROVALS_PENDING, APPROVALS_DECIDED):
        d.mkdir(parents=True, exist_ok=True)

    stop = threading.Event()
    signal.signal(signal.SIGTERM, lambda *_: stop.set())
    signal.signal(signal.SIGINT, lambda *_: stop.set())
    threading.Thread(target=_reporting_thread, args=(stop,), daemon=True).start()
    threading.Thread(target=_heartbeat_thread, args=(stop,), daemon=True).start()

    post_message(CH_ALERTS,
                 f":satellite: EMBIZ Slack daemon online (Socket Mode, local "
                 f"{PRIMARY_MODEL}, host={os.uname().nodename}). "
                 f"Ollama: {'up' if ollama_alive() else 'DOWN'}.")

    # Outer reconnect loop: SocketModeClient auto-reconnects, but if the
    # connection object dies entirely we rebuild it rather than exiting.
    while not stop.is_set():
        sm = SocketModeClient(app_token=app_token, web_client=_web)
        sm.socket_mode_request_listeners.append(process)
        try:
            sm.connect()
            log.info("Socket Mode connected.")
            while not stop.is_set():
                time.sleep(5)
        except Exception as exc:  # noqa: BLE001
            log.error("Socket Mode connection failed: %s — retrying in 15s", exc)
            post_error("slack_daemon.connect", exc)
            time.sleep(15)
        finally:
            try:
                sm.close()
            except Exception:  # noqa: BLE001
                pass

    post_message(CH_ALERTS, ":zzz: EMBIZ Slack daemon shutting down (signal).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
