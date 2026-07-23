#!/usr/bin/env python3
"""Evaluate vectorization quality: compare outputs across git iterations.

Metrics:
- Silhouette matching: pixel-level overlap between rasterized SVG and original
- Contour quality: point density, smoothness, curve accuracy
- Proportions: bounding box and area preservation
- Visual consistency: deviation from expected embroidery digitization
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from skimage import measure


class QualityMetrics(NamedTuple):
    """Vectorization quality metrics."""
    iteration: str
    image_name: str
    svg_path: str
    silhouette_iou: float
    contour_point_count: int
    avg_point_spacing: float
    bbox_iou: float
    area_preservation: float
    complexity_score: float


def extract_svg_contours(svg_path: str) -> list[dict]:
    """Extract path contours from SVG file."""
    try:
        svg_text = Path(svg_path).read_text()
    except FileNotFoundError:
        return []

    contours = []
    for match in re.finditer(r'<path d="([^"]+)"[^>]*fill="([^"]+)"', svg_text):
        path_d = match.group(1)
        fill_color = match.group(2)

        # Parse M x,y L x,y ... Z format
        points = []
        for pt_match in re.finditer(r'(\d+(?:\.\d+)?),(\d+(?:\.\d+)?)', path_d):
            x, y = float(pt_match.group(1)), float(pt_match.group(2))
            points.append((x, y))

        if len(points) >= 3:
            contours.append({
                "points": points,
                "color": fill_color,
                "point_count": len(points),
            })

    return contours


def rasterize_svg(svg_path: str, width: int = 480, height: int = 201) -> np.ndarray:
    """Convert SVG to binary raster (silhouette)."""
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return np.zeros((height, width), dtype=bool)

    contours = extract_svg_contours(svg_path)
    if not contours:
        return np.zeros((height, width), dtype=bool)

    img = Image.new("1", (width, height), 0)
    draw = ImageDraw.Draw(img)

    for contour in contours:
        points = contour["points"]
        if len(points) >= 3:
            draw.polygon(points, fill=1)

    return np.array(img, dtype=bool)


def compute_silhouette_iou(original: np.ndarray, rasterized: np.ndarray) -> float:
    """Compute Intersection over Union between original and rasterized SVG."""
    if original.size == 0 or rasterized.size == 0:
        return 0.0

    # Ensure same size
    if original.shape != rasterized.shape:
        h, w = max(original.shape[0], rasterized.shape[0]), max(original.shape[1], rasterized.shape[1])
        orig_padded = np.zeros((h, w), dtype=bool)
        rast_padded = np.zeros((h, w), dtype=bool)
        orig_padded[:original.shape[0], :original.shape[1]] = original
        rast_padded[:rasterized.shape[0], :rasterized.shape[1]] = rasterized
        original = orig_padded
        rasterized = rast_padded

    intersection = np.logical_and(original, rasterized).sum()
    union = np.logical_or(original, rasterized).sum()

    if union == 0:
        return 0.0
    return float(intersection) / float(union)


def compute_bbox_iou(original: np.ndarray, rasterized: np.ndarray) -> float:
    """Compute IoU of bounding boxes."""
    def get_bbox(mask):
        if mask.sum() == 0:
            return None
        rows, cols = np.where(mask)
        return (rows.min(), cols.min(), rows.max(), cols.max())

    bbox_orig = get_bbox(original)
    bbox_rast = get_bbox(rasterized)

    if bbox_orig is None or bbox_rast is None:
        return 0.0

    # Compute intersection of boxes
    y1_min = max(bbox_orig[0], bbox_rast[0])
    x1_min = max(bbox_orig[1], bbox_rast[1])
    y1_max = min(bbox_orig[2], bbox_rast[2])
    x1_max = min(bbox_orig[3], bbox_rast[3])

    if y1_max < y1_min or x1_max < x1_min:
        return 0.0

    intersection = (y1_max - y1_min) * (x1_max - x1_min)
    area_orig = (bbox_orig[2] - bbox_orig[0]) * (bbox_orig[3] - bbox_orig[1])
    area_rast = (bbox_rast[2] - bbox_rast[0]) * (bbox_rast[3] - bbox_rast[1])
    union = area_orig + area_rast - intersection

    if union == 0:
        return 0.0
    return float(intersection) / float(union)


def compute_area_preservation(original: np.ndarray, rasterized: np.ndarray) -> float:
    """Compute how well area is preserved (ratio of areas)."""
    area_orig = original.sum()
    area_rast = rasterized.sum()

    if area_orig == 0:
        return 1.0 if area_rast == 0 else 0.0

    ratio = area_rast / area_orig
    return float(min(ratio, 1.0 / ratio)) if ratio > 0 else 0.0


def compute_contour_metrics(contours: list[dict]) -> tuple[int, float]:
    """Compute average point spacing and total point count."""
    if not contours:
        return 0, 0.0

    total_points = 0
    total_spacing = 0
    spacing_count = 0

    for contour in contours:
        points = contour["points"]
        total_points += len(points)

        # Compute spacing between consecutive points
        for i in range(len(points)):
            p1 = points[i]
            p2 = points[(i + 1) % len(points)]
            dist = np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
            total_spacing += dist
            spacing_count += 1

    avg_spacing = total_spacing / spacing_count if spacing_count > 0 else 0
    return total_points, avg_spacing


def load_image_binary(image_path: str) -> np.ndarray:
    """Load image and convert to binary silhouette."""
    try:
        img = Image.open(image_path).convert("L")
        img_array = np.array(img, dtype=np.uint8)
        # Binary threshold
        binary = img_array > 127
        return binary
    except Exception as e:
        print(f"  Error loading {image_path}: {e}", file=sys.stderr)
        return np.zeros((1, 1), dtype=bool)


def get_image_dimensions(image_path: str) -> tuple[int, int]:
    """Get image dimensions."""
    try:
        img = Image.open(image_path)
        return img.size[::-1]  # Return (height, width)
    except:
        return 201, 480  # Default


def evaluate_iteration(iteration: str, image_name: str, image_path: str, svg_path: str) -> QualityMetrics | None:
    """Evaluate single iteration's output."""
    if not Path(svg_path).exists():
        return None

    # Load original image
    original_binary = load_image_binary(image_path)
    h, w = get_image_dimensions(image_path)

    # Rasterize SVG
    rasterized = rasterize_svg(svg_path, width=w, height=h)

    # Extract contours from SVG
    contours = extract_svg_contours(svg_path)

    # Compute metrics
    silhouette_iou = compute_silhouette_iou(original_binary, rasterized)
    bbox_iou = compute_bbox_iou(original_binary, rasterized)
    area_preservation = compute_area_preservation(original_binary, rasterized)
    point_count, avg_spacing = compute_contour_metrics(contours)

    # Complexity score: balance between point density and smoothness
    # Higher is more detailed but risks over-fitting noise
    complexity_score = min(point_count / 50.0, 2.0) if point_count > 0 else 0.0

    return QualityMetrics(
        iteration=iteration,
        image_name=image_name,
        svg_path=svg_path,
        silhouette_iou=silhouette_iou,
        contour_point_count=point_count,
        avg_point_spacing=avg_spacing,
        bbox_iou=bbox_iou,
        area_preservation=area_preservation,
        complexity_score=complexity_score,
    )


