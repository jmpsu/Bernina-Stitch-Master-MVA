#!/usr/bin/env python3
"""vectorizer_v2.py — ground-up vectorization engine. No vtracer.

Direct raster → SVG via contour extraction + path simplification.
"""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage
from skimage import filters, measure, morphology

log = logging.getLogger("vectorizer_v2")

OUT_DIR = Path("vectorized_svg")


def load_image(path: str) -> np.ndarray:
    """Load PNG as RGB uint8."""
    img = Image.open(path).convert("RGB")
    return np.array(img, dtype=np.uint8)


def posterize_aggressive(rgb: np.ndarray, max_colors: int = 8) -> np.ndarray:
    """Flatten to max_colors via k-means in Lab space."""
    from skimage import color as skcolor

    h, w = rgb.shape[:2]
    lab = skcolor.rgb2lab(rgb.astype(np.float32) / 255.0)
    lab_flat = lab.reshape(-1, 3)

    # K-means
    rng = np.random.default_rng(42)
    idx = rng.choice(len(lab_flat), max_colors, replace=False)
    centers = lab_flat[idx].copy()

    for _ in range(10):
        dists = np.linalg.norm(lab_flat[:, None] - centers[None], axis=2)
        labels = dists.argmin(axis=1)
        for i in range(max_colors):
            if (labels == i).any():
                centers[i] = lab_flat[labels == i].mean(axis=0)

    # Map back
    dists = np.linalg.norm(lab_flat[:, None] - centers[None], axis=2)
    labels = dists.argmin(axis=1)
    lab_flat[...] = centers[labels]
    lab = lab_flat.reshape(h, w, 3)

    rgb_out = skcolor.lab2rgb(lab)
    return (np.clip(rgb_out, 0, 1) * 255).astype(np.uint8)


def rdp_simplify(points: np.ndarray, epsilon: float = 1.0) -> np.ndarray:
    """Ramer-Douglas-Peucker contour simplification."""
    if len(points) < 3:
        return points

    start = points[0]
    end = points[-1]
    dmax = 0
    index = 0

    for i in range(1, len(points) - 1):
        # Point-to-line distance
        line_vec = end - start
        point_vec = points[i] - start
        line_len = np.linalg.norm(line_vec)
        if line_len > 0:
            d = np.abs(line_vec[0] * point_vec[1] - line_vec[1] * point_vec[0]) / line_len
        else:
            d = np.linalg.norm(point_vec)
        if d > dmax:
            dmax = d
            index = i

    if dmax > epsilon:
        rec1 = rdp_simplify(points[:index+1], epsilon)
        rec2 = rdp_simplify(points[index:], epsilon)
        return np.vstack([rec1[:-1], rec2])
    else:
        return np.array([start, end])


