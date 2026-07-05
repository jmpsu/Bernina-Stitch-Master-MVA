#!/usr/bin/env python3
"""Model-free, library-driven, iterative raster -> SVG vectorizer.

NO LLM / model calls anywhere. Pure deterministic image algorithms:
  raster --(vtracer)--> SVG --(cairosvg)--> raster --(skimage SSIM/edge IoU)-->
  score --(coordinate-descent hill-climb)--> better params --> repeat.

Pipeline:
  1. image_features(path)      : cheap descriptors used to seed params and to
                                 bucket images for cross-image param transfer.
  2. trace(path, params)       : run vtracer -> SVG text.
  3. render_svg_rgb(svg, size) : cairosvg -> RGB-on-white, same framing
                                 convention as metrics._fit_gray_to_canvas.
  4. score(orig, rendered)     : ssim_color / rmse_norm / edge_iou / composite.
  5. optimize(path, ...)       : hill-climb over vtracer params, logging EVERY
                                 attempt to vectorization_attempts.jsonl and the
                                 winning params to parameter_correlation_index_vec.json.

vtracer version pinned at run time: 0.6.15 (pip). Binding:
  vtracer.convert_image_to_svg_py(image_path, out_path, colormode, hierarchical,
      mode, filter_speckle, color_precision, layer_difference, corner_threshold,
      length_threshold, max_iterations, splice_threshold, path_precision)

------------------------------------------------------------------------------
DOCTRINE_SEED  --  parameter guidance extracted from the EMBIZ library doctrine
------------------------------------------------------------------------------
Source doctrine skimmed (read-only worktree of origin/mila/embiz-agent-system):
  directives/repo_adapted_embiz_doctrine/potrace_EMBIZ_ADAPTED_DOCTRINE.md
  directives/repo_adapted_embiz_doctrine/inkscape_EMBIZ_ADAPTED_DOCTRINE.md
  directives/repo_adapted_embiz_doctrine/inkstitch_EMBIZ_ADAPTED_DOCTRINE.md

Honest note: the doctrine is potrace/inkscape-oriented prose. It contains
concrete NUMBERS for potrace (a *different* tracer than vtracer), plus color
constraints from inkscape. There are no vtracer-native parameter tables in the
doctrine, so the numbers below are (a) taken verbatim where they map cleanly and
(b) translated conceptually into vtracer's parameter space, then blended with
sensible vtracer defaults. Concrete extracted numbers:

  potrace (potrace_EMBIZ_ADAPTED_DOCTRINE.md, "Parameter Constraints" +
           "potrace_defaults.conf" presets):
    turdsize     default 2,  logo 5,   text 2      (range 2-100) noise/speckle
    alphamax     default 1.0, logo 0.8, text 1.2   (range 0-1.3334) corner sharpness
    opttolerance default 0.2, logo 0.3, text 0.1   (range 0-1.0) curve smoothness/points
    Quality gate: min 300 DPI logos / 600 DPI text; trace time limit 60s/image;
    output must parse as XML and contain <path> elements.

  inkscape (inkscape_EMBIZ_ADAPTED_DOCTRINE.md, "Color Palette Management" +
            quality_thresholds):
    max_thread_colors = 15  -> cap on distinct colors (color layering budget)
    max_color_delta_e = 5.0 -> color-merge tolerance (informs layer_difference)

Conceptual mapping potrace/inkscape -> vtracer (used to build the seed presets):
    turdsize (noise filter)     -> filter_speckle   (speckle removal)
    alphamax (corner sharpness) -> corner_threshold (higher potrace alphamax =
                                    smoother/rounder -> lower vtracer corner_threshold)
    opttolerance (fewer points) -> path_precision / length_threshold / splice_threshold
    max_thread_colors=15        -> color_precision cap so <= ~15 quantized colors
    logo vs text presets        -> "logo"/"line_art" seed presets below
"""

from __future__ import annotations

import io
import json
import os
import time

import numpy as np

# --- paths (repo-relative, resolved to this file's directory) ----------------
_HERE = os.path.dirname(os.path.abspath(__file__))
ATTEMPTS_LOG = os.path.join(_HERE, "vectorization_attempts.jsonl")
PARAM_INDEX = os.path.join(_HERE, "parameter_correlation_index_vec.json")
OUT_DIR = os.path.join(_HERE, "vectorized_svg")

RENDER_SIZE = 512  # square canvas for scoring

# -----------------------------------------------------------------------------
# v2 anti-collapse guardrail + color-fidelity constants (see reports/vectorizer_v2.md)
# A degenerate candidate that flattens the image (e.g. a flat gray plate) can score
# HIGH composite on a mostly-light source (low RMSE + ok SSIM). These constants let
# score() detect that collapse and multiplicatively penalize it so it can never win.
# -----------------------------------------------------------------------------
COLLAPSE_QUANT_COLORS = 32       # PIL quantize palette size for distinct-color count
COLLAPSE_MIN_BIN_FRAC = 0.005    # palette bin must cover >=0.5% of pixels to count
COLLAPSE_COLOR_FRAC = 0.60       # rendered distinct colors must be >=60% of source
COLLAPSE_STD_FRAC = 0.60         # rendered global std must be >=60% of source std
COLLAPSE_FG_FRAC = 0.50          # rendered foreground fraction must be >=50% of source
COLLAPSE_PENALTY = 0.30          # multiplicative composite penalty when collapsed

