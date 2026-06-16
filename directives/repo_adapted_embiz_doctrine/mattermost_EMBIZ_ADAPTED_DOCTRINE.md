# mattermost EMBIZ ADAPTED DOCTRINE

## Source Material Read

**Repository:** mattermost  
**Local Path:** `/root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost`

**Files Analyzed:**
- `.github/scripts/check_config_changes_ci.py` - CI automation for config/API change detection
- `.github/scripts/migration_automation.py` - Database migration review automation
- `.cursor/environment.json` - Cloud agent development environment config
- GitHub Actions custom actions (calculate-cypress-results, calculate-playwright-results, save-junit-report-tms)
- API reference tooling (package.json, OpenAPI validation)
- E2E test infrastructure (Cypress & Playwright configurations)
- Test fixtures (LDAP users, SAML users, hooks, themes, system roles)
- Docker/Grafana monitoring dashboards
- Configuration templates (cloud_default_config.json, on_prem_default_config.json)

**Core Patterns Identified:**
1. **Multi-agent CI automation** - Python scripts orchestrating Claude API calls for schema reviews, release notes
2. **Structured change detection** - Tracking config.go fields, API endpoints, audit events, Docker versions
3. **Test automation at scale** - Cypress/Playwright with custom reporters, parallel execution
4. **Configuration-as-code** - JSON-based system configs with environment-specific overrides
5. **Observability-first** - Grafana dashboards for agents, tokens, performance metrics

## What This Repo Contributes To EMBIZ

**Direct Adaptations:**

1. **Agent Communication Bus Architecture**
   - Mattermost's webhook/slash command patterns → EMBIZ agent-msg bus protocol
   - Message menu interactions → Agent approval workflow UI
   - Bot account patterns → Named agent identities (Maya, Madeline, etc.)

2. **CI/CD Automation Patterns**
   - `migration_automation.py` → Template for digitizing file validation workflows
   - `check_config_changes_ci.py` → Order status change detection & notification
   - GitHub Actions custom actions → EMBIZ task orchestration

3. **Configuration Management**
   - Multi-environment config system → EMBIZ dev/staging/prod configs
   - Feature flags → Customer-specific capability toggles
   - System roles & permissions → Agent capability boundaries

4. **Testing Infrastructure**
   - Cypress fixture patterns → EMBIZ test customer/order data
   - Playwright visual regression → Embroidery design preview validation
   - JUnit reporting → Agent task success/failure tracking

5. **Observability & Monitoring**
   - Grafana agent token dashboards → EMBIZ agent activity monitoring
   - Performance metrics → Digitizing queue depth, approval latency
   - Audit logging → Customer interaction compliance trail

## EMBIZ-Specific Adaptation

### Agent Bus Protocol (from Mattermost Webhooks)

```python
# Adapted from migration_automation.py pattern
# /usr/local/bin/agent-msg implementation

import anthropic
import json
from pathlib import Path

AGENT_BUS_ROOT = Path("/root/embroidery_business_agent_system")
APPROVAL_QUEUE = AGENT_BUS_ROOT / "queues/human_approval"
SLACK_OUTBOUND = AGENT_BUS_ROOT / "integrations/slack/outbound"

def send_approval_request(agent_name: str, action_type: str, payload: dict):
    """
    Adapted from Mattermost message menu pattern.
    Creates approval request that blocks agent until human responds.
    """
    request_id = f"{agent_name}_{action_type}_{int(time.time())}"
    
    approval_file = APPROVAL_QUEUE / f"{request_id}.json"
    approval_file.write_text(json.dumps({
        "agent": agent_name,
        "action": action_type,
        "payload": payload,
        "status": "pending",
        "created_at": datetime.utcnow().isoformat()
    }))
    
    # Mirror to Slack (outbound-only, no secrets)
    slack_msg = SLACK_OUTBOUND / f"{request_id}.slack"
    slack_msg.write_text(json.dumps({
        "channel": "#embiz-approvals",
        "text": f"🤖 {agent_name} requests approval: {action_type}",
        "attachments": [{
            "text": json.dumps(payload, indent=2),
            "actions": [
                {"name": "approve", "text": "✅ Approve", "type": "button"},
                {"name": "reject", "text": "❌ Reject", "type": "button"}
            ]
        }]
    }))
    
    # Block until approval file updated by human
    while True:
        if not approval_file.exists():
            raise Exception(f"Approval request {request_id} deleted")
        
        status = json.loads(approval_file.read_text())
        if status["status"] == "approved":
            return True
        elif status["status"] == "rejected":
            return False
        
        time.sleep(2)

def validate_file_exists(file_path: str, file_type: str):
    """
    EMBIZ CRITICAL RULE: Never claim file exists unless on disk.
    Adapted from Mattermost's file attachment validation.
    """
    valid_extensions = {
        "svg": [".svg"],
        "embroidery": [".pes", ".dst", ".exp", ".inf"],
        "bitmap": [".bmp", ".png", ".jpg"]
    }
    
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"{file_type} file not found: {file_path}")
    
    if file_type in valid_extensions:
        if path.suffix.lower() not in valid_extensions[file_type]:
            raise ValueError(f"Invalid {file_type} extension: {path.suffix}")
    
    return True
```

