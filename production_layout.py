#!/usr/bin/env python3
"""Production-run visual output: composite artwork onto a ruler/grid template.

After a design's final stitch plan is generated, this module renders THREE
mobile-friendly JPEGs into ``production_runs/<stem>/`` so the customer can
review both dimensions and fidelity from a phone:

  1. ``1_original_on_ruler.jpg``   original customer raster, background removed
  2. ``2_svg_on_ruler.jpg``        the generated vector (SVG) render
  3. ``3_stitchplan_on_ruler.jpg`` the PES stitch-out render

All three subjects are scaled to the SAME true production size (3 in / 76.2 mm
tall) and composited over an attached transparent L-ruler + square-grid
background, anchored at the ruler origin, so the artwork visibly spans the
correct number of grid units / ruler inches and the three images are directly
comparable.

Ruler-template calibration (measured from assets/ruler_grid_background.png,
the clean IMG_0931 template, 704x1527 px):
  * The white background is a square grid; one grid square == 0.25 in and
    measures ~70.8 px (grid lines detected at 70-71 px spacing in both axes).
    => 4 grid squares per inch.
  * The transparent L-ruler on the left/bottom is an INCH scale. Its bold
    number labels 0/1/2 sit at y == 1226/945/666 px (center), i.e. 2 inches
    span 560 px => 280 px/in, agreeing with the grid (4 * 70.8 = 283).
  * We adopt PIXELS_PER_INCH = 283.0 (grid-derived; 0.25 in per square).
    A 3 in subject therefore spans 3 * 283 = 849 px == 12 grid squares.
  * The L-ruler ORIGIN (the 0/0 corner) is the bottom-left anchor at
    approx (x=155, y=1230): x just right of the vertical ruler's measuring
    edge, y on the 0-inch line. Subjects are placed bottom-left at the origin
    and grow up-and-to-the-right, exactly like the sample patches in
    IMG_0928/IMG_0929, so their height reads directly against the inch ticks.

Every renderer is defensive: any failure returns None / is logged and skipped
so visual generation never crashes stitch-plan generation.
"""

import os
import io
import tempfile

import numpy as np
from PIL import Image

# Reuse existing pipeline pieces.
import digitizer  # remove_background(), render_preview() (color PES renderer)

ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
RULER_BG_PATH = os.path.join(ASSETS_DIR, "ruler_grid_background.png")

# --- Calibrated ruler-template constants (see module docstring) -------------
PIXELS_PER_INCH = 283.0          # grid: 0.25 in per ~70.8 px square
GRID_INCH_PER_SQUARE = 0.25      # 4 grid squares == 1 inch
RULER_ORIGIN = (155, 1230)       # (x, y) bottom-left 0/0 corner, in bg pixels

MM_PER_INCH = 25.4


def load_ruler_background():
    """Return (bg_rgba PIL.Image, pixels_per_inch float, origin (x,y) tuple).

    origin is the L-ruler 0/0 corner (bottom-left anchor for subjects)."""
    bg = Image.open(RULER_BG_PATH).convert("RGBA")
    return bg, PIXELS_PER_INCH, RULER_ORIGIN


