# VISUAL FIDELITY MANDATE — #AUTH-05_VISUAL_FIDELITY_MANDATE

> Authority file. Non-negotiable. This mandate governs three gate steps and any
> future step that finalizes a vectorized SVG or derives a stitch plan/PES from
> an SVG. It exists because a vectorized/stitched output is worthless if it does
> not still look like the customer's image.

## The rule
There MUST be code that automatically tests visual fidelity BEFORE the agent
posits a finished vectorized SVG output, and BEFORE the agent creates an
embroidery stitch plan from an SVG. The agent may not "eyeball" it and assert
success. The test is `engine/fidelity_compare.py`, which measures silhouette IoU,
proportion error, relative scale, and artistic-intent similarity against the
customer SOURCE image, checked against `config/fidelity_thresholds.json`.

## The mandated confirmation sentence (verbatim clause)
After — and only after — the metrics pass, the agent MUST state, out loud in its
step output and recorded in the evidence artifact's `attestation` field, a
sentence of exactly this form, with the real filenames substituted in:

```
I HAVE REVIEWED <artwork>.svg and <artwork>.pes and can confirm they preserve
consistent silhouette, proportions, recognizable artistic intent, and relative
scale with the customer source image
```

Rules for the sentence:
- It MUST begin with `I HAVE REVIEWED`.
- It MUST contain, verbatim, the clause: *"preserve consistent silhouette,
  proportions, recognizable artistic intent, and relative scale with the customer
  source image"*.
- It MUST name the actual artifact filename(s) being attested (the `.svg` at the
  SVG gate; the `.svg` and `.pes` at the export gate). For the pre-stitch gate it
  names the `.svg` about to be digitized.
- The evidence MUST also carry `attested_files` (the real filenames) and
  `fidelity_metrics` (the real output of `fidelity_compare.py`).

## Enforcement (defeats false attestation)
`validators/fidelity_attestation.py` rejects the step unless: the lead phrase is
present, the verbatim clause is present, every named artifact appears in the
sentence, and `fidelity_metrics` are present AND pass thresholds. A missing or
under-threshold metric, or a recited sentence with no backing metrics, is a
`FAILURE` that routes into `recovery/` — where the fix is to reprocess the vector
(not to soften the words).

## Where the gates live
- `#S05-08_VISUAL_FIDELITY_ATTESTATION_SVG` — before the SVG is posited finished
  (end of Vector Validation).
- `#S06-01_VISUAL_FIDELITY_ATTESTATION_PRESTITCH` — before any stitch plan is
  created from the SVG (start of Stitch Planning).
- `#S08-…_VISUAL_FIDELITY_ATTESTATION_EXPORT` — before export artifacts are
  registered (SVG + PES vs source).

These gates instruct the agent on HOW to build/run the comparison code, then
require the verbatim confirmation backed by that code's real output.
