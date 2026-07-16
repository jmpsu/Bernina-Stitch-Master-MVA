#!/usr/bin/env python3
"""solidify.py — library-grounded solid-shape posterization.

Turns a customer raster (typically a pencil/colored-pencil drawing on
textured paper) into SOLID, flat-color, well-defined shapes: the form that
both vectorizes into clean SVG paths and digitizes into neat satin-bordered
fills. This is the missing stage the knowledge library prescribes; every step
cites the knowledge object it applies.

Knowledge objects applied (knowledge/vectorization/*):

  noise_agent/mkbitmap_lowpass_foreground_smoothing
      -> median + gaussian pre-smooth BEFORE any thresholding/clustering,
         so paper grain and pencil texture never become regions.
  noise_agent/mkbitmap_highpass_background_gradient
      -> background flattening is delegated to digitizer.remove_background
         (corner-sampled background estimate = the highpass analogue).
  noise_agent/blacklevel_bilevel_cutoff
      -> foreground/background split at the luminance valley (Otsu inside
         remove_background), not a fixed cutoff.
  noise_agent/turdsize_speckle_suppression
      -> per-region minimum area; specks are reassigned to the surrounding
         region instead of surviving as micro-shapes.
  color_agent/hsl_perceptual_color_matching
      -> clustering runs in CIE Lab (perceptual), not raw RGB.
  color_agent/color_delta_e_merge_tolerance
      -> cluster centers within delta-E 5.0 are merged into one thread color.
  color_agent/max_thread_color_budget
      -> the palette is capped (default 6 here, well under the 15 max).
  color_agent/hierarchical_color_layering
      -> regions are returned back-to-front (largest first) for opaque
         stacked emission, matching how fills are digitized.
  edge_agent/max_path_deviation_fidelity
      -> boundary smoothing uses a closing/opening radius bounded by the
         0.5 mm deviation budget at the final stitch scale.

Public API:
    regions, poster = solidify(rgb, fg_mask, max_colors=6, ...)
      regions: list of (rgb_tuple, mask_bool) back-to-front, non-overlapping,
               each mask SOLID (holes filled unless another region owns them)
      poster:  uint8 RGB posterized image (background white)
    solidify_file(in_path, out_path, ...) -> out_path (posterized PNG)
"""

from __future__ import annotations

import numpy as np
from scipy import ndimage
from skimage import color as skcolor
from skimage import filters, morphology

# color_agent/color_delta_e_merge_tolerance: delta-E <= 5.0 == same thread
DELTA_E_MERGE = 5.0
# color_agent/max_thread_color_budget: practical per-design budget (<= 15)
MAX_COLORS = 6
# noise_agent/turdsize_speckle_suppression: min region area as image fraction
MIN_REGION_FRAC = 0.004
# noise_agent/mkbitmap_lowpass_foreground_smoothing: pre-smooth strength
LOWPASS_SIGMA = 1.6
# edge_agent/max_path_deviation_fidelity: boundary smoothing radius (px at
# ~600 px per 76.2 mm -> 1 px ~ 0.13 mm; radius 3 px ~ 0.4 mm <= 0.5 mm)
BOUNDARY_SMOOTH_PX = 3


def _lowpass(rgb: np.ndarray, sigma: float) -> np.ndarray:
    """mkbitmap-style lowpass: median (kills salt/pepper + pencil grain)
    then gaussian (anti-alias) per channel."""
    out = np.empty_like(rgb, dtype=np.float64)
    for c in range(3):
        ch = ndimage.median_filter(rgb[..., c], size=3)
        out[..., c] = ndimage.gaussian_filter(ch.astype(np.float64), sigma)
    return out


def _kmeans_lab(lab_pixels: np.ndarray, k: int, iters: int = 15,
                seed: int = 0):
    """Tiny k-means in Lab space. Returns (labels, centers)."""
    rng = np.random.default_rng(seed)
    n = len(lab_pixels)
    if n <= k:
        return np.arange(n), lab_pixels.astype(np.float64).copy()
    idx = rng.choice(n, k, replace=False)
    centers = lab_pixels[idx].astype(np.float64)
    labels = np.zeros(n, dtype=int)
    for _ in range(iters):
        d = np.linalg.norm(lab_pixels[:, None, :] - centers[None], axis=2)
        new = d.argmin(axis=1)
        if np.array_equal(new, labels):
            break
        labels = new
        for c in range(k):
            m = labels == c
            if m.any():
                centers[c] = lab_pixels[m].mean(axis=0)
    return labels, centers


def _merge_centers(labels: np.ndarray, centers: np.ndarray,
                   delta_e: float):
    """color_delta_e_merge_tolerance: greedily merge centers closer than
    delta_e (CIE76 in Lab), weighting by member count."""
    counts = np.bincount(labels, minlength=len(centers)).astype(np.float64)
    alive = list(range(len(centers)))
    merged = {i: i for i in alive}
    changed = True
    while changed:
        changed = False
        alive = sorted(set(merged[i] for i in merged), key=lambda i: -counts[i])
        for a_i, a in enumerate(alive):
            for b in alive[a_i + 1:]:
                if np.linalg.norm(centers[a] - centers[b]) <= delta_e:
                    w = counts[a] + counts[b]
                    centers[a] = (centers[a] * counts[a]
                                  + centers[b] * counts[b]) / max(w, 1)
                    counts[a] = w
                    counts[b] = 0
                    for k_, v in merged.items():
                        if v == b:
                            merged[k_] = a
                    changed = True
            if changed:
                break
    new_labels = np.array([merged[l] for l in labels])
    return new_labels, centers


