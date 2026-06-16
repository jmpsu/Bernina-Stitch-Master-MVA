# obra-superpowers EMBIZ ADAPTED DOCTRINE

## Source Material Read

**Repository:** obra-superpowers  
**Location:** `/root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/obra-superpowers`

**Core Components Identified:**
- Skills-based agent workflow system (brainstorming, TDD, planning, code review, git worktrees)
- Multi-platform plugin architecture (Claude Code, Codex, Cursor, OpenCode, Gemini, Copilot)
- Subagent-driven development methodology
- Visual brainstorming companion (Node.js server with WebSocket)
- Token usage analysis tooling
- Session hooks and bootstrap injection system
- Skill discovery and frontmatter parsing infrastructure

**Key Files Analyzed:**
- Plugin manifests (`.claude-plugin/`, `.codex-plugin/`, `.cursor-plugin/`, `.opencode/`)
- Test infrastructure (`tests/claude-code/`, `tests/brainstorm-server/`)
- Documentation (`AGENTS.md`, `CLAUDE.md`, `README.md`, `RELEASE-NOTES.md`)
- Design specs and implementation plans (`docs/plans/`, `docs/superpowers/`)
- Hook system (`hooks/`)

## What This Repo Contributes To EMBIZ

**Direct Contributions:**

1. **Agent Workflow Discipline** — Structured methodology for multi-agent task execution with mandatory checkpoints
2. **Skill-Based Architecture** — Composable, discoverable capabilities with frontmatter metadata
3. **Subagent Dispatch Patterns** — Proven patterns for delegating work to specialized agents with review loops
4. **Session Bootstrap System** — Automatic context injection at agent startup
5. **Token Budget Awareness** — Analysis tooling for tracking multi-agent token consumption
6. **TDD Enforcement** — RED-GREEN-REFACTOR discipline with verification gates
7. **Git Worktree Isolation** — Branch-per-task workflow with cleanup protocols
8. **Visual Companion Pattern** — Browser-based interactive displays alongside terminal conversation

**EMBIZ-Specific Value:**

- **Order workflow** maps to brainstorming → spec → plan → execute → review → finish
- **Digitizing approval gates** align with human-in-loop verification checkpoints
- **Multi-agent coordination** for parallel order processing (Maya coordinates, specialists execute)
- **File existence verification** discipline prevents hallucinated asset claims
- **Customer contact approval** fits existing human approval requirement pattern
- **Slack integration** can mirror visual companion pattern (outbound-only constraint respected)

## EMBIZ-Specific Adaptation

### Agent Role Mapping

**Obra Pattern → EMBIZ Agents:**

| Obra Role | EMBIZ Agent | Responsibility |
|-----------|-------------|----------------|
| Coordinator (main session) | Maya | Order intake, workflow orchestration, customer communication approval |
| Spec Reviewer | Madeline | Design validation, requirement completeness |
| Plan Reviewer | Morgan | Implementation plan verification, task decomposition |
| Implementer (subagent) | Mila, Melanie, Mackenzie | Execute individual tasks (digitizing, file ops, communication drafts) |
| Code Reviewer | Marina | Quality gates, file existence verification, compliance checks |
| Finisher | Monica | Order completion, cleanup, handoff preparation |

**Reserved for future:**
- Meredith, Mckenna, Margaret, Miranda, Michaela, Maeve, Matilda, Melody, Miriam, Mallory

### Workflow Adaptation

**Obra Workflow → EMBIZ Order Flow:**

```
1. BRAINSTORMING (superpowers:brainstorming)
   → EMBIZ: Order Intake & Specification
   - Maya extracts requirements from customer inquiry
   - Madeline reviews spec for completeness (logo placement, thread colors, file formats)
   - Spec saved to /root/embroidery_business_agent_system/orders/{order-id}/spec.md

2. USING-GIT-WORKTREES (superpowers:using-git-worktrees)
   → EMBIZ: Order Workspace Isolation
   - Maya creates worktree at /root/embroidery_business_agent_system/.worktrees/{order-id}
   - Prevents cross-contamination between concurrent orders

3. WRITING-PLANS (superpowers:writing-plans)
   → EMBIZ: Digitizing & Fulfillment Plan
   - Maya breaks order into tasks (digitize logo, test stitch, generate preview, draft email)
   - Morgan reviews plan for file path accuracy, approval gate placement
   - Plan saved to orders/{order-id}/plan.md

4. SUBAGENT-DRIVEN-DEVELOPMENT (superpowers:subagent-driven-development)
   → EMBIZ: Parallel Order Execution
   - Maya dispatches Mila (digitizing), Mackenzie (file ops), Melanie (communication drafts)
   - Each subagent works in isolated context with specific task + verification
   - Marina reviews each task output before proceeding

5. REQUESTING-CODE-REVIEW (superpowers:requesting-code-review)
   → EMBIZ: Quality & Compliance Gates
   - Marina verifies:
     * Digitized files exist on disk (no hallucinated PES/DST claims)
     * Customer communication drafts await human approval
     * File formats match order spec
     * No secrets in Slack mirror content

6. FINISHING-A-DEVELOPMENT-BRANCH (superpowers:finishing-a-development-branch)
   → EMBIZ: Order Completion & Cleanup
   - Monica presents completion options (deliver, revise, archive)
   - Cleans up worktree after human approval
   - Archives order artifacts to /root/embroidery_business_agent_system/orders/{order-id}/archive/
```

