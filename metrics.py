"""Measurement module for the Bernina Stitch Master optimization loop.

Pure stdlib + pyembroidery. Two entry points:
  - svg_metrics(path) -> dict
  - pes_metrics(path) -> dict

Both functions are robust: they never raise on a bad file. On failure they
return a dict shaped like {"valid": False, "error": "<message>", ...}.
"""

import math
import os
import re
import xml.etree.ElementTree as ET

try:
    import pyembroidery
    _HAVE_PYEMB = True
except Exception:  # pragma: no cover - environment dependent
    pyembroidery = None
    _HAVE_PYEMB = False


# All SVG path command letters.
_PATH_CMD_LETTERS = set("MmLlHhVvCcSsQqTtAaZz")
_PATH_CMD_RE = re.compile(r"[MmLlHhVvCcSsQqTtAaZz]")


def _localname(tag):
    """Strip XML namespace, e.g. '{http://...}path' -> 'path'."""
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def svg_metrics(path):
    """Parse an SVG file with xml.etree and return structural metrics.

    Namespace-agnostic. Never raises.
    """
    result = {
        "artifact": os.path.basename(path),
        "kind": "svg",
        "valid": False,
    }
    try:
        result["bytes"] = os.path.getsize(path)
    except OSError as e:
        result["bytes"] = None
        result["error"] = str(e)
        return result

    try:
        tree = ET.parse(path)
        root = tree.getroot()
    except Exception as e:
        result["error"] = str(e)
        return result

    root_local = _localname(root.tag).lower()
    # "svg-ish" root: either literally <svg> or a root that contains svg content.
    valid = root_local == "svg"

    path_count = 0
    group_count = 0
    element_count = 0
    node_count = 0

    for el in root.iter():
        element_count += 1
        local = _localname(el.tag).lower()
        if local == "path":
            path_count += 1
            d = el.get("d")
            if d:
                node_count += len(_PATH_CMD_RE.findall(d))
        elif local == "g":
            group_count += 1

    # Include the root element in the total element count if iter() excluded it.
    # ET.Element.iter() DOES include the root, so element_count is already total.

    if not valid:
        # Still report what we counted, but flag invalid root.
        valid = path_count > 0  # tolerate svg fragments that still have paths

    result.update({
        "valid": bool(valid),
        "path_count": path_count,
        "node_count": node_count,
        "group_count": group_count,
        "element_count": element_count,
    })
    return result


def _command_of(stitch):
    """Return the masked command code of a [x, y, cmd] stitch entry."""
    cmd = stitch[2]
    if _HAVE_PYEMB:
        return cmd & pyembroidery.COMMAND_MASK
    return cmd


def _percentile(sorted_vals, pct):
    """Linear-interpolation percentile of an already-sorted list.

    pct in [0, 100]. Returns 0.0 for an empty list. Never raises.
    """
    n = len(sorted_vals)
    if n == 0:
        return 0.0
    if n == 1:
        return float(sorted_vals[0])
    rank = (pct / 100.0) * (n - 1)
    lo = int(math.floor(rank))
    hi = int(math.ceil(rank))
    if lo == hi:
        return float(sorted_vals[lo])
    frac = rank - lo
    return float(sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * frac)


