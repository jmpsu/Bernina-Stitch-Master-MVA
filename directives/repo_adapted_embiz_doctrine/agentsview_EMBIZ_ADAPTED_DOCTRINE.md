# agentsview EMBIZ ADAPTED DOCTRINE

## Source Material Read

Complete read of agentsview repository source bundle including:
- Build/packaging scripts (Python wheel builder, desktop Tauri wrapper)
- Test infrastructure and fixtures (Gemini, Kiro SQLite parsers)
- Configuration files (package.json, tauri.conf.json, Docker, CI/CD workflows)
- Core documentation (AGENTS.md, CLAUDE.md, README.md, SECURITY.md)
- Architecture overview and project structure
- Desktop release setup and DuckDB backend planning docs

**Key Finding**: agentsview is a **local-first AI agent session viewer** that syncs multi-agent coding sessions into SQLite/PostgreSQL, provides full-text search via FTS5, serves a Svelte 5 SPA, and tracks token costs across Claude, Codex, Forge, Gemini, OpenCode, and other agents. It's a **passive observer/analytics tool**, not an active agent orchestrator.

## What This Repo Contributes To EMBIZ

### Direct Contributions
1. **Multi-Agent Session Aggregation Pattern** - Unified view across heterogeneous agent systems (Claude, Codex, Gemini, etc.)
2. **Local-First Analytics Architecture** - SQLite + FTS5 for fast token/cost tracking without cloud dependencies
3. **Session Parser Framework** - Extensible per-agent parsers in `internal/parser/types.go`
4. **Cost Tracking Methodology** - LiteLLM pricing integration, cache-aware token accounting
5. **Security Posture for Sensitive Data** - Secrets detection, redaction, loopback-only defaults, DNS rebinding defense

### Indirect Contributions
1. **Desktop Packaging Pattern** - Tauri sidecar model for Go backend + web UI
2. **Multi-Backend Storage Strategy** - SQLite primary + PostgreSQL/DuckDB mirrors
3. **File Watcher + Sync Engine** - Real-time session discovery and indexing
4. **SSE Event Streaming** - Live updates without polling
5. **Test-Driven Parser Development** - Fuzz testing for wire formats (Antigravity, etc.)

## EMBIZ-Specific Adaptation

### What EMBIZ Needs From This
**agentsview is NOT an agent itself** - it's a **session observer and cost tracker**. EMBIZ adaptation focuses on:

1. **Session Logging Integration**
   - All EMBIZ agents (Maya, Madeline, Morgan, etc.) MUST log sessions in agentsview-compatible format
   - Store in `/root/embroidery_business_agent_system/sessions/<agent_name>/`
   - Use standardized message schema from `internal/parser/types.go`

2. **Cost Accountability**
   - Track token usage per agent, per customer order, per digitizing task
   - Monthly cost reports for business accounting
   - Alert on budget overruns (e.g., >$50/day across all agents)

3. **Audit Trail**
   - Immutable session archive for customer disputes
   - "What did the agent say to the customer?" queries
   - Compliance with "human approval before customer contact" rule

4. **Multi-Agent Coordination Visibility**
   - See when Maya hands off to Madeline
   - Track subagent spawning (agentsview already has `subagents_per_session` metric)
   - Identify bottlenecks in agent workflows

### What EMBIZ Does NOT Need
- ❌ Desktop app (server-only deployment)
- ❌ PostgreSQL sync (SQLite sufficient for single-machine EMBIZ)
- ❌ Public URL exposure (loopback-only, SSH tunnel for remote access)
- ❌ Multi-user auth (single business owner)

## Assigned Agent Ownership

**Primary**: **Meredith** (Analytics & Reporting Agent)
- Runs agentsview server as background service
- Generates daily cost reports
- Monitors for anomalies (sudden token spikes, failed sessions)
- Maintains session archive integrity

**Secondary**: **Mackenzie** (System Integration Agent)
- Ensures all agents write compatible session logs
- Implements EMBIZ-specific parsers if needed (e.g., for embroidery-specific tool calls)
- Manages agentsview upgrades and schema migrations