### Skill Adaptation Requirements

**Skills requiring EMBIZ-specific versions:**

1. **brainstorming** → `embiz:order-intake`
   - Replace "software feature" language with "embroidery order"
   - Add mandatory fields: logo file, thread colors, garment type, placement, quantity
   - Include file format verification (SVG input, PES/DST/EXP output)

2. **writing-plans** → `embiz:order-planning`
   - Task templates for digitizing workflow (not code implementation)
   - Verification steps: "File exists at {path}" not "Tests pass"
   - Approval gates: "Human approves customer email" not "Code review passes"

3. **subagent-driven-development** → `embiz:order-execution`
   - Dispatch patterns for digitizing tools (not code subagents)
   - File existence verification after every file-generating task
   - Slack mirror constraint enforcement (outbound-only, no secrets)

4. **requesting-code-review** → `embiz:quality-gates`
   - Checklist adapted for embroidery deliverables:
     * Digitized file exists and is valid format
     * Preview image generated
     * Customer communication draft complete and awaiting approval
     * No hallucinated file claims
     * No secrets in any output

5. **test-driven-development** → `embiz:verification-driven-workflow`
   - Replace "write test first" with "define verification criteria first"
   - Example: "Logo renders correctly in preview" before "Generate preview image"

**Skills usable as-is (with tool mapping):**

- `using-git-worktrees` (order isolation)
- `finishing-a-development-branch` (order completion)
- `verification-before-completion` (file existence checks)

### Tool Mapping

**Obra Tools → EMBIZ Equivalents:**

| Obra Tool | EMBIZ Equivalent | Notes |
|-----------|------------------|-------|
| `Skill` | `/usr/local/bin/agent-msg load-skill` | Skill discovery via agent bus |
| `Task` (subagent dispatch) | `/usr/local/bin/agent-msg dispatch` | Named agent dispatch (Maya → Mila) |
| `TodoWrite` | Order task tracker (TBD) | Persistent task state across sessions |
| `Bash` | Direct shell execution | Already available |
| `Read`/`Write`/`Edit` | Standard file ops | Already available |
| Visual Companion | Slack mirror (outbound) | Browser → Slack channel (no inbound) |

### File Structure Adaptation

**Obra Structure → EMBIZ Structure:**

```
obra-superpowers/
├── skills/                          → /root/embroidery_business_agent_system/skills/
│   ├── brainstorming/              → embiz:order-intake/
│   ├── writing-plans/              → embiz:order-planning/
│   └── subagent-driven-development/ → embiz:order-execution/
├── .claude-plugin/                  → (not applicable - no Claude Code)
├── hooks/                           → /root/embroidery_business_agent_system/hooks/
└── tests/                           → /root/embroidery_business_agent_system/tests/

EMBIZ-specific additions:
/root/embroidery_business_agent_system/
├── orders/                          # Per-order workspaces
│   └── {order-id}/
│       ├── spec.md                  # Customer requirements
│       ├── plan.md                  # Execution plan
│       ├── input/                   # Customer-provided files (SVG logos)
│       ├── output/                  # Generated files (PES, DST, previews)
│       └── archive/                 # Completed order artifacts
├── .worktrees/                      # Isolated order workspaces (git worktree)
└── directives/                      # Agent instructions (including this doctrine)
```

## Assigned Agent Ownership

**Primary Ownership:**

- **Maya** — Workflow orchestration, skill loading, subagent dispatch, customer communication approval
  - Loads `embiz:order-intake`, `embiz:order-planning`, `embiz:order-execution`
  - Dispatches Madeline (spec review), Morgan (plan review), Mila/Melanie/Mackenzie (execution)
  - Enforces human approval gates before customer contact

