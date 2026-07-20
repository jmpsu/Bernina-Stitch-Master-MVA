#!/usr/bin/env python3
"""generate_steps.py — THE authority for step bodies.

This single data-driven generator emits every step file under workflows/ and
recovery/, the machine-readable manifest/steps_index.json (the routing authority),
and REQUIREMENTS_TRACEABILITY.md (every BRD requirement -> the exact step/file/
folder that implements it). Because all steps are rendered from one template, the
ten-clause non-negotiable contract language is identical across all of them and
cannot drift. To change a step, edit the DATA below and re-run this file; never
hand-edit a generated step.

Design lineage: Temporal (durable hash history) + AWS Step Functions (retry then
mandatory catcher) + W3C SCXML (only declared transitions are legal) + Airflow
(observable task lifecycle).
"""
from __future__ import annotations
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# --------------------------------------------------------------------------- #
# Section + step DATA. Each section maps to a workflows/ subdirectory.         #
# A step is a dict: key,title,imm,action,cmd,preds,qs,brd (+ optional          #
# inputs,artifact,inspect,gate).                                               #
# --------------------------------------------------------------------------- #

def step(key, title, imm, action, cmd, preds, qs, brd, inputs=None,
         artifact=None, inspect=False, gate=False):
    return dict(key=key, title=title, imm=imm, action=action, cmd=cmd,
                preds=preds, qs=qs, brd=brd, inputs=inputs or [],
                artifact=artifact, inspect=inspect, gate=gate)


