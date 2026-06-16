# hexo-ai-sia EMBIZ ADAPTED DOCTRINE

## Source Material Read

**Repository**: hexo-ai-sia  
**Type**: Self-Improving AI (SIA) framework - meta-learning orchestrator for iterative agent improvement  
**Core Pattern**: Meta-agent generates/improves target-agent code → target-agent executes task → feedback-agent analyzes results → loop

**Key Components Identified**:
- **Orchestrator** (`orchestrator.py`): Main evolution loop managing generations
- **Agent Implementations** (`agent_impls/`): Pluggable meta/feedback agent runners (claude, openhands, pydantic-ai)
- **Profiles System** (`profiles.py`, `providers.py`): JSON-based agent configuration (model, provider, reference code)
- **Agent Reference** (`agent_reference.py`): Seed code management (default/file/directory sources)
- **Task System** (`tasks/`, `layout.py`): Bundled tasks (GPQA, LawBench, etc.) with evaluation harnesses
- **Context Management** (`context_manager.py`): Tracks evolution across generations in `context.md`
- **Prompts** (`prompts.py`): Meta-agent and feedback-agent prompt builders
- **Run Setup** (`run_setup.py`): Virtual environment, directory structure, requirements installation

## What This Repo Contributes To EMBIZ

This is a **meta-learning orchestration pattern** that EMBIZ can adapt for:

1. **Iterative Agent Improvement**: Apply SIA's generation loop to improve embroidery-specific agents (quote generation, digitizing workflow, customer communication)
2. **Task-Specific Tuning**: Use the task/evaluation framework to create embroidery benchmarks (quote accuracy, design complexity assessment, customer satisfaction prediction)
3. **Multi-Agent Coordination**: Adapt the meta/feedback/target agent pattern for EMBIZ's named agent hierarchy
4. **Execution Logging**: Multi-trajectory logging pattern for tracking agent decisions across customer interactions
5. **Profile-Based Configuration**: JSON profiles for different agent roles/capabilities without code changes

**NOT a direct integration** - this is an architectural pattern to extract, not a library to import.

## EMBIZ-Specific Adaptation

### Core Pattern Translation

**SIA Pattern** → **EMBIZ Application**:

```
Meta-Agent (generates code)     → Madeline (workflow architect, generates agent coordination logic)
Target-Agent (executes task)    → Maya/Morgan/Mila (execute customer-facing tasks)
Feedback-Agent (analyzes)       → Meredith (quality analyst, reviews outcomes)
Task (GPQA, LawBench)          → EMBIZ Tasks (quote generation, design assessment, customer communication)
Generation Loop                 → Weekly improvement cycles on agent performance
```

### Adapted Components

#### 1. **EMBIZ Agent Profile System**
```json
// /root/embroidery_business_agent_system/config/agent_profiles/maya_quote_agent.json
{
  "profile_id": "maya-quote-v1",
  "agent_name": "Maya",
  "role": "quote_generation",
  "model": "claude-sonnet-4-20250514",
  "provider_id": "anthropic-main",
  "agent_reference": {
    "source": "/root/embroidery_business_agent_system/agents/maya/quote_logic.py",
    "entrypoint": "generate_quote.py"
  },
  "evaluation_metrics": ["quote_accuracy", "customer_acceptance_rate", "processing_time"]
}
```

#### 2. **EMBIZ Task Structure**
```
/root/embroidery_business_agent_system/tasks/
├── quote_generation/
│   ├── data/
│   │   ├── public/
│   │   │   ├── task.md              # Quote generation requirements
│   │   │   ├── sample_quotes.json   # Historical quotes (anonymized)
│   │   │   └── evaluate.py          # Quote accuracy evaluator
│   │   └── private/
│   │       └── ground_truth.json    # Actual accepted quotes
│   └── reference/
│       ├── reference_target_agent.py  # Maya's baseline quote logic
│       └── SAMPLE_TASK_DESCRIPTIONS.md
├── design_assessment/
│   └── ... (similar structure)
└── _shared/
    └── embiz_tools.py  # Shared EMBIZ-specific tools
```

