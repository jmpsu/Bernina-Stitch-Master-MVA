<!--
LOCAL-FIRST FULL AUTONOMOUS-AGENT-OWNED VERSION
Derived from: EMBIZ_Jupiter_Embroidery_Autonomous_Agent_Owned_FULL_VERSION.md
Generated at: 2026-07-07
Transformation goal: reroute ALL agent reasoning, planning, task execution, Slack
handling, and automation onto the PROVEN local machine (Dell Pro Max 16 Premium,
Linux Mint, NVIDIA RTX PRO 2000 Blackwell, qwen3:8b via Ollama at 100% GPU offload)
while preserving EVERY directive, workflow, agent role, QA gate, approval flow,
decision-trace requirement, ledger, and reporting standard of the original
FULL VERSION document. NOTHING from the original document is dropped or undone.
Only WHERE the reasoning runs has changed: local Ollama first, paid model APIs
only as the final, logged, Slack-notified escalation rung.
-->

---

# Ownership Clause (applies to every MUST in this document)

Throughout this document, every occurrence of **MUST** carries the complete
ownership mandate of the original FULL VERSION document, in full and undiminished:

> MUST be completely and fully owned, run, executed, verified, maintained, and
> continuously improved by fixed autonomous agents operating as a continuously
> running system that can reason, execute tasks, and deliver results without
> repeated prompting.

This clause is a notational device only. It does not weaken, shorten, or remove
any directive of the original document; it binds the full mandate to every
requirement below exactly as the original document did on every line.

---

# Global Autonomous Agent Ownership Mandate (Preserved in Full)

Every task, workflow, subsystem, service, requirement, verification step, quality
gate, report, artifact, dashboard function, intake action, vectorization action,
digitization action, production action, infrastructure action, communication
action, learning action, experimentation action, and maintenance action in this
document MUST be completely and fully owned, run, executed, verified, maintained,
and continuously improved by fixed autonomous agents operating as a continuously
running system that can reason, execute tasks, and deliver results without
repeated prompting.

No task in this document may depend on repeated prompting. Any task that requires
a prompt, reminder, manual restart, manual follow-up, or ad hoc human execution
MUST be converted into a continuously running autonomous-agent-owned capability
with observable state, durable logs, explicit retry behavior, verifiable output,
and permanent evidence.

Human involvement is allowed only as an explicit approval gate, exception review
gate, or production-business decision gate. Human gates must never replace
autonomous agent ownership, autonomous execution, autonomous verification,
autonomous retry handling, autonomous reporting, or autonomous continuous
improvement.

Every autonomous agent MUST be fixed, bounded, named, observable, restartable,
testable, monitored, and accountable for a specific responsibility. Every
autonomous agent MUST continuously reason over local project knowledge, execute
assigned work, verify results, preserve evidence, report outcomes, and continue
useful work during idle periods without repeated prompting.

**NEW, GOVERNING ADDITION — LOCAL-FIRST EXECUTION MANDATE:** All autonomous agent
reasoning, planning, task execution, Slack handling, and automation MUST run on
the proven local machine using the local Ollama runtime (qwen3:8b on the Blackwell
GPU) as the PRIMARY engine. Paid model resources (Anthropic API, OpenAI API, or
any metered remote inference) MUST NOT be used unless the local system cannot
complete a required task AND no local fallback exists, and then only through the
explicit, logged, Slack-notified escalation ladder defined in this document.

---

# EMBIZ / JUPITER EMBROIDERY AUTOMATION SYSTEM — LOCAL-FIRST EDITION

## Full Technical System Business Requirements Document

**Document Type**

Full Technical System Business Requirements Document (Local-First Execution
Edition)

**Existing System Roots**

* Original agent system root: `/root/embroidery_business_agent_system`
* Local-first execution root (this repository): `Bernina-Stitch-Master-MVA`
  (deployed on the local machine, e.g. `/home/jmmint/Bernina-Stitch-Master-MVA`)

**Business Domain**

Automated embroidery intake, artwork preparation, digitizing workflow, quality
assurance (QA), Slack-visible fixed autonomous agent collaboration, production
tracking, and autonomous embroidery production — executed locally.

---

# Proven Local Execution Environment (Verification Passed All Checks)

The execution target for every agent in this document is the user's PROVEN local
machine:

| Component | Verified State |
|---|---|
| Machine | Dell Pro Max 16 Premium |
| OS | Linux Mint (Ubuntu noble base), user `jmmint` |
| GPU | NVIDIA RTX PRO 2000 Blackwell Generation Laptop GPU |
| VRAM | 8151 MiB, compute capability 12.0 |
| Driver | nvidia-580.173.02 OPEN kernel module (DKMS, apt-pinned, autoremove-proof — verified stable) |
| RAM | 32 GB |
| LLM Runtime | Ollama at `http://localhost:11434` |
| Primary Model | **qwen3:8b**, confirmed running at **100% GPU offload** (6.2 GB, 4096-token default context) |
| Model Behavior | qwen3:8b is a thinking model — it emits `<think>...</think>` ("Thinking...") blocks; every consumer MUST strip think blocks or use `/no_think` handling before using its output |

## VRAM Budget Awareness (Mandatory Routing Constraint)

* Total VRAM: 8151 MiB. qwen3:8b occupies ~6.2 GB when loaded.
* **Only ONE model may be resident on the GPU at a time.** Parallel model loading
  is PROHIBITED. The model router and every agent MUST serialize LLM calls
  through a single loaded model and MUST NOT trigger simultaneous loads of two
  different Ollama models (an alternate local model swap unloads qwen3:8b first;
  Ollama does this natively, and the router must treat swaps as expensive,
  serialized events).
* Context growth costs VRAM: raising `num_ctx` beyond the 4096 default (rung 2 of
  the escalation ladder) increases KV-cache usage. The router caps `num_ctx` at a
  configured maximum (default 16384) and treats CUDA OOM / partial-offload
  degradation as a rung failure that advances the ladder.
* The deterministic embroidery pipeline (`digitizer.py`, `vectorizer.py`,
  `run_iteration.py`, `metrics.py`) uses CPU/RAM only and never competes for
  VRAM. It may run concurrently with LLM inference.

---

# Local-First Execution Policy and Model Escalation Ladder

The local Ollama runtime (qwen3:8b on the Blackwell GPU) is the PRIMARY engine
for: reasoning, planning, task execution, agent operation, Slack handling, and
automation. Paid model resources MUST NOT be used unless the local system cannot
complete a required task AND no local fallback exists.

## The Escalation Ladder (strict order, no rung may be skipped)

1. **Rung 1 — qwen3:8b on GPU (primary).** Every LLM task starts here. Default
   context 4096, think-blocks stripped from all responses.
2. **Rung 2 — Retry locally with a larger context and/or a different local
   prompt strategy.** Permitted adjustments: raise `num_ctx` (8192, then 16384),
   switch between thinking and `/no_think` modes, decompose the task into
   smaller sub-prompts, re-prompt with retrieved knowledge-library context, and
   lower temperature for structured outputs. All retries remain on the local
   GPU and cost nothing.
3. **Rung 3 — Other locally pulled Ollama models, if present.** The router
   enumerates locally available models via `GET /api/tags` (CLI equivalent:
   `ollama list`) and tries suitable alternates one at a time (never in
   parallel — see VRAM budget). Model swaps are logged as decision-trace events.
4. **Rung 4 — ONLY THEN a paid API.** A paid call is permitted only after rungs
   1–3 have demonstrably failed for the specific task. Every paid call MUST be:
   * appended to the paid-usage audit log `local_agents/state/paid_usage_audit.jsonl`
     (task type, prompt hash, rungs attempted, failure reasons, provider, model,
     token counts when available, timestamp), and
   * announced in the Slack alerts channel BEFORE and AFTER the call (cost
     transparency), and
   * recorded in `decision_trace.jsonl` with the reason no local fallback existed.
   The paid provider and model are configured exclusively via environment
   variables (`EMBIZ_PAID_PROVIDER`, `EMBIZ_PAID_MODEL`, `EMBIZ_PAID_API_KEY`);
   if they are unset, rung 4 is disabled and the task fails locally with a
   Slack error notification instead of silently spending money.

## Per-Task-Type Routing Rules

The routing component (`local_agents/model_router.py`) implements the ladder with
per-task-type rules. Representative task types and their policies:

| Task Type | Rung 1 | Rung 2 | Rung 3 | Rung 4 (paid) |
|---|---|---|---|---|
| `slack_reply` (agent conversation) | qwen3:8b, `/no_think` | retry, ctx 8192 | alternates | never (local answer or apologize) |
| `plan` (job planning, step decomposition) | qwen3:8b, thinking on | retry, ctx 8192→16384, decomposition | alternates | allowed, logged |
| `summarize` (reports, transcripts) | qwen3:8b, `/no_think` | retry, ctx 16384, chunked map-reduce | alternates | never (chunking always works) |
| `qa_review` (interpret QA metrics text) | qwen3:8b | retry with knowledge context | alternates | allowed, logged |
| `classify` (routing, intake triage) | qwen3:8b, `/no_think`, temp 0 | retry, schema-constrained re-prompt | alternates | never |
| `code` (self-improvement proposals) | qwen3:8b, thinking on | retry, ctx 16384 | alternates | allowed, logged |
| `customer_reply` drafting | qwen3:8b | retry with templates from knowledge library | alternates | allowed, logged (human approval gate ALWAYS applies before send) |

**Deterministic pipeline work is NOT an LLM task type.** `digitizer.py`,
`vectorizer.py`, `run_iteration.py`, and `metrics.py` are local deterministic
Python — they need no LLM at all and run natively on the Mint machine. The LLM
only orchestrates (decides what to run, interprets ledgers and metrics, writes
reports). Vectorization and digitization are 100% local compute, always.

---

# System Vision, Objectives, and Permanent Design Requirements (Preserved)

This document defines the complete technical architecture, business requirements,
implementation roadmap, long-term autonomous evolution strategy, and permanent
engineering principles for the EMBIZ / Jupiter Embroidery Automation System,
executed local-first.

The purpose of this project is not to build an isolated collection of AI fixed
autonomous agents or workflow automations, but to continuously refine the
existing production system into a fully autonomous, continuously operating,
continuously self-learning, and continuously self-improving multi-agent
embroidery production platform.

The existing system MUST be expanded and refined — not replaced — into an
AI-driven production environment capable of autonomously converting:

* Customer emails
* Attached artwork
* Rough sketches
* Production specifications
* Business requirements
* Production constraints

into:

* Production-grade vector artwork
* Production-grade embroidery stitch plans
* Verified PES embroidery files

through a structured, observable, measurable, verifiable, and continuously
improving autonomous job pipeline.

The completed EMBIZ platform MUST function as a continuously operating autonomous
embroidery production environment capable of reliably transforming customer
communications, artwork, production requirements, and engineering knowledge into
production-grade embroidery deliverables while continuously improving every
component of its architecture through:

* Autonomous learning
* Experimentation
* Validation
* Historical analysis
* Regression analysis
* Knowledge accumulation
* Repository improvement
* Code review
* Quality improvements
* Documentation improvements
* Autonomous self-improvement activities

The continuously running autonomous system is intended to become a permanent
production platform. It MUST never intentionally stop operating. During idle
periods it MUST continuously perform useful autonomous work rather than remaining
idle (on this machine: `run_iteration.py` experiment sweeps, ledger analysis,
knowledge memorialization, regression comparison — all free local compute).

Every architectural decision, implementation decision, workflow addition,
subsystem, agent, service, and production pipeline MUST move the system toward a
completely autonomous embroidery production platform with:

* Observable reasoning
* Measurable quality improvements
* Continuous learning
* Continuous experimentation
* Continuously improving production output

Every capability MUST be observable, testable, measurable, and continuously
improvable. No capability MUST exist in isolation. Every component MUST integrate
naturally with the remainder of the platform.

---

# Core Autonomous Platform Capabilities (Preserved)

