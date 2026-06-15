#!/usr/bin/env python3
import json, re
from pathlib import Path
from datetime import datetime

ROOT = Path("/root/embroidery_business_agent_system")
JOBS = ROOT / "jobs"
LOGS = ROOT / "logs"
STATE = ROOT / "state"

def now_iso():
    return datetime.now().isoformat()

def log_file(name, msg):
    LOGS.mkdir(parents=True, exist_ok=True)
    with open(LOGS / name, "a") as f:
        f.write(f"{now_iso()} {msg}\n")

def atomic_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)

def read_json(path, default=None):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return default if default is not None else {}

def write_if_missing(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(text, encoding="utf-8")

def parse_intake_summary(job_dir):
    job_dir = Path(job_dir)
    content = (job_dir / "intake_summary.md").read_text(encoding="utf-8", errors="replace") if (job_dir / "intake_summary.md").exists() else ""
    meta = {"job_id": job_dir.name, "from": "", "to": "", "subject": "", "received": ""}
    for line in content.splitlines():
        if line.startswith("- From:"):
            meta["from"] = line.split(":", 1)[1].strip()
        elif line.startswith("- To:"):
            meta["to"] = line.split(":", 1)[1].strip()
        elif line.startswith("- Subject:"):
            meta["subject"] = line.split(":", 1)[1].strip()
        elif line.startswith("- Received:"):
            meta["received"] = line.split(":", 1)[1].strip()
    body = content.split("## Body", 1)[1].strip() if "## Body" in content else ""
    return meta, body

def read_missing(job_dir):
    p = Path(job_dir) / "missing_questions.md"
    return p.read_text(encoding="utf-8", errors="replace").strip() if p.exists() else ""

def preview(text, limit=900):
    s = re.sub(r"\s+", " ", text or "").strip()
    return s[:limit] + ("..." if len(s) > limit else "")

def source_for_job(job_id):
    if job_id.startswith("JOB-CF-"):
        return "cloudflare_email"
    if job_id.startswith("JOB-WEB-"):
        return "web_form"
    if job_id.startswith("JOB-MANUAL-"):
        return "manual"
    return "unknown"
