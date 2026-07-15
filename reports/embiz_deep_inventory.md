# EMBIZ Deep Inventory Audit

- Generated: `2026-07-15T00:19:09.896436+00:00`
- Repo root: `/home/user/Bernina-Stitch-Master-MVA`

## Executive verdicts

| Check | Status | Detail |
|---|---:|---|
| runtime file vectorizer.py | ok |  |
| runtime file digitizer.py | ok |  |
| runtime file run_iteration.py | ok |  |
| runtime file metrics.py | ok |  |
| runtime file local_agents/continuous_run.py | ok |  |
| runtime file local_agents/knowledge_ingest.py | ok |  |
| runtime file local_agents/knowledge_retrieval.py | ok |  |
| runtime file local_agents/model_router.py | ok |  |
| runtime file local_agents/qwen_client.py | ok |  |
| runtime file local_agents/slack_daemon.py | ok |  |
| runtime file local_agents/agent_loop.py | ok |  |
| runtime file local_agents/personas.py | ok |  |
| knowledge gate mila | ok | ok |
| knowledge gate melanie | ok | ok |
| knowledge gate mckenna | ok | ok |
| knowledge gate meredith | ok | ok |
| knowledge gate miranda | ok | ok |
| knowledge gate mackenzie | ok | ok |
| knowledge gate monica | ok | ok |
| knowledge gate maya | ok | ok |
| knowledge gate marnie | ok | ok |
| knowledge gate mercy | ok | ok |
| knowledge gate mabel | ok | ok |
| knowledge gate mira | ok | ok |
| knowledge gate margo | ok | ok |
| knowledge gate minerva | ok | ok |
| attached URL seed coverage | ok |  |
| cloudflare customer-facing surface | missing | cloudflare_aws_surface_incomplete_or_absent |
| open GitHub PR discovery | unknown | uses gh CLI when authenticated |

## Git / PR state
- Repo slug: `http://local_proxy@127.0.0.1:41729/git/jmpsu/Bernina-Stitch-Master-MVA`
- Current branch: `claude/trusting-hawking-mizv2d`
- HEAD: `73b47664d41c43c16a4df1f38d3d23c0e477e1c7`
- `gh` available: `False`

## Knowledge roots

| Root | Exists | Readable | Writable | JSONL count | Global files |
|---|---:|---:|---:|---:|---|
| `/root/web-archive/ai_agents_skills_library` | False | False | False | 0 |  |
| `/root/EMBIZ_EXPORTS` | False | False | False | 0 |  |
| `/home/user/Bernina-Stitch-Master-MVA/knowledge/library` | True | True | True | 10 | /home/user/Bernina-Stitch-Master-MVA/knowledge/library/global_knowledge_objects.jsonl, /home/user/Bernina-Stitch-Master-MVA/knowledge/library/global_knowledge_objects.multimodal.jsonl |

## Corpus inventory

| Corpus | Present | Records | Files |
|---|---:|---:|---|
| `raster-to-vector` | True | 36 | /home/user/Bernina-Stitch-Master-MVA/knowledge/library/5-agent-architecture/raster-to-vector-agent/knowledge_objects.jsonl |
| `vector-design` | True | 4 | /home/user/Bernina-Stitch-Master-MVA/knowledge/library/5-agent-architecture/vector-design-agent/knowledge_objects.jsonl |
| `visual-semantics` | False | 0 |  |
| `svg-specification` | True | 10 | /home/user/Bernina-Stitch-Master-MVA/knowledge/library/9-knowledge-management-architecture/svg-specification-corpus/knowledge_objects.jsonl |
| `inkscape` | False | 0 |  |
| `svg-conformance` | False | 0 |  |
| `ink-stitch-docs` | True | 5 | /home/user/Bernina-Stitch-Master-MVA/knowledge/library/14-ink-stitch-automation-framework/documents/knowledge_objects.jsonl |
| `embroidery-techniques` | True | 1 | /home/user/Bernina-Stitch-Master-MVA/knowledge/library/14-ink-stitch-automation-framework/embroidery-techniques/visual_captions.jsonl |
| `bernina-b700` | True | 4 | /home/user/Bernina-Stitch-Master-MVA/knowledge/library/10-machine-integration/bernina-b700-corpus/knowledge_objects.jsonl |
| `visual-qa` | True | 4 | /home/user/Bernina-Stitch-Master-MVA/knowledge/library/12-quality-assurance/visual-qa-corpus/knowledge_objects.jsonl |
| `global` | True | 65 | /home/user/Bernina-Stitch-Master-MVA/knowledge/library/global_knowledge_objects.jsonl, /home/user/Bernina-Stitch-Master-MVA/knowledge/library/global_knowledge_objects.multimodal.jsonl |

