"""webhook_api.py — EMBIZ internal webhook API + authenticated dashboard.

Implements the BRD's internal API surface with the standard library only:

  GET  /                    operational dashboard (regenerated per request)
  GET  /api/jobs            job list (BRD "Job API")
  GET  /api/jobs/<id>       one job + its audit history
  POST /cloudflare-email    email-intake webhook (BRD "Email Intake Webhook")
                            body: {from, subject, body, customer?,
                                   attachments?: [{filename, content_b64}]}
                            Attachments carry base64 CONTENT, never server
                            paths — a remote caller cannot name a server file
                            to ingest.
  POST /api/job-status      status transition control (BRD "Job Status
                            Management"): {job_id, status, reason?} —
                            invalid transitions rejected with 409
  POST /api/approve         manual approval (roster-structured; all five
                            approval elements required)
  POST /api/resolve-alert   {alert_id} — alerts stay visible until resolved

Authentication (BRD critical requirement "Dashboard authentication"): every
request must present the token from ``EMBIZ_DASHBOARD_TOKEN`` as
``Authorization: Bearer <token>`` or ``?token=``. If the variable is unset a
random token is generated at startup and printed once. Every operator action
is recorded in the job audit history.
"""

from __future__ import annotations

import json
import os
import secrets
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

try:
    from . import dashboard, intake, jobs as jobs_mod
    from .agent_bus import approval_event, resolve_alert
except ImportError:
    import dashboard
    import intake
    import jobs as jobs_mod
    from agent_bus import approval_event, resolve_alert

TOKEN = os.environ.get("EMBIZ_DASHBOARD_TOKEN") or secrets.token_urlsafe(24)


class Handler(BaseHTTPRequestHandler):
    server_version = "EMBIZ/1.0"

    # --- helpers -------------------------------------------------------------
    def _authed(self) -> bool:
        auth = self.headers.get("Authorization", "")
        if auth.startswith("Bearer ") and secrets.compare_digest(
                auth[7:].strip(), TOKEN):
            return True
        qs = parse_qs(urlparse(self.path).query)
        return any(secrets.compare_digest(t, TOKEN)
                   for t in qs.get("token", []))

    def _send(self, code: int, body: bytes, ctype: str = "application/json"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code: int, obj) -> None:
        self._send(code, (json.dumps(obj, indent=2) + "\n").encode())

    def _body(self) -> dict:
        n = int(self.headers.get("Content-Length") or 0)
        if n <= 0 or n > 10 * 2**20:
            return {}
        try:
            return json.loads(self.rfile.read(n))
        except ValueError:
            return {}

    def log_message(self, fmt, *args):  # quiet default logging
        pass

    # --- routes ----------------------------------------------------------------
    def do_GET(self):
        if not self._authed():
            return self._json(401, {"error": "authentication required"})
        path = urlparse(self.path).path
        if path == "/":
            page = dashboard.generate()
            return self._send(200, page.read_bytes(), "text/html; charset=utf-8")
        if path == "/api/jobs":
            return self._json(200, {"jobs": jobs_mod.list_jobs()})
        if path.startswith("/api/jobs/"):
            jid = path.rsplit("/", 1)[1]
            try:
                return self._json(200, {"job": jobs_mod.load_job(jid),
                                        "audit": jobs_mod.audit_history(jid)})
            except (FileNotFoundError, ValueError):
                return self._json(404, {"error": f"unknown job {jid}"})
        return self._json(404, {"error": "not found"})

    def do_POST(self):
        if not self._authed():
            return self._json(401, {"error": "authentication required"})
        path = urlparse(self.path).path
        body = self._body()
        if path == "/cloudflare-email":
            if not body:
                return self._json(400, {"error": "JSON body required"})
            job = intake.run_intake(body)
            return self._json(201, {"job": job})
        if path == "/api/job-status":
            try:
                rec = jobs_mod.transition(
                    body["job_id"], body["status"], actor="operator",
                    reason=body.get("reason", "dashboard status control"))
                return self._json(200, {"job": rec})
            except KeyError as e:
                return self._json(400, {"error": f"missing field {e}"})
            except jobs_mod.InvalidTransition as e:
                return self._json(409, {"error": str(e)})
            except FileNotFoundError:
                return self._json(404, {"error": "unknown job"})
        if path == "/api/approve":
            try:
                ev = approval_event(
                    body.get("agent", "maya"), body.get("job_id"),
                    what_checked=body["what_checked"],
                    how_checked=body["how_checked"],
                    why_passed=body["why_passed"], files=body["files"],
                    next_owner=body["next_owner"])
                return self._json(200, {"approval": ev})
            except (KeyError, ValueError) as e:
                return self._json(400, {"error": str(e)})
        if path == "/api/resolve-alert":
            ok = resolve_alert(body.get("alert_id", ""), actor="operator")
            return self._json(200 if ok else 404, {"resolved": ok})
        return self._json(404, {"error": "not found"})


def serve(port: int = 8787):
    if not os.environ.get("EMBIZ_DASHBOARD_TOKEN"):
        print(f"[webhook_api] generated token: {TOKEN}")
    httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"[webhook_api] listening on http://127.0.0.1:{port} (authenticated)")
    httpd.serve_forever()


if __name__ == "__main__":
    import sys
    serve(int(sys.argv[1]) if len(sys.argv) > 1 else 8787)