**Specialist Ownership:**

- **Madeline** — Spec review (order completeness, file format validation)
- **Morgan** — Plan review (task decomposition, verification step accuracy)
- **Mila** — Digitizing execution (SVG → PES/DST conversion, stitch testing)
- **Melanie** — Communication drafts (customer emails, Slack updates)
- **Mackenzie** — File operations (moving files, generating previews, archiving)
- **Marina** — Quality gates (file existence verification, compliance checks)
- **Monica** — Order completion (cleanup, archiving, handoff)

**Skill Maintenance:**

- **Meredith** — Skill authoring and updates (when `embiz:writing-skills` is needed)

## Local Skill / Knowledge Library Integration

**Integration Points:**

1. **Skill Discovery Path:**
   ```
   /root/embroidery_business_agent_system/skills/  (EMBIZ-specific, highest priority)
   /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/obra-superpowers/skills/  (reference, lower priority)
   ```

2. **Skill Loading Mechanism:**
   - Agent bus command: `/usr/local/bin/agent-msg load-skill embiz:order-intake`
   - Reads `SKILL.md` with YAML frontmatter (obra format compatible)
   - Injects skill content into agent context

3. **Bootstrap Integration:**
   - Adapt `hooks/session-start` to inject EMBIZ bootstrap instead of obra bootstrap
   - EMBIZ bootstrap content:
     ```markdown
     # EMBIZ Agent System Bootstrap
     
     You are part of the EMBIZ embroidery business agent system.
     
     **Mandatory workflows:**
     - Order intake → Spec review → Plan → Execute → Quality gates → Completion
     - Human approval required before customer contact
     - Human approval required before digitizing
     - Never claim files exist unless verified on disk
     
     **Available skills:** (auto-discovered from /root/embroidery_business_agent_system/skills/)
     
     **Your role:** [Agent name from named agent list]
     
     **Agent bus:** /usr/local/bin/agent-msg [command]
     ```

4. **Skill Authoring:**
   - Use `embiz:writing-skills` (adapted from `superpowers:writing-skills`)
   - Frontmatter format (obra-compatible):
     ```yaml
     ---
     name: embiz:order-intake
     description: Use when customer inquiry received - extracts requirements and creates order spec
     ---
     ```

5. **Knowledge Corpus Integration:**
   - Obra skills remain in `/root/web-archive/` as reference material
   - EMBIZ skills in `/root/embroidery_business_agent_system/skills/` shadow/override obra skills
   - Skill discovery checks EMBIZ path first, falls back to obra path

## Runtime Rules

**Mandatory Constraints (from EMBIZ context):**

1. **File Existence Verification:**
   - NEVER claim SVG/PES/DST/EXP/INF/BMP exists unless file verified on disk
   - Every file-generating task MUST include verification step: `ls -lh {path}`
   - Marina enforces this in quality gates

2. **Human Approval Gates:**
   - Customer contact (email, phone, Slack DM) requires human approval
   - Digitizing operations require human approval
   - Maya enforces approval workflow, blocks subagent dispatch until approved

3. **Slack Mirror Constraint:**
   - Outbound-only (agents can post, cannot read)
   - No secrets (API keys, passwords, customer PII beyond order context)
   - Melanie enforces when drafting Slack updates

4. **Agent Bus Usage:**
   - All inter-agent communication via `/usr/local/bin/agent-msg`
   - No direct agent-to-agent calls
   - Maya coordinates all dispatch

5. **Worktree Isolation:**
   - One worktree per active order
   - Worktree path: `/root/embroidery_business_agent_system/.worktrees/{order-id}`
   - Monica cleans up after order completion

**Obra-Derived Rules (adapted):**

6. **Skill Auto-Triggering:**
   - `embiz:order-intake` triggers on customer inquiry detection
   - `embiz:order-planning` triggers after spec approval
   - `embiz:order-execution` triggers after plan approval
   - `embiz:quality-gates` triggers between tasks and at completion

7. **Review Loops:**
   - Spec review: Madeline reviews, Maya fixes, max 3 iterations
   - Plan review: Morgan reviews, Maya fixes, max 3 iterations
   - Quality review: Marina reviews, implementer fixes, max 5 iterations

8. **Verification-Driven Workflow:**
   - Define verification criteria before executing task
   - Example: "Preview image shows logo centered on left chest" before generating preview
   - Every task ends with verification step execution

