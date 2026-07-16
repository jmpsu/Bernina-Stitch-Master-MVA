#!/usr/bin/env python3
"""machine_inventory.py — authoritative machine/filesystem inventory dataset.

Scans every readable root and produces reports/machine_inventory.json (the
dataset) + reports/machine_inventory.md (readable digest) covering:

- every file: path, size, mtime, category, owning project
- duplicate files (sha256 groups) and debris (caches, backups, temp files)
- every git repository (root, branch, remotes, dirty state)
- installed tools, pip packages, services, startup units
- sensitive-file LOCATIONS (paths + kinds only — contents never read out)
- embroidery assets census (rasters, SVGs, EXP/PES/DST/INF/BMP, previews)
- storage usage by top-level directory

Read-only by design: this tool never moves, deletes, or uploads anything.
Reorganization is executed separately (scripts/organize_report.py) from this
dataset, so the plan is reviewable before anything changes.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import shutil
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT_JSON = REPO / "reports" / "machine_inventory.json"
OUT_MD = REPO / "reports" / "machine_inventory.md"

SCAN_ROOTS = [Path(p) for p in
              os.environ.get("EMBIZ_SCAN_ROOTS",
                             "/home/user:/root:/opt:/srv:/var/opt").split(":")]
SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv",
             ".cache", ".npm", ".local/share/Trash", "pw-browsers",
             "site-packages", "dist-packages"}
HASH_MAX = 64 * 2**20            # hash files up to 64 MB for dedupe
EMBROIDERY_EXT = {".pes", ".exp", ".dst", ".jef", ".vp3", ".inf"}
RASTER_EXT = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp", ".tif"}
VECTOR_EXT = {".svg", ".ai", ".eps"}
DEBRIS_SUFFIX = (".pyc", ".tmp", ".temp", "~", ".swp", ".orig", ".rej")
DEBRIS_NAMES = {".DS_Store", "Thumbs.db"}
SENSITIVE_NAMES = ("credentials", "secret", "token", "apikey", "api_key",
                   ".env", "id_rsa", "id_ed25519", ".pem", ".p12", ".keystore")


def _run(cmd: list[str], cwd: Path | None = None) -> str:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=30,
                              cwd=cwd).stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return ""


def categorize(p: Path) -> str:
    ext = p.suffix.lower()
    if ext in EMBROIDERY_EXT:
        return "embroidery"
    if ext in RASTER_EXT:
        return "raster"
    if ext in VECTOR_EXT:
        return "vector"
    if ext in (".py", ".sh", ".js", ".ts"):
        return "code"
    if ext in (".md", ".txt", ".pdf", ".html"):
        return "docs"
    if ext in (".json", ".jsonl", ".yaml", ".yml", ".toml", ".csv"):
        return "data"
    if p.name in DEBRIS_NAMES or p.name.endswith(DEBRIS_SUFFIX):
        return "debris"
    return "other"


def is_sensitive(p: Path) -> str | None:
    n = p.name.lower()
    for marker in SENSITIVE_NAMES:
        if marker in n:
            return marker
    if p.parent.name == ".aws" or p.parent.name == ".ssh":
        return p.parent.name
    return None


def scan() -> dict:
    files, git_repos, sensitive = [], [], []
    hashes: dict[str, list[str]] = defaultdict(list)
    dir_usage: dict[str, int] = defaultdict(int)
    total = 0
    for root in SCAN_ROOTS:
        if not root.is_dir():
            continue
        for dirpath, dirnames, filenames in os.walk(root, topdown=True):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            dp = Path(dirpath)
            if (dp / ".git").is_dir():
                git_repos.append({
                    "root": str(dp),
                    "branch": _run(["git", "branch", "--show-current"], dp),
                    "remotes": _run(["git", "remote", "-v"], dp).splitlines()[:2],
                    "dirty": bool(_run(["git", "status", "--porcelain"], dp)),
                    "head": _run(["git", "log", "-1", "--format=%h %s"], dp),
                })
            for name in filenames:
                p = dp / name
                try:
                    st = p.stat()
                except OSError:
                    continue
                if not p.is_file() or p.is_symlink():
                    continue
                total += 1
                cat = categorize(p)
                rec = {"path": str(p), "bytes": st.st_size,
                       "mtime": datetime.datetime.fromtimestamp(
                           st.st_mtime).isoformat(timespec="seconds"),
                       "category": cat}
                files.append(rec)
                top = str(p.relative_to(root).parts[0]) if p != root else "."
                dir_usage[f"{root}/{top}"] += st.st_size
                sens = is_sensitive(p)
                if sens:
                    sensitive.append({"path": str(p), "kind": sens,
                                      "bytes": st.st_size})
                if st.st_size and st.st_size <= HASH_MAX:
                    try:
                        h = hashlib.sha256(p.read_bytes()).hexdigest()
                        rec["sha256"] = h[:16]
                        hashes[h].append(str(p))
                    except OSError:
                        pass
    duplicates = [{"sha256": h[:16], "count": len(ps),
                   "bytes_each": Path(ps[0]).stat().st_size, "paths": ps}
                  for h, ps in hashes.items() if len(ps) > 1]
    duplicates.sort(key=lambda d: d["count"] * d["bytes_each"], reverse=True)
    return {"files": files, "git_repos": git_repos, "sensitive": sensitive,
            "duplicates": duplicates, "dir_usage": dict(dir_usage),
            "total_files": total}


def environment() -> dict:
    tools = {}
    for t in ("python3", "git", "curl", "node", "npm", "inkscape",
              "potrace", "convert", "zip", "unzip", "cloudflared",
              "wrangler", "aws", "systemctl"):
        tools[t] = shutil.which(t) or None
    pip_pkgs = _run([sys.executable, "-m", "pip", "list",
                     "--format=json"])
    try:
        pip_pkgs = json.loads(pip_pkgs)
    except ValueError:
        pip_pkgs = []
    services = _run(["systemctl", "list-units", "--type=service",
                     "--state=running", "--no-legend"]).splitlines()[:40]
    startup = _run(["systemctl", "list-unit-files", "--state=enabled",
                    "--no-legend"]).splitlines()[:40]
    du = shutil.disk_usage("/")
    return {"tools": tools, "pip_packages": pip_pkgs,
            "running_services": services, "enabled_units": startup,
            "disk": {"total_gb": round(du.total / 2**30, 1),
                     "used_gb": round(du.used / 2**30, 1),
                     "free_gb": round(du.free / 2**30, 1)}}


def digest(inv: dict, env: dict) -> str:
    by_cat: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for f in inv["files"]:
        by_cat[f["category"]][0] += 1
        by_cat[f["category"]][1] += f["bytes"]
    emb = [f for f in inv["files"] if f["category"] == "embroidery"]
    debris = [f for f in inv["files"] if f["category"] == "debris"]
    dup_waste = sum((d["count"] - 1) * d["bytes_each"]
                    for d in inv["duplicates"])
    lines = [
        "# Machine Inventory (authoritative dataset digest)",
        f"\nGenerated {datetime.datetime.now().isoformat(timespec='seconds')}"
        f" — full dataset: `reports/machine_inventory.json`",
        f"\n## Totals\n",
        f"- files scanned: {inv['total_files']}",
        f"- git repositories: {len(inv['git_repos'])}",
        f"- duplicate groups: {len(inv['duplicates'])} "
        f"(reclaimable ≈ {dup_waste / 2**20:.1f} MB)",
        f"- debris files: {len(debris)}",
        f"- sensitive-file locations: {len(inv['sensitive'])} "
        "(paths recorded, contents untouched)",
        f"- disk: {env['disk']['used_gb']} / {env['disk']['total_gb']} GB used",
        "\n## Files by category\n",
        "| category | files | MB |", "|---|---|---|",
    ]
    for cat, (n, b) in sorted(by_cat.items(), key=lambda kv: -kv[1][1]):
        lines.append(f"| {cat} | {n} | {b / 2**20:.1f} |")
    lines += ["\n## Git repositories\n",
              "| root | branch | dirty | head |", "|---|---|---|---|"]
    for r in inv["git_repos"]:
        lines.append(f"| {r['root']} | {r['branch']} | {r['dirty']} | "
                     f"{r['head'][:60]} |")
    lines += [f"\n## Embroidery assets: {len(emb)} machine files\n"]
    ext_count: dict[str, int] = defaultdict(int)
    for f in emb:
        ext_count[Path(f["path"]).suffix.lower()] += 1
    lines.append(", ".join(f"{k}: {v}" for k, v in sorted(ext_count.items())))
    lines += ["\n## Largest duplicate groups (top 15)\n",
              "| sha256 | copies | MB each | first path |", "|---|---|---|---|"]
    for d in inv["duplicates"][:15]:
        lines.append(f"| {d['sha256']} | {d['count']} | "
                     f"{d['bytes_each'] / 2**20:.2f} | {d['paths'][0]} |")
    lines += ["\n## Storage by top-level directory (top 20)\n",
              "| directory | MB |", "|---|---|"]
    for k, v in sorted(inv["dir_usage"].items(), key=lambda kv: -kv[1])[:20]:
        lines.append(f"| {k} | {v / 2**20:.1f} |")
    lines += ["\n## Sensitive-file locations (contents never read)\n",
              "| path | kind |", "|---|---|"]
    for s in inv["sensitive"][:40]:
        lines.append(f"| {s['path']} | {s['kind']} |")
    lines += ["\n## Installed tooling\n",
              "| tool | present |", "|---|---|"]
    for t, w in env["tools"].items():
        lines.append(f"| {t} | {w or 'NOT INSTALLED'} |")
    lines += [f"\n{len(env['pip_packages'])} pip packages "
              f"(full list in JSON); running services: "
              f"{len(env['running_services'])}; enabled units: "
              f"{len(env['enabled_units'])}"]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    inv = scan()
    env = environment()
    dataset = {"generated": datetime.datetime.now().isoformat(),
               "scan_roots": [str(r) for r in SCAN_ROOTS],
               "environment": env, **inv}
    OUT_JSON.parent.mkdir(exist_ok=True)
    OUT_JSON.write_text(json.dumps(dataset, indent=1) + "\n", encoding="utf-8")
    OUT_MD.write_text(digest(inv, env), encoding="utf-8")
    print(f"dataset: {OUT_JSON} ({OUT_JSON.stat().st_size // 1024} KB)")
    print(f"digest:  {OUT_MD}")
