"""intake.py — customer artwork intake and intelligent analysis (Madeline).

Implements the BRD's "Customer Artwork Intake and Intelligent Analysis"
requirement as a deterministic, observable pipeline:

  attachment extraction -> file validation -> metadata/customer extraction ->
  artwork identification -> artwork review -> complexity analysis ->
  missing-information detection -> job creation -> canonical artifacts ->
  knowledge retrieval -> autonomous routing

Intake sources: RFC-822 email files (.eml), JSON payloads (the
POST /cloudflare-email body shape), and direct file drops. Every stage writes
observable evidence into the job directory; the canonical artifacts are
exactly the BRD's list: intake_summary.md, job.json, raw_email.json,
missing_questions.md, artwork_review.md.
"""

from __future__ import annotations

import datetime
import email
import email.policy
import json
import os
import re
import shutil
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

try:
    from . import jobs as jobs_mod
    from .agent_bus import status_event
except ImportError:
    import jobs as jobs_mod
    from agent_bus import status_event

REPO_ROOT = Path(__file__).resolve().parent.parent

RASTER_EXT = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".tif", ".tiff"}
VECTOR_EXT = {".svg", ".ai", ".eps", ".pdf"}
EMBROIDERY_EXT = {".pes", ".exp", ".dst", ".jef", ".vp3", ".xxx", ".hus"}
OFFICE_EXT = {".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt", ".md"}
ARCHIVE_EXT = {".zip"}

REQUIRED_INFO = ["garment", "garment_color", "placement", "size",
                 "thread_colors", "quantity", "deadline"]

_INFO_PATTERNS = {
    "garment": r"\b(polo|t-?shirt|hoodie|hat|cap|jacket|towel|bag|apron|blanket|beanie|vest|sweatshirt)s?\b",
    "garment_color": r"\b(black|white|navy|red|blue|green|gray|grey|heather|charcoal|maroon|pink|purple|orange|yellow)\b(?=[^.]*\b(shirt|polo|hoodie|garment|hat|jacket|fabric)\b)",
    "placement": r"\b(left chest|right chest|full back|full front|sleeve|collar|cuff|center chest|back yoke)\b",
    "size": r"\b(\d+(?:\.\d+)?)\s*(?:in|inch|inches|\"|mm|cm)\b",
    "thread_colors": r"\bthread(?:\s+colors?)?[:\s]+([a-z, ]+)|\b(white and \w+|(?:\w+,\s*)+\w+ thread)\b",
    "quantity": r"\b(\d+)\s*(?:pcs|pieces|units|shirts|polos|hats|items|qty)\b|\bquantity[:\s]+(\d+)\b",
    "deadline": r"\b(?:by|before|due|deadline|within|needed?(?:\s+by)?)\s+([a-z0-9 ,/]+?(?:week|day|month|\d{4}|\d{1,2}/\d{1,2})s?)\b",
}


def _utcnow() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


# Roots a webhook payload may reference attachments from. Anything outside
# (after symlink resolution) is rejected — a JSON body must never be able to
# pull arbitrary host files into job artifacts.
ALLOWED_ATTACHMENT_ROOTS = [
    Path(os.environ["EMBIZ_INTAKE_DIR"]).resolve()
    if os.environ.get("EMBIZ_INTAKE_DIR") else REPO_ROOT.resolve()
]


def _safe_name(name: str) -> str:
    """Flatten any client-supplied filename to a single safe path component."""
    name = re.sub(r"[^A-Za-z0-9._-]", "_", Path(name).name)
    return name.lstrip(".") or "attachment.bin"


def _contained(child: Path, base: Path) -> bool:
    try:
        return child.resolve().is_relative_to(base.resolve())
    except OSError:
        return False


def _payload_attachment_ok(p: Path) -> bool:
    return any(_contained(p, root) for root in ALLOWED_ATTACHMENT_ROOTS)


# --- stage 1: attachment extraction -----------------------------------------