#### 3. **EMBIZ Orchestrator Adaptation**
```python
# /root/embroidery_business_agent_system/orchestration/embiz_improvement_loop.py

from sia.orchestrator import run_generation  # Import pattern, not direct use
from embiz.agents import get_agent_by_name
from embiz.approval import require_human_approval

async def run_embiz_improvement_cycle(
    task: str,  # "quote_generation", "design_assessment", etc.
    target_agent_name: str,  # "Maya", "Morgan", etc.
    meta_agent_name: str = "Madeline",
    feedback_agent_name: str = "Meredith",
    max_generations: int = 3
):
    """
    Adapted SIA generation loop for EMBIZ agent improvement.
    
    Key differences from SIA:
    - Human approval gates before customer-facing changes
    - File existence verification for design files
    - Slack notification (outbound-only) for improvement milestones
    - Integration with OpenClaw workspace for persistent storage
    """
    
    # Setup (adapted from sia.run_setup)
    run_dir = f"/root/.openclaw/workspace/improvement_runs/{task}_{datetime.now():%Y%m%d_%H%M%S}"
    os.makedirs(run_dir, exist_ok=True)
    
    for gen in range(1, max_generations + 1):
        logger.info(f"=== Generation {gen}/{max_generations} ===")
        
        # 1. Meta-agent generates improved target agent code
        if gen == 1:
            # Use reference implementation
            agent_code = load_reference_agent(task, target_agent_name)
        else:
            # Madeline generates improvement based on Meredith's feedback
            agent_code = await generate_improvement(
                meta_agent=meta_agent_name,
                previous_code=previous_agent_code,
                feedback=feedback_from_meredith,
                task_context=task
            )
        
        # 2. EMBIZ-SPECIFIC: Human approval before deployment
        if gen > 1:
            approval = await require_human_approval(
                f"Approve {target_agent_name} code changes for {task}?",
                diff=compute_diff(previous_agent_code, agent_code),
                agent_bus="/usr/local/bin/agent-msg"
            )
            if not approval:
                logger.warning(f"Generation {gen} rejected by human. Stopping.")
                break
        
        # 3. Execute target agent on test cases
        results = await execute_target_agent(
            agent_name=target_agent_name,
            agent_code=agent_code,
            task=task,
            working_dir=f"{run_dir}/gen_{gen}"
        )
        
        # 4. Evaluate results
        metrics = evaluate_task(task, results)
        
        # 5. Feedback agent analyzes
        feedback_from_meredith = await generate_feedback(
            feedback_agent=feedback_agent_name,
            results=results,
            metrics=metrics,
            agent_code=agent_code
        )
        
        # 6. Log to context.md (adapted from sia.context_manager)
        update_context_md(run_dir, gen, agent_code, metrics, feedback_from_meredith)
        
        # 7. Slack notification (outbound-only)
        await notify_slack(
            f"🔄 {target_agent_name} improvement cycle {gen}/{max_generations} complete. "
            f"Metrics: {metrics}"
        )
        
        previous_agent_code = agent_code
```

