Read this local source bundle and create complete EMBIZ-specific operational doctrine.

Repository: tolaria
Local source: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/tolaria
Bundle: /root/embroidery_business_agent_system/directives/repo_adapted_embiz_doctrine/_prompts/tolaria_SOURCE_BUNDLE.md

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
# tolaria EMBIZ ADAPTED DOCTRINE
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


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/tolaria/scripts/generate_demo_vault.py =====

#!/usr/bin/env python3
"""Generate a large synthetic vault for scale and performance checks.

Creates a realistic 2-year knowledge vault (Q1 2024 - Q4 2025) for a
fictional persona based on Luca Rossi, founder of Refactoring.

The curated `demo-vault-v2/` fixture is intentionally small and lives in git.
This script generates the larger corpus on demand outside that checked-in QA
fixture.

Usage:
  python3 scripts/generate_demo_vault.py
  python3 scripts/generate_demo_vault.py --output /tmp/demo-vault-large
"""

import argparse
import random
import shutil
from datetime import date, timedelta
from pathlib import Path

random.seed(42)

DEFAULT_VAULT = Path(__file__).resolve().parent.parent / "generated-fixtures" / "demo-vault-large"
VAULT = DEFAULT_VAULT
SUBDIRS = [
    "area", "responsibility", "measure", "target", "goal", "year",
    "quarter", "month", "project", "experiment", "procedure", "task",
    "person", "topic", "event", "evergreen", "note",
]
COUNTS: dict[str, int] = {}

# ── Quarter / month mappings ─────────────────────────────────────
QUARTER_SLUGS = ["24q1", "24q2", "24q3", "24q4", "25q1", "25q2", "25q3", "25q4"]
Q_YEAR = {q: ("2024" if q.startswith("24") else "2025") for q in QUARTER_SLUGS}
Q_LABEL = {
    "24q1": "Q1 2024", "24q2": "Q2 2024", "24q3": "Q3 2024", "24q4": "Q4 2024",
    "25q1": "Q1 2025", "25q2": "Q2 2025", "25q3": "Q3 2025", "25q4": "Q4 2025",
}
Q_MONTHS = {
    "24q1": ["2024-01", "2024-02", "2024-03"], "24q2": ["2024-04", "2024-05", "2024-06"],
    "24q3": ["2024-07", "2024-08", "2024-09"], "24q4": ["2024-10", "2024-11", "2024-12"],
    "25q1": ["2025-01", "2025-02", "2025-03"], "25q2": ["2025-04", "2025-05", "2025-06"],
    "25q3": ["2025-07", "2025-08", "2025-09"], "25q4": ["2025-10", "2025-11", "2025-12"],
}
Q_START = {
    "24q1": "2024-01-01", "24q2": "2024-04-01", "24q3": "2024-07-01", "24q4": "2024-10-01",
    "25q1": "2025-01-01", "25q2": "2025-04-01", "25q3": "2025-07-01", "25q4": "2025-10-01",
}
MONTH_NAMES = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]
MONTH_RATINGS = ["😄", "😄", "🤩", "😄", "😐", "🤩", "😄", "😄",
                 "🤩", "😄", "😐", "😄", "🤩", "😄", "😄", "🤩",
                 "😄", "😐", "🤩", "😄", "😄", "🤩", "😄", "😄"]

# Subscriber trajectory: (start, end) per quarter
SUB_TRAJ = {
    "24q1": (35000, 38000), "24q2": (38000, 42000),
    "24q3": (42000, 47000), "24q4": (47000, 53000),
    "25q1": (53000, 59000), "25q2": (59000, 66000),
    "25q3": (66000, 75000), "25q4": (75000, 85000),
}
# Revenue trajectory: monthly EUR at quarter end
REV_TRAJ = {
    "24q1": 8000, "24q2": 10000, "24q3": 12000, "24q4": 14000,
    "25q1": 15000, "25q2": 17000, "25q3": 19000, "25q4": 22000,
}

# ── Helpers ──────────────────────────────────────────────────────
_UNQUOTED = {
    "Open", "Done", "Draft", "Published", "Abandoned", "Behind",
    "Year", "Quarter", "Month", "Area", "Responsibility", "Measure",
    "Target", "Goal", "Project", "Experiment", "Procedure", "Task",
    "Person", "Topic", "Event", "Evergreen", "Note",
    "Weekly", "Bi-weekly", "Monthly", "Quarterly", "Daily",
}


def wl(slug: str) -> str:
    return f"[[{slug}]]"


def fm(fields: dict) -> str:
    lines = ["---"]
    for k, v in fields.items():
        if isinstance(v, list):
            inner = ", ".join(f'"{i}"' for i in v)
            lines.append(f"{k}: [{inner}]")
        elif isinstance(v, (int, float)):
            lines.append(f"{k}: {v}")
        elif isinstance(v, str) and v in _UNQUOTED:
            lines.append(f"{k}: {v}")
        else:
            lines.append(f'{k}: "{v}"')
    lines.append("---")
    return "\n".join(lines)


def write_md(subdir: str, slug: str, fields: dict, body: str):
    path = VAULT / subdir / f"{slug}.md"
    path.write_text(fm(fields) + "\n" + body.rstrip() + "\n", encoding="utf-8")
    COUNTS[subdir] = COUNTS.get(subdir, 0) + 1


def month_slug_to_q(ms: str) -> str:
    y, m = ms.split("-")
    qi = (int(m) - 1) // 3 + 1
    return f"{y[2:]}{'' if y == '2024' else ''}q{qi}" if y == "2024" else f"{y[2:]}q{qi}"


# ── AREAS ────────────────────────────────────────────────────────
# (slug, name, responsibility_slugs)
AREAS = [
    ("area-building", "Building", [
        "responsibility-grow-newsletter", "responsibility-sponsorships",
        "responsibility-content-production", "responsibility-podcast",
        "responsibility-team-management"]),
    ("area-health", "Health", ["responsibility-health-fitness"]),
    ("area-personal", "Personal", []),
    ("area-learning", "Learning", ["responsibility-learning"]),
    ("area-finance", "Finance", ["responsibility-personal-finance"]),
]

# ── RESPONSIBILITIES ─────────────────────────────────────────────
# (slug, name, area, measures, procedures, body)
RESPONSIBILITIES = [
    ("responsibility-grow-newsletter", "Grow Newsletter", "area-building",
     ["measure-subscribers", "measure-open-rate"],
     ["procedure-monthly-subscriber-metrics", "procedure-referral-program",
      "procedure-welcome-email-sequence", "procedure-seo-content-optimization"],
     "Growing the Refactoring newsletter subscriber base through organic content, SEO, referrals, and strategic partnerships.\n\n## KPIs\n- Subscribers: target 100k by end 2025\n- Open rate: maintain >45%"),
    ("responsibility-sponsorships", "Sponsorships", "area-building",
     ["measure-sponsorship-mrr", "measure-close-rate"],
     ["procedure-monthly-sponsor-report", "procedure-quarterly-sponsor-outreach",
      "procedure-sponsor-onboarding", "procedure-invoice-processing", "procedure-sponsor-renewal"],
     "Selling and managing sponsorships for Refactoring. Building long-term relationships with B2B tech companies.\n\n## KPIs\n- MRR: grow from €8k to €22k\n- Close rate: maintain >30%"),
    ("responsibility-content-production", "Content Production", "area-building",
     ["measure-articles-per-week", "measure-essay-quality-score"],
     ["procedure-weekly-newsletter", "procedure-monthly-pillar-planning",
      "procedure-social-media-scheduling", "procedure-newsletter-ab-testing",
      "procedure-content-calendar-review", "procedure-editorial-review",
      "procedure-evergreen-content-audit", "procedure-newsletter-metrics-weekly"],
     "Publishing weekly essays and newsletter editions. Maintaining high editorial quality while shipping consistently.\n\n## KPIs\n- Articles per week: 1 newsletter + 1 essay minimum\n- Quality score: reader feedback >4.5/5"),
    ("responsibility-podcast", "Podcast", "area-building",
     ["measure-podcast-downloads", "measure-podcast-episodes-per-month"],
     ["procedure-podcast-recording", "procedure-podcast-guest-outreach",
      "procedure-podcast-editing", "procedure-podcast-show-notes", "procedure-podcast-analytics"],
     "Running the Refactoring podcast — bi-weekly episodes with tech leaders on engineering culture, leadership, and building.\n\n## KPIs\n- Downloads per episode: target 5k+\n- Episodes per month: 2"),
    ("responsibility-team-management", "Team Management", "area-building",
     ["measure-team-nps", "measure-task-completion-rate"],
     ["procedure-weekly-team-sync", "procedure-biweekly-1on1-matteo",
      "procedure-biweekly-1on1-paco", "procedure-biweekly-1on1-sara",
      "procedure-quarterly-team-retro"],
     "Managing Matteo (partnerships), Paco (operations), and Sara (editor). Building a small but high-performing team.\n\n## KPIs\n- Team NPS: >8\n- Task completion rate: >85%"),
    ("responsibility-health-fitness", "Health & Fitness", "area-health",
     ["measure-resting-hr", "measure-cycling-km-per-month"],
     ["procedure-weekly-cycling-block", "procedure-gym-routine",
      "procedure-monthly-health-review", "procedure-race-preparation"],
     "Staying fit through cycling, gym, and good nutrition. Training for gran fondos and maintaining energy for work.\n\n## KPIs\n- Resting HR: <55 bpm\n- Cycling: 300+ km/month in season"),
    ("responsibility-personal-finance", "Personal Finance", "area-finance",
     ["measure-net-worth", "measure-savings-rate"],
     ["procedure-monthly-portfolio-review", "procedure-quarterly-financial-planning"],
     "Managing investments, savings, and financial planning. Building long-term wealth through index funds and diversification.\n\n## KPIs\n- Savings rate: >30% of income\n- Net worth: track monthly"),
    ("responsibility-learning", "Learning", "area-learning",
     ["measure-books-per-month", "measure-evergreen-notes-created"],
     ["procedure-weekly-reading-session", "procedure-evergreen-note-writing"],
     "Reading widely, studying deeply, and creating evergreen notes. Focused on non-fiction: business, technology, science, and self-improvement.\n\n## KPIs\n- Books per month: 2+\n- Evergreen notes: 3+ per month"),
]