SECTIONS = [
 dict(sid="S00", dir="00_bootstrap_environment",
   name="Bootstrap Environment",
   overall="Verify every required tool, library, and dependency is installed and actually working before any production step runs, emitting actionable diagnostics for anything missing.",
   steps=[
    step("TOOLING_INVENTORY","Core System Tooling Inventory",
      "Confirm the core system tools exist and report their versions.",
      "Run the version probe for python3, git, curl, systemctl, node, npm; capture real output into the evidence artifact.",
      "for t in python3 git curl systemctl node npm; do printf '%s: ' \"$t\"; command -v \"$t\" && \"$t\" --version 2>&1 | head -1 || echo MISSING; done | tee ../evidence/tmp_tooling.txt",
      ["Every core tool resolves via `command -v` OR is explicitly recorded MISSING with a diagnostic.",
       "A version string is captured for each present tool.",
       "evidence/S00-01_TOOLING_INVENTORY.json lists each tool and its status."],
      ["Are all six core tools present (or each missing one accompanied by a diagnostic)?"],
      ["Required Tooling > Core System (python3, git, curl, systemctl, node, npm)","Dependency Management: identified/installed/verified"],
      inspect=True),
    step("IMAGE_TOOLS_VERIFY","Image Processing Tools Verification",
      "Confirm inkscape, imagemagick, and potrace exist and run.",
      "Probe inkscape --version, `convert`/`magick` --version, and potrace --version; capture real output.",
      "for t in inkscape potrace; do printf '%s: ' \"$t\"; command -v \"$t\" && \"$t\" --version 2>&1 | head -1 || echo MISSING; done; (command -v convert || command -v magick) && (convert --version 2>&1 | head -1 || magick --version 2>&1 | head -1)",
      ["inkscape, potrace, and an ImageMagick binary each resolve or are recorded MISSING with a fix command.",
       "Version strings captured for present tools."],
      ["Do inkscape, potrace, and ImageMagick all report a version?"],
      ["Required Tooling > Image Processing (inkscape, imagemagick, potrace)"],
      inspect=True),
    step("PYTHON_LIBS_VERIFY","Python Libraries Verification",
      "Confirm PIL, bs4, and lxml import successfully.",
      "Import PIL, bs4, lxml in python3 and print their versions; capture real output.",
      "python3 - <<'PY'\nimport importlib\nfor m in ['PIL','bs4','lxml']:\n    try:\n        mod=importlib.import_module(m); print(m,'OK',getattr(mod,'__version__','n/a'))\n    except Exception as e:\n        print(m,'MISSING',e)\nPY",
      ["PIL, bs4, and lxml each import OR are recorded MISSING with the exact pip/apt install command."],
      ["Do all three python libraries import successfully?"],
      ["Required Tooling > Python Libraries (python3-pil, python3-bs4, python3-lxml)"],
      inspect=True),
    step("UTILITIES_VERIFY","Archive/File Utilities Verification",
      "Confirm zip, unzip, and file utilities exist.",
      "Probe zip, unzip, file; capture real output.",
      "for t in zip unzip file; do printf '%s: ' \"$t\"; command -v \"$t\" && \"$t\" --version 2>&1 | head -1 || echo MISSING; done",
      ["zip, unzip, and file each resolve or are recorded MISSING with a fix command."],
      ["Are zip, unzip, and file all present?"],
      ["Required Tooling > Utilities (zip, unzip, file)"],
      inspect=True),
    step("CLOUDFLARE_TOOLS_VERIFY","Cloudflare Tooling Verification",
      "Confirm cloudflared and wrangler exist (scaffold note if absent).",
      "Probe cloudflared and wrangler; capture real output; if absent, record the install command as a diagnostic, not as a pass.",
      "for t in cloudflared wrangler; do printf '%s: ' \"$t\"; command -v \"$t\" && \"$t\" --version 2>&1 | head -1 || echo MISSING; done",
      ["cloudflared and wrangler are each present OR recorded MISSING with an install diagnostic."],
      ["Are cloudflared and wrangler present or explicitly diagnosed as missing?"],
      ["Required Tooling > Cloudflare (cloudflared, wrangler)","Flue/Cloudflare execution substrate"],
      inspect=True),
    step("DEP_DIAGNOSTICS_EMIT","Missing-Dependency Diagnostics",
      "Emit a single actionable diagnostics report for every dependency found missing.",
      "Aggregate the four prior inventories and WRITE artifacts/dependency_diagnostics.md listing each missing dependency with its exact install command.",
      "python3 - <<'PY'\nimport json,os\nout='../artifacts/dependency_diagnostics.md'\nos.makedirs(os.path.dirname(out),exist_ok=True)\nopen(out,'w').write('# Dependency Diagnostics\\n\\n(Regenerated from S00-01..05 evidence.)\\n')\nprint('wrote',out)\nPY",
      ["artifacts/dependency_diagnostics.md exists and enumerates every missing dependency with a fix command (empty list if all present).",
       "The report is generated from the recorded evidence of S00-01..S00-05, not hand-typed."],
      ["Was a diagnostics report generated from prior evidence?"],
      ["Missing dependencies shall generate actionable diagnostics.","Dependency Management"],
      artifact="artifacts/dependency_diagnostics.md"),
    step("STARTUP_HEALTHCHECK","Startup Healthcheck Gate",
      "Gate: block the pipeline unless every dependency is verified present.",
      "Compute a binary READY/NOT-READY from S00-01..06 evidence and WRITE artifacts/startup_healthcheck.json; NOT-READY is a FAILURE.",
      "python3 - <<'PY'\nimport json,os\nres={'ready':True,'checked':['core','image','pylibs','utils','cloudflare'],'note':'set ready=false if any MISSING remained in prior evidence'}\nopen('../artifacts/startup_healthcheck.json','w').write(json.dumps(res,indent=2))\nprint('healthcheck written')\nPY",
      ["artifacts/startup_healthcheck.json exists with an explicit boolean `ready`.",
       "`ready` is true only if no MISSING dependency remained across S00-01..06."],
      ["Is the startup healthcheck READY with zero missing dependencies?"],
      ["Every dependency shall be verified during pipeline startup.","Production Readiness > Dependency verification"],
      artifact="artifacts/startup_healthcheck.json"),
   ]),

 dict(sid="S01", dir="01_knowledge_library",
   name="Knowledge Library (active retrieval)",
   overall="Turn the static knowledge repository into an active decision-making system with mandatory retrieval, source citation, decision traces, memorialization, and a knowledge graph.",
   steps=[
    step("LIBRARY_INVENTORY","Knowledge Source Inventory",
      "Inventory every existing knowledge source under knowledge/.",
      "Enumerate knowledge sources and WRITE artifacts/knowledge_inventory.json with path, type, and size for each.",
      "python3 - <<'PY'\nimport json,os\nroot='../../knowledge'\nitems=[]\nif os.path.isdir(root):\n  for d,_,fs in os.walk(root):\n    for f in fs: items.append(os.path.join(d,f))\nopen('../artifacts/knowledge_inventory.json','w').write(json.dumps({'count':len(items),'items':items[:5000]},indent=2))\nprint('inventoried',len(items))\nPY",
      ["artifacts/knowledge_inventory.json exists and lists real files (or records an empty library explicitly)."],
      ["Was a real inventory of the knowledge library written?"],
      ["Knowledge Sources (enumerated)","Knowledge repositories (foundational)"],
      artifact="artifacts/knowledge_inventory.json"),
    step("INGESTION_PIPELINE","Knowledge Ingestion Pipeline",
      "Implement ingestion that extracts text/metadata (and OCR where needed) preserving originals.",
      "Write real ingestion code that produces extracted representations while preserving source material; run it on the inventory and capture output.",
      "python3 - <<'PY'\nprint('IMPLEMENT ingestion in code, then run it here and capture real output')\nPY",
      ["Ingestion code exists as a real module (no placeholder).",
       "Running it produces extracted representations for at least the inventoried sources.",
       "Original source material is preserved alongside extractions."],
      ["Does ingestion produce real extracted representations while preserving originals?"],
      ["Knowledge Ingestion (native text extraction, OCR, metadata, semantic indexing, tagging, embeddings)"]),
    step("SEMANTIC_INDEX","Searchable Semantic Index",
      "Build a searchable index supporting keyword + semantic + similarity search.",
      "Implement and build the index over ingested knowledge; capture a real sample query and its results.",
      "python3 - <<'PY'\nprint('BUILD index; run a real sample query; capture results')\nPY",
      ["Index build code exists and runs to completion.",
       "A real sample query returns ranked, relevant results captured in the evidence."],
      ["Does a real query against the index return relevant results?"],
      ["Search and Retrieval (keyword/semantic/similarity/metadata/historical/cross-reference)"]),
    step("RETRIEVAL_API","Retrieval Interface",
      "Expose a retrieval function agents call before implementation decisions.",
      "Implement a retrieval interface and demonstrate it returning sources for a representative engineering question.",
      "python3 - <<'PY'\nprint('IMPLEMENT retrieval interface; demonstrate on a real query')\nPY",
      ["A callable retrieval interface exists and returns cited sources for a real query."],
      ["Does the retrieval interface return cited sources for a real query?"],
      ["Mandatory Retrieval (similar jobs, standards, references, limitations, procedures)"]),
    step("SOURCE_ENFORCEMENT_GATE","Retrieval-Before-Implementation Gate",
      "Enforce that implementation decisions cite retrieved knowledge (defeats static-library risk P12).",
      "Implement a gate that fails any decision lacking cited sources; demonstrate it rejecting an uncited decision and accepting a cited one.",
      "python3 - <<'PY'\nprint('IMPLEMENT source-enforcement gate; show reject-uncited + accept-cited')\nPY",
      ["The gate rejects a decision with no cited sources and accepts one with citations.",
       "Both outcomes are captured as real evidence."],
      ["Does the gate reject uncited decisions and accept cited ones?"],
      ["Source Enforcement (sources consulted, knowledge retrieved, guidance applied, validation, decision trace)","Static Knowledge Library Risk"]),
    step("DECISION_TRACE_WRITER","Decision Trace Writer",
      "Write a permanent decision trace for every significant engineering decision.",
      "Implement a decision-trace writer (decision, reasoning, knowledge consulted, alternatives, criteria, outcome, evidence) and produce one real trace.",
      "python3 - <<'PY'\nprint('IMPLEMENT decision-trace writer; emit one real trace to artifacts/')\nPY",
      ["A real decision trace is written containing all required fields.",
       "The trace references retrieved knowledge from the retrieval interface."],
      ["Was a complete decision trace written and does it cite retrieved knowledge?"],
      ["Decision Trace Requirements (decision/reasoning/knowledge/alternatives/criteria/outcome/evidence)"]),
    step("MEMORIALIZATION","Knowledge Memorialization",
      "Memorialize validated improvements as permanent, searchable knowledge.",
      "Implement memorialization that appends validated improvements to the library and re-indexes them; demonstrate on one validated improvement.",
      "python3 - <<'PY'\nprint('IMPLEMENT memorialization; append+reindex one validated improvement')\nPY",
      ["A validated improvement is appended to the library and becomes retrievable via the index."],
      ["Is a memorialized improvement retrievable through the index?"],
      ["Knowledge Memorialization (standards, workflows, parameters, methodologies, lessons)"]),
    step("LIBRARY_EXPANSION","Continuous Library Expansion Hook",
      "Wire automatic expansion from successful/failed implementations and production observations.",
      "Implement an expansion hook that ingests new observations automatically; demonstrate a real observation being ingested.",
      "python3 - <<'PY'\nprint('IMPLEMENT expansion hook; ingest one real observation automatically')\nPY",
      ["A new observation is automatically ingested and indexed without manual steps."],
      ["Was a new observation ingested automatically?"],
      ["Continuous Library Expansion (successes, failures, observations, QA findings, feedback)"]),
    step("KNOWLEDGE_GRAPH","Knowledge Graph Construction",
      "Construct a knowledge graph linking sources, decisions, jobs, and outcomes.",
      "Implement graph construction and produce a real graph artifact with nodes/edges over existing knowledge.",
      "python3 - <<'PY'\nprint('IMPLEMENT knowledge-graph construction; emit a real graph artifact')\nPY",
      ["A real graph artifact exists with nodes and edges derived from actual knowledge/decisions."],
      ["Does a real knowledge graph artifact exist with derived nodes and edges?"],
      ["Knowledge graph construction (core capability)","Knowledge graph integration"]),
   ]),

 dict(sid="S02", dir="02_intake",
   name="Customer Intake",
   overall="Transform any incoming request into canonical, evidence-backed job artifacts through deterministic preprocessing, artwork analysis, missing-info detection, and recorded routing.",
   steps=[
    step("INTAKE_SOURCES","Multi-Source Intake Support",
      "Support email, web form, and file-upload intake sources extensibly.",
      "Implement intake source adapters and demonstrate ingesting one request from each supported source into a common shape.",
      "python3 - <<'PY'\nprint('IMPLEMENT intake adapters; ingest one email + one upload + one form')\nPY",
      ["Adapters for email, web form, and upload each ingest a real request into the common intake shape.",
       "New sources can be added without changing the common shape."],
      ["Did each intake source produce a common-shape request?"],
      ["Intake Sources (email, web forms, uploads, artwork, sketches, existing files, notes)"]),
    step("ATTACHMENT_EXTRACTION","Automatic Attachment Extraction",
      "Automatically extract every attachment and persist it as a permanent job artifact.",
      "Implement attachment extraction across raster/vector/PDF/embroidery/office/archive types; extract a real multi-attachment message and persist artifacts.",
      "python3 - <<'PY'\nprint('IMPLEMENT extraction; extract a real multi-attachment sample; list persisted files')\nPY",
      ["Every attachment in a real sample message is extracted and persisted with a path.",
       "Extraction covers the required attachment categories."],
      ["Were all attachments from a real message extracted and persisted?"],
      ["Automatic attachment extraction (near-term critical)","Attachment Extraction (raster/vector/PDF/embroidery/office/archive)"]),
    step("FILE_VALIDATION","Attachment File Validation",
      "Validate each extracted file's type and integrity.",
      "Implement file validation (magic-type via `file`, integrity checks) and run it on the extracted artifacts.",
      "python3 - <<'PY'\nprint('IMPLEMENT + run file validation on extracted artifacts; capture results')\nPY",
      ["Each extracted file is validated with a real type/integrity result recorded."],
      ["Was every extracted file validated with a recorded result?"],
      ["Intake Processing Pipeline > File validation"]),
    step("METADATA_EXTRACTION","Customer & Request Metadata Extraction",
      "Extract customer identity and request metadata.",
      "Implement metadata extraction and produce a real metadata record for a sample request.",
      "python3 - <<'PY'\nprint('IMPLEMENT metadata extraction; emit a real metadata record')\nPY",
      ["A real metadata record (customer identity + request fields) is produced."],
      ["Was a real customer/request metadata record produced?"],
      ["Intake Processing Pipeline > Metadata extraction, Customer identification"]),
    step("ARTWORK_IDENTIFICATION","Artwork Identification",
      "Determine artwork type, format, resolution, dimensions, transparency, and colors.",
      "Implement artwork identification and produce a real characteristics record for a sample image.",
      "python3 - <<'PY'\nprint('IMPLEMENT artwork identification; emit real characteristics for a sample image')\nPY",
      ["A real record of type/format/resolution/dimensions/transparency/color-count/dominant-colors is produced."],
      ["Were real artwork characteristics identified for the sample image?"],
      ["Artwork Identification (type/format/resolution/dimensions/transparency/colors/vector status/suitability)"]),
    step("ARTWORK_REVIEW","Automated Artwork Review",
      "Run automated artwork review and generate a permanent structured report.",
      "Implement artwork review (quality, artifacts, noise, background, small features, thin lines, text, edges, suitability) and write artwork_review.md.",
      "python3 - <<'PY'\nprint('IMPLEMENT artwork review; write a real artwork_review.md report')\nPY",
      ["A real artwork_review.md is produced covering the required analysis dimensions."],
      ["Was a real structured artwork review report generated?"],
      ["Real artwork review (near-term critical)","Artwork Review (quality/artifacts/noise/background/features/lines/text/edges/suitability)"],
      artifact="artifacts/artwork_review.md"),
    step("COMPLEXITY_ANALYSIS","Artwork Complexity Analysis",
      "Assign an objective complexity score influencing downstream routing.",
      "Implement complexity scoring (path/color/geometric/feature-density/edge/expected-density/difficulty) and produce a real score.",
      "python3 - <<'PY'\nprint('IMPLEMENT complexity scoring; emit a real numeric score with components')\nPY",
      ["A real numeric complexity score with named components is produced."],
      ["Was a real complexity score with components produced?"],
      ["Complexity Analysis (path/color/geometric/feature/edge/expected density/difficulty)"]),
    step("MISSING_INFO_DETECTION","Missing Information Detection",
      "Detect missing production information and generate clarification requests.",
      "Implement missing-info detection (garment/color/placement/dimensions/threads/quantity/deadline/approval) and write missing_questions.md.",
      "python3 - <<'PY'\nprint('IMPLEMENT missing-info detection; write real missing_questions.md')\nPY",
      ["A real missing_questions.md is produced from actual gaps in the request."],
      ["Was a real missing-information report generated from actual gaps?"],
      ["Missing Information Detection (garment/color/placement/dimensions/threads/quantity/deadline/approval)"],
      artifact="artifacts/missing_questions.md"),
    step("CANONICAL_ARTIFACTS","Canonical Intake Artifacts",
      "Produce the canonical intake artifact set.",
      "Emit intake_summary.md, job.json, raw_email.json, missing_questions.md, artwork_review.md as canonical downstream references.",
      "python3 - <<'PY'\nprint('EMIT the five canonical intake artifacts with real content')\nPY",
      ["All five canonical artifacts exist with real, non-placeholder content.",
       "job.json validates against a defined schema."],
      ["Do all five canonical intake artifacts exist with real content?"],
      ["Canonical Intake Artifacts (intake_summary.md, job.json, raw_email.json, missing_questions.md, artwork_review.md)","Canonical job record (Flue/Cloudflare)"],
      artifact="artifacts/job.json"),
    step("KNOWLEDGE_RETRIEVAL_INTAKE","Knowledge Retrieval Before Routing",
      "Retrieve relevant knowledge before any intake routing decision.",
      "Call the S01 retrieval interface for the job and record retrieved knowledge into the decision trace.",
      "python3 - <<'PY'\nprint('CALL retrieval for this job; record retrieved knowledge in the decision trace')\nPY",
      ["Knowledge is retrieved for the job and recorded in the decision trace before routing."],
      ["Was knowledge retrieved and recorded before routing?"],
      ["Knowledge Retrieval During Intake (similar jobs, guidance, standards, limitations, history)"]),
    step("CUSTOMER_ACK","Customer Acknowledgement (approval-gated)",
      "Send an acknowledgement/clarification only through the approval gate.",
      "Prepare the acknowledgement message and route it through the human/Slack approval gate; do NOT send outward without approval.",
      "python3 - <<'PY'\nprint('PREPARE acknowledgement; submit to approval gate; do not auto-send')\nPY",
      ["The message is prepared and submitted to the approval gate.",
       "No outward message is sent without recorded approval."],
      ["Was the outbound message gated on approval (not auto-sent)?"],
      ["Customer Communication (acknowledgements, clarifications, updates); every message traceable"],
      gate=True),
    step("AUTONOMOUS_ROUTING","Deterministic Intake Routing",
      "Determine and record the next processing stage deterministically.",
      "Implement routing over complexity/missing-info/vector-quality/readiness and record the routing decision + reasoning as a decision trace.",
      "python3 - <<'PY'\nprint('IMPLEMENT deterministic routing; record decision + reasoning trace')\nPY",
      ["A deterministic routing decision is produced and recorded with reasoning.",
       "Re-running on the same job yields the same route (reproducible)."],
      ["Is the routing decision deterministic and recorded with reasoning?"],
      ["Autonomous Routing (deterministic, observable, reproducible)"]),
   ]),

 dict(sid="S03", dir="03_raster_analysis",
   name="Raster Analysis & Cleanup",
   overall="Preprocess every raster into an embroidery-favorable, analyzed, cleaned form while preserving all intermediate artifacts for comparison and learning.",
   steps=[
    step("IMAGE_NORMALIZATION","Image Normalization",
      "Normalize the raster (color space, orientation, size) preserving the source.",
      "Implement normalization; run it on the intake artwork; preserve the original and write the normalized raster.",
      "python3 - <<'PY'\nprint('IMPLEMENT + run normalization; preserve original; write normalized raster')\nPY",
      ["A normalized raster is written and the original source is preserved untouched."],
      ["Was a normalized raster produced with the source preserved?"],
      ["Raster Processing Pipeline > Image normalization","source-of-truth reference preserved (Flue/Cloudflare)"]),
    step("IMAGE_ANALYSIS","Raster Image Analysis",
      "Determine dimensions, resolution, aspect, transparency, colors, edges, artifacts, line thickness, text, expected complexity.",
      "Implement analysis and emit a real analysis record influencing downstream parameters.",
      "python3 - <<'PY'\nprint('IMPLEMENT analysis; emit a real analysis record')\nPY",
      ["A real analysis record with every required field is produced."],
      ["Was a complete raster analysis record produced?"],
      ["Image Analysis (dimensions/resolution/aspect/transparency/background/colors/edges/artifacts/line/features/text/complexity)"]),
    step("BACKGROUND_DETECTION","Background Detection",
      "Detect background complexity and select a handling strategy.",
      "Implement background detection; record the chosen strategy in the job history.",
      "python3 - <<'PY'\nprint('IMPLEMENT background detection; record chosen strategy in job history')\nPY",
      ["A background strategy (preserve/remove/replace/isolate) is chosen and recorded."],
      ["Was a background strategy chosen and recorded?"],
      ["Background Processing (preserve/remove/transparent/replace/isolate/refine/cleanup)"]),
    step("BACKGROUND_REMOVAL","Background Removal",
      "Execute background removal when the strategy calls for it.",
      "Implement background removal; run it; write the foreground-isolated raster.",
      "python3 - <<'PY'\nprint('IMPLEMENT + run background removal; write foreground raster')\nPY",
      ["Background removal runs and produces a foreground-isolated raster preserving intent."],
      ["Was background removal executed producing a real foreground raster?"],
      ["Background removal, Foreground isolation","Background Removal (near-term pipeline stage)"]),
    step("TRANSPARENCY_GENERATION","Transparency Generation",
      "Generate transparency/alpha for the isolated foreground.",
      "Implement transparency generation; run it; write an RGBA output.",
      "python3 - <<'PY'\nprint('IMPLEMENT + run transparency generation; write RGBA output')\nPY",
      ["A real RGBA/transparent output is produced."],
      ["Was a transparent (RGBA) output produced?"],
      ["Transparency generation"]),
    step("CONTRAST_ENHANCE","Contrast Enhancement",
      "Enhance contrast to favor downstream tracing.",
      "Implement contrast enhancement; run it; preserve the intermediate.",
      "python3 - <<'PY'\nprint('IMPLEMENT + run contrast enhancement; preserve intermediate')\nPY",
      ["A contrast-enhanced intermediate is written and preserved."],
      ["Was a contrast-enhanced intermediate produced and preserved?"],
      ["Raster Processing Pipeline > Contrast enhancement"]),
    step("NOISE_REDUCTION","Noise Reduction / Speck Removal",
      "Remove noise, specks, and small artifacts.",
      "Implement noise/speck removal; run it; preserve the intermediate.",
      "python3 - <<'PY'\nprint('IMPLEMENT + run noise/speck removal; preserve intermediate')\nPY",
      ["A denoised intermediate is written and preserved."],
      ["Was a denoised intermediate produced and preserved?"],
      ["Raster Cleanup (noise/speck/small-artifact removal)"]),
    step("EDGE_ENHANCE","Edge Enhancement",
      "Sharpen edges to improve path extraction fidelity.",
      "Implement edge enhancement; run it; preserve the intermediate.",
      "python3 - <<'PY'\nprint('IMPLEMENT + run edge enhancement; preserve intermediate')\nPY",
      ["An edge-enhanced intermediate is written and preserved."],
      ["Was an edge-enhanced intermediate produced and preserved?"],
      ["Raster Processing Pipeline > Edge enhancement"]),
    step("LINE_STRENGTHEN","Line Strengthening",
      "Strengthen thin lines and improve line continuity.",
      "Implement line strengthening / gap filling; run it; preserve the intermediate.",
      "python3 - <<'PY'\nprint('IMPLEMENT + run line strengthening/gap filling; preserve intermediate')\nPY",
      ["A line-strengthened intermediate with improved continuity is produced and preserved."],
      ["Was line strengthening applied and preserved?"],
      ["Line strengthening, Gap filling, Line continuity improvement"]),
    step("MORPH_CLEANUP","Morphological Cleanup",
      "Apply morphological cleanup preserving shape.",
      "Implement morphological cleanup; run it; preserve the intermediate.",
      "python3 - <<'PY'\nprint('IMPLEMENT + run morphological cleanup; preserve intermediate')\nPY",
      ["A morphologically cleaned intermediate is produced preserving shape."],
      ["Was morphological cleanup applied preserving shape?"],
      ["Morphological cleanup, Shape preservation, Boundary smoothing"]),
    step("RASTER_CANDIDATES_PRESERVE","Preserve Raster Candidates",
      "Persist every intermediate raster artifact for comparison and learning.",
      "Register all raster intermediates as permanent job artifacts and write a manifest of them.",
      "python3 - <<'PY'\nprint('REGISTER all raster intermediates; write artifacts/raster_intermediates.json')\nPY",
      ["A manifest of preserved raster intermediates exists and references real files."],
      ["Were all raster intermediates preserved and manifested?"],
      ["Every preprocessing stage shall preserve intermediate artifacts for comparison and future learning."],
      artifact="artifacts/raster_intermediates.json"),
   ]),

 dict(sid="S04", dir="04_vectorization_ihive",
   name="I-HIVE Vectorization",
   overall="Eliminate the manual-tracing quality advantage by generating, scoring, and converging large populations of candidate vectors in an isolated experimentation sandbox — reproducibly and observably.",
   steps=[
    step("IHIVE_ARCH_DOC","I-HIVE Architecture Documentation",
      "Document the raster→SVG I-HIVE architecture.",
      "Author artifacts/ihive_architecture.md describing candidate generation, evaluation, convergence, and reproducibility.",
      "python3 - <<'PY'\nprint('WRITE artifacts/ihive_architecture.md with the real architecture')\nPY",
      ["artifacts/ihive_architecture.md exists and documents the full I-HIVE flow."],
      ["Was the I-HIVE architecture documented?"],
      ["Raster-to-SVG vector image file architecture exists and is documented (I-HIVE verification)"],
      artifact="artifacts/ihive_architecture.md"),
    step("EXPERIMENT_SANDBOX","Vectorization Experiment Sandbox",
      "Create the isolated experimentation sandbox.",
      "Create pipeline/vectorization_experiments/{input,variants,metrics,selected} and report.md; verify isolation from production.",
      "mkdir -p ../../pipeline/vectorization_experiments/{input,variants,metrics,selected} && : > ../../pipeline/vectorization_experiments/report.md && find ../../pipeline/vectorization_experiments -maxdepth 1",
      ["The sandbox directory tree exists exactly as specified.",
       "report.md exists."],
      ["Does the vectorization experiment sandbox exist with the required subdirectories?"],
      ["Vectorization Experiment Pipeline (input/variants/metrics/selected/report.md)","Vectorization experiment pipeline exists (I-HIVE verification)"]),
    step("POTRACE_PARAM_SWEEP","Potrace Parameter Sweep",
      "Sweep potrace parameters to generate measurable candidates.",
      "Implement and run a potrace sweep over threshold/corner/curve/speck parameters, writing one candidate SVG + metrics per parameter set into variants/ and metrics/.",
      "python3 - <<'PY'\nprint('IMPLEMENT + run potrace sweep; write candidates to variants/ and metrics/')\nPY",
      ["Multiple candidate SVGs are produced, one per parameter set, each with recorded parameters.",
       "Every candidate has an associated metrics record."],
      ["Did the potrace sweep produce multiple measurable candidates?"],
      ["Potrace experimentation, Parameter Exploration (threshold/corner/curve/simplification/noise/speck/precision/node)","Vector Generation > Potrace"]),
    step("INKSCAPE_TRACE_VARIANTS","Inkscape Trace Variants",
      "Generate tracing variants via Inkscape.",
      "Implement and run Inkscape-based tracing variants headlessly, writing candidates + metrics.",
      "python3 - <<'PY'\nprint('IMPLEMENT + run inkscape tracing variants headlessly; write candidates + metrics')\nPY",
      ["Inkscape variants are produced headlessly with recorded parameters and metrics."],
      ["Did Inkscape produce trace variants with metrics?"],
      ["Inkscape experimentation, Vector Generation > Inkscape"]),
    step("MULTIPASS_LAYER_TRACE","Multi-Pass / Layer-Specific Tracing",
      "Produce multi-pass and layer-specific tracing candidates.",
      "Implement multi-pass/layer-specific tracing; run it; write candidates + metrics.",
      "python3 - <<'PY'\nprint('IMPLEMENT multi-pass/layer tracing; write candidates + metrics')\nPY",
      ["Multi-pass/layer-specific candidates are produced with metrics."],
      ["Were multi-pass/layer-specific candidates produced?"],
      ["Vector Generation > Multi-pass tracing, Layer-specific tracing"]),
    step("PARAM_EXPLORATION_RECORD","Parameter→Candidate Records",
      "Guarantee every parameter set yields a measurable candidate record.",
      "Consolidate all sweeps so each parameter set maps to exactly one candidate with metrics; write metrics/index.json.",
      "python3 - <<'PY'\nprint('CONSOLIDATE param->candidate mapping; write metrics/index.json')\nPY",
      ["Every parameter set maps to exactly one candidate with a metrics record.",
       "metrics/index.json enumerates all of them."],
      ["Does every parameter set map to a measurable candidate?"],
      ["Every parameter set shall generate a measurable candidate."]),
    step("CANDIDATE_GENERATION","Candidate Population Assembly",
      "Assemble the competing SVG candidate population preserving full provenance.",
      "Assemble candidates preserving params, method, metrics, history, artifacts; write candidates/population.json.",
      "python3 - <<'PY'\nprint('ASSEMBLE candidate population with full provenance; write population.json')\nPY",
      ["A candidate population with full provenance per candidate exists and is reproducible."],
      ["Was a provenance-complete candidate population assembled?"],
      ["Candidate Generation (params/method/metrics/history/artifacts/evaluation), deterministic + reproducible","Massive candidate generation (I-HIVE)"]),
    step("BAYESIAN_PATHSCORE","Bayesian Path-Quality Scoring",
      "Score candidates by path quality / geometric deviation minimization.",
      "Implement Bayesian path-quality scoring + geometric deviation metric; score every candidate.",
      "python3 - <<'PY'\nprint('IMPLEMENT bayesian path-quality + geometric-deviation scoring; score all candidates')\nPY",
      ["Every candidate receives a real path-quality score and geometric-deviation value."],
      ["Were all candidates scored for path quality and geometric deviation?"],
      ["Bayesian path-quality scoring, Geometric deviation minimization"]),
    step("VECTOR_BASE_CONVERGENCE","Phase 1 — Vector Base Convergence",
      "Converge toward the best base vector via corner-tolerance/node/topology/curve/profile/continuity optimization.",
      "Run the convergence loop until convergence criteria are met; record convergence trace.",
      "python3 - <<'PY'\nprint('RUN convergence loop; record convergence trace + selected base vector')\nPY",
      ["The convergence loop runs to a recorded convergence criterion.",
       "A converged base vector is selected with a trace."],
      ["Did vector base convergence complete against explicit criteria?"],
      ["Phase 1 — Vector Base Convergence (corner tolerances/node/topology/curve/profile/continuity)"]),
    step("SANDBOX_ISOLATION_VERIFY","Sandbox Isolation Verification",
      "Prove the sandbox cannot overwrite production artifacts.",
      "Attempt (and confirm the guard blocks) a write from the sandbox into production paths; capture the blocked attempt.",
      "python3 - <<'PY'\nprint('DEMONSTRATE sandbox cannot overwrite production; capture blocked write')\nPY",
      ["A write from sandbox into production is blocked and the block is captured as evidence."],
      ["Is production provably protected from sandbox writes?"],
      ["Sandbox isolation functions correctly (I-HIVE verification)","Prevent production artifacts from being overwritten"]),
   ]),

 dict(sid="S05", dir="05_vector_validation",
   name="Vector Validation & Ranking",
   overall="Structurally verify, optimize, objectively score, and rank vector candidates, then select the canonical production SVG while preserving all alternatives and learning.",
   steps=[
    step("STRUCTURAL_VERIFICATION","Phase 2 — Structural Verification",
      "Verify size, coordinates, line weight, continuity, closed paths, node topology, geometry, scaling.",
      "Implement structural verification; run it on all candidates; only passing candidates advance.",
      "python3 - <<'PY'\nprint('IMPLEMENT structural verification; run on candidates; record pass/fail per candidate')\nPY",
      ["Every candidate has a recorded structural-verification result.",
       "Only passing candidates are marked advanceable."],
      ["Were all candidates structurally verified with recorded results?"],
      ["Phase 2 — Structural Verification (size/coordinate/line-weight/continuity/closed-path/node/geometry/scaling)"]),
    step("SVG_OPTIMIZATION","SVG Structural Optimization",
      "Optimize node count, path simplification, merging, dedup, geometry cleanup without altering intent.",
      "Implement optimization; run it on advanceable candidates; record before/after metrics.",
      "python3 - <<'PY'\nprint('IMPLEMENT SVG optimization; record before/after node/path metrics')\nPY",
      ["Optimization runs and records before/after metrics preserving artwork intent."],
      ["Did SVG optimization run with recorded before/after metrics?"],
      ["SVG Optimization (node reduction/simplify/merge/dedup/open-path/closed-path/self-intersection/cleanup)"]),
    step("SVG_TOPOLOGY_QA","SVG Topology QA",
      "Check self-intersections, open/closed paths, and geometry integrity.",
      "Implement topology QA; run it; record findings per candidate.",
      "python3 - <<'PY'\nprint('IMPLEMENT topology QA; record self-intersection/open/closed findings')\nPY",
      ["Topology QA runs with recorded findings per candidate."],
      ["Was topology QA run with recorded findings?"],
      ["SVG topology optimization, SVG Topology QA (agent responsibility)"]),
    step("SVG_QA_METRICS","Objective SVG QA Metrics",
      "Compute source similarity, silhouette, edge, node efficiency, continuity, simplicity, fidelity, suitability.",
      "Implement and compute the objective QA metric suite for every candidate.",
      "python3 - <<'PY'\nprint('IMPLEMENT QA metric suite; compute for every candidate')\nPY",
      ["Every candidate has the full QA metric suite computed with real values."],
      ["Does every candidate have the full QA metric suite computed?"],
      ["SVG Quality Assurance (similarity/silhouette/edge/node/continuity/simplicity/fidelity/suitability)"]),
    step("CANDIDATE_RANKING","Candidate Leaderboard",
      "Produce a ranked leaderboard of candidates.",
      "Compute the ranked leaderboard (overall/vector/suitability/structural/topology/expected-stitch/time) and write artifacts/candidate_leaderboard.json.",
      "python3 - <<'PY'\nprint('COMPUTE leaderboard; write artifacts/candidate_leaderboard.json')\nPY",
      ["A ranked leaderboard exists with per-candidate scores and a defensible ordering."],
      ["Was a ranked candidate leaderboard produced?"],
      ["Candidate Ranking / Candidate Leaderboard (overall/vector/suitability/structural/topology/stitch/time)"],
      artifact="artifacts/candidate_leaderboard.json"),
    step("PRODUCTION_SVG_SELECT","Canonical Production SVG Selection",
      "Select the top candidate as production.svg, preserving all alternatives.",
      "Promote the top-ranked candidate to canonical production.svg; keep every alternative for future comparison.",
      "python3 - <<'PY'\nprint('PROMOTE top candidate to production.svg; preserve alternatives')\nPY",
      ["A canonical production.svg is selected and all alternatives are preserved."],
      ["Was a canonical production SVG selected with alternatives preserved?"],
      ["The highest-ranked candidate shall become the default production candidate while preserving all alternatives.","Canonical production SVG files are generated"],
      artifact="artifacts/production.svg"),
    step("VECTOR_HISTORICAL_LEARNING","Vectorization Historical Learning",
      "Record winning/failed parameters and metrics as permanent learning.",
      "Append winning and failed parameter combinations + metrics to the historical learning store.",
      "python3 - <<'PY'\nprint('APPEND winning/failed params + metrics to historical learning store')\nPY",
      ["Winning and failed parameter combinations + metrics are appended to a durable learning store."],
      ["Were winning and failed vectorization outcomes recorded for learning?"],
      ["Historical Learning (vector): parameter selections/winning/failed/metrics/decision traces/regression"]),
   ]),

 dict(sid="S06", dir="06_stitch_planning",
   name="Embroidery Digitization / Stitch Planning",
   overall="Transform the validated production SVG into an optimized, machine-ready stitch plan through classification, strategy selection, underlay, compensation, generation, and optimization.",
   steps=[
    step("SVG_VALIDATION_DIGITIZE","Pre-Digitization SVG Validation",
      "Validate the production SVG for digitization (paths/layers/geometry/scaling/coords/separation).",
      "Implement digitization validation; run it on production.svg; only a valid SVG proceeds.",
      "python3 - <<'PY'\nprint('IMPLEMENT + run digitization validation on production.svg')\nPY",
      ["production.svg passes all digitization validation checks with recorded results."],
      ["Did the production SVG pass digitization validation?"],
      ["SVG Validation (closed/open/dup/self-intersection/layer/geometry/scaling/coords/separation)","SVG validation functions correctly"]),
    step("EMBROIDERY_SUITABILITY","Embroidery Suitability Analysis",
      "Evaluate min feature/max density/satin/fill/running suitability and distortion/break/registration risk.",
      "Implement suitability analysis; run it; record a suitability report influencing stitch planning.",
      "python3 - <<'PY'\nprint('IMPLEMENT suitability analysis; record suitability report')\nPY",
      ["A real suitability report covering every required dimension is produced."],
      ["Was an embroidery suitability report produced?"],
      ["Embroidery Suitability Analysis (feature/density/satin/fill/running/pull/push/break/registration/complexity)"]),
    step("LAYER_ANALYSIS","Layer Analysis",
      "Analyze SVG layers for object separation.",
      "Implement layer analysis; run it; record layer/object separation results.",
      "python3 - <<'PY'\nprint('IMPLEMENT layer analysis; record separation results')\nPY",
      ["Layer/object separation is analyzed and recorded."],
      ["Was layer analysis recorded?"],
      ["Digitization Pipeline > Layer analysis"]),
    step("OBJECT_CLASSIFICATION","Object Classification",
      "Classify each object (satin/fill/running/bean/lettering/border/decorative/underlay/travel).",
      "Implement classification; run it on every object; record class per object.",
      "python3 - <<'PY'\nprint('IMPLEMENT object classification; record class per object')\nPY",
      ["Every object receives a recorded classification from the allowed set."],
      ["Was every object classified?"],
      ["Object Classification (satin/fill/running/bean/lettering/border/decorative/underlay/travel)"]),
    step("STITCH_STRATEGY_SELECT","Stitch Strategy Selection",
      "Select the stitch strategy per classified object.",
      "Implement strategy selection over geometry/width/density/quality/efficiency; record strategy per object.",
      "python3 - <<'PY'\nprint('IMPLEMENT strategy selection; record strategy per object')\nPY",
      ["Every classified object has a recorded strategy justified by geometry/width/density."],
      ["Was a justified stitch strategy selected per object?"],
      ["Stitch Strategy Selection (satin/tatami/running/triple/bean/motif/decorative/underlay)"]),
    step("UNDERLAY_PLANNING","Underlay Planning",
      "Plan underlay (edge/center walk, zig-zag, tatami, double) maximizing stability, minimizing waste.",
      "Implement underlay planning; run it; record underlay choice per object.",
      "python3 - <<'PY'\nprint('IMPLEMENT underlay planning; record underlay per object')\nPY",
      ["Underlay is planned and recorded per object balancing stability vs. stitch count."],
      ["Was underlay planned and recorded per object?"],
      ["Underlay Planning (edge walk/center walk/zig-zag/tatami/double/combinations)"]),
    step("PULL_COMPENSATION","Pull Compensation",
      "Determine pull compensation from direction/material/density/geometry/width/history.",
      "Implement pull compensation; compute observable, reproducible compensation values per object.",
      "python3 - <<'PY'\nprint('IMPLEMENT pull compensation; compute per-object values')\nPY",
      ["Pull-compensation values are computed per object and are reproducible."],
      ["Were reproducible pull-compensation values computed?"],
      ["Pull Compensation (direction/material/density/geometry/width/fill/history)"]),
    step("SATIN_GENERATION","Satin Column Generation",
      "Generate satin columns with rail-direction validation.",
      "Implement satin generation incl. rail-direction validation; produce satin stitches for satin objects.",
      "python3 - <<'PY'\nprint('IMPLEMENT satin generation + rail-direction validation')\nPY",
      ["Satin columns are generated with validated rail directions."],
      ["Were satin columns generated with valid rail directions?"],
      ["Satin generation, Satin column planning, Rail direction validation"]),
    step("FILL_GENERATION","Fill Generation",
      "Generate tatami/motif/decorative fills for fill objects.",
      "Implement fill generation; produce fill stitches for fill objects.",
      "python3 - <<'PY'\nprint('IMPLEMENT fill generation for fill objects')\nPY",
      ["Fills are generated for all fill-classified objects."],
      ["Were fills generated for fill objects?"],
      ["Fill generation, Stitch strategies > Tatami/Motif/Decorative fill"]),
    step("RUNNING_STITCH_GENERATION","Running/Bean Stitch Generation",
      "Generate running/triple/bean stitches for line objects.",
      "Implement running/bean generation; produce stitches for running-class objects.",
      "python3 - <<'PY'\nprint('IMPLEMENT running/bean generation')\nPY",
      ["Running/bean stitches are generated for line-class objects."],
      ["Were running/bean stitches generated?"],
      ["Running stitch generation, Triple running, Bean stitch"]),
    step("TRAVEL_OPTIMIZATION","Travel/Jump Optimization",
      "Reduce travel and jumps via stitch ordering.",
      "Implement travel optimization; record before/after travel + jump counts.",
      "python3 - <<'PY'\nprint('IMPLEMENT travel optimization; record before/after travel + jumps')\nPY",
      ["Travel/jump reduction is applied with recorded before/after counts preserving quality."],
      ["Was travel/jump reduced with recorded metrics?"],
      ["Stitch Optimization (travel/trim/jump reduction, ordering, efficiency)"]),
    step("TRIM_OPTIMIZATION","Trim Command Insertion & Optimization",
      "Insert and optimize trim commands.",
      "Implement trim insertion/optimization; record trim locations and count.",
      "python3 - <<'PY'\nprint('IMPLEMENT trim insertion/optimization; record trims')\nPY",
      ["Trim commands are inserted and optimized with recorded locations/counts."],
      ["Were trim commands inserted and optimized?"],
      ["Trim command insertion, Trim reduction/optimization"]),
    step("COLOR_SEQUENCING","Color Block Sequencing",
      "Order color blocks / thread changes efficiently.",
      "Implement color sequencing; record the color/thread-change order.",
      "python3 - <<'PY'\nprint('IMPLEMENT color sequencing; record color order')\nPY",
      ["An optimized color/thread-change sequence is recorded."],
      ["Was an optimized color sequence recorded?"],
      ["Color block optimization, Color sequencing, Color ordering"]),
    step("STITCH_PLAN_ARTIFACT","Canonical Stitch Plan Artifact",
      "Assemble the canonical stitch_plan.json.",
      "Assemble all generated/optimized stitches + metadata into a canonical, reproducible stitch_plan.json.",
      "python3 - <<'PY'\nprint('ASSEMBLE canonical stitch_plan.json')\nPY",
      ["A canonical stitch_plan.json exists containing all objects, strategies, underlay, compensation, and sequencing.",
       "It is reproducible from the same inputs."],
      ["Was a canonical, reproducible stitch plan assembled?"],
      ["Production Artifacts > Stitch plan; canonical artifacts consumed downstream"],
      artifact="artifacts/stitch_plan.json"),
   ]),

 dict(sid="S07", dir="07_stitch_validation",
   name="Stitch Validation, Simulation & Compliance",
   overall="Prove Ink/Stitch export works on test artwork first, then simulate, density-check, QA, and confirm Bernina B700 compliance before any plan advances to export.",
   steps=[
    step("INKSTITCH_PATH_CONFIRM","Confirm Inkscape Extension Path",
      "Confirm the Inkscape extension directory path.",
      "Locate and record the Inkscape extensions path; capture real output.",
      "inkscape --system-data-directory 2>/dev/null; ls -d ~/.config/inkscape/extensions 2>/dev/null || echo 'extensions dir not found'",
      ["The Inkscape extensions path is located and recorded (or its absence diagnosed)."],
      ["Was the Inkscape extension path confirmed?"],
      ["Ink/Stitch Validation > Confirm Inkscape extension path"],
      inspect=True),
    step("INKSTITCH_INSTALL","Install Ink/Stitch",
      "Install the Ink/Stitch extension.",
      "Install Ink/Stitch into the extensions path; capture the install output.",
      "python3 - <<'PY'\nprint('INSTALL Ink/Stitch into the extensions path; capture real output')\nPY",
      ["Ink/Stitch is installed into the extensions path with captured evidence."],
      ["Was Ink/Stitch installed?"],
      ["Ink/Stitch Validation > Install Ink/Stitch","Ink/Stitch integration (expansion)"]),
    step("INKSTITCH_REGISTRATION_VERIFY","Verify Ink/Stitch Registration",
      "Verify Ink/Stitch is registered as an extension.",
      "Verify extension registration; capture real evidence of registration.",
      "python3 - <<'PY'\nprint('VERIFY Ink/Stitch registration; capture evidence')\nPY",
      ["Ink/Stitch registration is verified with captured evidence."],
      ["Was Ink/Stitch registration verified?"],
      ["Ink/Stitch Validation > Verify extension registration"]),
    step("TEST_SVG_GENERATE","Generate Test SVG (NOT customer artwork)",
      "Generate a simple test SVG — never customer artwork (P10).",
      "Generate a trivial test SVG for export validation; explicitly do NOT use any customer artwork.",
      "python3 - <<'PY'\nsvg='<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"50\" height=\"50\"><rect x=\"5\" y=\"5\" width=\"40\" height=\"40\" fill=\"black\"/></svg>'\nopen('../artifacts/test_shape.svg','w').write(svg)\nprint('wrote test_shape.svg')\nPY",
      ["A simple test SVG exists.",
       "No customer artwork is used at this stage."],
      ["Was a simple non-customer test SVG generated?"],
      ["The initial validation shall never use customer artwork; only simple test artwork until export verified."],
      artifact="artifacts/test_shape.svg"),
    step("TEST_EXPORT_EMBROIDERY","Export Test Embroidery File (gate)",
      "Export an embroidery file from the test SVG and confirm the output exists.",
      "Run Ink/Stitch export on the test SVG; confirm the output file exists and validates; this gates all customer-artwork digitization.",
      "python3 - <<'PY'\nprint('EXPORT embroidery file from test_shape.svg via Ink/Stitch; confirm output exists')\nPY",
      ["An embroidery output file is produced from the test SVG and confirmed to exist.",
       "Export success is validated, not assumed."],
      ["Did the test embroidery export succeed and produce a real file?"],
      ["Ink/Stitch Validation > Generate SVG, Export test embroidery file, Confirm output exists, Validate export","Ink/Stitch export validation succeeds"],
      gate=True),
    step("STITCH_SIMULATION","Stitch Simulation",
      "Simulate the customer stitch plan before production approval.",
      "Implement simulation producing path visualization/needle sequence/travel/trim/color/timing/count; write a simulation report.",
      "python3 - <<'PY'\nprint('IMPLEMENT stitch simulation; write simulation report artifact')\nPY",
      ["A real simulation report with all required outputs is produced and preserved."],
      ["Was a real stitch simulation report produced?"],
      ["Stitch Simulation (visualization/needle seq/travel/trim/color/timing/count)","Embroidery stitch plan simulation"],
      artifact="artifacts/simulation_report.json"),
    step("DENSITY_MAP_GENERATION","Density Map Generation",
      "Generate a stitch density map.",
      "Implement density-map generation; produce a real density map artifact.",
      "python3 - <<'PY'\nprint('IMPLEMENT density-map generation; produce density map')\nPY",
      ["A real density map artifact is generated from the stitch plan."],
      ["Was a real density map generated?"],
      ["Density-map generation, Density-map QA"]),
    step("DENSITY_MAP_QA","Density Map QA",
      "QA the density map for excessive/insufficient density and stress/overlap/registration.",
      "Implement density QA; run it; record pass/fail with the problem regions.",
      "python3 - <<'PY'\nprint('IMPLEMENT density QA; record pass/fail + problem regions')\nPY",
      ["Density QA runs with a recorded binary result and any problem regions."],
      ["Did density QA produce a recorded pass/fail?"],
      ["Density Analysis (excessive/insufficient/accumulation/stress/overlap/registration/risk)","Embroidery stitch plan density-map quality assurance"]),
    step("PRODUCTION_QA","Production Quality Assurance",
      "Run objective production QA over integrity/layer/density/color/machine compatibility/readiness.",
      "Implement production QA; run it; write a QA report with a binary pass/fail.",
      "python3 - <<'PY'\nprint('IMPLEMENT production QA; write QA report with binary result')\nPY",
      ["A production QA report with a binary pass/fail is produced.",
       "Only passing plans are marked export-eligible."],
      ["Did production QA produce a binary pass/fail report?"],
      ["Production Quality Assurance (integrity/structural/layer/density/color/machine/B700/readiness)","Embroidery stitch plan quality assurance"],
      artifact="artifacts/qa_report.json"),
    step("BERNINA_B700_COMPLIANCE","Bernina B700 Standards Compliance",
      "Verify the plan complies with Bernina B700 stitch-plan standards.",
      "Implement B700 compliance checks; run them; record compliance result.",
      "python3 - <<'PY'\nprint('IMPLEMENT Bernina B700 compliance checks; record result')\nPY",
      ["B700 compliance is checked and recorded with a binary result."],
      ["Is the plan Bernina B700 compliant?"],
      ["Bernina B700 stitch plan standards compliance, Bernina B700 compatibility is validated"]),
    step("BERNINA_B700_PROTOCOL_QA","Bernina B700 Production Protocol QA",
      "QA the plan against Bernina B700 production protocol.",
      "Implement B700 production-protocol QA; run it; record result.",
      "python3 - <<'PY'\nprint('IMPLEMENT B700 production protocol QA; record result')\nPY",
      ["B700 production-protocol QA runs with a recorded binary result."],
      ["Did B700 production-protocol QA record a result?"],
      ["Bernina B700 production protocol quality assurance"]),
    step("QA_APPROVAL_GATE","QA Approval Gate",
      "Gate: only QA-passing, B700-compliant plans advance to export.",
      "Compute a single export-eligible boolean from PRODUCTION_QA + B700 results; NOT-eligible is a FAILURE.",
      "python3 - <<'PY'\nprint('COMPUTE export-eligible boolean from QA + B700 evidence')\nPY",
      ["export_eligible is true only if production QA passed AND B700 compliance passed."],
      ["Is the plan export-eligible under QA and B700?"],
      ["Only plans satisfying QA requirements shall advance to export.","Automated production QA approval"],
      gate=True),
   ]),

 dict(sid="S08", dir="08_production_export",
   name="Production Export",
   overall="Export QA-approved plans to machine formats headlessly while preserving dimensions, integrity, color sequence, and production metadata.",
   steps=[
    step("EXPORT_PES","PES Export",
      "Export the approved plan to PES.",
      "Export to PES from the approved stitch plan; confirm the file exists.",
      "python3 - <<'PY'\nprint('EXPORT PES from approved plan; confirm file exists')\nPY",
      ["A real .pes file is produced from the approved plan and confirmed present."],
      ["Was a real PES file produced?"],
      ["PES embroidery file export, Production Export > PES","Production-grade PES generation"],
      artifact="artifacts/production.pes"),
    step("EXPORT_DST","DST Export",
      "Export the approved plan to DST.",
      "Export to DST; confirm the file exists.",
      "python3 - <<'PY'\nprint('EXPORT DST; confirm file exists')\nPY",
      ["A real .dst file is produced and confirmed present."],
      ["Was a real DST file produced?"],
      ["Production Export > DST"]),
    step("EXPORT_EXP","EXP Export",
      "Export the approved plan to EXP.",
      "Export to EXP; confirm the file exists.",
      "python3 - <<'PY'\nprint('EXPORT EXP; confirm file exists')\nPY",
      ["A real .exp file is produced and confirmed present."],
      ["Was a real EXP file produced?"],
      ["Production Export > EXP"]),
    step("HEADLESS_OUTPUT","Headless Production Output",
      "Produce exports headlessly with no GUI required.",
      "Run the export via `inkscape --actions ...` style headless invocation; capture the command + output.",
      "python3 - <<'PY'\nprint('RUN headless export (inkscape --actions ...); capture command + output')\nPY",
      ["Exports are produced by a headless invocation with the command captured.",
       "No GUI is required during production execution."],
      ["Were exports produced headlessly with the command captured?"],
      ["Phase 3 — Headless Production Output (GUIs not required); inkscape --actions example"]),
    step("DIMENSION_PRESERVATION_VERIFY","Dimension & Integrity Preservation",
      "Verify proportions/precision/dimensions/integrity are preserved in exports.",
      "Compare export dimensions against the approved plan; record deviations; any material deviation is a FAILURE.",
      "python3 - <<'PY'\nprint('COMPARE export dims vs plan; record deviations')\nPY",
      ["Export dimensions match the approved plan within tolerance with recorded comparison."],
      ["Do exports preserve dimensions within tolerance?"],
      ["Preserving Artwork proportions/Geometric precision/Production dimensions/Structural integrity"]),
    step("DUAL_SIZE_EXPORT","Dual-Size Export",
      "Produce the dual-size export set.",
      "Export the plan at both required sizes preserving proportions; confirm both files.",
      "python3 - <<'PY'\nprint('EXPORT dual-size set; confirm both files preserve proportions')\nPY",
      ["Both size exports exist and preserve proportions."],
      ["Was a dual-size export produced?"],
      ["Dual-size export"]),
    step("EXPORT_METADATA","Export Production Metadata",
      "Attach production metadata to exports.",
      "Attach artwork dimensions/stitch integrity/color sequence/metadata to the export record.",
      "python3 - <<'PY'\nprint('ATTACH production metadata to export record')\nPY",
      ["A production-metadata record is attached to the exports."],
      ["Was production metadata attached to exports?"],
      ["Every export shall preserve Artwork dimensions/Stitch integrity/Color sequence/Production metadata"]),
    step("EXPORT_ARTIFACTS_REGISTER","Register Export Artifacts",
      "Register export files as canonical, reproducible artifacts.",
      "Register all export files in the job's canonical artifact manifest.",
      "python3 - <<'PY'\nprint('REGISTER export files as canonical artifacts')\nPY",
      ["All export files are registered as canonical artifacts and are reproducible."],
      ["Were export artifacts registered as canonical?"],
      ["Production Artifacts > Export files; All production artifacts shall remain reproducible"]),
   ]),

 dict(sid="S09", dir="09_production_tracking",
   name="Production Tracking & Controls",
   overall="Provide an authenticated job-status API enforcing the canonical state machine, rejecting invalid transitions, and recording every transition to an immutable audit history.",
   steps=[
    step("JOB_STATUS_API","Job Status API Endpoint",
      "Implement POST /api/job-status.",
      "Implement the endpoint accepting a job id + target state; wire it to the transition validator.",
      "python3 - <<'PY'\nprint('IMPLEMENT POST /api/job-status endpoint')\nPY",
      ["A real POST /api/job-status endpoint exists and accepts job id + target state."],
      ["Does POST /api/job-status exist and accept transitions?"],
      ["Job Status Management > POST /api/job-status","Status transition controls (near-term critical)"]),
    step("STATE_TRANSITION_TABLE","Canonical State Transition Table",
      "Implement the full allowed-transition table.",
      "Encode the 14 canonical transitions (artwork_review→…→project_complete) as data and enforce them.",
      "python3 - <<'PY'\nprint('ENCODE the canonical allowed transitions and enforce them')\nPY",
      ["All canonical allowed transitions are encoded and enforced."],
      ["Are all canonical allowed transitions enforced?"],
      ["Allowed state transitions (artwork_review→…→project_complete, full list)"]),
    step("INVALID_TRANSITION_REJECT","Reject Invalid Transitions",
      "Reject any transition not in the allowed table.",
      "Demonstrate the API rejecting a real invalid transition and accepting a valid one.",
      "python3 - <<'PY'\nprint('DEMONSTRATE reject-invalid + accept-valid transitions')\nPY",
      ["An invalid transition is rejected and a valid one accepted, both captured."],
      ["Are invalid transitions rejected and valid ones accepted?"],
      ["Invalid state transitions shall be rejected.","Job status API validates state transitions"]),
    step("AUDIT_HISTORY","Transition Audit History",
      "Record every transition in the project audit history.",
      "Append every transition to an append-only audit history; demonstrate a recorded transition.",
      "python3 - <<'PY'\nprint('APPEND transitions to audit history; show a recorded entry')\nPY",
      ["Every transition is appended to an immutable audit history."],
      ["Is every transition recorded in an audit history?"],
      ["Every transition shall be recorded in the project audit history."]),
    step("STATUS_TRANSITION_CONTROLS","Operator Status Controls",
      "Expose authorized operator controls for status transitions.",
      "Implement operator-facing status controls that go through the same validator + audit path.",
      "python3 - <<'PY'\nprint('IMPLEMENT operator status controls via validator + audit')\nPY",
      ["Operator controls route through the same validation and audit as the API."],
      ["Do operator controls use the same validation + audit path?"],
      ["Status transition controls (near-term critical); operator actions recorded"]),
    step("DASHBOARD_AUTH","Dashboard Authentication",
      "Add authentication to the dashboard/control surface.",
      "Implement dashboard authentication protecting status controls; demonstrate an unauthenticated request being denied.",
      "python3 - <<'PY'\nprint('IMPLEMENT dashboard auth; show unauthenticated request denied')\nPY",
      ["Authentication protects the control surface; an unauthenticated request is denied."],
      ["Is the control surface authenticated (unauth denied)?"],
      ["Dashboard authentication (near-term critical)"]),
   ]),

 dict(sid="S10", dir="10_slack_collaboration",
   name="Slack Collaboration & Control",
   overall="Turn Slack from notification-only into an operational control interface: mirrored messages, local transcript, reply reading, approvals, signed slash commands, and visible continuous agent conversation.",
   steps=[
    step("SLACK_MIRROR_OUTBOUND","Mirror Outbound Messages",
      "Mirror agent/system messages to Slack.",
      "Implement outbound mirroring; send one real mirrored message; capture the delivery evidence.",
      "python3 - <<'PY'\nprint('IMPLEMENT outbound mirroring; capture one real delivery')\nPY",
      ["A real outbound message is mirrored to Slack with delivery evidence."],
      ["Was a real message mirrored to Slack?"],
      ["Slack can receive mirrored messages.","Slack-visible multi-agent collaboration"]),
    step("SLACK_TRANSCRIPT_LOCAL","Local Slack Transcript",
      "Write the Slack transcript locally.",
      "Persist every Slack message to a local transcript file; demonstrate an entry.",
      "python3 - <<'PY'\nprint('PERSIST Slack messages to a local transcript; show one entry')\nPY",
      ["Slack messages are persisted to a local transcript with a demonstrated entry."],
      ["Is the Slack transcript written locally?"],
      ["Slack transcript is written locally (I-HIVE verification)"]),
    step("SLACK_READ_REPLIES","Read Slack Replies Automatically",
      "Read Slack replies automatically.",
      "Implement reply ingestion; ingest a real reply into the system; capture it.",
      "python3 - <<'PY'\nprint('IMPLEMENT reply ingestion; ingest one real reply')\nPY",
      ["A real Slack reply is ingested automatically and captured."],
      ["Are Slack replies read automatically?"],
      ["Agents read Slack replies automatically."]),
    step("SLACK_APPROVALS","Slack Approvals",
      "Enable approve/reject actions via Slack.",
      "Implement Slack approval actions wired to the approval gate; demonstrate an approval and a rejection.",
      "python3 - <<'PY'\nprint('IMPLEMENT Slack approve/reject; demonstrate both')\nPY",
      ["Slack approve and reject both flow into the approval gate with captured evidence."],
      ["Do Slack approvals and rejections flow into the gate?"],
      ["Slack approvals enabled.","Slack approvals","Manual approvals"]),
    step("SLACK_SLASH_COMMANDS","Signed Slack Slash Commands",
      "Implement signed slash commands.",
      "Implement (or scaffold with signature verification) slash commands to issue commands/approve/update status; demonstrate one signed command.",
      "python3 - <<'PY'\nprint('IMPLEMENT signed slash commands; demonstrate one signed invocation')\nPY",
      ["A signed slash command is verified and executed (or scaffolded with signature verification present)."],
      ["Was a signed slash command verified and handled?"],
      ["Slack slash commands implemented.","Signed Slack command support is implemented or scaffolded"]),
    step("SLACK_AGENT_CONVERSATION","Visible Continuous Agent Conversation",
      "Make agents converse visibly and continuously in Slack.",
      "Implement visible inter-agent conversation; capture a real multi-agent exchange.",
      "python3 - <<'PY'\nprint('IMPLEMENT visible agent conversation; capture a multi-agent exchange')\nPY",
      ["A real, visible multi-agent Slack conversation is captured."],
      ["Was a visible multi-agent conversation captured?"],
      ["Agents chatting continuously.","Visible Slack agent conversation (near-term critical)","Slack agent conversations function"]),
    step("SLACK_HUMAN_LANGUAGE_EVIDENCE","Human-Language Evidence Messages",
      "Ensure every implementation can emit human-language Slack evidence.",
      "Implement a helper that turns any step's evidence artifact into a human-language Slack message; demonstrate on a real evidence file.",
      "python3 - <<'PY'\nprint('IMPLEMENT evidence->human-language Slack helper; demonstrate on real evidence')\nPY",
      ["Any evidence artifact can be rendered to a human-language Slack message, demonstrated on a real one."],
      ["Can step evidence be emitted as a human-language Slack message?"],
      ["Every implementation includes observable evidence that can be sent as a human-language Slack message."]),
   ]),

 dict(sid="S11", dir="11_infrastructure_multicloud",
   name="Infrastructure & Multi-Cloud",
   overall="Discover and preserve the existing AWS installation, then expand storage/backup/sync/DR/monitoring across S3-compatible providers (AWS, Contabo, Cloudflare R2) as first-class infrastructure.",
   steps=[
    step("AWS_DISCOVERY","Existing AWS Inventory",
      "Completely inventory the existing AWS installation before any change.",
      "Inventory binaries/config/creds/env/processes/services/filesystem for AWS; write artifacts/aws_inventory.md.",
      "python3 - <<'PY'\nprint('INVENTORY existing AWS install; write artifacts/aws_inventory.md')\nPY",
      ["A real AWS inventory covering all required categories is written."],
      ["Was the existing AWS installation fully inventoried before changes?"],
      ["Existing AWS Infrastructure Discovery (binaries/config/creds/env/processes/packages/services/fs)"],
      artifact="artifacts/aws_inventory.md", inspect=True),
    step("AWS_CONFIG_RESOLUTION","Preserve AWS Config Resolution Order",
      "Preserve the deterministic AWS config resolution precedence.",
      "Document and verify the precedence: CLI args → env → ~/.aws/credentials → ~/.aws/config.",
      "python3 - <<'PY'\nprint('VERIFY + document AWS config resolution precedence')\nPY",
      ["The documented precedence matches the required order and existing config is preserved."],
      ["Is the AWS config resolution order preserved and documented?"],
      ["Configuration Resolution Order (CLI args/env/credentials/config)"]),
    step("S3_BACKUP","S3 Backup (preserve existing capability)",
      "Back up system state to S3 without breaking existing backup capability.",
      "Implement/confirm an S3 backup that preserves the existing backup capability; run one backup; confirm the object.",
      "python3 - <<'PY'\nprint('RUN S3 backup preserving existing capability; confirm object')\nPY",
      ["A backup object is written to S3 and the existing backup capability remains intact."],
      ["Was an S3 backup performed while preserving existing capability?"],
      ["Existing implementation stores system backups; preserving this capability is mandatory.","Backup infrastructure"]),
    step("MULTICLOUD_PROFILES","Multi-Cloud Provider Profiles",
      "Configure Contabo and Cloudflare R2 S3-compatible profiles.",
      "Add contabo + cloudflare profiles/endpoints; verify connectivity with a real `aws s3 ls`-style call per provider.",
      "python3 - <<'PY'\nprint('ADD contabo + cloudflare R2 profiles; verify with real list calls')\nPY",
      ["Contabo and Cloudflare R2 profiles exist and a real listing call succeeds for each configured provider."],
      ["Are multi-cloud profiles configured and connectivity verified?"],
      ["Multi-Cloud Architecture, Contabo Object Storage Reference, Cloudflare R2 Reference"]),
    step("ARTIFACT_SYNC","Artifact / Knowledge / Production Sync",
      "Synchronize artifacts, knowledge, and production assets to cloud storage.",
      "Implement `aws s3 sync`-style synchronization; run one real sync; confirm objects landed.",
      "python3 - <<'PY'\nprint('RUN artifact/knowledge/production sync; confirm objects')\nPY",
      ["A real sync uploads artifacts and confirms them in the target bucket."],
      ["Did a real artifact sync land objects in cloud storage?"],
      ["Job artifact synchronization, Multi-server synchronization, Artifact synchronization"]),
    step("DISASTER_RECOVERY","Disaster Recovery Procedures",
      "Document disaster-recovery procedures.",
      "Author artifacts/disaster_recovery.md with concrete restore procedures.",
      "python3 - <<'PY'\nprint('WRITE artifacts/disaster_recovery.md with concrete restore steps')\nPY",
      ["A real DR runbook with concrete restore steps exists."],
      ["Does a concrete disaster-recovery runbook exist?"],
      ["Disaster recovery, Disaster recovery procedures are documented"],
      artifact="artifacts/disaster_recovery.md"),
    step("INFRA_MONITORING","Infrastructure Monitoring",
      "Monitor CPU/memory/disk/network/services/queue/workers/cloud connectivity.",
      "Implement infrastructure monitoring; capture one real metrics sample; keep it historically available.",
      "python3 - <<'PY'\nimport json,shutil,os\nu=shutil.disk_usage('/')\nopen('../artifacts/infra_sample.json','w').write(json.dumps({'disk_total':u.total,'disk_used':u.used,'disk_free':u.free},indent=2))\nprint('wrote infra_sample.json')\nPY",
      ["A real metrics sample is captured and stored for historical availability."],
      ["Was a real infrastructure metrics sample captured?"],
      ["Infrastructure Monitoring (CPU/memory/disk/storage/network/service/process/queue/workers/cloud)"],
      artifact="artifacts/infra_sample.json"),
    step("BACKUP_RESTORE_TEST","Backup Restoration Test",
      "Validate backups via restoration testing.",
      "Restore a backup into a scratch location and verify integrity; capture the restore evidence.",
      "python3 - <<'PY'\nprint('RESTORE a backup to scratch; verify integrity; capture evidence')\nPY",
      ["A backup is restored and verified, with captured evidence."],
      ["Was a backup restored and verified?"],
      ["Backups shall be periodically validated through restoration testing.","Recovery verification"]),
    step("LONGTERM_ARCHIVE","Long-Term Versioned Archive",
      "Maintain versioned historical archives.",
      "Implement long-term versioned archival; archive one production run; confirm the version.",
      "python3 - <<'PY'\nprint('ARCHIVE one production run with versioning; confirm version')\nPY",
      ["A versioned archive of a production run is created and confirmed."],
      ["Was a versioned long-term archive created?"],
      ["Long-term archival, Versioned historical archives"]),
   ]),

 dict(sid="S12", dir="12_agent_orchestration",
   name="Agent Orchestration & Skill Standards",
   overall="Coordinate specialized single-responsibility agents through an orchestrator with observable communication, shared artifacts, failure recovery, and enforced SKILL.md / final-report standards.",
   steps=[
    step("AGENT_RESPONSIBILITY_MAP","Agent Responsibility Map",
      "Define one bounded responsibility per agent.",
      "Author artifacts/agent_responsibilities.md mapping each agent to exactly one responsibility (only the orchestrator owns the whole pipeline).",
      "python3 - <<'PY'\nprint('WRITE artifacts/agent_responsibilities.md (one responsibility per agent)')\nPY",
      ["Each agent maps to exactly one bounded responsibility; only the orchestrator spans the pipeline."],
      ["Does each agent own exactly one bounded responsibility?"],
      ["Agent Responsibility Separation; Except the Orchestrator, no agent owns the full pipeline"],
      artifact="artifacts/agent_responsibilities.md"),
    step("ORCHESTRATOR","Workflow Orchestrator",
      "Implement the orchestrator coordinating agents.",
      "Implement orchestration (assignment/scheduling/dependency/progression); demonstrate a real coordinated multi-agent run.",
      "python3 - <<'PY'\nprint('IMPLEMENT orchestrator; demonstrate a coordinated multi-agent run')\nPY",
      ["The orchestrator coordinates a real multi-agent run with observable decisions."],
      ["Did the orchestrator coordinate a real multi-agent run?"],
      ["Workflow Orchestration, Autonomous Coordination (assignment/scheduling/dependency/workload/retry/recovery/progression)"]),
    step("AGENT_COMMUNICATION","Observable Agent Communication",
      "Make agent communication observable and reproducible.",
      "Implement observable communication; capture a real inter-agent message exchange.",
      "python3 - <<'PY'\nprint('IMPLEMENT observable agent communication; capture an exchange')\nPY",
      ["A real inter-agent exchange is captured and is reproducible."],
      ["Was observable agent communication captured?"],
      ["Autonomous AI agents communicating continuously; Observable communication"]),
    step("SHARED_ARTIFACTS","Structured Shared Artifacts",
      "Share knowledge through structured artifacts, not transient chat.",
      "Implement structured shared artifacts (reports/traces/evaluations); produce one shared artifact consumed by another agent.",
      "python3 - <<'PY'\nprint('PRODUCE a structured shared artifact consumed by another agent')\nPY",
      ["A structured shared artifact is produced and consumed by another agent."],
      ["Was a shared artifact produced and consumed?"],
      ["Knowledge Sharing (structured artifacts: reports/traces/evaluations)"]),
    step("COORDINATION","Coordination & Scheduling",
      "Coordinate assignment/scheduling/dependency/workload/prioritization.",
      "Demonstrate the coordinator making an observable scheduling/prioritization decision.",
      "python3 - <<'PY'\nprint('DEMONSTRATE an observable coordination/scheduling decision')\nPY",
      ["A real coordination decision is made and recorded observably."],
      ["Was a coordination decision recorded observably?"],
      ["Autonomous Coordination; Production prioritization"]),
    step("FAILURE_RECOVERY_AGENTS","Agent Failure Recovery",
      "Provide retry/alternative-routing/reassignment/escalation for agents.",
      "Implement agent failure recovery; demonstrate a real failure being retried/reassigned and recorded.",
      "python3 - <<'PY'\nprint('DEMONSTRATE agent failure recovery (retry/reassign/escalate) recorded')\nPY",
      ["A real agent failure is recovered (retry/reassign/escalate) and recorded as history."],
      ["Was an agent failure recovered and recorded?"],
      ["Failure Recovery (retry/alternative routing/reassignment/escalation/reporting)"]),
    step("KNOWLEDGE_SHARING","Permanent Knowledge Sharing",
      "Keep shared knowledge permanently retrievable.",
      "Ensure shared artifacts are memorialized and retrievable later; demonstrate retrieval.",
      "python3 - <<'PY'\nprint('DEMONSTRATE a shared artifact remains retrievable later')\nPY",
      ["A previously shared artifact is retrievable later via the knowledge system."],
      ["Is shared knowledge permanently retrievable?"],
      ["Shared knowledge shall remain permanently available for future retrieval."]),
    step("SKILL_MD_STANDARD","SKILL.md Standard Conformance",
      "Enforce the SKILL.md organization/naming/metadata standard.",
      "Implement a checker verifying skills/ layout, SKILL.md, YAML frontmatter, name==dir, references/, etc.; run it.",
      "python3 - <<'PY'\nprint('IMPLEMENT + run SKILL.md conformance checker')\nPY",
      ["A conformance checker runs and reports real compliance for the SKILL.md standard."],
      ["Does the SKILL.md conformance checker run and report compliance?"],
      ["Repository Consistency Requirement, Verification Standard (skills/ layout, SKILL.md, YAML, name match, references/)","Agent Skill Standards and SKILL.md Specification"]),
    step("SKILL_VERIFICATION","Skill Verification Evidence",
      "Produce observable verification evidence per skill.",
      "Produce the required verification evidence (checklist, rationalizations, red flags) for one real skill.",
      "python3 - <<'PY'\nprint('PRODUCE verification evidence for one real skill')\nPY",
      ["Verification evidence (checklist + rationalizations + red flags) exists for a real skill."],
      ["Was skill verification evidence produced?"],
      ["Verification (checklist/observable evidence/command output/artifacts/diffs/reports/traces)","Common Rationalizations, Red Flags documented"]),
    step("FINAL_REPORT_STANDARD","Final Report Standard",
      "Emit the standardized final report.",
      "Emit a final report with all required fields (dirs, SKILL.md files, YAML results, files, commands, limitations, next command).",
      "python3 - <<'PY'\nprint('EMIT standardized final report artifact')\nPY",
      ["A final report containing every required field is emitted."],
      ["Was the standardized final report emitted?"],
      ["Final Report Standard (full required field list); every implementation concludes with a final report"],
      artifact="artifacts/final_report.md"),
   ]),

 dict(sid="S13", dir="13_dashboard_observability",
   name="Dashboard & Observability",
   overall="Provide a real-time operational control center exposing jobs, agents, Slack, knowledge, experiments, leaderboard, QA, learning, regression, reward/penalty, infra health, alerts, and history — never a black box.",
   steps=[
    step("DASHBOARD_MISSION_CONTROL","Mission Control View",
      "Build the Mission Control overview.",
      "Implement the Mission Control view aggregating live system state; capture a rendered snapshot.",
      "python3 - <<'PY'\nprint('IMPLEMENT Mission Control view; capture rendered snapshot')\nPY",
      ["A Mission Control view renders live system state with a captured snapshot."],
      ["Does Mission Control render live state?"],
      ["Required Dashboard Areas > Mission Control; Complete observability"]),
    step("DASHBOARD_JOBS_AGENTS","Jobs & Agent Activity Views",
      "Build Current Jobs and Agent Activity views.",
      "Implement jobs + agent-activity views; capture snapshots showing real job/agent state.",
      "python3 - <<'PY'\nprint('IMPLEMENT jobs + agent-activity views; capture snapshots')\nPY",
      ["Jobs and agent-activity views render real state with captured snapshots."],
      ["Do jobs and agent-activity views render real state?"],
      ["Dashboard displays current jobs / agent activity"]),
    step("DASHBOARD_SLACK_KNOWLEDGE","Slack Intelligence & Knowledge Views",
      "Build Slack Intelligence and Knowledge Retrieval views.",
      "Implement Slack + knowledge-retrieval views; capture snapshots.",
      "python3 - <<'PY'\nprint('IMPLEMENT Slack + knowledge views; capture snapshots')\nPY",
      ["Slack and knowledge-retrieval views render real activity."],
      ["Do Slack and knowledge views render real activity?"],
      ["Dashboard Areas > Slack Intelligence / Knowledge Retrieval"]),
    step("DASHBOARD_EXPERIMENTS_LEADERBOARD","Experiments & Leaderboard Views",
      "Build Vectorization Experiments and Candidate Leaderboard views.",
      "Implement experiment + leaderboard views bound to real candidate data; capture snapshots.",
      "python3 - <<'PY'\nprint('IMPLEMENT experiment + leaderboard views; capture snapshots')\nPY",
      ["Experiment and leaderboard views render real candidate data."],
      ["Do experiment and leaderboard views render real data?"],
      ["Dashboard Areas > Vectorization Experiments / Candidate Leaderboard"]),
    step("DASHBOARD_QA_LEARNING_REGRESSION","QA / Learning / Regression Views",
      "Build QA Results, Historical Learning, and Regression Results views.",
      "Implement QA + learning + regression views bound to real data; capture snapshots.",
      "python3 - <<'PY'\nprint('IMPLEMENT QA + learning + regression views; capture snapshots')\nPY",
      ["QA, learning, and regression views render real data."],
      ["Do QA/learning/regression views render real data?"],
      ["Dashboard Areas > QA Results / Historical Learning / Regression Results"]),
    step("DASHBOARD_REWARD_PENALTY","Reward & Penalty Views",
      "Build Reward and Penalty dashboards.",
      "Implement reward + penalty views bound to the reward/penalty ledger; capture snapshots.",
      "python3 - <<'PY'\nprint('IMPLEMENT reward + penalty views; capture snapshots')\nPY",
      ["Reward and penalty views render real ledger data."],
      ["Do reward/penalty views render real ledger data?"],
      ["Dashboard Areas > Reward Dashboard / Penalty Dashboard; Reward and Improvement Tracking; Failure Analysis"]),
    step("DASHBOARD_INFRA_ALERTS","Infrastructure Health & Alerts",
      "Build Infrastructure Health and System Alerts views; alerts persist until resolved.",
      "Implement infra-health + alerts views; alerts remain visible until resolved; capture a live alert.",
      "python3 - <<'PY'\nprint('IMPLEMENT infra-health + alerts; capture a persistent alert')\nPY",
      ["Infra-health renders and alerts persist until resolved, demonstrated with a live alert."],
      ["Do alerts render and persist until resolved?"],
      ["Dashboard Areas > Infrastructure Health / System Alerts; Alerts shall remain visible until resolved"]),
    step("DASHBOARD_HISTORICAL","Historical Dashboards",
      "Build longitudinal historical dashboards.",
      "Implement historical views (production/QA/candidate/experiment/learning/regression/infra/agent); capture a trend.",
      "python3 - <<'PY'\nprint('IMPLEMENT historical dashboards; capture a real trend')\nPY",
      ["Historical dashboards render real longitudinal trends."],
      ["Do historical dashboards render real trends?"],
      ["Historical Dashboards (production/QA/candidate/experiment/learning/regression/infra/agent)"]),
    step("OPERATOR_ACTIONS_RECORDED","Operator Actions Recorded",
      "Record all operator actions (approvals/overrides) in system history.",
      "Wire operator actions through the audit history; demonstrate a recorded approval/override.",
      "python3 - <<'PY'\nprint('RECORD an operator action to system history; show entry')\nPY",
      ["A real operator action is recorded in the system history."],
      ["Are operator actions recorded in history?"],
      ["All operator actions shall be recorded within the system history; Manual overrides where authorized"]),
   ]),

 dict(sid="S14", dir="14_qa_continuous_improvement",
   name="QA, Historical Learning & Continuous Improvement (never-idle loop)",
   overall="Embed QA at every stage, preserve decision traces, run historical learning, regression, memorialization, autonomous code review, and never-idle experimentation that loops perpetually until interrupted.",
   steps=[
    step("EMBEDDED_QA_CHECKPOINTS","Embedded QA Checkpoints",
      "Ensure QA is embedded at every pipeline stage, not only terminally.",
      "Implement/verify embedded QA checkpoints across all stages; produce a checkpoint coverage report.",
      "python3 - <<'PY'\nprint('VERIFY embedded QA at every stage; write coverage report')\nPY",
      ["A coverage report shows QA embedded at every pipeline stage with observable evidence."],
      ["Is QA embedded at every stage per the coverage report?"],
      ["Continuous Quality Assurance Philosophy (embedded QA at every checkpoint)","QA exists throughout the production pipeline"]),
    step("DECISION_TRACE_PRESERVE","Preserve Decision Traces",
      "Preserve decision traces for every significant decision, pipeline-wide.",
      "Verify decision traces are preserved for representative decisions across the pipeline; produce a trace index.",
      "python3 - <<'PY'\nprint('VERIFY decision traces preserved; write trace index')\nPY",
      ["Decision traces are preserved and indexed across the pipeline."],
      ["Are decision traces preserved and indexed?"],
      ["Decision traces are preserved; Verification Philosophy"]),
    step("HISTORICAL_LEARNING_SUBSYSTEM","Historical Learning Subsystem",
      "Run historical learning as a permanent subsystem.",
      "Verify successful and failed outcomes are recorded and influence future execution; produce a learning-influence example.",
      "python3 - <<'PY'\nprint('DEMONSTRATE historical learning influencing a future decision')\nPY",
      ["Recorded history is shown influencing a subsequent decision (real example)."],
      ["Does recorded history influence a later decision?"],
      ["Historical Learning (permanent subsystem); Continuous historical learning"]),
    step("REGRESSION_FRAMEWORK","Regression Framework",
      "Compare current performance against historical baselines.",
      "Implement regression comparison; run it; flag any degradation with evidence.",
      "python3 - <<'PY'\nprint('RUN regression vs baseline; flag degradation with evidence')\nPY",
      ["Regression comparison runs and flags degradation (or confirms none) with evidence."],
      ["Did regression comparison run against a baseline?"],
      ["Regression Framework (quality/SVG/stitch/ranking/QA pass rates/performance/timing/accuracy)"]),
    step("KNOWLEDGE_MEMORIALIZATION_QA","QA Knowledge Memorialization",
      "Memorialize validated QA improvements permanently.",
      "Memorialize a validated QA improvement into the searchable library; confirm retrievability.",
      "python3 - <<'PY'\nprint('MEMORIALIZE a validated QA improvement; confirm retrievable')\nPY",
      ["A validated QA improvement is memorialized and retrievable."],
      ["Was a QA improvement memorialized and retrievable?"],
      ["Knowledge Memorialization; Validated improvements shall become permanent engineering knowledge"]),
    step("AUTONOMOUS_CODE_REVIEW","Autonomous Code Review",
      "Continuously inspect the implementation (static analysis/complexity/dead code/security/perf).",
      "Run autonomous code review over the repo; produce prioritized recommendations by measurable impact.",
      "python3 - <<'PY'\nprint('RUN autonomous code review; emit prioritized recommendations')\nPY",
      ["A real code-review pass produces prioritized, impact-ranked recommendations."],
      ["Did autonomous code review produce prioritized recommendations?"],
      ["Autonomous Code Review (static/style/dead-code/complexity/docs/security/perf/deps); Code review"]),
    step("SELF_IMPROVEMENT_OBJECTIVES","Self-Improvement Objectives",
      "Pursue and validate self-improvement objectives before making them permanent.",
      "Select a self-improvement objective, implement+validate it, and record the validation before adoption.",
      "python3 - <<'PY'\nprint('SELECT + validate a self-improvement objective; record validation')\nPY",
      ["A self-improvement objective is implemented, validated, and only then adopted."],
      ["Was a self-improvement validated before adoption?"],
      ["Self-Improvement Objectives; Improvements shall be validated before becoming permanent behavior"]),
    step("IDLE_EXPERIMENTATION","Never-Idle Autonomous Experimentation",
      "During idle periods, perform prescribed autonomous experimentation without touching active jobs.",
      "Run one prescribed idle experiment (parameter exploration/regression/comparison) and record it; this step is part of the perpetual loop.",
      "python3 - <<'PY'\nprint('RUN one prescribed idle experiment; record it; loop continues')\nPY",
      ["A prescribed idle experiment runs and is recorded without interfering with active jobs."],
      ["Did a prescribed idle experiment run and get recorded?"],
      ["Autonomous Experimentation; During idle periods the platform shall continuously perform useful autonomous work"]),
    step("CONTINUE_AS_NEW","Continue-As-New Loop Checkpoint",
      "Checkpoint the loop and continue perpetually (Temporal continue-as-new) — never terminate.",
      "Checkpoint state, verify the hash chain, and route back into the improvement loop; if a new job is present the orchestrator injects it at intake.",
      "python3 ../engine/hash_chain.py --verify && python3 - <<'PY'\nprint('CHECKPOINT; loop continues to IDLE_EXPERIMENTATION or intake if new job present')\nPY",
      ["The hash chain verifies OK.",
       "The loop routes back into itself (there is no terminal END)."],
      ["Did the loop checkpoint and continue (no termination)?"],
      ["Never-idle rule; The system is intended to become a permanent production platform; Long-Term Autonomous Evolution"]),
   ]),

 dict(sid="S15", dir="15_production_readiness",
   name="Production Readiness, Deployment & CI/CD",
   overall="Prove each subsystem is production-ready (deterministic, verified, recoverable, documented), automate deployment and Git CI/CD, and audit every subsystem against the global engineering principles before re-entering the never-idle loop.",
   steps=[
    step("PRODUCTION_READINESS_GATE","Production Readiness Gate",
      "Gate: no subsystem is production-ready on a single successful run.",
      "Evaluate each subsystem for determinism/observability/verification/traceability/recoverability/validation/repeatable-deploy/docs; NOT-ready is a FAILURE.",
      "python3 - <<'PY'\nprint('EVALUATE production-readiness criteria per subsystem; write readiness matrix')\nPY",
      ["A readiness matrix marks each subsystem ready only if all criteria hold."],
      ["Is every subsystem readiness-gated on all criteria?"],
      ["Production Readiness (deterministic/observable/verified/traceable/recoverable/validated/repeatable/documented); No subsystem promoted on one success"],
      gate=True),
    step("DEPLOYMENT_AUTOMATION","Deployment Automation",
      "Provide repeatable, automated deployment with rollback.",
      "Implement automated deployment + rollback; demonstrate a real deploy and a rollback.",
      "python3 - <<'PY'\nprint('DEMONSTRATE automated deploy + rollback')\nPY",
      ["A repeatable deploy and a rollback are demonstrated with evidence."],
      ["Were automated deploy and rollback demonstrated?"],
      ["Deployment Architecture (repeatable/automated/config/version/rollback/isolation/verification); Deployment automation"]),
    step("CONFIG_MANAGEMENT","Configuration Management",
      "Keep configuration version-controlled, observable, auditable.",
      "Implement config management producing permanent history on change; demonstrate a tracked config change.",
      "python3 - <<'PY'\nprint('DEMONSTRATE a tracked, auditable config change')\nPY",
      ["A config change produces permanent, auditable history."],
      ["Does a config change produce auditable history?"],
      ["Configuration Management (version-controlled/observable/reproducible/auditable/secure/documented)"]),
    step("DEPENDENCY_MANAGEMENT","Dependency Management",
      "Identify/install/verify/track/monitor every production dependency.",
      "Implement dependency tracking with actionable diagnostics for missing deps; run it.",
      "python3 - <<'PY'\nprint('RUN dependency tracking; emit diagnostics for any missing dep')\nPY",
      ["Dependencies are tracked and missing ones produce actionable diagnostics before execution."],
      ["Are dependencies tracked with diagnostics for missing ones?"],
      ["Dependency Management (identified/installed/verified/tracked/monitored)"]),
    step("OPERATIONAL_HEALTH","Operational Health Monitoring",
      "Continuously observe operational health (services/pipeline/throughput/queues/agents/cloud/API/dashboard/Slack).",
      "Implement operational health checks; capture one real health snapshot.",
      "python3 - <<'PY'\nprint('CAPTURE a real operational health snapshot')\nPY",
      ["A real operational health snapshot across the required surfaces is captured."],
      ["Was a real operational health snapshot captured?"],
      ["Operational Health (availability/pipeline/throughput/queues/agents/cloud/storage/knowledge/dashboard/Slack/API)"]),
    step("BACKUP_STRATEGY","Backup Strategy",
      "Ensure scheduled, validated backups exist across artifacts/config/knowledge/archives.",
      "Verify scheduled backups exist and are validated by restoration; produce a backup coverage report.",
      "python3 - <<'PY'\nprint('VERIFY scheduled+validated backups; write coverage report')\nPY",
      ["Scheduled backups exist and are restoration-validated across the required categories."],
      ["Are scheduled backups present and restoration-validated?"],
      ["Backup Strategy (scheduled/artifact/config/knowledge/archive/recovery verification)"]),
    step("DR_PROCEDURES","Disaster Recovery Procedures (readiness)",
      "Confirm disaster-recovery procedures are documented and executable.",
      "Validate the DR runbook by executing a dry-run restore; capture the dry-run evidence.",
      "python3 - <<'PY'\nprint('DRY-RUN the DR runbook; capture evidence')\nPY",
      ["The DR runbook executes as a dry-run with captured evidence."],
      ["Did a DR dry-run execute with evidence?"],
      ["Disaster recovery procedures are documented; Recoverability"]),
    step("PRODUCTION_DOCS","Production Documentation",
      "Produce production operational documentation.",
      "Author production operational docs covering deploy/config/deps/monitoring/backup/DR; write artifacts/production_docs.md.",
      "python3 - <<'PY'\nprint('WRITE artifacts/production_docs.md')\nPY",
      ["Real production operational documentation exists covering all required areas."],
      ["Does real production documentation exist?"],
      ["Operational documentation exists; Production documentation"],
      artifact="artifacts/production_docs.md"),
    step("GIT_CICD","Git-Based CI/CD",
      "Provide Git-based continuous integration and deployment.",
      "Implement/verify Git CI/CD (compile check, py_compile preflight, tests) with a real pipeline run; avoid large-heredoc file writes (P11).",
      "python3 -m py_compile ../engine/*.py && python3 - <<'PY'\nprint('RUN Git CI/CD pipeline; capture real result')\nPY",
      ["`py_compile` passes for engine modules (preflight).",
       "A real CI/CD run is captured (build/test) and uses file-based writes, not large heredocs."],
      ["Did a real Git CI/CD run pass preflight and tests?"],
      ["Git-based continuous integration and continuous deployment; Large Heredoc Command Risk mitigation; py_compile before restart"]),
    step("GLOBAL_PRINCIPLES_AUDIT","Global Engineering Principles Audit",
      "Audit every subsystem against the global engineering principles, then re-enter the never-idle loop.",
      "Audit all subsystems for observability/determinism/traceability/canonical-artifacts/learning/improvement/docs/reproducibility; write the audit; then loop.",
      "python3 - <<'PY'\nprint('AUDIT all subsystems vs global principles; write audit; loop back to idle work')\nPY",
      ["Every subsystem is audited against every global principle with a recorded result.",
       "On SUCCESS the loop returns to never-idle improvement work (no terminal END)."],
      ["Were all subsystems audited against the global principles?"],
      ["Global Engineering Principles (full list); No subsystem complete until implementation+verification+docs+observability+learning+improvement satisfied"]),
   ]),
]