#### 4. **EMBIZ-Specific Tools** (adapted from `_shared/reference_target_agent.py`)
```python
# /root/embroidery_business_agent_system/tasks/_shared/embiz_tools.py

import subprocess
from pathlib import Path

EMBIZ_TOOLS = [
    {
        "name": "verify_design_file",
        "description": "Verify a design file exists on disk before claiming it exists. REQUIRED before mentioning SVG/PES/DST/EXP/INF/BMP files to customers.",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Absolute path to design file"},
                "file_type": {"type": "string", "enum": ["SVG", "PES", "DST", "EXP", "INF", "BMP"]}
            },
            "required": ["file_path", "file_type"]
        }
    },
    {
        "name": "request_human_approval",
        "description": "Request human approval before customer contact or digitizing. REQUIRED for customer-facing actions.",
        "input_schema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "description": "Action requiring approval"},
                "context": {"type": "string", "description": "Context for approval decision"}
            },
            "required": ["action", "context"]
        }
    },
    {
        "name": "check_openclaw_workspace",
        "description": "Check if a file exists in OpenClaw workspace.",
        "input_schema": {
            "type": "object",
            "properties": {
                "relative_path": {"type": "string", "description": "Path relative to /root/.openclaw/workspace"}
            },
            "required": ["relative_path"]
        }
    }
]

def verify_design_file(file_path: str, file_type: str) -> dict:
    """EMBIZ-specific: Never claim a design file exists unless verified on disk."""
    path = Path(file_path)
    if not path.exists():
        return {
            "exists": False,
            "error": f"{file_type} file does not exist: {file_path}",
            "instruction": "DO NOT mention this file to customer. Generate it first or use a different file."
        }
    
    if not path.suffix.upper() == f".{file_type}":
        return {
            "exists": True,
            "error": f"File exists but wrong type. Expected {file_type}, got {path.suffix}",
            "instruction": "Verify file type before proceeding."
        }
    
    return {
        "exists": True,
        "file_path": str(path.absolute()),
        "file_size": path.stat().st_size,
        "message": f"✓ {file_type} file verified on disk"
    }

def request_human_approval(action: str, context: str) -> dict:
    """EMBIZ-specific: Human approval gate."""
    # Write approval request to agent bus
    request_file = f"/tmp/approval_request_{os.getpid()}.json"
    with open(request_file, 'w') as f:
        json.dump({"action": action, "context": context, "timestamp": datetime.now().isoformat()}, f)
    
    # Send via agent-msg (blocks until response)
    result = subprocess.run(
        ["/usr/local/bin/agent-msg", "request-approval", request_file],
        capture_output=True,
        text=True,
        timeout=300  # 5 min timeout
    )
    
    if result.returncode == 0:
        return {"approved": True, "message": "Human approved action"}
    else:
        return {"approved": False, "message": "Human rejected action", "reason": result.stderr}
```

## Assigned Agent Ownership

| SIA Component | EMBIZ Agent Owner | Responsibility |
|---------------|-------------------|----------------|
| **Meta-Agent** (code generation) | **Madeline** | Generates improved agent logic based on feedback |
| **Feedback-Agent** (analysis) | **Meredith** | Analyzes agent performance, identifies improvement areas |
| **Target-Agent** (task execution) | **Maya, Morgan, Mila, etc.** | Execute customer-facing tasks (quotes, design, communication) |
| **Orchestrator** (loop management) | **Mackenzie** | Manages improvement cycles, coordinates agents |
| **Evaluation** (metrics) | **Melody** | Runs evaluation harnesses, computes metrics |
| **Context Management** | **Miranda** | Maintains improvement history in context.md |

## Local Skill / Knowledge Library Integration

### Storage Locations

```
/root/web-archive/ai_agents_skills_library/
└── 0-platform-precursor-systems/
    └── imported/
        └── hexo-ai-sia/          # This repo (reference only, not executed)
            └── sia/
                ├── orchestrator.py      → Pattern for /root/embroidery_business_agent_system/orchestration/
                ├── agent_impls/         → Pattern for agent execution strategies
                ├── profiles.py          → Pattern for /root/embroidery_business_agent_system/config/agent_profiles/
                └── tasks/               → Pattern for /root/embroidery_business_agent_system/tasks/

/root/embroidery_business_agent_system/
├── orchestration/
│   ├── embiz_improvement_loop.py    # Adapted from sia.orchestrator
│   └── generation_runner.py         # Adapted from sia.run_setup
├── config/
│   ├── agent_profiles/              # Adapted from sia/profiles/
│   │   ├── maya_quote_agent.json
│   │   ├── madeline_meta_agent.json
│   │   └── meredith_feedback_agent.json
│   └── providers/                   # Adapted from sia/providers/
│       ├── anthropic_main.json
│       └── openai_backup.json
├── tasks/                           # Adapted from sia/tasks/
│   ├── quote_generation/
│   ├── design_assessment/
│   └── _shared/
│       └── embiz_tools.py
└── agents/                          # Target agent implementations
    ├── maya/
    │   └── quote_logic.py
    ├── morgan/
    └── mila/

/root/.openclaw/workspace/
└── improvement_runs/                # Equivalent to sia's ./runs/
    ├── quote_generation_20250527_143022/
    │   ├── gen_1/
    │   ├── gen_2/
    │   ├── gen_3/
    │   └── context.md
    └── design_assessment_20250528_091544/
```

