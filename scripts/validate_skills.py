#!/usr/bin/env python3
"""Validate skills/ and agents/contracts/ against the EMBIZ BRD standards.

Skill checks implement the BRD "Verification Standard"
(docs/requirements/EMBIZ_BRD.md): location, SKILL.md naming, YAML
frontmatter, name/directory match, description quality, naming conventions,
required sections, rationalizations table, red flags, conciseness, and no
empty scripts/ directories.

Contract checks (--contracts, also run by default) verify the compiled
roster: 18 agents, required fields, agent_id/filename match, resolvable
handoff targets, and index consistency.

Exit code 0 = all PASS; 1 = any failure.
"""

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILLS = REPO / "skills"
CONTRACTS = REPO / "agents" / "contracts"

REQUIRED_SECTIONS = [
    "Purpose", "When to Use", "Required Inputs",
    "Repository Inspection Workflow", "Architecture Inspection Workflow",
    "Agent Responsibility Separation Rules", "Implementation Workflow",
    "Verification Workflow", "Evidence Requirements",
    "Common Rationalizations", "Red Flags", "Final Report Format",
]

CONTRACT_FIELDS = [
    "agent_id", "primary_mission", "inputs", "outputs", "allowed_actions",
    "required_repositories", "quality_gates", "required_slack_events",
    "approval_rules", "rejection_rules", "handoff_targets",
    "performance_metrics",
]

MAX_SKILL_LINES = 200  # "The primary SKILL.md remains concise"

failures = []


def check(cond: bool, label: str):
    print(f"  {'PASS' if cond else 'FAIL'}  {label}")
    if not cond:
        failures.append(label)


def parse_frontmatter(text: str):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None
    fm = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip()
    return fm


def validate_skill(skill_dir: Path):
    print(f"skill: {skill_dir.name}")
    check(re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", skill_dir.name) is not None,
          "directory name is lowercase hyphen-separated")
    entry = skill_dir / "SKILL.md"
    check(entry.exists(), "primary file is named SKILL.md")
    others = [p for p in skill_dir.rglob("*") if p.is_file() and p != entry]
    for p in others:
        check(re.fullmatch(r"[a-z0-9][a-z0-9.-]*", p.name) is not None,
              f"supporting file lowercase hyphen-separated: {p.name}")
    for d in [p for p in skill_dir.rglob("*") if p.is_dir()]:
        check(any(d.iterdir()), f"optional directory not empty: {d.name}")
    if not entry.exists():
        return
    text = entry.read_text(encoding="utf-8")
    fm = parse_frontmatter(text)
    check(fm is not None, "YAML frontmatter is valid")
    if fm:
        check(fm.get("name") == skill_dir.name,
              "frontmatter name matches directory name")
        desc = fm.get("description", "")
        check(len(desc) > 40 and re.search(r"\buse\b", desc, re.I) is not None,
              "description explains what the skill does and when to use it")
    body = text.split("---", 2)[-1]
    for section in REQUIRED_SECTIONS:
        check(re.search(rf"^## {re.escape(section)}$", body, re.M) is not None,
              f"required section present: {section}")
    check("| Rationalization |" in body and "|---|" in body,
          "rationalizations table present")
    check(len(text.splitlines()) <= MAX_SKILL_LINES,
          f"SKILL.md concise (<= {MAX_SKILL_LINES} lines)")


def validate_skills():
    check(SKILLS.is_dir(), "skills/ directory exists")
    check((SKILLS / "references").is_dir(), "shared references under skills/references/")
    for skill_dir in sorted(p for p in SKILLS.iterdir() if p.is_dir()):
        if skill_dir.name == "references":
            continue
        validate_skill(skill_dir)


def validate_contracts():
    print("contracts:")
    index_path = CONTRACTS / "index.json"
    check(index_path.exists(), "agents/contracts/index.json exists")
    if not index_path.exists():
        return
    index = json.loads(index_path.read_text(encoding="utf-8"))
    agents = index.get("agents", [])
    check(len(agents) == 18, f"18 roster agents compiled (found {len(agents)})")
    ids = set()
    for entry in agents:
        path = REPO / entry["contract"]
        check(path.exists(), f"contract file exists: {entry['agent_id']}")
        if not path.exists():
            continue
        c = json.loads(path.read_text(encoding="utf-8"))
        ids.add(c["agent_id"])
        check(c["agent_id"] == path.stem, f"agent_id matches filename: {path.name}")
        for field in CONTRACT_FIELDS:
            check(bool(c.get(field)), f"{c['agent_id']}: field populated: {field}")
    names = {i.capitalize() for i in ids} | {"Mckenna"}  # roster spellings
    for entry in agents:
        c = json.loads((REPO / entry["contract"]).read_text(encoding="utf-8"))
        unresolved = [t for t in c["handoff_targets"] if t not in names]
        check(not unresolved,
              f"{c['agent_id']}: handoff targets resolve ({unresolved or 'ok'})")


def main():
    args = set(sys.argv[1:])
    if not args or "--skills" in args:
        validate_skills()
    if not args or "--contracts" in args:
        validate_contracts()
    print(f"\n{'ALL CHECKS PASSED' if not failures else f'{len(failures)} FAILURE(S)'}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
