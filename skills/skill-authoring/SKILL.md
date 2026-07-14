---
name: skill-authoring
description: Authors and validates EMBIZ agent skills to the BRD's SKILL.md specification. Use whenever creating a new skill, restructuring an existing skill, or verifying that skills/ conforms to the repository consistency requirement before declaring any implementation complete.
---

# Skill Authoring

## Purpose

Encode the BRD's "Agent Skill Standards and SKILL.md Specification"
(`docs/requirements/EMBIZ_BRD.md`) as an executable workflow so every skill in
this repository is organized, named, documented, and verified identically.
This is the meta-skill: all other skills are produced and audited through it.

## When to Use

- Creating any new skill under `skills/`.
- Modifying the structure, frontmatter, or sections of an existing skill.
- Auditing repository consistency before a final report.

Do **not** use for one-off documentation that is not an agent workflow
(that belongs in `docs/`), or for knowledge/reference material
(that belongs in `knowledge/` or `skills/references/`).

## Required Inputs

- The skill's bounded responsibility (one per skill — see separation rules).
- The BRD skill specification: `docs/requirements/EMBIZ_BRD.md`.
- The validator: `scripts/validate_skills.py`.

## Repository Inspection Workflow

1. `ls skills/` — confirm the skill does not already exist under another name.
2. Read `skills/references/` — reuse shared references instead of duplicating.
3. Check `agents/contracts/index.json` for the agent(s) that will execute the
   skill, so responsibility boundaries match their contracts.

## Architecture Inspection Workflow

1. Confirm where the skill sits in the canonical pipeline
   (BRD § "Production Pipeline Architecture").
2. Confirm which contract fields (`quality_gates`, `required_slack_events`)
   the skill must satisfy.

## Agent Responsibility Separation Rules

Each skill serves one clearly bounded responsibility. Except for
orchestration (Maya), no skill may claim the complete embroidery production
pipeline. If a draft skill spans two responsibilities, split it and
cross-reference.

## Implementation Workflow

1. Create `skills/<skill-name>/` — lowercase, hyphen-separated, descriptive.
2. Create exactly one primary entry point named `SKILL.md` (uppercase).
3. Add YAML frontmatter: `name` identical to the directory name;
   `description` stating both what the skill does and when to use it.
4. Write the required sections, in order: Purpose, When to Use, Required
   Inputs, Repository Inspection Workflow, Architecture Inspection Workflow,
   Agent Responsibility Separation Rules, Implementation Workflow,
   Verification Workflow, Evidence Requirements, Common Rationalizations,
   Red Flags, Final Report Format.
5. Add `scripts/` only when runnable helpers are required; add supporting
   markdown (lowercase, hyphen-separated) only when it keeps `SKILL.md`
   concise. Shared material goes in `skills/references/`.
6. Cross-reference other skills rather than duplicating their workflows.

## Verification Workflow

Run the automated validator and require a clean pass:

```bash
python3 scripts/validate_skills.py
```

It checks: location under `skills/`, `SKILL.md` naming, valid YAML
frontmatter, `name` == directory, description covers what + when, naming
conventions, required sections present, rationalizations table present,
red flags present, and no empty `scripts/` directories.

## Evidence Requirements

- Validator output showing `PASS` for every skill.
- `git diff --stat` for the created/modified skill files.
- Justification recorded for every supporting file and optional directory.

## Common Rationalizations

| Rationalization | Why it is incorrect | Required corrective action |
|---|---|---|
| "The skill is small, frontmatter is overkill." | The validator and retrieval tooling key off frontmatter; one nonconforming skill breaks repository consistency. | Add frontmatter and re-run the validator. |
| "I'll fix naming later." | Later never comes; inconsistent names break cross-references. | Rename now; update references. |
| "This content is obviously correct, no verification needed." | The BRD verification standard requires observable evidence for every claim. | Run `scripts/validate_skills.py` and attach output. |
| "I'll duplicate the workflow here for convenience." | Duplication drifts; the spec mandates cross-skill references. | Link the owning skill instead. |

## Red Flags

- A skill directory without `SKILL.md`, or with a lowercase/renamed entry point.
- Frontmatter `name` differing from the directory name.
- An empty `scripts/` directory in a markdown-only skill.
- A missing rationalizations table or red-flags section.
- A final report claiming conformance without validator output.

## Final Report Format

Follow the shared standard: `skills/references/final-report-standard.md`.