9. **YAGNI Enforcement:**
   - No unrequested features (don't add embroidery effects customer didn't ask for)
   - No speculative file format conversions (only generate requested formats)

10. **Token Budget Awareness:**
    - Use `tests/claude-code/analyze-token-usage.py` pattern for multi-agent sessions
    - Maya tracks cumulative token usage across subagents
    - Warn human if session exceeds 100K tokens

## Required Files / Configs

**Critical Files (must exist):**

1. **Agent Bus:**
   - `/usr/local/bin/agent-msg` (executable)

2. **Skill Directories:**
   - `/root/embroidery_business_agent_system/skills/` (EMBIZ skills)
   - `/root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/obra-superpowers/skills/` (obra reference)

3. **Bootstrap Hook:**
   - `/root/embroidery_business_agent_system/hooks/session-start` (adapted from obra `hooks/session-start`)

4. **Order Workspace:**
   - `/root/embroidery_business_agent_system/orders/` (order storage)
   - `/root/embroidery_business_agent_system/.worktrees/` (git worktrees)

5. **OpenClaw Workspace:**
   - `/root/.openclaw/workspace` (agent coordination)

**Configuration Files:**

6. **Agent Registry:**
   - `/root/embroidery_business_agent_system/config/agents.json`
   ```json
   {
     "agents": [
       {"name": "Maya", "role": "coordinator"},
       {"name": "Madeline", "role": "spec-reviewer"},
       {"name": "Morgan", "role": "plan-reviewer"},
       {"name": "Mila", "role": "digitizer"},
       {"name": "Melanie", "role": "communicator"},
       {"name": "Mackenzie", "role": "file-ops"},
       {"name": "Marina", "role": "quality-gate"},
       {"name": "Monica", "role": "finisher"}
     ]
   }
   ```

7. **Skill Discovery Config:**
   - `/root/embroidery_business_agent_system/config/skills.json`
   ```json
   {
     "skill_paths": [
       "/root/embroidery_business_agent_system/skills",
       "/root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/obra-superpowers/skills"
     ],
     "namespace": "embiz"
   }
   ```

**Optional (for visual companion adaptation):**

8. **Slack Mirror Config:**
   - `/root/embroidery_business_agent_system/config/slack.json`
   ```json
   {
     "webhook_url": "https://hooks.slack.com/services/...",
     "channel": "#embiz-orders",
     "outbound_only": true
   }
   ```

## Commands / Checks

**Agent Bus Commands:**

```bash
# Load skill into agent context
/usr/local/bin/agent-msg load-skill embiz:order-intake

# Dispatch subagent
/usr/local/bin/agent-msg dispatch --agent Mila --task "Digitize logo" --context orders/ORD-001/spec.md

# List available skills
/usr/local/bin/agent-msg list-skills

# Check agent status
/usr/local/bin/agent-msg status --agent Maya
```

**Verification Commands (from obra patterns):**

```bash
# File existence check (MANDATORY after file generation)
ls -lh /root/embroidery_business_agent_system/orders/ORD-001/output/logo.pes

# Worktree status
git worktree list

# Token usage analysis (adapt obra script)
python3 /root/embroidery_business_agent_system/tools/analyze-token-usage.py session.jsonl

# Skill validation (check frontmatter)
grep -A 5 "^---$" /root/embroidery_business_agent_system/skills/embiz:order-intake/SKILL.md
```

**Health Checks:**

```bash
# Verify agent bus is operational
/usr/local/bin/agent-msg ping

# Check skill discovery
/usr/local/bin/agent-msg list-skills | grep embiz:

# Verify no orphaned worktrees
git worktree list | grep -c ".worktrees/"

# Check for stale order workspaces (older than 7 days)
find /root/embroidery_business_agent_system/orders/ -maxdepth 1 -type d -mtime +7
```

## Security Restrictions

**From EMBIZ Context:**

1. **No Inbound Slack Access:**
   - Agents cannot read Slack messages
   - Outbound posts only (via webhook)
   - Enforced at Slack mirror config level

2. **No Secret Exposure:**
   - API keys, passwords, tokens never in Slack posts
   - Customer PII limited to order context (name, email in order spec only)
   - Marina checks all outbound content before posting

3. **File System Boundaries:**
   - Agents confined to `/root/embroidery_business_agent_system/` and `/root/.openclaw/workspace`
   - No access to `/root/web-archive/` (read-only reference only)
   - No writes outside order workspaces

**From Obra Patterns:**

