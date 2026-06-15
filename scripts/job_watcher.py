#!/usr/bin/env python3
import sys, time, subprocess, traceback
from pathlib import Path
from pipeline_utils import ROOT, JOBS, STATE, now_iso, atomic_json, read_json, parse_intake_summary, read_missing, preview, source_for_job, log_file

SEEN = STATE / "job_watcher_seen.json"
ORCH = ROOT / "scripts" / "orchestrator.py"
SLACK = Path("/usr/local/bin/openclaw-slack")
AGENT = Path("/usr/local/bin/agent-msg")

def load_seen():
    data = read_json(SEEN, {"seen_jobs": {}})
    if "seen_jobs" not in data:
        data = {"seen_jobs": {}}
    return data

def save_seen(data):
    atomic_json(SEEN, data)

def send_slack(message):
    try:
        if not SLACK.exists():
            log_file("slack_notifications.log", "MISSING openclaw-slack")
            return False
        r = subprocess.run([str(SLACK), message], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=25)
        log_file("slack_notifications.log", f"SLACK rc={r.returncode} stdout={r.stdout.strip()} stderr={r.stderr.strip()}")
        return r.returncode == 0
    except Exception as e:
        log_file("slack_notifications.log", f"SLACK_EXCEPTION {e}")
        return False

def send_agent(job_id):
    try:
        if AGENT.exists():
            subprocess.run([str(AGENT), "send", "job_watcher", "orchestrator", f"NEW_JOB {job_id} status=needs_review"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
    except Exception as e:
        log_file("job_watcher.log", f"AGENT_MSG_FAIL {job_id} {e}")

def build_slack_message(job_dir):
    meta, body = parse_intake_summary(job_dir)
    missing = read_missing(job_dir)
    return (
        "🧵 New Embroidery Job Received\n\n"
        f"Job ID: {job_dir.name}\n"
        f"Source: {source_for_job(job_dir.name)}\n"
        f"From: {meta.get('from') or 'UNKNOWN'}\n"
        f"To: {meta.get('to') or 'UNKNOWN'}\n"
        f"Subject: {meta.get('subject') or 'No subject'}\n\n"
        f"Preview:\n{preview(body, 900)}\n\n"
        "Status: needs_review\n\n"
        f"Missing questions:\n{missing or 'None listed.'}\n\n"
        "Dashboard:\nhttps://embiz-hook.jupiterembroideryco.com/dashboard\n\n"
        f"Server path:\n{job_dir}"
    )

def process_job(job_dir, seen):
    job_id = job_dir.name
    rec = seen["seen_jobs"].get(job_id)
    if rec and rec.get("slack_notified"):
        return
    if not (job_dir / "intake_summary.md").exists():
        log_file("job_watcher.log", f"WAIT_INCOMPLETE {job_id}")
        return
    if time.time() - job_dir.stat().st_mtime < 2:
        return
    subprocess.run([sys.executable, str(ORCH), str(job_dir)], check=True, timeout=60)
    phase2 = ROOT / "scripts" / "phase2_requirements_and_reply.py"
    phase2_ok = False
    if phase2.exists():
        try:
            subprocess.run([sys.executable, str(phase2), str(job_dir)], check=True, timeout=60)
            phase2_ok = True
            log_file("job_watcher.log", f"PHASE2_OK {job_id}")
        except Exception as e:
            log_file("job_watcher.log", f"PHASE2_FAIL {job_id} {e}")
    state = {}
    try:
        import json
        state = json.loads((job_dir / "job_state.json").read_text())
    except Exception:
        state = {}
    draft_path = job_dir / "pipeline" / "customer_reply" / "draft.md"
    draft_preview = ""
    if draft_path.exists():
        draft_preview = "\n\nDraft reply preview:\n" + draft_path.read_text(errors="replace")[:900]
    ok = send_slack(
        build_slack_message(job_dir)
        + ("\\n\\nPhase 2: requirements extracted + customer reply draft ready" if phase2_ok else "\\n\\nPhase 2: not completed")
        + "\nPipeline status: " + str(state.get("pipeline_status") or state.get("status") or "needs_review")
        + "\nCurrent owner: " + str(state.get("current_owner") or "joey_review")
        + "\nNext action: " + str(state.get("next_action") or "Review job")
        + draft_preview
    )
    dash = ROOT / "scripts" / "embiz_refresh_dashboard.py"
    if dash.exists():
        try:
            subprocess.run([sys.executable, str(dash)], check=False, timeout=30)
            log_file("job_watcher.log", f"DASHBOARD_REFRESH_OK {job_id}")
        except Exception as e:
            log_file("job_watcher.log", f"DASHBOARD_REFRESH_FAIL {job_id} {e}")
    send_agent(job_id)
    seen["seen_jobs"][job_id] = {"first_seen": rec.get("first_seen") if rec else now_iso(), "processed": True, "slack_notified": ok, "pipeline_initialized": True, "last_attempt": now_iso()}
    save_seen(seen)
    log_file("job_watcher.log", f"PROCESSED {job_id} slack={ok}")

def main():
    STATE.mkdir(parents=True, exist_ok=True)
    log_file("job_watcher.log", "START")
    while True:
        try:
            seen = load_seen()
            for job_dir in sorted(JOBS.glob("JOB-*"), key=lambda p: p.stat().st_mtime):
                process_job(job_dir, seen)
        except Exception as e:
            log_file("job_watcher.log", f"LOOP_ERROR {e} {traceback.format_exc()}")
        time.sleep(5)

if __name__ == "__main__":
    main()
