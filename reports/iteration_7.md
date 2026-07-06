# Iteration 7 Report

- Timestamp: `2026-07-06T05:12:03.787385+00:00`
- Artifacts measured: **8**
- **OVERALL_SCORE: 0.5808**

## Sub-scores

| Dimension | Score | Original wt | Renorm wt | Note |
|---|---|---|---|---|
| visual_similarity | 0.6779 | 0.40 | 0.4000 | mean over 3 matched pairs of clamp(0.6*ssim + 0.2*edge_overlap + 0.2*(1-rmse_norm),0,1); design(SVG raster) vs stitch-out(PES raster) fidelity, non-circular. Self-test PASSED. |
| topology_quality | 0.6667 | 0.25 | 0.2500 | mean over 3 SVGs of validity*node-per-path-band score |
| embroidery_suitability | 0.0160 | 0.20 | 0.2000 | mean over 5 PES of clamp(safe_len_frac - 1.5*short - 2*long - min(trims_per_1000/50,0.3),0,1); bbox density NOT used |
| performance | 0.8980 | 0.10 | 0.1000 | 1 - median_total_runtime(0.2040s)/budget(2.0s) over 5 runs [min=0.1999s median=0.2040s p95=0.2075s] |
| code_reliability | 1.0000 | 0.05 | 0.0500 | 8/8 files measured without error |

### Renormalization

visual_similarity is AVAILABLE this iteration (real design-vs-stitch-out fidelity), so NO weight is dropped and the FULL weights.json weights are used unchanged (they already sum to 1.00). Weights: visual_similarity=0.40, topology_quality=0.25, embroidery_suitability=0.20, performance=0.10, code_reliability=0.05.

### Scoring basis (dual)

DUAL-BASIS reporting. (a) overall_score=0.580817 is the NEW full-weight score including visual_similarity at its real weight 0.40 - this is the honest current score now that all five dimensions are measurable. (b) overall_score_continuity_4metric=0.516107 drops visual and renormalizes over the same 4 metrics as iterations 1-3, so it is directly comparable to iteration 3's 0.5127. Comparing (a) to 0.5127 would be confounded by reintroducing the 0.40 weight; use (b) for a clean iteration-over-iteration delta.

- OVERALL_SCORE (full-weight, visual 0.40 included): **0.580817**
- OVERALL (continuity, 4-metric renorm, visual dropped, same basis as iterations 1-3): **0.516107**

## Visual similarity (Phase 6): design vs stitch-out

Real, NON-CIRCULAR fidelity between each vector DESIGN (SVG rendered to raster) and its actual EMBROIDERY STITCH-OUT (PES rendered to raster) on a shared framing convention. Per-pair sub-score = clamp(0.6*ssim + 0.2*edge_overlap + 0.2*(1-rmse_norm),0,1).

| SVG design | Compared against | Basis | SSIM | rmse_norm | edge_overlap | sub-score | note |
|---|---|---|---|---|---|---|---|
| drink_v2.svg | drink_v2.pes | svg_vs_pes | 0.777640 | 0.262180 | 0.060929 | 0.626334 | scored (svg_vs_pes) |
| coastal_objects_all.svg | summer_coastal-icons.pes | svg_vs_pes | 0.910099 | 0.164669 | 0.412078 | 0.795541 | scored (svg_vs_pes) |
| drink_trace.svg | drink.pes | svg_vs_pes | 0.761027 | 0.295047 | 0.070820 | 0.611771 | scored (svg_vs_pes) |

- **visual_similarity sub-score = 0.677882** (mean over scored pairs)
- Excluded PES (no SVG source pair): basket_7scans.pes, basket_small.pes

### Visual metric self-test (validation)

| case | ssim | rmse_norm | edge_overlap | expectation | ok |
|---|---|---|---|---|---|
| identity (image vs itself) | 1.000000 | 0.000000 | 1.000000 | ssim=1, rmse=0, edge=1 | True |
| degraded (Gaussian blur r=4) | 0.962805 | 0.051673 | 0.305030 | ssim<1 | True |

- Self-test **PASSED**.

### Performance timing variance (median-of-N)

Performance is scored from the MEDIAN total runtime over 5 runs, not a single run, so sub-second jitter on this trivial (~0.2s) workload no longer swamps real quality changes.

| runs | min (s) | median (s) | p95 (s) | all runs (s) |
|---|---|---|---|---|
| 5 | 0.199895 | 0.204040 | 0.207484 | 0.204668, 0.202587, 0.204040, 0.208188, 0.199895 |