### Knowledge Extraction Commands

```bash
# Extract orchestration pattern
cd /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia
grep -A 50 "def run_generation" sia/orchestrator.py > /tmp/sia_generation_pattern.txt

# Extract profile system pattern
grep -A 30 "class MetaAgentProfile" sia/profiles.py > /tmp/sia_profile_pattern.txt

# Extract multi-trajectory logging pattern
grep -A 40 "class MultiTrajectoryLogger" sia/tasks/_shared/reference_target_agent.py > /tmp/sia_logging_pattern.txt

# Copy to EMBIZ knowledge base
cp /tmp/sia_*_pattern.txt /root/embroidery_business_agent_system/docs/patterns/
```

## Runtime Rules

### Execution Constraints

1. **NEVER execute SIA code directly** - this is a pattern library, not a runtime dependency
2. **Human approval required** before:
   - Deploying improved agent code to production
   - Any customer contact from improved agents
   - Any digitizing operations from improved agents
3. **File verification required** before claiming design files exist:
   ```python
   # WRONG (SIA pattern)
   return f"Here's your design: {file_path}"
   
   # RIGHT (EMBIZ adaptation)
   verified = verify_design_file(file_path, "PES")
   if not verified["exists"]:
       return "I need to generate that file first. One moment..."
   return f"Here's your design: {verified['file_path']}"
   ```
4. **Slack notifications** are outbound-only (no secrets, no interactive responses)
5. **Agent bus** (`/usr/local/bin/agent-msg`) is the only inter-agent communication channel
6. **OpenClaw workspace** (`/root/.openclaw/workspace`) is the only persistent storage for improvement runs

### Improvement Cycle Workflow

```
1. Mackenzie initiates improvement cycle for task X
2. Madeline (meta-agent) generates improved code for target agent Y
3. Human reviews code diff via agent-msg approval request
4. If approved:
   a. Melody runs evaluation harness on test cases
   b. Meredith analyzes results, generates feedback
   c. Miranda updates context.md with generation summary
   d. Slack notification sent (outbound-only)
5. If rejected:
   a. Cycle stops, context.md notes rejection
   b. Slack notification sent with rejection reason
6. Repeat for max_generations or until human stops
```

## Required Files / Configs

### Minimum EMBIZ Adaptation Setup

```
/root/embroidery_business_agent_system/
├── config/
│   ├── agent_profiles/
│   │   ├── madeline_meta_agent.json       # REQUIRED: Meta-agent profile
│   │   ├── meredith_feedback_agent.json   # REQUIRED: Feedback-agent profile
│   │   └── maya_quote_agent.json          # REQUIRED: At least one target agent profile
│   ├── providers/
│   │   └── anthropic_main.json            # REQUIRED: At least one provider
│   └── embiz_config.json                  # REQUIRED: Global EMBIZ settings
├── orchestration/
│   ├── embiz_improvement_loop.py          # REQUIRED: Main orchestrator
│   └── generation_runner.py               # REQUIRED: Generation execution
├── tasks/
│   ├── quote_generation/                  # REQUIRED: At least one task
│   │   ├── data/public/task.md
│   │   ├── data/public/evaluate.py
│   │   └── reference/reference_target_agent.py
│   └── _shared/
│       └── embiz_tools.py                 # REQUIRED: EMBIZ-specific tools
└── docs/
    └── patterns/
        └── sia_adaptation_notes.md        # REQUIRED: This doctrine document
```

### Environment Variables

```bash
# Required for meta/feedback agents
export ANTHROPIC_API_KEY="sk-ant-..."

# Required for OpenClaw integration
export OPENCLAW_WORKSPACE="/root/.openclaw/workspace"

# Required for agent bus
export AGENT_BUS_PATH="/usr/local/bin/agent-msg"

# Optional: Override default improvement settings
export EMBIZ_MAX_GENERATIONS=5
export EMBIZ_APPROVAL_TIMEOUT=300  # seconds
```

