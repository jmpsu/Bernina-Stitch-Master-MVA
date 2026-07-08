# Knowledge Audit — 2026-07-08 (container session claude/slack-session-kgbmsg)

Honest inventory of what knowledge exists IN THIS CONTAINER versus what the
Multimodal Knowledge Objects spec references on the user's local (Mint)
machine, plus the ingestion/retrieval work done in this session.

## 1. Disk

- `/` (all of `/home/user` lives here): 252G total, 7.5G used, 30G available (21% of quota) — healthy.
- Repo `Bernina-Stitch-Master-MVA`: 49M total. Largest members: `production_runs/` 8.2M, `vectorized_svg/` 7.3M, `stitch_plans/` 3.5M, `vectorization_attempts.jsonl` 2.7M, `vector_source/` 2.4M.
- New `knowledge/library/`: 1.9M (dominated by the three committed source PDFs).

## 2. Spec-referenced corpora roots — NOT PRESENT here

The spec's primary knowledge roots exist on the user's local machine, not in
this container:

| Path | Status in this container |
|---|---|
| `/root/web-archive/` (incl. `ai_agents_skills_library/*.jsonl`) | **NOT PRESENT** |
| `/root/EMBIZ_EXPORTS/` | **NOT PRESENT** |

Root discovery is implemented in `local_agents/knowledge_ingest.py::discover_library_roots()`:
`$EMBIZ_KNOWLEDGE_ROOTS` (override) → `/root/web-archive/ai_agents_skills_library`
→ `/root/EMBIZ_EXPORTS` → `knowledge/library/` (in-repo portable fallback).
On the user's Mint machine the /root corpora become PRIMARY automatically; in
this container only the in-repo fallback resolves.

## 3. Upload inventory (`/root/.claude/uploads/8072825f-8d96-59ba-8443-e3f358bb097a/`)

| File | Size | Notes |
|---|---|---|
| `0beace62-SVG_Tutorial.pdf` | 108 KB | 8 pages (W3Schools SVG tutorial print) — INGESTED |
| `5b9b89fe-Potrace.pdf` | 1.5 MB | **10 pages** (potrace project page: description, algorithm options, technical documentation links) — INGESTED. NOTE: the task brief described it as the 15-page Selinger paper; the actual upload is the 10-page potrace site document. Recorded honestly. |
| `88425ea8-The_Anatomy_of_a_Vector_IllustrationPart_One.pdf` | 93 KB | 2 pages — INGESTED |
| `ceffc337-EMBIZ_Jupiter_Embroidery_Autonomous_Agent_Owned_FULL_VERSION.md` | 169 KB | spec document (also in repo as `EMBIZ_Jupiter_LOCAL_FIRST_Autonomous_Agent_FULL_VERSION.md`) |
| `inkstitch-gh-pages.zip` | — | **NOT PRESENT** in uploads. The `14-ink-stitch-automation-framework/documents` corpus could NOT be built. |
| Bernina B700 manual PDFs | — | **NOT PRESENT** in uploads. The `bernina-b700` corpus could NOT be built. |

## 4. Repo knowledge stores (pre-existing, line counts)

- `vectorization_attempts.jsonl` 5028 · `observations.jsonl` 331 · `knowledge_experiments.jsonl` 237 · `local_agents/state/transcripts/agent_feed.jsonl` 233 · `reports/agent_meetings.jsonl` 32 · `reports/milestones.jsonl` 13 · `decision_trace.jsonl` 12 · `reward_penalty_ledger.jsonl` 11
- `knowledge/vectorization/{color,curve,edge,noise}_agent/` — 16 technique-note JSON objects + `parameter_correlation_index*.json`.

## 5. New knowledge library (`knowledge/library/`) — built this session