def extract_attachments(source: Path, dest: Path) -> list[dict]:
    """Extract every attachment from an .eml / archive / direct file into
    ``dest``; returns categorized inventory. Extracted files are permanent
    job artifacts."""
    dest.mkdir(parents=True, exist_ok=True)
    files: list[Path] = []
    if source.suffix.lower() == ".eml":
        msg = email.message_from_bytes(source.read_bytes(),
                                       policy=email.policy.default)
        for part in msg.iter_attachments():
            out = dest / _safe_name(part.get_filename() or "attachment.bin")
            if not _contained(out, dest):
                continue  # hostile filename — never escape the job dir
            out.write_bytes(part.get_payload(decode=True) or b"")
            files.append(out)
    elif source.suffix.lower() in ARCHIVE_EXT:
        with zipfile.ZipFile(source) as zf:
            for info in zf.infolist():
                if info.is_dir() or info.file_size > 100 * 2**20:
                    continue
                out = dest / _safe_name(info.filename)
                if not _contained(out, dest):
                    continue
                out.write_bytes(zf.read(info))
                files.append(out)
    else:  # direct file drop
        out = dest / source.name
        if source.resolve() != out.resolve():
            shutil.copy2(source, out)
        files.append(out)

    inventory = []
    for f in sorted(set(files)):
        ext = f.suffix.lower()
        category = ("raster" if ext in RASTER_EXT else
                    "vector" if ext in VECTOR_EXT else
                    "embroidery" if ext in EMBROIDERY_EXT else
                    "office" if ext in OFFICE_EXT else
                    "archive" if ext in ARCHIVE_EXT else "other")
        inventory.append({"file": f.name, "bytes": f.stat().st_size,
                          "category": category, "valid": f.stat().st_size > 0})
        # nested archives extracted one level deep
        if category == "archive":
            inventory.extend(extract_attachments(f, dest))
    return inventory


# --- stage 2: artwork identification -----------------------------------------

def identify_artwork(path: Path) -> dict:
    """BRD artwork identification: type, format, resolution, dimensions,
    transparency, background complexity, colors, vector/embroidery status."""
    ext = path.suffix.lower()
    ident = {"file": path.name, "artwork_type": "unknown", "format": ext.lstrip("."),
             "is_vector": ext in VECTOR_EXT, "is_embroidery": ext in EMBROIDERY_EXT}
    if ext in VECTOR_EXT or ext in EMBROIDERY_EXT:
        ident["artwork_type"] = "vector" if ext in VECTOR_EXT else "embroidery"
        return ident
    if ext not in RASTER_EXT:
        return ident
    with Image.open(path) as im:
        im.load()
        rgba = im.convert("RGBA")
    a = np.asarray(rgba, dtype=np.uint8)
    alpha = a[..., 3]
    rgb = a[..., :3].astype(np.float32)
    # quantized color census
    q = rgba.convert("RGB").quantize(colors=32, method=Image.MEDIANCUT)
    counts = sorted(q.getcolors(a.shape[0] * a.shape[1]) or [], reverse=True)
    palette = q.getpalette()
    dominant = []
    total = a.shape[0] * a.shape[1]
    for n, idx in counts[:5]:
        r, g, b = palette[idx * 3:idx * 3 + 3]
        dominant.append({"rgb": [r, g, b], "share": round(n / total, 4)})
    # background complexity from border-pixel variance
    border = np.concatenate([rgb[0].reshape(-1, 3), rgb[-1].reshape(-1, 3),
                             rgb[:, 0].reshape(-1, 3), rgb[:, -1].reshape(-1, 3)])
    bg_std = float(border.std(axis=0).mean())
    significant = [c for c in (q.getcolors(total) or []) if c[0] / total > 0.01]
    ident.update({
        "artwork_type": "raster",
        "resolution": [im.width, im.height],
        "dimensions_px": [im.width, im.height],
        "has_transparency": bool((alpha < 255).any()),
        "background_complexity": round(bg_std / 128.0, 4),  # 0 flat .. ~1 busy
        "num_colors": len(significant),
        "dominant_colors": dominant,
    })
    return ident


# --- stage 3: artwork review --------------------------------------------------

