# EMBIZ Directive / Skill / Config File Plan

## Core Master Files

- `00_MASTER_EMBIZ_AGENT_SYSTEM_DIRECTIVE.md`
- `01_REQUIREMENT_TRACEABILITY_MATRIX.md`
- `02_AGENT_TO_LOCAL_SKILL_MAPPING.md`
- `03_LOCAL_KNOWLEDGE_LIBRARY_USAGE_DIRECTIVE.md`
- `04_OPENCLAW_ORCHESTRATION_DIRECTIVE.md`
- `05_AGENT_BUS_AND_SLACK_MIRROR_DIRECTIVE.md`
- `06_VISUAL_KNOWLEDGE_EXTRACTION_DIRECTIVE.md`
- `07_HISTORICAL_LEARNING_AND_RAG_DIRECTIVE.md`
- `08_SELF_HEALING_RECURSIVE_OPTIMIZATION_DIRECTIVE.md`
- `09_AGENT_TRAINING_AND_BENCHMARKING_DIRECTIVE.md`
- `10_SECURITY_AND_SECRET_HANDLING_DIRECTIVE.md`
- `11_BACKUP_ROLLBACK_AND_DEPLOYMENT_DIRECTIVE.md`

## Agent-Specific Directive Files

- `agents/orchestrator/EMBIZ_ORCHESTRATOR_AGENT_DIRECTIVE.md`
- `agents/customer_intake/EMBIZ_CUSTOMER_INTAKE_AGENT_DIRECTIVE.md`
- `agents/requirements/EMBIZ_REQUIREMENTS_AGENT_DIRECTIVE.md`
- `agents/raster_to_vector/EMBIZ_RASTER_TO_VECTOR_AGENT_DIRECTIVE.md`
- `agents/vector_design/EMBIZ_VECTOR_DESIGN_AGENT_DIRECTIVE.md`
- `agents/artwork_review/EMBIZ_ARTWORK_REVIEW_AGENT_DIRECTIVE.md`
- `agents/visual_knowledge/EMBIZ_VISUAL_KNOWLEDGE_EXTRACTION_AGENT_DIRECTIVE.md`
- `agents/inkscape_automation/EMBIZ_INKSCAPE_AUTOMATION_AGENT_DIRECTIVE.md`
- `agents/inkstitch_automation/EMBIZ_INKSTITCH_AUTOMATION_AGENT_DIRECTIVE.md`
- `agents/digitizer/EMBIZ_DIGITIZATION_AGENT_DIRECTIVE.md`
- `agents/stitch_qa/EMBIZ_STITCH_QA_AGENT_DIRECTIVE.md`
- `agents/bernina_b700/EMBIZ_BERNINA_B700_COMPATIBILITY_AGENT_DIRECTIVE.md`
- `agents/continuous_research/EMBIZ_CONTINUOUS_RESEARCH_AGENT_DIRECTIVE.md`
- `agents/knowledge_librarian/EMBIZ_KNOWLEDGE_LIBRARIAN_AGENT_DIRECTIVE.md`
- `agents/security_audit/EMBIZ_SECURITY_AUDIT_AGENT_DIRECTIVE.md`
- `agents/self_healing/EMBIZ_SELF_HEALING_AGENT_DIRECTIVE.md`
- `agents/agent_training/EMBIZ_AGENT_TRAINING_EVALUATION_AGENT_DIRECTIVE.md`
- `agents/collaboration/EMBIZ_AGENT_BUS_SLACK_COLLABORATION_AGENT_DIRECTIVE.md`

## Skill Pack Files

- `skills/embiz-agent-skills/EMBIZ_SKILL_ANATOMY_STANDARD.md`
- `skills/embiz-agent-skills/EMBIZ_IMPORTED_SKILLS_ADAPTATION_POLICY.md`
- `skills/embiz-agent-skills/EMBIZ_24_SKILL_LIFECYCLE_MAP.md`
- `skills/embiz-agent-skills/EMBIZ_SKILL_USAGE_RUNTIME_RULES.md`

## Config Files

- `config/embiz_agent_registry.json`
- `config/embiz_skill_registry.json`
- `config/embiz_knowledge_sources.json`
- `config/embiz_visual_knowledge_sources.json`
- `config/embiz_agent_bus_policy.json`
- `config/embiz_approval_gates.json`
- `config/embiz_training_benchmarks.json`

## Required Local Library Paths

Agents must use local sources first:

- `/root/web-archive/ai_agents_skills_library`
- `/root/embroidery_business_agent_system/skills/embiz-agent-skills`
- `/root/embroidery_business_agent_system/directives`
- `/root/.openclaw/workspace`
- `/root/.openclaw/agent_bus/messages.log`

## Required Communication Commands

- `agent-msg send FROM TO "message"`
- `agent-msg broadcast FROM "message"`
- `agent-msg inbox AGENT`
- `agent-msg tail`

Slack is outbound-only. Never send secrets, full logs, API keys, webhook URLs, or private credentials.
