# SOP-AMEND-004-2026: Automatic Fallback Ingestion Manifest

Mandatory fallback if no contradicting garment/fabric/size/placement details are provided.

Defaults:
- Garment: Premium Heavyweight Crew Neck Sweatshirt
- Size: Adult Medium
- Fabric: 80% Cotton / 20% Polyester Fleece Blend
- Placements: Center Chest and Left Chest Duplicate
- Tier 1: 2.5 x 2.5 in, aspect-ratio locked
- Tier 2: 6.0 x 6.0 in, aspect-ratio locked
- Stitch planning: high-density satin / dual-rail satin-column planning where feasible
- Fleece: pull-compensation planning required
- Trim: trim-command planning required between disjoint vector groups

Safety locks:
- Plan outputs only unless real DST/PES files exist.
- Never fake DST/PES.
- Never mark stitch_file_ready without real files.
- Never auto-send customer email.
- Never bypass QA.