| Corpus | File | Objects |
|---|---|---|
| raster-to-vector (`5-agent-architecture/raster-to-vector-agent/`) | `knowledge_objects.jsonl` | 36 (Potrace, 10 pages) |
| vector-design (`5-agent-architecture/vector-design-agent/`) | `knowledge_objects.jsonl` | 4 (Anatomy of a Vector Illustration, 2 pages) |
| svg-specification (`9-knowledge-management-architecture/svg-specification-corpus/`) | `knowledge_objects.jsonl` | 10 (SVG Tutorial, 8 pages) |
| embroidery-techniques (`14-ink-stitch-automation-framework/embroidery-techniques/`) | `visual_captions.jsonl` | 1 (CustomLettering00.png caption entry; image itself unreachable — `image_path: null`, fetch error recorded) |
| global | `global_knowledge_objects.jsonl` | 50 |
| global multimodal | `global_knowledge_objects.multimodal.jsonl` | 15 (objects on pages with embedded images, + the caption entry) |

Source PDFs copied to `knowledge/library/sources/` (committed). Every
ingestion/fetch attempt is logged in `knowledge/library/ingestion_log.jsonl`.

## 6. #LIBRARY URL fetch outcomes — ALL FAILED (honest record)

All silverseams.com fetches failed: the container's egress proxy denies the
host (`CONNECT tunnel failed: 403 Forbidden`, confirmed policy denial in
`$HTTPS_PROXY/__agentproxy/status`). WebFetch also returned HTTP 403, and
web.archive.org is blocked. Attempted 2026-07-08, errors recorded per-URL in
`knowledge/library/ingestion_log.jsonl`:

- https://silverseams.com/tutorials/ — FAILED (proxy 403)
- https://silverseams.com/tutorials/digitizing-outlined-graphics.html — FAILED (proxy 403)
- https://silverseams.com/tutorials/using-a-5x12-hoop-on-a-5x7-embroidery-machine.html — FAILED (proxy 403)
- https://silverseams.com/tutorials/color_sorting_with_ink_stitch.html — FAILED (proxy 403)
- https://silverseams.com/tutorials/digitizing_with_ink_stitch/index.html — FAILED (proxy 403)
- https://silverseams.com/tutorials/satin-joins-and-corners.html — FAILED (proxy 403)
- https://silverseams.com/tutorials/cropping-with-inkstitch.html — FAILED (proxy 403)
- https://silverseams.com/pictures/CustomLettering00.png — image download FAILED (proxy 403); caption entry created with `image_path: null`

Re-running `python3 local_agents/knowledge_ingest.py url <url> 14-ink-stitch-automation-framework/embroidery-techniques`
on a machine with open egress (e.g. the user's Mint box) will populate the corpus.

## 7. Retrieval router + hard gates (built this session)

- `local_agents/knowledge_retrieval.py` — `route(agent, job_id, task_type, query, ...)`;
  agent→corpora map for specialists (Mila, Melanie, Mckenna, Meredith,
  Miranda, Mackenzie, Monica) and run personas (Maya→Mila's, Marnie→Mckenna+Miranda's,
  Mercy→Mackenzie's, Mabel→global). Every call appends proof to
  `reports/retrieval_log.jsonl`.
- HARD GATES verified live: Mckenna retrievals report
  `MISSING_REQUIRED_CORPUS: ink-stitch-docs`; Miranda reports
  `MISSING_REQUIRED_CORPUS: bernina-b700` (strict mode raises
  `KnowledgeGateError`). These are REAL missing-corpus failures — the source
  material (inkstitch zip, B700 manuals) is not in this container.
- Wired into `local_agents/continuous_run.py::mabel_knowledge_pass` →
  `_finalization_retrievals`: finalization now routes weakness-derived
  queries for Mabel + Mila + Mckenna + Melanie + Miranda; proofs are stored
  in the finalization record and the retrieval log. Verified on the real
  re-finalization of `cr_img_0293` (5 retrievals, 25 objects selected, 2 gate
  failures recorded honestly).

## 8. What must happen on the user's machine to close the gaps

1. Provide `inkstitch-gh-pages.zip` (or run ingest where /root/web-archive exists) → builds `ink-stitch-docs`, clears Mckenna/Meredith/Marnie gates.
2. Provide Bernina B700 manual PDFs → builds `bernina-b700`, clears Miranda's gate.
3. Fetch the silverseams tutorials from an unproxied network → populates `embroidery-techniques`.
4. Visual-semantics / visual-qa / inkscape / svg-conformance corpora have no source material in this container at all.