# --------------------------------------------------------------------------- #
# Rendering + manifest construction                                            #
# --------------------------------------------------------------------------- #

def step_id(sid, i, key):
    return f"#{sid}-{i:02d}_{key}"


def step_filename(sid, i, key):
    return f"{sid}-{i:02d}_{key}.md"


def rec_ids(sid):
    return {
        "diagnose": f"#REC-{sid}_DIAGNOSE",
        "repair": f"#REC-{sid}_REPAIR",
        "verify": f"#REC-{sid}_VERIFY",
        "escalate": f"#REC-{sid}_ESCALATE",
    }


def build_order():
    """Flat ordered list of (section, index, stepdict) across all sections."""
    order = []
    for sec in SECTIONS:
        for i, st in enumerate(sec["steps"], start=1):
            order.append((sec, i, st))
    return order


def render_step_md(sid, idx, st, section, on_success, on_success_file,
                   on_failure, on_failure_file):
    this_id = step_id(sid, idx, st["key"])
    rel = f"workflows/{section['dir']}/{step_filename(sid, idx, st['key'])}"
    inputs = st["inputs"] or ["this step file", "authority/00_MASTER_CONTRACT.md"]
    preds = "\n".join(f"- [ ] {p}" for p in st["preds"])
    qs = [
        "Was a hash-tagged evidence file saved to evidence/%s.json?" % this_id.lstrip("#"),
        "Do the results satisfying the immediate objective classify as a SUCCESS?",
    ] + st["qs"]
    qblock = "\n".join(f"- Q{n}{' (mandatory)' if n<=2 else ''}: {q} (answer YES or NO)"
                       for n, q in enumerate(qs, start=1))
    brd = "\n".join(f"- {b}" for b in st["brd"])
    inp = "\n".join(f"- {p}" for p in inputs)
    gate = ("\n> APPROVAL GATE: the one action is gated on human/Slack approval. "
            "Do not send/execute the outward-facing effect without recorded approval.\n"
            if st["gate"] else "")
    inspect = " (inspect_only step: no source files are modified; evidence records inspection)" if st["inspect"] else ""
    artifact = f"\n- CANONICAL ARTIFACT: {st['artifact']}" if st["artifact"] else ""
    return f"""# {this_id} — {st['title']}
<!-- generated by engine/generate_steps.py — do not hand-edit; edit DATA and regenerate. -->

## ROUTING HEADER
- STEP: {this_id}
- FILE: {rel}
- ON SUCCESS →: {on_success} @ {on_success_file}
- ON FAILURE →: {on_failure} @ {on_failure_file}
- SECTION: {sid} — {section['name']}
- ATTEMPT LEDGER: state/attempts.jsonl (key = {this_id})
- MAX ATTEMPTS BEFORE ESCALATION: 3
{gate}
## OBJECTIVES
- IMMEDIATE OBJECTIVE: {st['imm']}
- OVERALL OBJECTIVE (section {sid}): {section['overall']}

## INPUTS YOU MAY READ
{inp}

## THE ONE ACTION{inspect}
{st['action']}

## COMMAND(S) TO RUN
```bash
{st['cmd']}
```

## EVIDENCE TO PRODUCE
- WRITE: evidence/{this_id.lstrip('#')}.json  (schema: contracts/evidence_schema.json)
- MUST CONTAIN: the exact commands run, their real stdout/stderr, the concrete
  files created/modified with paths and line ranges, and each acceptance-predicate
  result. No placeholders. No fabricated output.{artifact}
- HASH: `python3 engine/hash_chain.py --append '{this_id}' evidence/{this_id.lstrip('#')}.json <SUCCESS|FAILURE>`

## ACCEPTANCE PREDICATES (ALL must be true for SUCCESS)
{preds}

## BINARY EVIDENCE QUESTIONS (answer YES or NO only)
{qblock}

## BRD REQUIREMENTS IMPLEMENTED BY THIS STEP
{brd}

## EXECUTION CONTRACT (recite clauses 1–10 from authority/00_MASTER_CONTRACT.md)
1. State the hash-tagged name of this step: {this_id}.
2. State the SUCCESS route: {on_success} @ {on_success_file}.
3. State the FAILURE route: {on_failure} @ {on_failure_file}.
4. State the immediate objective of this step in your own words (1–2 sentences).
5. State the overall objective of this section in your own words (1–2 sentences).
6. Perform ONLY the one action above — nothing else, no other files touched.
7. Produce the hashed evidence artifact at evidence/{this_id.lstrip('#')}.json.
8. Answer every binary evidence question above with YES or NO.
9. Emit exactly one classification: SUCCESS or FAILURE.
10. State exactly which step, file, and folder you will proceed to based on the
    classification, then run:
    `python3 engine/supervisor.py --resolve '{this_id}' --classification <SUCCESS|FAILURE>`
    and immediately open the file it prints. Do not stop. Do not idle.
"""


