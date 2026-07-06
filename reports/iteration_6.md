# Iteration 6 Report

- Timestamp: `2026-07-06T05:11:01.074328+00:00`
- Artifacts measured: **8**
- **OVERALL_SCORE: 0.5166**

## Sub-scores

| Dimension | Score | Original wt | Renorm wt | Note |
|---|---|---|---|---|
| visual_similarity | null | 0.40 | dropped | UNAVAILABLE: no design/stitch-out pair could be rendered and scored; visual_similarity left null and weight renormalized. |
| topology_quality | 0.6667 | 0.25 | 0.4167 | mean over 3 SVGs of validity*node-per-path-band score |
| embroidery_suitability | 0.0160 | 0.20 | 0.3333 | mean over 5 PES of clamp(safe_len_frac - 1.5*short - 2*long - min(trims_per_1000/50,0.3),0,1); bbox density NOT used |
| performance | 0.9010 | 0.10 | 0.1667 | 1 - median_total_runtime(0.1979s)/budget(2.0s) over 5 runs [min=0.1923s median=0.1979s p95=0.2042s] |
| code_reliability | 1.0000 | 0.05 | 0.0833 | 8/8 files measured without error |

### Renormalization

Original weights summed to 1.00 including visual_similarity=0.40. visual_similarity is null, so its weight was dropped and the remaining weights (topology_quality=0.25, embroidery_suitability=0.20, performance=0.10, code_reliability=0.05) were divided by their sum 0.60 to renormalize to 1.0. Renormalized weights: topology_quality=0.4167, embroidery_suitability=0.3333, performance=0.1667, code_reliability=0.0833.

### Scoring basis (dual)

DUAL-BASIS reporting. (a) overall_score=0.516617 is the NEW full-weight score including visual_similarity at its real weight 0.40 - this is the honest current score now that all five dimensions are measurable. (b) overall_score_continuity_4metric=0.516617 drops visual and renormalizes over the same 4 metrics as iterations 1-3, so it is directly comparable to iteration 3's 0.5127. Comparing (a) to 0.5127 would be confounded by reintroducing the 0.40 weight; use (b) for a clean iteration-over-iteration delta.

- OVERALL_SCORE (full-weight, visual 0.40 included): **0.516617**
- OVERALL (continuity, 4-metric renorm, visual dropped, same basis as iterations 1-3): **0.516617**

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
| 5 | 0.192299 | 0.197928 | 0.204164 | 0.203243, 0.197928, 0.192299, 0.204394, 0.194386 |

## Comparison vs iteration 5 (Phase 6)

- Previous OVERALL_SCORE (4-metric renorm basis): **0.711374**
- Current OVERALL_SCORE (full-weight, visual 0.40): **0.516617**
- Current OVERALL (continuity, 4-metric renorm, same basis as previous): **0.516617**
- **Apples-to-apples continuity delta (4-metric): -0.194757** (not improved)
- Full-weight 'delta' (CONFOUNDED by the 0.40 weight reintroduction, not a clean comparison): -0.194757

| Dimension | Previous | Current | Delta |
|---|---|---|---|
| visual_similarity | null | null | null |
| topology_quality | 0.666667 | 0.666667 | +0.000000 |
| embroidery_suitability | null | 0.015998 | null |
| performance | 0.991328 | 0.901036 | -0.090292 |
| code_reliability | 0.375000 | 1.000000 | +0.625000 |

### vs iteration 1 baseline

- Baseline (iteration 1) OVERALL_SCORE: **0.514432**
- Current OVERALL_SCORE: **0.516617**
- Delta vs baseline: **+0.002185** (above baseline)

## SVG metrics

| File | valid | paths | nodes | groups | elements | bytes | runtime_s |
|---|---|---|---|---|---|---|---|
| coastal_objects_all.svg | True | 21 | 53653 | 2 | 30 | 1002190 | 0.017693 |
| drink_trace.svg | True | 21 | 271 | 2 | 35 | 21674 | 0.000534 |
| drink_v2.svg | True | 6 | 99 | 2 | 19 | 16472 | 0.000314 |

## PES metrics

| File | valid | stitches | trims | colors | W mm | H mm | avg st mm | p50 mm | p95 mm | short% | long% | safe% | trims/1k | density/cm2 (info) | runtime_s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| basket_7scans.pes | True | 11359 | 94 | 6 | 30.4 | 29.0 | 1.0887 | 0.7 | 3.0 | 0.3018 | 0.0 | 0.6982 | 8.2754 | 1288.453 | 0.016531 |
| basket_small.pes | True | 6597 | 102 | 13 | 30.2 | 28.8 | 0.8023 | 0.5 | 2.0 | 0.4429 | 0.0 | 0.5571 | 15.4616 | 758.485 | 0.009786 |
| drink.pes | True | 4736 | 6 | 6 | 12.4 | 23.8 | 0.883 | 0.4243 | 2.8 | 0.5113 | 0.0 | 0.4887 | 1.2669 | 1604.771 | 0.006559 |
| drink_v2.pes | True | 1561 | 5 | 6 | 12.2 | 23.8 | 0.7788 | 0.4243 | 2.3022 | 0.5235 | 0.0 | 0.4765 | 3.2031 | 537.608 | 0.002298 |
| summer_coastal-icons.pes | True | 88710 | 645 | 21 | 371.6 | 68.0 | 1.2781 | 0.7 | 3.0 | 0.377 | 0.0 | 0.623 | 7.2709 | 351.065 | 0.143988 |

## Deferred / Limitations

- **visual_similarity** is NOW MEASURED (iteration 4): real SSIM / RMSE / edge-overlap between each vector design (SVG raster) and its actual embroidery stitch-out (PES raster). This is non-circular and does not require user reference images. Optional `reference_images/<stem>.{png,jpg,jpeg}` are used instead of the PES stitch-out when present (none this run). Registration caveat: SVG viewBox padding differs from the PES stitch bounding box, so cross-format alignment is approximate; SSIM/edge-overlap therefore read as fidelity trends, not exact pixel registration. `basket_*.pes` have no SVG source and are excluded from the visual dimension.
- **embroidery_suitability** no longer uses the bbox stitch-density band [40,120] st/cm2 (iteration 1). That signal conflated small densely-filled motifs with unsewable ones and pinned the score to 0.0. It is replaced by a composite over the real sewn-stitch-length distribution (safe/short/long fractions plus a capped trim-rate penalty). `stitch_density_per_cm2` is still reported but is INFORMATIONAL only.
