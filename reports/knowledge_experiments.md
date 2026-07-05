# Stage-2 knowledge-correlation experiments

_Isolated-factor, regression-style test of whether each Stage-1 library-derived knowledge artifact's recommended parameter change correlates with improved vectorization quality. Deterministic, model-free: only vectorizer.trace / render_svg_rgb / score are used._

- Baseline param set: `vectorizer.DOCTRINE_SEED['default']` (color_precision=6, filter_speckle=4, corner_threshold=60, path_precision=8, layer_difference=16, splice_threshold=45, mode=spline, hierarchical=stacked, colormode=color).
- Test images (5, known behavior): flags, crest, caddie, house, squirrel.
- Target sub-metric per agent: color->color_fidelity, edge->edge_iou, curve/noise->ssim_color.
- Confidence: **validated** = mean Delta-composite > 0 and >=4/5 images improve; **weak/positive** = net positive but mixed (<4/5 improve); **neutral** = |mean Delta| <= 5e-05 (best candidate == baseline / no net effect); **refuted** = net negative. NOTE: on this already-near-optimal baseline seed the magnitudes are small (sub-0.002 composite); 'validated' here means a consistent positive DIRECTION across images, not a large win.
- Run: elapsed 0.0s, internal budget 300s, budget_hit=False. Every trial logged to `knowledge_experiments.jsonl`.

## Baseline scores

| image | composite | ssim_color | color_fidelity | edge_iou |
|---|---|---|---|---|
| flags | 0.9397 | 0.9797 | 0.9916 | 0.7056 |
| crest | 0.9497 | 0.9794 | 0.9769 | 0.7916 |
| caddie | 0.9475 | 0.9840 | 0.9957 | 0.7433 |
| house | 0.5644 | 0.6198 | 0.7650 | 0.0622 |
| squirrel | 0.9186 | 0.9709 | 0.9279 | 0.6756 |

## Ranked artifacts (isolated-factor result)

| # | agent | concept | source | param | best value | mean Delta-composite +- std | images improved | mean Delta-target | confidence | predicted | dir match |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | curve | opticurve: true Bezier optimization vs raw polygon | potrace_SOURCE_BUNDLE.md | `mode` | polygon | +0.0010 +- 0.0005 | 5/5 (100%) | +0.0005 (ssim_color) | **validated** | spline (Bezier) | no |
| 2 | edge | turnpolicy: resolving ambiguous turns in path decomposition | potrace_SOURCE_BUNDLE.md | `mode` | polygon | +0.0010 +- 0.0005 | 5/5 (100%) | +0.0037 (edge_iou) | **validated** | spline (weak/no analogue) | no |
| 3 | noise | turdsize: suppress paths below an area (speckle removal) | potrace_SOURCE_BUNDLE.md | `filter_speckle` | 1 | +0.0007 +- 0.0005 | 4/5 (80%) | +0.0002 (ssim_color) | **validated** | moderate-low 1-4 (per-artwork ~2) | yes |
| 4 | curve | alphamax corner threshold (curve vs corner decision) | potrace_SOURCE_BUNDLE.md | `corner_threshold` | 40 | +0.0004 +- 0.0003 | 5/5 (100%) | +0.0002 (ssim_color) | **validated** | lower 40-50 (smoother, curve bias) | yes |
| 5 | curve | Curve segment joining and splice length (secondary opttolerance analogue) | potrace_EMBIZ_ADAPTED_DOCTRINE.md | `splice_threshold` | 30 | +0.0002 +- 0.0001 | 5/5 (100%) | +0.0001 (ssim_color) | **validated** | hold/raise 45-60 | no |
| 6 | color | Stacked vs cutout color layering topology | inkscape_EMBIZ_ADAPTED_DOCTRINE.md | `hierarchical` | cutout | +0.0001 +- 0.0073 | 3/5 (60%) | -0.0000 (color_fidelity) | **weak/positive** | stacked | no |
| 7 | color | Perceptual color-merge tolerance (delta_e <= 5.0) | inkscape_EMBIZ_ADAPTED_DOCTRINE.md | `layer_difference` | 16 | +0.0000 +- 0.0000 | 0/5 (0%) | +0.0000 (color_fidelity) | **neutral** | moderate 8-16 (not min 4) | yes |
| 8 | color | HSL-distance nearest-color matching for palette mapping | inkscape_EMBIZ_ADAPTED_DOCTRINE.md | `colormode` | color | +0.0000 +- 0.0000 | 0/5 (0%) | +0.0000 (color_fidelity) | **neutral** | color (only option) | yes |
| 9 | color | Bounded color palette (max 15 thread colors) | inkscape_EMBIZ_ADAPTED_DOCTRINE.md | `color_precision` | 6 | +0.0000 +- 0.0000 | 0/5 (0%) | +0.0000 (color_fidelity) | **neutral** | moderate 5-6 (<=15 colors) | yes |
| 10 | curve | opttolerance curve-optimization tolerance (node count vs fit) | potrace_SOURCE_BUNDLE.md | `path_precision` | 5 | +0.0000 +- 0.0000 | 0/5 (0%) | +0.0000 (ssim_color) | **neutral** | higher 7-8 (more faithful) | no |
| 11 | edge | Corner detection threshold for edge/corner fidelity | potrace_EMBIZ_ADAPTED_DOCTRINE.md | `corner_threshold` | 60 | +0.0000 +- 0.0000 | 0/5 (0%) | +0.0000 (edge_iou) | **neutral** | higher (increase) -> 90 | no |
| 12 | edge | max path deviation <= 0.5mm (geometric edge fidelity target) | inkscape_EMBIZ_ADAPTED_DOCTRINE.md | `path_precision` | 6 | +0.0000 +- 0.0000 | 0/5 (0%) | +0.0000 (edge_iou) | **neutral** | increase toward 8 | no |
| 13 | edge | Node/element count as a path-topology quality target | inkstitch_EMBIZ_ADAPTED_DOCTRINE.md | `path_precision` | 5 | +0.0000 +- 0.0000 | 0/5 (0%) | +0.0000 (edge_iou) | **neutral** | decrease -> 4 (fewer nodes, negligible loss) | no |
| 14 | noise | mkbitmap lowpass filter: smoothing foreground detail before tracing | potrace_SOURCE_BUNDLE.md | `source_presmooth` | none | +0.0000 +- 0.0000 | 0/5 (0%) | +0.0000 (ssim_color) | **neutral** | presmooth helps noisy/AA; none on clean | yes |

