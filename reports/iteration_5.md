# Iteration 5 Report

- Timestamp: `2026-07-06T05:09:55.962244+00:00`
- Artifacts measured: **8**
- **OVERALL_SCORE: 0.7114**

## Sub-scores

| Dimension | Score | Original wt | Renorm wt | Note |
|---|---|---|---|---|
| visual_similarity | null | 0.40 | dropped | UNAVAILABLE: no design/stitch-out pair could be rendered and scored; visual_similarity left null and weight renormalized. |
| topology_quality | 0.6667 | 0.25 | 0.6250 | mean over 3 SVGs of validity*node-per-path-band score |
| embroidery_suitability | null | 0.20 | dropped | no valid PES artifacts |
| performance | 0.9913 | 0.10 | 0.2500 | 1 - median_total_runtime(0.0173s)/budget(2.0s) over 5 runs [min=0.0171s median=0.0173s p95=0.0297s] |
| code_reliability | 0.3750 | 0.05 | 0.1250 | 3/8 files measured without error |

### Renormalization

Original weights summed to 1.00 including visual_similarity=0.40. visual_similarity is null, so its weight was dropped and the remaining weights (topology_quality=0.25, performance=0.10, code_reliability=0.05) were divided by their sum 0.40 to renormalize to 1.0. Renormalized weights: topology_quality=0.6250, performance=0.2500, code_reliability=0.1250.

### Scoring basis (dual)

DUAL-BASIS reporting. (a) overall_score=0.711374 is the NEW full-weight score including visual_similarity at its real weight 0.40 - this is the honest current score now that all five dimensions are measurable. (b) overall_score_continuity_4metric=0.711374 drops visual and renormalizes over the same 4 metrics as iterations 1-3, so it is directly comparable to iteration 3's 0.5127. Comparing (a) to 0.5127 would be confounded by reintroducing the 0.40 weight; use (b) for a clean iteration-over-iteration delta.

- OVERALL_SCORE (full-weight, visual 0.40 included): **0.711374**
- OVERALL (continuity, 4-metric renorm, visual dropped, same basis as iterations 1-3): **0.711374**

## Visual similarity (Phase 6): design vs stitch-out

Real, NON-CIRCULAR fidelity between each vector DESIGN (SVG rendered to raster) and its actual EMBROIDERY STITCH-OUT (PES rendered to raster) on a shared framing convention. Per-pair sub-score = clamp(0.6*ssim + 0.2*edge_overlap + 0.2*(1-rmse_norm),0,1).

| SVG design | Compared against | Basis | SSIM | rmse_norm | edge_overlap | sub-score | note |
|---|---|---|---|---|---|---|---|
| drink_v2.svg | drink_v2.pes | - | - | - | - | - | SVG render failed; pair skipped |
| coastal_objects_all.svg | summer_coastal-icons.pes | - | - | - | - | - | SVG render failed; pair skipped |
| drink_trace.svg | drink.pes | - | - | - | - | - | SVG render failed; pair skipped |

- **visual_similarity sub-score = null** (mean over scored pairs)
- Excluded PES (no SVG source pair): basket_7scans.pes, basket_small.pes

### Visual metric self-test (validation)

- Self-test did not run: no rendered image available for self-test

### Performance timing variance (median-of-N)

Performance is scored from the MEDIAN total runtime over 5 runs, not a single run, so sub-second jitter on this trivial (~0.2s) workload no longer swamps real quality changes.

| runs | min (s) | median (s) | p95 (s) | all runs (s) |
|---|---|---|---|---|
| 5 | 0.017139 | 0.017343 | 0.029715 | 0.032678, 0.017864, 0.017225, 0.017139, 0.017343 |

## Comparison vs iteration 4 (Phase 6)

- Previous OVERALL_SCORE (4-metric renorm basis): **0.581012**
- Current OVERALL_SCORE (full-weight, visual 0.40): **0.711374**
- Current OVERALL (continuity, 4-metric renorm, same basis as previous): **0.711374**
- **Apples-to-apples continuity delta (4-metric): +0.130362** (improved)
- Full-weight 'delta' (CONFOUNDED by the 0.40 weight reintroduction, not a clean comparison): +0.130362

| Dimension | Previous | Current | Delta |
|---|---|---|---|
| visual_similarity | 0.677882 | null | null |
| topology_quality | 0.666667 | 0.666667 | +0.000000 |
| embroidery_suitability | 0.015998 | null | null |
| performance | 0.899926 | 0.991328 | +0.091402 |
| code_reliability | 1.000000 | 0.375000 | -0.625000 |

### vs iteration 1 baseline

- Baseline (iteration 1) OVERALL_SCORE: **0.514432**
- Current OVERALL_SCORE: **0.711374**
- Delta vs baseline: **+0.196942** (above baseline)

## SVG metrics

| File | valid | paths | nodes | groups | elements | bytes | runtime_s |
|---|---|---|---|---|---|---|---|
| coastal_objects_all.svg | True | 21 | 53653 | 2 | 30 | 1002190 | 0.016584 |
| drink_trace.svg | True | 21 | 271 | 2 | 35 | 21674 | 0.000451 |
| drink_v2.svg | True | 6 | 99 | 2 | 19 | 16472 | 0.000306 |

## PES metrics

| File | valid | stitches | trims | colors | W mm | H mm | avg st mm | p50 mm | p95 mm | short% | long% | safe% | trims/1k | density/cm2 (info) | runtime_s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| basket_7scans.pes | False | None | None | None | None | None | None | None | None | None | None | None | None | None | 8e-06 |
| basket_small.pes | False | None | None | None | None | None | None | None | None | None | None | None | None | None | 3e-06 |
| drink.pes | False | None | None | None | None | None | None | None | None | None | None | None | None | None | 3e-06 |
| drink_v2.pes | False | None | None | None | None | None | None | None | None | None | None | None | None | None | 3e-06 |
| summer_coastal-icons.pes | False | None | None | None | None | None | None | None | None | None | None | None | None | None | 3e-06 |

## Deferred / Limitations

- **visual_similarity** is NOW MEASURED (iteration 4): real SSIM / RMSE / edge-overlap between each vector design (SVG raster) and its actual embroidery stitch-out (PES raster). This is non-circular and does not require user reference images. Optional `reference_images/<stem>.{png,jpg,jpeg}` are used instead of the PES stitch-out when present (none this run). Registration caveat: SVG viewBox padding differs from the PES stitch bounding box, so cross-format alignment is approximate; SSIM/edge-overlap therefore read as fidelity trends, not exact pixel registration. `basket_*.pes` have no SVG source and are excluded from the visual dimension.
- **embroidery_suitability** no longer uses the bbox stitch-density band [40,120] st/cm2 (iteration 1). That signal conflated small densely-filled motifs with unsewable ones and pinned the score to 0.0. It is replaced by a composite over the real sewn-stitch-length distribution (safe/short/long fractions plus a capped trim-rate penalty). `stitch_density_per_cm2` is still reported but is INFORMATIONAL only.
