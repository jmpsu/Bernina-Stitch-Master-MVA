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

## Ruler-template calibration (synthesized 5 in × 5 in)

Template `assets/ruler_grid_5x5.png` is **synthesized** (PIL, deterministic /
model-free) as a clean square **5 in × 5 in** measurement sheet, replacing the
earlier portrait photographed template so wide 3 in designs fit fully:

- **`PIXELS_PER_INCH = 283`** (kept consistent with the original photographed
  template's grid calibration). Canvas = 5 × 283 = **1415 × 1415 px**, white
  background.
- **Grid unit:** one square = **0.25 in** = ~70.75 px (4 squares per inch),
  a **20 × 20** grid. Light gray thin lines every 0.25 in; heavier/darker
  lines every **1 in** (every 4th line).
- **L-ruler:** an **inch** scale along the LEFT and BOTTOM edges (semi-
  transparent print-like band over the grid) with tick marks (inch + quarter-
  inch) and numeric labels **0..5** up the left and along the bottom.
- **Origin (0/0 corner):** bottom-left anchor at **(x=60, y=1355)** — the
  drawn ruler inset. Subjects are placed bottom-left at the origin and grow
  up-and-to-the-right, so both dimensions read against both ruler arms.
- A **3 in** subject spans **3 × 283 = 849 px = 12 grid squares**, leaving
  ~2 in of headroom in both width and height so even wide 3 in designs
  (crest, caddie) sit fully inside the grid.

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

The template is now a square **5 in × 5 in** canvas, so there is ~5 in of grid
in both axes from the origin. Since the digitizer scales every design to **3 in
tall**, even the widest designs (the crest and caddie, which are wider than
tall) now fit **fully** inside the grid with ~2 in of margin, reading correctly
against both ruler arms. Both dimensions read exactly against the ruler, and
all three JPEGs for a design register at the same scale/anchor.

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

Each folder contains all three JPEGs, regenerated on the 5 in × 5 in template.
Visually confirmed (crest, caddie, flags): backgrounds are replaced/keyed
cleanly, each subject is anchored at the 0/0 corner, sits **fully inside** the
5 in × 5 in grid at true 3 in tall (≈12 grid squares), and reads correctly
against both ruler arms; all three renders per design register at the same
scale. The previously-clipped wide designs (crest, caddie) now fit entirely.

> Customer originals are **not** committed — only the generic measurement
> template (`assets/`) and the generated review JPEGs (`production_runs/`).
