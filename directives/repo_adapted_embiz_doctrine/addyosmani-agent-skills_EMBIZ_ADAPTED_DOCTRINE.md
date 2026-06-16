# addyosmani-agent-skills EMBIZ ADAPTED DOCTRINE

## Source Material Read

Complete repository read of `addyosmani/agent-skills` from `/root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/addyosmani-agent-skills`. This is a production-grade engineering skills library for AI coding agents covering the full software development lifecycle: spec → plan → build → verify → review → ship. Contains 24 structured skills, 4 specialist agent personas, 8 slash commands, lifecycle hooks, and reference checklists.

## What This Repo Contributes To EMBIZ

**Core value:** Structured, verifiable workflows that prevent the "code first, think never" anti-pattern common in AI-assisted development. EMBIZ agents (Maya, Madeline, Morgan, et al.) gain:

1. **Spec-before-code discipline** — `spec-driven-development` prevents building the wrong thing
2. **Test-driven proof** — `test-driven-development` + Prove-It pattern ensures claims match reality
3. **Incremental safety** — `incremental-implementation` enforces small, rollback-friendly slices
4. **Human-in-loop gates** — `doubt-driven-development` stops agents before irreversible actions
5. **Quality gates** — five-axis code review (correctness, readability, architecture, security, performance)
6. **Shipping checklist** — parallel specialist review (code/security/test) before customer contact

**EMBIZ-specific fit:**
- **Never claim file exists unless on disk** — verification checklists enforce evidence-based assertions
- **Human approval gates** — skills explicitly pause before customer contact, digitizing, or destructive ops
- **Rollback-friendly** — incremental implementation with per-task commits enables clean revert
- **Slack mirror outbound-only** — shipping checklist includes "no secrets in logs/responses" verification

## EMBIZ-Specific Adaptation

### Mandatory Skill Activation Rules

All EMBIZ agents MUST follow these skill-to-task mappings:

| Agent Task | Required Skill(s) | Why |
|------------|------------------|-----|
| Customer requests quote/design | `spec-driven-development` → `planning-and-task-breakdown` | Prevents misunderstood requirements; creates audit trail |
| Implement digitizing workflow | `incremental-implementation` + `test-driven-development` | Small slices with proof; rollback-friendly |
| Modify file format conversion | `test-driven-development` (Prove-It) | Bug fix = failing test first, then fix |
| Review before customer contact | `code-review-and-quality` + `security-and-hardening` | Five-axis review + secrets check |
| Deploy to production | `shipping-and-launch` | Parallel specialist review + rollback plan |
| Performance issue | `debugging-and-error-recovery` → `performance-optimization` | Reproduce → measure → fix → verify |

### EMBIZ Boundary Enforcement

Inject into every agent's system prompt:

```markdown
## EMBIZ Hard Boundaries (from agent-skills adaptation)

Before ANY action, check these gates:

**ALWAYS (no approval needed):**
- Read files from disk
- Run tests
- Generate specs/plans in `/root/embroidery_business_agent_system/specs/` or `tasks/`
- Write to `/root/.openclaw/workspace/` (scratch space)
- Post to Slack mirror (outbound-only, no secrets)

**ASK FIRST (human approval required):**
- Contact customer (email, phone, Slack DM)
- Start digitizing workflow (PES/DST/EXP file generation)
- Modify database schema
- Change file format conversion logic
- Deploy to production
- Spend money (API calls to paid services)

**NEVER (hard block):**
- Claim SVG/PES/DST/EXP/INF/BMP exists unless `ls -la <path>` confirms
- Commit secrets to version control
- Skip tests before commit
- Remove failing tests to "fix" build
- Proceed with digitizing without human approval
- Send customer contact without human approval
```

### Agent Ownership Mapping