4. **Subagent Isolation:**
   - Each subagent sees only its task context (not full plan)
   - No cross-subagent communication (all via Maya)
   - Worktree isolation prevents file conflicts

5. **Human Approval Gates:**
   - Customer contact blocked until human approves draft
   - Digitizing blocked until human approves plan
   - Enforced by Maya before subagent dispatch

6. **File Existence Verification:**
   - Prevents hallucinated file claims
   - Marina rejects any task claiming file exists without `ls` proof

## Verification Checklist

**Pre-Deployment Checks:**

- [ ] Agent bus (`/usr/local/bin/agent-msg`) is executable and responds to `ping`
- [ ] Skill directories exist and contain valid `SKILL.md` files with frontmatter
- [ ] Bootstrap hook (`hooks/session-start`) injects EMBIZ context (not obra context)
- [ ] Agent registry (`config/agents.json`) lists all 18 named agents
- [ ] Order workspace (`orders/`) and worktree directory (`.worktrees/`) exist
- [ ] Slack webhook configured (if using Slack mirror)
- [ ] No secrets in any config files or skill content

**Runtime Verification (per order):**

- [ ] Order spec created and reviewed by Madeline
- [ ] Plan created and reviewed by Morgan
- [ ] Worktree created for order isolation
- [ ] Every file-generating task includes `ls -lh` verification step
- [ ] Customer communication draft awaits human approval
- [ ] Digitizing operation awaits human approval
- [ ] Marina quality gate passed before order completion
- [ ] Worktree cleaned up by Monica after completion

**Skill Verification (when authoring new skills):**

- [ ] Frontmatter includes `name:` and `description:` fields
- [ ] Description follows "Use when [condition] - [what it does]" format
- [ ] Skill file is `SKILL.md` (not `skill.md` or `README.md`)
- [ ] Skill tested with `agent-msg load-skill` command
- [ ] Skill includes verification steps for all file operations
- [ ] Skill respects human approval gates where applicable

## Build Tasks

**Initial Setup (one-time):**

1. **Extract Obra Skills to EMBIZ Namespace:**
   ```bash
   cd /root/embroidery_business_agent_system
   mkdir -p skills
   
   # Copy obra skills as templates
   cp -r /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/obra-superpowers/skills/brainstorming skills/embiz:order-intake
   cp -r /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/obra-superpowers/skills/writing-plans skills/embiz:order-planning
   cp -r /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/obra-superpowers/skills/subagent-driven-development skills/embiz:order-execution
   ```

2. **Adapt Skill Content:**
   - Replace "software feature" with "embroidery order"
   - Replace "tests pass" with "file exists at {path}"
   - Add embroidery-specific verification steps
   - Update frontmatter `name:` fields to `embiz:*` namespace

3. **Create Bootstrap Hook:**
   ```bash
   cp /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/obra-superpowers/hooks/session-start \
      /root/embroidery_business_agent_system/hooks/session-start
   
   # Edit to inject EMBIZ bootstrap instead of obra bootstrap
   ```

4. **Install Token Analysis Tool:**
   ```bash
   cp /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/obra-superpowers/tests/claude-code/analyze-token-usage.py \
      /root/embroidery_business_agent_system/tools/
   ```

**Ongoing Maintenance:**

5. **Sync Obra Updates (when upstream changes):**
   ```bash
   cd /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/obra-superpowers
   git pull
   
   # Review RELEASE-NOTES.md for relevant changes
   # Manually port applicable changes to EMBIZ skills
   ```

6. **Test Skill Changes:**
   ```bash
   # Validate frontmatter
   grep -A 5 "^---$" /root/embroidery_business_agent_system/skills/embiz:order-intake/SKILL.md
   
   # Test skill loading
   /usr/local/bin/agent-msg load-skill embiz:order-intake
   ```

## What Not To Use

**Obra Components NOT Applicable to EMBIZ:**

1. **Plugin System:**
   - `.claude-plugin/`, `.codex-plugin/`, `.cursor-plugin/`, `.opencode/` directories
   - EMBIZ uses agent bus, not IDE plugins
   - **Reason:** No Claude Code/Cursor/Codex in EMBIZ environment

2. **Visual Brainstorming Server (as-is):**
   - `skills/brainstorming/scripts/server.js`, `helper.js`, `frame-template.html`
   - **Reason:** Slack mirror is outbound-only, cannot support interactive browser UI
   - **Alternative:** Adapt pattern for Slack posts with static images (no WebSocket feedback)

