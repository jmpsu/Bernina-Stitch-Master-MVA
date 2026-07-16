"""agent_bus.py — contract-structured agent events (Mallory's bus).

Implements the roster's uniform Slack/event requirements as enforced message
builders (see ``skills/references/slack-event-standard.md``):

* approval events state what was checked, how, why it passed, which files are
  approved, and which agent owns the next step — all five are required
  arguments, so a non-compliant approval cannot be constructed;
* rejection/escalation events state the failed gate, observed defect, likely
  cause, affected file, and requested next action — likewise required;
* every event is secret-sanitized (Mallory's no-secrets rule) and mirrored to
  the local agent feed via ``personas.post_as`` (Slack when configured, local
  transcript always), plus the job audit history when a job_id is given.
"""

from __future__ import annotations

import re
from pathlib import Path

try:  # package-relative when imported as local_agents.agent_bus
    from . import jobs as jobs_mod
    from .personas import CHANNELS, PERSONAS, post_as
except ImportError:  # flat import when run from local_agents/
    import jobs as jobs_mod
    from personas import CHANNELS, PERSONAS, post_as

# Anything token-shaped never leaves the process (Mallory: "no-secrets
# message sanitation").
_SECRET_PATTERNS = [
    re.compile(r"xox[baprs]-[A-Za-z0-9-]+"),          # Slack tokens
    re.compile(r"hooks\.slack\.com/services/\S+"),     # webhook URLs
    re.compile(r"(?i)bearer\s+[a-z0-9._-]{16,}"),
    re.compile(r"(?i)(api[_-]?key|token|secret|password)\s*[=:]\s*\S+"),
    re.compile(r"AKIA[0-9A-Z]{16}"),                   # AWS access keys
]


def sanitize(text: str) -> str:
    for pat in _SECRET_PATTERNS:
        text = pat.sub("[REDACTED]", text)
    return text


def _emit(agent: str, channel: str, text: str, job_id: str | None,
          action: str, detail: dict) -> dict:
    persona = PERSONAS.get(agent) or PERSONAS["maya"]
    text = sanitize(text)
    post_as(persona, channel, text=text)
    if job_id:
        try:
            jobs_mod._audit(job_id, action, detail, actor=agent)
        except (OSError, ValueError):
            pass  # events never break the pipeline
    return {"agent": agent, "channel": channel, "text": text, "action": action}


def status_event(agent: str, job_id: str | None, file: str, event: str,
                 note: str = "") -> dict:
    """File received / transformed / handed off — the routine status update."""
    text = (f"{event.upper()} — job {job_id or 'n/a'} — file `{file}`"
            + (f" — {note}" if note else ""))
    return _emit(agent, CHANNELS["jobs"], text, job_id, "status_event",
                 {"file": file, "event": event, "note": note})


def approval_event(agent: str, job_id: str | None, *, what_checked: str,
                   how_checked: str, why_passed: str, files: list[str],
                   next_owner: str) -> dict:
    """Contract-compliant approval. All five roster-required elements are
    mandatory keyword arguments — an approval without them cannot be built."""
    for name, val in [("what_checked", what_checked), ("how_checked", how_checked),
                      ("why_passed", why_passed), ("files", files),
                      ("next_owner", next_owner)]:
        if not val:
            raise ValueError(f"approval requires non-empty {name}")
    text = ("APPROVED — job {j}\n"
            "• what was checked: {w}\n"
            "• how it was checked: {h}\n"
            "• why it passed: {y}\n"
            "• files approved: {f}\n"
            "• next step owner: {n}").format(
        j=job_id or "n/a", w=what_checked, h=how_checked, y=why_passed,
        f=", ".join(files), n=next_owner)
    return _emit(agent, CHANNELS["qa"], text, job_id, "approval",
                 {"what": what_checked, "how": how_checked, "why": why_passed,
                  "files": files, "next_owner": next_owner})