## Summary

**VALIDATED as improving quality (5):**
- curve / opticurve: true Bezier optimization vs raw polygon: `mode=polygon` (Delta +0.0010 +- 0.0005, 100% improved, potrace_SOURCE_BUNDLE.md)
- edge / turnpolicy: resolving ambiguous turns in path decomposition: `mode=polygon` (Delta +0.0010 +- 0.0005, 100% improved, potrace_SOURCE_BUNDLE.md)
- noise / turdsize: suppress paths below an area (speckle removal): `filter_speckle=1` (Delta +0.0007 +- 0.0005, 80% improved, potrace_SOURCE_BUNDLE.md)
- curve / alphamax corner threshold (curve vs corner decision): `corner_threshold=40` (Delta +0.0004 +- 0.0003, 100% improved, potrace_SOURCE_BUNDLE.md)
- curve / Curve segment joining and splice length (secondary opttolerance analogue): `splice_threshold=30` (Delta +0.0002 +- 0.0001, 100% improved, potrace_EMBIZ_ADAPTED_DOCTRINE.md)

**WEAK / net-positive (1):**
- color / Stacked vs cutout color layering topology: `hierarchical=cutout` (Delta +0.0001 +- 0.0073, 60% improved, inkscape_EMBIZ_ADAPTED_DOCTRINE.md)

**NEUTRAL (~0 net effect over the baseline seed) (8):**
- color / Perceptual color-merge tolerance (delta_e <= 5.0): `layer_difference=16` (Delta +0.0000 +- 0.0000, 0% improved, inkscape_EMBIZ_ADAPTED_DOCTRINE.md)
- color / HSL-distance nearest-color matching for palette mapping: `colormode=color` (Delta +0.0000 +- 0.0000, 0% improved, inkscape_EMBIZ_ADAPTED_DOCTRINE.md)
- color / Bounded color palette (max 15 thread colors): `color_precision=6` (Delta +0.0000 +- 0.0000, 0% improved, inkscape_EMBIZ_ADAPTED_DOCTRINE.md)
- curve / opttolerance curve-optimization tolerance (node count vs fit): `path_precision=5` (Delta +0.0000 +- 0.0000, 0% improved, potrace_SOURCE_BUNDLE.md)
- edge / Corner detection threshold for edge/corner fidelity: `corner_threshold=60` (Delta +0.0000 +- 0.0000, 0% improved, potrace_EMBIZ_ADAPTED_DOCTRINE.md)
- edge / max path deviation <= 0.5mm (geometric edge fidelity target): `path_precision=6` (Delta +0.0000 +- 0.0000, 0% improved, inkscape_EMBIZ_ADAPTED_DOCTRINE.md)
- edge / Node/element count as a path-topology quality target: `path_precision=5` (Delta +0.0000 +- 0.0000, 0% improved, inkstitch_EMBIZ_ADAPTED_DOCTRINE.md)
- noise / mkbitmap lowpass filter: smoothing foreground detail before tracing: `source_presmooth=none` (Delta +0.0000 +- 0.0000, 0% improved, potrace_SOURCE_BUNDLE.md)

