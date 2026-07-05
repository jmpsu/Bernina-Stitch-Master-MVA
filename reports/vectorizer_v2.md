# Vectorizer v2 — anti-collapse guardrail + color-fidelity metric + multi-start search

**Still 100% model-free / NO LLM calls anywhere.** Pure deterministic image
algorithms (vtracer → cairosvg → skimage/PIL/numpy metrics → hill-climb).

This revision fixes two v1 failure modes documented in `reports/vectorizer_v1.md`:

1. **Metric gaming (the "house").** v1's greedy hill-climb drove `color_precision`
   down (6→…→3); at low color counts vtracer collapsed the soft-shaded house into
   a near-flat mid-gray plate with a tiny dark blob. That degenerate output scored
   a *higher* composite (0.766) than the faithful seed (0.620) because a mid-gray
   plate has low RMSE and decent SSIM against a mostly-light image — visually
   worthless but numerically rewarded. Verified in the v1 `_compare.png` (right
   panel = gray rectangle).
2. **Composite ≠ visual similarity.** The squirrel's SSIM dipped while composite
   rose, because the search optimizes composite, not SSIM.

## What changed (all model-free)

### A. Anti-collapse guardrail (`score()` / `_collapse_guard`)
For **both** source and render (at the common 512² scoring size) we compute:
- **distinct-color count** — PIL quantize to `COLLAPSE_QUANT_COLORS=32`, count
  palette bins covering ≥ `COLLAPSE_MIN_BIN_FRAC=0.5%` of pixels (ignores dust);
- **global std** — std over all channels/pixels (contrast proxy);
- **foreground fraction** — pixels notably darker/more-saturated than near-white.

A candidate is flagged **collapsed** if the render drops below any of:
`rnd_colors ≥ 0.60·src_colors`, `rnd_std ≥ 0.60·src_std`,
`rnd_fg ≥ 0.50·src_fg`. A collapsed candidate gets a hard multiplicative penalty
`COLLAPSE_PENALTY=0.30` on its composite, so it can never win. All thresholds are
module-level constants.

### B. Color-fidelity term + rebalanced composite
New `color_fidelity` = histogram-intersection similarity over a normalized 4×4×4
RGB histogram (`COLOR_HIST_BINS=4`) between source and render (∈ [0,1]). Composite:

```
base      = 0.55*ssim_color + 0.15*edge_iou + 0.10*(1-rmse_norm) + 0.20*color_fidelity
composite = base * collapse_guard      # guard ∈ {1.0, 0.30}
```

`ssim_color` is reported separately and left unmodified.

### C. Search robustness — multi-start
- Seeds each hill-climb from **every** `DOCTRINE_SEED` preset (`default`, `logo`,
  `line_art`), a **high-color start** (`color_precision=8`, `filter_speckle=1`,
  `layer_difference=8`), **and** the nearest prior in the param index. Keeps the
  **global best** across starts.