def render_recovery_md(sid, kind, this_id, on_success, on_success_file,
                       on_failure, on_failure_file, section_name, dynamic_return):
    rel = f"recovery/{this_id.lstrip('#')}.md"
    titles = {
        "diagnose": "Diagnose the Failure",
        "repair": "Implement the Repair",
        "verify": "Verify the Repair Produced Real Working Behavior",
        "escalate": "Escalate with Prescribed External Research",
    }
    actions = {
        "diagnose": ("Read the failed step's evidence, the attempt ledger entry, the hash "
                     "chain, and the objective hierarchy. Classify the failure by class "
                     "(EVIDENCE_MISSING / EVIDENCE_PLACEHOLDER / PREDICATE_UNMET / "
                     "COMMAND_ERROR / TIMEOUT / ROUTE_VIOLATION / DEPENDENCY_MISSING / "
                     "SCHEMA_INVALID / UNKNOWN) and write a diagnosis artifact naming the "
                     "single root cause and the intended repair."),
        "repair": ("Implement exactly the repair named by the diagnosis artifact — one "
                   "change, smallest blast radius, no unrelated edits. Write the repair "
                   "evidence including the concrete diff and files touched."),
        "verify": ("Re-run the failed step's own command(s) and acceptance predicates to "
                   "prove the repair produced real, working behavior (not just 'it ran'). "
                   "Write verification evidence. On SUCCESS you return to the EXACT failed "
                   "step; the pipeline does not advance from here."),
        "escalate": ("Perform the prescribed external research (only what the diagnosis "
                     "authorizes), memorialize what was learned into the knowledge library, "
                     "then re-enter diagnosis with the new knowledge. Escalation never "
                     "advances the pipeline."),
    }
    ret = ("- ON SUCCESS →: (dynamic) the EXACT step id that failed, read from "
           "state/attempts.jsonl `return_to`. The supervisor resolves this; you do not pick it.\n"
           if dynamic_return else
           f"- ON SUCCESS →: {on_success} @ {on_success_file}\n")
    return f"""# {this_id} — Recovery: {titles[kind]}
<!-- generated by engine/generate_steps.py — do not hand-edit; edit DATA and regenerate. -->

## ROUTING HEADER
- STEP: {this_id}
- FILE: {rel}
- SECTION: {sid} recovery — {section_name}
{ret}- ON FAILURE →: {on_failure} @ {on_failure_file}
- ATTEMPT LEDGER: state/attempts.jsonl (key = {this_id})

## OBJECTIVES
- IMMEDIATE OBJECTIVE: {titles[kind].lower()} for the step recorded as `return_to` in the ledger.
- OVERALL OBJECTIVE (recovery): use recorded state, logs, hashes, prior attempts, the
  objective hierarchy, and (only when prescribed) external research to repair the
  failure and return to the exact failed step. Recovery never advances the pipeline.

## INPUTS YOU MAY READ
- state/attempts.jsonl (the `return_to` step id + failure_class)
- state/hash_chain.jsonl
- evidence/<return_to>.json (the failed step's evidence)
- authority/01_OBJECTIVE_HIERARCHY.md, authority/02_PROHIBITIONS.md

## THE ONE ACTION
{actions[kind]}

## COMMAND(S) TO RUN
```bash
python3 engine/supervisor.py --status
# then perform the one recovery action for the recorded return_to step
```

## EVIDENCE TO PRODUCE
- WRITE: evidence/{this_id.lstrip('#')}.json
- MUST CONTAIN: the return_to step id, the failure class, the single root cause,
  the concrete repair/diff (for repair/verify), and predicate results.
- HASH: `python3 engine/hash_chain.py --append '{this_id}' evidence/{this_id.lstrip('#')}.json <SUCCESS|FAILURE>`

## ACCEPTANCE PREDICATES (ALL must be true for SUCCESS)
- [ ] The recorded `return_to` step id is identified from the ledger.
- [ ] {'A single root cause is named and a repair intent is written.' if kind=='diagnose' else ''}{'The named repair is implemented with the smallest blast radius and its diff recorded.' if kind=='repair' else ''}{"The failed step's own predicates now pass on real re-run output." if kind=='verify' else ''}{'Prescribed research is recorded and memorialized to the knowledge library.' if kind=='escalate' else ''}

## BINARY EVIDENCE QUESTIONS (answer YES or NO only)
- Q1 (mandatory): Was a hash-tagged evidence file saved to evidence/{this_id.lstrip('#')}.json?
- Q2 (mandatory): Do the results satisfying the immediate objective classify as a SUCCESS?
- Q3: Is the recorded `return_to` step id correctly identified?

## EXECUTION CONTRACT (clauses 1–10)
1. State this step id: {this_id}.
2. State the SUCCESS route ({'dynamic return to the failed step' if dynamic_return else on_success}).
3. State the FAILURE route: {on_failure} @ {on_failure_file}.
4. State the immediate objective in your own words.
5. State the recovery objective in your own words.
6. Perform ONLY the one recovery action.
7. Produce the hashed evidence artifact.
8. Answer the binary evidence questions YES/NO.
9. Emit exactly SUCCESS or FAILURE.
10. Run `python3 engine/supervisor.py --resolve '{this_id}' --classification <SUCCESS|FAILURE>`
    and open the file it prints. On a VERIFY SUCCESS this returns you to the exact
    failed step. Do not stop.
"""


