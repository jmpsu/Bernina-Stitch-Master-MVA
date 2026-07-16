---
name: embroidery-vector-generation
description: Converts customer raster artwork into embroidery-ready optimized SVG using the repo's iterative vectorizer with parameter exploration and SSIM-scored candidates. Use for any raster-to-vector job (Mila's responsibility) and for improving vectorization quality on stalled images; not for stitch planning or SVG structural QA, which are separate skills.
---

# Embroidery Vector Generation

## Purpose

Transform raster artwork into clean, flat-color, background-removed,
silhouette-faithful vector SVG (the roster's "Column B standard") using the
existing model-free iterative vectorizer, so downstream digitization receives
production-grade paths rather than auto-traced noise.

## When to Use

- A job's canonical record holds a customer raster needing vectorization
  (contract owner: Mila, `agents/contracts/mila.json`).
- A continuous-run image is stalled below its SSIM/composite target and needs
  further parameter exploration.

Not for: SVG topology/structure QA (`skills/svg-topology-qa`), stitch plan
generation (`skills/stitch-plan-generation`), or artwork feasibility review
(Mackenzie's contract).

## Required Inputs

- Source raster (customer-provided, preserved as source-of-truth reference).
- Target SSIM (default 0.98 in `vectorizer.py`).
- Prior attempts for this image from `vectorization_attempts.jsonl` and
  `parameter_correlation_index_vec.json` (historical learning).

## Repository Inspection Workflow

1. Read `vectorizer.py` (`main`, iteration loop) — do not reimplement it.
2. Check `vectorization_attempts.jsonl` for the image's attempt history.
3. Check `vectorized_svg/` and `vector_source/` for existing outputs.
4. Retrieve guidance first via `skills/knowledge-retrieval`.

## Architecture Inspection Workflow

Position in the canonical pipeline: Customer Artwork → Artwork Review →
Background Removal → Raster Cleanup → Path Extraction → **Optimized SVG** →
Embroidery-Ready Vector (BRD § I-HIVE). This skill owns the raster→optimized
SVG span only.

## Agent Responsibility Separation Rules

Mila owns raster→vector conversion. Vector optimization/cleanup beyond the
vectorizer's own output belongs to Melanie; Inkscape batch scripting to
Monica; approval to Mackenzie. Route, don't absorb.

## Implementation Workflow

1. Preserve the original raster unchanged; never substitute generic clip art.
2. Run the iterative vectorizer:

```bash
python3 vectorizer.py <image.png> --target-ssim 0.98 --json
```

3. For exploration, vary preprocessing/trace parameters per the historical
   correlation index; every attempt is appended to
   `vectorization_attempts.jsonl` with its scores.
4. Enforce background removal absolutely: no paper texture, off-white
   residue, white rectangles, or hidden background objects in the final SVG
   (unless the customer explicitly requested a background).
5. Treat internal white areas deliberately: true knockout holes or explicit
   white thread paths, per garment color and customer intent.
6. Rank candidates by SSIM/composite; select the best; record the decision
   trace (`decision_trace.jsonl`).
7. Emit Slack events per `skills/references/slack-event-standard.md` and hand
   off to Melanie (optimization) or Mackenzie (review) per contract.

## Verification Workflow

- Automated: vectorizer JSON result shows achieved SSIM vs target; attempt
  logged in `vectorization_attempts.jsonl`.
- Manual: render the SVG and compare silhouette/proportions against the
  source raster; confirm zero background remnants at the raster level.

## Evidence Requirements

- Vectorizer command and JSON output (achieved SSIM, iterations).
- The appended `vectorization_attempts.jsonl` record.
- Output SVG path under `vectorized_svg/`.
- Decision trace entry explaining candidate selection.

## Common Rationalizations

| Rationalization | Why it is incorrect | Required corrective action |
|---|---|---|
| "SSIM is close enough, ship it." | Targets are contract gates; near-misses stall downstream QA. | Continue exploration or escalate as stalled with evidence. |
| "The background is nearly white, it won't stitch." | Residual background objects become stitch paths after digitization. | Remove them; verify at SVG object level. |
| "A fresh trace looks fine, skip the history." | Historical learning is a permanent BRD requirement; repeats waste attempts. | Consult the correlation index and attempts log first. |
| "I'll clean up topology while I'm here." | That is Melanie's/`svg-topology-qa`'s bounded responsibility. | Hand off with a clear file-state note. |

## Red Flags

- An output SVG whose path count or bounding box wildly differs from the
  source silhouette.
- No new record in `vectorization_attempts.jsonl` after a claimed run.
- A leftover embedded raster or hidden layer in the "final" SVG.
- Claimed SSIM with no JSON output attached.

## Final Report Format

Follow `skills/references/final-report-standard.md`, extended with: image ID,
attempts run, best SSIM/composite achieved vs target, and the selected
candidate's parameters.