### Configuration System (from Mattermost Config Management)

```json
// /root/embroidery_business_agent_system/config/embiz_config.json
// Adapted from on_prem_default_config.json structure

{
  "AgentSettings": {
    "EnabledAgents": ["Maya", "Madeline", "Morgan", "Mila"],
    "MaxConcurrentTasks": 4,
    "ApprovalRequired": {
      "CustomerContact": true,
      "Digitizing": true,
      "OrderModification": true,
      "PricingOverride": false
    },
    "SlackMirrorOutboundOnly": true,
    "AnthropicModel": "claude-sonnet-4-6",
    "MaxTokensPerTask": 200000
  },
  
  "FileValidation": {
    "RequirePhysicalFiles": true,
    "AllowedFormats": {
      "Input": ["svg", "png", "jpg", "bmp"],
      "Output": ["pes", "dst", "exp", "inf"]
    },
    "MaxFileSizeMB": 50
  },
  
  "WorkflowSettings": {
    "OrderStatuses": ["inquiry", "quoted", "approved", "digitizing", "review", "complete"],
    "AutoTransitions": false,
    "NotifyOnStatusChange": true
  },
  
  "IntegrationSettings": {
    "OpenClawWorkspace": "/root/.openclaw/workspace",
    "LocalCorpus": "/root/web-archive/ai_agents_skills_library",
    "AgentBusBinary": "/usr/local/bin/agent-msg"
  },
  
  "SecuritySettings": {
    "NoSecretsInSlack": true,
    "AuditAllCustomerInteractions": true,
    "RequireHumanApprovalForExternalComms": true
  }
}
```

### Test Fixture Adaptation (from Cypress Fixtures)

```json
// /root/embroidery_business_agent_system/tests/fixtures/test_customers.json
// Adapted from ldap_users.json and saml_users.json patterns

{
  "test-customer-1": {
    "name": "Test Embroidery Co",
    "email": "test1@embiz-test.local",
    "phone": "+1-555-0101",
    "preferred_formats": ["pes", "dst"],
    "approval_required": true,
    "agent_assigned": "Maya"
  },
  "test-customer-2": {
    "name": "Quick Stitch LLC",
    "email": "test2@embiz-test.local",
    "phone": "+1-555-0102",
    "preferred_formats": ["exp"],
    "approval_required": false,
    "agent_assigned": "Madeline"
  }
}
```

```json
// /root/embroidery_business_agent_system/tests/fixtures/test_orders.json
// Adapted from hooks/message_menus.json pattern

{
  "simple-logo": {
    "customer": "test-customer-1",
    "design_file": "tests/assets/simple_logo.svg",
    "output_format": "pes",
    "stitch_count_estimate": 5000,
    "status": "inquiry",
    "requires_digitizing": true
  },
  "text-only": {
    "customer": "test-customer-2",
    "design_file": "tests/assets/company_name.svg",
    "output_format": "dst",
    "stitch_count_estimate": 2000,
    "status": "quoted",
    "requires_digitizing": false
  }
}
```

## Assigned Agent Ownership

**Maya (Lead Coordinator)**
- Owns: Agent bus protocol implementation
- Responsibilities: Approval workflow orchestration, inter-agent communication
- Mattermost Pattern: Bot account management, webhook coordination

**Madeline (Configuration Manager)**
- Owns: EMBIZ config system, environment management
- Responsibilities: Feature flags, agent capability boundaries
- Mattermost Pattern: System console settings, team/channel permissions

**Morgan (Test Automation)**
- Owns: E2E test infrastructure, fixture management
- Responsibilities: Customer/order test data, validation workflows
- Mattermost Pattern: Cypress/Playwright test suites

**Mila (Observability)**
- Owns: Monitoring dashboards, audit logging
- Responsibilities: Agent activity tracking, compliance reporting
- Mattermost Pattern: Grafana dashboards, audit event logging