## Agent knowledge gates

| Agent | Gate | Missing required |
|---|---|---|
| `mila` | ok |  |
| `melanie` | ok |  |
| `mckenna` | ok |  |
| `meredith` | ok |  |
| `miranda` | ok |  |
| `mackenzie` | ok |  |
| `monica` | ok |  |
| `maya` | ok |  |
| `marnie` | ok |  |
| `mercy` | ok |  |
| `mabel` | ok |  |
| `mira` | ok |  |
| `margo` | ok |  |
| `minerva` | ok |  |

## Attached URL seed coverage

- Exact URLs covered: `24/24`

| URL | Exact covered | Domain seen | Files |
|---|---:|---:|---|
| `http://tavmjong.free.fr/INKSCAPE/MANUAL/html/Glossary.html#svg` | True | True | reports/embiz_deep_inventory.json, reports/embiz_deep_inventory.md, tools/embiz_deep_inventory_audit.py |
| `http://tavmjong.free.fr/INKSCAPE/MANUAL/html/` | True | True | reports/embiz_deep_inventory.json, reports/embiz_deep_inventory.md, tools/embiz_deep_inventory_audit.py |
| `https://sketchpad.net/` | True | True | reports/embiz_deep_inventory.json, reports/embiz_deep_inventory.md, tools/embiz_deep_inventory_audit.py |
| `https://sketchpad.net/drawing1.htm` | True | True | reports/embiz_deep_inventory.json, reports/embiz_deep_inventory.md, tools/embiz_deep_inventory_audit.py |
| `https://sketchpad.net/drawing2.htm` | True | True | reports/embiz_deep_inventory.json, reports/embiz_deep_inventory.md, tools/embiz_deep_inventory_audit.py |
| `https://sketchpad.net/drawing3.htm` | True | True | reports/embiz_deep_inventory.json, reports/embiz_deep_inventory.md, tools/embiz_deep_inventory_audit.py |
| `https://sketchpad.net/drawing3a.htm` | True | True | reports/embiz_deep_inventory.json, reports/embiz_deep_inventory.md, tools/embiz_deep_inventory_audit.py |
| `https://sketchpad.net/drawing4.htm` | True | True | reports/embiz_deep_inventory.json, reports/embiz_deep_inventory.md, tools/embiz_deep_inventory_audit.py |
| `https://sketchpad.net/drawing5.htm` | True | True | reports/embiz_deep_inventory.json, reports/embiz_deep_inventory.md, tools/embiz_deep_inventory_audit.py |
| `https://sketchpad.net/drawing6.htm` | True | True | reports/embiz_deep_inventory.json, reports/embiz_deep_inventory.md, tools/embiz_deep_inventory_audit.py |
| `https://sketchpad.net/drawing7.htm` | True | True | reports/embiz_deep_inventory.json, reports/embiz_deep_inventory.md, tools/embiz_deep_inventory_audit.py |
| `https://sketchpad.net/drawing8.htm` | True | True | reports/embiz_deep_inventory.json, reports/embiz_deep_inventory.md, tools/embiz_deep_inventory_audit.py |
| `https://sketchpad.net/drawing9.htm` | True | True | reports/embiz_deep_inventory.json, reports/embiz_deep_inventory.md, tools/embiz_deep_inventory_audit.py |
| `https://sketchpad.net/drawing10.htm` | True | True | reports/embiz_deep_inventory.json, reports/embiz_deep_inventory.md, tools/embiz_deep_inventory_audit.py |
| `https://sketchpad.net/drawing11.htm` | True | True | reports/embiz_deep_inventory.json, reports/embiz_deep_inventory.md, tools/embiz_deep_inventory_audit.py |
| `https://inkscape.gitlab.io/extensions/documentation/` | True | True | reports/embiz_deep_inventory.json, reports/embiz_deep_inventory.md, tools/embiz_deep_inventory_audit.py |
| `https://inkscape.gitlab.io/extensions/documentation/source/index.html` | True | True | reports/embiz_deep_inventory.json, reports/embiz_deep_inventory.md, tools/embiz_deep_inventory_audit.py |
| `https://github.com/Kauhentus/inkscape-cli` | True | True | reports/embiz_deep_inventory.json, reports/embiz_deep_inventory.md, tools/embiz_deep_inventory_audit.py |
| `https://github.com/The3DSquare/inkscape-cli` | True | True | reports/embiz_deep_inventory.json, reports/embiz_deep_inventory.md, tools/embiz_deep_inventory_audit.py |
| `https://www.npmjs.com/package/inkscape-cli` | True | True | reports/embiz_deep_inventory.json, reports/embiz_deep_inventory.md, tools/embiz_deep_inventory_audit.py |
| `https://inkscape.org/forums/embroidery/` | True | True | reports/embiz_deep_inventory.json, reports/embiz_deep_inventory.md, tools/embiz_deep_inventory_audit.py |
| `https://potrace.sourceforge.net/` | True | True | reports/embiz_deep_inventory.json, reports/embiz_deep_inventory.md, tools/embiz_deep_inventory_audit.py |
| `https://www.w3.org/TR/SVG11/` | True | True | reports/embiz_deep_inventory.json, reports/embiz_deep_inventory.md, tools/embiz_deep_inventory_audit.py |
| `https://www.w3.org/TR/SVG2/` | True | True | reports/embiz_deep_inventory.json, reports/embiz_deep_inventory.md, tools/embiz_deep_inventory_audit.py |

