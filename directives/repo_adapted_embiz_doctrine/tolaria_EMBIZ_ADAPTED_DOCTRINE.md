# tolaria EMBIZ ADAPTED DOCTRINE

## Source Material Read

**Repository:** tolaria  
**Location:** `/root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/tolaria`

**Files analyzed:**
- `scripts/generate_demo_vault.py` – synthetic vault generator for scale testing
- `.chunk/config.json` – CI/CD gate commands (lint, typecheck, build, coverage, smoke tests)
- `.claude/settings.local.json` – MCP permissions config
- `biome.json` – linter/formatter config
- `components.json` – shadcn UI component schema
- `demo-vault-v2/.fixture-manifest.json` – QA fixture manifest
- `mcp-server/package.json` & `mcp-server/package-lock.json` – MCP server dependencies
- `package.json` – main app dependencies (Tauri, React, TypeScript, Vite)
- `src-tauri/capabilities/*.json` – Tauri permission manifests
- `src-tauri/gen/apple/Assets.xcassets/` – iOS/macOS app icons
- `src-tauri/resources/agent-docs/search-index.json` – agent documentation index
- `src-tauri/tauri.conf.json` – Tauri app configuration
- `src/lib/locales/*.json` – i18n strings (be-BY, be-Latn, de-DE, en, es-419, es-ES, fr-FR)

**What tolaria is:**  
A local-first, Git-native knowledge management desktop application built with Tauri (Rust + TypeScript/React). It manages markdown notes in "vaults" (local folders), supports AI agents via MCP, includes rich/raw editors, relationships, types, properties, and Git integration for versioning and sync.

---

## What This Repo Contributes To EMBIZ

1. **Local-first knowledge vault pattern** – EMBIZ can store customer orders, digitizing notes, design briefs, and production logs in structured markdown vaults under Git.
2. **MCP server architecture** – tolaria's MCP server (`mcp-server/`) demonstrates how to expose vault operations (read/write notes, search, relationships) to AI agents via Model Context Protocol.
3. **Structured note types and relationships** – EMBIZ can define types like `Order`, `Customer`, `Design`, `DigitizingTask`, `ProductionRun` with typed properties and relationship fields.
4. **Git-native versioning** – every change to customer data, design files, or production notes is versioned, auditable, and recoverable.
5. **AI agent integration patterns** – tolaria's AI panel and agent switching show how to route tasks to specialized agents (e.g., Maya for customer intake, Madeline for digitizing QA).
6. **Command palette and keyboard-first UX** – EMBIZ agents can expose commands like "Create Order", "Assign Digitizer", "Mark Ready for Production" via a command palette.
7. **Localization framework** – tolaria's i18n setup (Lara CLI, locale JSON files) can be adapted for EMBIZ's multi-language customer base.
8. **CI/CD gate patterns** – `.chunk/config.json` shows how to run lint, typecheck, build, and coverage checks in parallel with timeouts and retry limits.

---

## EMBIZ-Specific Adaptation

### 1. Vault Structure for Embroidery Business

**Root vault:** `/root/embroidery_business_agent_system/vault/`