Each capability below is a permanent architectural objective that MUST be
designed, implemented, validated, continuously improved, and maintained
throughout the lifetime of the system. All reasoning components run on qwen3:8b
locally; all compute components run natively on the Mint machine.

* Autonomous multi-agent teams
* Local-library-driven reasoning
* Autonomous retrieval-driven decision making
* Raster-to-vector image conversion (local deterministic: `vectorizer.py`)
* Raster-to-vector image quality assurance (QA) (local deterministic: `metrics.py`)
* Inkscape vectorized SVG generation automation (local headless Inkscape)
* Vectorized SVG quality assurance
* Ink/Stitch embroidery stitch plan generation (local)
* Embroidery stitch plan quality assurance
* PES embroidery file export (local: `digitizer.py`, pyembroidery)
* Embroidery stitch plan simulation
* Embroidery stitch plan density-map quality assurance
* Bernina B700 stitch plan standards compliance
* Bernina B700 production protocol quality assurance
* Production tracking
* Continuous historical learning (ledgers: `decision_trace.jsonl`,
  `observations.jsonl`, `reward_penalty_ledger.jsonl`,
  `vectorization_attempts.jsonl`, `knowledge_experiments.jsonl`)
* Knowledge graph construction
* Slack-visible multi-agent collaboration (Socket Mode daemon, local)
* Autonomous AI agents communicating continuously
* LLM-powered artwork preparation (qwen3:8b local)
* Customer reply automation (qwen3:8b local, human approval gate preserved)
* Git-based continuous integration and continuous deployment (CI/CD)

---

# Foundational Infrastructure and Platform Services (Preserved)

These platform services MUST be considered foundational architectural components
rather than optional features:

* Artifact persistence
* Distributed storage
* Knowledge repositories
* Production history preservation
* Autonomous agent communication infrastructure
* Deployment automation
* Disaster recovery
* Data synchronization
* Long-term archival
* Infrastructure monitoring
* Autonomous operational reporting
* Multi-cloud orchestration (for storage/backup ONLY — never for LLM inference
  unless the rung-4 escalation applies)

---

# Immediate Development Priorities (Preserved)

Development MUST prioritize the foundational infrastructure required for reliable
autonomous production before expanding into advanced embroidery generation
capabilities.

**Critical Near-Term Requirements**

* Automatic attachment extraction
* Real artwork review
* Visible Slack agent conversation (Socket Mode daemon — `slack_daemon.py`)
* Dashboard authentication
* Status transition controls

Once these foundational capabilities are functioning reliably, development MUST
expand toward:

* Ink/Stitch integration
* Automated stitch planning
* Production-grade PES generation

---

# Persisting Design Requirements (Preserved)

The following requirements permanently influence every aspect of the EMBIZ
platform and MUST be considered throughout all future architecture,
implementation, testing, deployment, maintenance, and autonomous evolution. They
apply equally to: system architecture, agent design, agent communication,
autonomous reasoning, knowledge retrieval, development workflow, Git release
process, continuous integration, continuous deployment, dashboard design,
production pipeline, quality assurance, and long-term autonomous evolution.

These requirements MUST be represented throughout every subsystem whenever
technically appropriate. There MUST never be any portion of the final
architecture, implementation, production pipeline, agent design, workflow, or
source code that does not maximize representation of these requirements within
its intended responsibility.

**Persistent Collaboration Requirements**

* Slack MUST receive mirrored messages.
* Fixed autonomous agents read Slack replies automatically (Socket Mode events).
* Slack approvals enabled.
* Slack slash commands implemented.
* Fixed autonomous agents chatting continuously.

**NEW Persistent Local-First Requirements**

* Every agent's reasoning calls route through `model_router.py` — no agent may
  call a paid API directly.
* The Slack system is a continuously running autonomous daemon system (systemd
  user services), NOT a one-off chatbot session. Once set up, it runs
  persistently: reasons, executes tasks, monitors Slack, responds, triggers
  workflows, delivers results, and continues without repeated prompting. It
  survives reboots (`loginctl enable-linger jmmint`).
* Socket Mode is the required transport — no public ingress is needed on a
  laptop.

---

# Repository Consistency Requirement (Preserved)

All future EMBIZ agent skills MUST conform to consistent organization, naming,
metadata, documentation, verification, and cross-reference standards. The
implementing agent MUST verify compliance before considering work complete.

# Verification Standard (Preserved)

The implementing agent MUST provide observable evidence confirming:

* The skill resides under `skills/`
* The primary file is named `SKILL.md`
* Optional directories exist only when justified
* YAML frontmatter is valid
* The `name` field matches the directory name
* The `description` explains both what the skill does and when it MUST be used
* Supporting files use lowercase hyphen-separated names
* Shared references reside under `references/`
* Cross-skill references are used instead of duplicating workflows
* The recommended document structure is present
* Verification includes observable evidence
* Common rationalizations are documented
* Red flags are documented
* The primary `SKILL.md` remains concise

# Final Report Standard (Preserved)

Unless superseded by a more specific project requirement, every implementation
MUST conclude with a final report containing:

* Skill directories created or updated
* Primary `SKILL.md` files created or modified
* YAML frontmatter validation results
* Skill naming convention verification
* Supporting files created
* Justification for every supporting file
* Optional directories created and justification
* Shared references utilized
* Cross-skill references added
* Verification checklist implementation
* Rationalizations table implementation
* Red flags documented
* Repository consistency verification
* Commands executed
* Files created
* Files modified
* Known limitations
* Recommended future improvements
* Next exact command

Project-specific report requirements MUST be autonomously extended when validated
but MUST NOT redefine this list.

---

# Project Requirement — Agent Skill Standards and SKILL.md Specification (Preserved)

**Priority:** Critical

**Objective:** Establish a single production-ready standard governing the
organization, naming, structure, documentation, metadata, verification, and
cross-referencing of every agent skill within the EMBIZ project. Every new skill
created for EMBIZ pipeline agents MUST conform to this specification unless a
more restrictive project standard explicitly supersedes it.

## Skill Directory Structure

Every skill MUST reside within the project's `skills/` directory:

```text
skills/
  autonomous-agent-skill-name/
    SKILL.md
    scripts/                 optional
    supporting-file.md       optional
```

## Required Files

Every skill directory MUST contain exactly one primary entry point named
`SKILL.md`. Rules: `SKILL.md` is the only required file; the filename MUST always
be uppercase; no alternative filename is permitted.

## Optional Files

Optional content MUST only exist when it improves readability, maintainability,
or workflow execution. `scripts/` MUST exist only when runnable helper scripts
are required. Markdown-only skills MUST NOT contain an empty `scripts/`
directory. Supporting markdown files MUST only be created when they reduce
complexity or keep `SKILL.md` concise, and MUST reduce complexity rather than
increase it.

## Naming Conventions

Skill directory names MUST use lowercase letters, hyphen-separated words, remain
descriptive, and remain consistent throughout the repository. Examples:
`cloudflare-flue-orchestrator`, `potrace-parameter-sweep`, `svg-topology-qa`,
`embroidery-vector-generation`, and (new, local-first) `local-model-routing`,
`ollama-context-strategy`.

## Supporting Files

Supporting documentation MUST use lowercase hyphen-separated filenames, exist
only when justified, improve readability and maintainability, and avoid
unnecessary complexity. Appropriate supporting files include lengthy reference
material, large checklists, implementation examples, reusable templates,
parameter references, and runnable helper documentation. The primary `SKILL.md`
MUST remain the concise authoritative entry point.

## Recommended SKILL.md Structure

Every skill MUST contain: Skill Title; Overview (what, why it exists, why it
matters); When to Use (triggering conditions, activation criteria, exclusions,
when NOT to use); Required Inputs; Core Workflow (ordered phases with decision
points, code/configuration/command examples, ASCII flow diagrams as applicable);
Specific Techniques (reusable patterns, templates, configuration guidance,
specialized recommendations); Verification Workflow (automated verification,
autonomous verification with explicit human inspection only when required,
observable evidence, expected outputs); Common Rationalizations (a table of
excuses agents use to skip required work — each entry MUST include the
rationalization, why it is incorrect, and the required corrective action); Red
Flags (skipped verification, undocumented assumptions, missing evidence,
incomplete testing, undocumented implementation decisions, unsupported
completion claims); Verification (completion checklist, observable evidence,
command output, generated artifacts, modified files, repository diffs,
validation reports, decision traces, screenshots where applicable).

## Required Skill Content

Every production skill MUST contain, at minimum: Purpose; When to Use; Required
Inputs; Repository Inspection Workflow; Architecture Inspection Workflow; Agent
Responsibility Separation Rules; Implementation Workflow; Verification Workflow;
Evidence Requirements; Common Rationalizations; Red Flags; Final Report Format.

---

# Agent Responsibility Separation (Preserved)

Each agent MUST own one clearly bounded responsibility. Representative
responsibilities include:

* Knowledge Retrieval
* Raster Preprocessing
* Potrace Parameter Sweep
* SVG Optimization
* SVG Topology QA
* Candidate Leaderboard
* Methodology Memorialization
* Embroidery Vector Generation
* Stitch Plan Generation
* Production Output
* Slack Conversation
* Workflow Orchestration
* **Model Routing (new, local-first):** owns the escalation ladder and the
  paid-usage audit log; no other agent may bypass it.

Except for the Orchestrator, no individual agent MUST attempt to own the complete
embroidery production pipeline.

---

# Operational Protocol — Integrated Heavily-Iterated Vectorization Engine (I-HIVE) (Preserved)

**Document Class:** System Architecture & Agent Operational Specification

**Core Objective:** Absolute elimination of non-autonomous GUI-tracing quality
advantages through massive, multi-iteration algorithmic exploration using
headless automation infrastructure as the deterministic execution engine.

**LOCAL-FIRST NOTE:** I-HIVE is 100% local deterministic compute. Candidate
generation (`vectorizer.py`), measurement (`metrics.py`), iteration
(`run_iteration.py`), and stitch generation (`digitizer.py`) require NO LLM.
qwen3:8b only orchestrates: choosing sweep budgets, interpreting leaderboards,
and writing reports.

## System Overview

In high-precision vector asset generation for industrial textile applications,
the primary advantage of an intelligent technical agent is not simply speed — it
is the capacity for exhaustive, hyper-iterative experimentation. While a human
designer using the Inkscape graphical interface relies on intuitive, singular,
and comparatively slow manual tracing, I-HIVE performs thousands of programmatic
structural variations for a single source image. Each iteration MUST be
autonomously permitted to modify: node structures, path simplification, rail
directions, point allocation, and geometric topology. Each variation becomes a
candidate for automated evaluation before downstream embroidery generation.

I-HIVE MUST function as a deterministic, continuously improving vectorization
framework. Rather than producing a single vector output, the system MUST
generate, evaluate, compare, rank, and continuously refine large populations of
candidate vectors until convergence criteria are satisfied. Every candidate MUST
remain observable, measurable, reproducible, and traceable.

## Phase 1 — Vector Base Convergence

The initial customer artwork MUST enter the I-HIVE processing pipeline
immediately following artwork intake. The engine MUST generate thousands of
structural vector variations while systematically optimizing: corner tolerances,
node placement, path topology, curve fitting, profile line accuracy, and
structural continuity. The objective is to converge toward a vector
representation that most accurately reproduces the source artwork while
simultaneously optimizing downstream embroidery suitability.

## Phase 2 — Structural Verification

Following convergence, every candidate vector MUST undergo automated structural
verification including, where applicable: size verification, coordinate
validation, line weight consistency, path continuity, closed-path verification,
node topology inspection, geometry validation, and scaling validation. Only
candidates satisfying structural verification requirements MUST advance to
subsequent processing stages.

## Phase 3 — Headless Production Output

Approved vectors MUST proceed through fully automated headless processing.
Graphical user interfaces MUST NOT be required during production execution.
Representative workflow:

```bash
inkscape --actions="export-filename:sailboat_2_5.dst; export-do; export-filename:sailboat_6_0.dst" sailboat.svg
```