## Runtime wiring patterns

### knowledge_root_discovery
- `docs/SYSTEM_ATLAS.md`
- `local_agents/continuous_doctrine_run.py`
- `local_agents/doctrine_visible_run.py`
- `local_agents/knowledge_ingest.py`
- `local_agents/knowledge_retrieval.py`
- `reports/embiz_deep_inventory.json`
- `reports/embiz_deep_inventory.md`
- `reports/embiz_deep_inventory_followup_log_20260708.md`
- `reports/knowledge_audit.md`
- `tools/embiz_deep_inventory_audit.py`

### retrieval_gate_enforcement
- `OUTPUTS.md`
- `docs/SYSTEM_ATLAS.md`
- `docs/requirements/SPEC_COVERAGE.md`
- `local_agents/continuous_run.py`
- `local_agents/dashboard.py`
- `local_agents/knowledge_retrieval.py`
- `reports/agent_meetings.jsonl`
- `reports/embiz_deep_inventory.json`
- `reports/embiz_deep_inventory.md`
- `reports/knowledge_audit.md`
- `reports/retrieval_log.jsonl`
- `reports/slack_messages/cr_img_0293_final_production_message.json`
- `reports/slack_messages/order_0001_drink_v2_final_production_message.json`
- `reports/slack_messages/order_0002_img_0331_final_production_message.json`
- `scripts/seed_missing_corpora.py`
- `tools/embiz_deep_inventory_audit.py`

### finalization_retrieval_wiring
- `OUTPUTS.md`
- `docs/SYSTEM_ATLAS.md`
- `local_agents/README.md`
- `local_agents/agent_loop.py`
- `local_agents/continuous_run.py`
- `local_agents/intake.py`
- `local_agents/knowledge_retrieval.py`
- `local_agents/model_router.py`
- `local_agents/slack_daemon.py`
- `reports/agent_meetings.jsonl`
- `reports/embiz_deep_inventory.json`
- `reports/knowledge_audit.md`
- `tools/embiz_deep_inventory_audit.py`

### vectorizer_learning
- `EMBIZ_Jupiter_LOCAL_FIRST_Autonomous_Agent_FULL_VERSION.md`
- `OUTPUTS.md`
- `README.md`
- `docs/SYSTEM_ATLAS.md`
- `ihive.py`
- `knowledge/library_coverage.json`
- `local_agents/continuous_run.py`
- `local_agents/dashboard.py`
- `reports/agent_meetings.jsonl`
- `reports/embiz_deep_inventory.json`
- `reports/knowledge_audit.md`
- `reports/library_utilization_coverage.md`
- `reports/slack_messages/cr_img_0263_final_production_message.json`
- `reports/slack_messages/cr_img_0293_final_production_message.json`
- `reports/slack_messages/cr_img_0322_final_production_message.json`
- `reports/slack_messages/cr_img_0331_final_production_message.json`
- `reports/slack_messages/cr_img_1126_final_production_message.json`
- `reports/slack_messages/order_0001_drink_v2_final_production_message.json`
- `reports/slack_messages/order_0002_img_0331_final_production_message.json`
- `reports/vectorizer_v1.md`
- `reports/vectorizer_v2.md`
- `reports/vectorizer_v3.md`
- `reports/vectorizer_v5_promotion.md`
- `skills/embroidery-vector-generation/SKILL.md`
- `tools/embiz_deep_inventory_audit.py`
- `vectorizer.py`

