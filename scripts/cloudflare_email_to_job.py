#!/usr/bin/env python3
import json, sys, pathlib, datetime, re, os
ROOT=pathlib.Path("/root/embroidery_business_agent_system")
INBOX=ROOT/"inbox/cloudflare"
JOBS=ROOT/"jobs"
INBOX.mkdir(parents=True, exist_ok=True)
JOBS.mkdir(parents=True, exist_ok=True)
raw=sys.stdin.read()
ts=datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
(INBOX/f"cloudflare-email-{ts}.json").write_text(raw)
try:
    data=json.loads(raw)
except Exception:
    data={"raw":raw}
sender=data.get("from") or data.get("sender") or "UNKNOWN_SENDER"
to=data.get("to") or "info@jupiterembroideryco.com"
subject=data.get("subject") or "No subject"
body=data.get("text") or data.get("body") or data.get("raw") or ""
safe=re.sub(r"[^A-Za-z0-9._@ -]+"," ",subject)[:120]
job_id="JOB-CF-"+ts
job_dir=JOBS/job_id
job_dir.mkdir(parents=True, exist_ok=True)
(job_dir/"raw_email.json").write_text(json.dumps(data, indent=2))
(job_dir/"intake_summary.md").write_text(f"# Cloudflare Email Intake\n\n- Job ID: {job_id}\n- From: {sender}\n- To: {to}\n- Subject: {subject}\n- Received: {datetime.datetime.now().isoformat()}\n\n## Body\n\n{body}\n")
(job_dir/"job.json").write_text(json.dumps({"job_id":job_id,"source":"cloudflare_email","from":sender,"to":to,"subject":subject,"status":"needs_review","created":datetime.datetime.now().isoformat()}, indent=2))
(job_dir/"missing_questions.md").write_text("# Missing Questions\n\n- Confirm garment type\n- Confirm quantity\n- Confirm logo/artwork file\n- Confirm placement\n- Confirm thread colors\n- Confirm deadline\n")
msg=f"NEW CLOUDFLARE EMAIL JOB: {job_id} | From: {sender} | Subject: {subject}"
os.system(f"agent-msg send cloudflare_intake orchestrator {json.dumps(msg)!r} >/dev/null 2>&1 || true")
os.system(f"openclaw-slack {json.dumps(msg)!r} >/dev/null 2>&1 || true")
print(job_id)