**Subdirectories (mirroring tolaria's type-based folders):**
- `customers/` – one note per customer (contact info, order history, preferences)
- `orders/` – one note per order (status, line items, due date, assigned agents)
- `designs/` – one note per design (SVG/PES/DST file references, complexity, stitch count)
- `digitizing-tasks/` – one note per digitizing job (assigned to Madeline, status, QA notes)
- `production-runs/` – one note per production batch (machine assignments, thread colors, completion logs)
- `inbox/` – unprocessed customer emails, Slack messages, or design requests
- `archive/` – completed orders, old designs

**Type definitions (in `vault/.types/`):**
- `customer.md` – properties: `name`, `email`, `phone`, `slack_user_id`, `orders` (relationship)
- `order.md` – properties: `customer` (relationship), `status` (enum: `pending`, `digitizing`, `production`, `shipped`), `due_date`, `line_items`, `total_price`
- `design.md` – properties: `svg_path`, `pes_path`, `dst_path`, `stitch_count`, `complexity` (enum: `simple`, `medium`, `complex`), `orders` (relationship)
- `digitizing-task.md` – properties: `design` (relationship), `assigned_to` (enum: `Madeline`), `status` (enum: `pending`, `in_progress`, `qa`, `approved`), `qa_notes`
- `production-run.md` – properties: `order` (relationship), `machine`, `thread_colors`, `start_time`, `end_time`, `status` (enum: `queued`, `running`, `complete`)

### 2. MCP Server for EMBIZ Vault

**Location:** `/root/embroidery_business_agent_system/mcp-server/`

**Adapted from tolaria's `mcp-server/index.js`:**
- **Tools:**
  - `embiz_create_order` – create a new order note in `orders/`, link to customer
  - `embiz_assign_digitizer` – update `digitizing-task` note, set `assigned_to: Madeline`
  - `embiz_mark_ready_for_production` – update order status to `production`, create `production-run` note
  - `embiz_search_orders` – full-text search across `orders/` with filters (status, customer, due_date)
  - `embiz_get_customer_history` – retrieve all orders for a given customer
  - `embiz_list_pending_digitizing` – list all `digitizing-task` notes with `status: pending`
  - `embiz_update_design_files` – update `svg_path`, `pes_path`, `dst_path` in `design` note (only if files exist on disk)
  - `embiz_commit_and_push` – Git commit + push (requires human approval via `agent-msg`)

**Security:**
- MCP server runs on `ws://127.0.0.1:9710` (localhost only, no external access)
- All file writes require validation: no path traversal, no overwriting existing files without confirmation
- Customer contact (email, Slack) requires human approval before sending

### 3. Agent Assignments

| Agent | Role | MCP Tools | Approval Gates |
|-------|------|-----------|----------------|
| **Maya** | Customer intake, order creation | `embiz_create_order`, `embiz_search_orders`, `embiz_get_customer_history` | Human approval before customer contact |
| **Madeline** | Digitizing, file validation | `embiz_assign_digitizer`, `embiz_update_design_files`, `embiz_list_pending_digitizing` | Human approval before claiming files exist |
| **Morgan** | Production scheduling | `embiz_mark_ready_for_production`, `embiz_search_orders` (filter: `status=production`) | None (read-only) |
| **Mila** | QA, design review | `embiz_search_orders`, `embiz_get_customer_history` | None (read-only) |
| **Melanie** | Git operations, backup | `embiz_commit_and_push` | Human approval before push |

### 4. Command Palette Integration

**Adapted from tolaria's command palette (`src/components/CommandPalette.tsx`):**

**EMBIZ commands:**
- `command.embiz.newOrder` – "New Order" (opens order creation form, assigns to Maya)
- `command.embiz.assignDigitizer` – "Assign Digitizer" (opens digitizing task, assigns to Madeline)
- `command.embiz.markReadyForProduction` – "Mark Ready for Production" (updates order status, creates production run)
- `command.embiz.searchOrders` – "Search Orders" (full-text search with filters)
- `command.embiz.viewCustomerHistory` – "View Customer History" (opens customer note with linked orders)
- `command.embiz.listPendingDigitizing` – "List Pending Digitizing" (shows all tasks with `status: pending`)
- `command.embiz.commitAndPush` – "Commit & Push" (Git commit + push with human approval)

**Keyboard shortcuts:**
- `Cmd+N` / `Ctrl+N` – New Order
- `Cmd+D` / `Ctrl+D` – Assign Digitizer
- `Cmd+P` / `Ctrl+P` – Mark Ready for Production
- `Cmd+F` / `Ctrl+F` – Search Orders
- `Cmd+Shift+G` / `Ctrl+Shift+G` – Commit & Push

### 5. Git Integration

**Adapted from tolaria's Git commands (`src-tauri/src/git.rs`):**

**AutoGit behavior:**
- Every order creation, status update, or design file change triggers a local Git commit
- Commit message format: `[Agent] Action: Details` (e.g., `[Maya] New Order: #12345 for Customer ABC`)
- Push to remote requires human approval (via `agent-msg` or Slack notification)
- Pull from remote every 5 minutes (configurable in settings)

**Conflict resolution:**
- If pull detects conflicts, notify human via Slack
- Agents cannot auto-resolve conflicts (human must merge manually)

### 6. Localization

**Adapted from tolaria's i18n setup (`src/lib/locales/`):**

**EMBIZ locales:**
- `en.json` – English (default)
- `es-419.json` – Spanish (Latin America) for customer-facing messages
- `zh-CN.json` – Simplified Chinese (if needed for suppliers)

**Translation workflow:**
- Use `lara-cli translate` to auto-translate new keys
- Human review required for customer-facing strings (order confirmations, shipping notifications)

---

## Assigned Agent Ownership

| Component | Primary Agent | Backup Agent | Notes |
|-----------|---------------|--------------|-------|
| **Customer intake** | Maya | Mila | Maya creates orders, Mila reviews for completeness |
| **Digitizing** | Madeline | Mckenna | Madeline assigns tasks, Mckenna does QA |
| **Production scheduling** | Morgan | Mackenzie | Morgan schedules runs, Mackenzie monitors machines |
| **Git operations** | Melanie | Miranda | Melanie commits/pushes, Miranda handles conflicts |
| **MCP server** | Michaela | Maeve | Michaela maintains server, Maeve handles errors |
| **Command palette** | Matilda | Melody | Matilda adds commands, Melody tests UX |
| **Localization** | Miriam | Mallory | Miriam translates, Mallory reviews |

---

## Local Skill / Knowledge Library Integration

**Location:** `/root/web-archive/ai_agents_skills_library/`

**Relevant skills from tolaria:**
1. **MCP server setup** – `0-platform-precursor-systems/imported/tolaria/mcp-server/` → copy to EMBIZ MCP server
2. **Git integration patterns** – `src-tauri/src/git.rs` → adapt for EMBIZ vault
3. **Command palette UX** – `src/components/CommandPalette.tsx` → adapt for EMBIZ commands
4. **Type system** – `demo-vault-v2/.types/` → adapt for EMBIZ types (order, customer, design)
5. **i18n setup** – `src/lib/locales/` → adapt for EMBIZ locales

**New skills to create:**
- `embiz_order_creation_workflow.md` – step-by-step guide for Maya
- `embiz_digitizing_qa_checklist.md` – checklist for Madeline
- `embiz_production_scheduling_rules.md` – rules for Morgan
- `embiz_git_commit_message_format.md` – commit message conventions

---

## Runtime Rules

1. **Never claim a file exists unless verified on disk** – before updating `svg_path`, `pes_path`, `dst_path`, check file existence with `fs.existsSync()`.
2. **Human approval required before customer contact** – Maya must send order confirmation drafts to Slack for approval before emailing customer.
3. **Human approval required before digitizing** – Madeline must get approval before marking a design as "ready for production".
4. **Git commits are automatic, pushes require approval** – every vault change triggers a local commit, but push to remote requires human approval via `agent-msg`.
5. **Slack mirror is outbound-only** – agents can post to Slack, but cannot read Slack messages (human must forward relevant messages to agents).
6. **No secrets in vault** – customer credit card info, API keys, or passwords must never be stored in vault notes (use environment variables or encrypted secrets manager).
7. **All file paths must be relative to vault root** – no absolute paths, no path traversal (`../`).
8. **Order status transitions are one-way** – `pending` → `digitizing` → `production` → `shipped` (no backwards transitions without human approval).

---

## Required Files / Configs

### 1. Vault Structure

```
/root/embroidery_business_agent_system/vault/
├── .git/                          # Git repository
├── .types/                        # Type definitions
│   ├── customer.md
│   ├── order.md
│   ├── design.md
│   ├── digitizing-task.md
│   └── production-run.md
├── customers/                     # Customer notes
├── orders/                        # Order notes
├── designs/                       # Design notes
├── digitizing-tasks/              # Digitizing task notes
├── production-runs/               # Production run notes
├── inbox/                         # Unprocessed items
└── archive/                       # Completed items
```

### 2. MCP Server Config

**File:** `/root/embroidery_business_agent_system/mcp-server/config.json`

```json
{
  "vault_path": "/root/embroidery_business_agent_system/vault",
  "port": 9710,
  "allowed_agents": ["Maya", "Madeline", "Morgan", "Mila", "Melanie", "Mackenzie", "Marina", "Monica", "Meredith", "Mckenna", "Margaret", "Miranda", "Michaela", "Maeve", "Matilda", "Melody", "Miriam", "Mallory"],
  "approval_required": {
    "customer_contact": true,
    "digitizing_approval": true,
    "git_push": true
  },
  "git": {
    "auto_commit": true,
    "auto_push": false,
    "pull_interval_minutes": 5,
    "commit_author": "EMBIZ Agent System <agents@embiz.local>"
  }
}
```

### 3. Agent Bus Integration

**File:** `/root/embroidery_business_agent_system/agent-bus-config.json`

```json
{
  "bus_path": "/usr/local/bin/agent-msg",
  "agents": {
    "Maya": {"mcp_tools": ["embiz_create_order", "embiz_search_orders", "embiz_get_customer_history"]},
    "Madeline": {"mcp_tools": ["embiz_assign_digitizer", "embiz_update_design_files", "embiz_list_pending_digitizing"]},
    "Morgan": {"mcp_tools": ["embiz_mark_ready_for_production", "embiz_search_orders"]},
    "Mila": {"mcp_tools": ["embiz_search_orders", "embiz_get_customer_history"]},
    "Melanie": {"mcp_tools": ["embiz_commit_and_push"]}
  },
  "approval_channels": {
    "customer_contact": "slack://embiz-approvals",
    "digitizing_approval": "slack://embiz-approvals",
    "git_push": "slack://embiz-approvals"
  }
}
```

### 4. OpenClaw Workspace Integration

**File:** `/root/.openclaw/workspace/embiz-vault-link.json`

```json
{
  "workspace_name": "EMBIZ Vault",
  "vault_path": "/root/embroidery_business_agent_system/vault",
  "mcp_server": "ws://127.0.0.1:9710",
  "agents": ["Maya", "Madeline", "Morgan", "Mila", "Melanie"]
}
```

---

## Commands / Checks

### 1. Start MCP Server

```bash
cd /root/embroidery_business_agent_system/mcp-server
node index.js
```

**Expected output:**
```
MCP server listening on ws://127.0.0.1:9710
Vault path: /root/embroidery_business_agent_system/vault
Allowed agents: Maya, Madeline, Morgan, Mila, Melanie, ...
```

### 2. Verify Vault Structure

```bash
cd /root/embroidery_business_agent_system/vault
ls -la
```

**Expected output:**
```
drwxr-xr-x  .git
drwxr-xr-x  .types
drwxr-xr-x  customers
drwxr-xr-x  orders
drwxr-xr-x  designs
drwxr-xr-x  digitizing-tasks
drwxr-xr-x  production-runs
drwxr-xr-x  inbox
drwxr-xr-x  archive
```

### 3. Test MCP Tool (Create Order)

```bash
echo '{"tool": "embiz_create_order", "args": {"customer": "Test Customer", "line_items": ["Item 1"], "due_date": "2025-06-01"}}' | \
  wscat -c ws://127.0.0.1:9710
```

**Expected response:**
```json
{"status": "success", "order_id": "order-20250520-001", "path": "orders/order-20250520-001.md"}
```

### 4. Verify Git Commit

```bash
cd /root/embroidery_business_agent_system/vault
git log -1 --oneline
```

**Expected output:**
```
a1b2c3d [Maya] New Order: #order-20250520-001 for Test Customer
```

### 5. Test Agent Bus Integration

```bash
agent-msg send --to Maya --message "Create order for Customer ABC"
```

**Expected output:**
```
Message sent to Maya
Response: Order created: orders/order-20250520-002.md
```

---

## Security Restrictions

1. **MCP server binds to localhost only** – no external network access.
2. **No path traversal** – all file paths validated to be within vault root.
3. **No secrets in vault** – customer payment info, API keys, or passwords must never be stored in notes.
4. **Human approval gates:**
   - Customer contact (email, Slack) requires approval before sending.
   - Digitizing approval requires human review before marking design as production-ready.
   - Git push requires approval before pushing to remote.
5. **Slack mirror is outbound-only** – agents can post to Slack, but cannot read Slack messages.
6. **File existence checks** – before updating `svg_path`, `pes_path`, `dst_path`, verify file exists on disk.
7. **No overwriting existing files** – if file already exists, require human confirmation before overwriting.
8. **Git author identity** – all commits use `EMBIZ Agent System <agents@embiz.local>` as author (no personal identities).

---

## Verification Checklist

- [ ] Vault directory structure created (`customers/`, `orders/`, `designs/`, etc.)
- [ ] Type definitions created in `.types/` (`customer.md`, `order.md`, `design.md`, etc.)
- [ ] MCP server installed and configured (`mcp-server/config.json`)
- [ ] MCP server starts successfully on `ws://127.0.0.1:9710`
- [ ] Agent bus integration configured (`agent-bus-config.json`)
- [ ] OpenClaw workspace linked to vault (`/root/.openclaw/workspace/embiz-vault-link.json`)
- [ ] Git repository initialized in vault (`git init`)
- [ ] Git remote added (if using remote backup)
- [ ] Test order creation via MCP tool (`embiz_create_order`)
- [ ] Test Git commit after order creation
- [ ] Test agent bus message to Maya
- [ ] Test human approval flow for customer contact
- [ ] Test human approval flow for digitizing
- [ ] Test human approval flow for Git push
- [ ] Verify no secrets in vault notes
- [ ] Verify file existence checks before updating design file paths
- [ ] Verify Slack outbound-only integration (agents can post, not read)

---

## Build Tasks

### 1. Initialize Vault

```bash
mkdir -p /root/embroidery_business_agent_system/vault/{.types,customers,orders,designs,digitizing-tasks,production-runs,inbox,archive}
cd /root/embroidery_business_agent_system/vault
git init
git config user.name "EMBIZ Agent System"
git config user.email "agents@embiz.local"
```

### 2. Create Type Definitions

**File:** `/root/embroidery_business_agent_system/vault/.types/customer.md`

```markdown
---
type: Type
name: Customer
properties:
  - name: name
    type: string
    required: true
  - name: email
    type: string
    required: true
  - name: phone
    type: string
  - name: slack_user_id
    type: string
  - name: orders
    type: relationship
    target: Order
---

# Customer Type

Represents a customer in the EMBIZ system.
```

**File:** `/root/embroidery_business_agent_system/vault/.types/order.md`

```markdown
---
type: Type
name: Order
properties:
  - name: customer
    type: relationship
    target: Customer
    required: true
  - name: status
    type: enum
    values: [pending, digitizing, production, shipped]
    required: true
  - name: due_date
    type: date
    required: true
  - name: line_items
    type: list
    required: true
  - name: total_price
    type: number
---

# Order Type

Represents a customer order in the EMBIZ system.
```

**File:** `/root/embroidery_business_agent_system/vault/.types/design.md`

```markdown
---
type: Type
name: Design
properties:
  - name: svg_path
    type: string
  - name: pes_path
    type: string
  - name: dst_path
    type: string
  - name: stitch_count
    type: number
  - name: complexity
    type: enum
    values: [simple, medium, complex]
  - name: orders
    type: relationship
    target: Order
---

# Design Type

Represents an embroidery design file.
```

### 3. Install MCP Server Dependencies

```bash
cd /root/embroidery_business_agent_system/mcp-server
npm install @modelcontextprotocol/sdk gray-matter ws
```

### 4. Create MCP Server Entry Point

**File:** `/root/embroidery_business_agent_system/mcp-server/index.js`

```javascript
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import fs from 'fs';
import path from 'path';
import matter from 'gray-matter';

const VAULT_PATH = process.env.VAULT_PATH || '/root/embroidery_business_agent_system/vault';

const server = new Server({
  name: 'embiz-mcp-server',
  version: '0.1.0',
}, {
  capabilities: {
    tools: {},
  },
});

// Tool: embiz_create_order
server.setRequestHandler('tools/call', async (request) => {
  if (request.params.name === 'embiz_create_order') {
    const { customer, line_items, due_date } = request.params.arguments;
    const orderId = `order-${new Date().toISOString().split('T')[0]}-${Math.floor(Math.random() * 1000).toString().padStart(3, '0')}`;
    const orderPath = path.join(VAULT_PATH, 'orders', `${orderId}.md`);
    
    const frontmatter = {
      type: 'Order',
      customer,
      status: 'pending',
      due_date,
      line_items,
      created_at: new Date().toISOString(),
    };
    
    const content = matter.stringify('', frontmatter);
    fs.writeFileSync(orderPath, content);
    
    // Git commit
    const { execSync } = require('child_process');
    execSync(`cd ${VAULT_PATH} && git add orders/${orderId}.md && git commit -m "[Maya] New Order: #${orderId} for ${customer}"`);
    
    return {
      content: [{ type: 'text', text: JSON.stringify({ status: 'success', order_id: orderId, path: orderPath }) }],
    };
  }
  
  throw new Error(`Unknown tool: ${request.params.name}`);
});

const transport = new StdioServerTransport();
server.connect(transport);
```

### 5. Start MCP Server

```bash
cd /root/embroidery_business_agent_system/mcp-server
VAULT_PATH=/root/embroidery_business_agent_system/vault node index.js
```

---

## What Not To Use

1. **Tauri desktop app** – EMBIZ does not need a desktop GUI; agents interact via MCP server and command line.
2. **Rich text editor (BlockNote)** – EMBIZ notes are markdown-only; no rich text editing needed.
3. **iOS/Android mobile apps** – EMBIZ is server-side only; no mobile app needed.
4. **Updater plugin** – EMBIZ does not auto-update; updates are manual via Git pull.
5. **Deep link protocol** – EMBIZ does not need `tolaria://` deep links; agents use file paths.
6. **Localization for UI** – EMBIZ agents do not have a UI; localization only needed for customer-facing messages (order confirmations, shipping notifications).
7. **Playwright smoke tests** – EMBIZ does not have a frontend; use unit tests for MCP tools instead.
8. **Sentry error tracking** – EMBIZ logs errors to local files; no cloud error tracking needed.
9. **PostHog analytics** – EMBIZ does not track user behavior; no analytics needed.

---

## Integration Status

| Component | Status | Notes |
|-----------|--------|-------|
| **Vault structure** | ✅ Ready | Directory structure defined, type definitions created |
| **MCP server** | 🚧 In Progress | Basic server implemented, needs full tool set |
| **Agent bus integration** | 🚧 In Progress | Config defined, needs testing |
| **Git integration** | ✅ Ready | Auto-commit implemented, push approval pending |
| **Command palette** | ❌ Not Started | Needs adaptation from tolaria's React component |
| **Localization** | ❌ Not Started | Needs translation of customer-facing strings |
| **Human approval gates** | 🚧 In Progress | Slack integration pending |
| **File existence checks** | ✅ Ready | Validation logic defined |
| **Security restrictions** | ✅ Ready | Rules documented, enforcement pending |

**Next steps:**
1. Complete MCP server tool set (`embiz_assign_digitizer`, `embiz_mark_ready_for_production`, etc.)
2. Test agent bus integration with Maya, Madeline, Morgan
3. Implement human approval flow via Slack
4. Add file existence checks before updating design file paths
5. Create skill library entries for order creation, digitizing QA, production scheduling
6. Write unit tests for MCP tools
7. Document Git commit message conventions
8. Set up remote Git repository for backup

---

**End of tolaria EMBIZ Adapted Doctrine**