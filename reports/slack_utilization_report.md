# Slack utilization report — delivery status

_Human-readable, per-source library-application messages for the embroidery pipeline.
This logs what was drafted and whether it was actually sent._

## Slack capability detection (what was found)

| check | result |
|---|---|
| env `SLACK_WEBHOOK_URL` | **not set** |
| env `SLACK_BOT_TOKEN` | **not set** |
| `config/slack.json` (from the read-only worktree) | present, but **no webhook URL or token**. Contents: `mode=outbound_only`, `command=openclaw-slack`, `can_read_replies=false`, `secret_rule="never print slack.env or webhook"` |
| `openclaw-slack` command (referenced by slack.json) | **not installed / not on PATH** |
| `config/webhook.env` | present, but it is an **EMBIZ internal webhook** (keys `EMBIZ_WEBHOOK_SECRET`, `EMBIZ_WEBHOOK_PORT`) — **not a Slack webhook** (no slack.com reference). Values were not printed, per the secret_rule. |

**Verdict: NO usable Slack webhook URL or bot token is available.** Nothing was
POSTed. No delivery was fabricated. (Note: `mcp__slackbot__*` MCP tools exist in the
runtime environment, but the requested webhook/token channel is undefined and the
sub-task specifies webhook/token + curl delivery; posting to an unknown channel was
not done to avoid fabricating a destination.)

## What is required to actually post

Provide **one** of the following, then re-run the POST step:

1. **`SLACK_WEBHOOK_URL`** environment variable containing an incoming-webhook URL
   (`https://hooks.slack.com/services/...`), OR
2. **`SLACK_BOT_TOKEN`** env var (+ a target channel) for the Slack Web API, OR
3. A **webhook/token field inside `config/slack.json`** (currently it only names the
   uninstalled `openclaw-slack` command with no URL) — or install/expose the
   `openclaw-slack` outbound command that `config/slack.json` points to.

With a webhook, each message below is posted via:

```
curl -sS -X POST -H 'Content-type: application/json' \
  --data '{"text":"<message>"}' "$SLACK_WEBHOOK_URL"
```

## Messages drafted (pending a webhook)

Written to `reports/slack_messages/` as one plain-English `.txt` per message. 39
sources are grouped sensibly (by transform vs the four pipeline themes) rather than one
message per source:

| file | contents | delivery status | HTTP code |
|---|---|---|---|
| `01_header.txt` | header: "Embroidery pipeline — library utilization report" | drafted, NOT sent | n/a (no webhook) |
| `02_transform_sources.txt` | Group A — Potrace / Inkscape / Ink-Stitch (the transform) | drafted, NOT sent | n/a |
| `03_pipeline_build_and_learn.txt` | Group B pt1 — build & knowledge extraction | drafted, NOT sent | n/a |
| `04_pipeline_verify_and_test.txt` | Group B pt2 — verification & testing | drafted, NOT sent | n/a |
| `05_pipeline_observe_and_log.txt` | Group B pt3 — observability & logging | drafted, NOT sent | n/a |
| `06_pipeline_review_secure_ship.txt` | Group B pt4 — review, security, shipping | drafted, NOT sent | n/a |
| `07_unused_and_honest_notes.txt` | honest "no current application" sources | drafted, NOT sent | n/a |
| `08_closing_summary.txt` | closing coverage summary (39 / 3 / 33 / 3) | drafted, NOT sent | n/a |

The drafts are natural-language and reusable: they state, for each source group, which
knowledge is now applied and where (transform vs pipeline), and are honest about the 3
unused sources. They mirror the machine-readable matrix in
`reports/library_utilization_coverage.md` / `knowledge/library_coverage.json`.
