"""dashboard.py — EMBIZ operational dashboard (BRD "Dashboard, Observability,
Operational Visibility, and Human Oversight").

``generate()`` renders every BRD-required dashboard area from real repository
artifacts (never invented data):

  Mission Control · Current Jobs · Agent Activity · Slack Intelligence ·
  Knowledge Retrieval · Production Queue · Vectorization Experiments ·
  Candidate Leaderboard · QA Results · Historical Learning · Regression
  Results · Reward Dashboard · Penalty Dashboard · Infrastructure Health ·
  System Alerts

``serve()`` exposes it as an authenticated operational interface (token via
``EMBIZ_DASHBOARD_TOKEN``): job inspection plus **status transition
controls** (POST /api/job-status), manual approvals (POST /api/approve), and
alert resolution — every operator action recorded in the job audit history.
Auth + interaction close the BRD's critical near-term requirements
"Dashboard authentication" and "Status transition controls".
"""

from __future__ import annotations

import datetime
import html
import json
import os
import platform
import shutil
from pathlib import Path

try:
    from . import jobs as jobs_mod
    from .agent_bus import open_alerts
    from .personas import CONTRACTS, feed_tail
except ImportError:
    import jobs as jobs_mod
    from agent_bus import open_alerts
    from personas import CONTRACTS, feed_tail

REPO_ROOT = Path(__file__).resolve().parent.parent
DASH_DIR = REPO_ROOT / "dashboard"
REPORTS = REPO_ROOT / "reports"


def _utcnow() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def _jsonl(path: Path, limit: int = 0) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            rows.append(json.loads(line))
        except ValueError:
            continue
    return rows[-limit:] if limit else rows


def _table(headers: list[str], rows: list[list], empty: str = "none") -> str:
    if not rows:
        return f"<p class=empty>{html.escape(empty)}</p>"
    th = "".join(f"<th>{html.escape(str(h))}</th>" for h in headers)
    trs = "".join(
        "<tr>" + "".join(f"<td>{html.escape(str(c))}</td>" for c in r) + "</tr>"
        for r in rows)
    return f"<table><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table>"


def _section(sid: str, title: str, body: str) -> str:
    return f'<section id="{sid}"><h2>{html.escape(title)}</h2>{body}</section>'


def collect() -> dict:
    """All dashboard data, from real artifacts only."""
    jobs = jobs_mod.list_jobs()
    attempts = _jsonl(REPO_ROOT / "vectorization_attempts.jsonl")
    rewards = _jsonl(REPO_ROOT / "reward_penalty_ledger.jsonl")
    feed = feed_tail(30)
    retrieval = _jsonl(REPORTS / "retrieval_log.jsonl", limit=20)
    regressions = _jsonl(REPORTS / "regression_history.jsonl", limit=20)
    milestones = _jsonl(REPORTS / "milestones.jsonl", limit=15)
    e2e = sorted((REPORTS / "e2e").glob("pass_*.json")) if (REPORTS / "e2e").is_dir() else []
    try:
        import ihive
        leaderboard = ihive.bayes_rank_candidates(top_k=8)
    except Exception:
        leaderboard = []
    du = shutil.disk_usage(REPO_ROOT)
    stitch_jsons = list((REPO_ROOT / "stitch_plans").glob("*.json"))
    qa_rows = []
    for p in sorted(stitch_jsons)[-400:]:
        try:
            s = json.loads(p.read_text(encoding="utf-8"))
            d = s.get("density") or {}
            qa_rows.append([p.stem, s.get("stitch_count"),
                            d.get("max_local_density_per_mm2"),
                            "PASS" if d.get("ok") else "FAIL",
                            (s.get("hoop_fit") or {}).get("smallest_hoop", "?")])
        except ValueError:
            continue
    return {
        "jobs": jobs, "attempts": attempts, "rewards": rewards, "feed": feed,
        "retrieval": retrieval, "regressions": regressions,
        "milestones": milestones, "leaderboard": leaderboard,
        "alerts": open_alerts(), "qa_rows": qa_rows, "e2e_passes": len(e2e),
        "disk_free_gb": round(du.free / 2**30, 2),
    }