## Comparison vs iteration 6 (Phase 6)

- Previous OVERALL_SCORE (4-metric renorm basis): **0.516617**
- Current OVERALL_SCORE (full-weight, visual 0.40): **0.580817**
- Current OVERALL (continuity, 4-metric renorm, same basis as previous): **0.516107**
- **Apples-to-apples continuity delta (4-metric): -0.000510** (not improved)
- Full-weight 'delta' (CONFOUNDED by the 0.40 weight reintroduction, not a clean comparison): +0.064200

BASIS CHANGE: iteration 7 reintroduces visual_similarity at weight 0.40, so the primary OVERALL_SCORE (0.580817) is on a NEW full-weight basis and is NOT directly comparable to the previous 4-metric score 0.516617. The apples-to-apples continuity delta (4-metric, visual dropped) is -0.000510; the full-weight 'delta' +0.064200 is confounded by the weight change and is reported only for completeness.

| Dimension | Previous | Current | Delta |
|---|---|---|---|
| visual_similarity | null | 0.677882 | null |
| topology_quality | 0.666667 | 0.666667 | +0.000000 |
| embroidery_suitability | 0.015998 | 0.015998 | +0.000000 |
| performance | 0.901036 | 0.897980 | -0.003056 |
| code_reliability | 1.000000 | 1.000000 | +0.000000 |

### vs iteration 1 baseline

- Baseline (iteration 1) OVERALL_SCORE: **0.514432**
- Current OVERALL_SCORE: **0.580817**
- Delta vs baseline: **+0.066385** (above baseline)

## SVG metrics

| File | valid | paths | nodes | groups | elements | bytes | runtime_s |
|---|---|---|---|---|---|---|---|
| coastal_objects_all.svg | True | 21 | 53653 | 2 | 30 | 1002190 | 0.017852 |
| drink_trace.svg | True | 21 | 271 | 2 | 35 | 21674 | 0.000541 |
| drink_v2.svg | True | 6 | 99 | 2 | 19 | 16472 | 0.000288 |

## PES metrics

| File | valid | stitches | trims | colors | W mm | H mm | avg st mm | p50 mm | p95 mm | short% | long% | safe% | trims/1k | density/cm2 (info) | runtime_s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| basket_7scans.pes | True | 11359 | 94 | 6 | 30.4 | 29.0 | 1.0887 | 0.7 | 3.0 | 0.3018 | 0.0 | 0.6982 | 8.2754 | 1288.453 | 0.017316 |
| basket_small.pes | True | 6597 | 102 | 13 | 30.2 | 28.8 | 0.8023 | 0.5 | 2.0 | 0.4429 | 0.0 | 0.5571 | 15.4616 | 758.485 | 0.009904 |
| drink.pes | True | 4736 | 6 | 6 | 12.4 | 23.8 | 0.883 | 0.4243 | 2.8 | 0.5113 | 0.0 | 0.4887 | 1.2669 | 1604.771 | 0.006854 |
| drink_v2.pes | True | 1561 | 5 | 6 | 12.2 | 23.8 | 0.7788 | 0.4243 | 2.3022 | 0.5235 | 0.0 | 0.4765 | 3.2031 | 537.608 | 0.002362 |
| summer_coastal-icons.pes | True | 88710 | 645 | 21 | 371.6 | 68.0 | 1.2781 | 0.7 | 3.0 | 0.377 | 0.0 | 0.623 | 7.2709 | 351.065 | 0.149073 |

## Deferred / Limitations

- **visual_similarity** is NOW MEASURED (iteration 4): real SSIM / RMSE / edge-overlap between each vector design (SVG raster) and its actual embroidery stitch-out (PES raster). This is non-circular and does not require user reference images. Optional `reference_images/<stem>.{png,jpg,jpeg}` are used instead of the PES stitch-out when present (none this run). Registration caveat: SVG viewBox padding differs from the PES stitch bounding box, so cross-format alignment is approximate; SSIM/edge-overlap therefore read as fidelity trends, not exact pixel registration. `basket_*.pes` have no SVG source and are excluded from the visual dimension.
- **embroidery_suitability** no longer uses the bbox stitch-density band [40,120] st/cm2 (iteration 1). That signal conflated small densely-filled motifs with unsewable ones and pinned the score to 0.0. It is replaced by a composite over the real sewn-stitch-length distribution (safe/short/long fractions plus a capped trim-rate penalty). `stitch_density_per_cm2` is still reported but is INFORMATIONAL only.