**Tertiary**: All named agents
- Each agent MUST log sessions to its designated directory
- Session format: JSON with `sessionId`, `startTime`, `messages[]`, `tokens{}`
- Example: `/root/embroidery_business_agent_system/sessions/maya/sess-2026-01-15-001.json`

## Local Skill / Knowledge Library Integration

### Storage Location
```
/root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/agentsview/
```

### Knowledge Extraction
1. **Session Parser Patterns** → `/skills/session_logging/parser_templates/`
   - Copy `internal/parser/*.go` as reference implementations
   - Adapt for EMBIZ-specific message types (e.g., "digitizing_request", "customer_approval")

2. **Cost Tracking Logic** → `/skills/analytics/token_accounting.md`
   - Document LiteLLM pricing fetch mechanism
   - Cache-aware cost calculation formulas
   - Budget alert thresholds

3. **Security Patterns** → `/skills/security/sensitive_data_handling.md`
   - Secrets detection regex patterns
   - Redaction strategies for customer PII
   - Loopback-only server configuration

4. **Test Fixtures** → `/skills/testing/session_test_data/`
   - Copy `internal/parser/testdata/` for parser validation
   - Use as templates for EMBIZ session format tests

## Runtime Rules

### Server Deployment
```bash
# Run as systemd service on EMBIZ host
/usr/local/bin/agentsview serve \
  --data-dir /root/embroidery_business_agent_system/sessions \
  --port 8080 \
  --no-update-check \
  --require-auth \
  --auth-token-file /root/.agentsview/token
```

### Session Logging Requirements
1. **All agents MUST**:
   - Write session JSON to `/root/embroidery_business_agent_system/sessions/<agent_name>/`
   - Include `sessionId` (UUID), `startTime` (ISO8601), `messages[]`
   - Log token usage in `tokens{input, output, cached, total}`
   - Flush after every message (for real-time sync)

2. **Message Schema**:
   ```json
   {
     "sessionId": "maya-2026-01-15-001",
     "startTime": "2026-01-15T10:00:00Z",
     "messages": [
       {
         "id": "msg-1",
         "type": "user",
         "content": "Digitize this logo",
         "timestamp": "2026-01-15T10:00:00Z"
       },
       {
         "id": "msg-2",
         "type": "maya",
         "content": "I'll analyze the image first...",
         "timestamp": "2026-01-15T10:00:05Z",
         "tokens": {"input": 1200, "output": 150, "total": 1350},
         "toolCalls": [{"name": "analyze_image", "args": {"path": "/tmp/logo.png"}}]
       }
     ]
   }
   ```

3. **Forbidden Actions**:
   - ❌ Never delete session files (archive is immutable)
   - ❌ Never log customer API keys or passwords (use secrets redaction)
   - ❌ Never expose agentsview on public IP (loopback only)

### Cost Monitoring
```bash
# Daily cost check (run via cron at 11:59 PM)
/usr/local/bin/agentsview usage daily --json > /tmp/daily_cost.json

# Alert if total > $50
if [ $(jq '.total_cost' /tmp/daily_cost.json | cut -d. -f1) -gt 50 ]; then
  agent-msg --to meredith --priority high "Daily cost exceeded $50"
fi
```

### Backup Strategy
```bash
# Weekly SQLite backup (run via cron Sunday 2 AM)
cp /root/embroidery_business_agent_system/sessions/agentsview.db \
   /root/embroidery_business_agent_system/backups/agentsview-$(date +%Y%m%d).db
```

## Required Files / Configs

