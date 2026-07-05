# Vectorizer v1 — Model-free library-driven iterative raster→SVG

**Pipeline (NO LLM / model calls anywhere — pure deterministic algorithms):**

```
raster --(vtracer)--> SVG --(cairosvg)--> raster --(skimage SSIM / Sobel edge IoU / RMSE)-->
composite score --(coordinate-descent hill-climb over vtracer params)--> repeat
```

- **Tracer:** `vtracer` **0.6.15** (pip), Rust raster→SVG. Binding
  `vtracer.convert_image_to_svg_py(image_path, out_path, colormode, hierarchical,
  mode, filter_speckle, color_precision, layer_difference, corner_threshold,
  length_threshold, max_iterations, splice_threshold, path_precision)`.
- **Score:** `composite = 0.7*ssim_color + 0.15*edge_iou + 0.15*(1-rmse_norm)`,
  `ssim_color` = skimage `structural_similarity(channel_axis=-1, data_range=255)`
  on 512² white-canvas renders (same framing convention as `metrics._fit_gray_to_canvas`).
- **Search:** greedy coordinate-descent / hill-climb. Perturb one factor per step,
  trace→render→score, ACCEPT iff composite improves, else revert. Stop on
  `ssim>=target (0.98)`, K-factor stall, or `max_iters=200`. **Every** attempt is
  appended to `vectorization_attempts.jsonl` (112 attempts this run).
- **Cross-image transfer:** winning params are stored in
  `parameter_correlation_index_vec.json` keyed by a feature bucket
  (`kind|color-band|edge-band`). A new image is seeded from the nearest prior
  (weighted feature distance) if one is close, else from the doctrine preset.

## Doctrine seed params (extracted, with source)

Skimmed read-only worktree of `origin/mila/embiz-agent-system`:
- `directives/repo_adapted_embiz_doctrine/potrace_EMBIZ_ADAPTED_DOCTRINE.md`
- `directives/repo_adapted_embiz_doctrine/inkscape_EMBIZ_ADAPTED_DOCTRINE.md`
- `directives/repo_adapted_embiz_doctrine/inkstitch_EMBIZ_ADAPTED_DOCTRINE.md`

**Honest note on the doctrine:** it is potrace/inkscape-oriented prose. It has
concrete numbers for **potrace** (a different tracer) and color constraints from
inkscape, but **no vtracer-native parameter tables**. Concrete numbers extracted:

| Source | Parameter | Values | Meaning |
|---|---|---|---|
| potrace doctrine (Parameter Constraints + `potrace_defaults.conf`) | `turdsize` | default 2, logo 5, text 2 (range 2–100) | noise / speckle removal |
| potrace | `alphamax` | default 1.0, logo 0.8, text 1.2 (0–1.3334) | corner sharpness |
| potrace | `opttolerance` | default 0.2, logo 0.3, text 0.1 (0–1.0) | curve smoothness / point count |
| potrace | quality gate | 300 DPI logos / 600 DPI text; 60 s trace limit; SVG must parse + contain `<path>` | — |
| inkscape doctrine (Color Palette Mgmt + quality_thresholds) | `max_thread_colors` | 15 | distinct-color / layering budget |
| inkscape | `max_color_delta_e` | 5.0 | color-merge tolerance |

**Conceptual mapping potrace/inkscape → vtracer** (used to build `DOCTRINE_SEED`
in `vectorizer.py`): turdsize→`filter_speckle`; alphamax→`corner_threshold`
(higher alphamax = smoother ⇒ lower vtracer corner_threshold); opttolerance→
`path_precision`/`length_threshold`/`splice_threshold`; 15-color cap→`color_precision`
ceiling; logo/text presets→`logo`/`line_art` seeds.

Resulting `DOCTRINE_SEED` presets (vtracer space):

| preset | color_precision | filter_speckle | corner_threshold | path_precision | mode | layer_difference |
|---|---|---|---|---|---|---|
| default  | 6 | 4 | 60 | 8 | spline | 16 |
| logo     | 7 | 5 | 50 | 6 | spline | 16 |
| line_art | 4 | 2 | 70 | 8 | spline | 16 |