The production system MUST generate required production assets while preserving
artwork proportions, geometric precision, production dimensions, and structural
integrity. The objective is deterministic conversion from customer artwork into
production-ready embroidery assets.

## I-HIVE Design Principles

The architecture MUST emphasize: massive candidate generation, automated
experimentation, continuous convergence, deterministic evaluation, historical
learning, statistical comparison, continuous optimization, reproducibility, and
observable decision making.

## Candidate Evaluation Philosophy

Each generated candidate represents a measurable experiment rather than a final
result. Candidates MUST be evaluated using objective quality metrics rather than
subjective selection. Representative evaluation criteria: source similarity,
silhouette preservation, topology quality, node efficiency, embroidery
suitability, structural simplicity, production robustness, downstream stitch
quality. Candidate evaluation MUST remain continuously extensible as new quality
metrics are developed.

## Continuous Learning

Successful candidates MUST become permanent learning assets. **EVERY PROCESS RUN
MUST continuously improve future parameter selection, convergence strategies,
topology optimization, and production quality.** The system MUST preserve:
historical experiments, successful parameter combinations, failed parameter
combinations, quality metrics, regression history, performance trends, decision
traces, and production observations. **Historical learning MUST directly
influence future autonomous execution.** (In this repository this is realized by
`decision_trace.jsonl`, `observations.jsonl`, `reward_penalty_ledger.jsonl`,
`vectorization_attempts.jsonl`, `knowledge_experiments.jsonl`,
`parameter_correlation_index*.json`, and `weights.json` — all local.)

## Autonomous Experimentation

During idle execution periods the system MUST continuously perform productive
experimentation: parameter exploration, candidate generation, metric refinement,
regression testing, historical comparison, knowledge accumulation, methodology
refinement, and pipeline optimization. **Autonomous experimentation MUST
continuously improve future production quality without interrupting normal
production workflows.** On this machine, idle experimentation is free CPU work
(`run_iteration.py`) and MUST be the default idle activity of the agent loop.

## Observable Evidence Requirements

Every significant processing stage MUST produce observable evidence:
commands executed, parameters selected, candidate counts, evaluation metrics,
quality scores, generated artifacts, comparison reports, decision traces,
production outputs, verification results. No stage MUST be considered complete
without observable evidence supporting its outcome.

## Architectural Goals

I-HIVE MUST continuously evolve toward: higher vector quality, greater production
reliability, lower human-gated intervention (only when required), increased
automation, greater historical intelligence, faster convergence, better
embroidery suitability, improved downstream stitch generation, and continuous
autonomous improvement — while preserving deterministic, observable, and
reproducible execution.

## Transition to Downstream Pipeline

Once candidate convergence and structural verification have completed
successfully, approved vector assets MUST become canonical production inputs for
downstream processing including: SVG optimization, embroidery vector
preparation, stitch assignment, Ink/Stitch processing, stitch simulation,
density analysis, quality assurance, PES generation, and production validation.
Only verified production candidates MUST advance into the embroidery generation
pipeline.

---

# AWS Infrastructure Integration Requirements (Preserved — Storage/Backup Only)

## Purpose

An existing AWS infrastructure is already present and operational. The existing
implementation is capable of storing system backups, and preserving this
capability is a mandatory requirement. The autonomous agent team MUST treat the
existing AWS infrastructure as a production asset and continuously determine how
it can be expanded throughout the EMBIZ architecture.

**The objective is not merely to preserve AWS compatibility, but to continuously
leverage AWS services, S3-compatible storage, cloud infrastructure, automation,
backup, synchronization, messaging, artifact storage, distributed workflow
capabilities, and future cloud integrations wherever they provide measurable
value.**

**LOCAL-FIRST CLARIFICATION:** AWS/S3/R2/Contabo integration is for STORAGE,
BACKUP, SYNC, and NOTIFICATION infrastructure only. It never hosts LLM
inference. Inference stays on the local GPU per the escalation ladder.

## Primary Integration Objectives

The agent team MUST investigate, design, implement, validate, and continuously
improve AWS integration, leveraging the existing installation whenever validated
as practical rather than replacing or bypassing it. Potential areas: backup
infrastructure, artifact storage, knowledge library storage, production archive
storage, job artifact synchronization, multi-server synchronization, cloud
object storage, Cloudflare R2 integration, Contabo object storage, distributed
production assets, Slack notification pipelines, autonomous infrastructure
monitoring, disaster recovery, versioned historical archives. AWS MUST become a
first-class infrastructure component wherever technically appropriate.

## Existing AWS Infrastructure Discovery

Before implementing modifications, agents MUST completely inventory the existing
AWS installation: installed binaries, runtime configuration, credentials,
environment variables, runtime processes, package installations, shell
integration, system services, filesystem layout. Execute the discovery workflow
before making architectural decisions:

```bash
echo -e "\n=== 1. BINARY & SYMLINK DISCOVERY ==="
which aws 2>/dev/null && aws --version
whereis aws
find /usr/local/bin /usr/bin /bin /usr/local/aws-cli /opt -name "aws" -type l -o -type f 2>/dev/null

echo -e "\n=== 2. ENVIRONMENT VARIABLE INTERROGATION ==="
env | grep -E -i "aws_|amazon|secret|token"

echo -e "\n=== 3. RUNTIME & GLOBAL CONFIGURATION PATHS ==="
ls -la ~/.aws/ 2>/dev/null
cat ~/.aws/config 2>/dev/null | sed 's/aws_access_key_id.*/aws_access_key_id = [MASKED]/g'
cat ~/.aws/credentials 2>/dev/null | sed 's/aws_secret_access_key.*/aws_secret_access_key = [MASKED]/g'

echo -e "\n=== 4. PACKAGE MANAGER AUDIT ==="
echo "--- APT ---" && dpkg -l | grep -i aws
echo "--- Snap ---" && snap list 2>/dev/null | grep -i aws
echo "--- Pip ---" && pip3 list 2>/dev/null | grep -i aws

echo -e "\n=== 5. SHELL PROFILE AUDIT ==="
grep -H "aws" ~/.bashrc ~/.zshrc ~/.profile ~/.bash_profile /etc/environment 2>/dev/null

echo -e "\n=== 6. RUNTIME PROCESSES & SYSTEMD HOOKS ==="
ps aux | grep -i aws | grep -v grep
systemctl list-units --type=service | grep -i aws
```

## AWS Filesystem Architecture, Core Configuration, Resolution Order (Preserved)

AWS CLI installations maintain state under `/usr/local/aws-cli/v2/current/`,
`/usr/local/bin/aws`, `~/.aws/config`, `~/.aws/credentials`, `~/.local/bin/aws`.
`~/.aws/config` contains regions, output formats, profiles, endpoint
configuration (`[profile dev]` / `[default]`). `~/.aws/credentials` contains
credential information per profile. Configuration MUST resolve in precedence
order: command-line arguments → environment variables → `~/.aws/credentials` →
`~/.aws/config`. The agent team MUST preserve this deterministic resolution
behavior.

## Multi-Cloud Architecture (Preserved)

The AWS CLI MUST be treated as a generalized cloud interface. The platform MUST
support multiple S3-compatible providers simultaneously: AWS S3, Contabo Object
Storage, Cloudflare R2, additional S3-compatible providers.

Contabo reference:

```ini
[profile contabo]
region = eu-central-1
output = json
endpoint_url = ${DISCOVERED_CONTABO_OBJECT_STORAGE_ENDPOINT_URL}
```

Verification: `aws s3 ls --profile contabo`

Cloudflare R2 reference (S3-compatible API; the AWS CLI MUST become a primary
operational interface for artifact synchronization, backup, production assets,
deployment assets, distributed storage):

```ini
[cloudflare]
aws_access_key_id = ${CLOUDFLARE_R2_ACCESS_KEY_ID}
aws_secret_access_key = ${CLOUDFLARE_R2_SECRET_ACCESS_KEY}

[profile cloudflare]
region = auto
output = json
```

```bash
aws s3 sync /var/www/html/ \
s3://${DISCOVERED_R2_BUCKET}/ \
--endpoint-url https://${DISCOVERED_CLOUDFLARE_ACCOUNT_ID}.r2.cloudflarestorage.com \
--profile cloudflare
```

## Infrastructure Notification Pipeline (Preserved)

Infrastructure events MUST automatically generate Slack-visible operational
notifications including: successful synchronization, backup completion,
authentication failures, connectivity failures, infrastructure outages, recovery
events, scheduled maintenance, autonomous health checks. (The representative
webhook script of the original document remains valid; on the local machine
these notifications route through the Slack daemon's error/ops notification
handlers so that all Slack traffic is transcript-logged.)

## Long-Term AWS Design Goals (Preserved)

The AWS subsystem MUST evolve beyond backup storage into a foundational cloud
services layer supporting: artifact persistence, distributed storage, knowledge
repositories, production history, agent communication, deployment automation,
disaster recovery, synchronization, long-term archival, infrastructure
monitoring, autonomous reporting, multi-cloud orchestration. **Every future AWS
integration MUST preserve compatibility with the existing installation while
expanding its usefulness throughout the EMBIZ production platform.**

---

# Reference Architecture — Agent Coordination, Communication, APIs, Observability, and Knowledge Graph (Preserved)

The following architecture serves as a reference implementation that MUST be
autonomously evaluated and, when validated, adopted, refined, generalized, or
replaced where doing so improves maintainability, scalability, observability,
autonomy, production reliability, or engineering quality. The intent is to
preserve the architectural principles while allowing implementation flexibility.

## Agent Lifecycle

Autonomous agents MUST execute through a deterministic lifecycle with observable
state transitions:

```text
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│  READY  │───►│ASSIGNED │───►│ RUNNING │───►│AWAITING │───►│COMPLETE │
│         │    │         │    │         │    │APPROVAL │    │         │
└─────────┘    └─────────┘    └────┬────┘    └────┬────┘    └─────────┘
     ▲                             │              │
     └─────────────────────────────┘              │
     │         retry on failure                   │
     └────────────────────────────────────────────┘
                  approval granted
```

The implementation is not required to match this exact state model but MUST
provide equivalent observability, deterministic execution, retry handling,
approval workflows, and completion states. (`agent_loop.py` implements exactly
this lifecycle over the filesystem job queue: `pending → active →
awaiting_approval → done/failed`.)

## Agent Communication Architecture

Agents MUST communicate using standardized asynchronous messaging with:
asynchronous message passing, inbox-based communication, broadcast capability,
message history, observable logs, traceable conversations. Representative
command interface (alternative implementations acceptable provided equivalent
functionality exists):

```bash
agent-msg send ${FROM_AGENT} ${TO_AGENT} "message"
agent-msg inbox ${AGENT}
agent-msg broadcast ${FROM_AGENT} "status"
agent-msg tail
```

Locally this is realized by the filesystem queue (`local_agents/state/queue/`),
the Slack channels (observable broadcast), and the transcript log
(`local_agents/state/slack_transcript.jsonl`).

## Slack Collaboration (Preserved, Now Daemonized Locally)

Slack MUST remain a primary operational interface for EMBIZ. Slack integration
MUST support: agent collaboration, production visibility, quality assurance,
autonomous approval workflows with explicit human gates only when required,
operational alerts, autonomous reporting. Representative channels:

* `#embiz-jobs`
* `#embiz-artwork`
* `#embiz-qa`
* `#embiz-alerts`

**Future implementations MUST reorganize channels only when validated while
preserving equivalent capabilities.** See the dedicated "Autonomous Slack Agent
System" section below for the full, mandatory responsibility list and the local
daemon specification.

## Internal Webhook API (Preserved)

The internal API MUST expose stable interfaces for communication between
platform components. Equivalent or improved implementations are acceptable.

## Email Intake Webhook (Preserved)

`POST /cloudflare-email` with headers `Content-Type: application/json`,
`X-Embiz-Secret: ${EMBIZ_WEBHOOK_SECRET}`; request body
`{"from","to","subject","text","receivedAt"}`; response `200 OK` returning a Job
ID; representative errors `403 Forbidden`, `500 Internal Server Error`.

