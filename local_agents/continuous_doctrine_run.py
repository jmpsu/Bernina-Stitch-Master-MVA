#!/usr/bin/env python3
"""continuous_doctrine_run.py — knowledge-driven EMBIZ continuous run.

This is the production-grade doctrine entrypoint for the stronger requirement:
knowledge retrieval must happen before attempts, selected knowledge must visibly
influence optimizer inputs, QA/learning must be recorded after attempts, and the
central knowledge base must grow between runs.

It imports the real continuous_run pipeline and monkeypatches vectorizer.optimize
so the actual optimizer receives extra knowledge-guided starts. This means the
knowledge layer is not only narrated in Slack; it changes attempt inputs in a
traceable, repeatable way.
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

import continuous_run  # noqa: E402
from personas import CHANNELS, PERSONAS, post_as  # noqa: E402

RASTER_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".heic"}
SKIP_DIRS = {".git", "node_modules", ".cache", "__pycache__", ".venv", "venv", "dist", "build"}
KNOWLEDGE_FILENAMES = {
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
    "mila": ["raster", "vector", "trace", "silhouette", "bitmap", "source", "background", "mask", "threshold"],
    "melanie": ["svg", "path", "viewBox", "fill", "stroke", "cleanup", "conformance", "background", "hidden"],
    "mckenna": ["ink/stitch", "stitch", "satin", "fill", "underlay", "density", "thread", "column"],
    "meredith": ["inkscape", "extension", "export", "automation", "pes", "exp", "stitch", "command"],
    "miranda": ["bernina", "b700", "machine", "hoop", "exp", "density", "compatibility", "limit"],
    "mackenzie": ["visual", "qa", "compare", "preview", "fidelity", "source", "render", "similarity"],
    "mabel": ["parameter", "learning", "correlation", "prior", "attempt", "score", "method", "seed"],
    "minerva": ["decision", "meeting", "handoff", "risk", "next", "owner", "regression"],
}

_DOCTRINE: dict[str, Any] = {}
_ORIGINAL_OPTIMIZE = None


def utcnow() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def safe_read_text(path: Path, max_bytes: int = 2_000_000) -> str:
    try:
        if not path.is_file() or path.stat().st_size > max_bytes:
            return ""
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def safe_iter_files(root: Path):
    try:
        if root.is_file():
            yield root
            return
        if not root.is_dir():
            return
    except OSError:
        return
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        pdir = Path(dirpath)
        if any(part in SKIP_DIRS for part in pdir.parts):
            continue
        for name in filenames:
            yield pdir / name


def discover_roots(extra: list[str], deep_scan_home: bool) -> list[Path]:
    roots: list[Path] = []
    for part in os.environ.get("EMBIZ_KNOWLEDGE_ROOTS", "").split(":"):
        if part.strip():
            roots.append(Path(part).expanduser())
    roots.extend(Path(x).expanduser() for x in extra)
    roots.extend([
        REPO_ROOT / "knowledge" / "library",
        REPO_ROOT / "knowledge",
        REPO_ROOT / "reports",
        Path.home() / "web-archive" / "ai_agents_skills_library",
        Path.home() / "EMBIZ_EXPORTS",
        Path.home() / "Documents" / "Embroidery_Business_Documents",
        Path.home() / "Documents" / "clone_embroidery_business_agent_system" / "knowledge",
        Path("/root/web-archive/ai_agents_skills_library"),
        Path("/root/EMBIZ_EXPORTS"),
    ])
    if deep_scan_home:
        roots.extend([Path.home() / "Documents", Path.home() / "Pictures", Path.home() / ".config"])
    out: list[Path] = []
    seen: set[str] = set()
    for r in roots:
        try:
            if not r.exists():
                continue
            key = str(r.resolve())
        except OSError:
            continue
        if key not in seen:
            seen.add(key)
            out.append(r)
    return out


def discover_knowledge_files(roots: list[Path]) -> list[Path]:
    files: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        for p in safe_iter_files(root):
            lower = str(p).lower()
            if p.name in KNOWLEDGE_FILENAMES or (p.suffix.lower() == ".jsonl" and any(term in lower for term in ("knowledge", "corpus", "vector", "stitch", "bernina", "svg", "qa"))):
                try:
                    key = str(p.resolve())
                except OSError:
                    key = str(p)
                if key not in seen:
                    seen.add(key)
                    files.append(p)
    return sorted(files, key=lambda p: str(p))


def load_knowledge(files: list[Path], max_records: int) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for f in files:
        if len(records) >= max_records:
            break
        text = safe_read_text(f, max_bytes=8_000_000)
        if not text:
            continue
        for line_no, line in enumerate(text.splitlines(), 1):
            if len(records) >= max_records:
                break
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except Exception:
                obj = {"text": line[:3000]}
            if not isinstance(obj, dict):
                obj = {"text": str(obj)[:3000]}
            body = " ".join(str(obj.get(k, "")) for k in (
                "id", "title", "section", "summary", "visual_summary", "caption",
                "text", "chunk", "tags", "agent_relevance", "source", "source_path"
            ))
            if not body.strip():
                continue
            rid = obj.get("id") or hashlib.sha256((str(f) + str(line_no) + body[:250]).encode()).hexdigest()[:16]
            records.append({
                "id": str(rid),
                "source_file": str(f),
                "line": line_no,
                "source": str(obj.get("source") or obj.get("source_path") or f),
                "title": str(obj.get("title") or obj.get("section") or f.name),
                "text": body[:4000],
                "raw_keys": sorted(obj.keys())[:40],
            })
    return records


def stem_for(path: Path) -> str:
    try:
        return continuous_run._stem(path)  # noqa: SLF001
    except Exception:
        s = re.sub(r"\.[^.]+$", "", path.name)
        s = re.sub(r"[^A-Za-z0-9_.-]+", "_", s).strip("._-")
        return s or hashlib.sha256(path.name.encode()).hexdigest()[:12]


def score_record(rec: dict[str, Any], agent: str, image_name: str) -> int:
    terms = AGENT_TERMS.get(agent, []) + [x for x in re.split(r"[_\-. ]+", image_name.lower()) if x]
    hay = (rec.get("title", "") + " " + rec.get("source", "") + " " + rec.get("text", "")).lower()
    score = 0
    for term in terms:
        if term.lower() in hay:
            score += 5 if len(term) > 5 else 2
    for bonus in ("embroidery", "svg", "stitch", "vector", "qa", "density", "background"):
        if bonus in hay:
            score += 1
    return score


def select_records(records: list[dict[str, Any]], agent: str, image_name: str, limit: int) -> list[dict[str, Any]]:
    scored = [(score_record(r, agent, image_name), r) for r in records]
    scored = [(s, r) for s, r in scored if s > 0]
    scored.sort(key=lambda x: (-x[0], x[1].get("source_file", ""), x[1].get("line", 0)))
    return [r for _, r in scored[:limit]]


def snippet(text: str, n: int = 240) -> str:
    clean = re.sub(r"\s+", " ", text or "").strip()
    return clean[:n] + ("..." if len(clean) > n else "")


def ladder_value(grid: dict[str, list[Any]], name: str, preference: str) -> Any | None:
    if name not in grid or not grid[name]:
        return None
    vals = grid[name]
    if preference == "high":
        return vals[-1]
    if preference == "low":
        return vals[0]
    return vals[len(vals) // 2]


def derive_params_from_knowledge(text: str, base: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    grid = getattr(continuous_run.vectorizer, "PARAM_GRID", {})
    params = dict(base or {})
    reasons: list[str] = []
    lower = text.lower()

    if any(t in lower for t in ("background", "paper", "noise", "speckle", "artifact", "shadow")):
        for key in ("filter_speckle", "turdsize", "despeckle"):
            val = ladder_value(grid, key, "high")
            if val is not None:
                params[key] = val
                reasons.append(f"raise {key} for background/noise control")
                break
    if any(t in lower for t in ("detail", "thin", "line", "stroke", "small", "fidelity")):
        for key in ("color_precision", "colors", "posterize", "threshold"):
            val = ladder_value(grid, key, "high")
            if val is not None:
                params[key] = val
                reasons.append(f"raise {key} to preserve detail")
                break
        for key in ("corner_threshold", "alphamax"):
            val = ladder_value(grid, key, "low")
            if val is not None:
                params[key] = val
                reasons.append(f"lower {key} to reduce corner loss")
                break
    if any(t in lower for t in ("silhouette", "shape", "outline", "contour")):
        for key in ("mode", "trace_mode", "colormode"):
            vals = grid.get(key, [])
            preferred = next((v for v in vals if str(v).lower() in {"single", "binary", "sillhouette", "silhouette", "poster", "color"}), None)
            if preferred is not None:
                params[key] = preferred
                reasons.append(f"set {key}={preferred} for silhouette preservation")
                break
    if any(t in lower for t in ("smooth", "simplify", "path", "nodes", "cleanup")):
        for key in ("corner_threshold", "opttolerance", "simplify_tolerance"):
            val = ladder_value(grid, key, "mid")
            if val is not None:
                params[key] = val
                reasons.append(f"set {key} to balanced cleanup value")
                break
    if any(t in lower for t in ("layer", "separate", "color", "thread")):
        for key in ("layer_difference", "color_precision"):
            val = ladder_value(grid, key, "high")
            if val is not None:
                params[key] = val
                reasons.append(f"raise {key} for color/layer separation")
                break

    if not reasons:
        for key in grid:
            if key not in params:
                val = ladder_value(grid, key, "mid")
                if val is not None:
                    params[key] = val
        reasons.append("use balanced grid midpoint because record is relevant but not parameter-specific")
    return params, reasons


def base_params_for(stem: str) -> dict[str, Any]:
    state = load_state(continuous_run.STATE_FILE)
    rec = state.get("images", {}).get(stem, {})
    best = rec.get("best_params")
    if isinstance(best, dict):
        return dict(best)
    grid = getattr(continuous_run.vectorizer, "PARAM_GRID", {})
    return {k: v[len(v) // 2] for k, v in grid.items() if v}


def load_state(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"images": {}}


def build_doctrine_context(image_path: Path, cycle: int) -> dict[str, Any]:
    records = _DOCTRINE.get("records", [])
    per_agent = int(_DOCTRINE.get("knowledge_per_agent", 2))
    event_log = Path(_DOCTRINE["event_log"])
    stem = stem_for(image_path)
    base = base_params_for(stem)
    selected_by_agent: dict[str, list[dict[str, Any]]] = {}
    extra_starts: list[tuple[str, dict[str, Any]]] = []

    for agent in AGENTS:
        selected = select_records(records, agent, image_path.name, per_agent)
        selected_by_agent[agent] = selected
        persona = PERSONAS[agent]
        if not selected:
            text = (f"cycle {cycle}, {image_path.name}: I found no usable knowledge object in the visible roots for my role. "
                    f"That is a blocking knowledge-library gap if my role is required for approval.")
            post_as(persona, CHANNELS["reports"], text=text)
            append_jsonl(event_log, {"timestamp": utcnow(), "type": "knowledge_gap", "cycle": cycle, "image": image_path.name, "agent": agent})
            continue
        for rec in selected:
            params, reasons = derive_params_from_knowledge(rec["text"], base)
            label = f"doctrine_{agent}_{rec['id']}_{cycle}"[:80]
            if params:
                extra_starts.append((label, params))
            message = (
                f"cycle {cycle}, {image_path.name}: I found knowledge point `{rec['id']}` from `{rec['source']}`. "
                f"It likely helps this attempt because: {snippet(rec['text'])} "
                f"I am changing optimizer start `{label}` by: {', '.join(reasons)}. "
                f"I will verify by comparing composite/SSIM after this epoch, not by assuming it worked."
            )
            post_as(persona, CHANNELS["reports"], text=message)
            append_jsonl(event_log, {
                "timestamp": utcnow(), "type": "knowledge_applied_to_optimizer", "cycle": cycle,
                "image": image_path.name, "stem": stem, "agent": agent, "record_id": rec["id"],
                "source": rec["source"], "source_file": rec["source_file"], "line": rec["line"],
                "optimizer_start_label": label, "parameter_changes": reasons,
                "params": params,
            })
    return {"extra_starts": extra_starts, "selected_by_agent": selected_by_agent}


def install_optimizer_patch() -> None:
    global _ORIGINAL_OPTIMIZE
    if _ORIGINAL_OPTIMIZE is not None:
        return
    _ORIGINAL_OPTIMIZE = continuous_run.vectorizer.optimize

    def doctrine_optimize(image_path: str, *args, **kwargs):
        path = Path(image_path)
        cycle = int(_DOCTRINE.get("cycle", 0))
        context = build_doctrine_context(path, cycle)
        existing = list(kwargs.get("extra_starts") or [])
        merged: list[tuple[str, dict[str, Any]]] = []
        seen: set[str] = set()
        for label, params in existing + context["extra_starts"]:
            sig = json.dumps(params, sort_keys=True, default=str)
            if sig in seen:
                continue
            seen.add(sig)
            merged.append((label, params))
        if merged:
            kwargs["extra_starts"] = merged
            post_as(PERSONAS["mabel"], CHANNELS["reports"], text=(
                f"cycle {cycle}, {path.name}: I injected {len(merged)} total optimizer start(s), "
                f"including {len(context['extra_starts'])} knowledge-derived start(s). This changes the actual vectorizer.optimize input."
            ))
        return _ORIGINAL_OPTIMIZE(image_path, *args, **kwargs)

    continuous_run.vectorizer.optimize = doctrine_optimize


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
        if p.is_file() and p.suffix.lower() in {".svg", ".png", ".jpg", ".jpeg"} and gallery not in p.parents:
            safe = str(p.relative_to(out_dir)).replace("/", "__")
            shutil.copy2(p, gallery / safe)


def run_epoch_with_learning(state: dict[str, Any], image: Path, iters: int, cycle: int, output_dir: Path) -> dict[str, Any]:
    stem = stem_for(image)
    before = state.get("images", {}).get(stem, {}).copy()
    before_comp = float(before.get("best_composite", -1.0))
    before_ssim = float(before.get("best_ssim", -1.0))
    _DOCTRINE["cycle"] = cycle
    rec = continuous_run.run_epoch(state, image, iters)
    after_comp = float(rec.get("best_composite", -1.0))
    after_ssim = float(rec.get("best_ssim", -1.0))
    delta_comp = after_comp - before_comp
    delta_ssim = after_ssim - before_ssim
    status = "improved" if delta_comp > 0.0001 else "stalled_or_flat" if abs(delta_comp) <= 0.0001 else "regressed"

    event = {
        "timestamp": utcnow(), "type": "post_attempt_learning", "cycle": cycle,
        "image": image.name, "stem": stem, "status": status,
        "before_composite": before_comp, "after_composite": after_comp,
        "delta_composite": delta_comp, "before_ssim": before_ssim,
        "after_ssim": after_ssim, "delta_ssim": delta_ssim,
        "best_params": rec.get("best_params"),
        "rule": (
            f"When {stem} uses doctrine-selected knowledge starts and composite delta is {delta_comp:.6f}, "
            f"retain the best params if improved and retain the evidence as a negative example if flat/regressed."
        ),
    }
    append_jsonl(Path(_DOCTRINE["event_log"]), event)
    append_jsonl(REPO_ROOT / "knowledge" / "vectorization" / "central_doctrine_learnings.jsonl", event)
    append_jsonl(output_dir / "reports" / "central_doctrine_learnings.snapshot.jsonl", event)

    if status == "improved":
        post_as(PERSONAS["mabel"], CHANNELS["reports"], text=(
            f"cycle {cycle}, {image.name}: that worked. Composite {before_comp:.4f} -> {after_comp:.4f} "
            f"and SSIM {before_ssim:.4f} -> {after_ssim:.4f}. I recorded this as a reusable positive doctrine rule."
        ))
        post_as(PERSONAS["mercy"], CHANNELS["qa"], text=(
            f"cycle {cycle}, {image.name}: QA confirms a measurable improvement. This is mathematically traceable: "
            f"delta_composite={delta_comp:.6f}, delta_ssim={delta_ssim:.6f}."
        ))
    else:
        post_as(PERSONAS["mabel"], CHANNELS["reports"], text=(
            f"cycle {cycle}, {image.name}: no provable improvement ({before_comp:.4f} -> {after_comp:.4f}). "
            f"I recorded this as a negative/flat learning so the library grows even when an attempt fails."
        ))
    return rec


def write_manifest(out_dir: Path, roots: list[Path], kfiles: list[Path], records: list[dict[str, Any]], cycles: int, failures: int) -> None:
    state = load_state(continuous_run.STATE_FILE)
    lines = [
        "# EMBIZ continuous doctrine run",
        "",
        f"- Generated: `{utcnow()}`",
        f"- Output directory: `{out_dir}`",
        f"- Cycles requested: `{cycles}`",
        f"- Knowledge roots discovered: `{len(roots)}`",
        f"- Knowledge JSONL files discovered: `{len(kfiles)}`",
        f"- Knowledge records loaded: `{len(records)}`",
        f"- Failures: `{failures}`",
        "",
        "## Score summary",
    ]
    for stem, rec in sorted(state.get("images", {}).items()):
        lines.append(f"- `{stem}`: epochs={rec.get('epochs')} best_ssim={rec.get('best_ssim')} best_composite={rec.get('best_composite')} done={rec.get('done')} finalized={rec.get('finalized', False)}")
    lines.extend(["", "## Knowledge roots", ""])
    for root in roots:
        lines.append(f"- `{root}`")
    lines.extend(["", "## Generated files", ""])
    for sub in ("gallery", "vectorized_svg", "stitch_plans", "production_runs", "reports", "state"):
        lines.append(f"### {sub}")
        d = out_dir / sub
        for p in sorted(d.rglob("*")) if d.exists() else []:
            if p.is_file():
                lines.append(f"- `{p.relative_to(out_dir)}`")
        lines.append("")
    (out_dir / "MANIFEST.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Run EMBIZ doctrine-enhanced continuous improvement pipeline")
    ap.add_argument("--input-dir", required=True)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--cycles", type=int, default=8)
    ap.add_argument("--iters-per-epoch", type=int, default=180)
    ap.add_argument("--target-ssim", type=float, default=0.98)
    ap.add_argument("--stall-epochs", type=int, default=continuous_run.DEFAULT_STALL_EPOCHS)
    ap.add_argument("--knowledge-per-agent", type=int, default=2)
    ap.add_argument("--knowledge-record-limit", type=int, default=75000)
    ap.add_argument("--knowledge-root", action="append", default=[])
    ap.add_argument("--deep-scan-home", action="store_true")
    args = ap.parse_args(argv)

    input_dir = Path(args.input_dir).expanduser().resolve()
    output_base = Path(args.output_dir).expanduser().resolve()
    run_id = dt.datetime.now().strftime("embiz_continuous_doctrine_%Y%m%d_%H%M%S")
    out_dir = output_base / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    for sub in ("reports", "state", "input_images"):
        (out_dir / sub).mkdir(parents=True, exist_ok=True)

    images = sorted([p for p in input_dir.iterdir() if p.is_file() and p.suffix.lower() in RASTER_EXTS], key=lambda p: p.name)
    if not images:
        print(f"No raster images found in {input_dir}", file=sys.stderr)
        return 2

    # Keep this run isolated and easy to inspect.
    for rel in ("input_images", "vectorized_svg", "stitch_plans", "production_runs"):
        d = REPO_ROOT / rel
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True, exist_ok=True)
    for img in images:
        shutil.copy2(img, REPO_ROOT / "input_images" / img.name)
        shutil.copy2(img, out_dir / "input_images" / img.name)

    continuous_run.STATE_DIR = out_dir / "state"
    continuous_run.STATE_FILE = continuous_run.STATE_DIR / "continuous_run_state.json"
    continuous_run.WORK_DIR = continuous_run.STATE_DIR / "continuous_run_work"
    continuous_run.REPORTS_DIR = out_dir / "reports"
    continuous_run.MILESTONES_LOG = continuous_run.REPORTS_DIR / "milestones.jsonl"
    continuous_run.MEETINGS_LOG = continuous_run.REPORTS_DIR / "agent_meetings.jsonl"
    continuous_run.SLACK_DRAFTS_DIR = continuous_run.REPORTS_DIR / "slack_messages"

    roots = discover_roots(args.knowledge_root, args.deep_scan_home)
    kfiles = discover_knowledge_files(roots)
    records = load_knowledge(kfiles, args.knowledge_record_limit)
    event_log = out_dir / "reports" / "doctrine_events.jsonl"
    _DOCTRINE.update({
        "records": records,
        "knowledge_per_agent": args.knowledge_per_agent,
        "event_log": str(event_log),
        "cycle": 0,
    })
    append_jsonl(event_log, {"timestamp": utcnow(), "type": "knowledge_inventory", "roots": [str(r) for r in roots], "files": [str(f) for f in kfiles], "records": len(records)})
    post_as(PERSONAS["monica"], CHANNELS["reports"], text=(
        f"continuous doctrine run {run_id}: I discovered {len(kfiles)} knowledge JSONL file(s) and loaded {len(records)} record(s). "
        f"Every epoch will retrieve, announce, apply optimizer starts, score, QA, and persist learning."
    ))

    install_optimizer_patch()
    state = continuous_run.load_state(args.target_ssim, args.stall_epochs)
    failures = 0
    image_names = [p.name for p in images]
    pending_by_name = {p.name: p for p in images}

    for cycle in range(1, args.cycles + 1):
        post_as(PERSONAS["mira"], CHANNELS["jobs"], text=(
            f"continuous doctrine cycle {cycle}/{args.cycles}: I am processing {len(images)} customer drawing(s). "
            f"Knowledge must be retrieved before attempts, applied to optimizer starts, then scored and recorded after attempts."
        ))
        for name in image_names:
            try:
                run_epoch_with_learning(state, pending_by_name[name], args.iters_per_epoch, cycle, out_dir)
                continuous_run.save_state(state)
            except Exception as exc:  # noqa: BLE001
                failures += 1
                append_jsonl(event_log, {"timestamp": utcnow(), "type": "cycle_exception", "cycle": cycle, "image": name, "error": str(exc)})
                post_as(PERSONAS["mira"], CHANNELS["alerts"], text=f"cycle {cycle}, {name}: exception recorded: {type(exc).__name__}: {exc}")

    for rel in ("vectorized_svg", "stitch_plans", "production_runs"):
        copy_tree(REPO_ROOT / rel, out_dir / rel)
    copy_tree(continuous_run.REPORTS_DIR, out_dir / "reports")
    copy_tree(continuous_run.STATE_DIR, out_dir / "state")
    build_gallery(out_dir)
    write_manifest(out_dir, roots, kfiles, records, args.cycles, failures)
    post_as(PERSONAS["mira"], CHANNELS["milestones"], text=f"continuous doctrine run complete: `{out_dir}`; gallery `{out_dir / 'gallery'}`; failures={failures}.")

    print(f"OUTPUT_DIR={out_dir}")
    print(f"GALLERY_DIR={out_dir / 'gallery'}")
    print(f"MANIFEST={out_dir / 'MANIFEST.md'}")
    print(f"DOCTRINE_EVENTS={event_log}")
    print(f"AGENT_FEED={continuous_run.STATE_DIR / 'transcripts' / 'agent_feed.jsonl'}")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