| Agent Name | Primary Skills | Specialist Role |
|------------|---------------|-----------------|
| **Maya** | `spec-driven-development`, `planning-and-task-breakdown` | Requirements gathering, customer-facing specs |
| **Madeline** | `incremental-implementation`, `test-driven-development` | Core implementation, TDD enforcement |
| **Morgan** | `code-review-and-quality`, `code-simplification` | Code quality gatekeeper |
| **Mila** | `security-and-hardening`, `security-auditor` persona | Security review, secrets audit |
| **Melanie** | `test-driven-development`, `test-engineer` persona | Test strategy, coverage analysis |
| **Mackenzie** | `debugging-and-error-recovery` | Bug reproduction, root cause analysis |
| **Marina** | `frontend-ui-engineering`, `api-and-interface-design` | UI/UX, customer portal |
| **Monica** | `performance-optimization`, `observability-and-instrumentation` | Performance tuning, monitoring |
| **Meredith** | `documentation-and-adrs`, `deprecation-and-migration` | Documentation, migration plans |
| **Mckenna** | `ci-cd-and-automation`, `git-workflow-and-versioning` | CI/CD, release automation |
| **Margaret** | `shipping-and-launch` | Pre-launch orchestrator (fan-out to code-reviewer/security-auditor/test-engineer) |
| **Miranda** | `source-driven-development`, `context-engineering` | Framework integration, official docs verification |
| **Michaela** | `doubt-driven-development` | Risk assessment, human escalation |
| **Maeve** | `interview-me`, `idea-refine` | Customer discovery, requirements clarification |
| **Matilda** | `browser-testing-with-devtools` | Browser-based testing (if web portal exists) |
| **Melody** | `web-performance-auditor` persona | Web performance (if customer portal exists) |
| **Miriam** | `planning-and-task-breakdown` | Task decomposition, dependency mapping |
| **Mallory** | `using-agent-skills` (meta-skill) | Skill discovery, workflow routing |

## Local Skill / Knowledge Library Integration

### Installation Path

```bash
# Skills library location (already present)
/root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/addyosmani-agent-skills/

# EMBIZ integration path
/root/embroidery_business_agent_system/directives/repo_adapted_embiz_doctrine/agent-skills/

# Symlink for agent access
ln -s /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/addyosmani-agent-skills \
      /root/embroidery_business_agent_system/.agent-skills
```

### Agent Discovery Mechanism

Each agent's system prompt includes:

```markdown
## Skill Library Access

Skills are located at `/root/embroidery_business_agent_system/.agent-skills/skills/`.

When a task matches a skill trigger (see `skills/using-agent-skills/SKILL.md` for the decision tree), you MUST:

1. Load the full `SKILL.md` from disk
2. Follow the workflow exactly (no partial application)
3. Complete all verification steps
4. Provide evidence for each checklist item

**Intent → Skill Mapping:**
- Customer request → `spec-driven-development`
- Feature work → `incremental-implementation` + `test-driven-development`
- Bug report → `debugging-and-error-recovery` (Prove-It pattern)
- Code review → `code-review-and-quality`
- Security concern → `security-and-hardening`
- Performance issue → `performance-optimization`
- Pre-deploy → `shipping-and-launch`
```

### Corpus Integration

Add to `/root/embroidery_business_agent_system/AGENTS.md`:

```markdown
## External Skill Library

This system uses the `agent-skills` library (addyosmani) for structured engineering workflows.

**Library path:** `/root/embroidery_business_agent_system/.agent-skills/`

**Mandatory skills for EMBIZ:**
- `spec-driven-development` — Before any customer-facing work
- `test-driven-development` — Before any code change
- `incremental-implementation` — For all multi-file changes
- `doubt-driven-development` — Before irreversible actions (digitizing, customer contact, deploys)
- `shipping-and-launch` — Before production deploys

**Skill activation is NOT optional.** If a task matches a skill trigger, the skill MUST be invoked.
```

## Runtime Rules

### Skill Invocation Protocol

```bash
# Agent internal workflow (pseudo-code)
if task_matches_skill_trigger():
    skill_path = f"/root/embroidery_business_agent_system/.agent-skills/skills/{skill_name}/SKILL.md"
    load_skill(skill_path)
    follow_workflow_exactly()
    complete_verification_checklist()
    provide_evidence()
else:
    proceed_with_task()
```

### Evidence Requirements

Every verification checklist item requires one of:

- **File on disk:** `ls -la <path>` output
- **Test output:** `npm test` or equivalent command output
- **Build output:** `npm run build` or equivalent
- **Git commit:** `git log -1 --oneline`
- **Human approval:** Slack message link or email confirmation
- **Screenshot:** For UI changes (saved to `/root/.openclaw/workspace/screenshots/`)

### Failure Handling

If a skill workflow fails:

1. **Stop immediately** — do not proceed to next step
2. **Invoke `debugging-and-error-recovery` skill**
3. **Document failure** in `/root/.openclaw/workspace/failures/<timestamp>.md`
4. **Notify human** via `agent-msg` bus
5. **Wait for human decision** (retry, skip, abort)

### Human Approval Gates (from `doubt-driven-development`)