## Job API (Preserved)

`GET /api/jobs` returns entries of the form:

```json
[
  {
    "id":"JOB-CF-20260614-213321",
    "from":"joe.metz.psu@gmail.com",
    "to":"info@jupiterembroideryco.com",
    "subject":"test customer order v2",
    "received":"2026-06-14T21:33:21.550083"
  }
]
```

## Job Creation (Preserved)

`cloudflare_email_to_job.py`: JSON via stdin → Job ID via stdout; errors to
`logs/webhook_error.log`. Generated artifacts: `intake_summary.md`, `job.json`,
`raw_email.json`, `missing_questions.md`. Job ID format:

```text
JOB-CF-YYYYMMDD-HHMMSS
│   │  │           │
│   │  │           └── UTC Time
│   │  └────────────── Date
│   └───────────────── Source
└──────────────────── Prefix
```

## Cloudflare Tunnel (Preserved, With Local Note)

Representative deployment: tunnel name `embiz`, daemon `cloudflared`, protocol
QUIC (HTTP/3), authentication via Origin Certificate + Tunnel Credentials,
ingress `embiz-hook.jupiterembroideryco.com → http://127.0.0.1:8787`. Equivalent
implementations are acceptable. **Local note:** the Slack daemon itself needs NO
tunnel and NO ingress (Socket Mode is outbound-only); the tunnel remains
relevant solely for the email-intake webhook when that subsystem runs on the
laptop.

## Agent Directory Architecture (Preserved)

```text
agents/
├── orchestrator/
│   ├── instructions.md
│   ├── status.json
│   ├── in/
│   ├── out/
│   └── logs/
├── artwork_prep/
├── digitizer/
├── customer_reply/
├── requirements/
├── qa/
├── business_ops/
├── gmail_intake/
├── inkstitch_knowledge/
└── security_audit/
```

The architecture MUST be autonomously evaluated and, when validated, evolve
provided responsibilities remain clearly separated.

## Health, Observability, and Debugging (Preserved)

Operational visibility MUST be treated as a core capability. Every subsystem
MUST expose sufficient logging, diagnostics, metrics, health reporting,
debugging information, decision traces, and historical execution records to
support complete operational observability.

Representative log files: `logs/webhook_access.log`, `logs/webhook_error.log`,
`logs/wrangler_*.log`, `logs/cf_create_tunnel.raw.json`,
`logs/cf_create_dns_*.raw.json`. Equivalent observability is acceptable even if
storage locations evolve. New local logs: `local_agents/state/*.jsonl`,
`journalctl --user -u embiz-slack-daemon -f`,
`journalctl --user -u embiz-agent-loop -f`.

Representative health verification: webhook service, tunnel service, health
endpoint, dashboard endpoint, customer form endpoint, job API, worker logs,
tunnel status — plus (new) Ollama runtime health (`GET /api/tags`), GPU health
(`nvidia-smi`), and daemon heartbeats.

## Knowledge Graph Architecture (Preserved)

A graph-based knowledge model is recommended for representing long-term
operational knowledge. **Future implementations MUST preserve, extend, or
redesign the schema while maintaining equivalent or greater capability.**

Representative node types: `(:Customer)`, `(:Job)`, `(:Garment)`, `(:Artwork)`,
`(:StitchFile)`, `(:Agent)`, `(:Question)`, `(:SlackMessage)`.

Representative relationships:

```cypher
(:Customer)-[:SUBMITTED]->(:Job)
(:Job)-[:HAS_ARTWORK]->(:Artwork)
(:Artwork)-[:DIGITIZED_TO]->(:StitchFile)
(:Job)-[:ASSIGNED_TO]->(:Agent)
(:Agent)-[:POSTED]->(:SlackMessage)
```

Representative visualization query:

```cypher
MATCH (c:Customer)-[:SUBMITTED]->(j:Job)-[:ASSIGNED_TO]->(a:Agent)
OPTIONAL MATCH (j)-[:HAS_ARTWORK]->(art:Artwork)
OPTIONAL MATCH (art)-[:DIGITIZED_TO]->(s:StitchFile)
OPTIONAL MATCH (j)-[:REQUIRES]->(q:Question)
RETURN c,j,a,art,s,q
```

---

# Design Objective — Knowledge Library and Model Independence (Preserved and Strengthened)

**The primary MODULATE KNOWLEDGE LIBRARY MUST BE READ IN ITS ENTIRETY BEFORE
ATTEMPTING TO ACCESS ANY LLM IN ANY WAY, SHAPE, OR FORM.** The knowledge of the
EMBIZ platform MUST reside locally within the repository rather than inside
prompts or assumptions about the capabilities of any particular AI model.

All evaluation and analysis of workflows, engineering knowledge, reference
material, historical learning, implementation standards, and production
methodology MUST remain under agent governance and durable regardless of which
model executes the work. This directive is the philosophical foundation of the
local-first policy: because knowledge lives in the repo, an 8B local model
operating over retrieved local knowledge is the correct default reasoning
engine, and paid frontier models add value only in the rare rung-4 cases.

The architecture MUST prioritize:

* Local-first operation
* Vendor independence
* Model independence
* Agent-readable and human-readable documentation
* Machine-readable structure
* Version-controlled knowledge
* Retrieval-driven engineering
* Deterministic workflows
* Continuous learning
* Continuous improvement
* Long-term maintainability

The KNOWLEDGE library MUST emphasize: local documentation over remote prompting
(NEVER use remote prompting for knowledge — keep reading and looking through
every folder for the necessary answer until it is found; never attempt external
search for knowledge); structured engineering knowledge over conversational
instructions; reusable reference material over provider-specific prompt
engineering; retrieval of engineering guidance before implementation; separation
of permanent knowledge from temporary execution context; version-controlled
evolution of engineering knowledge; continuous expansion through validated
experiments; preservation of historical learning; agent-readable, human-readable
and machine-readable formats; modular organization supporting autonomous
retrieval.

## Agent Skills Repository (Preserved)

```text
agent-skills/
├── skills/
├── engineering/
│   ├── requirements-analysis/
│   ├── planning/
│   ├── architecture-design/
│   ├── implementation/
│   ├── source-driven-development/
│   ├── retrieval-driven-development/
│   ├── context-engineering/
│   ├── debugging/
│   ├── testing/
│   ├── verification/
│   ├── code-review/
│   ├── refactoring/
│   ├── simplification/
│   ├── security/
│   ├── performance/
│   ├── observability/
│   ├── deployment/
│   ├── automation/
│   ├── documentation/
│   ├── continuous-learning/
│   └── continuous-improvement/
├── embroidery/
│   ├── artwork-analysis/
│   ├── raster-analysis/
│   ├── vectorization/
│   ├── svg-cleanup/
│   ├── path-topology/
│   ├── stitch-planning/
│   ├── inkstitch/
│   ├── density-analysis/
│   ├── pull-compensation/
│   ├── underlay/
│   ├── satin-columns/
│   ├── fills/
│   ├── lettering/
│   ├── machine-limitations/
│   ├── bernina-b700/
│   ├── pes-validation/
│   └── quality-assurance/
├── business/
│   ├── customer-intake/
│   ├── estimating/
│   ├── quoting/
│   ├── production/
│   ├── scheduling/
│   ├── crm/
│   ├── fulfillment/
│   └── reporting/
├── references/
│   ├── standards/
│   ├── checklists/
│   ├── best-practices/
│   ├── architecture-patterns/
│   ├── troubleshooting/
│   ├── examples/
│   └── anti-patterns/
├── experiments/
│   ├── successful/
│   ├── unsuccessful/
│   ├── metrics/
│   ├── observations/
│   └── regression-history/
├── knowledge/
│   ├── manuals/
│   ├── research/
│   ├── extracted-text/
│   ├── diagrams/
│   ├── screenshots/
│   ├── image-analysis/
│   ├── indexed/
│   └── embeddings/
├── templates/
│   ├── plans/
│   ├── reports/
│   ├── reviews/
│   ├── specifications/
│   ├── qa/
│   └── architecture/
├── workflows/
│   ├── production/
│   ├── learning/
│   ├── review/
│   ├── experimentation/
│   ├── deployment/
│   └── recovery/
└── docs/
    ├── architecture/
    ├── onboarding/
    ├── conventions/
    └── system-overview/
```

## Immediate Requirement — Obsidian Knowledge Library (Preserved)

SCAN EVERY FOLDER AND FILE FOR KNOWLEDGE DERIVED FROM HTML WEB RESOURCES AND PDF
USER GUIDES AND LIBRARIES. CREATE AN OBSIDIAN KNOWLEDGE LIBRARY THAT CAN BE
PERFECTLY AND OPTIMALLY WOVEN INTO THE FINEST LEVEL OF DECISION MAKING MADE AT
EVERY SINGLE MOMENT DURING THE PRODUCTION RUN AND BY ALL AGENTS. BEFORE ANY
THOUGHT IS EVEN THOUGHT, THE ENTIRE LIBRARY MUST BE READ AND USED TO DERIVE
APPLICABLE AND RELEVANT KNOWLEDGE RELEVANT TO THE DECISION AT HAND.

The agent KNOWLEDGE library MUST evolve into a comprehensive engineering
knowledge system where agents retrieve nearly all procedural knowledge from
local resources before generating solutions. The AI model (qwen3:8b locally)
MUST function primarily as a reasoning engine operating over a durable,
continuously expanding, project-specific engineering knowledge base rather than
serving as the primary source of engineering methodology. The platform is THE
ONLY RELIABLE WAY AGENTS accumulate engineering expertise, through:
documentation, validated workflows, historical experiments, reference material,
production observations, regression testing, decision traces, quality metrics,
engineering standards, knowledge repositories.

---

# Project Requirement — I-HIVE Target Engine, Infrastructure, and Production Readiness (Preserved)

**Priority:** Critical

**Objective:** Develop the I-HIVE Target Engine into a production-grade
autonomous vectorization and embroidery digitizing architecture capable of
transforming imperfect customer raster artwork into optimized, embroidery-ready
stitch plans through continuous experimentation, quality analysis, autonomous
refinement, and historical learning. The objective is not simply to generate
embroidery files; it is to build a continuously improving engineering platform
capable of discovering, validating, documenting, and memorializing the best
methods for every stage of the embroidery pipeline.

## I-HIVE Target Engine Purpose

The I-HIVE Target Engine MUST serve as the primary research, experimentation,
optimization, and production pipeline responsible for transforming customer
artwork into production-ready embroidery, optimizing each stage independently
before integrating the complete production pipeline. Pipeline stages: Customer
Artwork → Artwork Review → Background Removal → Raster Cleanup → Path Extraction
→ Optimized SVG → Embroidery-Ready Vector → Digitized Stitch Plan → Quality
Assurance → Production Output.

## I-HIVE Target Capabilities (Preserved, all local compute)

The completed I-HIVE engine MUST support: locked background tracing layer,
automatic raster cleanup, background removal, transparency generation,
multi-stage preprocessing, path extraction, multi-variant vector generation,
Bayesian path-quality scoring, geometric deviation minimization, Potrace
experimentation, Inkscape experimentation, SVG structural cleanup, SVG topology
optimization, satin column planning, rail direction validation, underlay
planning, trim command insertion, color block optimization, dual-size export,
stitch simulation, density-map generation, density-map QA, automated production
QA approval, continuous historical learning. Every I-HIVE capability MUST be
independently measurable and continuously improvable.

## Immediate Requirement (Preserved)

AUTONOMOUS AGENTS MUST OWN, RUN, IMPLEMENT, VERIFY, AND CONTINUOUSLY OPERATE THE
FULLY AUTONOMOUS CORE ITERATIVE VECTORIZATION ENGINE, including project
manifests, engineering protocols, repository structure, and initial pipeline
scaffolding.

## Required Tooling (Preserved, plus local-model additions)

The autonomous dependency-verification agents MUST verify the software below
during startup; missing software MUST trigger autonomous installation attempts
where safe and actionable diagnostics where installation cannot be completed
automatically.

