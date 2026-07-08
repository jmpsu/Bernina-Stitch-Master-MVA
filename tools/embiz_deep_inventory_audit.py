#!/usr/bin/env python3
"""embiz_deep_inventory_audit.py

Local-first EMBIZ inventory/audit tool.

It does not change the repo, start services, fetch URLs, merge PRs, or modify
Cloudflare. It inspects the current checkout and writes:

    reports/embiz_deep_inventory.json
    reports/embiz_deep_inventory.md

Run from the repository root:

    python3 tools/embiz_deep_inventory_audit.py --expected-pr 5

Optional: install/authenticate `gh` before running for live GitHub PR metadata.
Without `gh`, the GitHub section is reported as unavailable rather than guessed.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Any

EXPECTED_URLS = [
    "http://tavmjong.free.fr/INKSCAPE/MANUAL/html/Glossary.html#svg",
    "http://tavmjong.free.fr/INKSCAPE/MANUAL/html/",
    "https://sketchpad.net/",
    "https://sketchpad.net/drawing1.htm",
    "https://sketchpad.net/drawing2.htm",
    "https://sketchpad.net/drawing3.htm",
    "https://sketchpad.net/drawing3a.htm",
    "https://sketchpad.net/drawing4.htm",
    "https://sketchpad.net/drawing5.htm",
    "https://sketchpad.net/drawing6.htm",
    "https://sketchpad.net/drawing7.htm",
    "https://sketchpad.net/drawing8.htm",
    "https://sketchpad.net/drawing9.htm",
    "https://sketchpad.net/drawing10.htm",
    "https://sketchpad.net/drawing11.htm",
    "https://inkscape.gitlab.io/extensions/documentation/",
    "https://inkscape.gitlab.io/extensions/documentation/source/index.html",
    "https://github.com/Kauhentus/inkscape-cli",
    "https://github.com/The3DSquare/inkscape-cli",
    "https://www.npmjs.com/package/inkscape-cli",
    "https://inkscape.org/forums/embroidery/",
    "https://potrace.sourceforge.net/",
    "https://www.w3.org/TR/SVG11/",
    "https://www.w3.org/TR/SVG2/",
]

EXPECTED_CORPORA: dict[str, str] = {
    "raster-to-vector": "5-agent-architecture/raster-to-vector-agent",
    "vector-design": "5-agent-architecture/vector-design-agent",
    "visual-semantics": "5-agent-architecture/visual-semantics-corpus",
    "svg-specification": "9-knowledge-management-architecture/svg-specification-corpus",
    "inkscape": "9-knowledge-management-architecture/inkscape-corpus",
    "svg-conformance": "9-knowledge-management-architecture/svg-conformance-corpus",
    "ink-stitch-docs": "14-ink-stitch-automation-framework/documents",
    "embroidery-techniques": "14-ink-stitch-automation-framework/embroidery-techniques",
    "bernina-b700": "10-machine-integration/bernina-b700-corpus",
    "visual-qa": "12-quality-assurance/visual-qa-corpus",
    "global": ".",
}

AGENT_REQUIREMENTS: dict[str, dict[str, list[str]]] = {
    "mila": {"required": ["raster-to-vector", "vector-design"], "optional": ["visual-semantics", "global"]},
    "melanie": {"required": ["vector-design", "svg-specification"], "optional": ["inkscape", "svg-conformance", "global"]},
    "mckenna": {"required": ["ink-stitch-docs", "embroidery-techniques"], "optional": ["bernina-b700", "global"]},
    "meredith": {"required": ["ink-stitch-docs", "embroidery-techniques"], "optional": ["global"]},
    "miranda": {"required": ["bernina-b700"], "optional": ["embroidery-techniques", "global"]},
    "mackenzie": {"required": ["visual-qa"], "optional": ["visual-semantics", "global"]},
    "monica": {"required": ["global"], "optional": list(EXPECTED_CORPORA)},
    "maya": {"required": ["raster-to-vector", "vector-design"], "optional": ["visual-semantics", "global"]},
    "marnie": {"required": ["ink-stitch-docs", "embroidery-techniques", "bernina-b700"], "optional": ["global"]},
    "mercy": {"required": ["visual-qa"], "optional": ["visual-semantics", "global"]},
    "mabel": {"required": ["global"], "optional": list(EXPECTED_CORPORA)},
    "mira": {"required": [], "optional": ["global"]},
    "margo": {"required": [], "optional": ["global"]},
    "minerva": {"required": [], "optional": ["global"]},
}

CLOUDFLARE_AWS_EXPECTED_SURFACE = [
    "wrangler.toml",
    "functions/_middleware.ts",
    "functions/api/quote.ts",
    "functions/api/order.ts",
    "functions/api/upload.ts",
    "functions/api/contact.ts",
    "terraform/main.tf",
    "terraform/variables.tf",
    "terraform/outputs.tf",
    ".github/workflows/deploy-cloudflare-pages.yml",
    ".github/workflows/deploy-aws.yml",
    "aws/lambdas/",
    "package.json",
]

RUNTIME_FILES = [
    "vectorizer.py",
    "digitizer.py",
    "run_iteration.py",
    "metrics.py",
    "local_agents/continuous_run.py",
    "local_agents/knowledge_ingest.py",
    "local_agents/knowledge_retrieval.py",
    "local_agents/model_router.py",
    "local_agents/qwen_client.py",
    "local_agents/slack_daemon.py",
    "local_agents/agent_loop.py",
    "local_agents/personas.py",
]

RUNTIME_PATTERNS = {
    "knowledge_root_discovery": ["discover_library_roots", "EMBIZ_KNOWLEDGE_ROOTS", "global_knowledge_objects.multimodal.jsonl"],
    "retrieval_gate_enforcement": ["MISSING_REQUIRED_CORPUS", "KnowledgeGateError", "strict=True", "retrieval_log.jsonl"],
    "finalization_retrieval_wiring": ["_finalization_retrievals", "mabel_knowledge_pass", "knowledge_fetch", "route("],
    "vectorizer_learning": ["parameter_correlation_index_vec.json", "vectorization_attempts.jsonl", "_seed_from_index", "_log_attempt"],
    "cross_order_transplant_pr5": ["plan_config_transplant", "TRANSPLANT_MIN_COMPOSITE", "extra_starts", "skip_preset_starts"],
    "qwen_local_first": ["qwen3:8b", "Ollama", "model_router", "EMBIZ_LOCAL_MODEL"],
    "slack_operation": ["Socket Mode", "SLACK_BOT_TOKEN", "files_upload_v2", "reports/slack_messages"],
    "cloudflare_customer_surface": ["wrangler", "cloudflare", "DurableObject", "Worker", "D1", "R2", "Vectorize"],
}


def now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def run(cmd: list[str], cwd: Path, timeout: int = 30) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            cmd, cwd=str(cwd), text=True, capture_output=True, timeout=timeout
        )
        return {
            "cmd": cmd,
            "returncode": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
            "ok": proc.returncode == 0,
        }
    except FileNotFoundError as exc:
        return {"cmd": cmd, "ok": False, "returncode": None, "stdout": "", "stderr": str(exc)}
    except subprocess.TimeoutExpired as exc:
        return {
            "cmd": cmd,
            "ok": False,
            "returncode": None,
            "stdout": (exc.stdout or "").strip() if isinstance(exc.stdout, str) else "",
            "stderr": f"timeout after {timeout}s",
        }


def repo_root_from(start: Path) -> Path:
    got = run(["git", "rev-parse", "--show-toplevel"], start)
    if got["ok"] and got["stdout"]:
        return Path(got["stdout"]).resolve()
    return start.resolve()


def safe_read(path: Path, max_bytes: int = 2_000_000) -> str:
    try:
        if not path.is_file() or path.stat().st_size > max_bytes:
            return ""
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def count_jsonl(path: Path) -> dict[str, Any]:
    info: dict[str, Any] = {"path": str(path), "exists": path.exists(), "lines": 0, "valid_json": 0, "invalid_json": 0, "sample_keys": []}
    if not path.is_file():
        return info
    keys: set[str] = set()
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            info["lines"] += 1
            try:
                obj = json.loads(line)
                info["valid_json"] += 1
                if isinstance(obj, dict):
                    keys.update(obj.keys())
            except Exception:
                info["invalid_json"] += 1
    except OSError as exc:
        info["error"] = str(exc)
    info["sample_keys"] = sorted(keys)[:30]
    return info


def infer_repo_slug(repo: Path) -> str | None:
    remote = run(["git", "config", "--get", "remote.origin.url"], repo)
    if not remote["ok"] or not remote["stdout"]:
        return None
    raw = remote["stdout"].strip()
    if raw.endswith(".git"):
        raw = raw[:-4]
    m = re.search(r"github\.com[:/](?P<owner>[^/]+)/(?P<repo>[^/]+)$", raw)
    if m:
        return f"{m.group('owner')}/{m.group('repo')}"
    return raw


def git_inventory(repo: Path, expected_pr: int | None) -> dict[str, Any]:
    inv: dict[str, Any] = {
        "root": str(repo),
        "remote": run(["git", "config", "--get", "remote.origin.url"], repo),
        "status": run(["git", "status", "--short", "--branch"], repo),
        "branch": run(["git", "branch", "--show-current"], repo),
        "head": run(["git", "rev-parse", "HEAD"], repo),
        "main": run(["git", "rev-parse", "main"], repo),
        "origin_main": run(["git", "rev-parse", "origin/main"], repo),
        "recent_log": run(["git", "--no-pager", "log", "--oneline", "--decorate", "-n", "20"], repo),
    }
    slug = infer_repo_slug(repo)
    inv["repo_slug"] = slug

    gh = shutil.which("gh")
    inv["gh_available"] = bool(gh)
    if gh and slug:
        inv["gh_auth_status"] = run(["gh", "auth", "status"], repo, timeout=20)
        inv["prs_all"] = run([
            "gh", "pr", "list", "--repo", slug, "--state", "all", "--limit", "30",
            "--json", "number,title,state,isDraft,mergeable,headRefName,baseRefName,headRefOid,updatedAt,mergedAt,url,statusCheckRollup"
        ], repo, timeout=60)
        inv["prs_open"] = run([
            "gh", "pr", "list", "--repo", slug, "--state", "open", "--limit", "20",
            "--json", "number,title,state,isDraft,mergeable,headRefName,baseRefName,headRefOid,updatedAt,url,statusCheckRollup"
        ], repo, timeout=60)
        if expected_pr is not None:
            inv[f"pr_{expected_pr}"] = run([
                "gh", "pr", "view", str(expected_pr), "--repo", slug,
                "--json", "number,title,state,isDraft,mergeable,headRefName,baseRefName,headRefOid,commits,files,reviews,comments,statusCheckRollup,url"
            ], repo, timeout=60)
    return inv


def default_roots(repo: Path) -> list[Path]:
    roots: list[Path] = []
    env = os.environ.get("EMBIZ_KNOWLEDGE_ROOTS", "")
    for part in env.split(":"):
        part = part.strip()
        if part:
            roots.append(Path(part).expanduser())
    roots.extend([
        Path("/root/web-archive/ai_agents_skills_library"),
        Path("/root/EMBIZ_EXPORTS"),
        Path.home() / "web-archive" / "ai_agents_skills_library",
        Path.home() / "EMBIZ_EXPORTS",
        repo / "knowledge" / "library",
    ])
    out: list[Path] = []
    seen: set[str] = set()
    for r in roots:
        key = str(r.resolve()) if r.exists() else str(r)
        if key not in seen:
            seen.add(key)
            out.append(r)
    return out


def corpus_files(root: Path, corpus: str) -> list[Path]:
    if corpus == "global":
        return [p for p in [
            root / "global_knowledge_objects.jsonl",
            root / "global_knowledge_objects.clean.jsonl",
            root / "global_knowledge_objects.multimodal.jsonl",
        ] if p.exists()]
    rel = EXPECTED_CORPORA[corpus]
    d = root / rel
    if not d.is_dir():
        return []
    return sorted(d.glob("*.jsonl"))


def knowledge_inventory(repo: Path) -> dict[str, Any]:
    roots = default_roots(repo)
    inv: dict[str, Any] = {
        "env_EMBIZ_KNOWLEDGE_ROOTS": os.environ.get("EMBIZ_KNOWLEDGE_ROOTS", ""),
        "roots": [],
        "corpora": {},
        "agent_gates": {},
        "all_jsonl_files": [],
    }

    for root in roots:
        root_info: dict[str, Any] = {
            "path": str(root),
            "exists": root.exists(),
            "is_dir": root.is_dir(),
            "readable": os.access(root, os.R_OK) if root.exists() else False,
            "writable": os.access(root, os.W_OK) if root.exists() else False,
        }
        if root.is_dir():
            jsonls = sorted(root.rglob("*.jsonl"))
            root_info["jsonl_count"] = len(jsonls)
            root_info["jsonl_total_lines"] = sum(count_jsonl(p)["lines"] for p in jsonls[:500])
            root_info["global_files"] = [str(p) for p in corpus_files(root, "global")]
        inv["roots"].append(root_info)

    for corpus in EXPECTED_CORPORA:
        files: list[Path] = []
        for root in roots:
            if root.is_dir():
                files.extend(corpus_files(root, corpus))
        file_counts = [count_jsonl(p) for p in files]
        inv["corpora"][corpus] = {
            "present": bool(files),
            "files": file_counts,
            "records": sum(f["valid_json"] for f in file_counts),
        }

    for agent, spec in AGENT_REQUIREMENTS.items():
        missing = [c for c in spec["required"] if not inv["corpora"].get(c, {}).get("present")]
        present_required = [c for c in spec["required"] if c not in missing]
        present_optional = [c for c in spec["optional"] if inv["corpora"].get(c, {}).get("present")]
        inv["agent_gates"][agent] = {
            "required": spec["required"],
            "optional": spec["optional"],
            "present_required": present_required,
            "present_optional": present_optional,
            "missing_required": missing,
            "gate": "ok" if not missing else "MISSING_REQUIRED_CORPUS: " + ", ".join(missing),
        }

    repo_jsonl = sorted((repo / "knowledge").rglob("*.jsonl")) if (repo / "knowledge").is_dir() else []
    for p in repo_jsonl[:300]:
        inv["all_jsonl_files"].append(count_jsonl(p))
    return inv


def search_files(repo: Path, needles: list[str], max_files: int = 6000) -> dict[str, Any]:
    matches = {n: [] for n in needles}
    skip_dirs = {".git", ".venv", "__pycache__", "node_modules", ".mypy_cache", ".pytest_cache"}
    exts = {".py", ".md", ".txt", ".json", ".jsonl", ".toml", ".yml", ".yaml", ".ts", ".tsx", ".js", ".html", ".htm"}
    visited = 0
    for p in repo.rglob("*"):
        if visited >= max_files:
            break
        if any(part in skip_dirs for part in p.parts):
            continue
        if not p.is_file() or p.suffix.lower() not in exts:
            continue
        visited += 1
        text = safe_read(p, max_bytes=1_500_000)
        if not text:
            continue
        rel = str(p.relative_to(repo))
        lower = text.lower()
        for n in needles:
            if n.lower() in lower:
                matches[n].append(rel)
    return {"files_scanned": visited, "matches": {k: sorted(set(v)) for k, v in matches.items()}}


def runtime_inventory(repo: Path) -> dict[str, Any]:
    inv: dict[str, Any] = {"files": {}, "patterns": {}}
    for rel in RUNTIME_FILES:
        p = repo / rel
        text = safe_read(p)
        inv["files"][rel] = {
            "exists": p.exists(),
            "size": p.stat().st_size if p.exists() else None,
            "lines": text.count("\n") + 1 if text else 0,
        }
    for label, needles in RUNTIME_PATTERNS.items():
        hits = search_files(repo, needles)
        inv["patterns"][label] = hits
    return inv


def url_coverage(repo: Path, knowledge: dict[str, Any]) -> dict[str, Any]:
    needles = EXPECTED_URLS + sorted({re.sub(r"^https?://(www\.)?", "", u).split("/")[0] for u in EXPECTED_URLS})
    repo_hits = search_files(repo, needles, max_files=8000)["matches"]

    jsonl_hits: dict[str, list[str]] = {u: [] for u in EXPECTED_URLS}
    for root_info in knowledge.get("roots", []):
        root = Path(root_info["path"])
        if not root.is_dir():
            continue
        for jf in sorted(root.rglob("*.jsonl"))[:800]:
            text = safe_read(jf, max_bytes=5_000_000)
            if not text:
                continue
            for url in EXPECTED_URLS:
                if url in text or url.rstrip("/") in text:
                    jsonl_hits[url].append(str(jf))

    rows = []
    for url in EXPECTED_URLS:
        domain = re.sub(r"^https?://(www\.)?", "", url).split("/")[0]
        rows.append({
            "url": url,
            "domain": domain,
            "exact_in_repo": bool(repo_hits.get(url)),
            "domain_in_repo": bool(repo_hits.get(domain)),
            "exact_in_jsonl": bool(jsonl_hits[url]),
            "repo_files": repo_hits.get(url, [])[:10],
            "domain_files": repo_hits.get(domain, [])[:10],
            "jsonl_files": jsonl_hits[url][:10],
        })
    return {
        "expected_url_count": len(EXPECTED_URLS),
        "covered_exact_urls": sum(1 for r in rows if r["exact_in_repo"] or r["exact_in_jsonl"]),
        "covered_domains": sum(1 for r in rows if r["domain_in_repo"]),
        "rows": rows,
    }


def cloudflare_inventory(repo: Path) -> dict[str, Any]:
    names = ["wrangler.toml", "wrangler.json", "worker.ts", "worker.js", "cloudflare", "flue", "durable", "d1", "r2", "vectorize", "terraform", "lambda", "sqs", "ses", "x-ray", "xray", "pages functions"]
    hits = search_files(repo, names, max_files=8000)["matches"]
    files = []
    for rel in sorted(set(sum(hits.values(), []))):
        p = repo / rel
        files.append({"path": rel, "size": p.stat().st_size if p.exists() else None})

    expected = []
    for rel in CLOUDFLARE_AWS_EXPECTED_SURFACE:
        p = repo / rel
        if rel.endswith("/"):
            present = p.is_dir()
        else:
            present = p.exists()
        expected.append({"path": rel, "present": present})

    missing_expected = [x["path"] for x in expected if not x["present"]]
    return {
        "matched_files": files,
        "pattern_hits": hits,
        "expected_surface": expected,
        "missing_expected_surface": missing_expected,
        "status": (
            "expected_cloudflare_aws_surface_present"
            if expected and not missing_expected
            else "cloudflare_aws_surface_incomplete_or_absent"
        ),
    }


def service_inventory(repo: Path) -> dict[str, Any]:
    out: dict[str, Any] = {}
    systemctl = shutil.which("systemctl")
    if not systemctl:
        return {"systemctl_available": False}
    out["systemctl_available"] = True
    out["user_embiz_units"] = run(["systemctl", "--user", "list-units", "--type=service", "--all", "--no-pager"], repo, timeout=20)
    out["system_embiz_units"] = run(["systemctl", "list-units", "--type=service", "--all", "--no-pager"], repo, timeout=20)
    for key in ("user_embiz_units", "system_embiz_units"):
        stdout = out[key].get("stdout", "")
        out[key]["embiz_lines"] = [line for line in stdout.splitlines() if "embiz" in line.lower()]
    return out


def verdicts(report: dict[str, Any]) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    runtime = report["runtime"]["files"]
    for rel in RUNTIME_FILES:
        items.append({"check": f"runtime file {rel}", "status": "ok" if runtime[rel]["exists"] else "missing"})

    for agent, gate in report["knowledge"]["agent_gates"].items():
        status = "ok" if not gate["missing_required"] else "blocked"
        items.append({"check": f"knowledge gate {agent}", "status": status, "detail": gate["gate"]})

    if report["urls"]["covered_exact_urls"] < report["urls"]["expected_url_count"]:
        items.append({
            "check": "attached URL seed coverage",
            "status": "blocked",
            "detail": f"{report['urls']['covered_exact_urls']}/{report['urls']['expected_url_count']} exact URLs found in repo/library",
        })
    else:
        items.append({"check": "attached URL seed coverage", "status": "ok"})

    cf_status = report["cloudflare"]["status"]
    items.append({
        "check": "cloudflare customer-facing surface",
        "status": "ok" if cf_status == "expected_cloudflare_aws_surface_present" else "missing",
        "detail": cf_status,
    })

    git = report["git"]
    open_pr_known = False
    prs_open = git.get("prs_open", {})
    if prs_open.get("ok") and prs_open.get("stdout"):
        try:
            open_pr_known = bool(json.loads(prs_open["stdout"]))
        except Exception:
            open_pr_known = False
    items.append({
        "check": "open GitHub PR discovery",
        "status": "ok" if open_pr_known else ("unknown" if not git.get("gh_available") else "none"),
        "detail": "uses gh CLI when authenticated",
    })
    return items


def md_escape(text: Any) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines: list[str] = []
    lines.append("# EMBIZ Deep Inventory Audit")
    lines.append("")
    lines.append(f"- Generated: `{report['generated_at']}`")
    lines.append(f"- Repo root: `{report['repo_root']}`")
    lines.append("")
    lines.append("## Executive verdicts")
    lines.append("")
    lines.append("| Check | Status | Detail |")
    lines.append("|---|---:|---|")
    for v in report["verdicts"]:
        lines.append(f"| {md_escape(v['check'])} | {md_escape(v['status'])} | {md_escape(v.get('detail', ''))} |")

    lines.append("")
    lines.append("## Git / PR state")
    git = report["git"]
    lines.append(f"- Repo slug: `{git.get('repo_slug')}`")
    lines.append(f"- Current branch: `{git.get('branch', {}).get('stdout', '')}`")
    lines.append(f"- HEAD: `{git.get('head', {}).get('stdout', '')}`")
    lines.append(f"- `gh` available: `{git.get('gh_available')}`")
    if git.get("prs_open", {}).get("stdout"):
        lines.append("")
        lines.append("```json")
        lines.append(git["prs_open"]["stdout"][:5000])
        lines.append("```")

    lines.append("")
    lines.append("## Knowledge roots")
    lines.append("")
    lines.append("| Root | Exists | Readable | Writable | JSONL count | Global files |")
    lines.append("|---|---:|---:|---:|---:|---|")
    for r in report["knowledge"]["roots"]:
        lines.append(
            f"| `{md_escape(r['path'])}` | {r['exists']} | {r['readable']} | {r['writable']} | {r.get('jsonl_count', 0)} | {md_escape(', '.join(r.get('global_files', [])))} |"
        )

    lines.append("")
    lines.append("## Corpus inventory")
    lines.append("")
    lines.append("| Corpus | Present | Records | Files |")
    lines.append("|---|---:|---:|---|")
    for corpus, c in report["knowledge"]["corpora"].items():
        file_list = ", ".join(f["path"] for f in c["files"][:8])
        lines.append(f"| `{corpus}` | {c['present']} | {c['records']} | {md_escape(file_list)} |")

    lines.append("")
    lines.append("## Agent knowledge gates")
    lines.append("")
    lines.append("| Agent | Gate | Missing required |")
    lines.append("|---|---|---|")
    for agent, g in report["knowledge"]["agent_gates"].items():
        lines.append(f"| `{agent}` | {md_escape(g['gate'])} | {md_escape(', '.join(g['missing_required']))} |")

    lines.append("")
    lines.append("## Attached URL seed coverage")
    lines.append("")
    lines.append(f"- Exact URLs covered: `{report['urls']['covered_exact_urls']}/{report['urls']['expected_url_count']}`")
    lines.append("")
    lines.append("| URL | Exact covered | Domain seen | Files |")
    lines.append("|---|---:|---:|---|")
    for row in report["urls"]["rows"]:
        files = row["repo_files"] or row["jsonl_files"] or row["domain_files"]
        lines.append(f"| `{md_escape(row['url'])}` | {row['exact_in_repo'] or row['exact_in_jsonl']} | {row['domain_in_repo']} | {md_escape(', '.join(files[:4]))} |")

    lines.append("")
    lines.append("## Runtime wiring patterns")
    lines.append("")
    for label, data in report["runtime"]["patterns"].items():
        lines.append(f"### {label}")
        matched_files = sorted(set(sum(data["matches"].values(), [])))
        if matched_files:
            for rel in matched_files[:30]:
                lines.append(f"- `{rel}`")
        else:
            lines.append("- No matches found.")
        lines.append("")

    lines.append("## Cloudflare/customer-facing surface")
    lines.append("")
    lines.append(f"- Status: `{report['cloudflare']['status']}`")
    lines.append("")
    lines.append("### Expected Cloudflare + AWS surface")
    lines.append("")
    lines.append("| Path | Present |")
    lines.append("|---|---:|")
    for f in report["cloudflare"].get("expected_surface", []):
        lines.append(f"| `{f['path']}` | {f['present']} |")
    lines.append("")
    lines.append("### Pattern-matched files")
    for f in report["cloudflare"]["matched_files"][:50]:
        lines.append(f"- `{f['path']}`")

    lines.append("")
    lines.append("## EMBIZ services")
    lines.append("")
    svc = report["services"]
    if not svc.get("systemctl_available"):
        lines.append("- `systemctl` unavailable.")
    else:
        lines.append("### User units")
        for line in svc.get("user_embiz_units", {}).get("embiz_lines", []):
            lines.append(f"- `{line}`")
        lines.append("### System units")
        for line in svc.get("system_embiz_units", {}).get("embiz_lines", []):
            lines.append(f"- `{line}`")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".", help="Repository root or any path inside it.")
    ap.add_argument("--expected-pr", type=int, default=5, help="PR number to inspect with gh when available.")
    ap.add_argument("--json-out", default="reports/embiz_deep_inventory.json")
    ap.add_argument("--md-out", default="reports/embiz_deep_inventory.md")
    args = ap.parse_args(argv)

    start = Path(args.repo).expanduser().resolve()
    repo = repo_root_from(start)
    report: dict[str, Any] = {
        "generated_at": now(),
        "repo_root": str(repo),
        "git": git_inventory(repo, args.expected_pr),
        "knowledge": knowledge_inventory(repo),
        "runtime": runtime_inventory(repo),
        "cloudflare": cloudflare_inventory(repo),
        "services": service_inventory(repo),
    }
    report["urls"] = url_coverage(repo, report["knowledge"])
    report["verdicts"] = verdicts(report)

    json_out = repo / args.json_out
    md_out = repo / args.md_out
    json_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    write_markdown(report, md_out)

    print(f"Wrote {json_out}")
    print(f"Wrote {md_out}")

    blocked = [v for v in report["verdicts"] if v["status"] in {"blocked", "missing"}]
    if blocked:
        print("Blocked/missing checks:")
        for v in blocked:
            print(f"- {v['check']}: {v['status']} {v.get('detail', '')}")
    else:
        print("No blocked/missing checks detected by this audit.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
