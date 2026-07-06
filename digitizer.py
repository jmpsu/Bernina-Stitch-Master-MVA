#!/usr/bin/env python3
"""
image -> Bernina B700 embroidery digitizer.

Pipeline (see functions below):
  1. remove_background(img_path)      -> (rgb, fg_mask, method)
  2. segment_objects(fg_mask, ...)    -> [(obj_mask, bbox), ...]
  3. digitize_object(rgb, obj_mask)   -> pyembroidery.EmbPattern (+ stats)
  4. write_outputs(...)               -> .exp (Bernina), .pes, preview.png, .json

All objects are scaled so the OBJECT is target_h_mm = 76.2 mm (3 in) tall.
pyembroidery units are 0.1 mm, so 76.2 mm == 762 units.

Background removal tries `rembg` first; if the model cannot be fetched
(egress blocked) it falls back to a robust, no-network corner-sampling +
Otsu-on-color-distance method that handles both light-on-dark and
dark-on-light source images.

CLI: `python3 digitizer.py` digitizes all 5 hard-coded source images.
"""

import os
import sys
import json
import math
import warnings

warnings.filterwarnings("ignore")  # silence skimage deprecation chatter

import numpy as np
from PIL import Image, ImageDraw

from skimage import measure, morphology, filters
from scipy import ndimage as ndi

import pyembroidery as pe

# ----------------------------------------------------------------------------
# Parameters (kept in sync with parameter_correlation_index.json)
# ----------------------------------------------------------------------------
TARGET_H_MM = 76.2          # 3 inches
ROW_SPACING_MM = 0.4        # scanline fill row spacing
MAX_STITCH_MM = 3.0         # max fill stitch length
RUNNING_STITCH_MM = 2.0     # running-stitch spacing along contours
MIN_STITCH_MM = 0.5         # minimum stitch length (short stitches dropped)
UNITS_PER_MM = 10.0         # pyembroidery: 1 unit = 0.1 mm
TRIM_JUMP_MM = 8.0          # insert a TRIM before jumps longer than this
MAX_STITCHES_WARN = 60000

SPECK_FRAC = 0.002          # drop components smaller than 0.2% of image area
AGGLO_GAP_FRAC = 0.08       # merge components whose bbox gap < this * img_width

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stitch_plans")
REF_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reference_images")
VEC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vectorized_svg")
PROD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "production_runs")


# ----------------------------------------------------------------------------
# 1. Background removal
# ----------------------------------------------------------------------------
_REMBG_OK = None  # tri-state cache: None=untried, False=unavailable


def _rembg_remove(rgb):
    """Try rembg. Returns fg_mask (bool) or None if unavailable/blocked.

    The model download is attempted only once per process; if it is blocked
    (egress policy) the failure is cached so later images fall back silently."""
    global _REMBG_OK
    if _REMBG_OK is False:
        return None
    try:
        from rembg import remove
        out = remove(Image.fromarray(rgb))
        arr = np.array(out.convert("RGBA"))
        _REMBG_OK = True
        return arr[..., 3] > 20
    except Exception:
        # Model download blocked / backend missing / any runtime error.
        _REMBG_OK = False
        return None


def _saturation(rgb):
    a = rgb.astype(np.float64)
    mx = a.max(axis=2)
    mn = a.min(axis=2)
    return np.where(mx > 0, (mx - mn) / np.maximum(mx, 1), 0.0)