* Core system: python3, git, curl, systemctl, node, npm
* Image processing: inkscape, imagemagick, potrace
* Python libraries: python3-pil, python3-bs4, python3-lxml
* Utilities: zip, unzip, file
* Cloudflare: cloudflared, wrangler
* **Local-first additions:** ollama (runtime up at `localhost:11434`), qwen3:8b
  pulled, nvidia-smi reporting the RTX PRO 2000, `slack_sdk` and `requests` in
  the Python environment

Every dependency MUST be verified during pipeline startup. Missing dependencies
MUST generate actionable diagnostics.

## Knowledge Library Requirements (Preserved)

The engineering library MUST become an active decision-making system. Current
state: repository knowledge exists; most knowledge remains static. Target state:
stage-level source enforcement, mandatory retrieval before implementation,
knowledge citation for engineering decisions, continuous library expansion,
automatic memorialization of validated improvements. Every engineering decision
MUST identify: sources consulted, knowledge extracted, implementation
influenced, validation evidence.

## Vectorization Experiment Pipeline (Preserved)

Create and maintain a sandboxed experimentation environment:

```text
pipeline/vectorization_experiments/
├── input/
├── variants/
├── metrics/
├── selected/
└── report.md
```

Purpose: safely evaluate competing vectorization strategies, preserve
experimental outputs, compare metrics, select best-performing variants, prevent
production artifacts from being overwritten.

## Job Status Management (Preserved — full state machine)

Create `POST /api/job-status`. Allowed state transitions:

* artwork_review → artwork_approved
* artwork_approved → digitizing_plan
* digitizing_plan → digitizing_in_progress
* digitizing_in_progress → stitch_file_ready
* stitch_file_ready → qa_review
* qa_review → qa_passed
* qa_passed → customer_approval_needed
* customer_approval_needed → approved_for_production
* approved_for_production → with_sarah_for_embroidery
* with_sarah_for_embroidery → embroidering_on_bernina
* embroidering_on_bernina → embroidered_complete
* embroidered_complete → ready_for_pickup_or_shipping
* ready_for_pickup_or_shipping → sent_to_customer
* sent_to_customer → project_complete

Invalid state transitions MUST be rejected. Every transition MUST be recorded in
the project audit history (and posted as a Slack job status update by the
daemon).

## Ink/Stitch Validation (Preserved)

Before production artwork is processed: confirm Inkscape extension path, install
Ink/Stitch, verify extension registration, generate a simple SVG, export a test
embroidery file, confirm the output file exists, validate successful export.
The initial validation MUST never use customer artwork. Only simple test artwork
MUST be used until export has been verified.

## Engineering Risks (Preserved, plus local-model risks)

**Large Heredoc Command Risk.** Observed: large heredoc commands have repeatedly
become corrupted during transmission. Mitigation: break large implementations
into smaller scripts; use Git or SCP for large files; run
`python -m py_compile` before restarting services; execute preflight validation
commands; create automatic backups before modifying production files.

**Static Knowledge Library Risk.** Current: knowledge exists but is not actively
consumed. Target: stage-level knowledge retrieval, mandatory source enforcement,
automatic retrieval before implementation, continuous knowledge integration.

**Slack Notification-Only Risk.** Current: Slack only receives outbound
messages. Target: Slack becomes a secure operational control interface capable
of issuing commands, approving work, rejecting work, updating status, and
triggering workflows. (Fully addressed by `slack_daemon.py` — Socket Mode makes
Slack bidirectional.)

**NEW — Thinking-Block Contamination Risk.** qwen3:8b emits `<think>...</think>`
blocks. If not stripped, they contaminate Slack messages, JSON parsing, and
reports. Mitigation: ALL responses pass through `qwen_client.strip_think()`;
structured-output tasks use `/no_think`.

**NEW — VRAM Exhaustion Risk.** 8 GB VRAM with a 6.2 GB model leaves little
headroom. Mitigation: single-model-at-a-time policy, capped `num_ctx`, OOM
treated as ladder-rung failure, no parallel LLM calls.

**NEW — Silent Paid Spend Risk.** Mitigation: rung 4 disabled unless env-
configured; every paid call pre-announced and post-announced in Slack and
appended to the paid-usage audit log.

## I-HIVE Verification Requirements (Preserved)

The implementing agent MUST provide evidence confirming: raster-to-SVG vector
image file architecture exists and is documented; required tooling is installed
and verified; vectorization experiment pipeline exists; sandbox isolation
functions correctly; knowledge retrieval is enforced; stage-level source
enforcement exists; Slack agent conversations function; Slack transcript is
written locally; signed Slack command support is implemented or scaffolded; job
status API validates state transitions; Ink/Stitch export validation succeeds;
continuous learning mechanisms are documented; every implementation includes
observable evidence that can be sent as a human-language Slack message.

## I-HIVE Final Report Requirements (Preserved)

At completion the implementing agent MUST report: I-HIVE implementation status,
tool verification results, pipeline capabilities completed, experimental
framework status, knowledge retrieval implementation, Slack integration status,
job status API implementation, Ink/Stitch validation results, engineering risks
addressed, commands executed, files created, files modified, known limitations,
recommended future enhancements, next exact command.

---

# Project Requirement — Customer Artwork Intake and Intelligent Analysis (Preserved)

**Priority:** Critical

**Objective:** Create a fully autonomous intake and artwork analysis system
capable of transforming incoming customer communications into structured
production jobs requiring no repeated prompting and no human intervention except
explicitly gated human approval events. The intake system MUST become the
canonical entry point for every production workflow. Every customer interaction
MUST be converted into structured engineering information before downstream
processing begins.

## Intake Sources

The intake pipeline MUST support: email, web forms, file uploads, customer
artwork, customer sketches, existing embroidery files, production notes,
business requirements. Future intake sources MUST be extensible without
redesigning the pipeline.

## Intake Processing Pipeline

Every incoming request MUST pass through a deterministic preprocessing pipeline:
attachment extraction, file validation, metadata extraction, customer
identification, artwork identification, production requirement extraction,
missing information detection, job creation, artifact generation, knowledge
retrieval, pipeline routing. Every stage MUST produce observable evidence.
(Intake classification/triage is an LLM `classify` task routed to qwen3:8b;
attachment extraction and validation are deterministic local Python.)

## Attachment Extraction

The intake system MUST automatically extract every attachment associated with an
incoming request. Supported categories: raster images, vector artwork, PDF
files, existing embroidery files, office documents, archive files, production
references. Extracted files MUST become permanent job artifacts.

## Artwork Identification

The system MUST automatically determine: artwork type, file format, resolution,
dimensions, transparency, background complexity, number of colors, dominant
colors, existing vector status, existing embroidery suitability. Artwork
characteristics MUST influence downstream routing decisions.

## Artwork Review

Every artwork submission MUST undergo automated review before vectorization:
image quality, compression artifacts, noise detection, background complexity,
missing regions, small feature detection, thin line detection, text detection,
edge clarity, overall embroidery suitability. The review MUST generate a
permanent structured report.

## Complexity Analysis

Artwork MUST be assigned an objective complexity score based on: path
complexity, color complexity, geometric complexity, small feature density, edge
quality, expected stitch density, estimated production difficulty. Complexity
scores MUST influence: agent selection, parameter selection, experimentation
budget, QA thresholds, production estimates.

## Missing Information Detection

The intake system MUST automatically determine whether required production
information is missing: garment type, garment color, placement location,
finished dimensions, thread colors, quantity, deadline, customer approval
requirements. Missing information MUST generate structured clarification
requests.

## Canonical Intake Artifacts

Every intake MUST produce: `intake_summary.md`, `job.json`, `raw_email.json`,
`missing_questions.md`, `artwork_review.md`. These artifacts become
authoritative references for downstream agents.

## Customer Communication

Customer communication MUST become progressively more autonomous: automatic
acknowledgements, clarification requests, progress updates, approval requests,
completion notifications, delivery notifications. Every customer-facing message
MUST be traceable within the job history. (Drafted by qwen3:8b locally; outbound
customer sends remain behind the human approval gate.)

## Knowledge Retrieval During Intake

Before making implementation or routing decisions the intake system MUST
retrieve relevant knowledge from the engineering library: similar historical
jobs, artwork processing guidance, production standards, machine limitations,
customer history, previous successful approaches. Retrieved knowledge MUST be
recorded as part of the decision trace.

## Autonomous Routing

Following intake analysis the system MUST automatically determine the next
processing stage considering: artwork complexity, missing information, existing
vector quality, production readiness, required experimentation, QA requirements,
customer approval requirements. Routing decisions MUST remain deterministic,
observable, and reproducible.

## Intake Verification Requirements

Evidence MUST confirm: automatic attachment extraction functions correctly;
customer metadata is extracted; artwork metadata is extracted; artwork review
reports are generated; missing information is detected; canonical intake
artifacts are created; knowledge retrieval occurs before routing decisions;
routing decisions are recorded; observable evidence exists for every intake
stage.

## Intake Final Report Requirements

At completion the implementing agent MUST report: intake implementation status,
supported intake sources, attachment extraction verification, artwork analysis
verification, generated intake artifacts, knowledge retrieval verification,
routing verification, commands executed, files created, files modified, known
limitations, recommended future improvements, next exact command.

---

# Project Requirement — Autonomous Raster Processing and Vector Generation (Preserved)

**Priority:** Critical

**Objective:** Develop a production-grade raster processing and vector
generation pipeline capable of transforming customer artwork into optimized,
embroidery-ready SVG files through deterministic processing, autonomous
experimentation, quality evaluation, and continuous historical learning. The
objective is not simply to vectorize artwork, but to determine the
highest-quality vector representation suitable for downstream embroidery
generation. **This entire pipeline is 100% local deterministic compute
(`vectorizer.py`, potrace/vtracer, Pillow, scikit-image) — no LLM required.**

## Raster Processing Pipeline

Every raster image MUST pass through a structured preprocessing pipeline: image
normalization, resolution analysis, background detection, background removal,
transparency generation, contrast enhancement, noise reduction, edge
enhancement, line strengthening, morphological cleanup, candidate generation.
Every preprocessing stage MUST preserve intermediate artifacts for comparison
and future learning.

## Image Analysis

Prior to vectorization the system MUST automatically determine: image
dimensions, resolution, aspect ratio, transparency, background complexity, color
count, edge quality, compression artifacts, line thickness, small feature
density, text presence, expected embroidery complexity. Analysis results MUST
influence parameter selection throughout downstream processing.

## Background Processing

The system MUST automatically determine the most appropriate background handling
strategy: preserve background, remove background, transparent background
generation, solid color replacement, foreground isolation, edge refinement,
artifact cleanup. The selected strategy MUST become part of the permanent job
history.

## Raster Cleanup

Representative cleanup operations: noise removal, speck removal, small artifact
removal, gap filling, line continuity improvement, shape preservation, boundary
smoothing, edge sharpening, contrast normalization. Cleanup MUST prioritize
downstream vector quality rather than visual appearance alone.

## Vector Generation

The platform MUST support multiple vectorization strategies: Potrace, Inkscape,
adaptive parameter sweeps, multi-pass tracing, layer-specific tracing,
experimental algorithms, future vectorization engines. The architecture MUST
allow additional vectorization engines to be incorporated without redesigning
the production pipeline. (`vectorizer.py` with vtracer is the current local
engine; potrace/Inkscape remain supported.)

## Parameter Exploration

Rather than executing a single vectorization attempt, the platform MUST explore
multiple parameter combinations: threshold values, corner detection, curve
optimization, path simplification, noise suppression, speck filtering, curve
precision, node optimization. Every parameter set MUST generate a measurable
candidate.

## Candidate Generation

The system MUST generate multiple competing SVG candidates. Every candidate MUST
preserve: processing parameters, generation method, quality metrics, processing
history, generated artifacts, evaluation results. Candidate generation MUST
remain deterministic and reproducible.

## SVG Optimization

