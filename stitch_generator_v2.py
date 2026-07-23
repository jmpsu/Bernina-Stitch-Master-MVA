#!/usr/bin/env python3
"""Generate embroidery stitch patterns from vectorized SVG contours.

Creates run-stitch and fill-stitch patterns from edge-detected contours.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


def extract_svg_contours(svg_path: str) -> list[dict]:
    """Extract contours from SVG."""
    svg_text = Path(svg_path).read_text()
    contours = []
    for match in re.finditer(r'<path d="([^"]+)"[^>]*fill="([^"]+)"', svg_text):
        path_d = match.group(1)
        fill_color = match.group(2)
        points = []
        for pt_match in re.finditer(r'(\d+(?:\.\d+)?),(\d+(?:\.\d+)?)', path_d):
            x, y = float(pt_match.group(1)), float(pt_match.group(2))
            points.append((x, y))
        if len(points) >= 3:
            contours.append({"points": points, "color": fill_color})
    return contours


def contour_to_stitches(points: list[tuple], stitch_spacing_mm: float = 2.5) -> list[tuple]:
    """Convert contour points to stitch coordinates (in mm).

    Uses run stitch along the contour outline.
    """
    mm_per_pixel = 0.127
    stitches = []

    # Add stitches along the contour at specified spacing
    total_distance = 0.0
    last_stitch_at = 0.0

    for i in range(len(points)):
        p1 = np.array(points[i])
        p2 = np.array(points[(i + 1) % len(points)])
        segment_len = np.linalg.norm(p2 - p1)
        total_distance += segment_len

        # If we've traveled enough distance, add a stitch
        if total_distance - last_stitch_at >= stitch_spacing_mm / mm_per_pixel:
            x, y = p2[0] * mm_per_pixel, p2[1] * mm_per_pixel
            stitches.append((x, y))
            last_stitch_at = total_distance

    # Ensure we end at the start point (run stitch closes the shape)
    if stitches and stitches[0] != stitches[-1]:
        stitches.append(stitches[0])

    return stitches


def fill_contour_with_stitches(
    points: list[tuple], spacing_mm: float = 0.5
) -> list[tuple]:
    """Fill a contour with parallel stitch lines (scanline fill).

    Creates serpentine (boustrophedon) pattern for filling.
    """
    mm_per_pixel = 0.127
    spacing_px = max(1, int(spacing_mm / mm_per_pixel))

    # Get bounding box
    points_arr = np.array(points)
    y_min, y_max = points_arr[:, 1].min(), points_arr[:, 1].max()
    x_min, x_max = points_arr[:, 0].min(), points_arr[:, 0].max()

    # Create binary mask
    mask = Image.new("L", (int(x_max) + 2, int(y_max) + 2), 0)
    draw = ImageDraw.Draw(mask)
    draw.polygon([(p[0], p[1]) for p in points], fill=255)
    mask_arr = np.array(mask, dtype=bool)

    stitches = []
    reverse = False

    # Scan horizontally with spacing
    for y in range(int(y_min), int(y_max) + 1, spacing_px):
        if y >= mask_arr.shape[0]:
            continue

        row = mask_arr[y, :]
        if row.sum() == 0:
            continue

        # Find runs of filled pixels
        runs = []
        in_run = False
        run_start = 0

        for x in range(len(row)):
            if row[x] and not in_run:
                in_run = True
                run_start = x
            elif not row[x] and in_run:
                in_run = False
                runs.append((run_start, x - 1))

        if in_run:
            runs.append((run_start, len(row) - 1))

        if not runs:
            continue

        # Alternate direction for serpentine
        if reverse:
            runs.reverse()

        # Add stitch points
        for run_start, run_end in runs:
            # Jump to start
            if stitches:
                stitches.append((float(run_start) * mm_per_pixel, float(y) * mm_per_pixel))
            # Stitch to end
            stitches.append((float(run_end) * mm_per_pixel, float(y) * mm_per_pixel))

        reverse = not reverse

    return stitches


def generate_stitch_plan(svg_path: str) -> dict:
    """Generate stitch plan from vectorized SVG."""
    contours = extract_svg_contours(svg_path)

    objects = []
    for contour in contours:
        points = contour["points"]
        if len(points) < 3:
            continue

        # Generate run stitches (outline)
        run_stitches = contour_to_stitches(points, stitch_spacing_mm=2.5)

        # Generate fill stitches (interior)
        fill_stitches = fill_contour_with_stitches(points, spacing_mm=0.5)

        obj = {
            "type": "embroidery_shape",
            "color": contour["color"],
            "outline_stitches": run_stitches,
            "fill_stitches": fill_stitches,
            "total_stitches": len(run_stitches) + len(fill_stitches),
        }
        objects.append(obj)

    total_stitches = sum(obj["total_stitches"] for obj in objects)

    return {
        "objects": objects,
        "total_stitches": total_stitches,
        "machine_format": "exp",
        "stitch_density": f"{total_stitches / (600 * 600) * 1000:.1f} stitches per 600x600px",
    }


def stitch_plan_to_exp(stitch_plan: dict) -> str:
    """Convert stitch plan to embroidery EXP format."""
    lines = ["STITCH FILE"]

    for obj in stitch_plan["objects"]:
        for x, y in obj["outline_stitches"] + obj["fill_stitches"]:
            # EXP format: coordinate pairs in 1/10mm units
            lines.append(f"{int(x*10)},{int(y*10)}")

    return "\n".join(lines)


def main():
    """Generate stitch plans for all vectorized images."""
    test_images = [
        "order_0001_drink_v2",
        "order_0002_img_0331",
        "order_0003_coastal_objects_all",
    ]

    Path("stitch_plans").mkdir(exist_ok=True)

    print("\n" + "="*70)
    print("GENERATING EMBROIDERY STITCH PATTERNS")
    print("="*70 + "\n")

    for stem in test_images:
        svg_path = f"vectorized_svg/{stem}_v2.svg"
        if not Path(svg_path).exists():
            print(f"✗ Missing SVG: {svg_path}")
            continue

        # Generate stitch plan
        stitch_plan = generate_stitch_plan(svg_path)

        # Save JSON
        json_path = f"stitch_plans/{stem}_v2.json"
        Path(json_path).write_text(json.dumps(stitch_plan, indent=2, default=str))
        print(f"✓ {json_path}: {stitch_plan['total_stitches']} stitches")

        # Save EXP format
        exp_text = stitch_plan_to_exp(stitch_plan)
        exp_path = f"stitch_plans/{stem}_v2.exp"
        Path(exp_path).write_text(exp_text)
        print(f"  → {exp_path}")

    print("\n" + "="*70)


if __name__ == "__main__":
    main()