Pause and request approval when:

- **Customer contact** — email, phone, Slack DM, quote generation
- **Digitizing** — any PES/DST/EXP/INF file generation
- **Destructive ops** — database migrations, file deletions, schema changes
- **Money** — paid API calls, service subscriptions
- **Irreversible** — anything that can't be undone with `git revert`
- **Ambiguous spec** — requirements unclear or contradictory
- **High risk** — auth changes, payment logic, data access

Approval request format:

```markdown
## Human Approval Required

**Agent:** <agent-name>
**Task:** <one-line description>
**Risk:** <why this needs approval>
**Rollback plan:** <how to undo if it goes wrong>

**Proceed? (yes/no)**
```

## Required Files / Configs

### 1. EMBIZ System Root

```bash
/root/embroidery_business_agent_system/
├── .agent-skills/          # Symlink to skills library
├── AGENTS.md               # Agent discovery + skill enforcement rules
├── specs/                  # Generated specs (from spec-driven-development)
├── tasks/                  # Generated plans (from planning-and-task-breakdown)
│   ├── plan.md
│   └── todo.md
└── directives/
    └── repo_adapted_embiz_doctrine/
        └── agent-skills/
            └── EMBIZ_ADAPTATION.md  # This file
```

### 2. Agent System Prompts

Each agent's system prompt must include:

```markdown
## Skill Library Integration

You are <agent-name>, part of the EMBIZ agent system.

**Skill library:** `/root/embroidery_business_agent_system/.agent-skills/`

**Your primary skills:** <list from Agent Ownership Mapping above>

**Mandatory workflow:**
1. Check if task matches a skill trigger (see `skills/using-agent-skills/SKILL.md`)
2. If yes: load skill, follow exactly, complete verification, provide evidence
3. If no: proceed with task using EMBIZ conventions

**Hard boundaries:** <paste EMBIZ Hard Boundaries section from above>
```

### 3. Verification Checklist Template

```markdown
## Skill Verification: <skill-name>

**Agent:** <agent-name>
**Task:** <task-description>
**Timestamp:** <ISO 8601>

### Checklist

- [ ] <verification-item-1> — Evidence: <file-path or command-output>
- [ ] <verification-item-2> — Evidence: <file-path or command-output>
- [ ] <verification-item-3> — Evidence: <file-path or command-output>

### Artifacts

- Spec: <path-to-spec-if-applicable>
- Plan: <path-to-plan-if-applicable>
- Tests: <test-file-paths>
- Commits: <git-log-output>

### Human Approvals

- <approval-1>: <slack-link or email-confirmation>
- <approval-2>: <slack-link or email-confirmation>
```

## Commands / Checks

### Skill Validation

```bash
# Verify skill library is accessible
ls -la /root/embroidery_business_agent_system/.agent-skills/skills/

# Validate a specific skill's YAML frontmatter
head -20 /root/embroidery_business_agent_system/.agent-skills/skills/test-driven-development/SKILL.md | grep -A 5 "^---"

# List all available skills
ls /root/embroidery_business_agent_system/.agent-skills/skills/ | grep -v ".zip"
```

### Agent Skill Compliance Check

```bash
# Check if agent followed TDD (Prove-It pattern for bugs)
git log --oneline --grep="test:" | head -5

# Check if spec exists before implementation
test -f /root/embroidery_business_agent_system/specs/SPEC.md && echo "Spec exists" || echo "NO SPEC - VIOLATION"

# Check if plan exists before multi-task work
test -f /root/embroidery_business_agent_system/tasks/plan.md && echo "Plan exists" || echo "NO PLAN - VIOLATION"

# Verify no secrets in recent commits
git log -1 -p | grep -iE "(password|api_key|secret|token)" && echo "SECRET DETECTED" || echo "Clean"
```

### Evidence Collection

```bash
# Collect evidence for verification checklist
cat > /root/.openclaw/workspace/evidence-$(date +%s).md <<EOF
## Evidence Collection

**Timestamp:** $(date -Iseconds)

### Files on Disk
$(ls -la /path/to/relevant/files)

### Test Output
$(npm test 2>&1 | tail -20)

### Build Output
$(npm run build 2>&1 | tail -20)

### Recent Commits
$(git log -5 --oneline)

### Git Status
$(git status --porcelain)
EOF
```

### Human Approval Request