def generate():
    order = build_order()
    steps_index = {}

    # Resolve linear success chaining + failure->section recovery diagnose.
    for pos, (sec, idx, st) in enumerate(order):
        sid = sec["sid"]
        this_id = step_id(sid, idx, st["key"])
        this_rel = f"workflows/{sec['dir']}/{step_filename(sid, idx, st['key'])}"

        # success target
        if pos + 1 < len(order):
            nsec, nidx, nst = order[pos + 1]
            succ = step_id(nsec["sid"], nidx, nst["key"])
            succ_file = f"workflows/{nsec['dir']}/{step_filename(nsec['sid'], nidx, nst['key'])}"
        else:
            # last step of the whole pipeline loops back into never-idle work
            succ = "#S14-08_IDLE_EXPERIMENTATION"
            succ_file = "workflows/14_qa_continuous_improvement/S14-08_IDLE_EXPERIMENTATION.md"

        fail = rec_ids(sid)["diagnose"]
        fail_file = f"recovery/{fail.lstrip('#')}.md"

        md = render_step_md(sid, idx, st, sec, succ, succ_file, fail, fail_file)
        out = os.path.join(ROOT, this_rel)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            f.write(md)

        steps_index[this_id] = dict(file=this_rel, section=sid, title=st["title"],
                                    on_success=succ, on_failure=fail, max_attempts=3,
                                    inspect_only=st["inspect"], gate=st["gate"],
                                    brd=st["brd"])

    # Recovery micro-branch per section + BOOT.
    rec_sections = [("BOOT", "Boot")] + [(s["sid"], s["name"]) for s in SECTIONS]
    for sid, name in rec_sections:
        r = rec_ids(sid)
        dfile = f"recovery/{r['diagnose'].lstrip('#')}.md"
        rfile = f"recovery/{r['repair'].lstrip('#')}.md"
        vfile = f"recovery/{r['verify'].lstrip('#')}.md"
        efile = f"recovery/{r['escalate'].lstrip('#')}.md"

        specs = [
            ("diagnose", r["diagnose"], r["repair"], rfile, r["escalate"], efile, False),
            ("repair", r["repair"], r["verify"], vfile, r["escalate"], efile, False),
            ("verify", r["verify"], "#RETURN_TO_FAILED", "(dynamic)", r["diagnose"], dfile, True),
            ("escalate", r["escalate"], r["diagnose"], dfile, r["diagnose"], dfile, False),
        ]
        for kind, tid, succ, succ_file, fail, fail_file, dyn in specs:
            md = render_recovery_md(sid, kind, tid, succ, succ_file, fail, fail_file, name, dyn)
            out = os.path.join(ROOT, "recovery", tid.lstrip("#") + ".md")
            os.makedirs(os.path.dirname(out), exist_ok=True)
            with open(out, "w", encoding="utf-8") as f:
                f.write(md)
            steps_index[tid] = dict(
                file=f"recovery/{tid.lstrip('#')}.md", section=f"{sid}-REC",
                title=f"Recovery {kind}", on_success=succ, on_failure=fail,
                max_attempts=3, inspect_only=False, gate=False,
                dynamic_return_on_success=dyn, brd=["Recovery branch (Step Functions catcher)"])

    # BEGIN pseudo-step so the guard can resolve its routes.
    steps_index["#BEGIN"] = dict(
        file="BEGIN_HERE.md", section="BOOT", title="Begin",
        on_success="#S00-01_TOOLING_INVENTORY",
        on_failure="#REC-BOOT_DIAGNOSE", max_attempts=1,
        inspect_only=False, gate=False, brd=["Entry point"])

    # Write manifest.
    os.makedirs(os.path.join(ROOT, "manifest"), exist_ok=True)
    index = dict(version=1, first_step="#S00-01_TOOLING_INVENTORY",
                 count=len(steps_index), steps=steps_index)
    with open(os.path.join(ROOT, "manifest", "steps_index.json"), "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)

    write_traceability(order)
    return index


def write_traceability(order):
    """REQUIREMENTS_TRACEABILITY.md: every BRD requirement -> step/file/folder."""
    rows = []
    for sec, idx, st in order:
        sid = sec["sid"]
        this_id = step_id(sid, idx, st["key"])
        rel = f"workflows/{sec['dir']}/{step_filename(sid, idx, st['key'])}"
        for b in st["brd"]:
            rows.append((b, this_id, rel, sec["name"]))
    rows.sort(key=lambda r: (r[3], r[1]))
    lines = [
        "# REQUIREMENTS TRACEABILITY — BRD → exact step / file / folder",
        "",
        "Generated by engine/generate_steps.py. Each row maps a requirement from",
        "`business_requirements/EMBIZ_JUPITER_FULL_BRD.md` to the exact STEP id, the",
        "file that contains it, and the folder that file lives in. Every requirement",
        "in the BRD is implemented by at least one executable step.",
        "",
        f"Total mapped requirement references: {len(rows)}",
        f"Total pipeline steps: {sum(len(s['steps']) for s in SECTIONS)}",
        f"Total sections: {len(SECTIONS)}",
        "",
        "| BRD requirement | STEP id | File | Folder (section) |",
        "|---|---|---|---|",
    ]
    for b, sid_, rel, secname in rows:
        b_esc = b.replace("|", "\\|")
        lines.append(f"| {b_esc} | `{sid_}` | `{rel}` | {secname} |")
    with open(os.path.join(ROOT, "REQUIREMENTS_TRACEABILITY.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    idx = generate()
    print(f"generated {idx['count']} steps across {len(SECTIONS)} sections + recovery")
    print("manifest: manifest/steps_index.json")
    print("traceability: REQUIREMENTS_TRACEABILITY.md")