3. **Obra Bootstrap Content:**
   - `skills/using-superpowers/SKILL.md` (software development focused)
   - **Reason:** EMBIZ needs embroidery-specific bootstrap
   - **Alternative:** Create `skills/embiz:bootstrap/SKILL.md` with order workflow context

4. **Test-Driven Development Skill (as-is):**
   - `skills/test-driven-development/SKILL.md`
   - **Reason:** Embroidery orders don't have "tests" in software sense
   - **Alternative:** `embiz:verification-driven-workflow` (define verification criteria first)

5. **Code Review Skill (as-is):**
   - `skills/requesting-code-review/SKILL.md`
   - **Reason:** No code to review in embroidery workflow
   - **Alternative:** `embiz:quality-gates` (file existence, format validation, compliance)

6. **GitHub-Specific Tooling:**
   - `.github/` directory (issue templates, PR templates, funding)
   - **Reason:** EMBIZ is not a GitHub project
   - **Alternative:** Internal issue tracking (if needed)

7. **Platform-Specific Documentation:**
   - `docs/README.opencode.md`, `GEMINI.md`
   - **Reason:** EMBIZ doesn't use these platforms
   - **Keep:** `AGENTS.md`, `CLAUDE.md` as reference for agent behavior patterns

8. **Obra-Specific Terminology:**
   - "Your human partner" (obra uses this, EMBIZ should use "the human operator")
   - "Subagent-driven development" (obra term, EMBIZ uses "order execution workflow")
   - "Code reviewer" (obra role, EMBIZ uses "quality gate agent")

## Integration Status

**Current State:** ✅ Design Complete, ⚠️ Implementation Pending

**Completed:**
- [x] Source material analysis
- [x] Agent role mapping (18 named agents assigned)
- [x] Workflow adaptation (6-phase order flow defined)
- [x] Skill adaptation requirements identified
- [x] Tool mapping documented
- [x] File structure designed
- [x] Security restrictions defined
- [x] Verification checklist created

**In Progress:**
- [ ] Skill content adaptation (brainstorming → order-intake, etc.)
- [ ] Bootstrap hook creation
- [ ] Agent bus integration testing
- [ ] Token analysis tool adaptation

**Blocked/Pending:**
- [ ] Slack mirror implementation (depends on webhook config)
- [ ] Visual companion adaptation (requires Slack outbound-only pattern)
- [ ] Order workspace automation (depends on git worktree setup)

**Next Steps:**

1. **Immediate (Week 1):**
   - Create EMBIZ skill directory structure
   - Adapt `brainstorming` → `embiz:order-intake` (Meredith)
   - Create bootstrap hook with EMBIZ context
   - Test skill loading via agent bus

2. **Short-term (Week 2-3):**
   - Adapt remaining core skills (planning, execution, quality gates)
   - Implement worktree isolation for orders
   - Create agent registry and skill discovery config
   - Test end-to-end order flow with Maya + subagents

3. **Medium-term (Month 1):**
   - Adapt token analysis tooling for multi-agent sessions
   - Implement Slack mirror (outbound-only)
   - Create order archival automation
   - Document EMBIZ-specific skill authoring guidelines

4. **Long-term (Month 2+):**
   - Develop EMBIZ-specific skills (thread color optimization, stitch density analysis)
   - Integrate with digitizing tools (if available)
   - Build order analytics dashboard
   - Expand agent specialization (dedicated preview generator, format converter)

**Risk Mitigation:**

- **Obra upstream changes:** Monitor `RELEASE-NOTES.md`, port relevant fixes to EMBIZ skills
- **Agent bus reliability:** Implement health checks, fallback to direct file ops if bus unavailable
- **Skill discovery failures:** Graceful degradation (warn but continue with available skills)
- **Token budget overruns:** Maya enforces 100K token warning, suggests session split

**Success Criteria:**

- [ ] Maya successfully orchestrates full order flow (intake → completion)
- [ ] All file-generating tasks include verification steps (no hallucinated files)
- [ ] Human approval gates enforced (customer contact, digitizing)
- [ ] Subagent dispatch works via agent bus
- [ ] Token usage tracked across multi-agent sessions
- [ ] Order worktrees isolated and cleaned up properly
- [ ] Slack mirror posts order updates (outbound-only, no secrets)

---

**Doctrine Version:** 1.0  
**Last Updated:** 2025-01-XX (date of this analysis)  
**Maintained By:** Meredith (skill authoring agent)  
**Review Cycle:** Monthly (sync with obra-superpowers upstream releases)