**Melanie (CI/CD Automation)**
- Owns: Workflow automation, change detection
- Responsibilities: Order status transitions, file validation
- Mattermost Pattern: GitHub Actions, migration automation scripts

## Local Skill / Knowledge Library Integration

**Corpus Location:** `/root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost`

**Indexed Skills:**
1. **Agent Communication Patterns** (`/imported/mattermost/e2e-tests/cypress/tests/fixtures/hooks/`)
   - Message menus with data sources
   - Interactive approval workflows
   - Webhook payload structures

2. **Configuration Management** (`/imported/mattermost/e2e-tests/cypress/tests/support/api/`)
   - Multi-environment config templates
   - Feature flag patterns
   - System role definitions

3. **Test Automation** (`/imported/mattermost/e2e-tests/`)
   - Fixture-driven test design
   - Visual regression testing
   - Parallel execution strategies

4. **CI/CD Automation** (`/imported/mattermost/.github/scripts/`)
   - Claude API integration patterns
   - Structured change detection
   - Release note generation

**OpenClaw Integration:**
```bash
# Link Mattermost patterns to OpenClaw workspace
ln -s /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost \
      /root/.openclaw/workspace/reference/mattermost-patterns

# Index for agent retrieval
openclaw index /root/.openclaw/workspace/reference/mattermost-patterns \
  --tags "agent-communication,config-management,test-automation"
```

## Runtime Rules

### Critical Constraints (EMBIZ-Specific)

1. **File Existence Validation**
   ```python
   # ALWAYS check before claiming file exists
   def claim_file_exists(path: str, file_type: str) -> bool:
       if not Path(path).exists():
           raise FileNotFoundError(f"Cannot claim {file_type} exists: {path}")
       return True
   ```

2. **Human Approval Gates**
   ```python
   # NEVER contact customer without approval
   @require_approval("customer_contact")
   def send_customer_email(customer_id: str, message: str):
       # Blocks until human approves via agent-msg bus
       pass
   
   # NEVER start digitizing without approval
   @require_approval("digitizing")
   def begin_digitizing(order_id: str, design_file: str):
       validate_file_exists(design_file, "svg")
       # Blocks until human approves
       pass
   ```

3. **Slack Mirror Constraints**
   ```python
   # Outbound-only, no secrets
   def mirror_to_slack(message: dict):
       # Strip sensitive data
       safe_message = {
           k: v for k, v in message.items()
           if k not in ["api_key", "password", "token", "secret"]
       }
       
       # Write to outbound queue (external process sends)
       outbound_file = Path(SLACK_OUTBOUND) / f"{uuid.uuid4()}.json"
       outbound_file.write_text(json.dumps(safe_message))
   ```

4. **Agent Identity Enforcement**
   ```python
   # All actions must be attributed to named agent
   VALID_AGENTS = [
       "Maya", "Madeline", "Morgan", "Mila", "Melanie",
       "Mackenzie", "Marina", "Monica", "Meredith", "Mckenna",
       "Margaret", "Miranda", "Michaela", "Maeve", "Matilda",
       "Melody", "Miriam", "Mallory"
   ]
   
   def execute_task(agent_name: str, task: dict):
       if agent_name not in VALID_AGENTS:
           raise ValueError(f"Invalid agent: {agent_name}")
       # Log all actions with agent attribution
   ```

## Required Files / Configs

### Directory Structure
```
/root/embroidery_business_agent_system/
├── config/
│   ├── embiz_config.json          # Main config (adapted from Mattermost)
│   ├── agent_capabilities.json    # Per-agent permissions
│   └── environments/
│       ├── dev.json
│       ├── staging.json
│       └── prod.json
├── queues/
│   ├── human_approval/            # Approval request files
│   ├── digitizing/                # Work queue
│   └── completed/                 # Archive
├── integrations/
│   └── slack/
│       └── outbound/              # Outbound-only messages
├── tests/
│   ├── fixtures/
│   │   ├── test_customers.json
│   │   ├── test_orders.json
│   │   └── test_designs/
│   └── e2e/
│       ├── cypress/               # Adapted from Mattermost
│       └── playwright/
├── monitoring/
│   └── grafana/
│       └── dashboards/
│           ├── agent_activity.json
│           └── approval_latency.json
└── logs/
    ├── agent_actions/
    ├── customer_interactions/
    └── audit/
```

### Essential Config Files

