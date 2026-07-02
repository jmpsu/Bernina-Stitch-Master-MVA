# Iteration 1 Report

- Timestamp: `2026-06-29T07:14:43.890048+00:00`
- Artifacts measured: **8**
- **OVERALL_SCORE: 0.5144**

## Sub-scores

| Dimension | Score | Original wt | Renorm wt | Note |
|---|---|---|---|---|
| visual_similarity | null | 0.40 | dropped | UNAVAILABLE: requires reference raster images in reference_images/ (none present this iteration). Not fabricated; marked null and weight renormalized. |
| topology_quality | 0.6667 | 0.25 | 0.4167 | mean over 3 SVGs of validity*node-per-path-band score |
| embroidery_suitability | 0.0000 | 0.20 | 0.3333 | mean over 5 PES of density-in-[40,120]st/cm2 score |
| performance | 0.9199 | 0.10 | 0.1667 | 1 - total_runtime(0.1601s)/budget(2.0s) |
| code_reliability | 1.0000 | 0.05 | 0.0833 | 8/8 files measured without error |

### Renormalization

Original weights summed to 1.00 including visual_similarity=0.40. visual_similarity is null (no reference images), so its weight was dropped and the remaining weights (topology_quality=0.25, embroidery_suitability=0.20, performance=0.10, code_reliability=0.05) were divided by their sum 0.60 to renormalize to 1.0. Renormalized weights: topology_quality=0.4167, embroidery_suitability=0.3333, performance=0.1667, code_reliability=0.0833.

## SVG metrics

| File | valid | paths | nodes | groups | elements | bytes | runtime_s |
|---|---|---|---|---|---|---|---|
| coastal_objects_all.svg | True | 21 | 53653 | 2 | 30 | 1002190 | 0.016523 |
| drink_trace.svg | True | 21 | 271 | 2 | 35 | 21674 | 0.000479 |
| drink_v2.svg | True | 6 | 99 | 2 | 19 | 16472 | 0.00029 |

## PES metrics

| File | valid | stitches | jumps | trims | colorchg | colors | W mm | H mm | travel mm | avg st mm | density/cm2 | bytes | runtime_s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| basket_7scans.pes | True | 11359 | 96 | 94 | 5 | 6 | 30.4 | 29.0 | 12366.161 | 1.0887 | 1288.453 | 73086 | 0.013539 |
| basket_small.pes | True | 6597 | 104 | 102 | 12 | 13 | 30.2 | 28.8 | 5292.92 | 0.8023 | 758.485 | 46351 | 0.007196 |
| drink.pes | True | 4736 | 8 | 6 | 5 | 6 | 12.4 | 23.8 | 4181.773 | 0.883 | 1604.771 | 30888 | 0.005399 |
| drink_v2.pes | True | 1561 | 7 | 5 | 5 | 6 | 12.2 | 23.8 | 1215.66 | 0.7788 | 537.608 | 11810 | 0.001748 |
| summer_coastal-icons.pes | True | 88710 | 647 | 645 | 20 | 21 | 371.6 | 68.0 | 113378.322 | 1.2781 | 351.065 | 555805 | 0.114976 |

## Deferred / Limitations

- **visual_similarity** (SSIM / RMSE / edge-overlap) requires reference raster images in `reference_images/`. None are present this iteration, so this dimension is null and excluded from the weighted score via renormalization. No SSIM value was invented.
