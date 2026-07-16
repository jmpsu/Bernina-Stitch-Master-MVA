#!/usr/bin/env python3
"""Compile the EMBIZ named agent roster into machine-readable runtime contracts.

Source of truth: docs/requirements/EMBIZ_BRD.md, section "NAMED AGENT ROSTER".
Output: agents/contracts/<agent_id>.json (one per agent) + agents/contracts/index.json.

The BRD requires every agent to have a machine-readable contract containing:
agent_id, primary_mission, inputs, outputs, allowed_actions,
required_repositories, quality_gates, required_slack_events, approval_rules,
rejection_rules, handoff_targets, performance_metrics.

Re-run after any roster edit in the BRD; contracts are generated artifacts and
should never be hand-edited.
"""

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BRD = REPO / "docs" / "requirements" / "EMBIZ_BRD.md"
OUT = REPO / "agents" / "contracts"

# Map roster ##### section headings onto contract fields.
SECTION_FIELD = {
    "Primary Mission Expansion": "primary_mission_expansion",
    "Inputs": "inputs",
    "Core Responsibilities": "core_responsibilities",
    "End-to-End Workflow": "end_to_end_workflow",
    "Quality Gates": "quality_gates",
    "Validation Checklist": "validation_checklist",
    "Failure Modes / Red Flags": "rejection_rules",
    "Collaboration Requirements": "collaboration_requirements",
    "Slack / Event Requirements": "required_slack_events",
    "Escalation Conditions": "escalation_conditions",
    "Knowledge Sources": "knowledge_sources",
    "Continuous Improvement Responsibilities": "continuous_improvement",
    "Performance Metrics": "performance_metrics",
}

PREAMBLE_KEYS = {
    "Primary Mission": "primary_mission",
    "Autonomous Decision Authority": "autonomous_decision_authority",
    "Communication / File Operations": "communication_file_operations",
    "Outputs": "outputs_raw",
    "Repositories": "repositories_raw",
    "Skills": "skills_raw",
}


def roster_text() -> str:
    text = BRD.read_text(encoding="utf-8")
    m = re.search(r"^## NAMED AGENT ROSTER$", text, re.M)
    if not m:
        sys.exit("NAMED AGENT ROSTER heading not found in BRD")
    return text[m.start():]


def split_agents(text: str):
    """Yield (name, role, body) for each '#### Name - Role' block."""
    parts = re.split(r"^#### +(.+?)$", text, flags=re.M)
    # parts[0] is the roster preamble; then alternating header/body.
    for header, body in zip(parts[1::2], parts[2::2]):
        if " - " not in header:
            continue
        name, role = (s.strip() for s in header.split(" - ", 1))
        # Stop each body at the next ### group heading if present.
        body = re.split(r"^### ", body, maxsplit=1, flags=re.M)[0]
        yield name, role, body


def parse_preamble(lines):
    """Parse the indented key: value lines before the first ##### heading."""
    fields = {}
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        # 'Repositories - ...- Skills: ...' appears joined on one line.
        if "- Skills:" in stripped and stripped.startswith("Repositories"):
            repos, skills = stripped.split("- Skills:", 1)
            fields["repositories_raw"] = repos.strip(" -")
            fields["skills_raw"] = skills.strip()
            continue
        for key, field in PREAMBLE_KEYS.items():
            if stripped.startswith(key + ":") or stripped.startswith(key + " -"):
                fields[field] = stripped[len(key):].lstrip(":- ").strip()
                break
    return fields


def parse_sections(body: str):
    """Split the agent body into preamble lines + ##### sections of items."""
    chunks = re.split(r"^##### *(.+?): *$", body, flags=re.M)
    preamble = chunks[0].splitlines()
    sections = {}
    for heading, content in zip(chunks[1::2], chunks[2::2]):
        items = [ln.strip() for ln in content.splitlines() if ln.strip()]
        sections.setdefault(heading.strip(), []).extend(items)
    return preamble, sections


def extract_repositories(raw: str):
    if not raw:
        return []
    return sorted(set(re.findall(r"([a-z0-9][a-z0-9_-]+) with label", raw))) or [raw]


def compile_contracts():
    text = roster_text()
    agents = list(split_agents(text))
    names = {name for name, _, _ in agents}
    OUT.mkdir(parents=True, exist_ok=True)

    index = []
    for name, role, body in agents:
        preamble_lines, sections = parse_sections(body)
        pre = parse_preamble(preamble_lines)

        contract = {
            "agent_id": name.lower(),
            "name": name,
            "role": role,
            "primary_mission": pre.get("primary_mission", ""),
            "inputs": sections.get("Inputs", []),
            "outputs": [o.strip() for o in pre.get("outputs_raw", "").split(",") if o.strip()],
            "allowed_actions": [
                a for a in (
                    pre.get("autonomous_decision_authority", ""),
                    pre.get("communication_file_operations", ""),
                ) if a
            ],
            "required_repositories": extract_repositories(pre.get("repositories_raw", "")),
            "skills": [s.strip() for s in pre.get("skills_raw", "").split(",") if s.strip()],
            "quality_gates": sections.get("Quality Gates", []),
            "required_slack_events": sections.get("Slack / Event Requirements", []),
            "approval_rules": [
                a for a in [pre.get("autonomous_decision_authority", "")] if a
            ] + [
                item for item in sections.get("Quality Gates", [])
                if re.search(r"approv", item, re.I)
            ],
            # Morgan's roster entry has no Failure Modes section; escalation
            # conditions are the roster's rejection semantics in that case.
            "rejection_rules": sections.get("Failure Modes / Red Flags")
                or sections.get("Escalation Conditions", []),
            "handoff_targets": sorted(
                other for other in names
                if other != name and re.search(rf"\b{other}\b", body)
            ),
            "performance_metrics": sections.get("Performance Metrics", []),
        }
        # Supplementary roster fields kept verbatim for runtime use.
        for heading, field in SECTION_FIELD.items():
            if field in contract:
                continue
            if heading in sections:
                contract[field] = sections[heading]

        path = OUT / f"{contract['agent_id']}.json"
        path.write_text(json.dumps(contract, indent=2) + "\n", encoding="utf-8")
        index.append({
            "agent_id": contract["agent_id"],
            "role": role,
            "contract": f"agents/contracts/{path.name}",
            "handoff_targets": contract["handoff_targets"],
        })
        print(f"wrote {path.relative_to(REPO)}  gates={len(contract['quality_gates'])} "
              f"slack={len(contract['required_slack_events'])} handoffs={len(contract['handoff_targets'])}")

    (OUT / "index.json").write_text(
        json.dumps({"source": "docs/requirements/EMBIZ_BRD.md#named-agent-roster",
                    "agents": index}, indent=2) + "\n",
        encoding="utf-8")
    print(f"wrote agents/contracts/index.json ({len(index)} agents)")


if __name__ == "__main__":
    compile_contracts()
