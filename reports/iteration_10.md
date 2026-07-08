# Iteration 10 Report

- Timestamp: `2026-07-06T06:50:02.627197+00:00`
- Artifacts measured: **83**
- **OVERALL_SCORE: 0.7327**

## Sub-scores

| Dimension | Score | Original wt | Renorm wt | Note |
|---|---|---|---|---|
| visual_similarity | 0.6779 | 0.40 | 0.4000 | mean over 3 matched pairs of clamp(0.6*ssim + 0.2*edge_overlap + 0.2*(1-rmse_norm),0,1); design(SVG raster) vs stitch-out(PES raster) fidelity, non-circular. Self-test PASSED. |
| topology_quality | 0.8267 | 0.25 | 0.2500 | mean over 8 SVGs of validity*node-per-path-band score |
| embroidery_suitability | 0.6373 | 0.20 | 0.2000 | mean over 75 PES of clamp(safe_len_frac - 1.5*short - 2*long - min(trims_per_1000/50,0.3),0,1); bbox density NOT used |
| performance | 0.7738 | 0.10 | 0.1000 | 1 - median_total_runtime(0.4524s)/budget(2.0s) over 5 runs [min=0.4511s median=0.4524s p95=0.4565s] |
| code_reliability | 1.0000 | 0.05 | 0.0500 | 83/83 files measured without error |

### Renormalization

visual_similarity is AVAILABLE this iteration (real design-vs-stitch-out fidelity), so NO weight is dropped and the FULL weights.json weights are used unchanged (they already sum to 1.00). Weights: visual_similarity=0.40, topology_quality=0.25, embroidery_suitability=0.20, performance=0.10, code_reliability=0.05.

### Scoring basis (dual)

DUAL-BASIS reporting. (a) overall_score=0.732675 is the NEW full-weight score including visual_similarity at its real weight 0.40 - this is the honest current score now that all five dimensions are measurable. (b) overall_score_continuity_4metric=0.769203 drops visual and renormalizes over the same 4 metrics as iterations 1-3, so it is directly comparable to iteration 3's 0.5127. Comparing (a) to 0.5127 would be confounded by reintroducing the 0.40 weight; use (b) for a clean iteration-over-iteration delta.

- OVERALL_SCORE (full-weight, visual 0.40 included): **0.732675**
- OVERALL (continuity, 4-metric renorm, visual dropped, same basis as iterations 1-3): **0.769203**

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
| 5 | 0.451075 | 0.452396 | 0.456450 | 0.452396, 0.451075, 0.452447, 0.457450, 0.451853 |

## Comparison vs iteration 9 (Phase 6)

- Previous OVERALL_SCORE (4-metric renorm basis): **0.694753**
- Current OVERALL_SCORE (full-weight, visual 0.40): **0.732675**
- Current OVERALL (continuity, 4-metric renorm, same basis as previous): **0.769203**
- **Apples-to-apples continuity delta (4-metric): +0.074450** (improved)
- Full-weight 'delta' (CONFOUNDED by the 0.40 weight reintroduction, not a clean comparison): +0.037922

BASIS CHANGE: iteration 10 reintroduces visual_similarity at weight 0.40, so the primary OVERALL_SCORE (0.732675) is on a NEW full-weight basis and is NOT directly comparable to the previous 4-metric score 0.694753. The apples-to-apples continuity delta (4-metric, visual dropped) is +0.074450; the full-weight 'delta' +0.037922 is confounded by the weight change and is reported only for completeness.

| Dimension | Previous | Current | Delta |
|---|---|---|---|
| visual_similarity | 0.581812 | 0.677882 | +0.096070 |
| topology_quality | 0.826727 | 0.826727 | +0.000000 |
| embroidery_suitability | 0.634830 | 0.637300 | +0.002470 |
| performance | 0.783802 | 0.773802 | -0.010000 |
| code_reliability | 1.000000 | 1.000000 | +0.000000 |

### vs iteration 1 baseline

- Baseline (iteration 1) OVERALL_SCORE: **0.514432**
- Current OVERALL_SCORE: **0.732675**
- Delta vs baseline: **+0.218243** (above baseline)

## SVG metrics