### cross_order_transplant_pr5
- `docs/SYSTEM_ATLAS.md`
- `docs/requirements/SPEC_COVERAGE.md`
- `local_agents/continuous_doctrine_run.py`
- `local_agents/continuous_run.py`
- `production_pipeline.py`
- `reports/embiz_deep_inventory.json`
- `tools/embiz_deep_inventory_audit.py`
- `vectorizer.py`

### qwen_local_first
- `EMBIZ_Jupiter_LOCAL_FIRST_Autonomous_Agent_FULL_VERSION.md`
- `OUTPUTS.md`
- `docs/SYSTEM_ATLAS.md`
- `local_agents/README.md`
- `local_agents/agent_loop.py`
- `local_agents/continuous_run.py`
- `local_agents/model_router.py`
- `local_agents/qwen_client.py`
- `local_agents/slack_daemon.py`
- `reports/agent_meetings.jsonl`
- `reports/embiz_deep_inventory.json`
- `reports/embiz_deep_inventory.md`
- `reports/embiz_deep_inventory_followup_log_20260708.md`
- `tools/embiz_deep_inventory_audit.py`

### slack_operation
- `EMBIZ_Jupiter_LOCAL_FIRST_Autonomous_Agent_FULL_VERSION.md`
- `OUTPUTS.md`
- `docs/SYSTEM_ATLAS.md`
- `docs/requirements/SPEC_COVERAGE.md`
- `local_agents/README.md`
- `local_agents/agent_loop.py`
- `local_agents/continuous_run.py`
- `local_agents/model_router.py`
- `local_agents/personas.py`
- `local_agents/slack_daemon.py`
- `reports/embiz_deep_inventory.json`
- `reports/embiz_deep_inventory.md`
- `reports/slack_messages/cr_img_0263_final_production_message.json`
- `reports/slack_messages/cr_img_0293_final_production_message.json`
- `reports/slack_messages/cr_img_0322_final_production_message.json`
- `reports/slack_messages/cr_img_0331_final_production_message.json`
- `reports/slack_messages/cr_img_1126_final_production_message.json`
- `reports/slack_messages/order_0001_drink_v2_final_production_message.json`
- `reports/slack_messages/order_0002_img_0331_final_production_message.json`
- `reports/slack_utilization_report.md`
- `tools/embiz_deep_inventory_audit.py`

### cloudflare_customer_surface
- `EMBIZ_Jupiter_LOCAL_FIRST_Autonomous_Agent_FULL_VERSION.md`
- `OUTPUTS.md`
- `agents/contracts/mallory.json`
- `agents/contracts/maya.json`
- `agents/contracts/morgan.json`
- `digitizer.py`
- `docs/SYSTEM_ATLAS.md`
- `docs/requirements/EMBIZ_ARCHITECTURAL_MATRIX_v1.html`
- `docs/requirements/EMBIZ_BRD.md`
- `docs/requirements/GAP_ANALYSIS.md`
- `docs/requirements/SPEC_COVERAGE.md`
- `experiment_harness.py`
- `ihive.py`
- `knowledge/library/12-quality-assurance/visual-qa-corpus/knowledge_objects.jsonl`
- `knowledge/library/5-agent-architecture/raster-to-vector-agent/knowledge_objects.jsonl`
- `knowledge/library/global_knowledge_objects.jsonl`
- `knowledge/library/global_knowledge_objects.multimodal.jsonl`
- `knowledge/library_coverage.json`
- `knowledge/vectorization/INDEX.md`
- `knowledge/vectorization/color_agent/color_delta_e_merge_tolerance.json`
- `knowledge/vectorization/color_agent/hierarchical_color_layering.json`
- `knowledge/vectorization/color_agent/hsl_perceptual_color_matching.json`
- `knowledge/vectorization/color_agent/max_thread_color_budget.json`
- `knowledge/vectorization/curve_agent/alphamax_corner_threshold.json`
- `knowledge/vectorization/curve_agent/opticurve_bezier_vs_polygon.json`
- `knowledge/vectorization/curve_agent/opttolerance_curve_smoothness.json`
- `knowledge/vectorization/curve_agent/opttolerance_segment_joining.json`
- `knowledge/vectorization/edge_agent/corner_sharpness_edge_fidelity.json`
- `knowledge/vectorization/edge_agent/max_path_deviation_fidelity.json`
- `knowledge/vectorization/edge_agent/node_count_topology_target.json`

