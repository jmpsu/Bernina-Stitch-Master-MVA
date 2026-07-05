# Vectorizer v3 — content-crop scoring registration (fair SSIM) + fair re-measurement

**Still 100% model-free / NO LLM calls anywhere.** Pure deterministic image
algorithms (vtracer → cairosvg → skimage/PIL/numpy metrics → hill-climb).

v3 changes the **scoring** step only, to test the v2 hypothesis that the house's
low SSIM was partly a *registration* artifact (source raster carries whitespace
margins while the SVG render tightens to its content bounding box, so the render
fills more of the 512² canvas → pixel-level misregistration that penalizes SSIM
even for a faithful trace). This report re-measures every image **fairly** under
the new metric, without re-optimizing (to avoid the non-convergent house search
exhausting the budget).

## The registration fix (scoring change)

`_crop_to_content(rgb, thresh)` crops an RGB array to the bounding box of its
non-white content (a pixel is "white" only when its **minimum** channel ≥ `thresh`).
`score()` now, before computing any metric:

1. content-crops **both** the source and the render (`CROP_CONTENT_THRESH = 240`);
2. re-fits **both** into a common 512² canvas, aspect preserved + centered
   (`_fit_rgb_to_canvas`, same convention used everywhere else — no shape
   distortion);
3. then computes `ssim_color / edge_iou / rmse / color_fidelity` and the v2
   composite (anti-collapse guard + `color_fidelity` term all retained unchanged).

`CROP_CONTENT_THRESH = 240` (not the 250 default): cairosvg's anti-alias halo is
~245–249 (visually white); at 250 that halo asymmetrically enlarges the render
bbox vs the sharp source jpeg and mis-scales the two. At 240 the halo is treated
as background and the source/render content bboxes match to within 1 px on the
clean images. Identity (image scored against itself) stays exactly `ssim = 1.0`.

## Identity sanity

`score(img, img)` → **`ssim_color = 1.0`, `composite = 1.0`** (verified on both
the crest and the house). The cropped metric is self-consistent.

## Per-image SSIM trajectory — v1 → v2 → v3 (fair)

v3(fair) = re-score of the **already-saved best SVG** with the new content-crop
`score()` (no re-optimization). `Δ(v3−v2)` isolates the effect of the content-crop
registration change on the *same* SVG.

| Image | Type | v1 SSIM | v2 SSIM | **v3 (fair) SSIM** | Δ(v3−v2) | ≥0.98 | collapsed |
|---|---|---|---|---|---|---|---|
| IMG_0331 flags | flat/logo | 0.9807 | 0.9806 | **0.9807** | +0.0001 | ✅ | False |
| IMG_1126 crest | multicolor logo | 0.9804 | 0.9804 | **0.9384** | −0.0420 | ❌ | False |
| IMG_0322 caddie | line art | 0.9844 | 0.9840 | **0.9680** | −0.0160 | ❌ | False |
| IMG_0293 house | soft-shaded | 0.7659 *(gamed)* | 0.6280 | **0.6252** | −0.0028 | ❌ | False |
| IMG_0263 squirrel | line art | 0.9713 | 0.9810 | **0.9812** | +0.0002 | ✅ | False |

(v1 house = the gamed gray-plate collapse, not a faithful trace; see
`reports/vectorizer_v2.md`. The flags SVG was re-optimized during v3 exploration;
crest/caddie/house/squirrel SVGs are the v2 best, re-scored.)

## Honest verdict on the registration fix

**The content-crop registration change did not achieve its goal, and is
neutral-to-slightly-negative on this set.** The measurements show why:

- **No misregistration existed to fix on the clean images.** vtracer preserves the
  source's canvas dimensions, so the v2 (non-crop) metric already framed source and
  render identically. On flags and squirrel the content bboxes are pixel-identical
  and v3 is a no-op (±0.0002).
- **On detailed clean art it slightly *hurts*.** Cropping to a tight bbox and
  re-centering introduces a small resampling / centering shift that mis-registers
  fine detail: crest **−0.042** (0.9804 → 0.9384), caddie **−0.016**. The crest
  `_compare.png` is **visually near-perfect** (red ring, CAPE MAY / BEACH PATROL
  text, yellow oars, boat, waves, birds, clouds all reproduced) yet now scores
  0.938 — i.e. the cropped metric under-reports a trace that is visually excellent.
  This is a metric-validity regression, not a tracing change.
