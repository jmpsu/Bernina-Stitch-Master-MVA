---
name: svg-topology-qa
description: Validates and cleans the structure of vectorized SVGs — path topology, object count, background remnants, white-area handling — before digitization. Use after vector generation and before stitch planning (Melanie/Mackenzie responsibilities); not for generating vectors or stitch plans.
---

# SVG Topology QA

## Purpose

Guarantee that an SVG entering digitization contains only production-relevant
subject paths with sound topology, so stitch planning never inherits hidden
backgrounds, stray objects, degenerate paths, or ambiguous white areas.

## When to Use

- After `skills/embroidery-vector-generation` produces a candidate SVG.
- Before `skills/stitch-plan-generation` consumes an SVG.
- When Mackenzie's review contract requires a structural pass/fail with
  evidence.

Not for: re-tracing rasters, stitch density QA (that is stitch-plan QA), or
visual/feasibility judgment (Mackenzie's broader review).

## Required Inputs

- Candidate SVG (from `vectorized_svg/` or the job record).
- The source raster for silhouette comparison.
- Garment/fabric color context for white-area decisions.

## Repository Inspection Workflow

1. Read `metrics.py` for the existing scoring dimensions before adding checks.
2. Check `reports/` for prior QA findings on the same image.
3. Consult `skills/knowledge-retrieval` for topology guidance in the
   knowledge library.

## Architecture Inspection Workflow

Position in pipeline: Optimized SVG → **Structural Verification** →
Embroidery-Ready Vector (BRD § I-HIVE Phase 2). Failures route back to
vector generation; passes hand forward to digitization.

## Agent Responsibility Separation Rules

Melanie owns vector optimization; Mackenzie owns review/approval. This skill
gives both the same structural checklist. Stitch-related judgments (density,
pull) belong to `skills/stitch-plan-generation` and Margaret's stitch QA.

## Implementation Workflow

1. Parse the SVG (python3-lxml / python3-bs4 are the sanctioned parsers).
2. Verify object inventory: only production-relevant subject paths; no
   leftover raster `<image>`, test layers, or hidden background objects
   (archival/source content only in a locked layer excluded from export).
3. Verify background removal at object level: no full-canvas rectangles, no
   off-white fills approximating paper.
4. Verify white-area intent: knockout/transparent holes vs explicit white
   thread paths, matching garment color and customer intent from the job
   record.
5. Verify topology: closed subject paths, no self-intersections that break
   fill regions, no zero-area or duplicate paths, sane winding for holes.
6. Verify silhouette fidelity against the source raster (proportions and
   recognizable intent preserved).
7. Record pass/fail per check; on fail, emit a rejection event naming the
   failed gate, defect, likely cause, file, and next agent
   (`skills/references/slack-event-standard.md`).

## Verification Workflow

- Automated: parser-level checks (object counts, path validity) with output
  captured.
- Manual: side-by-side render of SVG vs raster.
- The QA result must be reproducible from the recorded SVG alone.

## Evidence Requirements

- Check-by-check pass/fail list with the offending element IDs on failures.
- Render artifact used for the silhouette comparison.
- The rejection/approval event text.

## Common Rationalizations

| Rationalization | Why it is incorrect | Required corrective action |
|---|---|---|
| "The renderer hides that stray object, it's harmless." | Digitizers stitch objects, not renders; hidden objects become stitches. | Delete or archive-lock the object; re-verify. |
| "White areas will sort themselves out at stitch time." | White handling is a customer-intent decision, not a stitch-time default. | Resolve knockout vs white-thread now, from the job record. |
| "One tiny duplicate path won't matter." | Duplicates double-stitch and can jam the B700. | Remove duplicates; re-run checks. |
| "Visual check is enough." | The BRD requires observable, reproducible evidence. | Capture parser output per check. |

## Red Flags

- An "approved" SVG that still contains an `<image>` element.
- Approval events lacking the what/how/why/files/next-owner structure.
- QA passes with no recorded element inventory.
- Silhouette drift accepted without an explicit customer redesign request.

## Final Report Format

Follow `skills/references/final-report-standard.md`, extended with: SVG file,
checks run, failures with element IDs, and the routing decision.
