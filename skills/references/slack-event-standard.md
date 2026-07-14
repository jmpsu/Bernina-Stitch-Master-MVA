# Slack / Event Standard (shared reference)

Source: `docs/requirements/EMBIZ_BRD.md` § "NAMED AGENT ROSTER" (uniform
Slack / Event Requirements) and `agents/contracts/*.json`
(`required_slack_events`).

Every EMBIZ agent, in every skill, obeys the same event discipline:

1. Publish or route a concise status update when a file is received,
   transformed, approved, rejected, escalated, or handed off.
2. **Approval messages** state exactly:
   - what was checked,
   - how it was checked,
   - why it passed,
   - which files are approved,
   - which agent owns the next step.
3. **Rejection / escalation messages** state exactly:
   - the failed gate,
   - the observed defect,
   - the likely cause,
   - the affected file,
   - the requested next action.
4. Messages never contain secrets; publication is routed through Mallory
   (Agent Bus / Slack Collaboration Agent, `agents/contracts/mallory.json`).

Skills cross-reference this file instead of restating these rules.
