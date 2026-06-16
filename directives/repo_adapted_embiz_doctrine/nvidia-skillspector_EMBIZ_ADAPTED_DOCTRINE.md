# nvidia-skillspector EMBIZ ADAPTED DOCTRINE

## Source Material Read
- **Repository**: nvidia-skillspector
- **Location**: `/root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/nvidia-skillspector`
- **Core Purpose**: Security scanner for AI agent skills using LangGraph workflow
- **Architecture**: Multi-stage analyzer pipeline (static patterns, behavioral AST, MCP validation, semantic LLM analysis, meta-analysis)
- **Key Components**:
  - Input handler (Git/URL/zip/directory resolution)
  - Context builder (manifest parsing, file caching, component metadata)
  - 20+ specialized analyzers (static patterns, behavioral, MCP, semantic)
  - Meta-analyzer (finding aggregation, deduplication, severity scoring)
  - Multi-format report generator (terminal, JSON, markdown, SARIF)

## What This Repo Contributes To EMBIZ
This repo provides **pre-deployment security validation** for AI agent skills before they enter the EMBIZ production environment. It adapts to:

1. **Skill Validation Pipeline**: Scan all agent skills (Maya's order intake prompts, Madeline's digitizing instructions, Morgan's customer communication templates) before deployment
2. **Prompt Injection Defense**: Detect hidden instructions, Unicode deception, and semantic attacks in customer-facing agent prompts
3. **Data Exfiltration Prevention**: Flag unauthorized network calls, credential access, or file system scanning in agent code
4. **Supply Chain Security**: Validate dependencies in agent tooling (Python scripts, Node.js utilities) for known CVEs
5. **Human-Approval Gate**: Provide structured findings that require human review before skills go live
6. **Audit Trail**: Generate SARIF/JSON reports for compliance and incident response

## EMBIZ-Specific Adaptation

### Operational Context
- **Scan Trigger**: Before any agent skill deployment, before digitizing workflow updates, before customer-facing prompt changes
- **Scan Scope**: 
  - Agent prompt files (`/root/embroidery_business_agent_system/agents/*/prompts/*.md`)
  - Digitizing scripts (`/root/embroidery_business_agent_system/digitizing/*.py`)
  - Customer communication templates (`/root/embroidery_business_agent_system/templates/*.md`)
  - Tool definitions (`/root/embroidery_business_agent_system/tools/*.py`)
- **Human Gate**: All HIGH/CRITICAL findings block deployment until human reviews and approves
- **Slack Notification**: Post scan summary to `#embiz-security` (outbound-only, no secrets)

### EMBIZ-Specific Rules
1. **Never scan files claiming to exist unless verified on disk** (aligns with EMBIZ file-existence doctrine)
2. **Block any skill that accesses customer PII** without explicit human approval
3. **Block any skill that modifies digitizing parameters** (DST/PES/EXP files) without Madeline's approval
4. **Block any skill that sends external HTTP requests** without Morgan's approval (customer contact gate)
5. **Whitelist approved dependencies**: Only scan against known-good package versions in `/root/embroidery_business_agent_system/requirements.txt`

### Adapted Workflow
```
Input: Agent skill file/directory
  ↓
resolve_input (local paths only, no Git clone in production)
  ↓
build_context (extract manifest, cache files, detect file types)
  ↓
[Parallel Analyzers]
  - static_patterns_* (prompt injection, data exfiltration, privilege escalation)
  - behavioral_ast (exec/eval/subprocess detection)
  - behavioral_taint_tracking (credential flow to network sinks)
  - mcp_least_privilege (permission vs capability mismatch)
  - mcp_tool_poisoning (hidden instructions, Unicode deception)
  - semantic_security_discovery (LLM-based intent analysis, if use_llm=True)
  - semantic_developer_intent (description-behavior mismatch)
  - semantic_quality_policy (missing warnings, vague triggers)
  ↓
meta_analyzer (deduplicate, aggregate, assign final severity)
  ↓
report (terminal/JSON/SARIF output)
  ↓
Human Review Gate (if HIGH/CRITICAL findings)
  ↓
Deployment (if approved) OR Block (if rejected)
```

## Assigned Agent Ownership
- **Primary Owner**: **Mckenna** (Security & Compliance Agent)
  - Runs skillspector scans before deployment
  - Reviews findings and escalates to humans
  - Maintains whitelist of approved dependencies
  - Posts scan summaries to Slack `#embiz-security`

- **Secondary Reviewers**:
  - **Madeline**: Reviews findings related to digitizing workflows (DST/PES/EXP file access)
  - **Morgan**: Reviews findings related to customer communication (external HTTP, email templates)
  - **Maya**: Reviews findings related to order intake prompts (prompt injection, data exfiltration)

## Local Skill / Knowledge Library Integration
- **Skill Library Path**: `/root/web-archive/ai_agents_skills_library`
- **EMBIZ Skills Path**: `/root/embroidery_business_agent_system/agents/*/skills`
- **Integration**:
  - Mckenna scans all files in `agents/*/skills` before they are symlinked into active agent directories
  - Scan results stored in `/root/embroidery_business_agent_system/security/scan_results/{timestamp}.json`
  - Approved skills tracked in `/root/embroidery_business_agent_system/security/approved_skills.yaml`

## Runtime Rules
1. **Pre-Deployment Scan**: Mckenna MUST run `skillspector scan` on any new/modified skill before deployment
2. **LLM Analysis**: Use `--no-llm` in air-gapped environments; enable LLM analysis (semantic_*) when NVIDIA_INFERENCE_KEY is available
3. **Severity Thresholds**:
   - **CRITICAL**: Block deployment, require human approval + remediation
   - **HIGH**: Block deployment, require human approval (may deploy with documented risk acceptance)
   - **MEDIUM**: Warn, log to audit trail, deploy with human acknowledgment
   - **LOW**: Log only, auto-deploy
4. **Whitelist Bypass**: Skills in `approved_skills.yaml` skip re-scan unless file hash changes
5. **Scan Timeout**: 120 seconds per skill (fail-safe: if scan times out, block deployment)
6. **Output Format**: JSON for programmatic processing, terminal for human review, SARIF for CI/CD integration

## Required Files / Configs
```
/root/embroidery_business_agent_system/
├── security/
│   ├── scan_results/          # Timestamped scan outputs
│   ├── approved_skills.yaml   # Whitelist of approved skills (name, hash, approval_date, approver)
│   ├── yara_rules/            # Custom YARA rules for EMBIZ-specific patterns
│   └── model_registry.yaml    # Token limits for LLM models (if using semantic analyzers)
├── .env                       # NVIDIA_INFERENCE_KEY (if using LLM analysis)
└── requirements.txt           # Approved dependency versions
```

### Example `approved_skills.yaml`
```yaml
skills:
  - name: "maya_order_intake_v1"
    file_hash: "sha256:abc123..."
    approval_date: "2025-01-15"
    approver: "human_operator_jane"
    findings_accepted: ["E1"]  # Accepted external HTTP call to order API
  - name: "madeline_digitizing_params_v2"
    file_hash: "sha256:def456..."
    approval_date: "2025-01-20"
    approver: "human_operator_john"
    findings_accepted: []
```

### Example Custom YARA Rule (`security/yara_rules/embiz_patterns.yar`)
```yara
rule EMBIZ_Unauthorized_Digitizing_Access {
    meta:
        description = "Detects unauthorized access to digitizing file formats"
        severity = "HIGH"
    strings:
        $dst = /\.dst/i nocase
        $pes = /\.pes/i nocase
        $exp = /\.exp/i nocase
        $write = /open\s*\([^)]*['\"][wa]['\"]/
    condition:
        ($dst or $pes or $exp) and $write
}
```

## Commands / Checks

### Scan a Single Skill
```bash
# Mckenna runs this before deploying a new skill
skillspector scan /root/embroidery_business_agent_system/agents/maya/skills/order_intake_v2.md \
  --format json \
  --output /root/embroidery_business_agent_system/security/scan_results/$(date +%s)_order_intake_v2.json \
  --yara-rules-dir /root/embroidery_business_agent_system/security/yara_rules \
  --verbose
```

### Scan All Agent Skills
```bash
# Batch scan all skills (run nightly or on-demand)
for agent_dir in /root/embroidery_business_agent_system/agents/*/skills; do
  agent_name=$(basename $(dirname "$agent_dir"))
  skillspector scan "$agent_dir" \
    --format json \
    --output "/root/embroidery_business_agent_system/security/scan_results/$(date +%s)_${agent_name}_batch.json"
done
```

### Check Scan Results
```bash
# Mckenna checks for HIGH/CRITICAL findings
jq '.findings[] | select(.severity == "HIGH" or .severity == "CRITICAL")' \
  /root/embroidery_business_agent_system/security/scan_results/latest.json
```

### Approve a Skill (After Human Review)
```bash
# Human operator adds to approved_skills.yaml
cat >> /root/embroidery_business_agent_system/security/approved_skills.yaml <<EOF
  - name: "maya_order_intake_v2"
    file_hash: "$(sha256sum /root/embroidery_business_agent_system/agents/maya/skills/order_intake_v2.md | awk '{print $1}')"
    approval_date: "$(date +%Y-%m-%d)"
    approver: "human_operator_jane"
    findings_accepted: ["E1"]
EOF
```

### Slack Notification (Mckenna posts scan summary)
```bash
# Post to #embiz-security (outbound-only)
agent-msg post-slack "#embiz-security" \
  "🔒 Skillspector scan complete for maya_order_intake_v2: 2 MEDIUM findings, 0 HIGH/CRITICAL. Review: /root/embroidery_business_agent_system/security/scan_results/latest.json"
```

## Security Restrictions
1. **No Secrets in Scan Output**: Redact any matched credential patterns before writing to JSON/SARIF
2. **No External Network Calls During Scan**: Disable OSV.dev API lookups in air-gapped mode (use static CVE list)
3. **No Git Clone in Production**: Only scan local files; block `git clone` in `resolve_input` node
4. **No LLM API Keys in Logs**: Mask `NVIDIA_INFERENCE_KEY` in verbose output
5. **Read-Only Scan**: Skillspector MUST NOT modify any scanned files
6. **Sandboxed Execution**: If running behavioral analysis (AST parsing), use restricted Python environment (no `exec`, no network)

## Verification Checklist
- [ ] Mckenna can run `skillspector scan` on a test skill file
- [ ] Scan detects prompt injection patterns (P1, P2, P3)
- [ ] Scan detects data exfiltration patterns (E1, E2, E3)
- [ ] Scan detects unauthorized digitizing file access (custom YARA rule)
- [ ] HIGH/CRITICAL findings block deployment (manual gate enforced)
- [ ] Approved skills bypass re-scan (hash-based whitelist works)
- [ ] Scan results posted to Slack `#embiz-security` (outbound-only)
- [ ] No secrets leaked in scan output JSON
- [ ] Scan completes within 120-second timeout
- [ ] SARIF output compatible with GitHub Code Scanning (if using CI/CD)

## Build Tasks
1. **Install skillspector**:
   ```bash
   cd /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/nvidia-skillspector
   pip install -e .
   ```

2. **Create EMBIZ security directories**:
   ```bash
   mkdir -p /root/embroidery_business_agent_system/security/{scan_results,yara_rules}
   touch /root/embroidery_business_agent_system/security/approved_skills.yaml
   ```

3. **Add custom YARA rules** (see example above)

4. **Configure environment**:
   ```bash
   # Optional: Enable LLM semantic analysis
   echo "NVIDIA_INFERENCE_KEY=nvapi-..." >> /root/embroidery_business_agent_system/.env
   
   # Set log level
   echo "SKILLSPECTOR_LOG_LEVEL=INFO" >> /root/embroidery_business_agent_system/.env
   ```

5. **Test scan**:
   ```bash
   skillspector scan /root/embroidery_business_agent_system/agents/maya/skills/test_skill.md --format terminal
   ```

## What Not To Use
1. **Git Clone Feature**: Do NOT use `skillspector scan <git-url>` in production (only local paths)
2. **Remote YARA Rules**: Do NOT fetch YARA rules from external URLs (use local `yara_rules/` only)
3. **OSV.dev API in Air-Gap**: Do NOT enable live CVE lookups if network is restricted (use `--no-llm` equivalent for static-only mode)
4. **Auto-Remediation**: Do NOT use any auto-fix features (skillspector is read-only; humans remediate)
5. **Unapproved LLM Models**: Do NOT use LLM models outside `model_registry.yaml` (token limits must be known)

## Integration Status
- **Status**: ✅ **ADAPTED FOR EMBIZ**
- **Owner**: Mckenna (Security & Compliance Agent)
- **Deployment Stage**: Pre-production (requires human approval gate implementation)
- **Dependencies**:
  - Python 3.10+ (installed)
  - LangGraph (installed via skillspector)
  - YARA-python (optional, for custom rules)
  - NVIDIA Inference API key (optional, for semantic analysis)
- **Next Steps**:
  1. Implement human approval gate in agent deployment workflow
  2. Train Mckenna to interpret scan findings and escalate appropriately
  3. Populate `approved_skills.yaml` with baseline-approved skills
  4. Integrate scan results into Slack notification pipeline
  5. Add SARIF output to CI/CD pipeline (if using GitHub Actions)

---

**Doctrine Completed**: This adaptation transforms nvidia-skillspector from a general-purpose AI skill scanner into an EMBIZ-specific security gate that enforces human approval, protects customer data, and prevents unauthorized digitizing/communication actions. All scans are local, all findings require human review for HIGH/CRITICAL severity, and all results are auditable via JSON/SARIF output.