**REFUTED (net negative) (0):**
- (none)

**NOT-YET-TESTABLE (2):**
- noise / blacklevel / bilevel cutoff: threshold choice preserves silhouette (`source_threshold_level`, potrace_SOURCE_BUNDLE.md): vectorizer traces in colormode='color' (multi-layer), not a bilevel/blacklevel cutoff; no grey-cutoff parameter is exposed to isolate.
- noise / mkbitmap highpass filter: evening out background gradients (`source_background_flatten`, potrace_SOURCE_BUNDLE.md): vectorizer exposes no highpass background-flatten stage; _presmoothed_source only does median smoothing, not gradient removal. No pipeline hook to isolate.

## Predicted-vs-observed direction

Of 14 tested hypotheses with a directional prediction, **6 matched** the observed best direction and 8 did not (see `dir match` column). A mismatch means the library's predicted parameter bias did not produce the best score on this particular 5-image set -- honest evidence the artifact's numeric guidance is artwork-class dependent rather than universal.

## Per-image vs universal wins

Per-candidate per-image deltas are in the ledger. The baseline seed is already near-optimal for these clean logo/line-art images (composites ~0.94-0.99), so most isolated single-factor changes move composite by <0.01. Where an artifact helps, the `best_per_image_dcomp` field in the ledger shows whether the gain is universal (all 5) or concentrated on one class (e.g. a color/soft-shade knob helping the house/crest but flat on line art like caddie/squirrel).

- **opticurve: true Bezier optimization vs raw polygon** (`mode=polygon`): flags +0.0019, crest +0.0007, caddie +0.0010, house +0.0003, squirrel +0.0010
- **turnpolicy: resolving ambiguous turns in path decomposition** (`mode=polygon`): flags +0.0019, crest +0.0007, caddie +0.0010, house +0.0003, squirrel +0.0010
- **turdsize: suppress paths below an area (speckle removal)** (`filter_speckle=1`): flags +0.0014, crest +0.0008, caddie +0.0005, house -0.0001, squirrel +0.0010
- **alphamax corner threshold (curve vs corner decision)** (`corner_threshold=40`): flags +0.0007, crest +0.0005, caddie +0.0001, house +0.0001, squirrel +0.0008
- **Curve segment joining and splice length (secondary opttolerance analogue)** (`splice_threshold=30`): flags +0.0003, crest +0.0001, caddie +0.0003, house +0.0002, squirrel +0.0000
- **Stacked vs cutout color layering topology** (`hierarchical=cutout`): flags +0.0086, crest -0.0134, caddie -0.0001, house +0.0025, squirrel +0.0027
- **Perceptual color-merge tolerance (delta_e <= 5.0)** (`layer_difference=16`): flags +0.0000, crest +0.0000, caddie +0.0000, house +0.0000, squirrel +0.0000
- **HSL-distance nearest-color matching for palette mapping** (`colormode=color`): flags +0.0000, crest +0.0000, caddie +0.0000, house +0.0000, squirrel +0.0000
- **Bounded color palette (max 15 thread colors)** (`color_precision=6`): flags +0.0000, crest +0.0000, caddie +0.0000, house +0.0000, squirrel +0.0000
- **opttolerance curve-optimization tolerance (node count vs fit)** (`path_precision=5`): flags +0.0000, crest +0.0000, caddie +0.0000, house +0.0000, squirrel +0.0000
- **Corner detection threshold for edge/corner fidelity** (`corner_threshold=60`): flags +0.0000, crest +0.0000, caddie +0.0000, house +0.0000, squirrel +0.0000
- **max path deviation <= 0.5mm (geometric edge fidelity target)** (`path_precision=6`): flags +0.0000, crest +0.0000, caddie +0.0000, house +0.0000, squirrel +0.0000
- **Node/element count as a path-topology quality target** (`path_precision=5`): flags +0.0000, crest +0.0000, caddie +0.0000, house +0.0000, squirrel +0.0000
- **mkbitmap lowpass filter: smoothing foreground detail before tracing** (`source_presmooth=none`): flags +0.0000, crest +0.0000, caddie +0.0000, house +0.0000, squirrel +0.0000