# ── MEASURES ─────────────────────────────────────────────────────
# (slug, name, responsibility, unit)
MEASURES = [
    ("measure-subscribers", "Newsletter Subscribers", "responsibility-grow-newsletter", "subscribers"),
    ("measure-open-rate", "Newsletter Open Rate", "responsibility-grow-newsletter", "percent"),
    ("measure-sponsorship-mrr", "Sponsorship MRR", "responsibility-sponsorships", "EUR/month"),
    ("measure-close-rate", "Sponsorship Close Rate", "responsibility-sponsorships", "percent"),
    ("measure-articles-per-week", "Articles Per Week", "responsibility-content-production", "articles"),
    ("measure-essay-quality-score", "Essay Quality Score", "responsibility-content-production", "score (1-5)"),


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/tolaria/.chunk/config.json =====

{
  "commands": [
    {
      "name": "lint",
      "run": "pnpm lint",
      "role": "gate",
      "fileExt": ".ts,.tsx,.js,.jsx,.mjs,.json",
      "timeout": 120,
      "limit": 3
    },
    {
      "name": "typecheck",
      "run": "npx tsc --noEmit",
      "role": "gate",
      "fileExt": ".ts,.tsx",
      "timeout": 180,
      "limit": 3
    },
    {
      "name": "build",
      "run": "pnpm build",
      "role": "gate",
      "fileExt": ".ts,.tsx,.css,.html,.json",
      "timeout": 300,
      "limit": 2
    },
    {
      "name": "frontend-coverage",
      "run": "pnpm test:coverage --silent",
      "role": "gate",
      "fileExt": ".ts,.tsx",
      "timeout": 600,
      "limit": 2
    },
    {
      "name": "rust-lint",
      "run": "cargo clippy --manifest-path=src-tauri/Cargo.toml -- -D warnings && cargo fmt --manifest-path=src-tauri/Cargo.toml -- --check",
      "role": "gate",
      "fileExt": ".rs",
      "timeout": 300,
      "limit": 2
    },
    {
      "name": "rust-coverage",
      "run": "cargo llvm-cov --manifest-path src-tauri/Cargo.toml --no-clean --ignore-filename-regex \"lib\\.rs|main\\.rs|menu\\.rs\" --fail-under-lines 85 -- --test-threads=1",
      "role": "gate",
      "fileExt": ".rs",
      "timeout": 900,
      "limit": 1
    },
    {
      "name": "smoke-1",
      "run": "bash .chunk/run-playwright-smoke.sh 1/8",
      "role": "gate",
      "fileExt": ".ts,.tsx",
      "timeout": 240,
      "limit": 1
    },
    {
      "name": "smoke-2",
      "run": "bash .chunk/run-playwright-smoke.sh 2/8",
      "role": "gate",
      "fileExt": ".ts,.tsx",
      "timeout": 240,
      "limit": 1
    },
    {
      "name": "smoke-3",
      "run": "bash .chunk/run-playwright-smoke.sh 3/8",
      "role": "gate",
      "fileExt": ".ts,.tsx",
      "timeout": 240,
      "limit": 1
    },
    {
      "name": "smoke-4",
      "run": "bash .chunk/run-playwright-smoke.sh 4/8",
      "role": "gate",
      "fileExt": ".ts,.tsx",
      "timeout": 240,
      "limit": 1
    },
    {
      "name": "smoke-5",
      "run": "bash .chunk/run-playwright-smoke.sh 5/8",
      "role": "gate",
      "fileExt": ".ts,.tsx",
      "timeout": 240,
      "limit": 1
    },
    {
      "name": "smoke-6",
      "run": "bash .chunk/run-playwright-smoke.sh 6/8",
      "role": "gate",
      "fileExt": ".ts,.tsx",
      "timeout": 240,
      "limit": 1
    },
    {
      "name": "smoke-7",
      "run": "bash .chunk/run-playwright-smoke.sh 7/8",
      "role": "gate",
      "fileExt": ".ts,.tsx",
      "timeout": 240,
      "limit": 1
    },
    {
      "name": "smoke-8",
      "run": "bash .chunk/run-playwright-smoke.sh 8/8",
      "role": "gate",
      "fileExt": ".ts,.tsx",
      "timeout": 240,
      "limit": 1
    }
  ],
  "stopHookMaxAttempts": 2,
  "vcs": {
    "org": "refactoringhq",
    "repo": "tolaria"
  },
  "orgID": "39f93336-5295-4c6c-845f-e692c1d3f968",
  "environment": {
    "stack": "javascript-rust-tauri",
    "setup": [
      {
        "name": "system",
        "command": "sudo apt-get update && sudo apt-get install -y --no-install-recommends build-essential curl file git libwebkit2gtk-4.1-dev libxdo-dev libssl-dev libayatana-appindicator3-dev librsvg2-dev libsoup-3.0-dev patchelf pkg-config unzip wget xvfb && sudo rm -rf /var/lib/apt/lists/*"
      },
      {
        "name": "rust",
        "command": "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --profile minimal && . \"$HOME/.cargo/env\" && rustup default stable && rustup component add clippy rustfmt && cargo install cargo-llvm-cov --locked"
      },
      {
        "name": "node",
        "command": "curl -fsSL https://nodejs.org/dist/v26.3.0/node-v26.3.0-linux-x64.tar.xz | sudo tar -xJ -C /usr/local --strip-components=1 && node --version && npm --version"
      },
      {
        "name": "pnpm",
        "command": "sudo npm install -g pnpm@10.33.0 && pnpm --version"
      },
      {
        "name": "install",
        "command": "mkdir -p \"$HOME/Documents\" && pnpm install --frozen-lockfile && . \"$HOME/.cargo/env\" && cargo fetch --manifest-path src-tauri/Cargo.toml"
      },
      {
        "name": "playwright-deps",
        "command": "pnpm exec playwright install-deps chromium"
      },
      {
        "name": "playwright",
        "command": "node .chunk/install-playwright-browsers.mjs"
      }
    ],
    "image": "cimg/node",
    "image_version": "26.3.0"
  }
}


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/tolaria/.claude/settings.local.json =====

{
  "permissions": {
    "allow": [
      "mcp__codescene__*",
      "Read(*)",
      "Bash(cat*)",
      "Bash(ls*)",
      "Write(*)"
    ]
  }
}


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/tolaria/biome.json =====

{
  "$schema": "https://biomejs.dev/schemas/2.4.15/schema.json",
  "files": {
    "includes": [
      "**",
      "!src-tauri/gen/**",
      "!target/**",
      "!dist/**",
      "!node_modules/**"
    ]
  },
  "css": {
    "parser": {
      "tailwindDirectives": true
    }
  },
  "overrides": [
    {
      "includes": ["site/**/*.vue"],
      "linter": {
        "rules": {
          "correctness": {
            "noUnusedImports": "off",
            "noUnusedVariables": "off",
            "useHookAtTopLevel": "off"
          }
        }
      }
    }
  ],
  "linter": {
    "rules": {
      "correctness": {
        "useQwikValidLexicalScope": "off"
      }
    }
  }
}


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/tolaria/components.json =====

{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "new-york",
  "rsc": false,
  "tsx": true,
  "tailwind": {
    "config": "",
    "css": "src/index.css",
    "baseColor": "neutral",
    "cssVariables": true,
    "prefix": ""
  },
  "aliases": {
    "components": "@/components",
    "utils": "@/lib/utils",
    "ui": "@/components/ui",
    "lib": "@/lib",
    "hooks": "@/hooks"
  },
  "iconLibrary": "phosphor"
}


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/tolaria/demo-vault-v2/.fixture-manifest.json =====

{
  "name": "Tolaria QA fixture",
  "purpose": "Curated local vault for native QA and developer flows. This is not the public Getting Started starter vault.",
  "large_fixture": {
    "generator": "python3 scripts/generate_demo_vault.py",
    "default_output": "generated-fixtures/demo-vault-large"
  },
  "scenarios": [
    {
      "id": "exact-match-search",
      "reason": "Quick Open should rank the exact title 'Writing' above prefix matches.",
      "files": [
        "topic-writing.md",
        "writing-for-clarity-vs-writing-for-credit.md",
        "writing-weekly-rhythm.md"
      ]
    },
    {
      "id": "relationship-rendering",
      "reason": "Relationship keys should render in the inspector instead of as plain properties.",
      "files": [
        "responsibility-sponsorships.md",
        "measure-sponsorship-mrr.md",
        "measure-close-rate.md",
        "procedure-quarterly-sponsor-outreach.md",
        "procedure-sponsor-onboarding.md",
        "24q4-laputa-start.md",
        "24q4.md",
        "person-luca-rossi.md"
      ]
    },
    {
      "id": "project-navigation",
      "reason": "Projects, quarters, and a saved view give keyboard QA a compact but representative browsing path.",
      "files": [
        "24q4.md",
        "25q1.md",
        "25q2.md",
        "24q4-laputa-start.md",
        "25q1-laputa-v1.md",
        "25q2-laputa-v2.md",
        "views/active-projects.yml"
      ]
    },
    {
      "id": "attachment-rendering",
      "reason": "A note with a real binary attachment keeps image/block QA anchored to the fixture.",
      "files": [
        "laputa-qa-reference.md",
        "attachments/laputa-reference.png"
      ]
    },
    {
      "id": "rtl-mixed-direction",
      "reason": "Arabic and mixed English/Arabic paragraphs keep rich editor and raw editor BiDi QA anchored to the fixture.",
      "files": [
        "rtl-mixed-direction-qa.md"
      ]
    }
  ]
}


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/tolaria/mcp-server/package-lock.json =====

{
  "name": "tolaria-mcp-server",
  "version": "0.1.0",
  "lockfileVersion": 3,
  "requires": true,
  "packages": {
    "": {
      "name": "tolaria-mcp-server",
      "version": "0.1.0",
      "dependencies": {
        "@modelcontextprotocol/sdk": "^1.0.0",
        "gray-matter": "^4.0.3",
        "ws": "^8.20.1"
      }
    },
    "node_modules/@hono/node-server": {
      "version": "1.19.13",
      "resolved": "https://registry.npmjs.org/@hono/node-server/-/node-server-1.19.13.tgz",
      "integrity": "sha512-TsQLe4i2gvoTtrHje625ngThGBySOgSK3Xo2XRYOdqGN1teR8+I7vchQC46uLJi8OF62YTYA3AhSpumtkhsaKQ==",
      "license": "MIT",
      "engines": {
        "node": ">=18.14.1"
      },
      "peerDependencies": {
        "hono": "^4"
      }
    },
    "node_modules/@modelcontextprotocol/sdk": {
      "version": "1.26.0",
      "resolved": "https://registry.npmjs.org/@modelcontextprotocol/sdk/-/sdk-1.26.0.tgz",
      "integrity": "sha512-Y5RmPncpiDtTXDbLKswIJzTqu2hyBKxTNsgKqKclDbhIgg1wgtf1fRuvxgTnRfcnxtvvgbIEcqUOzZrJ6iSReg==",
      "license": "MIT",
      "dependencies": {
        "@hono/node-server": "^1.19.9",
        "ajv": "^8.17.1",
        "ajv-formats": "^3.0.1",
        "content-type": "^1.0.5",
        "cors": "^2.8.5",
        "cross-spawn": "^7.0.5",
        "eventsource": "^3.0.2",
        "eventsource-parser": "^3.0.0",
        "express": "^5.2.1",
        "express-rate-limit": "^8.2.1",
        "hono": "^4.11.4",
        "jose": "^6.1.3",
        "json-schema-typed": "^8.0.2",
        "pkce-challenge": "^5.0.0",
        "raw-body": "^3.0.0",
        "zod": "^3.25 || ^4.0",
        "zod-to-json-schema": "^3.25.1"
      },
      "engines": {
        "node": ">=18"
      },
      "peerDependencies": {
        "@cfworker/json-schema": "^4.1.1",
        "zod": "^3.25 || ^4.0"
      },
      "peerDependenciesMeta": {
        "@cfworker/json-schema": {
          "optional": true
        },
        "zod": {
          "optional": false
        }
      }
    },
    "node_modules/accepts": {
      "version": "2.0.0",
      "resolved": "https://registry.npmjs.org/accepts/-/accepts-2.0.0.tgz",
      "integrity": "sha512-5cvg6CtKwfgdmVqY1WIiXKc3Q1bkRqGLi+2W/6ao+6Y7gu/RCwRuAhGEzh5B4KlszSuTLgZYuqFqo5bImjNKng==",
      "license": "MIT",
      "dependencies": {
        "mime-types": "^3.0.0",
        "negotiator": "^1.0.0"
      },
      "engines": {
        "node": ">= 0.6"
      }
    },
    "node_modules/ajv": {
      "version": "8.18.0",
      "resolved": "https://registry.npmjs.org/ajv/-/ajv-8.18.0.tgz",
      "integrity": "sha512-PlXPeEWMXMZ7sPYOHqmDyCJzcfNrUr3fGNKtezX14ykXOEIvyK81d+qydx89KY5O71FKMPaQ2vBfBFI5NHR63A==",
      "license": "MIT",
      "dependencies": {
        "fast-deep-equal": "^3.1.3",
        "fast-uri": "^3.0.1",
        "json-schema-traverse": "^1.0.0",
        "require-from-string": "^2.0.2"
      },
      "funding": {
        "type": "github",
        "url": "https://github.com/sponsors/epoberezkin"
      }
    },
    "node_modules/ajv-formats": {
      "version": "3.0.1",
      "resolved": "https://registry.npmjs.org/ajv-formats/-/ajv-formats-3.0.1.tgz",
      "integrity": "sha512-8iUql50EUR+uUcdRQ3HDqa6EVyo3docL8g5WJ3FNcWmu62IbkGUue/pEyLBW8VGKKucTPgqeks4fIU1DA4yowQ==",
      "license": "MIT",
      "dependencies": {
        "ajv": "^8.0.0"
      },
      "peerDependencies": {
        "ajv": "^8.0.0"
      },
      "peerDependenciesMeta": {
        "ajv": {
          "optional": true
        }
      }
    },
    "node_modules/argparse": {
      "version": "1.0.10",
      "resolved": "https://registry.npmjs.org/argparse/-/argparse-1.0.10.tgz",
      "integrity": "sha512-o5Roy6tNG4SL/FOkCAN6RzjiakZS25RLYFrcMttJqbdd8BWrnA+fGz57iN5Pb06pvBGvl5gQ0B48dJlslXvoTg==",
      "license": "MIT",
      "dependencies": {
        "sprintf-js": "~1.0.2"
      }
    },
    "node_modules/body-parser": {
      "version": "2.2.2",
      "resolved": "https://registry.npmjs.org/body-parser/-/body-parser-2.2.2.tgz",
      "integrity": "sha512-oP5VkATKlNwcgvxi0vM0p/D3n2C3EReYVX+DNYs5TjZFn/oQt2j+4sVJtSMr18pdRr8wjTcBl6LoV+FUwzPmNA==",
      "license": "MIT",
      "dependencies": {
        "bytes": "^3.1.2",
        "content-type": "^1.0.5",
        "debug": "^4.4.3",
        "http-errors": "^2.0.0",
        "iconv-lite": "^0.7.0",
        "on-finished": "^2.4.1",
        "qs": "^6.14.1",
        "raw-body": "^3.0.1",
        "type-is": "^2.0.1"
      },
      "engines": {
        "node": ">=18"
      },
      "funding": {
        "type": "opencollective",
        "url": "https://opencollective.com/express"
      }
    },
    "node_modules/bytes": {
      "version": "3.1.2",
      "resolved": "https://registry.npmjs.org/bytes/-/bytes-3.1.2.tgz",
      "integrity": "sha512-/Nf7TyzTx6S3yRJObOAV7956r8cr2+Oj8AC5dt8wSP3BQAoeX58NoHyCU8P8zGkNXStjTSi6fzO6F0pBdcYbEg==",
      "license": "MIT",
      "engines": {
        "node": ">= 0.8"
      }
    },
    "node_modules/call-bind-apply-helpers": {
      "version": "1.0.2",
      "resolved": "https://registry.npmjs.org/call-bind-apply-helpers/-/call-bind-apply-helpers-1.0.2.tgz",
      "integrity": "sha512-Sp1ablJ0ivDkSzjcaJdxEunN5/XvksFJ2sMBFfq6x0ryhQV/2b/KwFe21cMpmHtPOSij8K99/wSfoEuTObmuMQ==",
      "license": "MIT",
      "dependencies": {
        "es-errors": "^1.3.0",
        "function-bind": "^1.1.2"
      },
      "engines": {
        "node": ">= 0.4"
      }
    },
    "node_modules/call-bound": {
      "version": "1.0.4",
      "resolved": "https://registry.npmjs.org/call-bound/-/call-bound-1.0.4.tgz",
      "integrity": "sha512-+ys997U96po4Kx/ABpBCqhA9EuxJaQWDQg7295H4hBphv3IZg0boBKuwYpt4YXp6MZ5AmZQnU/tyMTlRpaSejg==",
      "license": "MIT",
      "dependencies": {
        "call-bind-apply-helpers": "^1.0.2",
        "get-intrinsic": "^1.3.0"
      },
      "engines": {
        "node": ">= 0.4"
      },


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/tolaria/mcp-server/package.json =====

{
  "name": "tolaria-mcp-server",
  "version": "0.1.0",
  "description": "MCP server for Tolaria vault operations",
  "type": "module",
  "main": "index.js",
  "scripts": {
    "start": "node index.js",
    "test": "node --test test.js tool-service.test.js"
  },
  "dependencies": {
    "@modelcontextprotocol/sdk": "^1.0.0",
    "gray-matter": "^4.0.3",
    "ws": "^8.20.1"
  },
  "overrides": {
    "@hono/node-server": "1.19.13",
    "express-rate-limit": "8.2.2",
    "fast-uri": "3.1.2",
    "hono": "4.12.21",
    "qs": "6.15.2",
    "ip-address": "10.1.1",
    "path-to-regexp": "8.4.0"
  }
}


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/tolaria/package.json =====

{
  "name": "tolaria",
  "private": true,
  "license": "AGPL-3.0-or-later",
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "agent-docs": "node scripts/build-agent-docs.mjs",
    "bundle-mcp": "node scripts/bundle-mcp-server.mjs",
    "docs:dev": "vitepress dev site --host 127.0.0.1",
    "docs:build": "pnpm agent-docs && vitepress build site",
    "docs:preview": "vitepress preview site --host 127.0.0.1",
    "lint": "eslint . --max-warnings=0",
    "l10n:translate": "lara-cli translate",
    "l10n:translate:force": "lara-cli translate --force",
    "l10n:validate": "node scripts/validate-locales.mjs",
    "preview": "vite preview",
    "tauri": "tauri",
    "test": "vitest run",
    "test:watch": "vitest",
    "test:e2e": "playwright test",
    "playwright:smoke": "playwright test --config playwright.smoke.config.ts tests/smoke/autosave-low-end-typing.spec.ts tests/smoke/create-note-backing-file.spec.ts tests/smoke/delete-note-nonblocking.spec.ts tests/smoke/example.spec.ts tests/smoke/fix-crash-create-note.spec.ts tests/smoke/quick-open-create-note.spec.ts tests/smoke/save-before-note-switch.spec.ts tests/smoke/h1-untitled-auto-rename.spec.ts tests/smoke/keyboard-command-routing.spec.ts tests/smoke/missing-string-metadata-open-note.spec.ts tests/smoke/multibyte-search-snippet.spec.ts tests/smoke/pull-refresh-open-note.spec.ts tests/smoke/wikilink-path-fix.spec.ts",
    "playwright:regression": "playwright test tests/smoke/",
    "playwright:integration": "playwright test --config playwright.integration.config.ts",
    "test:coverage": "node scripts/run-vitest-coverage.mjs",
    "prepare": "husky"
  },
  "dependencies": {
    "@anthropic-ai/sdk": "^0.78.0",
    "@blocknote/code-block": "^0.46.2",
    "@blocknote/core": "^0.46.2",
    "@blocknote/mantine": "^0.46.2",
    "@blocknote/react": "^0.46.2",
    "@codemirror/commands": "^6.10.2",
    "@codemirror/lang-markdown": "^6.5.0",
    "@codemirror/lang-yaml": "^6.1.2",
    "@codemirror/language": "^6.12.2",
    "@codemirror/state": "^6.5.4",
    "@codemirror/view": "^6.39.16",
    "@dnd-kit/core": "^6.3.1",
    "@dnd-kit/sortable": "^10.0.0",
    "@dnd-kit/utilities": "^3.2.2",
    "@lezer/highlight": "^1.2.3",
    "@mantine/core": "^8.3.14",
    "@phosphor-icons/react": "^2.1.10",
    "@radix-ui/react-dialog": "^1.1.15",
    "@radix-ui/react-dropdown-menu": "^2.1.16",
    "@radix-ui/react-select": "^2.2.6",
    "@radix-ui/react-separator": "^1.1.8",
    "@radix-ui/react-slot": "^1.2.4",
    "@radix-ui/react-tabs": "^1.1.13",
    "@radix-ui/react-tooltip": "^1.2.8",
    "@sentry/react": "^10.47.0",
    "@shikijs/langs": "3.23.0",
    "@tailwindcss/vite": "^4.1.18",
    "@tauri-apps/api": "^2.10.1",
    "@tauri-apps/plugin-deep-link": "2.4.9",
    "@tauri-apps/plugin-dialog": "^2.6.0",
    "@tauri-apps/plugin-opener": "^2.5.3",
    "@tauri-apps/plugin-process": "^2.3.1",
    "@tauri-apps/plugin-updater": "^2.10.0",
    "@tldraw/assets": "4.5.10",
    "class-variance-authority": "^0.7.1",
    "clsx": "^2.1.1",
    "date-fns": "^4.1.0",
    "dompurify": "3.4.2",
    "katex": "^0.16.28",
    "mermaid": "^11.14.0",
    "posthog-js": "^1.363.5",
    "radix-ui": "^1.4.3",
    "react": "^19.2.0",
    "react-day-picker": "^9.13.2",
    "react-dom": "^19.2.0",
    "react-markdown": "^10.1.0",
    "react-virtuoso": "^4.18.1",
    "rehype-highlight": "^7.0.2",
    "remark-gfm": "^4.0.1",
    "safe-regex2": "5.1.1",
    "tailwind-merge": "^3.4.1",
    "tailwindcss": "^4.1.18",
    "tldraw": "^4.5.10",
    "tw-animate-css": "^1.4.0",
    "unicode-emoji-json": "^0.8.0"
  },
  "devDependencies": {
    "@eslint/js": "^9.39.1",
    "@playwright/test": "^1.58.2",
    "@tauri-apps/cli": "^2.10.0",
    "@testing-library/jest-dom": "^6.9.1",
    "@testing-library/react": "^16.3.2",
    "@translated/lara-cli": "^1.3.2",
    "@types/node": "^24.10.1",
    "@types/react": "^19.2.7",
    "@types/react-dom": "^19.2.3",
    "@types/ws": "^8.18.1",
    "@vitejs/plugin-react": "^5.1.1",
    "@vitest/coverage-v8": "^4.0.18",
    "esbuild": "^0.27.3",
    "eslint": "^9.39.1",
    "eslint-plugin-react-hooks": "^7.0.1",
    "eslint-plugin-react-refresh": "^0.4.24",
    "globals": "^16.5.0",
    "gray-matter": "^4.0.3",
    "husky": "^9.1.7",
    "jsdom": "^28.0.0",
    "typescript": "~5.9.3",
    "typescript-eslint": "^8.48.0",
    "vite": "^7.3.2",
    "vitepress": "^1.6.4",
    "vitest": "^4.0.18",
    "ws": "^8.19.0"
  },
  "pnpm": {
    "overrides": {
      "@hono/node-server": "1.19.13",
      "express-rate-limit": "8.2.2",
      "hono": "4.12.18",
      "ip-address": "10.1.1",
      "mermaid>uuid": "11.1.1",
      "path-to-regexp": "8.4.0",
      "fast-uri": "3.1.2",
      "fast-xml-builder": "1.1.7",
      "flatted": "3.4.2",
      "minimatch@3.1.2": "3.1.5",
      "minimatch@3.1.3": "3.1.5",
      "minimatch@9.0.5": "9.0.9",
      "minimatch@9.0.6": "9.0.9",
      "picomatch": "4.0.4",
      "postcss": "8.5.10",
      "protobufjs": "7.5.6",
      "qs": "6.15.2",
      "rollup": "4.59.0",
      "undici": "7.25.0",
      "@blocknote/core>uuid": "11.1.1"
    },
    "patchedDependencies": {
      "@blocknote/core@0.46.2": "patches/@blocknote__core@0.46.2.patch",
      "@blocknote/react@0.46.2": "patches/@blocknote__react@0.46.2.patch",
      "@tiptap/extension-link@3.19.0": "patches/@tiptap__extension-link@3.19.0.patch",
      "prosemirror-tables@1.8.5": "patches/prosemirror-tables@1.8.5.patch",
      "@blocknote/code-block@0.46.2": "patches/@blocknote__code-block@0.46.2.patch"
    }
  }
}


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/tolaria/src-tauri/capabilities/default.json =====

{
  "$schema": "../gen/schemas/desktop-schema.json",
  "identifier": "default",
  "description": "enables the default permissions",
  "windows": [
    "main",
    "ai-workspace",
    "note-*"
  ],
  "platforms": ["linux", "macOS", "windows"],
  "permissions": [
    "core:default",
    "core:window:allow-create",
    "core:window:allow-start-dragging",
    "core:window:allow-start-resize-dragging",
    "core:window:allow-minimize",
    "core:window:allow-toggle-maximize",
    "core:window:allow-close",
    "core:window:allow-set-title",
    "core:webview:allow-create-webview-window",
    "core:event:default",
    "dialog:default",
    "deep-link:default",
    "updater:default",
    "process:default",
    "opener:default"
  ]
}


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/tolaria/src-tauri/capabilities/mobile.json =====

{
  "$schema": "../gen/schemas/mobile-schema.json",
  "identifier": "mobile",
  "description": "permissions for iOS/iPadOS",
  "windows": [
    "main"
  ],
  "platforms": ["iOS", "android"],
  "permissions": [
    "core:default",
    "core:window:allow-close",
    "core:window:allow-set-title",
    "dialog:default"
  ]
}


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/tolaria/src-tauri/gen/apple/Assets.xcassets/AppIcon.appiconset/Contents.json =====

{
  "images" : [
    {
      "size" : "20x20",
      "idiom" : "iphone",
      "filename" : "AppIcon-20x20@2x.png",
      "scale" : "2x"
    },
    {
      "size" : "20x20",
      "idiom" : "iphone",
      "filename" : "AppIcon-20x20@3x.png",
      "scale" : "3x"
    },
    {
      "size" : "29x29",
      "idiom" : "iphone",
      "filename" : "AppIcon-29x29@2x-1.png",
      "scale" : "2x"
    },
    {
      "size" : "29x29",
      "idiom" : "iphone",
      "filename" : "AppIcon-29x29@3x.png",
      "scale" : "3x"
    },
    {
      "size" : "40x40",
      "idiom" : "iphone",
      "filename" : "AppIcon-40x40@2x.png",
      "scale" : "2x"
    },
    {
      "size" : "40x40",
      "idiom" : "iphone",
      "filename" : "AppIcon-40x40@3x.png",
      "scale" : "3x"
    },
    {
      "size" : "60x60",
      "idiom" : "iphone",
      "filename" : "AppIcon-60x60@2x.png",
      "scale" : "2x"
    },
    {
      "size" : "60x60",
      "idiom" : "iphone",
      "filename" : "AppIcon-60x60@3x.png",
      "scale" : "3x"
    },
    {
      "size" : "20x20",
      "idiom" : "ipad",
      "filename" : "AppIcon-20x20@1x.png",
      "scale" : "1x"
    },
    {
      "size" : "20x20",
      "idiom" : "ipad",
      "filename" : "AppIcon-20x20@2x-1.png",
      "scale" : "2x"
    },
    {
      "size" : "29x29",
      "idiom" : "ipad",
      "filename" : "AppIcon-29x29@1x.png",
      "scale" : "1x"
    },
    {
      "size" : "29x29",
      "idiom" : "ipad",
      "filename" : "AppIcon-29x29@2x.png",
      "scale" : "2x"
    },
    {
      "size" : "40x40",
      "idiom" : "ipad",
      "filename" : "AppIcon-40x40@1x.png",
      "scale" : "1x"
    },
    {
      "size" : "40x40",
      "idiom" : "ipad",
      "filename" : "AppIcon-40x40@2x-1.png",
      "scale" : "2x"
    },
    {
      "size" : "76x76",
      "idiom" : "ipad",
      "filename" : "AppIcon-76x76@1x.png",
      "scale" : "1x"
    },
    {
      "size" : "76x76",
      "idiom" : "ipad",
      "filename" : "AppIcon-76x76@2x.png",
      "scale" : "2x"
    },
    {
      "size" : "83.5x83.5",
      "idiom" : "ipad",
      "filename" : "AppIcon-83.5x83.5@2x.png",
      "scale" : "2x"
    },
    {
      "size" : "1024x1024",
      "idiom" : "ios-marketing",
      "filename" : "AppIcon-512@2x.png",
      "scale" : "1x"
    }
  ],
  "info" : {
    "version" : 1,
    "author" : "xcode"
  }
}


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/tolaria/src-tauri/gen/apple/Assets.xcassets/Contents.json =====

{
  "info" : {
    "version" : 1,
    "author" : "xcode"
  }
}


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/tolaria/src-tauri/gen/apple/assets/mcp-server/package.json =====

{"type":"commonjs"}


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/tolaria/src-tauri/resources/agent-docs/search-index.json =====

[
  {
    "title": "Index",
    "path": "pages/index.md",
    "url": "/",
    "section": "home",
    "headings": []
  },
  {
    "title": "First Launch",
    "path": "pages/start/first-launch.md",
    "url": "/start/first-launch",
    "section": "start",
    "headings": [
      "What You Choose",
      "What Tolaria Creates",
      "First Commands To Try",
      "AI Setup Prompt"
    ]
  },
  {
    "title": "Getting Started Vault",
    "path": "pages/start/getting-started-vault.md",
    "url": "/start/getting-started-vault",
    "section": "start",
    "headings": [
      "What It Demonstrates",
      "Local-Only By Default",
      "Use It Alongside Your Own Vaults",
      "When To Move On"
    ]
  },
  {
    "title": "Install Tolaria",
    "path": "pages/start/install.md",
    "url": "/start/install",
    "section": "start",
    "headings": [
      "Download",
      "Homebrew",
      "Platform Status",
      "Managed Windows Devices",
      "After Installing"
    ]
  },
  {
    "title": "Open Or Create A Vault",
    "path": "pages/start/open-or-create-vault.md",
    "url": "/start/open-or-create-vault",
    "section": "start",
    "headings": [
      "Open An Existing Folder",
      "Create A New Vault",
      "Use More Than One Vault",
      "Git Is Recommended, Not Required"
    ]
  },
  {
    "title": "AI",
    "path": "pages/concepts/ai.md",
    "url": "/concepts/ai",
    "section": "concepts",
    "headings": [
      "Coding Agents",
      "Direct Models",
      "External MCP Setup",
      "Why Git Matters For AI"
    ]
  },
  {
    "title": "Editor",
    "path": "pages/concepts/editor.md",
    "url": "/concepts/editor",
    "section": "concepts",
    "headings": [
      "Rich Editing",
      "Raw Mode",
      "Table Of Contents",
      "Width"
    ]
  },
  {
    "title": "Files And Media",
    "path": "pages/concepts/files-and-media.md",
    "url": "/concepts/files-and-media",
    "section": "concepts",
    "headings": [
      "Mermaid Diagrams",
      "Attachments",
      "Previews",
      "Whiteboards",
      "Git Boundary"
    ]
  },
  {
    "title": "Git",
    "path": "pages/concepts/git.md",
    "url": "/concepts/git",
    "section": "concepts",
    "headings": [
      "What Tolaria Uses Git For",
      "History And Diffs",
      "Local Commits",
      "Remotes"
    ]
  },
  {
    "title": "Inbox",
    "path": "pages/concepts/inbox.md",
    "url": "/concepts/inbox",
    "section": "concepts",
    "headings": [
      "Why It Exists",
      "Organizing Inbox Notes",
      "Healthy Inbox Habit"
    ]
  },
  {
    "title": "Notes",
    "path": "pages/concepts/notes.md",
    "url": "/concepts/notes",
    "section": "concepts",
    "headings": [
      "Anatomy",
      "Titles",
      "Body Links",
      "Frontmatter"
    ]
  },
  {
    "title": "Properties",
    "path": "pages/concepts/properties.md",
    "url": "/concepts/properties",
    "section": "concepts",
    "headings": [
      "Suggested Properties",
      "System Properties",
      "Property Editing"
    ]
  },
  {
    "title": "Relationships",
    "path": "pages/concepts/relationships.md",
    "url": "/concepts/relationships",
    "section": "concepts",
    "headings": [
      "Relationship Fields",
      "Body Links Versus Relationship Fields",
      "Backlinks"
    ]
  },
  {
    "title": "Types",
    "path": "pages/concepts/types.md",
    "url": "/concepts/types",
    "section": "concepts",
    "headings": [
      "Type Field",
      "Prefer Types Over Folders",
      "Type Documents",
      "What Types Control",
      "New Note Defaults"
    ]
  },
  {
    "title": "Vaults",
    "path": "pages/concepts/vaults.md",
    "url": "/concepts/vaults",
    "section": "concepts",
    "headings": [
      "Core Rules",
      "Why Local Files Matter",
      "Git Is A Capability",
      "Multiple Vaults At The Same Time",
      "App State Versus Vault State"
    ]
  },
  {
    "title": "Build Custom Views",
    "path": "pages/guides/build-custom-views.md",


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/tolaria/src-tauri/tauri.conf.json =====

{
  "$schema": "../node_modules/@tauri-apps/cli/config.schema.json",
  "productName": "Tolaria",
  "version": "0.1.0",
  "identifier": "club.refactoring.tolaria",
  "build": {
    "frontendDist": "../dist",
    "devUrl": "http://localhost:5202",
    "beforeDevCommand": "pnpm dev",
    "beforeBuildCommand": "pnpm build && pnpm bundle-mcp && pnpm agent-docs"
  },
  "app": {
    "withGlobalTauri": true,
    "macOSPrivateApi": true,
    "windows": [
      {
        "title": "Tolaria",
        "width": 1400,
        "height": 900,
        "minWidth": 480,
        "minHeight": 400,
        "resizable": true,
        "fullscreen": false,
        "titleBarStyle": "Overlay",
        "trafficLightPosition": {
          "x": 18,
          "y": 24
        },
        "hiddenTitle": true,
        "backgroundColor": "#F7F6F3",
        "dragDropEnabled": false
      }
    ],
    "security": {
      "csp": {
        "default-src": "'self' ipc: http://ipc.localhost",
        "script-src": "'self' https://us.i.posthog.com https://eu.i.posthog.com https://us-assets.i.posthog.com https://eu-assets.i.posthog.com",
        "connect-src": "'self' ipc: http://ipc.localhost data: ws://localhost:9710 ws://127.0.0.1:9710 ws://localhost:9711 ws://127.0.0.1:9711 https:",
        "img-src": "'self' asset: http://asset.localhost data: blob: https:",
        "style-src": "'self' 'unsafe-inline' https://fonts.googleapis.com",
        "style-src-elem": "'self' 'nonce-tolaria-runtime-style' https://fonts.googleapis.com",
        "style-src-attr": "'unsafe-inline'",
        "font-src": "'self' data: https://fonts.gstatic.com",
        "media-src": "'self' asset: http://asset.localhost data: blob: https:",
        "object-src": "'self' asset: http://asset.localhost"
      },
      "devCsp": "default-src 'self' ipc: http://ipc.localhost http://localhost:5202 http://127.0.0.1:5202 asset: http://asset.localhost data: blob: https:; script-src 'self' 'unsafe-inline' 'unsafe-eval' http://localhost:5202 http://127.0.0.1:5202 https://us.i.posthog.com https://eu.i.posthog.com https://us-assets.i.posthog.com https://eu-assets.i.posthog.com; connect-src 'self' ipc: http://ipc.localhost http://localhost:5202 http://127.0.0.1:5202 data: ws://localhost:5202 ws://127.0.0.1:5202 ws://localhost:9710 ws://127.0.0.1:9710 ws://localhost:9711 ws://127.0.0.1:9711 https:; img-src 'self' asset: http://asset.localhost data: blob: https:; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; style-src-elem 'self' 'unsafe-inline' 'nonce-tolaria-runtime-style' https://fonts.googleapis.com; style-src-attr 'unsafe-inline'; font-src 'self' data: https://fonts.gstatic.com; media-src 'self' asset: http://asset.localhost data: blob: https:; object-src 'self' asset: http://asset.localhost",
      "assetProtocol": {
        "enable": true,
        "scope": []
      }
    }
  },
  "bundle": {
    "active": true,
    "targets": "all",
    "createUpdaterArtifacts": true,
    "category": "Productivity",
    "windows": {
      "webviewInstallMode": {
        "type": "downloadBootstrapper"
      }
    },
    "resources": {
      "resources/mcp-server/**/*": "mcp-server/",
      "resources/agent-docs/**/*": "agent-docs/"
    },
    "icon": [
      "icons/32x32.png",
      "icons/128x128.png",
      "icons/128x128@2x.png",
      "icons/icon.icns",
      "icons/icon.ico"
    ]
  },
  "plugins": {
    "deep-link": {
      "desktop": {
        "schemes": ["tolaria"]
      }
    },
    "updater": {
      "endpoints": [
        "https://refactoringhq.github.io/tolaria/stable/latest.json"
      ],
      "windows": {
        "installMode": "passive"
      },
      "pubkey": "dW50cnVzdGVkIGNvbW1lbnQ6IG1pbmlzaWduIHB1YmxpYyBrZXk6IEE4NkQ5MDI3REVCRkFGNUMKUldSY3I3L2VKNUJ0cU5JRlRZZlp3NGhnU3ZwbkVKeGVvREpmb2sxRVJndHFpVFZPNlArbEE5R1IK"
    }
  }
}


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/tolaria/src/lib/locales/be-BY.json =====

{
  "command.noMatches": "Няма адпаведных каманд",
  "command.palettePlaceholder": "Увядзіце каманду...",
  "command.footerNavigate": "↑↓ навігацыя",
  "command.footerSelect": "↵ выбраць",
  "command.footerClose": "esc закрыць",
  "command.footerSend": "↵ адправіць",
  "command.aiMode": "Рэжым {agent}",
  "command.openSettings": "Адкрыць налады",
  "command.openSettings.keywords": "preferences config налады прэферэнцыі",
  "command.openLanguageSettings": "Адкрыць налады мовы",
  "command.openLanguageSettings.keywords": "language locale i18n internationalization localization мова лакаль беларуская англійская італьянская французcкая нямецкая руская іспанская партугальская кітайская японская карэйская польская 中文 繁體中文 zh-tw",
  "command.useSystemLanguage": "Выкарыстоўваць сістэмную мову",
  "command.openH1Setting": "Налады аўтаматычнага перайменавання па H1",
  "command.toggleGitignoredFilesVisibility": "Паказаць/схаваць файлы, якія ігнаруюцца Git",
  "command.contribute": "Далучыцца да праекта",
  "command.checkUpdates": "Праверыць абнаўленні",
  "menu.application": "Меню праграмы",
  "menu.file": "Файл",
  "menu.edit": "Рэдагаваць",
  "menu.view": "Прагляд",
  "menu.go": "Перайсці",
  "menu.note": "Нататка",
  "menu.vault": "Сховішча",
  "menu.window": "Акно",
  "menu.file.quickOpen": "Хуткае адкрыццё",
  "menu.file.quickOpenCmdO": "Хуткае адкрыццё (Cmd+O)",
  "menu.file.quickOpenCtrlO": "Хуткае адкрыццё (Ctrl+O)",
  "menu.file.save": "Захаваць",
  "menu.edit.pasteWithoutFormatting": "Уставіць без фарматавання",
  "menu.edit.findInVault": "Знайсці ў Vault",
  "menu.edit.toggleNoteListSearch": "Уключыць/выключыць пошук у спісе нататак",
  "menu.view.allPanels": "Усе панэлі",
  "menu.view.zoomIn": "Павелічэнне",
  "menu.view.zoomOut": "Паменшыць",
  "menu.view.actualSize": "Фактычны памер",
  "menu.view.commandPalette": "Палітра каманд",
  "menu.go.allNotes": "Усе нататкі",
  "menu.go.archived": "Архівавана",
  "menu.go.changes": "Змены",
  "menu.go.inbox": "Уваходныя",
  "menu.note.toggleOrganized": "Пераключыць «Упарадкавана»",
  "menu.note.toggleTableOfContents": "Пераключыць змест",
  "menu.vault.addRemote": "Дадаць аддаленае…",
  "feedback.title": "Зрабіце ўнёсак у Tolaria",
  "feedback.description": "Выберыце шлях, які адпавядае таму, што вы хочаце зрабіць! Мы будзем удзячныя за любую дапамогу",
  "feedback.sponsor.title": "Спонсар / Падтрымка",
  "feedback.sponsor.description": "Гэта Лука 👋. Мая праца на поўны працоўны дзень — кіраванне Refactoring, інфармацыйным бюлетэнем для больш чым 170 000 інжынераў пра тое, як кіраваць добрымі камандамі і выпускаць праграмнае забеспячэнне з дапамогай ШІ. Я пішу пра працоўныя працэсы, бяру інтэрв'ю ў тэхналагічных лідэраў (напрыклад, DHH, Марціна Фаўлера і іншых) і кірую прыватнай супольнасцю з больш чым 2000 інжынераў, праводзячы штомесячны жывы коўчынг, клуб ШІ і многае іншае.\n\nTolaria — гэта FOSS, і так будзе заўсёды. Калі вам гэта падабаецца, лепшы спосаб падтрымаць — падпісацца на рассылку.",
  "feedback.sponsor.cta": "Паглядзіце Refactoring",
  "feedback.sponsor.linkLabel": "Refactoring",
  "feedback.featureRequests.title": "Запыты на функцыі",
  "feedback.featureRequests.description": "Спачатку выканайце пошук на дошцы, прагаласуйце за існуючыя ідэі і стварайце новыя публікацыі, калі яны сапраўды новыя!",
  "feedback.featureRequests.cta": "Адкрыць дошку прадукту",
  "feedback.featureRequests.linkLabel": "Дошка прадукту",
  "feedback.discussions.title": "Дыскусіі",
  "feedback.discussions.description": "Выкарыстоўвайце «Обсуждения» для пытанняў, размоваў, паказу і расповеду, а таксама кантэксту супольнасці.",
  "feedback.discussions.cta": "Адкрытыя абмеркаванні",
  "feedback.discussions.linkLabel": "Обсуждения GitHub",
  "feedback.contributeCode.title": "Унесці код",
  "feedback.contributeCode.description": "Вітаюцца невялікія, мэтанакіраваныя PR. Спачатку праверце дошку, каб ствараць правільныя рэчы!",
  "feedback.contributeCode.cta": "Адкрытыя запыты на ўключэнне змяненняў",
  "feedback.contributeCode.linkLabel": "Запыты на ўцягванне GitHub",
  "feedback.contributingGuide.cta": "Адкрыць дапаможнік для ўдзельнікаў",
  "feedback.contributingGuide.linkLabel": "дапаможнік па ўкладах",
  "feedback.reportBug.title": "Паведаміць пра памылку",
  "feedback.reportBug.description": "Растлумачце, як прайграць, што вы чакалі і што адбылося. Калі ласка, дадайце дыягностыку!",
  "feedback.reportBug.cta": "Адкрыць праблемы GitHub",
  "feedback.reportBug.linkLabel": "Праблемы GitHub",
  "feedback.linkFallback.title": "Немагчыма адкрыць {label} аўтаматычна.",
  "feedback.linkFallback.description": "Адкрыйце гэты URL уручную замест гэтага:",
  "feedback.copyDiagnostics": "Капіраваць ачышчаную дыягностыку",
  "feedback.diagnosticsCopied": "Дыягностыка скапіявана",
  "feedback.diagnosticsCopiedSentence": "Дыягностыка скапіявана.",
  "feedback.clipboardUnavailable": "Доступ да буфера абмену зараз недаступны. Вы ўсё яшчэ можаце адкрываць праблемы GitHub непасрэдна.",
  "command.group.navigation": "Навігацыя",
  "command.group.note": "Нататка",
  "command.group.git": "Git",
  "command.group.view": "Выгляд",
  "command.group.settings": "Налады",
  "command.navigation.searchNotes": "Пошук нататак",
  "command.navigation.goAllNotes": "Перайсці да ўсіх нататак",
  "command.navigation.goArchived": "Перайсці ў архіў",
  "command.navigation.goChanges": "Перайсці да змяненняў",
  "command.navigation.goHistory": "Перайсці да гісторыі",
  "command.navigation.goBack": "Крок назад",
  "command.navigation.goForward": "Крок наперад",
  "command.navigation.goInbox": "Перайсці ва Уваходныя",
  "command.navigation.renameFolder": "Перайменаваць папку",
  "command.navigation.deleteFolder": "Выдаліць папку",
  "command.navigation.showOpenNotes": "Паказаць адкрытыя нататкі",
  "command.navigation.showArchivedNotes": "Паказаць архіваваныя нататкі",
  "command.navigation.listType": "Спіс {type}",
  "command.note.newNote": "Новая нататка",
  "command.note.newNoteInCurrentFolder": "Стварыць новую нататку ў бягучай папцы",
  "command.note.newType": "Новы тып",
  "command.note.newTypedNote": "Стварыць {type}",
  "command.note.saveNote": "Захаваць нататку",
  "command.note.undo": "Адрабіць",
  "command.note.undoAction": "Адмяніць {action}",
  "command.note.redo": "Повторити",
  "command.note.redoAction": "Паўтарыць {action}",
  "command.note.pastePlainText": "Уставіць як просты тэкст",
  "command.note.findInNote": "Знайсці ў нататцы",
  "command.note.replaceInNote": "Замяніць у нататцы",
  "command.note.deleteNote": "Выдаліць нататку",
  "command.note.archiveNote": "У архіў",
  "command.note.unarchiveNote": "Дастаць з архіва",
  "command.note.addFavorite": "Дадаць у абранае",
  "command.note.removeFavorite": "Выдаліць з абранага",
  "command.note.markOrganized": "Адзначыць як упарадкаванае",
  "command.note.markUnorganized": "Адзначыць як неўпарадкаванае",
  "command.note.restoreDeleted": "Аднавіць выдаленую нататку",
  "command.note.setIcon": "Усталяваць значок нататкі",
  "command.note.removeIcon": "Выдаліць значок нататкі",
  "command.note.changeType": "Змяніць тып нататкі…",
  "command.note.moveToFolder": "Перамясціць нататку ў папку…",
  "command.note.copyDeepLink": "Капіяваць глыбокі спасылку на бягучы элемент",
  "command.note.exportPdf": "Экспартаваць нататку ў фармаце PDF",
  "command.note.openNewWindow": "Адкрыць у новым акне",
  "command.git.initialize": "Ініцыялізаваць Git для бягучага сховішча",
  "command.git.commitPush": "Закаміціць і адправіць (Commit & Push)",
  "command.git.addRemote": "Дадаць аддалены сервер (Remote) да сховішча",
  "command.git.pull": "Атрымаць змены (Pull)",
  "command.git.pullRepository": "Атрымаць з аддаленага рэпазіторыя: {repository}",
  "command.git.resolveConflicts": "Вырашыць канфлікты",
  "command.git.viewChanges": "Прагледзець чакаючыя змены",
  "git.author.label": "Аўтар каміту",
  "git.author.warning.localOverridesGlobal": "Аўтар Git у рэпазітары адрозніваецца ад вашага глабальнага аўтара Git. Калі здаецца, што нешта не так, скасуйце і абнавіце git config гэтага сховішча перад камітам.",
  "git.repository.select": "Сховішча",
  "git.toast.autoGitFailed": "Памылка AutoGit: {error}",
  "git.toast.commitFailed": "Памылка каміта: {error}",
  "git.toast.missingAuthor": "Задайце аўтара Git, перш чым AutoGit зможа ствараць каміты. Выканайце git config --global user.name \"Your Name\" і git config --global user.email you@example.com.",
  "command.view.editorOnly": "Толькі рэдактар",
  "command.view.editorNoteList": "Рэдактар + Спіс нататак",
  "command.view.fullLayout": "Поўны выгляд",
  "command.view.toggleProperties": "Паказаць/схаваць панэль уласцівасцей",
  "command.view.toggleDiff": "Уключыць/выключыць рэжым параўнання (Diff)",
  "command.view.toggleRaw": "Рэдактар зыходнага кода",
  "command.view.noteWidthNormal": "Звычайная шырыня нататкі",
  "command.view.noteWidthWide": "Шырокая нататка",
  "command.view.defaultNoteWidthNormal": "Звычайная шырыня нататкі па змаўчанні",
  "command.view.defaultNoteWidthWide": "Шырокая нататка па змаўчанні",
  "command.view.leftLayout": "Размяшчэнне злева",
  "command.view.centerLayout": "Размяшчэнне па цэнтры",
  "command.view.toggleAiPanel": "Панэль ШІ",
  "command.view.newAiChat": "Новы ШІ чат",
  "command.view.toggleBacklinks": "Паказаць/схаваць адваротныя спасылкі",
  "command.view.moveViewUp": "Перамясціць выгляд вышэй",
  "command.view.moveViewDown": "Перамясціць выгляд ніжэй",
  "command.view.moveNamedViewUp": "Перамясціць {name} вышэй",
  "command.view.moveNamedViewDown": "Перамясціць {name} ніжэй",
  "command.view.zoomIn": "Павялічыць маштаб ({zoom}%)",
  "command.view.zoomOut": "Паменшыць маштаб ({zoom}%)",
  "command.view.resetZoom": "Скінуць маштаб",
  "command.settings.createEmptyVault": "Стварыць пустое сховішча…",
  "command.settings.openVault": "Адкрыць сховішча…",
  "command.settings.removeVault": "Выдаліць сховішча са спісу",
  "command.settings.restoreGettingStarted": "Аднавіць навучальнае сховішча",
  "command.settings.manageExternalAi": "Кіраванне вонкавымі інструментамі ШІ…",
  "command.settings.setupExternalAi": "Наладзіць вонкавыя інструменты ШІ…",
  "command.settings.reloadVault": "Перазагрузіць сховішча",
  "command.settings.repairVault": "Аднавіць сховішча",
  "command.settings.useLightMode": "Светлая тэма",
  "command.settings.useDarkMode": "Цёмная тэма",
  "command.settings.useSystemTheme": "Сістэмная тэма",
  "command.settings.toggleGitignoredFilesVisibility": "Паказаць/схаваць файлы, што ігнаруюцца Git",
  "command.ai.openAgents": "Адкрыць ШІ агентаў",
  "command.ai.restoreGuidance": "Аднавіць інструкцыі для Tolaria ШІ",
  "command.ai.switchToAgent": "Пераключыць ШІ агента на {agent}",
  "command.ai.switchDefault": "Змяніць стандартнага ШІ агента",
  "command.ai.switchDefaultWithAgent": "Змяніць стандартнага ШІ агента ({agent})",
  "settings.title": "Налады",
  "settings.close": "Закрыць налады",
  "settings.sync.title": "Сінхранізацыя і Абнаўленні",
  "settings.sync.description": "Наладка фонавай загрузкі і канала абнаўленняў Tolaria.",
  "settings.pullInterval": "Інтэрвал сінхранізацыі (хвіліны)",
  "settings.pullIntervalDescription": "Як часта Tolaria правярае змены на аддаленым серверы.",
  "settings.releaseChannel": "Канал абнаўленняў",
  "settings.releaseChannelDescription": "Стабільны канал для правераных рэлізаў; Альфа – для самых апошніх змяненняў.",
  "settings.releaseStable": "Стабільны (Stable)",


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/tolaria/src/lib/locales/be-Latn.json =====

{
  "command.noMatches": "Niama adpaviednych kamand",
  "command.palettePlaceholder": "Uviadzicie kamandu...",
  "command.footerNavigate": "↑↓ navihacyja",
  "command.footerSelect": "↵ vybrać",
  "command.footerClose": "esc zakryć",
  "command.footerSend": "↵ adpravić",
  "command.aiMode": "Režym {agent}",
  "command.openSettings": "Adkryć nalady",
  "command.openSettings.keywords": "preferences config nalady prefierencyi",
  "command.openLanguageSettings": "Adkryć nalady movy",
  "command.openLanguageSettings.keywords": "language locale i18n internationalization localization mova lakaĺ bielaruskaja anhlijskaja itaĺjanskaja francuzckaja niamieckaja ruskaja ispanskaja partuhaĺskaja kitajskaja japonskaja karejskaja poĺskaja 中文 繁體中文 zh-tw",
  "command.useSystemLanguage": "Vykarystoŭvać sistemnuju movu",
  "command.openH1Setting": "Nalady aŭtamatyčnaha pierajmienavannia pa H1",
  "command.toggleGitignoredFilesVisibility": "Pakazać/schavać fajly, jakija ihnarujucca Git",
  "command.contribute": "Dalučycca da prajekta",
  "command.checkUpdates": "Pravieryć abnaŭlienni",
  "menu.application": "Mieniu prahramy",
  "menu.file": "Fajl",
  "menu.edit": "Redahavannie",
  "menu.view": "Vyhliad",
  "menu.go": "Pierajsci",
  "menu.note": "Natatka",
  "menu.vault": "Schovišča",
  "menu.window": "Akno",
  "menu.file.quickOpen": "Chutka adkryć",
  "menu.file.quickOpenCmdO": "Chutka adkryć (Cmd+O)",
  "menu.file.quickOpenCtrlO": "Chutka adkryć (Ctrl+O)",
  "menu.file.save": "Zachavać",
  "menu.edit.pasteWithoutFormatting": "Ustavić biez farmatavannia",
  "menu.edit.findInVault": "Znajsci ŭ schoviščy",
  "menu.edit.toggleNoteListSearch": "Pakazać/schavać pošuk u spisie natatak",
  "menu.view.allPanels": "Usie paneli",
  "menu.view.zoomIn": "Pavialičyć maštab",
  "menu.view.zoomOut": "Pamienšyć maštab",
  "menu.view.actualSize": "Sapraŭdny pamier",
  "menu.view.commandPalette": "Palitra kamand",
  "menu.go.allNotes": "Usie natatki",
  "menu.go.archived": "Archivavanyja",
  "menu.go.changes": "Zmieny",
  "menu.go.inbox": "Uvachodnyja",
  "menu.note.toggleOrganized": "Pierakliučyć uparadkavannie",
  "menu.note.toggleTableOfContents": "Pakazać/schavać źmiest",
  "menu.vault.addRemote": "Dadać addalieny siervier…",
  "feedback.title": "Dalučycca da Tolaria",
  "feedback.description": "Vybierycie šliach, jaki adpaviadaje tamu, što vy chočacie zrabić! Liubaja dapamoha vartaia",
  "feedback.sponsor.title": "Sponsorstva / Padtrymka",
  "feedback.sponsor.description": "Luca tut 👋 maja asnoŭnaja praca — viesci Refactoring, rasylku dlia 170K+ inžynieraŭ pra toje, jak kiravać mocnymi kamandami i pastavljać prahramy z ŠI. Ja pišu pra pracovnyja pracesy, hutaryu z technaličnymi liderami (napryklad DHH, Martin Fowler i inšymi) i viadu pryvatnuju supoĺnaść z 2000+ inžynieraŭ z štomiesiačnym live-coaching, AI club i inšym.\n\nTolaria — heta FOSS i zaŭsiody budzie takim. Kali vam padabajecca prajekt, lepšy sposab padtrymać jaho — padpisaćca na rasylku.",
  "feedback.sponsor.cta": "Prahliedzieć Refactoring",
  "feedback.sponsor.linkLabel": "Refactoring",
  "feedback.featureRequests.title": "Zapyty na funkcyi",
  "feedback.featureRequests.description": "Spačatku pašukajcie na došcy, prahalasujcie za isnuiučyja idei i stvarajcie novyja zapisy toĺki kali idea sapraŭdy novaja!",
  "feedback.featureRequests.cta": "Adkryć praduktavuju došku",
  "feedback.featureRequests.linkLabel": "Praduktavaja doška",
  "feedback.discussions.title": "Dyskussii",
  "feedback.discussions.description": "Vykarystoŭvajcie Discussions dlia pytanniaŭ, razmoŭ, show & tell i kantêkstu supoĺnaści.",
  "feedback.discussions.cta": "Adkryć dyskussii",
  "feedback.discussions.linkLabel": "GitHub Discussions",
  "feedback.contributeCode.title": "Dalučycca kodam",
  "feedback.contributeCode.description": "Malenkija, dakladnyja PR vitajucca. Spačatku pravierycie došku, kab budavać praviĺnyja rečy!",
  "feedback.contributeCode.cta": "Adkryć Pull Requests",
  "feedback.contributeCode.linkLabel": "GitHub Pull Requests",
  "feedback.contributingGuide.cta": "Adkryć vodič pa ŭnieskach",
  "feedback.contributingGuide.linkLabel": "vodič pa ŭnieskach",
  "feedback.reportBug.title": "Paviedamić pra pamylku",
  "feedback.reportBug.description": "Apishicie, jak paŭtaryć, što vy čakali i što adbylosia. Kali laska, daduć dyjahnostyku!",
  "feedback.reportBug.cta": "Adkryć GitHub Issues",
  "feedback.reportBug.linkLabel": "GitHub Issues",
  "feedback.linkFallback.title": "Nie ŭdalosia aŭtamatyčna adkryć {label}.",
  "feedback.linkFallback.description": "Adkryjcie hety URL ručna:",
  "feedback.copyDiagnostics": "Skapijavać ačyščanuju dyjahnostyku",
  "feedback.diagnosticsCopied": "Dyjahnostyka skapijavanaja",
  "feedback.diagnosticsCopiedSentence": "Dyjahnostyka skapijavanaja.",
  "feedback.clipboardUnavailable": "Bufer abmienu ciapier niedastupny. Vy ŭsio roŭna možacie adkryć GitHub Issues napramuju.",
  "command.group.navigation": "Navihacyja",
  "command.group.note": "Natatka",
  "command.group.git": "Git",
  "command.group.view": "Vyhliad",
  "command.group.settings": "Nalady",
  "command.navigation.searchNotes": "Pošuk natatak",
  "command.navigation.goAllNotes": "Pierajsci da ŭsich natatak",
  "command.navigation.goArchived": "Pierajsci ŭ archiŭ",
  "command.navigation.goChanges": "Pierajsci da zmianienniaŭ",
  "command.navigation.goHistory": "Pierajsci da historyi",
  "command.navigation.goBack": "Krok nazad",
  "command.navigation.goForward": "Krok napierad",
  "command.navigation.goInbox": "Pierajsci va Uvachodnyja",
  "command.navigation.renameFolder": "Pierajmienavać papku",
  "command.navigation.deleteFolder": "Vydalić papku",
  "command.navigation.showOpenNotes": "Pakazać adkrytyja natatki",
  "command.navigation.showArchivedNotes": "Pakazać archivavanyja natatki",
  "command.navigation.listType": "Spis {type}",
  "command.note.newNote": "Novaja natatka",
  "command.note.newNoteInCurrentFolder": "Stvaryć novuju natatku ŭ biahučaj papcy",
  "command.note.newType": "Novy typ",
  "command.note.newTypedNote": "Stvaryć {type}",
  "command.note.saveNote": "Zachavać natatku",
  "command.note.undo": "Adkacić",
  "command.note.undoAction": "Adkacić {action}",
  "command.note.redo": "Paŭtaryć",
  "command.note.redoAction": "Paŭtaryć {action}",
  "command.note.pastePlainText": "Ustavić jak prosty tekst",
  "command.note.findInNote": "Znajsci ŭ natatcy",
  "command.note.replaceInNote": "Zamianić u natatcy",
  "command.note.deleteNote": "Vydalić natatku",
  "command.note.archiveNote": "U archiŭ",
  "command.note.unarchiveNote": "Dastać z archiva",
  "command.note.addFavorite": "Dadać u abranaje",
  "command.note.removeFavorite": "Vydalić z abranaha",
  "command.note.markOrganized": "Adznačyć jak uparadkavanaje",
  "command.note.markUnorganized": "Adznačyć jak nieŭparadkavanaje",
  "command.note.restoreDeleted": "Adnavić vydalienuju natatku",
  "command.note.setIcon": "Ustaliavać značok natatki",
  "command.note.removeIcon": "Vydalić značok natatki",
  "command.note.changeType": "Zmianić typ natatki…",
  "command.note.moveToFolder": "Pieramiascić natatku ŭ papku…",
  "command.note.exportPdf": "Ekspartavać natatku ŭ farmacie PDF",
  "command.note.openNewWindow": "Adkryć u novym aknie",
  "command.note.copyDeepLink": "Kapijavać deep-link da biahučaha elementa",
  "command.git.initialize": "Inicyjalizavać Git dlia biahučaha schovišča",
  "command.git.commitPush": "Zakamicić i adpravić (Commit & Push)",
  "command.git.addRemote": "Dadać addalieny siervier (Remote) da schovišča",
  "command.git.pull": "Atrymać zmieny (Pull)",
  "command.git.pullRepository": "Atrymać z addalienaha repazitoryja: {repository}",
  "command.git.resolveConflicts": "Vyrašyć kanflikty",
  "command.git.viewChanges": "Prahliedzieć čakajučyja zmieny",
  "git.author.label": "Aŭtar kamita",
  "git.author.warning.localOverridesGlobal": "Aŭtar Git u repazitoryi adroźnivajecca ad vašaha hlabalnaha aŭtara Git. Kali zdajecca, što niešta nie tak, skasujcie i abnavicie git config hetaha schovišča pierad kamitam.",
  "git.repository.select": "Schovišča",
  "git.toast.autoGitFailed": "Pamylka AutoGit: {error}",
  "git.toast.commitFailed": "Pamylka kamita: {error}",
  "git.toast.missingAuthor": "Zadajcie aŭtara Git, pierš čym AutoGit zmoža stvarać kamity. Vykanajcie git config --global user.name \"Your Name\" i git config --global user.email you@example.com.",
  "command.view.editorOnly": "Toĺki redaktar",
  "command.view.editorNoteList": "Redaktar + Spis natatak",
  "command.view.fullLayout": "Poŭny vyhliad",
  "command.view.toggleProperties": "Pakazać/schavać paneĺ ulascivasciej",
  "command.view.toggleDiff": "Ukliučyć/vykliučyć režym paraŭnannia (Diff)",
  "command.view.toggleRaw": "Redaktar zychodnaha koda",
  "command.view.noteWidthNormal": "Zvyčajnaja šyrynia natatki",
  "command.view.noteWidthWide": "Šyrokaja natatka",
  "command.view.defaultNoteWidthNormal": "Zvyčajnaja šyrynia natatki pa zmaŭčanni",
  "command.view.defaultNoteWidthWide": "Šyrokaja natatka pa zmaŭčanni",
  "command.view.leftLayout": "Razmiaščennie zlieva",
  "command.view.centerLayout": "Razmiaščennie pa centry",
  "command.view.toggleAiPanel": "Paneĺ ŠI",
  "command.view.newAiChat": "Novy ŠI čat",
  "command.view.toggleBacklinks": "Pakazać/schavać advarotnyja spasylki",
  "command.view.moveViewUp": "Pieramiascić vyhliad vyšej",
  "command.view.moveViewDown": "Pieramiascić vyhliad nižej",
  "command.view.moveNamedViewUp": "Pieramiascić {name} vyšej",
  "command.view.moveNamedViewDown": "Pieramiascić {name} nižej",
  "command.view.zoomIn": "Pavialičyć maštab ({zoom}%)",
  "command.view.zoomOut": "Pamienšyć maštab ({zoom}%)",
  "command.view.resetZoom": "Skinuć maštab",
  "command.settings.createEmptyVault": "Stvaryć pustoje schovišča…",
  "command.settings.openVault": "Adkryć schovišča…",
  "command.settings.removeVault": "Vydalić schovišča sa spisu",
  "command.settings.restoreGettingStarted": "Adnavić navučaĺnaje schovišča",
  "command.settings.manageExternalAi": "Kiravannie vonkavymi instrumientami ŠI…",
  "command.settings.setupExternalAi": "Naladzić vonkavyja instrumienty ŠI…",
  "command.settings.reloadVault": "Pierazahruzić schovišča",
  "command.settings.repairVault": "Adnavić schovišča",
  "command.settings.useLightMode": "Svietlaja tema",
  "command.settings.useDarkMode": "Ciomnaja tema",
  "command.settings.useSystemTheme": "Sistemnaja tema",
  "command.settings.toggleGitignoredFilesVisibility": "Pakazać/schavać fajly, što ihnarujucca Git",
  "command.ai.openAgents": "Adkryć ŠI ahientaŭ",
  "command.ai.restoreGuidance": "Adnavić instrukcyi dlia Tolaria ŠI",
  "command.ai.switchToAgent": "Pierakliučyć ŠI ahienta na {agent}",
  "command.ai.switchDefault": "Zmianić standartnaha ŠI ahienta",
  "command.ai.switchDefaultWithAgent": "Zmianić standartnaha ŠI ahienta ({agent})",
  "settings.title": "Nalady",
  "settings.close": "Zakryć nalady",
  "settings.sync.title": "Sinchranizacyja i Abnaŭlienni",
  "settings.sync.description": "Naladka fonavaj zahruzki i kanala abnaŭlienniaŭ Tolaria.",
  "settings.pullInterval": "Interval sinchranizacyi (chviliny)",
  "settings.pullIntervalDescription": "Jak časta Tolaria praviaraje zmieny na addalienym sierviery.",
  "settings.releaseChannel": "Kanal abnaŭlienniaŭ",
  "settings.releaseChannelDescription": "Stabiĺny kanal dlia pravieranych relizaŭ; Aĺfa – dlia samych apošnich zmianienniaŭ.",
  "settings.releaseStable": "Stabiĺny (Stable)",


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/tolaria/src/lib/locales/de-DE.json =====

{
  "command.noMatches": "Keine passenden Befehle",
  "command.palettePlaceholder": "Geben Sie einen Befehl ein …",
  "command.footerNavigate": "↑↓ navigieren",
  "command.footerSelect": "↵ Auswählen",
  "command.footerClose": "esc schließen",
  "command.footerSend": "↵ Senden",
  "command.aiMode": "{agent}-Modus",
  "command.openSettings": "Einstellungen öffnen",
  "command.openSettings.keywords": "Einstellungen Konfiguration",
  "command.openLanguageSettings": "Spracheinstellungen öffnen",
  "command.openLanguageSettings.keywords": "Sprache Gebietsschema i18n Internationalisierung Lokalisierung Englisch Italienisch Französisch Deutsch Russisch Spanisch Portugiesisch Chinesisch vereinfacht traditionell Japanisch Koreanisch Polnisch 中文 繁體中文 zh-tw",
  "command.useSystemLanguage": "Systemsprache verwenden",
  "command.openH1Setting": "Einstellung für automatische H1-Umbenennung öffnen",
  "command.toggleGitignoredFilesVisibility": "Sichtbarkeit von Gitignored-Dateien umschalten",
  "command.contribute": "Mitwirken",
  "command.checkUpdates": "Nach Updates suchen",
  "menu.application": "Anwendungsmenü",
  "menu.file": "Datei",
  "menu.edit": "Bearbeiten",
  "menu.view": "Anzeigen",
  "menu.go": "Los",
  "menu.note": "Notiz",
  "menu.vault": "Vault",
  "menu.window": "Fenster",
  "menu.file.quickOpen": "Schnell öffnen",
  "menu.file.quickOpenCmdO": "Schnell öffnen (Cmd+O)",
  "menu.file.quickOpenCtrlO": "Schnell öffnen (Strg+O)",
  "menu.file.save": "Speichern",
  "menu.edit.pasteWithoutFormatting": "Ohne Formatierung einfügen",
  "menu.edit.findInVault": "Im Vault suchen",
  "menu.edit.toggleNoteListSearch": "Suche in der Notizenliste umschalten",
  "menu.view.allPanels": "Alle Panels",
  "menu.view.zoomIn": "Vergrößern",
  "menu.view.zoomOut": "Verkleinern",
  "menu.view.actualSize": "Tatsächliche Größe",
  "menu.view.commandPalette": "Befehlspalette",
  "menu.go.allNotes": "Alle Notizen",
  "menu.go.archived": "Archiviert",
  "menu.go.changes": "Änderungen",
  "menu.go.inbox": "Posteingang",
  "menu.note.toggleOrganized": "„Organisiert“ umschalten",
  "menu.note.toggleTableOfContents": "Inhaltsverzeichnis ein-/ausblenden",
  "menu.vault.addRemote": "Remote hinzufügen …",
  "feedback.title": "Zu Tolaria beitragen",
  "feedback.description": "Wähle den Weg, der zu dem passt, was du tun möchtest! Jede Art von Hilfe wird geschätzt",
  "feedback.sponsor.title": "Sponsor / Unterstützung",
  "feedback.sponsor.description": "Ich bin Luca 👋. Mein Vollzeitjob ist die Leitung von Refactoring, einem Newsletter für über 170.000 Ingenieure, in dem es darum geht, wie man gute Teams führt und Software mit KI bereitstellt. Ich schreibe über Workflows, interviewe Tech-Leader (z. B. DHH, Martin Fowler und andere) und leite eine private Community mit über 2.000 Ingenieuren, in der es monatliches Live-Coaching, einen KI-Club und vieles mehr gibt.\n\nTolaria ist FOSS und wird es immer sein. Wenn es dir gefällt, unterstützt du es am besten, indem du den Newsletter abonnierst.",
  "feedback.sponsor.cta": "Schau dir Refactoring an",
  "feedback.sponsor.linkLabel": "Refactoring",
  "feedback.featureRequests.title": "Funktionsanfragen",
  "feedback.featureRequests.description": "Suche zuerst im Board, stimme für bestehende Ideen ab und erstelle neue Beiträge, wenn sie wirklich neu sind!",
  "feedback.featureRequests.cta": "Product Board öffnen",
  "feedback.featureRequests.linkLabel": "Product Board",
  "feedback.discussions.title": "Diskussionen",
  "feedback.discussions.description": "Nutze Diskussionen für Fragen, Gespräche, Show & Tell und Community-Kontext.",
  "feedback.discussions.cta": "Offene Diskussionen",
  "feedback.discussions.linkLabel": "GitHub-Diskussionen",
  "feedback.contributeCode.title": "Code beisteuern",
  "feedback.contributeCode.description": "Kleine, fokussierte PRs sind willkommen. Schau dir zuerst das Board an, damit du die richtigen Dinge baust!",
  "feedback.contributeCode.cta": "Offene Pull Requests",
  "feedback.contributeCode.linkLabel": "GitHub-Pull-Requests",
  "feedback.contributingGuide.cta": "Leitfaden für Mitwirkende öffnen",
  "feedback.contributingGuide.linkLabel": "der Leitfaden für Mitwirkende",
  "feedback.reportBug.title": "Einen Fehler melden",
  "feedback.reportBug.description": "Erkläre, wie man ihn reproduziert, was du erwartet hast und was passiert ist. Bitte füge die Diagnose bei!",
  "feedback.reportBug.cta": "GitHub-Issues öffnen",
  "feedback.reportBug.linkLabel": "GitHub-Issues",
  "feedback.linkFallback.title": "{label} konnte nicht automatisch geöffnet werden.",
  "feedback.linkFallback.description": "Öffnen Sie stattdessen diese URL manuell:",
  "feedback.copyDiagnostics": "Bereinigte Diagnose kopieren",
  "feedback.diagnosticsCopied": "Diagnose kopiert",
  "feedback.diagnosticsCopiedSentence": "Diagnose kopiert.",
  "feedback.clipboardUnavailable": "Der Zugriff auf die Zwischenablage ist derzeit nicht möglich. Du kannst GitHub-Issues weiterhin direkt öffnen.",
  "command.group.navigation": "Navigation",
  "command.group.note": "Notiz",
  "command.group.git": "Git",
  "command.group.view": "Anzeigen",
  "command.group.settings": "Einstellungen",
  "command.navigation.searchNotes": "Notizen durchsuchen",
  "command.navigation.goAllNotes": "Zu allen Notizen",
  "command.navigation.goArchived": "Zu Archivierten Notizen",
  "command.navigation.goChanges": "Zu den Änderungen",
  "command.navigation.goHistory": "Zum Verlauf",
  "command.navigation.goBack": "Zurück",
  "command.navigation.goForward": "Vorwärts",
  "command.navigation.goInbox": "Zum Posteingang",
  "command.navigation.renameFolder": "Ordner umbenennen",
  "command.navigation.deleteFolder": "Ordner löschen",
  "command.navigation.showOpenNotes": "Offene Notizen anzeigen",
  "command.navigation.showArchivedNotes": "Archivierte Notizen anzeigen",
  "command.navigation.listType": "{type}-Liste",
  "command.note.newNote": "Neue Notiz",
  "command.note.newNoteInCurrentFolder": "Neue Notiz im aktuellen Ordner erstellen",
  "command.note.newType": "Neuer Typ",
  "command.note.newTypedNote": "Neuer {type}",
  "command.note.saveNote": "Notiz speichern",
  "command.note.undo": "Rückgängig machen",
  "command.note.undoAction": "{action} rückgängig machen",
  "command.note.redo": "Wiederholen",
  "command.note.redoAction": "{action} wiederholen",
  "command.note.pastePlainText": "Ohne Formatierung einfügen",
  "command.note.findInNote": "In Notiz suchen",
  "command.note.replaceInNote": "In Notiz ersetzen",
  "command.note.deleteNote": "Notiz löschen",
  "command.note.archiveNote": "Notiz archivieren",
  "command.note.unarchiveNote": "Notiz aus dem Archiv holen",
  "command.note.addFavorite": "Zu Favoriten hinzufügen",
  "command.note.removeFavorite": "Aus Favoriten entfernen",
  "command.note.markOrganized": "Als organisiert markieren",
  "command.note.markUnorganized": "Als unorganisiert markieren",
  "command.note.restoreDeleted": "Gelöschte Notiz wiederherstellen",
  "command.note.setIcon": "Notizsymbol festlegen",
  "command.note.removeIcon": "Notizsymbol entfernen",
  "command.note.changeType": "Notiztyp ändern …",
  "command.note.moveToFolder": "Notiz in Ordner verschieben …",
  "command.note.copyDeepLink": "Deep-Link zum aktuellen Element kopieren",
  "command.note.exportPdf": "Notiz als PDF exportieren",
  "command.note.openNewWindow": "In neuem Fenster öffnen",
  "command.git.initialize": "Git für den aktuellen Vault initialisieren",
  "command.git.commitPush": "Commit & Push",
  "command.git.addRemote": "Remote zum aktuellen Vault hinzufügen",
  "command.git.pull": "Von Remote abrufen",
  "command.git.pullRepository": "Aus Remote abrufen: {repository}",
  "command.git.resolveConflicts": "Konflikte auflösen",
  "command.git.viewChanges": "Ausstehende Änderungen anzeigen",
  "git.author.label": "Autor des Commits",
  "git.author.warning.localOverridesGlobal": "Der Git-Autor des Repositorys unterscheidet sich von Ihrem globalen Git-Autor. Breche ab und aktualisiere die Git-Konfiguration dieses Vaults, bevor du einen Commit durchführst, wenn sie falsch aussieht.",
  "git.repository.select": "Repository",
  "git.toast.autoGitFailed": "AutoGit ist fehlgeschlagen: {error}",
  "git.toast.commitFailed": "Commit fehlgeschlagen: {error}",
  "git.toast.missingAuthor": "Legen Sie einen Git-Autor fest, bevor AutoGit einen Commit durchführen kann. Führen Sie git config --global user.name \"Ihr Name\" und git config --global user.email you@example.com aus.",
  "command.view.editorOnly": "Nur Editor",
  "command.view.editorNoteList": "Editor + Notizenliste",
  "command.view.fullLayout": "Vollständiges Layout",
  "command.view.toggleProperties": "Eigenschaften-Panel ein-/ausblenden",
  "command.view.toggleDiff": "Diff-Modus umschalten",
  "command.view.toggleRaw": "Raw-Editor umschalten",
  "command.view.noteWidthNormal": "Normale Notizenbreite verwenden",
  "command.view.noteWidthWide": "Breite Notizenbreite verwenden",
  "command.view.defaultNoteWidthNormal": "Standardmäßig normale Notenbreite verwenden",
  "command.view.defaultNoteWidthWide": "Standardmäßig breite Notenbreite verwenden",
  "command.view.leftLayout": "Linksbündiges Notizenlayout verwenden",
  "command.view.centerLayout": "Zentriertes Notizen-Layout verwenden",
  "command.view.toggleAiPanel": "KI-Panel umschalten",
  "command.view.newAiChat": "Neuer KI-Chat",
  "command.view.toggleBacklinks": "Backlinks ein-/ausblenden",
  "command.view.moveViewUp": "Ansicht nach oben verschieben",
  "command.view.moveViewDown": "Ansicht nach unten verschieben",
  "command.view.moveNamedViewUp": "{name} nach oben verschieben",
  "command.view.moveNamedViewDown": "{name} nach unten verschieben",
  "command.view.zoomIn": "Vergrößern ({zoom} %)",
  "command.view.zoomOut": "Verkleinern ({zoom} %)",
  "command.view.resetZoom": "Zoom zurücksetzen",
  "command.settings.createEmptyVault": "Leeren Vault erstellen …",
  "command.settings.openVault": "Vault öffnen …",
  "command.settings.removeVault": "Vault aus der Liste entfernen",
  "command.settings.restoreGettingStarted": "Getting-Started-Vault wiederherstellen",
  "command.settings.manageExternalAi": "Externe KI-Tools verwalten …",
  "command.settings.setupExternalAi": "Externe KI-Tools einrichten …",
  "command.settings.reloadVault": "Vault neu laden",
  "command.settings.repairVault": "Vault reparieren",
  "command.settings.useLightMode": "Hellen Modus verwenden",
  "command.settings.useDarkMode": "Dunklen Modus verwenden",
  "command.settings.useSystemTheme": "Systemdesign verwenden",
  "command.settings.toggleGitignoredFilesVisibility": "Sichtbarkeit von Gitignored-Dateien umschalten",
  "command.ai.openAgents": "KI-Agents öffnen",
  "command.ai.restoreGuidance": "Tolaria-KI-Anleitung wiederherstellen",
  "command.ai.switchToAgent": "KI-Agent auf {agent} umstellen",
  "command.ai.switchDefault": "Standard-AI-Agent wechseln",
  "command.ai.switchDefaultWithAgent": "Standard-AI-Agent ({agent}) wechseln",
  "settings.title": "Einstellungen",
  "settings.close": "Einstellungen schließen",
  "settings.sync.title": "Synchronisierung & Updates",
  "settings.sync.description": "Konfigurieren Sie das Abrufen im Hintergrund und legen Sie fest, welchem Update-Feed Tolaria folgt. Stable erhält nur manuell promotete Releases, während Alpha jedem Push auf main folgt.",
  "settings.pullInterval": "Pull-Intervall (Minuten)",
  "settings.pullIntervalDescription": "Wie oft Tolaria nach entfernten Vault-Änderungen sucht.",
  "settings.releaseChannel": "Release-Kanal",
  "settings.releaseChannelDescription": "Stable folgt freigegebenen Releases; Alpha folgt jedem Push auf main.",
  "settings.releaseStable": "Stable",


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/tolaria/src/lib/locales/en.json =====

{
  "command.noMatches": "No matching commands",
  "command.palettePlaceholder": "Type a command...",
  "command.footerNavigate": "↑↓ navigate",
  "command.footerSelect": "↵ select",
  "command.footerClose": "esc close",
  "command.footerSend": "↵ send",
  "command.aiMode": "{agent} mode",
  "command.openSettings": "Open Settings",
  "command.openSettings.keywords": "preferences config",
  "command.openLanguageSettings": "Open Language Settings",
  "command.openLanguageSettings.keywords": "language locale i18n internationalization localization english italian french german russian spanish portuguese chinese simplified traditional japanese korean polish 中文 繁體中文 zh-tw",
  "command.useSystemLanguage": "Use System Language",
  "command.openH1Setting": "Open H1 Auto-Rename Setting",
  "command.toggleGitignoredFilesVisibility": "Toggle Gitignored Files Visibility",
  "command.contribute": "Contribute",
  "command.checkUpdates": "Check for Updates",
  "menu.application": "Application menu",
  "menu.file": "File",
  "menu.edit": "Edit",
  "menu.view": "View",
  "menu.go": "Go",
  "menu.note": "Note",
  "menu.vault": "Vault",
  "menu.window": "Window",
  "menu.file.quickOpen": "Quick Open",
  "menu.file.quickOpenCmdO": "Quick Open (Cmd+O)",
  "menu.file.quickOpenCtrlO": "Quick Open (Ctrl+O)",
  "menu.file.save": "Save",
  "menu.edit.pasteWithoutFormatting": "Paste without Formatting",
  "menu.edit.findInVault": "Find in Vault",
  "menu.edit.toggleNoteListSearch": "Toggle Note List Search",
  "menu.view.allPanels": "All Panels",
  "menu.view.zoomIn": "Zoom In",
  "menu.view.zoomOut": "Zoom Out",
  "menu.view.actualSize": "Actual Size",
  "menu.view.commandPalette": "Command Palette",
  "menu.go.allNotes": "All Notes",
  "menu.go.archived": "Archived",
  "menu.go.changes": "Changes",
  "menu.go.inbox": "Inbox",
  "menu.note.toggleOrganized": "Toggle Organized",
  "menu.note.toggleTableOfContents": "Toggle Table of Contents",
  "menu.vault.addRemote": "Add Remote…",
  "feedback.title": "Contribute to Tolaria",
  "feedback.description": "Pick the path that fits what you want to do! Any type of help is appreciated",
  "feedback.sponsor.title": "Sponsor / Support",
  "feedback.sponsor.description": "Luca here 👋 my full-time job is running Refactoring, a newsletter for 170K+ engineers about how to run good teams and ship software with AI. I write about workflows, interview tech leaders (e.g. DHH, Martin Fowler, and more) and run a private community of 2000+ engineers with monthly live coaching, AI club, and more.\n\nTolaria is FOSS and always will be. If you like it, the best way to support it is to subscribe to the newsletter.",
  "feedback.sponsor.cta": "Check out Refactoring",
  "feedback.sponsor.linkLabel": "Refactoring",
  "feedback.featureRequests.title": "Feature requests",
  "feedback.featureRequests.description": "Search on the board first, upvote existing ideas, and create new posts when genuinely new!",
  "feedback.featureRequests.cta": "Open Product Board",
  "feedback.featureRequests.linkLabel": "Product Board",
  "feedback.discussions.title": "Discussions",
  "feedback.discussions.description": "Use Discussions for questions, conversations, show & tell, and community context.",
  "feedback.discussions.cta": "Open Discussions",
  "feedback.discussions.linkLabel": "GitHub Discussions",
  "feedback.contributeCode.title": "Contribute code",
  "feedback.contributeCode.description": "Small, focused PRs are welcome. Check the board first so you build the right things!",
  "feedback.contributeCode.cta": "Open Pull Requests",
  "feedback.contributeCode.linkLabel": "GitHub Pull Requests",
  "feedback.contributingGuide.cta": "Open Contributing Guide",
  "feedback.contributingGuide.linkLabel": "the contributing guide",
  "feedback.reportBug.title": "Report a bug",
  "feedback.reportBug.description": "Explain how to reproduce, what you expected, vs what happened. Attach the diagnostics please!",
  "feedback.reportBug.cta": "Open GitHub Issues",
  "feedback.reportBug.linkLabel": "GitHub Issues",
  "feedback.linkFallback.title": "Couldn’t open {label} automatically.",
  "feedback.linkFallback.description": "Open this URL manually instead:",
  "feedback.copyDiagnostics": "Copy sanitized diagnostics",
  "feedback.diagnosticsCopied": "Diagnostics copied",
  "feedback.diagnosticsCopiedSentence": "Diagnostics copied.",
  "feedback.clipboardUnavailable": "Clipboard access is unavailable right now. You can still open GitHub Issues directly.",
  "command.group.navigation": "Navigation",
  "command.group.note": "Note",
  "command.group.git": "Git",
  "command.group.view": "View",
  "command.group.settings": "Settings",
  "command.navigation.searchNotes": "Search Notes",
  "command.navigation.goAllNotes": "Go to All Notes",
  "command.navigation.goArchived": "Go to Archived",
  "command.navigation.goChanges": "Go to Changes",
  "command.navigation.goHistory": "Go to History",
  "command.navigation.goBack": "Go Back",
  "command.navigation.goForward": "Go Forward",
  "command.navigation.goInbox": "Go to Inbox",
  "command.navigation.renameFolder": "Rename Folder",
  "command.navigation.deleteFolder": "Delete Folder",
  "command.navigation.showOpenNotes": "Show Open Notes",
  "command.navigation.showArchivedNotes": "Show Archived Notes",
  "command.navigation.listType": "List {type}",
  "command.note.newNote": "New Note",
  "command.note.newNoteInCurrentFolder": "Create New Note in Current Folder",
  "command.note.newType": "New Type",
  "command.note.newTypedNote": "New {type}",
  "command.note.saveNote": "Save Note",
  "command.note.undo": "Undo",
  "command.note.undoAction": "Undo {action}",
  "command.note.redo": "Redo",
  "command.note.redoAction": "Redo {action}",
  "command.note.pastePlainText": "Paste without formatting",
  "command.note.findInNote": "Find in Note",
  "command.note.replaceInNote": "Replace in Note",
  "command.note.deleteNote": "Delete Note",
  "command.note.archiveNote": "Archive Note",
  "command.note.unarchiveNote": "Unarchive Note",
  "command.note.addFavorite": "Add to Favorites",
  "command.note.removeFavorite": "Remove from Favorites",
  "command.note.markOrganized": "Mark as Organized",
  "command.note.markUnorganized": "Mark as Unorganized",
  "command.note.restoreDeleted": "Restore Deleted Note",
  "command.note.setIcon": "Set Note Icon",
  "command.note.removeIcon": "Remove Note Icon",
  "command.note.changeType": "Change Note Type…",
  "command.note.moveToFolder": "Move Note to Folder…",
  "command.note.copyDeepLink": "Copy deep link to current item",
  "command.note.exportPdf": "Export note as PDF",
  "command.note.openNewWindow": "Open in New Window",
  "command.git.initialize": "Initialize Git for Current Vault",
  "command.git.commitPush": "Commit & Push",
  "command.git.addRemote": "Add Remote to Current Vault",
  "command.git.pull": "Pull from Remote",
  "command.git.pullRepository": "Pull from Remote: {repository}",
  "command.git.resolveConflicts": "Resolve Conflicts",
  "command.git.viewChanges": "View Pending Changes",
  "git.author.label": "Commit author",
  "git.author.warning.localOverridesGlobal": "Repository Git author differs from your global Git author. Cancel and update this vault's git config before committing if it looks wrong.",
  "git.repository.select": "Repository",
  "git.toast.autoGitFailed": "AutoGit failed: {error}",
  "git.toast.commitFailed": "Commit failed: {error}",
  "git.toast.missingAuthor": "Set a Git author before AutoGit can commit. Run git config --global user.name \"Your Name\" and git config --global user.email you@example.com.",
  "command.view.editorOnly": "Editor Only",
  "command.view.editorNoteList": "Editor + Note List",
  "command.view.fullLayout": "Full Layout",
  "command.view.toggleProperties": "Toggle Properties Panel",
  "command.view.toggleDiff": "Toggle Diff Mode",
  "command.view.toggleRaw": "Toggle Raw Editor",
  "command.view.noteWidthNormal": "Use Normal Note Width",
  "command.view.noteWidthWide": "Use Wide Note Width",
  "command.view.defaultNoteWidthNormal": "Use Normal Note Width by Default",
  "command.view.defaultNoteWidthWide": "Use Wide Note Width by Default",
  "command.view.leftLayout": "Use Left-Aligned Note Layout",
  "command.view.centerLayout": "Use Centered Note Layout",
  "command.view.toggleAiPanel": "Toggle AI Panel",
  "command.view.newAiChat": "New AI chat",
  "command.view.toggleBacklinks": "Toggle Backlinks",
  "command.view.moveViewUp": "Move View Up",
  "command.view.moveViewDown": "Move View Down",
  "command.view.moveNamedViewUp": "Move {name} Up",
  "command.view.moveNamedViewDown": "Move {name} Down",
  "command.view.zoomIn": "Zoom In ({zoom}%)",
  "command.view.zoomOut": "Zoom Out ({zoom}%)",
  "command.view.resetZoom": "Reset Zoom",
  "command.settings.createEmptyVault": "Create Empty Vault…",
  "command.settings.openVault": "Open Vault…",
  "command.settings.removeVault": "Remove Vault from List",
  "command.settings.restoreGettingStarted": "Restore Getting Started Vault",
  "command.settings.manageExternalAi": "Manage External AI Tools…",
  "command.settings.setupExternalAi": "Set Up External AI Tools…",
  "command.settings.reloadVault": "Reload Vault",
  "command.settings.repairVault": "Repair Vault",
  "command.settings.useLightMode": "Use Light Mode",
  "command.settings.useDarkMode": "Use Dark Mode",
  "command.settings.useSystemTheme": "Use System Theme",
  "command.settings.toggleGitignoredFilesVisibility": "Toggle Gitignored Files Visibility",
  "command.ai.openAgents": "Open AI Agents",
  "command.ai.restoreGuidance": "Restore Tolaria AI Guidance",
  "command.ai.switchToAgent": "Switch AI Agent to {agent}",
  "command.ai.switchDefault": "Switch Default AI Agent",
  "command.ai.switchDefaultWithAgent": "Switch Default AI Agent ({agent})",
  "settings.title": "Settings",
  "settings.close": "Close settings",
  "settings.sync.title": "Sync & Updates",
  "settings.sync.description": "Configure background pulling and which update feed Tolaria follows. Stable only receives manually promoted releases, while Alpha follows every push to main.",
  "settings.pullInterval": "Pull interval (minutes)",
  "settings.pullIntervalDescription": "How often Tolaria checks for remote vault changes.",
  "settings.releaseChannel": "Release channel",
  "settings.releaseChannelDescription": "Stable follows promoted releases; Alpha follows every push to main.",
  "settings.releaseStable": "Stable",


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/tolaria/src/lib/locales/es-419.json =====

{
  "command.noMatches": "No hay comandos que coincidan",
  "command.palettePlaceholder": "Escriba un comando...",
  "command.footerNavigate": "↑↓ navegar",
  "command.footerSelect": "↵ seleccionar",
  "command.footerClose": "esc cerrar",
  "command.footerSend": "↵ enviar",
  "command.aiMode": "Modo {agent}",
  "command.openSettings": "Abrir Configuración",
  "command.openSettings.keywords": "configuración de preferencias",
  "command.openLanguageSettings": "Abrir la configuración de idioma",
  "command.openLanguageSettings.keywords": "idioma configuración regional i18n internacionalización localización inglés italiano francés alemán ruso español portugués chino simplificado tradicional japonés coreano polaco 中文 繁體中文 zh-tw",
  "command.useSystemLanguage": "Usar el idioma del sistema",
  "command.openH1Setting": "Abrir la configuración de renombrado automático de H1",
  "command.toggleGitignoredFilesVisibility": "Alternar la visibilidad de los archivos Gitignored",
  "command.contribute": "Contribuir",
  "command.checkUpdates": "Buscar actualizaciones",
  "menu.application": "Menú de la aplicación",
  "menu.file": "Archivo",
  "menu.edit": "Editar",
  "menu.view": "Ver",
  "menu.go": "Ir",
  "menu.note": "Nota",
  "menu.vault": "Vault",
  "menu.window": "Ventana",
  "menu.file.quickOpen": "Abrir rápido",
  "menu.file.quickOpenCmdO": "Abrir rápido (Cmd+O)",
  "menu.file.quickOpenCtrlO": "Abrir rápido (Ctrl+O)",
  "menu.file.save": "Guardar",
  "menu.edit.pasteWithoutFormatting": "Pegar sin formato",
  "menu.edit.findInVault": "Buscar en Vault",
  "menu.edit.toggleNoteListSearch": "Activar/desactivar la búsqueda en la lista de notas",
  "menu.view.allPanels": "Todos los paneles",
  "menu.view.zoomIn": "Acercar",
  "menu.view.zoomOut": "Alejar",
  "menu.view.actualSize": "Tamaño real",
  "menu.view.commandPalette": "Paleta de comandos",
  "menu.go.allNotes": "Todas las notas",
  "menu.go.archived": "Archivado",
  "menu.go.changes": "Cambios",
  "menu.go.inbox": "Bandeja de entrada",
  "menu.note.toggleOrganized": "Alternar Organizado",
  "menu.note.toggleTableOfContents": "Alternar Índice",
  "menu.vault.addRemote": "Agregar remoto…",
  "feedback.title": "Contribuir a Tolaria",
  "feedback.description": "¡Elige el camino que se adapte a lo que quieres hacer! Cualquier tipo de ayuda es bienvenida",
  "feedback.sponsor.title": "Patrocinio / Apoyo",
  "feedback.sponsor.description": "Soy Luca 👋. Mi trabajo de tiempo completo es dirigir Refactoring, un boletín para más de 170 000 ingenieros sobre cómo dirigir buenos equipos y lanzar software con IA. Escribo sobre flujos de trabajo, entrevisto a líderes tecnológicos (por ejemplo, DHH, Martin Fowler y más) y dirijo una comunidad privada de más de 2000 ingenieros con coaching mensual en vivo, club de IA y más.\n\nTolaria es FOSS y siempre lo será. Si te gusta, la mejor manera de apoyarla es suscribirte al boletín.",
  "feedback.sponsor.cta": "Echa un vistazo a Refactoring",
  "feedback.sponsor.linkLabel": "Refactoring",
  "feedback.featureRequests.title": "Solicitudes de funciones",
  "feedback.featureRequests.description": "Primero busca en el tablero, vota a favor de las ideas existentes y crea nuevas publicaciones cuando sean realmente nuevas.",
  "feedback.featureRequests.cta": "Abrir el Tablero de productos",
  "feedback.featureRequests.linkLabel": "Product Board",
  "feedback.discussions.title": "Discusiones",
  "feedback.discussions.description": "Utiliza Discussions para preguntas, conversaciones, presentaciones y contexto de la comunidad.",
  "feedback.discussions.cta": "Abrir Discussions",
  "feedback.discussions.linkLabel": "Discusiones de GitHub",
  "feedback.contributeCode.title": "Contribuir con código",
  "feedback.contributeCode.description": "Las PR pequeñas y específicas son bienvenidas. ¡Revisa primero el tablero para que desarrolles lo correcto!",
  "feedback.contributeCode.cta": "Solicitudes de extracción abiertas",
  "feedback.contributeCode.linkLabel": "Solicitudes de extracción de GitHub",
  "feedback.contributingGuide.cta": "Abrir la Guía para contribuir",
  "feedback.contributingGuide.linkLabel": "la guía de contribución",
  "feedback.reportBug.title": "Informar un error",
  "feedback.reportBug.description": "Explica cómo reproducirlo, qué esperabas y qué sucedió. ¡Adjunta el diagnóstico, por favor!",
  "feedback.reportBug.cta": "Abrir incidencias de GitHub",
  "feedback.reportBug.linkLabel": "Incidencias de GitHub",
  "feedback.linkFallback.title": "No se pudo abrir {label} automáticamente.",
  "feedback.linkFallback.description": "En su lugar, abra esta URL manualmente:",
  "feedback.copyDiagnostics": "Copiar diagnósticos depurados",
  "feedback.diagnosticsCopied": "Diagnósticos copiados",
  "feedback.diagnosticsCopiedSentence": "Diagnósticos copiados.",
  "feedback.clipboardUnavailable": "El acceso al portapapeles no está disponible en este momento. Aún puedes abrir los problemas de GitHub directamente.",
  "command.group.navigation": "Navegación",
  "command.group.note": "Nota",
  "command.group.git": "Git",
  "command.group.view": "Ver",
  "command.group.settings": "Configuración",
  "command.navigation.searchNotes": "Buscar notas",
  "command.navigation.goAllNotes": "Ir a Todas las notas",
  "command.navigation.goArchived": "Ir a Archivadas",
  "command.navigation.goChanges": "Ir a Cambios",
  "command.navigation.goHistory": "Ir a Historial",
  "command.navigation.goBack": "Volver",
  "command.navigation.goForward": "Avanzar",
  "command.navigation.goInbox": "Ir a la bandeja de entrada",
  "command.navigation.renameFolder": "Cambiar el nombre de la carpeta",
  "command.navigation.deleteFolder": "Eliminar carpeta",
  "command.navigation.showOpenNotes": "Mostrar notas abiertas",
  "command.navigation.showArchivedNotes": "Mostrar notas archivadas",
  "command.navigation.listType": "Lista {type}",
  "command.note.newNote": "Nueva nota",
  "command.note.newNoteInCurrentFolder": "Crear nueva nota en la carpeta actual",
  "command.note.newType": "Nuevo tipo",
  "command.note.newTypedNote": "Nuevo {type}",
  "command.note.saveNote": "Guardar nota",
  "command.note.undo": "Deshacer",
  "command.note.undoAction": "Deshacer {action}",
  "command.note.redo": "Rehacer",
  "command.note.redoAction": "Rehacer {action}",
  "command.note.pastePlainText": "Pegar sin formato",
  "command.note.findInNote": "Buscar en la nota",
  "command.note.replaceInNote": "Reemplazar en la nota",
  "command.note.deleteNote": "Eliminar nota",
  "command.note.archiveNote": "Archivar nota",
  "command.note.unarchiveNote": "Desarchivar nota",
  "command.note.addFavorite": "Agregar a Favoritos",
  "command.note.removeFavorite": "Eliminar de Favoritos",
  "command.note.markOrganized": "Marcar como organizada",
  "command.note.markUnorganized": "Marcar como no organizada",
  "command.note.restoreDeleted": "Restaurar nota eliminada",
  "command.note.setIcon": "Establecer ícono de nota",
  "command.note.removeIcon": "Eliminar ícono de nota",
  "command.note.changeType": "Cambiar tipo de nota…",
  "command.note.moveToFolder": "Mover nota a la carpeta…",
  "command.note.copyDeepLink": "Copiar el enlace profundo al elemento actual",
  "command.note.exportPdf": "Exportar nota como PDF",
  "command.note.openNewWindow": "Abrir en una ventana nueva",
  "command.git.initialize": "Inicializar Git para el repositorio actual",
  "command.git.commitPush": "Confirmar y enviar",
  "command.git.addRemote": "Agregar repositorio remoto al repositorio actual",
  "command.git.pull": "Extraer desde el repositorio remoto",
  "command.git.pullRepository": "Extraer del repositorio remoto: {repository}",
  "command.git.resolveConflicts": "Resolver conflictos",
  "command.git.viewChanges": "Ver cambios pendientes",
  "git.author.label": "Autor de la confirmación",
  "git.author.warning.localOverridesGlobal": "El autor del repositorio Git es diferente de su autor global de Git. Cancele y actualice la configuración de Git de este repositorio antes de confirmar si parece incorrecta.",
  "git.repository.select": "Repositorio",
  "git.toast.autoGitFailed": "Error de AutoGit: {error}",
  "git.toast.commitFailed": "Error al confirmar: {error}",
  "git.toast.missingAuthor": "Establezca un autor de Git antes de que AutoGit pueda realizar la confirmación. Ejecute git config --global user.name \"Su nombre\" y git config --global user.email you@example.com.",
  "command.view.editorOnly": "Solo editor",
  "command.view.editorNoteList": "Editor + Lista de notas",
  "command.view.fullLayout": "Diseño completo",
  "command.view.toggleProperties": "Activar/desactivar el panel de propiedades",
  "command.view.toggleDiff": "Activar/desactivar el modo de diferencias",
  "command.view.toggleRaw": "Activar/desactivar el editor sin formato",
  "command.view.noteWidthNormal": "Usar ancho de nota normal",
  "command.view.noteWidthWide": "Usar ancho de nota amplio",
  "command.view.defaultNoteWidthNormal": "Usar el ancho de nota normal de forma predeterminada",
  "command.view.defaultNoteWidthWide": "Usar ancho de nota amplio de forma predeterminada",
  "command.view.leftLayout": "Usar diseño de nota alineado a la izquierda",
  "command.view.centerLayout": "Usar diseño de nota centrado",
  "command.view.toggleAiPanel": "Activar/desactivar el panel de IA",
  "command.view.newAiChat": "Nuevo chat de IA",
  "command.view.toggleBacklinks": "Activar/desactivar enlaces de retroceso",
  "command.view.moveViewUp": "Mover vista hacia arriba",
  "command.view.moveViewDown": "Mover vista hacia abajo",
  "command.view.moveNamedViewUp": "Mover {name} hacia arriba",
  "command.view.moveNamedViewDown": "Mover {name} hacia abajo",
  "command.view.zoomIn": "Acercar ({zoom} %)",
  "command.view.zoomOut": "Alejar ({zoom} %)",
  "command.view.resetZoom": "Restablecer el zoom",
  "command.settings.createEmptyVault": "Crear bóveda vacía…",
  "command.settings.openVault": "Abrir bóveda…",
  "command.settings.removeVault": "Eliminar caja fuerte de la lista",
  "command.settings.restoreGettingStarted": "Restaurar el almacén de introducción",
  "command.settings.manageExternalAi": "Administrar herramientas de IA externas…",
  "command.settings.setupExternalAi": "Configurar herramientas de IA externas…",
  "command.settings.reloadVault": "Volver a cargar el almacén",
  "command.settings.repairVault": "Reparar el repositorio",
  "command.settings.useLightMode": "Usar modo claro",
  "command.settings.useDarkMode": "Usar modo oscuro",
  "command.settings.useSystemTheme": "Usar el tema del sistema",
  "command.settings.toggleGitignoredFilesVisibility": "Activar/desactivar la visibilidad de los archivos ignorados por Git",
  "command.ai.openAgents": "Abrir agentes de IA",
  "command.ai.restoreGuidance": "Restaurar la guía de IA de Tolaria",
  "command.ai.switchToAgent": "Cambiar el agente de IA a {agent}",
  "command.ai.switchDefault": "Cambiar el agente de IA predeterminado",
  "command.ai.switchDefaultWithAgent": "Cambiar agente de IA predeterminado ({agent})",
  "settings.title": "Configuración",
  "settings.close": "Cerrar la configuración",
  "settings.sync.title": "Sincronización y actualizaciones",
  "settings.sync.description": "Configure la extracción en segundo plano y el feed de actualizaciones que sigue Tolaria. Stable solo recibe las versiones promocionadas manualmente, mientras que Alpha sigue cada push a main.",
  "settings.pullInterval": "Intervalo de extracción (minutos)",
  "settings.pullIntervalDescription": "Con qué frecuencia Tolaria comprueba cambios remotos en el almacén.",
  "settings.releaseChannel": "Canal de versiones",
  "settings.releaseChannelDescription": "Stable sigue las versiones promocionadas; Alpha sigue cada push a main.",
  "settings.releaseStable": "Stable",


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/tolaria/src/lib/locales/es-ES.json =====

{
  "command.noMatches": "No hay comandos que coincidan",
  "command.palettePlaceholder": "Escribe un comando...",
  "command.footerNavigate": "↑↓ navegar",
  "command.footerSelect": "↵ seleccionar",
  "command.footerClose": "esc cerrar",
  "command.footerSend": "↵ enviar",
  "command.aiMode": "Modo {agent}",
  "command.openSettings": "Abrir Ajustes",
  "command.openSettings.keywords": "preferencias config",
  "command.openLanguageSettings": "Abrir la configuración de idioma",
  "command.openLanguageSettings.keywords": "idioma configuración regional i18n internacionalización localización inglés italiano francés alemán ruso español portugués chino simplificado tradicional japonés coreano polaco 中文 繁體中文 zh-tw",
  "command.useSystemLanguage": "Usar el idioma del sistema",
  "command.openH1Setting": "Abrir la configuración de renombrado automático de H1",
  "command.toggleGitignoredFilesVisibility": "Activar/desactivar la visibilidad de los archivos Gitignored",
  "command.contribute": "Contribuir",
  "command.checkUpdates": "Buscar actualizaciones",
  "menu.application": "Menú de la aplicación",
  "menu.file": "Archivo",
  "menu.edit": "Editar",
  "menu.view": "Ver",
  "menu.go": "Ir",
  "menu.note": "Nota",
  "menu.vault": "Repositorio",
  "menu.window": "Ventana",
  "menu.file.quickOpen": "Abrir rápido",
  "menu.file.quickOpenCmdO": "Abrir rápido (Cmd+O)",
  "menu.file.quickOpenCtrlO": "Abrir rápidamente (Ctrl+O)",
  "menu.file.save": "Guardar",
  "menu.edit.pasteWithoutFormatting": "Pegar sin formato",
  "menu.edit.findInVault": "Buscar en el repositorio",
  "menu.edit.toggleNoteListSearch": "Activar/desactivar la búsqueda en la lista de notas",
  "menu.view.allPanels": "Todos los paneles",
  "menu.view.zoomIn": "Acercar",
  "menu.view.zoomOut": "Alejar",
  "menu.view.actualSize": "Tamaño real",
  "menu.view.commandPalette": "Paleta de comandos",
  "menu.go.allNotes": "Todas las notas",
  "menu.go.archived": "Archivado",
  "menu.go.changes": "Cambios",
  "menu.go.inbox": "Bandeja de entrada",
  "menu.note.toggleOrganized": "Alternar Organizado",
  "menu.note.toggleTableOfContents": "Activar/desactivar índice",
  "menu.vault.addRemote": "Añadir remoto…",
  "feedback.title": "Contribuir a Tolaria",
  "feedback.description": "¡Elige la ruta que mejor se adapte a lo que quieres hacer! Cualquier tipo de ayuda es bienvenida",
  "feedback.sponsor.title": "Patrocinio / Apoyo",
  "feedback.sponsor.description": "Soy Luca 👋. Mi trabajo a tiempo completo es dirigir Refactoring, un boletín para más de 170 000 ingenieros sobre cómo dirigir buenos equipos y lanzar software con IA. Escribo sobre flujos de trabajo, entrevisto a líderes tecnológicos (por ejemplo, DHH, Martin Fowler y otros) y dirijo una comunidad privada de más de 2000 ingenieros con coaching mensual en directo, club de IA y mucho más.\n\nTolaria es FOSS y siempre lo será. Si te gusta, la mejor manera de apoyarla es suscribirte al boletín.",
  "feedback.sponsor.cta": "Echa un vistazo a Refactoring",
  "feedback.sponsor.linkLabel": "Refactoring",
  "feedback.featureRequests.title": "Solicitudes de funciones",
  "feedback.featureRequests.description": "Primero busca en el foro, vota las ideas existentes y crea nuevas publicaciones cuando sean realmente nuevas.",
  "feedback.featureRequests.cta": "Abrir Product Board",
  "feedback.featureRequests.linkLabel": "Product Board",
  "feedback.discussions.title": "Discusiones",
  "feedback.discussions.description": "Utiliza Discussions para preguntas, conversaciones, presentaciones y contexto de la comunidad.",
  "feedback.discussions.cta": "Abrir Discussions",
  "feedback.discussions.linkLabel": "Discusiones de GitHub",
  "feedback.contributeCode.title": "Contribuir con código",
  "feedback.contributeCode.description": "Se aceptan solicitudes de extracción pequeñas y específicas. ¡Revisa primero el tablero para crear lo correcto!",
  "feedback.contributeCode.cta": "Solicitudes de extracción abiertas",
  "feedback.contributeCode.linkLabel": "Solicitudes de extracción de GitHub",
  "feedback.contributingGuide.cta": "Abrir la Guía para contribuir",
  "feedback.contributingGuide.linkLabel": "la guía de contribución",
  "feedback.reportBug.title": "Informar de un error",
  "feedback.reportBug.description": "Explica cómo reproducirlo, qué esperabas y qué ha ocurrido. ¡Adjunta el diagnóstico, por favor!",
  "feedback.reportBug.cta": "Abrir incidencias de GitHub",
  "feedback.reportBug.linkLabel": "Incidencias de GitHub",
  "feedback.linkFallback.title": "No se ha podido abrir {label} automáticamente.",
  "feedback.linkFallback.description": "Abra esta URL manualmente en su lugar:",
  "feedback.copyDiagnostics": "Copiar diagnósticos depurados",
  "feedback.diagnosticsCopied": "Diagnósticos copiados",
  "feedback.diagnosticsCopiedSentence": "Diagnósticos copiados.",
  "feedback.clipboardUnavailable": "El acceso al portapapeles no está disponible en este momento. Aún puede abrir los problemas de GitHub directamente.",
  "command.group.navigation": "Navegación",
  "command.group.note": "Nota",
  "command.group.git": "Git",
  "command.group.view": "Ver",
  "command.group.settings": "Ajustes",
  "command.navigation.searchNotes": "Buscar en las notas",
  "command.navigation.goAllNotes": "Ir a Todas las notas",
  "command.navigation.goArchived": "Ir a Archivadas",
  "command.navigation.goChanges": "Ir a Cambios",
  "command.navigation.goHistory": "Ir al historial",
  "command.navigation.goBack": "Volver atrás",
  "command.navigation.goForward": "Ir adelante",
  "command.navigation.goInbox": "Ir a la bandeja de entrada",
  "command.navigation.renameFolder": "Cambiar el nombre de la carpeta",
  "command.navigation.deleteFolder": "Eliminar carpeta",
  "command.navigation.showOpenNotes": "Mostrar notas abiertas",
  "command.navigation.showArchivedNotes": "Mostrar notas archivadas",
  "command.navigation.listType": "Lista {type}",
  "command.note.newNote": "Nueva nota",
  "command.note.newNoteInCurrentFolder": "Crear nueva nota en la carpeta actual",
  "command.note.newType": "Nuevo tipo",
  "command.note.newTypedNote": "Nuevo {type}",
  "command.note.saveNote": "Guardar nota",
  "command.note.undo": "Deshacer",
  "command.note.undoAction": "Deshacer {action}",
  "command.note.redo": "Rehacer",
  "command.note.redoAction": "Rehacer {action}",
  "command.note.pastePlainText": "Pegar sin formato",
  "command.note.findInNote": "Buscar en la nota",
  "command.note.replaceInNote": "Reemplazar en la nota",
  "command.note.deleteNote": "Eliminar nota",
  "command.note.archiveNote": "Archivar nota",
  "command.note.unarchiveNote": "Desarchivar nota",
  "command.note.addFavorite": "Añadir a Favoritos",
  "command.note.removeFavorite": "Eliminar de Favoritos",
  "command.note.markOrganized": "Marcar como organizada",
  "command.note.markUnorganized": "Marcar como no organizada",
  "command.note.restoreDeleted": "Restaurar nota eliminada",
  "command.note.setIcon": "Establecer icono de nota",
  "command.note.removeIcon": "Eliminar icono de nota",
  "command.note.changeType": "Cambiar tipo de nota…",
  "command.note.moveToFolder": "Mover nota a la carpeta…",
  "command.note.copyDeepLink": "Copiar el enlace profundo al elemento actual",
  "command.note.exportPdf": "Exportar nota como PDF",
  "command.note.openNewWindow": "Abrir en una ventana nueva",
  "command.git.initialize": "Inicializar Git para el almacén actual",
  "command.git.commitPush": "Confirmar y enviar",
  "command.git.addRemote": "Añadir repositorio remoto al almacén actual",
  "command.git.pull": "Extraer del repositorio remoto",
  "command.git.pullRepository": "Extraer del repositorio remoto: {repository}",
  "command.git.resolveConflicts": "Resolver conflictos",
  "command.git.viewChanges": "Ver cambios pendientes",
  "git.author.label": "Autor de la confirmación",
  "git.author.warning.localOverridesGlobal": "El autor del repositorio Git es diferente de su autor global de Git. Cancele y actualice la configuración de Git de este almacén antes de confirmar si parece incorrecta.",
  "git.repository.select": "Repositorio",
  "git.toast.autoGitFailed": "Error de AutoGit: {error}",
  "git.toast.commitFailed": "Error al confirmar: {error}",
  "git.toast.missingAuthor": "Establezca un autor de Git antes de que AutoGit pueda realizar la confirmación. Ejecute git config --global user.name \"Su nombre\" y git config --global user.email you@example.com.",
  "command.view.editorOnly": "Solo editor",
  "command.view.editorNoteList": "Editor + Lista de notas",
  "command.view.fullLayout": "Diseño completo",
  "command.view.toggleProperties": "Activar/desactivar el panel de propiedades",
  "command.view.toggleDiff": "Activar/desactivar el modo de diferencias",
  "command.view.toggleRaw": "Activar/desactivar el editor sin formato",
  "command.view.noteWidthNormal": "Usar ancho de nota normal",
  "command.view.noteWidthWide": "Usar ancho de nota amplio",
  "command.view.defaultNoteWidthNormal": "Usar el ancho de nota normal de forma predeterminada",
  "command.view.defaultNoteWidthWide": "Usar ancho de nota amplio de forma predeterminada",
  "command.view.leftLayout": "Usar diseño de nota alineado a la izquierda",
  "command.view.centerLayout": "Usar diseño de nota centrado",
  "command.view.toggleAiPanel": "Activar/desactivar el panel de IA",
  "command.view.newAiChat": "Nuevo chat de IA",
  "command.view.toggleBacklinks": "Activar/desactivar los enlaces de retroceso",
  "command.view.moveViewUp": "Subir la vista",
  "command.view.moveViewDown": "Mover vista hacia abajo",
  "command.view.moveNamedViewUp": "Subir {name}",
  "command.view.moveNamedViewDown": "Mover {name} hacia abajo",
  "command.view.zoomIn": "Acercar ({zoom} %)",
  "command.view.zoomOut": "Alejar ({zoom} %)",
  "command.view.resetZoom": "Restablecer el zoom",
  "command.settings.createEmptyVault": "Crear caja fuerte vacía…",
  "command.settings.openVault": "Abrir caja fuerte…",
  "command.settings.removeVault": "Eliminar caja fuerte de la lista",
  "command.settings.restoreGettingStarted": "Restaurar el almacén de introducción",
  "command.settings.manageExternalAi": "Gestionar herramientas externas de IA…",
  "command.settings.setupExternalAi": "Configurar herramientas de IA externas…",
  "command.settings.reloadVault": "Volver a cargar el almacén",
  "command.settings.repairVault": "Reparar el almacén",
  "command.settings.useLightMode": "Usar modo claro",
  "command.settings.useDarkMode": "Usar modo oscuro",
  "command.settings.useSystemTheme": "Usar el tema del sistema",
  "command.settings.toggleGitignoredFilesVisibility": "Activar/desactivar la visibilidad de los archivos gitignored",
  "command.ai.openAgents": "Abrir agentes de IA",
  "command.ai.restoreGuidance": "Restaurar la guía de IA de Tolaria",
  "command.ai.switchToAgent": "Cambiar el agente de IA a {agent}",
  "command.ai.switchDefault": "Cambiar agente de IA predeterminado",
  "command.ai.switchDefaultWithAgent": "Cambiar agente de IA predeterminado ({agent})",
  "settings.title": "Ajustes",
  "settings.close": "Cerrar ajustes",
  "settings.sync.title": "Sincronización y actualizaciones",
  "settings.sync.description": "Configurar la descarga en segundo plano y el canal de actualizaciones que sigue Tolaria. Stable solo recibe las versiones promocionadas manualmente, mientras que Alpha sigue todos los pushes a main.",
  "settings.pullInterval": "Intervalo de extracción (minutos)",
  "settings.pullIntervalDescription": "Con qué frecuencia Tolaria comprueba cambios remotos en el almacén.",
  "settings.releaseChannel": "Canal de versiones",
  "settings.releaseChannelDescription": "Stable sigue las versiones promocionadas; Alpha sigue cada push a main.",
  "settings.releaseStable": "Stable",


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/tolaria/src/lib/locales/fr-FR.json =====

{
  "command.noMatches": "Aucune commande correspondante",
  "command.palettePlaceholder": "Saisir une commande…",
  "command.footerNavigate": "↑↓ naviguer",
  "command.footerSelect": "↵ sélectionner",
  "command.footerClose": "esc fermer",
  "command.footerSend": "↵ envoyer",
  "command.aiMode": "Mode {agent}",
  "command.openSettings": "Ouvrir les paramètres",
  "command.openSettings.keywords": "préférences config",
  "command.openLanguageSettings": "Ouvrir les paramètres de langue",
  "command.openLanguageSettings.keywords": "langue paramètres régionaux i18n internationalisation localisation anglais italien français allemand russe espagnol portugais chinois simplifié traditionnel japonais coréen polonais 中文 繁體中文 zh-tw",
  "command.useSystemLanguage": "Utiliser la langue du système",
  "command.openH1Setting": "Ouvrir le paramètre de renommage automatique des titres H1",
  "command.toggleGitignoredFilesVisibility": "Activer/désactiver la visibilité des fichiers Gitignored",
  "command.contribute": "Contribuer",
  "command.checkUpdates": "Rechercher les mises à jour",
  "menu.application": "Menu de l'application",
  "menu.file": "Fichier",
  "menu.edit": "Modifier",
  "menu.view": "Afficher",
  "menu.go": "Aller",
  "menu.note": "Note",
  "menu.vault": "Coffre",
  "menu.window": "Fenêtre",
  "menu.file.quickOpen": "Ouverture rapide",
  "menu.file.quickOpenCmdO": "Ouverture rapide (Cmd+O)",
  "menu.file.quickOpenCtrlO": "Ouverture rapide (Ctrl+O)",
  "menu.file.save": "Enregistrer",
  "menu.edit.pasteWithoutFormatting": "Coller sans formatage",
  "menu.edit.findInVault": "Rechercher dans le coffre-fort",
  "menu.edit.toggleNoteListSearch": "Activer/désactiver la recherche dans la liste de notes",
  "menu.view.allPanels": "Tous les panneaux",
  "menu.view.zoomIn": "Zoom avant",
  "menu.view.zoomOut": "Zoom arrière",
  "menu.view.actualSize": "Taille réelle",
  "menu.view.commandPalette": "Palette de commandes",
  "menu.go.allNotes": "Toutes les notes",
  "menu.go.archived": "Archivé",
  "menu.go.changes": "Modifications",
  "menu.go.inbox": "Boîte de réception",
  "menu.note.toggleOrganized": "Activer/désactiver Organisé",
  "menu.note.toggleTableOfContents": "Activer/désactiver la table des matières",
  "menu.vault.addRemote": "Ajouter un dépôt distant…",
  "feedback.title": "Contribuer à Tolaria",
  "feedback.description": "Choisissez le chemin qui correspond à ce que vous voulez faire ! Toute aide est la bienvenue",
  "feedback.sponsor.title": "Sponsor / Soutien",
  "feedback.sponsor.description": "C'est Luca 👋 Mon travail à temps plein est de gérer Refactoring, une newsletter destinée à plus de 170 000 ingénieurs sur la façon de gérer de bonnes équipes et de livrer des logiciels avec l'IA. J'écris sur les workflows, j'interviewe des leaders du secteur tech (par exemple, DHH, Martin Fowler et bien d'autres) et je gère une communauté privée de plus de 2 000 ingénieurs avec un coaching mensuel en direct, un club IA et bien plus encore.\n\nTolaria est FOSS et le restera. Si vous l'aimez, la meilleure façon de la soutenir est de vous abonner à la newsletter.",
  "feedback.sponsor.cta": "Découvrez Refactoring",
  "feedback.sponsor.linkLabel": "Refactoring",
  "feedback.featureRequests.title": "Demandes de fonctionnalités",
  "feedback.featureRequests.description": "Recherchez d'abord sur le forum, votez pour les idées existantes et créez de nouveaux messages lorsqu'ils sont vraiment nouveaux !",
  "feedback.featureRequests.cta": "Ouvrir le Product Board",
  "feedback.featureRequests.linkLabel": "Tableau produit",
  "feedback.discussions.title": "Discussions",
  "feedback.discussions.description": "Utilisez Discussions pour les questions, les conversations, les présentations et le contexte de la communauté.",
  "feedback.discussions.cta": "Ouvrir Discussions",
  "feedback.discussions.linkLabel": "Discussions GitHub",
  "feedback.contributeCode.title": "Contribuer du code",
  "feedback.contributeCode.description": "Les petites PR ciblées sont les bienvenues. Consultez d'abord le tableau pour créer les bonnes choses !",
  "feedback.contributeCode.cta": "Pull requests ouvertes",
  "feedback.contributeCode.linkLabel": "Demandes de tirage GitHub",
  "feedback.contributingGuide.cta": "Ouvrir le guide de contribution",
  "feedback.contributingGuide.linkLabel": "le guide de contribution",
  "feedback.reportBug.title": "Signaler un bug",
  "feedback.reportBug.description": "Expliquez comment reproduire le problème, ce à quoi vous vous attendiez et ce qui s'est passé. Veuillez joindre les diagnostics !",
  "feedback.reportBug.cta": "Ouvrir les tickets GitHub",
  "feedback.reportBug.linkLabel": "Tickets GitHub",
  "feedback.linkFallback.title": "Impossible d'ouvrir {label} automatiquement.",
  "feedback.linkFallback.description": "Ouvrez plutôt cette URL manuellement :",
  "feedback.copyDiagnostics": "Copier les diagnostics nettoyés",
  "feedback.diagnosticsCopied": "Diagnostics copiés",
  "feedback.diagnosticsCopiedSentence": "Diagnostics copiés.",
  "feedback.clipboardUnavailable": "L'accès au presse-papiers n'est pas disponible pour le moment. Vous pouvez toujours ouvrir les tickets GitHub directement.",
  "command.group.navigation": "Navigation",
  "command.group.note": "Note",
  "command.group.git": "Git",
  "command.group.view": "Afficher",
  "command.group.settings": "Paramètres",
  "command.navigation.searchNotes": "Rechercher dans les notes",
  "command.navigation.goAllNotes": "Accéder à toutes les notes",
  "command.navigation.goArchived": "Accéder aux notes archivées",
  "command.navigation.goChanges": "Accéder aux modifications",
  "command.navigation.goHistory": "Accéder à l'historique",
  "command.navigation.goBack": "Retour en arrière",
  "command.navigation.goForward": "Aller en avant",
  "command.navigation.goInbox": "Accéder à la boîte de réception",
  "command.navigation.renameFolder": "Renommer le dossier",
  "command.navigation.deleteFolder": "Supprimer le dossier",
  "command.navigation.showOpenNotes": "Afficher les notes ouvertes",
  "command.navigation.showArchivedNotes": "Afficher les notes archivées",
  "command.navigation.listType": "Liste {type}",
  "command.note.newNote": "Nouvelle note",
  "command.note.newNoteInCurrentFolder": "Créer une nouvelle note dans le dossier actuel",
  "command.note.newType": "Nouveau type",
  "command.note.newTypedNote": "Nouveau {type}",
  "command.note.saveNote": "Enregistrer la note",
  "command.note.undo": "Annuler",
  "command.note.undoAction": "Annuler {action}",
  "command.note.redo": "Rétablir",
  "command.note.redoAction": "Rétablir {action}",
  "command.note.pastePlainText": "Coller sans mise en forme",
  "command.note.findInNote": "Rechercher dans la note",
  "command.note.replaceInNote": "Remplacer dans la note",
  "command.note.deleteNote": "Supprimer la note",
  "command.note.archiveNote": "Archiver la note",
  "command.note.unarchiveNote": "Désarchiver la note",
  "command.note.addFavorite": "Ajouter aux favoris",
  "command.note.removeFavorite": "Supprimer des favoris",
  "command.note.markOrganized": "Marquer comme organisée",
  "command.note.markUnorganized": "Marquer comme non organisée",
  "command.note.restoreDeleted": "Restaurer la note supprimée",
  "command.note.setIcon": "Définir l'icône de la note",
  "command.note.removeIcon": "Supprimer l'icône de la note",
  "command.note.changeType": "Modifier le type de note…",
  "command.note.moveToFolder": "Déplacer la note vers le dossier…",
  "command.note.copyDeepLink": "Copier le lien profond vers l'élément actuel",
  "command.note.exportPdf": "Exporter la note au format PDF",
  "command.note.openNe