def extract_contours(rgb: np.ndarray, min_area: int = 100) -> list[dict]:
    """Extract actual contours from posterized image via connected components."""
    # Convert to grayscale
    gray = rgb.mean(axis=2).astype(np.uint8)

    # Binary threshold at midpoint
    binary = gray > 127

    # Label connected components
    labeled, num_features = ndimage.label(binary)

    regions = []
    for label_id in range(1, num_features + 1):
        mask = labeled == label_id
        area = mask.sum()

        if area < min_area:
            continue

        # Trace actual contour using skimage
        contours = measure.find_contours(mask.astype(float), level=0.5)

        if not contours:
            continue

        # Use longest contour (outer boundary)
        contour_pts = contours[0]
        if len(contours) > 1:
            contour_pts = max(contours, key=len)

        # Simplify contour by decimation + RDP
        if len(contour_pts) > 4:
            # Decimate by keeping every nth point
            decimated = contour_pts[::max(1, len(contour_pts) // 20)]
            # Apply RDP simplification
            simplified = rdp_simplify(decimated, epsilon=1.0)
            contour_pts = simplified

        # Convert from (row, col) to (x, y) and to list of lists
        contour = [[int(x), int(y)] for y, x in contour_pts]

        # Get mean color from mask
        color = tuple(int(c) for c in rgb[mask].mean(axis=0))

        # Get bounding box
        rows, cols = np.where(mask)
        x_min, x_max = cols.min(), cols.max()
        y_min, y_max = rows.min(), rows.max()

        regions.append({
            "contour": contour,
            "area": area,
            "color": color,
            "bbox": [x_min, y_min, x_max - x_min, y_max - y_min],
            "mask": mask,
        })

    # Sort by area (largest first)
    regions.sort(key=lambda r: -r["area"])
    return regions


def paths_to_svg(regions: list[dict], width: int, height: int) -> str:
    """Convert regions (actual contours) to SVG polygon paths."""
    svg_lines = [
        f'<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        f'xmlns="http://www.w3.org/2000/svg">',
        f'<rect width="{width}" height="{height}" fill="white"/>',
    ]

    for region in regions:
        contour = region["contour"]
        if not contour or len(contour) < 3:
            continue

        # Build path from contour points: M x,y L x,y ... Z
        points_str = " L ".join(f"{int(pt[0])},{int(pt[1])}" for pt in contour)
        path_d = f"M {points_str} Z"

        color = region["color"]
        color_hex = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"

        svg_lines.append(
            f'<path d="{path_d}" fill="{color_hex}" stroke="none"/>'
        )

    svg_lines.append("</svg>")
    return "\n".join(svg_lines)


def svg_to_stitch_plan(svg_text: str, mm_per_px: float = 0.127) -> dict:
    """Convert SVG paths to stitch plan (polylines with stitch points)."""
    import re

    stitch_rows = []

    # Extract all path elements
    for match in re.finditer(r'<path d="([^"]+)"[^>]*fill="([^"]+)"', svg_text):
        path_d = match.group(1)
        fill_color = match.group(2)

        # Parse path: simple case of M x,y L x,y ... Z
        points = []
        for pt_match in re.finditer(r'(\d+),(\d+)', path_d):
            x, y = int(pt_match.group(1)), int(pt_match.group(2))
            points.append((x, y))

        if len(points) < 2:
            continue

        # Stitch points: simple scanline-like interpolation
        stitches = []
        for i, (x, y) in enumerate(points):
            stitches.append((x * mm_per_px, y * mm_per_px))

        # Create stitch object
        stitch_rows.append({
            "type": "fill",
            "color": fill_color,
            "points": stitches,
            "stitch_count": len(stitches),
        })

    return {"objects": stitch_rows, "total_stitches": sum(s["stitch_count"] for s in stitch_rows)}


def vectorize_v2(image_path: str) -> dict:
    """Full pipeline: raster → posterize → contours → SVG → stitch plan."""
    t0 = time.time()
    stem = Path(image_path).stem

    # Load
    rgb = load_image(image_path)
    h, w = rgb.shape[:2]

    # Posterize aggressively
    rgb_poster = posterize_aggressive(rgb, max_colors=8)

    # Extract contours
    regions = extract_contours(rgb_poster, min_area=200)

    # Generate SVG
    svg_text = paths_to_svg(regions, w, h)

    # Save SVG
    OUT_DIR.mkdir(exist_ok=True)
    svg_path = OUT_DIR / f"{stem}_v2.svg"
    svg_path.write_text(svg_text)

    # Generate stitch plan
    stitch_plan = svg_to_stitch_plan(svg_text)

    elapsed = time.time() - t0

    return {
        "image": image_path,
        "stem": stem,
        "svg_path": str(svg_path),
        "regions": len(regions),
        "stitch_plan": stitch_plan,
        "elapsed_sec": elapsed,
        "status": "ok",
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: vectorizer_v2.py <image.png>")
        sys.exit(1)

    result = vectorize_v2(sys.argv[1])
    print(json.dumps(result, indent=2))