Generated vectors MUST undergo structural optimization: node reduction, path
simplification, path merging, duplicate removal, open path detection, closed
path validation, self-intersection detection, geometry cleanup, structural
normalization. Optimization MUST improve downstream embroidery quality without
altering artwork intent.

## SVG Quality Assurance

Every SVG candidate MUST undergo objective evaluation: source similarity,
silhouette preservation, edge accuracy, node efficiency, path continuity,
structural simplicity, geometric fidelity, embroidery suitability. Quality
scores MUST determine downstream candidate selection. (Realized locally by
`metrics.py` sub-scores and `run_iteration.py` OVERALL_SCORE.)

## Candidate Ranking

Candidate evaluation MUST produce a ranked leaderboard. Each candidate MUST
include: overall score, vector quality, embroidery suitability, structural
quality, topology quality, expected stitch quality, processing time. The
highest-ranked candidate MUST become the default production candidate while
preserving all alternatives for future comparison.

## Historical Learning

Every successful vectorization MUST contribute to permanent historical learning:
parameter selections, winning candidates, failed candidates, processing metrics,
quality scores, decision traces, production observations, regression history.
Historical knowledge MUST continuously influence future parameter selection.

## Production Artifacts

The raster processing pipeline MUST generate permanent artifacts: normalized
raster, cleaned raster, candidate SVG files, optimization reports, candidate
leaderboard, processing metrics, quality reports, decision trace, final
production SVG. Every artifact MUST remain reproducible.

## Vectorization Verification Requirements

Evidence MUST confirm: raster preprocessing functions correctly; background
processing functions correctly; multiple vectorization strategies execute
successfully; parameter exploration occurs; multiple candidates are generated;
SVG optimization functions correctly; candidate ranking functions correctly;
historical learning records successful outputs; canonical production SVG files
are generated; observable evidence exists for every processing stage.

## Vectorization Final Report Requirements

At completion the implementing agent MUST report: raster processing
implementation status, vectorization engine verification, candidate generation
results, SVG optimization verification, candidate ranking verification,
historical learning implementation, generated production artifacts, commands
executed, files created, files modified, known limitations, recommended future
improvements, next exact command.

---

# Project Requirement — Embroidery Digitization and Stitch Plan Generation (Preserved)

**Priority:** Critical

**Objective:** Develop a production-grade embroidery digitization pipeline
capable of transforming validated SVG artwork into optimized, production-ready
embroidery stitch plans suitable for direct machine execution while continuously
improving through experimentation, historical learning, quality assurance, and
production feedback. The objective is not simply to export embroidery files, but
to generate stitch plans that maximize production quality, machine efficiency,
visual fidelity, and repeatability. **This entire pipeline is 100% local
deterministic compute (`digitizer.py`, pyembroidery, Ink/Stitch headless) — no
LLM required.**

## Digitization Pipeline

Every approved production SVG MUST pass through a structured embroidery
digitization workflow: SVG validation, embroidery suitability analysis, layer
analysis, object classification, stitch strategy selection, underlay planning,
pull compensation, satin generation, fill generation, running stitch generation,
travel optimization, trim optimization, color sequencing, stitch simulation,
quality assurance, production export. Every stage MUST preserve observable
evidence.

## SVG Validation

Prior to digitization the production SVG MUST be validated: closed path
verification, open path detection, duplicate path detection, self-intersection
detection, layer consistency, geometry integrity, scaling verification,
coordinate validation, object separation, structural consistency. Only validated
production artwork MUST proceed into embroidery generation.

## Embroidery Suitability Analysis

The system MUST evaluate whether artwork is appropriate for embroidery
production: minimum feature size, maximum stitch density, satin suitability,
fill suitability, running stitch suitability, pull distortion risk, push
distortion risk, thread break risk, registration complexity, production
complexity. Suitability analysis MUST influence downstream stitch planning.

## Object Classification

Each artwork object MUST be classified prior to stitch assignment: satin column,
fill region, running stitch, bean stitch, lettering, border, decorative element,
underlay region, travel region. Classification MUST remain extensible for future
embroidery strategies.

## Stitch Strategy Selection

The system MUST automatically determine the most appropriate stitch strategy for
every classified object: satin stitch, tatami fill, running stitch, triple
running stitch, bean stitch, motif fill, decorative fill, underlay variants.
Strategy selection MUST consider: object geometry, feature width, density
requirements, production quality, machine efficiency.

## Underlay Planning

Representative underlay strategies: edge walk, center walk, zig-zag, tatami
underlay, double underlay, multiple underlay combinations. Underlay selection
MUST maximize embroidery stability while minimizing unnecessary stitch count.

## Pull Compensation

Automatic pull compensation MUST be determined based upon: stitch direction,
material characteristics, stitch density, object geometry, satin width, fill
strategy, historical production learning. Compensation values MUST remain
observable and reproducible.

## Stitch Optimization

Representative optimization: travel reduction, trim reduction, jump reduction,
stitch ordering, color ordering, thread efficiency, production efficiency,
machine efficiency. Optimization MUST preserve embroidery quality while
minimizing unnecessary machine operations.

## Stitch Simulation

Every generated stitch plan MUST undergo automated simulation before production
approval: stitch path visualization, needle penetration sequence, travel paths,
trim locations, color sequence, production timing, estimated stitch count,
machine execution preview. Simulation results MUST become permanent production
artifacts.

## Density Analysis

Every stitch plan MUST undergo density evaluation: excessive density detection,
insufficient density detection, thread accumulation, fabric stress, stitch
overlap, registration concerns, production risk identification. Density analysis
MUST directly influence QA approval.

## Production Quality Assurance

Every embroidery plan MUST undergo objective quality evaluation: stitch
integrity, structural integrity, layer validation, density validation, color
sequence validation, machine compatibility, Bernina B700 compliance, production
readiness. Only plans satisfying QA requirements MUST advance to export.

## Production Export

Representative production outputs: PES, DST, EXP, additional supported
embroidery formats. Every export MUST preserve: artwork dimensions, stitch
integrity, color sequence, production metadata.

## Historical Learning

Successful embroidery plans MUST contribute to permanent production knowledge:
stitch parameters, underlay selections, density values, pull compensation, QA
results, machine observations, production outcomes, customer feedback,
regression history. Historical learning MUST continuously improve future stitch
generation.

## Production Artifacts

Representative production artifacts: stitch plan, simulation report, density
report, QA report, production metrics, decision trace, export files, production
history. All production artifacts MUST remain reproducible.

## Digitization Verification Requirements

Evidence MUST confirm: SVG validation functions correctly; embroidery
suitability analysis functions correctly; object classification functions
correctly; stitch strategy selection functions correctly; underlay planning
functions correctly; pull compensation functions correctly; stitch optimization
functions correctly; stitch simulation functions correctly; density analysis
functions correctly; QA approval functions correctly; production export
succeeds; Bernina B700 compatibility is validated; observable evidence exists
for every processing stage.

## Digitization Final Report Requirements

At completion the implementing agent MUST report: digitization implementation
status, SVG validation verification, stitch generation verification, simulation
verification, density analysis verification, QA verification, production export
verification, historical learning implementation, commands executed, files
created, files modified, known limitations, recommended future improvements,
next exact command.

---

# Project Requirement — Quality Assurance, Verification, Historical Learning, and Continuous Improvement (Preserved)

**Priority:** Critical

**Objective:** Develop a production-grade quality assurance framework that
continuously validates every stage of the EMBIZ production pipeline while
accumulating historical knowledge to improve future production quality,
engineering decisions, autonomous reasoning, and system performance. QA MUST NOT
function as a single terminal validation step; QA MUST exist throughout every
stage of the production pipeline.

## Continuous Quality Assurance Philosophy

Every production stage MUST include embedded quality assurance. Representative
QA checkpoints: customer intake, attachment extraction, artwork review, raster
preprocessing, vector generation, SVG optimization, embroidery suitability
analysis, stitch planning, stitch simulation, density analysis, production
export, customer approval, production completion. Every checkpoint MUST generate
observable evidence — and MUST be Slack-visible (QA results are posted to
`#embiz-qa` by the daemon).

## Verification Philosophy

No implementation, workflow, pipeline stage, or engineering task MUST be
considered complete solely because execution finished successfully. Completion
MUST require observable verification emphasizing: objective evidence,
repeatability, reproducibility, traceability, deterministic validation,
historical comparison. Unsupported completion claims MUST never be accepted.

## Observable Evidence

Every engineering activity MUST produce measurable evidence: commands executed,
configuration values, generated artifacts, repository changes, processing
metrics, quality metrics, candidate rankings, decision traces, validation
reports, log output, production outputs, screenshots where applicable. Evidence
MUST become part of the permanent engineering history.

## Decision Trace Requirements

Every significant engineering decision MUST produce a permanent decision trace:
decision made, reasoning, knowledge consulted, alternatives evaluated, selection
criteria, final outcome, validation evidence. Decision traces MUST support
future learning and regression analysis. (Convention: append-only
`decision_trace.jsonl` at the repository root; the local agents write to the
same file and mirror significant traces to Slack as Slack-visible decision
traces.)

## Historical Learning

Historical learning MUST become a permanent subsystem rather than an optional
feature. The platform MUST preserve: successful implementations, failed
implementations, production observations, customer feedback, parameter
selections, engineering decisions, QA outcomes, production metrics, performance
history, regression history. Historical information MUST directly influence
future autonomous execution.

## Regression Framework

The platform MUST continuously compare current performance against historical
baselines: production quality, SVG quality, stitch quality, candidate ranking,
QA pass rates, performance metrics, production timing, engineering accuracy.
Regression testing MUST automatically identify quality degradation.

## Continuous Experimentation

During idle execution the platform MUST continue improving itself through
autonomous experimentation: parameter exploration, alternative algorithms,
pipeline optimization, performance improvements, candidate comparison,
methodology refinement, engineering workflow improvements, QA refinement.
Experimentation MUST never interfere with active production jobs.

## Knowledge Memorialization

Validated engineering improvements MUST become permanent engineering knowledge:
engineering standards, successful workflows, proven parameter selections, QA
methodologies, lessons learned, best practices, historical observations,
regression outcomes. Knowledge MUST remain searchable and retrievable.

## Autonomous Code Review

The platform MUST continuously inspect its own implementation: static analysis,
style consistency, dead code detection, complexity analysis, documentation
review, security review, performance review, dependency review. Recommendations
MUST be prioritized according to measurable engineering impact. (LLM-assisted
review is a `code` task on qwen3:8b; deterministic linters run natively.)

## Self-Improvement Objectives

The platform MUST continuously seek opportunities to improve: production
quality, vector quality, stitch quality, QA accuracy, pipeline reliability,
performance, maintainability, documentation, knowledge quality, engineering
consistency. Improvements MUST be validated before becoming permanent behavior.

## QA Verification Requirements

Evidence MUST confirm: QA exists throughout the production pipeline; observable
evidence is generated at every stage; decision traces are preserved; historical
learning records successful and unsuccessful outcomes; regression testing
functions correctly; knowledge memorialization functions correctly; autonomous
experimentation functions correctly; autonomous code review functions correctly;
continuous improvement mechanisms function correctly; every production artifact
is traceable to supporting evidence.

## QA Final Report Requirements

At completion the implementing agent MUST report: QA implementation status,
verification framework status, historical learning implementation, regression
framework implementation, knowledge memorialization implementation, continuous
experimentation implementation, autonomous review implementation, commands
executed, files created, files modified, known limitations, recommended future
improvements, next exact command.

---

# Project Requirement — Dashboard, Observability, Operational Visibility, and Autonomous Oversight With Explicit Human Gates (Preserved)

**Priority:** Critical

**Objective:** Develop a comprehensive operational dashboard providing complete
visibility into every subsystem, autonomous agent, production job, engineering
decision, quality metric, experiment, and historical learning activity. The
dashboard MUST function as the primary operational control center.

## Dashboard Design Principles

The dashboard MUST prioritize: complete observability, real-time visibility,
human readability, engineering transparency, production awareness, historical
context, autonomous activity monitoring. Every significant autonomous activity
MUST be observable through the dashboard.

