# EMBIZ Deep Inventory Follow-up Log — 2026-07-08

## Scope

This log records the local audit run, terminal failures, hotfixes, audit interpretation, safety boundary for credential inventory, and next implementation gates for the EMBIZ deep inventory work.

Repository: `jmpsu/Bernina-Stitch-Master-MVA`

Audit branch / PR: `assistant/embiz-deep-inventory-audit-20260708` / PR #6

Related implementation PR: PR #5, `claude/embiz-paused-run-inspect-r5x91e`

## What happened locally

The first audit command failed because the shell was in `/home/jmmint/embroidery_business_agent_system`, which is not a Git checkout. Git operations returned:

```text
fatal: not a git repository (or any of the parent directories): .git
python3: can't open file '/home/jmmint/embroidery_business_agent_system/tools/embiz_deep_inventory_audit.py': [Errno 2] No such file or directory
```

A follow-up wrapper located the actual checkout at:

```text
/home/jmmint/Documents/clone_embroidery_business_agent_system
```

That checkout was already on:

```text
assistant/embiz-deep-inventory-audit-20260708
```

The audit then crashed while inspecting the production knowledge roots because the laptop user could not stat root-only paths:

```text
PermissionError: [Errno 13] Permission denied: '/root/web-archive/ai_agents_skills_library'
```

## Hotfix applied locally

A local hotfix was applied to `tools/embiz_deep_inventory_audit.py` so inaccessible paths are treated as inaccessible inventory facts instead of fatal exceptions.

The helper behavior added locally:

- `path_exists()` catches `OSError` / permission errors.
- `path_is_file()` catches permission errors.
- `path_is_dir()` catches permission errors.
- `path_size()` catches permission errors.
- `path_readable()` and `path_writable()` report access state without crashing.
- `safe_rglob()` and `safe_glob()` avoid crashing on unreadable directory trees.

After this hotfix, the audit completed and wrote:

```text
reports/embiz_deep_inventory.json
reports/embiz_deep_inventory.md
```

## Audit results observed from local run

Runtime files reported as present / OK:

- `vectorizer.py`
- `digitizer.py`
- `run_iteration.py`
- `metrics.py`
- `local_agents/continuous_run.py`
- `local_agents/knowledge_ingest.py`
- `local_agents/knowledge_retrieval.py`
- `local_agents/model_router.py`
- `local_agents/qwen_client.py`
- `local_agents/slack_daemon.py`
- `local_agents/agent_loop.py`
- `local_agents/personas.py`

Open PR discovery succeeded through `gh`.

PR #6 state from local report:

- Open
- Draft
- Mergeable
- CI / CodeQL checks green at the time of the report

PR #5 state from local report:

- Open
- Not draft
- Mergeable
- CI / CodeQL checks green at the time of the report

## Knowledge root results observed

The laptop audit could not read the VPS-style production roots:

```text
/root/web-archive/ai_agents_skills_library
/root/EMBIZ_EXPORTS
```

The laptop-visible repo library was:

```text
/home/jmmint/Documents/clone_embroidery_business_agent_system/knowledge/library
```

Observed local corpus counts:

- `raster-to-vector`: present, 36 records
- `vector-design`: present, 4 records
- `svg-specification`: present, 10 records
- `embroidery-techniques`: present only as 1 visual caption
- `global`: present, 65 records
- `visual-semantics`: missing
- `inkscape`: missing
- `svg-conformance`: missing
- `ink-stitch-docs`: missing
- `bernina-b700`: missing
- `visual-qa`: missing

Blocked knowledge gates from local report:

- `mckenna`: missing `ink-stitch-docs`
- `meredith`: missing `ink-stitch-docs`
- `miranda`: missing `bernina-b700`
- `mackenzie`: missing `visual-qa`
- `marnie`: missing `ink-stitch-docs`, `bernina-b700`
- `mercy`: missing `visual-qa`

## URL coverage interpretation correction

The first successful audit reported all attached URL seeds as covered.

That result is misleading because each URL row pointed to:

```text
tools/embiz_deep_inventory_audit.py
```

That only proves the audit tool contains the hard-coded expected URL list. It does not prove that the URLs were recursively fetched, converted, or ingested into JSONL.

Required audit correction:

- Exclude `tools/embiz_deep_inventory_audit.py` from URL coverage evidence.
- Exclude generated audit reports such as `reports/embiz_deep_inventory*` from URL coverage evidence.
- Treat URL seed coverage as real only when evidence appears in crawled artifacts, source archives, or JSONL knowledge records.

Expected result after correction:

- URL seed ingestion should likely become blocked or partial until the crawler output is present in readable knowledge roots.

## Cloudflare / AWS customer-facing surface

The audit reported:

```text
cloudflare customer-facing surface: missing cloudflare_aws_surface_incomplete_or_absent
```

The required surface checked by the audit includes:

- `wrangler.toml`
- `functions/_middleware.ts`
- `functions/api/quote.ts`
- `functions/api/order.ts`
- `functions/api/upload.ts`
- `functions/api/contact.ts`
- `terraform/main.tf`
- `terraform/variables.tf`
- `terraform/outputs.tf`
- `.github/workflows/deploy-cloudflare-pages.yml`
- `.github/workflows/deploy-aws.yml`
- `aws/lambdas/`
- `package.json`

This should be handled on a separate implementation branch after the audit branch is corrected.

## Credential / secret inventory safety boundary

The user requested recursively searching for keys, passwords, logins, AWS, Cloudflare, Contabo, Slack, and GitHub credentials.

The safe rule established for this repository:

- Do not dump credential values into GitHub.
- Do not create a single document containing all secrets.
- Do not commit tokens, passwords, API keys, private keys, or login values.
- Only create inventory reports that list likely secret-containing file paths, categories, sizes, hashes, and a note that values were intentionally not extracted.

Safe generated local inventory targets:

```text
reports/secret_file_inventory.jsonl
reports/secret_file_inventory.tsv
```

These files must be reviewed before any commit. They should not be committed unless confirmed to contain no secret values.

## Local URL inventory

A local URL inventory script was provided to scan readable text files from common user roots and write:

```text
reports/local_url_inventory.jsonl
reports/local_url_inventory.tsv
```

These outputs may contain private URLs or operational endpoints. They must be reviewed before commit.

## Required next actions

1. Commit/push the unreadable-path crash fix in `tools/embiz_deep_inventory_audit.py`.
2. Commit/push the URL coverage correction that excludes the audit tool and generated reports from coverage evidence.
3. Rerun the audit.
4. Confirm URL coverage becomes real ingestion evidence rather than self-reference evidence.
5. Decide whether to import/copy the production knowledge library into a readable laptop location, such as:

```text
/home/jmmint/web-archive/ai_agents_skills_library
```

6. Re-run the audit with `EMBIZ_KNOWLEDGE_ROOTS` set if the real library exists elsewhere.
7. Do not merge PR #5 until the generated production artifacts are intentionally reviewed.
8. Do not merge PR #6 until the audit tool can run without hotfixing locally and its URL-coverage result is truthful.

## Non-negotiable audit standard

The audit must distinguish between:

- expected configuration constants,
- local runtime wiring,
- generated reports,
- real crawled source artifacts,
- real JSONL knowledge ingestion,
- root paths that are unavailable due to permissions,
- corpora that are actually missing.

A passing audit must never count its own expected-list constants as proof of ingestion.