### 1. Systemd Service
**File**: `/etc/systemd/system/agentsview.service`
```ini
[Unit]
Description=AgentsView Session Viewer
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/embroidery_business_agent_system
ExecStart=/usr/local/bin/agentsview serve \
  --data-dir /root/embroidery_business_agent_system/sessions \
  --port 8080 \
  --no-update-check \
  --require-auth \
  --auth-token-file /root/.agentsview/token
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 2. Auth Token
**File**: `/root/.agentsview/token`
```bash
# Generate once
openssl rand -base64 32 > /root/.agentsview/token
chmod 600 /root/.agentsview/token
```

### 3. Session Directories
```bash
mkdir -p /root/embroidery_business_agent_system/sessions/{maya,madeline,morgan,mila,melanie,mackenzie,marina,monica,meredith,mckenna,margaret,miranda,michaela,maeve,matilda,melody,miriam,mallory}
```

### 4. Agent Session Logger Library
**File**: `/root/embroidery_business_agent_system/lib/session_logger.py`
```python
import json
import uuid
from datetime import datetime
from pathlib import Path

class SessionLogger:
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.session_id = f"{agent_name}-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
        self.session_file = Path(f"/root/embroidery_business_agent_system/sessions/{agent_name}/{self.session_id}.json")
        self.messages = []
        
    def log_message(self, msg_type: str, content: str, tokens: dict = None, tool_calls: list = None):
        msg = {
            "id": f"msg-{len(self.messages)+1}",
            "type": msg_type,
            "content": content,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        if tokens:
            msg["tokens"] = tokens
        if tool_calls:
            msg["toolCalls"] = tool_calls
        self.messages.append(msg)
        self._flush()
    
    def _flush(self):
        session_data = {
            "sessionId": self.session_id,
            "startTime": self.messages[0]["timestamp"] if self.messages else datetime.utcnow().isoformat() + "Z",
            "messages": self.messages
        }
        self.session_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.session_file, 'w') as f:
            json.dump(session_data, f, indent=2)
```

## Commands / Checks

### Installation
```bash
# Install agentsview binary
curl -fsSL https://agentsview.io/install.sh | bash

# Verify installation
agentsview version

# Enable systemd service
systemctl enable agentsview
systemctl start agentsview
systemctl status agentsview
```

### Health Checks
```bash
# Check server is running
curl -H "Authorization: Bearer $(cat /root/.agentsview/token)" \
  http://127.0.0.1:8080/api/v1/sessions | jq '.sessions | length'

# Check session count per agent
agentsview usage daily --breakdown

# Verify file watcher is syncing
tail -f /var/log/syslog | grep agentsview
```

### Maintenance
```bash
# Force resync all sessions
systemctl stop agentsview
rm /root/embroidery_business_agent_system/sessions/agentsview.db
systemctl start agentsview

# Vacuum database (monthly)
sqlite3 /root/embroidery_business_agent_system/sessions/agentsview.db "VACUUM;"

# Check database size
du -h /root/embroidery_business_agent_system/sessions/agentsview.db
```

## Security Restrictions

### 1. Network Exposure
- ✅ **ALLOWED**: Loopback-only binding (`127.0.0.1:8080`)
- ✅ **ALLOWED**: SSH tunnel for remote access (`ssh -L 8080:127.0.0.1:8080 embiz-host`)
- ❌ **FORBIDDEN**: Public IP binding
- ❌ **FORBIDDEN**: Exposing without `--require-auth`

### 2. Data Handling
- ✅ **ALLOWED**: Logging customer messages (with PII redaction)
- ✅ **ALLOWED**: Storing tool call arguments (file paths, commands)
- ❌ **FORBIDDEN**: Logging raw API keys or passwords
- ❌ **FORBIDDEN**: Deleting session files (archive is immutable)

### 3. Access Control
- ✅ **ALLOWED**: Single bearer token for all API access
- ❌ **FORBIDDEN**: Sharing token in Slack or public channels
- ❌ **FORBIDDEN**: Storing token in version control

### 4. Secrets Detection
- ✅ **ENABLED**: Built-in secrets detector (redacts in UI/CLI)
- ✅ **REQUIRED**: Manual review of redacted content before sharing sessions
- ❌ **FORBIDDEN**: Disabling secrets detection

## Verification Checklist

### Pre-Deployment
- [ ] agentsview binary installed to `/usr/local/bin/`
- [ ] Systemd service file created and enabled
- [ ] Auth token generated and secured (600 permissions)
- [ ] Session directories created for all 18 agents
- [ ] `session_logger.py` library added to `/root/embroidery_business_agent_system/lib/`

### Post-Deployment
- [ ] Server responds to `curl http://127.0.0.1:8080/api/v1/sessions` with auth token
- [ ] At least one test session logged by each agent
- [ ] `agentsview usage daily` shows non-zero token counts
- [ ] Secrets detector redacts test API key in UI
- [ ] SSH tunnel access works from remote machine
- [ ] Daily cost alert cron job configured
- [ ] Weekly backup cron job configured

