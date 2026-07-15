# EMBIZ BRD — Spec Coverage Census

Line-by-line map of every unique BRD requirement to its implementation and
test evidence. Canonical spec: `docs/requirements/EMBIZ_BRD.md`. Statuses:
**BUILT** (implemented + exercised in the E2E corpus run) · **PARTIAL** ·
**EXTERNAL** (requires the operator's machine or cloud accounts — cannot run
or be verified from this repository alone) · **N/A-HERE** (spec describes the
other system root `/root/embroidery_business_agent_system`).

Evidence pointers reference: `reports/e2e/pass_NN.json` (per-image pipeline
results over the full `input_images/` corpus), `jobs/<id>/` (canonical
artifacts + audit), `dashboard/index.html`, `reports/alerts.jsonl`,
`reports/regression_history.jsonl`.

## 1. Vision & permanent design requirements

| BRD requirement | Status | Implementation / evidence |
|---|---|---|
| Refine existing system, not replace | **BUILT** | All modules extend the existing repo (`digitizer.py`, `vectorizer.py`, `local_agents/`); PR #5/#6 branch work merged in, not rewritten. |
| Email/artwork/specs → SVG → stitch plans → verified machine files | **BUILT** | `production_pipeline.py` drives the full chain; per-image evidence in `reports/e2e/`. |
| Never stops; useful idle work | **EXTERNAL** | systemd units (`local_agents/systemd/`, `Restart=always`, idle rescan loop in `continuous_run.py`) — runs on the operator's machine. |
| Everything observable/testable/measurable | **BUILT** | Every stage writes JSON evidence; dashboard renders 15 areas from artifacts only. |
| Slack mirroring, agents read replies, approvals, slash commands, continuous chat | **PARTIAL/EXTERNAL** | Mirroring + structured events: `local_agents/agent_bus.py` (+ local feed fallback). Reply-reading & slash commands live in `slack_daemon.py` and need Slack tokens on the host. |

## 2. Agent skill standards (Critical)

| Requirement | Status | Evidence |
|---|---|---|
| `skills/` + `SKILL.md` spec, naming, frontmatter, sections, rationalizations, red flags | **BUILT** | 6 skills; `scripts/validate_skills.py` — all checks PASS. |
| Verification + Final Report standards | **BUILT** | Encoded in `skills/references/`; PR bodies follow them. |

## 3. Named roster → runtime contracts

| Requirement | Status | Evidence |
|---|---|---|
| 18×M roster compiled to machine-readable contracts (12 fields) | **BUILT** | `scripts/compile_agent_contracts.py` → `agents/contracts/*.json`; validator: 389 checks PASS. |
| Runtime loads contracts | **BUILT** | `local_agents/personas.py` (`CONTRACTS`, `contract_for`, roster personas registered). |
| Contract-structured approval/rejection messages | **BUILT** | `agent_bus.approval_event` / `rejection_event` — required elements are mandatory arguments; live samples in `reports/slack_messages/` + job audits. |

## 4. I-HIVE target engine

