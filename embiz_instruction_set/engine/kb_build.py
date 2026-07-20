#!/usr/bin/env python3
"""kb_build.py — build the NEW knowledge object library from the VPS web archive.

Ingests HTML + PDF (+ md/txt/json) and images from the source roots declared in
config/knowledge_sources.json, imports the existing global *.jsonl stores, and
writes a unified knowledge object library under runtime knowledge_object_library/.

This is real, runnable code. It MUST run on the VPS where the source archives
exist (/root/web-archive/..., /root/EMBIZ_EXPORTS/...). Off-VPS it will find no
sources and report an empty build (which is honest, not a failure to hide).

Knowledge object schema (one JSON per line in knowledge_objects.jsonl):
  {
    "id": "<sha1 of source_path[:page]>",
    "source_path": "<absolute path>",
    "kind": "pdf|html|markdown|text|json|image",
    "title": "<derived>",
    "text": "<extracted text or caption>",
    "tags": ["<domain tags>"],
    "sha256": "<content hash>",
    "page": <int or null>,
    "ingested_at": "<iso8601>"
  }

Degradation is explicit: if pdftotext / bs4 are unavailable, the object records
`extract_error` instead of silently producing empty text, so QA can catch it.
"""
from __future__ import annotations
import glob
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CFG = os.path.join(ROOT, "config", "knowledge_sources.json")


def now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def oid(source: str, page=None) -> str:
    return hashlib.sha1(f"{source}:{page}".encode()).hexdigest()


def load_cfg() -> dict:
    with open(CFG, "r", encoding="utf-8") as f:
        return json.load(f)


def tags_for(path: str, hints: dict) -> list[str]:
    low = path.lower()
    tags = sorted({v for k, v in hints.items() if k in low})
    return tags or ["general"]


def pdf_text(path: str) -> tuple[str, str | None]:
    """Return (text, error). Prefer pdftotext; fall back to pdfminer if present."""
    if shutil.which("pdftotext"):
        try:
            out = subprocess.run(["pdftotext", "-q", path, "-"], capture_output=True, timeout=120)
            if out.returncode == 0:
                return out.stdout.decode("utf-8", "replace"), None
        except Exception as e:  # noqa: BLE001
            return "", f"pdftotext_error:{e}"
    try:
        from pdfminer.high_level import extract_text  # type: ignore
        return extract_text(path) or "", None
    except Exception as e:  # noqa: BLE001
        return "", f"no_pdf_extractor:{e}"


def html_text(path: str) -> tuple[str, str | None]:
    raw = open(path, "rb").read().decode("utf-8", "replace")
    try:
        from bs4 import BeautifulSoup  # type: ignore
        soup = BeautifulSoup(raw, "html.parser")
        for s in soup(["script", "style"]):
            s.decompose()
        return soup.get_text(" ", strip=True), None
    except Exception as e:  # noqa: BLE001
        return raw, f"bs4_unavailable:{e}"


def ingest_file(path: str, hints: dict) -> dict | None:
    try:
        data = open(path, "rb").read()
    except Exception:  # noqa: BLE001
        return None
    ext = os.path.splitext(path)[1].lower()
    kind = {".pdf": "pdf", ".html": "html", ".htm": "html", ".md": "markdown",
            ".txt": "text", ".json": "json"}.get(ext, "text")
    err = None
    if kind == "pdf":
        text, err = pdf_text(path)
    elif kind == "html":
        text, err = html_text(path)
    else:
        text = data.decode("utf-8", "replace")
    obj = {
        "id": oid(path), "source_path": path, "kind": kind,
        "title": os.path.basename(path), "text": text[:2_000_000],
        "tags": tags_for(path, hints), "sha256": sha256_bytes(data),
        "page": None, "ingested_at": now(),
    }
    if err:
        obj["extract_error"] = err
    return obj


def ingest_image_caption(path: str, hints: dict) -> dict:
    data = open(path, "rb").read()
    return {
        "id": oid(path), "source_path": path, "kind": "image",
        "title": os.path.basename(path),
        "text": f"[image asset: {os.path.basename(path)}] (caption pending visual model)",
        "tags": tags_for(path, hints) + ["visual"], "sha256": sha256_bytes(data),
        "page": None, "ingested_at": now(),
    }


def existing_root(cfg: dict) -> str | None:
    for key in ("primary_archive_root", "portable_export_root",
                "focused_raster_to_svg_export", "backup_sorted_root"):
        p = cfg.get(key)
        if p and os.path.isdir(p):
            return p
    return None


def build() -> dict:
    cfg = load_cfg()
    hints = cfg.get("domain_tag_hints", {})
    out_dir = cfg["output_dir"]
    os.makedirs(out_dir, exist_ok=True)
    new_path = os.path.join(out_dir, cfg["outputs"]["new_objects"])
    merged_path = os.path.join(out_dir, cfg["outputs"]["merged_global"])
    vis_path = os.path.join(out_dir, cfg["outputs"]["visual_captions"])
    manifest_path = os.path.join(out_dir, cfg["outputs"]["manifest"])

    stats = {"files_ingested": 0, "images_ingested": 0, "imported_objects": 0,
             "skipped_sources": [], "roots_scanned": [], "started": now()}

    root = existing_root(cfg)
    with open(new_path, "w", encoding="utf-8") as nf, open(vis_path, "w", encoding="utf-8") as vf:
        if root:
            stats["roots_scanned"].append(root)
            for pat in cfg.get("ingest_file_globs", []):
                for p in glob.glob(os.path.join(root, pat), recursive=True):
                    if os.path.isfile(p):
                        obj = ingest_file(p, hints)
                        if obj:
                            nf.write(json.dumps(obj) + "\n")
                            stats["files_ingested"] += 1
            for pat in cfg.get("ingest_image_globs", []):
                for p in glob.glob(os.path.join(root, pat), recursive=True):
                    if os.path.isfile(p):
                        vf.write(json.dumps(ingest_image_caption(p, hints)) + "\n")
                        stats["images_ingested"] += 1
        else:
            stats["skipped_sources"].append("no source root present on this host")

    # Merge existing global stores (import as-is, deduped by line hash).
    seen = set()
    with open(merged_path, "w", encoding="utf-8") as mf:
        # first, our new objects
        if os.path.exists(new_path):
            for line in open(new_path, encoding="utf-8"):
                h = hashlib.sha1(line.encode()).hexdigest()
                if h not in seen:
                    seen.add(h); mf.write(line)
        for store in cfg.get("import_existing_global_stores", []):
            if os.path.isfile(store):
                for line in open(store, encoding="utf-8", errors="replace"):
                    line = line.rstrip("\n")
                    if not line:
                        continue
                    h = hashlib.sha1(line.encode()).hexdigest()
                    if h not in seen:
                        seen.add(h); mf.write(line + "\n"); stats["imported_objects"] += 1
            else:
                stats["skipped_sources"].append(store)

    stats["finished"] = now()
    stats["merged_object_count"] = len(seen)
    stats["outputs"] = {"new_objects": new_path, "merged_global": merged_path,
                        "visual_captions": vis_path}
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)
    return stats


if __name__ == "__main__":
    s = build()
    print(json.dumps(s, indent=2))
    # Non-zero exit if nothing was ingested AND nothing imported: honest failure.
    if s["files_ingested"] == 0 and s["imported_objects"] == 0:
        print("KB_BUILD_EMPTY: no sources found on this host (expected off-VPS).", file=sys.stderr)
        sys.exit(3)
