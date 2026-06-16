# restic EMBIZ ADAPTED DOCTRINE

## Source Material Read

**Repository:** restic  
**Local Path:** `/root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/restic`  
**Bundle:** `restic_SOURCE_BUNDLE.md`

**Files Analyzed:**
- Documentation configuration (Sphinx/ReadTheDocs setup)
- GitHub workflows (CI/CD, Docker, testing)
- Configuration files (.golangci.yml, dependabot, codespell)
- Core documentation (installation, backup, restore, encryption, scripting, troubleshooting)
- Project governance and contribution guidelines
- README and changelog

**Core Concepts Identified:**
- Backup/restore operations with snapshots
- Repository initialization and management
- Encryption and key management
- Multiple backend support (local, SFTP, S3, Azure, B2, GCS, etc.)
- Snapshot lifecycle management (forget/prune policies)
- Data verification and integrity checking
- Scripting/automation patterns
- Exit codes and error handling
- JSON output for programmatic use

---

## What This Repo Contributes To EMBIZ

**Operational Patterns for EMBIZ:**

1. **Snapshot-Based State Management**
   - Design files (SVG, PES, DST, etc.) versioned as snapshots
   - Customer order states captured at key milestones
   - Rollback capability for design iterations

2. **Repository Structure Principles**
   - Encrypted, deduplicated storage model
   - Multiple access keys (different agents/humans)
   - Backend-agnostic design (local + cloud options)

