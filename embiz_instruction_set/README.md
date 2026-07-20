# EMBIZ / Jupiter — Deterministic Instruction-Set System (Draft C)

This directory is a **self-contained instruction section** meant to live inside a
larger Project folder. A worker (Claude or any model) dropped into this folder
follows the steps here, in a fixed order, under a deterministic supervisor. It is
**instructions only** — running the steps is what implements the EMBIZ platform;
this repository does not execute them for you.

It implements the **Draft C** architecture: an external deterministic supervisor
owns the loop, retries, hashes, checkpoints, and restart behavior; the worker
receives exactly one step at a time and cannot choose its own direction.

## Why this exists
Repeated autonomous interpretation, incomplete execution, context loss, false
completion, and unnecessary rewrites fragmented the project. This system replaces
worker discretion with a closed, auditable, never-idle loop where every step:
1. states what it understands, 2. performs one explicit action, 3. produces hashed
logs + concrete evidence, 4. validates as binary SUCCESS/FAILURE, 5. states its
predetermined destination, and 6. proceeds there immediately — with failures
entering a structured diagnosis/recovery branch that returns to the exact failed
step.

## Layout (top level)
- `BEGIN_HERE.md` — the only entry point.
- `authority/` — the non-negotiable contract, objective hierarchy, prohibitions,
  step anatomy, glossary. Read once at boot.
- `business_requirements/` — the full EMBIZ BRD (source of every requirement).
- `engine/` — supervisor + state machine + transition guard + evidence verifier +
  hash chain + recovery router + **generate_steps.py** (renders every step).
- `bin/` — `start-worker`, `resume-worker`, `inspect-state`.
- `contracts/` — JSON schemas for the manifest and evidence artifacts.
- `manifest/steps_index.json` — machine-readable routing authority (generated).
- `workflows/00…15/` — the pipeline sections, one folder each, one step per file.
- `recovery/` — per-section diagnose→repair→verify→escalate branches.
- `validators/` — binary validator + full self-test.
- `state/`, `evidence/`, `logs/`, `artifacts/` — durable runtime state.
- `REQUIREMENTS_TRACEABILITY.md` — every BRD requirement → exact step/file/folder.

## Build / regenerate
```bash
bash build_instruction_set.sh   # creates dirs, renders steps, inits state, self-tests
```

## Run the loop (what the worker does)
```bash
bash bin/start-worker                    # prints the first step file to open
# open OPEN_THIS_FILE, execute exactly one step under its EXECUTION CONTRACT, then:
python3 engine/supervisor.py --resolve '#S00-01_TOOLING_INVENTORY' --classification SUCCESS
# open the next file it prints; repeat forever (never-idle loop).
```

## Design lineage
Temporal (durable hash history + continue-as-new), AWS Step Functions (bounded
retries then a mandatory catcher), W3C SCXML (only declared transitions are
legal), Apache Airflow (observable task lifecycle). See `authority/04_GLOSSARY.md`.