def solidify(rgb: np.ndarray, fg_mask: np.ndarray,
             max_colors: int = MAX_COLORS,
             delta_e_merge: float = DELTA_E_MERGE,
             min_region_frac: float = MIN_REGION_FRAC,
             lowpass_sigma: float = LOWPASS_SIGMA,
             boundary_smooth_px: int = BOUNDARY_SMOOTH_PX):
    """Posterize the foreground into <= max_colors SOLID flat regions.

    Returns (regions, poster):
      regions: [(rgb_tuple, mask_bool), ...] back-to-front (stacked layering),
               pairwise disjoint, union == cleaned fg silhouette.
      poster:  uint8 RGB image, regions painted flat on white.
    """
    h, w = fg_mask.shape
    smooth = _lowpass(rgb, lowpass_sigma)                      # lowpass note
    lab = skcolor.rgb2lab(np.clip(smooth, 0, 255) / 255.0)

    fg = morphology.remove_small_holes(
        fg_mask, area_threshold=int(0.02 * h * w))             # solid silhouette
    fg = morphology.remove_small_objects(
        fg, min_size=max(32, int(min_region_frac * h * w)))    # turdsize note

    coords = np.argwhere(fg)
    if len(coords) < 50:
        return [], np.full((h, w, 3), 255, dtype=np.uint8)
    px_lab = lab[fg]

    # Perceptual clustering (hsl/Lab note) with headroom, then delta-E merge.
    k0 = min(max_colors + 3, max(2, len(np.unique(
        (px_lab // 8).astype(int), axis=0))))
    sub = px_lab
    if len(sub) > 60000:
        sel = np.random.default_rng(0).choice(len(sub), 60000, replace=False)
        sub = sub[sel]
    _, centers = _kmeans_lab(sub, k0)
    d = np.linalg.norm(px_lab[:, None, :] - centers[None], axis=2)
    labels = d.argmin(axis=1)
    labels, centers = _merge_centers(labels, centers, delta_e_merge)

    # Enforce the thread budget: keep the max_colors most-populous centers,
    # reassign the rest to their nearest survivor (max_thread_color_budget).
    ids, counts = np.unique(labels, return_counts=True)
    keep = ids[np.argsort(-counts)][:max_colors]
    if len(ids) > len(keep):
        for i in ids:
            if i not in keep:
                near = keep[np.argmin(np.linalg.norm(
                    centers[keep] - centers[i], axis=1))]
                labels[labels == i] = near
        ids = keep

    # Per-color masks -> smooth solid shapes, no overlaps.
    label_map = np.full((h, w), -1, dtype=int)
    label_map[fg] = labels
    disk = morphology.disk(boundary_smooth_px)                 # <=0.5mm note
    small = morphology.disk(1)
    min_area = max(48, int(min_region_frac * h * w))
    cleaned = np.full((h, w), -1, dtype=int)
    order = []
    for i in ids:
        m = label_map == i
        m = morphology.binary_opening(m, small)                # shave fringe
        m = morphology.binary_closing(m, disk)                 # smooth boundary
        m = morphology.remove_small_objects(m, min_size=min_area)  # turdsize
        m = morphology.remove_small_holes(m, area_threshold=min_area)
        if not m.any():
            continue
        cleaned[m & fg] = i
        order.append(i)
    if not order:
        return [], np.full((h, w, 3), 255, dtype=np.uint8)

    # Unclaimed fg pixels (speckle homes, shaved fringes, cleanup casualties)
    # -> nearest surviving region, so the union stays SOLID with no pinholes.
    unclaimed = fg & (cleaned < 0)
    if unclaimed.any():
        _, (ir, ic) = ndimage.distance_transform_edt(
            cleaned < 0, return_indices=True)
        cleaned[unclaimed] = cleaned[ir[unclaimed], ic[unclaimed]]

    # Final region list: measured mean color per region from the ORIGINAL
    # (unsmoothed) pixels, back-to-front by area (stacked layering note).
    regions = []
    for i in order:
        m = cleaned == i
        if m.sum() < min_area:
            cleaned[m] = -2  # tiny leftover -> absorbed below
            continue
        mean = rgb[m].mean(axis=0)
        regions.append((tuple(int(v) for v in mean), m))
    leftover = cleaned == -2
    if leftover.any() and regions:
        _, (ir, ic) = ndimage.distance_transform_edt(
            leftover, return_indices=True)
        for idx, (col, m) in enumerate(regions):
            add = leftover & m[ir, ic]
            if add.any():
                regions[idx] = (col, m | add)
    regions.sort(key=lambda r: -int(r[1].sum()))               # stacked order

    poster = np.full((h, w, 3), 255, dtype=np.uint8)
    for col, m in regions:
        poster[m] = col
    return regions, poster


def solidify_file(in_path: str, out_path: str, **kw) -> str:
    """Posterize an image file -> flat solid-color PNG (white background).
    Foreground extraction reuses digitizer.remove_background (highpass +
    luminance-valley cutoff notes live there)."""
    from PIL import Image
    import digitizer
    rgb, fg_mask, _method = digitizer.remove_background(in_path)
    _regions, poster = solidify(rgb, fg_mask, **kw)
    Image.fromarray(poster).save(out_path)
    return out_path


if __name__ == "__main__":
    import sys
    print(solidify_file(sys.argv[1], sys.argv[2]))
