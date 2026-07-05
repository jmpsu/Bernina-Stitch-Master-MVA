# Production-Run Visual Output

Per-design ruler/grid review sheets: after a design's final stitch plan
(`.exp`/`.pes`) is written, three mobile-friendly JPEGs are generated into
`production_runs/<stem>/` so the customer can review both **dimensions** and
**fidelity** at true production size from a phone (e.g. on GitHub mobile):

| File | Subject |
|------|---------|
| `1_original_on_ruler.jpg`   | Original customer raster, background removed |
| `2_svg_on_ruler.jpg`        | Generated vector (SVG) render |
| `3_stitchplan_on_ruler.jpg` | PES stitch-out render (colour) |

All three subjects are scaled to the **same true size — 3 in / 76.2 mm tall** —
and composited over the same transparent L-ruler + square-grid template, so the
three images are directly comparable and the height reads against the ruler.

## Ruler-template calibration (derived)

Measured from the clean template `assets/ruler_grid_background.png`
(IMG_0931, 704 x 1527 px, portrait):

- **Grid unit:** one white grid square = **0.25 in** (4 squares per inch).
  Grid lines were detected at **70–71 px** spacing in both axes.
- **L-ruler:** an **inch** scale on the left/bottom. Its bold number labels
  `0`/`1`/`2` sit at y = 1226 / 945 / 666 px (centres), i.e. 2 inches span
  560 px = **280 px/in**, in agreement with the grid (4 × 70.8 = 283).
- **Adopted `PIXELS_PER_INCH = 283.0`** (grid-derived; 0.25 in per square).
  A **3 in** subject therefore spans **3 × 283 = 849 px = 12 grid squares** —
  the verification target when viewing the sheets.
- **Origin (0/0 corner):** bottom-left anchor at approx **(x=155, y=1230)** —
  x just right of the vertical ruler's measuring edge, y on the 0-inch line.

The two other attached templates (IMG_0928, IMG_0929) already carry sample
patches; IMG_0931 is the clean template and is the canonical background.
The bottom-of-image *separate* horizontal ruler photographs at a different
scale (~248 px/in) and is **not** used for calibration — the grid and the
vertical L-ruler (which the grid aligns to) are authoritative.

## Layout logic (`production_layout.py`)

- `load_ruler_background()` → `(bg_rgba, pixels_per_inch, origin_xy)`.
- `compose_on_ruler(subject_rgba, target_h_in=3.0)`: crop the subject to its
  non-transparent bbox, scale so bbox height = `target_h_in * ppi`, anchor its
  **bottom-left at the ruler origin** (grows up-and-to-the-right, like the
  sample patches in IMG_0928/0929), alpha-composite over the template, return
  RGB.
- `make_production_visuals(original, svg, pes, out_dir, target_h_mm=76.2)`:
  builds each subject as RGBA and composites it.

Subject builders reuse the existing pipeline:
- **Original** → `digitizer.remove_background()` (rembg, else corner+Otsu
  fallback); the returned mask becomes the alpha channel.
- **SVG** → rasterised with cairosvg (same engine as
  `metrics.render_svg_to_gray`); its background is keyed to transparent by
  sampling the render's corner colour (handles white *and* coloured traced
  backgrounds — e.g. the crest's red field) plus near-white.
- **PES** → rendered in colour by reusing `digitizer.render_preview`, then the
  near-white preview background is keyed to transparent.

### Note on width

The template is portrait (only ~1.9 in of grid to the right of the origin).
Since the digitizer scales every design to **3 in tall**, designs wider than
~1.9 in at that height (e.g. the crest and caddie) extend past the right edge.
The **height** (the production-critical dimension) always reads exactly against
the ruler, and all three JPEGs for a design are cropped identically, so the
side-by-side fidelity comparison remains valid.

## Integration

`digitizer.generate_production_visuals(...)` is called right after
`write_outputs(...)` writes an object's `.exp`/`.pes` (in both `process_images`
and `process_all`). It looks up the matching SVG at
`vectorized_svg/<original-stem>.svg` and writes into `production_runs/<stem>/`
(single-object) or `production_runs/<stem>_<label>/` (multi-object strips).
The call is fully guarded: any failure logs and continues so visual generation
never crashes stitch-plan generation.

## Example sets generated

Generated for the five vectorizer test designs that have a complete triple
(original upload + `vectorized_svg/<stem>.svg` + `stitch_plans/*.pes`):

| Folder | Original | SVG | PES |
|--------|----------|-----|-----|
| `production_runs/flags/`    | 340931ae-IMG_0331.jpeg | 340931ae-IMG_0331.svg | img_0331_logo.pes |
| `production_runs/crest/`    | 65892eaa-IMG_1126.jpeg | 65892eaa-IMG_1126.svg | cape_may_crest_crest.pes |
| `production_runs/caddie/`   | 76ca38b2-IMG_0322.jpeg | 76ca38b2-IMG_0322.svg | img_0322_logo.pes |
| `production_runs/house/`    | 61c7ce08-IMG_0293.jpeg | 61c7ce08-IMG_0293.svg | img_0293_logo.pes |
| `production_runs/squirrel/` | 8b4ed770-IMG_0263.jpeg | 8b4ed770-IMG_0263.svg | img_0263_logo.pes |

Each folder contains all three JPEGs. Visually confirmed (crest, caddie,
squirrel, flags): backgrounds are replaced/keyed cleanly, each subject is
anchored at the 0/0 corner and spans 0 → ~3 in (≈12 grid squares) against the
vertical ruler, and all three renders per design register at the same scale.

> Customer originals are **not** committed — only the generic measurement
> template (`assets/`) and the generated review JPEGs (`production_runs/`).