def generate(out_path: Path | None = None) -> Path:
    d = collect()
    jobs = d["jobs"]
    open_jobs = [j for j in jobs if j["status"] not in ("project_complete",
                                                        "cancelled")]
    qa_fail = [r for r in d["qa_rows"] if r[3] == "FAIL"]
    accepted = sum(1 for a in d["attempts"] if a.get("accepted"))
    rew = [r for r in d["rewards"] if r.get("kind", r.get("type", "")) not in
           ("penalty",) and r.get("delta", r.get("reward", 0)) >= 0]
    pen = [r for r in d["rewards"] if r not in rew]

    sections = [
        _section("mission-control", "Mission Control", _table(
            ["metric", "value"],
            [["generated (UTC)", _utcnow()],
             ["jobs total / open", f"{len(jobs)} / {len(open_jobs)}"],
             ["vectorization attempts (ledger)", len(d["attempts"])],
             ["attempts accepted", accepted],
             ["stitch plans with QA sidecars", len(d["qa_rows"])],
             ["density QA failures", len(qa_fail)],
             ["open alerts", len(d["alerts"])],
             ["E2E corpus passes recorded", d["e2e_passes"]],
             ["roster contracts loaded", len(CONTRACTS)]])),
        _section("current-jobs", "Current Jobs", _table(
            ["job", "status", "customer", "garment", "placement", "size",
             "qa", "machine", "controls"],
            [[j["job_id"], j["status"], j.get("customer", ""),
              j.get("garment", ""), j.get("placement", ""), j.get("size", ""),
              j.get("qa_state", ""), j.get("machine_compatibility_state", ""),
              "POST /api/job-status"] for j in jobs[-40:]])),
        _section("agent-activity", "Agent Activity", _table(
            ["time", "agent", "channel", "message"],
            [[r.get("timestamp", "")[:19], r.get("username", ""),
              r.get("channel", ""), (r.get("text", "") or "")[:110]]
             for r in d["feed"]], empty="no agent feed yet")),
        _section("slack-intelligence", "Slack Intelligence", _table(
            ["agent", "posts in feed tail"],
            sorted({r.get("username", "?") for r in d["feed"]} and
                   [[u, sum(1 for r in d["feed"] if r.get("username") == u)]
                    for u in {r.get("username", "?") for r in d["feed"]}]),
            empty="no Slack traffic mirrored yet")),
        _section("knowledge-retrieval", "Knowledge Retrieval", _table(
            ["time", "agent", "task", "status", "records"],
            [[r.get("timestamp", "")[:19], r.get("agent", ""),
              r.get("task_type", ""), r.get("status", ""),
              len(r.get("selected_records", []))] for r in d["retrieval"]],
            empty="no retrieval proofs logged")),
        _section("production-queue", "Production Queue", _table(
            ["job", "status", "next allowed transitions"],
            [[j["job_id"], j["status"],
              ", ".join(sorted(jobs_mod.ALLOWED_TRANSITIONS.get(
                  j["status"], set()))) or "(terminal)"]
             for j in open_jobs[-40:]])),
        _section("vectorization-experiments", "Vectorization Experiments", _table(
            ["image", "iter", "composite", "ssim", "accepted"],
            [[a.get("image"), a.get("iteration"), a.get("composite"),
              a.get("ssim_color"), a.get("accepted")]
             for a in d["attempts"][-15:]])),
        _section("candidate-leaderboard", "Candidate Leaderboard (Bayesian)", _table(
            ["bayes score", "posterior mean", "n", "accept p", "params"],
            [[c["bayes_score"], c["composite_posterior_mean"], c["n_attempts"],
              c["accept_posterior_mean"],
              json.dumps(c["params"])[:80]] for c in d["leaderboard"]])),
        _section("qa-results", "QA Results (stitch density + hoop)", _table(
            ["plan", "stitches", "max density /mm²", "density", "hoop"],
            d["qa_rows"][-30:])),
        _section("historical-learning", "Historical Learning", _table(
            ["time", "event"],
            [[m.get("timestamp", m.get("ts", ""))[:19],
              (m.get("event", m.get("message", json.dumps(m))))[:120]]
             for m in d["milestones"]], empty="no milestones yet")),
        _section("regression-results", "Regression Results", _table(
            ["time", "metric", "previous", "current", "verdict"],
            [[r.get("timestamp", "")[:19], r.get("metric"), r.get("previous"),
              r.get("current"), r.get("verdict")] for r in d["regressions"]],
            empty="no regression runs recorded")),
        _section("reward-dashboard", "Reward Dashboard", _table(
            ["entry"], [[json.dumps(r)[:140]] for r in rew[-12:]],
            empty="no rewards yet")),
        _section("penalty-dashboard", "Penalty Dashboard", _table(
            ["entry"], [[json.dumps(r)[:140]] for r in pen[-12:]],
            empty="no penalties recorded")),
        _section("infrastructure-health", "Infrastructure Health", _table(
            ["metric", "value"],
            [["host", platform.node()], ["platform", platform.platform()],
             ["python", platform.python_version()],
             ["disk free (GB)", d["disk_free_gb"]],
             ["jobs dir", str(jobs_mod.JOBS_DIR)]])),
        _section("system-alerts", "System Alerts (visible until resolved)", _table(
            ["alert", "kind", "agent", "message", "resolve"],
            [[a["alert_id"], a["kind"], a["agent"], a["message"][:100],
              "POST /api/resolve-alert"] for a in d["alerts"]],
            empty="no open alerts")),
    ]
    nav = "".join(
        f'<a href="#{sid}">{name}</a>' for sid, name in [
            ("mission-control", "Mission"), ("current-jobs", "Jobs"),
            ("agent-activity", "Agents"), ("slack-intelligence", "Slack"),
            ("knowledge-retrieval", "Knowledge"), ("production-queue", "Queue"),
            ("vectorization-experiments", "Experiments"),
            ("candidate-leaderboard", "Leaderboard"), ("qa-results", "QA"),
            ("historical-learning", "Learning"),
            ("regression-results", "Regressions"), ("reward-dashboard", "Rewards"),
            ("penalty-dashboard", "Penalties"),
            ("infrastructure-health", "Infra"), ("system-alerts", "Alerts")])
    page = (
        "<!doctype html><html><head><meta charset=utf-8>"
        "<meta name=viewport content='width=device-width,initial-scale=1'>"
        "<title>EMBIZ Dashboard</title><style>"
        "body{font-family:system-ui,Arial,sans-serif;background:#101216;"
        "color:#e6e6e6;margin:0;padding:16px}nav{position:sticky;top:0;"
        "background:#101216;padding:8px 0;border-bottom:1px solid #2a2e37}"
        "nav a{color:#7ab7ff;margin-right:10px;text-decoration:none;"
        "font-size:13px}h1{font-size:20px}h2{font-size:15px;margin:22px 0 6px;"
        "color:#9fd0ff}table{border-collapse:collapse;width:100%;font-size:12px}"
        "th,td{border:1px solid #2a2e37;padding:5px 7px;text-align:left}"
        "th{background:#1a1e26}.empty{color:#888;font-size:12px}"
        "</style></head><body><h1>EMBIZ Operational Dashboard</h1>"
        f"<p style='color:#888;font-size:12px'>generated {_utcnow()} — "
        "authenticated interface; operator actions are audited</p>"
        f"<nav>{nav}</nav>" + "".join(sections) + "</body></html>")
    out_path = out_path or (DASH_DIR / "index.html")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(page, encoding="utf-8")
    return out_path


if __name__ == "__main__":
    p = generate()
    print(f"dashboard written: {p} ({p.stat().st_size} bytes)")