## Commands / Checks

### Setup Commands

```bash
# 1. Create EMBIZ task structure (adapted from SIA)
cd /root/embroidery_business_agent_system
mkdir -p tasks/quote_generation/{data/{public,private},reference}
mkdir -p tasks/_shared
mkdir -p config/{agent_profiles,providers}
mkdir -p orchestration

# 2. Copy SIA patterns (reference only)
cp /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/sia/tasks/_shared/reference_target_agent.py \
   tasks/_shared/embiz_tools.py.template

# 3. Initialize OpenClaw workspace for improvement runs
mkdir -p /root/.openclaw/workspace/improvement_runs

# 4. Verify agent bus exists
test -x /usr/local/bin/agent-msg && echo "✓ Agent bus found" || echo "✗ Agent bus missing"

# 5. Create initial agent profiles
cat > config/agent_profiles/madeline_meta_agent.json <<EOF
{
  "profile_id": "madeline-meta-v1",
  "agent_name": "Madeline",
  "role": "meta_agent",
  "model": "claude-sonnet-4-20250514",
  "provider_id": "anthropic-main",
  "agent_impl": "claude"
}
EOF
```

### Runtime Checks

```bash
# Check if improvement run is active
ls -lt /root/.openclaw/workspace/improvement_runs/ | head -5

# Verify agent profile validity
python3 -c "
from embiz.config import load_agent_profile
profile = load_agent_profile('madeline_meta_agent')
print(f'✓ Profile valid: {profile.agent_name}')
"

# Check last improvement cycle results
tail -50 /root/.openclaw/workspace/improvement_runs/*/context.md

# Verify design file before claiming it exists (CRITICAL)
python3 -c "
from embiz.tools import verify_design_file
result = verify_design_file('/path/to/design.pes', 'PES')
print(result)
"

# Test human approval flow
/usr/local/bin/agent-msg request-approval '{"action": "test", "context": "verification"}'
```

### Monitoring Commands

```bash
# Watch improvement cycle progress
watch -n 5 'ls -lh /root/.openclaw/workspace/improvement_runs/*/gen_*/results.json'

# Check Slack notification log (outbound-only)
tail -f /var/log/embiz/slack_notifications.log

# Monitor agent bus messages
tail -f /var/log/embiz/agent_bus.log

# Check approval request queue
ls -lh /tmp/approval_request_*.json
```

## Security Restrictions

### Critical EMBIZ Constraints (from context)

1. **File Existence Verification**:
   ```python
   # NEVER do this (SIA pattern allows it)
   return f"Your PES file is ready: design_123.pes"
   
   # ALWAYS do this (EMBIZ requirement)
   verified = verify_design_file("design_123.pes", "PES")
   if not verified["exists"]:
       raise FileNotFoundError("Cannot claim file exists when it doesn't")
   return f"Your PES file is ready: {verified['file_path']}"
   ```

2. **Human Approval Gates**:
   - **Before customer contact**: Any email, Slack message, or communication generated by improved agent
   - **Before digitizing**: Any operation that creates/modifies PES/DST/EXP files
   - **Before code deployment**: Any improved agent code moving to production

3. **Slack Mirror Restrictions**:
   - **Outbound-only**: Can send notifications, cannot read responses
   - **No secrets**: Never include API keys, file paths with sensitive data, customer PII
   - **Format**: Plain text summaries only, no JSON blobs

4. **Agent Bus Security**:
   - **Only communication channel**: No direct agent-to-agent function calls
   - **Logged**: All messages logged to `/var/log/embiz/agent_bus.log`
   - **Timeout**: 5-minute max wait for approval responses

5. **OpenClaw Workspace Isolation**:
   - **Read-only for agents**: Agents can read from workspace, but writes go through approval
   - **No customer data**: Never store raw customer emails, payment info, or PII in workspace
   - **Cleanup**: Old improvement runs auto-archived after 30 days