- **It does not close the house gap** (the entire motivation): **−0.0028**, from
  0.6280 to 0.6252. Registration was never the house's problem.

## House verdict (regenerated `_compare.png` viewed)

Viewed the fair (content-cropped, aligned) house `_compare.png`. With fair
registration the render is unmistakably the **same house** — gray hip roof, two
brown chimneys, tan brick façade, white columns, dark windows, green foundation
bushes, light door — and it is **not** the v1 gray-plate collapse (`collapsed=False`,
cp floored at 6). But it is **still clearly distinguishable from the source — a
real gap remains**, and the concrete reason is **tracing, not registration**:

- The source is a **soft, anti-aliased illustration with continuous gradient
  shading** (smoothly graded roof, subtly shaded brick, soft shadows). Flat
  region-tracing can only approximate gradients with a handful of **solid fills**,
  so the render reads blockier and harder-edged: chunky rectangular windows,
  shutters split into separate dark blocks, flat roof and brick with visible region
  seams instead of smooth tonal transitions.
- The render also spreads its content across a larger area than the compact source
  (render content bbox 383×499 vs source 276×363); normalizing scale via
  content-crop does not reconcile the per-pixel tonal divergence.

Net: the house's honest faithful ceiling under **flat-color vectorizing** is
~0.63 SSIM, and it is limited by gradient/soft-shading reproduction that flat
region tracing cannot represent — fair registration confirms this rather than
lifting it.

## Bounded re-optimization (STEP 5) — skipped, deliberately

House fair SSIM (0.625) is below 0.90, but re-optimization was **skipped**:

- There is **no clear tracing headroom**. The saved house already uses a rich
  palette (cp=6, `collapsed=False`); the gap is the gradient-vs-flat-fill ceiling
  above, which parameter tuning within vtracer's flat-region model cannot cross.
- The house search is **non-convergent** (never reaches the SSIM target; it is what
  exhausted the previous worker's budget). A bounded run still fans out across all
  multi-start seeds (`max_iters` is *per start*), so it risked running long for a
  ~0.00 expected SSIM gain. Per the task's guard ("if it risks running long, skip
  and report the re-scored number") it was skipped.

## Final per-image status (honest)

- **Flags (IMG_0331)** — faithful, **0.9807 ≥ 0.98**. Visually indistinguishable
  bar minor edge roughening on the flag outlines.
- **Squirrel (IMG_0263)** — faithful, **0.9812 ≥ 0.98**. Visually indistinguishable.
- **Crest (IMG_1126)** — **visually indistinguishable** (see `_compare.png`); the
  0.9384 cropped score is an artifact of the content-crop re-centering shift, not a
  visual defect (v2 non-crop = 0.9804).
- **Caddie (IMG_0322)** — visually faithful line art; 0.9680 cropped
  (v2 non-crop 0.9840), same crop-shift effect as the crest.
- **House (IMG_0293)** — genuine, non-collapsed house render but a **real,
  honest gap** (0.625). Ceiling = flat region-tracing cannot reproduce continuous
  gradient / soft shading. Not a registration problem.

## Recommendation / follow-up

The v2 (non-crop) metric tracked visual quality **better** than v3's content-crop
metric on this set (crest is visually perfect at 0.98 uncropped but 0.94 cropped).
The content-crop change should be reconsidered: either revert `score()` to the
non-crop v2 framing, or replace the crop-then-recenter step with a
**scale-only normalization that does not re-center** (to remove the sub-pixel shift
that penalizes detailed clean art). This is offered as a follow-up, not done here,
to stay within the "scoring change only, no re-optimize" scope.

## Artifacts

- `vectorizer.py` — v3 `_crop_to_content` + content-crop-in-`score()`
  (`CROP_CONTENT_THRESH = 240`); v2 anti-collapse guard + `color_fidelity` retained.
- `vectorized_svg/<stem>_compare.png` — regenerated from the **content-cropped,
  aligned** images (fair side-by-side) for all 5.
- `vectorization_attempts.jsonl` — all prior rows preserved (112 v1 + 507 v2 +
  107 v3 exploration from the prior worker); **5 v3 fair re-score rows appended**
  (`start="rescore"`).
- `parameter_correlation_index_vec.json` — **unchanged** (no re-optimization).
</content>
