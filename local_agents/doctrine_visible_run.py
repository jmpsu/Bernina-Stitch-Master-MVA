#!/usr/bin/env python3
"""Visible EMBIZ doctrine run harness.

This script wraps continuous_run.py with a knowledge-visible doctrine layer:

- discovers local knowledge JSONL artifacts across repo + common EMBIZ library roots,
- posts named-agent knowledge findings before each epoch cycle,
- runs bounded continuous-run epochs on customer images,
- reads score deltas from continuous_run state,
- posts QA / learning feedback messages,
- records reusable central doctrine learnings into JSONL,
- copies all generated images and artifacts into a chosen local output folder.

It does not claim that all findings improved the run. It records whether the
measured score improved, stalled, or regressed after each cycle.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Any

HERE = Path(__file__).resolve().parent
REPO_ROOT = Path(os.environ.get("EMBIZ_REPO_ROOT", HERE.parent)).resolve()
for p in (str(REPO_ROOT), str(HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)

from personas import CHANNELS, PERSONAS, post_as  # noqa: E402

RASTER_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".heic"}
SKIP_DIRS = {".git", "node_modules", ".cache", "__pycache__", ".venv", "venv", "dist", "build"}
KNOWLEDGE_NAMES = {
    "knowledge_objects.jsonl",
    "global_knowledge_objects.jsonl",
    "global_knowledge_objects.clean.jsonl",
    "global_knowledge_objects.multimodal.jsonl",
    "visual_captions.jsonl",
    "embroidery_knowledge_objects.jsonl",
    "stall_break_wins.jsonl",
    "central_doctrine_learnings.jsonl",
}
AGENTS = ["mila", "melanie", "mckenna", "meredith", "miranda", "mackenzie", "mabel", "minerva"]

AGENT_TERMS = {
    "mila": ["raster", "vector", "trace", "silhouette", "bitmap", "source", "background", "mask"],
    "melanie": ["svg", "path", "viewBox", "fill", "stroke", "cleanup", "conformance", "background"],
    "mckenna": ["ink/stitch", "stitch", "satin", "fill", "underlay", "density", "thread"],
    "meredith": ["inkscape", "extension", "export", "automation", "pes", "exp", "stitch"],
    "miranda": ["bernina", "b700", "machine", "hoop", "exp", "density", "compatibility"],
    "mackenzie": ["visual", "qa", "compare", "preview", "fidelity", "source", "render"],
    "mabel": ["parameter", "learning", "correlation", "prior", "attempt", "score", "method"],
    "minerva": ["decision", "meeting", "handoff", "risk", "next", "owner"],
}


def utcnow() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def safe_read(path: Path, max_bytes: int = 2_000_000) -> str:
    try:
        if not path.is_file() or path.stat().st_size > max_bytes:
            return ""
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def stem_for(path: Path) -> str:
    name = path.name
    s = re.sub(r"\.[^.]+$", "", name)
    s = re.sub(r"[^A-Za-z0-9_.-]+", "_", s).strip("._-")
    return s or hashlib.sha256(name.encode()).hexdigest()[:12]


def iter_files(root: Path):
    if root.is_file():
        yield root
        return
    if not root.is_dir():
        return
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        pdir = Path(dirpath)
        if any(part in SKIP_DIRS for part in pdir.parts):
            continue
        for name in filenames:
            yield pdir / name


def discover_knowledge_files(extra_roots: list[Path]) -> list[Path]:
    roots: list[Path] = []
    env = os.environ.get("EMBIZ_KNOWLEDGE_ROOTS", "")
    for part in env.split(":"):
        if part.strip():
            roots.append(Path(part).expanduser())
    roots.extend(extra_roots)
    roots.extend([
        REPO_ROOT / "knowledge" / "library",
        REPO_ROOT / "knowledge",
        Path.home() / "web-archive" / "ai_agents_skills_library",
        Path.home() / "EMBIZ_EXPORTS",
        Path.home() / "Documents" / "Embroidery_Business_Documents",
        Path.home() / "Documents" / "clone_embroidery_business_agent_system" / "knowledge",
        Path("/root/web-archive/ai_agents_skills_library"),
        Path("/root/EMBIZ_EXPORTS"),
    ])
    out: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        try:
            if not root.exists():
                continue
        except OSError:
            continue
        for f in iter_files(root):
            if f.name in KNOWLEDGE_NAMES or (f.suffix == ".jsonl" and "knowledge" in str(f).lower()):
                key = str(f.resolve()) if f.exists() else str(f)
                if key not in seen:
                    seen.add(key)
                    out.append(f)
    return sorted(out, key=lambda p: str(p))


def load_knowledge(files: list[Path], max_records: int) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for f in files:
        if len(records) >= max_records:
            break
        try:
            lines = f.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for i, line in enumerate(lines, 1):
            if len(records) >= max_records:
                break
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except Exception:
                obj = {"text": line[:2000]}
            if not isinstance(obj, dict):
                obj = {"text": str(obj)[:2000]}
            text = " ".join(str(obj.get(k, "")) for k in ("title", "section", "summary", "visual_summary", "caption", "text", "chunk", "tags"))
            rid = obj.get("id") or hashlib.sha256((str(f) + str(i) + text[:200]).encode()).hexdigest()[:16]
            records.append({
                "id": rid,
                "source_file": str(f),
                "line": i,
                "title": obj.get("title") or obj.get("section") or f.name,
                "source": obj.get("source") or obj.get("source_path") or str(f),
                "text": text[:3000],
                "raw_keys": sorted(obj.keys())[:30],
            })
    return records


def score_record(rec: dict[str, Any], terms: list[str]) -> int:
    hay = (rec.get("title", "") + " " + rec.get("source", "") + " " + rec.get("text", "")).lower()
    score = 0
    for t in terms:
        t = t.lower()
        if t in hay:
            score += 4 if len(t) > 4 else 2
    if "embroidery" in hay:
        score += 2
    if "svg" in hay:
        score += 1
    if "stitch" in hay:
        score += 1
    return score


def select_records(records: list[dict[str, Any]], agent: str, image_name: str, limit: int) -> list[dict[str, Any]]:
    terms = AGENT_TERMS.get(agent, []) + re.split(r"[_\-. ]+", image_name.lower())
    scored = []
    for rec in records:
        sc = score_record(rec, terms)
        if sc > 0:
            scored.append((sc, rec))
    scored.sort(key=lambda x: (-x[0], x[1].get("source_file", ""), x[1].get("line", 0)))
    return [r for _, r in scored[:limit]]


def message_snippet(text: str, n: int = 220) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    return text[:n] + ("..." if len(text) > n else "")


def post_knowledge_messages(records: list[dict[str, Any]], image: Path, cycle: int, per_agent: int, event_log: Path) -> None:
    for agent in AGENTS:
        persona = PERSONAS[agent]
        selected = select_records(records, agent, image.name, per_agent)
        if not selected:
            text = f"cycle {cycle}, {image.name}: I did not find a relevant knowledge object in the visible library roots. That is a gap; Monica should ingest more corpus material before this agent makes strong claims."
            post_as(persona, CHANNELS["reports"], text=text)
            append_jsonl(event_log, {"timestamp": utcnow(), "type": "knowledge_gap", "agent": agent, "image": image.name, "cycle": cycle})
            continue
        for rec in selected:
            action = {
                "mila": "I will bias the next vectorization attempt toward source-faithful silhouette/background handling.",
                "melanie": "I will watch the next SVG for path cleanup, viewBox, fills/strokes, hidden rasters, and residue.",
                "mckenna": "I will check whether the generated stitch plan obeys stitch density, fill, satin, and thread constraints.",
                "meredith": "I will treat export and automation behavior as a reproducibility constraint, not an assumption.",
                "miranda": "I will treat Bernina/B700 compatibility as a blocking machine-readiness gate if the corpus supports it.",
                "mackenzie": "I will compare source intent against rendered output instead of accepting a generic-looking vector.",
                "mabel": "I will record whether this knowledge point correlates with measurable score movement after the cycle.",
                "minerva": "I will put this into the decision trace and assign the next owner based on measured improvement.",
            }.get(agent, "I will apply this knowledge point to the next attempt.")
            text = (
                f"cycle {cycle}, {image.name}: I found knowledge point `{rec['id']}` from `{rec['source']}`. "
                f"It can likely help because: {message_snippet(rec['text'])} {action}"
            )
            post_as(persona, CHANNELS["reports"], text=text)
            append_jsonl(event_log, {
                "timestamp": utcnow(), "type": "knowledge_selected", "agent": agent,
                "image": image.name, "cycle": cycle, "record_id": rec["id"],
                "source": rec["source"], "source_file": rec["source_file"], "line": rec["line"],
                "action": action,
            })


def load_state(state_file: Path) -> dict[str, Any]:
    try:
        return json.loads(state_file.read_text(encoding="utf-8"))
    except Exception:
        return {"images": {}}


def run_continuous_epoch(python: str, image_names: list[str], iters: int, target_ssim: float, state_dir: Path) -> int:
    env = os.environ.copy()
    env["EMBIZ_REPO_ROOT"] = str(REPO_ROOT)
    env["EMBIZ_STATE_DIR"] = str(state_dir)
    cmd = [
        python, str(REPO_ROOT / "local_agents" / "continuous_run.py"),
        "--round-robin",
        "--epochs-budget", str(len(image_names)),
        "--iters-per-epoch", str(iters),
        "--meeting-interval", "1",
        "--target-ssim", str(target_ssim),
        "--images", *image_names,
    ]
    return subprocess.call(cmd, cwd=str(REPO_ROOT), env=env)


def copy_tree(src: Path, dst: Path) -> None:
    if not src.exists():
        return
    dst.mkdir(parents=True, exist_ok=True)
    if src.is_file():
        shutil.copy2(src, dst / src.name)
        return
    for p in src.rglob("*"):
        if p.is_file():
            rel = p.relative_to(src)
            (dst / rel.parent).mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, dst / rel)


def build_gallery(out_dir: Path) -> None:
    gallery = out_dir / "gallery"
    gallery.mkdir(parents=True, exist_ok=True)
    for p in out_dir.rglob("*"):
        if p.is_file() and p.suffix.lower() in {".png", ".jpg", ".jpeg", ".svg"}:
            if gallery in p.parents:
                continue
            safe = str(p.relative_to(out_dir)).replace("/", "__")
            shutil.copy2(p, gallery / safe)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input-dir", required=True)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--cycles", type=int, default=8)
    ap.add_argument("--iters-per-epoch", type=int, default=180)
    ap.add_argument("--target-ssim", type=float, default=0.98)
    ap.add_argument("--knowledge-record-limit", type=int, default=50000)
    ap.add_argument("--knowledge-per-agent", type=int, default=2)
    ap.add_argument("--python", default=sys.executable)
    ap.add_argument("--knowledge-root", action="append", default=[])
    args = ap.parse_args(argv)

    input_dir = Path(args.input_dir).expanduser().resolve()
    out_base = Path(args.output_dir).expanduser().resolve()
    run_id = dt.datetime.now().strftime("embiz_doctrine_%Y%m%d_%H%M%S")
    out_dir = out_base / run_id
    state_dir = out_dir / "state"
    event_log = out_dir / "reports" / "doctrine_events.jsonl"
    learning_log = REPO_ROOT / "knowledge" / "vectorization" / "central_doctrine_learnings.jsonl"

    out_dir.mkdir(parents=True, exist_ok=True)
    for sub in ("reports", "state", "input_images"):
        (out_dir / sub).mkdir(parents=True, exist_ok=True)

    images = sorted([p for p in input_dir.iterdir() if p.is_file() and p.suffix.lower() in RASTER_EXTS], key=lambda p: p.name)
    if not images:
        print(f"No raster images found in {input_dir}", file=sys.stderr)
        return 2

    # Clean repo run directories so this run's artifacts are easy to collect.
    for rel in ("input_images", "vectorized_svg", "stitch_plans", "production_runs"):
        d = REPO_ROOT / rel
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True, exist_ok=True)
    for img in images:
        shutil.copy2(img, REPO_ROOT / "input_images" / img.name)
        shutil.copy2(img, out_dir / "input_images" / img.name)

    kfiles = discover_knowledge_files([Path(x).expanduser() for x in args.knowledge_root])
    records = load_knowledge(kfiles, args.knowledge_record_limit)
    post_as(PERSONAS["monica"], CHANNELS["reports"], text=(
        f"doctrine run {run_id}: I discovered {len(kfiles)} knowledge JSONL file(s) and loaded "
        f"{len(records)} record(s). I will make the retrieval evidence visible before each attempt cycle."
    ))
    append_jsonl(event_log, {"timestamp": utcnow(), "type": "knowledge_inventory", "files": [str(p) for p in kfiles], "records": len(records)})

    image_names = [p.name for p in images]
    previous_state = load_state(state_dir / "continuous_run_state.json")
    failures = 0

    for cycle in range(1, args.cycles + 1):
        post_as(PERSONAS["mira"], CHANNELS["jobs"], text=(
            f"doctrine cycle {cycle}/{args.cycles}: I am running all customer drawings through vectorization, stitch planning, QA, knowledge discussion, and persistent learning."
        ))
        for img in images:
            post_knowledge_messages(records, img, cycle, args.knowledge_per_agent, event_log)

        code = run_continuous_epoch(args.python, image_names, args.iters_per_epoch, args.target_ssim, state_dir)
        if code != 0:
            failures += 1
            post_as(PERSONAS["mira"], CHANNELS["alerts"], text=f"doctrine cycle {cycle}: continuous_run exited with code {code}; I am recording the failure and continuing summary collection.")

        state = load_state(state_dir / "continuous_run_state.json")
        for img in images:
            stem = stem_for(img)
            rec = state.get("images", {}).get(stem, {})
            prev = previous_state.get("images", {}).get(stem, {})
            before = float(prev.get("best_composite", -1.0))
            after = float(rec.get("best_composite", -1.0))
            delta = after - before
            best_ssim = rec.get("best_ssim", -1.0)
            status = "improved" if delta > 0.0001 else "stalled_or_flat" if abs(delta) <= 0.0001 else "regressed"
            learning = {
                "timestamp": utcnow(), "run_id": run_id, "cycle": cycle, "image": img.name,
                "stem": stem, "status": status, "before_composite": before,
                "after_composite": after, "delta_composite": delta,
                "best_ssim": best_ssim, "best_params": rec.get("best_params"),
                "rule": (
                    f"When image stem {stem} is in cycle {cycle} and composite delta is {delta:.6f}, "
                    f"record the current best parameters and selected knowledge evidence for future seeding."
                ),
            }
            append_jsonl(learning_log, learning)
            append_jsonl(event_log, {"timestamp": utcnow(), "type": "cycle_score", **learning})
            if status == "improved":
                post_as(PERSONAS["mabel"], CHANNELS["reports"], text=(
                    f"cycle {cycle}, {img.name}: that worked. Composite moved from {before:.4f} to {after:.4f} "
                    f"(delta {delta:.4f}); I recorded the reusable rule and best parameters in `{learning_log}`."
                ))
                post_as(PERSONAS["mercy"], CHANNELS["qa"], text=(
                    f"cycle {cycle}, {img.name}: QA has measurable improvement: composite={after:.4f}, ssim={float(best_ssim):.4f}. This is traceable in doctrine_events.jsonl and continuous_run_state.json."
                ))
            else:
                post_as(PERSONAS["mabel"], CHANNELS["reports"], text=(
                    f"cycle {cycle}, {img.name}: no provable improvement this cycle ({before:.4f} -> {after:.4f}). I recorded this as a negative/flat example so future runs avoid treating it as a win."
                ))
        previous_state = state

    for rel in ("vectorized_svg", "stitch_plans", "production_runs", "reports"):
        copy_tree(REPO_ROOT / rel, out_dir / rel)
    copy_tree(state_dir, out_dir / "state")
    build_gallery(out_dir)

    manifest = out_dir / "MANIFEST.md"
    state = load_state(state_dir / "continuous_run_state.json")
    lines = [
        "# EMBIZ visible doctrine run",
        "",
        f"- Run ID: `{run_id}`",
        f"- Input directory: `{input_dir}`",
        f"- Output directory: `{out_dir}`",
        f"- Images: `{len(images)}`",
        f"- Cycles: `{args.cycles}`",
        f"- Iterations per epoch: `{args.iters_per_epoch}`",
        f"- Knowledge JSONL files discovered: `{len(kfiles)}`",
        f"- Knowledge records loaded: `{len(records)}`",
        f"- Cycle failures: `{failures}`",
        "",
        "## Score summary",
    ]
    for stem, rec in sorted(state.get("images", {}).items()):
        lines.append(f"- `{stem}`: epochs={rec.get('epochs')} best_ssim={rec.get('best_ssim')} best_composite={rec.get('best_composite')} done={rec.get('done')} finalized={rec.get('finalized', False)}")
    lines.extend(["", "## Generated files", ""])
    for sub in ("gallery", "vectorized_svg", "stitch_plans", "production_runs", "reports", "state"):
        lines.append(f"### {sub}")
        for p in sorted((out_dir / sub).rglob("*")):
            if p.is_file():
                lines.append(f"- `{p.relative_to(out_dir)}`")
        lines.append("")
    manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")

    post_as(PERSONAS["mira"], CHANNELS["milestones"], text=f"doctrine run {run_id} complete. Outputs are in `{out_dir}`; gallery is `{out_dir / 'gallery'}`.")
    print(f"OUTPUT_DIR={out_dir}")
    print(f"GALLERY_DIR={out_dir / 'gallery'}")
    print(f"MANIFEST={manifest}")
    print(f"AGENT_FEED={state_dir / 'transcripts' / 'agent_feed.jsonl'}")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
