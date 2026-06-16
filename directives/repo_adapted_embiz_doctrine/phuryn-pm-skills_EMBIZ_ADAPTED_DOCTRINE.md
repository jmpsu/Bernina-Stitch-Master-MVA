# phuryn-pm-skills EMBIZ ADAPTED DOCTRINE

## Source Material Read

**Repository:** phuryn-pm-skills  
**Location:** `/root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/phuryn-pm-skills`  
**Structure:** 9 independent PM plugins (68 skills, 42 commands) designed for Claude Code/Cowork  
**Author:** Paweł Huryn (The Product Compass Newsletter)  
**License:** MIT

**Core Architecture:**
- **Skills** = domain knowledge (nouns/frameworks) — auto-loaded when contextually relevant
- **Commands** = workflows (verbs) — user-triggered with `/command-name`
- **Plugins** = grouped skill/command packages by PM domain
- Validation tooling (`validate_plugins.py`) enforces manifest structure, frontmatter requirements, cross-references

**Key Design Principles:**
- No cross-plugin references (plugins install independently)
- Intra-plugin references allowed (skills/commands ship together)
- Progressive disclosure (lean frontmatter, detail in body)
- Marketplace-driven distribution via `.claude-plugin/marketplace.json`

## What This Repo Contributes To EMBIZ

**Structured PM Workflow Discipline for Custom Embroidery Operations:**

1. **Discovery & Validation Frameworks** — customer interview synthesis, assumption testing, feature prioritization adapted to embroidery service requests
2. **Execution Rigor** — PRD templates, stakeholder mapping, pre-mortem risk analysis for digitizing projects, production runs, equipment purchases
3. **Data-Driven Decision Making** — cohort analysis for customer retention, A/B testing for marketing/pricing, SQL query generation for order analytics
4. **Documentation Standards** — meeting notes, release notes, test scenarios applicable to process documentation and quality control
5. **Strategic Planning Tools** — OKRs, roadmaps, business model canvas adapted to embroidery business growth
6. **AI Shipping Discipline** — security/performance audits, test coverage mapping, documentation-first approach for any custom tooling EMBIZ builds

**Critical Value:** Brings product management rigor to a craft business — transforms "we've always done it this way" into evidence-based process improvement.

## EMBIZ-Specific Adaptation

### Renamed Agent-Facing Commands (EMBIZ Namespace)

All commands adapted to `/embiz:` namespace to avoid collision with any future Claude marketplace installs:

**Discovery & Customer Research:**
- `/embiz:discover` ← `/discover` — customer request analysis, assumption mapping for custom orders
- `/embiz:interview` ← `/interview` — customer consultation script prep, post-interview synthesis
- `/embiz:triage-requests` ← `/triage-requests` — batch feature request analysis (customer design requests)

**Strategy & Planning:**
- `/embiz:strategy` ← `/strategy` — business model canvas, SWOT for embroidery service expansion
- `/embiz:plan-okrs` ← `/plan-okrs` — quarterly goals for production, sales, quality metrics

**Execution & Documentation:**
- `/embiz:write-prd` ← `/write-prd` — project requirements for new equipment, process changes, software tools
- `/embiz:pre-mortem` ← `/pre-mortem` — risk analysis before major purchases, process rollouts
- `/embiz:red-team-prd` ← `/red-team-prd` — challenge assumptions in expansion plans, new service offerings
- `/embiz:stakeholder-map` ← `/stakeholder-map` — map customer segments, supplier relationships, team roles
- `/embiz:sprint` ← `/sprint` — weekly production planning, retrospectives
- `/embiz:write-stories` ← `/write-stories` — break down projects into tasks (digitizing, production, QC)
- `/embiz:test-scenarios` ← `/test-scenarios` — quality control test plans for new designs
- `/embiz:meeting-notes` ← `/meeting-notes` — customer meeting summaries, team standup notes

**Data & Analytics:**
- `/embiz:analyze-cohorts` ← `/analyze-cohorts` — customer retention by acquisition channel, order frequency
- `/embiz:analyze-test` ← `/analyze-test` — A/B test analysis for pricing, marketing campaigns
- `/embiz:write-query` ← `/write-query` — SQL for order analytics, inventory tracking