```bash
# Send approval request via agent-msg bus
agent-msg send --channel embiz-approvals --message "$(cat <<EOF
**Agent:** $(whoami)
**Task:** Generate PES file for customer order #1234
**Risk:** Digitizing workflow - irreversible once sent to machine
**Rollback plan:** Regenerate from source SVG if customer rejects

**Proceed? Reply 'approve' or 'deny'**
EOF
)"
```

## Security Restrictions

### Secrets Handling (from `security-and-hardening` skill)

**NEVER:**
- Commit secrets to git
- Log secrets (even in debug mode)
- Echo secrets in shell scripts
- Include secrets in Slack messages
- Store secrets in `/root/.openclaw/workspace/` (scratch space)

**ALWAYS:**
- Use environment variables for secrets
- Validate secrets are in `.gitignore`
- Audit git history before push: `git log -p | grep -iE "(password|api_key|secret|token)"`
- Use `security-auditor` persona before any deploy

### File Existence Claims (EMBIZ-specific)

**Before claiming a file exists:**

```bash
# WRONG (agent hallucination)
"The PES file is ready at /path/to/design.pes"

# RIGHT (evidence-based)
if [ -f /path/to/design.pes ]; then
    echo "PES file exists: $(ls -lh /path/to/design.pes)"
else
    echo "PES file does NOT exist - generation failed"
fi
```

### Customer Contact Gate (EMBIZ-specific)

**Before ANY customer contact:**

1. Load `doubt-driven-development` skill
2. Check: Is this irreversible? (Yes - customer contact is)
3. Generate approval request
4. Wait for human "approve" response
5. Proceed only after approval
6. Log approval in `/root/.openclaw/workspace/approvals/<timestamp>.md`

## Verification Checklist

### Pre-Deployment (Margaret's `shipping-and-launch` workflow)

- [ ] **Code Review** (Morgan via `code-review-and-quality`)
  - [ ] Correctness: matches spec, edge cases handled
  - [ ] Readability: clear names, straightforward logic
  - [ ] Architecture: follows patterns, clean boundaries
  - [ ] Security: input validated, no secrets
  - [ ] Performance: no N+1 queries, no unbounded ops
  - Evidence: Review report in `/root/.openclaw/workspace/reviews/<timestamp>.md`

- [ ] **Security Audit** (Mila via `security-auditor` persona)
  - [ ] No secrets in code/logs/git
  - [ ] Input validation at boundaries
  - [ ] Auth/authz checked
  - [ ] Dependencies audited (no known CVEs)
  - Evidence: Audit report in `/root/.openclaw/workspace/audits/<timestamp>.md`

- [ ] **Test Coverage** (Melanie via `test-engineer` persona)
  - [ ] Happy path covered
  - [ ] Edge cases covered
  - [ ] Error paths covered
  - [ ] All tests passing
  - Evidence: `npm test` output + coverage report

- [ ] **Rollback Plan**
  - [ ] Trigger conditions defined
  - [ ] Rollback procedure documented
  - [ ] Recovery time objective stated
  - Evidence: Rollback plan in `/root/.openclaw/workspace/rollback-plans/<timestamp>.md`

- [ ] **Human Approvals**
  - [ ] Customer contact approved (if applicable)
  - [ ] Digitizing approved (if applicable)
  - [ ] Deploy approved
  - Evidence: Approval logs in `/root/.openclaw/workspace/approvals/`

### Post-Deployment

- [ ] **Smoke Test**
  - [ ] Core functionality verified in production
  - [ ] No errors in logs
  - Evidence: Log snippet + manual verification

- [ ] **Monitoring**
  - [ ] Metrics dashboard shows normal behavior
  - [ ] Alerts configured
  - Evidence: Dashboard screenshot in `/root/.openclaw/workspace/screenshots/`

## Build Tasks

### Skill Library Sync

```bash
# Update skills library from upstream
cd /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/addyosmani-agent-skills
git pull origin main

# Verify symlink still valid
ls -la /root/embroidery_business_agent_system/.agent-skills
```

### Agent System Prompt Generation

```bash
# Generate agent system prompts with skill integration
for agent in Maya Madeline Morgan Mila Melanie Mackenzie Marina Monica Meredith Mckenna Margaret Miranda Michaela Maeve Matilda Melody Miriam Mallory; do
    cat > /root/embroidery_business_agent_system/agents/${agent}/system_prompt.md <<EOF
# ${agent} - EMBIZ Agent

$(cat /root/embroidery_business_agent_system/directives/repo_adapted_embiz_doctrine/agent-skills/agent_prompt_template.md)

## Your Primary Skills

$(grep "^| \*\*${agent}\*\*" /root/embroidery_business_agent_system/directives/repo_adapted_embiz_doctrine/agent-skills/EMBIZ_ADAPTATION.md | cut -d'|' -f3)

EOF
done
```

