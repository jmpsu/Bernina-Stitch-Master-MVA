---
name: agent-contract-compliance
description: Loads, obeys, and regenerates the machine-readable runtime contracts compiled from the BRD's named agent roster. Use at the start of any agent task to bind the agent to its contract, whenever the roster changes in the BRD, or when auditing that an agent's behavior matched its quality gates and Slack/event rules.
---

# Agent Contract Compliance

## Purpose

The BRD requires the 18×M named agent roster to be "compiled into enforceable
runtime contracts, not just markdown." This skill defines how agents load
their contract from `agents/contracts/`, how the contracts are regenerated
from the BRD, and how compliance is verified.

## When to Use

- At the start of every agent task: load the executing agent's contract.
- After any edit to the roster section of `docs/requirements/EMBIZ_BRD.md`.
- When auditing a completed job for gate and event compliance.

Do **not** hand-edit contract JSON — contracts are generated artifacts; edit
the BRD roster and recompile.

## Required Inputs

- `agents/contracts/<agent_id>.json` for the executing agent.
- `agents/contracts/index.json` for routing (handoff targets).
- Compiler: `scripts/compile_agent_contracts.py`.

## Repository Inspection Workflow

1. `python3 -c "import json; print(json.load(open('agents/contracts/index.json'))['agents'])"`
   — confirm all 18 agents are present.
2. Read the executing agent's contract; confirm `quality_gates`,
   `required_slack_events`, `approval_rules`, `rejection_rules`,
   `handoff_targets`, and `performance_metrics` are non-empty where the
   roster defines them.

## Architecture Inspection Workflow

1. Confirm the agent's position in the routing graph
   (BRD § "AGENT Production architecture"): ingress → Maya → specialized
   agents → Maya final approval → Mallory event log + Maeve/Marina knowledge
   capture.
2. When the Cloudflare Agents SDK runtime is adopted, each contract maps to
   one Durable Object agent; the contract is the operating contract that
   runtime must enforce.

## Agent Responsibility Separation Rules

An agent may only perform actions within its own contract's
`allowed_actions` and responsibilities. Work belonging to another roster
agent is routed to that agent (`handoff_targets`), never absorbed.

## Implementation Workflow

1. Load the contract JSON for the executing agent.
2. Before acting, check the action against `allowed_actions` and the
   contract's approval rules (e.g. Maya may grant approvals only with a
   fully itemized Slack approval message).
3. Execute the bounded task, honoring every `quality_gates` entry as a
   blocking gate — a failed gate produces a rejection, not a workaround.
4. Emit Slack/events per `skills/references/slack-event-standard.md`.
5. Hand off to the contracted next agent; record the file-state transition
   in the canonical job record.
6. To regenerate after a roster change:

```bash
python3 scripts/compile_agent_contracts.py
```

## Verification Workflow

```bash
python3 scripts/validate_skills.py --contracts
```

Checks: 18 contracts present, required fields populated, `agent_id` matches
filename, handoff targets resolve to existing agents, and index consistency.

## Evidence Requirements

- Validator output for the contracts check.
- For a job audit: the sequence of Slack/event messages against
  `required_slack_events`, and the gate-by-gate pass/fail record.

## Common Rationalizations

| Rationalization | Why it is incorrect | Required corrective action |
|---|---|---|
| "The gate obviously passes, no need to record it." | Contracts require observable evidence per gate; unrecorded gates are unverifiable. | Record what was checked, how, and why it passed. |
| "I'll just do the next agent's step myself." | Responsibility separation is a permanent design requirement. | Hand off to the contracted agent. |
| "The contract JSON is slightly wrong, I'll patch it." | Contracts are compiled artifacts; patches are lost on recompile. | Fix the BRD roster, re-run the compiler. |
| "Slack messages slow things down." | Slack-visible collaboration is a persistent BRD requirement. | Emit the required events. |

## Red Flags

- A contract JSON edited without a corresponding BRD roster change.
- An approval message missing any of: what/how/why/files/next owner.
- An agent acting outside its `allowed_actions`.
- Handoffs to agents not present in `handoff_targets`.

## Final Report Format

Follow `skills/references/final-report-standard.md`, extended with: contracts
regenerated (yes/no), validator output, and any roster/contract divergences
found.
