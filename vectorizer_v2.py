#!/usr/bin/env python3
"""vectorizer_v2.py — ground-up vectorization via edge detection + contour tracing.

Raster → grayscale → edge detection → contour tracing → SVG simplification.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage
from skimage import feature, measure, morphology


def load_image(path: str) -> np.ndarray:
    """Load PNG as grayscale uint8."""
    img = Image.open(path).convert("L")
    return np.array(img, dtype=np.uint8)


def detect_edges(gray: np.ndarray) -> np.ndarray:
    """Detect edges using Canny edge detection."""
    edges = feature.canny(gray, sigma=1.0)
    return edges.astype(np.uint8) * 255


def rdp_simplify(points: np.ndarray, epsilon: float = 1.5) -> np.ndarray:
    """Ramer-Douglas-Peucker contour simplification."""
    if len(points) < 3:
        return points

    start = points[0]
    end = points[-1]
    dmax = 0
    index = 0

    for i in range(1, len(points) - 1):
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


def extract_contours_from_edges(edges: np.ndarray, original_gray: np.ndarray) -> list[dict]:
    """Extract contours from edge-detected image."""
    # Dilate edges to fill small gaps
    edges_dilated = morphology.dilation(edges > 127)

    # Label connected components in edge regions
    labeled, num_features = ndimage.label(edges_dilated)

    regions = []
    for label_id in range(1, num_features + 1):
        mask = labeled == label_id
        area = mask.sum()

        # Skip very small regions (noise)
        if area < 50:
            continue

        # Find contours
        contours = measure.find_contours(mask.astype(float), level=0.5)

        if not contours:
            continue

        # Use longest contour (outer boundary)
        contour_pts = contours[0]
        if len(contours) > 1:
            contour_pts = max(contours, key=len)

        # Simplify if large
        if len(contour_pts) > 10:
            contour_pts = rdp_simplify(contour_pts, epsilon=1.5)

        # Convert (row, col) to (x, y)
        contour = [[int(x), int(y)] for y, x in contour_pts]

        # Get mean color from original in this region
        color_val = int(original_gray[mask].mean())
        color = (color_val, color_val, color_val)

        regions.append({
            "contour": contour,
            "area": area,
            "color": color,
        })

    regions.sort(key=lambda r: -r["area"])
    return regions


def paths_to_svg(regions: list[dict], width: int, height: int) -> str:
    """Convert regions to SVG polygon paths."""
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

        points_str = " L ".join(f"{int(pt[0])},{int(pt[1])}" for pt in contour)
        path_d = f"M {points_str} Z"

        color = region["color"]
        color_hex = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"

        svg_lines.append(f'<path d="{path_d}" fill="{color_hex}" stroke="none"/>')

    svg_lines.append("</svg>")
    return "\n".join(svg_lines)


def vectorize_v2(image_path: str) -> dict:
    """Full pipeline: raster → grayscale → edges → contours → SVG."""
    t0 = time.time()
    stem = Path(image_path).stem

    # Load as grayscale
    gray = load_image(image_path)
    h, w = gray.shape

    # Detect edges
    edges = detect_edges(gray)

    # Extract contours
    regions = extract_contours_from_edges(edges, gray)

    # Generate SVG
    svg_text = paths_to_svg(regions, w, h)

    # Save SVG
    out_dir = Path("vectorized_svg")
    out_dir.mkdir(exist_ok=True)
    svg_path = out_dir / f"{stem}_v2.svg"
    svg_path.write_text(svg_text)

    elapsed = time.time() - t0

    return {
        "image": image_path,
        "stem": stem,
        "svg_path": str(svg_path),
        "regions": len(regions),
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