def rejection_event(agent: str, job_id: str | None, *, failed_gate: str,
                    defect: str, likely_cause: str, file: str,
                    next_action: str) -> dict:
    """Contract-compliant rejection/escalation — all five elements required."""
    for name, val in [("failed_gate", failed_gate), ("defect", defect),
                      ("likely_cause", likely_cause), ("file", file),
                      ("next_action", next_action)]:
        if not val:
            raise ValueError(f"rejection requires non-empty {name}")
    text = ("REJECTED — job {j}\n"
            "• failed gate: {g}\n"
            "• observed defect: {d}\n"
            "• likely cause: {c}\n"
            "• affected file: {f}\n"
            "• requested next action: {n}").format(
        j=job_id or "n/a", g=failed_gate, d=defect, c=likely_cause, f=file,
        n=next_action)
    return _emit(agent, CHANNELS["qa"], text, job_id, "rejection",
                 {"gate": failed_gate, "defect": defect, "cause": likely_cause,
                  "file": file, "next_action": next_action})


ALERTS_PATH = Path(__file__).resolve().parent.parent / "reports" / "alerts.jsonl"


def alert_event(agent: str, kind: str, message: str,
                job_id: str | None = None) -> dict:
    """Operational alert (production/QA/infrastructure failure, missing
    knowledge/approval/artifact, pipeline interruption). Persisted to
    reports/alerts.jsonl and shown on the dashboard until resolved (BRD:
    "alerts shall remain visible until resolved")."""
    import datetime
    import json as _json
    import uuid
    alert = {"alert_id": uuid.uuid4().hex[:12],
             "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
             "agent": agent, "kind": kind, "message": sanitize(message),
             "job_id": job_id, "resolved": False}
    ALERTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with ALERTS_PATH.open("a", encoding="utf-8") as f:
        f.write(_json.dumps(alert) + "\n")
    _emit(agent, CHANNELS["alerts"], f"ALERT [{kind}] {message}",
          job_id, "alert", {"kind": kind, "message": message,
                            "alert_id": alert["alert_id"]})
    return alert


def resolve_alert(alert_id: str, actor: str = "operator") -> bool:
    """Mark an alert resolved (rewrites the ledger; the resolution is itself
    recorded with actor + timestamp)."""
    import datetime
    import json as _json
    if not ALERTS_PATH.exists():
        return False
    lines = ALERTS_PATH.read_text(encoding="utf-8").splitlines()
    changed = False
    out = []
    for line in lines:
        try:
            rec = _json.loads(line)
        except ValueError:
            continue
        if rec.get("alert_id") == alert_id and not rec.get("resolved"):
            rec["resolved"] = True
            rec["resolved_by"] = actor
            rec["resolved_at"] = datetime.datetime.now(
                datetime.timezone.utc).isoformat()
            changed = True
        out.append(_json.dumps(rec))
    if changed:
        ALERTS_PATH.write_text("\n".join(out) + "\n", encoding="utf-8")
    return changed


def open_alerts() -> list[dict]:
    import json as _json
    if not ALERTS_PATH.exists():
        return []
    out = []
    for line in ALERTS_PATH.read_text(encoding="utf-8").splitlines():
        try:
            rec = _json.loads(line)
            if not rec.get("resolved"):
                out.append(rec)
        except ValueError:
            continue
    return out


if __name__ == "__main__":
    ev = approval_event(
        "mackenzie", None, what_checked="SVG topology (9 checks)",
        how_checked="svg_topology_qa.py automated inventory",
        why_passed="0 stray objects, background clear, silhouette SSIM 0.97",
        files=["vectorized_svg/demo.svg"], next_owner="mckenna")
    print(ev["text"])
    try:
        approval_event("maya", None, what_checked="x", how_checked="y",
                       why_passed="", files=["f"], next_owner="z")
        raise SystemExit("FAIL: incomplete approval accepted")
    except ValueError as e:
        print("rejected as required:", e)
    print(sanitize("token=xoxb-123456789-abcdef and Bearer abcdefghij1234567890"))
