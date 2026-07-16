# EMBIZ BRD → Repository Gap Analysis

Date: 2026-07-14. Canonical requirements: `docs/requirements/EMBIZ_BRD.md`
(+ `EMBIZ_ARCHITECTURAL_MATRIX_v1.html`, rev.3). Repo state: branch
`claude/trusting-hawking-mizv2d` from `main` @ `0e358c8`.

Status legend: **DONE** implemented and verified here · **PARTIAL** exists
but short of the BRD requirement · **MISSING** no implementation in this
repository · **EXTERNAL** lives outside this repo (local machine or cloud
accounts) and cannot be verified from it.

| # | BRD requirement | Status | Repository reality |
|---|---|---|---|
| 1 | Agent Skill Standards / `SKILL.md` spec (Critical) | **DONE** | `skills/` created: 6 conformant skills + `skills/references/`; enforced by `scripts/validate_skills.py` (all checks pass). |
| 2 | Roster compiled into machine-readable runtime contracts | **DONE** | `scripts/compile_agent_contracts.py` → `agents/contracts/*.json` (18 agents, all 12 BRD-required fields populated, handoffs resolved). |
| 3 | Repository tells the agent what to do | **DONE** | BRD + matrix canonicalized under `docs/requirements/`; contracts and skills reference them. |
| 4 | I-HIVE vectorization engine | **PARTIAL** | `vectorizer.py` (iterative, SSIM-targeted, attempt logging) exceeds the BRD's "not yet fully implemented" note, but Bayesian scoring, locked tracing layer, and dual-size export are absent. |
| 5 | Digitization with density QA, satin, underlay | **PARTIAL** | `digitizer.py` has satin fill + B700 density guard (1.2/mm², verified PASS in production cycle); pull compensation, trim insertion, color-block optimization not implemented. |
| 6 | Knowledge library as active decision system | **PARTIAL** | Ingestion + retrieval router + finalization knowledge gate exist (`local_agents/knowledge_*`); continuous expansion and embeddings/indexed tiers absent. |
| 7 | Named 18×M roster as runtime agents | **PARTIAL** | Contracts compiled (see #2), but `local_agents/personas.py` still defines a divergent 14-persona set (6 names outside the roster); runtime does not yet load contracts. |
| 8 | Customer intake (email webhook, attachment extraction, artwork ID) | **MISSING** | No intake pipeline in this repo; `cloudflare_email_to_job.py`, job API, and tunnel are BRD references to the external system root. |
| 9 | Dashboard + authentication + status controls | **MISSING** | No dashboard code in this repo. |
| 10 | Cloudflare Agents SDK + Flue runtime (Durable Objects) | **MISSING** | No Workers/wrangler config; contracts in #2 are the prerequisite operating contracts. |
| 11 | AWS transactional core, Terraform IAC, DynamoDB single-table (matrix regions AWS/IAC) | **MISSING** | No AWS or Terraform artifacts in this repo. |
| 12 | Slack-visible agent collaboration | **EXTERNAL/PARTIAL** | `local_agents/slack_daemon.py` + Slack uploads exist and ran in production; approval/rejection message structure is now contract-encoded but not enforced in daemon code. |
| 13 | systemd continuous operation ("never stops") | **EXTERNAL** | Unit files in `local_agents/systemd/`; runtime state lives on the operator's machine (`state/` is gitignored by design) and cannot be inspected from this environment. |
| 14 | Existing system root `/root/embroidery_business_agent_system` | **EXTERNAL** | Not this repository; integration points untestable from here. |

## Notable contradictions resolved in the BRD's favor

- BRD § "Current Implementation Reality" predates this repo's progress: the
  iterative vectorization engine *is* implemented and completed a production
  cycle (5 images finalized, SSIM 0.968–0.993, all gates PASS — see
  `docs/SYSTEM_ATLAS.md`). The BRD's forward requirements (#4) still stand.
- Persona names: the BRD roster is canonical. Migrating
  `local_agents/personas.py` to load `agents/contracts/` (and retiring the 6
  off-roster personas) is the next code change (#7).

## Recommended sequence (per BRD "Immediate Development Priorities")

1. Wire `local_agents/` runtime to `agents/contracts/` (closes #7).
2. Attachment extraction + real artwork review intake path (#8).
3. Visible Slack conversation upgraded to contract-structured
   approval/rejection events (#12).
4. Dashboard with authentication and status transition controls (#9).
5. Then: Ink/Stitch integration depth, PES generation, and the Cloudflare
   Agents SDK runtime (#10) with contracts as the operating layer.