def _fallback_mask(rgb):
    """No-network foreground estimation.

    Sample the 4 corner regions to estimate the background colour and whether
    it is light or dark. Then split on brightness in the appropriate direction
    (Otsu), and for light (paper) backgrounds also fold in a saturation term so
    coloured-pencil fills are captured. A colour-distance term is included only
    as a mild booster (it is unreliable on gradient/vignetted backgrounds, so it
    is not the primary signal). Finally clean up morphologically and fill small
    holes. Handles both light-on-dark (navy line-art) and dark-on-light (paper).
    """
    h, w = rgb.shape[:2]
    ch, cw = max(1, h // 12), max(1, w // 12)
    corners = np.concatenate([
        rgb[:ch, :cw].reshape(-1, 3),
        rgb[:ch, -cw:].reshape(-1, 3),
        rgb[-ch:, :cw].reshape(-1, 3),
        rgb[-ch:, -cw:].reshape(-1, 3),
    ], axis=0).astype(np.float64)
    bg = np.median(corners, axis=0)
    bg_is_light = bg.mean() > 110

    gray = rgb.astype(np.float64).mean(axis=2)
    try:
        b_thr = filters.threshold_otsu(gray)
    except Exception:
        b_thr = gray.mean()

    if bg_is_light:
        # dark strokes on light paper + saturated coloured fills + pencil edges
        fg = gray < (b_thr - 3)
        sat = _saturation(rgb)
        try:
            s_thr = filters.threshold_otsu(sat)
        except Exception:
            s_thr = sat.mean() + sat.std()
        s_thr = max(s_thr, 0.12)
        fg |= sat > s_thr
        # Gradient magnitude catches faint pencil OUTLINES of pale objects
        # (oyster shell, cocktail glass) that brightness/saturation miss.
        edge = filters.sobel(gray / 255.0)
        fg |= edge > 0.06
    else:
        # bright strokes on dark background (brightness only: robust to the
        # background luminance gradient that breaks colour-distance methods)
        fg = gray > (b_thr + 3)

    # Morphology: close small gaps, remove specks, fill small holes.
    fg = morphology.closing(fg, morphology.disk(2))
    fg = morphology.opening(fg, morphology.disk(2))
    min_obj = int(SPECK_FRAC * h * w * 0.25)
    fg = morphology.remove_small_objects(fg, min_size=max(32, min_obj))
    # Fill only SMALL holes so line-art interiors are not flooded solid.
    hole_area = int(0.01 * h * w)
    fg = morphology.remove_small_holes(fg, area_threshold=max(64, hole_area))
    return fg


def remove_background(img_path):
    """Return (rgb_uint8, fg_mask_bool, method_str)."""
    rgb = np.array(Image.open(img_path).convert("RGB"))
    mask = _rembg_remove(rgb)
    if mask is not None and mask.mean() > 0.005:
        method = "rembg"
    else:
        mask = _fallback_mask(rgb)
        method = "fallback(corner+otsu)"
    return rgb, mask, method


# ----------------------------------------------------------------------------
# 2. Object separation
# ----------------------------------------------------------------------------
def _bbox_gap(a, b):
    """Minimum gap (px) between two bboxes (min_r, min_c, max_r, max_c).
    0 if they overlap/touch."""
    ar0, ac0, ar1, ac1 = a
    br0, bc0, br1, bc1 = b
    dx = max(0, max(bc0 - ac1, ac0 - bc1))
    dy = max(0, max(br0 - ar1, ar0 - br1))
    if dx == 0 and dy == 0:
        return 0.0
    return math.hypot(dx, dy)


def _tight_bbox(mask):
    rows = np.any(mask, axis=1)
    cols = np.any(mask, axis=0)
    r0, r1 = np.where(rows)[0][[0, -1]]
    c0, c1 = np.where(cols)[0][[0, -1]]
    return (int(r0), int(c0), int(r1) + 1, int(c1) + 1)


def _clean_components(fg_mask):
    """Drop specks, return labelled image + kept regionprops."""
    h, w = fg_mask.shape
    lbl = measure.label(fg_mask, connectivity=2)
    regions = measure.regionprops(lbl)
    min_area = SPECK_FRAC * h * w
    comps = [r for r in regions if r.area >= min_area]
    return lbl, comps


def _segment_strip(fg_mask):
    """Split a horizontal strip into objects by vertical-whitespace valleys in
    the column-density profile. Robust to thin between-object noise."""
    h, w = fg_mask.shape
    col = fg_mask.sum(axis=0).astype(np.float64)
    # Smooth the profile so pencil texture does not create spurious valleys.
    k = max(3, int(0.01 * w) | 1)
    kernel = np.ones(k) / k
    col_s = np.convolve(col, kernel, mode="same")
    thresh = max(2.0, 0.04 * col_s.max())
    active = col_s > thresh

    # Find contiguous active bands.
    bands = []
    start = None
    for x in range(w):
        if active[x] and start is None:
            start = x
        elif not active[x] and start is not None:
            bands.append((start, x))
            start = None
    if start is not None:
        bands.append((start, w))

    # Merge bands separated by a gap narrower than 4% of width.
    min_gap = 0.04 * w
    merged = []
    for b in bands:
        if merged and b[0] - merged[-1][1] < min_gap:
            merged[-1] = (merged[-1][0], b[1])
        else:
            merged.append(list(b))
    # Drop bands narrower than 3% of width (noise).
    merged = [b for b in merged if (b[1] - b[0]) >= 0.03 * w]

    objects = []
    for (c0, c1) in merged:
        band = np.zeros_like(fg_mask)
        band[:, c0:c1] = fg_mask[:, c0:c1]
        # keep only real components inside the band
        lbl, comps = _clean_components(band)
        if not comps:
            continue
        om = np.zeros_like(fg_mask)
        for r in comps:
            om |= (lbl == r.label)
        if om.sum() < SPECK_FRAC * h * w:
            continue
        objects.append((om, _tight_bbox(om)))
    return objects


def segment_objects(fg_mask):
    """Layout-aware object separation.

    Wide images (aspect > 1.8) are horizontal strips: split by vertical
    whitespace valleys into separate objects. Otherwise the image holds a
    single design: union all non-speck components into one object (so a
    disconnected logo / a two-piece bikini stays ONE object).

    Returns list of (obj_mask_bool, bbox=(min_r,min_c,max_r,max_c)),
    ordered left-to-right."""
    h, w = fg_mask.shape
    if w / h > 1.8:
        objects = _segment_strip(fg_mask)
    else:
        lbl, comps = _clean_components(fg_mask)
        if not comps:
            return []
        om = np.zeros_like(fg_mask)
        for r in comps:
            om |= (lbl == r.label)
        objects = [(om, _tight_bbox(om))]

    objects.sort(key=lambda o: (o[1][1], o[1][0]))
    return objects


# ----------------------------------------------------------------------------
# 3. Digitize one object
# ----------------------------------------------------------------------------
def _kmeans(pixels, k, iters=12, seed=0):
    """Tiny numpy k-means over RGB pixels. Returns (labels, centers)."""
    rng = np.random.default_rng(seed)
    if len(pixels) <= k:
        centers = pixels.astype(np.float64).copy()
        return np.arange(len(pixels)), centers
    idx = rng.choice(len(pixels), k, replace=False)
    centers = pixels[idx].astype(np.float64)
    labels = np.zeros(len(pixels), dtype=int)
    for _ in range(iters):
        d = np.linalg.norm(pixels[:, None, :] - centers[None, :, :], axis=2)
        new = d.argmin(axis=1)
        if np.array_equal(new, labels):
            break
        labels = new
        for c in range(k):
            m = labels == c
            if m.any():
                centers[c] = pixels[m].mean(axis=0)
    return labels, centers


def _choose_k(rgb, obj_mask, bbox):
    """Adaptive colour count and a line-art flag from fill density."""
    r0, c0, r1, c1 = bbox
    sub = obj_mask[r0:r1, c0:c1]
    fill_ratio = sub.mean()
    line_art = fill_ratio < 0.14
    if line_art:
        return 1, True
    # Colour art: gauge colour spread to pick K in [2, 6].
    fg = rgb[r0:r1, c0:c1][sub]
    if len(fg) < 50:
        return 2, False
    samp = fg[np.random.default_rng(0).choice(len(fg), min(4000, len(fg)), replace=False)]
    spread = samp.astype(np.float64).std(axis=0).mean()
    if spread < 22:
        k = 2
    elif spread < 40:
        k = 3
    elif spread < 60:
        k = 4
    else:
        k = 6
    return k, False


def _resample_polyline(pts, spacing):
    """Resample an (N,2) polyline to points ~spacing apart (keeps endpoints)."""
    if len(pts) < 2:
        return pts
    out = [pts[0]]
    acc = 0.0
    for i in range(1, len(pts)):
        seg = pts[i] - pts[i - 1]
        seglen = math.hypot(seg[0], seg[1])
        if seglen == 0:
            continue
        while acc + seglen >= spacing:
            t = (spacing - acc) / seglen
            newp = pts[i - 1] + seg * t
            out.append(newp)
            pts_prev = newp
            seg = pts[i] - newp
            seglen = math.hypot(seg[0], seg[1])
            pts[i - 1] = newp
            acc = 0.0
        acc += seglen
    if not np.allclose(out[-1], pts[-1]):
        out.append(pts[-1])
    return np.array(out)


def _contour_runs(region_mask, spacing_px):
    """Running-stitch polylines along region contours (in (x,y) px)."""
    runs = []
    for contour in measure.find_contours(region_mask.astype(float), 0.5):
        # contour is (row, col) == (y, x)
        pts = np.column_stack([contour[:, 1], contour[:, 0]]).astype(np.float64)
        if len(pts) < 3:
            continue
        rs = _resample_polyline(pts.copy(), spacing_px)
        if len(rs) >= 2:
            runs.append(rs)
    return runs


def _fill_runs(region_mask, row_spacing_px, max_stitch_px):
    """Boustrophedon scanline fill. Returns list of (x,y) polylines (px)."""
    h, w = region_mask.shape
    runs = []
    step = max(1, int(round(row_spacing_px)))
    flip = False
    for y in range(0, h, step):
        row = region_mask[y]
        if not row.any():
            continue
        # find contiguous runs of True in this row
        xs = np.where(row)[0]
        splits = np.where(np.diff(xs) > 1)[0]
        segments = np.split(xs, splits + 1)
        seg_ranges = [(s[0], s[-1]) for s in segments if len(s) > 0]
        if flip:
            seg_ranges = seg_ranges[::-1]
        for (x0, x1) in seg_ranges:
            if flip:
                x0, x1 = x1, x0
            length = abs(x1 - x0)
            n = max(1, int(math.ceil(length / max_stitch_px)))
            xs_line = np.linspace(x0, x1, n + 1)
            poly = np.column_stack([xs_line, np.full(n + 1, y)]).astype(np.float64)
            runs.append(poly)
        flip = not flip
    return runs


def digitize_object(rgb, obj_mask, bbox, target_h_mm=TARGET_H_MM, name="object"):
    """Build an EmbPattern for one object. Returns (pattern, stats_dict)."""
    r0, c0, r1, c1 = bbox
    bbox_h_px = r1 - r0
    bbox_w_px = c1 - c0
    if bbox_h_px < 3 or bbox_w_px < 3 or obj_mask[r0:r1, c0:c1].sum() < 20:
        return None, None

    units_per_px = (target_h_mm * UNITS_PER_MM) / bbox_h_px
    mm_per_px = target_h_mm / bbox_h_px
    row_spacing_px = max(1.0, ROW_SPACING_MM / mm_per_px)
    max_stitch_px = max(1.0, MAX_STITCH_MM / mm_per_px)
    running_px = max(1.0, RUNNING_STITCH_MM / mm_per_px)
    min_stitch_units = MIN_STITCH_MM * UNITS_PER_MM

    crop_rgb = rgb[r0:r1, c0:c1]
    crop_mask = obj_mask[r0:r1, c0:c1]

    k, line_art = _choose_k(rgb, obj_mask, bbox)

    fg_pixels = crop_rgb[crop_mask]
    fg_coords = np.argwhere(crop_mask)  # (row, col)
    labels, centers = _kmeans(fg_pixels, k)

    # Build per-colour region masks.
    regions = []  # (mean_rgb, region_mask, is_line, area)
    for c in range(len(centers)):
        sel = labels == c
        frac = sel.mean() if len(labels) else 0
        if frac < 0.01:
            continue
        rmask = np.zeros(crop_mask.shape, dtype=bool)
        coords = fg_coords[sel]
        rmask[coords[:, 0], coords[:, 1]] = True
        # clean
        rmask = morphology.binary_closing(rmask, morphology.disk(1))
        rmask = morphology.remove_small_objects(rmask, min_size=16)
        rmask = morphology.remove_small_holes(rmask, area_threshold=max(32, int(0.002 * rmask.size)))
        area = int(rmask.sum())
        if area < 20:
            continue
        # thin/line-like test: perimeter^2 / area high -> thin
        perim = measure.perimeter(rmask) if area > 0 else 0
        thinness = (perim * perim) / (4 * math.pi * area) if area else 0
        is_line = line_art or thinness > 12 or area < (0.02 * crop_mask.size)
        regions.append((centers[c].astype(int), rmask, is_line, area))

    if not regions:
        return None, None

    # Process larger / solid regions first, thin outlines last for crisp edges.
    regions.sort(key=lambda r: (r[2], -r[3]))

    def to_units(x_px, y_px):
        xu = int(round(x_px * units_per_px))
        yu = int(round((bbox_h_px - y_px) * units_per_px))  # flip y (embroidery up)
        return xu, yu

    pattern = pe.EmbPattern()
    thread_rgbs = []
    last_xy = None
    first = True

    for (mean_rgb, rmask, is_line, area) in regions:
        # Thread for this colour block.
        th = pe.EmbThread()
        r, g, b = [int(v) for v in mean_rgb]
        th.set_color(r, g, b)
        pattern.add_thread(th)
        thread_rgbs.append([r, g, b])

        if not first:
            pattern.color_change()
        first = False

        runs = []
        if is_line:
            runs = _contour_runs(rmask, running_px)
        else:
            runs = _fill_runs(rmask, row_spacing_px, max_stitch_px)
            # crisp outline around the filled region
            runs += _contour_runs(rmask, running_px)

        for poly in runs:
            if len(poly) < 2:
                continue
            sx, sy = to_units(poly[0][0], poly[0][1])
            # decide jump vs continue
            if last_xy is not None:
                jd = math.hypot(sx - last_xy[0], sy - last_xy[1])
                if jd > MAX_STITCH_MM * UNITS_PER_MM:
                    if jd > TRIM_JUMP_MM * UNITS_PER_MM:
                        pattern.add_command(pe.TRIM)
                    pattern.add_stitch_absolute(pe.JUMP, sx, sy)
            else:
                pattern.add_stitch_absolute(pe.JUMP, sx, sy)
            prev = (sx, sy)
            pattern.add_stitch_absolute(pe.STITCH, sx, sy)
            for p in poly[1:]:
                xu, yu = to_units(p[0], p[1])
                if math.hypot(xu - prev[0], yu - prev[1]) < min_stitch_units:
                    continue
                pattern.add_stitch_absolute(pe.STITCH, xu, yu)
                prev = (xu, yu)
            last_xy = prev

    pattern.end()

    stats = _pattern_stats(pattern)
    stats.update({
        "name": name,
        "color_count": len(thread_rgbs),
        "thread_rgb": thread_rgbs,
        "line_art": bool(line_art),
        "regions": len(regions),
    })
    # Verify physical size.
    minx, miny, maxx, maxy = pattern.bounds()
    stats["width_mm"] = round((maxx - minx) / UNITS_PER_MM, 2)
    stats["height_mm"] = round((maxy - miny) / UNITS_PER_MM, 2)
    return pattern, stats


def _pattern_stats(pattern):
    stitch = jump = trim = color = 0
    for s in pattern.stitches:
        cmd = s[2] & pe.COMMAND_MASK
        if cmd == pe.STITCH:
            stitch += 1
        elif cmd == pe.JUMP:
            jump += 1
        elif cmd == pe.TRIM:
            trim += 1
        elif cmd in (pe.COLOR_CHANGE, pe.COLOR_BREAK):
            color += 1
    return {"stitch_count": stitch, "jump_count": jump,
            "trim_count": trim, "color_change_count": color}


# ----------------------------------------------------------------------------
# 4. Outputs
# ----------------------------------------------------------------------------
def render_preview(pattern, thread_rgbs, path, px_per_mm=4.0, pad=20):
    """Render the actual stitch path to a colour PNG with PIL."""
    minx, miny, maxx, maxy = pattern.bounds()
    scale = px_per_mm / UNITS_PER_MM
    W = int((maxx - minx) * scale) + 2 * pad
    H = int((maxy - miny) * scale) + 2 * pad
    W = max(W, 32); H = max(H, 32)
    img = Image.new("RGB", (W, H), (250, 250, 250))
    dr = ImageDraw.Draw(img)

    def tp(x, y):
        px = (x - minx) * scale + pad
        py = (maxy - y) * scale + pad  # flip back for display (image y down)
        return (px, py)

    ci = 0
    color = thread_rgbs[0] if thread_rgbs else [0, 0, 0]
    prev = None
    pen_down = False
    for s in pattern.stitches:
        x, y, cmd = s[0], s[1], s[2] & pe.COMMAND_MASK
        if cmd in (pe.COLOR_CHANGE, pe.COLOR_BREAK):
            ci = min(ci + 1, len(thread_rgbs) - 1)
            color = thread_rgbs[ci]
            prev = None
            pen_down = False
            continue
        if cmd == pe.STITCH:
            p = tp(x, y)
            if pen_down and prev is not None:
                dr.line([prev, p], fill=tuple(color), width=1)
            prev = p
            pen_down = True
        else:  # JUMP / TRIM / END etc.
            prev = tp(x, y)
            pen_down = False
    img.save(path)


def write_outputs(pattern, stats, stem, obj_label, method):
    os.makedirs(OUT_DIR, exist_ok=True)
    base = os.path.join(OUT_DIR, f"{stem}_{obj_label}")
    exp_path = base + ".exp"
    pes_path = base + ".pes"
    png_path = base + "_preview.png"
    json_path = base + ".json"

    pe.write_exp(pattern, exp_path)
    pe.write_pes(pattern, pes_path)
    render_preview(pattern, stats["thread_rgb"], png_path)

    sidecar = {
        "object": obj_label,
        "name": stats.get("name"),
        "width_mm": stats["width_mm"],
        "height_mm": stats["height_mm"],
        "height_target_mm": TARGET_H_MM,
        "height_ok": abs(stats["height_mm"] - TARGET_H_MM) <= 1.0,
        "stitch_count": stats["stitch_count"],
        "jump_count": stats["jump_count"],
        "trim_count": stats["trim_count"],
        "color_count": stats["color_count"],
        "thread_rgb": stats["thread_rgb"],
        "line_art": stats["line_art"],
        "bg_removal_method": method,
        "files": {"exp": os.path.basename(exp_path),
                  "pes": os.path.basename(pes_path),
                  "preview": os.path.basename(png_path)},
    }
    with open(json_path, "w") as f:
        json.dump(sidecar, f, indent=2)
    return exp_path, pes_path, png_path, json_path


def generate_production_visuals(original_path, pes_path, stem, label, n_objects):
    """Render the 3 ruler-review JPEGs for a just-written stitch plan into
    production_runs/<stem>/ (original bg-removed / SVG / stitch-out, all at true
    3 in). The matching SVG is looked up in vectorized_svg/<original-stem>.svg.

    Fully guarded: a failure here logs and returns without disturbing the
    stitch-generation pipeline."""
    try:
        import production_layout  # lazy: avoids import cost / circular import
        base = os.path.splitext(os.path.basename(original_path))[0]
        svg_path = os.path.join(VEC_DIR, base + ".svg")
        folder = stem if n_objects == 1 else f"{stem}_{label}"
        out_dir = os.path.join(PROD_DIR, folder)
        written = production_layout.make_production_visuals(
            original_path, svg_path, pes_path, out_dir)
        print(f"  [visuals] {folder}: {len(written)} JPEG(s)")
    except Exception as e:
        print(f"  [visuals error] {stem}/{label}: {e}")


# ----------------------------------------------------------------------------
# CLI orchestration
# ----------------------------------------------------------------------------
IMAGES = [
    # (path, stem, [object names left->right] or None for auto-index)
    ("/root/.claude/uploads/0f26c418-97eb-5ee4-97aa-b775bedafccc/55c10055-IMG_0745.jpeg",
     "skull_moon_rose", ["design"]),
    ("/root/.claude/uploads/0f26c418-97eb-5ee4-97aa-b775bedafccc/65892eaa-IMG_1126.jpeg",
     "cape_may_crest", ["crest"]),
    ("/root/.claude/uploads/0f26c418-97eb-5ee4-97aa-b775bedafccc/82187835-IMG_0066.png",
     "bikini", ["bikini"]),
    ("/root/.claude/uploads/0f26c418-97eb-5ee4-97aa-b775bedafccc/b2c5a4cd-IMG_0063.png",
     "seafood_strip", ["basket", "lobster", "shell", "cocktail"]),
    ("/root/.claude/uploads/0f26c418-97eb-5ee4-97aa-b775bedafccc/2dd22ec8-house_board_crab_light_drawing.jpeg",
     "beach_strip", ["cabana", "surfboard", "crab", "lighthouse"]),
]


def copy_reference(img_path, stem):
    os.makedirs(REF_DIR, exist_ok=True)
    ext = os.path.splitext(img_path)[1]
    dst = os.path.join(REF_DIR, f"{stem}{ext}")
    try:
        Image.open(img_path).convert("RGB").save(dst)
    except Exception:
        pass


def _stem_from_path(path):
    """Readable stem from an uploaded filename.
    '340931ae-IMG_0331.jpeg' -> 'img_0331'."""
    base = os.path.basename(path)
    if "-" in base:
        base = base.split("-", 1)[1]
    stem = os.path.splitext(base)[0]
    return stem.lower().replace(" ", "_").replace("-", "_")


def _outputs_exist(stem):
    import glob
    return bool(glob.glob(os.path.join(OUT_DIR, f"{stem}_*.json")))


def process_images(paths, target_h_mm=TARGET_H_MM):
    """Digitize an arbitrary list of image paths.

    Reuses the full pipeline: fallback bg-removal (with Sobel edge term),
    layout-aware segmentation (aspect>1.8 strip splitter), and
    digitize_object at target_h_mm. Single-design images -> one 'logo'
    object (component union already handles disconnected logos + year text).
    IDEMPOTENT: skips any image whose <stem>_*.json outputs already exist.
    Returns list of (stem, label, stats)."""
    rows = []
    for path in paths:
        if not os.path.exists(path):
            print(f"MISSING: {path}")
            continue
        stem = _stem_from_path(path)
        if _outputs_exist(stem):
            print(f"[skip existing] {stem}")
            continue
        try:
            rgb, mask, method = remove_background(path)
            objects = segment_objects(mask)
        except Exception as e:
            print(f"[error] {stem}: {e}")
            continue
        n = len(objects)
        print(f"\n=== {stem}  bg={method}  fg_frac={mask.mean():.3f}  objects={n} ===")
        for idx, (obj_mask, bbox) in enumerate(objects):
            label = "logo" if n == 1 else f"obj{idx+1}"
            try:
                pattern, stats = digitize_object(rgb, obj_mask, bbox,
                                                 target_h_mm=target_h_mm, name=label)
            except Exception as e:
                print(f"  [error] {label}: {e}")
                continue
            if pattern is None:
                print(f"  [skip] {label}: degenerate/empty")
                continue
            _exp_p, pes_p, _png_p, _js_p = write_outputs(pattern, stats, stem, label, method)
            generate_production_visuals(path, pes_p, stem, label, n)
            rows.append((stem, label, stats))
            print(f"  {label:8s} {stats['width_mm']:6.1f} x {stats['height_mm']:6.1f} mm "
                  f"stitches={stats['stitch_count']:6d} jumps={stats['jump_count']:4d} "
                  f"trims={stats['trim_count']:3d} colors={stats['color_count']} "
                  f"{'LINE' if stats['line_art'] else 'FILL'}")
    return rows


def process_all():
    rows = []
    for img_path, stem, names in IMAGES:
        if not os.path.exists(img_path):
            print(f"MISSING: {img_path}")
            continue
        copy_reference(img_path, stem)
        rgb, mask, method = remove_background(img_path)
        objects = segment_objects(mask)
        print(f"\n=== {stem}  bg={method}  fg_frac={mask.mean():.3f}  "
              f"objects={len(objects)} ===")
        for idx, (obj_mask, bbox) in enumerate(objects):
            if names and idx < len(names):
                label = names[idx]
            elif names and len(names) == 1:
                label = names[0]
            else:
                label = f"obj{idx+1}"
            name = label
            pattern, stats = digitize_object(rgb, obj_mask, bbox, name=name)
            if pattern is None:
                print(f"  [skip] {label}: degenerate/empty")
                continue
            if stats["stitch_count"] > MAX_STITCHES_WARN:
                print(f"  [warn] {label}: {stats['stitch_count']} stitches > cap")
            exp_p, pes_p, png_p, js_p = write_outputs(pattern, stats, stem, label, method)
            generate_production_visuals(img_path, pes_p, stem, label, len(objects))
            rows.append((stem, label, stats))
            print(f"  {label:10s} {stats['width_mm']:6.1f} x {stats['height_mm']:6.1f} mm "
                  f"stitches={stats['stitch_count']:6d} jumps={stats['jump_count']:4d} "
                  f"trims={stats['trim_count']:3d} colors={stats['color_count']} "
                  f"{'LINE' if stats['line_art'] else 'FILL'}")

    # Summary table
    print("\n" + "=" * 78)
    print(f"{'image':16s} {'object':10s} {'W(mm)':>7s} {'H(mm)':>7s} "
          f"{'stitch':>7s} {'jmp':>5s} {'trm':>4s} {'col':>4s}")
    print("-" * 78)
    for stem, label, s in rows:
        print(f"{stem:16s} {label:10s} {s['width_mm']:7.1f} {s['height_mm']:7.1f} "
              f"{s['stitch_count']:7d} {s['jump_count']:5d} {s['trim_count']:4d} "
              f"{s['color_count']:4d}")
    print("=" * 78)
    return rows


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    if args:
        process_images(args)
    else:
        process_all()