## Cloudflare/customer-facing surface

- Status: `cloudflare_aws_surface_incomplete_or_absent`

### Expected Cloudflare + AWS surface

| Path | Present |
|---|---:|
| `wrangler.toml` | False |
| `functions/_middleware.ts` | False |
| `functions/api/quote.ts` | False |
| `functions/api/order.ts` | False |
| `functions/api/upload.ts` | False |
| `functions/api/contact.ts` | False |
| `terraform/main.tf` | False |
| `terraform/variables.tf` | False |
| `terraform/outputs.tf` | False |
| `.github/workflows/deploy-cloudflare-pages.yml` | False |
| `.github/workflows/deploy-aws.yml` | False |
| `aws/lambdas/` | False |
| `package.json` | False |

### Pattern-matched files
- `.github/workflows/blank.yml`
- `EMBIZ_Jupiter_LOCAL_FIRST_Autonomous_Agent_FULL_VERSION.md`
- `OUTPUTS.md`
- `README.md`
- `agents/contracts/mackenzie.json`
- `agents/contracts/madeline.json`
- `agents/contracts/maeve.json`
- `agents/contracts/mallory.json`
- `agents/contracts/margaret.json`
- `agents/contracts/marina.json`
- `agents/contracts/matilda.json`
- `agents/contracts/maya.json`
- `agents/contracts/mckenna.json`
- `agents/contracts/melanie.json`
- `agents/contracts/melody.json`
- `agents/contracts/meredith.json`
- `agents/contracts/michaela.json`
- `agents/contracts/mila.json`
- `agents/contracts/miranda.json`
- `agents/contracts/miriam.json`
- `agents/contracts/monica.json`
- `agents/contracts/morgan.json`
- `dashboard/index.html`
- `decision_trace.jsonl`
- `digitizer.py`
- `docs/SYSTEM_ATLAS.md`
- `docs/requirements/EMBIZ_ARCHITECTURAL_MATRIX_v1.html`
- `docs/requirements/EMBIZ_BRD.md`
- `docs/requirements/GAP_ANALYSIS.md`
- `docs/requirements/SPEC_COVERAGE.md`
- `experiment_harness.py`
- `ihive.py`
- `knowledge/library/12-quality-assurance/visual-qa-corpus/knowledge_objects.jsonl`
- `knowledge/library/5-agent-architecture/raster-to-vector-agent/knowledge_objects.jsonl`
- `knowledge/library/9-knowledge-management-architecture/svg-specification-corpus/knowledge_objects.jsonl`
- `knowledge/library/global_knowledge_objects.jsonl`
- `knowledge/library/global_knowledge_objects.multimodal.jsonl`
- `knowledge/library_coverage.json`
- `knowledge/vectorization/INDEX.md`
- `knowledge/vectorization/color_agent/color_delta_e_merge_tolerance.json`
- `knowledge/vectorization/color_agent/hierarchical_color_layering.json`
- `knowledge/vectorization/color_agent/hsl_perceptual_color_matching.json`
- `knowledge/vectorization/color_agent/max_thread_color_budget.json`
- `knowledge/vectorization/curve_agent/alphamax_corner_threshold.json`
- `knowledge/vectorization/curve_agent/opticurve_bezier_vs_polygon.json`
- `knowledge/vectorization/curve_agent/opttolerance_curve_smoothness.json`
- `knowledge/vectorization/curve_agent/opttolerance_segment_joining.json`
- `knowledge/vectorization/edge_agent/corner_sharpness_edge_fidelity.json`
- `knowledge/vectorization/edge_agent/max_path_deviation_fidelity.json`
- `knowledge/vectorization/edge_agent/node_count_topology_target.json`

## EMBIZ services

### User units
### System units
