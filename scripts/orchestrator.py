#!/usr/bin/env python3
import sys
from pathlib import Path
from pipeline_utils import ROOT, JOBS, now_iso, atomic_json, read_json, write_if_missing, parse_intake_summary, read_missing, source_for_job, log_file

STAGES = ["requirements", "artwork_prep", "digitizer", "qa", "customer_reply"]

def task_text(stage, meta, missing):
    jid = meta.get("job_id","")
    subj = meta.get("subject","")
    sender = meta.get("from","")
    base = f"# {stage} task\n\nJob: {jid}\nFrom: {sender}\nSubject: {subj}\n\n"
    if stage == "requirements":
        return base + "Extract customer requirements without inventing details. Update requirements_extracted.md. Current missing questions:\n\n" + (missing or "None listed.") + "\n"
    if stage == "artwork_prep":
        return base + "Determine whether usable logo/artwork exists. Classify artwork. Never claim stitch-ready artwork without evidence.\n"
    if stage == "digitizer":
        return base + "Prepare digitizing plan only. Do not create or claim DST/PES files unless real files exist.\n"
    if stage == "qa":
        return base + "Review risks: tiny text, thin lines, colors, missing garment, missing artwork, placement, deadline.\n"
    if stage == "customer_reply":
        return base + "Draft customer reply only. Never send. Ask only necessary missing questions.\n"
    return base

def init_job(job_dir):
    job_dir = Path(job_dir)
    if not (job_dir / "intake_summary.md").exists():
        raise FileNotFoundError(f"missing intake_summary.md for {job_dir}")
    meta, body = parse_intake_summary(job_dir)
    meta["job_id"] = job_dir.name
    missing = read_missing(job_dir)
    stages_state = {}
    for stage in STAGES:
        sd = job_dir / "pipeline" / stage
        sd.mkdir(parents=True, exist_ok=True)
        write_if_missing(sd / "task.md", task_text(stage, meta, missing))
        if stage == "customer_reply":
            write_if_missing(sd / "draft.md", "Status: Not drafted yet.\n")
        else:
            write_if_missing(sd / "output.md", "Status: Not completed yet.\n")
        status = "ready" if stage == "requirements" else "waiting"
        if not (sd / "status.json").exists():
            atomic_json(sd / "status.json", {"stage": stage, "status": status, "updated": now_iso()})
        stages_state[stage] = {"status": status, "assigned_agent": stage, "task_file": f"pipeline/{stage}/task.md"}
    od = job_dir / "pipeline" / "orchestrator"
    od.mkdir(parents=True, exist_ok=True)
    write_if_missing(od / "timeline.md", f"# Orchestrator timeline\n\n- {now_iso()} pipeline initialized for {job_dir.name}\n")
    write_if_missing(od / "decisions.md", "# Decisions\n\n- No autonomous email sending.\n- No paid LLM use.\n- No fake digitizing output.\n")
    write_if_missing(od / "handoff_log.md", "# Handoff log\n\n- requirements: ready\n- artwork_prep: waiting\n- digitizer: waiting\n- qa: waiting\n- customer_reply: waiting\n")
    state = read_json(job_dir / "job_state.json", {})
    state.update({
        "job_id": job_dir.name,
        "status": "needs_review",
        "source": source_for_job(job_dir.name),
        "created": meta.get("received") or "",
        "watcher_seen": state.get("watcher_seen") or now_iso(),
        "pipeline_initialized": True,
        "current_stage": "requirements",
        "stages": stages_state,
        "approval_required_before_customer_contact": True,
        "approval_required_before_digitizing": True,
        "paid_model_use_allowed": False,
        "customer_email_auto_send_allowed": False,
        "updated": now_iso()
    })
    atomic_json(job_dir / "job_state.json", state)
    log_file("orchestrator.log", f"INIT {job_dir.name}")
    print(job_dir.name)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--backfill":
        for j in sorted(JOBS.glob("JOB-*")):
            try:
                init_job(j)
            except Exception as e:
                log_file("orchestrator.log", f"BACKFILL_ERROR {j.name} {e}")
    elif len(sys.argv) > 1:
        init_job(sys.argv[1])
    else:
        sys.exit("usage: orchestrator.py JOB_DIR | --backfill")
