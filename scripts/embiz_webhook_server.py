#!/usr/bin/env python3
import os, sys, subprocess, json, glob
from http.server import BaseHTTPRequestHandler, HTTPServer

ROOT = "/root/embroidery_business_agent_system"
SECRET = os.environ.get("EMBIZ_WEBHOOK_SECRET","")

def get_jobs():
    jobs = []
    for d in sorted(glob.glob(ROOT+"/jobs/JOB-*"), key=os.path.getmtime, reverse=True):
        job_id = os.path.basename(d)
        summary_file = d+"/intake_summary.md"
        job = {"id": job_id, "from": "", "to": "", "subject": "", "received": ""}
        if os.path.exists(summary_file):
            with open(summary_file) as f:
                content = f.read()
            for line in content.split("\n"):
                if line.startswith("- From:"):
                    job["from"] = line.split(":",1)[1].strip()
                elif line.startswith("- To:"):
                    job["to"] = line.split(":",1)[1].strip()
                elif line.startswith("- Subject:"):
                    job["subject"] = line.split(":",1)[1].strip()
                elif line.startswith("- Received:"):
                    job["received"] = line.split(":",1)[1].strip()
                elif line.startswith("## Body"):
                    break
        jobs.append(job)
    return jobs

class H(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        try:
            open(ROOT+"/logs/webhook_access.log","a").write(fmt%args+"\n")
        except:
            pass

    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type","application/json")
        self.send_header("Access-Control-Allow-Origin","*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def send_file(self, path, content_type, status=200):
        if not os.path.exists(path):
            self.send_error(404)
            return
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.end_headers()
        with open(path,"rb") as f:
            self.wfile.write(f.read())

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Access-Control-Allow-Methods","GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers","Content-Type, X-Embiz-Secret")
        self.end_headers()

    def do_GET(self):
        p = self.path
        if p == "/":
            self.send_response(302)
            self.send_header("Location", "/dashboard")
            self.end_headers()
            return
        if p == "/health":
            self.send_response(200); self.end_headers(); self.wfile.write(b"ok\n"); return
        if p == "/dashboard" or p == "/dashboard/":
            self.send_file(ROOT+"/dashboard/index.html","text/html"); return
        if p == "/form" or p == "/form/":
            self.send_file(ROOT+"/web/form.html","text/html"); return
        if p == "/api/jobs":
            self.send_json(get_jobs()); return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if self.path != "/cloudflare-email":
            self.send_response(404); self.end_headers(); return
        if self.headers.get("X-Embiz-Secret","") != SECRET:
            self.send_response(403); self.end_headers(); self.wfile.write(b"forbidden\n"); return
        n = int(self.headers.get("Content-Length","0") or 0)
        body = self.rfile.read(n)
        p = subprocess.run([ROOT+"/scripts/cloudflare_email_to_job.py"], input=body, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if p.returncode != 0:
            open(ROOT+"/logs/webhook_error.log","ab").write(p.stderr+b"\n")
            self.send_response(500); self.end_headers(); self.wfile.write(b"error\n"); return
        self.send_response(200); self.end_headers(); self.wfile.write(p.stdout)

HTTPServer(("127.0.0.1", int(os.environ.get("EMBIZ_WEBHOOK_PORT","8787"))), H).serve_forever()