def run_iteration(commit_hash: str) -> bool:
    """Checkout commit and run vectorizer on test images."""
    print(f"\n{'='*70}")
    print(f"Evaluating iteration: {commit_hash}")
    print(f"{'='*70}")

    # Checkout commit
    try:
        subprocess.run(
            ["git", "checkout", commit_hash],
            cwd=Path.cwd(),
            capture_output=True,
            check=True,
            timeout=10,
        )
        print(f"✓ Checked out {commit_hash}")
    except Exception as e:
        print(f"✗ Failed to checkout: {e}", file=sys.stderr)
        return False

    return True


def main():
    """Evaluate vectorization quality across iterations."""
    test_images = [
        ("order_0001_drink_v2.png", "input_images/order_0001_drink_v2.png"),
        ("order_0002_img_0331.png", "input_images/order_0002_img_0331.png"),
        ("order_0003_coastal_objects_all.png", "input_images/order_0003_coastal_objects_all.png"),
    ]

    # Define iterations to compare (git commits)
    iterations = [
        ("e784db9", "v2.0 - Bounding boxes only"),
        ("45b30bd", "v2.1 - Contour tracing with RDP"),
    ]

    results: list[QualityMetrics] = []

    for commit_hash, label in iterations:
        # Checkout iteration
        if not run_iteration(commit_hash):
            continue

        # Evaluate each test image
        for image_name, image_path in test_images:
            # Infer SVG path based on vectorizer output
            stem = Path(image_path).stem
            svg_path = f"vectorized_svg/{stem}_v2.svg"

            # Run evaluation
            metrics = evaluate_iteration(commit_hash, image_name, image_path, svg_path)
            if metrics:
                results.append(metrics)
                print(
                    f"  {image_name}: "
                    f"IOU={metrics.silhouette_iou:.3f}, "
                    f"Points={metrics.contour_point_count}, "
                    f"Spacing={metrics.avg_point_spacing:.2f}"
                )

    # Generate report
    print(f"\n{'='*70}")
    print("EVALUATION SUMMARY")
    print(f"{'='*70}\n")

    if not results:
        print("No results to compare.")
        return

    # Group by image
    by_image = {}
    for result in results:
        if result.image_name not in by_image:
            by_image[result.image_name] = []
        by_image[result.image_name].append(result)

    # Print comparison table
    for image_name, metrics_list in by_image.items():
        print(f"\n{image_name}")
        print("-" * 70)
        print(f"{'Iteration':<25} {'Silhouette IOU':<15} {'Points':<10} {'Spacing':<10}")
        print("-" * 70)

        for m in metrics_list:
            iteration_label = m.iteration[:8]  # Short commit hash
            print(
                f"{iteration_label:<25} {m.silhouette_iou:<15.3f} "
                f"{m.contour_point_count:<10} {m.avg_point_spacing:<10.2f}"
            )

    # Quality delta analysis
    print(f"\n{'='*70}")
    print("QUALITY IMPROVEMENTS")
    print(f"{'='*70}\n")

    for image_name, metrics_list in by_image.items():
        if len(metrics_list) < 2:
            continue

        old = metrics_list[0]
        new = metrics_list[1]

        iou_delta = new.silhouette_iou - old.silhouette_iou
        point_delta = new.contour_point_count - old.contour_point_count
        spacing_delta = new.avg_point_spacing - old.avg_point_spacing

        print(f"{image_name}")
        print(f"  Silhouette IOU:     {old.silhouette_iou:.3f} → {new.silhouette_iou:.3f} ({iou_delta:+.3f})")
        print(f"  Contour points:     {old.contour_point_count} → {new.contour_point_count} ({point_delta:+d})")
        print(f"  Avg point spacing:  {old.avg_point_spacing:.2f} → {new.avg_point_spacing:.2f} ({spacing_delta:+.2f})")
        print()

    # Save detailed results to JSON
    output_file = Path("vectorization_eval_results.json")
    output_file.write_text(
        json.dumps(
            [
                {
                    "iteration": m.iteration,
                    "image": m.image_name,
                    "svg_path": m.svg_path,
                    "silhouette_iou": m.silhouette_iou,
                    "contour_points": m.contour_point_count,
                    "avg_point_spacing": m.avg_point_spacing,
                    "bbox_iou": m.bbox_iou,
                    "area_preservation": m.area_preservation,
                    "complexity_score": m.complexity_score,
                }
                for m in results
            ],
            indent=2,
        )
    )
    print(f"Detailed results saved to: {output_file}")

    # Restore to original branch
    try:
        subprocess.run(
            ["git", "checkout", "-"],
            cwd=Path.cwd(),
            capture_output=True,
            timeout=10,
        )
        print(f"\n✓ Restored to original branch")
    except:
        pass


if __name__ == "__main__":
    main()
