# OBJECTIVE HIERARCHY — #AUTH-01_OBJECTIVE_HIERARCHY

> Authority file. Used by `recovery/` steps to break ties and to decide, during a
> repair, which of several possible fixes to pursue first. Higher tiers win.

The single north star (from the EMBIZ BRD): **continuously refine the existing
production system into a self-learning, self-improving multi-agent raster→vector→
embroidery platform that reliably transforms electronic image files into
production-grade digitized embroidery stitch plans visually indistinguishable
from the original customer pixel-based image.** Everything below serves it.

## Tier 0 — Safety & Truthfulness (never violable)
- Never fabricate evidence, output, or completion.
- Never destroy existing working code or data not named as a step target.
- Never send external/customer-facing communications without the approval gate.

## Tier 1 — Continuity & Auditability
- Every action produces a hashed, append-only evidence record.
- The failed step is always returned to; the pipeline never silently advances.
- Canonical artifacts are preserved and reproducible.

## Tier 2 — Business-Requirement Completeness
- Every requirement in `business_requirements/EMBIZ_JUPITER_FULL_BRD.md` maps to
  at least one executable step (see `REQUIREMENTS_TRACEABILITY.md`).
- "Anything not running as production code must be written as code and tested."
  A step is not `SUCCESS` until its slice of the BRD is real, tested code.

## Tier 3 — Production Quality
- Visual fidelity of vector/stitch output to the source image.
- Bernina B700 compliance and machine-executable exports.
- Density/QA thresholds met with observable metrics.

## Tier 4 — Autonomous Improvement
- Historical learning, regression baselines, idle experimentation, knowledge
  memorialization, autonomous code review.

## Tie-break procedure (used by recovery)
1. If two candidate repairs differ in tier, choose the higher tier.
2. If same tier, choose the one with smaller blast radius (fewer files touched).
3. If still tied, choose the one with the stronger existing evidence/precedent in
   `evidence/` or the repo's historical `*.jsonl` learning logs.
4. Record the tie-break reasoning in the recovery evidence artifact.
