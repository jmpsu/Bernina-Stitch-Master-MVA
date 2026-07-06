# Vectorization Knowledge Index (Stage 1: extraction only)

Four specialized knowledge agents each OWN one vectorization element and mine the
local EMBIZ library into cited knowledge objects, mapped into the model-free
vectorizer's actual vtracer parameter space (`vectorizer.py` `PARAM_GRID` /
`DOCTRINE_SEED` / `_ALLOWED`).

Sources mined (read-only worktree of `origin/mila/embiz-agent-system`):
- `potrace_EMBIZ_ADAPTED_DOCTRINE.md` (concrete param constraints + presets)
- `inkscape_EMBIZ_ADAPTED_DOCTRINE.md` (color budget, delta-E, HSL, deviation)
- `inkstitch_EMBIZ_ADAPTED_DOCTRINE.md` (node/element iteration — thin here)
- `potrace_SOURCE_BUNDLE.md` (`potracelib.h`, `mkbitmap.c`, dictionary/man — the
  AUTHORITATIVE param semantics, `grep`'d not read whole)

**Mapping honesty:** potrace/inkscape are different tools than vtracer. Where a
knowledge object maps cleanly it is marked *direct*; where the vtracer analogue is
conceptual (or vtracer has no equivalent) it is marked *inferred* / *weak* below.
16 knowledge objects total; `knowledge_agents.load_agent_hypotheses()` turns them
into 16 candidate isolated-factor experiments (13 directly runnable on vtracer, 3
pre-tracer pipeline / topology knobs).

---

## color_agent (element: color) -> color_precision, layer_difference, hierarchical, colormode

| concept | source | param mapping | direct/inferred | hypothesis (short) |
|---|---|---|---|---|
| color delta_e merge tolerance <=5.0 | inkscape doctrine | `layer_difference` set [4,8,16,24] | inferred (layer_difference is not calibrated CIE dE) | mid layer_difference (8-16) drops redundant near-dup layers, holds color_fidelity |
| max thread color budget (15) | inkscape doctrine | `color_precision` set [4,5,6,7] | direct-ish (concept maps, values chosen) | land palette near <=15 & above source floor -> max color_fidelity, no collapse |
| HSL perceptual color matching | inkscape doctrine | `colormode` set ["color"] | direct | keep colormode=color so hue survives for downstream HSL match |
| stacked vs cutout layering | inkscape doctrine | `hierarchical` set [stacked,cutout] | inferred (vtracer flag not named) | stacked mirrors opaque fills; A/B vs cutout for boundary slivers |

## curve_agent (element: curve) -> corner_threshold, path_precision, mode, splice_threshold, length_threshold

| concept | source | param mapping | direct/inferred | hypothesis (short) |
|---|---|---|---|---|
| alphamax corner threshold (def 1.0, 0-1.3334) | potrace SOURCE_BUNDLE (potracelib.h) | `corner_threshold` set [40..80] | direct concept, INVERTED sense (high alphamax -> low corner_threshold) | logo->lower (smoother), text->higher (sharper) raises ssim per artwork |
| opttolerance curve smoothness (def 0.2, 0-1.0) | potrace SOURCE_BUNDLE (potracelib.h) | `path_precision` set [5,6,7,8] | direct concept (primary axis) | high path_precision (low opttol) -> faithful/more nodes; low -> fewer nodes |
| opttolerance segment joining | potrace doctrine | `splice_threshold` set [30,45,60] | direct concept (secondary axis) | higher splice joins segments, smooths, cuts node count |
| opticurve: bezier vs polygon | potrace SOURCE_BUNDLE (potracelib.h) | `mode` set [spline,polygon] | direct | spline (opticurve on) beats polygon on curves; polygon on angular/gradient |

## noise_agent (element: noise) -> filter_speckle + pre-tracer denoise/threshold

| concept | source | param mapping | direct/inferred | hypothesis (short) |
|---|---|---|---|---|
| turdsize speckle suppression (def 2, 2-100) | potrace SOURCE_BUNDLE (potracelib.h) | `filter_speckle` set [0,1,2,4,6,8] | direct | raise to clean speckle until genuine small features erode; optimum ~2 detail / ~5 logo |
| mkbitmap lowpass foreground smoothing | potrace SOURCE_BUNDLE (mkbitmap.c) | `source_presmooth` (pipeline) [median3,gaussian,none] | NO vtracer param — maps to existing `_presmoothed_source()` | presmooth noisy/AA sources so filter_speckle stays low, lifts fidelity |
| mkbitmap highpass background gradient | potrace SOURCE_BUNDLE (mkbitmap.c) | `source_background_flatten` (pipeline) [highpass,none] | NO vtracer param — new pre-tracer step | flatten uneven backgrounds to kill spurious regions |
| blacklevel / bilevel cutoff (0-1, def 0.5) | potrace SOURCE_BUNDLE (potracelib.h/mkbitmap.c) | `source_threshold_level` (pipeline) [0.45,0.5,0.55] | NO vtracer param in color mode — pre-binarize knob | cutoff at luminance valley preserves thin silhouettes, lifts edge_iou |

## edge_agent (element: edge) -> corner_threshold, mode, path_precision, node-count checks

| concept | source | param mapping | direct/inferred | hypothesis (short) |
|---|---|---|---|---|
| max path deviation <=0.5mm | inkscape doctrine | `path_precision` increase [6,7,8] | inferred coupling (0.5mm is downstream target, not vtracer unit) | higher path_precision bounds edge drift -> edge_iou + meets deviation gate |
| corner sharpness edge fidelity | potrace doctrine | `corner_threshold` increase [60..90] | direct concept (opposite bias to curve agent) | keep corners crisp on angular art -> edge_iou; trades off vs curve smoothing |
| turnpolicy topology resolution (def minority) | potrace SOURCE_BUNDLE (potracelib.h) | `mode` set [spline,polygon] | WEAK/inferred — vtracer has NO turnpolicy analogue | can't tune diagonal-pinch topology directly; use node/region-count check instead |
| node/element count topology target | inkstitch doctrine | `path_precision` decrease [4,5,6] | concept direct, numeric target inferred | once fidelity met, lower path_precision to hit node budget for clean digitizing |

---

## Honest notes on library thinness

- **vtracer is never named in the library.** Every mapping is potrace/inkscape ->
  vtracer. Direct concept matches (turdsize->filter_speckle, alphamax->corner_threshold
  with inverted sense, opticurve->mode, opttolerance->path_precision) are solid;
  `layer_difference<-delta_e` and `hierarchical` are *inferred* — vtracer's units are
  not the library's units.
- **noise agent:** 3 of its 4 knowledge objects (mkbitmap lowpass/highpass, blacklevel)
  are **pre-tracer pipeline knobs with NO vtracer parameter**. They map onto the
  vectorizer's existing `_presmoothed_source()` and its implicit foreground cutoff, or
  propose new pre-tracer stages. Only `filter_speckle` is a direct vtracer knob.
- **edge agent / turnpolicy:** vtracer exposes **no** turnpolicy equivalent; that object
  is flagged weak and points to a post-trace node/region-count check as the real remedy.
- **inkstitch doctrine is thin for vectorization** — it is mostly thread-inventory and
  node-iteration prose, not tracing parameters. Only the node/element-iteration concept
  was usable (edge agent node-count target); the numeric node budget is inferred, not stated.
- **inkscape doctrine** gave the strongest color numbers (delta_e<=5.0, <=15 colors,
  HSL matching, <=0.5mm deviation) but they are quality *targets*, not tracer params, so
  they are coupled to params as fidelity levers rather than copied as values.

Runnable by Stage 2 directly on vtracer: **13/16**. Pipeline/topology (need harness
support): **3/16** (source_presmooth, source_background_flatten, source_threshold_level).