**Market & Growth:**
- `/embiz:market-research` ← market research commands — competitor analysis, customer personas
- `/embiz:plan-launch` ← `/plan-launch` — GTM for new services (e.g., direct-to-garment, patches)
- `/embiz:north-star` ← `/north-star` — define key business metrics

**AI Shipping (for custom tools):**
- `/embiz:ship-check` ← `/ship-check` — audit any custom software before production use
- `/embiz:document-app` ← `/document-app` — document custom scripts, integrations
- `/embiz:security-audit` ← `/security-audit-static` — security review of customer data handling
- `/embiz:performance-audit` ← `/performance-audit-static` — performance check for order processing systems

**Utilities:**
- `/embiz:generate-data` ← `/generate-data` — test datasets for new systems
- `/embiz:transform-roadmap` ← `/transform-roadmap` — convert feature lists to outcome-focused roadmaps

### Embroidery-Specific Skill Adaptations

**Skills requiring context injection for embroidery domain:**

1. **`brainstorm-ideas-existing`** — inject embroidery context: "existing product" = current service offerings (logo embroidery, patches, custom apparel)
2. **`identify-assumptions-existing`** — map to embroidery risks: Value (will customers pay premium?), Usability (can we deliver quality at scale?), Viability (margins sustainable?), Feasibility (equipment/skill constraints)
3. **`prioritize-features`** — adapt to service requests: impact = revenue potential, effort = digitizing hours + production time, risk = quality/deadline risk
4. **`create-prd`** — template sections map to: equipment purchases, new service launches, process improvements, software tool adoption
5. **`stakeholder-map`** — embroidery stakeholders: customers (corporate, individual, wholesale), suppliers (thread, blanks, equipment), team (digitizers, operators, QC), partners (decorators, fulfillment)
6. **`cohort-analysis`** — customer cohorts by: acquisition channel, order type, industry vertical, order frequency
7. **`market-sizing`** — TAM/SAM/SOM for embroidery services in target geography/verticals

### Integration with EMBIZ Constraints

**Human Approval Gates:**
- `/embiz:write-prd` output for customer-facing changes → requires human review before customer contact
- `/embiz:interview` scripts → human approval before sending to customers
- Any command generating customer communications → flag for approval

**File Existence Verification:**
- Commands referencing design files (SVG, PES, DST, etc.) → verify file exists on disk before claiming availability
- `/embiz:test-scenarios` for digitizing QC → reference actual test files in `/root/embroidery_business_agent_system/test_designs/`

**Slack Integration:**
- Command outputs → post summaries to Slack (outbound-only, no secrets)
- `/embiz:meeting-notes` → auto-post to #team-updates
- `/embiz:sprint` retrospectives → post to #production-planning

**Agent Bus Coordination:**
- Multi-step workflows (e.g., `/embiz:discover`) → coordinate via `/usr/local/bin/agent-msg`
- Handoffs between Maya (customer-facing) and Mila (digitizing) → structured message passing

## Assigned Agent Ownership

**Maya (Customer Success & Discovery):**
- `/embiz:discover`, `/embiz:interview`, `/embiz:triage-requests`
- `/embiz:meeting-notes` (customer meetings)
- `/embiz:stakeholder-map` (customer segmentation)
- Skills: `brainstorm-ideas-*`, `identify-assumptions-*`, `interview-script`, `summarize-interview`, `analyze-feature-requests`

**Madeline (Strategy & Planning):**
- `/embiz:strategy`, `/embiz:plan-okrs`, `/embiz:transform-roadmap`
- `/embiz:market-research`, `/embiz:plan-launch`, `/embiz:north-star`
- Skills: `lean-canvas`, `business-model-canvas`, `swot`, `okrs`, `outcome-roadmap`, `market-sizing`

**Morgan (Execution & Project Management):**
- `/embiz:write-prd`, `/embiz:pre-mortem`, `/embiz:red-team-prd`
- `/embiz:sprint`, `/embiz:write-stories`, `/embiz:test-scenarios`
- Skills: `create-prd`, `pre-mortem`, `strategy-red-team`, `sprint-plan`, `user-stories`, `job-stories`, `test-scenarios`

