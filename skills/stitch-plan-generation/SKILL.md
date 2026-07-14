---
name: stitch-plan-generation
description: Digitizes an embroidery-ready SVG into a stitch plan and machine files with satin/fill strategy, density guardrails, and Bernina B700 jam safety. Use for stitch planning, EXP/PES export, and density QA (Mckenna/Meredith/Margaret/Miranda responsibilities); not for vector generation or SVG structural QA.
---

# Stitch Plan Generation

## Purpose

Turn a structurally verified SVG into a production stitch plan and machine
files using the repo's digitizer, with the B700 jam-safety density guard as a
blocking gate, so every exported file is machine-safe and evidence-backed.

## When to Use

- An SVG has passed `skills/svg-topology-qa` and the job requires stitch
  files (plan: Mckenna; generation: Meredith; stitch QA: Margaret; machine
  compatibility: Miranda).

Not for: raster→vector work, SVG cleanup, or customer communication.

## Required Inputs

- Embroidery-ready SVG (post topology QA).
- Target physical size, hoop constraints, fabric/garment notes, thread-color
  expectations from the canonical job record.
- Machine profile (Bernina B700 unless specified otherwise).

## Repository Inspection Workflow

1. Read `digitizer.py` — satin fill + density guardrails already exist
   (`MAX_LOCAL_DENSITY_PER_MM2 = 1.2`, `DENSITY_CELL_MM = 3.0`,
   `_density_report`); never bypass or duplicate them.
2. Check `stitch_plans/` and `stitch_files/` for prior artifacts for the
   image.
3. Consult `parameter_correlation_index.json` for historically good
   digitization parameters.

## Architecture Inspection Workflow

Position in pipeline: Embroidery-Ready Vector → Digitized Stitch Plan →
Quality Assurance → Production Output (BRD § I-HIVE Phases 2–3). Miranda's
machine-compatibility check is downstream and must not be preempted here —
but hoop-size sanity is checked before wasting a digitization run.

## Agent Responsibility Separation Rules

Stitch planning (Mckenna), file generation (Meredith), stitch QA (Margaret),
and B700 compatibility (Miranda) are distinct contract owners. This skill
covers their shared technical workflow; approvals stay with the contracted
owner at each step.

## Implementation Workflow

1. Select stitch strategy per object class (satin columns for narrow
   elements, fills for regions), with underlay and pull compensation per the
   knowledge library (`skills/knowledge-retrieval` first).
2. Run the digitizer over the verified SVG to produce the plan and machine
   files (EXP; PES where required).
3. Treat the density report as a blocking gate: local needle-penetration
   density must not exceed 1.2/mm² in any 3.0 mm cell — this is the B700 jam
   guard. A failing report rejects the plan; adjust spacing/strategy and
   re-digitize.
4. For Bernina USB EXP handoff, produce the companion `.INF` thread-color
   file and `.BMP` preview when the handoff method requires them
   (Miranda's contract).
5. Verify final design size against B700 embroidery area and the job's hoop
   constraints.
6. Record plan, density report, and decision trace; emit events per
   `skills/references/slack-event-standard.md`; hand off to stitch QA.

## Verification Workflow

- Automated: density report (`_density_report`) with
  `max_local_density_per_mm2`, `density_ok`, `stitch_count_ok` captured —
  e.g. the first production cycle's gate evidence reads
  `max local density 1.111/mm^2 (limit 1.2), PASS`.
- Automated: stitch simulation / preview render for visual QA.
- Manual: preview compared against the SVG for coverage gaps and overruns.

## Evidence Requirements

- Density report JSON for the exported plan.
- Exported file paths (`stitch_files/…`) with sizes and formats.
- Simulation/preview artifact.
- Decision trace entry for strategy and parameter choices.

## Common Rationalizations

| Rationalization | Why it is incorrect | Required corrective action |
|---|---|---|
| "Density is only slightly over the limit." | 1.2/mm² is a jam-safety limit for a physical machine, not a style guide. | Re-plan with wider spacing or different strategy until PASS. |
| "Simulation looks fine, skip the density report." | Simulations don't measure local penetration density. | Run and attach the density report. |
| "EXP exported, job done." | USB handoff may require .INF and .BMP companions; size/hoop checks remain. | Complete companions and machine checks per Miranda's contract. |
| "I'll approve my own stitch QA." | QA approval belongs to Margaret's contract, compatibility to Miranda's. | Hand off with evidence. |

## Red Flags

- An exported stitch file with no stored density report.
- Density guard constants modified to make a plan pass.
- Missing `.INF`/`.BMP` companions on a USB EXP handoff.
- Design size exceeding the hoop with no escalation.

## Final Report Format

Follow `skills/references/final-report-standard.md`, extended with: input
SVG, strategy chosen, max local density vs limit, stitch count, exported
files, and QA handoff target.
