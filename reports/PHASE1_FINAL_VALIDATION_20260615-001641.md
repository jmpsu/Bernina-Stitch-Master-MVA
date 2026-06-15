# Embiz Phase 1 Final Validation
Generated: 2026-06-15T00:16:41+02:00

## Services
active
active
active

## Public endpoints
/health 200
/dashboard 200
/api/jobs 200

## Newest job
/root/embroidery_business_agent_system/jobs/JOB-CF-20260614-235534

## Job state
{
  "job_id": "JOB-CF-20260614-235534",
  "status": "needs_review",
  "source": "cloudflare_email",
  "created": "2026-06-14T23:55:34.316842",
  "watcher_seen": "2026-06-14T23:55:41.334087",
  "pipeline_initialized": true,
  "current_stage": "requirements",
  "stages": {
    "requirements": {
      "status": "ready",
      "assigned_agent": "requirements",
      "task_file": "pipeline/requirements/task.md"
    },
    "artwork_prep": {
      "status": "waiting",
      "assigned_agent": "artwork_prep",
      "task_file": "pipeline/artwork_prep/task.md"
    },
    "digitizer": {
      "status": "waiting",
      "assigned_agent": "digitizer",
      "task_file": "pipeline/digitizer/task.md"
    },
    "qa": {
      "status": "waiting",
      "assigned_agent": "qa",
      "task_file": "pipeline/qa/task.md"
    },
    "customer_reply": {
      "status": "waiting",
      "assigned_agent": "customer_reply",
      "task_file": "pipeline/customer_reply/task.md"
    }
  },
  "approval_required_before_customer_contact": true,
  "approval_required_before_digitizing": true,
  "paid_model_use_allowed": false,
  "customer_email_auto_send_allowed": false,
  "updated": "2026-06-14T23:55:41.334093"
}
## Pipeline files
/root/embroidery_business_agent_system/jobs/JOB-CF-20260614-235534/pipeline/artwork_prep/output.md
/root/embroidery_business_agent_system/jobs/JOB-CF-20260614-235534/pipeline/artwork_prep/status.json
/root/embroidery_business_agent_system/jobs/JOB-CF-20260614-235534/pipeline/artwork_prep/task.md
/root/embroidery_business_agent_system/jobs/JOB-CF-20260614-235534/pipeline/customer_reply/draft.md
/root/embroidery_business_agent_system/jobs/JOB-CF-20260614-235534/pipeline/customer_reply/status.json
/root/embroidery_business_agent_system/jobs/JOB-CF-20260614-235534/pipeline/customer_reply/task.md
/root/embroidery_business_agent_system/jobs/JOB-CF-20260614-235534/pipeline/digitizer/output.md
/root/embroidery_business_agent_system/jobs/JOB-CF-20260614-235534/pipeline/digitizer/status.json
/root/embroidery_business_agent_system/jobs/JOB-CF-20260614-235534/pipeline/digitizer/task.md
/root/embroidery_business_agent_system/jobs/JOB-CF-20260614-235534/pipeline/orchestrator/decisions.md
/root/embroidery_business_agent_system/jobs/JOB-CF-20260614-235534/pipeline/orchestrator/handoff_log.md
/root/embroidery_business_agent_system/jobs/JOB-CF-20260614-235534/pipeline/orchestrator/timeline.md
/root/embroidery_business_agent_system/jobs/JOB-CF-20260614-235534/pipeline/qa/output.md
/root/embroidery_business_agent_system/jobs/JOB-CF-20260614-235534/pipeline/qa/status.json
/root/embroidery_business_agent_system/jobs/JOB-CF-20260614-235534/pipeline/qa/task.md
/root/embroidery_business_agent_system/jobs/JOB-CF-20260614-235534/pipeline/requirements/output.md
/root/embroidery_business_agent_system/jobs/JOB-CF-20260614-235534/pipeline/requirements/status.json
/root/embroidery_business_agent_system/jobs/JOB-CF-20260614-235534/pipeline/requirements/task.md

## Watcher log
2026-06-14T23:52:31.129249 START
2026-06-14T23:55:41.854191 PROCESSED JOB-CF-20260614-235534 slack=True

## Slack log
2026-06-14T23:55:41.584988 SLACK rc=0 stdout=ok stderr=

## Agent instructions
/root/embroidery_business_agent_system/agents/artwork_prep/instructions.md
/root/embroidery_business_agent_system/agents/business_ops/instructions.md
/root/embroidery_business_agent_system/agents/customer_reply/instructions.md
/root/embroidery_business_agent_system/agents/digitizer/instructions.md
/root/embroidery_business_agent_system/agents/gmail_intake/instructions.md
/root/embroidery_business_agent_system/agents/inkstitch_knowledge/instructions.md
/root/embroidery_business_agent_system/agents/orchestrator/instructions.md
/root/embroidery_business_agent_system/agents/qa/instructions.md
/root/embroidery_business_agent_system/agents/requirements/instructions.md
/root/embroidery_business_agent_system/agents/security_audit/instructions.md

## Policy
{
  "phase": "phase1_deterministic_orchestration",
  "paid_model_use_allowed": false,
  "customer_email_auto_send_allowed": false,
  "approval_required_before_customer_contact": true,
  "approval_required_before_digitizing": true,
  "fake_digitizing_outputs_allowed": false,
  "slack_is_one_way_notifications_only": true
}
## Tree file
/root/embroidery_business_agent_system/reports/CURRENT_SYSTEM_TREE_20260615-001641.txt