**Mila (Digitizing & Quality):**
- `/embiz:test-scenarios` (digitizing QC)
- `/embiz:write-stories` (digitizing task breakdown)
- Skills: `test-scenarios`, `user-stories` (adapted to digitizing workflows)

**Melanie (Data & Analytics):**
- `/embiz:analyze-cohorts`, `/embiz:analyze-test`, `/embiz:write-query`
- Skills: `cohort-analysis`, `ab-test-analysis`, `sql-queries`

**Mackenzie (Operations & Documentation):**
- `/embiz:meeting-notes` (team meetings)
- `/embiz:generate-data` (test data for systems)
- Skills: `summarize-meeting`, `dummy-dataset`, `release-notes`

**Marina (AI Shipping & Security - for custom tools):**
- `/embiz:ship-check`, `/embiz:document-app`, `/embiz:security-audit`, `/embiz:performance-audit`
- Skills: `shipping-artifacts`, `intended-vs-implemented`

**Shared/Cross-Agent:**
- `prioritization-frameworks` — all agents reference when prioritizing
- `stakeholder-map` — Maya (customers), Morgan (projects), Madeline (strategy)

## Local Skill / Knowledge Library Integration

### Installation Path
```
/root/embroidery_business_agent_system/skills/phuryn-pm-skills/
```

### Directory Structure
```
skills/phuryn-pm-skills/
├── pm-product-discovery/
│   ├── skills/
│   │   ├── brainstorm-ideas-existing/SKILL.md
│   │   ├── identify-assumptions-existing/SKILL.md
│   │   ├── prioritize-assumptions/SKILL.md
│   │   └── [10 more skills]
│   └── commands/
│       ├── discover.md
│       ├── interview.md
│       └── [3 more commands]
├── pm-execution/
│   ├── skills/ [16 skills]
│   └── commands/ [11 commands]
├── pm-data-analytics/
│   ├── skills/ [3 skills]
│   └── commands/ [3 commands]
├── [6 more plugin directories]
└── EMBIZ_ADAPTATION.md  ← this doctrine
```

### Skill Loading Mechanism

**Auto-Loading (Context-Triggered):**
- Skills loaded when conversation topic matches `description` frontmatter
- Example: discussing customer retention → `cohort-analysis` skill auto-loads
- Example: planning equipment purchase → `create-prd` skill auto-loads

**Force-Loading:**
- `/embiz:skill-name` or `/pm-plugin-name:skill-name`
- Use when skill not auto-loading or to prioritize over general knowledge

**Command Invocation:**
- `/embiz:command-name [arguments]`
- Commands chain multiple skills into workflows

### Integration with EMBIZ Knowledge Base

**Cross-Reference Points:**
- `/embiz:write-prd` → references `/root/embroidery_business_agent_system/docs/equipment_specs/` for equipment PRDs
- `/embiz:test-scenarios` → references `/root/embroidery_business_agent_system/test_designs/` for QC scenarios
- `/embiz:analyze-cohorts` → queries `/root/embroidery_business_agent_system/data/customer_orders.db`
- `/embiz:stakeholder-map` → integrates with `/root/embroidery_business_agent_system/docs/customer_segments.md`

**Skill Enhancement with EMBIZ Data:**
- `cohort-analysis` + customer order history → retention analysis
- `market-sizing` + local competitor data → TAM/SAM/SOM for embroidery services
- `create-prd` + equipment vendor specs → equipment purchase PRDs

## Runtime Rules

### Command Execution Flow

1. **Pre-Execution Checks:**
   - Verify agent has ownership of command (see Assigned Agent Ownership)
   - Check for required context (files, data, prior outputs)
   - Validate arguments against `argument-hint` in command frontmatter

2. **Execution:**
   - Load referenced skills (apply progressive disclosure)
   - Follow command workflow steps
   - Generate structured output per command template
   - Save outputs to appropriate directories

