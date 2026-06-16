Read this local source bundle and create complete EMBIZ-specific operational doctrine.

Repository: phuryn-pm-skills
Local source: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/phuryn-pm-skills
Bundle: /root/embroidery_business_agent_system/directives/repo_adapted_embiz_doctrine/_prompts/phuryn-pm-skills_SOURCE_BUNDLE.md

EMBIZ context:
- Root: /root/embroidery_business_agent_system
- Local corpus: /root/web-archive/ai_agents_skills_library
- OpenClaw: /root/.openclaw/workspace
- Agent bus: /usr/local/bin/agent-msg
- Slack mirror outbound-only; no secrets.
- Human approval required before customer contact.
- Human approval required before digitizing.
- Never claim SVG/PES/DST/EXP/INF/BMP exists unless file exists on disk.
- Named agents: Maya, Madeline, Morgan, Mila, Melanie, Mackenzie, Marina, Monica, Meredith, Mckenna, Margaret, Miranda, Michaela, Maeve, Matilda, Melody, Miriam, Mallory

You must adapt this repo into EMBIZ doctrine, not summarize it.

Write these sections:
# phuryn-pm-skills EMBIZ ADAPTED DOCTRINE
## Source Material Read
## What This Repo Contributes To EMBIZ
## EMBIZ-Specific Adaptation
## Assigned Agent Ownership
## Local Skill / Knowledge Library Integration
## Runtime Rules
## Required Files / Configs
## Commands / Checks
## Security Restrictions
## Verification Checklist
## Build Tasks
## What Not To Use
## Integration Status

Now use this source bundle:


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/phuryn-pm-skills/validate_plugins.py =====