### SIA Patterns to REJECT for EMBIZ

| SIA Pattern | Why Rejected for EMBIZ | EMBIZ Alternative |
|-------------|------------------------|-------------------|
| Direct file writes without verification | Could claim non-existent files | `verify_design_file()` before any file reference |
| Autonomous code deployment | No human oversight | Human approval via agent-msg before deployment |
| Slack interactive responses | Security risk, not supported | Outbound-only notifications |
| Direct LLM API calls from target agents | Uncontrolled costs, no approval | All LLM calls go through meta/feedback agents with human approval |
| Arbitrary shell commands | Security risk | Whitelist of allowed commands in `embiz_tools.py` |

## Verification Checklist

### Before Running Improvement Cycle

- [ ] Agent profiles exist in `/root/embroidery_business_agent_system/config/agent_profiles/`
- [ ] Provider configs exist in `/root/embroidery_business_agent_system/config/providers/`
- [ ] Task directory has `data/public/task.md` and `data/public/evaluate.py`
- [ ] Reference agent exists in `tasks/{task_name}/reference/reference_target_agent.py`
- [ ] `ANTHROPIC_API_KEY` environment variable set
- [ ] Agent bus (`/usr/local/bin/agent-msg`) is executable
- [ ] OpenClaw workspace (`/root/.openclaw/workspace`) is writable
- [ ] Human approval mechanism tested and working
- [ ] Slack notification endpoint configured (outbound-only)

### After Each Generation

- [ ] `context.md` updated with generation summary
- [ ] `results.json` exists in generation directory
- [ ] Human approval logged in agent bus log
- [ ] No design files claimed without disk verification
- [ ] Slack notification sent (if configured)
- [ ] No secrets leaked in logs or notifications
- [ ] Agent execution logs saved to OpenClaw workspace

### Before Production Deployment

- [ ] All generations reviewed by human
- [ ] Evaluation metrics show improvement over baseline
- [ ] No regressions in critical metrics (quote accuracy, customer satisfaction)
- [ ] Code diff reviewed and approved
- [ ] Rollback plan documented
- [ ] Monitoring alerts configured for new agent version

## Build Tasks

### Initial Setup (One-Time)