| Capability (BRD list) | Status | Evidence |
|---|---|---|
| Locked background tracing layer | **BUILT** | `ihive.add_locked_tracing_layer` / `strip_archival_layers`; `<img>_work.svg` vs `<img>_production.svg` per pass. |
| Automatic raster cleanup / background removal / transparency | **BUILT** (pre-existing) | `digitizer.remove_background` (corner+Otsu+Sobel), `vectorizer._presmoothed_source`. |
| Multi-stage preprocessing, path extraction, multi-variant generation | **BUILT** (pre-existing) | `vectorizer.optimize` multi-start coordinate descent. |
| **Bayesian path-quality scoring** | **BUILT** | `ihive.bayes_rank_candidates` (Beta acceptance × Gaussian composite lower bound over the 7k-attempt ledger); seeds every E2E vectorization (`extra_starts`). |
| Potrace/Inkscape experimentation | **PARTIAL** | vtracer engine in production; potrace/inkscape not installed in this container (host tooling requirement, BRD "Required Tooling"). |
| SVG structural cleanup / topology optimization | **BUILT** (detection + rejection loop) | `svg_topology_qa.py` (8 checks; blocking gates reject to re-vectorization). |
| Satin column planning / rail validation | **BUILT** (pre-existing) | `digitizer._satin_border_runs` + width/density caps. |
| **Underlay planning** | **BUILT** | `digitizer` UNDERLAY_* constants + inset tatami pass; `underlay_runs` in every sidecar/E2E row. |
| **Pull compensation** | **BUILT** | `PULL_COMP_MM` row-axis dilation; recorded per sidecar. |
| Trim command insertion | **BUILT** (pre-existing) | `TRIM_JUMP_MM`; `trim_count` in stats. |
| **Color block optimization** | **BUILT** | Same-color region grouping + single thread block per color in `digitize_object`. |
| **Dual-size export** | **BUILT** | `DUAL_SIZE_MM = (76.2, 127.0)`; `*_5in.exp/pes/inf/bmp` emitted per object; `dual_size_export` per E2E row. |
| Stitch simulation | **BUILT** (pre-existing) | `render_preview` PNG per plan. |
| Density-map generation/QA | **BUILT** (pre-existing) | `_density_report`, 1.2/mm² blocking gate. |
| Automated production QA approval | **BUILT** | Margaret approval events after density+hoop gates in `production_pipeline.py`. |
| Continuous historical learning | **BUILT** (pre-existing + Bayesian layer) | attempts ledger, param index, transplant (PR #5), `bayes_rank_candidates`. |

## 5. Intake (BRD "Customer Artwork Intake")

| Stage | Status | Evidence |
|---|---|---|
| Sources: email webhook, .eml, file drops | **BUILT** | `local_agents/intake.py` (`run_intake`), `webhook_api.py` POST `/cloudflare-email`. Gmail/Slack-DM intake **EXTERNAL** (host credentials). |
| Attachment extraction (rasters, vectors, PDFs, embroidery, office, archives) | **BUILT** | `extract_attachments` (MIME + zip, categorized inventory); tested live with real attachment. |
| Artwork identification (type/format/resolution/transparency/bg complexity/colors/dominant) | **BUILT** | `identify_artwork`; recorded in `intake_analysis.json` per job. |
| Artwork review (quality/noise/compression/thin lines/small features/text/edges/suitability) | **BUILT** | `review_artwork`; `artwork_review.md` per job. |
| Complexity analysis → budgets/QA thresholds | **BUILT** | `complexity_analysis`; drives vectorizer budget + SSIM floor in E2E. |
| Missing information detection → clarification requests | **BUILT** | `missing_information` + `missing_questions.md` + Melody draft reply. |
| Canonical artifacts: intake_summary.md, job.json, raw_email.json, missing_questions.md, artwork_review.md | **BUILT** | All five per job — exact BRD filenames. |
| Knowledge retrieval before routing, recorded | **BUILT** | `knowledge_retrieval.route` proof in `intake_retrieval.json` + `reports/retrieval_log.jsonl`. |
| Autonomous deterministic routing | **BUILT** | Route + reason recorded per job; complexity-based. |

## 6. Job status management

| Requirement | Status | Evidence |
|---|---|---|
| POST /api/job-status | **BUILT** | `webhook_api.py`; live-tested. |
| Exact allowed-transition chain; invalid rejected | **BUILT** | `jobs.ALLOWED_TRANSITIONS` (BRD list verbatim); `InvalidTransition` → HTTP 409; smoke + live tests. |
| Every transition audited | **BUILT** | `jobs/<id>/audit.jsonl`. |

## 7. Dashboard & human oversight

| Requirement | Status | Evidence |
|---|---|---|
| All 15 BRD dashboard areas | **BUILT** | `local_agents/dashboard.py`; presence asserted programmatically. |
| **Dashboard authentication** (critical near-term) | **BUILT** | Bearer/`?token=` on every route; 401 verified live. |
| **Status transition controls** (critical near-term) | **BUILT** | POST `/api/job-status` (operator actor, audited). |
| Manual approvals / overrides recorded | **BUILT** | POST `/api/approve` → contract-structured event + audit. |
| Alerts visible until resolved | **BUILT** | `reports/alerts.jsonl` + `resolve_alert` + dashboard System Alerts area. |
| Historical views (production/QA/regression/learning) | **BUILT** | Dashboard areas fed from ledgers + `regression_history.jsonl`. |

## 8. QA / learning / regression

| Requirement | Status | Evidence |
|---|---|---|
| Verification with observable evidence, decision traces | **BUILT** | per-stage JSON, `decision_trace.jsonl` (pre-existing), job audits. |
| Regression framework | **BUILT** | `scripts/regression_check.py` → `reports/regression_history.jsonl` + regression alerts. |
| Reward/penalty tracking | **BUILT** (pre-existing) | `reward_penalty_ledger.jsonl`, dashboard areas. |
| Knowledge memorialization / library expansion | **BUILT** (pre-existing) | `knowledge_ingest.py`, stall-break notes, milestone ledger. |
| Autonomous code review / self-improvement | **PARTIAL** | Audit tool (`tools/embiz_deep_inventory_audit.py`, PR #6) + validators; no autonomous reviewer loop in-repo. |

## 9. Infrastructure (AWS / Cloudflare / multi-cloud / IAC)

| Requirement | Status | Evidence |
|---|---|---|
| Internal webhook API (email intake, job API) | **BUILT** (local) | `webhook_api.py` — the BRD's endpoint shapes, stdlib only. |
| Cloudflare tunnel / Worker ingress / Agents SDK + Flue runtime | **EXTERNAL** | Requires Cloudflare account + wrangler on host; contracts (`agents/contracts/`) are the operating layer it must enforce. |
| AWS discovery, S3/DynamoDB, Terraform, R2/Contabo sync | **EXTERNAL** | Account credentials required; matrix regions AWS/IAC remain to be provisioned. |
| Infrastructure notification pipeline | **PARTIAL** | Alert ledger + Slack-channel routing built; host webhook delivery external. |
| Ink/Stitch + Inkscape validation protocol | **EXTERNAL** | BRD requires host-installed Inkscape/Ink/Stitch; validation steps documented, `pyembroidery` export path used meanwhile. |

## 10. E2E verification (BRD verification standards)

Per-pass, per-image evidence over the full `input_images/` corpus (98 images
reconstructed from committed artifacts — original customer sources are
never committed by policy):

- `reports/e2e/pass_NN.json` — ssim, composite, topology QA, objects,
  max density vs 1.2/mm² limit, underlay runs, hoop fit, dual-size,
  companion files, final job status per image.
- `reports/e2e/pass_NN/` — per-image `_work.svg` / `_production.svg` /
  `_svg_qa.json` + stitch outputs (EXP/PES/INF/BMP/preview, both sizes).
- `jobs/` — one canonical job per image per pass with full audit chain.
- `reports/regression_history.jsonl` — pass-over-pass metric verdicts.