#!/usr/bin/env python3
"""
Plugin Collection Validator
===========================
Validates all plugins in the collection against the Claude Code plugin spec:
- plugin.json manifest: required fields, author attribution, keywords
- Skills: YAML frontmatter (name must match directory, description required)
- Commands: YAML frontmatter (description and argument-hint required)
- Cross-references: commands referencing skills that exist in the same plugin
- README: exists and has expected sections

Based on:
- Anthropic plugin-dev README (https://github.com/anthropics/claude-code/tree/main/plugins/plugin-dev)
- agentskills.io specification
- Claude Code plugins reference (https://code.claude.com/docs/en/plugins-reference)

Author: Paweł Huryn — The Product Compass Newsletter (https://www.productcompass.pm)
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import Optional


# ─── Configuration ───────────────────────────────────────────────────────────

# Required plugin.json fields per spec
REQUIRED_MANIFEST_FIELDS = ["name", "version", "description"]
RECOMMENDED_MANIFEST_FIELDS = ["author", "keywords", "homepage", "license"]
REQUIRED_AUTHOR_FIELDS = ["name", "email"]
RECOMMENDED_AUTHOR_FIELDS = ["url"]

# Required skill frontmatter fields
REQUIRED_SKILL_FIELDS = ["name", "description"]

# Required command frontmatter fields
REQUIRED_COMMAND_FIELDS = ["description"]
RECOMMENDED_COMMAND_FIELDS = ["argument-hint"]

# Expected README sections (case-insensitive substring match)
EXPECTED_README_SECTIONS = ["overview", "install", "skill", "command"]


# ─── ANSI Colors ─────────────────────────────────────────────────────────────

class C:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"


# ─── Helpers ─────────────────────────────────────────────────────────────────

def parse_yaml_frontmatter(content: str) -> Optional[dict]:
    """Extract YAML frontmatter from a markdown file (between --- markers)."""
    if not content.startswith("---"):
        return None
    end = content.find("---", 3)
    if end == -1:
        return None
    fm_text = content[3:end].strip()
    # Simple YAML parser for flat key-value pairs
    result = {}
    for line in fm_text.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.match(r'^(\S+):\s*(.+)$', line)
        if match:
            key = match.group(1)
            value = match.group(2).strip().strip('"').strip("'")
            result[key] = value
    return result


def count_words(content: str) -> int:
    """Count words in markdown content (excluding frontmatter)."""
    # Strip frontmatter
    if content.startswith("---"):
        end = content.find("---", 3)
        if end != -1:
            content = content[end + 3:]
    return len(content.split())


# ─── Validators ──────────────────────────────────────────────────────────────

class ValidationResult:
    def __init__(self):
        self.errors: list[str] = []      # Must fix
        self.warnings: list[str] = []    # Should fix
        self.info: list[str] = []        # FYI

    def error(self, msg: str):
        self.errors.append(msg)

    def warn(self, msg: str):
        self.warnings.append(msg)

    def note(self, msg: str):
        self.info.append(msg)

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0


def validate_manifest(plugin_dir: str) -> ValidationResult:
    """Validate plugin.json manifest."""
    result = ValidationResult()
    pj_path = os.path.join(plugin_dir, ".claude-plugin", "plugin.json")

    if not os.path.isfile(pj_path):
        result.error("Missing .claude-plugin/plugin.json")
        return result

    try:
        with open(pj_path, "r") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        result.error(f"Invalid JSON in plugin.json: {e}")
        return result

    # Required fields
    for field in REQUIRED_MANIFEST_FIELDS:
        if field not in data or not data[field]:
            result.error(f"Missing required field: {field}")

    # Name must match directory name
    dir_name = os.path.basename(plugin_dir)
    if data.get("name") and data["name"] != dir_name:
        result.error(f"Name mismatch: plugin.json says '{data['name']}' but directory is '{dir_name}'")

    # Version format
    version = data.get("version", "")
    if version and not re.match(r'^\d+\.\d+\.\d+$', version):
        result.warn(f"Version '{version}' doesn't follow semver (x.y.z)")

    # Recommended fields
    for field in RECOMMENDED_MANIFEST_FIELDS:
        if field not in data:
            result.warn(f"Missing recommended field: {field}")

    # Author validation
    author = data.get("author")
    if isinstance(author, dict):
        for field in REQUIRED_AUTHOR_FIELDS:
            if field not in author or not author[field]:
                result.warn(f"Missing author.{field}")
        for field in RECOMMENDED_AUTHOR_FIELDS:
            if field not in author:
                result.note(f"Missing author.{field}")
    elif author is not None:
        result.warn("Author should be an object with name, email, url fields")

    # Keywords validation
    keywords = data.get("keywords", [])
    if not keywords:
        result.warn("No keywords defined")
    elif not isinstance(keywords, list):
        result.error("Keywords must be an array")

    # Description length check
    desc = data.get("description", "")
    if desc and len(desc) < 20:
        result.warn(f"Description is very short ({len(desc)} chars)")

    result.note(f"Version: {version}")
    result.note(f"Keywords: {len(keywords) if isinstance(keywords, list) else 0}")

    return result



===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/phuryn-pm-skills/.claude-plugin/marketplace.json =====

{
  "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
  "name": "pm-skills",
  "version": "2.0.0",
  "description": "Structured AI workflows for better product decisions. 68 domain-specific skills and 42 chained workflows across 9 PM plugins — from discovery to strategy, execution, launch, growth, and shipping AI-built software.",
  "owner": {
    "name": "Paweł Huryn",
    "email": "pawel@productcompass.pm",
    "url": "https://www.productcompass.pm"
  },
  "plugins": [
    {
      "name": "pm-product-discovery",
      "description": "Product discovery skills for PMs: ideation, experiments, assumption testing, feature prioritization, and customer interview synthesis.",
      "source": "./pm-product-discovery",
      "category": "product-management"
    },
    {
      "name": "pm-product-strategy",
      "description": "Product strategy skills for PMs: vision, strategy canvas, value propositions, lean canvas, business model canvas, SWOT, PESTLE, Ansoff Matrix, Porter's Five Forces, and monetization.",
      "source": "./pm-product-strategy",
      "category": "product-management"
    },
    {
      "name": "pm-execution",
      "description": "Execution and product management skills: PRDs, OKRs, roadmaps, sprints, pre-mortems, stakeholder maps, user stories, prioritization frameworks, and more.",
      "source": "./pm-execution",
      "category": "product-management"
    },
    {
      "name": "pm-market-research",
      "description": "Market research skills for PMs: user personas, market segmentation, sentiment analysis, and competitive analysis.",
      "source": "./pm-market-research",
      "category": "product-management"
    },
    {
      "name": "pm-data-analytics",
      "description": "Data analytics skills for PMs: SQL query generation and cohort analysis. Analyze user data, generate queries, and identify retention patterns.",
      "source": "./pm-data-analytics",
      "category": "product-management"
    },
    {
      "name": "pm-go-to-market",
      "description": "Go-to-market skills for PMs: GTM strategy, growth loops, GTM motions, beachhead segments, and ideal customer profiles.",
      "source": "./pm-go-to-market",
      "category": "product-management"
    },
    {
      "name": "pm-marketing-growth",
      "description": "Product marketing and growth skills: marketing ideas, value proposition statements, North Star metrics, product naming, and positioning.",
      "source": "./pm-marketing-growth",
      "category": "product-management"
    },
    {
      "name": "pm-toolkit",
      "description": "PM utility skills: resume review, NDA drafting, privacy policy generation, and grammar/flow checking. Essential tools for product managers beyond core product work.",
      "source": "./pm-toolkit",
      "category": "product-management"
    },
    {
      "name": "pm-ai-shipping",
      "description": "AI Shipping Kit — for PMs and founders accountable for AI-built code. Document a vibe-coded app, audit it for intended-vs-implemented security gaps and performance issues, and produce a reviewer-ready shipping packet.",
      "source": "./pm-ai-shipping",
      "category": "product-management"
    }
  ]
}


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/phuryn-pm-skills/pm-ai-shipping/.claude-plugin/plugin.json =====

{
  "name": "pm-ai-shipping",
  "version": "2.0.0",
  "description": "AI Shipping Kit — for PMs and founders accountable for AI-built code. Document a vibe-coded app, audit it for intended-vs-implemented security gaps and performance issues, and produce a reviewer-ready shipping packet.",
  "author": {
    "name": "Paweł Huryn",
    "email": "pawel@productcompass.pm",
    "url": "https://www.productcompass.pm"
  },
  "keywords": [
    "product-management",
    "ai-shipping",
    "vibe-coding",
    "security-audit",
    "performance-audit",
    "code-review",
    "documentation",
    "owasp",
    "shipping"
  ],
  "homepage": "https://www.productcompass.pm",
  "license": "MIT"
}


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/phuryn-pm-skills/pm-data-analytics/.claude-plugin/plugin.json =====

{
  "name": "pm-data-analytics",
  "version": "2.0.0",
  "description": "Data analytics skills for PMs: SQL query generation and cohort analysis. Analyze user data, generate queries, and identify retention patterns.",
  "author": {
    "name": "Paweł Huryn",
    "email": "pawel@productcompass.pm",
    "url": "https://www.productcompass.pm"
  },
  "keywords": [
    "product-management",
    "data-analytics",
    "sql",
    "cohort-analysis",
    "retention"
  ],
  "homepage": "https://www.productcompass.pm",
  "license": "MIT"
}


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/phuryn-pm-skills/pm-execution/.claude-plugin/plugin.json =====

{
  "name": "pm-execution",
  "version": "2.0.0",
  "description": "Execution and product management skills: PRDs, OKRs, roadmaps, sprints, pre-mortems, stakeholder maps, user stories, prioritization frameworks, and more.",
  "author": {
    "name": "Paweł Huryn",
    "email": "pawel@productcompass.pm",
    "url": "https://www.productcompass.pm"
  },
  "keywords": [
    "product-management",
    "execution",
    "prd",
    "okrs",
    "roadmap",
    "sprint",
    "pre-mortem",
    "user-stories",
    "backlog",
    "prioritization",
    "agile"
  ],
  "homepage": "https://www.productcompass.pm",
  "license": "MIT"
}


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/phuryn-pm-skills/pm-go-to-market/.claude-plugin/plugin.json =====

{
  "name": "pm-go-to-market",
  "version": "2.0.0",
  "description": "Go-to-market skills for PMs: GTM strategy, growth loops, GTM motions, beachhead segments, and ideal customer profiles.",
  "author": {
    "name": "Paweł Huryn",
    "email": "pawel@productcompass.pm",
    "url": "https://www.productcompass.pm"
  },
  "keywords": [
    "product-management",
    "go-to-market",
    "gtm",
    "growth-loops",
    "icp",
    "launch"
  ],
  "homepage": "https://www.productcompass.pm",
  "license": "MIT"
}


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/phuryn-pm-skills/pm-market-research/.claude-plugin/plugin.json =====

{
  "name": "pm-market-research",
  "version": "2.0.0",
  "description": "Market research skills for PMs: user personas, market segmentation, sentiment analysis, and competitive analysis.",
  "author": {
    "name": "Paweł Huryn",
    "email": "pawel@productcompass.pm",
    "url": "https://www.productcompass.pm"
  },
  "keywords": [
    "product-management",
    "market-research",
    "personas",
    "segmentation",
    "competitor-analysis",
    "market-sizing",
    "TAM",
    "SAM",
    "SOM"
  ],
  "homepage": "https://www.productcompass.pm",
  "license": "MIT"
}


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/phuryn-pm-skills/pm-marketing-growth/.claude-plugin/plugin.json =====

{
  "name": "pm-marketing-growth",
  "version": "2.0.0",
  "description": "Product marketing and growth skills: marketing ideas, value proposition statements, North Star metrics, product naming, and positioning.",
  "author": {
    "name": "Paweł Huryn",
    "email": "pawel@productcompass.pm",
    "url": "https://www.productcompass.pm"
  },
  "keywords": [
    "product-management",
    "marketing",
    "growth",
    "north-star",
    "positioning",
    "branding"
  ],
  "homepage": "https://www.productcompass.pm",
  "license": "MIT"
}


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/phuryn-pm-skills/pm-product-discovery/.claude-plugin/plugin.json =====

{
  "name": "pm-product-discovery",
  "version": "2.0.0",
  "description": "Product discovery skills for PMs: ideation, experiments, assumption testing, feature prioritization, and customer interview synthesis.",
  "author": {
    "name": "Paweł Huryn",
    "email": "pawel@productcompass.pm",
    "url": "https://www.productcompass.pm"
  },
  "keywords": [
    "product-management",
    "discovery",
    "ideation",
    "experiments",
    "assumptions"
  ],
  "homepage": "https://www.productcompass.pm",
  "license": "MIT"
}


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/phuryn-pm-skills/pm-product-strategy/.claude-plugin/plugin.json =====

{
  "name": "pm-product-strategy",
  "version": "2.0.0",
  "description": "Product strategy skills for PMs: vision, strategy canvas, value propositions, lean canvas, business model canvas, SWOT, PESTLE, Ansoff Matrix, Porter's Five Forces, and monetization.",
  "author": {
    "name": "Paweł Huryn",
    "email": "pawel@productcompass.pm",
    "url": "https://www.productcompass.pm"
  },
  "keywords": [
    "product-management",
    "strategy",
    "vision",
    "business-model",
    "swot",
    "competitive-analysis"
  ],
  "homepage": "https://www.productcompass.pm",
  "license": "MIT"
}


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/phuryn-pm-skills/pm-toolkit/.claude-plugin/plugin.json =====

{
  "name": "pm-toolkit",
  "version": "2.0.0",
  "description": "PM utility skills: resume review, NDA drafting, privacy policy generation, and grammar/flow checking. Essential tools for product managers beyond core product work.",
  "author": {
    "name": "Paweł Huryn",
    "email": "pawel@productcompass.pm",
    "url": "https://www.productcompass.pm"
  },
  "keywords": [
    "product-management",
    "resume",
    "legal",
    "nda",
    "privacy-policy",
    "copywriting"
  ],
  "homepage": "https://www.productcompass.pm",
  "license": "MIT"
}


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/phuryn-pm-skills/AGENTS.md =====

# AGENTS.md

All agent guidance for this repository lives in **[CLAUDE.md](CLAUDE.md)** — that is the single source of truth.

Please read [CLAUDE.md](CLAUDE.md) before making changes. This file exists only so non-Claude agents that look for `AGENTS.md` are pointed to the same instructions; do not duplicate guidance here.


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/phuryn-pm-skills/CLAUDE.md =====

# CLAUDE.md

Guidance for AI agents (Claude Code, Cowork, and others) working in this repository. This file is the single source of truth for how the project is structured and maintained.

## Project Overview

**PM Skills** (`phuryn/pm-skills`) — a marketplace of **9 independent plugins** (68 skills, 42 commands) that bring structured product-management workflows to AI coding assistants. Built for Claude Code and Claude Cowork; the skills are also compatible with other agents (Gemini CLI, Cursor, Codex CLI).

Owner: Paweł Huryn — pawel@productcompass.pm — https://www.productcompass.pm

## Repo Structure

```
pm-skills/                           <- repo root
├── .claude-plugin/marketplace.json  <- root marketplace manifest (lists all 9 plugins)
├── .docs/images/                    <- images used by README (webp, gif)
├── .gitattributes
├── .gitignore
├── CLAUDE.md                        <- this file (agent guidance, single source of truth)
├── AGENTS.md                        <- pointer to CLAUDE.md (for non-Claude agents)
├── CONTRIBUTING.md                  <- contributor guidelines
├── README.md                        <- public documentation (GitHub)
├── LICENSE                          <- MIT
├── validate_plugins.py              <- plugin validator
└── pm-{name}/                       <- 9 plugin directories
    ├── .claude-plugin/plugin.json   <- per-plugin manifest
    ├── skills/{skill}/SKILL.md      <- one folder per skill
    ├── commands/{command}.md        <- one file per command
    └── README.md                    <- per-plugin documentation
```

### The 9 plugins

| Plugin | Focus |
|--------|-------|
| `pm-product-discovery` | Ideation, experiments, assumption testing, prioritization, interview synthesis |
| `pm-product-strategy` | Vision, strategy/lean/business-model canvas, SWOT, PESTLE, Ansoff, Porter, monetization |
| `pm-execution` | PRDs, OKRs, roadmaps, sprints, pre-mortems, stakeholder maps, user stories, red-teaming |
| `pm-market-research` | Personas, segmentation, sentiment analysis, competitive analysis, market sizing |
| `pm-data-analytics` | SQL query generation, cohort/retention analysis |
| `pm-go-to-market` | GTM strategy, growth loops, motions, beachhead segments, ICPs |
| `pm-marketing-growth` | Marketing ideas, value-prop statements, North Star metrics, naming, positioning |
| `pm-toolkit` | Resume review, NDA drafting, privacy policy, grammar/flow checking |
| `pm-ai-shipping` | AI Shipping Kit: document a vibe-coded app, map test coverage, audit security/performance against intended behavior, compile a shipping packet |

## Key Design Rules

- **Skills = nouns/concepts.** Frameworks and analytical knowledge Claude auto-loads when the topic matches (`lean-canvas`, `pre-mortem`, `market-sizing`).
- **Commands = verbs.** User-triggered workflows that chain one or more skills (`/write-prd`, `/discover`, `/plan-launch`).
- **No cross-plugin references.** Commands suggest follow-ups in natural language only ("Want me to design growth loops?"). Never hard-reference a command from another plugin — plugins install independently, so a hard reference can break.
- **Intra-plugin "Uses" references are fine** — skills and commands in the same plugin always ship together.
- Commands use a single `$ARGUMENTS` placeholder. Skills need no placeholders (they read context from the conversation).
- **Frontmatter required:** Skills need `name` + `description`; commands need `description` + `argument-hint`.
- A skill's `name` **must match its directory name**.
- Skills can be force-loaded with `/plugin-name:skill-name` or `/skill-name`.
- Keep frontmatter lean (always loaded); put detail in the SKILL.md body (loaded when triggered) — progressive disclosure.

## What's Visible Where

| Location | Visible in | Notes |
|----------|-----------|-------|
| `marketplace.json` → `description` | Cowork marketplace browser, Claude Code | One-liner for the whole marketplace |
| `plugin.json` → `description` | Cowork plugin list, Claude Code | Per-plugin summary; concise and functional |
| `SKILL.md` frontmatter → `description` | Cowork skill list, Claude auto-loading | Include trigger phrases so Claude loads the skill at the right time |
| Command frontmatter → `description` + `argument-hint` | Cowork and Claude Code (typing `/`) | Short and actionable |
| `README.md` (repo root) | GitHub only | Full docs; not loaded by Claude at runtime |

Descriptions in `plugin.json` and the repo `README.md` should stay aligned (identical text).

## Versioning

- All versions are currently **2.0.0** — `marketplace.json` and all 9 `plugin.json` files.
- **Keep every version in sync.** There is no independent per-plugin versioning.
- Bump any `plugin.json` → also bump `marketplace.json`, and vice-versa (bump all 9 to match).

## Article Links in Skills (Further Reading)

- Mapped skills end with a `### Further Reading` section linking to relevant Product Compass articles.
- **Tone must stay neutral** — no promotional language, no CTAs, no "subscribe"/"check out". Just the article title and URL.
- Claude surfaces these links based on conversational relevance, not on every response.
- Posts whose title contains "Masterclass" or "Course" are video courses — tag them `(video course)`.

## Operational Procedures

### After any skill/command change
1. Run `python3 validate_plugins.py` from the repo root to check all plugins.
2. If skills/commands were added or removed, update the counts in `README.md`.
3. If totals changed, update the count in the `marketplace.json` description.
4. Bump versions across all manifests (see Versioning).

### After a description change
- A `plugin.json` description changed → check whether `README.md` needs the same edit (they stay aligned).
- A `SKILL.md` description changed → no other sync needed (it's the single source for that skill).

## Validation

`validate_plugins.py` checks: `plugin.json` required fields / name match / semver / author / keywords; skill frontmatter and name-matches-directory; command frontmatter (`description` + `argument-hint`); README presence; and intra-plugin command→skill references.

```
python3 validate_plugins.py
```

## What to Suggest After Completing Work

Offer relevant follow-ups:
- After structural changes: "Want me to run the validator?"
- After adding/removing skills or commands: "Should I update the counts in README.md and marketplace.json?"
- After editing descriptions: "Should I sync this to README.md / plugin.json?"
- After any repo change: "Want me to bump the version?"


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/phuryn-pm-skills/CONTRIBUTING.md =====

# Contributing

PM Skills Marketplace is maintained by [Paweł Huryn](https://www.productcompass.pm) (pawel@productcompass.pm). Contributions are welcome — whether it's a bug fix, a typo, or a new skill idea.

## How to Contribute

- **Bugs and small fixes** — open a PR directly.
- **New skills, commands, or larger changes** — open an issue first so we can discuss the approach.

## Guidelines

- Keep PRs focused — one change per PR.
- Follow existing patterns: skills are nouns (domain knowledge), commands are verbs (workflows).
- Every skill needs frontmatter with `name` and `description`. Every command needs `description` and `argument-hint`.
- Skill `name` must match its directory name.
- No cross-plugin references in commands. Suggest follow-ups in natural language only.
- Every contributor will be listed publicly.
- Run the validator before submitting: `python3 validate_plugins.py`

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/phuryn-pm-skills/README.md =====

![GitHub stars](https://img.shields.io/github/stars/phuryn/pm-skills)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](https://github.com/phuryn/pm-skills/blob/main/LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen?style=flat-square)](https://github.com/phuryn/pm-skills/blob/main/CONTRIBUTING.md)
[![Companion: pm-skills](https://img.shields.io/badge/companion-pm--brain-blue)](https://github.com/phuryn/pm-brain)

# PM Skills Marketplace: The AI Operating System for Better Product Decisions

> 68 PM skills and 42 chained workflows across 9 plugins. Claude Code, Cowork, and more. From discovery to strategy, execution, launch, growth, and shipping AI-built code. 

![PM Skills marketplace: skills, commands, and all 9 plugins at a glance](.docs/images/plugins.png)

Designed for Claude Code and Cowork. Skills compatible with other AI assistants.

## Start Here

New idea? → `/discover`  
Need strategic clarity? → `/strategy`  
Writing a PRD? → `/write-prd`  
Planning a launch? → `/plan-launch`  
Defining metrics? → `/north-star`

If this project helps you, ⭐ the repo.

## Why PM Skills Marketplace?

Generic AI gives you text. PM Skills Marketplace gives you structure.

Each skill encodes a proven PM framework — discovery, assumption mapping, prioritization, strategy — and walks you through it step by step. You get the rigor of Teresa Torres, Marty Cagan, and Alberto Savoia built into your daily workflow, not sitting on a bookshelf.

The result: better product decisions, not just faster documents.

## How It Works (Skills, Commands, Plugins)

![Example prompts: a skill and two commands (/write-prd, /ship-check) in action](.docs/images/examples.png)

**Skills** are the building blocks of the marketplace. Each skill gives Claude domain knowledge, analytical frameworks, or a guided workflow for a specific PM task. Some skills also work as reusable foundations that multiple commands share. 

Skills are loaded automatically when relevant to the conversation — no explicit invocation needed. If needed (e.g., prioritizing skills over general knowledge), you can **force loading skills** with `/plugin-name:skill-name` or `/skill-name` (Claude will add the prefix).

**Commands** are user-triggered workflows invoked with `/command-name`. They chain one or more skills into an end-to-end process. For example, `/discover` chains four skills together: brainstorm-ideas → identify-assumptions → prioritize-assumptions → brainstorm-experiments.

**Plugins** group related skills and commands into installable packages. Each plugin covers a PM domain — discovery, strategy, execution, and so on. Installing the marketplace gives you all 9 plugins at once.

Commands use skills. Some skills serve multiple commands. Some skills (like `prioritization-frameworks` or `opportunity-solution-tree`) are standalone references that Claude draws on whenever relevant — no command needed.

Commands are designed to flow into each other, matching the PM workflow. After any command completes, it suggests relevant next commands — just follow the prompts.

## Installation

### Claude Cowork (recommended for non-developers)

1. Open **Customize** (bottom-left)
2. Go to **Browse plugins** → **Personal** → **+**
3. Select **Add marketplace from GitHub**
4. Enter: `phuryn/pm-skills`

All 9 plugins install automatically. You get both commands (`/discover`, `/strategy`, etc.) and skills.

![Installing PM Skills in Claude Cowork](.docs/images/pm-skills-install.gif)

### Claude Code (CLI)

```bash
# Step 1: Add the marketplace
claude plugin marketplace add phuryn/pm-skills

# Step 2: Install individual plugins
claude plugin install pm-toolkit@pm-skills
claude plugin install pm-product-strategy@pm-skills
claude plugin install pm-product-discovery@pm-skills 
claude plugin install pm-market-research@pm-skills 
claude plugin install pm-data-analytics@pm-skills
claude plugin install pm-marketing-growth@pm-skills
claude plugin install pm-go-to-market@pm-skills
claude plugin install pm-execution@pm-skills
claude plugin install pm-ai-shipping@pm-skills
```

### Codex CLI (OpenAI)

Codex reads the same plugin marketplace file as Claude Code, so you can install PM Skills natively — no conversion or file-copying needed:

```bash
# Step 1: Add the marketplace
codex plugin marketplace add phuryn/pm-skills

# Step 2: Install the plugins you want
codex plugin add pm-toolkit@pm-skills
codex plugin add pm-product-strategy@pm-skills
codex plugin add pm-product-discovery@pm-skills
codex plugin add pm-market-research@pm-skills
codex plugin add pm-data-analytics@pm-skills
codex plugin add pm-marketing-growth@pm-skills
codex plugin add pm-go-to-market@pm-skills
codex plugin add pm-execution@pm-skills
codex plugin add pm-ai-shipping@pm-skills
```

**What you get:** every skill (the PM frameworks), available to Codex and invocable by name. Install whole plugins rather than cherry-picking individual skills — a workflow usually relies on several skills that ship together.

**What's different from Claude Code:** the `/slash` commands (`/discover`, `/write-prd`, …) install but don't run as Codex slash commands — Codex plugins don't expose commands. To run a workflow, just describe the steps in plain language, for example:

> Run product discovery on *[your idea]*: brainstorm options, map assumptions, prioritize the risky ones, then design experiments — pause between each step.

**Optional — let Codex turn the workflows into skills.** Because the command files ship inside each installed plugin, you can ask Codex to convert the ones you use most:

> Read the command files in the pm-execution plugin and create equivalent Codex skills for the workflows I use most often.

This is a best-effort, model-driven conversion (some Claude-specific command syntax won't translate), but it's a quick way to get the guided workflows on Codex without leaving the CLI.

### Other AI assistants (skills only)

The `skills/*/SKILL.md` files follow the universal skill format and work with any tool that reads it. Commands (`/slash-commands`) are Claude-specific.

| Tool | How to use | What works |
|------|-----------|------------|
| **Gemini CLI** | Copy skill folders to `.gemini/skills/` | Skills only |
| **OpenCode** | Copy skill folders to `.opencode/skills/` | Skills only |
| **Cursor** | Copy skill folders to `.cursor/skills/` | Skills only |
| **Kiro** | Copy skill folders to `.kiro/skills/` | Skills only |

```bash
# Example: copy all skills for OpenCode (project-level)
for plugin in pm-*/; do
  mkdir -p .opencode/skills/
  cp -r "$plugin/skills/"* .opencode/skills/ 2>/dev/null
done

# Example: copy all skills for Gemini CLI (global)
for plugin in pm-*/; do
  cp -r "$plugin/skills/"* ~/.gemini/skills/ 2>/dev/null
done
```

---

## Available Plugins

<details>
<summary><strong>1. pm-product-discovery</strong> — Ideation, experiments, assumption testing, OSTs, interviews (13 skills, 5 commands)</summary>

**Skills (13):**

- `brainstorm-ideas-existing` — Multi-perspective ideation for existing products (PM, Designer, Engineer)
- `brainstorm-ideas-new` — Ideation for new products in initial discovery
- `brainstorm-experiments-existing` — Design experiments to test assumptions for existing products
- `brainstorm-experiments-new` — Design lean startup pretotypes for new products (Alberto Savoia)
- `identify-assumptions-existing` — Identify risky assumptions across Value, Usability, Viability, and Feasibility
- `identify-assumptions-new` — Identify risky assumptions across 8 risk categories including Go-to-Market, Strategy, and Team
- `prioritize-assumptions` — Prioritize assumptions using an Impact × Risk matrix with experiment suggestions
- `prioritize-features` — Prioritize a feature backlog based on impact, effort, risk, and strategic alignment
- `analyze-feature-requests` — Analyze and categorize customer feature requests by theme and strategic fit
- `opportunity-solution-tree` — Build an Opportunity Solution Tree (Teresa Torres) — outcome → opportunities → solutions → experiments
- `interview-script` — Create a structured customer interview script with JTBD probing questions
- `summarize-interview` — Summarize an interview transcript into JTBD, satisfaction signals, and action items
- `metrics-dashboard` — Design a product metrics dashboard with North Star, input metrics, and alert thresholds

**Commands (5):**

- `/discover` — Full discovery cycle: ideation → assumption mapping → prioritization → experiment design
- `/brainstorm` — Multi-perspective ideation (`ideas|experiments` × `existing|new`)
- `/triage-requests` — Analyze and prioritize a batch of feature requests
- `/interview` — Prepare an interview script or summarize a transcript (`prep|summarize`)
- `/setup-metrics` — Design a product metrics dashboard

**Examples:**

Skills:
- `What are the riskiest assumptions for our AI writing assistant idea?`
- `Help me build an Opportunity Solution Tree for improving user activation`
- `Prioritize these 12 feature requests from our enterprise customers [attach CSV]`

Commands:
- `/discover AI-powered meeting summarizer for remote teams`
- `/brainstorm experiments existing — We need to reduce churn in our onboarding flow`
- `/interview prep — We're interviewing enterprise buyers about their procurement workflow`

</details>

<details>


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/phuryn-pm-skills/pm-ai-shipping/README.md =====

# pm-ai-shipping — AI Shipping Kit

For PMs and founders accountable for AI-built code. Document a vibe-coded app, audit it for intended-vs-implemented security gaps and performance issues, and produce a reviewer-ready shipping packet.

## Overview

AI agents write code fast but leave no record of *intent* — what the system should do, who may do what, where the secrets live. Without that record, no human and no auditing agent can tell whether the code is safe to ship. This kit restores reviewability: it documents the system, then audits the gap between what the docs say and what the code does — the class of bug generic scanners miss because they have no model of intent.

Start with `/ship-check` for the full sequence, or run a single stage with the specialist commands.

## Install

Install from the [pm-skills marketplace](https://github.com/phuryn/pm-skills) and enable the `pm-ai-shipping` plugin. Each command can be triggered with `/pm-ai-shipping:<command>` or its short `/<command>` form; skills auto-load when the topic matches.

## Skills (2)

- **shipping-artifacts** — The durable documentation set that makes an AI-built app reviewable: a core every app needs (architecture, user/permission flows, permissions, variables/secrets, test-coverage map) plus conditional docs added only when they apply (emails, cron, SEO, embedded agents/automation). Defines what each doc must capture and how a reviewer uses it.
- **intended-vs-implemented** — The method for finding the gap between what a system is documented to do and what the code actually does, with cited evidence on both sides and without hand-wavy findings.

## Commands (5)

- `/pm-ai-shipping:ship-check` — Turn a vibe-coded repo into a reviewer-ready shipping packet: document, wire agent context, run security and performance audits, map test coverage, and compile the results.
- `/pm-ai-shipping:document-app` — Reverse-engineer a codebase into the system documents reviewers and auditors need — a core set (architecture, flows, permissions, variables) plus conditional docs (emails, cron, SEO, automation) when they apply.
- `/pm-ai-shipping:derive-tests` — Turn documented intent into a test-coverage map: inventory the tests that exist today, separate them from proposed tests and unverified gaps, mark each unit / guarded-live / manual, and recommend a green-before-merge CI gate.
- `/pm-ai-shipping:security-audit-static` — Static security audit: map trust boundaries, cross-reference documented intent, self-refute every finding, and report only evidence-backed risks.
- `/pm-ai-shipping:performance-audit-static` — Static performance audit: find over-fetching, missing indexes, and caching opportunities, ranked by effort and impact.

## Author

Paweł Huryn — [The Product Compass Newsletter](https://www.productcompass.pm)

## License

MIT


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/phuryn-pm-skills/pm-ai-shipping/commands/derive-tests.md =====

---
description: Turn documented intent into a test-coverage map — inventory the tests that exist today, derive use-case cases from the system docs, separate existing coverage from proposed tests and unverified gaps, mark each unit / guarded-live / manual, and recommend a green-before-merge CI gate
argument-hint: "<repo path or area; defaults to the whole repository>"
---

# /derive-tests -- Turn Intent Into Tests

The docs say what the system *should* do. An audit finds where the code *doesn't*. Tests are what stop that gap from reopening after the next AI edit. This command reads the documented intent, turns each load-bearing rule into a concrete test case, sorts them into what to automate, what needs a guarded live run, and what stays manual — then recommends the CI gate that keeps `main` honest.

This produces a coverage map (`tests.md`) and concrete test cases, not a finished suite — you or the next agent implement the deterministic ones.

## Invocation

```
/derive-tests
/derive-tests the checkout flow
/derive-tests supabase/functions
```

## Prerequisite: documented intent

Tests are derived from the docs, so the docs come first. If `/documentation/*.md` is missing or thin, run `/document-app` (and `/derive-tests` reads `flows.md`, `permissions.md`, and `automation.md` most heavily). You cannot map coverage to rules you never wrote down — where intent is absent, say so rather than inventing rules to test.

## The workflow

### 1. Read the intent — and the tests that already exist

Read the applicable system docs (architecture, flows, permissions, variables, and any of emails, cron, seo, automation that exist). Apply the **shipping-artifacts** skill for what each doc should contain, and the **intended-vs-implemented** skill for the discipline of treating docs as claims to verify, not proof.

Then inventory the **existing test suite** — the test files, what they actually assert, and what runs in CI today. The map you produce must distinguish coverage that exists *now* from coverage you're *proposing*; skipping this step yields a falsely-green map that claims rules are pinned when nothing checks them. If there are no tests, say so plainly — that is itself a finding.

### 2. Extract the rules worth testing

Pull out the load-bearing, deterministic rules — the ones whose violation crosses a trust, data, money, tenant, or privacy boundary:

- authorization allow **and deny** cases (especially the boundary crossings in `flows.md` and the matrix in `permissions.md`),
- input validation and output encoding at each sink,
- idempotency of jobs and dedup keys,
- fail-closed defaults (error / timeout / cache-miss / flag paths that must deny, not allow),
- side-effect conditions (exactly when an email sends, a write commits, a paid action fires),
- public-data-only constraints on public or bot routes,
- the output-contract and tool-surface limits of any agent in `automation.md`.

Skip cosmetic behavior. A rule earns a test when getting it wrong harms someone other than the actor.

### 3. Build the coverage map

One row per use case: **rule → expected behavior (incl. the negative case) → evidence source (doc + code) → test type → status (existing / proposed / none)**. The status column is what keeps the map honest — mark a rule *existing* only when a test in the repo actually asserts it today.

Test types:

- **unit** — pure and deterministic, no external services.
- **integration (deterministic)** — exercises real wiring against a local or in-memory dependency (test DB, mocked provider) and runs the same way every time.
- **guarded live** — needs a real external DB, email provider, LLM, or third party. Runs only behind an explicit flag, never in the default CI run.
- **manual** — UI/visual or judgment calls. A reviewer checklist item, not an automated test.

**What CI must require:** the deterministic local set — unit plus deterministic integration tests, the ones that pass or fail the same way on every run with no live dependencies. Prefer **unit** where the decision logic can be isolated; reach for **integration** when the rule lives in the wiring (middleware, RLS, auth guards) and only a real-but-local dependency can exercise it. Guarded-live and manual rows never gate the default run.

When a rule can only be exercised live, you can extract its *decision* into a pure helper so the logic is unit-testable — but only as a **complement, not a replacement** for testing the real enforcement. The unit test proves the helper's logic; it does **not** prove the framework actually calls it. Wiring and policy enforcement (route middleware, DB row-level security, auth guards, provider config) still needs an integration or guarded-live check, or the helper becomes a policy shadow that passes while the real path is unprotected.

### 4. Propose the tests

For each rule you can pin with a deterministic automated test (unit or integration), write the case: name, arrange/act/assert intent, and the negative case it must reject. Group cases by the doc or flow they defend. Prefer the smallest test that pins the rule — one clear assertion per boundary beats a sprawling integration test that fails for ten reasons.

### 5. Recommend the CI gate

Recommend — don't silently install — a CI setup matched to the repo's stack and existing tooling:

- run the **deterministic local set on every pull request** (unit + any integration test that runs without live services),
- keep **guarded-live tests opt-in** (manual or scheduled, never blocking),
- **gate merges to `main` on green** via a required status check + branch protection.

Output the workflow file and the branch-protection setting as a clearly-labeled suggestion for the user to approve, not an applied change.

### 6. Report coverage and gaps

Write `tests.md` in three clearly separated sections:

- **Existing coverage** — rules a test in the repo pins *today* (from the Step 1 inventory).
- **Proposed tests** — the cases you're recommending but that don't exist yet, by type.
- **Gaps** — documented rules with **no verification at all**, ranked by what crossing them exposes.

The gaps are the backlog, and they are exactly where the next AI edit can silently break a boundary. Be honest that proposed ≠ existing: a rule isn't covered until a test actually asserts it.

## Output

```
Test Coverage: [scope]

| Use case | Rule (doc) | Expected behavior (+ deny case) | Evidence | Type | Status |
|----------|-----------|---------------------------------|----------|------|--------|
[status: existing / proposed / none]

### Existing coverage
[tests already in the repo, each tied to the rule it pins]

### Proposed tests
[grouped by flow/doc — name · assert · negative case · type]

### Recommended CI gate
[workflow snippet for the detected stack + "green-before-merge" branch-protection note]

### Gaps — documented but unverified
[rules with no test yet, ranked by what crossing them exposes]
```

Optionally write the coverage map to `/documentation/tests.md` and the full report to `/reports/test_plan_{timestamp}.md`.

## Notes

- This is the verification half of "documented == implemented": the audits find today's gap, these tests stop it from reopening tomorrow.
- Don't fabricate rules to manufacture coverage. If the docs are silent, the gap is in the docs — fix `/document-app` first.
- Don't wire external services into the default CI run; flaky live tests erode the green-before-merge gate until people start ignoring it.
- Covers test derivation only. For the gap audit itself use `/security-audit-static`; for the full document → audit → test → packet sequence use `/ship-check`.


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/phuryn-pm-skills/pm-ai-shipping/commands/document-app.md =====

---
description: Reverse-engineer an AI-built codebase into the system documents reviewers and auditors need — a core set (architecture, flows, permissions, variables) plus conditional docs (emails, cron, SEO, automation) when they apply
argument-hint: "<repo path or area; defaults to the whole repository>"
---

# /document-app -- Make the System Reviewable

Produce the durable documentation an AI-built app is missing: an honest map of what the system is, who can do what, and where the risk lives. These docs are the foundation every later audit compares the code against.

## Invocation

```
/document-app
/document-app supabase/functions
/document-app the backend
```

## Workflow

### Step 1: Scope

Audit **$ARGUMENTS**. If empty, document the whole repository, prioritizing backend code, auth, data access, background jobs, and anything that sends, schedules, or exposes data.

### Step 2: Reverse-Engineer the Docs

Apply the **shipping-artifacts** skill. Reading the code as the source of truth, produce the applicable documents in `/documentation/`.

**Core (always):**

- `architecture.md` — system overview, stack, auth flow, trust boundaries
- `flows.md` — the permission-relevant journeys: each protected step's authz check, the trust-boundary crossings, and the side effects each flow causes
- `permissions.md` — roles, scope derivation, resource × operation × role matrix, RLS vs. code-enforced checks
- `variables.md` — config & secrets mapped to risk and rotation

**Conditional (only if the capability exists — otherwise note its absence in one line):**

- `emails.md` — notification path, templates, retry/backoff, failure visibility
- `cron.md` — scheduled-work inventory, idempotency, internal-call auth
- `seo.md` — SPA preview approach, route coverage, metadata sanitization
- `automation.md` — embedded agents/automations: trigger, tool surface, steering vs. hard guardrails, output contract, app-owned side effects, approval gates

Be brutally honest about the current state without being paranoid. Skip any conditional document that doesn't apply and say so. Add a "Related Documents" reference in `architecture.md` for each doc produced. (The test-coverage map, `tests.md`, is produced separately by `/derive-tests`.)

### Step 3: Report

Summarize what was created or updated, what was skipped and why, and any gaps where the code was too unclear to document confidently (those are the first things to fix).

### Step 4: Offer Next Steps

- "Want me to **derive a test-coverage map** (`/derive-tests`) so each documented rule has a verification plan?"
- "Want me to **run a security audit** now that the intended behavior is documented?"
- "Should I **check for performance issues** — over-fetching, missing indexes, caching?"
- "Want me to **run `/ship-check`** to wire agent context and produce a full shipping packet?"

## Notes

- These docs describe *this* system — keep generic theory and finished templates out.
- Write for two readers: a human reviewer and the next AI coding agent.
- Don't include an "updated date" line.
- The agent operating-context file (`CLAUDE.md` / `AGENTS.md`) is produced separately at the `/ship-check` handoff step — it's instructions derived from these docs, not system documentation.


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/phuryn-pm-skills/pm-ai-shipping/commands/performance-audit-static.md =====

---
description: Static performance audit of AI-built code — find over-fetching, missing indexes, and caching opportunities, ranked by effort and impact
argument-hint: "<repo path or area; defaults to the whole repository>"
---

# /performance-audit-static -- Find What Won't Scale

A focused performance review for AI-built code. Agents optimize for "it works on my seed data," not "it holds at 100× the rows." This command finds the three failure modes that surface as data grows — over-fetching, missing indexes, and absent caching — and ranks fixes by effort and impact.

This is a static review of code and queries, not a load test.

## Invocation

```
/performance-audit-static
/performance-audit-static src/views
```

## Scope

Audit **$ARGUMENTS**. If empty, review the whole repository, prioritizing list and dashboard views, frequently hit endpoints, and large tables.

## The audit

### 1. Over-fetch in view payloads

Review components that render list or dashboard views. Identify fields fetched from the database but never used in the frontend, `SELECT *` on wide tables, missing pagination, absent lazy loading, and redundant loads. Suggest a minimal field set per component or route.

### 2. Missing or inefficient indexes

Review queries, filters, and RPCs used in production views. Identify missing or inefficient indexes based on sort, filter, and join conditions, focusing on large tables and hot endpoints. Give specific index definitions, not "add an index."

### 3. Caching opportunities

Review endpoints and data-access patterns for frequently called paths that return static or rarely changing data. Identify where frontend or backend caching helps, and specify the invalidation rule for each — caching without an invalidation plan is a correctness bug in waiting.

## Output

Report findings per view, route, or table:

```
Performance Audit: [scope]

<view / route / table>:
  - Finding: <what is slow or wasteful>
  - Recommendation: <specific change — field set, index definition, cache + invalidation>
  - Effort: Low | Medium | High
  - Priority: Low | Medium | High
  - Expected effect: <e.g. payload size, query time, load time>
```

End with what's already efficient (say it explicitly) and what needs runtime profiling to confirm. Optionally write the report to `/reports/performance_audit_{timestamp}.md`.

## Notes

- Rank by impact-per-effort — one missing index on a hot table usually beats ten micro-optimizations.
- Don't flag theoretical inefficiency with no growth path; flag what breaks as rows or traffic scale.
- This command covers performance only. For authorization, injection, and data-exposure risks, use `/security-audit-static`.
- For an end-to-end pass with documentation and a shipping packet, use `/ship-check`.


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/phuryn-pm-skills/pm-ai-shipping/commands/security-audit-static.md =====

---
description: Static security audit of AI-built code — map trust boundaries, cross-reference documented intent, self-refute every finding, and report only evidence-backed risks
argument-hint: "<repo path or area; defaults to the whole repository>"
---

# /security-audit-static -- Audit the Code You Already Have

A focused, self-contained security audit for AI-built code. It keeps a small, durable engine — map the boundaries, check intent against implementation, refute before reporting — and refuses to emit anything it can't back with cited evidence.

This is a review, not a guarantee: it produces code-review findings, not confirmed exploits.

> Method adapted from the public, Apache-2.0 `security-guidance` plugin in Anthropic's
> `claude-plugins-official` repository. Not affiliated with or endorsed by Anthropic.

## Invocation

```
/security-audit-static
/security-audit-static supabase/functions
```

## Scope

Audit **$ARGUMENTS**. If empty, audit the whole repository, prioritizing request handlers, auth, data access, background jobs, and anything that renders, fetches, executes, logs, or stores user-controlled data. For non-trivial scopes, fan out with parallel subagents — one per function/module cluster, each running the mapping and inspection (steps 1–3); then merge candidates and run the self-refute (step 4) yourself over the full set.

## The audit (small engine, strong constraint)

### 1. Map entry points to trust boundaries and sinks

Optimize for recall first — read every file in scope in full, then grep for handler, route, RPC, and shared-helper names to find callers and downstream sinks. Reading the file that contains the bug is what prevents missing it.

Entry points: HTTP/RPC handlers, edge/serverless functions, webhooks, queue consumers, upload handlers, auth callbacks, cron-triggered endpoints. Sinks: raw SQL / query filters, shell/exec, `eval` / `new Function` / dynamic imports, HTML render and templates, outbound fetches, filesystem paths, IAM/role writes, logs and analytics, deserializers (incl. YAML/XML and archive extraction), response headers / cache-control, and **LLM prompts and tool calls** (prompt injection). For every value reaching a sink, decide whether an attacker can influence it and trace it back to its source.

### 2. Inspect the four high-value paths

Authorization, data access, session/identity, and input→output encoding. Compare sibling handlers — if one enforces a check another omits, the omission is a finding. Follow cross-file flows; input in module A reaching a dangerous operation in module B is where the real bugs hide.

### 3. Cross-reference intended vs. implemented

Apply the **intended-vs-implemented** skill against `/documentation/*.md`. A rule documented but not enforced in code is a finding on its own. If the docs are absent, note it and recommend `/document-app` first — an intent audit needs intent on record.

### 4. Self-refute every candidate

For each finding, try to disprove it. Default to **keep** unless you find cited evidence (file + line) for one of: a real sanitizer/encoder/validator/authorization check stops the exploit *at the sink*; the sink is non-dangerous (typed, hardcoded, isolated, schema-decoded); a frontend gate is independently re-enforced on the backend; an unvalidated credential is immediately forwarded to an upstream system that validates it; a config/flag gates the path and users can't influence it per request; or the path isn't reachable in production.

Name the **attacker** and the **victim**: refute if the only victim is the attacker on their own machine/account/tenant/data and no shared system or privilege boundary is crossed; keep if the impact reaches other users, tenants, shared infrastructure, billing, email reputation, secrets, or compliance-sensitive data. **Never apply attacker-equals-victim refutation to SSRF/outbound-network sinks, shared billing or quota sinks, data-exposure findings, cross-tenant or cross-principal flows, or server-side execution/rendering** — those harm someone other than the attacker by definition. Never refute a finding merely because the code is pre-existing — pre-existing bugs are the point. Do not speculate.

### 5. Report only what survives

## High-miss checklist (technology-shaped, not stack-specific)

Apply these — they're where AI-built apps most often fail:

- **Service-role / disabled-RLS boundaries** — if the DB client bypasses row-level security, *every* authorization decision must be in code; flag queries missing the org/owner filter.
- **Auth-provider drift** — claims from an external identity provider (e.g. Clerk) trusted without verifying how they map to data scope.
- **Gate/action field mismatch** — permission checked on one ID, action performed on an independent ID never proven to belong to it.
- **Forgeable request signals** — endpoints gated by `?source=cron`, `?bot=1`, guessable headers, or unsigned webhook-like payloads instead of real auth. Raise severity when the endpoint mutates data, sends email, or triggers paid usage.
- **Output encoding vs. input validation** — user data interpolated into HTML, `<title>`, attributes, JSON-LD, SQL, or Markdown must be encoded for *that* sink; input validation doesn't count. (XSS, CSP gaps.)
- **SSRF / renderer abuse** — attacker-influenced URLs, HTML, SVG, or Markdown reaching an outbound fetch or a renderer (headless browser, PDF/OG-image generator).
- **Parser / validator differentials** — the validator accepts a value the consumer interprets differently: unanchored regex, `startsWith`/substring allowlists, URL-parser disagreement, encoding/case/slash/path-normalization mismatch, or validation on one representation and execution on another.
- **Fail-open paths** — error, `catch`, timeout, cancellation, cache-miss, stale-cache, feature-flag, or boundary-value branches that default to *allow*. AI code loves a permissive fallback.
- **Secrets / PII to observability** — credentials, tokens, emails, or sensitive data reaching logs, traces, analytics, or error bodies; check error branches especially.
- **Public-data-only violations** — SPA/SEO bot routes or "public" endpoints over-fetching private fields.

## Output

Group surviving findings by file, sorted by severity, in the standard format:

```
Security Audit: [scope]

<file>:
  N. [SEVERITY] [Category] <location>
     Risk Level: Critical | High | Medium | Low
     Attack Scenario: <attacker -> sink -> impact, step by step>
     Impact: <what data or functionality is compromised>
     Solution: <concrete code change>
```

End with: the root-cause theme across findings; **what is well-built — say it explicitly**; and what you could not verify and the user should double-check. Optionally write the report to `/reports/security_audit_{timestamp}.md`.

## Notes

- Don't report generic hardening with no concrete impact, outdated deps without a reachable path, or test/mock code unless it ships. Logic and authorization bugs with no classic sink still count.
- This command covers security only. For over-fetching, indexes, and caching, use `/performance-audit-static`.
- For an end-to-end pass that documents first and produces a shipping packet, use `/ship-check`.


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/phuryn-pm-skills/pm-ai-shipping/commands/ship-check.md =====

---
description: Turn a vibe-coded repo into a reviewer-ready shipping packet — document the app, wire agent context, run security and performance audits, map test coverage, and compile the results
argument-hint: "<repo path or area; defaults to the whole repository>"
---

# /ship-check -- Is This Safe to Ship?

Your AI wrote the code. This command answers the question you actually have — *is it safe to ship?* — by running the full shipping sequence and compiling the results into one reviewer-ready packet a human can sign off on.

`/ship-check` does not replace the specialist commands. It coordinates them and produces the final artifact none of them produce alone: the **shipping packet**.

## Invocation

```
/ship-check
/ship-check the payments service
/ship-check supabase/functions
```

## The shipping sequence

Run on **$ARGUMENTS** (or the whole repository if empty). Each step builds on the last — the ordering is the point, because every audit is only as good as the documented intent it can compare the code against.

### Step 1: Document the system

Ensure the system docs exist and are current (run `/document-app` if they're missing or stale). Apply the **shipping-artifacts** skill — the core set (architecture, flows, permissions, variables) plus any conditional docs that apply (emails, cron, seo, automation). These docs are the intended-state baseline for everything that follows.

### Step 2: Wire the agent operating context

Create or refresh `CLAUDE.md` (and a thin `AGENTS.md` pointing to it) **derived from** the system docs — the operating instructions the next AI coding agent inherits: what the system is, the trust boundaries, what may and may not be touched, where the guardrails are. This is a different artifact from the system docs: instructions, not description.

### Step 3: Security audit

Run the security pass (`/security-audit-static`), applying the **intended-vs-implemented** skill to flag where the code diverges from `permissions.md`, `flows.md`, and `architecture.md`. Summarize surviving findings.

### Step 4: Performance audit

Run the performance pass (`/performance-audit-static`) — over-fetching, missing indexes, caching. Summarize findings.

### Step 5: Derive the test-coverage map

Run `/derive-tests` to turn the documented rules — and the gaps the audits just surfaced — into a coverage map (`tests.md`): which rules are pinned by tests that exist *today*, which are only proposed, which are guarded-live or manual, and which have no verification at all. Running this **after** the audits is deliberate: each confirmed finding becomes a concrete regression test to pin, so the same gap can't silently reopen on the next AI edit. This is the operational form of "documented == implemented," and the unverified boundary rules feed straight into the launch-blocker assessment below.

### Step 6: Compile the shipping packet

```
## Shipping Packet: [repo / area]

### Documentation Inventory
| Doc | Status (present / stale / missing / n/a) | Notes |

### Agent Context
CLAUDE.md / AGENTS.md: [created / updated / already current]

### Test Coverage
[Rules pinned by tests that exist today · proposed but not yet written · guarded-live/manual · and the documented rules nothing verifies yet]

### Security Summary
[Counts by severity + the surviving findings, each: Risk · Attack · Impact · Fix]

### Performance Summary
[Findings by view/route/table, each: Recommendation · Effort · Priority]

### Launch Blockers
[Unresolved Critical/High items — including any boundary rule that is both unverified and unaudited — that should stop a ship]

### Recommended Next Actions
[Concrete owner actions or commands to run next]
```

## Notes

- This is a handoff compiler: the value is sequencing plus synthesis, not re-deriving each audit.
- If documentation is missing, the packet says so loudly — an audit without documented intent is incomplete, and the inventory makes that visible rather than hiding it.
- Findings are code-review results, not confirmed exploits; the packet is a basis for human sign-off, not a substitute for it.
- Run the specialist commands directly (`/document-app`, `/derive-tests`, `/security-audit-static`, `/performance-audit-static`) when you only need one stage.


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/phuryn-pm-skills/pm-ai-shipping/skills/intended-vs-implemented/SKILL.md =====

---
name: intended-vs-implemented
description: "The method for finding the gap between what a system is supposed to do and what the code actually does — the class of bug generic scanners miss because they have no model of intent. Defines what counts as documented intent, what counts as implementation evidence, which mismatches matter, and how to avoid hand-wavy findings. Use when auditing AI-built code, reviewing access control against documented permissions, or checking whether a codebase matches its own documentation."
---

# Intended vs. Implemented: Auditing the Gap

## Purpose

A linter scans code in a vacuum. It can tell you the code is *internally* consistent; it cannot tell you the code does what you *meant*, because it has no model of your intent. The highest-value security and correctness bugs live in that gap — a permission documented but never enforced, a "cron-only" endpoint anyone can call, a field marked public-only that leaks private data.

This skill is the method for finding that gap. It is the differentiator: it only works when intent has been written down first (see the **shipping-artifacts** skill), and that's exactly why commodity tools can't replicate it.

## Context

Use this when documented intent exists — `permissions.md`, `architecture.md`, `variables.md`, etc. If those docs are absent or stale, that absence is itself the first finding: you cannot audit intent you never recorded. Recommend documenting first, then auditing.

## Method

1. **Establish intent.** Read the `/documentation/*.md` set as the source of truth for what *should* be true: who may access what, which boundaries are trusted, which data is public. Treat the docs as claims to verify, not as proof.

2. **Gather implementation evidence.** Read the code that enforces (or fails to enforce) each claim. Evidence is a cited file and line — the actual authorization check, the actual query filter, the actual sanitizer. "It's probably handled upstream" is not evidence; the code path is.

3. **Compare claim to code, one boundary at a time.** For each documented rule, ask: does an enforcement point actually implement it, on the server, on every path? Distrust comments like "internal only," "admin only," or "validated elsewhere" — verify them in code.

4. **Classify each mismatch by whether it matters.** A mismatch matters when crossing it lets a real actor reach data, money, infrastructure, or another tenant they shouldn't. It does not matter when the only person affected is the actor themselves on their own data. Drop cosmetic drift; keep boundary-crossing drift.

5. **Avoid hand-wavy findings.** Every finding names: the **documented intent** (quote the doc), the **implemented reality** (cite the code), the **attacker and victim**, and the **concrete fix**. If you cannot cite both sides of the gap, it is a question to investigate, not a finding to report.

## What counts

- **Intent:** a documented rule, boundary, scope, or public/private classification.
- **Implementation evidence:** a cited enforcement point (or its provable absence) in the code.
- **A mismatch that matters:** doc says one thing, code does another, and the difference crosses a trust, cost, data, or tenant boundary.

## Notes

- Documented-but-unenforced is a finding on its own — rank it by what crossing the gap exposes.
- Undocumented-but-enforced is usually fine, but flag it: the docs are now stale, which weakens the next audit.
- This method feeds the security and performance audits; it does not replace their sink-level analysis — it adds the intent axis they lack.
- Never fabricate intent to manufacture a gap. If the docs are silent, say the docs are silent.


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/phuryn-pm-skills/pm-ai-shipping/skills/shipping-artifacts/SKILL.md =====

---
name: shipping-artifacts
description: "The durable documentation set that makes an AI-built (vibe-coded) app reviewable before shipping. A small core every app needs — architecture, user/permission flows, permissions, variables/secrets, and a test-coverage map — plus conditional docs added only when they apply: emails, scheduled work, SEO, and embedded agents/automation. Defines what each doc must capture and how a reviewer or auditor uses it. Use when documenting a codebase for handoff, mapping user journeys and trust-boundary crossings, planning test coverage, or preparing for a security or performance audit."
---

# Shipping Artifacts: The Docs That Make AI-Built Code Reviewable

## Purpose

AI agents write code fast, but they leave no durable record of *intent* — what the system is supposed to do, who is allowed to do what, where the secrets live, which rules are actually verified. Without that record, no human (and no auditing agent) can tell whether the code is safe to ship. This skill defines the small set of documents that restore reviewability.

These docs live in `/documentation/` and are written for two readers: a human reviewer and the next AI coding agent. They are the **intended-state** half of every later audit — a security or performance review is only as good as the intent it can compare the code against.

## How the set is organized

The set is **not** a fixed list — it is a small **core** plus **conditional** docs you add only when the capability exists.

- **Core docs** — every reviewable app has these surfaces, so always produce them.
- **Conditional docs** — include one only if the app actually has that capability. If it doesn't, write a single line in `architecture.md` ("No scheduled work — no `cron.md`.") rather than inventing an empty document. Reviewability comes from an honest map, and "we don't do X" is part of the map.
- Most docs are reverse-engineered from code by `/document-app`. The one exception is `tests.md`, which is *derived from the other docs* by `/derive-tests` — it is the verification map, not a description of a subsystem.

Be brutally honest about the current state without being paranoid. The job is an accurate map, not a clean bill of health. Each doc is short, table-and-bullet heavy, and skips generic theory.

## Core documents

Each entry: file · one-line purpose · what it must capture · how a reviewer uses it.

1. **`architecture.md`** — what the system is and how it hangs together.
   - Must capture: product overview + key assumptions; tech stack; how auth/sessions/claims flow end to end; the trust boundaries (e.g. service-role vs. client); a short **Known risks / assumptions** list (each entry backed by where it shows up in the code, not a generic checklist); a "Related Documents" index of every other doc produced.
   - Reviewer use: the root document — everything else is cross-referenced from here.

2. **`flows.md`** — the journeys where permissions and side effects are actually exercised.
   - Must capture: each load-bearing flow as actor + precondition + success outcome; the step-by-step sequence across UI → server → data → jobs → providers → agents; the **authz check at each protected step** (which claim/role/scope, on which resource, and the expected *deny* case); the **trust-boundary crossings** (browser→server, server→provider, job→app, agent→tool, webhook→app); the state changes and side effects each step causes (writes, emails queued, jobs triggered, outbound calls).
   - Reviewer use: the runtime view a static `permissions.md` matrix can't show — *where* and *in what order* authorization is enforced, and where it can be skipped.
   - **Anti-PRD rule:** a flow that doesn't touch permissions, data integrity, external side effects, money, privacy, or operational safety does not belong here. This is a security/operations map, not a feature spec.

3. **`permissions.md`** — who is allowed to do what.
   - Must capture: roles/claims; where scope is derived (token vs. DB); a resource × operation × role matrix; which tables have row-level security and which rely on code-enforced checks.
   - Reviewer use: the baseline an access-control audit compares the code against. `flows.md` shows it in motion; this is the static reference.

4. **`variables.md`** — configuration and secrets, mapped to risk.
   - Must capture: a table of Name · used-by · scope (server/client) · source · rotation · risk; explicit confirmation that no secret is bundled client-side; a pre-go-live checklist.
   - Reviewer use: the secrets/PII-leak surface and the rotation plan during incident response.

5. **`tests.md`** — the verification map: which documented rules are actually checked, which are only proposed, and which are checked by nothing.
   - Must capture, in three clearly separated sections so the map can't read falsely green:
     - **Existing coverage** — tests that are in the repo *today*, each tied to the rule it pins (so the map reflects reality, not a wish-list).
     - **Proposed tests** — recommended cases not yet written, marked by **test type** (automated unit/integration · guarded live · manual review).
     - **Gaps** — documented rules with no verification at all, ranked by what crossing them exposes.
   - Each row carries: use-case → rule → expected behavior (including the deny/negative case) → evidence source (doc + code) → status (existing / proposed / none). It also notes which checks are CI-required and gate merges to `main`.
   - Reviewer use: the operational form of "documented == implemented" — it shows whether each rule the other docs claim is actually pinned by a test today, only proposed, or unverified.
   - Produced by `/derive-tests` (not `/document-app`), because it is derived from the other docs and the existing test suite rather than read off a subsystem.

## Conditional documents (include only when the capability exists)

6. **`emails.md`** — every notification the system sends. *Include only if the app sends transactional or automated email.*
   - Must capture: the queue → processor → provider path; templates and the variables they accept; retry/backoff behavior; where to look when a send fails.
   - Reviewer use: spotting unvalidated template inputs and PII exposure boundaries.

7. **`cron.md`** — all scheduled work and how to operate it safely. *Include only if scheduled or background jobs exist.*
   - Must capture: an inventory table (job → schedule → function → secrets → limits → retry); how each job stays idempotent; how internal calls authenticate; where to see last runs.
   - Reviewer use: finding forgeable triggers and unbounded background jobs.

8. **`seo.md`** — how a single-page app handles SEO and social previews. *Include only if there are public/indexable or bot-facing routes.*
   - Must capture: the preview approach (static meta / prerender / edge HTML); a route → needs-SEO → public-data-only table; how dynamic metadata is sanitized; bot-vs-human routing.
   - Reviewer use: catching public-data-only violations and metadata injection on bot routes.

9. **`automation.md`** — embedded agents and other automation paths. *Include only if the app embeds AI agents, LLM workflows, tool-calling, webhooks, or external automation.*
   - Must capture, per automation/agent: trigger + owner + whether it runs automatically or only after approval; the inputs it may read and the **exact tools/APIs it may call** (the tool surface is itself a hard guardrail); where **steering** lives (the prompt) vs. the **non-prompt hard guardrails**; the **output contract** back to the app (schema, validation, failure handling); **app-owned side effects vs. agent-owned suggestions**; and the controls — approval gates, audit/timeline logging, rate limits, retries, kill switch.
   - Reviewer use: makes hidden automation paths visible and draws the line between what an agent *proposes* and what the app *enforces* — the highest-risk surface in modern AI-built apps.

## Notes

- Each produced doc adds a reference to itself in `architecture.md` under a "Related Documents" section, so the set stays discoverable.
- Skip any conditional document that doesn't apply, and say so in one line rather than inventing content.
- Keep examples and finished templates out of these docs — they describe *this* system, not the general method.
- The agent operating-context file (`CLAUDE.md` / `AGENTS.md`) is a *different* artifact — instructions derived from these docs, not system documentation. It is produced at the handoff step by `/ship-check`, not here.
- `tests.md` is produced by `/derive-tests`; the rest are produced by `/document-app`.
- Do not include an "updated date" line; the file's history is the source of truth.


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/phuryn-pm-skills/pm-data-analytics/README.md =====

# pm-data-analytics

Data analytics skills for PMs: SQL query generation and cohort analysis. Analyze user data, generate queries, and identify retention patterns.

## Skills (3)

- **ab-test-analysis** — Analyze A/B test results with statistical significance, sample size validation, confidence intervals, and actionable recommendations.
- **cohort-analysis** — Perform cohort analysis on user engagement data.
- **sql-queries** — Generate SQL queries from natural language descriptions.

## Commands (3)

- `/pm-data-analytics:analyze-cohorts` — Perform cohort analysis on user data — retention curves, feature adoption, and engagement trends.
- `/pm-data-analytics:analyze-test` — Analyze A/B test results — statistical significance, sample size validation, and ship/extend/stop recommendations.
- `/pm-data-analytics:write-query` — Generate SQL queries from natural language — supports BigQuery, PostgreSQL, MySQL, and more.

## Author

Paweł Huryn — [The Product Compass Newsletter](https://www.productcompass.pm)

## License

MIT


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/phuryn-pm-skills/pm-data-analytics/commands/analyze-cohorts.md =====

---
description: Perform cohort analysis on user data — retention curves, feature adoption, and engagement trends
argument-hint: "<data file or description of what to analyze>"
---

# /analyze-cohorts -- Cohort Analysis

Analyze user retention and engagement patterns by cohort. Upload your data or describe what you need, and get retention curves, feature adoption trends, and actionable insights.

## Invocation

```
/analyze-cohorts [upload a CSV of user activity data]
/analyze-cohorts Monthly retention for users who signed up in Jan-Jun, grouped by acquisition channel
/analyze-cohorts Help me set up a cohort analysis for our onboarding redesign
```

## Workflow

### Step 1: Accept Data or Define Analysis

Two paths:
- **With data**: User uploads a CSV/spreadsheet with user-level data (user_id, signup_date, activity_date, event_type, etc.)
- **Without data**: User describes the analysis they need → generate the SQL query and analysis framework

### Step 2: Define Cohorts

Ask:
- What defines a cohort? (signup week/month, acquisition channel, plan tier, first feature used)
- What is the retention event? (login, core action, any activity, purchase)
- What time granularity? (daily, weekly, monthly)
- What time range?

### Step 3: Analyze

Apply the **cohort-analysis** skill:

**If data is provided:**
- Process the data using Python (pandas) to create cohort tables
- Calculate retention rates per cohort per period
- Generate retention curves
- Identify patterns: improving/declining cohorts, seasonal effects, anomalies
- Compare feature adoption across cohorts

**If describing an analysis:**
- Design the cohort analysis framework
- Generate SQL queries to extract the data
- Create a template spreadsheet for the analysis
- Define the metrics and visualization approach

### Step 4: Generate Report

```
## Cohort Analysis: [Description]

**Date**: [today]
**Cohort definition**: [e.g., signup month]
**Retention event**: [e.g., completed a project]
**Granularity**: [weekly/monthly]

### Retention Table
| Cohort | Size | Week 1 | Week 2 | Week 3 | ... | Week 12 |
|--------|------|--------|--------|--------|-----|---------|

### Key Findings
1. **[Finding]** — [supporting data]
2. ...

### Cohort Comparison
- **Best-performing cohort**: [which, why]
- **Worst-performing cohort**: [which, why]
- **Trend**: [improving/declining/stable over time]

### Retention Benchmarks
| Period | Your Rate | Industry Benchmark | Gap |
|--------|----------|-------------------|-----|

### Recommendations
1. [What to investigate or change based on findings]
2. ...

### Follow-Up Queries
[SQL queries for deeper investigation]
```

If data was provided, save analysis as both markdown report and CSV/spreadsheet.

### Step 5: Offer Next Steps

- "Want me to **segment this further** by another dimension?"
- "Should I **set up metrics alerts** based on these retention thresholds?"
- "Want me to **design experiments** to improve retention for the weakest cohort?"

## Notes

- Cohort analysis is only as good as the retention event definition — push for a meaningful action, not just "logged in"
- Early cohorts often look different due to founding user bias — note this when comparing
- If retention is calculated using a Python script, save the script so the user can re-run with new data
- Seasonal effects can masquerade as trends — flag if cohort differences might be calendar-driven


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/phuryn-pm-skills/pm-data-analytics/commands/analyze-test.md =====

---
description: Analyze A/B test results — statistical significance, sample size validation, and ship/extend/stop recommendations
argument-hint: "<test results as data, screenshot, or description>"
---

# /analyze-test -- A/B Test Analysis

Evaluate experiment results with statistical rigor and translate findings into a clear product decision: ship, extend, or stop.

## Invocation

```
/analyze-test Control: 4.2% conversion (n=5000), Variant: 4.8% conversion (n=5100)
/analyze-test [upload a CSV of test results]
/analyze-test [screenshot from your experimentation platform]
```

## Workflow

### Step 1: Accept Test Data

Accept in any format:
- Summary statistics (conversion rates, sample sizes per variant)
- Raw event data (CSV with user_id, variant, converted, timestamp)
- Screenshot from an experimentation platform (Optimizely, LaunchDarkly, etc.)
- Description of the experiment and results

### Step 2: Validate Test Design

Before analyzing results, check:
- Was sample size sufficient? (run a power analysis)
- Was the test run long enough? (capture weekly cycles, minimum 1-2 business cycles)
- Was randomization clean? (check for sample ratio mismatch)
- Were there any external factors during the test period?

Flag issues if found — results from a flawed test can be misleading.

### Step 3: Analyze Results

Apply the **ab-test-analysis** skill:

- **Statistical significance**: Calculate p-value and confidence interval
- **Effect size**: Absolute and relative difference between variants
- **Practical significance**: Is the effect large enough to matter for the business?
- **Confidence interval**: What's the range of plausible true effects?
- **Segment analysis**: If data allows, check for differential effects by user segment

### Step 4: Generate Analysis

```
## A/B Test Analysis: [Test Name]

**Date**: [today]
**Test duration**: [X days/weeks]
**Total sample**: [N users]

### Results Summary
| Variant | Sample | Metric | Rate | 95% CI |
|---------|--------|--------|------|--------|
| Control | [n] | [metric] | [X%] | [X% - Y%] |
| Variant | [n] | [metric] | [X%] | [X% - Y%] |

### Statistical Analysis
- **Relative lift**: [+X%] ([CI range])
- **P-value**: [X]
- **Statistically significant**: [Yes/No] at 95% confidence
- **Minimum detectable effect**: [X%] (what the test was powered to detect)

### Sample Size Check
- **Required sample**: [N] per variant (for [X%] MDE at 80% power)
- **Actual sample**: [N] per variant
- **Verdict**: [Sufficiently powered / Underpowered / Overpowered]

### Decision

**Recommendation: [SHIP / EXTEND / STOP]**

[Clear explanation of why, considering both statistical and practical significance]

### Business Impact Estimate
If shipped to 100% of users:
- **Expected impact**: [metric change per month/quarter]
- **Revenue impact**: [if applicable]
- **Confidence**: [How certain we are about this estimate]

### Caveats
- [Any concerns about the test validity]
- [Segments where results differ]
- [Novelty effects or other biases to consider]

### Follow-Up
- [What to test next based on learnings]
- [Monitoring plan if shipping the variant]
```

### Step 5: Offer Next Steps

- "Want me to **design a follow-up experiment** based on these findings?"
- "Should I **run the analysis for specific segments**?"
- "Want me to **generate the SQL** to monitor this metric post-launch?"

## Notes

- Statistical significance ≠ practical significance — a 0.1% lift can be significant with enough data but not worth shipping
- Always check for sample ratio mismatch before trusting results
- Novelty effects can inflate short-term results — recommend monitoring for 2-4 weeks post-launch
- If the test is underpowered, the right answer is usually "extend" not "no effect"
- For revenue metrics, use confidence intervals to estimate best-case and worst-case business impact
- If data is provided as CSV, generate the full analysis using Python with scipy.stats


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/phuryn-pm-skills/pm-data-analytics/commands/write-query.md =====

---
description: Generate SQL queries from natural language — supports BigQuery, PostgreSQL, MySQL, and more
argument-hint: "<what you want to know, in plain English>"
---

# /write-query -- SQL Query Generator

Describe what data you need in plain English and get an optimized SQL query. Supports multiple dialects and can read your schema from uploaded files.

## Invocation

```
/write-query Show me daily active users for the last 30 days, broken down by plan tier
/write-query Find users who signed up last month but never completed onboarding
/write-query [upload a schema diagram] What's the conversion rate from trial to paid by cohort?
```

## Workflow

### Step 1: Understand the Question

Parse the user's natural language request to identify:
- What data is being requested (metrics, dimensions, filters)
- Time range and granularity
- Grouping and ordering preferences
- Output expectations (raw data, aggregated, ranked)

### Step 2: Determine Schema

If a schema is available (uploaded diagram, DDL, or description):
- Map the request to specific tables and columns
- Identify necessary joins

If no schema is provided:
- Ask for the database type (BigQuery, PostgreSQL, MySQL, etc.)
- Infer a reasonable schema from the question and ask the user to confirm
- Use common SaaS data model conventions as defaults

### Step 3: Generate Query

Apply the **sql-queries** skill:

- Write the SQL query in the correct dialect
- Optimize for readability and performance
- Include comments explaining key logic
- Add CTEs for complex queries to improve readability
- Handle edge cases (NULLs, timezone considerations, duplicate handling)

### Step 4: Present and Iterate

```
## SQL Query: [What It Does]

**Dialect**: [BigQuery / PostgreSQL / MySQL / etc.]
**Tables used**: [list]

### Query
[SQL code block with comments]

### What This Returns
[Description of the output: columns, rows, expected result shape]

### Assumptions
- [Schema assumptions made]
- [Business logic assumptions]

### Notes
- [Performance considerations for large datasets]
- [Edge cases handled or flagged]
```

Offer:
- "Want me to **modify this** — add filters, change grouping, extend the time range?"
- "Should I **create a companion query** for a related metric?"
- "Want me to **build a dashboard** around this query?"
- "Need a **cohort analysis** version of this?"

## Notes

- Always include comments in the SQL — PMs share queries with analysts who need to understand intent
- Default to readable over clever — CTEs over nested subqueries
- Flag queries that might be slow on large datasets and suggest optimization
- If the request is ambiguous (e.g., "active users"), ask the user to define the metric precisely
- Offer to generate the query in multiple dialects if the user is unsure which database they're using


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/phuryn-pm-skills/pm-data-analytics/skills/ab-test-analysis/SKILL.md =====

---
name: ab-test-analysis
description: "Analyze A/B test results with statistical significance, sample size validation, confidence intervals, and ship/extend/stop recommendations. Use when evaluating experiment results, checking if a test reached significance, interpreting split test data, or deciding whether to ship a variant."
---

## A/B Test Analysis

Evaluate A/B test results with statistical rigor and translate findings into clear product decisions.

### Context

You are analyzing A/B test results for **$ARGUMENTS**.

If the user provides data files (CSV, Excel, or analytics exports), read and analyze them directly. Generate Python scripts for statistical calculations when needed.

### Instructions

1. **Understand the experiment**:
   - What was the hypothesis?
   - What was changed (the variant)?
   - What is the primary metric? Any guardrail metrics?
   - How long did the test run?
   - What is the traffic split?

2. **Validate the test setup**:
   - **Sample size**: Is the sample large enough for the expected effect size?
     - Use the formula: n = (Z²α/2 × 2 × p × (1-p)) / MDE²
     - Flag if the test is underpowered (<80% power)
   - **Duration**: Did the test run for at least 1-2 full business cycles?
   - **Randomization**: Any evidence of sample ratio mismatch (SRM)?
   - **Novelty/primacy effects**: Was there enough time to wash out initial behavior changes?

3. **Calculate statistical significance**:
   - **Conversion rate** for control and variant
   - **Relative lift**: (variant - control) / control × 100
   - **p-value**: Using a two-tailed z-test or chi-squared test
   - **Confidence interval**: 95% CI for the difference
   - **Statistical significance**: Is p < 0.05?
   - **Practical significance**: Is the lift meaningful for the business?

   If the user provides raw data, generate and run a Python script to calculate these.

4. **Check guardrail metrics**:
   - Did any guardrail metrics (revenue, engagement, page load time) degrade?
   - A winning primary metric with degraded guardrails may not be a true win

5. **Interpret results**:

   | Outcome | Recommendation |
   |---|---|
   | Significant positive lift, no guardrail issues | **Ship it** — roll out to 100% |
   | Significant positive lift, guardrail concerns | **Investigate** — understand trade-offs before shipping |
   | Not significant, positive trend | **Extend the test** — need more data or larger effect |
   | Not significant, flat | **Stop the test** — no meaningful difference detected |
   | Significant negative lift | **Don't ship** — revert to control, analyze why |

6. **Provide the analysis summary**:
   ```
   ## A/B Test Results: [Test Name]

   **Hypothesis**: [What we expected]
   **Duration**: [X days] | **Sample**: [N control / M variant]

   | Metric | Control | Variant | Lift | p-value | Significant? |
   |---|---|---|---|---|---|
   | [Primary] | X% | Y% | +Z% | 0.0X | Yes/No |
   | [Guardrail] | ... | ... | ... | ... | ... |

   **Recommendation**: [Ship / Extend / Stop / Investigate]
   **Reasoning**: [Why]
   **Next steps**: [What to do]
   ```

Think step by step. Save as markdown. Generate Python scripts for calculations if raw data is provided.

---

### Further Reading

- [A/B Testing 101 + Examples](https://www.productcompass.pm/p/ab-testing-101-for-pms)
- [Testing Product Ideas: The Ultimate Validation Experiments Library](https://www.productcompass.pm/p/the-ultimate-experiments-library)
- [Are You Tracking the Right Metrics?](https://www.productcompass.pm/p/are-you-tracking-the-right-metrics)


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/phuryn-pm-skills/pm-data-analytics/skills/cohort-analysis/SKILL.md =====

---
name: cohort-analysis
description: "Perform cohort analysis on user engagement data — retention curves, feature adoption trends, and segment-level insights. Use when analyzing user retention by cohort, studying feature adoption over time, investigating churn patterns, or identifying engagement trends."
---

# Cohort Analysis & Retention Explorer

## Purpose
Analyze user engagement and retention patterns by cohort to identify trends in user behavior, feature adoption, and long-term engagement. Combine quantitative insights with qualitative research recommendations.

## How It Works

### Step 1: Read and Validate Your Data
- Accept CSV, Excel, or JSON data files with user cohort information
- Verify data structure: cohort identifier, time periods, engagement metrics
- Check for missing values and data quality issues
- Summarize key statistics (cohort sizes, date ranges, metrics available)

### Step 2: Generate Quantitative Analysis
- Calculate cohort retention rates and engagement trends
- Identify retention curves, drop-off patterns, and anomalies
- Compute feature adoption rates across cohorts
- Calculate month-over-month or period-over-period changes
- Generate Python analysis scripts using pandas and numpy if requested

### Step 3: Create Visualizations
- Generate retention heatmaps (cohorts vs. time periods)
- Create line charts showing cohort progression
- Build comparison charts for feature adoption
- Visualize drop-off points and engagement trends
- Output as interactive charts or static images

### Step 4: Identify Insights & Patterns
- Spot one or more significant patterns:
  - Early churn in specific cohorts
  - Late-stage engagement changes
  - Feature adoption clusters
  - Seasonal or temporal trends
- Highlight surprising findings and deviations
- Compare cohort performance to establish baselines

### Step 5: Suggest Follow-Up Research
- Recommend qualitative research methods:
  - Targeted user interviews with churning users
  - Feature usage surveys with engaged cohorts
  - Session replays of key interaction patterns
  - Win/loss analysis for high vs. low retention cohorts
- Design follow-up quantitative studies
- Suggest A/B tests or feature experiments

## Usage Examples

**Example 1: Upload CSV Data**
```
Upload cohort_engagement.csv with columns: cohort_month, weeks_active,
user_id, feature_x_usage, engagement_score

Request: "Analyze retention patterns and identify why Q4 2025 cohorts
underperform compared to Q3"
```

**Example 2: Describe Data Format**
```
"I have monthly user cohorts from Jan-Dec 2025. Each row shows:
cohort date, user ID, purchase frequency, and support tickets.
Analyze which cohorts show best long-term retention."
```

**Example 3: Feature Adoption Analysis**
```
Upload feature_usage.xlsx with cohort adoption data.

Request: "Compare adoption curves for our new feature across cohorts.
Which cohorts adopted fastest? Any patterns?"
```

## Key Capabilities

- **Data Reading**: Import CSV, Excel, JSON, SQL query results
- **Retention Analysis**: Calculate and visualize retention rates over time
- **Cohort Comparison**: Compare metrics across cohort groups
- **Anomaly Detection**: Flag unusual patterns or drop-offs
- **Python Scripts**: Generate reusable analysis code for ongoing analysis
- **Visualizations**: Create heatmaps, charts, and interactive dashboards
- **Research Design**: Suggest targeted follow-up studies and interview approaches
- **Statistical Summary**: Provide quantitative metrics and correlation analysis

## Tips for Best Results

1. **Include time dimension**: Provide data across multiple time periods
2. **Define cohort clearly**: Make cohort grouping explicit (signup month, feature launch date, etc.)
3. **Provide context**: Explain product changes, launches, or events during the period
4. **Multiple metrics**: Include retention, engagement, feature usage, revenue, etc.
5. **Sufficient data**: At least 3-4 cohorts for meaningful pattern identification
6. **Request specific output**: Ask for visualizations, Python scripts, or research recommendations

## Output Format

You'll receive:
- **Data Summary**: Cohort overview and data quality assessment
- **Quantitative Findings**: Key metrics, retention rates, and trend analysis
- **Visualizations**: Charts showing retention curves, adoption patterns
- **Pattern Identification**: 2-3 significant insights from the data
- **Research Recommendations**: Specific qualitative and quantitative follow-ups
- **Analysis Scripts** (if requested): Python code for reproducible analysis
- **Next Steps**: Prioritized actions based on findings

---

### Further Reading

- [Cohort Analysis 101: How to Reduce Churn and Make Better Product Decisions](https://www.productcompass.pm/p/cohort-analysis)
- [The Product Analytics Playbook: AARRR, HEART, Cohorts & Funnels for PMs](https://www.productcompass.pm/p/the-product-analytics-playbook-aarrr)
- [Are You Tracking the Right Metrics?](https://www.productcompass.pm/p/are-you-tracking-the-right-metrics)


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/phuryn-pm-skills/pm-data-analytics/skills/sql-queries/SKILL.md =====

---
name: sql-queries
description: "Generate SQL queries from natural language descriptions. Supports BigQuery, PostgreSQL, MySQL, and other dialects. Reads database schemas from uploaded diagrams or documentation. Use when writing SQL, building data reports, exploring databases, or translating business questions into queries."
---

# SQL Query Generator

## Purpose
Transform natural language requirements into optimized SQL queries across multiple database platforms. This skill helps product managers, analysts, and engineers generate accurate queries without manual syntax work.

## How It Works

### Step 1: Understand Your Database Schema
- If you provide a schema file (SQL, documentation, or diagram description), I will read and analyze it
- Extract table names, column definitions, data types, and relationships
- Identify primary keys, foreign keys, and indexing strategies

### Step 2: Process Your Request
- Clarify the exact data you need to retrieve or analyze
- Confirm the SQL dialect (BigQuery, PostgreSQL, MySQL, Snowflake, etc.)
- Ask for any additional requirements (filters, aggregations, sorting)

### Step 3: Generate Optimized Query
- Write efficient SQL that leverages your database structure
- Include comments explaining complex logic
- Add performance considerations for large datasets
- Provide alternative approaches if applicable

### Step 4: Explain and Test
- Explain the query logic in plain English
- Suggest how to test or validate results
- Offer tips for performance optimization
- If you want, generate a test script or sample data

## Usage Examples

**Example 1: Query from Schema File**
```
Upload your database_schema.sql file and say:
"Generate a query to find users who signed up in the last 30 days
and had at least 5 active sessions"
```

**Example 2: Query from Diagram Description**
```
"Here's my database: Users table (id, email, created_at), Sessions table
(id, user_id, timestamp, duration). Generate a query for average session
duration per user in January 2026."
```

**Example 3: Complex Analysis Query**
```
"Create a BigQuery query to analyze our revenue by region and customer tier,
including year-over-year growth rates."
```

## Key Capabilities

- **Multi-Dialect Support**: Works with BigQuery, PostgreSQL, MySQL, Snowflake, SQL Server
- **File Reading**: Reads schema files, SQL dumps, and data documentation
- **Query Optimization**: Suggests indexes, partitioning, and performance improvements
- **Explanation**: Breaks down queries for learning and documentation
- **Testing**: Can generate test queries and sample data scripts
- **Script Execution**: Create executable SQL scripts for your database

## Tips for Best Results

1. **Provide context**: Share your database schema or structure
2. **Be specific**: Clearly describe what data you need and any filters
3. **Mention database**: Specify which SQL dialect you're using
4. **Include constraints**: Mention data volume, time ranges, and performance needs
5. **Request format**: Ask for the query result format if you need specific output

## Output Format

You'll receive:
- **SQL Query**: Production-ready SQL code with comments
- **Explanation**: What the query does and how it works
- **Performance Notes**: Optimization tips and considerations
- **Test Script** (if requested): Sample data and validation queries

---

### Further Reading

- [The Product Analytics Playbook: AARRR, HEART, Cohorts & Funnels for PMs](https://www.productcompass.pm/p/the-product-analytics-playbook-aarrr)
- [How to Become a Technology-Literate PM](https://www.productcompass.pm/p/how-to-become-a-technology-literate)


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/phuryn-pm-skills/pm-execution/README.md =====

# pm-execution

Execution and product management skills: PRDs, OKRs, roadmaps, sprints, pre-mortems, stakeholder maps, user stories, prioritization frameworks, and more.

## Skills (16)

- **brainstorm-okrs** — Brainstorm team-level OKRs aligned with company objectives.
- **create-prd** — Create a Product Requirements Document using a comprehensive 8-section template covering summary, background, objectives, market segments, value propositions, solution details, and release planning.
- **dummy-dataset** — Generate realistic dummy datasets for testing with customizable columns, constraints, and output formats (CSV, JSON, SQL, Python script).
- **job-stories** — Create job stories using the 'When [situation], I want to [motivation], so I can [outcome]' format with detailed acceptance criteria.
- **outcome-roadmap** — Transform an output-focused roadmap into an outcome-focused one.
- **pre-mortem** — Run a pre-mortem analysis on a PRD.
- **prioritization-frameworks** — Reference guide to 9 prioritization frameworks with formulas, when-to-use guidance, and templates.
- **release-notes** — Generate user-facing release notes from tickets, PRDs, or changelogs.
- **retro** — Facilitate a structured sprint retrospective.
- **sprint-plan** — Plan a sprint with capacity estimation, story selection, dependency mapping, and risk identification.
- **stakeholder-map** — Build a stakeholder map using a power/interest grid, identify communication strategies per quadrant, and generate a communication plan.
- **strategy-red-team** — Red-team a PRD, roadmap, or strategy by attacking its load-bearing assumptions; rank failure modes and return the cheapest test and kill criteria for each.
- **summarize-meeting** — Summarize a meeting transcript into a structured template with date, participants, topic, summary points, and action items.
- **test-scenarios** — Create comprehensive test scenarios from user stories with test objectives, starting conditions, user roles, step-by-step actions, and expected outcomes.
- **user-stories** — Create user stories following the 3 C's (Card, Conversation, Confirmation) and INVEST criteria with descriptions, design links, and acceptance criteria.
- **wwas** — Create product backlog items in Why-What-Acceptance format.

## Commands (11)

- `/pm-execution:generate-data` — Generate realistic dummy datasets for testing — CSV, JSON, SQL inserts, or Python scripts.
- `/pm-execution:meeting-notes` — Summarize a meeting transcript into structured notes with decisions, action items, and follow-ups.
- `/pm-execution:plan-okrs` — Brainstorm team-level OKRs aligned with company objectives — qualitative objectives with measurable key results.
- `/pm-execution:pre-mortem` — Run a pre-mortem risk analysis on a PRD, launch plan, or feature — identify what could go wrong before it does.
- `/pm-execution:red-team-prd` — Red-team a PRD, roadmap, or strategy — attack its load-bearing assumptions and return the cheapest test for each before you commit.
- `/pm-execution:sprint` — Sprint lifecycle — plan a sprint, run a retrospective, or generate release notes.
- `/pm-execution:stakeholder-map` — Map stakeholders on a Power × Interest grid and create a tailored communication plan.
- `/pm-execution:test-scenarios` — Generate comprehensive test scenarios from user stories or feature specs — happy paths, edge cases, and error handling.
- `/pm-execution:transform-roadmap` — Convert a feature-based roadmap into an outcome-focused roadmap that communicates strategic intent.
- `/pm-execution:write-prd` — Create a comprehensive Product Requirements Document from a feature idea or problem statement.
- `/pm-execution:write-stories` — Break a feature into backlog items — user stories, job stories, or WWA format with acceptance criteria.

## Author

Paweł Huryn — [The Product Compass Newsletter](https://www.productcompass.pm)

## License

MIT


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/phuryn-pm-skills/pm-execution/commands/generate-data.md =====

---
description: Generate realistic dummy datasets for testing — CSV, JSON, SQL inserts, or Python scripts
argument-hint: "<description of the data you need>"
---

# /generate-data -- Test Data Generator

Create realistic dummy datasets for development, testing, demos, or prototyping. Outputs as ready-to-use files in your preferred format.

## Invocation

```
/generate-data 1000 users with names, emails, plan tier, signup date, and activity score
/generate-data E-commerce orders dataset: products, customers, timestamps, amounts
/generate-data Sample data matching this schema: [paste table definition]
```

## Workflow

### Step 1: Define the Dataset

Understand:
- What entities? (users, orders, events, products, etc.)
- What columns? (with data types and constraints)
- How many rows?
- Any relationships between tables?
- Any specific distributions? (e.g., "80% should be on the free plan")
- Any realistic constraints? (emails should be unique, dates should be chronological)

### Step 2: Generate the Data

Apply the **dummy-dataset** skill:

- Create a Python script that generates the dataset
- Use realistic-looking data (not random strings): proper names, valid email formats, real-seeming dates
- Respect constraints: unique IDs, foreign key relationships, chronological ordering
- Apply specified distributions
- Execute the script and produce the output file

### Step 3: Deliver

Output in the requested format (or ask):
- **CSV**: Most common, works everywhere
- **JSON**: For API testing or frontend development
- **SQL INSERT**: For populating test databases
- **Python script**: For reproducible generation (user can tweak and re-run)

```
## Generated Dataset: [Description]

**Rows**: [count]
**Columns**: [list]
**Format**: [CSV / JSON / SQL / Python]

### Schema
| Column | Type | Constraints | Distribution |
|--------|------|-----------|-------------|

### Sample (first 5 rows)
[Preview of the data]

### Files
- [data file]
- [generator script, if applicable]
```

Save data file and generator script to the user's workspace.

### Step 4: Offer Follow-ups

- "Want me to **add more columns** or **increase the dataset size**?"
- "Should I **create related tables** (e.g., orders for these users)?"
- "Want me to **write test scenarios** that use this data?"
- "Should I **create SQL queries** to analyze this dataset?"

## Notes

- Always provide the generator script so the user can regenerate with different parameters
- For demo datasets, make the data tell a story (e.g., seasonal trends, a retention problem, a power user segment)
- Respect realistic cardinality: 1000 users don't have 1000 unique cities
- For financial data, use realistic price distributions — not uniform random
- Never include real personal data — all names, emails, and identifiers must be fake


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/phuryn-pm-skills/pm-execution/commands/meeting-notes.md =====

---
description: Summarize a meeting transcript into structured notes with decisions, action items, and follow-ups
argument-hint: "<transcript or meeting notes>"
---

# /meeting-notes -- Meeting Summary

Transform a raw meeting transcript or rough notes into clear, structured meeting minutes with decisions captured and action items assigned.

## Invocation

```
/meeting-notes [paste transcript]
/meeting-notes [upload transcript file, audio summary, or notes]
```

## Workflow

### Step 1: Accept the Transcript

Accept in any format:
- Full transcript (from Otter, Fireflies, Google Meet, Zoom, etc.)
- Rough notes taken during the meeting
- Audio summary or meeting recap from a transcription tool
- Multiple inputs (e.g., transcript + the user's own notes)

If the input is sparse, work with what's available and flag gaps.

### Step 2: Extract and Structure

Apply the **summarize-meeting** skill:

Parse the content to identify:
- **Participants**: Who was present (from introductions, speaker labels, or mentions)
- **Topics discussed**: Major agenda items or conversation threads
- **Decisions made**: Explicit agreements or conclusions reached
- **Action items**: Tasks assigned, with owner and deadline if mentioned
- **Open questions**: Unresolved items that need follow-up
- **Key quotes**: Important statements worth preserving verbatim
- **Context**: Meeting type, project, and background

### Step 3: Generate Meeting Summary

```
## Meeting Summary

**Date**: [date if known]
**Participants**: [names/roles]
**Meeting type**: [standup, planning, review, 1:1, stakeholder, etc.]
**Topic**: [primary subject]

### Summary
[3-5 sentence overview of what was discussed and concluded]

### Key Decisions
1. **[Decision]** — [context and rationale]
2. ...

### Action Items
| # | Action | Owner | Deadline | Status |
|---|--------|-------|----------|--------|

### Discussion Highlights
**[Topic 1]**: [key points, different perspectives, conclusion]
**[Topic 2]**: [key points, different perspectives, conclusion]

### Open Questions
- [Question] — needs input from [person/team]

### Next Steps
- [What happens next]
- Next meeting: [if mentioned]
```

Save as markdown.

### Step 4: Offer Follow-ups

- "Want me to **email these notes** to participants?"
- "Should I **create tickets** from the action items?"
- "Want me to **draft a stakeholder update** based on the decisions made?"

## Notes

- Decisions are the most valuable output — make sure every decision is captured clearly
- Action items without owners are useless — if no owner was mentioned, flag it
- Keep the summary concise — people who weren't in the meeting should get the gist in 30 seconds
- If the transcript is very long (60+ min meeting), offer a TL;DR before the full summary
- Distinguish between "discussed" and "decided" — many topics are explored without reaching a conclusion


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/phuryn-pm-skills/pm-execution/commands/plan-okrs.md =====

---
description: Brainstorm team-level OKRs aligned with company objectives — qualitative objectives with measurable key results
argument-hint: "<team, product area, or company objective>"
---

# /plan-okrs -- Team OKR Planning

Generate well-structured OKRs that connect team work to company strategy. Produces 3 OKR sets with qualitative objectives and quantitative key results.

## Invocation

```
/plan-okrs Growth team Q2 — company goal is 50% ARR increase
/plan-okrs Onboarding squad aligned to "improve activation rate"
/plan-okrs [upload company OKRs or strategy doc]
```

## Workflow

### Step 1: Gather Context

Ask the user:
- What team or product area are these OKRs for?
- What time period? (quarterly is standard, but could be annual or custom)
- What are the company-level objectives these should ladder up to?
- What happened last quarter? (hits, misses, learnings)
- Any constraints or known priorities?

Accept company OKRs or strategy documents as uploads.

### Step 2: Generate OKRs

Apply the **brainstorm-okrs** skill:

- Create 3 OKR sets (Objective + 3-5 Key Results each)
- **Objectives**: Qualitative, inspiring, ambitious but achievable, action-oriented
- **Key Results**: Quantitative, measurable, time-bound, have clear owners
- Ensure OKRs ladder to company objectives with visible connection
- Balance leading indicators (activity) with lagging indicators (outcomes)

### Step 3: Validate Quality

Check each OKR against best practices:
- Is the Objective inspiring? (Would you rally a team around it?)
- Are Key Results measurable? (Can you check completion with data, not judgment?)
- Are targets ambitious but not demoralizing? (70% achievement = well-calibrated)
- Are there 3-5 KRs per Objective? (More = unfocused)
- Do KRs avoid gaming? (e.g., "ship 5 features" incentivizes shipping junk)

Flag any issues and suggest improvements.

### Step 4: Present and Iterate

```
## Team OKRs: [Team Name] — [Period]

**Aligned to**: [Company Objective(s)]

### Objective 1: [Inspiring qualitative statement]
| # | Key Result | Baseline | Target | Owner |
|---|-----------|----------|--------|-------|
| KR1 | [measurable result] | [current] | [target] | [team/person] |
| KR2 | ... | ... | ... | ... |
| KR3 | ... | ... | ... | ... |

### Objective 2: [Inspiring qualitative statement]
[same format]

### Objective 3: [Inspiring qualitative statement]
[same format]

### Alignment Map
Company Objective → Team Objective → Key Results → Expected Impact

### Scoring Guide
- 0.0-0.3: Significant miss — investigate and learn
- 0.4-0.6: Progress made but fell short
- 0.7-0.9: Well-calibrated stretch goal — this is the target zone
- 1.0: Either nailed it or target wasn't ambitious enough

### Check-in Cadence
- **Weekly**: Quick traffic-light update on each KR
- **Mid-quarter**: Deep review, adjust targets if context changed
- **End of quarter**: Score, reflect, feed into next quarter
```

Offer:
- "Want me to **adjust ambition levels** — make them more/less aggressive?"
- "Should I **create a metrics dashboard** for tracking these?"
- "Want me to **draft a stakeholder update** introducing these OKRs?"

## Notes

- OKRs should describe outcomes, not outputs ("Increase activation by 20%" not "Ship onboarding redesign")
- If the user doesn't have company OKRs, help them derive team objectives from product strategy or business goals
- Maximum 3 objectives per team per quarter — more means less focus
- Key Results should be stretch goals — if you're certain you'll hit them, they're not ambitious enough
- Flag any KR that could be gamed and suggest a counter-metric


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/phuryn-pm-skills/pm-execution/commands/pre-mortem.md =====

---
description: Run a pre-mortem risk analysis on a PRD, launch plan, or feature — identify what could go wrong before it does
argument-hint: "<PRD, plan, or feature description>"
---

# /pre-mortem -- Pre-Launch Risk Analysis

Imagine your launch has failed. Now work backward to figure out why. This command applies the Tigers/Paper Tigers/Elephants framework to surface real risks and create mitigation plans.

## Invocation

```
/pre-mortem [paste or upload a PRD, launch plan, or feature spec]
/pre-mortem We're launching a self-serve billing portal next month
```

## Workflow

### Step 1: Accept the Plan

Accept in any format: PRD, feature spec, launch plan, project brief, or verbal description. The more detail provided, the sharper the risk analysis.

### Step 2: Risk Identification

Apply the **pre-mortem** skill:

Imagine the product has launched and failed. Generate risks across categories:
- **Technical**: Performance, scalability, integration failures, data issues
- **User**: Adoption barriers, usability problems, unmet expectations
- **Business**: Revenue impact, competitive response, market timing
- **Operational**: Support load, documentation gaps, training needs
- **Dependencies**: Third-party services, cross-team handoffs, regulatory

### Step 3: Classify Risks

Categorize each risk:

**Tigers** — Real, substantive risks that could cause failure
- Assess severity: Launch-blocking / Fast-follow / Track
- For launch-blocking Tigers: immediate mitigation required
- For fast-follow Tigers: plan to address within first sprint post-launch
- For track Tigers: monitor but don't delay launch

**Paper Tigers** — Risks that feel scary but are overblown
- Explain why the concern is manageable
- Note what would need to change for this to become a real Tiger

**Elephants** — Unspoken risks the team knows about but avoids discussing
- Surface political, organizational, or uncomfortable risks
- Frame constructively with suggested conversation starters

### Step 4: Generate Pre-Mortem Report

```
## Pre-Mortem: [Feature/Launch]

**Date**: [today]
**Status**: [Draft / Reviewed]

### Risk Summary
- **Tigers**: [count] ([launch-blocking], [fast-follow], [track])
- **Paper Tigers**: [count]
- **Elephants**: [count]

### Launch-Blocking Tigers
| # | Risk | Likelihood | Impact | Mitigation | Owner | Deadline |
|---|------|-----------|--------|-----------|-------|----------|

### Fast-Follow Tigers
| # | Risk | Likelihood | Impact | Planned Response | Owner |
|---|------|-----------|--------|-----------------|-------|

### Track Tigers
[Risks to monitor post-launch with trigger conditions]

### Paper Tigers
[Concerns that seem big but are manageable — with reasoning]

### Elephants in the Room
[Uncomfortable truths the team should discuss]

### Go/No-Go Checklist
- [ ] All launch-blocking Tigers mitigated
- [ ] Fast-follow plan documented and assigned
- [ ] Monitoring in place for Track Tigers
- [ ] Rollback plan defined
- [ ] Support team briefed
```

Save as markdown.

### Step 5: Offer Next Steps

- "Want me to **update the PRD** with risk mitigations?"
- "Should I **create test scenarios** for the riskiest areas?"
- "Want me to **draft a launch checklist** from these findings?"

## Notes

- The best pre-mortems happen when the plan is 80% done — early enough to change course, late enough to have substance
- Push past the obvious risks — the most dangerous risks are the ones nobody mentions
- Elephants are the highest-value output — surfacing what the team avoids discussing
- For each Tiger, the mitigation should be specific and assignable, not "be careful"
- If the pre-mortem reveals too many launch-blocking Tigers, recommend delaying or phasing the launch


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/phuryn-pm-skills/pm-execution/commands/red-team-prd.md =====

---
description: Red-team a PRD, roadmap, or strategy — attack its load-bearing assumptions and return the cheapest test for each before you commit
argument-hint: "<PRD, roadmap, strategy, or the current doc>"
---

# /red-team-prd -- Attack the Plan Before Reality Does

Most plans only survived polite feedback. This command finds the assumptions that would make yours fail, attacks them honestly, and hands you the cheapest test for each — so you can kill a bad bet this week instead of at launch.

## Invocation

```
/red-team-prd [paste or upload a PRD, roadmap, or strategy]
/red-team-prd Prioritize AI onboarding — activation is our bottleneck
/red-team-prd the current doc
```

## Workflow

### Step 1: Accept the Plan

Take it in any form — PRD, roadmap, strategy memo, one-line bet, or an uploaded doc. If the user says "the current doc," use the document in context.

### Step 2: Red-Team It

Apply the **strategy-red-team** skill:

- Extract every claim; keep only the **load-bearing** ones (false → plan dies).
- **Steelman each, then attack the steelman** — no strawmen.
- Write each failure mode as "**Fails if ___**."
- Rank by **(impact if wrong) × (likelihood wrong) × (cheapness to test)**.
- Default "the risk is real" unless the plan cites evidence against it — but **say plainly what's well-reasoned**, and never fabricate a weakness.

### Step 3: Return the Output

```
## Red-Team: [plan in one line]

### Top Kill-Assumptions (ranked)
- **Claim:** [load-bearing assertion]
  - **Fails if:** [concrete, falsifiable]
  - **Evidence to get this week:** [specific]
  - **Kill criterion:** [threshold]
  - **Cheapest test:** [smallest experiment]
[3–5 max]

### What's Well-Reasoned
[State it explicitly — don't manufacture doubt.]

### What I Couldn't Assess
[Where the plan didn't give enough to judge.]
```

### Step 4: Offer Next Steps

- "Want me to **turn the top kill-assumption into an experiment** you can run this week?"
- "Should I **run a pre-mortem** to complement this — imagine it already failed and trace the path?"
- "Want me to **rewrite the riskiest section** of the plan to address what survived?"

## Notes

- Lead with the ranking — the cheapest high-impact test is the whole point.
- Five real kill-assumptions with tests beat twenty generic