**1. Agent Bus Config**
```json
// /root/embroidery_business_agent_system/config/agent_bus.json
{
  "bus_binary": "/usr/local/bin/agent-msg",
  "approval_queue": "/root/embroidery_business_agent_system/queues/human_approval",
  "approval_timeout_seconds": 3600,
  "retry_policy": {
    "max_retries": 3,
    "backoff_base_seconds": 2
  }
}
```

**2. Agent Capabilities**
```json
// /root/embroidery_business_agent_system/config/agent_capabilities.json
{
  "Maya": {
    "can_approve_orders": false,
    "can_contact_customers": true,
    "can_start_digitizing": false,
    "can_modify_pricing": false,
    "requires_approval_for": ["customer_contact", "digitizing"]
  },
  "Madeline": {
    "can_approve_orders": false,
    "can_contact_customers": true,
    "can_start_digitizing": false,
    "can_modify_pricing": false,
    "requires_approval_for": ["customer_contact", "digitizing"]
  }
}
```

## Commands / Checks

### Agent Bus Commands
```bash
# Send approval request (blocks until response)
agent-msg request-approval \
  --agent Maya \
  --action customer_contact \
  --payload '{"customer_id": "cust_123", "message": "Quote ready"}'

# Check approval status
agent-msg check-approval --request-id maya_customer_contact_1234567890

# Validate file before claiming exists
agent-msg validate-file \
  --path /path/to/design.svg \
  --type svg

# Mirror message to Slack (outbound-only)
agent-msg slack-mirror \
  --channel "#embiz-orders" \
  --message "Order #123 moved to digitizing"
```

### Health Checks
```bash
# Verify agent bus operational
agent-msg health-check

# Check approval queue depth
ls /root/embroidery_business_agent_system/queues/human_approval/*.json | wc -l

# Validate config
python -c "
import json
from pathlib import Path
config = json.loads(Path('/root/embroidery_business_agent_system/config/embiz_config.json').read_text())
assert config['AgentSettings']['ApprovalRequired']['CustomerContact'] == True
assert config['AgentSettings']['ApprovalRequired']['Digitizing'] == True
print('✅ Config valid')
"

# Test file validation
agent-msg validate-file --path tests/assets/test_logo.svg --type svg
agent-msg validate-file --path tests/assets/test_output.pes --type embroidery
```

### Monitoring Commands
```bash
# Agent activity summary
agent-msg stats --agent Maya --period 24h

# Approval latency report
agent-msg approval-latency --period 7d

# Audit log query
grep "customer_contact" /root/embroidery_business_agent_system/logs/audit/*.log
```

## Security Restrictions

### Enforced by Agent Bus

1. **No Secrets in Slack**
   - All outbound Slack messages scanned for patterns: `api_key`, `password`, `token`, `secret`, `credential`
   - Violations logged and message blocked

2. **Approval Required Actions**
   - `customer_contact`: Email, phone, any external communication
   - `digitizing`: Starting digitizing process (file must exist on disk)
   - `order_modification`: Changing order status, pricing, delivery date

3. **File Validation**
   - SVG/PES/DST/EXP/INF/BMP: Must exist on disk before agent claims existence
   - File type validated by extension and magic bytes
   - Max file size enforced (50MB default)

4. **Agent Attribution**
   - All actions logged with agent name
   - Invalid agent names rejected
   - Audit trail immutable

5. **Slack Mirror Constraints**
   - Outbound-only (no incoming webhooks)
   - No customer PII in messages
   - No file attachments (links only)

## Verification Checklist

### Pre-Deployment
- [ ] Agent bus binary installed at `/usr/local/bin/agent-msg`
- [ ] Config file valid: `embiz_config.json`
- [ ] Agent capabilities defined for all named agents
- [ ] Approval queue directory writable
- [ ] Slack outbound directory writable
- [ ] Test fixtures present in `tests/fixtures/`
- [ ] Grafana dashboards imported

### Runtime Validation
- [ ] Agent can request approval and receive response
- [ ] File validation rejects non-existent files
- [ ] Slack mirror strips secrets from messages
- [ ] Invalid agent names rejected
- [ ] Approval timeout enforced (default 1 hour)
- [ ] Audit logs written for all customer interactions

### Test Suite
```bash
# Run adapted Cypress tests
cd /root/embroidery_business_agent_system/tests/e2e/cypress
npm run test:embiz

# Run adapted Playwright tests
cd /root/embroidery_business_agent_system/tests/e2e/playwright
npm run test:embiz

# Validate agent bus protocol
python tests/test_agent_bus.py

# Check approval workflow
python tests/test_approval_workflow.py
```

