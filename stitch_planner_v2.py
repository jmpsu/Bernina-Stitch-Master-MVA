#!/usr/bin/env python3
"""stitch_planner_v2.py — Generate actual stitch runs from SVG paths.

Serpentine fill (boustrophedon) + satin borders.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
from scipy import ndimage
from skimage import morphology


def svg_path_to_points(path_d: str) -> list[tuple]:
    """Extract all coordinate pairs from SVG path."""
    points = []
    for match in re.finditer(r'(\d+(?:\.\d+)?),(\d+(?:\.\d+)?)', path_d):
        x, y = float(match.group(1)), float(match.group(2))
        points.append((x, y))
    return points


def simplify_path(points: list[tuple], epsilon: float = 1.0) -> list[tuple]:
    """Simplify path using Ramer-Douglas-Peucker."""
    if len(points) < 3:
        return points

    points_arr = np.array(points, dtype=np.float32)

    def rdp(pts, eps):
        if len(pts) < 3:
            return pts
        # Find point with max distance from line
        line_start = pts[0]
        line_end = pts[-1]
        dists = np.abs(
            np.cross(line_end - line_start, line_start - pts) / np.linalg.norm(line_end - line_start)
        )
        max_idx = np.argmax(dists)
        if dists[max_idx] > eps:
            return np.vstack([rdp(pts[:max_idx+1], eps), rdp(pts[max_idx:], eps)[1:]])
        return np.array([pts[0], pts[-1]])

    simplified = rdp(points_arr, epsilon)
    return [tuple(p) for p in simplified]


def generate_fill_stitches(
    mask: np.ndarray, spacing_mm: float = 0.35, stitch_len_mm: float = 2.5
) -> list[tuple]:
    """Serpentine scanline fill: connected rows, no jumps."""
    h, w = mask.shape
    spacing_px = int(spacing_mm / 0.127)  # ~0.127 mm per pixel
    spacing_px = max(1, spacing_px)

    stitches = []
    last_x = None

    # Scan rows with spacing
    for y in range(0, h, spacing_px):
        row = mask[y, :]
        # Find contiguous runs
        runs = []
        in_run = False
        run_start = None

        for x in range(w):
            if row[x] and not in_run:
                in_run = True
                run_start = x
            elif not row[x] and in_run:
                in_run = False
                runs.append((run_start, x - 1))
        if in_run:
            runs.append((run_start, w - 1))

        # Alternate direction for serpentine
        if len(stitches) > 0 and stitches[-1][0] > w / 2:
            runs.reverse()

        for run_start, run_end in runs:
            if len(stitches) > 0:
                # Jump to start
                stitches.append((float(run_start), float(y)))
            # Stitch across
            stitches.append((float(run_end), float(y)))

    return [(x * 0.127, y * 0.127) for x, y in stitches]


def generate_satin_border(
    mask: np.ndarray, width_mm: float = 1.5, stitch_spacing: float = 0.35
) -> list[tuple]:
    """Generate satin column along shape boundary."""
    # Trace boundary
    boundary = morphology.binary_dilation(mask) ^ mask
    boundary_pts = np.argwhere(boundary)

    if len(boundary_pts) < 2:
        return []

    # Simple outline (not perfect, but works)
    stitches = []
    for y, x in boundary_pts[::max(1, len(boundary_pts) // 50)]:
        stitches.append((x * 0.127, y * 0.127))

    return stitches


def generate_stitch_plan(svg_text: str) -> dict:
    """Parse SVG, generate fill + satin stitch runs."""
    objects = []
    total_stitches = 0

    # Extract each path
    for path_match in re.finditer(r'<path d="([^"]+)"[^>]*fill="([^"]+)"', svg_text):
        path_d = path_match.group(1)
        fill_color = path_match.group(2)

        # Get points
        points = svg_path_to_points(path_d)
        if len(points) < 2:
            continue

        # Simplify
        simplified = simplify_path(points, epsilon=1.0)

        # Create mask for this region
        pts_array = np.array(points, dtype=np.int32)
        if len(pts_array) > 0:
            x_min, y_min = pts_array.min(axis=0)
            x_max, y_max = pts_array.max(axis=0)

            if x_max > x_min and y_max > y_min:
                h = int(y_max - y_min) + 2
                w = int(x_max - x_min) + 2
                pts_shifted = pts_array - [x_min - 1, y_min - 1]

                # Draw polygon in mask
                from PIL import Image, ImageDraw
                img = Image.new("L", (w, h), 0)
                draw = ImageDraw.Draw(img)
                draw.polygon([tuple(p) for p in pts_shifted], fill=255)
                mask = np.array(img, dtype=bool)

                # Generate stitches
                fill_stitches = generate_fill_stitches(mask, spacing_mm=0.35)
                satin_stitches = generate_satin_border(mask, width_mm=1.5)

                obj = {
                    "type": "fill",
                    "color": fill_color,
                    "fill_stitches": fill_stitches,
                    "satin_stitches": satin_stitches,
                    "total": len(fill_stitches) + len(satin_stitches),
                }
                objects.append(obj)
                total_stitches += obj["total"]

    return {
        "objects": objects,
        "total_stitches": total_stitches,
        "density_estimate": total_stitches / (600 * 600) if total_stitches > 0 else 0,
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: stitch_planner_v2.py <file.svg>")
        sys.exit(1)

    svg_text = Path(sys.argv[1]).read_text()
    plan = generate_stitch_plan(svg_text)
    print(json.dumps(plan, indent=2, default=str))