3. **Verification & Integrity Workflows**
   - Pre-upload verification (restic's `--no-extra-verify` pattern)
   - Post-operation checking (`check --read-data`)
   - Dry-run capabilities before destructive operations

4. **Automation & Scripting Patterns**
   - Environment variable configuration
   - Exit code handling for workflow decisions
   - JSON output for agent consumption
   - Password/credential management strategies

5. **Lifecycle Management**
   - Retention policies (keep-last, keep-daily, etc.)
   - Pruning strategies for storage optimization
   - Snapshot tagging and filtering

6. **Error Recovery Procedures**
   - Systematic troubleshooting steps
   - Index repair workflows
   - Backup-before-repair protocols

---

## EMBIZ-Specific Adaptation

### Repository Model for EMBIZ

**Primary Repository Types:**

1. **Design Asset Repository** (`/root/embroidery_business_agent_system/design_repo`)
   - Stores: SVG source files, converted embroidery formats (PES/DST/EXP/INF)
   - Snapshots: Tagged by customer order ID, design iteration
   - Retention: Keep all customer-approved versions indefinitely, prune intermediate iterations after 90 days

2. **Order State Repository** (`/root/embroidery_business_agent_system/order_repo`)
   - Stores: Order JSON documents, approval records, communication logs
   - Snapshots: Triggered on state transitions (received → quoted → approved → digitizing → completed)
   - Retention: Keep final state forever, intermediate states for 1 year

3. **Agent Knowledge Repository** (`/root/embroidery_business_agent_system/knowledge_repo`)
   - Stores: Learned patterns, customer preferences, digitizing templates
   - Snapshots: Daily automated backups
   - Retention: Keep weekly snapshots for 6 months, monthly for 2 years

### Snapshot Tagging Convention

```
--tag customer:<customer_id>
--tag order:<order_id>
--tag agent:<agent_name>
--tag state:<workflow_state>
--tag approval:<pending|approved|rejected>
--tag format:<svg|pes|dst|exp|inf|bmp>
```

### Verification Rules (Adapted from restic's verification model)

**Pre-Commit Verification:**
- File existence check (never claim file exists unless on disk)
- Format validation (SVG parseable, embroidery format headers valid)
- Metadata completeness (customer ID, order ID, agent attribution)

**Post-Snapshot Verification:**
- Restore dry-run to temp location
- Hash comparison against original
- Format-specific validation (embroidery file stitch count, color count)

### Automation Patterns

**Environment Variables (EMBIZ-specific):**
```bash
EMBIZ_DESIGN_REPO=/root/embroidery_business_agent_system/design_repo
EMBIZ_ORDER_REPO=/root/embroidery_business_agent_system/order_repo
EMBIZ_KNOWLEDGE_REPO=/root/embroidery_business_agent_system/knowledge_repo
EMBIZ_BACKUP_PASSWORD_FILE=/root/.embiz/repo_password
EMBIZ_SNAPSHOT_TAG_PREFIX=embiz
```

**Exit Code Handling (Adapted from restic exit codes):**
- 0: Success → Continue workflow
- 1: General failure → Alert human, halt workflow
- 3: Partial failure (e.g., some files unreadable) → Log warning, continue with available data
- 10: Repository doesn't exist → Initialize if first run, else alert
- 11: Lock failure → Retry with exponential backoff (3 attempts)
- 12: Wrong password → Alert human immediately (security issue)
- 130: Cancelled → Clean shutdown, preserve partial state

---

## Assigned Agent Ownership

**Meredith (Repository Manager)**
- **Primary Responsibility:** All snapshot operations, repository health
- **Tasks:**
  - Execute `backup` operations when design files are finalized
  - Run `check` operations daily (quick) and weekly (with `--read-data`)
  - Manage `forget`/`prune` policies
  - Handle repository initialization for new customers
  - Monitor repository size and backend health

**Mackenzie (Verification Specialist)**
- **Primary Responsibility:** Pre/post-snapshot verification
- **Tasks:**
  - Validate file existence before snapshot claims
  - Run `restore --dry-run` tests on critical snapshots
  - Verify embroidery file format integrity
  - Maintain verification logs for audit trail

**Miranda (Automation Coordinator)**
- **Primary Responsibility:** Scripting and scheduled operations
- **Tasks:**
  - Maintain backup automation scripts
  - Parse JSON output from restic commands
  - Handle exit code logic in workflows
  - Manage environment variable configuration
  - Coordinate with agent-msg bus for snapshot notifications

**Matilda (Recovery Specialist)**
- **Primary Responsibility:** Troubleshooting and repair
- **Tasks:**
  - Execute `repair index` when corruption detected
  - Follow systematic recovery procedures
  - Maintain backup copies before repair operations
  - Document recovery incidents for pattern analysis

---

## Local Skill / Knowledge Library Integration

**Integration Points:**

1. **Skill Library Path:** `/root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/restic`

2. **Knowledge Extraction:**
   - **Backup Patterns:** `doc/040_backup.rst` → EMBIZ design file backup workflows
   - **Restore Patterns:** `doc/050_restore.rst` → Customer design recovery procedures
   - **Scripting Patterns:** `doc/075_scripting.rst` → Agent automation templates
   - **Troubleshooting:** `doc/077_troubleshooting.rst` → Repository repair runbooks

3. **Skill Modules to Create:**
   - `embiz_snapshot_design.sh` - Wrapper for design file snapshots with EMBIZ tagging
   - `embiz_verify_snapshot.sh` - Post-snapshot verification with format checks
   - `embiz_restore_order.sh` - Order-specific restore with approval checks
   - `embiz_prune_policy.sh` - Retention policy enforcement with customer exceptions
   - `embiz_repo_health.sh` - Daily health check with Slack notifications

4. **Documentation to Generate:**
   - `EMBIZ_SNAPSHOT_GUIDE.md` - Adapted from restic docs for EMBIZ workflows
   - `EMBIZ_RECOVERY_RUNBOOK.md` - Based on troubleshooting guide
   - `EMBIZ_RETENTION_POLICY.md` - Forget/prune rules for design assets

---

## Runtime Rules

### Snapshot Creation Rules

1. **Design File Snapshots:**
   - **Trigger:** Design file saved to disk AND passes format validation
   - **Pre-Check:** File exists on disk (never claim existence without verification)
   - **Tags:** Customer ID, order ID, agent name, file format
   - **Verification:** Restore to temp, compare hash, validate format
   - **Notification:** Post to Slack (outbound-only) with snapshot ID

2. **Order State Snapshots:**
   - **Trigger:** Order state transition (e.g., approved → digitizing)
   - **Pre-Check:** Order JSON valid, all required fields present
   - **Tags:** Customer ID, order ID, state, approval status
   - **Verification:** JSON schema validation
   - **Notification:** Agent-msg bus notification to relevant agents

3. **Knowledge Snapshots:**
   - **Trigger:** Daily at 02:00 UTC (off-peak)
   - **Pre-Check:** Knowledge base consistency check
   - **Tags:** Date, agent contributions
   - **Verification:** Quick check (no `--read-data`)
   - **Notification:** Summary to Slack if changes detected

### Restore Rules

1. **Customer Design Restore:**
   - **Authorization:** Human approval required before restore
   - **Target:** Temporary directory first, never overwrite production
   - **Verification:** Format validation before delivery to customer
   - **Logging:** Full audit trail of restore operation

2. **Order State Rollback:**
   - **Authorization:** Human approval required
   - **Scope:** Restore specific order snapshot by ID
   - **Verification:** State consistency check before applying
   - **Notification:** Alert all agents involved in order

### Verification Rules

1. **Daily Quick Check:**
   - **Command:** `restic check` (no `--read-data`)
   - **Schedule:** 03:00 UTC daily
   - **Failure Action:** Alert Meredith, log to `/var/log/embiz/repo_health.log`

2. **Weekly Deep Check:**
   - **Command:** `restic check --read-data`
   - **Schedule:** Sunday 01:00 UTC
   - **Failure Action:** Alert human, halt all snapshot operations until resolved

3. **Pre-Snapshot Verification:**
   - **File Existence:** Stat file, verify size > 0
   - **Format Validation:** Run format-specific validator (SVG parser, embroidery header check)
   - **Metadata Check:** Customer ID, order ID present and valid

### Retention Policy Rules

1. **Design Files (Customer-Approved):**
   - **Keep:** Forever (no pruning)
   - **Rationale:** Legal/contractual obligation to preserve customer designs

2. **Design Files (Intermediate Iterations):**
   - **Keep:** Last 5 versions per order
   - **Prune:** After order completion + 90 days
   - **Command:** `restic forget --keep-last 5 --tag order:<id> --prune`

3. **Order States:**
   - **Keep:** Final state forever, intermediate states 1 year
   - **Command:** `restic forget --keep-within 1y --tag state:intermediate --prune`

4. **Knowledge Snapshots:**
   - **Keep:** Daily for 7 days, weekly for 6 months, monthly for 2 years
   - **Command:** `restic forget --keep-daily 7 --keep-weekly 26 --keep-monthly 24 --prune`

### Error Handling Rules

1. **Exit Code 0 (Success):**
   - Log success, continue workflow
   - Update snapshot registry

2. **Exit Code 1 (General Failure):**
   - Alert human via Slack
   - Halt workflow, preserve state
   - Log full error output

3. **Exit Code 3 (Partial Failure):**
   - Log warning with details
   - Continue with available data
   - Schedule retry for failed items

4. **Exit Code 10 (No Repository):**
   - If first run: Initialize repository
   - Else: Alert human (potential data loss)

5. **Exit Code 11 (Lock Failure):**
   - Retry 3 times with exponential backoff (5s, 15s, 45s)
   - If still failing: Alert human, check for stale locks

6. **Exit Code 12 (Wrong Password):**
   - Alert human immediately (security issue)
   - Halt all operations
   - Log incident for security audit

7. **Exit Code 130 (Cancelled):**
   - Clean shutdown
   - Preserve partial state
   - Log cancellation reason

---

## Required Files / Configs

### Repository Initialization Files

**Location:** `/root/embroidery_business_agent_system/repos/`

```
repos/
├── design_repo/          # Initialized with restic init
├── order_repo/           # Initialized with restic init
├── knowledge_repo/       # Initialized with restic init
└── .repo_passwords       # Encrypted password file (chmod 600)
```

### Configuration Files

**1. `/root/embroidery_business_agent_system/config/restic_env.sh`**
```bash
#!/bin/bash
# EMBIZ Restic Environment Configuration

export EMBIZ_DESIGN_REPO=/root/embroidery_business_agent_system/repos/design_repo
export EMBIZ_ORDER_REPO=/root/embroidery_business_agent_system/repos/order_repo
export EMBIZ_KNOWLEDGE_REPO=/root/embroidery_business_agent_system/repos/knowledge_repo

export RESTIC_PASSWORD_FILE=/root/embroidery_business_agent_system/repos/.repo_passwords
export RESTIC_COMPRESSION=auto
export RESTIC_PACK_SIZE=16  # 16 MiB default
export RESTIC_READ_CONCURRENCY=2  # Conservative for local disk

# Backup retention defaults
export EMBIZ_KEEP_DAILY=7
export EMBIZ_KEEP_WEEKLY=26
export EMBIZ_KEEP_MONTHLY=24
```

**2. `/root/embroidery_business_agent_system/config/snapshot_tags.json`**
```json
{
  "tag_schema": {
    "customer": "customer:<customer_id>",
    "order": "order:<order_id>",
    "agent": "agent:<agent_name>",
    "state": "state:<workflow_state>",
    "approval": "approval:<pending|approved|rejected>",
    "format": "format:<svg|pes|dst|exp|inf|bmp>"
  },
  "required_tags": ["customer", "order", "agent"],
  "optional_tags": ["state", "approval", "format"]
}
```

**3. `/root/embroidery_business_agent_system/config/retention_policy.json`**
```json
{
  "design_files": {
    "customer_approved": {
      "keep": "forever",
      "prune": false
    },
    "intermediate": {
      "keep_last": 5,
      "prune_after_days": 90,
      "condition": "order_completed"
    }
  },
  "order_states": {
    "final": {
      "keep": "forever"
    },
    "intermediate": {
      "keep_within": "1y"
    }
  },
  "knowledge": {
    "keep_daily": 7,
    "keep_weekly": 26,
    "keep_monthly": 24
  }
}
```

### Script Templates

**Location:** `/root/embroidery_business_agent_system/scripts/restic/`

**1. `embiz_snapshot_design.sh`**
```bash
#!/bin/bash
# EMBIZ Design File Snapshot Script
# Owner: Meredith (Repository Manager)

set -euo pipefail

source /root/embroidery_business_agent_system/config/restic_env.sh

DESIGN_FILE="$1"
CUSTOMER_ID="$2"
ORDER_ID="$3"
AGENT_NAME="$4"
FORMAT="$5"

# Pre-check: File exists
if [[ ! -f "$DESIGN_FILE" ]]; then
    echo "ERROR: File does not exist: $DESIGN_FILE" >&2
    exit 1
fi

# Pre-check: Format validation
case "$FORMAT" in
    svg)
        xmllint --noout "$DESIGN_FILE" || exit 1
        ;;
    pes|dst|exp|inf)
        # Run embroidery format validator (placeholder)
        /root/embroidery_business_agent_system/scripts/validate_embroidery.sh "$DESIGN_FILE" "$FORMAT" || exit 1
        ;;
    *)
        echo "ERROR: Unknown format: $FORMAT" >&2
        exit 1
        ;;
esac

# Create snapshot
restic -r "$EMBIZ_DESIGN_REPO" backup "$DESIGN_FILE" \
    --tag "customer:$CUSTOMER_ID" \
    --tag "order:$ORDER_ID" \
    --tag "agent:$AGENT_NAME" \
    --tag "format:$FORMAT" \
    --json > /tmp/snapshot_result.json

SNAPSHOT_ID=$(jq -r '.snapshot_id' /tmp/snapshot_result.json)

# Post-snapshot verification
/root/embroidery_business_agent_system/scripts/restic/embiz_verify_snapshot.sh "$SNAPSHOT_ID" "$DESIGN_FILE"

# Notify via agent-msg bus
/usr/local/bin/agent-msg publish snapshot.created \
    --snapshot-id "$SNAPSHOT_ID" \
    --customer-id "$CUSTOMER_ID" \
    --order-id "$ORDER_ID" \
    --agent "$AGENT_NAME"

echo "Snapshot created: $SNAPSHOT_ID"
```

**2. `embiz_verify_snapshot.sh`**
```bash
#!/bin/bash
# EMBIZ Snapshot Verification Script
# Owner: Mackenzie (Verification Specialist)

set -euo pipefail

source /root/embroidery_business_agent_system/config/restic_env.sh

SNAPSHOT_ID="$1"
ORIGINAL_FILE="$2"

TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

# Restore to temp
restic -r "$EMBIZ_DESIGN_REPO" restore "$SNAPSHOT_ID" --target "$TEMP_DIR" --quiet

# Find restored file (handle path structure)
RESTORED_FILE=$(find "$TEMP_DIR" -type f -name "$(basename "$ORIGINAL_FILE")")

if [[ ! -f "$RESTORED_FILE" ]]; then
    echo "ERROR: Restored file not found" >&2
    exit 1
fi

# Hash comparison
ORIGINAL_HASH=$(sha256sum "$ORIGINAL_FILE" | awk '{print $1}')
RESTORED_HASH=$(sha256sum "$RESTORED_FILE" | awk '{print $1}')

if [[ "$ORIGINAL_HASH" != "$RESTORED_HASH" ]]; then
    echo "ERROR: Hash mismatch - snapshot corrupted" >&2
    exit 1
fi

echo "Verification passed: $SNAPSHOT_ID"
```

**3. `embiz_prune_policy.sh`**
```bash
#!/bin/bash
# EMBIZ Retention Policy Enforcement
# Owner: Meredith (Repository Manager)

set -euo pipefail

source /root/embroidery_business_agent_system/config/restic_env.sh

# Knowledge repo: Standard retention
restic -r "$EMBIZ_KNOWLEDGE_REPO" forget \
    --keep-daily "$EMBIZ_KEEP_DAILY" \
    --keep-weekly "$EMBIZ_KEEP_WEEKLY" \
    --keep-monthly "$EMBIZ_KEEP_MONTHLY" \
    --prune \
    --dry-run  # Remove for actual execution

# Order repo: Keep final states forever, intermediate 1 year
restic -r "$EMBIZ_ORDER_REPO" forget \
    --keep-within 1y \
    --tag state:intermediate \
    --prune \
    --dry-run

# Design repo: Prune intermediate iterations (customer-approved never pruned)
# This requires custom logic to identify completed orders
# Placeholder for now
echo "Design repo pruning requires order completion check - manual review"
```

**4. `embiz_repo_health.sh`**
```bash
#!/bin/bash
# EMBIZ Repository Health Check
# Owner: Meredith (Repository Manager)

set -euo pipefail

source /root/embroidery_business_agent_system/config/restic_env.sh

LOG_FILE=/var/log/embiz/repo_health.log
SLACK_WEBHOOK_FILE=/root/.embiz/slack_webhook_url

check_repo() {
    local REPO_PATH=$1
    local REPO_NAME=$2
    local CHECK_DATA=$3
    
    echo "Checking $REPO_NAME..." | tee -a "$LOG_FILE"
    
    if [[ "$CHECK_DATA" == "true" ]]; then
        restic -r "$REPO_PATH" check --read-data 2>&1 | tee -a "$LOG_FILE"
    else
        restic -r "$REPO_PATH" check 2>&1 | tee -a "$LOG_FILE"
    fi
    
    local EXIT_CODE=$?
    
    if [[ $EXIT_CODE -ne 0 ]]; then
        echo "ERROR: $REPO_NAME check failed with exit code $EXIT_CODE" | tee -a "$LOG_FILE"
        
        # Alert to Slack (outbound-only)
        if [[ -f "$SLACK_WEBHOOK_FILE" ]]; then
            curl -X POST -H 'Content-type: application/json' \
                --data "{\"text\":\"⚠️ EMBIZ Repository Health Alert: $REPO_NAME check failed (exit code $EXIT_CODE)\"}" \
                "$(cat "$SLACK_WEBHOOK_FILE")"
        fi
        
        return $EXIT_CODE
    fi
    
    echo "$REPO_NAME check passed" | tee -a "$LOG_FILE"
    return 0
}

# Daily quick check (no --read-data)
if [[ "${1:-quick}" == "quick" ]]; then
    check_repo "$EMBIZ_DESIGN_REPO" "design_repo" false
    check_repo "$EMBIZ_ORDER_REPO" "order_repo" false
    check_repo "$EMBIZ_KNOWLEDGE_REPO" "knowledge_repo" false
# Weekly deep check (with --read-data)
elif [[ "$1" == "deep" ]]; then
    check_repo "$EMBIZ_DESIGN_REPO" "design_repo" true
    check_repo "$EMBIZ_ORDER_REPO" "order_repo" true
    check_repo "$EMBIZ_KNOWLEDGE_REPO" "knowledge_repo" true
fi
```

### Cron Jobs

**Location:** `/etc/cron.d/embiz-restic`

```cron
# EMBIZ Restic Scheduled Tasks

# Daily quick health check at 03:00 UTC
0 3 * * * root /root/embroidery_business_agent_system/scripts/restic/embiz_repo_health.sh quick

# Weekly deep health check on Sunday at 01:00 UTC
0 1 * * 0 root /root/embroidery_business_agent_system/scripts/restic/embiz_repo_health.sh deep

# Daily knowledge snapshot at 02:00 UTC
0 2 * * * root /root/embroidery_business_agent_system/scripts/restic/embiz_snapshot_knowledge.sh

# Weekly retention policy enforcement on Sunday at 04:00 UTC
0 4 * * 0 root /root/embroidery_business_agent_system/scripts/restic/embiz_prune_policy.sh
```

---

## Commands / Checks

### Initialization Commands

**Initialize Design Repository:**
```bash
restic -r /root/embroidery_business_agent_system/repos/design_repo init \
    --repository-version 2
```

**Initialize Order Repository:**
```bash
restic -r /root/embroidery_business_agent_system/repos/order_repo init \
    --repository-version 2
```

**Initialize Knowledge Repository:**
```bash
restic -r /root/embroidery_business_agent_system/repos/knowledge_repo init \
    --repository-version 2
```

### Daily Operations

**Create Design Snapshot:**
```bash
/root/embroidery_business_agent_system/scripts/restic/embiz_snapshot_design.sh \
    /path/to/design.svg \
    CUST123 \
    ORD456 \
    Maya \
    svg
```

**List Snapshots for Order:**
```bash
restic -r $EMBIZ_DESIGN_REPO snapshots \
    --tag order:ORD456 \
    --json
```

**Restore Design (Dry-Run):**
```bash
restic -r $EMBIZ_DESIGN_REPO restore latest \
    --tag order:ORD456 \
    --target /tmp/restore \
    --dry-run \
    --verbose=2
```

**Restore Design (Actual - Requires Human Approval):**
```bash
# Human approval check first
if [[ "$HUMAN_APPROVED" == "true" ]]; then
    restic -r $EMBIZ_DESIGN_REPO restore <snapshot-id> \
        --target /tmp/restore
fi
```

### Health Checks

**Quick Repository Check:**
```bash
restic -r $EMBIZ_DESIGN_REPO check
```

**Deep Repository Check (Weekly):**
```bash
restic -r $EMBIZ_DESIGN_REPO check --read-data
```

**Check Specific Snapshot:**
```bash
restic -r $EMBIZ_DESIGN_REPO check \
    --read-data-subset=<snapshot-id>
```

### Maintenance Commands

**Forget Intermediate Designs (Dry-Run):**
```bash
restic -r $EMBIZ_DESIGN_REPO forget \
    --keep-last 5 \
    --tag order:ORD456 \
    --tag approval:pending \
    --dry-run \
    --verbose
```

**Prune Repository:**
```bash
restic -r $EMBIZ_DESIGN_REPO prune \
    --dry-run  # Remove for actual execution
```

**Unlock Repository (Stale Lock):**
```bash
restic -r $EMBIZ_DESIGN_REPO unlock
```

### Recovery Commands

**Repair Index:**
```bash
restic -r $EMBIZ_DESIGN_REPO repair index
```

**Repair Pack Files:**
```bash
restic -r $EMBIZ_DESIGN_REPO repair packs
```

### Verification Commands

**List Files in Snapshot:**
```bash
restic -r $EMBIZ_DESIGN_REPO ls <snapshot-id> \
    --long \
    --json
```

**Find File Across Snapshots:**
```bash
restic -r $EMBIZ_DESIGN_REPO find design.svg \
    --tag customer:CUST123
```

**Diff Two Snapshots:**
```bash
restic -r $EMBIZ_DESIGN_REPO diff <snapshot-id-1> <snapshot-id-2>
```

### Monitoring Commands

**Repository Stats:**
```bash
restic -r $EMBIZ_DESIGN_REPO stats \
    --mode restore-size \
    --json
```

**Snapshot Summary:**
```bash
restic -r $EMBIZ_DESIGN_REPO snapshots \
    --group-by host,paths \
    --json
```

---

## Security Restrictions

### Access Control

1. **Repository Passwords:**
   - Stored in `/root/embroidery_business_agent_system/repos/.repo_passwords`
   - File permissions: `chmod 600` (owner read/write only)
   - Never logged, never transmitted via Slack
   - Rotated quarterly (manual process with human oversight)

2. **Repository Keys:**
   - Multiple keys supported (one per agent + human master key)
   - Agent keys: Limited to specific operations (backup, restore, check)
   - Human master key: Full access including key management
   - Key IDs logged for audit trail

3. **File System Permissions:**
   - Repository directories: `chmod 700` (owner only)
   - Snapshot scripts: `chmod 750` (owner execute, group read)
   - Configuration files: `chmod 640` (owner read/write, group read)

### Data Protection

1. **Encryption:**
   - All repositories use restic's built-in AES-256 encryption
   - Encryption keys derived from repository password
   - No plaintext data stored in repository

2. **Verification:**
   - Pre-snapshot: File existence, format validation
   - Post-snapshot: Restore dry-run, hash comparison
   - Never claim file exists unless verified on disk

3. **Audit Trail:**
   - All snapshot operations logged to `/var/log/embiz/snapshots.log`
   - Log rotation: 90 days retention
   - Includes: Timestamp, agent, customer ID, order ID, snapshot ID, exit code

### Network Security

1. **Backend Access:**
   - Local repositories: No network exposure
   - Cloud backends (if used): TLS 1.2+ required
   - Credentials stored in environment variables, never hardcoded

2. **Slack Notifications:**
   - Outbound-only (no inbound webhooks)
   - No sensitive data in messages (snapshot IDs only, no customer data)
   - Webhook URL stored in `/root/.embiz/slack_webhook_url` (chmod 600)

### Operational Security

1. **Human Approval Gates:**
   - Restore operations: Always require human approval
   - Repository initialization: Human approval required
   - Key rotation: Human-initiated only
   - Prune operations: Dry-run review required before execution

2. **Agent Restrictions:**
   - Agents cannot delete snapshots directly (only `forget` with human review)
   - Agents cannot modify repository configuration
   - Agents cannot access repository passwords directly (environment variable only)

3. **Backup Before Destructive Operations:**
   - Before `prune`: Create repository copy or verify recent backup
   - Before `repair`: Create index/snapshots backup
   - Before `forget`: Dry-run review and human approval

---

## Verification Checklist

### Pre-Deployment Verification

- [ ] All three repositories initialized (`design_repo`, `order_repo`, `knowledge_repo`)
- [ ] Repository passwords generated and stored securely
- [ ] File permissions set correctly (repos: 700, scripts: 750, configs: 640)
- [ ] Environment variables configured in `restic_env.sh`
- [ ] Snapshot tag schema validated against `snapshot_tags.json`
- [ ] Retention policy configured in `retention_policy.json`
- [ ] All scripts executable and tested with dry-run
- [ ] Cron jobs installed and scheduled correctly
- [ ] Slack webhook configured (if notifications enabled)
- [ ] Agent-msg bus integration tested

### Post-Deployment Verification

- [ ] Test snapshot creation for each file format (SVG, PES, DST, EXP, INF)
- [ ] Test snapshot verification (restore dry-run, hash comparison)
- [ ] Test snapshot listing with tag filters
- [ ] Test restore operation (with human approval simulation)
- [ ] Test forget/prune dry-run
- [ ] Test repository health check (quick and deep)
- [ ] Test exit code handling for all scenarios (0, 1, 3, 10, 11, 12, 130)
- [ ] Test JSON output parsing by agents
- [ ] Test Slack notifications (outbound-only)
- [ ] Test agent-msg bus notifications

### Ongoing Verification (Weekly)

- [ ] Review snapshot logs for anomalies
- [ ] Verify repository health check results
- [ ] Check repository size growth trends
- [ ] Review retention policy effectiveness
- [ ] Test restore operation on random snapshot
- [ ] Verify backup integrity with `check --read-data`
- [ ] Review agent access logs
- [ ] Confirm no stale locks present

### Quarterly Verification

- [ ] Rotate repository passwords
- [ ] Review and update retention policies
- [ ] Test full disaster recovery procedure
- [ ] Audit agent key usage
- [ ] Review and update documentation
- [ ] Performance tuning (pack size, concurrency)

---

## Build Tasks

### Initial Setup Tasks

**Task 1: Install Restic**
```bash
# Download latest restic binary
wget https://github.com/restic/restic/releases/latest/download/restic_0.17.3_linux_amd64.bz2
bunzip2 restic_0.17.3_linux_amd64.bz2
chmod +x restic_0.17.3_linux_amd64
sudo mv restic_0.17.3_linux_amd