def pes_metrics(path):
    """Read a PES file with pyembroidery and return embroidery metrics.

    PES coordinates are in 1/10 mm; lengths are divided by 10 to give mm.
    Never raises.
    """
    result = {
        "artifact": os.path.basename(path),
        "kind": "pes",
        "valid": False,
    }
    try:
        result["bytes"] = os.path.getsize(path)
    except OSError as e:
        result["bytes"] = None
        result["error"] = str(e)
        return result

    if not _HAVE_PYEMB:
        result["error"] = "pyembroidery not available"
        return result

    try:
        pattern = pyembroidery.read(path)
    except Exception as e:
        result["error"] = "read failed: %s" % e
        return result

    if pattern is None:
        result["error"] = "pyembroidery returned no pattern"
        return result

    try:
        stitches = pattern.stitches or []
        STITCH = pyembroidery.STITCH
        JUMP = pyembroidery.JUMP
        TRIM = pyembroidery.TRIM
        COLOR_CHANGE = pyembroidery.COLOR_CHANGE

        stitch_count = 0
        jump_count = 0
        trim_count = 0
        color_change_count = 0

        xs = []
        ys = []
        total_travel = 0.0
        prev = None
        prev_cmd = None
        # Real sewn-stitch segment lengths (mm). A segment counts only when both
        # its endpoints are STITCH commands, i.e. the machine actually sewed a
        # thread from the previous needle-down to this one. Segments that start
        # or end on a JUMP/TRIM/COLOR_CHANGE are travel/thread-cut moves, not
        # stitches, so they are excluded from the length distribution.
        stitch_lengths_mm = []

        for s in stitches:
            x, y = s[0], s[1]
            cmd = _command_of(s)
            if cmd == STITCH:
                stitch_count += 1
            elif cmd == JUMP:
                jump_count += 1
            elif cmd == TRIM:
                trim_count += 1
            elif cmd == COLOR_CHANGE:
                color_change_count += 1

            xs.append(x)
            ys.append(y)
            if prev is not None:
                dx = x - prev[0]
                dy = y - prev[1]
                seg = math.hypot(dx, dy)
                total_travel += seg
                if cmd == STITCH and prev_cmd == STITCH:
                    stitch_lengths_mm.append(seg / 10.0)
            prev = (x, y)
            prev_cmd = cmd

        # Color count: prefer threadlist, fall back to color changes + 1.
        try:
            color_count = len(pattern.threadlist)
        except Exception:
            color_count = 0
        if color_count == 0:
            color_count = color_change_count + 1 if stitches else 0

        if xs and ys:
            width_mm = (max(xs) - min(xs)) / 10.0
            height_mm = (max(ys) - min(ys)) / 10.0
        else:
            width_mm = 0.0
            height_mm = 0.0

        total_travel_mm = total_travel / 10.0
        avg_stitch_length_mm = (total_travel_mm / stitch_count) if stitch_count else 0.0

        area_cm2 = (width_mm / 10.0) * (height_mm / 10.0)
        # INFORMATIONAL ONLY as of iteration 2: bbox stitch density is a poor
        # proxy for embroiderability on small, densely-filled designs. It is
        # still reported for reference but no longer feeds embroidery_suitability.
        stitch_density_per_cm2 = (stitch_count / area_cm2) if area_cm2 > 0 else 0.0

        # Stitch-length distribution stats (mm) over real sewn segments only.
        # These drive the iteration-2 embroidery_suitability score: they capture
        # thread-nesting risk (very short stitches), snag/loose-stitch risk (very
        # long stitches), and the comfortable machine-embroidery range.
        n_seg = len(stitch_lengths_mm)
        if n_seg > 0:
            sorted_lengths = sorted(stitch_lengths_mm)
            stitch_len_p50_mm = _percentile(sorted_lengths, 50)
            stitch_len_p95_mm = _percentile(sorted_lengths, 95)
            short_stitch_frac = sum(1 for L in sorted_lengths if L < 0.5) / n_seg
            long_stitch_frac = sum(1 for L in sorted_lengths if L > 7.0) / n_seg
            safe_len_frac = sum(1 for L in sorted_lengths if 0.5 <= L <= 4.0) / n_seg
        else:
            stitch_len_p50_mm = 0.0
            stitch_len_p95_mm = 0.0
            short_stitch_frac = 0.0
            long_stitch_frac = 0.0
            safe_len_frac = 0.0

        trims_per_1000 = (trim_count / stitch_count * 1000.0) if stitch_count else 0.0

        result.update({
            "valid": True,
            "stitch_count": stitch_count,
            "jump_count": jump_count,
            "trim_count": trim_count,
            "color_change_count": color_change_count,
            "color_count": color_count,
            "width_mm": round(width_mm, 3),
            "height_mm": round(height_mm, 3),
            "total_travel_mm": round(total_travel_mm, 3),
            "avg_stitch_length_mm": round(avg_stitch_length_mm, 4),
            "stitch_density_per_cm2": round(stitch_density_per_cm2, 3),
            "stitch_segment_count": n_seg,
            "stitch_len_p50_mm": round(stitch_len_p50_mm, 4),
            "stitch_len_p95_mm": round(stitch_len_p95_mm, 4),
            "short_stitch_frac": round(short_stitch_frac, 4),
            "long_stitch_frac": round(long_stitch_frac, 4),
            "safe_len_frac": round(safe_len_frac, 4),
            "trims_per_1000": round(trims_per_1000, 4),
        })
        return result
    except Exception as e:  # defensive: never throw
        result["error"] = "metric computation failed: %s" % e
        return result


