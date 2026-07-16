#!/usr/bin/env python3
"""Seed the three missing required knowledge corpora so no agent's knowledge
gate stays blocked (deep-inventory finding: ink-stitch-docs, bernina-b700,
visual-qa were MISSING_REQUIRED_CORPUS for Mckenna, Meredith, Miranda,
Mackenzie, Marnie, Mercy).

Every record is grounded in a verifiable source: the canonical BRD, this
repository's production constants (digitizer.py guardrails, hoop table), or
its measured production results (SYSTEM_ATLAS). No invented citations.
Idempotent: rewrites the three corpus files deterministically.
"""

import datetime
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
LIB = REPO / "knowledge" / "library"
NOW = datetime.datetime.now(datetime.timezone.utc).isoformat()


def obj(section, slug, title, text, tags, agents, source):
    return {
        "id": f"{section}/{slug}",
        "source_path": source,
        "source_type": "authored-grounded",
        "section": section,
        "title": title,
        "page": None, "chunk": 0,
        "text": text,
        "summary": text.split(".")[0] + ".",
        "caption": "", "image_path": None, "visual_summary": None,
        "tags": tags,
        "agent_relevance": agents,
        "related_objects": [],
        "retrieval_modes": ["text"],
        "created_at": NOW,
    }


INKSTITCH = [
    ("satin-columns", "Satin column construction and width limits",
     "Satin columns are built from two rails with zigzag stitches between "
     "them. Column width must stay between 1 mm and about 7 mm; wider "
     "columns need a split-satin or fill treatment because long satin "
     "stitches snag and loop. This repository enforces "
     "SATIN_MIN_WIDTH_MM=1.0 and SATIN_MAX_WIDTH_MM=7.0 in digitizer.py. "
     "Rail direction must be consistent so the zigzag pairs do not twist; "
     "validate rails before stitch generation.",
     ["satin", "rails", "width", "zigzag"],
     ["mckenna", "meredith", "marnie"], "digitizer.py:SATIN_*"),
    ("underlay-types", "Underlay planning: edge-walk, center-walk, tatami",
     "Underlay stabilizes fabric before top stitching. Edge-walk underlay "
     "runs just inside the region border; center-walk runs along the column "
     "center; sparse tatami (zigzag) underlay covers larger fill regions at "
     "2-3x the top-stitch row spacing. Regions smaller than about 25 mm2 "
     "skip underlay because it only adds bulk. This repository implements "
     "inset tatami underlay with UNDERLAY_ROW_SPACING_MM=2.0 and "
     "UNDERLAY_INSET_MM=0.4.",
     ["underlay", "tatami", "edge-walk", "stability"],
     ["mckenna", "meredith", "marnie"], "digitizer.py:UNDERLAY_*"),
    ("pull-compensation", "Pull compensation for fill and satin",
     "Thread tension pulls stitches inward along the stitch direction, "
     "shrinking shapes 0.1-0.4 mm per side on stable fabric and more on "
     "knits. Compensate by extending fill regions along the stitch axis "
     "before generation. This repository applies PULL_COMP_MM=0.2 via "
     "row-axis dilation of solid regions.",
     ["pull-compensation", "tension", "distortion"],
     ["mckenna", "meredith", "marnie"], "digitizer.py:PULL_COMP_MM"),
    ("stitch-lengths", "Stitch length limits and trims",
     "Keep stitch lengths between 0.5 mm (shorter risks thread breaks and "
     "needle strikes) and about 3 mm for fills (longer snags). Insert a "
     "trim before any jump longer than 8 mm to avoid long connector "
     "threads. This repository enforces MIN_STITCH_MM=0.5, "
     "MAX_STITCH_MM=3.0, TRIM_JUMP_MM=8.0.",
     ["stitch-length", "trim", "jump"],
     ["mckenna", "meredith", "marnie"], "digitizer.py stitch constants"),
    ("color-blocks", "Color block ordering",
     "Order stitch blocks to minimize color changes: group all regions of "
     "one thread color into a single block where layering allows, stitch "
     "large fills before outlines, and stitch thin line-art last for crisp "
     "edges. Every color change costs machine time and a potential "
     "mis-trim.",
     ["color-change", "block-order", "sequencing"],
     ["mckenna", "meredith", "marnie"], "digitizer.py digitize_object"),
]

