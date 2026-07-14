---
name: knowledge-retrieval
description: Retrieves engineering guidance from the local knowledge library through the repo's retrieval router before any implementation or production decision. Use at the start of every pipeline task (mandatory retrieval gate) and when expanding the library; not a substitute for task-specific skills.
---

# Knowledge Retrieval

## Purpose

Make the local knowledge library the primary source of procedural knowledge:
agents retrieve validated, version-controlled guidance before generating
solutions, so methodology is durable and model-independent (BRD § "Knowledge
Retrieval, Engineering Memory, and Continuous Library Expansion").

## When to Use

- Before any vectorization, digitization, QA, or intake decision — retrieval
  is a mandatory gate, and finalization already enforces retrieval proof.
- When a task hits a knowledge gap (route the gap to Michaela's research
  contract; capture new findings via Marina/Maeve).

Not for: executing the production task itself — retrieve, then switch to the
owning skill.

## Required Inputs

- Agent name, job ID, task type, and a concrete query.
- The knowledge corpus under `knowledge/` (ingested via
  `local_agents/knowledge_ingest.py`).

## Repository Inspection Workflow

1. Read `local_agents/knowledge_retrieval.py` — the router (`route`,
   `load_corpus`, `score_record`) is the sanctioned retrieval path.
2. Check `knowledge/` and `reports/knowledge_audit.md` for corpus coverage
   and known gaps before assuming knowledge exists.

## Architecture Inspection Workflow

Retrieval sits upstream of every pipeline stage and is enforced as a
finalization gate (the knowledge gate — retrieval proofs are recorded with
finalized images). Ingestion (PDFs, web) feeds the corpus; retrieval routes
scored records to agents; capture memorializes new methodology back into the
corpus.

## Agent Responsibility Separation Rules

Retrieval serves every agent, but library expansion is contracted: research
gaps to Michaela, knowledge capture to Marina (visual) and Maeve
(documentation). Retrieval consumers do not write the corpus directly.

## Implementation Workflow

1. Formulate the query from the job's actual failure mode or decision point
   (not a generic topic).
2. Route it:

```bash
python3 local_agents/knowledge_retrieval.py --agent <name> --job <job_id> \
  --task-type <type> --query "<query>"
```

3. Apply source enforcement: only corpus-backed guidance counts as
   retrieval proof; absence of results is itself evidence (a recorded gap).
4. Record the retrieval proof (query, scored hits, chosen guidance) with the
   task's artifacts.
5. If a gap: file it to the research/capture contracts rather than
   improvising silently.

## Verification Workflow

- Automated: router output (scored records) captured verbatim.
- The finalization knowledge gate must find retrieval proofs for the job —
  the first production cycle's re-finalization recorded 5 retrieval proofs
  per image.

## Evidence Requirements

- The exact query and router invocation.
- Scored results (or the empty result recording a gap).
- The decision the guidance changed (decision trace reference).

## Common Rationalizations

| Rationalization | Why it is incorrect | Required corrective action |
|---|---|---|
| "I already know the answer." | Model memory is not durable engineering knowledge; the BRD requires retrieval-driven decisions. | Run the router; cite or record the gap. |
| "The corpus won't have this." | Unchecked assumptions hide real coverage; gaps must be recorded, not presumed. | Query anyway; file the gap if empty. |
| "Retrieval slows the pipeline." | The knowledge gate blocks finalization regardless; late retrieval costs more. | Retrieve first. |
| "I'll paste new knowledge straight into the corpus." | Ingestion and capture are contracted responsibilities with provenance rules. | Route through ingest/capture agents. |

## Red Flags

- Finalization attempted with no retrieval proofs on record.
- Guidance cited without a corresponding router query.
- The same gap hit repeatedly without a research task filed.
- Corpus edits without ingestion provenance.

## Final Report Format

Follow `skills/references/final-report-standard.md`, extended with: queries
run, proofs recorded, gaps filed, and corpus growth (records before/after).