```bash
# Task 1: Create EMBIZ directory structure
cd /root/embroidery_business_agent_system
mkdir -p {config/{agent_profiles,providers},orchestration,tasks/_shared,docs/patterns}

# Task 2: Extract SIA patterns to EMBIZ docs
cd /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia
grep -A 100 "def run_generation" sia/orchestrator.py > \
  /root/embroidery_business_agent_system/docs/patterns/sia_orchestration_pattern.py
grep -A 50 "class MultiTrajectoryLogger" sia/tasks/_shared/reference_target_agent.py > \
  /root/embroidery_business_agent_system/docs/patterns/sia_logging_pattern.py

# Task 3: Create EMBIZ-specific tools (adapted from SIA reference agent)
cat > /root/embroidery_business_agent_system/tasks/_shared/embiz_tools.py <<'EOF'
# Adapted from hexo-ai-sia/sia/tasks/_shared/reference_target_agent.py
# EMBIZ-specific additions: verify_design_file, request_human_approval, check_openclaw_workspace

import subprocess
import json
from pathlib import Path
from datetime import datetime

# [Insert EMBIZ tools from "EMBIZ-Specific Adaptation" section above]
EOF

# Task 4: Create initial agent profiles
cat > /root/embroidery_business_agent_system/config/agent_profiles/madeline_meta_agent.json <<'EOF'
{
  "profile_id": "madeline-meta-v1",
  "agent_name": "Madeline",
  "role": "meta_agent",
  "model": "claude-sonnet-4-20250514",
  "provider_id": "anthropic-main",
  "agent_impl": "claude",
  "description": "Meta-agent that generates improved agent code based on feedback"
}
EOF

cat > /root/embroidery_business_agent_system/config/agent_profiles/meredith_feedback_agent.json <<'EOF'
{
  "profile_id": "meredith-feedback-v1",
  "agent_name": "Meredith",
  "role": "feedback_agent",
  "model": "claude-sonnet-4-20250514",
  "provider_id": "anthropic-main",
  "agent_impl": "claude",
  "description": "Feedback agent that analyzes agent performance and suggests improvements"
}
EOF

# Task 5: Create provider config
cat > /root/embroidery_business_agent_system/config/providers/anthropic_main.json <<'EOF'
{
  "provider_id": "anthropic-main",
  "name": "Anthropic (Main)",
  "client_kind": "anthropic",
  "base_url": null,
  "api_key_env": "ANTHROPIC_API_KEY"
}
EOF

# Task 6: Initialize OpenClaw workspace
mkdir -p /root/.openclaw/workspace/improvement_runs
chmod 755 /root/.openclaw/workspace/improvement_runs

# Task 7: Create first EMBIZ task (quote generation)
mkdir -p /root/embroidery_business_agent_system/tasks/quote_generation/{data/{public,private},reference}
cat > /root/embroidery_business_agent_system/tasks/quote_generation/data/public/task.md <<'EOF'
# Quote Generation Task

Generate accurate embroidery quotes based on design specifications.

## Input
- Design file (SVG, PNG, or description)
- Garment type
- Quantity
- Turnaround time

## Output
- Quote amount (USD)
- Stitch count estimate
- Production time estimate
- Confidence score

## Evaluation Metrics
- Quote accuracy (within 10% of actual cost)
- Customer acceptance rate
- Processing time (< 2 minutes)
EOF

# Task 8: Create evaluation script
cat > /root/embroidery_business_agent_system/tasks/quote_generation/data/public/evaluate.py <<'EOF'
#!/usr/bin/env python3
import json
import sys
from pathlib import Path

def evaluate(submission_path: Path, ground_truth_path: Path) -> dict:
    with open(submission_path) as f:
        predictions = json.load(f)
    with open(ground_truth_path) as f:
        ground_truth = json.load(f)
    
    correct = 0
    total = len(ground_truth)
    
    for item in ground_truth:
        quote_id = item["id"]
        actual_cost = item["actual_cost"]
        predicted_cost = predictions.get(str(quote_id), {}).get("quote_amount", 0)
        
        # Within 10% is considered correct
        if abs(predicted_cost - actual_cost) / actual_cost <= 0.10:
            correct += 1
    
    return {
        "accuracy": correct / total,
        "n_correct": correct,
        "n_total": total
    }

if __name__ == "__main__":
    result = evaluate(Path(sys.argv[1]), Path(sys.argv[2]))
    print(json.dumps(result, indent=2))
EOF
chmod +x /root/embroidery_business_agent_system/tasks/quote_generation/data/public/evaluate.py
```

### Per-Task Setup (Repeatable)

```bash
# Create new EMBIZ task (e.g., design_assessment)
TASK_NAME="design_assessment"
cd /root/embroidery_business_agent_system/tasks
mkdir -p ${TASK_NAME}/{data/{public,private},reference}

# Copy template files
cp quote_generation/data/public/task.md ${TASK_NAME}/data/public/task.md
cp quote_generation/data/public/evaluate.py ${TASK_NAME}/data/public/evaluate.py

# Edit task.md and evaluate.py for new task
# [Manual step: customize for specific task requirements]
```

## What Not To Use

### SIA Components to IGNORE for EMBIZ

1. **Direct SIA Execution**:
   - Do NOT run `python -m sia` or import `sia.orchestrator` directly
   - Do NOT install `sia-agent` package in EMBIZ environment
   - Reason: SIA is a pattern library, not a runtime dependency

2. **SIA's Bundled Tasks**:
   - Do NOT use GPQA, LawBench, LongCoT-Chess, Spaceship-Titanic tasks
   - Reason: These are academic benchmarks, not embroidery business tasks

3. **SIA's Docker Sandbox**:
   - Do NOT use `--sandbox docker` mode
   - Reason: EMBIZ runs in controlled environment, doesn't need containerization

4. **SIA's Weights Mode** (RL