| File | valid | paths | nodes | groups | elements | bytes | runtime_s |
|---|---|---|---|---|---|---|---|
| coastal_objects_all.svg | True | 21 | 53653 | 2 | 30 | 1002190 | 0.017044 |
| drink_trace.svg | True | 21 | 271 | 2 | 35 | 21674 | 0.000476 |
| drink_v2.svg | True | 6 | 99 | 2 | 19 | 16472 | 0.000307 |
| img_0263.svg | True | 7562 | 13925 | 0 | 7563 | 672489 | 0.019285 |
| img_0293.svg | True | 43 | 909 | 0 | 44 | 8955 | 0.000309 |
| img_0322.svg | True | 162 | 3314 | 0 | 163 | 30987 | 0.000846 |
| img_0331.svg | True | 67 | 1604 | 0 | 68 | 15193 | 0.000422 |
| img_1126.svg | True | 4555 | 58056 | 0 | 4556 | 630041 | 0.016933 |

## PES metrics

| File | valid | stitches | trims | colors | W mm | H mm | avg st mm | p50 mm | p95 mm | short% | long% | safe% | trims/1k | density/cm2 (info) | runtime_s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| basket_7scans.pes | True | 11359 | 94 | 6 | 30.4 | 29.0 | 1.0887 | 0.7 | 3.0 | 0.3018 | 0.0 | 0.6982 | 8.2754 | 1288.453 | 0.016713 |
| basket_small.pes | True | 6597 | 102 | 13 | 30.2 | 28.8 | 0.8023 | 0.5 | 2.0 | 0.4429 | 0.0 | 0.5571 | 15.4616 | 758.485 | 0.009579 |
| drink.pes | True | 4736 | 6 | 6 | 12.4 | 23.8 | 0.883 | 0.4243 | 2.8 | 0.5113 | 0.0 | 0.4887 | 1.2669 | 1604.771 | 0.006679 |
| drink_v2.pes | True | 1561 | 5 | 6 | 12.2 | 23.8 | 0.7788 | 0.4243 | 2.3022 | 0.5235 | 0.0 | 0.4765 | 3.2031 | 537.608 | 0.002253 |
| summer_coastal-icons.pes | True | 88710 | 645 | 21 | 371.6 | 68.0 | 1.2781 | 0.7 | 3.0 | 0.377 | 0.0 | 0.623 | 7.2709 | 351.065 | 0.141171 |
| beach_strip_cabana.exp | True | 3270 | 246 | 2 | 48.0 | 76.1 | 2.6598 | 1.118 | 1.8358 | 0.0 | 0.0 | 1.0 | 75.2294 | 89.52 | 0.004686 |
| beach_strip_crab.exp | True | 2707 | 236 | 2 | 59.2 | 76.1 | 3.5097 | 1.3 | 1.9105 | 0.0004 | 0.0 | 0.9996 | 87.1814 | 60.087 | 0.004177 |
| beach_strip_lighthouse.exp | True | 1740 | 110 | 3 | 36.8 | 76.1 | 2.6614 | 1.562 | 1.9209 | 0.0 | 0.0 | 1.0 | 63.2184 | 62.132 | 0.002355 |
| beach_strip_surfboard.exp | True | 1281 | 93 | 2 | 31.4 | 76.1 | 3.1288 | 1.4422 | 1.9105 | 0.0 | 0.0 | 1.0 | 72.5995 | 53.609 | 0.001817 |
| bikini_bikini.exp | True | 1628 | 90 | 3 | 38.9 | 76.0 | 2.4988 | 1.456 | 1.9105 | 0.0 | 0.0 | 1.0 | 55.2826 | 55.067 | 0.002179 |
| cape_may_crest_crest.exp | True | 4177 | 214 | 6 | 63.4 | 76.1 | 3.0366 | 1.8385 | 1.9849 | 0.002 | 0.0 | 0.998 | 51.2329 | 86.575 | 0.005692 |
| coastal_objects_all_raster_logo.exp | True | 3278 | 175 | 6 | 427.3 | 76.1 | 7.7862 | 1.8439 | 2.0 | 0.0 | 0.0 | 1.0 | 53.3862 | 10.081 | 0.005579 |
| drink_trace_raster_logo.exp | True | 2521 | 68 | 4 | 64.7 | 76.0 | 2.8891 | 2.7 | 3.0 | 0.0041 | 0.0 | 0.9959 | 26.9734 | 51.269 | 0.002878 |
| drink_v2_raster_logo.exp | True | 2099 | 65 | 4 | 62.2 | 75.9 | 2.9659 | 2.7 | 3.0 | 0.0 | 0.0 | 1.0 | 30.9671 | 44.461 | 0.002411 |
| img_0226_logo.exp | True | 1309 | 92 | 6 | 67.2 | 75.3 | 3.4773 | 1.8682 | 2.0 | 0.0 | 0.0 | 1.0 | 70.2827 | 25.869 | 0.001835 |
| img_0227_logo.exp | True | 1092 | 27 | 4 | 30.8 | 76.0 | 2.3899 | 1.8788 | 2.0 | 0.0 | 0.0 | 1.0 | 24.7253 | 46.651 | 0.001348 |
| img_0228_logo.exp | True | 1328 | 59 | 6 | 49.5 | 76.0 | 3.1788 | 1.8868 | 2.0 | 0.0 | 0.0 | 1.0 | 44.4277 | 35.3 | 0.001709 |
| img_0229_logo.exp | True | 2611 | 105 | 6 | 63.7 | 76.0 | 3.1223 | 2.0 | 2.9 | 0.0114 | 0.0 | 0.9886 | 40.2145 | 53.933 | 0.003228 |
| img_0230_logo.exp | True | 2219 | 123 | 6 | 54.8 | 76.0 | 3.4879 | 1.9105 | 2.9 | 0.0272 | 0.0 | 0.9728 | 55.4304 | 53.28 | 0.002922 |
| img_0234_logo.exp | True | 4732 | 180 | 6 | 106.6 | 76.1 | 3.1542 | 1.9 | 2.0025 | 0.0018 | 0.0 | 0.9982 | 38.0389 | 58.331 | 0.006565 |
| img_0235_logo.exp | True | 2109 | 59 | 4 | 52.5 | 76.1 | 2.5324 | 1.8682 | 2.0 | 0.001 | 0.0 | 0.999 | 27.9753 | 52.788 | 0.002516 |
| img_0236_logo.exp | True | 1673 | 67 | 6 | 70.6 | 76.0 | 3.1114 | 1.9532 | 2.0 | 0.0 | 0.0 | 1.0 | 40.0478 | 31.18 | 0.002198 |
| img_0238_logo.exp | True | 2224 | 18 | 1 | 41.3 | 76.2 | 2.8522 | 2.9 | 3.0 | 0.0683 | 0.0 | 0.9317 | 8.0935 | 70.669 | 0.00236 |
| img_0240_logo.exp | True | 4072 | 164 | 6 | 123.0 | 75.9 | 3.267 | 1.9235 | 2.9 | 0.0332 | 0.0 | 0.9668 | 40.275 | 43.618 | 0.005128 |
| img_0241_logo.exp | True | 1805 | 90 | 6 | 71.0 | 76.0 | 3.0408 | 1.8385 | 2.0 | 0.0 | 0.0 | 1.0 | 49.8615 | 33.451 | 0.00235 |
| img_0242_logo.exp | True | 2110 | 5 | 1 | 41.5 | 76.2 | 2.8734 | 3.0 | 3.0 | 0.068 | 0.0 | 0.932 | 2.3697 | 66.724 | 0.002209 |
| img_0243_logo.exp | True | 2338 | 41 | 6 | 82.1 | 75.3 | 2.3248 | 1.8358 | 2.8 | 0.0518 | 0.0 | 0.9482 | 17.5364 | 37.819 | 0.002737 |
| img_0244_logo.exp | True | 5925 | 361 | 6 | 67.8 | 76.1 | 3.4269 | 1.8358 | 2.002 | 0.0015 | 0.0 | 0.9985 | 60.9283 | 114.835 | 0.008202 |
| img_0245_logo.exp | True | 1872 | 61 | 4 | 68.4 | 76.1 | 2.5546 | 1.8248 | 2.0 | 0.0 | 0.0 | 1.0 | 32.5855 | 35.964 | 0.002315 |
| img_0246_logo.exp | True | 3716 | 121 | 4 | 66.2 | 76.1 | 2.47 | 1.8358 | 2.0 | 0.0011 | 0.0 | 0.9989 | 32.5619 | 73.762 | 0.004506 |
| img_0250_logo.exp | True | 2866 | 166 | 6 | 85.6 | 76.0 | 3.462 | 1.9026 | 2.0 | 0.0 | 0.0 | 1.0 | 57.9204 | 44.054 | 0.003851 |
| img_0251_logo.exp | True | 2848 | 126 | 6 | 76.2 | 76.0 | 2.9955 | 1.7692 | 2.325 | 0.0179 | 0.0 | 0.9821 | 44.2416 | 49.178 | 0.00369 |
| img_0252_logo.exp | True | 1694 | 68 | 6 | 60.7 | 76.0 | 2.8624 | 1.8028 | 2.8 | 0.0262 | 0.0 | 0.9738 | 40.1417 | 36.721 | 0.002235 |
| img_0254_logo.exp | True | 2133 | 64 | 6 | 80.9 | 76.0 | 2.7867 | 1.8682 | 2.8 | 0.0138 | 0.0 | 0.9862 | 30.0047 | 34.692 | 0.002646 |
| img_0255_logo.exp | True | 4849 | 357 | 6 | 64.0 | 76.0 | 3.6351 | 1.8 | 2.0 | 0.0 | 0.0 | 1.0 | 73.6234 | 99.692 | 0.006997 |
| img_0260_logo.exp | True | 1716 | 68 | 4 | 45.0 | 75.9 | 2.9572 | 1.9209 | 2.9 | 0.0 | 0.0 | 1.0 | 39.627 | 50.242 | 0.002313 |
| img_0263_logo.exp | True | 1517 | 62 | 4 | 72.4 | 76.0 | 2.9349 | 1.8682 | 2.0 | 0.0 | 0.0 | 1.0 | 40.8701 | 27.57 | 0.001935 |
| img_0267_logo.exp | True | 2782 | 111 | 6 | 76.4 | 76.0 | 2.8055 | 1.7692 | 2.0 | 0.0 | 0.0 | 1.0 | 39.8994 | 47.913 | 0.003548 |
| img_0273_logo.exp | True | 1764 | 64 | 6 | 80.8 | 76.0 | 3.1731 | 1.8028 | 2.0 | 0.0 | 0.0 | 1.0 | 36.2812 | 28.726 | 0.002292 |
| img_0277_logo.exp | True | 2118 | 85 | 6 | 81.1 | 76.0 | 2.8316 | 1.8439 | 2.0 | 0.0 | 0.0 | 1.0 | 40.1322 | 34.363 | 0.002658 |
| img_0281_logo.exp | True | 2251 | 69 | 6 | 57.5 | 74.5 | 2.568 | 1.9105 | 2.0 | 0.0 | 0.0 | 1.0 | 30.653 | 52.547 | 0.002693 |
| img_0282_logo.exp | True | 1140 | 53 | 6 | 58.6 | 75.1 | 3.0981 | 1.8868 | 2.0 | 0.0 | 0.0 | 1.0 | 46.4912 | 25.904 | 0.00145 |
| img_0288_logo.exp | True | 1595 | 71 | 6 | 91.2 | 74.7 | 3.3554 | 1.8385 | 2.0 | 0.0 | 0.0 | 1.0 | 44.5141 | 23.412 | 0.002095 |
| img_0293_logo.exp | True | 2177 | 79 | 4 | 99.3 | 75.5 | 3.4532 | 2.0 | 2.0 | 0.0 | 0.0 | 1.0 | 36.2885 | 29.038 | 0.002737 |
| img_0298_logo.exp | True | 3330 | 132 | 6 | 60.2 | 76.0 | 2.8906 | 2.0 | 2.0 | 0.0 | 0.0 | 1.0 | 39.6396 | 72.784 | 0.004112 |
| img_0301_logo.exp | True | 3311 | 92 | 6 | 86.5 | 76.0 | 2.5386 | 1.8788 | 2.3 | 0.0209 | 0.0 | 0.9791 | 27.7862 | 50.365 | 0.004005 |
| img_0302_logo.exp | True | 1629 | 46 | 4 | 77.9 | 76.1 | 2.7234 | 1.8788 | 2.0 | 0.0 | 0.0 | 1.0 | 28.2382 | 27.479 | 0.001992 |
| img_0308_logo.exp | True | 2172 | 63 | 4 | 72.3 | 76.0 | 2.6962 | 1.9235 | 2.9 | 0.0153 | 0.0 | 0.9847 | 29.0055 | 39.528 | 0.002574 |
| img_0309_logo.exp | True | 3924 | 270 | 6 | 74.8 | 75.7 | 3.5796 | 1.8385 | 2.0 | 0.0 | 0.0 | 1.0 | 68.8073 | 69.3 | 0.005428 |
| img_0310_logo.exp | True | 2367 | 76 | 6 | 53.1 | 76.0 | 2.7168 | 1.9105 | 2.9 | 0.0493 | 0.0 | 0.9507 | 32.1082 | 58.653 | 0.00297 |
| img_0311_logo.exp | True | 1962 | 114 | 6 | 64.0 | 76.0 | 3.3773 | 1.7692 | 2.0 | 0.0 | 0.0 | 1.0 | 58.104 | 40.337 | 0.002714 |
| img_0312_logo.exp | True | 2931 | 81 | 6 | 121.7 | 75.9 | 2.7174 | 1.8439 | 2.3 | 0.039 | 0.0 | 0.961 | 27.6356 | 31.731 | 0.003599 |
| img_0313_logo.exp | True | 2014 | 38 | 6 | 36.2 | 76.0 | 2.1832 | 1.7205 | 2.01 | 0.022 | 0.0 | 0.978 | 18.8679 | 73.204 | 0.002416 |
| img_0314_logo.exp | True | 1912 | 51 | 6 | 52.5 | 75.3 | 2.7356 | 1.9209 | 2.9 | 0.0203 | 0.0 | 0.9797 | 26.6736 | 48.365 | 0.002266 |
| img_0315_logo.exp | True | 1976 | 52 | 6 | 48.9 | 76.0 | 2.4752 | 1.8439 | 2.0 | 0.0 | 0.0 | 1.0 | 26.3158 | 53.17 | 0.002364 |
| img_0316_logo.exp | True | 1376 | 56 | 6 | 48.5 | 76.0 | 2.6768 | 1.8439 | 2.2 | 0.0435 | 0.0 | 0.9565 | 40.6977 | 37.33 | 0.001769 |
| img_0317_logo.exp | True | 2556 | 122 | 6 | 58.2 | 76.0 | 2.9909 | 1.9026 | 2.0 | 0.0 | 0.0 | 1.0 | 47.7308 | 57.786 | 0.003277 |
| img_0318_logo.exp | True | 3818 | 131 | 6 | 61.7 | 76.0 | 2.8506 | 2.0 | 2.9 | 0.0403 | 0.0 | 0.9597 | 34.3112 | 81.421 | 0.004686 |
| img_0319_logo.exp | True | 2258 | 80 | 6 | 53.0 | 76.0 | 2.746 | 2.0 | 2.0 | 0.0005 | 0.0 | 0.9995 | 35.4296 | 56.058 | 0.002772 |
| img_0320_logo.exp | True | 3080 | 170 | 6 | 63.3 | 76.0 | 3.0722 | 1.7088 | 2.0 | 0.0 | 0.0 | 1.0 | 55.1948 | 64.023 | 0.004105 |
| img_0321_logo.exp | True | 1601 | 110 | 6 | 53.0 | 75.9 | 3.58 | 1.8788 | 2.0 | 0.0 | 0.0 | 1.0 | 68.7071 | 39.799 | 0.002266 |
| img_0322_logo.exp | True | 979 | 38 | 3 | 60.6 | 76.0 | 2.7812 | 1.8248 | 2.0 | 0.0 | 0.0 | 1.0 | 38.8151 | 21.257 | 0.001248 |
| img_0323_logo.exp | True | 2149 | 61 | 6 | 83.0 | 76.0 | 2.7708 | 1.8358 | 1.9849 | 0.0 | 0.0 | 1.0 | 28.3853 | 34.068 | 0.002669 |
| img_0324_logo.exp | True | 2450 | 139 | 6 | 72.1 | 76.0 | 3.2415 | 1.7889 | 2.0 | 0.0 | 0.0 | 1.0 | 56.7347 | 44.711 | 0.003341 |
| img_0325_logo.exp | True | 1928 | 59 | 6 | 106.1 | 76.0 | 3.1466 | 1.8868 | 2.0 | 0.0 | 0.0 | 1.0 | 30.6017 | 23.91 | 0.002462 |
| img_0327_logo.exp | True | 2534 | 49 | 6 | 55.5 | 76.0 | 2.5403 | 1.8788 | 2.8 | 0.04 | 0.0 | 0.96 | 19.337 | 60.076 | 0.003024 |
| img_0328_logo.exp | True | 3024 | 115 | 5 | 65.4 | 76.0 | 2.8845 | 2.0 | 3.0 | 0.0407 | 0.0 | 0.9593 | 38.0291 | 60.84 | 0.003666 |
| img_0330_logo.exp | True | 2477 | 136 | 6 | 78.4 | 76.0 | 3.6024 | 1.8358 | 2.0 | 0.0 | 0.0 | 1.0 | 54.9051 | 41.572 | 0.003453 |
| img_0331_logo.exp | True | 2609 | 163 | 6 | 96.1 | 76.0 | 4.425 | 1.8788 | 2.9 | 0.0078 | 0.0 | 0.9922 | 62.476 | 35.722 | 0.003693 |
| img_1126_logo.exp | True | 3577 | 268 | 6 | 63.5 | 76.1 | 3.4722 | 1.8028 | 2.0 | 0.0 | 0.0 | 1.0 | 74.9231 | 74.022 | 0.00511 |
| seafood_strip_basket.exp | True | 1705 | 73 | 3 | 76.2 | 75.9 | 2.8587 | 1.6125 | 1.9235 | 0.0 | 0.0 | 1.0 | 42.8152 | 29.48 | 0.002288 |
| seafood_strip_cocktail.exp | True | 791 | 22 | 2 | 62.9 | 75.8 | 2.3964 | 1.8439 | 2.0 | 0.0 | 0.0 | 1.0 | 27.8129 | 16.59 | 0.001018 |
| seafood_strip_lobster.exp | True | 1253 | 27 | 2 | 44.1 | 75.9 | 2.2205 | 1.6155 | 1.9416 | 0.0 | 0.0 | 1.0 | 21.5483 | 37.434 | 0.00155 |
| seafood_strip_shell.exp | True | 649 | 11 | 2 | 42.4 | 75.8 | 2.0643 | 1.7 | 1.9799 | 0.0 | 0.0 | 1.0 | 16.9492 | 20.193 | 0.000792 |
| skull_moon_rose_design.exp | True | 1444 | 101 | 3 | 51.0 | 76.1 | 3.4061 | 1.7493 | 2.0 | 0.0 | 0.0 | 1.0 | 69.9446 | 37.206 | 0.00203 |

## Deferred / Limitations

- **visual_similarity** is NOW MEASURED (iteration 4): real SSIM / RMSE / edge-overlap between each vector design (SVG raster) and its actual embroidery stitch-out (PES raster). This is non-circular and does not require user reference images. Optional `reference_images/<stem>.{png,jpg,jpeg}` are used instead of the PES stitch-out when present (none this run). Registration caveat: SVG viewBox padding differs from the PES stitch bounding box, so cross-format alignment is approximate; SSIM/edge-overlap therefore read as fidelity trends, not exact pixel registration. `basket_*.pes` have no SVG source and are excluded from the visual dimension.
- **embroidery_suitability** no longer uses the bbox stitch-density band [40,120] st/cm2 (iteration 1). That signal conflated small densely-filled motifs with unsewable ones and pinned the score to 0.0. It is replaced by a composite over the real sewn-stitch-length distribution (safe/short/long fractions plus a capped trim-rate penalty). `stitch_density_per_cm2` is still reported but is INFORMATIONAL only.