## Per-image convergence (target SSIM ≥ 0.98)

| Image | Type | Seed source | Start SSIM | Best SSIM | Iters | ≥0.98 |
|---|---|---|---|---|---|---|
| IMG_0331 (crossed flags) | logo/flat | DOCTRINE_SEED[line_art] | 0.9750 | **0.9807** | 15 | ✅ |
| IMG_1126 (Cape May crest, multicolor) | multicolor logo | param_index (line_art, d=2.45) | 0.9804 | **0.9804** | 1 | ✅ |
| IMG_0322 (green line-art caddie) | line art | param_index (line_art, d=0.32) | 0.9844 | **0.9844** | 1 | ✅ |
| IMG_0293 (house) | soft-shaded illustration | param_index (multicolor, d=0.32) | 0.6197 | 0.7659 | 44 | ❌ |
| IMG_0263 (squirrel "1916", tan) | line art | param_index (line_art, d=0.53) | 0.9721 | 0.9713 | 51 | ❌ |

Cross-image transfer worked: the crest and caddie reached target on the **seed
alone** (iteration 1) because they were seeded from proven line-art params — the
utilization matrix paid off.

## Visual confirmation (inspected `_compare.png`)

- **Crest (IMG_1126):** render is genuinely faithful — red ring, "CAPE MAY /
  BEACH PATROL" text, yellow crossed oars, boat, blue waves and clouds all
  reproduced. Confirms 0.98 SSIM = near-indistinguishable here.
- **Caddie (IMG_0322)** and **squirrel (IMG_0263)** line art: essentially
  indistinguishable from the originals.
- **Flags (IMG_0331):** faithful (green/white flags, tan poles); minor edge
  roughening on the flag outlines.

## Which converge to near-indistinguishable vs hit a ceiling, and why

**Converge (≥0.97, visually faithful):** clean logos / flat-color line art
(flags, crest, caddie, squirrel). These are exactly what region-based tracers are
built for — a small number of solid, well-separated colors with crisp edges. The
hill-climb needs few iterations and cross-image seeding often lands at target on
the first try.

**Hit a ceiling — house (IMG_0293), and honestly why:** the house is a
**soft-shaded, anti-aliased illustration** (gradient gray roof, tan brick,
white columns/shadows) — poorly matched to flat-color region tracing. More
importantly, this image exposed a real **blind spot in the SSIM/RMSE-weighted
composite metric**: the greedy search drove `color_precision` down 6→5→4→3, and
at cp=3 vtracer collapsed the whole image into a near-flat mid-gray field with a
tiny dark blob. That degenerate output scored *higher* composite (0.77 vs 0.62)
because a mid-gray plate has low RMSE and decent SSIM against a mostly-light
image, even though it is visually worthless (verified in the compare PNG — the
right panel is a gray rectangle). So the "ceiling" here is not that vtracer can't
trace the house; it is that (a) soft-gradient art resists flat-color vectorizing
and (b) the composite can be gamed by low-color flat fills on such images. This
is the honest failure mode to fix next (candidate guardrails, all still
model-free: reject candidates whose rendered distinct-color count or
foreground-fraction collapses relative to the source; or add a color-histogram /
LPIPS-free structural term to the composite).

The squirrel technically missed 0.98 (0.9721→0.9713): the optimizer traded a
hair of SSIM for higher edge_iou/1-rmse (it optimizes *composite*, not SSIM), so
composite rose 0.9295→0.9302 while SSIM dipped ~0.001. Visually it is already
near-indistinguishable; it is a target-threshold artifact, not a real regression.

## Artifacts

- `vectorizer.py` — pipeline + `DOCTRINE_SEED`, CLI.
- `vectorized_svg/<stem>.svg` + `<stem>_compare.png` (5 each).
- `vectorization_attempts.jsonl` — 112-row factor→result ledger.
- `parameter_correlation_index_vec.json` — cross-image utilization matrix (3 buckets).
- `requirements.txt` — vtracer added.
