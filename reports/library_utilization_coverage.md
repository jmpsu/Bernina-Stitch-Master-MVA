# Library utilization coverage matrix

_Every local library source on `origin/mila/embiz-agent-system` (enumerated via a read-only git worktree) mapped to at least one concrete knowledge artifact/concept it contributes AND the specific application point in THIS repo, classified honestly._

**Classification**

- **Class A — transform:** applied to the vectorization / stitch-plan transform (potrace/inkscape/inkstitch -> tracer/stitch params in vectorizer.py / digitizer.py).
- **Class B — pipeline engineering:** applied to how the system is built / verified / logged (TDD -> harness, observability -> ledgers, bounded search -> performance, etc.).
- **unused:** honest 'no current application' — the source has no real touchpoint here.

## Coverage summary

- **Sources total:** 39 (15 doctrine files + 24 skill packs)
- **Class A (transform):** 3 — potrace, inkscape, inkstitch
- **Class B (pipeline engineering):** 33
- **Unused (no current application):** 3 — masterdnsvpn, browser-testing-with-devtools, interview-me

Honest note: only 3 sources are Class A. The tracing/stitch doctrine (potrace, inkscape, inkstitch) is the sole material that touches the actual transform; every other source is a software-engineering methodology or infrastructure pattern that shaped HOW the pipeline was built, verified and logged — genuine Class B value, but not vectorization relevance. Three sources have no honest application at all and are marked unused rather than fabricated.

## Doctrine files (directives/repo_adapted_embiz_doctrine/)

| source | knowledge artifact / concept | application point in this repo | class | status |
|---|---|---|---|---|
| `potrace` | turdsize->filter_speckle, alphamax->corner_threshold, opticurve->mode, opttolerance->splice/path_precision (potracelib.h params) | vectorizer.DOCTRINE_SEED['default'] (v5-promoted: filter_speckle=1, corner_threshold=40, mode=polygon, splice_threshold=30) via knowledge_agents curve_agent + noise_agent | A (transform) | applied |
| `inkscape` | max_thread_colors<=15, delta_e<=5.0 color-merge, HSL matching, <=0.5mm path deviation | vectorizer color params: color_precision cap, layer_difference<-deltaE, promoted_hierarchical() gate (cutout<15 colors), colormode=color; via knowledge_agents color_agent | A (transform) | applied |
| `inkstitch` | SVG path -> stitch element pipeline (Fill/Satin/Stroke), node/element-count as a topology quality target | digitizer.py stitch-plan transform (_fill_runs boustrophedon fill, _contour_runs outline, ROW_SPACING_MM/MAX_STITCH_MM) + knowledge_agents edge_agent node-count -> path_precision budget (thin) | A (transform) | applied |
| `00_MASTER_REPO_SYNTHESIS` | cross-source synthesis / index-of-sources pattern | knowledge/vectorization/INDEX.md (source-mining index) + this reports/library_utilization_coverage.md matrix | B (pipeline) | applied |
| `addyosmani-agent-skills` | SDLC skills lifecycle (spec->plan->build->verify->review->ship), Prove-It / evidence-based assertions | parent source of skills/embiz-agent-skills (24 packs); governs how this pipeline is built, reviewed and shipped | B (pipeline) | applied |
| `agentsview` | local-first session analytics; FTS/append-only event capture; token/cost tracking; observability of multi-agent runs | the append-only JSONL ledgers: vectorization_attempts.jsonl, knowledge_experiments.jsonl, decision_trace.jsonl, observations.jsonl | B (pipeline) | applied |
| `crm-ai-analysis` | SQL-injection detection / input-validation agent (RAG text-to-SQL, CLTV/RFM analytics not relevant to imaging) | weak analogue only: the _ALLOWED param whitelist + int/float coercion in vectorizer.trace() (defensive input validation); no CRM/DB/RAG surface exists here | B (pipeline) | applied-weak |
| `hexo-ai-sia` | self-improving loop: generate -> execute -> feedback -> improve (meta-learning across generations) | the coordinate-descent hill-climb evaluate/accept loop in vectorizer.optimize() + the Stage-1 extract -> Stage-2 validate improvement cycle (knowledge_agents -> experiment_harness.py) | B (pipeline) | applied |
| `masterdnsvpn` | DNS-tunneling VPN, ARQ retransmit, multi-path failover, censorship resistance | no current application: a network-transport/censorship tool with no touchpoint in a deterministic raster->SVG->stitch pipeline | unused | unused |
| `mattermost` | CI automation, observability dashboards (agents/tokens/perf), team messaging/outbound reporting, config-as-code | outbound reporting pattern -> reports/slack_utilization_report.md + Slack drafts (sub-task C); observability -> the JSONL ledgers | B (pipeline) | applied |
| `nvidia-skillspector` | pre-deployment security scanner for agent skills; prompt-injection & data-exfil / secret detection | security-review discipline + honoring config/slack.json secret_rule ('never print webhook') in sub-task C detection; pairs with security-and-hardening skill | B (pipeline) | applied |
| `obra-superpowers` | skills workflow: git-worktree isolation, subagent-driven development, session hooks | the read-only git worktree pattern used to enumerate sources in sub-task B (git worktree add /tmp/embiz_cov origin/mila/embiz-agent-system) | B (pipeline) | applied |
| `phuryn-pm-skills` | PM workflow discipline: skills-vs-commands, progressive disclosure, manifest validation tooling | reports/*.md structure + knowledge/vectorization/INDEX.md progressive disclosure + machine-readable knowledge_agents JSON / library_coverage.json validation artifacts | B (pipeline) | applied-weak |
| `restic` | snapshots, append-only repository, data-integrity verification, forget/prune lifecycle | append-only JSONL ledgers as immutable event snapshots + per-sub-task git commits as rollback-friendly snapshots (integrity via deterministic re-run) | B (pipeline) | applied |
| `tolaria` | .chunk/config.json CI gate commands (lint/typecheck/build/coverage/smoke) + QA fixture manifest | deterministic reproducibility gates + the 5 fixed test-image fixtures (experiment_harness.IMAGES) driving Stage-2 regression | B (pipeline) | applied |

## Skill packs (skills/embiz-agent-skills/*/SKILL.md)