COLOR_HIST_BINS = 4              # 4x4x4 RGB histogram for the color_fidelity term

# v3 content-crop scoring threshold. score() crops BOTH source and render to their
# non-white content bbox before re-fitting to a common canvas (removes the
# whitespace-margin misregistration described in reports/vectorizer_v3.md). The
# threshold must treat cairosvg's ANTI-ALIAS HALO (edge pixels ~245-249, visually
# white) as background: at thresh=250 the render's halo asymmetrically enlarges its
# bbox vs the sharp source jpeg, mis-scaling the two and CRASHING SSIM on clean art
# (measured: crest 0.98->0.62, flags 0.98->0.94). At 240 both bboxes match exactly
# and every passing image holds >=0.98 (identity stays 1.0). 230 starts eating real
# near-white content (crest 0.93). 240 is the robust operating point.
CROP_CONTENT_THRESH = 240

# Composite weights (v2). Sums to 1.0 before the anti-collapse guard multiplier.
W_SSIM = 0.55
W_EDGE = 0.15
W_RMSE = 0.10
W_COLORFID = 0.20

# Search robustness (v2)
DEFAULT_MAX_ITERS = 300          # global iteration budget across all multi-starts
STALL_LIMIT = 40                 # stop a hill-climb after N consecutive non-improving iters

# -----------------------------------------------------------------------------
# DOCTRINE_SEED: seed presets derived from the doctrine (see module docstring).
# Values live in vtracer's parameter space. `default` is the generic starting
# point; `logo`/`line_art` mirror the potrace logo/text presets.
# -----------------------------------------------------------------------------
DOCTRINE_SEED = {
    # source: vtracer defaults blended with potrace default preset (turdsize 2,
    # alphamax 1.0, opttolerance 0.2) and inkscape 15-color cap.
    "default": {
        "colormode": "color",
        "hierarchical": "stacked",
        "mode": "spline",
        "color_precision": 6,     # ~ up to 2^? quantization; capped low for <=15 colors
        "filter_speckle": 4,      # <- potrace turdsize (noise); default region ~2-5
        "corner_threshold": 60,   # <- potrace alphamax 1.0 -> mid corner sharpness
        "length_threshold": 4.0,  # <- opttolerance-ish min segment length
        "splice_threshold": 45,   # curve joining
        "path_precision": 8,      # coordinate precision (higher = more faithful)
        "layer_difference": 16,   # <- inkscape deltaE color-merge tolerance
    },
    # source: potrace logo_preset (turdsize 5, alphamax 0.8=smoother,
    # opttolerance 0.3=fewer points). Multicolor crests/logos.
    "logo": {
        "colormode": "color",
        "hierarchical": "stacked",
        "mode": "spline",
        "color_precision": 7,     # crests need more colors (still <=15 target)
        "filter_speckle": 5,      # potrace turdsize logo = 5
        "corner_threshold": 50,   # alphamax 0.8 -> smoother -> lower threshold
        "length_threshold": 4.0,
        "splice_threshold": 45,
        "path_precision": 6,      # opttolerance 0.3 -> fewer points
        "layer_difference": 16,
    },
    # source: potrace text_preset (turdsize 2, alphamax 1.2=sharper corners,
    # opttolerance 0.1=more points/faithful). Green line-art / mono line work.
    "line_art": {
        "colormode": "color",
        "hierarchical": "stacked",
        "mode": "spline",
        "color_precision": 4,     # few colors in line art
        "filter_speckle": 2,      # potrace turdsize text = 2 (keep fine detail)
        "corner_threshold": 70,   # alphamax 1.2 -> sharper corners -> higher threshold
        "length_threshold": 4.0,
        "splice_threshold": 45,
        "path_precision": 8,      # opttolerance 0.1 -> more points, faithful
        "layer_difference": 16,
    },
}

# Parameter search space for the hill-climb (name -> ordered candidate ladder).
PARAM_GRID = {
    "color_precision": [1, 2, 3, 4, 5, 6, 7, 8],
    "filter_speckle": [0, 1, 2, 4, 6, 8, 12, 16],
    "corner_threshold": [10, 20, 30, 40, 50, 60, 70, 80, 90],
    "length_threshold": [3.5, 4.0, 5.0, 7.0, 10.0],
    "splice_threshold": [15, 30, 45, 60, 75],
    "path_precision": [3, 4, 5, 6, 7, 8],
    "layer_difference": [4, 8, 16, 24, 32, 48],
    "mode": ["spline", "polygon"],
}

# Order in which coordinate-descent perturbs factors (most impactful first).
SEARCH_ORDER = [
    "color_precision", "filter_speckle", "corner_threshold",
    "layer_difference", "path_precision", "mode",
    "splice_threshold", "length_threshold",
]