def review_artwork(path: Path) -> dict:
    """BRD automated artwork review: quality, noise, artifacts, small/thin
    features, text-likeness, edge clarity, overall embroidery suitability."""
    with Image.open(path) as im:
        gray = np.asarray(im.convert("L"), dtype=np.float32)
        edges = np.asarray(im.convert("L").filter(ImageFilter.FIND_EDGES),
                           dtype=np.float32)
    h, w = gray.shape
    # noise: energy of (image - 3x3 median) residual
    med = np.asarray(Image.fromarray(gray.astype(np.uint8))
                     .filter(ImageFilter.MedianFilter(3)), dtype=np.float32)
    noise = float(np.abs(gray - med).mean() / 255.0)
    # JPEG blockiness: discontinuity at 8px block boundaries vs elsewhere
    col_d = np.abs(np.diff(gray, axis=1)).mean(axis=0)
    block_cols = col_d[7::8].mean() if len(col_d) > 8 else 0.0
    other_cols = np.delete(col_d, np.s_[7::8]).mean() if len(col_d) > 8 else 1.0
    blockiness = float(max(0.0, (block_cols - other_cols) / 255.0))
    edge_clarity = float((edges > 64).mean())
    edge_strength = float(edges.mean() / 255.0)
    # thin-line detection: edges that vanish under erosion
    binary = (gray < 128).astype(np.uint8) * 255
    eroded = np.asarray(Image.fromarray(binary).filter(ImageFilter.MinFilter(3)))
    thin_ratio = float(max(0.0, (binary > 0).mean() - (eroded > 0).mean()))
    # small features: connected high-contrast specks (proxy via edge density
    # in 16px tiles with low fill)
    tile = 16
    tiles_e = edges[:h // tile * tile, :w // tile * tile].reshape(
        h // tile, tile, w // tile, tile).mean(axis=(1, 3))
    small_feature_density = float((tiles_e > 40).mean())
    text_like = bool(thin_ratio > 0.06 and small_feature_density > 0.35)
    quality = max(0.0, 1.0 - noise * 6 - blockiness * 12)
    suitability = round(max(0.0, min(1.0,
        0.35 * quality + 0.25 * (1 - thin_ratio * 6) +
        0.2 * (1 - small_feature_density) + 0.2 * min(1.0, edge_clarity * 4))), 4)
    return {
        "file": path.name,
        "image_quality": round(quality, 4),
        "noise_level": round(noise, 4),
        "compression_blockiness": round(blockiness, 4),
        "edge_clarity": round(edge_clarity, 4),
        "edge_strength": round(edge_strength, 4),
        "thin_line_ratio": round(thin_ratio, 4),
        "small_feature_density": round(small_feature_density, 4),
        "text_detected": text_like,
        "missing_regions": bool((gray > 250).mean() > 0.98),
        "embroidery_suitability": suitability,
    }


# --- stage 4: complexity analysis ---------------------------------------------

def complexity_analysis(ident: dict, review: dict) -> dict:
    """Objective complexity score driving budgets and QA thresholds."""
    color_c = min(1.0, ident.get("num_colors", 1) / 16.0)
    geo_c = review.get("edge_strength", 0.0)
    small_c = review.get("small_feature_density", 0.0)
    edge_pen = 1.0 - review.get("image_quality", 1.0)
    score = round(min(1.0, 0.3 * color_c + 0.25 * geo_c + 0.25 * small_c
                      + 0.2 * edge_pen), 4)
    band = "low" if score < 0.35 else "medium" if score < 0.65 else "high"
    return {
        "complexity_score": score,
        "band": band,
        "color_complexity": round(color_c, 4),
        "geometric_complexity": round(geo_c, 4),
        "small_feature_density": round(small_c, 4),
        # complexity drives budgets/thresholds (BRD):
        "experiment_budget_iters": {"low": 12, "medium": 24, "high": 40}[band],
        "qa_ssim_floor": {"low": 0.97, "medium": 0.95, "high": 0.92}[band],
        "estimated_difficulty": band,
    }


# --- stage 5: missing information ---------------------------------------------

def extract_requirements(text: str) -> dict:
    text_l = (text or "").lower()
    req: dict = {}
    for field, pattern in _INFO_PATTERNS.items():
        m = re.search(pattern, text_l)
        if m:
            val = next((g for g in m.groups() if g), m.group(0)).strip()
            req[field] = ([c.strip() for c in val.replace(" and ", ",").split(",")
                           if c.strip()] if field == "thread_colors" else val)
    return req


def missing_information(requirements: dict) -> list[str]:
    return [f for f in REQUIRED_INFO if not requirements.get(f)]


# --- orchestrated intake --------------------------------------------------------

def run_intake(source: Path | dict, actor: str = "madeline") -> dict:
    """Full intake for an email file, JSON payload, or dropped artwork file.
    Returns the job record; all canonical artifacts land in jobs/<id>/."""
    raw_email: dict = {}
    body_text = ""
    customer = sender = subject = ""
    if isinstance(source, dict):  # POST /cloudflare-email payload
        raw_email = source
        sender = source.get("from", "")
        subject = source.get("subject", "")
        body_text = source.get("body", "")
        customer = source.get("customer") or sender.split("@")[0]
        src_path = None
    else:
        src_path = Path(source)
        if src_path.suffix.lower() == ".eml":
            msg = email.message_from_bytes(src_path.read_bytes(),
                                           policy=email.policy.default)
            sender = str(msg.get("From", ""))
            subject = str(msg.get("Subject", ""))
            body = msg.get_body(preferencelist=("plain", "html"))
            body_text = body.get_content() if body else ""
            customer = sender.split("<")[0].strip() or sender
            raw_email = {"from": sender, "subject": subject,
                         "date": str(msg.get("Date", "")), "body": body_text}
        else:
            subject = f"File drop: {src_path.name}"
            customer = "file_drop"
            raw_email = {"source": "file_drop", "file": src_path.name}

    requirements = extract_requirements(f"{subject}\n{body_text}")
    job = jobs_mod.create_job(
        source="email" if raw_email.get("from") else "file_drop",
        customer=customer, email=sender, subject=subject,
        requirements=requirements)
    jid = job["job_id"]
    jdir = jobs_mod._job_dir(jid)
    art_dir = jdir / "artwork"

    # 1) attachment extraction
    if isinstance(source, dict):
        inventory = []
        for att in source.get("attachments", []):
            p = Path(str(att))
            # payload-supplied paths are untrusted: resolved containment in
            # the allowed intake roots or the reference is rejected+recorded
            if p.exists() and _payload_attachment_ok(p):
                inventory.extend(extract_attachments(p, art_dir))
            else:
                jobs_mod._audit(jid, "attachment_rejected",
                                {"ref": str(att)[:200],
                                 "reason": "outside allowed intake roots"},
                                actor=actor)
    else:
        inventory = extract_attachments(src_path, art_dir)
    status_event(actor, jid, str(src_path or "payload"), "received",
                 f"{len(inventory)} attachment(s) extracted")

    # 2-4) identify + review + complexity for every raster/vector artwork
    idents, reviews = [], []
    complexity = {"complexity_score": 0.0, "band": "low",
                  "experiment_budget_iters": 12, "qa_ssim_floor": 0.97}
    primary = None
    for item in inventory:
        f = art_dir / item["file"]
        if item["category"] in ("raster", "vector") and f.exists():
            ident = identify_artwork(f)
            idents.append(ident)
            if item["category"] == "raster":
                rev = review_artwork(f)
                reviews.append(rev)
                if primary is None:
                    primary = f
                    complexity = complexity_analysis(ident, rev)

    # 5) missing info
    missing = missing_information(requirements)
    if not any(i["category"] in ("raster", "vector") for i in inventory):
        missing.append("logo/artwork file")

    # 6) knowledge retrieval before routing (BRD: mandatory, recorded)
    retrieval = {"queried": False}
    try:
        try:
            from . import knowledge_retrieval as kr
        except ImportError:
            import knowledge_retrieval as kr
        result = kr.route(actor, jid, "intake",
                          f"artwork intake {complexity['band']} complexity "
                          f"{subject}", top_k=3)
        retrieval = {"queried": True,
                     "hits": len(result.get("selected_records", [])),
                     "proof": result.get("retrieval_proof", "")}
    except Exception as exc:  # retrieval gap is itself recorded evidence
        retrieval = {"queried": True, "error": str(exc)[:200]}
    (jdir / "intake_retrieval.json").write_text(
        json.dumps(retrieval, indent=2) + "\n", encoding="utf-8")

    # 7) autonomous routing (deterministic, observable, reproducible)
    if missing:
        route, route_reason = "needs_customer_info", f"missing: {', '.join(missing)}"
    elif any(i.get("is_vector") for i in idents):
        route, route_reason = "artwork_received", "vector artwork supplied — skip re-vectorization review path"
    else:
        route, route_reason = "artwork_received", (
            f"raster artwork, complexity {complexity['band']} — route to Mila "
            f"(budget {complexity['experiment_budget_iters']} iters, "
            f"QA floor {complexity['qa_ssim_floor']})")
    jobs_mod.transition(jid, "requirements_extracted", actor=actor,
                        reason="intake requirements parsed")
    jobs_mod.transition(jid, route, actor=actor, reason=route_reason,
                        customer_image=str(primary) if primary else "")

    # 8) canonical artifacts (BRD's exact list)
    (jdir / "raw_email.json").write_text(
        json.dumps(raw_email, indent=2, default=str) + "\n", encoding="utf-8")
    (jdir / "artwork_review.md").write_text(_artwork_review_md(idents, reviews,
                                                               complexity),
                                            encoding="utf-8")
    (jdir / "missing_questions.md").write_text(_missing_md(missing),
                                               encoding="utf-8")
    (jdir / "intake_summary.md").write_text(
        _summary_md(jid, customer, subject, inventory, requirements, missing,
                    complexity, route, route_reason, retrieval),
        encoding="utf-8")
    (jdir / "intake_analysis.json").write_text(json.dumps({
        "inventory": inventory, "identification": idents, "reviews": reviews,
        "complexity": complexity, "requirements": requirements,
        "missing": missing, "route": route, "route_reason": route_reason,
        "retrieval": retrieval, "timestamp": _utcnow()},
        indent=2) + "\n", encoding="utf-8")

    # customer communication draft (traceable in job history)
    draft = _ack_draft(customer, subject, missing)
    (jdir / "customer_replies").mkdir(exist_ok=True)
    (jdir / "customer_replies" / "draft_acknowledgement.md").write_text(
        draft, encoding="utf-8")
    jobs_mod._audit(jid, "customer_draft",
                    {"file": "customer_replies/draft_acknowledgement.md"},
                    actor="melody")

    return jobs_mod.load_job(jid)


def _artwork_review_md(idents, reviews, complexity) -> str:
    lines = ["# Artwork Review", ""]
    for i in idents:
        lines += [f"## {i['file']}", "",
                  "```json", json.dumps(i, indent=2), "```", ""]
    for r in reviews:
        lines += [f"### Automated review — {r['file']}", "",
                  "```json", json.dumps(r, indent=2), "```", ""]
    lines += ["## Complexity", "", "```json",
              json.dumps(complexity, indent=2), "```", ""]
    return "\n".join(lines)


def _missing_md(missing) -> str:
    if not missing:
        return "# Missing Questions\n\nNone — all required production information present.\n"
    qs = "\n".join(f"- Confirm {m.replace('_', ' ')}" for m in missing)
    return f"# Missing Questions\n\n{qs}\n"


def _summary_md(jid, customer, subject, inventory, requirements, missing,
                complexity, route, route_reason, retrieval) -> str:
    inv = "\n".join(f"- `{i['file']}` ({i['category']}, {i['bytes']} B)"
                    for i in inventory) or "- (none)"
    req = "\n".join(f"- {k}: {v}" for k, v in requirements.items()) or "- (none)"
    return (f"# Intake Summary — {jid}\n\n"
            f"**Customer:** {customer}\n**Subject:** {subject}\n\n"
            f"## Attachments\n{inv}\n\n## Extracted requirements\n{req}\n\n"
            f"## Missing information\n"
            + ("\n".join(f"- {m}" for m in missing) or "- none") +
            f"\n\n## Complexity\n- score {complexity['complexity_score']}"
            f" ({complexity['band']}); budget "
            f"{complexity['experiment_budget_iters']} iters; QA floor "
            f"{complexity['qa_ssim_floor']}\n\n"
            f"## Knowledge retrieval\n- {json.dumps(retrieval)}\n\n"
            f"## Routing\n- **{route}** — {route_reason}\n")


def _ack_draft(customer, subject, missing) -> str:
    ask = ("".join(f"\n- {m.replace('_', ' ').capitalize()}" for m in missing)
           if missing else "")
    return (f"# Draft acknowledgement (review before sending)\n\n"
            f"Hi {customer},\n\nThanks for reaching out about "
            f"\"{subject or 'your embroidery request'}\". We've logged your "
            f"request and started processing."
            + (f"\n\nTo move forward we still need:{ask}" if ask else "")
            + "\n\nWe'll follow up with a preview as soon as artwork "
              "processing completes.\n\n— Jupiter Embroidery\n")


if __name__ == "__main__":
    import sys
    job = run_intake(Path(sys.argv[1]))
    print(json.dumps(job, indent=2))