# --- Visual fidelity rendering + comparison (iteration 4) -------------------
# These functions render a vector DESIGN (SVG) and its actual EMBROIDERY
# STITCH-OUT (PES) to a common grayscale raster on the SAME framing convention
# (design bounding box fit into a size*size white canvas, aspect preserved,
# centered) so the two rasters are registration-comparable, then score real
# visual fidelity between them. This is NOT circular: it compares the vector we
# intend to sew against a simulation of what the machine actually sews, which is
# the meaningful fidelity question for an image->vector->embroidery pipeline.
#
# Heavy deps (numpy / Pillow / scikit-image / cairosvg / playwright) are imported
# lazily inside these functions so importing metrics.py stays stdlib-light and
# the deterministic svg_metrics/pes_metrics timing path is unaffected. Every
# function is robust: returns None on any failure.


def _fit_gray_to_canvas(gray_img, size):
    """Fit a grayscale PIL image (content on white) into a size*size white
    canvas, preserving aspect ratio and centering. Returns a uint8 numpy array.

    This is the SHARED framing convention for both the SVG and PES renderers so
    the two rasters land in the same place and are registration-comparable.
    """
    from PIL import Image
    import numpy as np
    g = gray_img.copy()
    # thumbnail() fits within (size, size) preserving aspect ratio in place.
    g.thumbnail((size, size), Image.LANCZOS)
    canvas = Image.new("L", (size, size), 255)
    off = ((size - g.width) // 2, (size - g.height) // 2)
    canvas.paste(g, off)
    return np.asarray(canvas, dtype=np.uint8)


def _render_svg_playwright(svg_path, size):
    """Fallback SVG rasterizer via Playwright/Chromium. Returns a PIL RGBA
    image or None. Only used when cairosvg is unavailable."""
    try:
        import io
        from PIL import Image
        from playwright.sync_api import sync_playwright
        with open(svg_path, "rb") as f:
            svg_data = f.read()
        exe = os.environ.get("CHROMIUM_PATH", "/opt/pw-browsers/chromium")
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=exe)
            page = browser.new_page(viewport={"width": size, "height": size})
            page.set_content(
                '<html><body style="margin:0;background:#fff">'
                '<img src="data:image/svg+xml;base64,%s" '
                'style="width:%dpx"></body></html>' % (
                    __import__("base64").b64encode(svg_data).decode(), size))
            page.wait_for_timeout(200)
            png = page.screenshot(type="png")
            browser.close()
        return Image.open(io.BytesIO(png))
    except Exception:
        return None


def render_svg_to_gray(svg_path, size=512):
    """Rasterize an SVG to a size*size grayscale numpy array (white canvas,
    aspect preserved, centered). Prefers cairosvg; falls back to
    Playwright/Chromium. Returns None on failure."""
    try:
        import io
        from PIL import Image
    except Exception:
        return None

    img = None
    try:
        import cairosvg
        png_bytes = cairosvg.svg2png(url=svg_path, output_width=size)
        img = Image.open(io.BytesIO(png_bytes))
    except Exception:
        img = None

    if img is None:
        img = _render_svg_playwright(svg_path, size)
    if img is None:
        return None

    try:
        # Composite over an opaque white background so transparency reads as
        # white (matching the PES canvas), then convert to grayscale.
        img = img.convert("RGBA")
        bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
        bg.alpha_composite(img)
        gray = bg.convert("L")
        return _fit_gray_to_canvas(gray, size)
    except Exception:
        return None