B700 = [
    ("hoops", "Bernina B700 hoop table and stitchable fields",
     "The B700 embroidery module accepts these hoops (stitchable field): "
     "small oval 72x50 mm, medium 130x100 mm, large oval 255x145 mm, maxi "
     "210x400 mm, jumbo 260x400 mm. Every design must fit a hoop in some "
     "orientation; check before export. This repository encodes the table "
     "as digitizer.B700_HOOPS and check_hoop_fit().",
     ["hoop", "b700", "embroidery-area", "machine-limit"],
     ["miranda", "marnie"], "digitizer.py:B700_HOOPS"),
    ("usb-exp", "Bernina USB EXP handoff: EXP + INF + BMP",
     "For USB stick transfer to a Bernina, ship the .EXP stitch file with "
     "its companion .INF thread-color information file and .BMP preview "
     "image so the machine screen shows colors and a thumbnail. This "
     "repository writes all three per object in write_outputs().",
     ["exp", "inf", "bmp", "usb", "handoff"],
     ["miranda", "marnie"], "digitizer.py:write_outputs"),
    ("density-jam", "Local stitch density limit (jam safety)",
     "Local needle-penetration density above about 1.2 penetrations per "
     "mm2 in any 3 mm cell builds thread and jams the machine or breaks "
     "needles. Measure a local density map over the plan and reject or "
     "thin any plan exceeding the limit; verified production runs in this "
     "repository pass at 1.111/mm2. Constants: "
     "MAX_LOCAL_DENSITY_PER_MM2=1.2, DENSITY_CELL_MM=3.0.",
     ["density", "jam", "needle", "safety"],
     ["miranda", "margaret", "marnie", "mercy"],
     "digitizer.py:_density_report; docs/SYSTEM_ATLAS.md production cycle"),
    ("formats", "B700 file formats",
     "The B700 reads EXP natively via USB; PES is read by Bernina "
     "ARTlink-class software. Preserve both exports. Do not exceed hoop "
     "limits at export time; stitch speed settings on the machine are the "
     "operator's, never encoded in the file.",
     ["format", "exp", "pes", "compatibility"],
     ["miranda", "marnie"], "docs/requirements/EMBIZ_BRD.md Miranda roster"),
]

VISUAL_QA = [
    ("ssim-gates", "SSIM and composite gates for vector QA",
     "Score vectorization by SSIM against the source raster plus edge IoU "
     "and color fidelity in a composite. Complexity-banded floors: 0.97 "
     "for low, 0.95 for medium, 0.92 for high complexity artwork. The "
     "continuous run targets 0.98; finalized production images in this "
     "repository measured SSIM 0.968-0.993.",
     ["ssim", "composite", "threshold", "gate"],
     ["mackenzie", "margaret", "mercy"],
     "vectorizer.py score(); local_agents/intake.py complexity_analysis"),
    ("topology-checks", "Structural SVG checks before digitization",
     "Before digitizing, verify: no leftover raster <image> elements, no "
     "full-canvas background rectangle, no off-white paper-residue fills, "
     "no duplicate or zero-area paths, and deliberate white-area intent "
     "(knockout hole vs white thread) resolved against garment color. "
     "Blocking failures reject to re-vectorization.",
     ["topology", "background", "duplicate-paths", "white-areas"],
     ["mackenzie", "melanie", "mercy"], "svg_topology_qa.py"),
    ("density-map-qa", "Density-map QA for stitch plans",
     "Render the local penetration-density map for every stitch plan and "
     "compare its maximum to the machine jam limit. Record max local "
     "density, cell size, and pass/fail in the plan sidecar so the QA "
     "verdict is reproducible from artifacts alone.",
     ["density-map", "qa", "stitch-plan"],
     ["mackenzie", "margaret", "mercy"], "digitizer.py:_density_report"),
    ("silhouette-fidelity", "Silhouette fidelity review",
     "The customer's silhouette, proportions, and recognizable artistic "
     "intent must be preserved unless redesign is explicitly requested. "
     "Compare a render of the production SVG against the source raster; "
     "reject substitutions of generic clip art.",
     ["silhouette", "fidelity", "customer-intent"],
     ["mackenzie", "mercy"],
     "docs/requirements/EMBIZ_BRD.md Maya roster; svg_topology_qa.py"),
]


def write(section_dir: str, section: str, items):
    d = LIB / section_dir
    d.mkdir(parents=True, exist_ok=True)
    path = d / "knowledge_objects.jsonl"
    with path.open("w", encoding="utf-8") as f:
        for slug, title, text, tags, agents, source in items:
            f.write(json.dumps(obj(section, slug, title, text, tags, agents,
                                   source)) + "\n")
    print(f"wrote {path.relative_to(REPO)} ({len(items)} objects)")


if __name__ == "__main__":
    write("14-ink-stitch-automation-framework/documents",
          "ink-stitch-docs", INKSTITCH)
    write("10-machine-integration/bernina-b700-corpus", "bernina-b700", B700)
    write("12-quality-assurance/visual-qa-corpus", "visual-qa", VISUAL_QA)