# =============================================================================
# 1. image features
# =============================================================================
def image_features(path):
    """Cheap deterministic descriptors of a raster image.

    Returns dict: width, height, aspect, distinct_colors (PIL quantize estimate),
    edge_density (mean Sobel magnitude in [0,1]), foreground_fraction (non-white
    fraction), is_line_art (bool). Used to pick a seed preset and to bucket
    images for cross-image parameter transfer.
    """
    from PIL import Image
    from skimage.filters import sobel

    img = Image.open(path).convert("RGB")
    w, h = img.size

    # distinct-color estimate via adaptive quantize to 64, count used palette.
    q = img.quantize(colors=64, method=Image.FASTOCTREE)
    color_counts = q.getcolors(maxcolors=64 * 64) or []
    total = float(sum(c for c, _ in color_counts)) or 1.0
    # count colors covering >=0.5% of pixels (ignore quantization dust)
    distinct_colors = sum(1 for c, _ in color_counts if c / total >= 0.005)

    gray = np.asarray(img.convert("L"), dtype=np.float64) / 255.0
    edges = sobel(gray)
    edge_density = float(edges.mean())

    # foreground = pixels notably darker/more-saturated than near-white paper.
    arr = np.asarray(img, dtype=np.float64)
    lum = arr.mean(axis=2)
    sat = arr.max(axis=2) - arr.min(axis=2)
    foreground = (lum < 240) | (sat > 25)
    foreground_fraction = float(foreground.mean())

    # line art: few colors AND sparse foreground AND crisp edges.
    is_line_art = bool(distinct_colors <= 6 and foreground_fraction < 0.35)

    return {
        "width": int(w),
        "height": int(h),
        "aspect": round(w / h, 4) if h else 1.0,
        "distinct_colors": int(distinct_colors),
        "edge_density": round(edge_density, 5),
        "foreground_fraction": round(foreground_fraction, 5),
        "is_line_art": is_line_art,
    }