_All 24 skills are software-engineering methodologies; none sets a tracer parameter, so none is Class A. Each is mapped to the concrete pipeline point where it is (or is not) used._

| skill | application point in this repo | class | status |
|---|---|---|---|
| `api-and-interface-design` | the module API contracts: trace(path,params)/score(orig,rendered)/optimize() signatures in vectorizer.py | B (pipeline) | applied |
| `browser-testing-with-devtools` | no current application: no browser/web UI in this CLI raster/stitch pipeline | unused | unused |
| `ci-cd-and-automation` | automated, reproducible experiment runs via experiment_harness.py | B (pipeline) | applied |
| `code-review-and-quality` | five-axis review discipline applied to this PR's diffs | B (pipeline) | applied |
| `code-simplification` | refactors such as the v4 revert removing the content-crop scoring step | B (pipeline) | applied |
| `context-engineering` | curated context: DOCTRINE_SEED docstring + knowledge-object JSON schema in knowledge/vectorization | B (pipeline) | applied |
| `debugging-and-error-recovery` | guarded tracer/render failure -> worst-score fallback in vectorizer.optimize().evaluate() | B (pipeline) | applied |
| `deprecation-and-migration` | documented v3->v4 migration: CROP_CONTENT_THRESH/_crop_to_content kept-but-UNUSED with rationale in score() docstring | B (pipeline) | applied |
| `documentation-and-adrs` | reports/vectorizer_v*.md and knowledge/vectorization/INDEX.md as decision records | B (pipeline) | applied |
| `doubt-driven-development` | explicit honesty caveats ('weak', 'no current application') + the anti-collapse guard in score() | B (pipeline) | applied |
| `frontend-ui-engineering` | weak: the only visual output is _save_compare()'s side-by-side original|render diff PNG; no real UI surface | B (pipeline) | applied-weak |
| `git-workflow-and-versioning` | per-sub-task commits + branch/PR #2 discipline on claude/slack-session-su21xh | B (pipeline) | applied |
| `idea-refine` | Stage-1 hypothesis refinement of library concepts into candidate experiments in knowledge_agents | B (pipeline) | applied |
| `incremental-implementation` | v1->v5 incremental vectorizer versions with per-step commits | B (pipeline) | applied |
| `interview-me` | no current application: no interactive human-elicitation step in a deterministic model-free pipeline | unused | unused |
| `observability-and-instrumentation` | vectorizer._log_attempt() -> vectorization_attempts.jsonl and the other JSONL ledgers | B (pipeline) | applied |
| `performance-optimization` | bounded search: DEFAULT_MAX_ITERS=300, STALL_LIMIT=40, per-start budget in vectorizer.optimize() | B (pipeline) | applied |
| `planning-and-task-breakdown` | SEARCH_ORDER factor prioritization + multi-sub-task decomposition of this work | B (pipeline) | applied |
| `security-and-hardening` | honored config/slack.json secret_rule (never print webhook) + _ALLOWED param whitelist in trace() | B (pipeline) | applied |
| `shipping-and-launch` | production_runs/ artifacts + production_layout.py final layout stage | B (pipeline) | applied |
| `source-driven-development` | knowledge_agents mining potrace/inkscape SOURCE_BUNDLE.md into cited knowledge objects (produced the Class-A seed) | B (pipeline) | applied |
| `spec-driven-development` | knowledge/vectorization/INDEX.md as the param-mapping spec before implementation | B (pipeline) | applied |
| `test-driven-development` | experiment_harness.py isolated-factor regression tests (Stage-2 validation) | B (pipeline) | applied |
| `using-agent-skills` | meta: the skill-usage discipline recorded in EMBIZ_SKILLS_RUNTIME_INDEX.md | B (pipeline) | applied |

