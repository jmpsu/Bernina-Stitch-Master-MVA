#!/usr/bin/env python3
"""Show comparison between original and vectorized SVG rendering."""

import re
from pathlib import Path
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


def render_svg(svg_path: str, width=480, height=201) -> Image.Image:
    """Render SVG to image."""
    contours = extract_svg_contours(svg_path)
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    for contour in contours:
        points = contour["points"]
        color_hex = contour["color"]
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


# Test images
tests = [
    ("order_0001_drink_v2", 480, 201),
    ("order_0002_img_0331", 480, 658),
    ("order_0003_coastal_objects_all", 480, 658),
]

print("\n" + "="*70)
print("VISUAL COMPARISON: ORIGINAL vs EDGE-DETECTED VECTORIZATION")
print("="*70 + "\n")

for stem, width, height in tests:
    orig_img = Image.open(f"input_images/{stem}.png").resize((width, height))
    vec_img = render_svg(f"vectorized_svg/{stem}_v2.svg", width=width, height=height)

    # Create side-by-side
    combined = Image.new("RGB", (width * 2 + 20, height + 60), "white")
    draw = ImageDraw.Draw(combined)

    draw.text((10, 10), "ORIGINAL", fill="black")
    draw.text((width + 30, 10), "VECTORIZED (Edge Detect)", fill="black")
    combined.paste(orig_img, (10, 40))
    combined.paste(vec_img, (width + 10, 40))

    out = f"comparison_output/{stem}_comparison.png"
    combined.save(out)
    print(f"✓ {out}")

print("\n" + "="*70)
