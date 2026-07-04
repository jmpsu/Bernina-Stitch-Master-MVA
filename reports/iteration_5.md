# Iteration 5 Report - image -> Bernina B700 digitizer

- Timestamp: `2026-07-04T13:30:11.238399+00:00`
- Capability added: raster image -> embroidery stitch plan (`digitizer.py`)
- Images processed: **5**   Objects digitized: **11**
- Every object scaled so the OBJECT is **3 in = 76.2 mm** tall (pyembroidery units = 0.1 mm)
- Outputs per object in `stitch_plans/`: `.exp` (Bernina, write_exp), `.pes` (write_pes), `_preview.png`, `.json` sidecar

## Pipeline
1. **Background removal** - tries `rembg` first; model download is blocked here (no egress) so it falls back to a no-network method: corner-sampled background-color key + Otsu brightness split (handles light-on-dark navy AND dark-on-light paper) + saturation term for colored fills + **Sobel edge-magnitude term** for faint pencil outlines, then morphological close/open + hole fill.
2. **Object separation** - single designs union all non-speck connected components into ONE object (disconnected skull / two-piece bikini / crest stay one object); wide strips (aspect > 1.8) split by vertical-whitespace valleys in the column-density profile into SEPARATE objects (each strip -> 4 objects).
3. **Digitize** - crop to bbox, scale bbox height -> 762 units; k-means color quantize (K=1 line art up to 6 color); per color region -> running stitch along contours (~2.0 mm) for thin/line shapes, boustrophedon scanline fill (row 0.4 mm, max 3.0 mm) + running-stitch border for solid regions; assemble EmbPattern with color_change + threadlist(region mean RGB) + end().

### CRITICAL FIX (why the prior run stalled)
The pale **oyster shell (gray)** and **cocktail glass (pale-orange outline)** were previously dropped as background because their color is too close to the paper. Adding a **Sobel edge-magnitude term** to the foreground detector captures the faint pencil outlines, and per-object hole-filling turns the outlined shapes into solid fillable regions. Both objects are now digitized and render as recognizable stitch-outs (confirmed by preview inspection).

## Digitizer parameters
| param | value |
|---|---|
| target_h_mm | 76.2 |
| row_spacing_mm | 0.4 |
| max_stitch_mm | 3.0 |
| running_stitch_mm | 2.0 |

## Per-image background method + object count
| image | bg method | objects |
|---|---|---|
| skull_moon_rose | fallback(corner+otsu) | 1 |
| cape_may_crest | fallback(corner+otsu) | 1 |
| bikini | fallback(corner+otsu) | 1 |
| seafood_strip | fallback(corner+otsu) | 4 |
| beach_strip | fallback(corner+otsu) | 4 |

## Per-object stitch plans
| image | object | W mm | H mm | H ok (~76.2) | stitches | jumps | trims | colors | mode |
|---|---|---|---|---|---|---|---|---|---|
| skull_moon_rose | design | 51.0 | 76.2 | True | 1444 | 136 | 103 | 3 | fill |
| cape_may_crest | crest | 63.4 | 76.2 | True | 4177 | 265 | 219 | 6 | fill |
| bikini | bikini | 39.3 | 76.2 | True | 1628 | 146 | 92 | 3 | fill |
| seafood_strip | basket | 76.2 | 76.2 | True | 1705 | 85 | 75 | 3 | fill |
| seafood_strip | cocktail | 62.9 | 76.2 | True | 791 | 29 | 23 | 2 | fill |
| seafood_strip | lobster | 44.1 | 76.2 | True | 1253 | 38 | 28 | 2 | fill |
| seafood_strip | shell | 42.4 | 76.2 | True | 649 | 15 | 12 | 2 | fill |
| beach_strip | cabana | 48.0 | 76.2 | True | 3270 | 358 | 246 | 2 | fill |
| beach_strip | crab | 59.2 | 76.2 | True | 2707 | 353 | 237 | 2 | fill |
| beach_strip | lighthouse | 36.8 | 76.2 | True | 1740 | 163 | 112 | 3 | fill |
| beach_strip | surfboard | 31.6 | 76.2 | True | 1281 | 119 | 93 | 2 | fill |

## Preview-quality assessment (visual inspection of each stitch-out PNG)
| image | object | assessment |
|---|---|---|
| skull_moon_rose | design | Good - arched tombstone frame with beaded border, moon and rose/dagger motif all legible. |
| cape_may_crest | crest | Excellent - 'CAPE MAY BEACH PATROL' lettering, life-ring, crossed oars and boat/waves clearly read. |
| bikini | bikini | Good - two-piece (top + bottom) with floral fill pattern clearly recognizable. |
| seafood_strip | basket | Good - handled basket with flowers; interior texture a bit busy but shape reads. |
| seafood_strip | cocktail | Good (CRITICAL FIX) - pale-orange cocktail glass recovered: goblet bowl, stem, lemon slice and ice cubes all legible. |
| seafood_strip | lobster | Good - claws, body, walking legs and tail all present and recognizable. |
| seafood_strip | shell | Good (CRITICAL FIX) - pale gray oyster shell outline recovered by Sobel edge term; shape reads as an oyster shell. |
| beach_strip | cabana | Good - beach cabana/hut with pennant flag on top; wood-plank texture reads. |
| beach_strip | crab | Good - crab body/shell with two front claws and side legs recognizable. |
| beach_strip | lighthouse | Good - tapered lighthouse tower with lantern room / gallery railing on top. |
| beach_strip | surfboard | Good - pointed surfboard silhouette with center stringer line. |

## Verification
- `python3 digitizer.py` ran clean end-to-end (rembg download blocked -> fallback used for all 5 images).
- All 11 preview PNGs opened and visually confirmed to resemble the source objects.
- All 11 `.exp` files re-read with `pyembroidery.read` without error.
- All 11 sidecars report `height_mm == 76.20` and `height_ok == true` (within +-1 mm of the 76.2 mm target).

## Honest limitations / still-weak
- rembg model could not be downloaded (no network egress); the no-network fallback is used for every image. Results are good but a real matting model could clean up interior texture.
- The **basket** interior and **crab/cabana** bodies pick up pencil-shading texture as extra small fill fragments (busy interiors). Shapes are clearly recognizable but not as clean as the line-art pieces.
- Fill of large solid regions is a straight-scanline (0-degree) boustrophedon; no angle optimization per region. Adequate for a 3 in motif but not production-tuned underlay/angles.