### Ongoing Monitoring
- [ ] Daily cost < $50 (alert if exceeded)
- [ ] Database size < 10GB (vacuum if exceeded)
- [ ] No sessions with `type: "error"` in last 24 hours
- [ ] All agents logging sessions (check via `agentsview usage daily --breakdown`)

## Build Tasks

### For EMBIZ Deployment (No Build Required)
agentsview is distributed as a pre-built binary. EMBIZ uses the official release:

```bash
# Download and install latest release
curl -fsSL https://agentsview.io/install.sh | bash
```

### For Custom Modifications (If Needed)
If EMBIZ requires custom parsers or features:

```bash
# Clone repo
git clone https://github.com/kenn-io/agentsview.git
cd agentsview

# Build frontend
cd frontend
npm ci
npm run build
cd ..

# Embed frontend and build Go binary
rm -rf internal/web/dist
cp -r frontend/dist internal/web/dist
go build -tags fts5 -o agentsview ./cmd/agentsview

# Install to system
sudo cp agentsview /usr/local/bin/
```

## What Not To Use

### Features to Avoid
1. **Desktop App** - EMBIZ runs server-only, no Tauri wrapper needed
2. **PostgreSQL Sync** - Overkill for single-machine deployment
3. **Public URL Exposure** - Security risk, use SSH tunnels instead
4. **Multi-User Auth** - Single business owner, bearer token sufficient
5. **Update Checks** - Disable with `--no-update-check` (manual upgrades only)

### Code to Ignore
1. `desktop/` - Tauri wrapper (not needed)
2. `scripts/build_wheels.py` - PyPI packaging (not relevant)
3. `internal/postgres/` - PostgreSQL backend (SQLite sufficient)
4. `.github/workflows/desktop-*.yml` - Desktop CI/CD (not used)
5. `docker-compose.prod.yaml` - Docker deployment (direct binary install preferred)

### Anti-Patterns
1. ❌ Running agentsview as root without `--require-auth`
2. ❌ Exposing port 8080 on public interface
3. ❌ Manually editing SQLite database (use API or resync)
4. ❌ Deleting session files to "clean up" (breaks audit trail)
5. ❌ Logging sensitive data without secrets redaction

## Integration Status

### Phase 1: Foundation (Week 1)
- [x] Read and analyze agentsview source
- [ ] Install agentsview binary on EMBIZ host
- [ ] Create systemd service
- [ ] Generate auth token
- [ ] Create session directories for all agents

### Phase 2: Agent Integration (Week 2)
- [ ] Implement `session_logger.py` library
- [ ] Update Maya to log sessions
- [ ] Update Madeline to log sessions
- [ ] Update Morgan to log sessions
- [ ] Test session sync and search

### Phase 3: Analytics (Week 3)
- [ ] Configure daily cost monitoring
- [ ] Set up cost alert cron job
- [ ] Create weekly backup cron job
- [ ] Build Meredith's cost reporting dashboard

### Phase 4: Production Hardening (Week 4)
- [ ] Enable secrets detection
- [ ] Test SSH tunnel access
- [ ] Document session format for all agents
- [ ] Create runbook for common issues
- [ ] Train business owner on UI usage

### Current Status
**Phase 1 In Progress** - Doctrine complete, awaiting deployment approval.

**Next Action**: Install agentsview binary and create systemd service (assigned to Mackenzie).

---

**Doctrine Completed**: 2026-01-15  
**Last Updated**: 2026-01-15  
**Maintained By**: Meredith (Analytics Agent) + Mackenzie (Integration Agent)