def render_pes_to_gray(pes_path, size=512):
    """Rasterize a PES stitch-out to a size*size grayscale numpy array.

    Reads the stitch list with pyembroidery and draws the SEWN paths as 1px dark
    lines on white with PIL.ImageDraw: a line is drawn only for a consecutive
    STITCH->STITCH segment (both endpoints needle-down). JUMP / TRIM /
    COLOR_CHANGE moves are NOT drawn, so travel/thread-cut connectors don't
    appear. Coordinates are normalized to the design bounding box and fit into
    the size*size canvas with the SAME framing convention as render_svg_to_gray
    (aspect preserved, centered). Y is NOT flipped: these PES files store
    coordinates in image (Y-down) orientation already, empirically calibrated on
    the asymmetric coastal layout (no-flip registers edge_overlap 0.41 / ssim
    0.91 vs flipped 0.13 / 0.85 against its SVG), so the raw Y matches the
    rendered SVG. Returns None on failure.
    """
    try:
        from PIL import Image, ImageDraw
        import numpy as np
    except Exception:
        return None
    if not _HAVE_PYEMB:
        return None
    try:
        pattern = pyembroidery.read(pes_path)
    except Exception:
        return None
    if pattern is None:
        return None

    try:
        stitches = pattern.stitches or []
        if not stitches:
            return None
        STITCH = pyembroidery.STITCH

        xs = [s[0] for s in stitches]
        ys = [s[1] for s in stitches]
        minx, maxx = min(xs), max(xs)
        miny, maxy = min(ys), max(ys)
        w = maxx - minx
        h = maxy - miny
        span = max(w, h)
        if span <= 0:
            return None

        # Scale the larger bbox dimension to fill the canvas (matches the SVG
        # thumbnail, which fills its larger dimension to `size`). Center both.
        scale = (size - 1) / span
        draw_w = w * scale
        draw_h = h * scale
        off_x = (size - draw_w) / 2.0
        off_y = (size - draw_h) / 2.0

        def tx(x, y):
            px = off_x + (x - minx) * scale
            # No Y flip: these PES coordinates are already Y-down (image
            # orientation), verified by registration against the SVG designs.
            py = off_y + (y - miny) * scale
            return (px, py)

        canvas = Image.new("L", (size, size), 255)
        draw = ImageDraw.Draw(canvas)
        prev = None
        prev_cmd = None
        for s in stitches:
            cmd = _command_of(s)
            pt = tx(s[0], s[1])
            if prev is not None and cmd == STITCH and prev_cmd == STITCH:
                draw.line([prev, pt], fill=0, width=1)
            prev = pt
            prev_cmd = cmd
        return np.asarray(canvas, dtype=np.uint8)
    except Exception:
        return None


def _edge_map(arr_float01):
    """Binary edge map via Sobel magnitude thresholded at mean+std.

    Returns an all-False map for a flat (all-zero-gradient) image so the IoU is
    well defined. Input is a float array in [0, 1]."""
    import numpy as np
    from skimage.filters import sobel
    e = sobel(arr_float01)
    emax = float(e.max())
    if emax <= 0.0:
        return np.zeros(e.shape, dtype=bool)
    thr = float(e.mean() + e.std())
    if thr <= 0.0:
        thr = 0.1 * emax
    return e > thr


def visual_compare(gray_a, gray_b):
    """Compare two grayscale rasters and return real fidelity metrics.

    Returns a dict with:
      - ssim:         skimage structural_similarity (data_range=255), in [-1,1]
      - rmse_norm:    root-mean-square error / 255, in [0,1]
      - edge_overlap: IoU of binary Sobel edge maps, in [0,1]
    Images are resized to a common shape if needed. Returns None if either input
    is None/empty. Identity input yields ssim=1.0, rmse_norm=0.0,
    edge_overlap=1.0.
    """
    try:
        import numpy as np
        from skimage.metrics import structural_similarity as ssim_fn
    except Exception:
        return None
    if gray_a is None or gray_b is None:
        return None
    a = np.asarray(gray_a)
    b = np.asarray(gray_b)
    if a.size == 0 or b.size == 0:
        return None

    if a.shape != b.shape:
        try:
            from PIL import Image
            b_img = Image.fromarray(b.astype(np.uint8)).resize(
                (a.shape[1], a.shape[0]), Image.LANCZOS)
            b = np.asarray(b_img)
        except Exception:
            return None

    af = a.astype(np.float64)
    bf = b.astype(np.float64)

    try:
        ssim_val = float(ssim_fn(af, bf, data_range=255.0))
    except Exception:
        ssim_val = 0.0

    rmse = float(np.sqrt(np.mean((af - bf) ** 2)))
    rmse_norm = rmse / 255.0

    ea = _edge_map(af / 255.0)
    eb = _edge_map(bf / 255.0)
    inter = int(np.logical_and(ea, eb).sum())
    union = int(np.logical_or(ea, eb).sum())
    edge_overlap = float(inter / union) if union > 0 else 0.0

    return {
        "ssim": round(ssim_val, 6),
        "rmse_norm": round(rmse_norm, 6),
        "edge_overlap": round(edge_overlap, 6),
    }


if __name__ == "__main__":
    import json
    import sys
    for p in sys.argv[1:]:
        if p.lower().endswith(".svg"):
            print(json.dumps(svg_metrics(p), indent=2))
        elif p.lower().endswith(".pes"):
            print(json.dumps(pes_metrics(p), indent=2))
        else:
            print("skip (unknown type):", p)