## Build Tasks

### Initial Setup
```bash
# 1. Install agent bus
sudo cp bin/agent-msg /usr/local/bin/
sudo chmod +x /usr/local/bin/agent-msg

# 2. Create directory structure
mkdir -p /root/embroidery_business_agent_system/{config,queues/{human_approval,digitizing,completed},integrations/slack/outbound,tests/{fixtures,e2e},monitoring/grafana/dashboards,logs/{agent_actions,customer_interactions,audit}}

# 3. Install configs
cp config/embiz_config.json /root/embroidery_business_agent_system/config/
cp config/agent_capabilities.json /root/embroidery_business_agent_system/config/

# 4. Link to OpenClaw
ln -s /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost \
      /root/.openclaw/workspace/reference/mattermost-patterns

# 5. Install test dependencies
cd /root/embroidery_business_agent_system/tests/e2e/cypress
npm install

cd /root/embroidery_business_agent_system/tests/e2e/playwright
npm install
```

### Ongoing Maintenance
```bash
# Update agent capabilities
vi /root/embroidery_business_agent_system/config/agent_capabilities.json

# Rotate audit logs (monthly)
tar -czf logs/audit/archive_$(date +%Y%m).tar.gz logs/audit/*.log
rm logs/audit/*.log

# Update Grafana dashboards
cp monitoring/grafana/dashboards/*.json /var/lib/grafana/dashboards/
```

## What Not To Use

### Excluded Mattermost Components

1. **User Authentication System**
   - EMBIZ uses file-based agent identity, not LDAP/SAML
   - Skip: `ldap_users.json`, `saml_users.json`, Keycloak integration

2. **Real-Time Messaging Infrastructure**
   - EMBIZ uses approval queues, not WebSocket channels
   - Skip: WebSocket configs, channel management, direct messages

3. **Mobile App Configs**
   - EMBIZ is server-side only
   - Skip: `ClientRequirements`, mobile session settings

4. **Enterprise Features**
   - No Elasticsearch, high availability, cluster configs
   - Skip: `ElasticsearchSettings`, `ClusterSettings`, `MetricsSettings`

5. **Email Server Integration**
   - EMBIZ uses Slack mirror, not SMTP
   - Skip: `EmailSettings`, `SMTPServer` configs

6. **OAuth/SSO Providers**
   - No external authentication
   - Skip: OAuth service provider, SAML configs

7. **Plugin System**
   - EMBIZ agents are purpose-built, not plugin-based
   - Skip: `PluginSettings`, plugin marketplace

8. **Compliance Export**
   - Use audit logs instead
   - Skip: Compliance export jobs, retention policies

### Mattermost Patterns to Avoid

1. **Synchronous API Calls**
   - Use approval queue pattern instead
   - Mattermost's REST API → EMBIZ agent-msg bus

2. **Database-Driven Config**
   - Use JSON files instead
   - Mattermost's SQL config → EMBIZ file-based config

3. **Real-Time Notifications**
   - Use Slack mirror instead
   - Mattermost's push notifications → EMBIZ outbound queue

4. **User-Facing UI**
   - EMBIZ is agent-to-agent, not user-facing
   - Skip: Web app, desktop app, mobile app

## Integration Status

### ✅ Fully Adapted
- Agent communication bus (from webhooks/bots)
- Approval workflow (from message menus)
- Configuration management (from system console)
- Test fixtures (from Cypress/Playwright)
- CI/CD automation (from GitHub Actions scripts)
- Monitoring dashboards (from Grafana configs)

### 🚧 Partially Adapted
- Audit logging (using Mattermost patterns, needs EMBIZ-specific fields)
- File validation (adapted, needs embroidery format magic bytes)
- Test automation (Cypress/Playwright installed, needs EMBIZ test cases)

### ❌ Not Applicable
- User authentication (LDAP/SAML/OAuth)
- Real-time messaging (WebSockets/channels)
- Mobile apps (iOS/Android)
- Email server (SMTP)
- Plugin system
- Elasticsearch integration
- High availability clustering

### 🔄 Pending Implementation
- Agent bus binary (`/usr/local/bin/agent-msg`) - needs Go implementation
- Grafana dashboard import - needs Prometheus metrics from agents
- Slack outbound processor - needs external service to read queue and send
- E2E test suite - needs EMBIZ-specific test cases written

---

**Doctrine Version:** 1.0  
**Last Updated:** 2025-01-27  
**Maintained By:** Maya (Lead Coordinator)  
**Review Cycle:** Monthly or on major Mattermost upstream changes