## Required Dashboard Areas

Mission Control; Current Jobs; Agent Activity; Slack Intelligence; Knowledge
Retrieval; Production Queue; Vectorization Experiments; Candidate Leaderboard;
QA Results; Historical Learning; Regression Results; Reward Dashboard; Penalty
Dashboard; Infrastructure Health; System Alerts — plus (new) **Local Model
Health** (Ollama status, loaded model, VRAM utilization, escalation-ladder
statistics, paid-usage audit totals). The dashboard architecture MUST remain
extensible as new capabilities are added.

## Operational Visibility

Operators MUST be able to determine at a glance: what every agent is doing, what
every production job is doing, which knowledge was retrieved, which engineering
decisions were made, which experiments are executing, which candidates are
leading, which QA checks succeeded, which QA checks failed, which regressions
occurred, which improvements were learned — and which model rung served each
LLM task. The platform MUST never become a "black box."

## Dashboard Interaction and Autonomous Oversight With Explicit Human Gates

The dashboard MUST function as an operational interface rather than a passive
monitoring display: real-time system monitoring, job inspection, agent
inspection, production history review, QA review, candidate comparison,
experiment review, knowledge retrieval inspection, manual approvals, manual
overrides where authorized, production status review. All operator actions MUST
be recorded within the system history.

## Historical Dashboards

Historical dashboards MUST preserve longitudinal visibility: production history,
QA history, candidate history, experiment history, learning history, regression
history, infrastructure history, agent performance history — supporting trend
analysis and long-term engineering improvement.

## Reward and Improvement Tracking

The platform MUST maintain structured records describing successful engineering
behavior: successful experiments, successful production runs, high-performing
parameter sets, high-performing workflows, effective engineering decisions,
reusable methodologies, validated improvements. Validated improvements MUST
become permanent engineering knowledge. (Realized locally by
`reward_penalty_ledger.jsonl`.)

## Failure Analysis

The platform MUST preserve structured information describing unsuccessful
execution: failed experiments, failed production runs, QA failures, regression
failures, infrastructure failures, engineering errors, recovery actions,
corrective actions. Failures MUST become learning opportunities rather than
discarded information.

## Operational Alerts

Representative alerts: production failures, infrastructure failures, QA
failures, regression detection, missing knowledge, missing approvals, missing
artifacts, pipeline interruptions, service outages — plus (new) Ollama runtime
down, GPU offload degraded below 100%, paid-API escalation occurred. Alerts MUST
remain visible until resolved.

## Dashboard Verification Requirements

Evidence MUST confirm the dashboard displays: real-time production activity,
agent activity, current jobs, QA results, knowledge retrieval activity,
historical learning, regression information, infrastructure health, operational
alerts — with observable evidence for every monitored subsystem.

## Dashboard Final Report Requirements

At completion the implementing agent MUST report: dashboard implementation
status, operational visibility verification, historical dashboard
implementation, alert implementation, QA dashboard implementation, learning
dashboard implementation, commands executed, files created, files modified,
known limitations, recommended future improvements, next exact command.

---

# Project Requirement — Autonomous Agent Collaboration and Orchestration (Preserved)

**Priority:** Critical

**Objective:** Develop a coordinated multi-agent architecture in which
specialized autonomous agents cooperate continuously while maintaining clearly
separated responsibilities, deterministic communication, observable execution,
and complete engineering traceability. The objective is coordinated
specialization rather than autonomous duplication of effort.

## Architectural Principles

The architecture MUST emphasize: clear responsibility boundaries, deterministic
execution, observable communication, continuous collaboration, knowledge
sharing, historical learning, fault isolation, extensibility, scalability. Every
agent MUST own a clearly defined engineering responsibility.

## Representative Agent Responsibilities

Customer Intake; Artwork Review; Raster Processing; Vector Generation; SVG
Optimization; Embroidery Preparation; Stitch Planning; Quality Assurance;
Historical Learning; Knowledge Retrieval; Documentation; Production Reporting;
Infrastructure Monitoring; Slack Operations; Workflow Orchestration; (new) Model
Routing. Additional agents MUST be introduced (when validated) without
redesigning the architecture.

## Collaboration Model

Agents MUST collaborate continuously throughout production: task delegation,
information exchange, knowledge sharing, progress reporting, clarification
requests, QA requests, approval requests, engineering recommendations, status
updates. Collaboration MUST remain observable and reproducible (Slack-mirrored
and transcript-logged).

## Knowledge Sharing

Agents MUST share engineering knowledge through structured artifacts rather than
transient conversation alone: production reports, QA reports, decision traces,
candidate evaluations, experiment reports, historical observations, knowledge
references. Shared knowledge MUST remain permanently available for future
retrieval.

## Autonomous Coordination

The orchestration layer MUST continuously coordinate: agent assignment, task
scheduling, dependency management, workload balancing, retry management, failure
recovery, pipeline progression, production prioritization. Coordination
decisions MUST remain observable. **Local constraint:** because only one LLM can
run at a time, the orchestrator serializes reasoning turns across agents (a
single agent loop multiplexing agent roles is the validated local pattern) while
deterministic pipeline work runs freely in parallel on CPU.

## Failure Recovery

Representative recovery mechanisms: automatic retry, alternative routing, agent
reassignment, escalation, manual approval requests, recovery reporting. Recovery
actions MUST become permanent engineering history.

## Engineering Communication

Communication MUST prioritize engineering precision: implementation decisions,
QA observations, engineering recommendations, production updates, knowledge
references, validation evidence, experiment outcomes. Communication MUST avoid
unsupported assumptions.

## Agent Verification Requirements

Evidence MUST confirm: agents have clearly separated responsibilities; agent
communication functions correctly; shared engineering artifacts are generated;
coordination functions correctly; failure recovery functions correctly;
knowledge sharing functions correctly; decision traces are preserved; observable
evidence exists for every significant collaboration event.

## Agent Final Report Requirements

At completion the implementing agent MUST report: agent implementation status,
responsibility verification, communication verification, coordination
verification, failure recovery verification, knowledge sharing verification,
commands executed, files created, files modified, known limitations, recommended
future improvements, next exact command.

---

# Project Requirement — Knowledge Retrieval, Engineering Memory, and Continuous Library Expansion (Preserved)

**Priority:** Critical

**Objective:** Develop a production-grade knowledge retrieval system that
continuously accumulates, organizes, retrieves, validates, and expands
engineering knowledge used throughout the EMBIZ platform. Knowledge retrieval
MUST become a mandatory prerequisite for engineering decisions rather than an
optional enhancement. The engineering library MUST function as the primary
source of procedural knowledge used by autonomous agents.

## Knowledge Philosophy

Engineering knowledge MUST exist independently of the underlying AI model. The
platform MUST prioritize: local knowledge, version-controlled knowledge,
structured documentation, searchable engineering references, historical
production knowledge, validated methodologies, continuous expansion, long-term
maintainability. Knowledge MUST remain durable regardless of future changes to
AI providers or reasoning engines.

## Knowledge Sources

Engineering documentation, internal standards, production observations,
historical projects, QA reports, machine documentation, embroidery manuals,
vendor documentation, research papers, image collections, diagrams, screenshots,
workflow illustrations, before-and-after examples, failure examples, successful
production examples. Every knowledge source MUST become searchable.

## Knowledge Ingestion

The platform MUST continuously ingest engineering knowledge: native text
extraction, OCR, image analysis, metadata extraction, semantic indexing,
structured tagging, knowledge graph integration, embedding generation. Ingestion
MUST preserve both original source material and extracted representations.

## Mandatory Retrieval

Before implementation decisions are made, the platform MUST retrieve relevant
engineering knowledge: similar historical implementations, production standards,
engineering references, machine limitations, QA procedures, historical
experiments, successful methodologies, previous failures. Engineering decisions
MUST cite retrieved knowledge.

## Source Enforcement

Every significant implementation decision MUST identify: sources consulted,
knowledge retrieved, engineering guidance applied, validation evidence, decision
trace. Unsupported implementation decisions MUST be treated as incomplete.

## Continuous Library Expansion

The engineering library MUST continuously grow through: successful
implementations, failed implementations, production observations, QA findings,
customer feedback, experimental results, engineering discoveries, validated
improvements. Knowledge accumulation MUST occur automatically whenever
practical.

## Knowledge Organization

Knowledge MUST remain organized using consistent taxonomy: Engineering,
Production, Embroidery, Infrastructure, Quality Assurance, Historical Learning,
Architecture, Troubleshooting, Standards, Experiments. The organization MUST
remain extensible.

## Search and Retrieval

Knowledge retrieval MUST support: keyword search, semantic search, similarity
search, metadata filtering, historical lookup, cross-reference discovery,
relationship traversal. Search MUST prioritize relevance and engineering
usefulness.

## Knowledge Verification Requirements

Evidence MUST confirm: knowledge ingestion functions correctly; knowledge
indexing functions correctly; mandatory retrieval occurs before implementation;
sources are cited; decision traces reference retrieved knowledge; library
expansion functions correctly; search functions correctly; observable evidence
exists for every retrieval stage.

## Knowledge Final Report Requirements

At completion the implementing agent MUST report: knowledge implementation
status, ingestion verification, retrieval verification, source enforcement
verification, search verification, library expansion verification, commands
executed, files created, files modified, known limitations, recommended future
improvements, next exact command.

---

# Project Requirement — Production Pipeline Architecture (Preserved)

**Priority:** Critical

**Objective:** Develop a deterministic, observable, extensible production
pipeline capable of transforming customer requests into completed embroidery
deliverables while preserving complete engineering traceability. Every pipeline
stage MUST generate canonical artifacts consumed by downstream stages.

## Canonical Pipeline

```text
Customer Request
↓
Customer Intake
↓
Attachment Extraction
↓
Artwork Review
↓
Knowledge Retrieval
↓
Raster Processing
↓
Vector Generation
↓
SVG Optimization
↓
Embroidery Preparation
↓
Stitch Planning
↓
Simulation
↓
Density Analysis
↓
Quality Assurance
↓
Customer Approval
↓
Production Export
↓
Production History
↓
Continuous Learning
```

Each stage MUST: produce observable evidence, generate canonical artifacts,
preserve historical records, support deterministic replay, support future
regression testing. (Stages "Raster Processing" through "Production Export" are
100% local deterministic compute; the LLM appears only in intake analysis,
knowledge synthesis, report writing, and Slack conversation.)

## Pipeline Artifact Requirements

Representative canonical artifacts: intake summary, job metadata, artwork
review, knowledge references, processing metrics, candidate leaderboard,
decision traces, QA reports, production reports, historical records. Every
artifact MUST remain reproducible and permanently associated with its
originating job.

## Pipeline Verification Requirements

Evidence MUST confirm: every pipeline stage produces canonical artifacts;
downstream stages consume canonical artifacts; historical traceability is
preserved; pipeline execution remains deterministic; observable evidence exists
throughout the production pipeline.

## Pipeline Final Report Requirements

At completion the implementing agent MUST report: pipeline implementation
status, artifact verification, pipeline verification, historical traceability
verification, commands executed, files created, files modified, known
limitations, recommended future improvements, next exact command.

---

# Project Requirement — Production Readiness, Deployment, Operations, and Long-Term Evolution (Preserved)

**Priority:** Critical

**Objective:** Develop a production environment that is reliable, observable,
fault tolerant, continuously operating, continuously improving, and capable of
supporting long-term autonomous evolution without requiring continual human
intervention (human gates only when required). The production environment MUST
prioritize reliability, repeatability, maintainability, operational
transparency, and engineering quality.

## Production Readiness

Before any subsystem is considered production-ready it MUST demonstrate:
deterministic execution, observable operation, complete verification, historical
traceability, recoverability, automated validation, repeatable deployment,
production documentation. No subsystem MUST be promoted to production solely
because it executes successfully once.

## Deployment Architecture

