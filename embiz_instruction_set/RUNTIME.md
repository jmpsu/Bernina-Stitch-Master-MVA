# RUNTIME — where this lives and how it runs on the VPS

This instruction set is designed to **live and run on the VPS at
`/root/projects/embiz`** (see `config/runtime.json`). The engine resolves all
paths relative to each file, so the tree runs in place wherever it is copied.

## One-time deploy (run ON the VPS)
```bash
# 1) Get the code onto the server (choose one):
#    a) git: from your clone of the repo
git -C /root/projects/embiz pull    # if already a clone, else:
git clone <your-repo-url> /root/projects/embiz/_repo && \
  cp -a /root/projects/embiz/_repo/embiz_instruction_set /root/projects/embiz/
#    b) or rsync the embiz_instruction_set/ directory to /root/projects/embiz/

# 2) Deploy + bring the loop online:
bash /root/projects/embiz/embiz_instruction_set/bin/deploy-to-vps

# 3) Build the NEW knowledge object library from the web archive + PDFs:
python3 /root/projects/embiz/embiz_instruction_set/engine/kb_build.py
```
`deploy-to-vps` preserves any existing `state/` and `evidence/` so a redeploy
never loses durable history.

## Knowledge object library
`engine/kb_build.py` reads `config/knowledge_sources.json` (all your archive
paths — `/root/web-archive/ai_agents_skills_library`, the EMBIZ_EXPORTS portable
+ focused-raster exports, and the existing global `*.jsonl` stores) and writes a
unified library to `/root/projects/embiz/knowledge_object_library/`:
- `knowledge_objects.jsonl` — newly ingested HTML + PDF (+md/txt/json) objects
- `global_knowledge_objects.jsonl` — new objects merged with your imported stores
- `visual_captions.jsonl` — image/figure assets (captions pending a visual model)
- `MANIFEST.json` — counts, roots scanned, skipped sources

The knowledge-library steps (`workflows/01_knowledge_library/`) drive and verify
this build; the retrieval interface (S01) reads from this library.

## Visual-fidelity attestation (mandatory)
Before a vectorized SVG is posited finished, and before a stitch plan/PES is made
from an SVG, the worker MUST run `engine/fidelity_compare.py` and state the
mandated confirmation sentence (see `authority/05_VISUAL_FIDELITY_MANDATE.md`),
which `validators/fidelity_attestation.py` enforces against real metrics.

## Optional deps that improve ingestion / fidelity on the VPS
- `pdftotext` (poppler-utils) or `pdfminer.six` — PDF text extraction
- `beautifulsoup4` — HTML text extraction
- `inkscape` or `cairosvg` — render SVG→PNG for fidelity comparison
- `Pillow` — image maths for fidelity comparison
Missing deps degrade explicitly (recorded as errors → FAILURE), never silently.