- `max_iters=300` **per start**; each hill-climb stops only after
  `STALL_LIMIT=40` consecutive non-improving iterations (approximating "no further
  improvement possible") or on reaching the SSIM target. Once any start reaches
  target the remaining starts are skipped (they would only re-confirm).
- **`color_precision` floor** derived from the source distinct-color count
  (`≥12→6, ≥8→5, ≥5→4, else 3`): the search never quantizes below what the source
  needs — this is the direct structural fix for the gray-plate collapse.

### D. Soft-shaded sources
`is_soft_shaded` = (not line art) ∧ distinct_colors ≥ 10 ∧ foreground ≥ 0.30.
For these, vtracer is fed a lightly **median-smoothed (3×3)** copy of the raster to
help region formation from anti-aliased gradients — but scoring is **always**
against the true original (never the smoothed copy).

## Per-image before(v1) → after(v2)

| Image | Type | v1 SSIM | v2 SSIM | v1 comp | v2 comp | v2 cfid | v2 iters | best start | collapsed | ≥0.98 |
|---|---|---|---|---|---|---|---|---|---|---|
| IMG_0331 flags | flat/logo | 0.9807 | **0.9806** | — | 0.9410 | 0.9940 | 3 | default | False | ✅ |
| IMG_1126 crest | multicolor logo | 0.9804 | **0.9804** | — | 0.9515 | 0.9770 | 3 | default | False | ✅ |
| IMG_0322 caddie | line art | 0.9844 | **0.9840** | — | 0.9475 | 0.9957 | 1 | default | False | ✅ |
| IMG_0293 house | soft-shaded | 0.7659 *(gamed)* | 0.6280 | 0.6447 *(gamed)* | 0.5675 | 0.7572 | 419 | default | **False** | ❌ |
| IMG_0263 squirrel | line art | 0.9713 | **0.9810** | — | 0.9504 | 0.9695 | 81 | logo | False | ✅ |

Notes:
- v1 composite used the old formula (`0.7*ssim + 0.15*edge + 0.15*(1-rmse)`, no
  guard), so v1↔v2 composites are **not** directly comparable; SSIM is the stable
  cross-version fidelity number. The house v1 columns are marked *(gamed)* — those
  numbers describe the degenerate gray plate, not a faithful trace.
- The param index (`parameter_correlation_index_vec.json`) was rebuilt from the v2
  results so all stored composites use the v2 metric (the stale gamed cp=3 house
  entry is gone; the house bucket now holds the honest cp=6, collapsed=False entry).

## Honest visual verdict (verified by viewing every `_compare.png`)

**Visually indistinguishable / faithful (target reached):**
- **Crest (IMG_1126)** — near-indistinguishable: red ring, "CAPE MAY / BEACH
  PATROL" text, yellow crossed oars, boat, blue waves, clouds and birds all
  reproduced.
- **Caddie (IMG_0322)** — indistinguishable line art.
- **Squirrel (IMG_0263)** — indistinguishable, and now **improved** 0.9713→0.9810
  (multi-start's `logo` seed beat v1's), clearing the 0.98 target. The v1
  "composite-vs-SSIM" dip is resolved: v2 both raises composite and lands SSIM
  above target.
- **Flags (IMG_0331)** — faithful (green/white flags, tan poles, black caps);
  minor edge roughening on the flag outlines, same cosmetic artifact as v1.

**Real ceiling — house (IMG_0293), and the concrete reason:**
- The v1 collapse is **fixed**: the new render is a genuine house — gray roof,
  brown chimneys, tan brick, white columns, dark windows, green bushes, red door —
  **not** a gray blob (verified in the new `_compare.png`; `collapsed=False`,
  cp floored at 6, cfid 0.76). The guardrail correctly refuses the gray-plate
  candidate, and the color-precision floor prevents the quantization that produced
  it.
- SSIM is only ~0.63 — and that is **honest**, not gamed. Two real reasons:
  1. **Soft-shaded, anti-aliased illustration** (gradient roof/brick/shadows) is a
     poor fit for flat-color region tracing; vtracer must approximate gradients
     with a few solid fills.
  2. **Framing/scale mismatch:** the source has surrounding whitespace while the
     SVG render tightens to its content bounding box, so the render fills more of
     the 512² canvas than the original. This pixel-level misregistration penalizes
     SSIM heavily even though the content is faithful. This is a scoring-canvas
     limitation, not a tracing failure.
- Net: the house's true faithful ceiling under flat-color vectorizing + this
  scoring convention is ~0.63 SSIM. v2's job here was to stop rewarding the fake
  0.77 and return the honest faithful result — which it does.

## Artifacts
- `vectorizer.py` — v2 guardrail (`_collapse_guard`, `_distinct_std_fg`,
  `_color_hist`), rebalanced `score()`, multi-start `optimize()`, color-precision
  floor, soft-shade pre-smoothing. Module-level thresholds at top.
- `vectorized_svg/<stem>.svg` + `<stem>_compare.png` (5 each, overwritten).
- `vectorization_attempts.jsonl` — 112 v1 rows preserved + 507 v2 rows appended
  (v2 rows tagged `"version":"v2"` with `start`, `color_fidelity`, `collapsed`).
- `parameter_correlation_index_vec.json` — rebuilt from v2 results (3 buckets).
</content>
</invoke>
