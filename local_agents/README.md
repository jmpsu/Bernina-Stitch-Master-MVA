# EMBIZ Local-First Autonomous Agent System

Persistent, autonomous, local-first agent daemons for the Bernina / EMBIZ
embroidery platform. Reasoning runs on **qwen3:8b via Ollama on the local GPU**
(Dell Pro Max 16 Premium, RTX PRO 2000 Blackwell, 8 GB VRAM, 100% GPU offload
verified). Paid model APIs are used ONLY as the final, audited, Slack-announced
escalation rung. The embroidery pipeline itself (`vectorizer.py`,
`digitizer.py`, `run_iteration.py`, `metrics.py`) is 100% local deterministic
Python and needs no LLM at all.

Full specification:
[`../EMBIZ_Jupiter_LOCAL_FIRST_Autonomous_Agent_FULL_VERSION.md`](../EMBIZ_Jupiter_LOCAL_FIRST_Autonomous_Agent_FULL_VERSION.md)

## Components

| File | Role |
|---|---|
| `qwen_client.py` | Ollama API client (`http://localhost:11434`), qwen3:8b, mandatory `<think>` block stripping, `/no_think` support, serialized GPU access |
| `model_router.py` | Local-first escalation ladder: qwen3:8b → local retry (bigger ctx / prompt strategy) → other `ollama list` models → paid API (env-gated, audited in `state/paid_usage_audit.jsonl`, Slack-announced) |
| `slack_daemon.py` | Socket Mode daemon owning all fifteen Slack responsibilities (monitoring, commands, slash commands, approvals, rejections, status updates, conversations, production/error notifications, ops reporting, workflow triggering, transcript logging, visible decision traces / QA results / progress) |
| `agent_loop.py` | Persistent plan → act → report loop: filesystem job queue, qwen3:8b planning, whitelisted deterministic pipeline tools, Slack approval gates, idle-period experimentation |
| `systemd/*.service` | systemd **user** units — the daemons run persistently and survive reboots |

## Prerequisites (on the Mint machine, user `jmmint`)

1. **Ollama with qwen3:8b** (already verified on this machine):

   ```bash
   ollama list                      # must show qwen3:8b
   curl -s localhost:11434/api/tags # runtime up
   nvidia-smi                       # RTX PRO 2000, driver 580.173.02
   ```

2. **Slack app** (one-time, at api.slack.com/apps):
   - Enable **Socket Mode** → generates the app-level token `xapp-...`
     (scope `connections:write`). No public URL / ingress / tunnel needed.
   - Bot token scopes: `app_mentions:read`, `channels:history`,
     `channels:read`, `chat:write`, `commands`, `im:history`, `im:read`,
     `im:write`, `reactions:read`.
   - Event subscriptions (Socket Mode): `app_mention`, `message.im`,
     `reaction_added`.
   - Slash command: `/embiz` (any placeholder URL — Socket Mode intercepts it).
   - Enable Interactivity (for the Approve/Reject buttons).
   - Install to the workspace; invite the bot to `#embiz-jobs`, `#embiz-qa`,
     `#embiz-alerts` (and `#embiz-artwork`).

## Install

```bash
cd ~/Bernina-Stitch-Master-MVA
python3 -m venv .venv
.venv/bin/pip install requests slack_sdk
```

### Environment file (no hardcoded secrets — required)

Create `~/.config/embiz/env` (or `/etc/embiz/env` and point the units at it),
mode 600:

```bash
mkdir -p ~/.config/embiz
cat > ~/.config/embiz/env <<'EOF'
# --- Slack (required) ---
SLACK_BOT_TOKEN=xoxb-...            # Bot User OAuth Token
SLACK_APP_TOKEN=xapp-...            # App-level token (Socket Mode)
EMBIZ_SLACK_CHANNEL_JOBS=#embiz-jobs
EMBIZ_SLACK_CHANNEL_QA=#embiz-qa
EMBIZ_SLACK_CHANNEL_ALERTS=#embiz-alerts
# Comma-separated Slack user IDs allowed to approve/reject (empty = anyone):
EMBIZ_SLACK_APPROVERS=U0XXXXXXX

# --- Local model (defaults shown) ---
EMBIZ_OLLAMA_URL=http://localhost:11434
EMBIZ_LOCAL_MODEL=qwen3:8b
EMBIZ_NUM_CTX_DEFAULT=4096
EMBIZ_NUM_CTX_MAX=16384

# --- Paid escalation rung 4 (OPTIONAL — leave unset to hard-disable paid use) ---
#EMBIZ_PAID_PROVIDER=anthropic      # or: openai
#EMBIZ_PAID_MODEL=<explicit model id — you choose, never a default>
#EMBIZ_PAID_API_KEY=...

# --- Behavior tuning (optional) ---
EMBIZ_REPORT_INTERVAL_S=21600       # ops report every 6h
EMBIZ_IDLE_EXPERIMENTS=1            # autonomous idle run_iteration.py sweeps
EMBIZ_IDLE_EXPERIMENT_INTERVAL_S=3600
EOF
chmod 600 ~/.config/embiz/env
```

### Enable the persistent services

```bash
mkdir -p ~/.config/systemd/user
cp local_agents/systemd/embiz-slack-daemon.service ~/.config/systemd/user/
cp local_agents/systemd/embiz-agent-loop.service   ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now embiz-slack-daemon.service embiz-agent-loop.service
loginctl enable-linger jmmint    # keep running after logout and across reboots
```

## Verify

```bash
systemctl --user status embiz-slack-daemon embiz-agent-loop
journalctl --user -u embiz-slack-daemon -f
journalctl --user -u embiz-agent-loop -f
```

Expected within a minute: startup messages in `#embiz-alerts`
(":satellite: EMBIZ Slack daemon online..." and ":robot_face: EMBIZ agent loop
online..."). Then in Slack:

```
/embiz health            -> operational report (queue, Ollama, score, paid usage)
/embiz models            -> local Ollama models (rung-3 candidates)
/embiz ask what do you do?   -> answered by qwen3:8b locally, think-stripped
/embiz run measure the corpus and report the overall score
```

The `run` command enqueues a job; the agent loop plans it with qwen3:8b,
executes the deterministic pipeline tools, posts step-by-step progress to
`#embiz-jobs`, QA output to `#embiz-qa`, and pauses at any `needs_approval`
step until you click **Approve**, react with a checkmark, or run
`/embiz approve JOB-ID`.

## Durable state

```
local_agents/state/
  queue/{pending,active,done,failed}/   filesystem job queue (atomic renames)
  approvals/{pending,decided}/          human-gate records
  slack_transcript.jsonl                every in/outbound Slack message
  paid_usage_audit.jsonl                every rung-4 paid call (cost ledger)
  router_events.jsonl                   every escalation-ladder decision
  daemon_heartbeat.json / agent_heartbeat.json
```

Decision traces continue to append to the repo-root `decision_trace.jsonl`
(existing convention) and significant ones are mirrored into Slack.

## Operating rules baked into the code

- **One model on the GPU at a time** (8 GB VRAM; qwen3:8b = 6.2 GB). All LLM
  calls are serialized; rung-3 model swaps are sequential, never parallel.
- **Think-stripping is mandatory**: every qwen3 response passes through
  `strip_think()` before any consumer sees it.
- **No agent calls a paid API directly** — only `model_router.route()`, and
  only after rungs 1–3 fail, and only if `EMBIZ_PAID_*` is configured. Every
  paid call is Slack-announced before and after and appended to the audit log.
- **Errors are never silent**: unhandled exceptions post to `#embiz-alerts`;
  systemd restarts the daemons (`Restart=always`).
