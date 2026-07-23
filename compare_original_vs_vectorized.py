#!/usr/bin/env python3
"""Side-by-side visual comparison: original PNG vs vectorized SVG."""

from pathlib import Path
import re
from PIL import Image, ImageDraw


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
            })

    return contours


def render_svg(svg_path: str, width: int = 480, height: int = 201) -> Image.Image:
    """Render SVG to PIL Image."""
    contours = extract_svg_contours(svg_path)

    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)

    for contour in contours:
        points = contour["points"]
        color_hex = contour["color"]

        # Parse hex color
        try:
            if color_hex.startswith("#"):
                color_hex = color_hex[1:]
            r = int(color_hex[0:2], 16)
            g = int(color_hex[2:4], 16)
            b = int(color_hex[4:6], 16)
            fill_color = (r, g, b)
        except:
            fill_color = (200, 200, 200)

        if len(points) >= 3:
            draw.polygon(points, fill=fill_color, outline=(50, 50, 50))

    return img


def create_side_by_side(original_path: str, svg_path: str, output_path: str):
    """Create side-by-side comparison image."""
    # Load original
    original = Image.open(original_path).convert("RGB")
    orig_w, orig_h = original.size

    # Render SVG
    vectorized = render_svg(svg_path, width=orig_w, height=orig_h)

    # Create combined image
    total_width = orig_w * 2 + 40  # 20px padding on sides, 40px between
    total_height = orig_h + 80  # 40px padding top/bottom for labels

    combined = Image.new("RGB", (total_width, total_height), "white")
    draw = ImageDraw.Draw(combined)

    # Add labels
    draw.text((20, 10), "ORIGINAL", fill="black")
    draw.text((orig_w + 60, 10), "VECTORIZED SVG", fill="black")

    # Paste images
    combined.paste(original, (20, 40))
    combined.paste(vectorized, (orig_w + 40, 40))

    # Draw separator line
    draw.line([(orig_w + 30, 40), (orig_w + 30, orig_h + 40)], fill="gray", width=2)

    combined.save(output_path)
    print(f"✓ {output_path}")


def main():
    """Generate comparisons for all images."""
    Path("comparison_output").mkdir(exist_ok=True)

    test_images = [
        ("order_0001_drink_v2.png", "order_0001_drink_v2.png"),
        ("order_0002_img_0331.png", "order_0002_img_0331.png"),
        ("order_0003_coastal_objects_all.png", "order_0003_coastal_objects_all.png"),
    ]

    print("\n" + "="*70)
    print("GENERATING VISUAL COMPARISONS: ORIGINAL vs VECTORIZED")
    print("="*70 + "\n")

    for orig_name, stem in test_images:
        orig_path = f"input_images/{orig_name}"
        # Try with _v2 suffix first
        svg_path = f"vectorized_svg/{stem}_v2.svg"
        if not Path(svg_path).exists():
            # Fall back to without suffix
            svg_path = f"vectorized_svg/{stem}.svg"
        out_path = f"comparison_output/{stem}_comparison.png"

        if not Path(orig_path).exists():
            print(f"✗ Missing original: {orig_path}")
            continue
        if not Path(svg_path).exists():
            print(f"✗ Missing SVG: {svg_path}")
            continue

        create_side_by_side(orig_path, svg_path, out_path)

    print("\n" + "="*70)
    print(f"Comparisons saved to: comparison_output/")
    print("="*70)


if __name__ == "__main__":
    main()
