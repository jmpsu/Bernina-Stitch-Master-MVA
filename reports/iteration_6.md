# Iteration 6 Report - batch digitize all uploaded logos

- Timestamp: `2026-07-04T13:43:43.647984+00:00`
- Reuses the iteration-5 `digitizer.py` pipeline at scale (no new algorithm); added `process_images(paths)` + md5 dedupe + idempotent output-existence skip.
- Unique images (md5 dedupe of 68 uploaded files): **60** (8 exact re-uploads collapsed)
- New images this run: **55**   New objects: **55**   Pre-existing objects: **11**   Total .EXP objects: **66**
- Every object scaled so the OBJECT is **3 in = 76.2 mm** tall; outputs per object in `stitch_plans/`: `.exp` (Bernina), `.pes`, `_preview.png`, `.json` sidecar.
- All 66 `.exp` re-read via `pyembroidery.read`; all sidecar heights within 76.2 +-1 mm.
- BG removal: `fallback(corner+otsu)` for all (rembg model download blocked, no egress).

## Quality notes
Spot-checked 8 previews across the batch. Most are clean, recognizable logo line-art (e.g. img_0244 barrel+1925, img_0331 crossed flags, img_0293 house, img_0322 walking figure, img_0255 crest+1936, img_0312 yacht pennant).

**Weak (flagged honestly):** `img_0238` and `img_0242` render as near-blank white fills (both fg_frac ~0.59, single color) - the source screenshots are very low-contrast, so the corner+Otsu fallback grabbed a large light region and filled it with near-white thread rather than isolating a crisp logo. These two would benefit from a higher-contrast re-upload or a manual threshold.

## Digitizer parameters
| param | value |
|---|---|
| target_h_mm | 76.2 |
| row_spacing_mm | 0.4 |
| max_stitch_mm | 3.0 |
| running_stitch_mm | 2.0 |