The deployment architecture MUST support: repeatable deployments, automated
deployment, configuration management, version control, rollback capability,
environment isolation, dependency verification, production validation.
Deployment MUST minimize production downtime. **Local realization:** systemd
user services (`embiz-slack-daemon.service`, `embiz-agent-loop.service`) with
`Restart=always`, environment loaded from `~/.config/embiz/env` (or
`/etc/embiz/env`), enabled to survive reboots via
`loginctl enable-linger jmmint`.

## Configuration Management

System configuration MUST remain: version controlled, observable, reproducible,
auditable, environment specific, secure, documented. Configuration changes MUST
produce permanent engineering history. Secrets are NEVER hardcoded — env files
only, mode 600.

## Dependency Management

Every production dependency MUST be: identified, installed, verified, version
tracked, continuously monitored. Missing dependencies MUST generate actionable
diagnostics before pipeline execution.

## Infrastructure Monitoring

CPU utilization, memory utilization, disk utilization, storage capacity, network
connectivity, service availability, process health, queue depth, background
workers, cloud connectivity — plus (new) GPU utilization/VRAM (`nvidia-smi`) and
Ollama runtime availability. Infrastructure metrics MUST remain historically
available.

## Operational Health

Service availability, pipeline health, job throughput, queue status, agent
availability, cloud services, storage availability, knowledge availability,
dashboard availability, Slack integration, API availability — plus (new) daemon
heartbeats. Operational health MUST remain continuously observable.

## Backup Strategy

Scheduled backups, artifact backups, configuration backups, knowledge backups,
historical archive backups, recovery verification. Backups MUST be periodically
validated through restoration testing. (AWS/S3/R2 infrastructure preserved for
this purpose.)

## Disaster Recovery

Recovery procedures MUST support: service restoration, configuration
restoration, artifact restoration, knowledge restoration, historical record
restoration, production continuity — documented and periodically validated.

## Security Principles

Least privilege, secure secrets management, auditability, access logging,
configuration integrity, artifact integrity, deployment integrity, operational
transparency. Security controls MUST NOT unnecessarily reduce engineering
observability. Slack request signing / Socket Mode token auth is mandatory;
approval actions are authorized against an allowlist of Slack user IDs
(`EMBIZ_SLACK_APPROVERS`).

## Operational Documentation

Architecture documentation, deployment documentation, configuration
documentation, troubleshooting documentation, recovery documentation,
engineering standards, operational procedures, maintenance procedures.
Documentation MUST evolve alongside the implementation. (`local_agents/README.md`
is the local deployment document.)

## Long-Term Autonomous Evolution

The EMBIZ platform MUST continuously evolve through: historical learning,
autonomous experimentation, engineering observations, regression analysis,
performance optimization, QA improvements, knowledge accumulation, workflow
refinement, architecture refinement, production feedback. Long-term improvement
MUST become a permanent characteristic rather than a discrete project phase.

## Production Verification Requirements

Evidence MUST confirm: production deployment functions correctly; configuration
management functions correctly; dependency verification functions correctly;
infrastructure monitoring functions correctly; operational health monitoring
functions correctly; backup procedures function correctly; disaster recovery
procedures are documented; operational documentation exists; continuous
improvement mechanisms remain operational; observable evidence exists for every
production subsystem.

## Production Final Report Requirements

At completion the implementing agent MUST report: production readiness status,
deployment verification, configuration verification, dependency verification,
infrastructure monitoring verification, operational health verification, backup
verification, disaster recovery verification, documentation completed, commands
executed, files created, files modified, known limitations, recommended future
improvements, next exact command.

---

# AUTONOMOUS SLACK AGENT SYSTEM — CONTINUOUSLY RUNNING LOCAL DAEMONS (MOST IMPORTANT)

The Slack system MUST be a continuously running autonomous daemon system — NOT a
one-off chatbot session. Once set up, it runs persistently: it reasons, executes
tasks, monitors Slack, responds, triggers workflows, delivers results, and
continues without repeated prompting. It is deployed as systemd user services on
the Mint machine and survives reboots.

## Transport

**Socket Mode is mandatory** (`SLACK_APP_TOKEN` app-level token with
`connections:write`). Socket Mode is outbound-only WebSocket — no public
ingress, no tunnel, no port-forward is needed on a laptop. The daemon MUST
implement reconnect logic and MUST alert (locally logged + retried Slack post)
on prolonged disconnection.

## Complete Slack Responsibility Ownership (all fifteen, mandatory)

The autonomous agents MUST fully own ALL of the following Slack
responsibilities. Each maps to a concrete handler in
`local_agents/slack_daemon.py` and/or a posting function used by
`local_agents/agent_loop.py`:

| # | Responsibility | Local Implementation |
|---|---|---|
| 1 | Slack message monitoring | Socket Mode `events_api` listener (`message`, `app_mention` events); every inbound event transcript-logged |
| 2 | Slack command handling | Natural-language commands addressed to the bot (`@embiz run ...`, `@embiz status`) parsed and dispatched; LLM (qwen3:8b) interprets free-form requests |
| 3 | Slack slash command support | `/embiz <subcommand>` (`status`, `jobs`, `queue`, `run`, `approve`, `reject`, `ask`, `report`, `models`, `health`) via Socket Mode `slash_commands` envelopes |
| 4 | Slack approval handling | Block Kit Approve button, `:white_check_mark:` reaction on approval messages, or `/embiz approve JOB-ID` — writes the approval decision file consumed by the agent loop; approver allowlist enforced |
| 5 | Slack rejection handling | Reject button, `:x:` reaction, or `/embiz reject JOB-ID reason...` — recorded with reason, job transitions to rejected/rework |
| 6 | Slack job status updates | Every job state transition (full state machine above) posted to `#embiz-jobs` |
| 7 | Slack agent conversations | Mentions and DMs answered by qwen3:8b through the model router (`slack_reply` task type, think-stripped); agents post inter-agent updates visibly |
| 8 | Slack production notifications | Production export complete, PES ready, leaderboard winner selected → `#embiz-jobs` |
| 9 | Slack error notifications | Every unhandled exception in daemon or agent loop posted to `#embiz-alerts` with traceback summary; errors never silently swallowed |
| 10 | Slack operational reporting | Scheduled operational report (default every 6 h): queue depth, jobs completed, OVERALL_SCORE trend, escalation-ladder stats, paid usage total → `#embiz-alerts` |
| 11 | Slack workflow triggering | `/embiz run <pipeline task>` and natural-language triggers enqueue jobs into the filesystem queue; the agent loop picks them up autonomously |
| 12 | Slack transcript logging | Every inbound and outbound Slack message appended to `local_agents/state/slack_transcript.jsonl` (durable, append-only) |
| 13 | Slack-visible decision traces | Significant decision-trace entries mirrored to Slack (`#embiz-jobs`/`#embiz-qa`) in human language, in addition to `decision_trace.jsonl` |
| 14 | Slack-visible QA results | QA gate outcomes (metrics.py scores, density QA, B700 compliance) posted to `#embiz-qa` with pass/fail and evidence pointers |
| 15 | Slack-visible job progress updates | The agent loop posts progress at every plan step (started, step n/m, awaiting approval, done/failed) to `#embiz-jobs` |

## Daemon Topology (systemd user services)

```text
┌───────────────────────────── Mint machine (jmmint) ─────────────────────────────┐
│                                                                                 │
│  embiz-slack-daemon.service          embiz-agent-loop.service                   │
│  ┌──────────────────────────┐        ┌────────────────────────────┐             │
│  │ slack_daemon.py          │        │ agent_loop.py              │             │
│  │  Socket Mode listener    │ files  │  plan → act → report loop  │             │
│  │  events / slash / blocks │◄──────►│  job queue consumer        │             │
│  │  approvals / rejections  │ queue  │  approval gate waiter      │             │
│  │  transcript logging      │ +      │  pipeline runner (CPU)     │             │
│  │  error notifications     │ appr.  │  idle experimentation      │             │
│  └────────────┬─────────────┘ files  └──────────────┬─────────────┘             │
│               │                                     │                           │
│               ▼                                     ▼                           │
│        model_router.py  ──────────────►  qwen_client.py ──► Ollama :11434       │
│        (escalation ladder,                (think-stripping)   qwen3:8b, GPU      │
│         paid-usage audit)                                                       │
│                                                                                 │
│  Deterministic pipeline (no LLM): vectorizer.py, digitizer.py,                   │
│  run_iteration.py, metrics.py  — CPU/RAM, runs in parallel with inference       │
└─────────────────────────────────────────────────────────────────────────────────┘
```

Both services: `Restart=always`, `EnvironmentFile=%h/.config/embiz/env`,
`WantedBy=default.target`, survive reboot via linger.

## Durable State Layout

```text
local_agents/state/
├── queue/
│   ├── pending/           one JSON file per queued job (atomic rename claims)
│   ├── active/            claimed jobs
│   ├── done/              completed jobs (evidence retained)
│   └── failed/            failed jobs (evidence retained)
├── approvals/
│   ├── pending/           approval requests awaiting a human gate
│   └── decided/           approve/reject decisions written by the Slack daemon
├── slack_transcript.jsonl     responsibility 12
├── paid_usage_audit.jsonl     rung-4 cost transparency
├── router_events.jsonl        every ladder decision
├── agent_heartbeat.json       liveness for health checks
└── daemon_heartbeat.json
```

Plus the repository-root ledgers already in production use:
`decision_trace.jsonl`, `observations.jsonl`, `reward_penalty_ledger.jsonl`.

## Local Implementation Components (code shipped with this document)

* `local_agents/qwen_client.py` — Ollama API client (`http://localhost:11434`),
  qwen3:8b chat/generate with retry, timeout, `num_ctx` control, `/no_think`
  support, and mandatory `<think>` block stripping.
* `local_agents/model_router.py` — the local-first escalation ladder with
  per-task-type routing rules, `ollama list` (API `/api/tags`) discovery for
  rung 3, env-gated paid rung 4, paid-usage audit log, Slack cost notifications,
  and router event logging.
* `local_agents/slack_daemon.py` — Socket Mode listener + dispatcher covering
  all fifteen Slack responsibilities.
* `local_agents/agent_loop.py` — persistent autonomous agent loop
  (plan → act → report) using qwen3:8b for reasoning, filesystem job queue,
  Slack approval gating, progress updates, decision traces, and idle-period
  autonomous experimentation (`run_iteration.py`).
* `local_agents/systemd/embiz-slack-daemon.service` and
  `local_agents/systemd/embiz-agent-loop.service` — persistence.
* `local_agents/README.md` — Mint machine setup, env vars, install, enable,
  verify.

---

# Global Engineering Principles (Preserved)

The following principles apply to every subsystem described throughout this
specification. Every subsystem MUST:

* Produce observable evidence.
* Preserve deterministic execution.
* Preserve historical traceability.
* Generate canonical artifacts.
* Support autonomous learning.
* Support continuous improvement.
* Preserve engineering transparency.
* Retrieve knowledge before implementation whenever applicable.
* Record engineering decision traces.
* Support regression testing.
* Generate production-quality documentation.
* Produce verifiable quality metrics.
* Preserve reproducibility.
* Minimize explicit human-gated intervention (only when required).
* Maximize autonomous operation.
* **Route every LLM call through the local-first escalation ladder; never spend
  on paid inference without a logged, Slack-visible escalation.**

No subsystem MUST be considered complete until implementation, verification,
documentation, observability, historical learning, and continuous improvement
requirements have all been satisfied.

---

# End of Business Requirements Document (Local-First Edition)

The purpose of this document is to establish a comprehensive, production-grade
engineering specification for the EMBIZ platform executed local-first on the
proven Mint machine. Every implementation MUST advance the continuously running
autonomous platform toward becoming a continuously operating, continuously
learning, continuously improving autonomous embroidery production system whose
engineering knowledge, production quality, and operational capabilities improve
over time through observable execution, measurable outcomes, validated learning,
and deterministic engineering practices — with all reasoning on the local GPU
and paid models reserved as the final, audited, Slack-announced escalation rung.

**End of Document**
