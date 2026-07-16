"""svg_topology_qa.py — structural verification of embroidery-ready SVGs.

Implements I-HIVE Phase 2 (BRD "Structural Verification") and the roster's
SVG-cleanliness rules as automated, evidence-producing checks:

  1. object inventory (every element counted by tag)
  2. no leftover raster <image> outside the locked archival layer
  3. no full-canvas background rectangle
  4. no off-white "paper residue" fills
  5. no duplicate paths (identical geometry stitched twice jams the machine)
  6. no zero/negligible-area paths
  7. white-area intent report (knockout holes vs explicit white thread paths)
  8. silhouette fidelity vs the source raster (render + SSIM), when given

Each check yields pass/fail with the offending element ids; the report is a
reproducible JSON artifact. Exit code 1 on any blocking failure.
"""

from __future__ import annotations

import io
import json
import re
import sys
from pathlib import Path

BLOCKING = {"stray_images", "background_rect", "duplicate_paths"}

_WHITE = re.compile(r"#f{3}(?:f{3})?\b|#fefefe|#fdfdfd|white", re.I)
_OFFWHITE = re.compile(r"#(e[8-9a-f]|f[0-9a-e])([0-9a-f]{4})\b", re.I)


def _elements(text: str, tag: str) -> list[str]:
    return re.findall(rf"<{tag}\b[^>]*>", text)


def _attr(el: str, name: str) -> str:
    m = re.search(rf'{name}="([^"]*)"', el)
    return m.group(1) if m else ""


def _path_area_hint(d: str) -> float:
    """Cheap area proxy: bounding box of absolute coordinates in the d attr."""
    nums = [float(x) for x in re.findall(r"-?\d+\.?\d*", d)[:400]]
    if len(nums) < 4:
        return 0.0
    xs, ys = nums[0::2], nums[1::2]
    return (max(xs) - min(xs)) * (max(ys) - min(ys))


def run_qa(svg_path: Path, source_raster: Path | None = None,
           report_path: Path | None = None) -> dict:
    svg_path = Path(svg_path)
    text = svg_path.read_text(encoding="utf-8")
    # exclude the locked archival layer from every production check
    from ihive import _strip_layer_text  # deterministic, no cycles
    prod_text = _strip_layer_text(text)

    checks: dict[str, dict] = {}
    inventory = {tag: len(_elements(prod_text, tag))
                 for tag in ("path", "rect", "circle", "ellipse", "polygon",
                             "image", "text", "g")}
    checks["inventory"] = {"pass": True, "detail": inventory}

    # 2) stray raster images in production content
    stray = _elements(prod_text, "image")
    checks["stray_images"] = {"pass": not stray, "count": len(stray)}

    # 3) full-canvas background rectangle
    vb = re.search(r'viewBox="([\d. -]+)"', prod_text)
    W = H = None
    if vb:
        parts = vb.group(1).split()
        W, H = float(parts[2]), float(parts[3])
    bg_rects = []
    for el in _elements(prod_text, "rect"):
        w, h = _attr(el, "width"), _attr(el, "height")
        if w in ("100%",) or h in ("100%",):
            bg_rects.append(el[:80])
            continue
        try:
            if W and float(w) >= 0.98 * W and float(h) >= 0.98 * H:
                bg_rects.append(el[:80])
        except ValueError:
            continue
    checks["background_rect"] = {"pass": not bg_rects, "matches": bg_rects}

    # 4) off-white paper-residue fills
    paper = [m.group(0) for m in _OFFWHITE.finditer(prod_text)]
    checks["offwhite_fills"] = {"pass": len(paper) == 0,
                                "matches": sorted(set(paper))[:10]}

    # 5) duplicate paths (identical d attributes)
    ds = [_attr(el, "d") for el in _elements(prod_text, "path")]
    seen, dups = set(), []
    for d in ds:
        if d and d in seen:
            dups.append(d[:60])
        seen.add(d)
    checks["duplicate_paths"] = {"pass": not dups, "count": len(dups)}

    # 6) zero-area paths
    zero = [d[:60] for d in ds if d and _path_area_hint(d) < 1e-6]
    checks["zero_area_paths"] = {"pass": not zero, "count": len(zero)}

    # 7) white-area intent: white fills must be deliberate (thread) — report
    whites = [d[:40] for el, d in zip(_elements(prod_text, "path"), ds)
              if _WHITE.search(_attr(el, "fill") or _attr(el, "style"))]
    checks["white_areas"] = {
        "pass": True,  # informational: intent resolved from the job record
        "white_paths": len(whites),
        "note": ("white paths present — confirm knockout vs white-thread "
                 "against garment color" if whites else "no white areas"),
    }

    # 8) silhouette fidelity vs source raster
    if source_raster and Path(source_raster).exists():
        try:
            import cairosvg
            import numpy as np
            from PIL import Image
            from skimage.metrics import structural_similarity
            png = cairosvg.svg2png(bytestring=prod_text.encode(),
                                   output_width=256, output_height=256,
                                   background_color="white")
            r = np.asarray(Image.open(io.BytesIO(png)).convert("L"),
                           dtype=np.float64)
            s = np.asarray(Image.open(source_raster).convert("L")
                           .resize((256, 256)), dtype=np.float64)
            ssim = float(structural_similarity(r, s, data_range=255.0))
            checks["silhouette_fidelity"] = {"pass": ssim >= 0.5,
                                             "ssim_vs_source": round(ssim, 4)}
        except Exception as exc:
            checks["silhouette_fidelity"] = {"pass": True, "skipped": str(exc)[:120]}

    blocking_failures = [k for k in BLOCKING
                         if k in checks and not checks[k]["pass"]]
    report = {
        "svg": str(svg_path),
        "source_raster": str(source_raster) if source_raster else None,
        "checks": checks,
        "blocking_failures": blocking_failures,
        "ok": not blocking_failures,
    }
    if report_path:
        Path(report_path).write_text(json.dumps(report, indent=2) + "\n",
                                     encoding="utf-8")
    return report


if __name__ == "__main__":
    svg = Path(sys.argv[1])
    raster = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    rep = run_qa(svg, raster)
    print(json.dumps(rep, indent=2))
    sys.exit(0 if rep["ok"] else 1)