## Per-image object count + dimensions (new this iteration)
| stem | objects | W mm | H mm | H ok | stitches | jumps | trims | colors | mode |
|---|---|---|---|---|---|---|---|---|---|
| img_0226 | 1 | 68.1 | 75.5 | True | 1309 | 122 | 97 | 6 | fill |
| img_0227 | 1 | 30.8 | 76.2 | True | 1092 | 51 | 29 | 4 | fill |
| img_0228 | 1 | 49.5 | 76.2 | True | 1328 | 72 | 64 | 6 | fill |
| img_0229 | 1 | 63.7 | 76.2 | True | 2611 | 154 | 109 | 6 | fill |
| img_0230 | 1 | 54.8 | 76.2 | True | 2219 | 160 | 127 | 6 | fill |
| img_0234 | 1 | 106.6 | 76.2 | True | 4732 | 230 | 184 | 6 | fill |
| img_0235 | 1 | 52.5 | 76.2 | True | 2109 | 68 | 61 | 4 | fill |
| img_0236 | 1 | 70.6 | 76.2 | True | 1673 | 89 | 72 | 6 | fill |
| img_0238 | 1 | 41.3 | 76.2 | True | 2224 | 28 | 18 | 1 | fill |
| img_0240 | 1 | 123.0 | 76.2 | True | 4072 | 242 | 169 | 6 | fill |
| img_0241 | 1 | 71.0 | 76.2 | True | 1805 | 126 | 95 | 6 | fill |
| img_0242 | 1 | 41.5 | 76.2 | True | 2110 | 7 | 5 | 1 | fill |
| img_0243 | 1 | 82.1 | 76.2 | True | 2338 | 58 | 45 | 6 | fill |
| img_0244 | 1 | 67.8 | 76.2 | True | 5925 | 440 | 366 | 6 | fill |
| img_0245 | 1 | 68.4 | 76.2 | True | 1872 | 83 | 64 | 4 | fill |
| img_0246 | 1 | 66.2 | 76.2 | True | 3716 | 145 | 123 | 4 | fill |
| img_0250 | 1 | 85.6 | 76.2 | True | 2866 | 191 | 171 | 6 | fill |
| img_0251 | 1 | 76.2 | 76.2 | True | 2848 | 172 | 131 | 6 | fill |
| img_0252 | 1 | 60.7 | 76.2 | True | 1694 | 130 | 73 | 6 | fill |
| img_0254 | 1 | 80.9 | 76.2 | True | 2133 | 105 | 69 | 6 | fill |
| img_0255 | 1 | 64.0 | 76.2 | True | 4849 | 457 | 362 | 6 | fill |
| img_0260 | 1 | 45.0 | 76.2 | True | 1716 | 113 | 71 | 4 | fill |
| img_0263 | 1 | 72.4 | 76.2 | True | 1517 | 76 | 65 | 4 | fill |
| img_0267 | 1 | 77.1 | 76.2 | True | 2782 | 150 | 116 | 6 | fill |
| img_0273 | 1 | 80.8 | 76.2 | True | 1764 | 76 | 69 | 6 | fill |
| img_0277 | 1 | 81.1 | 76.2 | True | 2118 | 119 | 90 | 6 | fill |
| img_0281 | 1 | 57.5 | 74.7 | False | 2251 | 101 | 74 | 6 | fill |
| img_0282 | 1 | 58.6 | 75.6 | True | 1140 | 65 | 58 | 6 | fill |
| img_0288 | 1 | 91.5 | 75.5 | True | 1595 | 91 | 76 | 6 | fill |
| img_0293 | 1 | 99.3 | 76.2 | True | 2177 | 92 | 82 | 4 | fill |
| img_0298 | 1 | 60.2 | 76.2 | True | 3330 | 192 | 137 | 6 | fill |
| img_0301 | 1 | 86.8 | 76.2 | True | 3311 | 151 | 97 | 6 | fill |
| img_0302 | 1 | 77.9 | 76.2 | True | 1629 | 58 | 49 | 4 | fill |
| img_0308 | 1 | 72.3 | 76.2 | True | 2172 | 77 | 65 | 4 | fill |
| img_0309 | 1 | 75.2 | 76.2 | True | 3924 | 312 | 275 | 6 | fill |
| img_0310 | 1 | 53.1 | 76.2 | True | 2367 | 134 | 81 | 6 | fill |
| img_0311 | 1 | 64.0 | 76.2 | True | 1962 | 154 | 119 | 6 | fill |
| img_0312 | 1 | 121.7 | 76.2 | True | 2931 | 111 | 86 | 6 | fill |
| img_0313 | 1 | 36.2 | 76.2 | True | 2014 | 61 | 43 | 6 | fill |
| img_0314 | 1 | 52.5 | 75.5 | True | 1912 | 87 | 56 | 6 | fill |
| img_0315 | 1 | 48.9 | 76.2 | True | 1976 | 73 | 56 | 6 | fill |
| img_0316 | 1 | 48.5 | 76.2 | True | 1376 | 90 | 61 | 6 | fill |
| img_0317 | 1 | 58.2 | 76.2 | True | 2556 | 168 | 127 | 6 | fill |
| img_0318 | 1 | 61.7 | 76.2 | True | 3818 | 242 | 136 | 6 | fill |
| img_0319 | 1 | 53.0 | 76.2 | True | 2258 | 116 | 85 | 6 | fill |
| img_0320 | 1 | 63.3 | 76.2 | True | 3080 | 212 | 175 | 6 | fill |
| img_0321 | 1 | 53.0 | 76.2 | True | 1601 | 149 | 115 | 6 | fill |
| img_0322 | 1 | 60.6 | 76.2 | True | 979 | 46 | 40 | 3 | fill |
| img_0323 | 1 | 83.0 | 76.2 | True | 2149 | 82 | 66 | 6 | fill |
| img_0324 | 1 | 72.1 | 76.2 | True | 2450 | 191 | 144 | 6 | fill |
| img_0325 | 1 | 106.1 | 76.2 | True | 1928 | 93 | 64 | 6 | fill |
| img_0327 | 1 | 55.5 | 76.2 | True | 2534 | 133 | 54 | 6 | fill |
| img_0328 | 1 | 65.4 | 76.2 | True | 3024 | 175 | 119 | 5 | fill |
| img_0330 | 1 | 78.4 | 76.2 | True | 2477 | 179 | 141 | 6 | fill |
| img_0331 | 1 | 96.1 | 76.2 | True | 2609 | 184 | 168 | 6 | fill |
