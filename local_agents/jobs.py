"""jobs.py — canonical EMBIZ job records + enforced status transitions.

Implements the BRD's "Job Status Management" requirement: the allowed
state-transition chain is enforced (invalid transitions rejected), and every
transition is recorded in the project audit history
(``jobs/<job_id>/audit.jsonl``).

The status taxonomy is the existing system's 22-state set (see the
``mila/embiz-agent-system`` snapshot dashboard), of which the BRD explicitly
specifies the production chain from ``artwork_review`` onward. The canonical
job record carries the fields Maya's contract requires: customer-provided
image, garment/fabric, placement, size, thread colors, deadline, quote state,
SVG state, stitch-file state, QA state, machine-compatibility state.
"""

from __future__ import annotations

import datetime
import json
import os
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
JOBS_DIR = Path(os.environ.get("EMBIZ_JOBS_DIR", REPO_ROOT / "jobs"))

# BRD § Job Status Management — allowed transitions (exact list), preceded by
# the existing system's intake states feeding into artwork_review.
ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "new_intake": {"requirements_extracted", "needs_customer_info"},
    "requirements_extracted": {"needs_customer_info", "artwork_needed",
                               "artwork_received"},
    "needs_customer_info": {"requirements_extracted", "artwork_needed"},
    "artwork_needed": {"artwork_received"},
    "artwork_received": {"artwork_review"},
    "artwork_review": {"artwork_approved"},
    "artwork_approved": {"digitizing_plan"},
    "digitizing_plan": {"digitizing_in_progress"},
    "digitizing_in_progress": {"stitch_file_ready"},
    "stitch_file_ready": {"qa_review"},
    "qa_review": {"qa_passed"},
    "qa_passed": {"customer_approval_needed"},
    "customer_approval_needed": {"approved_for_production"},
    "approved_for_production": {"with_sarah_for_embroidery"},
    "with_sarah_for_embroidery": {"embroidering_on_bernina"},
    "embroidering_on_bernina": {"embroidered_complete"},
    "embroidered_complete": {"ready_for_pickup_or_shipping"},
    "ready_for_pickup_or_shipping": {"sent_to_customer"},
    "sent_to_customer": {"project_complete"},
    "project_complete": set(),
    "blocked": set(),      # resolved via explicit unblock (restores held state)
    "cancelled": set(),
}
ALL_STATUSES = set(ALLOWED_TRANSITIONS)
# blocked / cancelled reachable from any live state.
TERMINAL = {"project_complete", "cancelled"}


class InvalidTransition(ValueError):
    """Raised when a status transition is not in the allowed chain."""


def _utcnow() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _job_dir(job_id: str) -> Path:
    # job_id may arrive from HTTP bodies: strict charset (no separators),
    # then a normpath+prefix containment check so no constructed path can
    # escape JOBS_DIR even if the charset rule ever loosens.
    if not re.fullmatch(r"JOB-[A-Za-z0-9_-]+", job_id) or ".." in job_id:
        raise ValueError(f"bad job_id: {job_id!r}")
    base = os.path.normpath(str(JOBS_DIR))
    cand = os.path.normpath(os.path.join(base, job_id))
    if not cand.startswith(base + os.sep):
        raise ValueError(f"job_id escapes jobs dir: {job_id!r}")
    return Path(cand)


def new_job_id(stamp: str | None = None) -> str:
    stamp = stamp or datetime.datetime.now(
        datetime.timezone.utc).strftime("%Y%m%d-%H%M%S%f")[:-3]
    return f"JOB-{stamp}"