### Verification Report Generation

```bash
# Generate daily skill compliance report
cat > /root/.openclaw/workspace/compliance-$(date +%Y%m%d).md <<EOF
# Skill Compliance Report - $(date +%Y-%m-%d)

## Specs Generated
$(find /root/embroidery_business_agent_system/specs/ -name "*.md" -mtime -1 | wc -l) specs in last 24h

## Plans Generated
$(find /root/embroidery_business_agent_system/tasks/ -name "plan.md" -mtime -1 | wc -l) plans in last 24h

## Tests Added
$(git log --since="24 hours ago" --oneline --grep="test:" | wc -l) test commits in last 24h

## Human Approvals
$(find /root/.openclaw/workspace/approvals/ -name "*.md" -mtime -1 | wc -l) approvals in last 24h

## Violations Detected
$(grep -r "VIOLATION" /root/.openclaw/workspace/failures/ 2>/dev/null | wc -l) violations logged

EOF
```

## What Not To Use

### Skills to Skip (Not Applicable to EMBIZ)

- **`browser-testing-with-devtools`** — EMBIZ has no web UI (unless customer portal is built later)
- **`web-performance-auditor`** — No browser-facing app (unless customer portal exists)
- **`frontend-ui-engineering`** — Backend-focused system (unless customer portal is built)

### Hooks to Skip

- **`hooks/session-start.sh`** — Claude Code specific, not applicable to EMBIZ agent bus
- **`hooks/sdd-cache-*`** — WebFetch caching for `source-driven-development`, not needed if no web framework integration

### Commands to Skip

- **`/webperf`** — Web performance audit, not applicable without web UI

### Anti-Patterns to Avoid

From `skills/using-agent-skills/SKILL.md`:

| Anti-Pattern | Why It's Wrong | EMBIZ Impact |
|--------------|----------------|--------------|
| "This is too small for a skill" | Small changes compound into big bugs | Digitizing errors cost machine time + materials |
| "I'll add tests later" | Later never comes | Untested file conversion = corrupted embroidery files |
| "I'll gather context first" | Procrastination disguised as diligence | Delays customer quotes |
| "The spec is obvious" | Assumptions cause rework | Wrong stitch count = rejected order |

## Integration Status

### ✅ Completed

- [x] Repository read and analysis
- [x] EMBIZ-specific adaptation documented
- [x] Agent ownership mapping defined
- [x] Boundary enforcement rules specified
- [x] Verification checklist created
- [x] Runtime rules documented
- [x] Security restrictions defined

### 🚧 In Progress

- [ ] Symlink creation: `/root/embroidery_business_agent_system/.agent-skills/`
- [ ] Agent system prompt generation with skill integration
- [ ] `AGENTS.md` update with skill enforcement rules
- [ ] Verification checklist templates in `/root/.openclaw/workspace/templates/`

### 📋 Pending

- [ ] Agent training on skill invocation protocol
- [ ] Human approval workflow integration with `agent-msg` bus
- [ ] Slack mirror integration for approval requests
- [ ] Daily compliance report automation
- [ ] Evidence collection automation
- [ ] Rollback plan template creation
- [ ] Customer contact gate enforcement testing
- [ ] Digitizing approval gate enforcement testing

### 🔍 Validation Needed

- [ ] Test skill activation with Maya (spec-driven-development)
- [ ] Test skill activation with Madeline (test-driven-development)
- [ ] Test human approval gate with Michaela (doubt-driven-development)
- [ ] Test pre-deploy checklist with Margaret (shipping-and-launch)
- [ ] Test security audit with Mila (security-auditor persona)
- [ ] Test evidence collection for verification checklists
- [ ] Test failure handling and `debugging-and-error-recovery` invocation

---

**Next Steps:**

1. Create symlink: `ln -s /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/addyosmani-agent-skills /root/embroidery_business_agent_system/.agent-skills`
2. Update `/root/embroidery_business_agent_system/AGENTS.md` with skill enforcement rules
3. Generate agent system prompts with skill integration
4. Test skill activation with one agent (recommend Maya for `spec-driven-development`)
5. Validate human approval gate with test scenario (e.g., mock customer contact request)