def feature_bucket(feat):
    """Coarse bucket key for cross-image param transfer (the utilization
    matrix). Buckets by line-art flag, color band, and edge-density band."""
    if feat["is_line_art"]:
        kind = "line_art"
    elif feat["distinct_colors"] >= 12:
        kind = "multicolor"
    else:
        kind = "logo"
    color_band = min(int(feat["distinct_colors"]) // 4, 8)  # 0..8
    edge_band = int(min(feat["edge_density"] * 20, 5))       # 0..5
    return f"{kind}|c{color_band}|e{edge_band}"


def seed_preset_for(feat):
    """Pick a DOCTRINE_SEED preset from features."""
    if feat["is_line_art"]:
        return "line_art"
    if feat["distinct_colors"] >= 8:
        return "logo"
    return "default"


# High-color multi-start seed (v2): a rich-palette / low-speckle starting point so
# the search can explore faithful traces of shaded art before considering low-color
# candidates (which the anti-collapse guard now blocks when they flatten the image).
HIGH_COLOR_SEED = {
    "colormode": "color",
    "hierarchical": "stacked",
    "mode": "spline",
    "color_precision": 8,     # max palette: keep source color richness
    "filter_speckle": 1,      # keep fine detail / small regions
    "corner_threshold": 60,
    "length_threshold": 4.0,
    "splice_threshold": 45,
    "path_precision": 8,
    "layer_difference": 8,    # finer color separation -> more layers
}


# Soft-shade tracing push (v3): for gradient/anti-aliased illustrations (the
# house), give the search extra high-fidelity starts -- max color budget, many
# layers (very low layer_difference), and BOTH spline and polygon region modes.
# Flat region-tracing can only approximate gradients, so we let it use as many
# solid layers as possible before conceding a real ceiling.
SOFT_SHADE_STARTS = {
    "soft_spline_max": {
        "colormode": "color", "hierarchical": "stacked", "mode": "spline",
        "color_precision": 8, "filter_speckle": 1, "corner_threshold": 60,
        "length_threshold": 4.0, "splice_threshold": 45, "path_precision": 8,
        "layer_difference": 4,
    },
    "soft_polygon_max": {
        "colormode": "color", "hierarchical": "stacked", "mode": "polygon",
        "color_precision": 8, "filter_speckle": 1, "corner_threshold": 60,
        "length_threshold": 4.0, "splice_threshold": 45, "path_precision": 8,
        "layer_difference": 4,
    },
}


def is_soft_shaded(feat):
    """Soft-shaded / anti-aliased illustration: many distinct colors, not line
    art, appreciable foreground. These resist flat-color region tracing and need
    a higher color budget + light source pre-smoothing."""
    return bool((not feat["is_line_art"])
                and feat["distinct_colors"] >= 10
                and feat["foreground_fraction"] >= 0.30)


def color_precision_floor(feat):
    """Lower bound on color_precision derived from the source's distinct-color
    count, so the hill-climb never quantizes below what the source needs (this is
    the root cause of the v1 gray-plate collapse)."""
    dc = feat["distinct_colors"]
    if dc >= 12:
        return 6
    if dc >= 8:
        return 5
    if dc >= 5:
        return 4
    return 3


def _presmoothed_source(path, feat):
    """For soft-shaded sources ONLY, write a lightly median-smoothed copy of the
    raster to a temp file and return its path (helps vtracer form clean regions
    from anti-aliased gradients). Returns (trace_path, cleanup_path_or_None).
    Scoring always uses the TRUE original, never this smoothed copy."""
    if not is_soft_shaded(feat):
        return path, None
    import tempfile
    from PIL import Image, ImageFilter
    img = Image.open(path).convert("RGB")
    # light median smoothing: edge-preserving, collapses anti-alias noise into
    # flatter regions without destroying structure.
    sm = img.filter(ImageFilter.MedianFilter(size=3))
    fd, out_path = tempfile.mkstemp(suffix=".png")
    os.close(fd)
    sm.save(out_path)
    return out_path, out_path


# =============================================================================
# 2. trace
# =============================================================================
_ALLOWED = {
    "colormode", "hierarchical", "mode", "filter_speckle", "color_precision",
    "layer_difference", "corner_threshold", "length_threshold",
    "max_iterations", "splice_threshold", "path_precision",
}


def trace(path, params):
    """Run vtracer with `params`; return SVG text. Raises on tracer failure."""
    import tempfile
    import vtracer

    kw = {k: v for k, v in params.items() if k in _ALLOWED}
    # vtracer wants ints for several fields
    for k in ("color_precision", "filter_speckle", "corner_threshold",
              "splice_threshold", "path_precision", "layer_difference",
              "max_iterations"):
        if k in kw and kw[k] is not None:
            kw[k] = int(kw[k])
    if "length_threshold" in kw and kw["length_threshold"] is not None:
        kw["length_threshold"] = float(kw["length_threshold"])

    fd, out_path = tempfile.mkstemp(suffix=".svg")
    os.close(fd)
    try:
        vtracer.convert_image_to_svg_py(path, out_path, **kw)
        with open(out_path, "r", encoding="utf-8") as f:
            return f.read()
    finally:
        try:
            os.remove(out_path)
        except OSError:
            pass


# =============================================================================
# 3. render SVG -> RGB
# =============================================================================
def _fit_rgb_to_canvas(rgb_img, size):
    """Color version of metrics._fit_gray_to_canvas: fit a PIL RGB image (on
    white) into a size*size white canvas, aspect preserved, centered."""
    from PIL import Image
    g = rgb_img.copy()
    g.thumbnail((size, size), Image.LANCZOS)
    canvas = Image.new("RGB", (size, size), (255, 255, 255))
    off = ((size - g.width) // 2, (size - g.height) // 2)
    canvas.paste(g, off)
    return np.asarray(canvas, dtype=np.uint8)


def render_svg_rgb(svg_str, size=RENDER_SIZE):
    """Rasterize SVG text to a size*size RGB numpy array (content on white,
    aspect preserved, centered). Returns None on failure."""
    from PIL import Image
    import cairosvg
    try:
        png_bytes = cairosvg.svg2png(
            bytestring=svg_str.encode("utf-8"), output_width=size)
        img = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
    except Exception:
        return None
    bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
    bg.alpha_composite(img)
    return _fit_rgb_to_canvas(bg.convert("RGB"), size)


def load_image_rgb(path, size=RENDER_SIZE):
    """Load a raster file into the same size*size RGB canvas framing."""
    from PIL import Image
    img = Image.open(path).convert("RGB")
    return _fit_rgb_to_canvas(img, size)


# =============================================================================
# 4. score
# =============================================================================
def _crop_to_content(rgb, thresh=250):
    """Crop an RGB uint8 array to the bounding box of its non-white content.

    Non-white = pixels whose MINIMUM channel value is < `thresh` (a pixel is
    "white" only when all three channels are near 255). Returns the cropped
    array. If the image is entirely white (no content), returns it unchanged.

    v3: this removes whitespace-margin misregistration before scoring. The
    source raster typically has wide white margins while the SVG render tightens
    to its content bbox and fills more of the canvas; cropping BOTH to content
    before resizing to a common size makes the comparison like-for-like.

    NOTE on `thresh`: score() calls this with CROP_CONTENT_THRESH (240), NOT the
    250 default, so cairosvg's anti-alias halo (~245-249, visually white) is
    treated as background and does not asymmetrically enlarge the render bbox.
    See CROP_CONTENT_THRESH for the measurements behind that choice.
    """
    if rgb is None:
        return rgb
    mask = rgb.min(axis=2) < thresh
    ys_xs = np.argwhere(mask)
    if ys_xs.size == 0:
        return rgb  # all white -> nothing to crop
    y0, x0 = ys_xs.min(axis=0)
    y1, x1 = ys_xs.max(axis=0)
    return rgb[y0:y1 + 1, x0:x1 + 1]


def _edge_map(gray01):
    """Binary Sobel edge map thresholded at mean+std (mirrors metrics._edge_map)."""
    from skimage.filters import sobel
    e = sobel(gray01)
    emax = float(e.max())
    if emax <= 0.0:
        return np.zeros(e.shape, dtype=bool)
    thr = float(e.mean() + e.std())
    if thr <= 0.0:
        thr = 0.1 * emax
    return e > thr


def _distinct_std_fg(rgb):
    """Return (distinct_color_count, global_std, foreground_fraction) for an RGB
    uint8 array. distinct = PIL quantize to COLLAPSE_QUANT_COLORS, count palette
    bins covering >= COLLAPSE_MIN_BIN_FRAC of pixels (ignores quantization dust).
    global_std = std over all channels/pixels. foreground = fraction of pixels
    that are notably darker/more saturated than near-white paper."""
    from PIL import Image
    img = Image.fromarray(rgb)
    q = img.quantize(colors=COLLAPSE_QUANT_COLORS, method=Image.FASTOCTREE)
    counts = q.getcolors(maxcolors=COLLAPSE_QUANT_COLORS * 8) or []
    total = float(sum(c for c, _ in counts)) or 1.0
    distinct = sum(1 for c, _ in counts if c / total >= COLLAPSE_MIN_BIN_FRAC)

    arr = rgb.astype(np.float64)
    global_std = float(arr.std())
    lum = arr.mean(axis=2)
    sat = arr.max(axis=2) - arr.min(axis=2)
    fg = float(((lum < 240) | (sat > 25)).mean())
    return distinct, global_std, fg


def _color_hist(rgb, bins=COLOR_HIST_BINS):
    """Normalized bins^3 RGB histogram (sums to 1.0) for color_fidelity."""
    idx = (rgb.astype(np.int64) * bins) // 256
    idx = np.clip(idx, 0, bins - 1)
    flat = (idx[..., 0] * bins + idx[..., 1]) * bins + idx[..., 2]
    h = np.bincount(flat.ravel(), minlength=bins ** 3).astype(np.float64)
    s = h.sum()
    return h / s if s > 0 else h


def _collapse_guard(orig_rgb, rendered_rgb):
    """Detect a degenerate/flattened render relative to the source. Returns
    (guard_factor, collapsed_bool, detail_dict). guard_factor is 1.0 when the
    render preserves the source's color richness/contrast/foreground, else
    COLLAPSE_PENALTY so such candidates can never win the composite."""
    od, os_std, ofg = _distinct_std_fg(orig_rgb)
    rd, rs_std, rfg = _distinct_std_fg(rendered_rgb)
    color_ok = rd >= COLLAPSE_COLOR_FRAC * max(od, 1)
    std_ok = rs_std >= COLLAPSE_STD_FRAC * max(os_std, 1e-6)
    fg_ok = rfg >= COLLAPSE_FG_FRAC * max(ofg, 1e-6)
    collapsed = not (color_ok and std_ok and fg_ok)
    detail = {
        "src_colors": int(od), "rnd_colors": int(rd),
        "src_std": round(os_std, 3), "rnd_std": round(rs_std, 3),
        "src_fg": round(ofg, 4), "rnd_fg": round(rfg, 4),
        "color_ok": color_ok, "std_ok": std_ok, "fg_ok": fg_ok,
    }
    return (COLLAPSE_PENALTY if collapsed else 1.0), collapsed, detail


def score(orig_rgb, rendered_rgb):
    """Fidelity metrics between two RGB uint8 arrays (resized to common size).

    v4 REVERT: the v3 content-crop-before-scoring step is removed. It hurt clean
    art (crest 0.98->0.94, caddie 0.984->0.968) by introducing a sub-pixel
    crop-then-recenter shift, and never closed the house gap (registration was
    never the house's problem). Both arrays already arrive framed identically by
    `_fit_rgb_to_canvas` (via load_image_rgb / render_svg_rgb), so scoring is done
    directly. `_crop_to_content` / CROP_CONTENT_THRESH remain defined but UNUSED.

    v2 composite (restored, unchanged):
      base = W_SSIM*ssim_color + W_EDGE*edge_iou + W_RMSE*(1-rmse_norm)
             + W_COLORFID*color_fidelity
      composite = base * collapse_guard   (guard is 1.0 or COLLAPSE_PENALTY)

    color_fidelity = histogram-intersection similarity over a reduced 4x4x4 RGB
    palette. The collapse guard hard-penalizes flattened/degenerate renders so a
    flat gray plate can never out-score a faithful trace. ssim_color is reported
    separately and unmodified.
    """
    from PIL import Image
    from skimage.metrics import structural_similarity as ssim_fn

    if orig_rgb is None or rendered_rgb is None:
        return None

    # v2 framing: both arrays already share the RENDER_SIZE canvas; only resize
    # if shapes somehow differ. No content-crop, no re-centering.
    if orig_rgb.shape != rendered_rgb.shape:
        h = min(orig_rgb.shape[0], rendered_rgb.shape[0])
        w = min(orig_rgb.shape[1], rendered_rgb.shape[1])
        orig_rgb = np.asarray(
            Image.fromarray(orig_rgb).resize((w, h), Image.LANCZOS))
        rendered_rgb = np.asarray(
            Image.fromarray(rendered_rgb).resize((w, h), Image.LANCZOS))

    a = orig_rgb.astype(np.float64)
    b = rendered_rgb.astype(np.float64)

    ssim_color = float(ssim_fn(orig_rgb, rendered_rgb,
                               channel_axis=-1, data_range=255))

    rmse = float(np.sqrt(np.mean((a - b) ** 2)))
    rmse_norm = rmse / 255.0

    ea = _edge_map(a.mean(axis=2) / 255.0)
    eb = _edge_map(b.mean(axis=2) / 255.0)
    inter = float(np.logical_and(ea, eb).sum())
    union = float(np.logical_or(ea, eb).sum())
    edge_iou = (inter / union) if union > 0 else 1.0

    # color fidelity: histogram-intersection over reduced RGB palette.
    ha = _color_hist(orig_rgb)
    hb = _color_hist(rendered_rgb)
    color_fidelity = float(np.minimum(ha, hb).sum())

    guard, collapsed, detail = _collapse_guard(orig_rgb, rendered_rgb)

    base = (W_SSIM * ssim_color + W_EDGE * edge_iou
            + W_RMSE * (1.0 - rmse_norm) + W_COLORFID * color_fidelity)
    composite = base * guard
    return {
        "ssim_color": round(ssim_color, 6),
        "rmse_norm": round(rmse_norm, 6),
        "edge_iou": round(edge_iou, 6),
        "color_fidelity": round(color_fidelity, 6),
        "collapsed": bool(collapsed),
        "collapse_detail": detail,
        "composite": round(composite, 6),
    }


# =============================================================================
# param-index (cross-image transfer / utilization matrix) helpers
# =============================================================================
def _load_param_index():
    if os.path.exists(PARAM_INDEX):
        try:
            with open(PARAM_INDEX, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _feature_distance(fa, fb):
    """Small weighted distance between two feature dicts for nearest-prior."""
    keys = [("distinct_colors", 12.0), ("edge_density", 0.15),
            ("foreground_fraction", 0.4), ("aspect", 1.0)]
    d = 0.0
    for k, scale in keys:
        d += ((float(fa.get(k, 0)) - float(fb.get(k, 0))) / scale) ** 2
    d += 0.0 if fa.get("is_line_art") == fb.get("is_line_art") else 4.0
    return d ** 0.5


def _seed_from_index(feat):
    """Return (params, source_str) seeded from a prior similar image if one
    exists in the index, else from the doctrine preset for these features."""
    index = _load_param_index()
    best_key, best_dist, best_entry = None, None, None
    for key, entry in index.items():
        ff = entry.get("features")
        if not ff:
            continue
        dist = _feature_distance(feat, ff)
        if best_dist is None or dist < best_dist:
            best_key, best_dist, best_entry = key, dist, entry

    # Accept a prior only if reasonably close.
    if best_entry is not None and best_dist is not None and best_dist < 3.0:
        params = dict(DOCTRINE_SEED[seed_preset_for(feat)])
        params.update(best_entry.get("params", {}))
        return params, f"param_index[{best_key}] dist={best_dist:.2f}"

    preset = seed_preset_for(feat)
    return dict(DOCTRINE_SEED[preset]), f"DOCTRINE_SEED[{preset}]"


def _update_param_index(feat, params, best_scores):
    index = _load_param_index()
    bucket = feature_bucket(feat)
    prev = index.get(bucket)
    prev_comp = prev.get("composite", -1) if prev else -1
    # keep the better-performing params for this bucket
    if best_scores["composite"] >= prev_comp:
        index[bucket] = {
            "features": feat,
            "params": {k: params[k] for k in params},
            "composite": best_scores["composite"],
            "ssim_color": best_scores["ssim_color"],
            "updated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
    with open(PARAM_INDEX, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, sort_keys=True)


def _log_attempt(record):
    with open(ATTEMPTS_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


# =============================================================================
# 5. optimize  --  coordinate-descent hill-climb
# =============================================================================
def _neighbor_candidates(factor, cur, cp_floor):
    """Candidate values for a factor: numeric ladders -> immediate up/down
    neighbours; categorical -> all others. color_precision is clamped to its
    floor so the search never quantizes below what the source needs."""
    ladder = PARAM_GRID[factor]
    candidates = []
    if cur in ladder:
        i = ladder.index(cur)
        for j in (i - 1, i + 1):
            if 0 <= j < len(ladder):
                candidates.append(ladder[j])
    else:
        candidates = list(ladder)
    if factor == "color_precision":
        candidates = [c for c in candidates if c >= cp_floor]
    seen = set()
    return [c for c in candidates
            if c != cur and not (c in seen or seen.add(c))]


def optimize(path, max_iters=DEFAULT_MAX_ITERS, target_ssim=0.98,
             stall_k=STALL_LIMIT, verbose=True):
    """Iteratively improve vtracer params for `path` by MULTI-START
    coordinate-descent hill-climbing of the (guarded) composite score.

    v2 search robustness:
      - seeds from each DOCTRINE_SEED preset (default/logo/line_art), a high-color
        start, and the nearest prior in the param index; hill-climb from each and
        keep the GLOBAL best.
      - `max_iters` is a global iteration budget across all starts (default 300).
      - each hill-climb stops after `stall_k` (=40) consecutive non-improving
        iterations ("no further improvement possible").
      - color_precision is floored by the source's distinct-color count.
      - soft-shaded sources are traced from a lightly pre-smoothed copy, but ALWAYS
        scored against the true original.

    Logs every attempt; saves best SVG + compare PNG; updates the param index."""
    stem = os.path.splitext(os.path.basename(path))[0]
    os.makedirs(OUT_DIR, exist_ok=True)

    feat = image_features(path)
    orig_rgb = load_image_rgb(path)              # TRUE original, used for scoring
    cp_floor = color_precision_floor(feat)
    trace_path, cleanup = _presmoothed_source(path, feat)  # vtracer input only

    iteration = 0

    def evaluate(p, note):
        nonlocal iteration
        iteration += 1
        try:
            svg = trace(trace_path, p)
            rendered = render_svg_rgb(svg)
            sc = score(orig_rgb, rendered)       # scored vs TRUE original
        except Exception as exc:  # tracer/render failure -> worst score
            sc = None
            svg = None
            note = f"{note} ERROR:{type(exc).__name__}"
        if sc is None:
            sc = {"ssim_color": -1.0, "rmse_norm": 1.0, "edge_iou": 0.0,
                  "color_fidelity": 0.0, "collapsed": True, "composite": -1.0}
        return svg, sc, note

    def _clamp_seed(p):
        p = dict(p)
        if "color_precision" in p:
            p["color_precision"] = max(int(p["color_precision"]), cp_floor)
        return p

    def log(trial, sc, accepted, note, start_label):
        _log_attempt({
            "image": stem, "version": "v3", "start": start_label,
            "iteration": iteration, "params": dict(trial),
            "ssim_color": sc["ssim_color"], "edge_iou": sc["edge_iou"],
            "rmse_norm": sc["rmse_norm"],
            "color_fidelity": sc.get("color_fidelity"),
            "collapsed": sc.get("collapsed"),
            "composite": sc["composite"], "accepted": accepted, "note": note,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })

    # --- assemble the multi-start seed list ---
    idx_params, idx_src = _seed_from_index(feat)
    starts = [
        ("default", _clamp_seed(DOCTRINE_SEED["default"])),
        ("logo", _clamp_seed(DOCTRINE_SEED["logo"])),
        ("line_art", _clamp_seed(DOCTRINE_SEED["line_art"])),
        ("high_color", _clamp_seed(HIGH_COLOR_SEED)),
        (f"index({idx_src})", _clamp_seed(idx_params)),
    ]
    # v3: soft-shaded sources get extra max-fidelity spline+polygon starts.
    if is_soft_shaded(feat):
        for lbl, seed in SOFT_SHADE_STARTS.items():
            starts.append((lbl, _clamp_seed(seed)))

    trajectory = []
    g_best_svg, g_best_sc, g_best_params, g_best_start = None, None, None, None

    def _hillclimb(start_label, seed_params):
        """One coordinate-descent hill-climb from seed_params. Returns
        (best_svg, best_sc, best_params). `max_iters` is the PER-START budget;
        the climb also stops after stall_k consecutive non-improving iters
        ('no further improvement possible') or on reaching target_ssim."""
        nonlocal iteration
        li = 0  # per-start iteration count (budget is per start)
        b_svg, b_sc, note = evaluate(seed_params, f"seed<-{start_label}")
        li += 1
        b_params = dict(seed_params)
        log(seed_params, b_sc, True, f"seed<-{start_label}", start_label)
        if verbose:
            print(f"[{stem}] start={start_label} seed "
                  f"ssim={b_sc['ssim_color']:.4f} "
                  f"cfid={b_sc.get('color_fidelity', -1):.4f} "
                  f"collapsed={b_sc.get('collapsed')} "
                  f"composite={b_sc['composite']:.4f}")

        stall = 0
        order_pos = 0
        while (li < max_iters and stall < stall_k
               and b_sc["ssim_color"] < target_ssim):
            factor = SEARCH_ORDER[order_pos % len(SEARCH_ORDER)]
            order_pos += 1
            candidates = _neighbor_candidates(factor, b_params.get(factor),
                                              cp_floor)
            improved = False
            for cand in candidates:
                if li >= max_iters or b_sc["ssim_color"] >= target_ssim:
                    break
                li += 1
                trial = dict(b_params)
                trial[factor] = cand
                svg, sc, note = evaluate(trial, f"{factor}:{b_params.get(factor)}->{cand}")
                accepted = sc["composite"] > b_sc["composite"] + 1e-6
                log(trial, sc, accepted, note, start_label)
                if accepted:
                    b_sc, b_params, b_svg = sc, trial, svg
                    improved = True
                    if verbose:
                        print(f"[{stem}] {start_label} it{iteration} {note} "
                              f"ACCEPT ssim={sc['ssim_color']:.4f} "
                              f"cfid={sc.get('color_fidelity', -1):.4f} "
                              f"composite={sc['composite']:.4f}")
                    break  # greedy restart of factor cycle
            stall = 0 if improved else stall + 1
        return b_svg, b_sc, b_params

    try:
        for start_label, seed_params in starts:
            # Once a start has already reached target, skip the rest (they would
            # only re-confirm); otherwise try every seed and keep the best.
            if g_best_sc is not None and g_best_sc["ssim_color"] >= target_ssim:
                break
            b_svg, b_sc, b_params = _hillclimb(start_label, seed_params)
            if b_sc is None:
                continue
            if g_best_sc is None or b_sc["composite"] > g_best_sc["composite"]:
                g_best_svg, g_best_sc = b_svg, b_sc
                g_best_params, g_best_start = b_params, start_label
                trajectory.append(g_best_sc["composite"])
                if verbose:
                    print(f"[{stem}] NEW GLOBAL BEST from {start_label}: "
                          f"ssim={b_sc['ssim_color']:.4f} "
                          f"composite={b_sc['composite']:.4f}")
    finally:
        if cleanup:
            try:
                os.remove(cleanup)
            except OSError:
                pass

    best_svg, best_sc, best_params = g_best_svg, g_best_sc, g_best_params
    start_composite = trajectory[0] if trajectory else best_sc["composite"]

    # --- persist best result ---
    svg_path = os.path.join(OUT_DIR, f"{stem}.svg")
    if best_svg is not None:
        with open(svg_path, "w", encoding="utf-8") as f:
            f.write(best_svg)
    compare_path = os.path.join(OUT_DIR, f"{stem}_compare.png")
    _save_compare(orig_rgb, best_svg, compare_path)

    _update_param_index(feat, best_params, best_sc)

    reached = bool(best_sc["ssim_color"] >= target_ssim)
    result = {
        "image": stem,
        "path": path,
        "features": feat,
        "feature_bucket": feature_bucket(feat),
        "soft_shaded": is_soft_shaded(feat),
        "color_precision_floor": cp_floor,
        "best_start": g_best_start,
        "iterations": iteration,
        "best_ssim": round(best_sc["ssim_color"], 6),
        "best_composite": round(best_sc["composite"], 6),
        "best_color_fidelity": best_sc.get("color_fidelity"),
        "best_collapsed": best_sc.get("collapsed"),
        "start_composite": round(start_composite, 6),
        "best_params": best_params,
        "best_scores": best_sc,
        "reached_target": reached,
        "svg_path": svg_path,
        "compare_path": compare_path,
        "trajectory": trajectory,
    }
    if verbose:
        print(f"[{stem}] DONE iters={iteration} best_start={g_best_start} "
              f"ssim={best_sc['ssim_color']:.4f} "
              f"collapsed={best_sc.get('collapsed')} "
              f"target>={target_ssim} reached={reached}")
    return result


def _save_compare(orig_rgb, best_svg, out_path):
    """Write a side-by-side original | render PNG."""
    from PIL import Image
    size = orig_rgb.shape[0]
    rendered = render_svg_rgb(best_svg, size) if best_svg else None
    if rendered is None:
        rendered = np.full_like(orig_rgb, 255)
    gap = 8
    canvas = np.full((size, size * 2 + gap, 3), 255, dtype=np.uint8)
    canvas[:, :size] = orig_rgb
    canvas[:, size + gap:] = rendered
    Image.fromarray(canvas).save(out_path)


# =============================================================================
# CLI
# =============================================================================
def main(argv):
    import argparse
    ap = argparse.ArgumentParser(description="Model-free iterative vectorizer")
    ap.add_argument("images", nargs="+", help="raster image paths")
    ap.add_argument("--max-iters", type=int, default=DEFAULT_MAX_ITERS)
    ap.add_argument("--target-ssim", type=float, default=0.98)
    ap.add_argument("--json", action="store_true", help="print result JSON")
    args = ap.parse_args(argv)

    results = []
    for p in args.images:
        res = optimize(p, max_iters=args.max_iters,
                       target_ssim=args.target_ssim)
        results.append(res)

    print("\n=== convergence summary ===")
    print(f"{'image':<28} {'best_ssim':>10} {'cfid':>7} {'collapse':>8} "
          f"{'iters':>6} {'best_start':>14} {'>=0.98':>7}")
    for r in results:
        print(f"{r['image']:<28} {r['best_ssim']:>10.4f} "
              f"{(r['best_color_fidelity'] or 0):>7.4f} "
              f"{str(r['best_collapsed']):>8} {r['iterations']:>6} "
              f"{str(r['best_start']):>14} {str(r['reached_target']):>7}")
    if args.json:
        print(json.dumps(results, indent=2))
    return results


if __name__ == "__main__":
    import sys
    main(sys.argv[1:])