def create_job(source: str, customer: str = "", email: str = "",
               subject: str = "", artwork: str = "",
               requirements: dict | None = None,
               job_id: str | None = None) -> dict:
    """Create the canonical job record (status ``new_intake``) on disk."""
    job_id = job_id or new_job_id()
    record = {
        "job_id": job_id,
        "status": "new_intake",
        "created": _utcnow(),
        "source": source,                     # email | file_drop | slack | api
        "customer": customer,
        "email": email,
        "subject": subject,
        # Maya's canonical job-record fields (BRD roster).
        "customer_image": artwork,            # source-of-truth reference
        "garment": (requirements or {}).get("garment", ""),
        "garment_color": (requirements or {}).get("garment_color", ""),
        "placement": (requirements or {}).get("placement", ""),
        "size": (requirements or {}).get("size", ""),
        "thread_colors": (requirements or {}).get("thread_colors", []),
        "quantity": (requirements or {}).get("quantity", ""),
        "deadline": (requirements or {}).get("deadline", ""),
        "quote_state": "not_quoted",
        "svg_state": "none",
        "stitch_file_state": "none",
        "qa_state": "none",
        "machine_compatibility_state": "none",
        "owner": "maya",
    }
    d = _job_dir(job_id)
    d.mkdir(parents=True, exist_ok=True)
    _write_record(record)
    _audit(job_id, "created", {"source": source, "status": "new_intake"})
    return record


def _record_path(job_id: str) -> Path:
    return _job_dir(job_id) / "job.json"


def _write_record(record: dict) -> None:
    _record_path(record["job_id"]).write_text(
        json.dumps(record, indent=2) + "\n", encoding="utf-8")


def load_job(job_id: str) -> dict:
    return json.loads(_record_path(job_id).read_text(encoding="utf-8"))


def list_jobs() -> list[dict]:
    if not JOBS_DIR.is_dir():
        return []
    out = []
    for d in sorted(JOBS_DIR.iterdir()):
        p = d / "job.json"
        if p.exists():
            try:
                out.append(json.loads(p.read_text(encoding="utf-8")))
            except ValueError:
                continue
    return out


def _audit(job_id: str, action: str, detail: dict, actor: str = "system") -> None:
    entry = {"timestamp": _utcnow(), "job_id": job_id, "actor": actor,
             "action": action, **detail}
    with (_job_dir(job_id) / "audit.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def audit_history(job_id: str) -> list[dict]:
    p = _job_dir(job_id) / "audit.jsonl"
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def transition(job_id: str, new_status: str, actor: str = "system",
               reason: str = "", **field_updates) -> dict:
    """Move a job to ``new_status``; invalid transitions raise
    InvalidTransition; every transition is audited."""
    record = load_job(job_id)
    current = record["status"]
    if new_status not in ALL_STATUSES:
        raise InvalidTransition(f"unknown status {new_status!r}")
    if new_status in ("blocked", "cancelled"):
        if current in TERMINAL:
            raise InvalidTransition(f"{current} is terminal")
        record["held_status"] = current
    elif current == "blocked" and new_status == record.get("held_status"):
        pass  # explicit unblock back to the held state
    elif new_status not in ALLOWED_TRANSITIONS.get(current, set()):
        raise InvalidTransition(
            f"{current} -> {new_status} is not an allowed transition")
    record["status"] = new_status
    record["updated"] = _utcnow()
    for k, v in field_updates.items():
        if k in record:
            record[k] = v
    _write_record(record)
    _audit(job_id, "status_transition",
           {"from": current, "to": new_status, "reason": reason}, actor)
    return record


if __name__ == "__main__":
    import tempfile
    JOBS_DIR = Path(tempfile.mkdtemp()) / "jobs"
    r = create_job("file_drop", customer="Smoke Test", artwork="x.png")
    jid = r["job_id"]
    chain = ["requirements_extracted", "artwork_received", "artwork_review",
             "artwork_approved", "digitizing_plan", "digitizing_in_progress",
             "stitch_file_ready", "qa_review", "qa_passed"]
    for s in chain:
        transition(jid, s, actor="smoke")
    try:
        transition(jid, "project_complete")
        raise SystemExit("FAIL: invalid transition accepted")
    except InvalidTransition as e:
        print("rejected as required:", e)
    print("final:", load_job(jid)["status"], "| audit entries:",
          len(audit_history(jid)))