3. **Post-Execution:**
   - Offer relevant next-step commands (per command's "Offer Next Steps" section)
   - Post summary to Slack if customer-facing or team-relevant
   - Log command execution to agent activity log

### Human Approval Triggers

**Always Require Approval Before:**
- Sending any output to customers (emails, quotes, design proofs)
- Starting digitizing work (even if `/embiz:write-stories` generated tasks)
- Purchasing equipment or supplies
- Changing production processes that affect quality
- Publishing marketing content
- Modifying pricing

**Commands That Trigger Approval:**
- `/embiz:interview` → approval before sending script to customer
- `/embiz:write-prd` (customer-facing) → approval before sharing
- `/embiz:plan-launch` → approval before executing GTM plan
- `/embiz:write-query` (if modifying production data) → approval before execution

### File Existence Verification

**Before Claiming File Exists:**
```python
import os

def verify_embroidery_file(file_path, file_type):
    """
    Verify file exists before claiming availability.
    file_type: 'svg', 'pes', 'dst', 'exp', 'inf', 'bmp', 'design', 'proof'
    """
    if not os.path.exists(file_path):
        return f"ERROR: {file_type.upper()} file does not exist at {file_path}"
    return f"VERIFIED: {file_type.upper()} file exists at {file_path}"
```

**Apply to:**
- Design file references in `/embiz:test-scenarios`
- Proof references in customer communications
- Template references in `/embiz:write-prd`

### Slack Posting Rules

**Auto-Post to Slack:**
- `/embiz:meeting-notes` → #team-updates (all meetings)
- `/embiz:sprint` retrospectives → #production-planning
- `/embiz:pre-mortem` findings → #risk-management
- `/embiz:analyze-cohorts` insights → #business-metrics
- `/embiz:plan-okrs` → #strategy (quarterly)

**Slack Message Format:**
```
🤖 [Agent Name] | [Command] | [Timestamp]

[Summary - 2-3 sentences]

📎 Full output: [link to saved file]
🔗 Related: [links to referenced docs/data]
⚠️ Action required: [if human approval needed]
```

**Never Post to Slack:**
- Customer PII (names, emails, addresses)
- Pricing details (unless #pricing-strategy channel)
- API keys, credentials, secrets
- Draft content pending approval

### Agent Bus Coordination

**Multi-Agent Workflows:**

Example: `/embiz:discover` (customer request analysis)
```
1. Maya receives customer request
2. Maya runs `/embiz:discover` → generates assumptions
3. Maya posts to agent-bus: "assumptions_mapped" event
4. Morgan subscribes → receives assumptions → runs `/embiz:write-prd`
5. Morgan posts to agent-bus: "prd_draft_ready" event
6. Maya subscribes → receives PRD → requests human approval
7. Human approves → Maya posts to agent-bus: "prd_approved" event
8. Mila subscribes → receives approved PRD → starts digitizing task breakdown
```

**Agent Bus Message Schema:**
```json
{
  "event": "command_completed",
  "agent": "Maya",
  "command": "/embiz:discover",
  "timestamp": "2025-06-15T14:30:00Z",
  "output_path": "/root/embroidery_business_agent_system/outputs/discovery/customer_request_20250615.md",
  "next_agent": "Morgan",
  "next_command": "/embiz:write-prd",
  "requires_approval": false,
  "metadata": {
    "customer_id": "CUST-12345",
    "request_type": "custom_logo_embroidery"
  }
}
```

**Coordination via `/usr/local/bin/agent-msg`:**
```bash
# Maya posts discovery completion
agent-msg publish --event discovery_complete \
  --agent Maya \
  --payload '{"output": "/outputs/discovery/req_001.md", "next": "Morgan"}'

# Morgan subscribes and receives
agent-msg subscribe --event discovery_complete --agent Morgan
```

## Required Files / Configs

### Skill Manifest Files

**Per-Plugin `plugin.json`:**
```json
{
  "name": "pm-execution",
  "version": "2.0.0",
  "description": "Execution and product management skills: PRDs, OKRs, roadmaps...",
  "author": {
    "name": "Paweł Huryn",
    "email": "pawel@productcompass.pm",
    "url": "https://www.productcompass.pm"
  },
  "keywords": ["product-management", "execution", "prd", "okrs"],
  "homepage": "https://www.productcompass.pm",
  "license": "MIT"
}
```

**Root `marketplace.json`:**
```json
{
  "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
  "name": "pm-skills",
  "version": "2.0.0",
  "description": "Structured AI workflows for better product decisions...",
  "owner": {
    "name": "Paweł Huryn",
    "email": "pawel@productcompass.pm",
    "url": "https://www.productcompass.pm"
  },
  "plugins": [
    {
      "name": "pm-product-discovery",
      "description": "Product discovery skills for PMs...",
      "source": "./pm-product-discovery",
      "category": "product-management"
    }
  ]
}
```

### Skill Frontmatter (Required)

**Skills (`SKILL.md`):**
```yaml
---
name: cohort-analysis
description: "Perform cohort analysis on user engagement data — retention curves, feature adoption trends, and segment-level insights. Use when analyzing user retention by cohort, studying feature adoption over time, investigating churn patterns, or identifying engagement trends."
---
```

**Commands (`.md`):**
```yaml
---
description: Perform cohort analysis on user data — retention curves, feature adoption, and engagement trends
argument-hint: "<data file or description of what to analyze>"
---
```

### EMBIZ-Specific Config

**`/root/embroidery_business_agent_system/config/phuryn-pm-skills.yaml`:**
```yaml
# EMBIZ adaptation of phuryn-pm-skills
version: "2.0.0-embiz"
namespace: "embiz"

# Agent ownership mapping
agent_ownership:
  Maya:
    - discover
    - interview
    - triage-requests
    - meeting-notes
    - stakeholder-map
  Madeline:
    - strategy
    - plan-okrs
    - transform-roadmap
    - market-research
    - plan-launch
    - north-star
  Morgan:
    - write-prd
    - pre-mortem
    - red-team-prd
    - sprint
    - write-stories
    - test-scenarios
  Mila:
    - test-scenarios  # digitizing QC
    - write-stories   # digitizing tasks
  Melanie:
    - analyze-cohorts
    - analyze-test
    - write-query
  Mackenzie:
    - meeting-notes  # team meetings
    - generate-data
  Marina:
    - ship-check
    - document-app
    - security-audit
    - performance-audit

# Human approval required for these commands
approval_required:
  - interview  # before sending to customer
  - write-prd  # if customer-facing
  - plan-launch  # before executing
  - write-query  # if modifying production data

# Slack posting rules
slack_channels:
  team-updates:
    - meeting-notes
  production-planning:
    - sprint
  risk-management:
    - pre-mortem
  business-metrics:
    - analyze-cohorts
  strategy:
    - plan-okrs

# File verification paths
file_paths:
  designs: "/root/embroidery_business_agent_system/designs/"
  test_designs: "/root/embroidery_business_agent_system/test_designs/"
  outputs: "/root/embroidery_business_agent_system/outputs/"
  docs: "/root/embroidery_business_agent_system/docs/"

# Database connections
databases:
  customer_orders: "/root/embroidery_business_agent_system/data/customer_orders.db"
  inventory: "/root/embroidery_business_agent_system/data/inventory.db"
```

### Agent Context Files

**`CLAUDE.md` / `AGENTS.md`:**
- Original repo has `CLAUDE.md` as single source of truth
- EMBIZ adaptation: create `/root/embroidery_business_agent_system/docs/agent_context/phuryn-pm-skills-embiz.md`
- Reference from each agent's `CLAUDE.md` or `AGENTS.md`

## Commands / Checks

### Validation

**Run Original Validator:**
```bash
cd /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/phuryn-pm-skills
python3 validate_plugins.py
```

**Expected Output:**
```
✓ pm-product-discovery: OK
✓ pm-execution: OK
✓ pm-data-analytics: OK
[... 6 more plugins]

All plugins valid.
```

**EMBIZ-Specific Validation:**
```bash
# Verify EMBIZ namespace commands exist
cd /root/embroidery_business_agent_system/skills/phuryn-pm-skills
grep -r "^# /embiz:" */commands/*.md | wc -l
# Should match total command count (42)

# Verify agent ownership mapping
python3 /root/embroidery_business_agent_system/scripts/validate_agent_ownership.py \
  --config config/phuryn-pm-skills.yaml \
  --skills-dir skills/phuryn-pm-skills/

# Verify file paths in config exist
python3 /root/embroidery_business_agent_system/scripts/validate_file_paths.py \
  --config config/phuryn-pm-skills.yaml
```

### Testing Commands

**Test Discovery Workflow:**
```bash
# Simulate customer request
echo "Customer wants custom logo embroidery on 50 polo shirts" | \
  agent-msg publish --event customer_request --agent Maya

# Maya should trigger /embiz:discover
# Check output
cat /root/embroidery_business_agent_system/outputs/discovery/latest.md
```

**Test Data Analytics:**
```bash
# Generate test customer data
/embiz:generate-data 1000 customers with order_date, order_value, product_type, repeat_customer

# Run cohort analysis
/embiz:analyze-cohorts customer_orders.csv

# Verify output
ls -lh /root/embroidery_business_agent_system/outputs/analytics/cohort_analysis_*.md
```

**Test PRD Generation:**
```bash
# Create PRD for equipment purchase
/embiz:write-prd New 15-needle embroidery machine to increase production capacity

# Verify output includes EMBIZ-specific sections
grep -A 5 "Equipment Specifications" /root/embroidery_business_agent_system/outputs/prds/latest.md
```

### Monitoring

**Command Usage Tracking:**
```bash
# Log all command invocations
tail -f /root/embroidery_business_agent_system/logs/command_usage.log

# Example log entry:
# 2025-06-15T14:30:00Z | Maya | /embiz:discover | customer_request_001 | SUCCESS
```

**Approval Queue:**
```bash
# Check pending approvals
ls /root/embroidery_business_agent_system/approvals/pending/

# Approve item
mv /root/embroidery_business_agent_system/approvals/pending/prd_001.md \
   /root/embroidery_business_agent_system/approvals/approved/
```

## Security Restrictions

### Data Access Controls

**Customer PII:**
- Skills/commands may read customer data for analysis
- **Never** include PII in Slack posts
- **Never** include PII in logs (use customer IDs only)
- Redact PII in command outputs saved to shared directories

**Database Access:**
- `/embiz:write-query` → read-only access to production DBs
- Write queries require human approval + separate credentials
- No direct DB modifications via commands

**File System:**
- Skills/commands read-only on `/root/embroidery_business_agent_system/designs/`
- Write access only to `/outputs/`, `/approvals/pending/`
- No access to `/root/.openclaw/` (OpenClaw workspace isolation)

### API Keys / Secrets

**Never in Command Outputs:**
- No API keys in PRDs, meeting notes, or any command output
- Reference secrets by name only (e.g., "STRIPE_API_KEY")
- Use environment variables, never hardcode

**Slack Integration:**
- Outbound-only (no secrets in Slack messages)
- Use webhook URL from environment, never inline
- Redact any accidentally included secrets before posting

### Approval Bypass Prevention

**Commands That Cannot Skip Approval:**
- `/embiz:interview` → always requires approval before customer contact
- `/embiz:write-prd` (customer-facing) → always requires approval
- Any command generating customer communications → always requires approval

**Enforcement:**
```python
def require_approval(command_name, output_path):
    """
    Enforce approval requirement for sensitive commands.
    """
    approval_required_commands = [
        'interview', 'write-prd', 'plan-launch', 'write-query'
    ]
    
    if any(cmd in command_name for cmd in approval_required_commands):
        approval_file = f"/root/embroidery_business_agent_system/approvals/pending/{os.path.basename(output_path)}"
        shutil.copy(output_path, approval_file)
        
        return {
            "status": "pending_approval",
            "approval_file": approval_file,
            "message": "Human approval required before proceeding."
        }
    
    return {"status": "approved", "message": "No approval required."}
```

## Verification Checklist

### Installation Verification

- [ ] All 9 plugin directories copied to `/root/embroidery_business_agent_system/skills/phuryn-pm-skills/`
- [ ] `validate_plugins.py` runs without errors
- [ ] All 68 skills have valid frontmatter (`name`, `description`)
- [ ] All 42 commands have valid frontmatter (`description`, `argument-hint`)
- [ ] `EMBIZ_ADAPTATION.md` (this file) exists in skills directory
- [ ] `config/phuryn-pm-skills.yaml` exists and validates

### Agent Ownership Verification

- [ ] Maya can invoke `/embiz:discover`, `/embiz:interview`, `/embiz:triage-requests`
- [ ] Madeline can invoke `/embiz:strategy`, `/embiz:plan-okrs`
- [ ] Morgan can invoke `/embiz:write-prd`, `/embiz:pre-mortem`, `/embiz:sprint`
- [ ] Mila can invoke `/embiz:test-scenarios` (digitizing context)
- [ ] Melanie can invoke `/embiz:analyze-cohorts`, `/embiz:write-query`
- [ ] Mackenzie can invoke `/embiz:meeting-notes`, `/embiz:generate-data`
- [ ] Marina can invoke `/embiz:ship-check`, `/embiz:security-audit`

### Workflow Verification

- [ ] `/embiz:discover` → generates assumptions → triggers `/embiz:write-prd` via agent-bus
- [ ] `/embiz:interview` → generates script → requires human approval → sends to customer
- [ ] `/embiz:analyze-cohorts` → reads customer_orders.db → generates report → posts to Slack
- [ ] `/embiz:write-prd` → saves to `/outputs/prds/` → triggers approval if customer-facing
- [ ] `/embiz:sprint` → generates retrospective → posts to #production-planning

### Security Verification

- [ ] No PII in Slack posts (test with sample customer data)
- [ ] No API keys in command outputs (grep for common patterns)
- [ ] File existence verification works (test with non-existent design file)
- [ ] Approval queue prevents bypass (test `/embiz:interview` without approval)
- [ ] Database access is read-only (test `/embiz:write-query` with INSERT statement)

### Integration Verification

- [ ] Skills auto-load when topic matches (test by discussing customer retention)
- [ ] Force-loading works (`/embiz:cohort-analysis` loads skill)
- [ ] Cross-references to EMBIZ knowledge base resolve (test `/embiz:write-prd` referencing equipment specs)
- [ ] Agent-bus coordination works (test multi-agent workflow)
- [ ] Slack posting works (test `/embiz:meeting-notes`)

## Build Tasks

### Initial Setup

```bash
# 1. Copy skills to EMBIZ directory
mkdir -p /root/embroidery_business_agent_system/skills/phuryn-pm-skills
cp -r /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/phuryn-pm-skills/* \
     /root/embroidery_business_agent_system/skills/phuryn-pm-skills/

# 2. Create EMBIZ config
cat > /root/embroidery_business_agent_system/config/phuryn-pm-skills.yaml << 'EOF'
# [paste config from Required Files section]
EOF

# 3. Create output directories
mkdir -p /root/embroidery_business_agent_system/outputs/{discovery,prds,analytics,meetings,sprints}
mkdir -p /root/embroidery_business_agent_system/approvals/{pending,approved,rejected}

# 4. Create validation scripts
cat > /root/embroidery_business_agent_system/scripts/validate_agent_ownership.py << 'EOF'
# [validation script]
EOF

# 5. Test installation
cd /root/embroidery_business_agent_system/skills/phuryn-pm-skills
python3 /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/phuryn-pm-skills/validate_plugins.py
```

### Command Namespace Adaptation

```bash
# Rename all commands to /embiz: namespace
cd /root/embroidery_business_agent_system/skills/phuryn-pm-skills

for plugin in pm-*/; do
  for cmd in "$plugin/commands/"*.md; do
    # Extract original command name from first heading
    original_cmd=$(grep -m 1 "^# /" "$cmd" | sed 's/^# \///' | cut -d' ' -f1)
    
    # Replace with /embiz: namespace
    sed -i "s|^# /$original_cmd|# /embiz:$original_cmd|" "$cmd"
    
    echo "Renamed: /$original_cmd → /embiz:$original_cmd in $cmd"
  done
done
```

### Agent Context Integration

```bash
# Create agent-specific context files
for agent in Maya Madeline Morgan Mila Melanie Mackenzie Marina; do
  cat > /root/embroidery_business_agent_system/docs/agent_context/${agent}_phuryn_pm_skills.md << EOF
# ${agent} - phuryn-pm-skills Integration

## Owned Commands
$(grep -A 10 "^  ${agent}:" /root/embroidery_business_agent_system/config/phuryn-pm-skills.yaml | grep "    -"