# ----------------------------------------------------------------------------
# Subject builders -> RGBA with transparent (alpha=0) background
# ----------------------------------------------------------------------------
def _bg_alpha_from_corners(rgb, white_thr=245, tol=28):
    """Return an alpha channel (uint8) keying out the background of an
    opaque RGB render: pixels near white OR near the median corner colour
    become transparent. Mirrors the corner-sampling idea used in digitizer's
    fallback background removal, so it handles both white and coloured
    SVG/PES backgrounds robustly."""
    h, w = rgb.shape[:2]
    ch, cw = max(1, h // 20), max(1, w // 20)
    corners = np.concatenate([
        rgb[:ch, :cw].reshape(-1, 3),
        rgb[:ch, -cw:].reshape(-1, 3),
        rgb[-ch:, :cw].reshape(-1, 3),
        rgb[-ch:, -cw:].reshape(-1, 3),
    ], axis=0).astype(np.float64)
    bg_col = np.median(corners, axis=0)

    a = rgb.astype(np.float64)
    near_white = a.min(axis=2) >= white_thr
    dist = np.linalg.norm(a - bg_col[None, None, :], axis=2)
    near_bg = dist <= tol
    transparent = near_white | near_bg
    alpha = np.where(transparent, 0, 255).astype(np.uint8)
    return alpha


def subject_from_original(original_path):
    """Original customer raster with background removed -> RGBA (numpy)."""
    rgb, mask, _method = digitizer.remove_background(original_path)
    alpha = np.where(mask, 255, 0).astype(np.uint8)
    rgba = np.dstack([rgb.astype(np.uint8), alpha])
    return rgba


def _render_svg_rgba(svg_path, out_width=1200):
    """Rasterize an SVG to an opaque RGB numpy array via cairosvg (same
    engine metrics.render_svg_to_gray uses), composited over white.
    Returns HxWx3 uint8 or None."""
    try:
        import cairosvg
    except Exception:
        return None
    try:
        png_bytes = cairosvg.svg2png(url=svg_path, output_width=out_width)
        img = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
        white = Image.new("RGBA", img.size, (255, 255, 255, 255))
        white.alpha_composite(img)
        return np.asarray(white.convert("RGB"), dtype=np.uint8)
    except Exception:
        return None


def subject_from_svg(svg_path):
    """Render SVG and key out its (white or coloured) background -> RGBA."""
    rgb = _render_svg_rgba(svg_path)
    if rgb is None:
        return None
    alpha = _bg_alpha_from_corners(rgb)
    return np.dstack([rgb, alpha])


def _pes_thread_rgbs(pattern):
    rgbs = []
    try:
        for t in pattern.threadlist:
            rgbs.append([t.get_red(), t.get_green(), t.get_blue()])
    except Exception:
        pass
    if not rgbs:
        rgbs = [[30, 30, 30]]
    return rgbs


def subject_from_pes(pes_path):
    """Render the PES stitch-out in colour (reusing digitizer.render_preview)
    and key out the near-white preview background -> RGBA."""
    import pyembroidery as pe
    try:
        pattern = pe.read(pes_path)
    except Exception:
        return None
    if pattern is None or not pattern.stitches:
        return None
    thread_rgbs = _pes_thread_rgbs(pattern)
    tmp = tempfile.NamedTemporaryFile(suffix="_pes.png", delete=False)
    tmp.close()
    try:
        # render_preview draws coloured sewn paths on a (250,250,250) canvas.
        digitizer.render_preview(pattern, thread_rgbs, tmp.name, px_per_mm=8.0)
        rgb = np.asarray(Image.open(tmp.name).convert("RGB"), dtype=np.uint8)
    except Exception:
        return None
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass
    alpha = _bg_alpha_from_corners(rgb)
    return np.dstack([rgb, alpha])


# ----------------------------------------------------------------------------
# Composition
# ----------------------------------------------------------------------------
def _tight_rgba(rgba, alpha_thr=8):
    """Crop an RGBA numpy array to its non-transparent bounding box.
    Returns a PIL RGBA image, or None if fully transparent."""
    alpha = rgba[..., 3]
    ys, xs = np.where(alpha > alpha_thr)
    if len(ys) == 0:
        return None
    r0, r1 = ys.min(), ys.max() + 1
    c0, c1 = xs.min(), xs.max() + 1
    return Image.fromarray(rgba[r0:r1, c0:c1], mode="RGBA")


def compose_on_ruler(subject_rgba, target_h_in=3.0):
    """Scale subject so its non-transparent bbox height == target_h_in * ppi,
    anchor its bottom-left at the ruler origin, alpha-composite over the ruler
    background, and return an RGB PIL image."""
    bg, ppi, (ox, oy) = load_ruler_background()
    bg = bg.copy()

    subj = _tight_rgba(subject_rgba)
    if subj is None:
        return bg.convert("RGB")

    target_h = int(round(target_h_in * ppi))
    scale = target_h / subj.height
    target_w = max(1, int(round(subj.width * scale)))
    subj = subj.resize((target_w, target_h), Image.LANCZOS)

    # Bottom-left anchored at the origin: left edge at ox, bottom edge at oy.
    left = int(round(ox))
    top = int(round(oy - subj.height))
    bg.alpha_composite(subj, dest=(max(0, left), max(0, top)))
    return bg.convert("RGB")


def make_production_visuals(original_path, svg_path, pes_path, out_dir,
                            target_h_mm=76.2):
    """Generate the three ruler JPEGs for one design into out_dir.

    Each subject is sized to target_h_mm (default 3 in). Individual subjects
    that cannot be built are skipped (logged) rather than aborting the rest.
    Returns a list of written file paths."""
    os.makedirs(out_dir, exist_ok=True)
    target_h_in = target_h_mm / MM_PER_INCH

    jobs = [
        ("1_original_on_ruler.jpg", subject_from_original, original_path),
        ("2_svg_on_ruler.jpg", subject_from_svg, svg_path),
        ("3_stitchplan_on_ruler.jpg", subject_from_pes, pes_path),
    ]
    written = []
    for fname, builder, src in jobs:
        try:
            if not src or not os.path.exists(src):
                print(f"  [visual skip] {fname}: source missing ({src})")
                continue
            subj = builder(src)
            if subj is None:
                print(f"  [visual skip] {fname}: could not build subject")
                continue
            rgb = compose_on_ruler(subj, target_h_in=target_h_in)
            out_path = os.path.join(out_dir, fname)
            rgb.save(out_path, "JPEG", quality=90)
            written.append(out_path)
        except Exception as e:  # never abort the other visuals / the stitch run
            print(f"  [visual error] {fname}: {e}")
    return written


if __name__ == "__main__":
    import sys
    # CLI: production_layout.py <original> <svg> <pes> <out_dir>
    if len(sys.argv) == 5:
        paths = make_production_visuals(sys.argv[1], sys.argv[2], sys.argv[3],
                                        sys.argv[4])
        print("wrote:", paths)
    else:
        print(__doc__)
