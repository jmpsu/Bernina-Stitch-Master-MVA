# Iteration 3 Report

- Timestamp: `2026-07-04T05:28:53.062077+00:00`
- Artifacts measured: **8**
- **OVERALL_SCORE: 0.5127**

## Sub-scores

| Dimension | Score | Original wt | Renorm wt | Note |
|---|---|---|---|---|
| visual_similarity | null | 0.40 | dropped | UNAVAILABLE: requires reference raster images in reference_images/ (none present this iteration). Not fabricated; marked null and weight renormalized. |
| topology_quality | 0.6667 | 0.25 | 0.4167 | mean over 3 SVGs of validity*node-per-path-band score |
| embroidery_suitability | 0.0160 | 0.20 | 0.3333 | mean over 5 PES of clamp(safe_len_frac - 1.5*short - 2*long - min(trims_per_1000/50,0.3),0,1); bbox density NOT used |
| performance | 0.8777 | 0.10 | 0.1667 | 1 - median_total_runtime(0.2447s)/budget(2.0s) over 5 runs [min=0.2374s median=0.2447s p95=0.4216s] |
| code_reliability | 1.0000 | 0.05 | 0.0833 | 8/8 files measured without error |

### Renormalization

Original weights summed to 1.00 including visual_similarity=0.40. visual_similarity is null (no reference images), so its weight was dropped and the remaining weights (topology_quality=0.25, embroidery_suitability=0.20, performance=0.10, code_reliability=0.05) were divided by their sum 0.60 to renormalize to 1.0. Renormalized weights: topology_quality=0.4167, embroidery_suitability=0.3333, performance=0.1667, code_reliability=0.0833.

### Performance timing variance (median-of-N)

Performance is scored from the MEDIAN total runtime over 5 runs, not a single run, so sub-second jitter on this trivial (~0.2s) workload no longer swamps real quality changes.

| runs | min (s) | median (s) | p95 (s) | all runs (s) |
|---|---|---|---|---|
| 5 | 0.237356 | 0.244658 | 0.421615 | 0.465269, 0.247002, 0.237356, 0.244658, 0.237397 |

## Comparison vs iteration 2 (Phase 6)

- Previous OVERALL_SCORE: **0.512292**
- Current OVERALL_SCORE: **0.512722**
- Delta: **+0.000430** (improved)

| Dimension | Previous | Current | Delta |
|---|---|---|---|
| visual_similarity | null | null | null |
| topology_quality | 0.666667 | 0.666667 | +0.000000 |
| embroidery_suitability | 0.015998 | 0.015998 | +0.000000 |
| performance | 0.875089 | 0.877671 | +0.002582 |
| code_reliability | 1.000000 | 1.000000 | +0.000000 |

### vs iteration 1 baseline

- Baseline (iteration 1) OVERALL_SCORE: **0.514432**
- Current OVERALL_SCORE: **0.512722**
- Delta vs baseline: **-0.001710** (below baseline)

## SVG metrics

| File | valid | paths | nodes | groups | elements | bytes | runtime_s |
|---|---|---|---|---|---|---|---|
| coastal_objects_all.svg | True | 21 | 53653 | 2 | 30 | 1002190 | 0.020413 |
| drink_trace.svg | True | 21 | 271 | 2 | 35 | 21674 | 0.000554 |
| drink_v2.svg | True | 6 | 99 | 2 | 19 | 16472 | 0.000348 |

## PES metrics

| File | valid | stitches | trims | colors | W mm | H mm | avg st mm | p50 mm | p95 mm | short% | long% | safe% | trims/1k | density/cm2 (info) | runtime_s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| basket_7scans.pes | True | 11359 | 94 | 6 | 30.4 | 29.0 | 1.0887 | 0.7 | 3.0 | 0.3018 | 0.0 | 0.6982 | 8.2754 | 1288.453 | 0.020344 |
| basket_small.pes | True | 6597 | 102 | 13 | 30.2 | 28.8 | 0.8023 | 0.5 | 2.0 | 0.4429 | 0.0 | 0.5571 | 15.4616 | 758.485 | 0.012582 |
| drink.pes | True | 4736 | 6 | 6 | 12.4 | 23.8 | 0.883 | 0.4243 | 2.8 | 0.5113 | 0.0 | 0.4887 | 1.2669 | 1604.771 | 0.008474 |
| drink_v2.pes | True | 1561 | 5 | 6 | 12.2 | 23.8 | 0.7788 | 0.4243 | 2.3022 | 0.5235 | 0.0 | 0.4765 | 3.2031 | 537.608 | 0.002892 |
| summer_coastal-icons.pes | True | 88710 | 645 | 21 | 371.6 | 68.0 | 1.2781 | 0.7 | 3.0 | 0.377 | 0.0 | 0.623 | 7.2709 | 351.065 | 0.175429 |

## Deferred / Limitations

- **visual_similarity** (SSIM / RMSE / edge-overlap) requires reference raster images in `reference_images/`. None are present this iteration, so this dimension is null and excluded from the weighted score via renormalization. No SSIM value was invented.
- **embroidery_suitability** no longer uses the bbox stitch-density band [40,120] st/cm2 (iteration 1). That signal conflated small densely-filled motifs with unsewable ones and pinned the score to 0.0. It is replaced by a composite over the real sewn-stitch-length distribution (safe/short/long fractions plus a capped trim-rate penalty). `stitch_density_per_cm2` is still reported but is INFORMATIONAL only.
