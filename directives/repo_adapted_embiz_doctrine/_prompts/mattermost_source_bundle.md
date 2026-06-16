
===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/.cursor/README.md =====

# Cursor Cloud Agent Environment

This directory defines the checked-in Cloud Agent environment for this repository. Cursor resolves `.cursor/environment.json` before personal or team saved environments, so this replaces the snapshot-dependent `/onboard` flow for agents started from this repo.

The Docker build context is `.cursor/` only. The Dockerfile intentionally does not copy the repository; Cursor checks out the requested commit at runtime.

## What Is Baked Into The Image

- Ubuntu 24.04.
- Docker CE 28.5.2 with `fuse-overlayfs` and `iptables-legacy`, matching Cursor's Docker-in-Cloud guidance for complex compose setups.
- Go 1.25.9 from `server/.go-version`.
- Node 24.11.1/npm 11 via nvm, matching `.nvmrc` and `webapp/package.json`.
- Browser runtime libraries for the Playwright e2e suite.
- AWS CLI v2 for S3 uploads.
- Common Mattermost build/test tools: `make`, `jq`, `xmlsec1`, `pgloader`, Git LFS, GitHub CLI, Python 3, and build essentials.

## Runtime Hooks

- `cloud-agent-install.sh` runs after Cursor checks out the repo. It refreshes nvm, verifies Cursor's multi-repo `mattermost/enterprise` checkout, runs `server` Go dependency hydration, installs webapp dependencies, and runs Playwright `npm ci`.
- `cloud-agent-start.sh` materializes `.cursor/cursor.md` as `.cursor/AGENTS.md`, fixes current-session Docker socket access, starts Docker, waits until `docker info` and `docker compose version` succeed, then logs in to Docker Hub when credentials are configured.

The environment declares `github.com/mattermost/enterprise` in `repositoryDependencies` so Cursor can provide it as part of the multi-repo workspace. Cursor currently clones the repositories as siblings, such as `/agent/repos/mattermost` and `/agent/repos/enterprise`, which matches `server/Makefile`'s default `../../enterprise` path. The install hook does not clone, pull, or symlink enterprise.

## Useful Skips

Set these environment variables to `true` to shorten startup for narrow tasks:

- `CLOUD_AGENT_SKIP_ENTERPRISE`
- `CLOUD_AGENT_SKIP_GO_DEPS`
- `CLOUD_AGENT_SKIP_WEBAPP_DEPS`
- `CLOUD_AGENT_SKIP_PLAYWRIGHT_DEPS`

## Expected Secrets

Configure these in the [Cursor Cloud Agents dashboard](https://cursor.com/dashboard/cloud-agents) as environment-scoped secrets for the Mattermost Cloud Agent environment.

- AWS uploads use the standard AWS CLI environment variables: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `AWS_S3_BUCKET_NAME`. The image only supplies the `aws` binary.
- Docker Hub pulls use the same variable names as CI: `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN`. The start hook runs `docker login` after `dockerd` is ready. Mark `DOCKERHUB_TOKEN` as **redacted** in the dashboard. When both are set, agents can pull the full default `make start-docker` image set without hitting anonymous rate limits.

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/.cursor/cursor.md =====

# Cursor Cloud Agent Instructions

These instructions apply to Cursor Cloud Agents after `.cursor/scripts/cloud-agent-start.sh` materializes this file as `.cursor/AGENTS.md`.

## Environment

- Docker must be available. If `docker info` fails, inspect `/tmp/docker-service-start.log` and `/tmp/dockerd.log`; do not assume a snapshot will provide Docker.
- The image includes Go, Node/npm, Docker Compose, and AWS CLI v2.
- Cursor should provide `mattermost/enterprise` through the multi-repo environment. The expected layout is sibling repositories, such as `/agent/repos/mattermost` and `/agent/repos/enterprise`; this matches `server/Makefile`'s default `../../enterprise` path.

## Running Mattermost

1. Start dependencies:

   ```bash
   cd server
   make start-docker
   ```

2. Start the server:

   ```bash
   cd server
   make run-server
   ```

3. Start the web app in another terminal when UI work needs live verification:

   ```bash
   cd webapp
   make run
   ```

The Mattermost server is expected at `http://localhost:8065`. The webapp dev server commonly uses `http://localhost:9005`.

### Known-good Cloud flow

- In this multi-repo Cloud environment, `mattermost` and `enterprise` are expected to start from `master`, so sibling checkout skew should not need extra handling.
- `server/Makefile`'s `run` target only reaches `run-client` if the server is backgrounded. In Cloud, the reliable combined startup is:

  ```bash
  cd server
  ENABLED_DOCKER_SERVICES='postgres redis' RUN_SERVER_IN_BACKGROUND=true make run
  ```

- If you want split terminals instead, use:

  ```bash
  cd server
  ENABLED_DOCKER_SERVICES='postgres redis' make run-server
  ```

  and then:

  ```bash
  cd webapp
  make run
  ```

- When the server starts and `MM_LICENSE` is present in the environment, the server applies that license automatically. If `MM_LICENSE` is not set, starting the server automatically applies an Entry license, which provides nearly all functionality needed for development.
- When `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` are configured as Cloud Agent secrets, `cloud-agent-start.sh` logs in to Docker Hub and the full default `make start-docker` dependency set can be used without trimming services.
- `ENABLED_DOCKER_SERVICES='postgres redis'` avoids optional local-dev services such as Prometheus, Grafana, Loki, Minio, Azurite, and OpenLDAP. Use this fallback when Docker Hub credentials are unavailable and anonymous pulls hit rate limits.
- If the first-user signup UI is flaky but the server is already healthy, seed local state with `mmctl` and then log in through the browser:

  ```bash
  cd server
  ./bin/mmctl --local user create --email cursor@example.com --username cursoradmin --password Password123! --system-admin --email-verified --disable-welcome-email
  ./bin/mmctl --local team create --name cursorteam --display-name "Cursor Team" --email cursor@example.com
  ```

- A healthy server responds at:

  ```bash
  curl http://127.0.0.1:8065/api/v4/system/ping
  ```

## Tests And Setup

- Backend workspace setup is handled by `cd server && make setup-go-work`; never run `go mod tidy` directly.
- Webapp dependencies are installed with `cd webapp && make node_modules`.
- Playwright dependencies are installed with `cd e2e-tests/playwright && npm ci`.
- For full Playwright compose flows, use the existing `e2e-tests` Makefile and scripts. Docker Compose is available in the Cloud Agent image.

## Browser Verification

Use the `computerUse` subagent's desktop (Chrome is preinstalled) for browser automation and screenshots. Prefer verifying UI changes against the running local Mattermost instance before opening or updating a PR.

## AWS And PR Artifacts

AWS CLI v2 is installed for uploading screenshots or reports. Cloud Agents should receive `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `AWS_S3_BUCKET_NAME` as environment variables.

Before uploading, verify credentials with:

```bash
aws sts get-caller-identity
```

- If the configured S3 bucket is public, upload with `aws s3 cp` and share the plain object URL `https://$AWS_S3_BUCKET_NAME.s3.amazonaws.com/<key>` instead of generating a presigned URL.
Do not hardcode AWS credentials or bucket secrets in the repository.

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/.cursor/environment.json =====

{
  "name": "Mattermost Cloud Agent",
  "user": "ubuntu",
  "build": {
    "dockerfile": "Dockerfile",
    "context": "."
  },
  "repositoryDependencies": [
    "github.com/mattermost/enterprise"
  ],
  "install": "bash .cursor/scripts/cloud-agent-install.sh",
  "start": "bash .cursor/scripts/cloud-agent-start.sh",
  "ports": [
    {
      "name": "Mattermost server",
      "port": 8065
    },
    {
      "name": "Webapp dev server",
      "port": 9005
    }
  ]
}

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/.github/ISSUE_TEMPLATE.md =====

Before filing a bug report, please check the following:

1. Confirm you’re filing a new issue. [Search existing tickets in Jira](https://mattermost.atlassian.net/jira/software/c/projects/MM/issues/) and [existing issues in GitHub](https://github.com/mattermost/mattermost/issues) to ensure that the ticket does not already exist.
2. Confirm your issue does not involve security. Please submit security issues via our [Responsible Disclosure Policy](https://mattermost.com/security-vulnerability-report/).
3. Confirm your issue is not a feature request. Please submit feature requests on [UserVoice](https://mattermost.uservoice.com/forums/306457-general).
4. Confirm your issue is not a troubleshooting question. Please submit troubleshooting questions on the [forum](https://forum.mattermost.com/).
5. File a bug report using the format below. Mattermost will confirm steps to reproduce and file in Jira, or ask for more details if there is trouble reproducing it. If there's already an existing bug in Jira, it will be linked back to the GitHub issue so you can track when it gets fixed.

#### Summary
Bug report in one concise sentence.

#### Steps to reproduce
What are the steps to reproduce the issue?

#### Operating System
What Operating System do you use? (examples: Windows 10 x64, macOS Ventura 13.2 Apple Silicon, Ubuntu Linux 22.04 LTS x64)

#### Mattermost Server Version
Which version of the Mattermost Server did this occur on? (You can find your Mattermost Server version via **Mattermost Menu** > **About Mattermost**)

#### Expected behavior
What is the expected behaviour?

#### Observed behavior
What issue did you see happen?

#### Log Output
Output from the log files if applicable.

#### Additional Information
Additional helpful information, such as error messages and/or screenshots.

#### Possible fixes
If you can, link to the line of code that might be responsible for the problem.

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/.github/ISSUE_TEMPLATE/bug_report.yml =====

name: Bug report
description: Create a report about an issue you found
title: "[Bug]: "
labels: "Bug Report/Open"
body:
- type: checkboxes
  attributes:
    label: Before you file a bug report
    description: Please ensure you can confirm the following
    options:
      - label: I have checked the [issue tracker](https://github.com/mattermost/mattermost/issues) and have not found an issue that matches the one I'm filing.
        required: true
      - label: "This issue is not a troubleshooting question. Troubleshooting questions go here: https://forum.mattermost.com/c/trouble-shoot/16."
        required: true
      - label: "This issue is not a feature request. You can request features and make product suggestions here: https://mattermost.uservoice.com/forums/306457-general/."
        required: true
      - label: This issue reproduces on one of the [currently supported server versions](https://docs.mattermost.com/about/mattermost-server-releases.html#latest-releases).
        required: true
      - label: I have read the [contribution guidelines](https://github.com/mattermost/mattermost/blob/master/CONTRIBUTING.md) and the [Mattermost Handbook Contribution Guidelines](https://handbook.mattermost.com/contributors/contributors/guidelines/contribution-guidelines).
        required: true
- type: input
  attributes:
    label: Mattermost Server Version
    description: |
      What version of the Mattermost server are you using? You can find it by going to [Main Menu] > [About Mattermost].
  validations:
    required: true
- type: input
  attributes:
    label: Operating System
    description: |
      What operating system does this issue occur on?
      Example: Windows 10
  validations:
    required: true
- type: textarea
  attributes:
    label: Steps to reproduce
    description: |
      Include a clear description of the steps taken to reproduce this issue.
      It is also helpful to attach a screenshot or video if applicable.
  validations:
    required: true
- type: textarea
  attributes:
    label: Expected behavior
    description: Include a clear description of what you expect to happen.
  validations:
    required: true
- type: textarea
  attributes:
    label: Observed behavior
    description: Include a clear description of what actually happens.
  validations:
    required: true
- type: textarea
  attributes:
    label: Log Output
    description: Please include output from the log files.
    render: shell
- type: textarea
  attributes:
    label: Additional Information
    description: If you have anything else to add to the ticket, you may do so here.

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/.github/PULL_REQUEST_TEMPLATE.md =====

<!-- Summary and Release Note are required. Include Ticket Link and Screenshots as needed. -->

#### Summary
<!-- What does this PR do? Include QA steps if not covered in the ticket. -->

#### Ticket Link
<!--
Fixes: https://github.com/mattermost/mattermost/issues/XXX
Fixes: https://mattermost.atlassian.net/browse/MM-XXX
-->

#### Screenshots
<!-- Include screenshots or GIFs for UI changes. -->

#### Release Note
<!--
Write a release note if this PR includes any of:
* API or config changes.
* Schema migrations (added/dropped tables or columns, index changes, column type changes).
* User-visible behavior changes (UI, CLI, websocket).
* Deprecations, breaking changes, or compatibility notes.

The release-note block must always be present. Use past tense. Write NONE if none of the above apply. Newlines are stripped.

Example:
```release-note
Added new API endpoints POST /api/v4/foo and GET /api/v4/foo/:foo_id.
```

```release-note
NONE
```
-->
```release-note

```

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/.github/actions/calculate-cypress-results/action.yaml =====

name: Calculate Cypress Results
description: Calculate Cypress test results with optional merge of retest results
author: Mattermost

inputs:
  original-results-path:
    description: Path to the original Cypress results directory (e.g., e2e-tests/cypress/results)
    required: true
  retest-results-path:
    description: Path to the retest Cypress results directory (optional - if not provided, only calculates from original)
    required: false
  write-merged:
    description: Whether to write merged results back to the original directory (default true)
    required: false
    default: "true"

outputs:
  # Merge outputs
  merged:
    description: Whether merge was performed (true/false)

  # Calculation outputs (same as calculate-cypress-test-results)
  passed:
    description: Number of passed tests
  failed:
    description: Number of failed tests
  pending:
    description: Number of pending/skipped tests
  total_specs:
    description: Total number of spec files
  commit_status_message:
    description: Message for commit status (e.g., "X failed, Y passed (Z spec files)")
  failed_specs:
    description: Comma-separated list of failed spec files (for retest)
  failed_specs_count:
    description: Number of failed spec files
  failed_tests:
    description: Markdown table rows of failed tests (for GitHub summary)
  total:
    description: Total number of tests (passed + failed)
  pass_rate:
    description: Pass rate percentage (e.g., "100.00")
  color:
    description: Color for webhook based on pass rate (green=100%, yellow=99%+, orange=98%+, red=<98%)
  test_duration:
    description: Wall-clock test duration (earliest start to latest end across all specs, formatted as "Xm Ys")

runs:
  using: node24
  main: dist/index.js

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/.github/actions/calculate-cypress-results/package-lock.json =====

{
  "name": "calculate-cypress-results",
  "version": "0.1.0",
  "lockfileVersion": 3,
  "requires": true,
  "packages": {
    "": {
      "name": "calculate-cypress-results",
      "version": "0.1.0",
      "dependencies": {
        "@actions/core": "3.0.0"
      },
      "devDependencies": {
        "@github/local-action": "7.0.0",
        "@types/jest": "30.0.0",
        "@types/node": "25.2.0",
        "jest": "30.2.0",
        "ts-jest": "29.4.6",
        "tsup": "8.5.1",
        "typescript": "5.9.3"
      }
    },
    "node_modules/@actions/artifact": {
      "version": "5.0.3",
      "resolved": "https://registry.npmjs.org/@actions/artifact/-/artifact-5.0.3.tgz",
      "integrity": "sha512-FIEG8Kum0wABZnktJvFi1xuVPc31xrunhZwLCvjrCGISQOm0ifyo7cjqf6PHiEeqoWMa5HIGOsB+lGM4aKCseA==",
      "dev": true,
      "license": "MIT",
      "dependencies": {
        "@actions/core": "^2.0.0",
        "@actions/github": "^6.0.1",
        "@actions/http-client": "^3.0.2",
        "@azure/storage-blob": "^12.29.1",
        "@octokit/core": "^5.2.1",
        "@octokit/plugin-request-log": "^1.0.4",
        "@octokit/plugin-retry": "^3.0.9",
        "@octokit/request": "^8.4.1",
        "@octokit/request-error": "^5.1.1",
        "@protobuf-ts/plugin": "^2.2.3-alpha.1",
        "archiver": "^7.0.1",
        "jwt-decode": "^3.1.2",
        "unzip-stream": "^0.3.1"
      }
    },
    "node_modules/@actions/artifact/node_modules/@actions/core": {
      "version": "2.0.3",
      "resolved": "https://registry.npmjs.org/@actions/core/-/core-2.0.3.tgz",
      "integrity": "sha512-Od9Thc3T1mQJYddvVPM4QGiLUewdh+3txmDYHHxoNdkqysR1MbCT+rFOtNUxYAz+7+6RIsqipVahY2GJqGPyxA==",
      "dev": true,
      "license": "MIT",
      "dependencies": {
        "@actions/exec": "^2.0.0",
        "@actions/http-client": "^3.0.2"
      }
    },
    "node_modules/@actions/artifact/node_modules/@actions/exec": {
      "version": "2.0.0",
      "resolved": "https://registry.npmjs.org/@actions/exec/-/exec-2.0.0.tgz",
      "integrity": "sha512-k8ngrX2voJ/RIN6r9xB82NVqKpnMRtxDoiO+g3olkIUpQNqjArXrCQceduQZCQj3P3xm32pChRLqRrtXTlqhIw==",
      "dev": true,
      "license": "MIT",
      "dependencies": {
        "@actions/io": "^2.0.0"
      }
    },
    "node_modules/@actions/artifact/node_modules/@actions/github": {
      "version": "6.0.1",
      "resolved": "https://registry.npmjs.org/@actions/github/-/github-6.0.1.tgz",
      "integrity": "sha512-xbZVcaqD4XnQAe35qSQqskb3SqIAfRyLBrHMd/8TuL7hJSz2QtbDwnNM8zWx4zO5l2fnGtseNE3MbEvD7BxVMw==",
      "dev": true,
      "license": "MIT",
      "dependencies": {
        "@actions/http-client": "^2.2.0",
        "@octokit/core": "^5.0.1",
        "@octokit/plugin-paginate-rest": "^9.2.2",
        "@octokit/plugin-rest-endpoint-methods": "^10.4.0",
        "@octokit/request": "^8.4.1",
        "@octokit/request-error": "^5.1.1",
        "undici": "^5.28.5"
      }
    },
    "node_modules/@actions/artifact/node_modules/@actions/github/node_modules/@actions/http-client": {
      "version": "2.2.3",
      "resolved": "https://registry.npmjs.org/@actions/http-client/-/http-client-2.2.3.tgz",
      "integrity": "sha512-mx8hyJi/hjFvbPokCg4uRd4ZX78t+YyRPtnKWwIl+RzNaVuFpQHfmlGVfsKEJN8LwTCvL+DfVgAM04XaHkm6bA==",
      "dev": true,
      "license": "MIT",
      "dependencies": {
        "tunnel": "^0.0.6",
        "undici": "^5.25.4"
      }
    },
    "node_modules/@actions/artifact/node_modules/@actions/github/node_modules/undici": {
      "version": "5.29.0",
      "resolved": "https://registry.npmjs.org/undici/-/undici-5.29.0.tgz",
      "integrity": "sha512-raqeBD6NQK4SkWhQzeYKd1KmIG6dllBOTt55Rmkt4HtI9mwdWtJljnrXjAFUBLTSN67HWrOIZ3EPF4kjUw80Bg==",
      "dev": true,
      "license": "MIT",
      "dependencies": {
        "@fastify/busboy": "^2.0.0"
      },
      "engines": {
        "node": ">=14.0"
      }
    },
    "node_modules/@actions/artifact/node_modules/@actions/http-client": {
      "version": "3.0.2",
      "resolved": "https://registry.npmjs.org/@actions/http-client/-/http-client-3.0.2.tgz",
      "integrity": "sha512-JP38FYYpyqvUsz+Igqlc/JG6YO9PaKuvqjM3iGvaLqFnJ7TFmcLyy2IDrY0bI0qCQug8E9K+elv5ZNfw62ZJzA==",
      "dev": true,
      "license": "MIT",
      "dependencies": {
        "tunnel": "^0.0.6",
        "undici": "^6.23.0"
      }
    },
    "node_modules/@actions/artifact/node_modules/@actions/io": {
      "version": "2.0.0",
      "resolved": "https://registry.npmjs.org/@actions/io/-/io-2.0.0.tgz",
      "integrity": "sha512-Jv33IN09XLO+0HS79aaODsvIRyduiF7NY/F6LYeK5oeUmrsz7aFdRphQjFoESF4jS7lMauDOttKALcpapVDIAg==",
      "dev": true,
      "license": "MIT"
    },
    "node_modules/@actions/artifact/node_modules/@octokit/auth-token": {
      "version": "4.0.0",
      "resolved": "https://registry.npmjs.org/@octokit/auth-token/-/auth-token-4.0.0.tgz",
      "integrity": "sha512-tY/msAuJo6ARbK6SPIxZrPBms3xPbfwBrulZe0Wtr/DIY9lje2HeV1uoebShn6mx7SjCHif6EjMvoREj+gZ+SA==",
      "dev": true,
      "license": "MIT",
      "engines": {
        "node": ">= 18"
      }
    },
    "node_modules/@actions/artifact/node_modules/@octokit/core": {
      "version": "5.2.2",
      "resolved": "https://registry.npmjs.org/@octokit/core/-/core-5.2.2.tgz",
      "integrity": "sha512-/g2d4sW9nUDJOMz3mabVQvOGhVa4e/BN/Um7yca9Bb2XTzPPnfTWHWQg+IsEYO7M3Vx+EXvaM/I2pJWIMun1bg==",
      "dev": true,
      "license": "MIT",
      "peer": true,
      "dependencies": {
        "@octokit/auth-token": "^4.0.0",
        "@octokit/graphql": "^7.1.0",
        "@octokit/request": "^8.4.1",
        "@octokit/request-error": "^5.1.1",
        "@octokit/types": "^13.0.0",
        "before-after-hook": "^2.2.0",
        "universal-user-agent": "^6.0.0"
      },
      "engines": {
        "node": ">= 18"
      }
    },
    "node_modules/@actions/artifact/node_modules/@octokit/graphql": {
      "version": "7.1.1",
      "resolved": "https://registry.npmjs.org/@octokit/graphql/-/graphql-7.1.1.tgz",
      "integrity": "sha512-3mkDltSfcDUoa176nlGoA32RGjeWjl3K7F/BwHwRMJUW/IteSa4bnSV8p2ThNkcIcZU2umkZWxwETSSCJf2Q7g==",
      "dev": true,
      "license": "MIT",
      "dependencies": {
        "@octokit/request": "^8.4.1",
        "@octokit/types": "^13.0.0",
        "universal-user-agent": "^6.0.0"
      },
      "engines": {
        "node": ">= 18"
      }
    },
    "node_modules/@actions/artifact/node_modules/@octokit/openapi-types": {
      "version": "24.2.0",
      "resolved": "https://registry.npmjs.org/@octokit/openapi-types/-/openapi-types-24.2.0.tgz",
      "integrity": "sha512-9sIH3nSUttelJSXUrmGzl7QUBFul0/mB8HRYl3fOlgHbIWG+WnYDXU3v/2zMtAvuzZ/ed00Ei6on975FhBfzrg==",
      "dev": true,
      "license": "MIT"
    },
    "node_modules/@actions/artifact/node_modules/@octokit/plugin-paginate-rest": {
      "version": "9.2.2",
      "resolved": "https://registry.npmjs.org/@octokit/plugin-paginate-rest/-/plugin-paginate-rest-9.2.2.tgz",
      "integrity": "sha512-u3KYkGF7GcZnSD/3UP0S7K5XUFT2FkOQdcfXZGZQPGv3lm4F2Xbf71lvjldr8c1H3nNbF+33cLEkWYbokGWqiQ==",
      "dev": true,

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/.github/actions/calculate-cypress-results/package.json =====

{
  "name": "calculate-cypress-results",
  "private": true,
  "version": "0.1.0",
  "main": "dist/index.js",
  "scripts": {
    "build": "tsup",
    "prettier": "npx prettier --write \"src/**/*.ts\"",
    "local-action": "local-action . src/main.ts .env",
    "test": "jest --verbose",
    "test:watch": "jest --watch --verbose",
    "test:silent": "jest --silent",
    "tsc": "tsc -b"
  },
  "dependencies": {
    "@actions/core": "3.0.0"
  },
  "devDependencies": {
    "@github/local-action": "7.0.0",
    "@types/jest": "30.0.0",
    "@types/node": "25.2.0",
    "jest": "30.2.0",
    "ts-jest": "29.4.6",
    "tsup": "8.5.1",
    "typescript": "5.9.3"
  }
}

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/.github/actions/calculate-cypress-results/tsconfig.json =====

{
  "compilerOptions": {
    "target": "ES2022",
    "module": "CommonJS",
    "moduleResolution": "Node",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "outDir": "./dist",
    "rootDir": "./src",
    "declaration": true,
    "isolatedModules": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist", "**/*.test.ts"]
}

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/.github/actions/calculate-playwright-results/action.yaml =====

name: Calculate Playwright Results
description: Calculate Playwright test results with optional merge of retest results
author: Mattermost

inputs:
  original-results-path:
    description: Path to the original Playwright results.json file
    required: true
  retest-results-path:
    description: Path to the retest Playwright results.json file (optional - if not provided, only calculates from original)
    required: false
  output-path:
    description: Path to write the merged results.json file (defaults to original-results-path)
    required: false

outputs:
  # Merge outputs
  merged:
    description: Whether merge was performed (true/false)

  # Calculation outputs (same as calculate-playwright-test-results)
  passed:
    description: Number of passed tests (not including flaky)
  failed:
    description: Number of failed tests
  flaky:
    description: Number of flaky tests (failed initially but passed on retry)
  skipped:
    description: Number of skipped tests
  total_specs:
    description: Total number of spec files
  commit_status_message:
    description: Message for commit status (e.g., "X failed, Y passed (Z spec files)")
  failed_specs:
    description: Comma-separated list of failed spec files (for retest)
  failed_specs_count:
    description: Number of failed spec files
  failed_tests:
    description: Markdown table rows of failed tests (for GitHub summary)
  total:
    description: Total number of tests (passed + flaky + failed)
  pass_rate:
    description: Pass rate percentage (e.g., "100.00")
  passing:
    description: Number of passing tests (passed + flaky)
  color:
    description: Color for webhook based on pass rate (green=100%, yellow=99%+, orange=98%+, red=<98%)
  test_duration:
    description: Test execution duration from stats (formatted as "Xm Ys")

runs:
  using: node24
  main: dist/index.js

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/.github/actions/calculate-playwright-results/package-lock.json =====

{
  "name": "calculate-playwright-results",
  "version": "0.1.0",
  "lockfileVersion": 3,
  "requires": true,
  "packages": {
    "": {
      "name": "calculate-playwright-results",
      "version": "0.1.0",
      "dependencies": {
        "@actions/core": "3.0.0"
      },
      "devDependencies": {
        "@github/local-action": "7.0.0",
        "@types/jest": "30.0.0",
        "@types/node": "25.2.0",
        "jest": "30.2.0",
        "ts-jest": "29.4.6",
        "tsup": "8.5.1",
        "typescript": "5.9.3"
      }
    },
    "node_modules/@actions/artifact": {
      "version": "5.0.3",
      "resolved": "https://registry.npmjs.org/@actions/artifact/-/artifact-5.0.3.tgz",
      "integrity": "sha512-FIEG8Kum0wABZnktJvFi1xuVPc31xrunhZwLCvjrCGISQOm0ifyo7cjqf6PHiEeqoWMa5HIGOsB+lGM4aKCseA==",
      "dev": true,
      "license": "MIT",
      "dependencies": {
        "@actions/core": "^2.0.0",
        "@actions/github": "^6.0.1",
        "@actions/http-client": "^3.0.2",
        "@azure/storage-blob": "^12.29.1",
        "@octokit/core": "^5.2.1",
        "@octokit/plugin-request-log": "^1.0.4",
        "@octokit/plugin-retry": "^3.0.9",
        "@octokit/request": "^8.4.1",
        "@octokit/request-error": "^5.1.1",
        "@protobuf-ts/plugin": "^2.2.3-alpha.1",
        "archiver": "^7.0.1",
        "jwt-decode": "^3.1.2",
        "unzip-stream": "^0.3.1"
      }
    },
    "node_modules/@actions/artifact/node_modules/@actions/core": {
      "version": "2.0.3",
      "resolved": "https://registry.npmjs.org/@actions/core/-/core-2.0.3.tgz",
      "integrity": "sha512-Od9Thc3T1mQJYddvVPM4QGiLUewdh+3txmDYHHxoNdkqysR1MbCT+rFOtNUxYAz+7+6RIsqipVahY2GJqGPyxA==",
      "dev": true,
      "license": "MIT",
      "dependencies": {
        "@actions/exec": "^2.0.0",
        "@actions/http-client": "^3.0.2"
      }
    },
    "node_modules/@actions/artifact/node_modules/@actions/exec": {
      "version": "2.0.0",
      "resolved": "https://registry.npmjs.org/@actions/exec/-/exec-2.0.0.tgz",
      "integrity": "sha512-k8ngrX2voJ/RIN6r9xB82NVqKpnMRtxDoiO+g3olkIUpQNqjArXrCQceduQZCQj3P3xm32pChRLqRrtXTlqhIw==",
      "dev": true,
      "license": "MIT",
      "dependencies": {
        "@actions/io": "^2.0.0"
      }
    },
    "node_modules/@actions/artifact/node_modules/@actions/github": {
      "version": "6.0.1",
      "resolved": "https://registry.npmjs.org/@actions/github/-/github-6.0.1.tgz",
      "integrity": "sha512-xbZVcaqD4XnQAe35qSQqskb3SqIAfRyLBrHMd/8TuL7hJSz2QtbDwnNM8zWx4zO5l2fnGtseNE3MbEvD7BxVMw==",
      "dev": true,
      "license": "MIT",
      "dependencies": {
        "@actions/http-client": "^2.2.0",
        "@octokit/core": "^5.0.1",
        "@octokit/plugin-paginate-rest": "^9.2.2",
        "@octokit/plugin-rest-endpoint-methods": "^10.4.0",
        "@octokit/request": "^8.4.1",
        "@octokit/request-error": "^5.1.1",
        "undici": "^5.28.5"
      }
    },
    "node_modules/@actions/artifact/node_modules/@actions/github/node_modules/@actions/http-client": {
      "version": "2.2.3",
      "resolved": "https://registry.npmjs.org/@actions/http-client/-/http-client-2.2.3.tgz",
      "integrity": "sha512-mx8hyJi/hjFvbPokCg4uRd4ZX78t+YyRPtnKWwIl+RzNaVuFpQHfmlGVfsKEJN8LwTCvL+DfVgAM04XaHkm6bA==",
      "dev": true,
      "license": "MIT",
      "dependencies": {
        "tunnel": "^0.0.6",
        "undici": "^5.25.4"
      }
    },
    "node_modules/@actions/artifact/node_modules/@actions/github/node_modules/undici": {
      "version": "5.29.0",
      "resolved": "https://registry.npmjs.org/undici/-/undici-5.29.0.tgz",
      "integrity": "sha512-raqeBD6NQK4SkWhQzeYKd1KmIG6dllBOTt55Rmkt4HtI9mwdWtJljnrXjAFUBLTSN67HWrOIZ3EPF4kjUw80Bg==",
      "dev": true,
      "license": "MIT",
      "dependencies": {
        "@fastify/busboy": "^2.0.0"
      },
      "engines": {
        "node": ">=14.0"
      }
    },
    "node_modules/@actions/artifact/node_modules/@actions/http-client": {
      "version": "3.0.2",
      "resolved": "https://registry.npmjs.org/@actions/http-client/-/http-client-3.0.2.tgz",
      "integrity": "sha512-JP38FYYpyqvUsz+Igqlc/JG6YO9PaKuvqjM3iGvaLqFnJ7TFmcLyy2IDrY0bI0qCQug8E9K+elv5ZNfw62ZJzA==",
      "dev": true,
      "license": "MIT",
      "dependencies": {
        "tunnel": "^0.0.6",
        "undici": "^6.23.0"
      }
    },
    "node_modules/@actions/artifact/node_modules/@actions/io": {
      "version": "2.0.0",
      "resolved": "https://registry.npmjs.org/@actions/io/-/io-2.0.0.tgz",
      "integrity": "sha512-Jv33IN09XLO+0HS79aaODsvIRyduiF7NY/F6LYeK5oeUmrsz7aFdRphQjFoESF4jS7lMauDOttKALcpapVDIAg==",
      "dev": true,
      "license": "MIT"
    },
    "node_modules/@actions/artifact/node_modules/@octokit/auth-token": {
      "version": "4.0.0",
      "resolved": "https://registry.npmjs.org/@octokit/auth-token/-/auth-token-4.0.0.tgz",
      "integrity": "sha512-tY/msAuJo6ARbK6SPIxZrPBms3xPbfwBrulZe0Wtr/DIY9lje2HeV1uoebShn6mx7SjCHif6EjMvoREj+gZ+SA==",
      "dev": true,
      "license": "MIT",
      "engines": {
        "node": ">= 18"
      }
    },
    "node_modules/@actions/artifact/node_modules/@octokit/core": {
      "version": "5.2.2",
      "resolved": "https://registry.npmjs.org/@octokit/core/-/core-5.2.2.tgz",
      "integrity": "sha512-/g2d4sW9nUDJOMz3mabVQvOGhVa4e/BN/Um7yca9Bb2XTzPPnfTWHWQg+IsEYO7M3Vx+EXvaM/I2pJWIMun1bg==",
      "dev": true,
      "license": "MIT",
      "peer": true,
      "dependencies": {
        "@octokit/auth-token": "^4.0.0",
        "@octokit/graphql": "^7.1.0",
        "@octokit/request": "^8.4.1",
        "@octokit/request-error": "^5.1.1",
        "@octokit/types": "^13.0.0",
        "before-after-hook": "^2.2.0",
        "universal-user-agent": "^6.0.0"
      },
      "engines": {
        "node": ">= 18"
      }
    },
    "node_modules/@actions/artifact/node_modules/@octokit/graphql": {
      "version": "7.1.1",
      "resolved": "https://registry.npmjs.org/@octokit/graphql/-/graphql-7.1.1.tgz",
      "integrity": "sha512-3mkDltSfcDUoa176nlGoA32RGjeWjl3K7F/BwHwRMJUW/IteSa4bnSV8p2ThNkcIcZU2umkZWxwETSSCJf2Q7g==",
      "dev": true,
      "license": "MIT",
      "dependencies": {
        "@octokit/request": "^8.4.1",
        "@octokit/types": "^13.0.0",
        "universal-user-agent": "^6.0.0"
      },
      "engines": {
        "node": ">= 18"
      }
    },
    "node_modules/@actions/artifact/node_modules/@octokit/openapi-types": {
      "version": "24.2.0",
      "resolved": "https://registry.npmjs.org/@octokit/openapi-types/-/openapi-types-24.2.0.tgz",
      "integrity": "sha512-9sIH3nSUttelJSXUrmGzl7QUBFul0/mB8HRYl3fOlgHbIWG+WnYDXU3v/2zMtAvuzZ/ed00Ei6on975FhBfzrg==",
      "dev": true,
      "license": "MIT"
    },
    "node_modules/@actions/artifact/node_modules/@octokit/plugin-paginate-rest": {
      "version": "9.2.2",
      "resolved": "https://registry.npmjs.org/@octokit/plugin-paginate-rest/-/plugin-paginate-rest-9.2.2.tgz",
      "integrity": "sha512-u3KYkGF7GcZnSD/3UP0S7K5XUFT2FkOQdcfXZGZQPGv3lm4F2Xbf71lvjldr8c1H3nNbF+33cLEkWYbokGWqiQ==",
      "dev": true,

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/.github/actions/calculate-playwright-results/package.json =====

{
  "name": "calculate-playwright-results",
  "private": true,
  "version": "0.1.0",
  "main": "dist/index.js",
  "scripts": {
    "build": "tsup",
    "prettier": "npx prettier --write \"src/**/*.ts\"",
    "local-action": "local-action . src/main.ts .env",
    "test": "jest --verbose",
    "test:watch": "jest --watch --verbose",
    "test:silent": "jest --silent",
    "tsc": "tsc -b"
  },
  "dependencies": {
    "@actions/core": "3.0.0"
  },
  "devDependencies": {
    "@github/local-action": "7.0.0",
    "@types/jest": "30.0.0",
    "@types/node": "25.2.0",
    "jest": "30.2.0",
    "ts-jest": "29.4.6",
    "tsup": "8.5.1",
    "typescript": "5.9.3"
  }
}

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/.github/actions/calculate-playwright-results/tsconfig.json =====

{
  "compilerOptions": {
    "target": "ES2022",
    "module": "CommonJS",
    "moduleResolution": "Node",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "outDir": "dist",
    "rootDir": "./src",
    "declaration": true,
    "isolatedModules": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist", "**/*.test.ts"]
}

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/.github/actions/check-e2e-test-only/action.yml =====

---
name: Check E2E Test Only
description: Check if PR contains only E2E test changes and determine the appropriate docker image tag

inputs:
  base_sha:
    description: Base commit SHA (PR base)
    required: false
  head_sha:
    description: Head commit SHA (PR head)
    required: false
  pr_number:
    description: PR number (used to fetch SHAs via API if base_sha/head_sha not provided)
    required: false

outputs:
  e2e_test_only:
    description: Whether the PR contains only E2E test changes (true/false)
    value: ${{ steps.check.outputs.e2e_test_only }}
  image_tag:
    description: Docker image tag to use (base branch ref for E2E-only, short SHA for mixed)
    value: ${{ steps.check.outputs.image_tag }}

runs:
  using: composite
  steps:
    - name: ci/check-e2e-test-only
      id: check
      shell: bash
      env:
        GH_TOKEN: ${{ github.token }}
        GITHUB_REPOSITORY: ${{ github.repository }}
        INPUT_BASE_SHA: ${{ inputs.base_sha }}
        INPUT_HEAD_SHA: ${{ inputs.head_sha }}
        INPUT_PR_NUMBER: ${{ inputs.pr_number }}
      run: |
        # Resolve SHAs and base branch from PR number if not provided
        BASE_REF=""
        if [ -z "$INPUT_BASE_SHA" ] || [ -z "$INPUT_HEAD_SHA" ]; then
          if [ -z "$INPUT_PR_NUMBER" ]; then
            echo "::error::Either base_sha/head_sha or pr_number must be provided"
            exit 1
          fi

          echo "Resolving SHAs from PR #${INPUT_PR_NUMBER}"
          PR_DATA=$(gh api "repos/${GITHUB_REPOSITORY}/pulls/${INPUT_PR_NUMBER}")
          INPUT_BASE_SHA=$(echo "$PR_DATA" | jq -r '.base.sha')
          INPUT_HEAD_SHA=$(echo "$PR_DATA" | jq -r '.head.sha')
          BASE_REF=$(echo "$PR_DATA" | jq -r '.base.ref')

          if [ -z "$INPUT_BASE_SHA" ] || [ "$INPUT_BASE_SHA" = "null" ] || \
             [ -z "$INPUT_HEAD_SHA" ] || [ "$INPUT_HEAD_SHA" = "null" ]; then
            echo "::error::Could not resolve SHAs for PR #${INPUT_PR_NUMBER}"
            exit 1
          fi
        elif [ -n "$INPUT_PR_NUMBER" ]; then
          # SHAs provided but we still need the base branch ref
          BASE_REF=$(gh api "repos/${GITHUB_REPOSITORY}/pulls/${INPUT_PR_NUMBER}" --jq '.base.ref')
        fi

        # Default to master if base ref could not be determined
        if [ -z "$BASE_REF" ] || [ "$BASE_REF" = "null" ]; then
          BASE_REF="master"
        fi
        echo "PR base branch: ${BASE_REF}"

        SHORT_SHA="${INPUT_HEAD_SHA::7}"

        # Get changed files - try git first, fall back to API
        CHANGED_FILES=$(git diff --name-only "$INPUT_BASE_SHA"..."$INPUT_HEAD_SHA" 2>/dev/null || \
          gh api "repos/${GITHUB_REPOSITORY}/pulls/${INPUT_PR_NUMBER}/files" --jq '.[].filename' 2>/dev/null || echo "")

        if [ -z "$CHANGED_FILES" ]; then
          echo "::warning::Could not determine changed files, assuming not E2E-only"
          echo "e2e_test_only=false" >> $GITHUB_OUTPUT
          echo "image_tag=${SHORT_SHA}" >> $GITHUB_OUTPUT
          exit 0
        fi

        echo "Changed files:"
        echo "$CHANGED_FILES"

        # Check if all files are E2E-related
        E2E_TEST_ONLY="true"
        while IFS= read -r file; do
          [ -z "$file" ] && continue
          if [[ ! "$file" =~ ^e2e-tests/ ]] && \
             [[ ! "$file" =~ ^\.github/workflows/e2e- ]] && \
             [[ ! "$file" =~ ^\.github/actions/ ]]; then
            echo "Non-E2E file found: $file"
            E2E_TEST_ONLY="false"
            break
          fi
        done <<< "$CHANGED_FILES"

        echo "E2E test only: ${E2E_TEST_ONLY}"

        # Set outputs
        echo "e2e_test_only=${E2E_TEST_ONLY}" >> $GITHUB_OUTPUT
        if [ "$E2E_TEST_ONLY" = "true" ] && \
           { [ "$BASE_REF" = "master" ] || [[ "$BASE_REF" =~ ^release-[0-9]+\.[0-9]+$ ]]; }; then
          echo "image_tag=${BASE_REF}" >> $GITHUB_OUTPUT
        else
          echo "image_tag=${SHORT_SHA}" >> $GITHUB_OUTPUT
        fi

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/.github/actions/runner-prep-openldap/action.yml =====

name: Runner prep for openldap
description: |
  Disable the Ubuntu 24.04 AppArmor user-namespace restriction and ensure
  docker-compose >= 2.36.0 before starting any stack that includes openldap.

  Background: Ubuntu 24.04 sets kernel.apparmor_restrict_unprivileged_userns=1
  by default.  The osixia/openldap:1.4.0 init scripts rely on unprivileged
  user namespaces; blocking them causes an immediate exit(1) with no useful
  stderr ("dependency failed to start: container mmserver-openldap-1 exited (1)").
  The container's own security_opt: apparmor:unconfined is insufficient — it
  only unconfines the slapd process, not the entrypoint.  The fix must be at
  the host-kernel level.

  docker-compose 2.35.1 (shipped on some ubuntu-24.04 runner images) also has
  a known `up` regression that surfaces as spurious dependency-failed errors
  under load.  We upgrade to >= 2.36.0 when needed.

runs:
  using: composite
  steps:
    - name: Disable AppArmor user-namespace restriction and ensure docker-compose >= 2.36.0
      shell: bash
      run: |
        echo "Before: docker compose version"
        docker compose version || true

        # Disable the AppArmor user-namespace restriction.  Idempotent;
        # safe if the key doesn't exist (older kernel).
        sudo sysctl -w kernel.apparmor_restrict_unprivileged_userns=0 || true

        # If docker-compose is older than 2.36.0, install a newer one to
        # the user's cli-plugins dir (takes precedence over the system copy).
        CURRENT=$(docker compose version --short 2>/dev/null || echo "0.0.0")
        NEED="2.36.0"
        if [ "$(printf '%s\n' "$NEED" "$CURRENT" | sort -V | head -n1)" != "$NEED" ]; then
          echo "Upgrading docker-compose from ${CURRENT} to 2.39.1"
          mkdir -p "$HOME/.docker/cli-plugins"
          curl -SL -o "$HOME/.docker/cli-plugins/docker-compose" \
            "https://github.com/docker/compose/releases/download/v2.39.1/docker-compose-linux-x86_64"
          chmod +x "$HOME/.docker/cli-plugins/docker-compose"
        fi

        echo "After: docker compose version"
        docker compose version

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/.github/actions/save-junit-report-tms/README.md =====

# Save JUnit Test Report to TMS Action

GitHub Action to save JUnit test reports to Zephyr Scale Test Management System.

## Usage

```yaml
- name: Save JUnit test report to Zephyr
  uses: ./.github/actions/save-junit-report-tms
  with:
    report-path: ./test-reports/report.xml
    zephyr-api-key: ${{ secrets.ZEPHYR_API_KEY }}
    build-image: ${{ env.BUILD_IMAGE }}
    zephyr-folder-id: '27504432'  # Optional, defaults to 27504432
    jira-project-key: 'MM'  # Optional, defaults to MM
```

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `report-path` | Path to the XML test report file (from artifact) | Yes | - |
| `zephyr-api-key` | Zephyr Scale API key | Yes | - |
| `build-image` | Docker build image used for testing | Yes | - |
| `zephyr-folder-id` | Zephyr Scale folder ID | No | `27504432` |
| `jira-project-key` | Jira project key | No | `MM` |

## Outputs

| Output | Description |
|--------|-------------|
| `test-cycle` | The created test cycle key in Zephyr Scale |
| `test-keys-execution-count` | Total number of test executions (including duplicates) |
| `test-keys-unique-count` | Number of unique test keys successfully saved to Zephyr |
| `junit-total-tests` | Total number of tests in the JUnit XML report |
| `junit-total-passed` | Number of passed tests in the JUnit XML report |
| `junit-total-failed` | Number of failed tests in the JUnit XML report |
| `junit-pass-rate` | Pass rate percentage from the JUnit XML report |
| `junit-duration-seconds` | Total test duration in seconds from the JUnit XML report |

## Local Development

1. Copy `.env.example` to `.env` and fill in your values
2. Run `npm install` to install dependencies
3. Run `npm run pretter` to format code
4. Run `npm test` to run unit tests
5. Run `npm run local-action` to test locally
6. Run `npm run build` to build for production

### Submitting Code Changes

**IMPORTANT**: When submitting code changes, you must run the following checks locally as there are no CI jobs for this action:

1. Run `npm run prettier` to format your code
2. Run `npm test` to ensure all tests pass
3. Run `npm run build` to compile your changes
4. Include the updated `dist/` folder in your commit

GitHub Actions runs the compiled code from the `dist/` folder, not the source TypeScript files. If you don't include the built files, your changes won't be reflected in the action.

## Report Format

The action expects a JUnit XML format report with test case names containing Zephyr test keys in the format `{PROJECT_KEY}-T{NUMBER}` (e.g., `MM-T1234`, `FOO-T5678`).

The test key pattern is automatically determined by the `jira-project-key` input (defaults to `MM`).

Example:
```xml
<testsuites tests="10" failures="2" errors="0" time="45.2">
  <testsuite name="mmctl tests" tests="10" failures="2" time="45.2" timestamp="2024-01-01T00:00:00Z">
    <testcase name="MM-T1234 - Test user creation" time="2.5"/>
    <testcase name="MM-T1235 - Test user login" time="3.2">
      <failure message="Login failed"/>
    </testcase>
  </testsuite>
</testsuites>
```

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/.github/actions/save-junit-report-tms/action.yaml =====

name: Save JUnit Test Report to TMS
description: Save JUnit test report to Zephyr Scale Test Management System
author: Mattermost

# Define your inputs here.
inputs:
  report-path:
    description: Path to the XML test report file (from artifact)
    required: true
  zephyr-api-key:
    description: Zephyr Scale API key
    required: true
  build-image:
    description: Docker build image used for testing
    required: true
  zephyr-folder-id:
    description: Zephyr Scale folder ID
    required: false
    default: '27504432'
  jira-project-key:
    description: Jira project key
    required: false
    default: 'MM'

# Define your outputs here.
outputs:
  test-cycle:
    description: The created test cycle key in Zephyr Scale
  test-keys-execution-count:
    description: Total number of test executions (including duplicates)
  test-keys-unique-count:
    description: Number of unique test keys successfully saved to Zephyr
  junit-total-tests:
    description: Total number of tests in the JUnit XML report
  junit-total-passed:
    description: Number of passed tests in the JUnit XML report
  junit-total-failed:
    description: Number of failed tests in the JUnit XML report
  junit-pass-rate:
    description: Pass rate percentage from the JUnit XML report
  junit-duration-seconds:
    description: Total test duration in seconds from the JUnit XML report

runs:
  using: node24
  main: dist/index.js

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/.github/actions/save-junit-report-tms/package.json =====

{
  "name": "save-junit-report-tms",
  "private": true,
  "version": "0.1.0",
  "main": "dist/index.js",
  "scripts": {
    "build": "tsup",
    "prettier": "npx prettier --write \"src/**/*.ts\"",
    "local-action": "local-action . src/main.ts .env",
    "test": "jest --verbose",
    "test:watch": "jest --watch --verbose",
    "test:silent": "jest --silent"
  },
  "dependencies": {
    "@actions/core": "1.11.1",
    "fast-xml-parser": "5.3.1"
  },
  "devDependencies": {
    "@github/local-action": "6.0.2",
    "@types/jest": "30.0.0",
    "jest": "30.2.0",
    "ts-jest": "29.4.5",
    "tsup": "8.5.0",
    "typescript": "5.9.3"
  }
}

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/.github/actions/save-junit-report-tms/tsconfig.json =====

{
  "compilerOptions": {
    "target": "esnext",
    "module": "commonjs",
    "outDir": "./lib",
    "rootDir": "./src",
    "strict": true,
    "noImplicitAny": true,
    "esModuleInterop": true,
    "typeRoots": ["./node_modules/@types"]
  },
  "exclude": ["node_modules", "../../../node_modules"]
}

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/.github/actions/webapp-setup/action.yml =====

name: "Web app setup"
description: "Set up NPM and dependencies"

runs:
  using: "composite"
  steps:
    - name: ci/setup-node
      uses: actions/setup-node@6044e13b5dc448c55e2357c09f80417699197238 # v6.2.0
      with:
        node-version-file: ".nvmrc"
    - name: ci/cache-node-modules
      uses: actions/cache@cdf6c1fa76f9f475f3d7449005a359c84ca0f306 # v5.0.3
      id: cache-node-modules
      with:
        path: |
          webapp/node_modules
          webapp/channels/node_modules
          webapp/platform/client/node_modules
          webapp/platform/components/node_modules
          webapp/platform/shared/node_modules
          webapp/platform/types/node_modules
        key: node-modules-${{ runner.os }}-${{ hashFiles('webapp/package-lock.json') }}
    - name: ci/get-node-modules
      if: steps.cache-node-modules.outputs.cache-hit != 'true'
      shell: bash
      working-directory: webapp
      run: |
        make node_modules
    - name: ci/build-platform-packages
      # These are built automatically when depenedencies are installed, but they aren't cached properly, so we need to
      # manually build them when the cache is hit. They aren't worth caching because they have too many dependencies.
      if: steps.cache-node-modules.outputs.cache-hit == 'true'
      shell: bash
      working-directory: webapp
      run: |
        npm run postinstall

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/.github/codecov.yml =====

codecov:
  require_ci_to_pass: false
  # Wait for all coverage uploads (4 server shards + 1 webapp) before
  # computing status. Without this, Codecov may report partial coverage
  # from the first shard to finish, showing a misleading drop on the PR.
  notify:
    after_n_builds: 5

coverage:
  status:
    project:
      default:
        target: auto
        threshold: 1%
        informational: true
    patch:
      default:
        target: 50%
        informational: true

  # Exclude generated code, mocks, and test infrastructure from reporting.
  # Go compiles these into the test binary, so they appear in cover.out,
  # but they aren't production code and inflate the denominator.
  ignore:
    - "server/**/retrylayer/**"
    - "server/**/timerlayer/**"
    - "server/**/*_serial_gen.go"
    - "server/**/mocks/**"
    - "server/**/storetest/**"
    - "server/**/plugintest/**"
    - "server/**/searchtest/**"

flags:
  server:
    after_n_builds: 4 # 4 server test shards
  webapp:
    after_n_builds: 1 # 1 merged webapp upload

comment:
  layout: "condensed_header,diff,flags"
  behavior: default
  require_changes: true

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/.github/codeql/codeql-config.yml =====

name: "CodeQL config"

query-filters:
  - exclude:
      problem.severity:
        - warning
        - recommendation
  - exclude:
      id: go/log-injection
  - exclude:
      id: js/insecure-randomness

paths-ignore:
  - templates
  - tests
  - 'api4/*_local.go'
  - webapp/channels/tests
  - '**/*.test.*'
  - e2e-tests

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/.github/dependabot.yml =====

version: 2
updates:
  - package-ecosystem: "github-actions"
    directory: "/"
    reviewers:
      - "mattermost/core-build-engineers"
    open-pull-requests-limit: 5
    groups:
      Github Actions updates:
        applies-to: version-updates
        dependency-type: production
    schedule:
      # Check for updates to GitHub Actions every week
      day: "monday"
      time: "09:00"
      interval: "weekly"
    cooldown:
      default-days: 15  # 15 days of cooldown for dependency updates (only version updates)

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/.github/e2e-tests-workflows.md =====

# E2E Test Pipelines

Three automated E2E test pipelines cover different stages of the development lifecycle.

## Pipelines

| Pipeline | Trigger | Editions Tested | Image Source |
|----------|---------|----------------|--------------|
| **PR** (`e2e-tests-ci.yml`) | Argo Events on `Enterprise CI/docker-image` status | enterprise | `mattermostdevelopment/**` |
| **Merge to master/release** (`e2e-tests-on-merge.yml`) | Platform delivery after docker build (`delivery-platform/.github/workflows/mattermost-platform-delivery.yaml`) | enterprise, fips | `mattermostdevelopment/**` |
| **Release cut** (`e2e-tests-on-release.yml`) | Platform release after docker build (`delivery-platform/.github/workflows/release-mattermost-platform.yml`) | enterprise, fips, team (future) | `mattermost/**` |

All pipelines follow the **smoke-then-full** pattern: smoke tests run first, full tests only run if smoke passes.

## Workflow Files

```
.github/workflows/
├── e2e-tests-ci.yml                       # PR orchestrator
├── e2e-tests-on-merge.yml                 # Merge orchestrator (master/release branches)
├── e2e-tests-on-release.yml               # Release cut orchestrator
├── e2e-tests-cypress.yml                  # Shared wrapper: routes to v1 or v2 template
├── e2e-tests-playwright.yml               # Shared wrapper: routes to v1 or v2 template
├── e2e-tests-cypress-template-v2.yml      # Active: cypress + test-system-io dispatch
├── e2e-tests-playwright-template-v2.yml   # Active: playwright + test-system-io dispatch
├── e2e-tests-cypress-template.yml         # Deprecated v1 (legacy in-job execution)
└── e2e-tests-playwright-template.yml      # Deprecated v1 (legacy in-job execution)
```

> **v1 templates are deprecated.** They remain available behind a feature flag during cutover but receive no further changes. New work targets the v2 templates exclusively. The wrappers route by `vars.E2E_USE_TEST_IO_DISPATCH` — `'true'` selects v2, anything else falls back to v1.

### Call hierarchy

```
e2e-tests-ci.yml ─────────────────┐
e2e-tests-on-merge.yml ───────────┤──► e2e-tests-cypress.yml ─────┐
e2e-tests-on-release.yml ─────────┘    e2e-tests-playwright.yml ──┤
                                                                  │
                                       ┌──────────────────────────┘
                                       │  routes on E2E_USE_TEST_IO_DISPATCH
                                       ▼
                  v2 (active) ──► e2e-tests-{cypress,playwright}-template-v2.yml
                  v1 (legacy) ──► e2e-tests-{cypress,playwright}-template.yml
```

---

## Workflow Architecture (v2)

v2 splits the template into five jobs — `prepare-run`, `prep-deps`, `dispatch-begin`, `workers` (matrix), and `report` — and pushes spec-level execution to [Test System IO](https://github.com/mattermost/mattermost-test-system-io) so workers stay thin and identical.

```
┌──────────────────────────────────────────────────────────────────────────┐
│  Template v2: e2e-tests-{cypress,playwright}-template-v2.yml              │
│                                                                            │
│   ┌───────────────────┐                ┌──────────────────────────────┐   │
│   │ prepare-run       │                │ prep-deps                    │   │
│   │ (1 runner)        │    parallel    │ (1 runner)                   │   │
│   │                   │ ◄────────────► │                              │   │
│   │ • build workers   │                │ Cypress:                     │   │
│   │   matrix [1..N]   │                │   • cypress/node_modules     │   │
│   │ • compute commit  │                │   • ~/.cache/Cypress (binary)│   │
│   │   status context  │                │                              │   │
│   │ • emit composite  │                │ Playwright:                  │   │
│   │   identity        │                │   • webapp/platform/{client, │   │
│   │                   │                │       types}/{lib,node_mod}  │   │
│   │                   │                │   • playwright/node_modules  │   │
│   │                   │                │   • playwright/lib/dist      │   │
│   │                   │                │   • ~/.cache/ms-playwright   │   │
│   │                   │                │     (chromium only)          │   │
│   │                   │                │                              │   │
│   │                   │                │   → saved to actions/cache   │   │
│   └─────────┬─────────┘                └───────────────┬──────────────┘   │
│             │                                          │                  │
│             │                                          ▼                  │
│             │                          ┌──────────────────────────────┐  │
│             │                          │ dispatch-begin               │  │
│             │                          │ • register run with          │  │
│             │                          │   Test System IO             │  │
│             │                          │ • runs immediately before    │  │
│             │                          │   workers to minimise the    │  │
│             │                          │   inactivity-timeout window  │  │
│             │                          └───────────────┬──────────────┘  │
│             │                                          │                  │
│             └────────────────────┬─────────────────────┘                  │
│                                  ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────┐    │
│   │ workers  (matrix, fail-fast: false)                             │    │
│   │   Cypress full: N=40       |   Playwright full: N=10            │    │
│   │                                                                 │    │
│   │   each worker, in parallel:                                     │    │
│   │     1. sparse-checkout actions + full checkout-repo             │    │
│   │     2. setup-node                                                │    │
│   │     3. restore caches  ◄─── actions/cache (from prep-deps)      │    │
│   │        (fail-on-cache-miss: true)                               │    │
│   │     4. cloud-init + start-server  (docker compose stack)        │    │
│   │     5. prepare-cypress | prepare-playwright (run setup project) │    │
│   │     6. dispatch-run  ──────────────────────────────────┐        │    │
│   │        (pulls specs from Test System IO, runs locally,  │       │    │
│   │         posts result, loops until queue is empty)       │       │    │
│   │     7. cloud-teardown                                   │       │    │
│   └────────────────────┬────────────────────────────────────┼───────┘    │
│                        │                                    │            │
│                        ▼                                    │            │
│   ┌─────────────────────────────────────────────────┐       │            │
│   │ report                                           │       │            │
│   │ • pull aggregated results from Test System IO    │  ◄────┘            │
│   │ • post commit status                             │                    │
│   │ • send webhook notification                      │                    │
│   └─────────────────────────────────────────────────┘                    │
└────────────────────────────────────────────────────────────────────────┬─┘
                                                                          │
                                              ┌───────────────────────────▼───┐
                                              │ Test System IO (external)     │
                                              │ • spec-level dispatch         │
                                              │ • result aggregation          │
                                              │ • retry orchestration         │
                                              └───────────────────────────────┘
```

### Key properties

- **Spec-level vs. job-level parallelism.** The matrix sizes the runner pool; Test System IO does the spec assignment. Slow specs don't block a worker — fast workers keep pulling the next spec from the queue.
- **Cache-only workers.** `prep-deps` installs once per workflow run and saves to `actions/cache`. Every worker restores with `fail-on-cache-miss: true` and runs zero `npm ci`. Eliminates the 40-way `EEXIST/ENOENT` race in npm's shared cacache writer.
- **dispatch-begin runs late.** It depends on `prep-deps` so the gap between Test System IO run registration and the first worker calling `dispatch-run` is just per-worker setup (~3–5 min). Registering earlier risks the run timing out before any worker checks in, bulk-failing every spec.
- **Playwright slim slice.** Playwright only consumes `@mattermost/client` and `@mattermost/types` from webapp, so prep-deps caches just those two packages' built `lib/` and `node_modules` (~10–30 MB) instead of the full `webapp/node_modules` tree (~1–2 GB).
- **Browser/binary caches.** Cypress caches `~/.cache/Cypress` (cypress binary lives outside node_modules); playwright caches `~/.cache/ms-playwright` (chromium only). Both keyed on the framework's lockfile so they invalidate on version bumps.
- **No retry plumbing in the template.** Test System IO handles per-spec retries; the workflow only sees aggregated results.

---

## Pipeline 1: PR (`e2e-tests-ci.yml`)

Runs E2E tests for every PR commit after the enterprise docker image is built. Fails if the commit is not associated with an open PR.

**Trigger chain:**
```
PR commit ─► Enterprise CI builds docker image
           ─► Argo Events detects "Enterprise CI/docker-image" status
           ─► dispatches e2e-tests-ci.yml
```

For PRs from forks, `body.branches` may be empty so the workflow falls back to `master` for workflow files (trusted code), while `commit_sha` still points to the fork's commit.

**Jobs:** 2 (cypress + playwright), each does smoke -> full

**Commit statuses (4 total):**

| Context | Description (pending) | Description (result) |
|---------|----------------------|---------------------|
| `e2e-test/cypress-smoke\|enterprise` | `tests running, image_tag:abc1234` | `100% passed (1313), 440 specs, image_tag:abc1234` |
| `e2e-test/cypress-full\|enterprise` | `tests running, image_tag:abc1234` | `100% passed (1313), 440 specs, image_tag:abc1234` |
| `e2e-test/playwright-smoke\|enterprise` | `tests running, image_tag:abc1234` | `100% passed (200), 50 specs, image_tag:abc1234` |
| `e2e-test/playwright-full\|enterprise` | `tests running, image_tag:abc1234` | `99.5% passed (199/200), 1 failed, 50 specs, image_tag:abc1234` |

**Manual trigger (CLI):**
```bash
gh workflow run e2e-tests-ci.yml \
  --repo mattermost/mattermost \
  --field pr_number="35171"
```

**Manual trigger (GitHub UI):**
1. Go to **Actions** > **E2E Tests (smoke-then-full)**
2. Click **Run workflow**
3. Fill in `pr_number` (e.g., `35171`)
4. Click **Run workflow**

### On-demand testing

For on-demand E2E testing, the existing triggers still work:
- **Comment triggers**: `/e2e-test`, `/e2e-test fips`, or with `MM_ENV` parameters
- **Label trigger**: `E2E/Run`

These are separate from the automated workflow and can be used for custom test configurations or re-runs.

---

## Pipeline 2: Merge (`e2e-tests-on-merge.yml`)


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/.github/holopin.yml =====

organization: mattermost # org name on holopin
defaultSticker: clul38u2n156490gl8ti3srnek # sticker ID for "Mattermost QA Community Contributors", can be changed in the future
stickers:
  - id: clul38u2n156490gl8ti3srnek # sticker id
    alias: Mattermost QA Community Contributors # shorthand-string
  - id: cm16x3e4g07500cl9y5kspako
    alias: Mattermost Hacktoberfest 2024 Contributor

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/.github/scripts/check_config_changes_ci.py =====

#!/usr/bin/env python3
"""
.github/scripts/check_config_changes_ci.py
 
CI script that detects notable changes across several Mattermost source files
and appends structured release-note entries to the PR description.
 
Checkers
────────
1. config.go          — exported struct field additions/removals
2. api4/              — API endpoint additions/removals (Handle() calls)
3. audit_events.go    — AuditEvent* constant additions/removals
4. Dockerfile.buildenv — Go (base-image) version changes
 
All inputs come from environment variables set by the GitHub Actions workflow:
  GITHUB_TOKEN  — built-in Actions token  (pull-requests: write scope)
  PR_NUMBER     — pull request number
  BASE_SHA      — base commit SHA
  HEAD_SHA      — head commit SHA
  REPO          — owner/repo  (e.g. mattermost/mattermost)
"""
 
import os
import re
import sys
import subprocess
import requests
from dataclasses import dataclass, field
from typing import Optional
 
# ── Environment ────────────────────────────────────────────────────────────────
 
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
PR_NUMBER    = int(os.environ["PR_NUMBER"])
BASE_SHA     = os.environ["BASE_SHA"]
HEAD_SHA     = os.environ["HEAD_SHA"]
REPO         = os.environ.get("REPO", "mattermost/mattermost")
 
BASE_URL = "https://api.github.com"
HEADERS  = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept":        "application/vnd.github.v3+json",
}
 
# Timeout for all GitHub API requests: (connect seconds, read seconds).
# Prevents the workflow from hanging indefinitely on a slow/unresponsive API.
_TIMEOUT = (5, 30)
 
# Paths watched by this script (must align with `paths:` in the workflow YAML)
WATCHED_PATHS = [
    "server/public/model/config.go",
    "server/channels/api4/",
    "server/public/model/audit_events.go",
    "server/build/Dockerfile.buildenv",
]
 
 
# ── Data types ─────────────────────────────────────────────────────────────────
 
@dataclass
class CheckResult:
    """Holds the findings from one checker."""
    label:     str                    # Section heading, e.g. "`config.json` Changes"
    additions: list  = field(default_factory=list)
    removals:  list  = field(default_factory=list)
    changes:   list  = field(default_factory=list)  # for free-form entries (version bumps)
 
    def has_findings(self) -> bool:
        return bool(self.additions or self.removals or self.changes)
 
    def to_markdown(self) -> str:
        lines = [f"### {self.label}"]
        if self.additions:
            lines.append("**Added:** "   + ", ".join(self.additions))
        if self.removals:
            lines.append("**Removed:** " + ", ".join(self.removals))
        for change in self.changes:
            lines.append(change)
        return "\n".join(lines)
 
 
# ── Diff helpers ───────────────────────────────────────────────────────────────
 
def get_full_patch() -> str:
    """Return unified diff for all watched paths between base and head."""
    result = subprocess.run(
        ["git", "diff", f"{BASE_SHA}...{HEAD_SHA}", "--"] + WATCHED_PATHS,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout
 
 
def split_patch_by_file(full_patch: str) -> dict[str, str]:
    """
    Split a multi-file unified diff into {filename: patch} mapping.
    Filenames are the b-side (new) path, stripped of the 'b/' prefix.
    """
    patches: dict[str, str] = {}
    current_file: Optional[str] = None
    current_lines: list[str] = []
 
    for line in full_patch.splitlines(keepends=True):
        if line.startswith("diff --git "):
            if current_file:
                patches[current_file] = "".join(current_lines)
            current_lines = [line]
            # Extract filename from "diff --git a/foo b/foo"
            m = re.search(r" b/(.+)$", line.rstrip())
            current_file = m.group(1) if m else None
        else:
            current_lines.append(line)
 
    if current_file:
        patches[current_file] = "".join(current_lines)
 
    return patches
 
 
def file_at(ref: str, path: str) -> str:
    """Return the full contents of `path` at git ref `ref`, or '' if absent."""
    try:
        return subprocess.run(
            ["git", "show", f"{ref}:{path}"],
            capture_output=True, text=True, check=True,
        ).stdout
    except subprocess.CalledProcessError:
        return ""


def _compute_merge_base() -> str:
    """Resolve the merge-base of BASE_SHA and HEAD_SHA.

    Per-checker comparisons must use this rather than BASE_SHA. BASE_SHA is the
    tip of the target branch at PR-event time; if that branch advances on a
    watched file after the PR diverges, comparing branch-tip vs target-tip
    would attribute those upstream edits to this PR (false add/remove).
    `git diff A...B` already does this implicitly; the per-file snapshots must
    match.
    """
    return subprocess.run(
        ["git", "merge-base", BASE_SHA, HEAD_SHA],
        capture_output=True, text=True, check=True,
    ).stdout.strip()


MERGE_BASE = _compute_merge_base()
 
 
# ── Checker 1 — config.go ──────────────────────────────────────────────────────
 
_CONFIG_PATH     = "server/public/model/config.go"
_STRUCT_DECL_RE  = re.compile(r"^type\s+(\w+)\s+struct\s*\{")
_FIELD_LINE_RE   = re.compile(r"^\t([A-Z][A-Za-z0-9_]*)\s+\S")
 
 
def _scan_struct_fields(src: str) -> set[tuple[str, str]]:
    """
    Walk Go source and return {(StructName, FieldName)} for every exported
    field in every struct.
 
    Uses a brace-depth stack so nested anonymous structs, interface bodies,
    and function literals don't corrupt the enclosing struct context.
    Named type declarations cannot be nested in Go, so the struct_stack
    never grows beyond one entry for named structs.
    """
    fields: set[tuple[str, str]] = set()
    # Each entry: (struct_name, brace_depth_when_opened)
    struct_stack: list[tuple[str, int]] = []
    depth = 0
 
    for line in src.splitlines():
        sm = _STRUCT_DECL_RE.match(line)
        if sm:
            # Record depth *before* counting this line's braces
            struct_stack.append((sm.group(1), depth))
 
        depth += line.count("{") - line.count("}")
 

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/.github/scripts/migration_automation.py =====

#!/usr/bin/env python3
"""
migration_automation.py
 
Triggered by GitHub Actions when a new .up.sql file lands on master.
 
Each Mattermost migration ships as a pair of files: NNNNNN_slug.up.sql
(applied on upgrade) and NNNNNN_slug.down.sql (applied on rollback).  The
workflow filters on .up.sql files only because:
  - The .up.sql is the canonical identifier for a new migration.
  - Both files are committed together, so detecting the up file is enough
    to locate the pair.
  - We never want to trigger a separate review run for a down migration
    that arrives without a matching up migration.
 
For each new .up.sql file detected:
  1. Reads the .up.sql and its paired .down.sql (if present) from the repo
  2. Fetches the review-migration skill from the AI marketplace
  3. Calls Claude to produce the schema review report
  4. Calls Claude to produce the RST release note draft + changelog summary
  5. Appends the combined output to $GITHUB_STEP_SUMMARY so it renders
     inline in the Actions run UI — no branch, PR, or extra secrets needed
 
Required environment variables:
  ANTHROPIC_API_KEY    — repo secret
  GITHUB_STEP_SUMMARY  — file path provided automatically by GitHub Actions
"""
 
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
 
import anthropic
 
 
# ── Config ────────────────────────────────────────────────────────────────────
 
MODEL = "claude-sonnet-4-6"
 
# The marketplace URL intentionally points to /main so the script always uses
# the latest version of Ben Cooke's review-migration skill.  Any push to
# mattermost-ai-marketplace/main WILL change the skill used by this workflow —
# that is by design.  To pin to a specific revision instead, replace "main"
# with a commit SHA (e.g. "/abc1234/plugins/...").
MARKETPLACE_BASE = (
    "https://raw.githubusercontent.com/mattermost/mattermost-ai-marketplace"
    "/main/plugins/review-migration/skills/review-migration"
)
MM_GUIDE_URL = (
    "https://developers.mattermost.com/contribute/more-info/server/schema-migration-guide/"
)
 
# Retry configuration
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 2  # seconds; waits 2, 4, 8 between attempts
 
# Allowlist pattern for migration file paths accepted by this script.
# Format: server/channels/db/migrations/postgres/NNNNNN_slug.up.sql
MIGRATION_PATH_RE = re.compile(
    r"^server/channels/db/migrations/postgres/\d{6}_[\w-]+\.up\.sql$"
)
 
RELEASE_NOTES_SKILL = """
You are helping a Mattermost release manager write database migration release notes.
 
When given a migration review report, produce two things:
 
## 1. Release Note Block
 
Three parts in this exact order:
 
### Part A — Description
A clear, concise paragraph (2–5 sentences) describing what changed and why.
Write for database admins and self-hosters who need to understand the change at a glance.
Cover what tables/columns/indexes changed, the purpose, and any performance impact.
Do NOT include upgrade instructions here.
 
Inline code formatting: use DOUBLE backticks for all table names, column names, and
identifiers in prose (RST/Sphinx style). E.g. ``roles``, ``schemeid``, ``permission_level``.
Never use single backticks in description prose.
 
### Part B — Fixed compatibility statement (copy verbatim every time):
The migrations are fully backwards-compatible and no database downtime is expected for this upgrade. The SQL queries included are:
 
### Part C — SQL in RST format (NOT markdown fences):
.. code-block:: sql
 
    <SQL here, indented 4 spaces>
 
For multiple SQL dialects use a separate labeled ``.. code-block:: sql`` block for each.
 
## 2. One-Line Changelog Summary
 
**Changelog summary:** `<one sentence under ~30 words, ending with an impact note>`
"""
 
 
# ── Startup validation ────────────────────────────────────────────────────────
 
def validate_env() -> str:
    """
    Validate required env vars and return the GITHUB_STEP_SUMMARY path.
    Exits with a clear error message if any required var is missing.
 
    ANTHROPIC_API_KEY is validated here so we fail fast with a readable
    message rather than an opaque SDK error, but it is not returned —
    the Anthropic SDK reads it directly from the environment.
    """
    required = {
        "ANTHROPIC_API_KEY": "Anthropic API key (repo secret)",
        "GITHUB_STEP_SUMMARY": "Job summary file path (provided automatically by Actions)",
    }
    missing = [
        f"  {var}  ({desc})"
        for var, desc in required.items()
        if not os.environ.get(var, "").strip()
    ]
    if missing:
        print("ERROR: The following required environment variables are not set:\n")
        for m in missing:
            print(m)
        sys.exit(1)
 
    return os.environ["GITHUB_STEP_SUMMARY"]
 
 
# ── Input validation ──────────────────────────────────────────────────────────
 
def validate_migration_paths(paths: list[str]) -> None:
    """
    Server-side validation: reject any path that does not match the canonical
    migration file pattern.  Defense-in-depth against path traversal or
    unexpected input if the workflow filter is ever bypassed.
    """
    invalid = [p for p in paths if not MIGRATION_PATH_RE.match(p)]
    if invalid:
        print(
            "ERROR: The following paths do not match the expected migration pattern "
            f"({MIGRATION_PATH_RE.pattern}):"
        )
        for p in invalid:
            print(f"  {p!r}")
        print("Aborting — only files under the canonical migrations directory are accepted.")
        sys.exit(1)
 
 
# ── Retry helper ──────────────────────────────────────────────────────────────
 
def _is_retryable_http_error(code: int) -> bool:
    return code in (429, 500, 502, 503, 504)
 
 
def with_retry(fn, *, label: str, retries: int = MAX_RETRIES):
    """Call fn() up to `retries` times with exponential backoff."""
    last_exc = None
    for attempt in range(1, retries + 1):
        try:
            return fn()
        except urllib.error.HTTPError as e:
            last_exc = e
            if not _is_retryable_http_error(e.code):
                raise
            wait = RETRY_BACKOFF_BASE ** attempt
            print(f"  [{label}] HTTP {e.code} on attempt {attempt}/{retries}. "
                  f"Retrying in {wait}s…")
            time.sleep(wait)
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            last_exc = e
            wait = RETRY_BACKOFF_BASE ** attempt
            print(f"  [{label}] Network error on attempt {attempt}/{retries}: {e}. "
                  f"Retrying in {wait}s…")
            time.sleep(wait)
        except anthropic.RateLimitError as e:
            last_exc = e
            wait = RETRY_BACKOFF_BASE ** attempt
            print(f"  [{label}] Anthropic rate limit on attempt {attempt}/{retries}. "

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/.github/workflows/api.yml =====

name: API

on:
  push:
    branches:
      - master
  pull_request:

permissions:
  contents: read

jobs:
  build:
    runs-on: ubuntu-24.04
    defaults:
      run:
        working-directory: ./api

    steps:
      - name: Checkout code
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2
        with:
          persist-credentials: false

      - uses: actions/setup-node@53b83947a5a98c8d113130e565377fae1a50d02f # v6.3.0
        with:
          node-version-file: .nvmrc
          cache: "npm"
          cache-dependency-path: api/package-lock.json

      - name: Run build
        run: make build

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/.github/workflows/build-server-image.yml =====

name: BuildEnv Docker Image

on:
  push:
    branches:
      - master
      - release-*
    paths:
      - server/build/Dockerfile.buildenv
      - server/build/Dockerfile.buildenv-fips
      - .github/workflows/build-server-image.yml
  pull_request:
    paths:
      - server/build/Dockerfile.buildenv
      - server/build/Dockerfile.buildenv-fips
      - .github/workflows/build-server-image.yml
  workflow_dispatch:

env:
  CHAINCTL_IDENTITY: ee399b4c72dd4e58e3d617f78fc47b74733c9557/922f2d48307d6f5f

permissions: {}

jobs:
  build-image:
    permissions:
      contents: read
    runs-on: ubuntu-22.04
    steps:
      - name: buildenv/checkout-repo
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2
        with:
          persist-credentials: false

      - name: buildenv/docker-login
        uses: docker/login-action@b45d80f862d83dbcd57f89517bcf500b2ab88fb2 # v4.0.0
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: buildenv/build
        uses: docker/build-push-action@d08e5c354a6adb9ed34480a06d141179aa583294 # v7.0.0
        with:
          provenance: false
          file: server/build/Dockerfile.buildenv
          load: true
          push: false
          pull: false
          tags: mattermost/mattermost-build-server:test

      - name: buildenv/test
        run: |
          docker run --rm mattermost/mattermost-build-server:test /bin/sh -c "go version && node --version"

      - name: buildenv/calculate-golang-version
        id: go
        run: |
          GO_VERSION=$(docker run --rm mattermost/mattermost-build-server:test go version | awk '{print $3}' | sed 's/go//')
          echo "GO_VERSION=${GO_VERSION}" >> "${GITHUB_OUTPUT}"

      - name: buildenv/push
        if: github.ref == 'refs/heads/master' || startsWith(github.ref, 'refs/heads/release-')
        uses: docker/build-push-action@d08e5c354a6adb9ed34480a06d141179aa583294 # v7.0.0
        with:
          provenance: false
          file: server/build/Dockerfile.buildenv
          load: false
          push: true
          pull: true
          tags: mattermost/mattermost-build-server:${{ steps.go.outputs.GO_VERSION }}

  build-image-fips:
    permissions:
      contents: read
      id-token: write
    runs-on: ubuntu-22.04
    steps:
      - uses: chainguard-dev/setup-chainctl@c125f765e82b09a42af3185f3214465314d75c5d # v0.5.0
        with:
          identity: ${{ env.CHAINCTL_IDENTITY }}
      - name: buildenv/checkout-repo
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2
        with:
          persist-credentials: false

      - name: buildenv/docker-login
        uses: docker/login-action@b45d80f862d83dbcd57f89517bcf500b2ab88fb2 # v4.0.0
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: buildenv/build
        uses: docker/build-push-action@d08e5c354a6adb9ed34480a06d141179aa583294 # v7.0.0
        with:
          provenance: false
          file: server/build/Dockerfile.buildenv-fips
          load: true
          push: false
          pull: false
          tags: mattermost/mattermost-build-server-fips:test

      - name: buildenv/test
        run: |
          docker run --rm --entrypoint bash mattermost/mattermost-build-server-fips:test -c "go version && node --version"

      - name: buildenv/calculate-golang-version
        id: go
        run: |
          GO_VERSION=$(docker run --rm --entrypoint bash mattermost/mattermost-build-server-fips:test -c "go version" | awk '{print $3}' | sed 's/go//')
          echo "GO_VERSION=${GO_VERSION}" >> "${GITHUB_OUTPUT}"

      - name: buildenv/push
        if: github.ref == 'refs/heads/master' || startsWith(github.ref, 'refs/heads/release-')
        uses: docker/build-push-action@d08e5c354a6adb9ed34480a06d141179aa583294 # v7.0.0
        with:
          provenance: false
          file: server/build/Dockerfile.buildenv-fips
          load: false
          push: true
          pull: true
          tags: mattermost/mattermost-build-server-fips:${{ steps.go.outputs.GO_VERSION }}

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/.github/workflows/claude.yml =====

name: Claude Code

on:
  issue_comment:
    types: [created]
  pull_request_review_comment:
    types: [created]
  issues:
    types: [opened, assigned]
  pull_request_review:
    types: [submitted]

permissions: {}

jobs:
  claude:
    if: |
      (github.event_name == 'issue_comment' && contains(github.event.comment.body, '@claude')) ||
      (github.event_name == 'pull_request_review_comment' && contains(github.event.comment.body, '@claude')) ||
      (github.event_name == 'pull_request_review' && contains(github.event.review.body, '@claude')) ||
      (github.event_name == 'issues' && (contains(github.event.issue.body, '@claude') || contains(github.event.issue.title, '@claude')))
    runs-on: ubuntu-24.04
    permissions:
      contents: read
      pull-requests: read
      issues: read
      id-token: write
    steps:
      # Keep persist-credentials default while anthropics/claude-code-action#1236 is open
      - name: Checkout repository
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2
        with:
          fetch-depth: 1

      - name: Run Claude Code
        id: claude
        uses: anthropics/claude-code-action@26ec041249acb0a944c0a47b6c0c13f05dbc5b44 # v1.0.70
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          model: claude-sonnet-4-20250514
          allowed_tools: "Bash(cd:*),Bash(git:*),Bash(make:*),Bash(npm:*),Bash(go:*)"

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/.github/workflows/codeql-analysis.yml =====

name: "CodeQL"

on:
  pull_request:
    # The branches below must be a subset of the branches above
    branches: [master]
  schedule:
    - cron: "30 5,17 * * *"

permissions: {}

jobs:
  analyze:
    permissions:
      contents: read
      security-events: write # for github/codeql-action/autobuild to send a status report
    name: Analyze
    if: github.repository_owner == 'mattermost'
    runs-on: ubuntu-24.04

    strategy:
      fail-fast: false
      matrix:
        language: ["go", "javascript"]

    steps:
      - name: Checkout repository
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2
        with:
          persist-credentials: false

      # Initializes the CodeQL tools for scanning.
      - name: Initialize CodeQL
        uses: github/codeql-action/init@0d579ffd059c29b07949a3cce3983f0780820c98 # v4.32.6
        with:
          languages: ${{ matrix.language }}
          debug: false
          config-file: ./.github/codeql/codeql-config.yml

      - name: Build JavaScript
        uses: github/codeql-action/autobuild@0d579ffd059c29b07949a3cce3983f0780820c98 # v4.32.6
        if: ${{ matrix.language  == 'javascript' }}

      - name: Setup go
        uses: actions/setup-go@4b73464bb391d4059bd26b0524d20df3927bd417 # v6.3.0
        with:
          go-version-file: server/go.mod
        if: ${{ matrix.language == 'go' }}

      - name: Build Golang
        run: |
          cd server
          make setup-go-work
          make build-linux-amd64
        if: ${{ matrix.language == 'go' }}

      # Perform Analysis
      - name: Perform CodeQL Analysis
        uses: github/codeql-action/analyze@0d579ffd059c29b07949a3cce3983f0780820c98 # v4.32.6

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/.github/workflows/config-change-checker.yml =====

# .github/workflows/config-change-checker.yml
#
# Automatically detects notable additions/removals across four source files
# and appends structured release-note entries to the PR description under
# the "## Release Notes" section.
#
# Tracked files / directories:
#   • server/public/model/config.go       — config struct field changes
#   • server/channels/api4/               — API endpoint additions/removals
#   • server/public/model/audit_events.go — audit log event constant changes
#   • server/build/Dockerfile.buildenv    — Go runtime version changes
#
# No secrets needed — uses the built-in GITHUB_TOKEN.
 
name: Config Change Checker
 
on:
  pull_request:
    types: [opened, synchronize, reopened]
    paths:
      - 'server/public/model/config.go'
      - 'server/channels/api4/**'
      - 'server/public/model/audit_events.go'
      - 'server/build/Dockerfile.buildenv'
 
# Cancel any in-progress run for the same PR when a new commit is pushed.
concurrency:
  group: ${{ github.workflow }}-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: true

permissions: {}

jobs:
  check-release-notes:
    name: Detect release-note-worthy changes
    runs-on: ubuntu-latest
    # Skip bot-authored PRs (Dependabot, mattermost-bot, etc.) — they will
    # not touch these paths intentionally and cannot receive description updates
    # via GITHUB_TOKEN anyway (fork-like restrictions apply to most bots).
    if: github.event.pull_request.user.type != 'Bot'
 
    permissions:
      pull-requests: write   # needed to update the PR description
      contents: read
 
    steps:
      - name: Checkout code
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd  # v6.0.2
        with:
          persist-credentials: false
          # Fetch enough history to diff against the base branch
          fetch-depth: 0
 
      - name: Set up Python
        uses: actions/setup-python@a309ff8b426b58ec0e2a45f0f869d46889d02405  # v6.2.0
        with:
          python-version: '3.11'
 
      - name: Install dependencies
        run: pip install requests==2.32.3 --quiet
 
      - name: Detect changes and update PR description
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          PR_NUMBER: ${{ github.event.pull_request.number }}
          BASE_SHA: ${{ github.event.pull_request.base.sha }}
          HEAD_SHA: ${{ github.event.pull_request.head.sha }}
          REPO: ${{ github.repository }}
        run: python3 .github/scripts/check_config_changes_ci.py

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/.github/workflows/docker-push-mirrored.yml =====

---
name: Push mirrored docker images
on:
  push:
    branches:
      - master
    paths:
      - server/scripts/mirror-docker-images.*

permissions:
  contents: read

jobs:
  build-docker:
    name: cd/Push mirrored docker images
    if: github.repository_owner == 'mattermost'
    runs-on: ubuntu-24.04
    steps:
      - name: Checkout mattermost project
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2
        with:
          persist-credentials: false
      - name: cd/Login to Docker Hub
        uses: docker/login-action@b45d80f862d83dbcd57f89517bcf500b2ab88fb2 # v4.0.0
        with:
          username: ${{ secrets.DOCKERHUB_DEV_USERNAME }}
          password: ${{ secrets.DOCKERHUB_DEV_TOKEN }}
      - name: cd/Run image upload script
        env:
          IMAGES_FILE: server/scripts/mirror-docker-images.json
          DRY_RUN: no
        run: ./server/scripts/mirror-docker-images.sh

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/.github/workflows/docs-impact-review.yml =====

name: Documentation Impact Review
 
on:
  pull_request:
    types: [opened, synchronize, reopened, ready_for_review]
    branches:
      - master
 
concurrency:
  group: ${{ format('docs-impact-{0}', github.event.pull_request.number) }}
  cancel-in-progress: true
 
permissions: {}

jobs:
  docs-impact-review:
    permissions:
      contents: read
      pull-requests: write
      issues: write
      id-token: write
    if: github.event.pull_request.draft == false && !startsWith(github.event.pull_request.user.login, 'unified-ci-app')
    runs-on: ubuntu-24.04
    env:
      HAS_ANTHROPIC_KEY: ${{ secrets.ANTHROPIC_API_KEY != '' }}
    steps:
      - name: Checkout PR code
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2
        with:
          persist-credentials: false
 
      - name: Checkout documentation repo
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2
        with:
          repository: mattermost/docs
          ref: master
          path: docs
          persist-credentials: false
          sparse-checkout: |
            source/administration-guide
            source/deployment-guide
            source/end-user-guide
            source/integrations-guide
            source/security-guide
            source/agents
            source/get-help
            source/product-overview
            source/use-case-guide
            source/conf.py
            source/index.rst
          sparse-checkout-cone-mode: false
 
      - name: Analyze documentation impact
        id: docs-analysis
        if: ${{ env.HAS_ANTHROPIC_KEY == 'true' }}
        uses: anthropics/claude-code-action@26ec041249acb0a944c0a47b6c0c13f05dbc5b44 # v1.0.70
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          allowed_bots: "cursor,claude"
          prompt: |
            REPO: ${{ github.repository }}
            PR NUMBER: ${{ github.event.pull_request.number }}
 
            ## Task
 
            You are a documentation impact analyst for the Mattermost project. Your job is to determine whether a pull request requires updates to the public documentation hosted at https://docs.mattermost.com (source repo: mattermost/docs).
 
            ## Repository Layout
 
            The PR code is checked out at the workspace root. The documentation source is checked out at `./docs/source/` (RST files, Sphinx-based).
 
            <monorepo_paths>
            ### Code Paths and Documentation Relevance
 
            - `server/channels/api4/` — REST API handlers → API docs
            - `server/public/model/config.go` — Configuration settings struct → admin guide updates
            - `server/public/model/feature_flags.go` — Feature flags → these control gradual rollouts and are **distinct from configuration settings**
            - `server/public/model/websocket_message.go` — WebSocket events → API/integration docs
            - `server/public/model/audit_events.go` — Audit event definitions → new or changed audit event types should be documented for compliance officers
            - `server/public/model/support_packet.go` — Support packet contents → admin guide; changes to what data is collected or exported affect troubleshooting and support workflows
            - `server/channels/db/migrations/` — Database schema changes → admin upgrade guide
            - `server/channels/app/` — Business logic → end-user or admin docs if behavior changes
            - `server/cmd/` — CLI commands (mmctl) → admin CLI docs
            - `api/v4/source/` — OpenAPI YAML specs (auto-published to api.mattermost.com) → review for completeness
            - `webapp/channels/src/components/` — UI components → end-user guide if user-facing
            - `webapp/channels/src/i18n/` — Internationalization strings → new user-facing strings suggest new features
            - `webapp/platform/` — Platform-level webapp code
            - `server/Makefile` - changes to plugin version pins starting at line ~155 may indicate plugin releases that require documentation updates in the integrations or deployment guide
            </monorepo_paths>
 
            <docs_directories>
            ### Documentation Directories (`./docs/source/`)
 
            - `administration-guide/` — Server config, admin console, upgrade notes, CLI, server management, support packet, audit events
            - `deployment-guide/` — Installation, deployment, scaling, high availability
            - `end-user-guide/` — User-facing features, messaging, channels, search, notifications
            - `integrations-guide/` — Webhooks, slash commands, plugins, bots, API usage
            - `security-guide/` — Authentication, permissions, security configs, compliance
            - `agents/` — AI agent integrations
            - `get-help/` — Troubleshooting guides
            - `product-overview/` — Product overview and feature descriptions
            - `use-case-guide/` — Use case specific guides
            </docs_directories>
 
            ## Documentation Personas
 
            Each code change can impact multiple audiences. Identify all affected personas and prioritize by breadth of impact.
 
            <personas>
            ### System Administrator
            Deploys, configures, and maintains Mattermost servers.
            - **Reads:** `administration-guide/`, `deployment-guide/`, `security-guide/`
            - **Cares about:** config settings, CLI commands (mmctl), database migrations, upgrade procedures, scaling, HA, environment variables, performance tuning
            - **Impact signals:** changes to `model/config.go`, `db/migrations/`, `server/cmd/`, `einterfaces/`, `model/audit_events.go`, `model/support_packet.go`
 
            ### End User
            Uses Mattermost daily for messaging, collaboration, and workflows.
            - **Reads:** `end-user-guide/`, `get-help/`
            - **Cares about:** UI changes, new messaging features, search behavior, notification settings, keyboard shortcuts, channel management, file sharing
            - **Impact signals:** changes to `webapp/channels/src/components/`, `i18n/` (new user-facing strings), `app/` changes that alter user-visible behavior
 
            ### Developer / Integrator
            Builds integrations, plugins, bots, and custom tools on top of Mattermost.
            - **Reads:** `integrations-guide/`, API reference (`api/v4/source/`)
            - **Cares about:** REST API endpoints, request/response schemas, webhook payloads, WebSocket events, plugin APIs, bot account behavior, OAuth/authentication flows
            - **Impact signals:** changes to `api4/` handlers, `api/v4/source/` specs, `model/websocket_message.go`, plugin interfaces
 
            ### Security / Compliance Officer
            Evaluates and enforces security and regulatory requirements.
            - **Reads:** `security-guide/`, relevant sections of `administration-guide/`
            - **Cares about:** authentication methods (SAML, LDAP, OAuth, MFA), permission model changes, data retention policies, audit logging, encryption settings, compliance exports
            - **Impact signals:** changes to security-related config, authentication handlers, audit/compliance code
            </personas>
 
            ## Analysis Steps
 
            Follow these steps in order. Complete each step before moving to the next.
 
            1. **Read the PR diff** using `gh pr diff ${{ github.event.pull_request.number }}` to understand what changed.
 
            2. **Categorize each changed file** by documentation relevance using one or more of these labels:
              - API changes (new endpoints, changed parameters, changed responses)
              - Configuration changes (new or modified settings in `config.go`)
              - Feature flag changes (new or modified flags in `feature_flags.go` — treat separately from configuration settings; feature flags are not the same as config settings)
              - Audit event changes (new or modified audit event types in `audit_events.go`)
              - Support packet changes (new or modified fields in `support_packet.go`)
              - Plugin version changes (version bumps in `server/Makefile` starting around line 155)
              - Database schema changes (new migrations)
              - WebSocket event changes
              - CLI command changes
              - User-facing behavioral changes
              - UI changes
 
            3. **Identify affected personas** for each documentation-relevant change using the impact signals defined above.
 
            4. **Search `./docs/source/`** for existing documentation covering each affected feature/area. Search for related RST files by name patterns and content. For every RST file you identify as potentially relevant, **read its actual content** and confirm it explicitly describes the specific behavior, setting, endpoint, or workflow being changed. Do not flag a page solely because its filename or section heading is related — only flag it if the file contains prose that would become inaccurate or incomplete due to this PR.
 
            5. **Evaluate documentation impact** for each change by applying these two criteria:
              - **Documented behavior changed:** The PR modifies behavior that is currently described in the documentation. The existing docs would become inaccurate or misleading if not updated. Flag these as **"Documentation Updates Required"**.
              - **Documentation gap identified:** The PR introduces new functionality, settings, endpoints, or behavioral changes that are not covered anywhere in the current documentation, and that are highly relevant to one or more identified personas. Flag these as **"Documentation Updates Recommended"** and note that new documentation is needed.
              - **API spec changes already in PR:** Changes to `api/v4/source/` YAML files are part of the PR itself and are automatically published to api.mattermost.com. These do **not** require a separate docs repo action. Do not create action items for them. You may note them in the table as "Handled in PR — auto-published to api.mattermost.com" but they must not appear as recommended actions.
 
            6. **Determine the documentation action** for each flagged change: does an existing page need updating (cite the exact RST file), or is an entirely new page needed (suggest the appropriate directory and a proposed filename)?
 
            Only flag changes that meet at least one of the two criteria above. Internal refactors, test changes, and implementation details that do not alter documented behavior or create a persona-relevant gap should not be flagged.
 
            **Important distinctions to apply during analysis:**
 
            - **The guiding principle for skipping documentation:** docs are **not** needed when the PR does not introduce or change a user/admin capability, documented setting, workflow, UI string, troubleshooting signal, or supported behavior claim. When in doubt, ask: "Would a system administrator, end user, developer, or compliance officer need to read or update any documentation to understand or work with this change?" If no, classify as "No Documentation Changes Needed."
 
            - **Common no-docs-needed patterns** (classify these as "No Documentation Changes Needed" and keep the response brief):
              - Prepackaged plugin version bumps where no user/admin workflow, configuration option, or observable capability changes — regardless of whether the version bump is major, minor, or patch
              - Internal performance improvements or implementation-only refactors with no externally observable behavioral change
              - Developer-facing renames, internal API restructuring, or code organization changes that do not affect product documentation, supported workflows, or any capability visible to admins or end users
              - Changes where existing documentation already accurately covers the behavior generically and no update is needed to remain accurate
 
            - Plugin version bumps in `server/Makefile`: flag only when the plugin update introduces or changes a user/admin workflow, configuration, UI element, or observable capability. A bump that is purely a prepackaged update with no such change does not require documentation regardless of version magnitude.
 
            - Feature flags (`feature_flags.go`) are **not** configuration settings. Do not conflate them. Config settings belong in the admin configuration reference.
 

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/.github/workflows/e2e-fulltests-ci.yml =====

---
name: E2E Tests
on:
  # For PRs, this workflow gets triggered from the Argo Events platform.
  # Check the following repo for details: https://github.com/mattermost/delivery-platform
  workflow_dispatch:
    inputs:
      ref:
        type: string
        description: Git ref to test. Must be a full commit SHA for PR testing, and a tag for release testing. Ignored for daily tests.
        required: false
      PR_NUMBER:
        type: string
        description: PR number (if applicable)
        required: false
      ROLLING_RELEASE_FROM_TAG:
        type: string
        description: Mattermost release git tag for RollingRelease tests. Optional.
        required: false
      MM_ENV:
        type: string
        required: false
        description: A comma-separated list of environment variables to set for the server. Spaces are not supported.
      MM_SERVICE_OVERRIDES:
        type: string
        required: false
        description: A comma-separated list of service overrides. E.g. "-elasticsearch,+opensearch"
      REPORT_TYPE:
        type: choice
        description: The context this report is being generated in
        options:
          - PR
          - RELEASE
          - RELEASE_CLOUD
          - MASTER
          - MASTER_UNSTABLE
          - CLOUD
          - CLOUD_UNSTABLE
          - NONE
        default: NONE
      RUN_CYPRESS:
        type: string
        description: Enable Cypress run
        default: "true"
      RUN_PLAYWRIGHT:
        type: string
        description: Enable Playwright run
        default: "true"
      FIPS_ENABLED:
        type: string
        description: When true, use mattermost-enterprise-fips-edition image for testing instead of standard enterprise edition
        default: "false"
        required: false

concurrency:
  group: "${{ github.workflow }}-${{ inputs.REPORT_TYPE }}-${{ inputs.FIPS_ENABLED }}-${{ inputs.PR_NUMBER || inputs.ref }}-${{ inputs.MM_ENV }}"
  cancel-in-progress: true

permissions: {}

jobs:
  generate-test-variables:
    runs-on: ubuntu-24.04
    permissions:
      contents: read
      issues: write
      pull-requests: write
    defaults:
      run:
        shell: bash
    outputs:
      commit_sha: "${{ steps.generate.outputs.commit_sha }}"
      BRANCH: "${{ steps.generate.outputs.BRANCH }}"
      SERVER_IMAGE: "${{ steps.generate.outputs.SERVER_IMAGE }}"
      status_check_context: "${{ steps.generate.outputs.status_check_context }}"
      workers_number: "${{ steps.generate.outputs.workers_number }}"
      server_uppercase: "${{ steps.generate.outputs.server_uppercase }}" # Required for license selection
      SERVER: "${{ steps.generate.outputs.SERVER }}"
      ENABLED_DOCKER_SERVICES: "${{ steps.generate.outputs.ENABLED_DOCKER_SERVICES }}"
      TEST_FILTER_CYPRESS: "${{ steps.generate.outputs.TEST_FILTER_CYPRESS }}"
      TEST_FILTER_PLAYWRIGHT: "tests"
      BUILD_ID: "${{ steps.generate.outputs.BUILD_ID }}"
      TM4J_ENABLE: "${{ steps.generate.outputs.TM4J_ENABLE }}"
      REPORT_TYPE: "${{ steps.generate.outputs.REPORT_TYPE }}"
      TESTCASE_FAILURE_FATAL: "${{ steps.generate.outputs.TESTCASE_FAILURE_FATAL }}"
      ROLLING_RELEASE_commit_sha: "${{ steps.generate.outputs.ROLLING_RELEASE_commit_sha }}"
      ROLLING_RELEASE_SERVER_IMAGE: "${{ steps.generate.outputs.ROLLING_RELEASE_SERVER_IMAGE }}"
      WORKFLOW_RUN_URL: "${{steps.generate.outputs.WORKFLOW_RUN_URL}}"
      CYCLE_URL: "${{steps.generate.outputs.CYCLE_URL}}"
      FIPS_SUFFIX: "${{ steps.generate.outputs.FIPS_SUFFIX }}"
    env:
      GH_TOKEN: "${{ github.token }}"
      REF: "${{ inputs.ref || github.sha }}"
      PR_NUMBER: "${{ inputs.PR_NUMBER || '' }}"
      REPORT_TYPE: "${{ inputs.REPORT_TYPE }}"
      ROLLING_RELEASE_FROM_TAG: "${{ inputs.ROLLING_RELEASE_FROM_TAG }}"
      AUTOMATION_DASHBOARD_URL: "${{ secrets.MM_E2E_AUTOMATION_DASHBOARD_URL }}"
      FIPS_ENABLED: "${{ inputs.FIPS_ENABLED }}"
      # We could exclude the @smoke group for PRs, but then we wouldn't have it in the report
      TEST_FILTER_CYPRESS_PR: >-
        --stage="@prod"
        --excludeGroup="@te_only,@cloud_only,@high_availability"
        --sortFirst="@compliance_export,@elasticsearch,@ldap_group,@ldap"
        --sortLast="@saml,@keycloak,@plugin,@plugins_uninstall,@mfa,@license_removal"
      TEST_FILTER_CYPRESS_PROD_ONPREM: >-
        --stage="@prod"
        --excludeGroup="@te_only,@cloud_only,@high_availability"
        --sortFirst="@compliance_export,@elasticsearch,@ldap_group,@ldap,@playbooks"
        --sortLast="@saml,@keycloak,@plugin,@plugins_uninstall,@mfa,@license_removal"
      TEST_FILTER_CYPRESS_PROD_CLOUD: >-
        --stage="@prod"
        --excludeGroup="@not_cloud,@cloud_trial,@e20_only,@te_only,@high_availability,@license_removal"
        --sortFirst="@compliance_export,@elasticsearch,@ldap_group,@ldap,@playbooks"
        --sortLast="@saml,@keycloak,@plugin,@plugins_uninstall,@mfa"
      MM_ENV: "${{ inputs.MM_ENV || '' }}"
      MM_SERVICE_OVERRIDES: "${{ inputs.MM_SERVICE_OVERRIDES }}"
    steps:
      - name: ci/checkout-repo
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2
        with:
          persist-credentials: false
          ref: "${{ inputs.ref || github.sha }}"
          fetch-depth: 0
      - name: ci/generate-test-variables
        id: generate
        env:
          GITHUB_RUN_ID: ${{ github.run_id }}
          GITHUB_RUN_ATTEMPT: ${{ github.run_attempt }}
          GITHUB_SERVER_URL: ${{ github.server_url }}
          GITHUB_REPOSITORY: ${{ github.repository }}
        run: |
          MM_ENV_HASH=$(md5sum -z <<<"$MM_ENV" | cut -c-8)
          TESTCASE_FAILURE_FATAL="true"
          if grep -q CLOUD <<<"$REPORT_TYPE"; then
            SERVER=cloud
          else
            SERVER=onprem
          fi
          case "$REPORT_TYPE" in
            NONE | PR)
              ### Populate support variables
              _COMMIT_SHA_COMPUTED=$(git rev-parse --verify "$REF") # NB: not actually used for resolving the commit; it's only to double check the value of 'inputs.ref'
              ### For image tag generation: utilize 'inputs.ref', assume that it is a full commit SHA
              COMMIT_SHA="${REF}"
              BRANCH="server-pr-${PR_NUMBER}"   # For reference, the real branch name may be retrievable with command: 'jq -r .head.ref <pr.json'
              SERVER_IMAGE_TAG="${COMMIT_SHA::7}"
              SERVER_IMAGE_ORG=mattermostdevelopment
              BUILD_ID_SUFFIX="${REPORT_TYPE@L}-${SERVER}-ent"
              WORKERS_NUMBER=20
              TEST_FILTER_CYPRESS="$TEST_FILTER_CYPRESS_PR"
              COMPUTED_REPORT_TYPE="${REPORT_TYPE}"
              ### Run sanity assertions after variable generations
              [ "$REF" = "${_COMMIT_SHA_COMPUTED}" ]             # 'inputs.ref' must be a full commit hash, and the commit must exist
              [ "$REPORT_TYPE" != "PR" ] || [ "$PR_NUMBER" -gt "0" ] # If report type is PR, then PR_NUMBER must be set to a number
              ;;
            MASTER | MASTER_UNSTABLE | CLOUD | CLOUD_UNSTABLE)
              ### Populate support variables
              _IS_TEST_UNSTABLE=$(sed -n -E 's/^.*(UNSTABLE).*$/\1/p' <<< "$REPORT_TYPE") # The variable's value is 'UNSTABLE' if report type is for unstable tests, otherwise it's empty
              _TEST_FILTER_CYPRESS_VARIABLE="TEST_FILTER_CYPRESS_PROD_${SERVER@U}"
              ### For ref and image tag generation: ignore 'inputs.ref', and use master branch directly. Note that 'COMMIT_SHA' will be used for reporting the test result, and for checking out the testing scripts and test cases
              COMMIT_SHA="$(git rev-parse --verify origin/master)"
              BRANCH=master
              SERVER_IMAGE_TAG=master
              SERVER_IMAGE_ORG=mattermostdevelopment
              BUILD_ID_SUFFIX="${_IS_TEST_UNSTABLE:+unstable-}daily-${SERVER}-ent"
              BUILD_ID_SUFFIX_IN_STATUS_CHECK=true
              WORKERS_NUMBER=10   # Daily tests are not time critical, and it's more efficient to run on fewer workers
              TEST_FILTER_CYPRESS="${!_TEST_FILTER_CYPRESS_VARIABLE} ${_IS_TEST_UNSTABLE:+--invert}"
              TM4J_ENABLE=true
              COMPUTED_REPORT_TYPE="${REPORT_TYPE}"
              [ -z "$_IS_TEST_UNSTABLE" ] || TESTCASE_FAILURE_FATAL="" # Assert that tests are stable. If they are not, the status check will be always green
              ;;
            RELEASE | RELEASE_CLOUD)
              ### Populate support variables
              _TEST_FILTER_CYPRESS_VARIABLE="TEST_FILTER_CYPRESS_PROD_${SERVER@U}"
              ### For ref and image tag generation: assume the 'inputs.ref' is a tag, and use the first two digits to construct the branch name
              COMMIT_SHA="$(git rev-parse --verify HEAD)"
              BRANCH=$(sed -E "s/v([0-9]+)\.([0-9]+)\..+$/release-\1.\2/g" <<<$REF)
              SERVER_IMAGE_TAG="$(cut -c2- <<<$REF)"   # Remove the leading 'v' from the given tag name, to generate the docker image tag
              SERVER_IMAGE_ORG=mattermost

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/.github/workflows/e2e-tests-check.yml =====

---
name: E2E Tests Check
on:
  pull_request:
    paths:
      - "e2e-tests/**"
      - "webapp/platform/client/**"
      - "webapp/platform/eslint-plugin/**"
      - "webapp/platform/types/**"
      - ".github/workflows/e2e-*.yml"

permissions:
  actions: write
  contents: read
  pull-requests: read

jobs:
  check:
    runs-on: ubuntu-24.04
    steps:
      - name: ci/checkout-repo
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2
        with:
          persist-credentials: false
          fetch-depth: 0

      - name: ci/setup-node
        uses: actions/setup-node@53b83947a5a98c8d113130e565377fae1a50d02f # v6.3.0
        with:
          node-version-file: ".nvmrc"
          cache: npm
          cache-dependency-path: |
            e2e-tests/cypress/package-lock.json
            e2e-tests/playwright/package-lock.json
            webapp/package-lock.json
      - name: ci/npm-cache-verify
        # Heal any partial/dangling entries left in the restored ~/.npm cache
        # before running `npm ci`. Avoids the intermittent EEXIST/ENOENT
        # failures in npm's cacache writer.
        run: npm cache verify

      # Set up web app subpackages and eslint plugin
      - name: ci/get-webapp-node-modules
        working-directory: webapp
        run: make node_modules

      # Cypress check
      - name: ci/cypress/npm-install
        working-directory: e2e-tests/cypress
        run: npm ci
      - name: ci/cypress/npm-check
        working-directory: e2e-tests/cypress
        run: npm run check

      # Playwright check
      - name: ci/playwright/npm-install
        working-directory: e2e-tests/playwright
        run: npm ci
      - name: ci/playwright/npm-check
        working-directory: e2e-tests/playwright
        run: npm run check

      # Shell check
      - name: ci/shell-check
        working-directory: e2e-tests
        run: make check-shell

      # E2E-only check and trigger
      - name: ci/check-e2e-test-only
        id: check
        uses: ./.github/actions/check-e2e-test-only
        with:
          base_sha: ${{ github.event.pull_request.base.sha }}
          head_sha: ${{ github.event.pull_request.head.sha }}
          pr_number: ${{ github.event.pull_request.number }}

      - name: ci/trigger-e2e-with-branch-image
        if: >-
          steps.check.outputs.e2e_test_only == 'true' &&
          (github.event.pull_request.base.ref == 'master' || startsWith(github.event.pull_request.base.ref, 'release-'))
        env:
          GH_TOKEN: ${{ github.token }}
          PR_NUMBER: ${{ github.event.pull_request.number }}
          IMAGE_TAG: ${{ steps.check.outputs.image_tag }}
        run: |
          echo "Triggering E2E tests for PR #${PR_NUMBER} with mattermostdevelopment/mattermost-enterprise-edition:${IMAGE_TAG}"
          gh workflow run e2e-tests-ci.yml --field pr_number="${PR_NUMBER}"

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/.github/workflows/e2e-tests-ci-template.yml =====

---
name: E2E Tests Template
on:
  workflow_call:
    inputs:
      # NB: this does not support using branch names that belong to forks.
      #     In those cases, you should specify directly the commit SHA that you want to test, or
      #     some wrapper workflow that does it for you (e.g. the slash command for initiating a PR test)
      commit_sha:
        type: string
        required: true
      status_check_context:
        type: string
        required: true
      workers_number:
        type: string # Should ideally be a number; see https://github.com/orgs/community/discussions/67182
        required: false
        default: "1"
      testcase_failure_fatal:
        type: boolean
        required: false
        default: true
      enable_reporting:
        type: boolean
        required: false
        default: false
      SERVER:
        type: string # Valid values are: onprem, cloud
        required: false
        default: onprem
      SERVER_IMAGE:
        type: string
        required: false
      ENABLED_DOCKER_SERVICES:
        type: string
        required: false
      TEST: # Valid values are: cypress, playwright
        type: string
        required: false
        default: "cypress"
      TEST_FILTER:
        type: string
        required: false
      MM_ENV:
        type: string
        required: false
      BRANCH:
        type: string
        required: false
      BUILD_ID:
        type: string
        required: false
      REPORT_TYPE:
        type: string
        required: false
      ROLLING_RELEASE_commit_sha:
        type: string
        required: false
      ROLLING_RELEASE_SERVER_IMAGE:
        type: string
        required: false
      PR_NUMBER:
        type: string
        required: false
    secrets:
      MM_LICENSE:
        required: false
      AUTOMATION_DASHBOARD_URL:
        required: false
      AUTOMATION_DASHBOARD_TOKEN:
        required: false
      PUSH_NOTIFICATION_SERVER:
        required: false
      REPORT_WEBHOOK_URL:
        required: false
      REPORT_TM4J_API_KEY:
        required: false
      REPORT_TM4J_TEST_CYCLE_LINK_PREFIX:
        required: false
      CWS_URL:
        required: false
      CWS_EXTRA_HTTP_HEADERS:
        required: false
      AWS_ACCESS_KEY_ID:
        required: false
      AWS_SECRET_ACCESS_KEY:
        required: false
    outputs:
      passed:
        value: "${{ jobs.report.outputs.passed }}"
      failed:
        value: "${{ jobs.report.outputs.failed }}"
      failed_expected:
        value: "${{ jobs.report.outputs.failed_expected }}"
      pass_rate:
        value: "${{ jobs.report.outputs.pass_rate }}"
      playwright_report_url:
        value: ${{ jobs.report.outputs.playwright_report_url }}

permissions: {}

jobs:
  update-initial-status:
    permissions:
      statuses: write
    runs-on: ubuntu-24.04
    steps:
      - uses: mattermost/actions/delivery/update-commit-status@f324ac89b05cc3511cb06e60642ac2fb829f0a63
        env:
          GITHUB_TOKEN: ${{ github.token }}
        with:
          repository_full_name: ${{ github.repository }}
          commit_sha: ${{ inputs.commit_sha }}
          context: ${{ inputs.status_check_context }}
          description: E2E tests for mattermost server app
          status: pending

  generate-build-variables:
    permissions:
      contents: read
    runs-on: ubuntu-24.04
    needs:
      - update-initial-status
    defaults:
      run:
        shell: bash
    outputs:
      workers: "${{ steps.generate.outputs.workers }}"
      node-cache-dependency-path: "${{ steps.generate.outputs.node-cache-dependency-path }}"
    steps:
      - name: ci/checkout-repo
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2
        with:
          persist-credentials: false
          ref: ${{ inputs.commit_sha }}
          fetch-depth: 0
      - name: ci/generate-build-variables
        id: generate
        env:
          WORKERS: ${{ inputs.workers_number }}
          TEST: ${{ inputs.TEST }}
        run: |
          [ "$WORKERS" -gt "0" ] # Assert that the workers number is an integer greater than 0
          echo "workers="$(jq --slurp --compact-output '[range('"$WORKERS"')] | map(tostring)' /dev/null) >> $GITHUB_OUTPUT
          echo "node-cache-dependency-path=e2e-tests/${TEST}/package-lock.json" >> $GITHUB_OUTPUT

  generate-test-cycle:
    permissions:
      contents: read
    runs-on: ubuntu-24.04
    needs:
      - generate-build-variables
    defaults:
      run:
        shell: bash
        working-directory: e2e-tests
    outputs:
      status_check_url: "${{ steps.e2e-test-gencycle.outputs.status_check_url }}"
    steps:
      - name: ci/checkout-repo
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2
        with:
          persist-credentials: false
          ref: ${{ inputs.commit_sha }}
          fetch-depth: 0
      - name: ci/setup-node
        uses: actions/setup-node@53b83947a5a98c8d113130e565377fae1a50d02f # v6.3.0
        id: setup_node
        with:
          node-version-file: ".nvmrc"
          cache: npm
          cache-dependency-path: "e2e-tests/cypress/package-lock.json" # NB: the generate-cycle script is cypress-specific operation for now
      - name: ci/e2e-test-gencycle
        id: e2e-test-gencycle
        env:
          AUTOMATION_DASHBOARD_URL: "${{ secrets.AUTOMATION_DASHBOARD_URL }}"
          AUTOMATION_DASHBOARD_TOKEN: "${{ secrets.AUTOMATION_DASHBOARD_TOKEN }}"
          BRANCH: "${{ inputs.BRANCH }}"
          BUILD_ID: "${{ inputs.BUILD_ID }}"
          TEST: "${{ inputs.TEST }}"

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/.github/workflows/e2e-tests-ci.yml =====

---
name: E2E Tests (pull request)
on:
  # Argo Events Trigger (automated):
  #   - Triggered by: Enterprise CI/docker-image status check (success)
  #   - Payload: { ref: "<branch>", inputs: { commit_sha: "<sha>" } }
  #   - Uses commit-specific docker image
  #   - Checks for relevant file changes before running tests
  #
  # Manual Trigger:
  #   - Enter PR number only - commit SHA is resolved automatically from PR head
  #   - Uses commit-specific docker image
  #   - E2E tests always run (no file change check)
  #
  workflow_dispatch:
    inputs:
      pr_number:
        description: "PR number to test (for manual triggers)"
        type: string
        required: false
      commit_sha:
        description: "Commit SHA to test (for Argo Events)"
        type: string
        required: false

permissions: {}

jobs:
  resolve-pr:
    permissions:
      contents: read
      pull-requests: read
    runs-on: ubuntu-24.04
    outputs:
      PR_NUMBER: "${{ steps.resolve.outputs.PR_NUMBER }}"
      COMMIT_SHA: "${{ steps.resolve.outputs.COMMIT_SHA }}"
      SERVER_IMAGE_TAG: "${{ steps.e2e-check.outputs.image_tag }}"
      HEAD_REF: "${{ steps.resolve.outputs.HEAD_REF }}"
    steps:
      - name: ci/checkout-repo
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2
        with:
          persist-credentials: false
          fetch-depth: 0

      - name: ci/resolve-pr-and-commit
        id: resolve
        env:
          GH_TOKEN: ${{ github.token }}
          GITHUB_REPOSITORY: ${{ github.repository }}
          INPUT_PR_NUMBER: ${{ inputs.pr_number }}
          INPUT_COMMIT_SHA: ${{ inputs.commit_sha }}
        run: |
          # Validate inputs
          if [ -n "$INPUT_PR_NUMBER" ] && ! [[ "$INPUT_PR_NUMBER" =~ ^[0-9]+$ ]]; then
            echo "::error::Invalid PR number format. Must be numeric."
            exit 1
          fi
          if [ -n "$INPUT_COMMIT_SHA" ] && ! [[ "$INPUT_COMMIT_SHA" =~ ^[a-f0-9]{7,40}$ ]]; then
            echo "::error::Invalid commit SHA format. Must be 7-40 hex characters."
            exit 1
          fi

          # Manual trigger: PR number provided, resolve commit SHA from PR head
          if [ -n "$INPUT_PR_NUMBER" ]; then
            echo "Manual trigger: resolving commit SHA from PR #${INPUT_PR_NUMBER}"
            PR_DATA=$(gh api "repos/${GITHUB_REPOSITORY}/pulls/${INPUT_PR_NUMBER}")
            COMMIT_SHA=$(echo "$PR_DATA" | jq -r '.head.sha')

            if [ -z "$COMMIT_SHA" ] || [ "$COMMIT_SHA" = "null" ]; then
              echo "::error::Could not resolve commit SHA for PR #${INPUT_PR_NUMBER}"
              exit 1
            fi

            echo "PR_NUMBER=${INPUT_PR_NUMBER}" >> $GITHUB_OUTPUT
            echo "COMMIT_SHA=${COMMIT_SHA}" >> $GITHUB_OUTPUT
            echo "HEAD_REF=$(echo "$PR_DATA" | jq -r '.head.ref')" >> $GITHUB_OUTPUT
            exit 0
          fi

          # Argo Events trigger: commit SHA provided, resolve PR number
          if [ -n "$INPUT_COMMIT_SHA" ]; then
            echo "Automated trigger: resolving PR number from commit ${INPUT_COMMIT_SHA}"
            PR_DATA=$(gh api "repos/${GITHUB_REPOSITORY}/commits/${INPUT_COMMIT_SHA}/pulls" \
              --jq '.[0] // empty' 2>/dev/null || echo "")
            PR_NUMBER=$(echo "$PR_DATA" | jq -r '.number // empty' 2>/dev/null || echo "")
            if [ -z "$PR_NUMBER" ]; then
              echo "::error::No PR found for commit ${INPUT_COMMIT_SHA}. This workflow is for PRs only."
              exit 1
            fi

            echo "Found PR #${PR_NUMBER} for commit ${INPUT_COMMIT_SHA}"

            # Skip if PR is already merged to master or a release branch.
            # The e2e-tests-on-merge workflow handles post-merge E2E tests.
            PR_MERGED=$(echo "$PR_DATA" | jq -r '.merged_at // empty' 2>/dev/null || echo "")
            PR_BASE_REF=$(echo "$PR_DATA" | jq -r '.base.ref // empty' 2>/dev/null || echo "")
            if [ -n "$PR_MERGED" ]; then
              if [ "$PR_BASE_REF" = "master" ] || [[ "$PR_BASE_REF" =~ ^release-[0-9]+\.[0-9]+$ ]]; then
                echo "PR #${PR_NUMBER} is already merged to ${PR_BASE_REF}. Skipping - handled by e2e-tests-on-merge workflow."
                echo "PR_NUMBER=" >> $GITHUB_OUTPUT
                echo "COMMIT_SHA=" >> $GITHUB_OUTPUT
                echo "HEAD_REF=" >> $GITHUB_OUTPUT
                exit 0
              fi
            fi

            echo "PR_NUMBER=${PR_NUMBER}" >> $GITHUB_OUTPUT
            echo "COMMIT_SHA=${INPUT_COMMIT_SHA}" >> $GITHUB_OUTPUT
            echo "HEAD_REF=$(echo "$PR_DATA" | jq -r '.head.ref // empty' 2>/dev/null || echo "")" >> $GITHUB_OUTPUT
            exit 0
          fi

          # Neither provided
          echo "::error::Either pr_number or commit_sha must be provided"
          exit 1

      - name: ci/check-e2e-test-only
        if: steps.resolve.outputs.PR_NUMBER != ''
        id: e2e-check
        uses: ./.github/actions/check-e2e-test-only
        with:
          pr_number: ${{ steps.resolve.outputs.PR_NUMBER }}


  check-changes:
    permissions:
      contents: read
      pull-requests: read
    needs: resolve-pr
    if: needs.resolve-pr.outputs.PR_NUMBER != ''
    runs-on: ubuntu-24.04
    outputs:
      should_run: "${{ steps.check.outputs.should_run }}"
      should_run_fips: "${{ steps.check.outputs.should_run_fips }}"
    steps:
      - name: ci/checkout-repo
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2
        with:
          persist-credentials: false
          ref: ${{ needs.resolve-pr.outputs.COMMIT_SHA }}
          fetch-depth: 0
      - name: ci/check-relevant-changes
        id: check
        env:
          GH_TOKEN: ${{ github.token }}
          GITHUB_REPOSITORY: ${{ github.repository }}
          PR_NUMBER: ${{ needs.resolve-pr.outputs.PR_NUMBER }}
          COMMIT_SHA: ${{ needs.resolve-pr.outputs.COMMIT_SHA }}
          INPUT_PR_NUMBER: ${{ inputs.pr_number }}
          HEAD_REF: ${{ needs.resolve-pr.outputs.HEAD_REF }}
        run: |
          # Get the base branch of the PR and changed files
          BASE_SHA=$(gh api "repos/${GITHUB_REPOSITORY}/pulls/${PR_NUMBER}" --jq '.base.sha')
          CHANGED_FILES=$(git diff --name-only "${BASE_SHA}...${COMMIT_SHA}")

          echo "Changed files:"
          echo "$CHANGED_FILES"

          # Determine should_run for regular E2E tests
          if [ -n "$INPUT_PR_NUMBER" ]; then
            # Manual trigger: always run E2E tests
            echo "Manual trigger detected - skipping file change check for regular E2E"
            SHOULD_RUN="true"
          else
            # Automated trigger: check for relevant file changes
            echo "Automated trigger detected - checking for relevant file changes"
            SHOULD_RUN="false"

            if echo "$CHANGED_FILES" | grep -qE '^server/.*\.go$'; then
              echo "Found server Go file changes"
              SHOULD_RUN="true"
            fi

            if echo "$CHANGED_FILES" | grep -qE '^webapp/.*\.(ts|tsx|js|jsx)$'; then
              echo "Found webapp TypeScript/JavaScript file changes"
              SHOULD_RUN="true"
            fi

            if echo "$CHANGED_FILES" | grep -qE '^e2e-tests/.*\.(ts|tsx|js|jsx)$'; then

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/.github/workflows/e2e-tests-cypress-template-v2.yml =====

---
name: E2E Tests - Cypress Template (v2 - test system io dispatch)

# Delegates Cypress spec dispatch + reporting to test system io.
# Authenticates via GitHub Actions OIDC; calling job MUST grant
# `id-token: write`.

on:
  workflow_call:
    inputs:
      test_type:
        description: "Type of test run (smoke or full)"
        type: string
        required: true
      workers:
        description: "Number of parallel test system io dispatch workers"
        type: number
        required: false
        default: 40
      enabled_docker_services:
        description: "Space-separated list of docker services to enable"
        type: string
        required: false
        default: "postgres inbucket minio openldap elasticsearch keycloak"

      commit_sha:
        type: string
        required: true
      branch:
        type: string
        required: true
      build_id:
        type: string
        required: true
      server_image_tag:
        description: "Server image tag (e.g., master or short SHA)"
        type: string
        required: true
      server:
        type: string
        required: false
        default: onprem
      server_edition:
        description: "Server edition: enterprise (default), fips, or team"
        type: string
        required: false
        default: enterprise
      server_image_repo:
        description: "Docker registry: mattermostdevelopment (default) or mattermost"
        type: string
        required: false
        default: mattermostdevelopment
      server_image_aliases:
        description: "Comma-separated alias tags for description"
        type: string
        required: false

      enable_reporting:
        type: boolean
        required: false
        default: false
      report_type:
        type: string
        required: false
      ref_branch:
        type: string
        required: false
      pr_number:
        type: string
        required: false
      context_name:
        description: "GitHub commit status context name"
        type: string
        required: true

      cypress_stage:
        description: "Comma-separated `// Stage:` tags; spec must share at least one. Empty disables filter."
        type: string
        required: false
        default: "@prod"
      cypress_include_group:
        description: "Comma-separated `// Group:` tags; spec must share at least one. Empty disables filter."
        type: string
        required: false
        default: ""
      cypress_exclude_group:
        description: "Comma-separated `// Group:` tags; spec dropped if it shares any."
        type: string
        required: false
        default: "@te_only,@cloud_only,@high_availability"
      cypress_skip_on:
        description: "Comma-separated active-env tag(s); spec dropped if its `// Skip:` line shares any."
        type: string
        required: false
        default: "@headless"
      cypress_sort_first:
        description: "Comma-separated `// Group:` tags; matching specs dispatch first."
        type: string
        required: false
        default: "@compliance_export,@elasticsearch,@ldap_group,@ldap"
      cypress_sort_last:
        description: "Comma-separated `// Group:` tags; matching specs dispatch last."
        type: string
        required: false
        default: "@saml,@keycloak,@plugin,@plugins_uninstall,@mfa,@license_removal"
      retest_on_fail:
        description: "Re-dispatch failed dispatch units once (whole-spec retry, on top of cypress.config retries)"
        type: boolean
        required: false
        default: true

    secrets:
      MM_LICENSE:
        required: false
      AUTOMATION_DASHBOARD_URL:
        required: false
      AUTOMATION_DASHBOARD_TOKEN:
        required: false
      PUSH_NOTIFICATION_SERVER:
        required: false
      REPORT_WEBHOOK_URL:
        required: false
      CWS_URL:
        required: false
      CWS_EXTRA_HTTP_HEADERS:
        required: false

# Callers must grant: contents: read, statuses: write, id-token: write
permissions:
  contents: read
  statuses: write
  id-token: write

env:
  SERVER_IMAGE: "${{ inputs.server_image_repo }}/${{ inputs.server_edition == 'fips' && 'mattermost-enterprise-fips-edition' || inputs.server_edition == 'team' && 'mattermost-team-edition' || 'mattermost-enterprise-edition' }}:${{ inputs.server_image_tag }}"

jobs:
  prepare-run:
    runs-on: ubuntu-24.04
    permissions:
      contents: read
      id-token: write
      statuses: write
    outputs:
      composite-identity-json: ${{ steps.composite-identity.outputs.composite-identity-json }}
      workers-matrix: ${{ steps.matrix.outputs.workers }}
      start_time: ${{ steps.matrix.outputs.start_time }}
    steps:
      - name: ci/checkout-repo
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2
        with:
          persist-credentials: false
          ref: ${{ inputs.commit_sha }}
          fetch-depth: 1
      - name: ci/composite-identity
        id: composite-identity
        env:
          CONTEXT_NAME: ${{ inputs.context_name }}
          GITHUB_REPOSITORY: ${{ github.repository }}
          MM_BRANCH: ${{ inputs.branch }}
          MM_SHA: ${{ inputs.commit_sha }}
          PR_NUMBER: ${{ inputs.pr_number }}
        run: |
          # Derive the test-system-io run name from the GitHub commit-status
          # context: drop the `e2e-test/` prefix (the framework name already
          # implies E2E in the dashboard) and swap remaining `/` for `-` so
          # the dashboard URL is path-safe. The commit-status context itself
          # stays unchanged elsewhere — branch protection rules depend on it.
          NAME="${CONTEXT_NAME#e2e-test/}"
          NAME="${NAME//\//-}"
          # gh_pr_number is optional; include it only when present.
          if [ -n "$PR_NUMBER" ]; then
            COMPOSITE_IDENTITY=$(jq -nc \
              --arg repo "${GITHUB_REPOSITORY}" \
              --arg sha "${MM_SHA}" \
              --arg run_id "${GITHUB_RUN_ID}" \
              --arg name "${NAME}" \
              --arg attempt "${GITHUB_RUN_ATTEMPT}" \
              --arg branch "${MM_BRANCH}" \
              --arg pr "${PR_NUMBER}" \

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/.github/workflows/e2e-tests-cypress-template.yml =====

---
name: E2E Tests - Cypress Template
on:
  workflow_call:
    inputs:
      # Test configuration
      test_type:
        description: "Type of test run (smoke or full)"
        type: string
        required: true
      test_filter:
        description: "Test filter arguments"
        type: string
        required: true
      workers:
        description: "Number of parallel workers"
        type: number
        required: false
        default: 1
      enabled_docker_services:
        description: "Space-separated list of docker services to enable"
        type: string
        required: false
        default: "postgres inbucket"

      # Common build variables
      commit_sha:
        type: string
        required: true
      branch:
        type: string
        required: true
      build_id:
        type: string
        required: true
      server_image_tag:
        description: "Server image tag (e.g., master or short SHA)"
        type: string
        required: true
      server:
        type: string
        required: false
        default: onprem
      server_edition:
        description: "Server edition: enterprise (default), fips, or team"
        type: string
        required: false
        default: enterprise
      server_image_repo:
        description: "Docker registry: mattermostdevelopment (default) or mattermost"
        type: string
        required: false
        default: mattermostdevelopment
      server_image_aliases:
        description: "Comma-separated alias tags for description (e.g., 'release-11.4, release-11')"
        type: string
        required: false

      # Reporting options
      enable_reporting:
        type: boolean
        required: false
        default: false
      report_type:
        type: string
        required: false
      ref_branch:
        description: "Source branch name for webhook messages (e.g., 'master' or 'release-11.4')"
        type: string
        required: false
      pr_number:
        type: string
        required: false
      # Commit status configuration
      context_name:
        description: "GitHub commit status context name"
        type: string
        required: true

    outputs:
      passed:
        description: "Number of passed tests"
        value: ${{ jobs.report.outputs.passed }}
      failed:
        description: "Number of failed tests"
        value: ${{ jobs.report.outputs.failed }}
      status_check_url:
        description: "URL to test results"
        value: ${{ jobs.generate-test-cycle.outputs.status_check_url }}

    secrets:
      MM_LICENSE:
        required: false
      AUTOMATION_DASHBOARD_URL:
        required: false
      AUTOMATION_DASHBOARD_TOKEN:
        required: false
      PUSH_NOTIFICATION_SERVER:
        required: false
      REPORT_WEBHOOK_URL:
        required: false
      CWS_URL:
        required: false
      CWS_EXTRA_HTTP_HEADERS:
        required: false

# Callers must grant at least these scopes on the job that uses this workflow
permissions:
  contents: read
  statuses: write

env:
  SERVER_IMAGE: "${{ inputs.server_image_repo }}/${{ inputs.server_edition == 'fips' && 'mattermost-enterprise-fips-edition' || inputs.server_edition == 'team' && 'mattermost-team-edition' || 'mattermost-enterprise-edition' }}:${{ inputs.server_image_tag }}"

jobs:
  update-initial-status:
    runs-on: ubuntu-24.04
    permissions:
      contents: read
      statuses: write
    steps:
      - name: ci/set-initial-status
        uses: mattermost/actions/delivery/update-commit-status@f324ac89b05cc3511cb06e60642ac2fb829f0a63
        env:
          GITHUB_TOKEN: ${{ github.token }}
        with:
          repository_full_name: ${{ github.repository }}
          commit_sha: ${{ inputs.commit_sha }}
          context: ${{ inputs.context_name }}
          description: "tests running, image_tag:${{ inputs.server_image_tag }}${{ inputs.server_image_aliases && format(' ({0})', inputs.server_image_aliases) || '' }}"
          status: pending

  generate-test-cycle:
    runs-on: ubuntu-24.04
    outputs:
      status_check_url: "${{ steps.generate-cycle.outputs.status_check_url }}"
      workers: "${{ steps.generate-workers.outputs.workers }}"
      start_time: "${{ steps.generate-workers.outputs.start_time }}"
    steps:
      - name: ci/generate-workers
        id: generate-workers
        env:
          INPUT_WORKERS: ${{ inputs.workers }}
        run: |
          echo "workers=$(jq -nc --argjson n "${INPUT_WORKERS}" '[range($n)]')" >> $GITHUB_OUTPUT
          echo "start_time=$(date +%s)" >> $GITHUB_OUTPUT

      - name: ci/checkout-repo
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2
        with:
          persist-credentials: false
          ref: ${{ inputs.commit_sha }}
          fetch-depth: 0
      - name: ci/setup-node
        uses: actions/setup-node@53b83947a5a98c8d113130e565377fae1a50d02f # v6.3.0
        with:
          node-version-file: ".nvmrc"
          cache: npm
          cache-dependency-path: "e2e-tests/cypress/package-lock.json"

      - name: ci/generate-test-cycle
        id: generate-cycle
        working-directory: e2e-tests
        env:
          AUTOMATION_DASHBOARD_URL: "${{ secrets.AUTOMATION_DASHBOARD_URL }}"
          AUTOMATION_DASHBOARD_TOKEN: "${{ secrets.AUTOMATION_DASHBOARD_TOKEN }}"
          BRANCH: "${{ inputs.branch }}-${{ inputs.test_type }}"
          BUILD_ID: "${{ inputs.build_id }}"
          TEST: cypress
          TEST_FILTER: "${{ inputs.test_filter }}"
          GITHUB_SERVER_URL: ${{ github.server_url }}
          GITHUB_REPOSITORY: ${{ github.repository }}
          GITHUB_RUN_ID: ${{ github.run_id }}
        run: |
          set -e -o pipefail
          make generate-test-cycle | tee generate-test-cycle.out
          TEST_CYCLE_ID=$(sed -nE "s/^.*id: '([^']+)'.*$/\1/p" <generate-test-cycle.out)
          if [ -n "$TEST_CYCLE_ID" ]; then
            echo "status_check_url=https://automation-dashboard.vercel.app/cycles/${TEST_CYCLE_ID}" >> $GITHUB_OUTPUT
          else

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/.github/workflows/e2e-tests-cypress.yml =====

---
name: E2E Tests - Cypress
on:
  workflow_call:
    inputs:
      commit_sha:
        type: string
        required: true
      enable_reporting:
        type: boolean
        required: false
        default: false
      server:
        type: string
        required: false
        default: onprem
      report_type:
        type: string
        required: false
      pr_number:
        type: string
        required: false
      server_image_tag:
        type: string
        required: false
        description: "Server image tag (e.g., master or short SHA)"
      server_edition:
        type: string
        required: false
        description: "Server edition: enterprise (default), fips, or team"
      server_image_repo:
        type: string
        required: false
        default: mattermostdevelopment
        description: "Docker registry: mattermostdevelopment (default) or mattermost"
      server_image_aliases:
        type: string
        required: false
        description: "Comma-separated alias tags for context name (e.g., 'release-11.4, release-11')"
      ref_branch:
        type: string
        required: false
        description: "Source branch name for webhook messages (e.g., 'master' or 'release-11.4')"
      should_run:
        type: string
        required: false
        default: "true"
        description: "Set to 'false' to skip tests and post a success status without running E2E"
    secrets:
      MM_LICENSE:
        required: false
      AUTOMATION_DASHBOARD_URL:
        required: false
      AUTOMATION_DASHBOARD_TOKEN:
        required: false
      PUSH_NOTIFICATION_SERVER:
        required: false
      REPORT_WEBHOOK_URL:
        required: false
      CWS_URL:
        required: false
      CWS_EXTRA_HTTP_HEADERS:
        required: false

permissions: {}

jobs:
  generate-build-variables:
    runs-on: ubuntu-24.04
    outputs:
      branch: "${{ steps.build-vars.outputs.branch }}"
      build_id: "${{ steps.build-vars.outputs.build_id }}"
      server_image_tag: "${{ steps.build-vars.outputs.server_image_tag }}"
      server_image: "${{ steps.build-vars.outputs.server_image }}"
      context_suffix: "${{ steps.build-vars.outputs.context_suffix }}"
    steps:
      - name: ci/generate-build-variables
        id: build-vars
        env:
          COMMIT_SHA: ${{ inputs.commit_sha }}
          INPUT_REF_BRANCH: ${{ inputs.ref_branch }}
          INPUT_REPORT_TYPE: ${{ inputs.report_type }}
          INPUT_SERVER_EDITION: ${{ inputs.server_edition }}
          INPUT_SERVER_IMAGE_ALIASES: ${{ inputs.server_image_aliases }}
          INPUT_SERVER_IMAGE_REPO: ${{ inputs.server_image_repo }}
          INPUT_SERVER_IMAGE_TAG: ${{ inputs.server_image_tag }}
          PR_NUMBER: ${{ inputs.pr_number }}
          RUN_ATTEMPT: ${{ github.run_attempt }}
          RUN_ID: ${{ github.run_id }}
        run: |
          # Use provided server_image_tag or derive from commit SHA
          if [ -n "$INPUT_SERVER_IMAGE_TAG" ]; then
            SERVER_IMAGE_TAG="$INPUT_SERVER_IMAGE_TAG"
          else
            SERVER_IMAGE_TAG="${COMMIT_SHA::7}"
          fi

          # Validate server_image_tag format (alphanumeric, dots, hyphens, underscores)
          if ! [[ "$SERVER_IMAGE_TAG" =~ ^[a-zA-Z0-9._-]+$ ]]; then
            echo "::error::Invalid server_image_tag format: ${SERVER_IMAGE_TAG}"
            exit 1
          fi
          echo "server_image_tag=${SERVER_IMAGE_TAG}" >> $GITHUB_OUTPUT

          # Generate branch name. For master/release runs we pass the real
          # ref_branch through verbatim (`master`, `release-11.7`) so the
          # dashboard's /reports/{repo}/{branch} grouping aggregates every
          # build on that branch instead of treating each image tag as its
          # own "branch". PR and commit-only fallback paths keep their
          # synthetic prefix because there's no real branch to use.
          REF_BRANCH="${INPUT_REF_BRANCH}"
          if [ -n "$PR_NUMBER" ]; then
            echo "branch=pr-${PR_NUMBER}" >> $GITHUB_OUTPUT
          elif [ -n "$REF_BRANCH" ]; then
            echo "branch=${REF_BRANCH}" >> $GITHUB_OUTPUT
          else
            echo "branch=commit-${COMMIT_SHA::7}" >> $GITHUB_OUTPUT
          fi

          # Determine server image name
          EDITION="${INPUT_SERVER_EDITION}"
          REPO="${INPUT_SERVER_IMAGE_REPO}"
          REPO="${REPO:-mattermostdevelopment}"
          case "$EDITION" in
            fips) IMAGE_NAME="mattermost-enterprise-fips-edition" ;;
            team) IMAGE_NAME="mattermost-team-edition" ;;
            *)    IMAGE_NAME="mattermost-enterprise-edition" ;;
          esac
          SERVER_IMAGE="${REPO}/${IMAGE_NAME}:${SERVER_IMAGE_TAG}"
          echo "server_image=${SERVER_IMAGE}" >> $GITHUB_OUTPUT

          # Validate server_image_aliases format if provided
          ALIASES="${INPUT_SERVER_IMAGE_ALIASES}"
          if [ -n "$ALIASES" ] && ! [[ "$ALIASES" =~ ^[a-zA-Z0-9._,\ -]+$ ]]; then
            echo "::error::Invalid server_image_aliases format: ${ALIASES}"
            exit 1
          fi

          # Generate build ID
          if [ -n "$EDITION" ] && [ "$EDITION" != "enterprise" ]; then
            echo "build_id=${RUN_ID}_${RUN_ATTEMPT}-${SERVER_IMAGE_TAG}-cypress-onprem-${EDITION}" >> $GITHUB_OUTPUT
          else
            echo "build_id=${RUN_ID}_${RUN_ATTEMPT}-${SERVER_IMAGE_TAG}-cypress-onprem-ent" >> $GITHUB_OUTPUT
          fi

          # Generate context name suffix based on report type
          REPORT_TYPE="${INPUT_REPORT_TYPE}"
          case "$REPORT_TYPE" in
            MASTER) echo "context_suffix=/master" >> $GITHUB_OUTPUT ;;
            RELEASE) echo "context_suffix=/release" >> $GITHUB_OUTPUT ;;
            RELEASE_CUT) echo "context_suffix=/release-cut" >> $GITHUB_OUTPUT ;;
            *) echo "context_suffix=" >> $GITHUB_OUTPUT ;;
          esac

  skip:
    needs:
      - generate-build-variables
    if: inputs.should_run == 'false'
    runs-on: ubuntu-24.04
    permissions:
      contents: read
      statuses: write
    steps:
      - name: ci/post-skip-status
        env:
          COMMIT_SHA: ${{ inputs.commit_sha }}
          CONTEXT_NAME: "e2e-test/cypress-full/${{ inputs.server_edition || 'enterprise' }}${{ needs.generate-build-variables.outputs.context_suffix }}"
          GH_TOKEN: ${{ github.token }}
          GITHUB_REPOSITORY: ${{ github.repository }}
          GITHUB_RUN_ID: ${{ github.run_id }}
        run: |
          gh api "repos/${GITHUB_REPOSITORY}/statuses/${COMMIT_SHA}" \
            -f state=success \
            -f context="${CONTEXT_NAME}" \
            -f description="No E2E-relevant changes - skipped" \
            -f target_url="https://github.com/${GITHUB_REPOSITORY}/actions/runs/${GITHUB_RUN_ID}"
          echo "Posted success for ${CONTEXT_NAME}"

  # ── Routing fork ─────────────────────────────────────────────────────
  # vars.E2E_USE_TEST_IO_DISPATCH selects between v1 (legacy) and v2.

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/.github/workflows/e2e-tests-on-merge.yml =====

---
name: E2E Tests (master/release - merge)
on:
  workflow_dispatch:
    inputs:
      branch:
        type: string
        required: true
        description: "Branch name (e.g., 'master' or 'release-11.4')"
      commit_sha:
        type: string
        required: true
        description: "Commit SHA to test"
      server_image_tag:
        type: string
        required: true
        description: "Docker image tag (e.g., 'abc1234_def5678' or 'master')"

permissions: {}

jobs:
  generate-build-variables:
    permissions:
      contents: read
    runs-on: ubuntu-24.04
    outputs:
      report_type: "${{ steps.vars.outputs.report_type }}"
      ref_branch: "${{ steps.vars.outputs.ref_branch }}"
      fips_supported: "${{ steps.vars.outputs.fips_supported }}"
    steps:
      - name: ci/checkout-repo
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2
        with:
          persist-credentials: false
          ref: ${{ inputs.branch }}
          fetch-depth: 50
      - name: ci/generate-variables
        id: vars
        env:
          BRANCH: ${{ inputs.branch }}
          COMMIT_SHA: ${{ inputs.commit_sha }}
        run: |
          # Strip refs/heads/ prefix if present
          BRANCH="${BRANCH#refs/heads/}"

          # Validate branch is master or release-X.Y, and decide whether FIPS is supported.
          # FIPS builds were introduced in release-11.0; skip FIPS tests for older branches.
          if [[ "$BRANCH" == "master" ]]; then
            echo "report_type=MASTER" >> $GITHUB_OUTPUT
            echo "fips_supported=true" >> $GITHUB_OUTPUT
          elif [[ "$BRANCH" =~ ^release-([0-9]+)\.[0-9]+$ ]]; then
            echo "report_type=RELEASE" >> $GITHUB_OUTPUT
            if [[ "${BASH_REMATCH[1]}" -ge 11 ]]; then
              echo "fips_supported=true" >> $GITHUB_OUTPUT
            else
              echo "fips_supported=false" >> $GITHUB_OUTPUT
            fi
          else
            echo "::error::Branch ${BRANCH} must be 'master' or 'release-X.Y' format."
            exit 1
          fi

          echo "ref_branch=${BRANCH}" >> $GITHUB_OUTPUT

          # Validate commit exists on the branch
          if ! git merge-base --is-ancestor "$COMMIT_SHA" HEAD; then
            echo "::error::Commit ${COMMIT_SHA} is not on branch ${BRANCH}."
            exit 1
          fi

  # Enterprise Edition
  e2e-cypress:
    needs: generate-build-variables
    permissions:
      contents: read
      statuses: write
      id-token: write
      pull-requests: write
    uses: ./.github/workflows/e2e-tests-cypress.yml
    with:
      commit_sha: ${{ inputs.commit_sha }}
      server_image_tag: ${{ inputs.server_image_tag }}
      server: onprem
      enable_reporting: true
      report_type: ${{ needs.generate-build-variables.outputs.report_type }}
      ref_branch: ${{ needs.generate-build-variables.outputs.ref_branch }}
    secrets:
      MM_LICENSE: "${{ secrets.MM_E2E_TEST_LICENSE_ONPREM_ENT }}"
      AUTOMATION_DASHBOARD_URL: "${{ secrets.MM_E2E_AUTOMATION_DASHBOARD_URL }}"
      AUTOMATION_DASHBOARD_TOKEN: "${{ secrets.MM_E2E_AUTOMATION_DASHBOARD_TOKEN }}"
      PUSH_NOTIFICATION_SERVER: "${{ secrets.MM_E2E_PUSH_NOTIFICATION_SERVER }}"
      REPORT_WEBHOOK_URL: "${{ secrets.MM_E2E_REPORT_WEBHOOK_URL }}"
      CWS_URL: "${{ secrets.MM_E2E_CWS_URL }}"
      CWS_EXTRA_HTTP_HEADERS: "${{ secrets.MM_E2E_CWS_EXTRA_HTTP_HEADERS }}"

  e2e-playwright:
    needs: generate-build-variables
    permissions:
      contents: read
      statuses: write
      id-token: write
      pull-requests: write
    uses: ./.github/workflows/e2e-tests-playwright.yml
    with:
      commit_sha: ${{ inputs.commit_sha }}
      server_image_tag: ${{ inputs.server_image_tag }}
      server: onprem
      enable_reporting: true
      report_type: ${{ needs.generate-build-variables.outputs.report_type }}
      ref_branch: ${{ needs.generate-build-variables.outputs.ref_branch }}
    secrets:
      MM_LICENSE: "${{ secrets.MM_E2E_TEST_LICENSE_ONPREM_ENT }}"
      AWS_ACCESS_KEY_ID: "${{ secrets.CYPRESS_AWS_ACCESS_KEY_ID }}"
      AWS_SECRET_ACCESS_KEY: "${{ secrets.CYPRESS_AWS_SECRET_ACCESS_KEY }}"
      REPORT_WEBHOOK_URL: "${{ secrets.MM_E2E_REPORT_WEBHOOK_URL }}"

  # Enterprise FIPS Edition
  # FIPS builds were introduced in release-11.0; skip for older branches.
  e2e-cypress-fips:
    needs: generate-build-variables
    if: needs.generate-build-variables.outputs.fips_supported == 'true'
    permissions:
      contents: read
      statuses: write
      id-token: write
      pull-requests: write
    uses: ./.github/workflows/e2e-tests-cypress.yml
    with:
      commit_sha: ${{ inputs.commit_sha }}
      server_image_tag: ${{ inputs.server_image_tag }}
      server_edition: fips
      server: onprem
      enable_reporting: true
      report_type: ${{ needs.generate-build-variables.outputs.report_type }}
      ref_branch: ${{ needs.generate-build-variables.outputs.ref_branch }}
    secrets:
      MM_LICENSE: "${{ secrets.MM_E2E_TEST_LICENSE_ONPREM_ENT }}"
      AUTOMATION_DASHBOARD_URL: "${{ secrets.MM_E2E_AUTOMATION_DASHBOARD_URL }}"
      AUTOMATION_DASHBOARD_TOKEN: "${{ secrets.MM_E2E_AUTOMATION_DASHBOARD_TOKEN }}"
      PUSH_NOTIFICATION_SERVER: "${{ secrets.MM_E2E_PUSH_NOTIFICATION_SERVER }}"
      REPORT_WEBHOOK_URL: "${{ secrets.MM_E2E_REPORT_WEBHOOK_URL }}"
      CWS_URL: "${{ secrets.MM_E2E_CWS_URL }}"
      CWS_EXTRA_HTTP_HEADERS: "${{ secrets.MM_E2E_CWS_EXTRA_HTTP_HEADERS }}"

  e2e-playwright-fips:
    needs: generate-build-variables
    if: needs.generate-build-variables.outputs.fips_supported == 'true'
    permissions:
      contents: read
      statuses: write
      id-token: write
      pull-requests: write
    uses: ./.github/workflows/e2e-tests-playwright.yml
    with:
      commit_sha: ${{ inputs.commit_sha }}
      server_image_tag: ${{ inputs.server_image_tag }}
      server_edition: fips
      server: onprem
      enable_reporting: true
      report_type: ${{ needs.generate-build-variables.outputs.report_type }}
      ref_branch: ${{ needs.generate-build-variables.outputs.ref_branch }}
    secrets:
      MM_LICENSE: "${{ secrets.MM_E2E_TEST_LICENSE_ONPREM_ENT }}"
      AWS_ACCESS_KEY_ID: "${{ secrets.CYPRESS_AWS_ACCESS_KEY_ID }}"
      AWS_SECRET_ACCESS_KEY: "${{ secrets.CYPRESS_AWS_SECRET_ACCESS_KEY }}"
      REPORT_WEBHOOK_URL: "${{ secrets.MM_E2E_REPORT_WEBHOOK_URL }}"

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/.github/workflows/e2e-tests-on-release.yml =====

---
name: E2E Tests (release cut)
on:
  workflow_dispatch:
    inputs:
      branch:
        type: string
        required: true
        description: "Release branch (e.g., 'release-11.4')"
      commit_sha:
        type: string
        required: true
        description: "Commit SHA to test"
      server_image_tag:
        type: string
        required: true
        description: "Docker image tag (e.g., '11.4.0', '11.4.0-rc3', or 'release-11.4')"
      server_image_aliases:
        type: string
        required: false
        description: "Comma-separated alias tags (e.g., 'release-11.4, release-11')"

permissions: {}

jobs:
  validate:
    permissions:
      contents: read
    runs-on: ubuntu-24.04
    outputs:
      ref_branch: "${{ steps.check.outputs.ref_branch }}"
      fips_supported: "${{ steps.check.outputs.fips_supported }}"
    steps:
      - name: ci/checkout-repo
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2
        with:
          persist-credentials: false
          ref: ${{ inputs.branch }}
          fetch-depth: 50
      - name: ci/validate-inputs
        id: check
        env:
          BRANCH: ${{ inputs.branch }}
          COMMIT_SHA: ${{ inputs.commit_sha }}
        run: |
          # Strip refs/heads/ prefix if present
          BRANCH="${BRANCH#refs/heads/}"

          # FIPS builds were introduced in release-11.0; skip FIPS tests for older branches.
          if ! [[ "$BRANCH" =~ ^release-([0-9]+)\.[0-9]+$ ]]; then
            echo "::error::Branch ${BRANCH} must be 'release-X.Y' format."
            exit 1
          elif ! git merge-base --is-ancestor "$COMMIT_SHA" HEAD; then
            echo "::error::Commit ${COMMIT_SHA} is not on branch ${BRANCH}."
            exit 1
          fi

          if [[ "${BASH_REMATCH[1]}" -ge 11 ]]; then
            echo "fips_supported=true" >> $GITHUB_OUTPUT
          else
            echo "fips_supported=false" >> $GITHUB_OUTPUT
          fi

          echo "ref_branch=${BRANCH}" >> $GITHUB_OUTPUT

  # Enterprise Edition
  e2e-cypress:
    needs: validate
    permissions:
      contents: read
      statuses: write
      id-token: write
      pull-requests: write
    uses: ./.github/workflows/e2e-tests-cypress.yml
    with:
      commit_sha: ${{ inputs.commit_sha }}
      server_image_tag: ${{ inputs.server_image_tag }}
      server_image_repo: mattermost
      server_image_aliases: ${{ inputs.server_image_aliases }}
      server: onprem
      enable_reporting: true
      report_type: RELEASE_CUT
      ref_branch: ${{ needs.validate.outputs.ref_branch }}
    secrets:
      MM_LICENSE: "${{ secrets.MM_E2E_TEST_LICENSE_ONPREM_ENT }}"
      AUTOMATION_DASHBOARD_URL: "${{ secrets.MM_E2E_AUTOMATION_DASHBOARD_URL }}"
      AUTOMATION_DASHBOARD_TOKEN: "${{ secrets.MM_E2E_AUTOMATION_DASHBOARD_TOKEN }}"
      PUSH_NOTIFICATION_SERVER: "${{ secrets.MM_E2E_PUSH_NOTIFICATION_SERVER }}"
      REPORT_WEBHOOK_URL: "${{ secrets.MM_E2E_REPORT_WEBHOOK_URL }}"
      CWS_URL: "${{ secrets.MM_E2E_CWS_URL }}"
      CWS_EXTRA_HTTP_HEADERS: "${{ secrets.MM_E2E_CWS_EXTRA_HTTP_HEADERS }}"

  e2e-playwright:
    needs: validate
    permissions:
      contents: read
      statuses: write
      id-token: write
      pull-requests: write
    uses: ./.github/workflows/e2e-tests-playwright.yml
    with:
      commit_sha: ${{ inputs.commit_sha }}
      server_image_tag: ${{ inputs.server_image_tag }}
      server_image_repo: mattermost
      server_image_aliases: ${{ inputs.server_image_aliases }}
      server: onprem
      enable_reporting: true
      report_type: RELEASE_CUT
      ref_branch: ${{ needs.validate.outputs.ref_branch }}
    secrets:
      MM_LICENSE: "${{ secrets.MM_E2E_TEST_LICENSE_ONPREM_ENT }}"
      AWS_ACCESS_KEY_ID: "${{ secrets.CYPRESS_AWS_ACCESS_KEY_ID }}"
      AWS_SECRET_ACCESS_KEY: "${{ secrets.CYPRESS_AWS_SECRET_ACCESS_KEY }}"
      REPORT_WEBHOOK_URL: "${{ secrets.MM_E2E_REPORT_WEBHOOK_URL }}"

  # Enterprise FIPS Edition
  # FIPS builds were introduced in release-11.0; skip for older branches.
  e2e-cypress-fips:
    needs: validate
    if: needs.validate.outputs.fips_supported == 'true'
    permissions:
      contents: read
      statuses: write
      id-token: write
      pull-requests: write
    uses: ./.github/workflows/e2e-tests-cypress.yml
    with:
      commit_sha: ${{ inputs.commit_sha }}
      server_image_tag: ${{ inputs.server_image_tag }}
      server_edition: fips
      server_image_repo: mattermost
      server_image_aliases: ${{ inputs.server_image_aliases }}
      server: onprem
      enable_reporting: true
      report_type: RELEASE_CUT
      ref_branch: ${{ needs.validate.outputs.ref_branch }}
    secrets:
      MM_LICENSE: "${{ secrets.MM_E2E_TEST_LICENSE_ONPREM_ENT }}"
      AUTOMATION_DASHBOARD_URL: "${{ secrets.MM_E2E_AUTOMATION_DASHBOARD_URL }}"
      AUTOMATION_DASHBOARD_TOKEN: "${{ secrets.MM_E2E_AUTOMATION_DASHBOARD_TOKEN }}"
      PUSH_NOTIFICATION_SERVER: "${{ secrets.MM_E2E_PUSH_NOTIFICATION_SERVER }}"
      REPORT_WEBHOOK_URL: "${{ secrets.MM_E2E_REPORT_WEBHOOK_URL }}"
      CWS_URL: "${{ secrets.MM_E2E_CWS_URL }}"
      CWS_EXTRA_HTTP_HEADERS: "${{ secrets.MM_E2E_CWS_EXTRA_HTTP_HEADERS }}"

  e2e-playwright-fips:
    needs: validate
    if: needs.validate.outputs.fips_supported == 'true'
    permissions:
      contents: read
      statuses: write
      id-token: write
      pull-requests: write
    uses: ./.github/workflows/e2e-tests-playwright.yml
    with:
      commit_sha: ${{ inputs.commit_sha }}
      server_image_tag: ${{ inputs.server_image_tag }}
      server_edition: fips
      server_image_repo: mattermost
      server_image_aliases: ${{ inputs.server_image_aliases }}
      server: onprem
      enable_reporting: true
      report_type: RELEASE_CUT
      ref_branch: ${{ needs.validate.outputs.ref_branch }}
    secrets:
      MM_LICENSE: "${{ secrets.MM_E2E_TEST_LICENSE_ONPREM_ENT }}"
      AWS_ACCESS_KEY_ID: "${{ secrets.CYPRESS_AWS_ACCESS_KEY_ID }}"
      AWS_SECRET_ACCESS_KEY: "${{ secrets.CYPRESS_AWS_SECRET_ACCESS_KEY }}"
      REPORT_WEBHOOK_URL: "${{ secrets.MM_E2E_REPORT_WEBHOOK_URL }}"

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/.github/workflows/e2e-tests-override-status.yml =====

---
name: E2E Tests - Override Status

on:
  workflow_dispatch:
    inputs:
      pr_number:
        description: "PR number to update status for"
        required: true
        type: string

permissions: {}

jobs:
  override-status:
    permissions:
      contents: read
      pull-requests: read
      statuses: write
    runs-on: ubuntu-24.04
    steps:
      - name: Validate inputs
        env:
          PR_NUMBER: ${{ inputs.pr_number }}
        run: |
          if ! [[ "$PR_NUMBER" =~ ^[0-9]+$ ]]; then
            echo "::error::Invalid PR number format. Must be numeric."
            exit 1
          fi
      - name: Get PR head SHA
        id: pr-info
        env:
          GH_TOKEN: ${{ github.token }}
          GITHUB_REPOSITORY: ${{ github.repository }}
          PR_NUMBER: ${{ inputs.pr_number }}
        run: |
          PR_DATA=$(gh api "repos/${GITHUB_REPOSITORY}/pulls/${PR_NUMBER}")
          HEAD_SHA=$(echo "$PR_DATA" | jq -r '.head.sha')
          echo "head_sha=$HEAD_SHA" >> $GITHUB_OUTPUT

      - name: Override failed full test statuses
        env:
          GH_TOKEN: ${{ github.token }}
          COMMIT_SHA: ${{ steps.pr-info.outputs.head_sha }}
          GITHUB_REPOSITORY: ${{ github.repository }}
        run: |
          # Only full tests can be overridden (smoke tests must pass)
          FULL_TEST_CONTEXTS=("e2e-test/playwright-full/enterprise" "e2e-test/cypress-full/enterprise" "e2e-test/playwright-full/fips" "e2e-test/cypress-full/fips")

          for CONTEXT_NAME in "${FULL_TEST_CONTEXTS[@]}"; do
            echo "Checking: $CONTEXT_NAME"

            # Get current status
            STATUS_JSON=$(gh api "repos/${GITHUB_REPOSITORY}/commits/${COMMIT_SHA}/statuses" \
              --jq "[.[] | select(.context == \"$CONTEXT_NAME\")] | first // empty")

            if [ -z "$STATUS_JSON" ]; then
              echo "  No status found, skipping"
              continue
            fi

            CURRENT_DESC=$(echo "$STATUS_JSON" | jq -r '.description // ""')
            CURRENT_URL=$(echo "$STATUS_JSON" | jq -r '.target_url // ""')
            CURRENT_STATE=$(echo "$STATUS_JSON" | jq -r '.state // ""')

            echo "  Current: $CURRENT_DESC ($CURRENT_STATE)"

            # Only override if status is failure
            if [ "$CURRENT_STATE" != "failure" ]; then
              echo "  Not failed, skipping"
              continue
            fi

            # Parse and construct new message
            if [[ "$CURRENT_DESC" =~ ^([0-9]+)\ failed,\ ([0-9]+)\ passed$ ]]; then
              FAILED="${BASH_REMATCH[1]}"
              PASSED="${BASH_REMATCH[2]}"
              NEW_MSG="${FAILED} failed (verified), ${PASSED} passed"
            elif [[ "$CURRENT_DESC" =~ ^([0-9]+)\ failed\ \([^)]+\),\ ([0-9]+)\ passed$ ]]; then
              FAILED="${BASH_REMATCH[1]}"
              PASSED="${BASH_REMATCH[2]}"
              NEW_MSG="${FAILED} failed (verified), ${PASSED} passed"
            else
              NEW_MSG="${CURRENT_DESC} (verified)"
            fi

            echo "  New: $NEW_MSG"

            # Update status via GitHub API
            gh api "repos/${GITHUB_REPOSITORY}/statuses/${COMMIT_SHA}" \
              -f state=success \
              -f context="$CONTEXT_NAME" \
              -f description="$NEW_MSG" \
              -f target_url="$CURRENT_URL"

            echo "  Updated to success"
          done

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/.github/workflows/e2e-tests-playwright-template-v2.yml =====

---
name: E2E Tests - Playwright Template (v2 - test system io dispatch)

# Delegates Playwright spec dispatch + reporting to test system io.
# Authenticates via GitHub Actions OIDC; calling job MUST grant
# `id-token: write`.

on:
  workflow_call:
    inputs:
      workers:
        description: "Number of parallel test system io dispatch workers"
        type: number
        required: false
        default: 8
      enabled_docker_services:
        description: "Space-separated list of docker services to enable"
        type: string
        required: false
        default: "postgres inbucket"

      commit_sha:
        type: string
        required: true
      branch:
        type: string
        required: true
      build_id:
        type: string
        required: true
      server_image_tag:
        description: "Server image tag (e.g., master or short SHA)"
        type: string
        required: true
      server:
        type: string
        required: false
        default: onprem
      server_edition:
        description: "Server edition: enterprise (default), fips, or team"
        type: string
        required: false
        default: enterprise
      server_image_repo:
        description: "Docker registry: mattermostdevelopment (default) or mattermost"
        type: string
        required: false
        default: mattermostdevelopment
      server_image_aliases:
        description: "Comma-separated alias tags for description"
        type: string
        required: false

      enable_reporting:
        type: boolean
        required: false
        default: false
      report_type:
        type: string
        required: false
      ref_branch:
        type: string
        required: false
      pr_number:
        type: string
        required: false
      context_name:
        description: "GitHub commit status context name"
        type: string
        required: true

      playwright_project:
        description: "Playwright project name (passed to dispatch-begin metadata and dispatch-run --project=)."
        type: string
        required: false
        default: chrome
      playwright_retries:
        description: "Playwright --retries=N (per-spec, in-process retry of flaky tests)"
        type: number
        required: false
        default: 1
      retest_on_fail:
        description: "Re-dispatch failed dispatch units once (whole-spec retry, on top of Playwright --retries)"
        type: boolean
        required: false
        default: true

    secrets:
      MM_LICENSE:
        required: false
      REPORT_WEBHOOK_URL:
        required: false

# Callers must grant: contents: read, statuses: write, id-token: write
permissions:
  contents: read
  statuses: write
  id-token: write

env:
  SERVER_IMAGE: "${{ inputs.server_image_repo }}/${{ inputs.server_edition == 'fips' && 'mattermost-enterprise-fips-edition' || inputs.server_edition == 'team' && 'mattermost-team-edition' || 'mattermost-enterprise-edition' }}:${{ inputs.server_image_tag }}"

jobs:
  prepare-run:
    runs-on: ubuntu-24.04
    permissions:
      contents: read
      id-token: write
      statuses: write
    outputs:
      composite-identity-json: ${{ steps.composite-identity.outputs.composite-identity-json }}
      workers-matrix: ${{ steps.matrix.outputs.workers }}
      start_time: ${{ steps.matrix.outputs.start_time }}
    steps:
      - name: ci/checkout-repo
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2
        with:
          persist-credentials: false
          ref: ${{ inputs.commit_sha }}
          fetch-depth: 1
      - name: ci/composite-identity
        id: composite-identity
        env:
          CONTEXT_NAME: ${{ inputs.context_name }}
          GITHUB_REPOSITORY: ${{ github.repository }}
          MM_BRANCH: ${{ inputs.branch }}
          MM_SHA: ${{ inputs.commit_sha }}
          PR_NUMBER: ${{ inputs.pr_number }}
        run: |
          # Derive the test-system-io run name from the GitHub commit-status
          # context: drop the `e2e-test/` prefix (the framework name already
          # implies E2E in the dashboard) and swap remaining `/` for `-` so
          # the dashboard URL is path-safe. The commit-status context itself
          # stays unchanged elsewhere — branch protection rules depend on it.
          NAME="${CONTEXT_NAME#e2e-test/}"
          NAME="${NAME//\//-}"
          if [ -n "$PR_NUMBER" ]; then
            COMPOSITE_IDENTITY=$(jq -nc \
              --arg repo "${GITHUB_REPOSITORY}" \
              --arg sha "${MM_SHA}" \
              --arg run_id "${GITHUB_RUN_ID}" \
              --arg name "${NAME}" \
              --arg attempt "${GITHUB_RUN_ATTEMPT}" \
              --arg branch "${MM_BRANCH}" \
              --arg pr "${PR_NUMBER}" \
              '{repository:$repo, commit_sha:$sha, gh_run_id:$run_id, name:$name, gh_run_attempt:$attempt, branch:$branch, gh_pr_number:$pr}')
          else
            COMPOSITE_IDENTITY=$(jq -nc \
              --arg repo "${GITHUB_REPOSITORY}" \
              --arg sha "${MM_SHA}" \
              --arg run_id "${GITHUB_RUN_ID}" \
              --arg name "${NAME}" \
              --arg attempt "${GITHUB_RUN_ATTEMPT}" \
              --arg branch "${MM_BRANCH}" \
              '{repository:$repo, commit_sha:$sha, gh_run_id:$run_id, name:$name, gh_run_attempt:$attempt, branch:$branch}')
          fi
          echo "composite-identity-json=${COMPOSITE_IDENTITY}" >> $GITHUB_OUTPUT
      - name: ci/matrix
        id: matrix
        env:
          INPUT_WORKERS: ${{ inputs.workers }}
        run: |
          echo "workers=$(jq -nc --argjson n "${INPUT_WORKERS}" '[range(1; $n+1)]')" >> $GITHUB_OUTPUT
          echo "start_time=$(date +%s)" >> $GITHUB_OUTPUT

  # Build @mattermost/client + @mattermost/types and install playwright deps once,
  # then workers restore from cache. Playwright only consumes those two packages
  # from webapp, so we cache just their built lib/ instead of all of webapp/node_modules.
  prep-deps:
    name: prep-deps
    runs-on: ubuntu-24.04
    timeout-minutes: 15
    permissions:
      contents: read
    steps:
      - name: ci/checkout-repo
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2
        with:
          persist-credentials: false
          ref: ${{ inputs.commit_sha }}

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/.github/workflows/e2e-tests-playwright-template.yml =====

---
name: E2E Tests - Playwright Template
on:
  workflow_call:
    inputs:
      # Test configuration
      test_type:
        description: "Type of test run (smoke or full)"
        type: string
        required: true
      test_filter:
        description: "Test filter arguments (e.g., --grep @smoke)"
        type: string
        required: true
      workers:
        description: "Number of parallel shards"
        type: number
        required: false
        default: 2
      enabled_docker_services:
        description: "Space-separated list of docker services to enable"
        type: string
        required: false
        default: "postgres inbucket"

      # Common build variables
      commit_sha:
        type: string
        required: true
      branch:
        type: string
        required: true
      build_id:
        type: string
        required: true
      server_image_tag:
        description: "Server image tag (e.g., master or short SHA)"
        type: string
        required: true
      server:
        type: string
        required: false
        default: onprem
      server_edition:
        description: "Server edition: enterprise (default), fips, or team"
        type: string
        required: false
        default: enterprise
      server_image_repo:
        description: "Docker registry: mattermostdevelopment (default) or mattermost"
        type: string
        required: false
        default: mattermostdevelopment
      server_image_aliases:
        description: "Comma-separated alias tags for description (e.g., 'release-11.4, release-11')"
        type: string
        required: false

      # Reporting options
      enable_reporting:
        type: boolean
        required: false
        default: false
      report_type:
        type: string
        required: false
      ref_branch:
        description: "Source branch name for webhook messages (e.g., 'master' or 'release-11.4')"
        type: string
        required: false
      pr_number:
        type: string
        required: false

      # Commit status configuration
      context_name:
        description: "GitHub commit status context name"
        type: string
        required: true

    outputs:
      passed:
        description: "Number of passed tests"
        value: ${{ jobs.report.outputs.passed }}
      failed:
        description: "Number of failed tests"
        value: ${{ jobs.report.outputs.failed }}
      report_url:
        description: "URL to test report on S3"
        value: ${{ jobs.report.outputs.report_url }}

    secrets:
      MM_LICENSE:
        required: false
      REPORT_WEBHOOK_URL:
        required: false
      AWS_ACCESS_KEY_ID:
        required: true
      AWS_SECRET_ACCESS_KEY:
        required: true

# Callers must grant at least these scopes on the job that uses this workflow
permissions:
  contents: read
  statuses: write

env:
  SERVER_IMAGE: "${{ inputs.server_image_repo }}/${{ inputs.server_edition == 'fips' && 'mattermost-enterprise-fips-edition' || inputs.server_edition == 'team' && 'mattermost-team-edition' || 'mattermost-enterprise-edition' }}:${{ inputs.server_image_tag }}"

jobs:
  update-initial-status:
    runs-on: ubuntu-24.04
    steps:
      - name: ci/set-initial-status
        uses: mattermost/actions/delivery/update-commit-status@f324ac89b05cc3511cb06e60642ac2fb829f0a63
        env:
          GITHUB_TOKEN: ${{ github.token }}
        with:
          repository_full_name: ${{ github.repository }}
          commit_sha: ${{ inputs.commit_sha }}
          context: ${{ inputs.context_name }}
          description: "tests running, image_tag:${{ inputs.server_image_tag }}${{ inputs.server_image_aliases && format(' ({0})', inputs.server_image_aliases) || '' }}"
          status: pending

  generate-test-variables:
    runs-on: ubuntu-24.04
    outputs:
      workers: "${{ steps.generate-workers.outputs.workers }}"
      start_time: "${{ steps.generate-workers.outputs.start_time }}"
    steps:
      - name: ci/generate-workers
        id: generate-workers
        env:
          INPUT_WORKERS: ${{ inputs.workers }}
        run: |
          echo "workers=$(jq -nc --argjson n "${INPUT_WORKERS}" '[range(1; $n + 1)]')" >> $GITHUB_OUTPUT
          echo "start_time=$(date +%s)" >> $GITHUB_OUTPUT

  run-tests:
    runs-on: ubuntu-24.04
    timeout-minutes: 60
    continue-on-error: true
    needs:
      - generate-test-variables
    if: needs.generate-test-variables.result == 'success'
    strategy:
      fail-fast: false
      matrix:
        worker_index: ${{ fromJSON(needs.generate-test-variables.outputs.workers) }}
    defaults:
      run:
        working-directory: e2e-tests
    env:
      SERVER: "${{ inputs.server }}"
      MM_LICENSE: "${{ secrets.MM_LICENSE }}"
      ENABLED_DOCKER_SERVICES: "${{ inputs.enabled_docker_services }}"
      TEST: playwright
      TEST_FILTER: "${{ inputs.test_filter }}"
      PW_SHARD: "${{ format('--shard={0}/{1}', matrix.worker_index, inputs.workers) }}"
      BRANCH: "${{ inputs.branch }}-${{ inputs.test_type }}"
      BUILD_ID: "${{ inputs.build_id }}"
      CI_BASE_URL: "${{ inputs.test_type }}-test-${{ matrix.worker_index }}"
    steps:
      - name: ci/checkout-actions
        # Sparse-checkout just .github/actions from the triggering ref (master)
        # so the composite action below is available before the full checkout
        # overwrites the workspace with inputs.commit_sha.
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2
        with:
          persist-credentials: false
          sparse-checkout: .github/actions
          sparse-checkout-cone-mode: true
      - name: ci/runner-prep-for-openldap
        uses: ./.github/actions/runner-prep-openldap
      - name: ci/checkout-repo
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2
        with:
          persist-credentials: false
          ref: ${{ inputs.commit_sha }}
          fetch-depth: 0

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/.github/workflows/e2e-tests-playwright.yml =====

---
name: E2E Tests - Playwright
on:
  workflow_call:
    inputs:
      commit_sha:
        type: string
        required: true
      enable_reporting:
        type: boolean
        required: false
        default: false
      server:
        type: string
        required: false
        default: onprem
      report_type:
        type: string
        required: false
      pr_number:
        type: string
        required: false
      server_image_tag:
        type: string
        required: false
        description: "Server image tag (e.g., master or short SHA)"
      server_edition:
        type: string
        required: false
        description: "Server edition: enterprise (default), fips, or team"
      server_image_repo:
        type: string
        required: false
        default: mattermostdevelopment
        description: "Docker registry: mattermostdevelopment (default) or mattermost"
      server_image_aliases:
        type: string
        required: false
        description: "Comma-separated alias tags for context name (e.g., 'release-11.4, release-11')"
      ref_branch:
        type: string
        required: false
        description: "Source branch name for webhook messages (e.g., 'master' or 'release-11.4')"
      should_run:
        type: string
        required: false
        default: "true"
        description: "Set to 'false' to skip tests and post a success status without running E2E"
    secrets:
      MM_LICENSE:
        required: false
      REPORT_WEBHOOK_URL:
        required: false
      AWS_ACCESS_KEY_ID:
        required: true
      AWS_SECRET_ACCESS_KEY:
        required: true

permissions: {}

jobs:
  generate-build-variables:
    runs-on: ubuntu-24.04
    outputs:
      branch: "${{ steps.build-vars.outputs.branch }}"
      build_id: "${{ steps.build-vars.outputs.build_id }}"
      server_image_tag: "${{ steps.build-vars.outputs.server_image_tag }}"
      server_image: "${{ steps.build-vars.outputs.server_image }}"
      context_suffix: "${{ steps.build-vars.outputs.context_suffix }}"
    steps:
      - name: ci/generate-build-variables
        id: build-vars
        env:
          COMMIT_SHA: ${{ inputs.commit_sha }}
          INPUT_REF_BRANCH: ${{ inputs.ref_branch }}
          INPUT_REPORT_TYPE: ${{ inputs.report_type }}
          INPUT_SERVER_EDITION: ${{ inputs.server_edition }}
          INPUT_SERVER_IMAGE_ALIASES: ${{ inputs.server_image_aliases }}
          INPUT_SERVER_IMAGE_REPO: ${{ inputs.server_image_repo }}
          INPUT_SERVER_IMAGE_TAG: ${{ inputs.server_image_tag }}
          PR_NUMBER: ${{ inputs.pr_number }}
          RUN_ATTEMPT: ${{ github.run_attempt }}
          RUN_ID: ${{ github.run_id }}
        run: |
          # Use provided server_image_tag or derive from commit SHA
          if [ -n "$INPUT_SERVER_IMAGE_TAG" ]; then
            SERVER_IMAGE_TAG="$INPUT_SERVER_IMAGE_TAG"
          else
            SERVER_IMAGE_TAG="${COMMIT_SHA::7}"
          fi

          # Validate server_image_tag format (alphanumeric, dots, hyphens, underscores)
          if ! [[ "$SERVER_IMAGE_TAG" =~ ^[a-zA-Z0-9._-]+$ ]]; then
            echo "::error::Invalid server_image_tag format: ${SERVER_IMAGE_TAG}"
            exit 1
          fi
          echo "server_image_tag=${SERVER_IMAGE_TAG}" >> $GITHUB_OUTPUT

          # Generate branch name. For master/release runs we pass the real
          # ref_branch through verbatim (`master`, `release-11.7`) so the
          # dashboard's /reports/{repo}/{branch} grouping aggregates every
          # build on that branch instead of treating each image tag as its
          # own "branch". PR and commit-only fallback paths keep their
          # synthetic prefix because there's no real branch to use.
          REF_BRANCH="${INPUT_REF_BRANCH}"
          if [ -n "$PR_NUMBER" ]; then
            echo "branch=pr-${PR_NUMBER}" >> $GITHUB_OUTPUT
          elif [ -n "$REF_BRANCH" ]; then
            echo "branch=${REF_BRANCH}" >> $GITHUB_OUTPUT
          else
            echo "branch=commit-${COMMIT_SHA::7}" >> $GITHUB_OUTPUT
          fi

          # Determine server image name
          EDITION="${INPUT_SERVER_EDITION}"
          REPO="${INPUT_SERVER_IMAGE_REPO}"
          REPO="${REPO:-mattermostdevelopment}"
          case "$EDITION" in
            fips) IMAGE_NAME="mattermost-enterprise-fips-edition" ;;
            team) IMAGE_NAME="mattermost-team-edition" ;;
            *)    IMAGE_NAME="mattermost-enterprise-edition" ;;
          esac
          SERVER_IMAGE="${REPO}/${IMAGE_NAME}:${SERVER_IMAGE_TAG}"
          echo "server_image=${SERVER_IMAGE}" >> $GITHUB_OUTPUT

          # Validate server_image_aliases format if provided
          ALIASES="${INPUT_SERVER_IMAGE_ALIASES}"
          if [ -n "$ALIASES" ] && ! [[ "$ALIASES" =~ ^[a-zA-Z0-9._,\ -]+$ ]]; then
            echo "::error::Invalid server_image_aliases format: ${ALIASES}"
            exit 1
          fi

          # Generate build ID
          if [ -n "$EDITION" ] && [ "$EDITION" != "enterprise" ]; then
            echo "build_id=${RUN_ID}_${RUN_ATTEMPT}-${SERVER_IMAGE_TAG}-playwright-onprem-${EDITION}" >> $GITHUB_OUTPUT
          else
            echo "build_id=${RUN_ID}_${RUN_ATTEMPT}-${SERVER_IMAGE_TAG}-playwright-onprem-ent" >> $GITHUB_OUTPUT
          fi

          # Generate context name suffix based on report type
          REPORT_TYPE="${INPUT_REPORT_TYPE}"
          case "$REPORT_TYPE" in
            MASTER) echo "context_suffix=/master" >> $GITHUB_OUTPUT ;;
            RELEASE) echo "context_suffix=/release" >> $GITHUB_OUTPUT ;;
            RELEASE_CUT) echo "context_suffix=/release-cut" >> $GITHUB_OUTPUT ;;
            *) echo "context_suffix=" >> $GITHUB_OUTPUT ;;
          esac

  skip:
    needs:
      - generate-build-variables
    if: inputs.should_run == 'false'
    runs-on: ubuntu-24.04
    permissions:
      contents: read
      statuses: write
    steps:
      - name: ci/post-skip-status
        env:
          COMMIT_SHA: ${{ inputs.commit_sha }}
          CONTEXT_NAME: "e2e-test/playwright-full/${{ inputs.server_edition || 'enterprise' }}${{ needs.generate-build-variables.outputs.context_suffix }}"
          GH_TOKEN: ${{ github.token }}
          GITHUB_REPOSITORY: ${{ github.repository }}
          GITHUB_RUN_ID: ${{ github.run_id }}
        run: |
          gh api "repos/${GITHUB_REPOSITORY}/statuses/${COMMIT_SHA}" \
            -f state=success \
            -f context="${CONTEXT_NAME}" \
            -f description="No E2E-relevant changes - skipped" \
            -f target_url="https://github.com/${GITHUB_REPOSITORY}/actions/runs/${GITHUB_RUN_ID}"
          echo "Posted success for ${CONTEXT_NAME}"

  # ── Routing fork ─────────────────────────────────────────────────────
  # vars.E2E_USE_TEST_IO_DISPATCH selects between v1 (legacy) and v2.
  # vars.E2E_USE_STAGING_TEST_IO_URL toggles v2's staging vs production
  # endpoint (default: staging).

  playwright-full-v1:
    needs:
      - generate-build-variables

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/.github/workflows/e2e-tests-verified-label.yml =====

---
name: "E2E Tests/verified"

on:
  pull_request:
    types: [labeled]

env:
  REPORT_WEBHOOK_URL: ${{ secrets.MM_E2E_REPORT_WEBHOOK_URL }}

permissions: {}

jobs:
  approve-e2e:
    permissions:
      contents: read
      pull-requests: read
      statuses: write
    if: github.event.label.name == 'E2E Tests/verified'
    runs-on: ubuntu-24.04
    steps:
      - name: ci/check-user-permission
        id: check-permission
        env:
          GH_TOKEN: ${{ github.token }}
          GITHUB_REPOSITORY: ${{ github.repository }}
          LABEL_AUTHOR: ${{ github.event.sender.login }}
        run: |
          # Check if user has write permission to the repository
          PERMISSION=$(gh api "repos/${GITHUB_REPOSITORY}/collaborators/${LABEL_AUTHOR}/permission" --jq '.permission' 2>/dev/null || echo "none")
          if [[ "$PERMISSION" != "admin" && "$PERMISSION" != "write" ]]; then
            echo "User ${LABEL_AUTHOR} doesn't have write permission to the repository (permission: ${PERMISSION})"
            exit 1
          fi
          echo "User ${LABEL_AUTHOR} has ${PERMISSION} permission to the repository"

      - name: ci/override-failed-statuses
        id: override
        env:
          GH_TOKEN: ${{ github.token }}
          COMMIT_SHA: ${{ github.event.pull_request.head.sha }}
          GITHUB_REPOSITORY: ${{ github.repository }}
        run: |
          # Only full tests can be overridden (smoke tests must pass)
          FULL_TEST_CONTEXTS=("e2e-test/playwright-full/enterprise" "e2e-test/cypress-full/enterprise" "e2e-test/playwright-full/fips" "e2e-test/cypress-full/fips")
          OVERRIDDEN=""
          WEBHOOK_DATA="[]"

          for CONTEXT_NAME in "${FULL_TEST_CONTEXTS[@]}"; do
            echo "Checking: $CONTEXT_NAME"

            # Get current status
            STATUS_JSON=$(gh api "repos/${GITHUB_REPOSITORY}/commits/${COMMIT_SHA}/statuses" \
              --jq "[.[] | select(.context == \"$CONTEXT_NAME\")] | first // empty")

            if [ -z "$STATUS_JSON" ]; then
              echo "  No status found, skipping"
              continue
            fi

            CURRENT_DESC=$(echo "$STATUS_JSON" | jq -r '.description // ""')
            CURRENT_URL=$(echo "$STATUS_JSON" | jq -r '.target_url // ""')
            CURRENT_STATE=$(echo "$STATUS_JSON" | jq -r '.state // ""')

            echo "  Current: $CURRENT_DESC ($CURRENT_STATE)"

            # Only override if status is failure
            if [ "$CURRENT_STATE" != "failure" ]; then
              echo "  Not failed, skipping"
              continue
            fi

          # Prefix existing description
          if [ -n "$CURRENT_DESC" ]; then
            NEW_MSG="(verified) ${CURRENT_DESC}"
          else
            NEW_MSG="(verified)"
          fi

            echo "  New: $NEW_MSG"

            # Update status via GitHub API
            gh api "repos/${GITHUB_REPOSITORY}/statuses/${COMMIT_SHA}" \
              -f state=success \
              -f context="$CONTEXT_NAME" \
              -f description="$NEW_MSG" \
              -f target_url="$CURRENT_URL"

            echo "  Updated to success"
            OVERRIDDEN="${OVERRIDDEN}- ${CONTEXT_NAME}\n"

            # Collect data for webhook
            TEST_TYPE="unknown"
            if [[ "$CONTEXT_NAME" == *"playwright"* ]]; then
              TEST_TYPE="playwright"
            elif [[ "$CONTEXT_NAME" == *"cypress"* ]]; then
              TEST_TYPE="cypress"
            fi

            WEBHOOK_DATA=$(echo "$WEBHOOK_DATA" | jq \
              --arg context "$CONTEXT_NAME" \
              --arg test_type "$TEST_TYPE" \
              --arg description "$CURRENT_DESC" \
              --arg report_url "$CURRENT_URL" \
              '. + [{context: $context, test_type: $test_type, description: $description, report_url: $report_url}]')
          done

          echo "overridden<<EOF" >> $GITHUB_OUTPUT
          echo -e "$OVERRIDDEN" >> $GITHUB_OUTPUT
          echo "EOF" >> $GITHUB_OUTPUT

          echo "webhook_data<<EOF" >> $GITHUB_OUTPUT
          echo "$WEBHOOK_DATA" >> $GITHUB_OUTPUT
          echo "EOF" >> $GITHUB_OUTPUT

      - name: ci/build-webhook-message
        if: env.REPORT_WEBHOOK_URL != '' && steps.override.outputs.overridden != ''
        id: webhook-message
        env:
          WEBHOOK_DATA: ${{ steps.override.outputs.webhook_data }}
        run: |
          MESSAGE_TEXT=""

          while IFS= read -r item; do
            [ -z "$item" ] && continue
            CONTEXT=$(echo "$item" | jq -r '.context')
            DESCRIPTION=$(echo "$item" | jq -r '.description')
            REPORT_URL=$(echo "$item" | jq -r '.report_url')

            MESSAGE_TEXT="${MESSAGE_TEXT}- **${CONTEXT}**: ${DESCRIPTION}, [view report](${REPORT_URL})\n"
          done < <(echo "$WEBHOOK_DATA" | jq -c '.[]')

          {
            echo "message_text<<EOF"
            echo -e "$MESSAGE_TEXT"
            echo "EOF"
          } >> $GITHUB_OUTPUT

      - name: ci/send-webhook-notification
        if: env.REPORT_WEBHOOK_URL != '' && steps.override.outputs.overridden != ''
        env:
          REPORT_WEBHOOK_URL: ${{ env.REPORT_WEBHOOK_URL }}
          MESSAGE_TEXT: ${{ steps.webhook-message.outputs.message_text }}
          PR_NUMBER: ${{ github.event.pull_request.number }}
          PR_URL: ${{ github.event.pull_request.html_url }}
          COMMIT_SHA: ${{ github.event.pull_request.head.sha }}
          SENDER: ${{ github.event.sender.login }}
        run: |
          PAYLOAD=$(cat <<EOF
          {
            "username": "E2E Test",
            "icon_url": "https://mattermost.com/wp-content/uploads/2022/02/icon_WS.png",
            "text": "**:white_check_mark: E2E Tests Verified**\n\nBy: \`@${SENDER}\` via \`E2E Tests/verified\` trigger-label\n:open-pull-request: [mattermost-pr-${PR_NUMBER}](${PR_URL}), commit: \`${COMMIT_SHA:0:7}\`\n\n${MESSAGE_TEXT}"
          }
          EOF
          )

          curl -X POST -H "Content-Type: application/json" -d "$PAYLOAD" "$REPORT_WEBHOOK_URL"

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/.github/workflows/i18n-ci-pr.yml =====

name: i18n CI PR
on:
  pull_request:
    paths:
      - "server/i18n/**"
      - "webapp/channels/src/i18n/**"
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

# This file just imports the template yml
# and runs it with concurrency. We have to do this in this way
# because the concurrency label cannot be added conditionally
# and it _always_ cancels pending workflows. So master CI builds
# always kept getting canceled.

permissions:
  contents: read

jobs:
  pr-ci:
    permissions:
      contents: read
    uses: ./.github/workflows/i18n-ci-template.yml

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/.github/workflows/i18n-ci-template.yml =====

# Base CI template which is called from i18n-ci-pr.yml

name: i18n CI Template
on:
  workflow_call:

permissions:
  contents: read

jobs:
  check-files:
    name: Check only English translation files changed
    runs-on: ubuntu-22.04
    if: github.event.pull_request.user.login != 'weblate' # Allow weblate to modify non-English
    steps:
      - name: Checkout code
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2
        with:
          persist-credentials: false

      - name: Get changed files
        id: changed-files
        uses: tj-actions/changed-files@22103cc46bda19c2b464ffe86db46df6922fd323 # v47.0.5
        with:
          files: |
            server/i18n/*.json
            webapp/channels/src/i18n/*.json
            !server/i18n/en.json
            !webapp/channels/src/i18n/en.json

      - name: Check changed files
        if: steps.changed-files.outputs.any_changed == 'true'
        run: |
          echo "::error title=Non-English i18n files changed::Only PRs from weblate should modify non-English translation files."
          exit 1

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/.github/workflows/migration-automation.yml =====

name: Migration Review & Release Notes
 
# Fires whenever a new .up.sql file lands on master.
# Runs the review-migration and migration-release-notes skills via Claude
# and writes the combined output to the job summary, visible directly in
# the Actions run UI — no GitHub App, PAT, or special permissions needed.
#
# Required secrets:
#   ANTHROPIC_API_KEY  — already a repo secret
 
on:
  push:
    branches: [master]
    paths:
      - 'server/channels/db/migrations/postgres/**.up.sql'
 
permissions:
  contents: read  # checkout only
 
# Only one run at a time per branch. If a new push to master arrives while
# a review is already in progress, the in-progress run is cancelled — the
# new run will cover the full push range anyway, avoiding duplicate API spend.
concurrency:
  group: migration-review-${{ github.ref }}
  cancel-in-progress: true
 
jobs:
  generate:
    name: Generate migration review & release notes
    runs-on: ubuntu-latest
 
    steps:
      - name: Checkout
        # actions/checkout v6.0.2
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd
        with:
          fetch-depth: 0             # full history — covers multi-commit pushes
          persist-credentials: false
 
      - name: Set up Python
        # actions/setup-python v6.2.0
        uses: actions/setup-python@a309ff8b426b58ec0e2a45f0f869d46889d02405
        with:
          python-version: '3.12'
 
      - name: Install dependencies
        # Pin anthropic to a known-good version for reproducible builds.
        # Bump intentionally when upgrading.
        run: pip install anthropic==0.105.2
 
      - name: Detect and process new migrations
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          PUSH_BASE_SHA: ${{ github.event.before }}
        run: |
          set -euo pipefail
 
          # Filter on .up.sql only: each migration is identified by its up
          # file; the paired .down.sql is read by the script if present.
          # Triggering on up files avoids duplicate runs when both files
          # arrive in the same push.
          MIGRATIONS_GLOB='server/channels/db/migrations/postgres/*.up.sql'
          mapfile -t files < <(
            git diff --name-only --diff-filter=A \
              "$PUSH_BASE_SHA" "$GITHUB_SHA" -- "$MIGRATIONS_GLOB"
          )
 
          if [ "${#files[@]}" -eq 0 ]; then
            echo "No new .up.sql files — skipping."
            exit 0
          fi
 
          echo "Found ${#files[@]} new migration(s):"
          printf '  %s\n' "${files[@]}"
 
          python .github/scripts/migration_automation.py "${files[@]}"

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/.github/workflows/mmctl-test-template.yml =====

name: mmctl CI
on:
  workflow_call:
    inputs:
      name:
        required: true
        type: string
      datasource:
        required: true
        type: string
      drivername:
        required: true
        type: string
      logsartifact:
        required: true
        type: string
      go-version:
        required: true
        type: string
      fips-enabled:
        required: false
        default: false
        type: boolean
    secrets:
      # Only if fips-enabled is true
      DOCKERHUB_USERNAME:
        required: false
      DOCKERHUB_TOKEN:
        required: false
      # Only master / release and there is report
      MM_E2E_ZEPHYR_API_KEY:
        required: false

permissions:
  contents: read
  actions: write

jobs:
  test:
    name: ${{ inputs.name }}
    runs-on: ubuntu-22.04
    env:
      COMPOSE_PROJECT_NAME: ghactions
      INPUT_DATASOURCE: ${{ inputs.datasource }}
      INPUT_FIPS_ENABLED: ${{ inputs.fips-enabled }}
      INPUT_GO_VERSION: ${{ inputs.go-version }}
      INPUT_LOGSARTIFACT: ${{ inputs.logsartifact }}
      INPUT_NAME: ${{ inputs.name }}
      INPUT_PR_NUMBER: ${{ github.event.pull_request.number }}
      REF_NAME: ${{ github.ref_name }}
    steps:
      - name: buildenv/docker-login
        # Only FIPS requires login for private build container. (Forks won't have credentials.)
        if: inputs.fips-enabled
        uses: docker/login-action@b45d80f862d83dbcd57f89517bcf500b2ab88fb2 # v4.0.0
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: Checkout mattermost project
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2
        with:
          persist-credentials: false
      - name: Setup BUILD_IMAGE
        id: build
        run: |
          if [[ "$INPUT_FIPS_ENABLED" == 'true' ]]; then
            echo "BUILD_IMAGE=mattermost/mattermost-build-server-fips:${INPUT_GO_VERSION}" >> "${GITHUB_OUTPUT}"
            echo "LOG_ARTIFACT_NAME=${INPUT_LOGSARTIFACT}-fips" >> "${GITHUB_OUTPUT}"
          else
            echo "BUILD_IMAGE=mattermost/mattermost-build-server:${INPUT_GO_VERSION}" >> "${GITHUB_OUTPUT}"
            echo "LOG_ARTIFACT_NAME=${INPUT_LOGSARTIFACT}" >> "${GITHUB_OUTPUT}"
          fi

      - name: Store required variables for publishing results
        run: |
          echo "$INPUT_NAME" > server/test-name
          echo "$INPUT_PR_NUMBER" > server/pr-number
      - name: Run docker compose
        env:
          POSTGRES_PASSWORD: ${{ inputs.fips-enabled && 'mostest-fips-test' || 'mostest' }}
        run: |
          cd server/build
          docker compose --ansi never run --rm start_dependencies
          cat ../tests/custom-schema-objectID.ldif | docker compose --ansi never exec -T openldap bash -c 'ldapadd -Y EXTERNAL -H ldapi:/// -w mostest || true';
          cat ../tests/custom-schema-cpa.ldif | docker compose --ansi never exec -T openldap bash -c 'ldapadd -Y EXTERNAL -H ldapi:/// -w mostest || true';
          cat ../tests/test-data.ldif | docker compose --ansi never exec -T openldap bash -c 'ldapadd -x -D "cn=admin,dc=mm,dc=test,dc=com" -w mostest';
          docker compose --ansi never exec -T minio sh -c 'mkdir -p /data/mattermost-test';
          docker compose --ansi never ps

      - name: Run mmctl Tests
        env:
          BUILD_IMAGE: ${{ steps.build.outputs.BUILD_IMAGE }}
        run: |
          if [[ "$REF_NAME" == 'master' ]]; then
            export TESTFLAGS="-timeout 90m -race"
          else
            export TESTFLAGS="-timeout 30m"
          fi
          docker run --net ghactions_mm-test \
            --ulimit nofile=8096:8096 \
            --env-file=server/build/dotenv/test.env \
            --env TEST_DATABASE_POSTGRESQL_DSN="$INPUT_DATASOURCE" \
            --env MM_SQLSETTINGS_DATASOURCE="$INPUT_DATASOURCE" \
            --env MMCTL_TESTFLAGS="$TESTFLAGS" \
            --env FIPS_ENABLED="$INPUT_FIPS_ENABLED" \
            -v $PWD:/mattermost \
            -w /mattermost/server \
            $BUILD_IMAGE \
            make test-mmctl BUILD_NUMBER=$GITHUB_HEAD_REF-$GITHUB_RUN_ID

      - name: Stop docker compose
        run: |
          cd server/build
          docker compose --ansi never stop

      - name: Save mmctl test report to Zephyr Scale
        if: ${{ always() && hashFiles('server/report.xml') != '' && github.event_name != 'pull_request' && (github.ref_name == 'master' || startsWith(github.ref_name, 'release-')) }}
        uses: ./.github/actions/save-junit-report-tms
        with:
          report-path: server/report.xml
          zephyr-api-key: ${{ secrets.MM_E2E_ZEPHYR_API_KEY }}
          build-image: ${{ steps.build.outputs.BUILD_IMAGE }}

      - name: Archive logs
        if: ${{ always() }}
        uses: actions/upload-artifact@bbbca2ddaa5d8feaa63e36b76fdaad77386f024f # v7.0.0
        with:
          name: ${{ steps.build.outputs.LOG_ARTIFACT_NAME }}
          path: |
            server/gotestsum.json
            server/report.xml
            server/test-name
            server/pr-number

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/.github/workflows/pr-test-analysis-override.yml =====

---
name: PR Test Analysis Override

on:
  issue_comment:
    types: [created]

concurrency:
  group: test-analyzer-${{ github.event.issue.number }}
  cancel-in-progress: false

permissions: {}

jobs:
  override:
    permissions:
      statuses: write
      pull-requests: read
      contents: read
      issues: write
    if: >-
      github.repository == 'mattermost/mattermost' &&
      github.event.issue.pull_request &&
      startsWith(github.event.comment.body, '/test-analysis-override') &&
      contains(fromJSON('["OWNER", "MEMBER", "COLLABORATOR"]'), github.event.comment.author_association)
    uses: mattermost/mattermost-test-automation-toolkit/.github/workflows/pr-test-analysis-override.yml@93d73f4f101e10dc03c7ed6b76b35eb5ff5babb7 # 2026-05-16
    with:
      pr_number: ${{ github.event.issue.number }}
      target_repo: mattermost/mattermost
      comment_body: ${{ github.event.comment.body }}
      comment_id: ${{ github.event.comment.id }}
      sender: ${{ github.event.comment.user.login }}
    secrets:
      GH_TOKEN: ${{ secrets.GH_TOKEN }}
      WEBHOOK_URL: ${{ secrets.WEBHOOK_URL_TEST_PR_ANALYSIS_HUB }}

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/.github/workflows/pr-test-analysis.yml =====

---
name: PR Test Analysis

on:
  pull_request:
    types: [opened, synchronize, reopened, ready_for_review]
    branches:
      - master
      - 'release-*'
  workflow_dispatch:
    inputs:
      pr_number:
        description: 'PR number to analyze'
        required: true
        type: number
      claude_model:
        description: 'Claude model to use (default: claude-sonnet-4-6)'
        required: false
        type: string

concurrency:
  group: test-analyzer-${{ github.event.pull_request.number || inputs.pr_number }}
  cancel-in-progress: true

permissions: {}

jobs:
  analyze:
    permissions:
      contents: read
      pull-requests: write
      statuses: write
      id-token: write
    # pull_request: skip drafts and forks (drafts are not ready for analysis;
    # fork runs do not receive this repo's Actions secrets).
    # workflow_dispatch: always allowed — runs in this repo with secrets, so you can pass a fork PR number manually.
    if: >-
      github.event_name == 'workflow_dispatch' ||
      (github.event.pull_request.draft == false &&
       github.event.pull_request.head.repo.full_name == 'mattermost/mattermost')
    uses: mattermost/mattermost-test-automation-toolkit/.github/workflows/pr-test-analysis.yml@93d73f4f101e10dc03c7ed6b76b35eb5ff5babb7 # 2026-05-16
    with:
      pr_number: ${{ github.event.pull_request.number || inputs.pr_number }}
      target_repo: mattermost/mattermost
      claude_model: ${{ inputs.claude_model || vars.CLAUDE_MODEL || 'claude-sonnet-4-6' }}
    secrets:
      GH_TOKEN: ${{ secrets.GH_TOKEN }}
      ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
      WEBHOOK_URL: ${{ secrets.WEBHOOK_URL_TEST_PR_ANALYSIS_HUB }}

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/.github/workflows/scorecards-analysis.yml =====

name: Scorecards supply-chain security
on:
  # Only the default branch is supported.
  branch_protection_rule:
  schedule:
    - cron: "44 6 * * *"

permissions: {}

jobs:
  analysis:
    name: Scorecard analysis
    if: github.repository_owner == 'mattermost'
    runs-on: ubuntu-24.04
    permissions:
      contents: read
      # Needed to upload the results to code-scanning dashboard.
      security-events: write
      # Needed to publish results and get a badge (see publish_results below).
      id-token: write

    steps:
      - name: "Checkout code"
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2
        with:
          persist-credentials: false

      - name: "Run analysis"
        uses: ossf/scorecard-action@4eaacf0543bb3f2c246792bd56e8cdeffafb205a # v2.4.3
        with:
          results_file: results.sarif
          results_format: sarif
          # (Optional) "write" PAT token. Uncomment the `repo_token` line below if:
          # - you want to enable the Branch-Protection check on a *public* repository, or
          # - you are installing Scorecard on a *private* repository
          # To create the PAT, follow the steps in https://github.com/ossf/scorecard-action#authentication-with-pat.
          repo_token: ${{ secrets.SCORECARD_READ_TOKEN }}

          # Public repositories:
          #   - Publish results to OpenSSF REST API for easy access by consumers
          #   - Allows the repository to include the Scorecard badge.
          #   - See https://github.com/ossf/scorecard-action#publishing-results.
          # For private repositories:
          #   - `publish_results` will always be set to `false`, regardless
          #     of the value entered here.
          publish_results: true

      # Upload the results as artifacts (optional). Commenting out will disable uploads of run results in SARIF
      # format to the repository Actions tab.
      - name: "Upload artifact"
        uses: actions/upload-artifact@bbbca2ddaa5d8feaa63e36b76fdaad77386f024f # v7.0.0
        with:
          name: SARIF file
          path: results.sarif
          retention-days: 5

      # Upload the results to GitHub's code scanning dashboard.
      - name: "Upload to code-scanning"
        uses: github/codeql-action/upload-sarif@0d579ffd059c29b07949a3cce3983f0780820c98 # v4.32.6
        with:
          sarif_file: results.sarif

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/.github/workflows/sentry.yaml =====

## Upload sentry results when Server CI master push completes (via workflow_call from server-ci.yml).
name: Sentry Upload

on:
  workflow_call:
    secrets:
      SENTRY_AUTH_TOKEN:
        required: true
      SENTRY_ORG:
        required: true
      SENTRY_PROJECT:
        required: true

permissions:
  contents: read

jobs:
  sentry:
    name: Send build info to sentry
    runs-on: ubuntu-22.04
    env:
      SENTRY_AUTH_TOKEN: ${{ secrets.SENTRY_AUTH_TOKEN }}
      SENTRY_ORG: ${{ secrets.SENTRY_ORG }}
      SENTRY_PROJECT: ${{ secrets.SENTRY_PROJECT }}
    steps:
      - name: cd/Checkout mattermost project
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2
        with:
          persist-credentials: false
      - name: cd/Create Sentry release
        uses: getsentry/action-release@dab6548b3c03c4717878099e43782cf5be654289 # v3.5.0


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/.github/workflows/server-ci-artifacts.yml =====

name: Server CI Artifacts

on:
  workflow_call:
    inputs:
      source-run-id:
        description: Server CI workflow run ID (for artifact download)
        required: true
        type: string
      source-event:
        description: github.event_name from the Server CI run
        required: true
        type: string
      head-sha:
        description: Commit SHA for status and published artifacts
        required: true
        type: string
      head-repository:
        description: head_repository.full_name from the Server CI run
        required: true
        type: string
    secrets:
      PR_BUILDS_BUCKET_AWS_ACCESS_KEY_ID:
        required: true
      PR_BUILDS_BUCKET_AWS_SECRET_ACCESS_KEY:
        required: true
      DOCKERHUB_DEV_TOKEN:
        required: true
      WIZ_DEVOPS_CLIENT_ID:
        required: true
      WIZ_DEVOPS_CLIENT_SECRET:
        required: true

env:
  COSIGN_VERSION: 2.2.0

permissions: {}

jobs:
  ## We only need the condition on the first job
  ## This will run only when a pull request is created with server changes
  update-initial-status:
    permissions:
      statuses: write
    if: github.repository_owner == 'mattermost' && inputs.source-event == 'pull_request' && inputs.head-repository == github.repository
    runs-on: ubuntu-22.04
    steps:
      - uses: mattermost/actions/delivery/update-commit-status@f324ac89b05cc3511cb06e60642ac2fb829f0a63
        env:
          GITHUB_TOKEN: ${{ github.token }}
        with:
          repository_full_name: ${{ github.repository }}
          commit_sha: ${{ inputs.head-sha }}
          context: Server CI/Artifacts Build
          description: Artifacts upload and build for mattermost team platform
          status: pending

  upload-artifacts:
    permissions:
      actions: read
      contents: read
    runs-on: ubuntu-22.04
    needs:
      - update-initial-status
    steps:
      - name: cd/configure-aws-credentials
        uses: aws-actions/configure-aws-credentials@8df5847569e6427dd6c4fb1cf565c83acfa8afa7 # v6.0.0
        with:
          aws-region: us-east-1
          aws-access-key-id: ${{ secrets.PR_BUILDS_BUCKET_AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.PR_BUILDS_BUCKET_AWS_SECRET_ACCESS_KEY }}

      - name: cd/download-artifacts-from-PR-workflow
        uses: actions/download-artifact@70fc10c6e5e1ce46ad2ea6f2b72d43f7d47b13c3 # v8.0.0
        with:
          run-id: ${{ inputs.source-run-id }}
          github-token: ${{ github.token }}
          name: server-dist-artifact
          path: server/dist

      - name: cd/generate-packages-file-list
        working-directory: ./server/dist
        run: |
          echo "PACKAGES_FILE_LIST<<EOF" >> "${GITHUB_ENV}"
          ls | grep -E "*.(tar.gz|zip)$" >> "${GITHUB_ENV}"
          echo "EOF" >> "${GITHUB_ENV}"

      - name: cd/upload-artifacts-to-s3
        env:
          WORKFLOW_RUN_HEAD_SHA: ${{ inputs.head-sha }}
        run: aws s3 sync server/dist/ "s3://pr-builds.mattermost.com/mattermost/commit/${WORKFLOW_RUN_HEAD_SHA}/" --cache-control no-cache --no-progress --acl public-read

      - name: cd/generate-summary
        env:
          WORKFLOW_RUN_HEAD_SHA: ${{ inputs.head-sha }}
        run: |
          echo "### Download links for Mattermost team package" >> "${GITHUB_STEP_SUMMARY}"
          echo " " >> "${GITHUB_STEP_SUMMARY}"
          echo "Mattermost Repo SHA: \`${WORKFLOW_RUN_HEAD_SHA}\`" >> "${GITHUB_STEP_SUMMARY}"
          echo "|Download Link|" >> "${GITHUB_STEP_SUMMARY}"
          echo "| --- |" >> "${GITHUB_STEP_SUMMARY}"
          for package in ${PACKAGES_FILE_LIST}
            do
              echo "|[${package}](https://pr-builds.mattermost.com/mattermost/commit/${WORKFLOW_RUN_HEAD_SHA}/${package})|" >> "${GITHUB_STEP_SUMMARY}"
          done

  build-docker:
    permissions:
      actions: read
      contents: read
    runs-on: ubuntu-22.04
    needs:
      - upload-artifacts
    outputs:
      TAG: ${{ steps.set_tag.outputs.TAG }}
    steps:
      - name: cd/docker-login
        uses: docker/login-action@b45d80f862d83dbcd57f89517bcf500b2ab88fb2 # v4.0.0
        with:
          username: mattermostdev
          password: ${{ secrets.DOCKERHUB_DEV_TOKEN }}

      - name: cd/checkout-build-files
        if: inputs.head-repository != github.repository
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2
        with:
          persist-credentials: false
          sparse-checkout: server/build/
          sparse-checkout-cone-mode: true

      - name: cd/download-build-artifact
        if: inputs.head-repository == github.repository
        uses: actions/download-artifact@70fc10c6e5e1ce46ad2ea6f2b72d43f7d47b13c3 # v8.0.0
        with:
          run-id: ${{ inputs.source-run-id }}
          github-token: ${{ github.token }}
          name: server-build-artifact
          path: server/build/

      - name: cd/setup-cosign
        uses: sigstore/cosign-installer@faadad0cce49287aee09b3a48701e75088a2c6ad # v4.0.0
        with:
          cosign-release: v${{ env.COSIGN_VERSION }}

      - name: cd/setup-docker-buildx
        uses: docker/setup-buildx-action@4d04d5d9486b7bd6fa91e7baf45bbb4f8b9deedd # v4.0.0

      - name: cd/set-docker-tag
        id: set_tag
        env:
          WORKFLOW_RUN_HEAD_SHA: ${{ inputs.head-sha }}
        run: |
          echo "TAG=$(echo "${WORKFLOW_RUN_HEAD_SHA}" | cut -c1-7)" >> $GITHUB_OUTPUT

      - name: cd/docker-build-and-push
        id: docker
        env:
          MM_PACKAGE: https://pr-builds.mattermost.com/mattermost/commit/${{ inputs.head-sha }}/mattermost-team-linux-amd64.tar.gz
          TAG: ${{ steps.set_tag.outputs.TAG }}
        run: |
          cd server/build
          docker buildx build --no-cache --platform linux/amd64 --push --build-arg MM_PACKAGE=${MM_PACKAGE} -t mattermostdevelopment/mm-te-test:${TAG} -t mattermostdevelopment/mattermost-team-edition:${TAG} .
          echo "DOCKERHUB_IMAGE_DIGEST=$(cosign triangulate mattermostdevelopment/mattermost-team-edition:${TAG} | cut -d: -f2 | sed 's/\.sig$//' | tr '-' ':')" >> "${GITHUB_OUTPUT}"

      - name: cd/generate-summary
        env:
          DOCKERHUB_IMAGE_DIGEST: ${{ steps.docker.outputs.DOCKERHUB_IMAGE_DIGEST }}
          TAG: ${{ steps.set_tag.outputs.TAG }}
          WORKFLOW_RUN_HEAD_SHA: ${{ inputs.head-sha }}
        run: |
          echo "### Docker Image for Mattermost team package" >> "${GITHUB_STEP_SUMMARY}"
          echo " " >> "${GITHUB_STEP_SUMMARY}"
          echo "Mattermost Repo SHA: \`${WORKFLOW_RUN_HEAD_SHA}\`" >> "${GITHUB_STEP_SUMMARY}"
          echo " " >> "${GITHUB_STEP_SUMMARY}"
          echo "Docker Image: \`mattermostdevelopment/mattermost-team-edition:${TAG}\`" >> "${GITHUB_STEP_SUMMARY}"
          echo "Image Digest: \`${DOCKERHUB_IMAGE_DIGEST}\`" >> "${GITHUB_STEP_SUMMARY}"
          echo "Secure Image: \`mattermostdevelopment/mattermost-team-edition:${TAG}@${DOCKERHUB_IMAGE_DIGEST}\`" >> "${GITHUB_STEP_SUMMARY}"

  scan-docker-image:
    runs-on: ubuntu-22.04

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/.github/workflows/server-ci-nightly-race.yml =====

# Nightly race detector run.
#
# Runs all server tests with Go's -race detector enabled to catch
# data races. Runs sequentially (fullyparallel: false) on a 2-core
# runner to minimize resource usage — race detection adds significant
# overhead that makes parallel execution impractical.
#
# Schedule: Nightly at ~2am ET (6am UTC)
#
# Previously, -race was implicitly bundled with the binary params job
# via the fullyparallel=false → RACE_MODE coupling. This decouples
# the two concerns: binary params tests the Postgres driver encoding;
# this workflow tests for data races.
name: Server CI Nightly Race
on:
  schedule:
    - cron: "0 6 * * *" # Daily 6am UTC (~2am ET)
  workflow_dispatch: # Manual trigger for on-demand race detection

permissions:
  contents: read

jobs:
  go:
    name: Compute Go Version
    runs-on: ubuntu-22.04
    outputs:
      version: ${{ steps.calculate.outputs.GO_VERSION }}
    steps:
      - name: Checkout mattermost project
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2
        with:
          persist-credentials: false
      - name: Calculate version
        id: calculate
        working-directory: server/
        run: echo GO_VERSION=$(cat .go-version) >> "${GITHUB_OUTPUT}"

  test-race:
    name: Race Detector
    needs: go
    permissions:
      contents: read
      actions: write
    uses: ./.github/workflows/server-test-template.yml
    with:
      name: Race Detector
      datasource: postgres://mmuser:mostest@postgres:5432/mattermost_test?sslmode=disable&connect_timeout=10
      drivername: postgres
      logsartifact: race-detector-server-test-logs
      go-version: ${{ needs.go.outputs.version }}
      fips-enabled: false
      fullyparallel: false
      race-enabled: true
      runner: ubuntu-22.04
      allow-failure: true

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/.github/workflows/server-ci-report.yml =====

# Server CI Report is invoked via workflow_call from server-ci.yml after test jobs finish.
name: Server CI Report

on:
  workflow_call:
    inputs:
      source-run-id:
        description: Server CI workflow run ID (for artifact download)
        required: true
        type: string
      source-event:
        description: github.event_name from the Server CI run
        required: true
        type: string
      head-commit-id:
        description: Commit ID for junit report annotations
        required: true
        type: string
      head-repository:
        description: head_repository.full_name from the Server CI run
        required: true
        type: string
      workflow-url:
        description: HTML URL of the Server CI workflow run
        required: true
        type: string
    secrets:
      WEBHOOK_URL_FLAKY_TEST:
        required: false
      WEBHOOK_AUTH_TOKEN_FLAKY_TEST:
        required: false
      WEBHOOK_URL_FLAKY_TEST_MM:
        required: false

permissions: {}

jobs:
  generate-report-matrix:
    permissions:
      actions: read
      contents: read
    if: inputs.head-repository == github.repository
    runs-on: ubuntu-22.04
    outputs:
      REPORT_MATRIX: ${{ steps.report.outputs.REPORT_MATRIX }}
    steps:
      - name: report/download-artifacts-from-PR-workflow
        uses: actions/download-artifact@70fc10c6e5e1ce46ad2ea6f2b72d43f7d47b13c3 # v8.0.0
        with:
          run-id: ${{ inputs.source-run-id }}
          github-token: ${{ github.token }}
          pattern: "*-test-logs"
          path: reports

      - name: report/validate-and-prepare-data
        id: validate
        run: |
          # Create validated data file
          > /tmp/validated-tests.json

          find "reports" -type f -name "test-name" | while read -r test_file; do
            folder=$(basename "$(dirname "$test_file")")
            test_name_raw=$(cat "$test_file" | tr -d '\n\r')

            # Validate test name: allow alphanumeric, spaces, hyphens, underscores, parentheses, and dots
            if [[ "$test_name_raw" =~ ^[a-zA-Z0-9\ \(\)_.-]+$ ]] && [[ ${#test_name_raw} -le 100 ]]; then
              # Use jq to safely escape the test name as JSON
              test_name_escaped=$(echo -n "$test_name_raw" | jq -R .)
              echo "{\"artifact\": \"$folder\", \"name\": $test_name_escaped}" >> /tmp/validated-tests.json
            else
              echo "Warning: Skipping invalid test name in $test_file: '$test_name_raw'" >&2
            fi
          done

          # Verify we have at least some valid tests
          if [[ ! -s /tmp/validated-tests.json ]]; then
            echo "Error: No valid test names found" >&2
            exit 1
          fi

      - name: report/generate-report-matrix
        id: report
        run: |
          # Convert validated JSON objects to matrix format
          jq -s '{ "test": . }' /tmp/validated-tests.json | tee /tmp/report-matrix
          echo REPORT_MATRIX=$(cat /tmp/report-matrix | jq --compact-output --monochrome-output) >> ${GITHUB_OUTPUT}

  publish-report:
    runs-on: ubuntu-22.04
    name: Publish Report ${{ matrix.test.name }}
    needs:
      - generate-report-matrix
    permissions:
      actions: read
      pull-requests: write
      checks: write
    strategy:
      matrix: ${{ fromJson(needs.generate-report-matrix.outputs.REPORT_MATRIX) }}
    steps:
      - name: report/download-artifacts-from-PR-workflow
        uses: actions/download-artifact@70fc10c6e5e1ce46ad2ea6f2b72d43f7d47b13c3 # v8.0.0
        with:
          run-id: ${{ inputs.source-run-id }}
          github-token: ${{ github.token }}
          name: ${{ matrix.test.artifact }}
          path: ${{ matrix.test.artifact }}
      - name: report/fetch-pr-number
        if: inputs.source-event == 'pull_request'
        id: incoming-pr
        env:
          ARTIFACT: "${{ matrix.test.artifact }}"
        run: |
          if [[ -f "$ARTIFACT/pr-number" ]]; then
            pr_number=$(cat "$ARTIFACT/pr-number" | tr -d '\n\r' | grep -E '^[0-9]+$')
            if [[ -n "$pr_number" ]] && [[ ${#pr_number} -le 10 ]]; then
              echo "NUMBER=$pr_number" >> ${GITHUB_OUTPUT}
            else
              echo "Invalid PR number format" >&2
              exit 1
            fi
          else
            echo "PR number file not found" >&2
            exit 1
          fi
      - name: Publish test report
        id: report
        uses: mikepenz/action-junit-report@49b2ca06f62aa7ef83ae6769a2179271e160d8e4 # v6.3.1
        with:
          report_paths: ${{ matrix.test.artifact }}/report.xml
          check_name: ${{ matrix.test.name }} (Results)
          job_name: ${{ matrix.test.name }}
          commit: ${{ inputs.head-commit-id }}
          require_tests: true
          check_retries: true
          flaky_summary: true
          include_passed: true
          check_annotations: true

      - name: Report retried tests to Mattermost channel (pull request)
        if: >-
          steps.report.outputs.flaky_summary != '<table><tr><th>Test</th><th>Retries</th></tr></table>'
          && steps.report.outputs.failed == '0'
          && inputs.source-event == 'pull_request'
          && env.WEBHOOK_URL_FLAKY_TEST_MM != ''
        continue-on-error: true
        env:
          WEBHOOK_URL_FLAKY_TEST_MM: ${{ secrets.WEBHOOK_URL_FLAKY_TEST_MM }}
          FLAKY_SUMMARY: ${{ steps.report.outputs.flaky_summary }}
          PR_NUMBER: ${{ steps.incoming-pr.outputs.NUMBER }}
          TEST_NAME: ${{ matrix.test.name }}
          REPO: ${{ github.repository }}
          WORKFLOW_RUN_HTML_URL: ${{ inputs.workflow-url }}
          SERVER_URL: ${{ github.server_url }}
        run: |
          PR_URL="${SERVER_URL}/${REPO}/pull/${PR_NUMBER}"

          # Convert the HTML <table> flaky summary into a Mattermost markdown table.
          # The summary contains a header row plus, per suite, a section-header row
          # (<td colspan="2"><strong>...</strong></td>) that markdown tables cannot
          # represent. Parse the HTML, keep only rows matching the header's column
          # count (dropping section-header rows), and emit a flat markdown table.
          TABLE_MD=$(python3 - <<'PY'
          import os, html
          from html.parser import HTMLParser


          class FlakyTableParser(HTMLParser):
              def __init__(self):
                  super().__init__()
                  self.rows = []
                  self.row = None
                  self.cell = None

              def handle_starttag(self, tag, attrs):
                  if tag == "tr":
                      self.row = []
                  elif tag in ("td", "th"):
                      self.cell = []

              def handle_endtag(self, tag):

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/.github/workflows/server-ci-weekly.yml =====

# Weekly Server CI jobs that don't need to run on every push/PR.
# These are important for compliance and compatibility but have low
# regression rates, so running them weekly saves significant 8-core
# runner capacity (9 fewer concurrent 8-core jobs per master push).
#
# Schedule: Monday ~1am ET (5am UTC)
#
# Jobs moved here from server-ci.yml:
# - Postgres with binary parameters (1x 8-core)
# - Postgres FIPS unsharded (1x 8-core) — sharded runs stay in server-ci.yml for PR iteration
# - mmctl FIPS tests (1x 8-core)
name: Server CI Weekly
on:
  schedule:
    - cron: "0 5 * * 1" # Monday 5am UTC (~1am ET)
  push:
    branches:
      - 'release-*'
  workflow_dispatch: # Allow manual trigger for urgent FIPS/binary verification

permissions:
  contents: read

jobs:
  go:
    name: Compute Go Version
    runs-on: ubuntu-22.04
    outputs:
      version: ${{ steps.calculate.outputs.GO_VERSION }}
    steps:
      - name: Checkout mattermost project
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2
        with:
          persist-credentials: false
      - name: Calculate version
        id: calculate
        working-directory: server/
        run: echo GO_VERSION=$(cat .go-version) >> "${GITHUB_OUTPUT}"

  test-postgres-binary:
    name: Postgres with binary parameters
    needs: go
    permissions:
      contents: read
      actions: write
    uses: ./.github/workflows/server-test-template.yml
    with:
      name: Postgres with binary parameters
      datasource: postgres://mmuser:mostest@postgres:5432/mattermost_test?sslmode=disable&connect_timeout=10&binary_parameters=yes
      drivername: postgres
      logsartifact: postgres-binary-server-test-logs
      go-version: ${{ needs.go.outputs.version }}
      fips-enabled: false
      # Unsharded run on a single 8-core runner: fullyparallel=true causes
      # resource exhaustion (too many server instances, WebSocket hubs, and
      # DB connections) and crashes the hosted runner. See #35995.
      fullyparallel: false

  test-postgres-normal-fips:
    name: Postgres FIPS
    needs: go
    permissions:
      contents: read
      actions: write
    uses: ./.github/workflows/server-test-template.yml
    secrets:
      DOCKERHUB_USERNAME: ${{ secrets.DOCKERHUB_USERNAME }}
      DOCKERHUB_TOKEN: ${{ secrets.DOCKERHUB_TOKEN }}
    with:
      name: Postgres FIPS
      datasource: postgres://mmuser:mostest-fips-test@postgres:5432/mattermost_test?sslmode=disable&connect_timeout=10
      drivername: postgres
      logsartifact: postgres-server-fips-test-logs
      go-version: ${{ needs.go.outputs.version }}
      fips-enabled: true
      # Unsharded run on a single 8-core runner: see note on test-postgres-binary.
      fullyparallel: false

  test-mmctl-fips:
    name: Run mmctl tests (FIPS)
    needs: go
    permissions:
      contents: read
      actions: write
    uses: ./.github/workflows/mmctl-test-template.yml
    secrets:
      DOCKERHUB_USERNAME: ${{ secrets.DOCKERHUB_USERNAME }}
      DOCKERHUB_TOKEN: ${{ secrets.DOCKERHUB_TOKEN }}
      MM_E2E_ZEPHYR_API_KEY: ${{ secrets.MM_E2E_ZEPHYR_API_KEY }}
    with:
      name: mmctl
      datasource: postgres://mmuser:mostest-fips-test@postgres:5432/mattermost_test?sslmode=disable&connect_timeout=10
      drivername: postgres
      logsartifact: mmctl-fips-test-logs
      go-version: ${{ needs.go.outputs.version }}
      fips-enabled: true

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/.github/workflows/server-ci.yml =====

# NOTE: This workflow name is referenced by other workflows:
# - server-ci-artifacts.yml
# - server-ci-report.yml
# - sentry.yaml
# If you rename this workflow, be sure to update those workflows as well.
name: Server CI
on:
  workflow_dispatch:  # Allow manual/API triggering for linked plugin CI
  push:
    branches:
      - master
      - release-*
  pull_request:
    paths:
      - "server/**"
      - ".github/workflows/server-ci.yml"
      - ".github/workflows/server-test-template.yml"
      - ".github/workflows/server-test-merge-template.yml"
      - ".github/workflows/mmctl-test-template.yml"
      - "!server/build/Dockerfile.buildenv"
      - "!server/build/Dockerfile.buildenv-fips"
      - "tools/mattermost-govet/**"
      - "!server/**/*.md"
      - "!server/NOTICE.txt"
      - "!server/CHANGELOG.md"

concurrency:
  group: ${{ github.event_name == 'pull_request' && format('{0}-{1}', github.workflow, github.ref) || github.run_id }}
  cancel-in-progress: ${{ github.event_name == 'pull_request' }}

permissions:
  contents: read

jobs:
  go:
    name: Compute Go Version
    runs-on: ubuntu-22.04
    permissions:
      contents: read
      pull-requests: read
    outputs:
      version: ${{ steps.calculate.outputs.GO_VERSION }}
      gomod-changed: ${{ steps.changed-files.outputs.any_changed }}
    steps:
      - name: Checkout mattermost project
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2
        with:
          persist-credentials: false
      - name: Calculate version
        id: calculate
        working-directory: server/
        run: echo GO_VERSION=$(cat .go-version) >> "${GITHUB_OUTPUT}"
      - name: Check for go.mod changes
        id: changed-files
        uses: tj-actions/changed-files@22103cc46bda19c2b464ffe86db46df6922fd323 # v47.0.5
        with:
          files: |
            **/go.mod
  check-mocks:
    name: Check mocks
    needs: go
    runs-on: ubuntu-22.04
    container: mattermost/mattermost-build-server:${{ needs.go.outputs.version }}
    defaults:
      run:
        working-directory: server
    steps:
      - name: Checkout mattermost project
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2
        with:
          persist-credentials: false
      - name: Run setup-go-work
        run: make setup-go-work
      - name: Generate mocks
        run: make mocks
      - name: Check mocks
        run: |
          git config --global --add safe.directory "$GITHUB_WORKSPACE"
          if [ -n "$(git status --porcelain)" ]; then
            echo "Please update the mocks using 'make mocks'"
            git diff
            exit 1
          fi
  check-go-mod-tidy:
    name: Check go mod tidy
    needs: go
    runs-on: ubuntu-22.04
    container: mattermost/mattermost-build-server:${{ needs.go.outputs.version }}
    defaults:
      run:
        working-directory: server
    steps:
      - name: Checkout mattermost project
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2
        with:
          persist-credentials: false
      - name: Run setup-go-work
        run: make setup-go-work
      - name: Run go mod tidy
        run: make modules-tidy
      - name: Check modules
        run: |
          git config --global --add safe.directory "$GITHUB_WORKSPACE"
          if [ -n "$(git status --porcelain)" ]; then
            echo "Please tidy up the Go modules using make modules-tidy"
            git diff
            exit 1
          fi
  check-go-fix:
    name: Check go fix
    needs: go
    runs-on: ubuntu-22.04
    container: mattermost/mattermost-build-server:${{ needs.go.outputs.version }}
    defaults:
      run:
        working-directory: server
    steps:
      - name: Checkout mattermost project
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2
        with:
          persist-credentials: false
      - name: Run setup-go-work
        run: make setup-go-work
      - name: Run go fix
        run: go fix ./...
      - name: Check go fix
        run: |
          git config --global --add safe.directory "$GITHUB_WORKSPACE"
          if [ -n "$(git status --porcelain)" ]; then
            echo "Please run 'go fix ./...' and commit the changes"
            git diff
            exit 1
          fi
  check-style:
    name: check-style
    needs: go
    runs-on: ubuntu-22.04
    container: mattermost/mattermost-build-server:${{ needs.go.outputs.version }}
    defaults:
      run:
        working-directory: server
    steps:
      - name: Checkout mattermost project
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2
        with:
          persist-credentials: false
      - name: Run setup-go-work
        run: make setup-go-work
      - name: Run golangci
        run: make check-style
  check-gen-serialized:
    name: Check serialization methods for hot structs
    needs: go
    runs-on: ubuntu-22.04
    container: mattermost/mattermost-build-server:${{ needs.go.outputs.version }}
    defaults:
      run:
        working-directory: server
    steps:
      - name: Checkout mattermost project
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2
        with:
          persist-credentials: false
      - name: Run setup-go-work
        run: make setup-go-work
      - name: Run make-gen-serialized
        run: make gen-serialized
      - name: Check serialized
        run: |
          git config --global --add safe.directory "$GITHUB_WORKSPACE"
          if [ -n "$(git status --porcelain)" ]; then
            echo "Please update the serialized files using 'make gen-serialized'"
            git diff
            exit 1
          fi
  check-mattermost-vet-api:
    name: Vet API
    needs: go
    runs-on: ubuntu-22.04
    container: mattermost/mattermost-build-server:${{ needs.go.outputs.version }}

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/.github/workflows/server-test-merge-template.yml =====

name: Server Test Merge Template

on:
  workflow_call:
    inputs:
      artifact-pattern:
        description: "Glob pattern to download shard artifacts"
        required: true
        type: string
      artifact-name:
        description: "Name for the merged output artifact"
        required: true
        type: string
      save-timing-cache:
        description: "Whether to save timing cache for future shard balancing"
        required: false
        type: boolean
        default: false
      all-shards-passed:
        description: "Whether every upstream shard succeeded. Used to gate the timing-cache save so a single shard failure doesn't poison the cache with missing-package data."
        required: false
        type: boolean
        default: false

permissions:
  contents: read
  actions: write

jobs:
  merge:
    name: Merge
    if: always()
    runs-on: ubuntu-22.04
    steps:
      - name: Download all shard artifacts
        uses: actions/download-artifact@70fc10c6e5e1ce46ad2ea6f2b72d43f7d47b13c3 # v8.0.0
        with:
          pattern: ${{ inputs.artifact-pattern }}
          path: shards

      - name: Merge JUnit reports
        run: |
          python3 -c "
          import glob, sys
          from xml.etree import ElementTree as ET

          root = ET.Element('testsuites')
          for path in sorted(glob.glob('shards/*/report.xml')):
              tree = ET.parse(path)
              r = tree.getroot()
              if r.tag == 'testsuites':
                  root.extend(r)
              else:
                  root.append(r)

          ET.ElementTree(root).write('merged-report.xml', xml_declaration=True, encoding='UTF-8')
          "

      - name: Prepare merged artifact
        run: |
          mkdir -p merged
          cp merged-report.xml merged/report.xml
          for dir in shards/*/; do
            if [[ -f "${dir}test-name" ]]; then
              cp "${dir}test-name" merged/test-name
              cp "${dir}pr-number" merged/pr-number
              break
            fi
          done

      - name: Upload merged test logs
        uses: actions/upload-artifact@bbbca2ddaa5d8feaa63e36b76fdaad77386f024f # v7.0.0
        with:
          name: ${{ inputs.artifact-name }}
          path: merged/

      - name: Prepare timing cache
        if: inputs.save-timing-cache
        id: timing-prep
        run: |
          mkdir -p server
          if [[ -f merged-report.xml && $(stat -c%s merged-report.xml) -gt 1024 ]]; then
            cp merged-report.xml server/prev-report.xml
            cat shards/*/gotestsum.json > server/prev-gotestsum.json 2>/dev/null || true
            echo "has_timing=true" >> "$GITHUB_OUTPUT"
          else
            echo "Skipping timing cache — merged report too small or missing"
            echo "has_timing=false" >> "$GITHUB_OUTPUT"
          fi

      # Only save when every upstream shard succeeded. If even one shard
      # failed/was killed, its gotestsum.json is missing and the merged report
      # has no timings for that shard's packages — saving that would poison
      # future shard splits (missing packages default to 1ms, all bin-pack
      # onto the lightest shard, overloading it and repeating the failure).
      - name: Save test timing cache
        if: inputs.save-timing-cache && inputs.all-shards-passed && steps.timing-prep.outputs.has_timing == 'true' && github.ref_name == github.event.repository.default_branch
        uses: actions/cache/save@5a3ec84eff668545956fd18022155c47e93e2684 # v4.2.3
        with:
          path: |
            server/prev-report.xml
            server/prev-gotestsum.json
          # The v2 prefix matches the v2 restore prefix in server-test-template.yml.
          key: server-test-timing-v2-master-${{ github.run_id }}

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/.github/workflows/server-test-template.yml =====

name: Server Test Template
on:
  workflow_call:
    inputs:
      name:
        required: true
        type: string
      datasource:
        required: true
        type: string
      drivername:
        required: true
        type: string
      logsartifact:
        required: true
        type: string
      fullyparallel:
        required: false
        type: boolean
        default: true
      allow-failure:
        required: false
        type: boolean
        default: false
      enablecoverage:
        required: false
        type: boolean
        default: false
      go-version:
        required: true
        type: string
      fips-enabled:
        required: false
        default: false
        type: boolean
      elasticsearch-version:
        required: false
        type: string
        default: "9.0.0"
      opensearch-version:
        required: false
        type: string
        default: "3.0.0"
      test-target:
        required: false
        type: string
        default: "test-server"
      # -- Test sharding inputs (leave defaults for non-sharded callers) --
      shard-index:
        required: false
        type: number
        default: -1 # -1 = no sharding; run all tests
      shard-total:
        required: false
        type: number
        default: 1
      runner:
        description: "GitHub-hosted runner label (default: ubuntu-latest-8-cores)"
        required: false
        type: string
        default: "ubuntu-latest-8-cores"
      race-enabled:
        description: "Run tests with Go race detector (-race)"
        required: false
        type: boolean
        default: false
    secrets:
      # Only if enablecoverage is true
      CODECOV_TOKEN:
        required: false
      # Only if fips-enabled is true
      DOCKERHUB_USERNAME:
        required: false
      DOCKERHUB_TOKEN:
        required: false

permissions:
  contents: read
  actions: write

jobs:
  test:
    name: ${{ inputs.name }}
    runs-on: ${{ inputs.runner }}
    continue-on-error: ${{ inputs.allow-failure }} # Used to avoid blocking PRs in case of flakiness
    env:
      COMPOSE_PROJECT_NAME: ghactions
      INPUT_DATASOURCE: ${{ inputs.datasource }}
      INPUT_DRIVERNAME: ${{ inputs.drivername }}
      INPUT_ENABLECOVERAGE: ${{ inputs.enablecoverage }}
      INPUT_FIPS_ENABLED: ${{ inputs.fips-enabled }}
      INPUT_FULLYPARALLEL: ${{ inputs.fullyparallel }}
      INPUT_GO_VERSION: ${{ inputs.go-version }}
      INPUT_LOGSARTIFACT: ${{ inputs.logsartifact }}
      INPUT_NAME: ${{ inputs.name }}
      INPUT_PR_NUMBER: ${{ github.event.pull_request.number }}
      INPUT_RACE_ENABLED: ${{ inputs.race-enabled }}
      INPUT_SHARD_TOTAL: ${{ inputs.shard-total }}
      INPUT_TEST_TARGET: ${{ inputs.test-target }}
    steps:
      - name: buildenv/docker-login
        # Only FIPS requires login for private build container. (Forks won't have credentials.)
        if: inputs.fips-enabled
        uses: docker/login-action@b45d80f862d83dbcd57f89517bcf500b2ab88fb2 # v4.0.0
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: Checkout mattermost project
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2
        with:
          persist-credentials: false

      - name: Restore test timing data
        if: inputs.shard-total > 1
        id: timing-cache
        uses: actions/cache/restore@5a3ec84eff668545956fd18022155c47e93e2684 # v4.2.3
        with:
          path: |
            server/prev-report.xml
            server/prev-gotestsum.json
          # Always restore from master — timing is only saved on the default
          # branch and is stable enough for shard balancing.
          # NOTE: the v2 prefix invalidates pre-existing caches that were
          # poisoned by shard failures (a killed shard loses its gotestsum.json,
          # so the merged report was missing those packages' timings; on the
          # next run they all defaulted to 1ms and bin-packed onto the lightest
          # shard, overloading it and perpetuating the cycle). See also the
          # all-shards-passed guard in server-test-merge-template.yml.
          key: server-test-timing-v2-master
          restore-keys: |
            server-test-timing-v2-

      - name: Setup BUILD_IMAGE
        id: build
        run: |
          if [[ "$INPUT_FIPS_ENABLED" == 'true' ]]; then
            echo "BUILD_IMAGE=mattermost/mattermost-build-server-fips:${INPUT_GO_VERSION}" >> "${GITHUB_OUTPUT}"
            echo "LOG_ARTIFACT_NAME=${INPUT_LOGSARTIFACT}-fips" >> "${GITHUB_OUTPUT}"
          else
            echo "BUILD_IMAGE=mattermost/mattermost-build-server:${INPUT_GO_VERSION}" >> "${GITHUB_OUTPUT}"
            echo "LOG_ARTIFACT_NAME=${INPUT_LOGSARTIFACT}" >> "${GITHUB_OUTPUT}"
          fi

      - name: Store required variables for publishing results
        run: |
          echo "$INPUT_NAME" > server/test-name
          echo "$INPUT_PR_NUMBER" > server/pr-number

      - name: Run docker compose
        env:
          ELASTICSEARCH_VERSION: ${{ inputs.elasticsearch-version }}
          OPENSEARCH_VERSION: ${{ inputs.opensearch-version }}
          POSTGRES_PASSWORD: ${{ inputs.fips-enabled && 'mostest-fips-test' || 'mostest' }}
        run: |
          cd server/build
          docker compose --ansi never run --rm start_dependencies
          cat ../tests/custom-schema-objectID.ldif | docker compose --ansi never exec -T openldap bash -c 'ldapadd -Y EXTERNAL -H ldapi:/// -w mostest || true';
          cat ../tests/custom-schema-cpa.ldif | docker compose --ansi never exec -T openldap bash -c 'ldapadd -Y EXTERNAL -H ldapi:/// -w mostest || true';
          cat ../tests/test-data.ldif | docker compose --ansi never exec -T openldap bash -c 'ldapadd -x -D "cn=admin,dc=mm,dc=test,dc=com" -w mostest';
          docker compose --ansi never exec -T minio sh -c 'mkdir -p /data/mattermost-test';
          docker compose --ansi never ps

      # ── Test-level sharding ────────────────────────────────────────────
      # When shard-total > 1, we split tests across N parallel runners.
      #
      # Two-tier splitting strategy:
      #   - "Light" packages (< 5 min): assigned whole to a shard
      #   - "Heavy" packages (≥ 5 min, e.g. api4, app): individual tests
      #     are distributed across shards using -run regex filters
      #
      # See server/scripts/shard-split.js for the full algorithm.
      # ─────────────────────────────────────────────────────────────────────

      - name: Setup Go for test discovery
        if: inputs.shard-total > 1
        uses: actions/setup-go@4b73464bb391d4059bd26b0524d20df3927bd417 # v6.3.0
        with:
          go-version: ${{ inputs.go-version }}


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/.github/workflows/tag-public-module.yaml =====

name: Tag Public Module

on:
  workflow_dispatch:
    inputs:
      semver_bump:
        type: choice
        required: false
        description: The semver update level
        options:
          - patch
          - minor
          - major
        default: patch
      commit_sha:
        type: string
        description: The commit sha to tag. Defaults to HEAD master
        required: false

permissions: {}

jobs:
  tag-public-module:
    permissions:
      contents: write
    runs-on: ubuntu-22.04
    env:
      COMMIT_SHA: ${{ inputs.commit_sha }}
    steps:
      - name: release/checkout-mattermost
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2
        with:
          persist-credentials: false
          fetch-depth: 0

      - name: release/find-latest-public-module-tags
        run: |
          echo LATEST_MODULE_TAG=$(git tag --list 'server/public/*' --format='%(refname:lstrip=-1)'  --sort -v:refname | head -1) >> ${GITHUB_ENV}

      - name: release/validate-commit-sha
        run: |
          if [ -n "$COMMIT_SHA" ]; then
            # Validate commit SHA format (40 character hex string)
            if [[ ! "$COMMIT_SHA" =~ ^[a-f0-9]{40}$ ]]; then
              echo "Error: Invalid commit SHA format. Must be a 40-character hexadecimal string."
              exit 1
            fi
            # Verify the commit exists in the repository
            if ! git cat-file -e "$COMMIT_SHA" 2>/dev/null; then
              echo "Error: Commit SHA '$COMMIT_SHA' does not exist in the repository."
              exit 1
            fi
            echo "Commit SHA validation passed: $COMMIT_SHA"
          else
            echo "No commit SHA provided, will use HEAD"
          fi

      - name: release/generate-module-release-notes
        run: |
          echo "RELEASE_NOTES<<EOF" >> ${GITHUB_ENV}
          if [ -z "$COMMIT_SHA" ]; then
            echo "$(git log --oneline --graph --decorate --abbrev-commit "server/public/${LATEST_MODULE_TAG}"...$(git rev-parse HEAD) server/public)" >> ${GITHUB_ENV}
          else
            echo "$(git log --oneline --graph --decorate --abbrev-commit "server/public/${LATEST_MODULE_TAG}"...${COMMIT_SHA} server/public)" >> ${GITHUB_ENV}
          fi
          echo "EOF" >> ${GITHUB_ENV}

      - name: release/semver-bump
        uses: mattermost/action-bump-semver@51a0e77acb7b1769f17ce3e0ee89f0a3b0978d51
        id: bump-semver
        with:
          current_version: ${{ env.LATEST_MODULE_TAG }}
          level: ${{ inputs.semver_bump }}

      - name: release/create-annotated-tag
        uses: mattermost/actions/delivery/create-tag@d5174b860704729f4c14ef8489ae075742bfa08a
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          tag: server/public/${{ steps.bump-semver.outputs.new_version }}
          message: ${{ env.RELEASE_NOTES }}
          commit_sha: ${{ inputs.commit_sha || github.sha }}

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/.github/workflows/tools-ci.yml =====

name: Tools CI
on:
  push:
    branches:
      - master
      - release-*
  pull_request:
    paths:
      - "tools/mattermost-govet/**"
      - ".github/workflows/tools-ci.yml"

concurrency:
  group: ${{ github.event_name == 'pull_request' && format('{0}-{1}', github.workflow, github.ref) || github.run_id }}
  cancel-in-progress: ${{ github.event_name == 'pull_request' }}

permissions:
  contents: read

jobs:
  check-style:
    name: check-style (mattermost-govet)
    runs-on: ubuntu-22.04
    defaults:
      run:
        working-directory: tools/mattermost-govet
    steps:
      - name: Checkout mattermost project
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2
        with:
          persist-credentials: false
      - name: Setup Go
        uses: actions/setup-go@4b73464bb391d4059bd26b0524d20df3927bd417 # v6.3.0
        with:
          go-version-file: tools/mattermost-govet/go.mod
      - name: Run check-style
        run: make check-style

  test:
    name: Test (mattermost-govet)
    runs-on: ubuntu-22.04
    defaults:
      run:
        working-directory: tools/mattermost-govet
    steps:
      - name: Checkout mattermost project
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2
        with:
          persist-credentials: false
      - name: Setup Go
        uses: actions/setup-go@4b73464bb391d4059bd26b0524d20df3927bd417 # v6.3.0
        with:
          go-version-file: tools/mattermost-govet/go.mod
      - name: Run tests
        run: make test

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/.github/workflows/webapp-ci.yml =====

name: Web App CI
on:
  push:
    branches:
      - master
      - release-*
  pull_request:
    paths:
      - "webapp/**"
      - ".github/workflows/webapp-ci.yml"
      - ".github/actions/webapp-setup/**"

concurrency:
  group: ${{ github.event_name == 'pull_request' && format('{0}-{1}', github.workflow, github.ref) || github.run_id }}
  cancel-in-progress: ${{ github.event_name == 'pull_request' }}

permissions: {}

jobs:
  check-lint:
    permissions:
      contents: read
    runs-on: ubuntu-24.04
    defaults:
      run:
        working-directory: webapp
    steps:
      - name: ci/checkout-repo
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2
        with:
          persist-credentials: false
      - name: ci/setup
        uses: ./.github/actions/webapp-setup
      - name: ci/lint
        run: |
          npm run check

  check-i18n:
    permissions:
      contents: read
    needs: check-lint
    runs-on: ubuntu-24.04
    defaults:
      run:
        working-directory: webapp
    steps:
      - name: ci/checkout-repo
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2
        with:
          persist-credentials: false
      - name: ci/setup
        uses: ./.github/actions/webapp-setup
      - name: ci/i18n-extract
        working-directory: webapp/channels
        run: |
          npm run i18n-extract:check

  check-external-links:
    permissions:
      contents: read
    needs: check-lint
    runs-on: ubuntu-24.04
    timeout-minutes: 15
    defaults:
      run:
        working-directory: webapp
    steps:
      - name: ci/checkout-repo
        uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
        with:
          persist-credentials: false
      - name: ci/setup
        uses: ./.github/actions/webapp-setup
      - name: ci/check-external-links
        run: |
          set -o pipefail
          npm run check-external-links -- --markdown | tee -a $GITHUB_STEP_SUMMARY

  check-types:
    permissions:
      contents: read
    needs: check-lint
    runs-on: ubuntu-24.04
    defaults:
      run:
        working-directory: webapp
    steps:
      - name: ci/checkout-repo
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2
        with:
          persist-credentials: false
      - name: ci/setup
        uses: ./.github/actions/webapp-setup
      - name: ci/lint
        run: |
          npm run check-types

  test-platform:
    needs: check-lint
    runs-on: ubuntu-24.04
    timeout-minutes: 30
    permissions:
      contents: read
      actions: write
      checks: write
      pull-requests: write
    name: test (platform)
    defaults:
      run:
        working-directory: webapp
    steps:
      - name: ci/checkout-repo
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2
        with:
          persist-credentials: false
      - name: ci/setup
        uses: ./.github/actions/webapp-setup
      - name: ci/test
        env:
          NODE_OPTIONS: --max_old_space_size=5120
        run: |
          npm run test-ci --workspace=platform/client --workspace=platform/components --workspace=platform/shared -- --coverage
      - name: ci/upload-coverage-artifact
        uses: actions/upload-artifact@bbbca2ddaa5d8feaa63e36b76fdaad77386f024f # v7.0.0
        with:
          name: coverage-platform
          path: |
            ./webapp/platform/client/coverage
            ./webapp/platform/components/coverage
            ./webapp/platform/shared/coverage
          retention-days: 1

  test-mattermost-redux:
    needs: check-lint
    runs-on: ubuntu-24.04
    timeout-minutes: 30
    permissions:
      contents: read
      actions: write
      checks: write
      pull-requests: write
    name: test (mattermost-redux)
    defaults:
      run:
        working-directory: webapp/channels
    steps:
      - name: ci/checkout-repo
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2
        with:
          persist-credentials: false
      - name: ci/setup
        uses: ./.github/actions/webapp-setup
      - name: ci/test
        env:
          NODE_OPTIONS: --max_old_space_size=5120
        run: |
          npm run test-ci -- --config jest.config.mattermost-redux.js
      - name: ci/upload-coverage-artifact
        uses: actions/upload-artifact@bbbca2ddaa5d8feaa63e36b76fdaad77386f024f # v7.0.0
        with:
          name: coverage-mattermost-redux
          path: ./webapp/channels/coverage
          retention-days: 1

  test-channels:
    needs: check-lint
    runs-on: ubuntu-24.04
    timeout-minutes: 30
    permissions:
      contents: read
      actions: write
      checks: write
      pull-requests: write
    strategy:
      fail-fast: false
      matrix:
        shard: [1, 2, 3, 4]
    name: test (channels shard ${{ matrix.shard }}/4)
    defaults:
      run:

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/.github/workflows/yamllint.yml =====

name: YAML Lint

on:
  push:
    branches:
      - master
      - release-*
  pull_request:
    paths:
      - ".github/workflows/**"
      - ".yamllint"

concurrency:
  group: ${{ github.event_name == 'pull_request' && format('{0}-{1}', github.workflow, github.ref) || github.run_id }}
  cancel-in-progress: ${{ github.event_name == 'pull_request' }}

permissions:
  contents: read

jobs:
  yamllint:
    runs-on: ubuntu-22.04
    steps:
      - uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2
        with:
          persist-credentials: false
      - name: Lint workflow YAML files
        run: yamllint .github/workflows/

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/.gitpod.yml =====

mainConfiguration: https://github.com/mattermost/mattermost-gitpod-config

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/AGENTS.md =====

# AGENTS.md

Explicitly import subdirectory instruction files that must always be in context:
@server/AGENTS.md

## Pull Requests

When creating a pull request, follow `.github/PULL_REQUEST_TEMPLATE.md` exactly:

- Remove all `<!-- -->` comments.
- Omit sections that are not applicable (Ticket Link, Screenshots) — do not write N/A, just remove the header.
- The `#### Release Note` header and its "```release-note" fenced code block **must always be present** (WITHOUT escaping the ``` characters). Write `NONE` if the change has no API, schema, UI, or breaking changes.

## Cursor Cloud Agents

This repository has a checked-in Cloud Agent environment under `.cursor/`. Docker is started by `.cursor/scripts/cloud-agent-start.sh`; if Docker is unavailable in Cloud, treat that as an environment failure rather than falling back to snapshot assumptions.

The environment declares `mattermost/enterprise` as a Cursor multi-repo dependency. Cursor clones the repositories as siblings, so `server/Makefile` can use its default `../../enterprise` path; the install hook does not clone or symlink enterprise.

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/CHANGELOG.md =====

# Mattermost Changelog

Please see [Mattermost Changelog](http://docs.mattermost.com/administration/changelog.html) in product documentation.

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/CONTRIBUTING.md =====

# Code Contribution Guidelines

Thank you for your interest in contributing! Please see the [Mattermost Contribution Guide](https://developers.mattermost.com/contribute/getting-started/) which describes the process for making code contributions across Mattermost projects and [join our "Contributors" community channel](https://community.mattermost.com/core/channels/tickets) to ask questions from community members and the Mattermost core team.

In addition, we recommend reviewing the [Contribution Guidelines](https://handbook.mattermost.com/contributors/contributors/guidelines/contribution-guidelines) in the Mattermost Handbook, which provide comprehensive best practices and expectations for contributors.

When you submit a pull request, it goes through a [code review process outlined here](https://developers.mattermost.com/contribute/getting-started/code-review/).

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/LICENSE.txt =====

Mattermost Licensing

SOFTWARE LICENSING

You are licensed to use compiled versions of the Mattermost platform produced by Mattermost, Inc. under an MIT LICENSE

-	See MIT-COMPILED-LICENSE.md included in compiled versions for details

You may be licensed to use source code to create compiled versions not produced by Mattermost, Inc. in one of two ways:

1. Under the Free Software Foundation’s GNU AGPL v3.0, subject to the exceptions outlined in this policy; or
2. Under a commercial license available from Mattermost, Inc. by contacting commercial@mattermost.com

You are licensed to use the source code in Admin Tools and Configuration Files (server/templates/, server/i18n/,
server/public/, webapp/ and all subdirectories thereof) under the Apache License v2.0.

We promise that we will not enforce the copyleft provisions in AGPL v3.0 against you if your application (a) does not
link to the Mattermost Platform directly, but exclusively uses the Mattermost Admin Tools and Configuration Files, and
(b) you have not modified, added to or adapted the source code of Mattermost in a way that results in the creation of
a “modified version” or “work based on” Mattermost as these terms are defined in the AGPL v3.0 license.

MATTERMOST TRADEMARK GUIDELINES

Your use of the mark Mattermost is subject to Mattermost, Inc's prior written approval and our organization’s Trademark
Standards of Use at https://mattermost.com/trademark-standards-of-use/. For trademark approval or any questions
you have about using these trademarks, please email trademark@mattermost.com

------------------------------------------------------------------------------------------------------------------------------

                               Apache License
                           Version 2.0, January 2004
                        http://www.apache.org/licenses/

   TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION

   1. Definitions.

      "License" shall mean the terms and conditions for use, reproduction,
      and distribution as defined by Sections 1 through 9 of this document.

      "Licensor" shall mean the copyright owner or entity authorized by
      the copyright owner that is granting the License.

      "Legal Entity" shall mean the union of the acting entity and all
      other entities that control, are controlled by, or are under common
      control with that entity. For the purposes of this definition,
      "control" means (i) the power, direct or indirect, to cause the
      direction or management of such entity, whether by contract or
      otherwise, or (ii) ownership of fifty percent (50%) or more of the
      outstanding shares, or (iii) beneficial ownership of such entity.

      "You" (or "Your") shall mean an individual or Legal Entity
      exercising permissions granted by this License.

      "Source" form shall mean the preferred form for making modifications,
      including but not limited to software source code, documentation
      source, and configuration files.

      "Object" form shall mean any form resulting from mechanical
      transformation or translation of a Source form, including but
      not limited to compiled object code, generated documentation,
      and conversions to other media types.

      "Work" shall mean the work of authorship, whether in Source or
      Object form, made available under the License, as indicated by a
      copyright notice that is included in or attached to the work
      (an example is provided in the Appendix below).

      "Derivative Works" shall mean any work, whether in Source or Object
      form, that is based on (or derived from) the Work and for which the
      editorial revisions, annotations, elaborations, or other modifications
      represent, as a whole, an original work of authorship. For the purposes
      of this License, Derivative Works shall not include works that remain
      separable from, or merely link (or bind by name) to the interfaces of,
      the Work and Derivative Works thereof.

      "Contribution" shall mean any work of authorship, including
      the original version of the Work and any modifications or additions
      to that Work or Derivative Works thereof, that is intentionally
      submitted to Licensor for inclusion in the Work by the copyright owner
      or by an individual or Legal Entity authorized to submit on behalf of
      the copyright owner. For the purposes of this definition, "submitted"
      means any form of electronic, verbal, or written communication sent
      to the Licensor or its representatives, including but not limited to
      communication on electronic mailing lists, source code control systems,
      and issue tracking systems that are managed by, or on behalf of, the
      Licensor for the purpose of discussing and improving the Work, but
      excluding communication that is conspicuously marked or otherwise
      designated in writing by the copyright owner as "Not a Contribution."

      "Contributor" shall mean Licensor and any individual or Legal Entity
      on behalf of whom a Contribution has been received by Licensor and
      subsequently incorporated within the Work.

   2. Grant of Copyright License. Subject to the terms and conditions of
      this License, each Contributor hereby grants to You a perpetual,
      worldwide, non-exclusive, no-charge, royalty-free, irrevocable
      copyright license to reproduce, prepare Derivative Works of,
      publicly display, publicly perform, sublicense, and distribute the
      Work and such Derivative Works in Source or Object form.

   3. Grant of Patent License. Subject to the terms and conditions of
      this License, each Contributor hereby grants to You a perpetual,
      worldwide, non-exclusive, no-charge, royalty-free, irrevocable
      (except as stated in this section) patent license to make, have made,
      use, offer to sell, sell, import, and otherwise transfer the Work,
      where such license applies only to those patent claims licensable
      by such Contributor that are necessarily infringed by their
      Contribution(s) alone or by combination of their Contribution(s)
      with the Work to which such Contribution(s) was submitted. If You
      institute patent litigation against any entity (including a
      cross-claim or counterclaim in a lawsuit) alleging that the Work
      or a Contribution incorporated within the Work constitutes direct
      or contributory patent infringement, then any patent licenses
      granted to You under this License for that Work shall terminate
      as of the date such litigation is filed.

   4. Redistribution. You may reproduce and distribute copies of the
      Work or Derivative Works thereof in any medium, with or without
      modifications, and in Source or Object form, provided that You
      meet the following conditions:

      (a) You must give any other recipients of the Work or
          Derivative Works a copy of this License; and

      (b) You must cause any modified files to carry prominent notices
          stating that You changed the files; and

      (c) You must retain, in the Source form of any Derivative Works
          that You distribute, all copyright, patent, trademark, and
          attribution notices from the Source form of the Work,
          excluding those notices that do not pertain to any part of
          the Derivative Works; and

      (d) If the Work includes a "NOTICE" text file as part of its
          distribution, then any Derivative Works that You distribute must
          include a readable copy of the attribution notices contained
          within such NOTICE file, excluding those notices that do not
          pertain to any part of the Derivative Works, in at least one
          of the following places: within a NOTICE text file distributed
          as part of the Derivative Works; within the Source form or
          documentation, if provided along with the Derivative Works; or,
          within a display generated by the Derivative Works, if and
          wherever such third-party notices normally appear. The contents
          of the NOTICE file are for informational purposes only and
          do not modify the License. You may add Your own attribution
          notices within Derivative Works that You distribute, alongside
          or as an addendum to the NOTICE text from the Work, provided
          that such additional attribution notices cannot be construed
          as modifying the License.

      You may add Your own copyright statement to Your modifications and
      may provide additional or different license terms and conditions
      for use, reproduction, or distribution of Your modifications, or
      for any such Derivative Works as a whole, provided Your use,
      reproduction, and distribution of the Work otherwise complies with
      the conditions stated in this License.

   5. Submission of Contributions. Unless You explicitly state otherwise,
      any Contribution intentionally submitted for inclusion in the Work
      by You to the Licensor shall be under the terms and conditions of
      this License, without any additional terms or conditions.
      Notwithstanding the above, nothing herein shall supersede or modify
      the terms of any separate license agreement you may have executed
      with Licensor regarding such Contributions.

   6. Trademarks. This License does not grant permission to use the trade
      names, trademarks, service marks, or product names of the Licensor,
      except as required for reasonable and customary use in describing the
      origin of the Work and reproducing the content of the NOTICE file.

   7. Disclaimer of Warranty. Unless required by applicable law or
      agreed to in writing, Licensor provides the Work (and each
      Contributor provides its Contributions) on an "AS IS" BASIS,
      WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
      implied, including, without limitation, any warranties or conditions
      of TITLE, NON-INFRINGEMENT, MERCHANTABILITY, or FITNESS FOR A
      PARTICULAR PURPOSE. You are solely responsible for determining the
      appropriateness of using or redistributing the Work and assume any
      risks associated with Your exercise of permissions under this License.

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/NOTICE.txt =====

Mattermost Server

©2015-present Mattermost,Inc. All Rights Reserved. See LICENSE for license information.

NOTICES:
--------

This document includes a list of open source components used in Mattermost Server, including those that have been modified.

--------

## @atlaskit/pragmatic-drag-and-drop

This product contains '@atlaskit/pragmatic-drag-and-drop' by Atlassian Pty Ltd.

The core package for Pragmatic drag and drop - enabling fast drag and drop for any experience on any tech stack

* HOMEPAGE:
  * https://atlassian.design/components/pragmatic-drag-and-drop/

* LICENSE: Apache-2.0

Copyright 2024 Atlassian Pty Ltd

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.


---

## @atlaskit/pragmatic-drag-and-drop-hitbox

This product contains '@atlaskit/pragmatic-drag-and-drop-hitbox' by Atlassian Pty Ltd.

An optional package for Pragmatic drag and drop that enables the attaching of interaction information to a drop target

* HOMEPAGE:
  * https://atlassian.design/components/pragmatic-drag-and-drop/

* LICENSE: Apache-2.0

Copyright 2024 Atlassian Pty Ltd

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.


---

## @atlaskit/pragmatic-drag-and-drop-react-drop-indicator

This product contains '@atlaskit/pragmatic-drag-and-drop-react-drop-indicator' by Atlassian Pty Ltd.

An optional Pragmatic drag and drop package containing react components that provide a visual indication about what the user will achieve when the drop (eg lines)

* HOMEPAGE:
  * https://atlassian.design/components/pragmatic-drag-and-drop/

* LICENSE: Apache-2.0

Copyright 2024 Atlassian Pty Ltd

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.


---

## @floating-ui/react

This product contains '@floating-ui/react' by atomiks.

Floating UI for React

* HOMEPAGE:
  * https://floating-ui.com/docs/react

* LICENSE: MIT

MIT License

Copyright (c) 2021 Floating UI contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.


---

## @giphy/js-fetch-api

This product contains '@giphy/js-fetch-api'.

Javascript API to fetch gifs and stickers from the GIPHY API.

* HOMEPAGE:
  * https://github.com/Giphy/giphy-js/tree/master/packages/fetch-api

* LICENSE: MIT

The MIT License (MIT)
Copyright (c) 2019 GIPHY

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.


---

## @giphy/react-components

This product contains '@giphy/react-components' by giannif.

A lightweight set of components, focused on easy-of-use and performance.

* HOMEPAGE:
  * https://github.com/Giphy/giphy-js/tree/master/packages/react-components

* LICENSE: MIT

The MIT License (MIT)
Copyright (c) 2019 GIPHY


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/README.md =====

# [![Mattermost logo](https://user-images.githubusercontent.com/7205829/137170381-fe86eef0-bccc-4fdd-8e92-b258884ebdd7.png)](https://mattermost.com)

[Mattermost](https://mattermost.com) is an open core, self-hosted collaboration platform that offers chat, workflow automation, voice calling, screen sharing, and AI integration. This repo is the primary source for core development on the Mattermost platform; it's written in Go and React, runs as a single Linux binary, and relies on PostgreSQL. A new compiled version is released under an MIT license every month on the 16th.

[Deploy Mattermost on-premises](https://mattermost.com/deploy/?utm_source=github-mattermost-server-readme), or [try it for free in the cloud](https://mattermost.com/sign-up/?utm_source=github-mattermost-server-readme).

<img width="1006" alt="mattermost user interface" src="https://user-images.githubusercontent.com/7205829/136107976-7a894c9e-290a-490d-8501-e5fdbfc3785a.png">

Learn more about the following use cases with Mattermost:

- [DevSecOps](https://mattermost.com/solutions/use-cases/devops/?utm_source=github-mattermost-server-readme)
- [Incident Resolution](https://mattermost.com/solutions/use-cases/incident-resolution/?utm_source=github-mattermost-server-readme)
- [IT Service Desk](https://mattermost.com/solutions/use-cases/it-service-desk/?utm_source=github-mattermost-server-readme)

Other useful resources:

- [Download and Install Mattermost](https://docs.mattermost.com/guides/deployment.html) - Install, setup, and configure your own Mattermost instance.
- [Product documentation](https://docs.mattermost.com/) - Learn how to run a Mattermost instance and take advantage of all the features.
- [Developer documentation](https://developers.mattermost.com/) - Contribute code to Mattermost or build an integration via APIs, Webhooks, slash commands, Apps, and plugins.

Table of contents
=================

- [Install Mattermost](#install-mattermost)
- [Native mobile and desktop apps](#native-mobile-and-desktop-apps)
- [Get security bulletins](#get-security-bulletins)
- [Get involved](#get-involved)
- [Learn more](#learn-more)
- [License](#license)
- [Get the latest news](#get-the-latest-news)
- [Contributing](#contributing)

## Install Mattermost

- [Download and Install Mattermost Self-Hosted](https://docs.mattermost.com/guides/deployment.html) - Deploy a Mattermost Self-hosted instance in minutes via Docker, Ubuntu, or tar.
- [Get started in the cloud](https://mattermost.com/sign-up/?utm_source=github-mattermost-server-readme) to try Mattermost today.
- [Developer machine setup](https://developers.mattermost.com/contribute/server/developer-setup) - Follow this guide if you want to write code for Mattermost.


Other install guides:

- [Deploy Mattermost on Docker](https://docs.mattermost.com/install/install-docker.html)
- [Mattermost Omnibus](https://docs.mattermost.com/install/installing-mattermost-omnibus.html)
- [Install Mattermost from Tar](https://docs.mattermost.com/install/install-tar.html)
- [Ubuntu 20.04 LTS](https://docs.mattermost.com/install/installing-ubuntu-2004-LTS.html)
- [Kubernetes](https://docs.mattermost.com/install/install-kubernetes.html)
- [Helm](https://docs.mattermost.com/install/install-kubernetes.html#installing-the-operators-via-helm)
- [Debian Buster](https://docs.mattermost.com/install/install-debian.html)
- [RHEL 8](https://docs.mattermost.com/install/install-rhel-8.html)
- [More server install guides](https://docs.mattermost.com/guides/deployment.html)

## Native mobile and desktop apps

In addition to the web interface, you can also download Mattermost clients for [Android](https://mattermost.com/pl/android-app/), [iOS](https://mattermost.com/pl/ios-app/), [Windows PC](https://docs.mattermost.com/install/desktop-app-install.html#windows-10-windows-8-1), [macOS](https://docs.mattermost.com/install/desktop-app-install.html#macos-10-9), and [Linux](https://docs.mattermost.com/install/desktop-app-install.html#linux).

[<img src="https://user-images.githubusercontent.com/30978331/272826427-6200c98f-7319-42c3-86d4-0b33ae99e01a.png" alt="Get Mattermost on Google Play" height="50px"/>](https://mattermost.com/pl/android-app/)  [<img src="https://developer.apple.com/assets/elements/badges/download-on-the-app-store.svg" alt="Get Mattermost on the App Store" height="50px"/>](https://itunes.apple.com/us/app/mattermost/id1257222717?mt=8)  [![Get Mattermost on Windows PC](https://user-images.githubusercontent.com/33878967/33095357-39cab8d2-ceb8-11e7-89a6-67dccc571ca3.png)](https://docs.mattermost.com/install/desktop.html#windows-10-windows-8-1-windows-7)  [![Get Mattermost on Mac OSX](https://user-images.githubusercontent.com/33878967/33095355-39a36f2a-ceb8-11e7-9b33-73d4f6d5d6c1.png)](https://docs.mattermost.com/install/desktop.html#macos-10-9)  [![Get Mattermost on Linux](https://user-images.githubusercontent.com/33878967/33095354-3990e256-ceb8-11e7-965d-b00a16e578de.png)](https://docs.mattermost.com/install/desktop.html#linux)

## Get security bulletins

Receive notifications of critical security updates. The sophistication of online attackers is perpetually increasing. If you're deploying Mattermost it's highly recommended you subscribe to the Mattermost Security Bulletin mailing list for updates on critical security releases.

[Subscribe here](https://mattermost.com/security-updates/#sign-up)

## Get involved

- [Contribute to Mattermost](https://handbook.mattermost.com/contributors/contributors/ways-to-contribute)
- [Find "Help Wanted" projects](https://github.com/mattermost/mattermost-server/issues?page=1&q=is%3Aissue+is%3Aopen+%22Help+Wanted%22&utf8=%E2%9C%93)
- [Join Developer Discussion on a Mattermost server for contributors](https://community.mattermost.com/signup_user_complete/?id=f1924a8db44ff3bb41c96424cdc20676)
- [Get Help With Mattermost](https://docs.mattermost.com/guides/get-help.html)

## Learn more

- [API options - webhooks, slash commands, drivers, and web service](https://api.mattermost.com/)
- [See who's using Mattermost](https://mattermost.com/customers/)
- [Browse over 700 Mattermost integrations](https://mattermost.com/marketplace/)

## License

See the [LICENSE file](LICENSE.txt) for license rights and limitations.

## Get the latest news

- **X** - Follow [Mattermost on X, formerly Twitter](https://twitter.com/mattermost).
- **Blog** - Get the latest updates from the [Mattermost blog](https://mattermost.com/blog/).
- **Facebook** - Follow [Mattermost on Facebook](https://www.facebook.com/MattermostHQ).
- **LinkedIn** - Follow [Mattermost on LinkedIn](https://www.linkedin.com/company/mattermost/).
- **Email** - Subscribe to our [newsletter](https://mattermost.us11.list-manage.com/subscribe?u=6cdba22349ae374e188e7ab8e&id=2add1c8034) (1 or 2 per month).
- **Mattermost** - Join the ~contributors channel on [the Mattermost Community Server](https://community.mattermost.com).
- **IRC** - Join the #matterbridge channel on [Freenode](https://freenode.net/) (thanks to [matterircd](https://github.com/42wim/matterircd)).
- **YouTube** -  Subscribe to [Mattermost](https://www.youtube.com/@MattermostHQ).

## Contributing

[![Small Image](https://img.shields.io/badge/Contribute%20with-Gitpod-908a85?logo=gitpod)](https://gitpod.io/#https://github.com/mattermost/mattermost)

Please see [CONTRIBUTING.md](./CONTRIBUTING.md).
[Join the Mattermost Contributors server](https://community.mattermost.com/signup_user_complete/?id=codoy5s743rq5mk18i7u5ksz7e) to join community discussions about contributions, development, and more.

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/SECURITY.md =====

Security
========

Safety and data security is of the utmost priority for the Mattermost community. If you are a security researcher and have discovered a security vulnerability in our codebase, we would appreciate your help in disclosing it to us in a responsible manner.

Reporting security issues
-------------------------

**Please do not use GitHub issues for security-sensitive communication.**

Security issues in the community test server, any of the open source codebases maintained by Mattermost, or any of our commercial offerings should be reported via email to [responsibledisclosure@mattermost.com](mailto:responsibledisclosure@mattermost.com). Mattermost is committed to working together with researchers and keeping them updated throughout the patching process. Researchers who responsibly report valid security issues will be publicly credited for their efforts (if they so choose).

For a more detailed description of the disclosure process and a list of researchers who have previously contributed to the disclosure program, see [Report a Security Vulnerability](https://mattermost.com/security-vulnerability-report/) on the Mattermost website.

Security updates
----------------

Mattermost has a mandatory upgrade policy, and updates are only provided for the latest 3 releases and the current Extended Support Release (ESR). Critical updates are delivered as dot releases. Details on security updates are announced 30 days after the availability of the update.

For more details about the security content of past releases, see the [Security Updates](https://mattermost.com/security-updates/) page on the Mattermost website. For timely notifications about new security updates, subscribe to the [Security Bulletins Mailing List](https://mattermost.com/security-updates/#sign-up).

Contributing to this policy
---------------------------

If you have feedback or suggestions on improving this policy document, please [create an issue](https://github.com/mattermost/mattermost-server/issues/new).

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/api/.spectral.yaml =====

extends: '@ibm-cloud/openapi-ruleset'
rules:
  operation-tags: off
  property-case-convention: off
  request-body-object: off
  operation-operationId: error
  operation-summary: warn
  array-responses: off
  parameter-description: error
  parameter-description: off
  parameter-case-convention: info
  no-$ref-siblings: off
  enum-case-convention: off
  path-segment-case-convention: info 

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/api/CONTRIBUTING.md =====

## Contributing

We're accepting pull requests! Specifically we're looking for documenation on routes defined [here](../server/channels/api4).

All the documentation is written in YAML and found in the [source](v4/source) directory.

* When adding a new route, please add it to the correct file. For example, a channel route will go in [channels.yaml](v4/source/channels.yaml).
* To add a new tag, please do so in [introduction.yaml](v4/source/introduction.yaml)
* Definitions should be added to [definitions.yaml](v4/source/definitions.yaml)

There is no strict style guide but please try to follow the example of the existing documentation.

To build the full YAML, run `make build` and it will be output to `html/static/mattermost-openapi.yaml`. To check for syntax, you can copy the contents of that into http://editor.swagger.io/ or you can look into using a commandline or ESLint-based syntax checker.

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/api/README.md =====

# Mattermost API Documentation

This repository holds the API reference documentation for Mattermost available at [https://developers.mattermost.com/api-reference](https://developers.mattermost.com/api-reference).

The Mattermost API reference uses the [OpenAPI standard](https://openapis.org/) and the [ReDoc document generator](https://github.com/Rebilly/ReDoc).

All documentation is available under the terms of a [Creative Commons License](https://creativecommons.org/licenses/by-nc-sa/3.0/).

## Contributing

We're accepting pull requests! See something that could be documented better or is missing documentation? Make a PR and we'll gladly accept it.

All the documentation is written in YAML and found in the [v4/source](v4/source) directories. APIv4 documentation is in the [v4 directory](v4).
APIs for [Playbooks](https://github.com/mattermost/mattermost-plugin-playbooks) are retrieved from GitHub at build time and integrated into the final YAML file.

* When adding a new route, please add it to the correct file. For example, a channel route will go in [channels.yaml](v4/source/channels.yaml).
* To add a new tag, please do so in [introduction.yaml](v4/source/introduction.yaml)
* Definitions should be added to [definitions.yaml](v4/source/definitions.yaml)

There is no strict style guide but please try to follow the example of the existing documentation.

To build the full YAML, run `make build` and it will be output to `v4/html/static/mattermost-openapi-v4.yaml`. This will also check syntax using [swagger-cli](https://github.com/APIDevTools/swagger-cli).

To test locally, run `make build`, `make run` and navigate to `http://127.0.0.1:8080`. For any updates to the source files, re-run the same commands.

## Deployment

Deployment is handled automatically by our Github Actions. When a pull request is merged, it will automatically be deployed to [https://developers.mattermost.com/api-reference](https://developers.mattermost.com/api-reference).

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/api/package-lock.json =====

{
  "name": "mattermost-api-reference",
  "version": "1.0.0",
  "lockfileVersion": 2,
  "requires": true,
  "packages": {
    "": {
      "name": "mattermost-api-reference",
      "version": "1.0.0",
      "license": "ISC",
      "dependencies": {
        "@redocly/cli": "^1.13.0",
        "swagger-cli": "4.0.4",
        "sync-fetch": "0.4.1",
        "yaml": "2.1.1"
      }
    },
    "node_modules/@apidevtools/json-schema-ref-parser": {
      "version": "9.0.6",
      "resolved": "https://registry.npmjs.org/@apidevtools/json-schema-ref-parser/-/json-schema-ref-parser-9.0.6.tgz",
      "integrity": "sha512-M3YgsLjI0lZxvrpeGVk9Ap032W6TPQkH6pRAZz81Ac3WUNF79VQooAFnp8umjvVzUmD93NkogxEwbSce7qMsUg==",
      "dependencies": {
        "@jsdevtools/ono": "^7.1.3",
        "call-me-maybe": "^1.0.1",
        "js-yaml": "^3.13.1"
      }
    },
    "node_modules/@apidevtools/openapi-schemas": {
      "version": "2.1.0",
      "resolved": "https://registry.npmjs.org/@apidevtools/openapi-schemas/-/openapi-schemas-2.1.0.tgz",
      "integrity": "sha512-Zc1AlqrJlX3SlpupFGpiLi2EbteyP7fXmUOGup6/DnkRgjP9bgMM/ag+n91rsv0U1Gpz0H3VILA/o3bW7Ua6BQ==",
      "engines": {
        "node": ">=10"
      }
    },
    "node_modules/@apidevtools/swagger-cli": {
      "version": "4.0.4",
      "resolved": "https://registry.npmjs.org/@apidevtools/swagger-cli/-/swagger-cli-4.0.4.tgz",
      "integrity": "sha512-hdDT3B6GLVovCsRZYDi3+wMcB1HfetTU20l2DC8zD3iFRNMC6QNAZG5fo/6PYeHWBEv7ri4MvnlKodhNB0nt7g==",
      "dependencies": {
        "@apidevtools/swagger-parser": "^10.0.1",
        "chalk": "^4.1.0",
        "js-yaml": "^3.14.0",
        "yargs": "^15.4.1"
      },
      "bin": {
        "swagger-cli": "bin/swagger-cli.js"
      },
      "engines": {
        "node": ">=10"
      }
    },
    "node_modules/@apidevtools/swagger-cli/node_modules/cliui": {
      "version": "6.0.0",
      "resolved": "https://registry.npmjs.org/cliui/-/cliui-6.0.0.tgz",
      "integrity": "sha512-t6wbgtoCXvAzst7QgXxJYqPt0usEfbgQdftEPbLL/cvv6HPE5VgvqCuAIDR0NgU52ds6rFwqrgakNLrHEjCbrQ==",
      "dependencies": {
        "string-width": "^4.2.0",
        "strip-ansi": "^6.0.0",
        "wrap-ansi": "^6.2.0"
      }
    },
    "node_modules/@apidevtools/swagger-cli/node_modules/find-up": {
      "version": "4.1.0",
      "resolved": "https://registry.npmjs.org/find-up/-/find-up-4.1.0.tgz",
      "integrity": "sha512-PpOwAdQ/YlXQ2vj8a3h8IipDuYRi3wceVQQGYWxNINccq40Anw7BlsEXCMbt1Zt+OLA6Fq9suIpIWD0OsnISlw==",
      "dependencies": {
        "locate-path": "^5.0.0",
        "path-exists": "^4.0.0"
      },
      "engines": {
        "node": ">=8"
      }
    },
    "node_modules/@apidevtools/swagger-cli/node_modules/locate-path": {
      "version": "5.0.0",
      "resolved": "https://registry.npmjs.org/locate-path/-/locate-path-5.0.0.tgz",
      "integrity": "sha512-t7hw9pI+WvuwNJXwk5zVHpyhIqzg2qTlklJOf0mVxGSbe3Fp2VieZcduNYjaLDoy6p9uGpQEGWG87WpMKlNq8g==",
      "dependencies": {
        "p-locate": "^4.1.0"
      },
      "engines": {
        "node": ">=8"
      }
    },
    "node_modules/@apidevtools/swagger-cli/node_modules/p-locate": {
      "version": "4.1.0",
      "resolved": "https://registry.npmjs.org/p-locate/-/p-locate-4.1.0.tgz",
      "integrity": "sha512-R79ZZ/0wAxKGu3oYMlz8jy/kbhsNrS7SKZ7PxEHBgJ5+F2mtFW2fK2cOtBh1cHYkQsbzFV7I+EoRKe6Yt0oK7A==",
      "dependencies": {
        "p-limit": "^2.2.0"
      },
      "engines": {
        "node": ">=8"
      }
    },
    "node_modules/@apidevtools/swagger-cli/node_modules/path-exists": {
      "version": "4.0.0",
      "resolved": "https://registry.npmjs.org/path-exists/-/path-exists-4.0.0.tgz",
      "integrity": "sha512-ak9Qy5Q7jYb2Wwcey5Fpvg2KoAc/ZIhLSLOSBmRmygPsGwkVVt0fZa0qrtMz+m6tJTAHfZQ8FnmB4MG4LWy7/w==",
      "engines": {
        "node": ">=8"
      }
    },
    "node_modules/@apidevtools/swagger-cli/node_modules/wrap-ansi": {
      "version": "6.2.0",
      "resolved": "https://registry.npmjs.org/wrap-ansi/-/wrap-ansi-6.2.0.tgz",
      "integrity": "sha512-r6lPcBGxZXlIcymEu7InxDMhdW0KDxpLgoFLcguasxCaJ/SOIZwINatK9KY/tf+ZrlywOKU0UDj3ATXUBfxJXA==",
      "dependencies": {
        "ansi-styles": "^4.0.0",
        "string-width": "^4.1.0",
        "strip-ansi": "^6.0.0"
      },
      "engines": {
        "node": ">=8"
      }
    },
    "node_modules/@apidevtools/swagger-cli/node_modules/y18n": {
      "version": "4.0.3",
      "resolved": "https://registry.npmjs.org/y18n/-/y18n-4.0.3.tgz",
      "integrity": "sha512-JKhqTOwSrqNA1NY5lSztJ1GrBiUodLMmIZuLiDaMRJ+itFd+ABVE8XBjOvIWL+rSqNDC74LCSFmlb/U4UZ4hJQ=="
    },
    "node_modules/@apidevtools/swagger-cli/node_modules/yargs": {
      "version": "15.4.1",
      "resolved": "https://registry.npmjs.org/yargs/-/yargs-15.4.1.tgz",
      "integrity": "sha512-aePbxDmcYW++PaqBsJ+HYUFwCdv4LVvdnhBy78E57PIor8/OVvhMrADFFEDh8DHDFRv/O9i3lPhsENjO7QX0+A==",
      "dependencies": {
        "cliui": "^6.0.0",
        "decamelize": "^1.2.0",
        "find-up": "^4.1.0",
        "get-caller-file": "^2.0.1",
        "require-directory": "^2.1.1",
        "require-main-filename": "^2.0.0",
        "set-blocking": "^2.0.0",
        "string-width": "^4.2.0",
        "which-module": "^2.0.0",
        "y18n": "^4.0.0",
        "yargs-parser": "^18.1.2"
      },
      "engines": {
        "node": ">=8"
      }
    },
    "node_modules/@apidevtools/swagger-cli/node_modules/yargs-parser": {
      "version": "18.1.3",
      "resolved": "https://registry.npmjs.org/yargs-parser/-/yargs-parser-18.1.3.tgz",
      "integrity": "sha512-o50j0JeToy/4K6OZcaQmW6lyXXKhq7csREXcDwk2omFPJEwUNOVtJKvmDr9EI1fAJZUyZcRF7kxGBWmRXudrCQ==",
      "dependencies": {
        "camelcase": "^5.0.0",
        "decamelize": "^1.2.0"
      },
      "engines": {
        "node": ">=6"
      }
    },
    "node_modules/@apidevtools/swagger-methods": {
      "version": "3.0.2",
      "resolved": "https://registry.npmjs.org/@apidevtools/swagger-methods/-/swagger-methods-3.0.2.tgz",
      "integrity": "sha512-QAkD5kK2b1WfjDS/UQn/qQkbwF31uqRjPTrsCs5ZG9BQGAkjwvqGFjjPqAuzac/IYzpPtRzjCP1WrTuAIjMrXg=="
    },
    "node_modules/@apidevtools/swagger-parser": {
      "version": "10.1.0",
      "resolved": "https://registry.npmjs.org/@apidevtools/swagger-parser/-/swagger-parser-10.1.0.tgz",
      "integrity": "sha512-9Kt7EuS/7WbMAUv2gSziqjvxwDbFSg3Xeyfuj5laUODX8o/k/CpsAKiQ8W7/R88eXFTMbJYg6+7uAmOWNKmwnw==",
      "dependencies": {
        "@apidevtools/json-schema-ref-parser": "9.0.6",
        "@apidevtools/openapi-schemas": "^2.1.0",
        "@apidevtools/swagger-methods": "^3.0.2",
        "@jsdevtools/ono": "^7.1.3",
        "ajv": "^8.6.3",
        "ajv-draft-04": "^1.0.0",
        "call-me-maybe": "^1.0.1"
      },
      "peerDependencies": {
        "openapi-types": ">=7"
      }
    },
    "node_modules/@babel/code-frame": {
      "version": "7.24.6",
      "resolved": "https://registry.npmjs.org/@babel/code-frame/-/code-frame-7.24.6.tgz",

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/api/package.json =====

{
  "name": "mattermost-api-reference",
  "version": "1.0.0",
  "description": "This repository holds the API reference documentation for Mattermost available at https://developers.mattermost.com/api-reference",
  "main": "index.js",
  "dependencies": {
    "@redocly/cli": "^1.13.0",
    "swagger-cli": "4.0.4",
    "sync-fetch": "0.4.1",
    "yaml": "2.1.1"
  },
  "overrides": {
    "node-fetch": {
      "whatwg-url": "^12.0.0"
    },
    "redoc": {
      "react-tabs": "^6.0.0"
    }
  },
  "scripts": {
    "test": "echo \"Error: no test specified\" && exit 1"
  },
  "repository": {
    "type": "git",
    "url": "https://github.com/mattermost/mattermost.git"
  },
  "author": "",
  "license": "ISC",
  "bugs": {
    "url": "https://github.com/mattermost/mattermost/issues"
  }
}

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/api/playbooks/tags.yaml =====

---
tags:
  - name: Playbooks
    description: Playbooks
  - name: PlaybookRuns
    description: Playbook runs
  - name: Internal
    description: Internal endpoints
  - name: Timeline
    description: Timeline
  - name: PlaybookAutofollows
    description: Playbook Autofollows
x-tagGroups:
  - name: Playbooks
    tags:
      - Playbooks
      - PlaybookRuns
      - PlaybookAutofollows
      - Timeline
      - Internal

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/api/v4/source/access_control.yaml =====

  /api/v4/access_control_policies:
    put:
      tags:
        - access control
      summary: Create an access control policy
      description: |
        Creates a new access control policy.
        ##### Permissions
        Must have the `manage_system` permission.
      operationId: CreateAccessControlPolicy
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/AccessControlPolicy"
      responses:
        "200":
          description: Access control policy created successfully.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/AccessControlPolicy"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "500":
          $ref: "#/components/responses/InternalServerError"
  /api/v4/access_control_policies/cel/check:
    post:
      tags:
        - access control
      summary: Check an access control policy expression
      description: |
        Checks the syntax and validity of an access control policy expression.
        ##### Permissions
        Must have the `manage_system` permission.
      operationId: CheckAccessControlPolicyExpression
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                expression:
                  type: string
                  description: The expression to check.
      responses:
        "200":
          description: Expression check result.
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: "#/components/schemas/ExpressionError"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "500":
          $ref: "#/components/responses/InternalServerError"
  /api/v4/access_control_policies/cel/validate_requester:
    post:
      tags:
        - access control
      summary: Validate if the current user matches a CEL expression
      description: |
        Validates whether the current authenticated user matches the given CEL expression.
        This is used to determine if a channel admin can test expressions they match.
        ##### Permissions
        Must have `manage_system` permission OR be a channel admin for the specified channel (channelId required for channel admins).
      operationId: ValidateExpressionAgainstRequester
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                expression:
                  type: string
                  description: The CEL expression to validate against the current user.
                channelId:
                  type: string
                  description: The channel ID for channel-specific permission checks (required for channel admins).
              required:
                - expression
      responses:
        "200":
          description: Validation result returned successfully.
          content:
            application/json:
              schema:
                type: object
                properties:
                  requester_matches:
                    type: boolean
                    description: Whether the current user matches the expression.
                required:
                  - requester_matches
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "500":
          $ref: "#/components/responses/InternalServerError"
  /api/v4/access_control_policies/cel/test:
    post:
      tags:
        - access control
      summary: Test an access control policy expression
      description: |
        Tests an access control policy expression against users to see who would be affected.
        ##### Permissions
        Must have the `manage_system` permission.
      operationId: TestAccessControlPolicyExpression
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/QueryExpressionParams"
      responses:
        "200":
          description: Expression test result.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/AccessControlPolicyTestResponse"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "500":
          $ref: "#/components/responses/InternalServerError"
  /api/v4/access_control_policies/cel/simulate_users:
    post:
      tags:
        - access control
      summary: Simulate an access control policy decision for an explicit user list
      description: |
        Runs the dual-lane PDP simulation against a draft (unsaved) access
        control policy for an explicit set of users (with optional per-user
        session-attribute overrides). The server compiles the draft
        in-memory, layers on persisted higher-scoped permission policies,
        and returns per-user, per-action ALLOW/DENY decisions plus blame
        attribution for any deny.

        Backs the picker-driven "Simulate access" UX in the System Console
        and Channel Settings so authors can see how a draft interacts with
        persisted higher-scoped policies before saving.

        Gated by the `PermissionPolicies` feature flag and the Enterprise
        Advanced license. Returns 501 (Not Implemented) when either is
        missing.

        ##### Permissions
        Must have the `manage_system` permission, OR be a team admin with
        `manage_team_access_rules` on the request's `team_id` (when any
        provided `channel_id` resolves to a channel in that team), OR be a
        channel admin with `manage_channel_access_rules` on the request's
        `channel_id`.
      operationId: SimulateAccessControlPolicyForUsers
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/PolicySimulationByUsersParams"

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/api/v4/source/actions.yaml =====

  /api/v4/actions/dialogs/open:
    post:
      tags:
        - integration_actions
      summary: Open a dialog
      description: >
        Open an interactive dialog using a trigger ID provided by a slash
        command, or some other action payload. See
        https://docs.mattermost.com/developer/interactive-dialogs.html for more
        information on interactive dialogs.

        __Minimum server version: 5.6__
      operationId: OpenInteractiveDialog
      requestBody:
        content:
          application/json:
            schema:
              type: object
              required:
                - trigger_id
                - url
                - dialog
              properties:
                trigger_id:
                  type: string
                  description: Trigger ID provided by other action
                url:
                  type: string
                  description: The URL to send the submitted dialog payload to
                dialog:
                  type: object
                  required:
                    - title
                    - elements
                  description: Post object to create
                  properties:
                    callback_id:
                      type: string
                      description: Set an ID that will be included when the dialog is
                        submitted
                    title:
                      type: string
                      description: Title of the dialog
                    introduction_text:
                      type: string
                      description: Markdown formatted introductory paragraph
                    elements:
                      type: array
                      description: Input elements, see
                        https://docs.mattermost.com/developer/interactive-dialogs.html#elements
                      items:
                        type: object
                    submit_label:
                      type: string
                      description: Label on the submit button
                    notify_on_cancel:
                      type: boolean
                      description: Set true to receive payloads when user cancels a dialog
                    state:
                      type: string
                      description: Set some state to be echoed back with the dialog
                        submission
        description: Metadata for the dialog to be opened
        required: true
      responses:
        "200":
          description: Dialog open successful
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/StatusOK"
        "400":
          $ref: "#/components/responses/BadRequest"
  /api/v4/actions/dialogs/submit:
    post:
      tags:
        - integration_actions
      summary: Submit a dialog
      description: >
        Endpoint used by the Mattermost clients to submit a dialog. See
        https://docs.mattermost.com/developer/interactive-dialogs.html for more
        information on interactive dialogs.

        __Minimum server version: 5.6__
      operationId: SubmitInteractiveDialog
      requestBody:
        content:
          application/json:
            schema:
              type: object
              required:
                - url
                - submission
                - channel_id
                - team_id
              properties:
                url:
                  type: string
                  description: The URL to send the submitted dialog payload to
                channel_id:
                  type: string
                  description: Channel ID the user submitted the dialog from
                team_id:
                  type: string
                  description: Team ID the user submitted the dialog from
                submission:
                  type: object
                  description: String map where keys are element names and values are the
                    element input values
                callback_id:
                  type: string
                  description: Callback ID sent when the dialog was opened
                state:
                  type: string
                  description: State sent when the dialog was opened
                cancelled:
                  type: boolean
                  description: Set to true if the dialog was cancelled
        description: Dialog submission data
        required: true
      responses:
        "200":
          description: Dialog submission successful
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/StatusOK"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
  /api/v4/actions/dialogs/lookup:
    post:
      tags:
        - integration_actions
      summary: Lookup dialog elements
      description: >
        Endpoint used by the Mattermost clients to lookup dynamic dialog
        elements. See https://docs.mattermost.com/developer/interactive-dialogs.html
        for more information on interactive dialogs.

        __Minimum server version: 11.0__
      operationId: LookupInteractiveDialog
      requestBody:
        content:
          application/json:
            schema:
              type: object
              required:
                - url
                - submission
                - channel_id
                - team_id
              properties:
                url:
                  type: string
                  description: The URL to send the lookup request to
                channel_id:
                  type: string
                  description: Channel ID the user is performing the lookup from
                team_id:
                  type: string
                  description: Team ID the user is performing the lookup from
                submission:
                  type: object
                  description: String map where keys are element names and values are the
                    element input values
                callback_id:
                  type: string
                  description: Callback ID sent when the dialog was opened
                state:
                  type: string
                  description: State sent when the dialog was opened
        description: Dialog lookup request data
        required: true
      responses:
        "200":
          description: Dialog lookup successful

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/api/v4/source/agents.yaml =====

  /api/v4/agents:
    get:
      tags:
        - agents
      summary: Get available agents
      description: >
        Retrieve all available agents from the plugin's bridge API.
        If a user ID is provided, only agents accessible to that user are returned.

        ##### Permissions

        Must be authenticated.

        __Minimum server version__: 11.2
      operationId: GetAgents
      responses:
        "200":
          description: Agents retrieved successfully
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/AgentsResponse"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "500":
          $ref: "#/components/responses/InternalServerError"
  /api/v4/agents/status:
    get:
      tags:
        - agents
      summary: Get agents bridge status
      description: >
        Retrieve the status of the AI plugin bridge.
        Returns availability boolean and a reason code if unavailable.

        ##### Permissions

        Must be authenticated.

        __Minimum server version__: 11.2
      operationId: GetAgentsStatus
      responses:
        "200":
          description: Status retrieved successfully
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/AgentsIntegrityResponse"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "500":
          $ref: "#/components/responses/InternalServerError"
  /api/v4/llmservices:
    get:
      tags:
        - agents
      summary: Get available LLM services
      description: >
        Retrieve all available LLM services from the plugin's bridge API.
        If a user ID is provided, only services accessible to that user
        (via their permitted bots) are returned.

        ##### Permissions

        Must be authenticated.

        __Minimum server version__: 11.2
      operationId: GetLLMServices
      responses:
        "200":
          description: LLM services retrieved successfully
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/ServicesResponse"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "500":
          $ref: "#/components/responses/InternalServerError"


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/api/v4/source/audit_logging.yaml =====

  /api/v4/audit_logs/certificate:
    post:
      tags:
        - audit_logs
      summary: Upload audit log certificate
      description: |
        Upload the certificate to be used for TLS verification with the audit log service.

        ##### Permissions
        Must have `sysconsole_write_experimental_features` permission.

        __Minimum server version__: 10.9
      operationId: AddAuditLogCertificate
      requestBody:
        content:
          multipart/form-data:
            schema:
              type: object
              properties:
                certificate:
                  description: The certificate file
                  type: string
                  format: binary
              required:
                - certificate
      responses:
        "200":
          description: Certificate upload successful
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/StatusOK"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "413":
          $ref: "#/components/responses/TooLarge"
        "501":
          $ref: "#/components/responses/NotImplemented"

    delete:
      tags:
        - audit_logs
      summary: Remove audit log certificate
      description: |
        Delete the current certificate being used with the audit log service.

        ##### Permissions
        Must have `sysconsole_write_experimental_features` permission.

        __Minimum server version__: 9.5
      operationId: RemoveAuditLogCertificate
      responses:
        "200":
          description: Certificate deletion successful
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/StatusOK"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "501":
          $ref: "#/components/responses/NotImplemented"

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/api/v4/source/boards.yaml =====

  "/api/v4/boards":
    post:
      tags:
        - boards
      summary: Create a board channel
      description: |
        *__Experimental__: This endpoint is experimental and may change or be removed in a future release.*

        Create a new board channel. Boards are channels with a kanban view backed
        by linked properties (status and assignee by default), and live alongside
        regular channels but cannot be created or modified through the
        `/api/v4/channels` endpoints.

        The request body is a `Channel` object whose `type` must be `BO`
        (open board) or `BP` (private board). `team_id` and `display_name` are
        required.

        This endpoint is gated behind the `IntegratedBoards` feature flag. When
        the flag is off, the route is not registered and requests return `404`.

        ##### Permissions
        Must have `create_public_channel` for type `BO`, or
        `create_private_channel` for type `BP`, on the target team.
      operationId: CreateBoard
      requestBody:
        required: true
        description: Board channel to be created
        content:
          application/json:
            schema:
              type: object
              required:
                - team_id
                - type
                - display_name
              properties:
                team_id:
                  type: string
                  description: The team ID the board belongs to
                type:
                  type: string
                  enum: [BO, BP]
                  description: |
                    The board channel type.
                    * `BO` - open board (visible to all team members)
                    * `BP` - private board (visible to invited members)
                display_name:
                  type: string
                  description: Human-readable name shown in the UI. Must not be empty.
                name:
                  type: string
                  description: URL-safe channel name. Auto-generated if omitted.
                header:
                  type: string
                purpose:
                  type: string
      responses:
        "201":
          description: Board channel creation successful
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Channel"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "404":
          $ref: "#/components/responses/NotFound"
        "500":
          $ref: "#/components/responses/InternalServerError"

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/api/v4/source/bookmarks.yaml =====

  /api/v4/channels/{channel_id}/bookmarks:
    get:
      tags:
        - bookmarks
      summary: Get channel bookmarks for Channel
      description: |
        __Minimum server version__: 9.5
      operationId: ListChannelBookmarksForChannel
      parameters:
        - name: channel_id
          in: path
          description: Channel GUID
          required: true
          schema:
            type: string
        - name: bookmarks_since
          in: query
          description: |
            Timestamp to filter the bookmarks with. If set, the
            endpoint returns bookmarks that have been added, updated
            or deleted since its value
          required: false
          schema:
            type: number
            format: int64
      responses:
        "200":
          description: Channel Bookmarks retrieval successful
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: "#/components/schemas/ChannelBookmarkWithFileInfo"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"

    post:
      tags:
        - bookmarks
      summary: Create channel bookmark
      description: |
        Creates a new channel bookmark for this channel.

        __Minimum server version__: 9.5

        ##### Permissions
        Must have the `add_bookmark_public_channel` or
        `add_bookmark_private_channel` depending on the channel
        type. If the channel is a DM or GM, must be a non-guest
        member.
      operationId: CreateChannelBookmark
      parameters:
        - name: channel_id
          in: path
          description: Channel GUID
          required: true
          schema:
            type: string
      body:
      requestBody:
        content:
          application/json:
            schema:
              type: object
              required:
                - display_name
                - type
              properties:
                file_id:
                  type: string
                  description: The ID of the file associated with the channel bookmark. Required for bookmarks of type 'file'
                display_name:
                  type: string
                  description: The name of the channel bookmark
                link_url:
                  type: string
                  description: The URL associated with the channel bookmark. Required for bookmarks of type 'link'
                image_url:
                  type: string
                  description: The URL of the image associated with the channel bookmark. Optional, only applies for bookmarks of type 'link'
                emoji:
                  type: string
                  description: The emoji of the channel bookmark
                type:
                  type: string
                  enum: [link, file]
                  description: |
                    * `link` for channel bookmarks that reference a link. `link_url` is required
                    * `file` for channel bookmarks that reference a file. `file_id` is required
        description: Channel Bookmark object to be created
        required: true
      responses:
        "201":
          description: Channel Bookmark creation successful
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/ChannelBookmarkWithFileInfo"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"

  /api/v4/channels/{channel_id}/bookmarks/{bookmark_id}:
    patch:
      tags:
        - bookmarks
      summary: Update channel bookmark
      description: |
        Partially update a channel bookmark by providing only the
        fields you want to update. Ommited fields will not be
        updated. The fields that can be updated are defined in the
        request body, all other provided fields will be ignored.

        __Minimum server version__: 9.5

        ##### Permissions
        Must have the `edit_bookmark_public_channel` or
        `edit_bookmark_private_channel` depending on the channel
        type. If the channel is a DM or GM, must be a non-guest
        member.
      operationId: UpdateChannelBookmark
      parameters:
        - name: channel_id
          in: path
          description: Channel GUID
          required: true
          schema:
            type: string
        - name: bookmark_id
          in: path
          description: Bookmark GUID
          required: true
          schema:
            type: string
      body:
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                file_id:
                  type: string
                  description: The ID of the file associated with the channel bookmark. Required for bookmarks of type 'file'
                display_name:
                  type: string
                  description: The name of the channel bookmark
                sort_order:
                  type: integer
                  format: int64
                  description: The order of the channel bookmark
                link_url:
                  type: string
                  description: The URL associated with the channel bookmark. Required for type bookmarks of type 'link'
                image_url:
                  type: string
                  description: The URL of the image associated with the channel bookmark
                emoji:
                  type: string
                  description: The emoji of the channel bookmark
                type:
                  type: string
                  enum: [link, file]
                  description: |
                    * `link` for channel bookmarks that reference a link. `link_url` is required
                    * `file` for channel bookmarks that reference a file. `file_id` is required
        description: Channel Bookmark object to be updated
        required: true
      responses:
        "200":
          description: Channel Bookmark update successful
          content:

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/api/v4/source/bots.yaml =====

  /api/v4/bots:
    post:
      tags:
        - bots
      summary: Create a bot
      description: |
        Create a new bot account on the system. Username is required.
        ##### Permissions
        Must have `create_bot` permission.
        __Minimum server version__: 5.10
      operationId: CreateBot
      requestBody:
          description: Bot to be created
          required: true
          content:
            application/json:
              schema:
                type: object
                required:
                  - username
                properties:
                  username:
                    type: string
                  display_name:
                    type: string
                  description:
                    type: string
      responses:
        "201":
          description: Bot creation successful
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Bot"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
    get:
      tags:
        - bots
      summary: Get bots
      description: >
        Get a page of a list of bots.

        ##### Permissions

        Must have `read_bots` permission for bots you are managing, and `read_others_bots` permission for bots others are managing.

        __Minimum server version__: 5.10
      operationId: GetBots
      parameters:
        - name: page
          in: query
          description: The page to select.
          schema:
            type: integer
            default: 0
        - name: per_page
          in: query
          description: The number of users per page.
          schema:
            type: integer
            default: 60
        - name: include_deleted
          in: query
          description: If deleted bots should be returned.
          schema:
            type: boolean
        - name: only_orphaned
          in: query
          description: When true, only orphaned bots will be returned. A bot is considered
            orphaned if its owner has been deactivated.
          schema:
            type: boolean
      responses:
        "200":
          description: Bot page retrieval successful
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: "#/components/schemas/Bot"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
  "/api/v4/bots/{bot_user_id}":
    put:
      tags:
        - bots
      summary: Patch a bot
      description: >
        Partially update a bot by providing only the fields you want to update.
        Omitted fields will not be updated. The fields that can be updated are
        defined in the request body, all other provided fields will be ignored.

        ##### Permissions

        Must have `manage_bots` permission. 

        __Minimum server version__: 5.10
      operationId: PatchBot
      parameters:
        - name: bot_user_id
          in: path
          description: Bot user ID
          required: true
          schema:
            type: string
      requestBody:
          description: Bot to be created
          required: true
          content:
            application/json:
              schema:
                type: object
                required:
                  - username
                properties:
                  username:
                    type: string
                  display_name:
                    type: string
                  description:
                    type: string
      responses:
        "200":
          description: Bot patch successful
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Bot"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
    get:
      tags:
        - bots
      summary: Get a bot
      description: >
        Get a bot specified by its bot id.

        ##### Permissions

        Must have `read_bots` permission for bots you are managing, and `read_others_bots` permission for bots others are managing.

        __Minimum server version__: 5.10
      operationId: GetBot
      parameters:
        - name: bot_user_id
          in: path
          description: Bot user ID
          required: true
          schema:
            type: string
        - name: include_deleted
          in: query
          description: If deleted bots should be returned.
          schema:
            type: boolean
      responses:
        "200":
          description: Bot successfully retrieved.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Bot"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/api/v4/source/brand.yaml =====

  /api/v4/brand/image:
    get:
      tags:
        - brand
      summary: Get brand image
      description: >
        Get the previously uploaded brand image. Returns 404 if no brand image
        has been uploaded.

        ##### Permissions

        No permission required.
      operationId: GetBrandImage
      responses:
        "200":
          description: Brand image retrieval successful
          content:
            application/json:
              schema:
                type: string
        "404":
          $ref: "#/components/responses/NotFound"
        "501":
          $ref: "#/components/responses/NotImplemented"
    post:
      tags:
        - brand
      summary: Upload brand image
      description: |
        Uploads a brand image.
        ##### Permissions
        Must have `manage_system` permission.
      operationId: UploadBrandImage
      requestBody:
        content:
          multipart/form-data:
            schema:
              type: object
              properties:
                image:
                  description: The image to be uploaded
                  type: string
                  format: binary
              required:
                - image
      responses:
        "201":
          description: Brand image upload successful
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/StatusOK"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "413":
          $ref: "#/components/responses/TooLarge"
        "501":
          $ref: "#/components/responses/NotImplemented"
    delete:
      tags:
        - brand
      summary: Delete current brand image
      description: >
        Deletes the previously uploaded brand image. Returns 404 if no brand
        image has been uploaded.

        ##### Permissions

        Must have `manage_system` permission.

        __Minimum server version: 5.6__
      operationId: DeleteBrandImage
      responses:
        "200":
          description: Brand image succesfully deleted
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/StatusOK"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "404":
          $ref: "#/components/responses/NotFound"

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/api/v4/source/channels.yaml =====

  /api/v4/channels:
    get:
      tags:
        - channels
      summary: Get a list of all channels
      description: |
        ##### Permissions
        `manage_system`
      operationId: GetAllChannels
      parameters:
      - name: not_associated_to_group
        in: query
        description: A group id to exclude channels that are associated with that group via GroupChannel records. This can also be left blank with `not_associated_to_group=`.
        schema:
          type: string
      - name: page
        in: query
        description: The page to select.
        schema:
          type: integer
          default: 0
      - name: per_page
        in: query
        description: The number of channels per page.
        schema:
          type: integer
          default: 0
      - name: exclude_default_channels
        in: query
        description: Whether to exclude default channels (ex Town Square, Off-Topic) from the results.
        schema:
          type: boolean
          default: false
      - name: include_deleted
        in: query
        description: Include channels that have been archived. This correlates to the `DeleteAt` flag being set in the database.
        schema:
          type: boolean
          default: false
      - name: include_total_count
        in: query
        description: >-
          Appends a total count of returned channels inside the response object - ex: `{ "channels": [], "total_count" : 0 }`.
        schema:
          type: boolean
          default: false
      - name: exclude_policy_constrained
        in: query
        schema:
          type: boolean
          default: false
        description: >-
          If set to true, channels which are part of a data retention policy will be excluded.
          The `sysconsole_read_compliance` permission is required to use this parameter.

          __Minimum server version__: 5.35
      responses:
        "200":
          description: Channel list retrieval successful
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/ChannelListWithTeamData"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "404":
          $ref: "#/components/responses/NotFound"
    post:
      tags:
        - channels
      summary: Create a channel
      description: >
        Create a new channel.

        ##### Permissions

        If creating a public channel, `create_public_channel` permission is required. If creating a private channel, `create_private_channel` permission is required.
      operationId: CreateChannel
      requestBody:
        content:
          application/json:
            schema:
              type: object
              required:
                - name
                - display_name
                - type
                - team_id
              properties:
                team_id:
                  type: string
                  description: The team ID of the team to create the channel on
                name:
                  type: string
                  description: The unique handle for the channel, will be present in the
                    channel URL
                display_name:
                  type: string
                  description: The non-unique UI name for the channel
                purpose:
                  type: string
                  description: A short description of the purpose of the channel
                header:
                  type: string
                  description: Markdown-formatted text to display in the header of the
                    channel
                type:
                  type: string
                  description: "'O' for a public channel, 'P' for a private channel"
                managed_category_name:
                  type: string
                  description: The name of the managed category to assign this channel to.
                    Requires an Enterprise license and the `ManagedChannelCategories` feature flag
                    to be enabled.
                default_category_name:
                  type: string
                  description: Default sidebar category name for members when joining this channel.
                    Requires `EnableChannelCategorySorting` to be enabled on the server.
        description: Channel object to be created
        required: true
      responses:
        "201":
          description: Channel creation successful
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Channel"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
  /api/v4/channels/direct:
    post:
      tags:
        - channels
      summary: Create a direct message channel
      description: >
        Create a new direct message channel between two users.

        ##### Permissions

        Must be one of the two users and have `create_direct_channel` permission. Having the `manage_system` permission voids the previous requirements.
      operationId: CreateDirectChannel
      requestBody:
        content:
          application/json:
            schema:
              type: array
              items:
                type: string
              minItems: 2
              maxItems: 2
        description: The two user ids to be in the direct message
        required: true
      responses:
        "201":
          description: Direct channel creation successful
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Channel"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
  /api/v4/channels/group:
    post:
      tags:
        - channels
      summary: Create a group message channel
      description: >
        Create a new group message channel to group of users. If the logged in
        user's id is not included in the list, it will be appended to the end.


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/api/v4/source/cloud.yaml =====

  /api/v4/cloud/limits:
    get:
      tags:
        - cloud
      summary: Get cloud workspace limits
      description: >
        Retrieve any cloud workspace limits applicable to this instance.

        ##### Permissions

        Must be authenticated and be licensed for Cloud.

        __Minimum server version__: 7.0
        __Note:__ This is intended for internal use and is subject to change.
      operationId: GetCloudLimits
      responses:
        "200":
          description: Cloud workspace limits returned successfully
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/ProductLimits"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "500":
          $ref: "#/components/responses/InternalServerError"
        "501":
          $ref: "#/components/responses/NotImplemented"
  /api/v4/cloud/products:
    get:
      tags:
        - cloud
      summary: Get cloud products
      description: >
        Retrieve a list of all products that are offered for Mattermost Cloud.

        ##### Permissions

        Must have `manage_system` permission and be licensed for Cloud.

        __Minimum server version__: 5.28
        __Note:__ This is intended for internal use and is subject to change.
      operationId: GetCloudProducts
      responses:
        "200":
          description: Cloud products returned successfully
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: "#/components/schemas/Product"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "501":
          $ref: "#/components/responses/NotImplemented"
  /api/v4/cloud/customer:
    get:
      tags:
        - cloud
      summary: Get cloud customer
      description: >
        Retrieves the customer information for the Mattermost Cloud customer bound to this installation.

        ##### Permissions

        Must have `manage_system` permission and be licensed for Cloud.

        __Minimum server version__: 5.28
        __Note:__ This is intended for internal use and is subject to change.
      operationId: GetCloudCustomer
      responses:
        "200":
          description: Cloud customer returned successfully
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/CloudCustomer"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "501":
          $ref: "#/components/responses/NotImplemented"
    put:
      tags:
        - cloud
      summary: Update cloud customer
      description: >
        Updates the customer information for the Mattermost Cloud customer bound to this installation.

        ##### Permissions

        Must have `manage_system` permission and be licensed for Cloud.

        __Minimum server version__: 5.29
        __Note:__ This is intended for internal use and is subject to change.
      operationId: UpdateCloudCustomer
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                name:
                  type: string
                email:
                  type: string
                contact_first_name:
                  type: string
                contact_last_name:
                  type: string
                num_employees:
                  type: string
        description: Customer patch including information to update
        required: true
      responses:
        "200":
          description: Cloud customer updated successfully
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/CloudCustomer"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "501":
          $ref: "#/components/responses/NotImplemented"
  /api/v4/cloud/customer/address:
    put:
      tags:
        - cloud
      summary: Update cloud customer address
      description: >
        Updates the company address for the Mattermost Cloud customer bound to this installation.

        ##### Permissions

        Must have `manage_system` permission and be licensed for Cloud.

        __Minimum server version__: 5.29
        __Note:__ This is intended for internal use and is subject to change.
      operationId: UpdateCloudCustomerAddress
      requestBody:
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/Address"
        description: Company address information to update
        required: true
      responses:
        "200":
          description: Cloud customer address updated successfully
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/CloudCustomer"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "501":
          $ref: "#/components/responses/NotImplemented"
  /api/v4/cloud/validate-business-email:
    post:
      tags:
        - cloud
      summary: Validate business email
      description: >

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/api/v4/source/cluster.yaml =====

  /api/v4/cluster/status:
    get:
      tags:
        - cluster
      summary: Get cluster status
      description: >
        Get a list of all healthy nodes, including local information and
        status of each one. If a node is not present, it means it is not
        healthy.

        ##### Permissions

        Must have `manage_system` permission.
      operationId: GetClusterStatus
      responses:
        "200":
          description: Cluster status retrieval successful
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: "#/components/schemas/ClusterInfo"
        "403":
          $ref: "#/components/responses/Forbidden"

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/api/v4/source/commands.yaml =====

  /api/v4/commands:
    post:
      tags:
        - commands
      summary: Create a command
      description: |
        Create a command for a team.
        ##### Permissions
        `manage_slash_commands` for the team the command is in.
      operationId: CreateCommand
      requestBody:
        content:
          application/json:
            schema:
              type: object
              required:
                - team_id
                - method
                - trigger
                - url
              properties:
                team_id:
                  type: string
                  description: Team ID to where the command should be created
                method:
                  type: string
                  description: "`'P'` for post request, `'G'` for get request"
                trigger:
                  type: string
                  description: Activation word to trigger the command
                url:
                  type: string
                  description: The URL that the command will make the request
        description: command to be created
        required: true
      responses:
        "201":
          description: Command creation successful
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Command"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "501":
          $ref: "#/components/responses/NotImplemented"
    get:
      tags:
        - commands
      summary: List commands for a team
      description: |
        List commands for a team.
        ##### Permissions
        `manage_slash_commands` if need list custom commands.
      operationId: ListCommands
      parameters:
        - name: team_id
          in: query
          description: The team id.
          schema:
            type: string
        - name: custom_only
          in: query
          description: >
            To get only the custom commands. If set to false will get the custom

            if the user have access plus the system commands, otherwise just the system commands.
          schema:
            type: boolean
            default: false
      responses:
        "200":
          description: List Commands retrieve successful
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: "#/components/schemas/Command"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "501":
          $ref: "#/components/responses/NotImplemented"
  "/api/v4/teams/{team_id}/commands/autocomplete":
    get:
      tags:
        - commands
      summary: List autocomplete commands
      description: |
        List autocomplete commands in the team.
        ##### Permissions
        `view_team` for the team.
      operationId: ListAutocompleteCommands
      parameters:
        - name: team_id
          in: path
          description: Team GUID
          required: true
          schema:
            type: string
      responses:
        "200":
          description: Autocomplete commands retrieval successful
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: "#/components/schemas/Command"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
  "/api/v4/teams/{team_id}/commands/autocomplete_suggestions":
    get:
      tags:
        - commands
      summary: List commands' autocomplete data
      description: |
        List commands' autocomplete data for the team.
        ##### Permissions
        `view_team` for the team.
        __Minimum server version__: 5.24
      operationId: ListCommandAutocompleteSuggestions
      parameters:
        - name: team_id
          in: path
          description: Team GUID
          required: true
          schema:
            type: string
        - name: user_input
          in: query
          description: String inputted by the user.
          required: true
          schema:
            type: string
      responses:
        "200":
          description: Commands' autocomplete data retrieval successful
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: "#/components/schemas/AutocompleteSuggestion"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
  "/api/v4/commands/{command_id}":
    get:
      tags:
        - commands
      summary: Get a command
      description: >
        Get a command definition based on command id string.

        ##### Permissions

        Must have `manage_slash_commands` permission for the team the command is in.


        __Minimum server version__: 5.22
      operationId: GetCommandById
      parameters:
        - in: path
          name: command_id

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/api/v4/source/compliance.yaml =====

  /api/v4/compliance/reports:
    post:
      tags:
        - compliance
      summary: Create report
      description: |
        Create and save a compliance report.
        ##### Permissions
        Must have `manage_system` permission.
      operationId: CreateComplianceReport
      responses:
        "201":
          description: Compliance report creation successful
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Compliance"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "501":
          $ref: "#/components/responses/NotImplemented"
    get:
      tags:
        - compliance
      summary: Get reports
      description: >
        Get a list of compliance reports previously created by page, selected
        with `page` and `per_page` query parameters.

        ##### Permissions

        Must have `manage_system` permission.
      operationId: GetComplianceReports
      parameters:
        - name: page
          in: query
          description: The page to select.
          schema:
            type: integer
            default: 0
        - name: per_page
          in: query
          description: The number of reports per page.
          schema:
            type: integer
            default: 60
      responses:
        "200":
          description: Compliance reports retrieval successful
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: "#/components/schemas/Compliance"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "501":
          $ref: "#/components/responses/NotImplemented"
  "/api/v4/compliance/reports/{report_id}":
    get:
      tags:
        - compliance
      summary: Get a report
      description: |
        Get a compliance reports previously created.
        ##### Permissions
        Must have `manage_system` permission.
      operationId: GetComplianceReport
      parameters:
        - name: report_id
          in: path
          description: Compliance report GUID
          required: true
          schema:
            type: string
      responses:
        "200":
          description: Compliance report retrieval successful
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Compliance"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "501":
          $ref: "#/components/responses/NotImplemented"
  "/api/v4/compliance/reports/{report_id}/download":
    get:
      tags:
        - compliance
      summary: Download a report
      description: |
        Download the full contents of a report as a file.
        ##### Permissions
        Must have `manage_system` permission.
      operationId: DownloadComplianceReport
      parameters:
        - name: report_id
          in: path
          description: Compliance report GUID
          required: true
          schema:
            type: string
      responses:
        "200":
          description: The compliance report file
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "501":
          $ref: "#/components/responses/NotImplemented"

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/api/v4/source/content_flagging.yaml =====

  /api/v4/content_flagging/flag/config:
    get:
      summary: Get content flagging configuration
      description: |
        Returns the configuration for content flagging, including the list of available reasons for flagging content. This data is used to gather details from the user when they flag content.
        An enterprise advanced license is required.
      tags:
        - Content Flagging
      operationId: GetCFFlagConfig
      responses:
        '200':
          description: Configuration retrieved successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  reasons:
                    type: array
                    items:
                      type: string
                    description: List of reasons for flagging content
                  reporter_comment_required:
                    type: boolean
                    description: Indicates if a comment from the reporter is required when flagging content
        '404':
          description: Feature is disabled via the feature flag.
        '500':
          description: Internal server error.
        '501':
          description: Feature is disabled either via config or an Enterprise Advanced license is not available.
  /api/v4/content_flagging/team/{team_id}/status:
    get:
      summary: Get content flagging status for a team
      description: |
        Returns the content flagging status for a specific team, indicating whether content flagging is enabled on the specified team or not.
        An enterprise advanced license is required.
      tags:
        - Content Flagging
      parameters:
        - in: path
          name: team_id
          required: true
          schema:
            type: string
          description: The ID of the team to retrieve the content flagging status for
      operationId: GetCFTeamStatus
      responses:
        '200':
          description: Content flagging status retrieved successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  enabled:
                    type: boolean
                    description: Indicates if content flagging is enabled for the team
        '403':
          description: Forbidden - User does not have permission to access this team.
        '404':
          description: The specified team was not found or the feature is disabled via the feature flag.
        '500':
          description: Internal server error.
        '501':
          description: Feature is disabled either via config or an Enterprise Advanced license is not available.
  /api/v4/content_flagging/post/{post_id}/flag:
    post:
      summary: Flag a post
      description: |
        Flags a post with a reason and a comment. The user must have access to the channel to which the post belongs to.
        An enterprise advanced license is required.
      tags:
        - Content Flagging
      parameters:
        - in: path
          name: post_id
          required: true
          schema:
            type: string
          description: The ID of the post to be flagged
      operationId: PostCFPostFlag
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                reason:
                  type: string
                  description: The reason for flagging the post. This must be one of the configured reasons available for selection.
                comment:
                  type: string
                  description: Comment from the user flagging the post.
      responses:
        "200":
          description: Post flagged successfully
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/StatusOK"
        '400':
          description: Bad request - Invalid input data or missing required fields.
        '403':
          description: Forbidden - User does not have permission to flag this post.
        '404':
          description: Post not found or feature is disabled via the feature flag.
        '500':
          description: Internal server error.
        '501':
          description: Feature is disabled either via config or an Enterprise Advanced license is not available.
  /api/v4/content_flagging/fields:
    get:
      summary: Get content flagging property fields
      description: |
        Returns the list of property fields that can be associated with content flagging reports. These fields are used for storing metadata about a post's flag.
        An enterprise advanced license is required.
      tags:
        - Content Flagging
      operationId: GetCFFields
      responses:
        '200':
          description: Custom fields retrieved successfully
          content:
            application/json:
              schema:
                type: object
                description: A map of property field names to their definitions
                additionalProperties:
                  $ref: "#/components/schemas/PropertyField"
        '404':
          description: Feature is disabled via the feature flag.
        '500':
          description: Internal server error.
        '501':
          description: Feature is disabled either via config or an Enterprise Advanced license is not available.
  /api/v4/content_flagging/post/{post_id}/field_values:
    get:
      summary: Get content flagging property field values for a post
      description: |
        Returns the property field values associated with content flagging reports for a specific post. These values provide additional context about the flags on the post.
        An enterprise advanced license is required.
      tags:
        - Content Flagging
      parameters:
        - in: path
          name: post_id
          required: true
          schema:
            type: string
          description: The ID of the post to retrieve property field values for
      operationId: GetCFPostFieldValues
      responses:
        '200':
          description: Property field values retrieved successfully
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: "#/components/schemas/PropertyValue"
                description: An array of property field values associated with the post
        '403':
          description: Forbidden - User does not have permission to access this post.
        '404':
          description: Post not found or feature is disabled via the feature flag.
        '500':
          description: Internal server error.
        '501':
          description: Feature is disabled either via config or an Enterprise Advanced license is not available.
  /api/v4/content_flagging/post/{post_id}:
    get:
        summary: Get a flagged post with all its content.
        description: |
            Returns the flagged post with all its data, even if it is soft-deleted. This endpoint is only accessible by content reviewers. A content reviewer can only fetch flagged posts from this API if the post is indeed flagged and they are a content reviewer of the post's team.
            An enterprise advanced license is required.
        tags:
            - Content Flagging
        parameters:

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/api/v4/source/custom_profile_attributes.yaml =====

  "/api/v4/custom_profile_attributes/fields":
    get:
      tags:
        - custom profile attributes
      summary: List all the Custom Profile Attributes fields
      description: |
        List all the Custom Profile Attributes fields.

        __Minimum server version__: 10.5

        ##### Permissions
        Must be authenticated.
      operationId: ListAllCPAFields
      responses:
        "200":
          description: Custom Profile Attributes fetch successful. Result may be empty.
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: "#/components/schemas/PropertyField"
        "401":
          $ref: "#/components/responses/Unauthorized"

    post:
      tags:
        - custom profile attributes
      summary: Create a Custom Profile Attribute field
      description: |
        Create a new Custom Profile Attribute field on the system.

        __Minimum server version__: 10.5

        ##### Permissions
        Must have `manage_system` permission.
      operationId: CreateCPAField
      requestBody:
        content:
          application/json:
            schema:
              type: object
              required:
                - name
                - type
              properties:
                name:
                  type: string
                  description: >
                    The internal identifier for this attribute. Must match
                    `^[A-Za-z_][A-Za-z0-9_]*$` and must not be a CEL reserved
                    word (true, false, null, in, as, break, const, continue, else,
                    for, function, if, import, let, loop, package, namespace,
                    return, var, void, while). This name is used in ABAC policy
                    expressions as `user.attributes.<name>`.
                type:
                  type: string
                attrs:
                  type: object
                  properties:
                    visibility:
                      type: string
                      description: "Visibility of the attribute"
                      enum: ["hidden", "when_set", "always"]
                      default: "when_set"
                    sort_order:
                      type: number
                      description: "Sort order for displaying this attribute"
                    options:
                      type: array
                      description: "Options for select/multiselect fields"
                      items:
                        type: object
                        properties:
                          name:
                            type: string
                          color:
                            type: string
                    value_type:
                      type: string
                      description: "Type of text value"
                      enum: ["email", "url", "phone"]
                    ldap:
                      type: string
                      description: "LDAP attribute for syncing"
                    saml:
                      type: string
                      description: "SAML attribute for syncing"
                    protected:
                      type: boolean
                      description: "If true, the field is read-only and cannot be modified."
                    source_plugin_id:
                      type: string
                      description: "The ID of the plugin that created this field. This attribute cannot be changed."
                    access_mode:
                      type: string
                      description: "Access mode of the field"
                      enum: ["", "source_only", "shared_only"]
                      default: ""
                    display_name:
                      type: string
                      description: >
                        Human-readable label shown in the UI. Defaults to the field
                        `name` when omitted or empty. Maximum 255 characters.
      responses:
        "201":
          description: Custom Profile Attribute field creation successful
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/PropertyField"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "422":
          description: >
            Validation error. Returned when `name` does not match the
            required identifier pattern, is a CEL reserved word, or when
            `attrs.display_name` exceeds 255 characters.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/AppError"

  "/api/v4/custom_profile_attributes/fields/{field_id}":
    patch:
      tags:
        - custom profile attributes
      summary: Patch a Custom Profile Attribute field
      description: |
        Partially update a Custom Profile Attribute field by providing
        only the fields you want to update. Omitted fields will not be
        updated. The fields that can be updated are defined in the
        request body, all other provided fields will be ignored.

        **Note:** Fields with `attrs.protected = true` cannot be
        modified and will return an error.

        __Minimum server version__: 10.5

        ##### Permissions
        Must have `manage_system` permission.
      operationId: PatchCPAField
      parameters:
        - name: field_id
          in: path
          description: Custom Profile Attribute field GUID
          required: true
          schema:
            type: string
      requestBody:
        description: Custom Profile Attribute field that is to be updated
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                name:
                  type: string
                  description: >
                    New name for the attribute. When changed, must match
                    `^[A-Za-z_][A-Za-z0-9_]*$` and must not be a CEL reserved
                    word. Pre-existing fields with non-conforming names remain
                    patchable on all other attributes; the validation only fires
                    when `name` actually changes.
                type:
                  type: string
                attrs:
                  type: object
                  properties:
                    visibility:
                      type: string
                      description: "Visibility of the attribute"
                      enum: ["hidden", "when_set", "always"]
                      default: "when_set"
                    sort_order:

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/api/v4/source/dataretention.yaml =====

  /api/v4/data_retention/policy:
    get:
      tags:
        - data retention
      summary: Get the global data retention policy
      description: |
        Gets the current global data retention policy details from the server,
        including what data should be purged and the cutoff times for each data
        type that should be purged.
        
        __Minimum server version__: 4.3
        
        ##### Permissions
        Requires an active session but no other permissions.

        ##### License
        Requires an E20 license.
      operationId: GetDataRetentionPolicy
      responses:
        "200":
          description: Global data retention policy details retrieved successfully.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/GlobalDataRetentionPolicy"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "500":
          $ref: "#/components/responses/InternalServerError"
        "501":
          $ref: "#/components/responses/NotImplemented"
  /api/v4/data_retention/policies_count:
    get:
      tags:
        - data retention
      summary: Get the number of granular data retention policies
      description: |
        Gets the number of granular (i.e. team or channel-specific) data retention
        policies from the server.

        __Minimum server version__: 5.35

        ##### Permissions
        Must have the `sysconsole_read_compliance_data_retention` permission.

        ##### License
        Requires an E20 license.
      operationId: GetDataRetentionPoliciesCount
      responses:
        "200":
          description: Number of retention policies retrieved successfully.
          content:
            application/json:
              schema:
                type: object
                properties:
                  total_count:
                    type: integer
                    description: The number of granular retention policies.
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "500":
          $ref: "#/components/responses/InternalServerError"
        "501":
          $ref: "#/components/responses/NotImplemented"
  /api/v4/data_retention/policies:
    get:
      tags:
        - data retention
      summary: Get the granular data retention policies
      description: |
        Gets details about the granular (i.e. team or channel-specific) data retention
        policies from the server.

        __Minimum server version__: 5.35

        ##### Permissions
        Must have the `sysconsole_read_compliance_data_retention` permission.

        ##### License
        Requires an E20 license.
      operationId: GetDataRetentionPolicies
      parameters:
        - name: page
          in: query
          description: The page to select.
          schema:
            type: integer
            default: 0
        - name: per_page
          in: query
          description: The number of policies per page.
          schema:
            type: integer
            default: 60
      responses:
        "200":
          description: Retention policies' details retrieved successfully.
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: "#/components/schemas/DataRetentionPolicyWithTeamAndChannelCounts"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "500":
          $ref: "#/components/responses/InternalServerError"
        "501":
          $ref: "#/components/responses/NotImplemented"
    post:
      tags:
        - data retention
      summary: Create a new granular data retention policy
      description: |
        Creates a new granular data retention policy with the specified display
        name and post duration.

        __Minimum server version__: 5.35

        ##### Permissions
        Must have the `sysconsole_write_compliance_data_retention` permission.

        ##### License
        Requires an E20 license.
      operationId: CreateDataRetentionPolicy
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/DataRetentionPolicyCreate"
      responses:
        "201":
          description: Retention policy successfully created.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/DataRetentionPolicyWithTeamAndChannelCounts"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "500":
          $ref: "#/components/responses/InternalServerError"
        "501":
          $ref: "#/components/responses/NotImplemented"
  "/api/v4/data_retention/policies/{policy_id}":
    get:
      tags:
        - data retention
      summary: Get a granular data retention policy
      description: |
        Gets details about a granular data retention policies by ID.

        __Minimum server version__: 5.35

        ##### Permissions
        Must have the `sysconsole_read_compliance_data_retention` permission.

        ##### License
        Requires an E20 license.
      operationId: GetDataRetentionPolicyByID
      parameters:
      - name: policy_id
        in: path
        description: The ID of the granular retention policy.
        required: true
        schema:
          type: string
      responses:
        "200":
          description: Retention policy's details retrieved successfully.
          content:

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/api/v4/source/definitions.yaml =====

components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
  responses:
    Forbidden:
      description: Do not have appropriate permissions
      content:
        application/json:
          schema:
            $ref: "#/components/schemas/AppError"
    Unauthorized:
      description: No access token provided
      content:
        application/json:
          schema:
            $ref: "#/components/schemas/AppError"
    BadRequest:
      description: Invalid or missing parameters in URL or request body
      content:
        application/json:
          schema:
            $ref: "#/components/schemas/AppError"
    NotFound:
      description: Resource not found
      content:
        application/json:
          schema:
            $ref: "#/components/schemas/AppError"
    Conflict:
      description: Request conflicts with current state of the resource
      content:
        application/json:
          schema:
            $ref: "#/components/schemas/AppError"
    TooLarge:
      description: Content too large
      content:
        application/json:
          schema:
            $ref: "#/components/schemas/AppError"
    NotImplemented:
      description: Feature is disabled
      content:
        application/json:
          schema:
            $ref: "#/components/schemas/AppError"
    TooManyRequests:
      description: Too many requests
      content:
        application/json:
          schema:
            $ref: "#/components/schemas/AppError"
    InternalServerError:
      description: Something went wrong with the server
      content:
        application/json:
          schema:
            $ref: "#/components/schemas/AppError"
    BadGateway:
      description: Bad gateway
      content:
        application/json:
          schema:
            $ref: "#/components/schemas/AppError"
  schemas:
    User:
      type: object
      properties:
        id:
          type: string
        create_at:
          description: The time in milliseconds a user was created
          type: integer
          format: int64
        update_at:
          description: The time in milliseconds a user was last updated
          type: integer
          format: int64
        delete_at:
          description: The time in milliseconds a user was deleted
          type: integer
          format: int64
        username:
          type: string
        first_name:
          type: string
        last_name:
          type: string
        nickname:
          type: string
        email:
          type: string
        email_verified:
          type: boolean
        auth_service:
          type: string
        roles:
          type: string
        locale:
          type: string
        notify_props:
          $ref: "#/components/schemas/UserNotifyProps"
        props:
          type: object
        last_password_update:
          type: integer
          format: int64
        last_picture_update:
          type: integer
          format: int64
        failed_attempts:
          type: integer
        mfa_active:
          type: boolean
        timezone:
          $ref: "#/components/schemas/Timezone"
        terms_of_service_id:
          description: ID of accepted terms of service, if any. This field is not present
            if empty.
          type: string
        terms_of_service_create_at:
          description: The time in milliseconds the user accepted the terms of service
          type: integer
          format: int64
    UsersStats:
      type: object
      properties:
        total_users_count:
          type: integer
    KnownUsers:
      type: array
      properties:
        items:
          type: string
    Team:
      type: object
      properties:
        id:
          type: string
        create_at:
          description: The time in milliseconds a team was created
          type: integer
          format: int64
        update_at:
          description: The time in milliseconds a team was last updated
          type: integer
          format: int64
        delete_at:
          description: The time in milliseconds a team was deleted
          type: integer
          format: int64
        display_name:
          type: string
        name:
          type: string
        description:
          type: string
        email:
          type: string
        type:
          type: string
        allowed_domains:
          type: string
        invite_id:
          type: string
        allow_open_invite:
          type: boolean
        policy_id:
          type: string
          description: >-
            The data retention policy to which this team has been assigned. If no such policy exists,
            or the caller does not have the `sysconsole_read_compliance_data_retention` permission,
            this field will be null.
    TeamStats:
      type: object
      properties:
        team_id:
          type: string

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/api/v4/source/elasticsearch.yaml =====

  /api/v4/elasticsearch/test:
    post:
      tags:
        - elasticsearch
      summary: Test Elasticsearch configuration
      description: >
        Test the current Elasticsearch configuration to see if the Elasticsearch
        server can be contacted successfully.

        Optionally provide a configuration in the request body to test. If no valid configuration is present in the

        request body the current server configuration will be tested.


        __Minimum server version__: 4.1

        ##### Permissions

        Must have `manage_system` permission.
      operationId: TestElasticsearch
      responses:
        "200":
          description: Elasticsearch test successful
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/StatusOK"
        "400":
          $ref: "#/components/responses/BadRequest"
        "500":
          $ref: "#/components/responses/InternalServerError"
        "501":
          $ref: "#/components/responses/NotImplemented"
  /api/v4/elasticsearch/purge_indexes:
    post:
      tags:
        - elasticsearch
      summary: Purge all Elasticsearch indexes
      description: >
        Deletes all Elasticsearch indexes and their contents. After calling this
        endpoint, it is

        necessary to schedule a new Elasticsearch indexing job to repopulate the indexes.

        __Minimum server version__: 4.1

        ##### Permissions

        Must have `manage_system` permission.
      operationId: PurgeElasticsearchIndexes
      responses:
        "200":
          description: Indexes purged successfully.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/StatusOK"
        "500":
          $ref: "#/components/responses/InternalServerError"
        "501":
          $ref: "#/components/responses/NotImplemented"

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/api/v4/source/emoji.yaml =====

  /api/v4/emoji:
    post:
      tags:
        - emoji
      summary: Create a custom emoji
      description: |
        Create a custom emoji for the team.
        ##### Permissions
        Must be authenticated.
      operationId: CreateEmoji
      requestBody:
        content:
          multipart/form-data:
            schema:
              type: object
              properties:
                image:
                  description: A file to be uploaded
                  type: string
                  format: binary
                emoji:
                  description: A JSON object containing a `name` field with the name of the
                    emoji and a `creator_id` field with the id of the
                    authenticated user.
                  type: string
              required:
                - image
                - emoji
      responses:
        "201":
          description: Emoji creation successful
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Emoji"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "413":
          $ref: "#/components/responses/TooLarge"
        "501":
          $ref: "#/components/responses/NotImplemented"
    get:
      tags:
        - emoji
      summary: Get a list of custom emoji
      description: >
        Get a page of metadata for custom emoji on the system. Since server
        version 4.7, sort using the `sort` query parameter.

        ##### Permissions

        Must be authenticated.
      operationId: GetEmojiList
      parameters:
        - name: page
          in: query
          description: The page to select.
          schema:
            type: integer
            default: 0
        - name: per_page
          in: query
          description: The number of emojis per page.
          schema:
            type: integer
            default: 60
        - name: sort
          in: query
          description: Either blank for no sorting or "name" to sort by emoji names.
            Minimum server version for sorting is 4.7.
          schema:
            type: string
            default: ""
      responses:
        "200":
          description: Emoji list retrieval successful
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Emoji"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "501":
          $ref: "#/components/responses/NotImplemented"
  "/api/v4/emoji/{emoji_id}":
    get:
      tags:
        - emoji
      summary: Get a custom emoji
      description: |
        Get some metadata for a custom emoji.
        ##### Permissions
        Must be authenticated.
      operationId: GetEmoji
      parameters:
        - name: emoji_id
          in: path
          description: Emoji GUID
          required: true
          schema:
            type: string
      responses:
        "200":
          description: Emoji retrieval successful
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Emoji"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "404":
          $ref: "#/components/responses/NotFound"
        "501":
          $ref: "#/components/responses/NotImplemented"
    delete:
      tags:
        - emoji
      summary: Delete a custom emoji
      description: >
        Delete a custom emoji.

        ##### Permissions

        Must have the `manage_team` or `manage_system` permissions or be the user who created the emoji.
      operationId: DeleteEmoji
      parameters:
        - name: emoji_id
          in: path
          description: Emoji GUID
          required: true
          schema:
            type: string
      responses:
        "200":
          description: Emoji delete successful
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Emoji"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "501":
          $ref: "#/components/responses/NotImplemented"
  "/api/v4/emoji/name/{emoji_name}":
    get:
      tags:
        - emoji
      summary: Get a custom emoji by name
      description: |
        Get some metadata for a custom emoji using its name.
        ##### Permissions
        Must be authenticated.

        __Minimum server version__: 4.7
      operationId: GetEmojiByName
      parameters:
        - name: emoji_name
          in: path
          description: Emoji name
          required: true
          schema:
            type: string
      responses:
        "200":
          description: Emoji retrieval successful
          content:

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/api/v4/source/exports.yaml =====

  "/api/v4/exports":
    get:
      tags:
        - exports
      summary: List export files
      description: >
        Lists all available export files.

        __Minimum server version__: 5.33

        ##### Permissions

        Must have `manage_system` permissions.
      operationId: ListExports
      responses:
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "500":
          $ref: "#/components/responses/InternalServerError"
  "/api/v4/exports/{export_name}":
    get:
      tags:
        - exports
      summary: Download an export file
      description: |
        Downloads an export file.


        __Minimum server version__: 5.33

        ##### Permissions

        Must have `manage_system` permissions.
      operationId: DownloadExport
      parameters:
        - name: export_name
          in: path
          description: The name of the export file to download
          required: true
          schema:
            type: string
      responses:
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "404":
          $ref: "#/components/responses/NotFound"
        "500":
          $ref: "#/components/responses/InternalServerError"
    delete:
      tags:
        - exports
      summary: Delete an export file
      description: |
        Deletes an export file.


        __Minimum server version__: 5.33

        ##### Permissions

        Must have `manage_system` permissions.
      operationId: DeleteExport
      parameters:
        - name: export_name
          in: path
          description: The name of the export file to delete
          required: true
          schema:
            type: string
      responses:
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "500":
          $ref: "#/components/responses/InternalServerError"
  "/api/v4/exports/{export_name}/presign-url":
    post:
      tags:
        - exports
      summary: Create a presigned URL for export download
      description: |
        Creates a presigned URL for downloading an export file.

        __Minimum server version__: 5.33

        ##### Permissions
        Must have `manage_system` permission.
      operationId: PresignExport
      parameters:
        - name: export_name
          in: path
          description: The name of the export file
          required: true
          schema:
            type: string
      responses:
        "200":
          description: Presigned URL created successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  url:
                    type: string
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "404":
          $ref: "#/components/responses/NotFound"
        "500":
          $ref: "#/components/responses/InternalServerError"

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/api/v4/source/files.yaml =====

  /api/v4/files:
    post:
      tags:
        - files
      summary: Upload a file
      description: >
        Uploads a file that can later be attached to a post.


        This request can either be a multipart/form-data request with a channel_id, files and optional

        client_ids defined in the FormData, or it can be a request with the channel_id and filename

        defined as query parameters with the contents of a single file in the body of the request.


        Only multipart/form-data requests are supported by server versions up to and including 4.7.

        Server versions 4.8 and higher support both types of requests.


        __Minimum server version__: 9.4

        Starting with server version 9.4 when uploading a file for a channel bookmark, the bookmark=true query
        parameter should be included in the query string


        ##### Permissions

        Must have `upload_file` permission.
      operationId: UploadFile
      parameters:
        - name: channel_id
          in: query
          description: The ID of the channel that this file will be uploaded to
          required: false
          schema:
            type: string
        - name: filename
          in: query
          description: The name of the file to be uploaded
          required: false
          schema:
            type: string
      requestBody:
        content:
          multipart/form-data:
            schema:
              type: object
              properties:
                files:
                  description: A file to be uploaded
                  type: string
                  format: binary
                channel_id:
                  description: The ID of the channel that this file will be uploaded to
                  type: string
                client_ids:
                  description: A unique identifier for the file that will be returned in
                    the response
                  type: string
      responses:
        "201":
          description: Corresponding lists of the provided client_ids and the metadata that
            has been stored in the database for each one
          content:
            application/json:
              schema:
                type: object
                properties:
                  file_infos:
                    description: A list of file metadata that has been stored in the
                      database
                    type: array
                    items:
                      $ref: "#/components/schemas/FileInfo"
                  client_ids:
                    description: A list of the client_ids that were provided in the request
                    type: array
                    items:
                      type: string
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "413":
          $ref: "#/components/responses/TooLarge"
        "501":
          $ref: "#/components/responses/NotImplemented"
  "/api/v4/files/{file_id}":
    get:
      tags:
        - files
      summary: Get a file
      description: |
        Gets a file that has been uploaded previously.
        ##### Permissions
        Must have `read_channel` permission or be uploader of the file.
      operationId: GetFile
      parameters:
        - name: file_id
          in: path
          description: The ID of the file to get
          required: true
          schema:
            type: string
      responses:
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          description: Do not have appropriate permissions
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/AppError"
          headers:
            First-Inaccessible-File-Time:
              schema:
                type: integer
              description: This header is included with the value "1" if the file is past the cloud's plan limit.
        "404":
          $ref: "#/components/responses/NotFound"
        "501":
          $ref: "#/components/responses/NotImplemented"
    head:
      tags:
        - files
      summary: Get file metadata headers
      description: |
        Performs the same permission and existence checks as getting a file, but returns headers only.
      operationId: HeadFile
      parameters:
        - name: file_id
          in: path
          description: The ID of the file to get
          required: true
          schema:
            type: string
      responses:
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "404":
          $ref: "#/components/responses/NotFound"
        "501":
          $ref: "#/components/responses/NotImplemented"
  "/api/v4/files/{file_id}/thumbnail":
    get:
      tags:
        - files
      summary: Get a file's thumbnail
      description: |
        Gets a file's thumbnail.
        ##### Permissions
        Must have `read_channel` permission or be uploader of the file.
      operationId: GetFileThumbnail
      parameters:
        - name: file_id
          in: path
          description: The ID of the file to get
          required: true
          schema:
            type: string
      responses:
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          description: Do not have appropriate permissions
          content:
            application/json:
              schema:

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/api/v4/source/groups.yaml =====

  /api/v4/groups:
    get:
      tags:
        - groups
      summary: Get groups
      description: >
        Retrieve a list of all groups not associated to a particular channel or
        team.


        If you use `not_associated_to_team`, you must be a team admin for that particular team (permission to manage that team).


        If you use `not_associated_to_channel`, you must be a channel admin for that particular channel (permission to manage that channel).


        __Minimum server version__: 5.11
      operationId: GetGroups
      parameters:
        - name: page
          in: query
          description: The page to select.
          schema:
            type: integer
            default: 0
        - name: per_page
          in: query
          description: The number of groups per page.
          schema:
            type: integer
            default: 60
        - name: q
          in: query
          description: String to pattern match the `name` and `display_name` field. Will
            return all groups whose `name` and `display_name` field match any of
            the text.
          schema:
            type: string
        - name: include_member_count
          in: query
          description: Boolean which adds the `member_count` attribute to each group JSON
            object
          schema:
            type: boolean
        - name: not_associated_to_team
          in: query
          description: Team GUID which is used to return all the groups not associated to
            this team
          schema:
            type: string
        - name: not_associated_to_channel
          in: query
          description: Group GUID which is used to return all the groups not associated to
            this channel
          schema:
            type: string
        - name: since
          in: query
          description: >
            Only return groups that have been modified since the given Unix
            timestamp (in milliseconds). All modified groups, including deleted
            and created groups, will be returned.

            __Minimum server version__: 5.24
          schema:
            type: integer
        - name: filter_allow_reference
          in: query
          description: Boolean which filters the group entries with the `allow_reference` attribute set.
          schema:
            type: boolean
            default: false
      responses:
        "200":
          description: Group list retrieval successful
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: "#/components/schemas/Group"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "501":
          $ref: "#/components/responses/NotImplemented"
    post:
      tags:
        - groups
      summary: Create a custom group
      description: |
        Create a `custom` type group.

        #### Permission
        Must have `create_custom_group` permission.

        __Minimum server version__: 6.3
      operationId: CreateGroup
      requestBody:
        content:
          application/json:
            schema:
              type: object
              required:
                - name
                - display_name
                - source
                - allow_reference
                - user_ids
              properties:
                name:
                  type: string
                  description: The unique group name used for at-mentioning.
                display_name:
                  type: string
                  description: The display name of the group which can include spaces.
                source:
                  type: string
                  description: Must be `custom`
                allow_reference:
                  type: boolean
                  description: Must be true
                user_ids:
                  type: array
                  description: The user ids of the group members to add.
                  items:
                    type: string
        description: Group object and initial members.
        required: true
      responses:
        "501":
          description: |
            Group has an invalid `source`, or
            `allow_reference` is not `true`, or
            group has a `remote_id`.
        "400":
          $ref: "#/components/responses/BadRequest"
        "201":
          description: Group creation and memberships successful.
        "403":
          $ref: "#/components/responses/Forbidden"
  "/api/v4/groups/{group_id}":
    get:
      tags:
        - groups
      summary: Get a group
      description: |
        Get group from the provided group id string

        ##### Permissions
        Must have `manage_system` permission.

        __Minimum server version__: 5.11
      operationId: GetGroup
      parameters:
        - name: group_id
          in: path
          description: Group GUID
          required: true
          schema:
            type: string
      responses:
        "200":
          description: Group retrieval successful
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Group"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "501":
          $ref: "#/components/responses/NotImplemented"
    delete:

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/api/v4/source/imports.yaml =====

  "/api/v4/imports":
    get:
      tags:
        - imports
      summary: List import files
      description: >
        Lists all available import files.


        __Minimum server version__: 5.31

        ##### Permissions

        Must have `manage_system` permissions.
      operationId: ListImports
      responses:
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "404":
          $ref: "#/components/responses/NotFound"
  "/api/v4/imports/{import_name}":
    delete:
      tags:
        - imports
      summary: Delete an import file
      description: |
        Deletes an import file.


        __Minimum server version__: 5.31

        ##### Permissions

        Must have `manage_system` permissions.
      operationId: DeleteImport
      parameters:
        - name: import_name
          in: path
          description: The name of the import file to delete
          required: true
          schema:
            type: string
      responses:
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "500":
          $ref: "#/components/responses/InternalServerError"

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/api/v4/source/introduction.yaml =====

openapi: 3.0.0
info:
  description: >
    The Mattermost Web Services API enables Mattermost clients and third-party applications
    to interact with Mattermost servers.


    [Official JavaScript and Golang drivers](#/#official-drivers)
    are available to simplify API integration.


    By using this API, you agree to our [terms of service](https://about.mattermost.com/default-terms/).


    [Find out more about Mattermost](https://about.mattermost.com/)

    ## Contents

    ### Core Concepts

    * [Schema & Conventions](#/#schema--conventions)

    * [Authentication](#/#authentication)

    * [Rate Limiting](#/#rate-limiting)

    * [Error Handling](#/#error-handling)

    * [WebSocket](#/#websocket)

      * [Authentication](#/#authentication-1)

      * [WebSocket Events](#/#websocket-events)

      * [WebSocket API](#/#websocket-api)

    ### Drivers

    * [Official Drivers](#/#official-drivers)

    * [Community-built Drivers](#/#community-built-drivers)

    ### Community

    * [Support](#/#support)

    * [Contributing](#/#contributing)


    ## Schema & Conventions

    - All API access is through HTTP(S) requests at `your-mattermost-url/api/v4`.

    - All request and response bodies are `application/json`.

    - When using endpoints that require a user id, the string `me` can be used in place
    of the user id to indicate the action is to be taken for the logged in user.

    - For all endpoints that implement pagination via the `per_page` parameter:

      - Maximum items per page: 200 (requests exceeding this will be silently truncated)

      - Default value if a paged API requires a `per_page` parameter and it is not provided: 60

    ## Authentication

      There are multiple ways to authenticate against the Mattermost API.

      All examples assume there is a Mattermost instance running at http://localhost:8065.

      ### Session Token

      Make an HTTP POST to `your-mattermost-url/api/v4/users/login` with a JSON
      body indicating the user's `login_id`, `password` and optionally the MFA
      `token`. The `login_id` can be an email, username or an AD/LDAP ID
      depending on the system's configuration.

      ```bash
      curl -i -d '{"login_id":"someone@nowhere.com","password":"thisisabadpassword"}' http://localhost:8065/api/v4/users/login
      ```

      NOTE: If you're running cURL on windows, you will have to change the single quotes to double quotes, and escape the inner double quotes with backslash, like below:


      ```bash
      curl -i -d "{\"login_id\":\"someone@nowhere.com\",\"password\":\"thisisabadpassword\"}" http://localhost:8065/api/v4/users/login
      ```

      If successful, the response will contain a `Token` header and a user object in the body.

      ```http
      HTTP/1.1 200 OK
      Content-Type: application/json
      Permissions-Policy:
      Referrer-Policy: no-referrer
      Token: ckh3t4knu3fzujt76o57f5jo4w
      Vary: Origin
      Vary: Accept-Encoding
      X-Content-Type-Options: nosniff
      X-Request-Id: bk3uzm335jr9tnoh4mcsybmmjr
      X-Version-Id: 10.6.0.13685270376.215f100adf6ccda09afcaaa84ac4bfbd.true
      Date: Fri, 28 Mar 2025 09:33:22 GMT
      Content-Length: 796

      {{user object as json}}
      ```

      Include the `Token` as part of the `Authorization` header on your future API requests with the `Bearer` method.

      ```bash
      curl -i -H 'Authorization: Bearer ckh3t4knu3fzujt76o57f5jo4w' http://localhost:8065/api/v4/users/me
      ```
      Alternatively, include the `Token` as your `MMAUTHTOKEN` cookie value on your future API requests:

      ```bash
      curl -i -H 'Cookie: MMAUTHTOKEN=ckh3t4knu3fzujt76o57f5jo4w' http://localhost:8065/api/v4/users/me
      ```


      You should now be able to access the API as the user you logged in as.


      ### Personal Access Tokens

      Using [personal access tokens](https://developers.mattermost.com/integrate/reference/personal-access-token/) is very similar to using a session token. The only real difference is that session tokens will expire, while personal access tokens will live until they are manually revoked by the user or an admin.

      Just like session tokens, include the personal access token as part of the `Authorization` header in your requests using the `Bearer` method. Assuming our personal access token is `9xuqwrwgstrb3mzrxb83nb357a`, we could use it as shown below.

      ```bash
      curl -i -H 'Authorization: Bearer 9xuqwrwgstrb3mzrxb83nb357a' http://localhost:8065/api/v4/users/me
      ```

    ## Rate Limiting
      Whenever you make an HTTP request to the Mattermost API you might notice
      the following headers included in the response:

      ```http
      X-Ratelimit-Limit: 10
      X-Ratelimit-Remaining: 9
      X-Ratelimit-Reset: 1441983590
      ```


      These headers are telling you your current rate limit status.


      | Header                  | Description                                                        |
      |:-----------------------|:-------------------------------------------------------------------|
      | X-Ratelimit-Limit      | The maximum number of requests you can make per second.            |
      | X-Ratelimit-Remaining  | The number of requests remaining in the current window.            |
      | X-Ratelimit-Reset      | The remaining UTC epoch seconds before the rate limit resets.      |

      If you exceed your rate limit for a window you will receive the following error in the body of the response:

      ```http
      HTTP/1.1 429 Too Many Requests
      Date: Tue, 10 Sep 2015 11:20:28 GMT
      X-RateLimit-Limit: 10
      X-RateLimit-Remaining: 0
      X-RateLimit-Reset: 1

      limit exceeded
      ```

    ## Error Handling

      All errors will return an appropriate HTTP response code along with the
      following JSON body:

      ```json
      {
          "id": "the.error.id",
          "message": "Something went wrong", // the reason for the error
          "request_id": "", // the ID of the request
          "status_code": 0, // the HTTP status code
          "is_oauth": false // whether the error is OAuth specific
      }

      ```


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/api/v4/source/ip_filters.yaml =====

  /api/v4/ip_filtering:
    get:
      tags:
        - ip
        - filtering
      summary: Get all IP filters
      description: >
        Retrieve a list of IP filters applied to the workspace

        __Minimum server version__: 9.1
        __Note:__ This is intended for internal use and only applicable to Cloud workspaces
      operationId: GetIPFilters
      responses:
        "200":
          description: IP Filters returned successfully
          content:
            application/json:
              schema:
                type: array
                items: 
                  $ref: "#/components/schemas/AllowedIPRange"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "500":
          $ref: "#/components/responses/InternalServerError"
        "501":
          $ref: "#/components/responses/NotImplemented"
    post:
      tags:
        - ip
        - filtering
      summary: Get all IP filters
      description: >
        Adjust IP Filters applied to the workspace

        __Minimum server version__: 9.1
        __Note:__ This is intended for internal use and only applicable to Cloud workspaces
      operationId: ApplyIPFilters
      requestBody:
        content:
          application/json:
            schema:
              type: array
              items: 
                $ref: "#/components/schemas/AllowedIPRange"
        description: IP Filters to apply
        required: true
      responses:
        "200":
          description: IP Filters returned successfully
          content:
            application/json:
              schema:
                type: array
                items: 
                  $ref: "#/components/schemas/AllowedIPRange"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "500":
          $ref: "#/components/responses/InternalServerError"
        "501":
          $ref: "#/components/responses/NotImplemented"
  /api/v4/ip_filtering/my_ip:
    get:
      tags:
        - ip
        - filtering
      summary: Get all IP filters
      description: >
        Retrieve your current IP address as seen by the workspace

        __Minimum server version__: 9.1
        __Note:__ This is intended for internal use and only applicable to Cloud workspaces
      operationId: MyIP
      responses:
        "200":
          description: IP address returned successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  ip:
                    type: string
                    description: Your current IP address
                    example: "192.168.0.1"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "500":
          $ref: "#/components/responses/InternalServerError"
        "501":
          $ref: "#/components/responses/NotImplemented"

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/api/v4/source/jobs.yaml =====

  /api/v4/jobs:
    get:
      tags:
        - jobs
      summary: Get the jobs.
      description: |
        Get a page of jobs. Use the query parameters to modify the behaviour of
        this endpoint.

        __Minimum server version: 4.1__

        ##### Permissions
        Must have permission to read at least one job type returned by this call.
        When no `job_type` query parameter is set, the server only includes job types your session may read; required permission depends on the job type:

        - `read_data_retention_job` — `data_retention`
        - `read_compliance_export_job` — `message_export`
        - `read_elasticsearch_post_indexing_job` — `elasticsearch_post_indexing`
        - `read_elasticsearch_post_aggregation_job` — `elasticsearch_post_aggregation`
        - `read_ldap_sync_job` — `ldap_sync`
        - `read_jobs` — `migrations`, `plugins`, `product_notices`, `expiry_notify`, `active_users`, `import_process`, `import_delete`, `export_process`, `export_delete`, `cloud`, `mobile_session_metadata`, `extract_content`
        - `manage_system` — `access_control_sync`

        When `job_type` is set, you must have the permission that matches that type (same mapping as above).

        This endpoint does not accept `team_id`. To list `access_control_sync` jobs scoped to a team without `manage_system`, use `GET /api/v4/jobs/type/access_control_sync` with query parameter `team_id` set to the team GUID (requires `manage_team_access_rules` on that team).
      operationId: GetJobs
      parameters:
        - name: page
          in: query
          description: The page to select.
          schema:
            type: integer
            default: 0
        - name: per_page
          in: query
          description: The number of jobs per page.
          schema:
            type: integer
            default: 5
        - name: job_type
          in: query
          description: The type of jobs to fetch.
          schema:
            type: string
        - name: status
          in: query
          description: The status of jobs to fetch.
          schema:
            type: string
      responses:
        "200":
          description: Job list retrieval successful
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: "#/components/schemas/Job"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
    post:
      tags:
        - jobs
      summary: Create a new job.
      description: |
        Create a new job.
        __Minimum server version: 4.1__
        ##### Permissions
        Must have permission to create the requested job type. Required permission depends on `type`:

        - `create_data_retention_job` — `data_retention`
        - `create_compliance_export_job` — `message_export`
        - `create_elasticsearch_post_indexing_job` — `elasticsearch_post_indexing`
        - `create_elasticsearch_post_aggregation_job` — `elasticsearch_post_aggregation`
        - `create_ldap_sync_job` — `ldap_sync`
        - `manage_jobs` — `migrations`, `plugins`, `product_notices`, `expiry_notify`, `active_users`, `import_process`, `import_delete`, `export_process`, `export_delete`, `cloud`, `extract_content`
        - `access_control_sync` — `manage_system`, or `manage_channel_access_rules` on the channel given in job `data`, or `manage_team_access_rules` on the team in job `data` (see server logic for scoped sync jobs)
      operationId: CreateJob
      requestBody:
        content:
          application/json:
            schema:
              type: object
              required:
                - type
              properties:
                type:
                  type: string
                  description: The type of job to create
                data:
                  type: object
                  description: An object containing any additional data required for this
                    job type
        description: Job object to be created
        required: true
      responses:
        "201":
          description: Job creation successful
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Job"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
  "/api/v4/jobs/{job_id}":
    get:
      tags:
        - jobs
      summary: Get a job.
      description: |
        Gets a single job.
        __Minimum server version: 4.1__
        ##### Permissions
        Must have permission to read the job's type:

        - `read_data_retention_job` — `data_retention`
        - `read_compliance_export_job` — `message_export`
        - `read_elasticsearch_post_indexing_job` — `elasticsearch_post_indexing`
        - `read_elasticsearch_post_aggregation_job` — `elasticsearch_post_aggregation`
        - `read_ldap_sync_job` — `ldap_sync`
        - `read_jobs` — `migrations`, `plugins`, `product_notices`, `expiry_notify`, `active_users`, `import_process`, `import_delete`, `export_process`, `export_delete`, `cloud`, `mobile_session_metadata`, `extract_content`
        - `manage_system` — `access_control_sync`
      operationId: GetJob
      parameters:
        - name: job_id
          in: path
          description: Job GUID
          required: true
          schema:
            type: string
      responses:
        "200":
          description: Job retrieval successful
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Job"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "404":
          $ref: "#/components/responses/NotFound"
  "/api/v4/jobs/{job_id}/download":
    get:
      tags:
        - jobs
      summary: Download the results of a job.
      description: |
        Download the result of a single job.
        __Minimum server version: 5.28__
        ##### Permissions
        Must have `download_compliance_export_result` permission for message export jobs.
      operationId: DownloadJob
      parameters:
        - name: job_id
          in: path
          description: Job GUID
          required: true
          schema:
            type: string
      responses:
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "404":

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/api/v4/source/ldap.yaml =====

  /api/v4/ldap/sync:
    post:
      tags:
        - LDAP
      summary: Sync with LDAP
      description: >
        Synchronize any user attribute changes in the configured AD/LDAP server
        with Mattermost.

        ##### Permissions

        Must have `manage_system` permission.
      operationId: SyncLdap
      responses:
        "200":
          description: LDAP sync successful
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/StatusOK"
        "501":
          $ref: "#/components/responses/NotImplemented"
  /api/v4/ldap/test:
    post:
      tags:
        - LDAP
      summary: Test LDAP configuration
      description: >
        Test the current AD/LDAP configuration to see if the AD/LDAP server can
        be contacted successfully.

        ##### Permissions

        Must have `manage_system` permission.
      operationId: TestLdap
      responses:
        "200":
          description: LDAP test successful
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/StatusOK"
        "500":
          $ref: "#/components/responses/InternalServerError"
        "501":
          $ref: "#/components/responses/NotImplemented"
  /api/v4/ldap/test_connection:
    post:
      tags:
        - LDAP
      summary: Test LDAP connection with specific settings
      description: >
        Test the LDAP connection using the provided settings without modifying
        the current server configuration.

        ##### Permissions

        Must have `sysconsole_read_authentication_ldap` or `manage_system` permission.
      operationId: TestLdapConnection
      requestBody:
        description: LDAP settings to test
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/LdapSettings"
      responses:
        "200":
          description: LDAP connection test successful
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/StatusOK"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "500":
          $ref: "#/components/responses/InternalServerError"
        "501":
          $ref: "#/components/responses/NotImplemented"
  /api/v4/ldap/test_diagnostics:
    post:
      tags:
        - LDAP
      summary: Test LDAP diagnostics with specific settings
      description: >
        Test LDAP diagnostics using the provided settings to validate configuration
        and see sample results without modifying the current server configuration.
        Use the `test` query parameter to specify which diagnostic to run.

        ##### Permissions

        Must have `sysconsole_read_authentication_ldap` or `manage_system` permission.
      operationId: TestLdapDiagnostics
      parameters:
        - in: query
          name: test
          required: true
          description: Type of LDAP diagnostic test to run
          schema:
            type: string
            enum:
              - filters
              - attributes
              - group_attributes
            example: filters
      requestBody:
        description: LDAP settings to test diagnostics with
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/LdapSettings"
      responses:
        "200":
          description: LDAP diagnostic test results
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: "#/components/schemas/LdapDiagnosticResult"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "500":
          $ref: "#/components/responses/InternalServerError"
        "501":
          $ref: "#/components/responses/NotImplemented"
  /api/v4/ldap/groups:
    get:
      tags:
        - LDAP
      summary: Returns a list of LDAP groups
      description: >
        ##### Permissions

        Must have `manage_system` permission.

        __Minimum server version__: 5.11
      operationId: GetLdapGroups
      parameters:
        - name: q
          in: query
          description: Search term
          required: false
          schema:
            type: string
        - name: page
          in: query
          description: The page to select.
          schema:
            type: integer
            default: 0
        - name: per_page
          in: query
          description: The number of users per page.
            per page.
          schema:
            type: integer
            default: 60
      responses:
        "200":
          description: LDAP group page retrieval successful
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: "#/components/schemas/LDAPGroupsPaged"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/api/v4/source/limits.yaml =====

  /api/v4/limits/server:
    get:
      tags:
        - users
      summary: Gets the server limits for the server
      description: >
        Gets the server limits for the server

        ##### Permissions

        Requires `sysconsole_read_user_management_users`.

      operationId: GetServerLimits
      responses:
        "200":
          description: App limits for server
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: "#/components/schemas/ServerLimits"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "500":
          $ref: "#/components/responses/InternalServerError"

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/api/v4/source/logs.yaml =====

  /api/v4/logs/download:
    get:
      tags:
        - logs
      summary: Download system logs
      description: >
        Downloads the system logs as a text file.
      operationId: DownloadSystemLogs
      responses:
        "200":
          description: System logs downloaded successfully.
          content:
            text/plain:
              schema:
                type: string
                format: binary
        "500":
          $ref: "#/components/responses/InternalServerError"

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/api/v4/source/metrics.yaml =====

  /api/v4/client_perf:
    post:
      tags:
        - metrics
      summary: Report client performance metrics
      description: >
        Uploads client performance measurements to the server as part of the Client Performance Monitoring feature.

        __Minimum server version__: 9.9.0
      operationId: SubmitPerformanceReport
      requestBody:
        content:
          application/json:
            schema:
              type: object
              required:
                - version
                - start
                - end
              properties:
                version:
                  type: string
                  description: An identifier for the schema of the data being submitted which currently must be "0.1.0"
                client_id:
                  type: string
                  description: Not currently used
                labels:
                  type: array
                  items:
                    type: string
                  description: Labels to be applied to all metrics when recorded by the metrics backend
                start:
                  type: integer
                  format: int64
                  description: The time in milliseconds of the first metric in this report
                end:
                  type: integer
                  format: int64
                  description: The time in milliseconds of the last metric in this report
                counters:
                  type: array
                  items:
                    type: object
                    required:
                      - metric
                      - value
                    properties:
                      metric:
                        type: string
                        description: The name of the counter
                      value:
                        type: number
                        format: double
                        description: The value to increment the counter by
                      timestamp:
                        type: integer
                        format: int64
                        description: The time that the counter was incremented
                      labels:
                        type: array
                        items:
                          type: string
                        description: Labels to be applied to this metric when recorded by the metrics backend
                  description: An array of counter metrics to be reported
                histograms:
                  type: array
                  items:
                    type: object
                    required:
                      - metric
                      - value
                    properties:
                      metric:
                        type: string
                        description: The name of the measurement
                      value:
                        type: number
                        format: double
                        description: The value of the measurement
                      timestamp:
                        type: integer
                        format: int64
                        description: The time that the measurement was taken
                      labels:
                        type: array
                        items:
                          type: string
                        description: Labels to be applied to this metric when recorded by the metrics backend
                  description: An array of histogram measurements to be reported
      responses:
        "200":
          description: Measurements reported successfully
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/StatusOK"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "500":
          $ref: "#/components/responses/InternalServerError"

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/api/v4/source/oauth.yaml =====

  /api/v4/oauth/apps:
    post:
      tags:
        - OAuth
      summary: Register OAuth app
      description: >
        Register an OAuth 2.0 client application with Mattermost as the service
        provider.

        ##### Permissions

        Must have `manage_oauth` permission.
      operationId: CreateOAuthApp
      requestBody:
        content:
          application/json:
            schema:
              type: object
              required:
                - name
                - description
                - callback_urls
                - homepage
              properties:
                name:
                  type: string
                  description: The name of the client application
                description:
                  type: string
                  description: A short description of the application
                icon_url:
                  type: string
                  description: A URL to an icon to display with the application
                callback_urls:
                  type: array
                  items:
                    type: string
                  description: A list of callback URLs for the appliation
                homepage:
                  type: string
                  description: A link to the website of the application
                is_trusted:
                  type: boolean
                  description: Set this to `true` to skip asking users for permission
                is_public:
                  type: boolean
                  description: Set this to `true` to create a public client (no client secret). Public clients must use PKCE for authorization.
        description: OAuth application to register
        required: true
      responses:
        "201":
          description: App registration successful
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/OAuthApp"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "501":
          $ref: "#/components/responses/NotImplemented"
    get:
      tags:
        - OAuth
      summary: Get OAuth apps
      description: >
        Get a page of OAuth 2.0 client applications registered with Mattermost.

        ##### Permissions

        With `manage_oauth` permission, the apps registered by the logged in user are returned. With `manage_system_wide_oauth` permission, all apps regardless of creator are returned.
      operationId: GetOAuthApps
      parameters:
        - name: page
          in: query
          description: The page to select.
          schema:
            type: integer
            default: 0
        - name: per_page
          in: query
          description: The number of apps per page.
          schema:
            type: integer
            default: 60
      responses:
        "200":
          description: OAuthApp list retrieval successful
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: "#/components/schemas/OAuthApp"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "501":
          $ref: "#/components/responses/NotImplemented"
  "/api/v4/oauth/apps/{app_id}":
    get:
      tags:
        - OAuth
      summary: Get an OAuth app
      description: >
        Get an OAuth 2.0 client application registered with Mattermost.

        ##### Permissions

        If app creator, must have `mange_oauth` permission otherwise `manage_system_wide_oauth` permission is required.
      operationId: GetOAuthApp
      parameters:
        - name: app_id
          in: path
          description: Application client id
          required: true
          schema:
            type: string
      responses:
        "200":
          description: App retrieval successful
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/OAuthApp"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "404":
          $ref: "#/components/responses/NotFound"
        "501":
          $ref: "#/components/responses/NotImplemented"
    put:
      tags:
        - OAuth
      summary: Update an OAuth app
      description: >
        Update an OAuth 2.0 client application based on OAuth struct.

        ##### Permissions

        If app creator, must have `mange_oauth` permission otherwise `manage_system_wide_oauth` permission is required.
      operationId: UpdateOAuthApp
      parameters:
        - name: app_id
          in: path
          description: Application client id
          required: true
          schema:
            type: string
      requestBody:
        content:
          application/json:
            schema:
              type: object
              required:
                - id
                - name
                - description
                - callback_urls
                - homepage
              properties:
                id:
                  type: string
                  description: The id of the client application
                name:
                  type: string
                  description: The name of the client application
                description:
                  type: string
                  description: A short description of the application

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/api/v4/source/outgoing_oauth_connections.yaml =====

  /api/v4/oauth/outgoing_connections:
    get:
      tags:
        - oauth
        - outgoing_connections
        - outgoing_oauth_connections
      summary: List all connections
      description: >
        List all outgoing OAuth connections.

        __Minimum server version__: 9.6
      operationId: ListOutgoingOAuthConnections
      parameters:
        - name: team_id
          in: query
          description: Current Team ID in integrations backstage
          required: true
          schema:
            type: string
      responses:
        "200":
          description: Successfully fetched outgoing OAuth connections
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: "#/components/schemas/OutgoingOAuthConnectionGetItem"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "500":
          $ref: "#/components/responses/InternalServerError"
        "501":
          $ref: "#/components/responses/NotImplemented"
    post:
      tags:
        - oauth
        - outgoing_connections
        - outgoing_oauth_connections
      summary: Create a connection
      description: >
        Create an outgoing OAuth connection.

        __Minimum server version__: 9.6
      operationId: CreateOutgoingOAuthConnection
      parameters:
        - name: team_id
          in: query
          description: Current Team ID in integrations backstage
          required: true
          schema:
            type: string
      requestBody:
        description: Outgoing OAuth connection to create
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/OutgoingOAuthConnectionPostItem"
      responses:
        "201":
          description: Successfully created outgoing OAuth connection
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/OutgoingOAuthConnectionGetItem"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "500":
          $ref: "#/components/responses/InternalServerError"
        "501":
          $ref: "#/components/responses/NotImplemented"
  /api/v4/oauth/outgoing_connections/{outgoing_oauth_connection_id}:
    get:
      tags:
        - oauth
        - outgoing_connections
        - outgoing_oauth_connections
      summary: Get a connection
      description: >
        Retrieve an outgoing OAuth connection.

        __Minimum server version__: 9.6
      operationId: GetOutgoingOAuthConnection
      parameters:
        - name: outgoing_oauth_connection_id
          in: path
          description: Outgoing OAuth connection ID
          required: true
          schema:
            type: string
        - name: team_id
          in: query
          description: Current Team ID in integrations backstage
          required: true
          schema:
            type: string
      responses:
        "200":
          description: Successfully fetched outgoing OAuth connection
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/OutgoingOAuthConnectionGetItem"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "500":
          $ref: "#/components/responses/InternalServerError"
        "501":
          $ref: "#/components/responses/NotImplemented"
    put:
      tags:
        - oauth
        - outgoing_connections
        - outgoing_oauth_connections
      summary: Update a connection
      description: >
        Update an outgoing OAuth connection.

        __Minimum server version__: 9.6
      operationId: UpdateOutgoingOAuthConnection
      parameters:
        - name: outgoing_oauth_connection_id
          in: path
          description: Outgoing OAuth connection ID
          required: true
          schema:
            type: string
        - name: team_id
          in: query
          description: Current Team ID in integrations backstage
          required: true
          schema:
            type: string
      requestBody:
        description: Outgoing OAuth connection to update
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/OutgoingOAuthConnectionPostItem"
      responses:
        "200":
          description: Successfully updated outgoing OAuth connection
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/OutgoingOAuthConnectionGetItem"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "404":
          $ref: "#/components/responses/NotFound"
        "500":
          $ref: "#/components/responses/InternalServerError"
        "501":
          $ref: "#/components/responses/NotImplemented"
    delete:
      tags:
        - oauth
        - outgoing_connections
        - outgoing_oauth_connections
      summary: Delete a connection
      description: >
        Delete an outgoing OAuth connection.

        __Minimum server version__: 9.6
      operationId: DeleteOutgoingOAuthConnection
      parameters:
        - name: outgoing_oauth_connection_id
          in: path
          description: Outgoing OAuth connection ID
          required: true
          schema:
            type: string
        - name: team_id
          in: query
          description: Current Team ID in integrations backstage
          required: true

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/api/v4/source/permissions.yaml =====

  /api/v4/permissions/ancillary:
    post:
      tags:
        - permissions
      summary: Return all system console subsection ancillary permissions
      description: >
        Returns all the ancillary permissions for the corresponding system console
        subsection permissions appended to the requested permission subsections.
        __Minimum server version__: 9.10
      operationId: GetAncillaryPermissionsPost
      requestBody:
        content:
          application/json:
            schema:
              type: array
              items:
                type: string
        description: List of subsection permissions
        required: true
      responses:
        "200":
          description: Successfully returned all ancillary and requested permissions
          content:
            application/json:
              schema:
                type: array
                items:
                  type: string
        "400":
          $ref: '#/components/responses/BadRequest'

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/api/v4/source/plugins.yaml =====

  /api/v4/plugins:
    post:
      tags:
        - plugins
      summary: Upload plugin
      description: >
        Upload a plugin that is contained within a compressed .tar.gz file.
        Plugins and plugin uploads must be enabled in the server's config
        settings.


        ##### Permissions

        Must have `manage_system` permission.


        __Minimum server version__: 4.4
      operationId: UploadPlugin
      requestBody:
        content:
          multipart/form-data:
            schema:
              type: object
              properties:
                plugin:
                  description: The plugin image to be uploaded
                  type: string
                  format: binary
                force:
                  description: Set to 'true' to overwrite a previously installed plugin
                    with the same ID, if any
                  type: string
              required:
                - plugin
      responses:
        "201":
          description: Plugin upload successful
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/StatusOK"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "413":
          $ref: "#/components/responses/TooLarge"
        "501":
          $ref: "#/components/responses/NotImplemented"
    get:
      tags:
        - plugins
      summary: Get plugins
      description: >
        Get a list of inactive and a list of active plugin manifests. Plugins
        must be enabled in the server's config settings.


        ##### Permissions

        Must have `manage_system` permission.


        __Minimum server version__: 4.4
      operationId: GetPlugins
      responses:
        "200":
          description: Plugins retrieval successful
          content:
            application/json:
              schema:
                type: object
                properties:
                  active:
                    type: array
                    items:
                      $ref: "#/components/schemas/PluginManifest"
                  inactive:
                    type: array
                    items:
                      $ref: "#/components/schemas/PluginManifest"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "501":
          $ref: "#/components/responses/NotImplemented"
  /api/v4/plugins/install_from_url:
    post:
      tags:
        - plugins
      summary: Install plugin from url
      description: >
        Supply a URL to a plugin compressed in a .tar.gz file. Plugins must be
        enabled in the server's config settings.


        ##### Permissions

        Must have `manage_system` permission.


        __Minimum server version__: 5.14
      operationId: InstallPluginFromUrl
      parameters:
        - name: plugin_download_url
          in: query
          description: URL used to download the plugin
          required: true
          schema:
            type: string
        - name: force
          in: query
          description: Set to 'true' to overwrite a previously installed plugin with the
            same ID, if any
          required: false
          schema:
            type: string
      responses:
        "201":
          description: Plugin install successful
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/StatusOK"
        "400":
          $ref: "#/components/responses/BadRequest"
        "403":
          $ref: "#/components/responses/Forbidden"
        "501":
          $ref: "#/components/responses/NotImplemented"
  "/api/v4/plugins/{plugin_id}":
    delete:
      tags:
        - plugins
      summary: Remove plugin
      description: >
        Remove the plugin with the provided ID from the server. All plugin files
        are deleted. Plugins must be enabled in the server's config settings.


        ##### Permissions

        Must have `manage_system` permission.


        __Minimum server version__: 4.4
      operationId: RemovePlugin
      parameters:
        - name: plugin_id
          description: Id of the plugin to be removed
          in: path
          required: true
          schema:
            type: string
      responses:
        "200":
          description: Plugin removed successfully
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/StatusOK"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "404":
          $ref: "#/components/responses/NotFound"
        "501":
          $ref: "#/components/responses/NotImplemented"
  "/api/v4/plugins/{plugin_id}/enable":
    post:
      tags:
        - plugins

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/api/v4/source/posts.yaml =====

  /api/v4/posts:
    post:
      tags:
        - posts
      summary: Create a post
      description: >
        Create a new post in a channel. To create the post as a comment on
        another post, provide `root_id`.

        ##### Permissions

        Must have `create_post` permission for the channel the post is being created in.
      operationId: CreatePost
      parameters:
        - name: set_online
          in: query
          description: Whether to set the user status as online or not.
          required: false
          schema:
            type: boolean
      requestBody:
        content:
          application/json:
            schema:
              type: object
              required:
                - channel_id
                - message
              properties:
                channel_id:
                  type: string
                  description: The channel ID to post in
                message:
                  type: string
                  description: The message contents, can be formatted with Markdown
                root_id:
                  type: string
                  description: The post ID to comment on
                file_ids:
                  type: array
                  description: A list of file IDs to associate with the post. Note that
                    posts are limited to 5 files maximum. Please use additional
                    posts for more files.
                  items:
                    type: string
                props:
                  description: A general JSON property bag to attach to the post
                  type: object
                metadata:
                  description: A JSON object to add post metadata, e.g the post's priority
                  type: object
                  properties:
                    priority:
                      type: object
                      description: An object containing the post's priority properties
                      properties:
                        priority:
                          type: string
                          description: The priority label of the post, could empty, important, or urgent
                        requested_ack:
                          type: boolean
                          description: Set to true to request for acknowledgements
        description: Post object to create
        required: true
      responses:
        "201":
          description: Post creation successful
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Post"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
  /api/v4/posts/ephemeral:
    post:
      tags:
        - posts
      summary: Create a ephemeral post
      description: >
        Create a new ephemeral post in a channel.

        ##### Permissions

        Must have `create_post_ephemeral` permission (currently only given to system admin)
      operationId: CreatePostEphemeral
      requestBody:
        content:
          application/json:
            schema:
              type: object
              required:
                - user_id
                - post
              properties:
                user_id:
                  type: string
                  description: The target user id for the ephemeral post
                post:
                  type: object
                  required:
                    - channel_id
                    - message
                  description: Post object to create
                  properties:
                    channel_id:
                      type: string
                      description: The channel ID to post in
                    message:
                      type: string
                      description: The message contents, can be formatted with Markdown
        description: Ephemeral Post object to send
        required: true
      responses:
        "201":
          description: Post creation successful
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Post"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
  /api/v4/posts/search:
    post:
      tags:
        - posts
      summary: Search posts across all teams
      description: |
        Search posts visible to the current user across all teams.
        ##### Permissions
        Must be authenticated.
      operationId: SearchPostsInAllTeams
      requestBody:
        content:
          application/json:
            schema:
              type: object
              required:
                - terms
              properties:
                terms:
                  type: string
                is_or_search:
                  type: boolean
                time_zone_offset:
                  type: integer
                include_deleted_channels:
                  type: boolean
                page:
                  type: integer
                per_page:
                  type: integer
        required: true
      responses:
        "200":
          description: Post search successful
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/PostListWithSearchMatches"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
  "/api/v4/posts/{post_id}":
    get:
      tags:
        - posts
      summary: Get a post
      description: >
        Get a single post.

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/api/v4/source/preferences.yaml =====

  "/api/v4/users/{user_id}/preferences":
    get:
      tags:
        - preferences
      summary: Get the user's preferences
      description: >
        Get a list of the user's preferences.

        ##### Permissions

        Must be logged in as the user being updated or have the `edit_other_users` permission.
      operationId: GetPreferences
      parameters:
        - name: user_id
          in: path
          description: User GUID
          required: true
          schema:
            type: string
      responses:
        "200":
          description: User preferences retrieval successful
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: "#/components/schemas/Preference"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
    put:
      tags:
        - preferences
      summary: Save the user's preferences
      description: >
        Save a list of the user's preferences.

        ##### Permissions

        Must be logged in as the user being updated or have the `edit_other_users` permission.
      operationId: UpdatePreferences
      parameters:
        - name: user_id
          in: path
          description: User GUID
          required: true
          schema:
            type: string
      requestBody:
        description: List of preference objects
        required: true
        content:
          application/json:
            schema:
              type: array
              items:
                $ref: '#/components/schemas/Preference'
              minItems: 1
              maxItems: 100
      responses:
        "200":
          description: User preferences saved successful
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/StatusOK"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "404":
          $ref: "#/components/responses/NotFound"
  "/api/v4/users/{user_id}/preferences/delete":
    post:
      tags:
        - preferences
      summary: Delete user's preferences
      description: >
        Delete a list of the user's preferences.

        ##### Permissions

        Must be logged in as the user being updated or have the `edit_other_users` permission.
      operationId: DeletePreferences
      parameters:
        - name: user_id
          in: path
          description: User GUID
          required: true
          schema:
            type: string
      requestBody:
        description: List of preference objects
        required: true
        content:
          application/json:
            schema:            
              type: array
              items:
                $ref: '#/components/schemas/Preference'
              minItems: 1
              maxItems: 100
      responses:
        "200":
          description: User preferences saved successful
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/StatusOK"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
  "/api/v4/users/{user_id}/preferences/{category}":
    get:
      tags:
        - preferences
      summary: List a user's preferences by category
      description: >
        Lists the current user's stored preferences in the given category.

        ##### Permissions

        Must be logged in as the user being updated or have the `edit_other_users` permission.
      operationId: GetPreferencesByCategory
      parameters:
        - name: user_id
          in: path
          description: User GUID
          required: true
          schema:
            type: string
        - name: category
          in: path
          description: The category of a group of preferences
          required: true
          schema:
            type: string
      responses:
        "200":
          description: A list of all of the current user's preferences in the given category
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: "#/components/schemas/Preference"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
  "/api/v4/users/{user_id}/preferences/{category}/name/{preference_name}":
    get:
      tags:
        - preferences
      summary: Get a specific user preference
      description: >
        Gets a single preference for the current user with the given category
        and name.

        ##### Permissions

        Must be logged in as the user being updated or have the `edit_other_users` permission.
      operationId: GetPreferencesByCategoryByName
      parameters:
        - name: user_id
          in: path
          description: User GUID
          required: true
          schema:

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/api/v4/source/properties.yaml =====

  "/api/v4/properties/groups/{group_name}/{object_type}/fields":
    post:
      tags:
        - properties
      summary: Create a property field
      description: >
        Create a new property field for a specific group and object type.
      operationId: CreatePropertyField
      parameters:
        - name: group_name
          in: path
          description: The name of the property group
          required: true
          schema:
            type: string
        - name: object_type
          in: path
          description: The type of object this property field applies to
          required: true
          schema:
            type: string
      requestBody:
        content:
          application/json:
            schema:
              type: object
              required:
                - name
                - type
                - target_type
              properties:
                name:
                  type: string
                  description: The name of the property field
                type:
                  type: string
                  description: The type of property field
                  enum: [text, select, multiselect, date, user, multiuser]
                attrs:
                  type: object
                  description: Additional attributes for the property field
                target_type:
                  type: string
                  description: The scope level of the property
                target_id:
                  type: string
                  description: The ID of the target
                permission_field:
                  type: string
                  enum: [none, sysadmin, member, admin]
                  description: >
                    Permission level for editing the field definition.
                    Only system admins can set this; ignored for non-admin users.
                  default: member
                permission_values:
                  type: string
                  enum: [none, sysadmin, member, admin]
                  description: >
                    Permission level for setting values on objects.
                    Only system admins can set this; ignored for non-admin users.
                  default: member
                permission_options:
                  type: string
                  enum: [none, sysadmin, member, admin]
                  description: >
                    Permission level for managing options on select/multiselect fields.
                    Only system admins can set this; ignored for non-admin users.
                  default: member
                linked_field_id:
                  type: string
                  description: >
                    The ID of a template field to link to. The source must be a
                    template field in the same group, must not itself be linked, and must
                    not be deleted. When set, the created field inherits the source's type,
                    options, and security attributes; the `type` field in the request body
                    is ignored. Can only be set at creation time.
        description: Property field object to create
        required: true
      responses:
        "201":
          description: Property field creation successful
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/PropertyField"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "409":
          description: >
            A property field with the same name already exists at the same or a
            conflicting hierarchy level.
          $ref: "#/components/responses/Conflict"
    get:
      tags:
        - properties
      summary: Get property fields
      description: >
        Get a list of property fields for a specific group and object type. Requires a target_type parameter to scope the query, except when `object_type=system` — in that case `target_type` is implicit and any value supplied is ignored. Filter further by target_id to narrow results. Uses cursor-based pagination.
      operationId: GetPropertyFields
      parameters:
        - name: group_name
          in: path
          description: The name of the property group
          required: true
          schema:
            type: string
        - name: object_type
          in: path
          description: The type of object to retrieve property fields for
          required: true
          schema:
            type: string
        - name: target_type
          in: query
          description: The scope level to query. Must be one of 'system', 'team', or 'channel'.
          required: true
          schema:
            type: string
            enum:
              - system
              - team
              - channel
        - name: target_id
          in: query
          description: Filter by target ID. Required when target_type is 'channel' or 'team'.
          schema:
            type: string
        - name: cursor_id
          in: query
          description: The ID of the last property field from the previous page, for cursor-based pagination.
          schema:
            type: string
        - name: cursor_create_at
          in: query
          description: The create_at timestamp of the last property field from the previous page. Must be provided together with cursor_id.
          schema:
            type: integer
            format: int64
        - name: per_page
          in: query
          description: The number of property fields per page.
          schema:
            type: integer
            default: 60
      responses:
        "200":
          description: Property fields retrieval successful
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: "#/components/schemas/PropertyField"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
  "/api/v4/properties/groups/{group_name}/{object_type}/fields/{field_id}":
    patch:
      tags:
        - properties
      summary: Update a property field
      description: >
        Partially update a property field by providing only the fields you want to update. Omitted fields will not be updated.
        The `attrs` object uses merge semantics: only the keys present in the patch are updated; omitted keys are preserved. Setting a key to `null` removes it from attrs.


        **Immutable fields:** `target_type`, `target_id`, and `object_type` cannot be changed after creation and are ignored if included in the patch.


        **Linked fields:** Fields with a `linked_field_id` cannot have their `type` or `attrs.options` modified (returns 400).
        The `linked_field_id` can only be cleared (set to empty string `""`) to unlink the field; it cannot be changed to a different value.
        For non-linked fields, `linked_field_id` cannot be set to a new value (linking is only allowed at creation time).


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/api/v4/source/reactions.yaml =====

  /api/v4/reactions:
    post:
      tags:
        - reactions
      summary: Create a reaction
      description: |
        Create a reaction.
        ##### Permissions
        Must have `read_channel` permission for the channel the post is in.
      operationId: SaveReaction
      requestBody:
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/Reaction"
        description: The user's reaction with its post_id, user_id, and emoji_name fields
          set
        required: true
      responses:
        "201":
          description: Reaction creation successful
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Reaction"
        "400":
          $ref: "#/components/responses/BadRequest"
        "403":
          $ref: "#/components/responses/Forbidden"
  "/api/v4/posts/{post_id}/reactions":
    get:
      tags:
        - reactions
      summary: Get a list of reactions to a post
      description: |
        Get a list of reactions made by all users to a given post.
        ##### Permissions
        Must have `read_channel` permission for the channel the post is in.
      operationId: GetReactions
      parameters:
        - name: post_id
          in: path
          description: ID of a post
          required: true
          schema:
            type: string
      responses:
        "200":
          description: List reactions retrieve successful
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: "#/components/schemas/Reaction"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
  "/api/v4/users/{user_id}/posts/{post_id}/reactions/{emoji_name}":
    delete:
      tags:
        - reactions
      summary: Remove a reaction from a post
      description: |
        Deletes a reaction made by a user from the given post.
        ##### Permissions
        Must be user or have `manage_system` permission.
      operationId: DeleteReaction
      parameters:
        - name: user_id
          in: path
          description: ID of the user
          required: true
          schema:
            type: string
        - name: post_id
          in: path
          description: ID of the post
          required: true
          schema:
            type: string
        - name: emoji_name
          in: path
          description: emoji name
          required: true
          schema:
            type: string
      responses:
        "200":
          description: Reaction deletion successful
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/StatusOK"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
  /api/v4/posts/ids/reactions:
    post:
      tags:
        - reactions
      summary: Bulk get the reaction for posts
      description: |
        Get a list of reactions made by all users to a given post.
        ##### Permissions
        Must have `read_channel` permission for the channel the post is in.

        __Minimum server version__: 5.8
      operationId: GetBulkReactions
      requestBody:
        content:
          application/json:
            schema:
              type: array
              items:
                type: string
        description: Array of post IDs
        required: true
      responses:
        "200":
          description: Reactions retrieval successful
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/PostIdToReactionsMap"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/api/v4/source/recaps.yaml =====

  "/api/v4/recaps":
    post:
      tags:
        - recaps
        - ai
      summary: Create a channel recap
      description: >
        Create a new AI-powered recap for the specified channels. The recap will
        summarize unread messages in the selected channels, extracting highlights
        and action items. This creates a background job that processes the recap
        asynchronously. The recap is created for the authenticated user.

        ##### Permissions

        Must be authenticated. User must be a member of all specified channels.

        __Minimum server version__: 11.2
      operationId: CreateRecap
      requestBody:
        content:
          application/json:
            schema:
              type: object
              required:
                - channel_ids
                - title
                - agent_id
              properties:
                title:
                  type: string
                  description: Title for the recap
                channel_ids:
                  type: array
                  items:
                    type: string
                  description: List of channel IDs to include in the recap
                  minItems: 1
                agent_id:
                  type: string
                  description: ID of the AI agent to use for generating the recap
        description: Recap creation request
        required: true
      responses:
        "201":
          description: Recap creation successful. The recap will be processed asynchronously.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Recap"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
    get:
      tags:
        - recaps
        - ai
      summary: Get current user's recaps
      description: >
        Get a paginated list of recaps created by the authenticated user.

        ##### Permissions

        Must be authenticated.

        __Minimum server version__: 11.2
      operationId: GetRecapsForUser
      parameters:
        - name: page
          in: query
          description: The page to select.
          schema:
            type: integer
            default: 0
        - name: per_page
          in: query
          description: The number of recaps per page.
          schema:
            type: integer
            default: 60
      responses:
        "200":
          description: Recaps retrieval successful
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: "#/components/schemas/Recap"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
  "/api/v4/recaps/mark_viewed":
    post:
      tags:
        - recaps
        - ai
      summary: Mark all of the authenticated user's finished recaps as viewed
      description: >
        Mark every not-yet-viewed completed or failed recap belonging to the
        authenticated user as viewed at the current time. Pending and
        processing recaps are not affected. Returns the IDs of the recaps
        that were updated. The server broadcasts a `recap_updated` WebSocket
        event for each affected recap.

        Typically called once when the recaps page is opened so the sidebar
        unread badge can be cleared in bulk.

        ##### Permissions

        Must be authenticated. Operates only on the authenticated user's
        own recaps.

        __Minimum server version__: 11.2
      operationId: MarkRecapsAsViewed
      responses:
        "200":
          description: Recaps marked as viewed successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  recap_ids:
                    type: array
                    items:
                      type: string
                    description: IDs of the recaps that were updated
        "401":
          $ref: "#/components/responses/Unauthorized"
        "501":
          description: AI Recaps feature flag is disabled
  "/api/v4/recaps/{recap_id}":
    get:
      tags:
        - recaps
        - ai
      summary: Get a specific recap
      description: >
        Get a recap by its ID, including all channel summaries. Only the authenticated
        user who created the recap can retrieve it.

        ##### Permissions

        Must be authenticated. Can only retrieve recaps created by the current user.

        __Minimum server version__: 11.2
      operationId: GetRecap
      parameters:
        - name: recap_id
          in: path
          description: Recap GUID
          required: true
          schema:
            type: string
      responses:
        "200":
          description: Recap retrieval successful
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Recap"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "404":
          $ref: "#/components/responses/NotFound"
    delete:
      tags:
        - recaps
        - ai
      summary: Delete a recap
      description: >
        Delete a recap by its ID. Only the authenticated user who created the recap
        can delete it.


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/api/v4/source/remoteclusters.yaml =====

  "/api/v4/remotecluster":
    get:
      tags:
        - remote clusters
      summary: Get a list of remote clusters.
      description: |
        Get a list of remote clusters.

        ##### Permissions
        `manage_secure_connections` or `manage_shared_channels`
      operationId: GetRemoteClusters
      parameters:
        - name: page
          in: query
          description: The page to select
          schema:
            type: integer
        - name: per_page
          in: query
          description: The number of remote clusters per page
          schema:
            type: integer
        - name: exclude_offline
          in: query
          description: Exclude offline remote clusters
          schema:
            type: boolean
        - name: in_channel
          in: query
          description: Select remote clusters in channel
          schema:
            type: string
        - name: not_in_channel
          in: query
          description: Select remote clusters not in this channel
          schema:
            type: string
        - name: only_confirmed
          in: query
          description: Select only remote clusters already confirmed
          schema:
            type: boolean
        - name: only_plugins
          in: query
          description: Select only remote clusters that belong to a plugin
          schema:
            type: boolean
        - name: exclude_plugins
          in: query
          description: Select only remote clusters that don't belong to a plugin
          schema:
            type: boolean
        - name: include_deleted
          in: query
          description: Include those remote clusters that have been deleted
          schema:
            type: boolean
      responses:
        "200":
          description: Remote clusters fetch successful. Result might be empty.
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: "#/components/schemas/RemoteCluster"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"

    post:
      tags:
        - remote clusters
      summary: Create a new remote cluster.
      description: |
        Create a new remote cluster and generate an invite code.

        ##### Permissions
        `manage_secure_connections`
      operationId: CreateRemoteCluster
      requestBody:
        content:
          application/json:
            schema:
              type: object
              required:
                - name
                - default_team_id
              properties:
                name:
                  type: string
                display_name:
                  type: string
                default_team_id:
                  type: string
                password:
                  type: string
                  description: |
                    The password to use in the invite code. If empty,
                    the server will generate one and it will be part
                    of the response
      responses:
        "201":
          description: Remote cluster creation successful
          content:
            application/json:
              schema:
                type: object
                properties:
                  remote_cluster:
                    $ref: "#/components/schemas/RemoteCluster"
                  invite:
                    type: string
                    description: The encrypted invite for the newly created remote cluster
                  password:
                    type: string
                    description: |
                      The password generated by the server if none was
                      sent on the create request
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"

  "/api/v4/remotecluster/{remote_id}":
    get:
      tags:
        - remote clusters
      summary: Get a remote cluster.
      description: |
        Get the Remote Cluster details from the provided id string.

        ##### Permissions
        `manage_secure_connections` or `manage_shared_channels`
      operationId: GetRemoteCluster
      parameters:
        - name: remote_id
          in: path
          description: Remote Cluster GUID
          required: true
          schema:
            type: string
      responses:
        "200":
          description: Remote Cluster retrieval successful
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/RemoteCluster"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "404":
          $ref: "#/components/responses/NotFound"
    patch:
      tags:
        - remote clusters
      summary: Patch a remote cluster.
      description: |
        Partially update a Remote Cluster by providing only the fields you want to update. Ommited fields will not be updated.

        ##### Permissions
        `manage_secure_connections`
      operationId: PatchRemoteCluster
      parameters:
        - name: remote_id
          in: path
          description: Remote Cluster GUID
          required: true
          schema:
            type: string
      requestBody:
        content:
          application/json:
            schema:
              type: object

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/api/v4/source/reports.yaml =====

  /api/v4/reports/users:
    get:
      tags:
        - reports
      summary: Get a list of paged and sorted users for admin reporting purposes
      description: >
        Get a list of paged users for admin reporting purposes, based on provided parameters.
        
        ##### Permissions
        
        Requires `sysconsole_read_user_management_users`.

      operationId: GetUsersForReporting
      parameters:
        - name: sort_column
          in: query
          description: The column to sort the users by. Must be one of ("CreateAt", "Username", "FirstName", "LastName", "Nickname", "Email") or the API will return an error.
          schema:
            type: string
            default: 'Username'
        - name: direction
          in: query
          description: The direction to accept paging values from. Will return values ahead of the cursor if "prev", and below the cursor if "next". Default is "next".
          schema:
            type: string
            default: 'next'
        - name: sort_direction
          in: query
          description: The sorting direction. Must be one of ("asc", "desc"). Will default to 'asc' if not specified or the input is invalid.
          schema:
            type: string
            default: 'asc'
        - name: page_size
          in: query
          description: The maximum number of users to return.
          schema:
            type: integer
            default: 50
            minimum: 1
            maximum: 100
        - name: from_column_value
          in: query
          description: The value of the sorted column corresponding to the cursor to read from. Should be blank for the first page asked for.
          schema:
            type: string
        - name: from_id
          in: query
          description: The value of the user id corresponding to the cursor to read from. Should be blank for the first page asked for.
          schema:
            type: string
        - name: date_range
          in: query
          description: The date range of the post statistics to display. Must be one of ("last30days", "previousmonth", "last6months", "alltime"). Will default to 'alltime' if the input is not valid.
          schema:
            type: string
            default: 'alltime'
        - name: role_filter
          in: query
          description: Filter users by their role.
          schema:
            type: string
        - name: team_filter
          in: query
          description: Filter users by a specified team ID.
          schema:
            type: string
        - name: has_no_team
          in: query
          description: If true, show only users that have no team. Will ignore provided "team_filter" if true.
          schema:
            type: boolean
        - name: hide_active
          in: query
          description: If true, show only users that are inactive. Cannot be used at the same time as "hide_inactive"
          schema:
            type: boolean
        - name: hide_inactive
          in: query
          description: If true, show only users that are active. Cannot be used at the same time as "hide_active"
          schema:
            type: boolean
        - name: search_term
          in: query
          description: A filtering search term that allows filtering by Username, FirstName, LastName, Nickname or Email
          schema:
            type: string
      responses:
        "200":
          description: User page retrieval successful
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: "#/components/schemas/UserReport"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "500":
          $ref: "#/components/responses/InternalServerError"
  /api/v4/reports/users/count:
    get:
      tags:
        - reports
      summary: Gets the full count of users that match the filter.
      description: >
        Get the full count of users admin reporting purposes, based on provided parameters.
        
        ##### Permissions
        
        Requires `sysconsole_read_user_management_users`.
      operationId: GetUserCountForReporting
      parameters:
        - name: role_filter
          in: query
          description: Filter users by their role.
          schema:
            type: string
        - name: team_filter
          in: query
          description: Filter users by a specified team ID.
          schema:
            type: string
        - name: has_no_team
          in: query
          description: If true, show only users that have no team. Will ignore provided "team_filter" if true.
          schema:
            type: boolean
        - name: hide_active
          in: query
          description: If true, show only users that are inactive. Cannot be used at the same time as "hide_inactive"
          schema:
            type: boolean
        - name: hide_inactive
          in: query
          description: If true, show only users that are active. Cannot be used at the same time as "hide_active"
          schema:
            type: boolean
        - name: search_term
          in: query
          description: A filtering search term that allows filtering by Username, FirstName, LastName, Nickname or Email
          schema:
            type: string
      responses:
        "200":
          description: User count retrieval successful
          content:
            application/json:
              schema:
                type: number
  /api/v4/reports/users/export:
    post:
      tags:
        - reports
      summary: Starts a job to export the users to a report file.
      description: >
        Starts a job to export the users to a report file.

        ##### Permissions

        Requires `sysconsole_read_user_management_users`.
      operationId: StartBatchUsersExport
      parameters:
        - name: date_range
          in: query
          description: The date range of the post statistics to display. Must be one of ("last30days", "previousmonth", "last6months", "alltime"). Will default to 'alltime' if the input is not valid.
          schema:
            type: string
            default: 'alltime'
      responses:
        "200":
          description: Job successfully started
          content:
            application/json:
              schema:
                type: array
                items:

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/api/v4/source/roles.yaml =====

  "/api/v4/roles":
    get:
      tags:
        - roles
      summary: Get a list of all the roles
      description: |
        ##### Permissions

        `manage_system` permission is required.

        __Minimum server version__: 5.33
      operationId: GetAllRoles
      responses:
        "200":
          description: Roles retrieval successful
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: "#/components/schemas/Role"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
  "/api/v4/roles/{role_id}":
    get:
      tags:
        - roles
      summary: Get a role
      description: |
        Get a role from the provided role id.

        ##### Permissions
        Requires an active session but no other permissions.

        __Minimum server version__: 4.9
      operationId: GetRole
      parameters:
        - name: role_id
          in: path
          description: Role GUID
          required: true
          schema:
            type: string
      responses:
        "200":
          description: Role retrieval successful
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Role"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "404":
          $ref: "#/components/responses/NotFound"
  "/api/v4/roles/name/{role_name}":
    get:
      tags:
        - roles
      summary: Get a role
      description: |
        Get a role from the provided role name.

        ##### Permissions
        Requires an active session but no other permissions.

        __Minimum server version__: 4.9
      operationId: GetRoleByName
      parameters:
        - name: role_name
          in: path
          description: Role Name
          required: true
          schema:
            type: string
      responses:
        "200":
          description: Role retrieval successful
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Role"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "404":
          $ref: "#/components/responses/NotFound"
  "/api/v4/roles/{role_id}/patch":
    put:
      tags:
        - roles
      summary: Patch a role
      description: >
        Partially update a role by providing only the fields you want to update.
        Omitted fields will not be updated. The fields that can be updated are
        defined in the request body, all other provided fields will be ignored.


        ##### Permissions

        Must have `sysconsole_write_user_management_permissions` or `manage_system` permission.
        When updating the role of a system admin, the `manage_system` permission is mandatory.


        __Minimum server version__: 4.9
      operationId: PatchRole
      parameters:
        - name: role_id
          in: path
          description: Role GUID
          required: true
          schema:
            type: string
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                permissions:
                  type: array
                  items:
                    type: string
                  description: The permissions the role should grant.
        description: Role object to be updated
        required: true
      responses:
        "200":
          description: Role patch successful
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Role"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "404":
          $ref: "#/components/responses/NotFound"
  /api/v4/roles/names:
    post:
      tags:
        - roles
      summary: Get a list of roles by name
      description: |
        Get a list of roles from their names.

        ##### Permissions
        Requires an active session but no other permissions.

        __Minimum server version__: 4.9
      operationId: GetRolesByNames
      requestBody:
        content:
          application/json:
            schema:
              type: array
              items:
                type: string
        description: List of role names
        required: true
      responses:
        "200":
          description: Role list retrieval successful
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: "#/components/schemas/Role"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "404":
          $ref: "#/components/responses/NotFound"

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/api/v4/source/saml.yaml =====

  /api/v4/saml/metadata:
    get:
      tags:
        - SAML
      summary: Get metadata
      description: |
        Get SAML metadata from the server. SAML must be configured properly.
        ##### Permissions
        No permission required.
      operationId: GetSamlMetadata
      responses:
        "200":
          description: SAML metadata retrieval successful
          content:
            application/json:
              schema:
                type: string
        "501":
          $ref: "#/components/responses/NotImplemented"
  /api/v4/saml/metadatafromidp:
    post:
      tags:
        - SAML
      summary: Get metadata from Identity Provider
      description: |
        Get SAML metadata from the Identity Provider. SAML must be configured properly.
        ##### Permissions
        No permission required.
      operationId: GetSamlMetadataFromIdp
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                saml_metadata_url:
                  type: string
                  description: The URL from which to retrieve the SAML IDP data.
      responses:
        "200":
          description: SAML metadata retrieval successful
          content:
            application/json:
              schema:
                type: string
        "501":
          $ref: "#/components/responses/NotImplemented"
  /api/v4/saml/certificate/idp:
    post:
      tags:
        - SAML
      summary: Upload IDP certificate
      description: >
        Upload the IDP certificate to be used with your SAML configuration. The
        server will pick a hard-coded filename for the IdpCertificateFile
        setting in your `config.json`.

        ##### Permissions

        Must have `sysconsole_write_authentication` permission.
      operationId: UploadSamlIdpCertificate
      requestBody:
        content:
          multipart/form-data:
            schema:
              type: object
              properties:
                certificate:
                  description: The IDP certificate file
                  type: string
                  format: binary
              required:
                - certificate
      responses:
        "200":
          description: SAML certificate upload successful
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/StatusOK"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "501":
          $ref: "#/components/responses/NotImplemented"
    delete:
      tags:
        - SAML
      summary: Remove IDP certificate
      description: >
        Delete the current IDP certificate being used with your SAML
        configuration. This will also disable SAML on your system as this
        certificate is required for SAML.

        ##### Permissions

        Must have `sysconsole_write_authentication` permission.
      operationId: DeleteSamlIdpCertificate
      responses:
        "200":
          description: SAML certificate delete successful
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/StatusOK"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "501":
          $ref: "#/components/responses/NotImplemented"
  /api/v4/saml/certificate/public:
    post:
      tags:
        - SAML
      summary: Upload public certificate
      description: >
        Upload the public certificate to be used for encryption with your SAML
        configuration. The server will pick a hard-coded filename for the
        PublicCertificateFile setting in your `config.json`.

        ##### Permissions

        Must have `sysconsole_write_authentication` permission.
      operationId: UploadSamlPublicCertificate
      requestBody:
        content:
          multipart/form-data:
            schema:
              type: object
              properties:
                certificate:
                  description: The public certificate file
                  type: string
                  format: binary
              required:
                - certificate
      responses:
        "200":
          description: SAML certificate upload successful
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/StatusOK"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "501":
          $ref: "#/components/responses/NotImplemented"
    delete:
      tags:
        - SAML
      summary: Remove public certificate
      description: >
        Delete the current public certificate being used with your SAML
        configuration. This will also disable encryption for SAML on your system
        as this certificate is required for that.

        ##### Permissions

        Must have `sysconsole_write_authentication` permission.
      operationId: DeleteSamlPublicCertificate
      responses:
        "200":
          description: SAML certificate delete successful
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/StatusOK"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "501":

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/api/v4/source/scheduled_post.yaml =====

  /api/v4/posts/schedule:
    post:
      tags:
        - scheduled_post
      summary: Creates a scheduled post
      description: >
        Creates a scheduled post

        ##### Permissions

        Must have `create_post` permission for the channel the post is being created in.

        __Minimum server version__: 10.3
      operationId: CreateScheduledPost
      requestBody:
        content:
          application/json:
            schema:
              type: object
              required:
                - channel_id
                - message
                - scheduled_at
              properties:
                scheduled_at:
                  type: integer
                  description: UNIX timestamp in milliseconds of the time when the scheduled post should be sent
                channel_id:
                  type: string
                  description: The channel ID to post in
                message:
                  type: string
                  description: The message contents, can be formatted with Markdown
                root_id:
                  type: string
                  description: The post ID to comment on
                file_ids:
                  type: array
                  description: A list of file IDs to associate with the post. Note that
                    posts are limited to 5 files maximum. Please use additional
                    posts for more files.
                props:
                  description: A general JSON property bag to attach to the post
                  type: object
      responses:
        "200":
          description: Created scheduled post
          content:
            application/json:
              schema:
                type: object
                items:
                  $ref: "#/components/schemas/ScheduledPost"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "500":
          $ref: "#/components/responses/InternalServerError"

  /api/v4/posts/scheduled/team/{team_id}:
    get:
      tags:
        - scheduled_post
      summary: Gets all scheduled posts for a user for the specified team..
      description: >
        Get user-team scheduled posts

        ##### Permissions

        Must have `view_team` permission for the team the scheduled posts are being fetched for.

        __Minimum server version__: 10.3
      operationId: GetUserScheduledPosts
      parameters:
        - name: includeDirectChannels
          in: query
          description: Whether to include scheduled posts from DMs an GMs or not. Default is false
          required: false
          schema:
            type: boolean
            default: false
      responses:
        "200":
          description: Created scheduled post
          content:
            application/json:
              schema:
                type: object
                additionalProperties:
                  type: array
                  items:
                    $ref: "#/components/schemas/ScheduledPost"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "500":
          $ref: "#/components/responses/InternalServerError"

  /api/v4/posts/schedule/{scheduled_post_id}:
    put:
      tags:
        - scheduled_post
      summary: Update a scheduled post
      description: >
        Updates a scheduled post

        ##### Permissions

        Must have `create_post` permission for the channel where the scheduled post belongs to.

        __Minimum server version__: 10.3
      operationId: UpdateScheduledPost
      parameters:
        - name: scheduled_post_id
          in: path
          description: ID of the scheduled post to update
          required: true
          schema:
            type: string
      requestBody:
        content:
          application/json:
            schema:
              type: object
              required:
                - id
                - channel_id
                - user_id
                - message
                - scheduled_at
              properties:
                id:
                  description: ID of the scheduled post to update
                  type: string
                channel_id:
                  type: string
                  description: The channel ID to post in
                user_id:
                  type: string
                  description: The current user ID
                scheduled_at:
                  type: integer
                  description: UNIX timestamp in milliseconds of the time when the scheduled post should be sent
                message:
                  type: string
                  description: The message contents, can be formatted with Markdown
      responses:
        "200":
          description: Updated scheduled post
          content:
            application/json:
              schema:
                type: object
                items:
                  $ref: "#/components/schemas/ScheduledPost"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "500":
          $ref: "#/components/responses/InternalServerError"

    delete:
      tags:
        - scheduled_post
      summary: Delete a scheduled post
      description: >
        Delete a scheduled post

        __Minimum server version__: 10.3
      operationId: DeleteScheduledPost
      parameters:

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/api/v4/source/schemes.yaml =====

  /api/v4/schemes:
    get:
      tags:
        - schemes
      summary: Get the schemes.
      description: >
        Get a page of schemes. Use the query parameters to modify the behaviour
        of this endpoint.


        ##### Permissions

        Must have `manage_system` permission.


        __Minimum server version__: 5.0
      operationId: GetSchemes
      parameters:
        - name: scope
          in: query
          description: Limit the results returned to the provided scope, either `team` or
            `channel`.
          schema:
            type: string
            default: ""
        - name: page
          in: query
          description: The page to select.
          schema:
            type: integer
            default: 0
        - name: per_page
          in: query
          description: The number of schemes per page.
          schema:
            type: integer
            default: 60
      responses:
        "200":
          description: Scheme list retrieval successful
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: "#/components/schemas/Scheme"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
    post:
      tags:
        - schemes
      summary: Create a scheme
      description: |
        Create a new scheme.

        ##### Permissions
        Must have `manage_system` permission.

        __Minimum server version__: 5.0
      operationId: CreateScheme
      requestBody:
        content:
          application/json:
            schema:
              type: object
              required:
                - display_name
                - scope
              properties:
                name:
                  type: string
                  description: The name of the scheme
                display_name:
                  type: string
                  description: The display name of the scheme
                description:
                  type: string
                  description: The description of the scheme
                scope:
                  type: string
                  description: The scope of the scheme ("team" or "channel")
        description: Scheme object to create
        required: true
      responses:
        "201":
          description: Scheme creation successful
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Scheme"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "501":
          $ref: "#/components/responses/NotImplemented"
  "/api/v4/schemes/{scheme_id}":
    get:
      tags:
        - schemes
      summary: Get a scheme
      description: |
        Get a scheme from the provided scheme id.

        ##### Permissions
        Must have `manage_system` permission.

        __Minimum server version__: 5.0
      operationId: GetScheme
      parameters:
        - name: scheme_id
          in: path
          description: Scheme GUID
          required: true
          schema:
            type: string
      responses:
        "200":
          description: Scheme retrieval successful
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Scheme"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "404":
          $ref: "#/components/responses/NotFound"
        "501":
          $ref: "#/components/responses/NotImplemented"
    delete:
      tags:
        - schemes
      summary: Delete a scheme
      description: |
        Soft deletes a scheme, by marking the scheme as deleted in the database.

        ##### Permissions
        Must have `manage_system` permission.

        __Minimum server version__: 5.0
      operationId: DeleteScheme
      parameters:
        - name: scheme_id
          in: path
          description: ID of the scheme to delete
          required: true
          schema:
            type: string
      responses:
        "200":
          description: Scheme deletion successful
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/StatusOK"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "501":
          $ref: "#/components/responses/NotImplemented"
  "/api/v4/schemes/{scheme_id}/patch":
    put:
      tags:
        - schemes
      summary: Patch a scheme
      description: >
        Partially update a scheme by providing only the fields you want to
        update. Omitted fields will not be updated. The fields that can be
        updated are defined in the request body, all other provided fields will
        be ignored.


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/api/v4/source/service_terms.yaml =====

  /api/v4/terms_of_service:
    get:
      tags:
        - terms of service
      summary: Get latest terms of service
      description: |
        Get latest terms of service from the server

        __Minimum server version__: 5.4
        ##### Permissions
        Must be authenticated.
      operationId: GetTermsOfService
      responses:
        "200":
          description: Terms of service fetched successfully
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/TermsOfService"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
    post:
      tags:
        - terms of service
      summary: Creates a new terms of service
      description: |
        Creates new terms of service

        __Minimum server version__: 5.4
        ##### Permissions
        Must have `manage_system` permission.
      operationId: CreateTermsOfService
      responses:
        "200":
          description: terms of service fetched successfully
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/TermsOfService"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/api/v4/source/sharedchannels.yaml =====

  "/api/v4/sharedchannels/{team_id}":
    get:
      tags:
        - shared channels
      summary: Get all shared channels for team.
      description: |
        Get all shared channels for a team.

        __Minimum server version__: 5.50

        ##### Permissions
        Must be authenticated and have the `view_team` permission for the team.
        Results are restricted to channels the user is a member of unless the user has
        `manage_shared_channels`.
      operationId: GetAllSharedChannels
      parameters:
        - name: team_id
          in: path
          description: Team Id
          required: true
          schema:
            type: string
        - name: page
          description: The page to select.
          in: query
          schema:
            type: integer
            default: 0
        - name: per_page
          description: The number of sharedchannels per page.
          in: query
          schema:
            type: integer
            default: 0
      responses:
        "200":
          description: Shared channels fetch successful. Result may be empty.
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: "#/components/schemas/SharedChannel"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"

  "/api/v4/remotecluster/{remote_id}/sharedchannelremotes":
    get:
      tags:
        - shared channels
      summary: Get shared channel remotes by remote cluster.
      description: |
        Get a list of the channels shared with a given remote cluster
        and their status.

        ##### Permissions
        `manage_secure_connections` or `manage_shared_channels`
      operationId: GetSharedChannelRemotesByRemoteCluster
      parameters:
        - name: remote_id
          in: path
          description: The remote cluster GUID
          required: true
          schema:
            type: string
        - name: include_unconfirmed
          in: query
          description: Include those Shared channel remotes that are unconfirmed
          schema:
            type: boolean
        - name: exclude_confirmed
          in: query
          description: Show only those Shared channel remotes that are not confirmed yet
          schema:
            type: boolean
        - name: exclude_home
          in: query
          description: Show only those Shared channel remotes that were shared with this server
          schema:
            type: boolean
        - name: exclude_remote
          in: query
          description: Show only those Shared channel remotes that were shared from this server
          schema:
            type: boolean
        - name: include_deleted
          in: query
          description: Include those Shared channel remotes that have been deleted
          schema:
            type: boolean
        - name: page
          in: query
          description: The page to select
          schema:
            type: integer
        - name: per_page
          in: query
          description: The number of shared channels per page
          schema:
            type: integer
      responses:
        "200":
          description: Shared channel remotes fetch successful. Result might be empty.
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: "#/components/schemas/SharedChannelRemote"

        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"

  "/api/v4/sharedchannels/remote_info/{remote_id}":
    get:
      tags:
        - shared channels
      summary: Get remote cluster info by ID for user.
      description: |
        Get remote cluster info based on remoteId.

        __Minimum server version__: 5.50

        ##### Permissions
        Must be authenticated and user must belong to at least one channel shared with the remote cluster.
      operationId: GetRemoteClusterInfo
      parameters:
        - name: remote_id
          in: path
          description: Remote Cluster GUID
          required: true
          schema:
            type: string
        - name: include_deleted
          in: query
          description: Include deleted remote clusters
          schema:
            type: boolean
            default: false
      responses:
        "200":
          description: Remote cluster info retrieval successful
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/RemoteClusterInfo"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "404":
          $ref: "#/components/responses/NotFound"

  "/api/v4/remotecluster/{remote_id}/channels/{channel_id}/invite":
    post:
      tags:
        - shared channels
      summary: Invites a remote cluster to a channel.
      description: |
        Invites a remote cluster to a channel, sharing the channel if
        needed. If the remote cluster was already invited to the
        channel, calling this endpoint will have no effect.

        ##### Permissions
        `manage_shared_channels`
      operationId: InviteRemoteClusterToChannel
      parameters:
        - name: remote_id
          in: path
          description: The remote cluster GUID
          required: true
          schema:

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/api/v4/source/status.yaml =====

  "/api/v4/users/{user_id}/status":
    get:
      tags:
        - status
      summary: Get user status
      description: |
        Get user status by id from the server.
        ##### Permissions
        Must be authenticated.
      operationId: GetUserStatus
      parameters:
        - name: user_id
          in: path
          description: User ID
          required: true
          schema:
            type: string
      responses:
        "200":
          description: User status retrieval successful
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Status"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
    put:
      tags:
        - status
      summary: Update user status
      description: >
        Manually set a user's status. When setting a user's status, the status
        will remain that value until set "online" again, which will return the
        status to being automatically updated based on user activity.

        ##### Permissions

        Must have `edit_other_users` permission for the team.
      operationId: UpdateUserStatus
      parameters:
        - name: user_id
          in: path
          description: User ID
          required: true
          schema:
            type: string
      requestBody:
        content:
          application/json:
            schema:
              type: object
              required:
                - status
                - user_id
              properties:
                user_id:
                  type: string
                  description: User ID
                status:
                  type: string
                  description: User status, can be `online`, `away`, `offline` and `dnd`
                dnd_end_time:
                  type: integer
                  description: Time in epoch seconds at which a dnd status would be unset.
        description: Status object that is to be updated
        required: true
      responses:
        "200":
          description: User status update successful
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Status"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
  /api/v4/users/status/ids:
    post:
      tags:
        - status
      summary: Get user statuses by id
      description: |
        Get a list of user statuses by id from the server.
        ##### Permissions
        Must be authenticated.
      operationId: GetUsersStatusesByIds
      requestBody:
        content:
          application/json:
            schema:
              type: array
              items:
                type: string
        description: List of user ids to fetch
        required: true
      responses:
        "200":
          description: User statuses retrieval successful
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: "#/components/schemas/Status"
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
  "/api/v4/users/{user_id}/status/custom":
    put:
      tags:
        - status
      summary: Update user custom status
      description: |
        Updates a user's custom status by setting the value in the user's props and updates the user. Also save the given custom status to the recent custom statuses in the user's props
        ##### Permissions
        Must be logged in as the user whose custom status is being updated.
      operationId: UpdateUserCustomStatus
      parameters:
        - name: user_id
          in: path
          description: User ID
          required: true
          schema:
            type: string
      requestBody:
        content:
          application/json:
            schema:
              type: object
              required:
                - emoji
                - text
              properties:
                emoji:
                  type: string
                  description: Any emoji
                text:
                  type: string
                  description: Any custom status text
                duration:
                  type: string
                  description: Duration of custom status, can be `thirty_minutes`, `one_hour`, `four_hours`, `today`, `this_week` or `date_and_time`
                expires_at:
                  type: string
                  description: The time at which custom status should be expired. It should be in ISO format.
        description: Custom status object that is to be updated
        required: true
      responses:
        "200":
          description: User custom status update successful
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"

    delete:
      tags:
        - status
      summary: Unsets user custom status
      description: |
        Unsets a user's custom status by updating the user's props and updates the user
        ##### Permissions
        Must be logged in as the user whose custom status is being removed.
      operationId: UnsetUserCustomStatus
      parameters:
        - name: user_id
          in: path
          description: User ID
          required: true
          schema:
            type: string
      responses:
        "200":
          description: User custom status delete successful
        "400":
          $ref: "#/components/responses/BadRequest"

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/api/v4/source/system.yaml =====

  /api/v4/system/timezones:
    get:
      tags:
        - system
      summary: Retrieve a list of supported timezones
      description: >
        __Minimum server version__: 3.10

        ##### Permissions

        Must be logged in.
      operationId: GetSupportedTimezone
      responses:
        "200":
          description: List of timezones retrieval successful
          content:
            application/json:
              schema:
                type: array
                items:
                  type: string
        "500":
          $ref: "#/components/responses/InternalServerError"
  /api/v4/system/ping:
    get:
      tags:
        - system
      summary: Check system health
      description: >
        Check if the server is up and healthy based on the configuration setting
        `GoRoutineHealthThreshold`. If `GoRoutineHealthThreshold` and the number
        of goroutines on the server exceeds that threshold the server is
        considered unhealthy. If `GoRoutineHealthThreshold` is not set or the
        number of goroutines is below the threshold the server is considered
        healthy.

        __Minimum server version__: 3.10

        If a "device_id" is passed in the query, it will test the Push Notification
        Proxy in order to discover whether the device is able to receive notifications.
        The response will have a "CanReceiveNotifications" property with one of the
        following values:
        - true: It can receive notifications
        - false: It cannot receive notifications
        - unknown: There has been an unknown error, and it is not certain whether it can
          receive notifications.

        __Minimum server version__: 6.5

        If "use_rest_semantics" is set to true in the query, the endpoint will not return
        an error status code in the header if the request is somehow completed successfully.

        __Minimum server version__: 9.6

        ##### Permissions

        None. Authentication is not required for this endpoint.

        ##### Response Details

        The response varies based on query parameters and authentication:

        - **Basic response** (no parameters): Returns basic server information including
          `status`, mobile app versions, and active search backend.

        - **Enhanced response** (`get_server_status=true`): Additionally returns
          `database_status` and `filestore_status` to verify backend connectivity.
          Authentication is not required.

        - **Admin response** (`get_server_status=true` with `manage_system` permission):
          Additionally returns `root_status` indicating whether the server is running as root.
          Requires authentication with `manage_system` permission.
      operationId: GetPing
      parameters:
        - name: get_server_status
          in: query
          description: >
            Check the status of the database and file storage as well.
            When true, adds `database_status` and `filestore_status` to the response.
            If authenticated with `manage_system` permission, also adds `root_status`.
          required: false
          schema:
            type: boolean
        - name: device_id
          in: query
          description: Check whether this device id can receive push notifications
          required: false
          schema:
            type: string
        - name: use_rest_semantics
          in: query
          description: Returns 200 status code even if the server status is unhealthy.
          required: false
          schema:
            type: boolean
      responses:
        "200":
          description: Status of the system
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/SystemStatusResponse"
        "500":
          $ref: "#/components/responses/InternalServerError"
  /api/v4/websocket:
    get:
      tags:
        - system
      summary: Open a WebSocket connection
      description: |
        Upgrades the HTTP connection to a WebSocket connection used for real-time events and websocket actions.

        ##### Permissions
        No permission required to connect. Authentication can be performed via standard API auth (cookie/header)
        or by sending an `authentication_challenge` action after connecting.
      operationId: ConnectWebSocket
      security: []
      parameters:
        - name: connection_id
          in: query
          description: Existing connection identifier for reconnect flows.
          required: false
          schema:
            type: string
        - name: sequence_number
          in: query
          description: Last received sequence number for reconnect flows.
          required: false
          schema:
            type: string
        - name: posted_ack
          in: query
          description: Whether post acknowledgement events are enabled for this connection.
          required: false
          schema:
            type: boolean
        - name: disconnect_err_code
          in: query
          description: Optional close code used by clients to indicate disconnect reason.
          required: false
          schema:
            type: string
      responses:
        "101":
          description: Switching Protocols
        "400":
          $ref: "#/components/responses/BadRequest"

  /manualtest:
    get:
      tags:
        - system
      summary: Run manual testing helpers
      description: |
        Invokes manual test helpers used by developers and automated manual test scenarios.
        This endpoint is only registered when `ServiceSettings.EnableTesting` is enabled.

        ##### Permissions

        None. Authentication is not required; this route uses the same handler stack as other unauthenticated API handlers (`APIHandler`).

        __Security note:__ Only enable `EnableTesting` on non-production, developer-oriented deployments.
      operationId: ManualTest
      security: []
      parameters:
        - name: test
          in: query
          description: Name of the manual test to run.
          required: true
          schema:
            type: string
        - name: uid
          in: query
          description: Optional unique value used to randomize generated resources.
          required: false
          schema:
            type: string
        - name: username
          in: query
          description: Optional username used for helper account creation.

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/api/v4/source/teams.yaml =====

  /api/v4/teams:
    post:
      tags:
        - teams
      summary: Create a team
      description: |
        Create a new team on the system.
        ##### Permissions
        Must be authenticated and have the `create_team` permission.
      operationId: CreateTeam
      requestBody:
        content:
          application/json:
            schema:
              type: object
              required:
                - name
                - display_name
                - type
              properties:
                name:
                  type: string
                  description: Unique handler for a team, will be present in the team URL
                display_name:
                  type: string
                  description: Non-unique UI name for the team
                type:
                  type: string
                  description: "`'O'` for open, `'I'` for invite only"
        description: Team that is to be created
        required: true
      responses:
        "201":
          description: Team creation successful
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Team"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
    get:
      tags:
        - teams
      summary: Get teams
      description: >
        For regular users only returns open teams. Users with the
        "manage_system" permission will return teams regardless of type. The
        result is based on query string parameters - page and per_page.

        ##### Permissions

        Must be authenticated. "manage_system" permission is required to show all teams.
      operationId: GetAllTeams
      parameters:
        - name: page
          in: query
          description: The page to select.
          schema:
            type: integer
            default: 0
        - name: per_page
          in: query
          description: The number of teams per page.
          schema:
            type: integer
            default: 60
        - name: include_total_count
          description: >-
            Appends a total count of returned teams inside the response object - ex: `{ "teams": [], "total_count" : 0 }`.      
          in: query
          schema:
            type: boolean
            default: false
        - name: exclude_policy_constrained
          in: query
          schema:
            type: boolean
            default: false
          description: >-
            If set to true, teams which are part of a data retention policy will be excluded.
            The `sysconsole_read_compliance` permission is required to use this parameter.

            __Minimum server version__: 5.35
      responses:
        "200":
          description: Team list retrieval successful
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: "#/components/schemas/Team"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
  "/api/v4/teams/{team_id}":
    get:
      tags:
        - teams
      summary: Get a team
      description: |
        Get a team on the system.
        ##### Permissions
        Must be authenticated and have the `view_team` permission.
      operationId: GetTeam
      parameters:
        - name: team_id
          in: path
          description: Team GUID
          required: true
          schema:
            type: string
      responses:
        "200":
          description: Team retrieval successful
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Team"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "404":
          $ref: "#/components/responses/NotFound"
    put:
      tags:
        - teams
      summary: Update a team
      description: >
        Update a team by providing the team object. The fields that can be
        updated are defined in the request body, all other provided fields will
        be ignored.

        ##### Permissions

        Must have the `manage_team` permission.
      operationId: UpdateTeam
      parameters:
        - name: team_id
          in: path
          description: Team GUID
          required: true
          schema:
            type: string
      requestBody:
        content:
          application/json:
            schema:
              type: object
              required:
                - id
                - display_name
                - description
                - company_name
                - allowed_domains
                - invite_id
                - allow_open_invite
              properties:
                id:
                  type: string
                display_name:
                  type: string
                description:
                  type: string
                company_name:
                  type: string
                allowed_domains:
                  type: string
                invite_id:
                  type: string
                allow_open_invite:
                  type: string

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/api/v4/source/uploads.yaml =====

  "/api/v4/uploads":
    post:
      tags:
        - uploads
      summary: Create an upload
      description: >
        Creates a new upload session.


        __Minimum server version__: 5.28

        ##### Permissions

        Must have `upload_file` permission.

      operationId: CreateUpload
      requestBody:
        content:
          application/json:
            schema:
              type: object
              required:
                - channel_id
                - filename
                - file_size
              properties:
                channel_id:
                  description: The ID of the channel to upload to.
                  type: string
                filename:
                  description: The name of the file to upload.
                  type: string
                file_size:
                  description: The size of the file to upload in bytes.
                  type: integer
                  format: int64
        required: true
      responses:
        "201":
          description: Upload creation successful.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/UploadSession"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "413":
          $ref: "#/components/responses/TooLarge"
        "501":
          $ref: "#/components/responses/NotImplemented"
  "/api/v4/uploads/{upload_id}":
    get:
      tags:
        - uploads
      summary: Get an upload session
      description: |
        Gets an upload session that has been previously created.

        ##### Permissions
        Must be logged in as the user who created the upload session.
      operationId: GetUpload
      parameters:
        - name: upload_id
          in: path
          description: The ID of the upload session to get.
          required: true
          schema:
            type: string
      responses:
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "404":
          $ref: "#/components/responses/NotFound"
        "501":
          $ref: "#/components/responses/NotImplemented"
    post:
      tags:
        - uploads
      summary: Perform a file upload
      description: |
        Starts or resumes a file upload.  
        To resume an existing (incomplete) upload, data should be sent starting from the offset specified in the upload session object.

        The request body can be in one of two formats:
        - Binary file content streamed in request's body
        - multipart/form-data

        ##### Permissions
        Must be logged in as the user who created the upload session.
      operationId: UploadData
      parameters:
        - name: upload_id
          in: path
          description: The ID of the upload session the data belongs to.
          required: true
          schema:
            type: string
      requestBody:
        content:
          application/octet-stream:
            schema:
              type: string
              format: binary
          multipart/form-data:
            schema:
              type: object
              properties:
                file:
                  type: string
                  format: binary
      responses:
        "201":
          description: Upload successful
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/FileInfo"
        "204":
          description: Upload incomplete
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "413":
          $ref: "#/components/responses/TooLarge"
        "501":
          $ref: "#/components/responses/NotImplemented"

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/api/v4/source/usage.yaml =====

  /api/v4/usage/posts:
    get:
      tags:
        - usage
      summary: Get current usage of posts
      description: >
        Retrieve rounded off total no. of posts for this instance.
        Example: returns 4000 instead of 4321

        ##### Permissions

        Must be authenticated.

        __Minimum server version__: 7.0
      operationId: GetPostsUsage
      responses:
        "200":
          description: Total no. of posts returned successfully
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/PostsUsage"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "500":
          $ref: "#/components/responses/InternalServerError"
  /api/v4/usage/storage:
    get:
      tags:
        - usage
      summary: Get the total file storage usage for the instance in bytes.
      description: >
        Get the total file storage usage for the instance in bytes rounded down to the most significant digit.
        Example: returns 4000 instead of 4321

        ##### Permissions

        Must be authenticated.

        __Minimum server version__: 7.1
      operationId: GetStorageUsage
      responses:
        "200":
          description: The total file storage usage for the instance in bytes rounded down to the most significant digit.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/StorageUsage"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "500":
          $ref: "#/components/responses/InternalServerError"
  /api/v4/usage/teams:
    get:
      tags:
        - usage
      summary: Get current usage of teams
      description: >
        Retrieve rounded total number of teams for this instance.

        ##### Permissions
        Must be authenticated.
      operationId: GetTeamsUsage
      responses:
        "200":
          description: Total number of teams returned successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  active:
                    type: integer
                  cloud_archived:
                    type: integer
                  teams:
                    type: integer
        "401":
          $ref: "#/components/responses/Unauthorized"
        "500":
          $ref: "#/components/responses/InternalServerError"

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/api/v4/source/users.yaml =====

  /api/v4/users/login:
    post:
      tags:
        - users
      summary: Login to Mattermost server
      description: >
        ##### Permissions

        No permission required
      operationId: Login
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                id:
                  type: string
                login_id:
                  type: string
                token:
                  type: string
                device_id:
                  type: string
                voip_device_id:
                  description: VoIP push token. Same prefix shape as device_id. Optional; when provided, enables ring-style call push notifications.
                  type: string
                ldap_only:
                  type: boolean
                password:
                  description: The password used for email authentication.
                  type: string
                magic_link_token:
                  description: Magic link token for passwordless guest authentication. When provided, authenticates the user using the magic link token instead of password. Requires guest magic link feature to be enabled.
                  type: string
        description: User authentication object
        required: true
      responses:
        "201":
          description: User login successful
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/User"
        "400":
          $ref: "#/components/responses/BadRequest"
        "403":
          $ref: "#/components/responses/Forbidden"
  /api/v4/users/login/desktop_token:
    post:
      tags:
        - users
      summary: Login using desktop token
      description: >
        Login to Mattermost with a short-lived desktop token.

        ##### Permissions
        No permission required.
      operationId: LoginWithDesktopToken
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - token
              properties:
                token:
                  type: string
                device_id:
                  type: string
      responses:
        "200":
          description: Desktop token login successful
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/User"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
  /api/v4/users/login/cws:
    post:
      tags:
        - users
      summary: Auto-Login to Mattermost server using CWS token
      description: >
        CWS stands for Customer Web Server which is the cloud service used to
        manage cloud instances.

        ##### Permissions

        A Cloud license is required
      operationId: LoginByCwsToken
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                login_id:
                  type: string
                cws_token:
                  type: string
        description: User authentication object
        required: true
      responses:
        "302":
          description: Login successful, it'll redirect to login page to perform the autologin
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
  /api/v4/users/login/sso/code-exchange:
    post:
      deprecated: true
      tags:
        - users
      summary: Exchange SSO login code for session tokens
      description: >
        Exchange a short-lived login_code for session tokens using SAML code exchange (mobile SSO flow).

        **Deprecated:** This endpoint is deprecated and will be removed in a future release.
        Mobile clients should use the direct SSO callback flow instead.

        ##### Permissions

        No permission required.
      operationId: LoginSSOCodeExchange
      requestBody:
        content:
          application/json:
            schema:
              type: object
              required:
                - login_code
                - code_verifier
                - state
              properties:
                login_code:
                  description: Short-lived one-time code from SSO callback
                  type: string
                code_verifier:
                  description: SAML verifier to prove code possession
                  type: string
                state:
                  description: State parameter to prevent CSRF attacks
                  type: string
        description: SSO code exchange object
        required: true
      responses:
        "200":
          description: Code exchange successful
          content:
            application/json:
              schema:
                type: object
                properties:
                  token:
                    description: Session token for authentication
                    type: string
                  csrf:
                    description: CSRF token for request validation
                    type: string
        "400":
          $ref: "#/components/responses/BadRequest"
        "403":
          $ref: "#/components/responses/Forbidden"
        "410":
          description: Endpoint is deprecated and disabled
  /oauth/intune:
    post:
      tags:
        - users

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/api/v4/source/views.yaml =====

  /api/v4/channels/{channel_id}/views:
    get:
      tags:
        - views
      summary: List channel views
      description: |
        *__Experimental__: This endpoint is experimental and may change or be removed in a future release.*

        Get a list of views for a channel.

        __Minimum server version__: 11.6

        ##### Permissions
        Must have `read_channel_content` permission for the channel.
      operationId: ListChannelViews
      parameters:
        - name: channel_id
          in: path
          description: Channel GUID
          required: true
          schema:
            type: string
        - name: per_page
          in: query
          description: The number of views per page (default 60, max 200)
          required: false
          schema:
            type: integer
            default: 60
            maximum: 200
        - name: page
          in: query
          description: The 0-based page number for pagination (default 0)
          required: false
          schema:
            type: integer
            default: 0
            minimum: 0
        - name: include_total_count
          in: query
          description: >
            When true, the response is a ViewsWithCount object containing
            a views array and a total_count integer. When false or omitted,
            the response is a plain JSON array of View objects.
          required: false
          schema:
            type: boolean
            default: false
      responses:
        "200":
          description: Channel views retrieval successful
          content:
            application/json:
              schema:
                oneOf:
                  - type: array
                    items:
                      $ref: "#/components/schemas/View"
                    description: Plain array of views (default, when include_total_count is false)
                  - $ref: "#/components/schemas/ViewsWithCount"
                    description: Views with total count (when include_total_count is true)
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "404":
          $ref: "#/components/responses/NotFound"
        "500":
          $ref: "#/components/responses/InternalServerError"

    post:
      tags:
        - views
      summary: Create channel view
      description: |
        *__Experimental__: This endpoint is experimental and may change or be removed in a future release.*

        Create a new view for a channel.

        __Minimum server version__: 11.6

        ##### Permissions
        Must have `create_post` permission for the channel.
      operationId: CreateChannelView
      parameters:
        - name: channel_id
          in: path
          description: Channel GUID
          required: true
          schema:
            type: string
      requestBody:
        content:
          application/json:
            schema:
              type: object
              required:
                - title
                - type
              properties:
                title:
                  type: string
                  description: The title of the view
                  maxLength: 256
                type:
                  type: string
                  enum: [kanban]
                  description: |
                    The type of the view.
                    * `kanban` - a kanban view
                description:
                  type: string
                  description: The description of the view
                  maxLength: 1024
                sort_order:
                  type: integer
                  description: The display order of the view within the channel
                props:
                  type: object
                  description: Arbitrary key-value properties for the view
                  additionalProperties: true
        description: View object to be created
        required: true
      responses:
        "201":
          description: Channel view creation successful
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/View"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "404":
          $ref: "#/components/responses/NotFound"
        "500":
          $ref: "#/components/responses/InternalServerError"

  /api/v4/channels/{channel_id}/views/{view_id}:
    get:
      tags:
        - views
      summary: Get a channel view
      description: |
        *__Experimental__: This endpoint is experimental and may change or be removed in a future release.*

        Get a single view by its ID.

        __Minimum server version__: 11.6

        ##### Permissions
        Must have `read_channel_content` permission for the channel.
      operationId: GetChannelView
      parameters:
        - name: channel_id
          in: path
          description: Channel GUID
          required: true
          schema:
            type: string
        - name: view_id
          in: path
          description: View GUID
          required: true
          schema:
            type: string
      responses:
        "200":
          description: Channel view retrieval successful
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/View"
        "400":
          $ref: "#/components/responses/BadRequest"

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/api/v4/source/webhooks.yaml =====

  /api/v4/hooks/incoming:
    post:
      tags:
        - webhooks
      summary: Create an incoming webhook
      description: |
        Create an incoming webhook for a channel.
        ##### Permissions
        `manage_webhooks` for the team the webhook is in.

        `manage_others_incoming_webhooks` for the team the webhook is in if the user is different than the requester.
      operationId: CreateIncomingWebhook
      requestBody:
        content:
          application/json:
            schema:
              type: object
              required:
                - channel_id
              properties:
                channel_id:
                  type: string
                  description: The ID of a public channel or private group that receives
                    the webhook payloads.
                user_id:
                  type: string
                  description: The ID of the owner of the webhook if different than the requester. Required for [local mode](https://docs.mattermost.com/administration/mmctl-cli-tool.html#local-mode).
                display_name:
                  type: string
                  description: The display name for this incoming webhook
                description:
                  type: string
                  description: The description for this incoming webhook
                username:
                  type: string
                  description: The username this incoming webhook will post as.
                icon_url:
                  type: string
                  description: The profile picture this incoming webhook will use when
                    posting.
                channel_locked:
                  type: boolean
                  description: Whether the webhook is locked to the channel.
        description: Incoming webhook to be created
        required: true
      responses:
        "201":
          description: Incoming webhook creation successful
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/IncomingWebhook"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
    get:
      tags:
        - webhooks
      summary: List incoming webhooks
      description: >
        Get a page of a list of incoming webhooks. Optionally filter for a
        specific team using query parameters.

        ##### Permissions

        `manage_webhooks` for the system or `manage_webhooks` for the specific team.
      operationId: GetIncomingWebhooks
      parameters:
        - name: page
          in: query
          description: The page to select.
          schema:
            type: integer
            default: 0
        - name: per_page
          in: query
          description: The number of hooks per page.
          schema:
            type: integer
            default: 60
        - name: team_id
          in: query
          description: The ID of the team to get hooks for.
          schema:
            type: string
        - name: include_total_count
          description: >-
            Appends a total count of returned hooks inside the response object - ex: `{ "incoming_webhooks": [], "total_count": 0 }`.
          in: query
          schema:
            type: boolean
            default: false
      responses:
        "200":
          description: Incoming webhooks retrieval successful
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: "#/components/schemas/IncomingWebhook"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
  "/api/v4/hooks/incoming/{hook_id}":
    get:
      tags:
        - webhooks
      summary: Get an incoming webhook
      description: >
        Get an incoming webhook given the hook id.

        ##### Permissions

        `manage_webhooks` for system or `manage_webhooks` for the specific team or `manage_webhooks` for the channel.
      operationId: GetIncomingWebhook
      parameters:
        - name: hook_id
          in: path
          description: Incoming Webhook GUID
          required: true
          schema:
            type: string
      responses:
        "200":
          description: Webhook retrieval successful
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/IncomingWebhook"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "404":
          $ref: "#/components/responses/NotFound"
    delete:
      tags:
        - webhooks
      summary: Delete an incoming webhook
      description: >
        Delete an incoming webhook given the hook id.

        ##### Permissions

        `manage_webhooks` for system or `manage_webhooks` for the specific team or `manage_webhooks` for the channel.
      operationId: DeleteIncomingWebhook
      parameters:
        - name: hook_id
          in: path
          description: Incoming webhook GUID
          required: true
          schema:
            type: string
      responses:
        "200":
          description: Webhook deletion successful
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/StatusOK"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "404":
          $ref: "#/components/responses/NotFound"
    put:
      tags:
        - webhooks

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/e2e-tests/.ci/dashboard.override.yml =====

---
services:
  dashboard:
    image: mattermostdevelopment/mirrored-node:18.17
    environment:
      PG_URI: postgres://mmuser:mostest@db:5432/automation_dashboard_db
      JWT_SECRET: s8gGBA3ujKRohSw1L8HLOY7Jjnu2ZYv8 # Generated with e.g. `dd if=/dev/urandom count=24 bs=1 2>/dev/null | base64 -w0`
      JWT_USER: cypress-test
      JWT_ROLE: integration
      JWT_ALG: HS256
      JWT_EXPIRES_IN: 365d
      ALLOWED_USER: cypress-test
      ALLOWED_ROLE: integration
    healthcheck:
      test: ["CMD", "curl", "-s", "-o/dev/null", "127.0.0.1:4000"]
      interval: 10s
      timeout: 15s
      retries: 12
    volumes:
      - "../:/app"
      - "../../dashboard.entrypoint.sh:/usr/local/bin/dashboard.entrypoint.sh:ro"
    working_dir: /app
    entrypoint: /usr/local/bin/dashboard.entrypoint.sh
    ports:
      - 4000:4000

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/e2e-tests/README.md =====

# E2E testing for the Mattermost web client

This directory contains the E2E testing code for the Mattermost web client.

### How to run locally

##### For test case development

Please refer to the [dedicated developer documentation](https://developers.mattermost.com/contribute/more-info/webapp/e2e-testing/) for instructions.

##### For pipeline debugging

The E2E testing pipeline's scripts depend on the following tools being installed on your system: `docker`, `docker-compose`, `make`, `git`, `jq`, `node`, and some common utilities (`coreutils`, `findutils`, `bash`, `awk`, `sed`, `grep`)

Instructions, tl;dr: create a local branch with your E2E test changes, then open a PR to the `mattermost-server` repo targeting the `master` branch (so that CI will produce the image that docker-compose needs), then run `make` in this directory.

Instructions, detailed:
1. (optional, undefined variables are set to sane defaults) Create the `.ci/env` file, and populate it with the variables you need out of the following list:
  * `SERVER`: either `onprem` (default) or `cloud`.
  * `CWS_URL` (mandatory when `SERVER=cloud`, only used in such case): when spinning up a cloud-like test server that communicates with a test instance of a customer web server.
  * `TEST`: either `cypress` (default), `playwright`, or `none` (to avoid creating the cypress/playwright sidecar containers, e.g. if you only want to launch a server instance)
  * `ENABLED_DOCKER_SERVICES`: a space-separated list of services to start alongside the server. Default to `postgres inbucket`, for smoke test purposes and for lightweight and faster start-up time. Depending on the test requirement being worked on, you may want to override as needed, as such:
    - Cypress full tests require all services to be running: `postgres inbucket minio openldap elasticsearch keycloak`.
    - Cypress smoke tests require only the following: `postgres inbucket`.
    - Playwright full tests require only the following: `postgres inbucket`.
  * The following variables, will be passed over to the server container: `MM_LICENSE` (no enterprise features will be available if this is unset; required when `SERVER=cloud`), and the exploded `MM_ENV` (a comma-separated list of env var specifications)
  * The following variables, which will be passed over to the cypress container: `BRANCH`, `BUILD_ID`, `CI_BASE_URL`, `BROWSER`, `AUTOMATION_DASHBOARD_URL` and `AUTOMATION_DASHBOARD_TOKEN`
  * The `SERVER_IMAGE` variable can also be set if you want to select a custom mattermost-server image. If not specified, the value of the `SERVER_IMAGE_DEFAULT` variable defined in file `.ci/.e2erc` is used.
  * The `TEST_FILTER` variable can also be set, to customize which tests you want Cypress/Playwright to run. If not specified, only the smoke tests will run
    - Its format depends on which tool is used: for Cypress, please check the `e2e-tests/cypress/run_tests.js` file for details. For Playwright, it can simply be populated with arguments you want to give to the `playwright test` command.
  * More variables may be required to configure reporting and cloud interactions. Check the content of the `.ci/report.*.sh` and `.ci/server.cloud_*.sh` scripts for reference.
2. (optional) `make start-dashboard && make generate-test-cycle`: start the automation dashboard in the background, and initiate a test cycle on it, for the given `BUILD_ID`
  * NB: the `BUILD_ID` value should stay the same across the `make generate-test-cycle` command, and the subsequent `make` (see next step). If you need to initiate a new test cycle on the same dashboard, you'll need to change the `BUILD_ID` value and rerun both `make generate-test-cycle` and `make`.
  * Note that part of the dashboard functionality assumes the `BUILD_ID` to have a certain format (see [here](https://github.com/saturninoabril/automation-dashboard/blob/175891781bf1072c162c58c6ec0abfc5bcb3520e/lib/common_utils.ts#L3-L23) for details). This is not relevant for local running, but it's important to note in the testing pipelines.
  * This also automatically sets the `AUTOMATION_DASHBOARD_URL` and `AUTOMATION_DASHBOARD_TOKEN` variables for the cypress container
  * Note that if you run the dashboard locally, but also specify other `AUTOMATION_DASHBOARD_*` variables in your `.ci/env` file, the latter variables will take precedence.
  * The dashboard is used for orchestrating specs with parallel test runs and is typically used in CI.
  * Only Cypress is currently using the dashboard; Playwright is not.
3. `make`: start and prepare the server, then run the Cypress smoke tests
  * You can track the progress of the run in the `http://localhost:4000/cycles` dashboard if you launched it locally
  * For `SERVER=cloud` runs, you'll need to first create a cloud customer against the specified `CWS_URL` service by running `make cloud-init`. The user isn't automatically removed, and may be reused across multiple runs until you run `make cloud-teardown` to delete it.
  * If you want to run the Playwright tests instead of the Cypress ones, you can run `TEST=playwright make`
  * If you just want to run a local server instance, without any further testing, you can run `TEST=none make`
  * If you're using the automation dashboard, you have the option of sharding the E2E test run: you can launch the `make` command in parallel on different machines (NB: you must use the same `BUILD_ID` and `BRANCH` values that you used for `make generate-test-cycle`) to distribute running the test cases across them. When doing this, you should also set on each machine the `CI_BASE_URL` variable to a value that uniquely identifies the instance where `make` is running.
  * This script will also parse the local test results, and write a `e2e-tests/${TEST}/results/summary.json` file containing the following keys: `passed`, `failed` and `failed_expected` (the total number of testcases that were run is the sum of these three numbers)
4. `make stop`: tears down the server (and the dashboard, if running)
  * This will stop and cleanup all of the E2E testing containers, including the database and its persistent volume.
  * This also implicitly runs `make clean`, which also removes any generated environment or docker-compose files.

Notes:
- Setting a variable in `.ci/env` is functionally equivalent to exporting variables in your current shell's environment, before invoking the makefile.
- The `.ci/.env.*` files are auto-generated by the pipeline scripts and aren't meant to be modified manually. The only file you should edit to control the containers' environment is `.ci/env`, as specified in the instructions above.
- All of the variables in `.ci/env` must be set before the `make generate-server` command is run (or, if using the dashboard, before the `make generate-test-cycle` command). Modifying that file afterward has no effect because the containers' env files are generated in that step.
- If you restart the dashboard at any point, you must also restart the server containers, so that it picks up the new IP of the dashboard from the newly generated `.env.dashboard` file
- If new variables need to be passed to any of the containers, here are the general principles to follow when deciding where to populate it:
  * If their value is fixed (e.g. a static server configuration), these may be simply added to the `docker_compose_generator.sh` file, to the appropriate container.
  * If you need to introduce variables that you want to control from `.ci/env`: you need to update the scripts under the `.ci/` dir and configure them to write the new variables' values over to the appropriate `.env.*` file. In particular, avoid defining variables that depend on other variables within the docker-compose override files: this is to ensure uniformity in their availability and simplifies the question of what container has access to which variable considerably.
  * Exceptions are of course accepted wherever it makes sense (e.g. if you need to group variables based on some common functionality)
- The `report` Make target is meant for internal usage. Usage and variables are documented in the respective scripts.
- `make start-server` won't cleanup containers that don't change across runs. This means that you can use it to emulate a Mattermost server upgrade while retaining your database data by simply changing the `SERVER_IMAGE` variable on your machine, and then re-running `make start-server`. But this also means that if you want to run a clean local environment, you may have to manually run `make stop` to cleanup any running containers and their volumes, which include e.g. the database.

##### For code changes:
* `make fmt-ci` to format and check yaml files and shell scripts.

##### For test stressing an E2E testcase

For Cypress:
1. Enter the `cypress/` subdirectory
2. Identify which test files you want to run, and how many times each. For instance: suppose you want to run `create_a_team_spec.js` and `demoted_user_spec.js` (which you can locate with the `find` command, under `cypress/tests/`), each run 3 times
3. Run the chosen testcases the desired amount of times: `node run_tests.js --include-file=create_a_team_spec.js,demoted_user_spec.js --invert --stress-test-count=3`
  * Your system needs to be setup for Cypress usage, to be able to run this command. Refer to the [E2E testing developer documentation](https://developers.mattermost.com/contribute/more-info/webapp/e2e-testing/) for this.
4. The `cypress/results/testPasses.json` file will count, for each of the testfiles, how many times it was run, and how many times each of the testcases contained in it passed. If the attempts and passes numbers do not match, that specific testcase may be flaky.

For Playwright: WIP

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/e2e-tests/cypress/README-Subpath.md =====

# Testing with subpath servers
Some tests need multiple servers running in subpath mode. These tests have the cypress `Group: @subpath` metadata near the top of the test file. Instructions on running a server under subpath can be found here: [https://developers.mattermost.com/blog/subpath/](https://developers.mattermost.com/blog/subpath/)

In the `cypress.json` configuration file, the `baseURL` setting will need to be updated with the subpath URL of the first server, and the `secondServerURL` setting with the subpath URL of the second server.

### Running subpath tests on local machine
Two mattermost servers running on the same machine must be served from different ports. To have the servers respond on the same URL and the same port under different subpaths, you will need to use a reverse proxy (nginx or apache) to proxy the same local url to both mattermost servers under different subpaths.

#### Example set up using NGINX:

You'll need to run two Mattermost servers.

1. Set the `SiteURL` and the listening port for the first server:

```
"SiteURL": "http://localhost/company/mattermost1"
"ListenAddress": ":8065",
```

2. Set the `SiteURL` and the listening port for the second server:

```
"SiteURL": "http://localhost/company/mattermost2"
"ListenAddress": ":8066",
```

The DB `DataSource` will need to be different for both servers.

3. Install NGINX -  exact steps depend on your OS

4. Update your NGINX site configuration. The specific details for each setting can be found in the [Mattermost docs](https://docs.mattermost.com/install/config-proxy-nginx.html)

```
upstream backend1 {
   server localhost:8065;
   keepalive 32;
}

upstream backend2 {
   server localhost:8066;
   keepalive 32;
}

server {
        listen 80 default_server;
        listen [::]:80 default_server;

        location ~ /company/mattermost1/api/v[0-9]+/(users/)?websocket$ {
               client_body_timeout 60;
               client_max_body_size 50M;
               lingering_timeout 5;
               proxy_buffer_size 16k;
               proxy_buffers 256 16k;
               proxy_connect_timeout 90;
               proxy_pass http://backend1;
               proxy_read_timeout 90s;
               proxy_send_timeout 300;
               proxy_set_header Connection "upgrade";
               proxy_set_header Host $host;
               proxy_set_header Upgrade $http_upgrade;
               proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
               proxy_set_header X-Forwarded-Proto $scheme;
               proxy_set_header X-Frame-Options SAMEORIGIN;
               proxy_set_header X-Real-IP $remote_addr;
               send_timeout 300;
        }

        location /company/mattermost1 {
                client_max_body_size 50M;
                proxy_buffer_size 16k;
                proxy_buffers 256 16k;
                proxy_cache_lock on;
                proxy_cache_min_uses 2;
                proxy_cache_revalidate on;
                proxy_cache_use_stale timeout;
                proxy_http_version 1.1;
                proxy_pass http://backend1;
                proxy_read_timeout 600s;
                proxy_set_header Connection "";
                proxy_set_header Host $http_host;
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                proxy_set_header X-Forwarded-Proto $scheme;
                proxy_set_header X-Frame-Options SAMEORIGIN;
                proxy_set_header X-Real-IP $remote_addr;
        }

        location ~ /company/mattermost2/api/v[0-9]+/(users/)?websocket$ {
               client_body_timeout 60;
               client_max_body_size 50M;
               lingering_timeout 5;
               proxy_buffer_size 16k;
               proxy_buffers 256 16k;
               proxy_connect_timeout 90;
               proxy_pass http://backend2;
               proxy_read_timeout 90s;
               proxy_send_timeout 300;
               proxy_set_header Connection "upgrade";
               proxy_set_header Host $host;
               proxy_set_header Upgrade $http_upgrade;
               proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
               proxy_set_header X-Forwarded-Proto $scheme;
               proxy_set_header X-Frame-Options SAMEORIGIN;
               proxy_set_header X-Real-IP $remote_addr;
               send_timeout 300;
        }

        location /company/mattermost2 {
                proxy_buffer_size 16k;
                proxy_buffers 256 16k;
                proxy_cache_lock on;
                proxy_cache_min_uses 2;
                proxy_cache_revalidate on;
                proxy_cache_use_stale timeout;
                proxy_http_version 1.1;
                proxy_pass http://backend2;
                proxy_read_timeout 600s;
                proxy_set_header Connection "";
                proxy_set_header Host $http_host;
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                proxy_set_header X-Forwarded-Proto $scheme;
                proxy_set_header X-Frame-Options SAMEORIGIN;
                proxy_set_header X-Real-IP $remote_addr;
                client_max_body_size 50M;
        }
}
```

5. Restart NGINX to reload the configuration. Exact steps depend on your OS/distribution. On most Linux distributions you can run `sudo systemctl restart nginx`

6. In the `cypress.json` file, set `baseURL` to  `"http://localhost/company/mattermost1"` and `secondServerURL` to `"http://localhost/company/mattermost2"`

7. Start both Mattermost tests and run the e2e tests.

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/e2e-tests/cypress/package-lock.json =====

{
  "name": "cypress",
  "lockfileVersion": 3,
  "requires": true,
  "packages": {
    "": {
      "name": "cypress",
      "devDependencies": {
        "@aws-sdk/client-s3": "3.1030.0",
        "@aws-sdk/lib-storage": "3.1030.0",
        "@cypress/request": "3.0.10",
        "@cypress/webpack-preprocessor": "7.1.0",
        "@mattermost/client": "11.5.0",
        "@mattermost/eslint-plugin": "file:../../webapp/platform/eslint-plugin",
        "@mattermost/types": "11.5.0",
        "@testing-library/cypress": "10.1.0",
        "@types/async": "3.2.25",
        "@types/authenticator": "1.1.4",
        "@types/express": "5.0.6",
        "@types/fs-extra": "11.0.4",
        "@types/lodash": "4.17.24",
        "@types/lodash.intersection": "4.4.9",
        "@types/lodash.mapkeys": "4.6.9",
        "@types/lodash.without": "4.4.9",
        "@types/mime-types": "3.0.1",
        "@types/mochawesome": "6.2.5",
        "@types/recursive-readdir": "2.2.4",
        "@types/shelljs": "0.10.0",
        "async": "3.2.6",
        "authenticator": "1.1.5",
        "axios": "1.15.0",
        "chai": "6.2.2",
        "chalk": "5.6.2",
        "client-oauth2": "github:larkox/js-client-oauth2#e24e2eb5dfcbbbb3a59d095e831dbe0012b0ac49",
        "cross-env": "10.1.0",
        "cypress": "15.13.1",
        "cypress-file-upload": "5.0.8",
        "cypress-multi-reporters": "2.0.5",
        "cypress-plugin-tab": "2.0.0",
        "cypress-real-events": "1.15.0",
        "cypress-wait-until": "3.0.2",
        "dayjs": "1.11.20",
        "deepmerge": "4.3.1",
        "dotenv": "17.4.2",
        "eslint": "9.39.3",
        "eslint-plugin-cypress": "^6.3.1",
        "eslint-plugin-no-only-tests": "^3.4.0",
        "express": "5.2.1",
        "extract-zip": "2.0.1",
        "globals": "17.5.0",
        "jiti": "2.6.1",
        "knex": "3.2.9",
        "localforage": "1.10.0",
        "lodash.intersection": "4.4.0",
        "lodash.mapkeys": "4.6.0",
        "lodash.without": "4.4.0",
        "lodash.xor": "4.5.0",
        "mime": "4.1.0",
        "mime-types": "3.0.2",
        "mocha": "11.7.5",
        "mocha-junit-reporter": "2.2.1",
        "mocha-multi-reporters": "1.5.1",
        "mochawesome": "7.1.4",
        "mochawesome-merge": "5.1.1",
        "mochawesome-report-generator": "6.3.2",
        "moment-timezone": "0.6.1",
        "node-polyfill-webpack-plugin": "4.1.0",
        "pdf-parse": "2.4.5",
        "pg": "8.20.0",
        "recursive-readdir": "2.2.3",
        "shelljs": "0.10.0",
        "timezones.json": "1.7.2",
        "ts-loader": "9.5.7",
        "typescript": "6.0.2",
        "uuid": "13.0.0",
        "yargs": "18.0.0"
      }
    },
    "../../webapp/platform/eslint-plugin": {
      "name": "@mattermost/eslint-plugin",
      "version": "2.0.0",
      "dev": true,
      "license": "Apache 2.0",
      "dependencies": {
        "@stylistic/eslint-plugin": "^5.10.0",
        "@typescript-eslint/eslint-plugin": "^8.61.0",
        "@typescript-eslint/parser": "^8.61.0",
        "eslint-plugin-headers": "^1.3.4",
        "eslint-plugin-import": "^2.32.0",
        "eslint-plugin-jsx-a11y": "^6.10.2",
        "eslint-plugin-react": "^7.37.5",
        "eslint-plugin-react-hooks": "^7.1.1",
        "jsx-ast-utils": "^3.3.3"
      },
      "peerDependencies": {
        "eslint": "^9.0.0"
      },
      "peerDependenciesMeta": {
        "eslint-plugin-react": {
          "optional": true
        },
        "eslint-plugin-react-hooks": {
          "optional": true
        }
      }
    },
    "node_modules/@aws-crypto/crc32": {
      "version": "5.2.0",
      "resolved": "https://registry.npmjs.org/@aws-crypto/crc32/-/crc32-5.2.0.tgz",
      "integrity": "sha512-nLbCWqQNgUiwwtFsen1AdzAtvuLRsQS8rYgMuxCrdKf9kOssamGLuPwyTY9wyYblNr9+1XM8v6zoDTPPSIeANg==",
      "dev": true,
      "license": "Apache-2.0",
      "dependencies": {
        "@aws-crypto/util": "^5.2.0",
        "@aws-sdk/types": "^3.222.0",
        "tslib": "^2.6.2"
      },
      "engines": {
        "node": ">=16.0.0"
      }
    },
    "node_modules/@aws-crypto/crc32c": {
      "version": "5.2.0",
      "resolved": "https://registry.npmjs.org/@aws-crypto/crc32c/-/crc32c-5.2.0.tgz",
      "integrity": "sha512-+iWb8qaHLYKrNvGRbiYRHSdKRWhto5XlZUEBwDjYNf+ly5SVYG6zEoYIdxvf5R3zyeP16w4PLBn3rH1xc74Rag==",
      "dev": true,
      "license": "Apache-2.0",
      "dependencies": {
        "@aws-crypto/util": "^5.2.0",
        "@aws-sdk/types": "^3.222.0",
        "tslib": "^2.6.2"
      }
    },
    "node_modules/@aws-crypto/sha1-browser": {
      "version": "5.2.0",
      "resolved": "https://registry.npmjs.org/@aws-crypto/sha1-browser/-/sha1-browser-5.2.0.tgz",
      "integrity": "sha512-OH6lveCFfcDjX4dbAvCFSYUjJZjDr/3XJ3xHtjn3Oj5b9RjojQo8npoLeA/bNwkOkrSQ0wgrHzXk4tDRxGKJeg==",
      "dev": true,
      "license": "Apache-2.0",
      "dependencies": {
        "@aws-crypto/supports-web-crypto": "^5.2.0",
        "@aws-crypto/util": "^5.2.0",
        "@aws-sdk/types": "^3.222.0",
        "@aws-sdk/util-locate-window": "^3.0.0",
        "@smithy/util-utf8": "^2.0.0",
        "tslib": "^2.6.2"
      }
    },
    "node_modules/@aws-crypto/sha1-browser/node_modules/@smithy/is-array-buffer": {
      "version": "2.2.0",
      "resolved": "https://registry.npmjs.org/@smithy/is-array-buffer/-/is-array-buffer-2.2.0.tgz",
      "integrity": "sha512-GGP3O9QFD24uGeAXYUjwSTXARoqpZykHadOmA8G5vfJPK0/DC67qa//0qvqrJzL1xc8WQWX7/yc7fwudjPHPhA==",
      "dev": true,
      "license": "Apache-2.0",
      "dependencies": {
        "tslib": "^2.6.2"
      },
      "engines": {
        "node": ">=14.0.0"
      }
    },
    "node_modules/@aws-crypto/sha1-browser/node_modules/@smithy/util-buffer-from": {
      "version": "2.2.0",
      "resolved": "https://registry.npmjs.org/@smithy/util-buffer-from/-/util-buffer-from-2.2.0.tgz",
      "integrity": "sha512-IJdWBbTcMQ6DA0gdNhh/BwrLkDR+ADW5Kr1aZmd4k3DIF6ezMV4R2NIAmT08wQJ3yUK82thHWmC/TnK/wpMMIA==",
      "dev": true,
      "license": "Apache-2.0",
      "dependencies": {
        "@smithy/is-array-buffer": "^2.2.0",
        "tslib": "^2.6.2"
      },
      "engines": {
        "node": ">=14.0.0"
      }
    },
    "node_modules/@aws-crypto/sha1-browser/node_modules/@smithy/util-utf8": {
      "version": "2.3.0",
      "resolved": "https://registry.npmjs.org/@smithy/util-utf8/-/util-utf8-2.3.0.tgz",
      "integrity": "sha512-R8Rdn8Hy72KKcebgLiv8jQcQkXoLMOGGv5uI1/k0l+snqkOzQ1R0ChUBCxWMlBsFMekWjq0wRudIweFs7sKT5A==",
      "dev": true,

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/e2e-tests/cypress/package.json =====

{
  "name": "cypress",
  "devDependencies": {
    "@aws-sdk/client-s3": "3.1030.0",
    "@aws-sdk/lib-storage": "3.1030.0",
    "@cypress/request": "3.0.10",
    "@cypress/webpack-preprocessor": "7.1.0",
    "@mattermost/client": "11.5.0",
    "@mattermost/eslint-plugin": "file:../../webapp/platform/eslint-plugin",
    "@mattermost/types": "11.5.0",
    "@testing-library/cypress": "10.1.0",
    "@types/async": "3.2.25",
    "@types/authenticator": "1.1.4",
    "@types/express": "5.0.6",
    "@types/fs-extra": "11.0.4",
    "@types/lodash": "4.17.24",
    "@types/lodash.intersection": "4.4.9",
    "@types/lodash.mapkeys": "4.6.9",
    "@types/lodash.without": "4.4.9",
    "@types/mime-types": "3.0.1",
    "@types/mochawesome": "6.2.5",
    "@types/recursive-readdir": "2.2.4",
    "@types/shelljs": "0.10.0",
    "async": "3.2.6",
    "authenticator": "1.1.5",
    "axios": "1.15.0",
    "chai": "6.2.2",
    "chalk": "5.6.2",
    "client-oauth2": "github:larkox/js-client-oauth2#e24e2eb5dfcbbbb3a59d095e831dbe0012b0ac49",
    "cross-env": "10.1.0",
    "cypress": "15.13.1",
    "cypress-file-upload": "5.0.8",
    "cypress-multi-reporters": "2.0.5",
    "cypress-plugin-tab": "2.0.0",
    "cypress-real-events": "1.15.0",
    "cypress-wait-until": "3.0.2",
    "dayjs": "1.11.20",
    "deepmerge": "4.3.1",
    "dotenv": "17.4.2",
    "eslint": "9.39.3",
    "eslint-plugin-cypress": "^6.3.1",
    "eslint-plugin-no-only-tests": "^3.4.0",
    "express": "5.2.1",
    "extract-zip": "2.0.1",
    "globals": "17.5.0",
    "jiti": "2.6.1",
    "knex": "3.2.9",
    "localforage": "1.10.0",
    "lodash.intersection": "4.4.0",
    "lodash.mapkeys": "4.6.0",
    "lodash.without": "4.4.0",
    "lodash.xor": "4.5.0",
    "mime": "4.1.0",
    "mime-types": "3.0.2",
    "mocha": "11.7.5",
    "mocha-junit-reporter": "2.2.1",
    "mocha-multi-reporters": "1.5.1",
    "mochawesome": "7.1.4",
    "mochawesome-merge": "5.1.1",
    "mochawesome-report-generator": "6.3.2",
    "moment-timezone": "0.6.1",
    "node-polyfill-webpack-plugin": "4.1.0",
    "pdf-parse": "2.4.5",
    "pg": "8.20.0",
    "recursive-readdir": "2.2.3",
    "shelljs": "0.10.0",
    "timezones.json": "1.7.2",
    "ts-loader": "9.5.7",
    "typescript": "6.0.2",
    "uuid": "13.0.0",
    "yargs": "18.0.0"
  },
  "overrides": {
    "@mattermost/client": {
      "typescript": "^6.0.2"
    },
    "@mattermost/types": {
      "typescript": "^6.0.2"
    }
  },
  "scripts": {
    "check-types": "tsc -b",
    "cypress:open": "cross-env TZ=Etc/UTC cypress open",
    "cypress:run": "cross-env TZ=Etc/UTC cypress run",
    "cypress:run:chrome": "cross-env TZ=Etc/UTC cypress run --browser chrome",
    "cypress:run:firefox": "cross-env TZ=Etc/UTC cypress run --browser firefox",
    "cypress:run:edge": "cross-env TZ=Etc/UTC cypress run --browser edge",
    "cypress:run:electron": "cross-env TZ=Etc/UTC cypress run --browser electron",
    "benchmarks:run-server": "cd mattermost && bin/mattermost",
    "start:webhook": "node webhook_serve.js",
    "pretest": "npm run clean",
    "test": "cross-env TZ=Etc/UTC cypress run",
    "test:smoke": "node run_tests.js --stage='@prod' --group='@smoke'",
    "test:ci": "node run_tests.js",
    "uniq-meta": "grep -r \"^// $META:\" cypress | grep -ow '@\\w*' | sort | uniq",
    "check": "eslint .",
    "fix": "eslint . --quiet --fix --cache"
  }
}

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/e2e-tests/cypress/reporter-config.json =====

{
  "reporterEnabled": "mocha-junit-reporter, mochawesome",
  "mochaJunitReporterReporterOptions": {
    "mochaFile": "results/junit/test_results[hash].xml",
    "toConsole": false
  },
  "mochawesomeReporterOptions": {
    "reportDir": "results/mochawesome-report",
    "reportFilename": "json/tests/[name]",
    "quiet": true,
    "overwrite": false,
    "html": false,
    "json": true
  }
}

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/e2e-tests/cypress/tests/extensions/Ignore-X-Frame-headers/manifest.json =====

{
  "update_url": "https://clients2.google.com/service/update2/crx",
  "manifest_version": 2,
  "name": "Ignore X-Frame headers",
  "description": "Drops X-Frame-Options and Content-Security-Policy HTTP response headers, allowing all pages to be iframed.",
  "version": "1.1",
  "background": {
    "scripts": [
      "background.js"
    ]
  },
  "permissions": [
    "webRequest",
    "webRequestBlocking",
    "<all_urls>"
  ]
}
===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/e2e-tests/cypress/tests/fixtures/client_billing.json =====

{
    "mastercard":{
        "cardNumber":"5555555555554444",
        "expDate":"4242",
        "cvc":"412"
    },
    "visa":{
        "cardNumber":"4242424242424242",
        "expDate":"4242",
        "cvc":"412"
    },
    "unionpay":{
        "cardNumber":"6200000000000005",
        "expDate":"1244",
        "cvc":"123"
    },
    "invalidvisa":{
        "cardNumber":"4242424242424141",
        "expDate":"1212",
        "cvc":"12"
    }
}
===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/e2e-tests/cypress/tests/fixtures/console-example-inputs.json =====

[
    {
        "section": "about.license",
        "disabledInputs": [
            {
                "path": "/admin_console/about/license",
                "selector": "remove-button"
            }
        ]
    },
    {
        "section": "reporting.system_analytics",
        "disabledInputs": []
    },
    {
        "section": "reporting.team_statistics",
        "disabledInputs": []
    },
    {
        "section": "reporting.server_logs",
        "disabledInputs": []
    },
    {
        "section": "user_management.system_users",
        "disabledInputs": []
    },
    {
        "section": "user_management.groups",
        "disabledInputs": []
    },
    {
        "section": "user_management.teams",
        "disabledInputs": []
    },
    {
        "section": "user_management.channel",
        "disabledInputs": []
    },
    {
        "section": "user_management.permissions",
        "disabledInputs": []
    },
    {
        "section": "environment.web_server",
        "disabledInputs": [
            {
                "path": "/admin_console/environment/web_server",
                "selector": "ServiceSettings.ListenAddressinput"
            }
        ]
    },
    {
        "section": "site.customization",
        "disabledInputs": [
            {
                "path": "admin_console/site_config/customization",
                "selector": "TeamSettings.SiteNameinput"
            }
        ]
    },
    {
        "section": "site.localization",
        "disabledInputs": [
            {
                "path": "admin_console/site_config/localization",
                "selector": "LocalizationSettings.DefaultServerLocaledropdown"
            }
        ]
    },
    {
        "section": "site.users_and_teams",
        "disabledInputs": [
            {
                "path": "admin_console/site_config/users_and_teams",
                "selector": "TeamSettings.MaxUsersPerTeamnumber"
            }
        ]
    },
    {
        "section": "site.notifications",
        "disabledInputs": [
            {
                "path": "admin_console/environment/notifications",
                "selector": "TeamSettings.EnableConfirmNotificationsToChanneltrue"
            }
        ]
    },
    {
        "section": "site.announcement_banner",
        "disabledInputs": [
            {
                "path": "admin_console/site_config/announcement_banner",
                "selector": "AnnouncementSettings.EnableBannertrue"
            }
        ]
    },
    {
        "section": "site.emoji",
        "disabledInputs": [
            {
                "path": "admin_console/site_config/emoji",
                "selector": "ServiceSettings.EnableEmojiPickertrue"
            }
        ]
    },
    {
        "section": "site.posts",
        "disabledInputs": [
            {
                "path": "admin_console/site_config/posts",
                "selector": "ServiceSettings.EnableLinkPreviewstrue"
            }
        ]
    },
    {
        "section": "site.file_sharing_downloads",
        "disabledInputs": [
            {
                "path": "admin_console/site_config/file_sharing_downloads",
                "selector": "FileSettings.EnableFileAttachmentstrue"
            }
        ]
    },
    {
        "section": "site.public_links",
        "disabledInputs": [
            {
                "path": "admin_console/site_config/public_links",
                "selector": "FileSettings.EnablePublicLinktrue"
            }
        ]
    },
    {
        "section": "site.notices",
        "disabledInputs": [
            {
                "path": "admin_console/site_config/notices",
                "selector": "AnnouncementSettings.AdminNoticesEnabledtrue"
            }
        ]
    },
    {
        "section": "environment.database",
        "disabledInputs": [
            {
                "path": "/admin_console/environment/database",
                "selector": "maxIdleConnsinput"
            }
        ]
    },
    {
        "section": "environment.elasticsearch",
        "disabledInputs": [
            {
                "path": "/admin_console/environment/elasticsearch",
                "selector": "enableIndexingtrue"
            }
        ]
    },
    {
        "section": "environment.storage",
        "disabledInputs": [
            {
                "path": "/admin_console/environment/file_storage",
                "selector": "FileSettings.DriverNamedropdown"
            }
        ]
    },
    {
        "section": "environment.image_proxy",
        "disabledInputs": [
            {
                "path": "/admin_console/environment/image_proxy",
                "selector": "ImageProxySettings.Enabletrue"
            }
        ]
    },
    {
        "section": "environment.smtp",
        "disabledInputs": [

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/e2e-tests/cypress/tests/fixtures/hooks/message_menus.json =====

{
    "attachments": [{
        "pretext": "This is the attachment pretext.",
        "text": "This is the attachment text.",
        "actions": [{
            "name": "Select an option...",
            "integration": {
                "url": "http://localhost:3000/message_menus",
                "context": {
                    "action": "do_something"
                }
            },
            "type": "select",
            "options": [{
                "text": "Option 1",
                "value": "option1"
            }, {
                "text": "Option 2",
                "value": "option2"
            }, {
                "text": "Option 3",
                "value": "option3"
            }]
        }]
    }]
}

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/e2e-tests/cypress/tests/fixtures/hooks/message_menus_with_datasource.json =====

{
    "attachments": [{
        "pretext": "This is the attachment pretext.",
        "text": "This is the attachment text.",
        "actions": [{
            "name": "Select an option...",
            "integration": {
                "url": "http://localhost:3000/message_menus_datasource",
                "context": {
                    "action": "do_something"
                }
            },
            "type": "select",
            "data_source": "channels"
        }]
    }]
}

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/e2e-tests/cypress/tests/fixtures/interactive_message_menus_options.json =====

{
    "many-options": [ 
        {"text": "Afghanistan", "value": "AF"}, 
        {"text": "Åland Islands", "value": "AX"}, 
        {"text": "Albania", "value": "AL"}, 
        {"text": "Algeria", "value": "DZ"}, 
        {"text": "American Samoa", "value": "AS"}, 
        {"text": "AndorrA", "value": "AD"}, 
        {"text": "Angola", "value": "AO"}, 
        {"text": "Anguilla", "value": "AI"}, 
        {"text": "Antarctica", "value": "AQ"}, 
        {"text": "Antigua and Barbuda", "value": "AG"}, 
        {"text": "Argentina", "value": "AR"}, 
        {"text": "Armenia", "value": "AM"}, 
        {"text": "Aruba", "value": "AW"}, 
        {"text": "Australia", "value": "AU"}, 
        {"text": "Austria", "value": "AT"}, 
        {"text": "Azerbaijan", "value": "AZ"}, 
        {"text": "Bahamas", "value": "BS"}, 
        {"text": "Bahrain", "value": "BH"}, 
        {"text": "Bangladesh", "value": "BD"}, 
        {"text": "Barbados", "value": "BB"}, 
        {"text": "Belarus", "value": "BY"}, 
        {"text": "Belgium", "value": "BE"}, 
        {"text": "Belize", "value": "BZ"}, 
        {"text": "Benin", "value": "BJ"}, 
        {"text": "Bermuda", "value": "BM"}, 
        {"text": "Bhutan", "value": "BT"}, 
        {"text": "Bolivia", "value": "BO"}, 
        {"text": "Bosnia and Herzegovina", "value": "BA"}, 
        {"text": "Botswana", "value": "BW"}, 
        {"text": "Bouvet Island", "value": "BV"}, 
        {"text": "Brazil", "value": "BR"}, 
        {"text": "British Indian Ocean Territory", "value": "IO"}, 
        {"text": "Brunei Darussalam", "value": "BN"}, 
        {"text": "Bulgaria", "value": "BG"}, 
        {"text": "Burkina Faso", "value": "BF"}, 
        {"text": "Burundi", "value": "BI"}, 
        {"text": "Cambodia", "value": "KH"}, 
        {"text": "Cameroon", "value": "CM"}, 
        {"text": "Canada", "value": "CA"}, 
        {"text": "Cape Verde", "value": "CV"}, 
        {"text": "Cayman Islands", "value": "KY"}, 
        {"text": "Central African Republic", "value": "CF"}, 
        {"text": "Chad", "value": "TD"}, 
        {"text": "Chile", "value": "CL"}, 
        {"text": "China", "value": "CN"}, 
        {"text": "Christmas Island", "value": "CX"}, 
        {"text": "Cocos (Keeling) Islands", "value": "CC"}, 
        {"text": "Colombia", "value": "CO"}, 
        {"text": "Comoros", "value": "KM"}, 
        {"text": "Congo", "value": "CG"}, 
        {"text": "Congo, The Democratic Republic of the", "value": "CD"}, 
        {"text": "Cook Islands", "value": "CK"}, 
        {"text": "Costa Rica", "value": "CR"}, 
        {"text": "Cote D\"Ivoire", "value": "CI"}, 
        {"text": "Croatia", "value": "HR"}, 
        {"text": "Cuba", "value": "CU"}, 
        {"text": "Cyprus", "value": "CY"}, 
        {"text": "Czech Republic", "value": "CZ"}
    ],
    "distinct-options": [
        {"text": "Apple", "value": "apple"},
        {"text": "Orange", "value": "orange"},
        {"text": "Banana", "value": "banana"},
        {"text": "Grapes", "value": "grapes"},
        {"text": "Melon", "value": "melon"},
        {"text": "Mango", "value": "mango"},
        {"text": "Mango Raw", "value": "mangoraw"},
        {"text": "Avocado", "value": "avocado"}
    ]
}

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/e2e-tests/cypress/tests/fixtures/ldap_users.json =====

{
    "dev-1": {
        "username": "dev.one",
        "password": "Password1",
        "email": "success+devone@simulator.amazonses.com",
        "userType": "Admin"
    },
    "dev-2": {
        "username": "dev.two",
        "password": "Password1",
        "email": "success+devtwo@simulator.amazonses.com",
        "userType": "Admin"
    },
    "test-1": {
        "username": "test.one",
        "password": "Password1",
        "email": "success+testone@simulator.amazonses.com",
        "userType": ""
    },
    "test-2": {
        "username": "test.two",
        "password": "Password1",
        "email": "success+testtwo@simulator.amazonses.com",
        "userType": ""
    },
    "test-3": {
        "username": "test.three",
        "password": "Password1",
        "email": "success+testthree@simulator.amazonses.com",
        "userType": ""
    },
    "board-1": {
        "username": "board.one",
        "password": "Password1",
        "email": "success+boardone@simulator.amazonses.com",
        "userType": ""
    },
    "board-2": {
        "username": "board.two",
        "password": "Password1",
        "email": "success+boardtwo@simulator.amazonses.com",
        "userType": ""
    }
}

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/e2e-tests/cypress/tests/fixtures/long_text_post.txt =====

The quick, brown fox jumps over a lazy dog. DJs flock by when MTV ax quiz prog. Junk MTV quiz graced by fox whelps. Bawds jog, flick quartz, vex nymphs. Waltz, bad nymph, for quick jigs vex! Fox nymphs grab quick-jived waltz. Brick quiz whangs jumpy veldt fox. Bright vixens jump; dozy fowl quack. Quick wafting zephyrs vex bold Jim. Quick zephyrs blow, vexing daft Jim. Sex-charged fop blew my junk TV quiz. How quickly daft jumping zebras vex. Two driven jocks help fax my big quiz. Quick, Baz, get my woven flax jodhpurs! "Now fax quiz Jack!" my brave ghost pled. Five quacking zephyrs jolt my wax bed. Flummoxed by job, kvetching W. zaps Iraq. Cozy sphinx waves quart jug of bad milk. A very bad quack might jinx zippy fowls. Few quips galvanized the mock jury box. Quick brown dogs jump over the lazy fox. The jay, pig, fox, zebra, and my wolves quack! Blowzy red vixens fight for a quick jump. Joaquin Phoenix was gazed by MTV for luck. A wizard’s job is to vex chumps quickly in fog. Watch "Jeopardy!", Alex Trebek's fun TV quiz game. Woven silk pyjamas exchanged for blue quartz. Brawny gods just flocked up to quiz and vex him. Adjusting quiver and bow, Zompyc[1] killed the fox. My faxed joke won a pager in the cable TV quiz show. Amazingly few discotheques provide jukeboxes. My girl wove six dozen plaid jackets before she quit. Six big devils from Japan quickly forgot how to waltz. Big July earthquakes confound zany experimental vow. Foxy parsons quiz and cajole the lovably dim wiki-girl. Have a pick: twenty six letters - no forcing a jumbled quiz! Crazy Fredericka bought many very exquisite opal jewels. Sixty zippers were quickly picked from the woven jute bag. A quick movement of the enemy will jeopardize six gunboats. All questions asked by five watch experts amazed the judge. Jack quietly moved up front and seized the big ball of wax. The quick, brown fox jumps over a lazy dog. DJs flock by when MTV ax quiz prog. Junk MTV quiz graced by fox whelps. Bawds jog, flick quartz, vex nymphs. Waltz, bad nymph, for quick jigs vex! Fox nymphs grab quick-jived waltz. Brick quiz whangs jumpy veldt fox. Bright vixens jump; dozy fowl quack. Quick wafting zephyrs vex bold Jim. Quick zephyrs blow, vexing daft Jim. Sex-charged fop blew my junk TV quiz. How quickly daft jumping zebras vex. Two driven jocks help fax my big quiz. Quick, Baz, get my woven flax jodhpurs! "Now fax quiz Jack!" my brave ghost pled. Five quacking zephyrs jolt my wax bed. Flummoxed by job, kvetching W. zaps Iraq. Cozy sphinx waves quart jug of bad milk. A very bad quack might jinx zippy fowls. Few quips galvanized the mock jury box. Quick brown dogs jump over the lazy fox. The jay, pig, fox, zebra, and my wolves quack! Blowzy red vixens fight for a quick jump. Joaquin Phoenix was gazed by MTV for luck. A wizard’s job is to vex chumps quickly in fog. Watch "Jeopardy!", Alex Trebek's fun TV quiz game. Woven silk pyjamas exchanged for blue quartz. Brawny gods just flocked up to quiz and vex him. Adjusting quiver and bow, Zompyc[1] killed the fox. My faxed joke won a pager in the cable TV quiz show. Amazingly few discotheques provide jukeboxes. My girl wove six dozen plaid jackets before she quit. Six big devils from Japan quickly forgot how to waltz. Big July earthquakes confound zany experimental vow. Foxy parsons quiz and cajole the lovably dim wiki-girl. Have a pick: twenty six letters - no forcing a jumbled quiz! Crazy Fredericka bought many very exquisite opal jewels. Sixty zippers were quickly picked from the woven jute bag. A quick movement of the enemy will jeopardize six gunboats. All questions asked by five watch experts amazed the judge. Jack quietly moved up front and seized the big ball of wax. The quick, brown fox jumps over a lazy dog. DJs flock by when MTV ax quiz prog. Junk MTV quiz graced by fox whelps. Bawds jog, flick quartz, vex nymphs. Waltz, bad nymph, for quick jigs vex! Fox nymphs grab quick-jived waltz. Brick quiz whangs jumpy veldt fox. Hello this is a long post, with more than 4000 characters, plus multiple attachments.
The quick, brown fox jumps over a lazy dog. DJs flock by when MTV ax quiz prog. Junk MTV quiz graced by fox whelps. Bawds jog, flick quartz, vex nymphs. Waltz, bad nymph, for quick jigs vex! Fox nymphs grab quick-jived waltz. Brick quiz whangs jumpy veldt fox. Bright vixens jump; dozy fowl quack. Quick wafting zephyrs vex bold Jim. Quick zephyrs blow, vexing daft Jim. Sex-charged fop blew my junk TV quiz. How quickly daft jumping zebras vex. Two driven jocks help fax my big quiz. Quick, Baz, get my woven flax jodhpurs! "Now fax quiz Jack!" my brave ghost pled. Five quacking zephyrs jolt my wax bed. Flummoxed by job, kvetching W. zaps Iraq. Cozy sphinx waves quart jug of bad milk. A very bad quack might jinx zippy fowls. Few quips galvanized the mock jury box. Quick brown dogs jump over the lazy fox. The jay, pig, fox, zebra, and my wolves quack! Blowzy red vixens fight for a quick jump. Joaquin Phoenix was gazed by MTV for luck. A wizard’s job is to vex chumps quickly in fog. Watch "Jeopardy!", Alex Trebek's fun TV quiz game. Woven silk pyjamas exchanged for blue quartz. Brawny gods just flocked up to quiz and vex him. Adjusting quiver and bow, Zompyc[1] killed the fox. My faxed joke won a pager in the cable TV quiz show. Amazingly few discotheques provide jukeboxes. My girl wove six dozen plaid jackets before she quit. Six big devils from Japan quickly forgot how to waltz. Big July earthquakes confound zany experimental vow. Foxy parsons quiz and cajole the lovably dim wiki-girl. Have a pick: twenty six letters - no forcing a jumbled quiz! Crazy Fredericka bought many very exquisite opal jewels. Sixty zippers were quickly picked from the woven jute bag. A quick movement of the enemy will jeopardize six gunboats. All questions asked by five watch experts amazed the judge. Jack quietly moved up front and seized the big ball of wax. The quick, brown fox jumps over a lazy dog. DJs flock by when MTV ax quiz prog. Junk MTV quiz graced by fox whelps. Bawds jog, flick quartz, vex nymphs. Waltz, bad nymph, for quick jigs vex! Fox nymphs grab quick-jived waltz. Brick quiz whangs jumpy veldt fox. Bright vixens jump; dozy fowl quack. Quick wafting zephyrs vex bold Jim. Quick zephyrs blow, vexing daft Jim. Sex-charged fop blew my junk TV quiz. How quickly daft jumping zebras vex. Two driven jocks help fax my big quiz. Quick, Baz, get my woven flax jodhpurs! "Now fax quiz Jack!" my brave ghost pled. Five quacking zephyrs jolt my wax bed. Flummoxed by job, kvetching W. zaps Iraq. Cozy sphinx waves quart jug of bad milk. A very bad quack might jinx zippy fowls. Few quips galvanized the mock jury box. Quick brown dogs jump over the lazy fox. The jay, pig, fox, zebra, and my wolves quack! Blowzy red vixens fight for a quick jump. Joaquin Phoenix was gazed by MTV for luck. A wizard’s job is to vex chumps quickly in fog. Watch "Jeopardy!", Alex Trebek's fun TV quiz game. Woven silk pyjamas exchanged for blue quartz. Brawny gods just flocked up to quiz and vex him. Adjusting quiver and bow, Zompyc[1] killed the fox. My faxed joke won a pager in the cable TV quiz show. Amazingly few discotheques provide jukeboxes. My girl wove six dozen plaid jackets before she quit. Six big devils from Japan quickly forgot how to waltz. Big July earthquakes confound zany experimental vow. Foxy parsons quiz and cajole the lovably dim wiki-girl. Have a pick: twenty six letters - no forcing a jumbled quiz! Crazy Fredericka bought many very exquisite opal jewels. Sixty zippers were quickly picked from the woven jute bag. A quick movement of the enemy will jeopardize six gunboats. All questions asked by five watch experts amazed the judge. Jack quietly moved up front and seized the big ball of wax. The quick, brown fox jumps over a lazy dog. DJs flock by when MTV ax quiz prog. Junk MTV quiz graced by fox whelps. Bawds jog, flick quartz, vex nymphs. Waltz, bad nymph, for quick jigs vex! Fox nymphs grab quick-jived waltz. Brick quiz whangs jumpy veldt fox. Hello this is a long post, with more than 4000 characters, plus multiple attachments.
===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/e2e-tests/cypress/tests/fixtures/markdown/markdown_basic.md =====

# Basic Markdown Testing
Tests for text style, code blocks, in-line code and images, lines, block quotes, and headings.

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/e2e-tests/cypress/tests/fixtures/markdown/markdown_block_quotes_1.md =====

### Block Quotes

>This text should render in a block quote.

**The following text should render in two block quotes separated by one line of text:**
> Block quote 1

Text between block quotes

> Block quote 2

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/e2e-tests/cypress/tests/fixtures/markdown/markdown_block_quotes_2.md =====

### Block Quotes

**The following markdown should render within the block quote:**
> #### Heading 4
> _Italics_, *Italics*, **Bold**, ***Bold-italics***, **_Bold-italics_**, ~~Strikethrough~~
> :) :-) ;) :-O :bamboo: :gift_heart: :dolls:

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/e2e-tests/cypress/tests/fixtures/markdown/markdown_carriage_return.md =====

### Carriage Return

Line #1 followed by one blank line

Line #2 followed by one blank line

Line #3 followed by Line #4
Line #4

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/e2e-tests/cypress/tests/fixtures/markdown/markdown_carriage_return_two_lines.md =====

**The following should appear as a carriage return separating two lines of text:**
```
Line #1 followed by a blank line

Line #2 following a blank line
```

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/e2e-tests/cypress/tests/fixtures/markdown/markdown_code_block.md =====

### Code Blocks

```
This text should render in a code block
```

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/e2e-tests/cypress/tests/fixtures/markdown/markdown_escape_characters.md =====

### Escaped Characters

**The following text should render the same as the raw text:**
Raw: `\\teamlinux\IT-Stuff\WorkingStuff`
Markdown: \\teamlinux\IT-Stuff\WorkingStuff

**The following text should escape out the first backslash so only one backslash appears:**
Raw: `\\()#`
Markdown: \\()#

The end of this long post will be hidden until you choose to `Show More`.

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/e2e-tests/cypress/tests/fixtures/markdown/markdown_headings.md =====

### Headings

# Heading 1 font size
## Heading 2 font size
### Heading 3 font size
#### Heading 4 font size
##### Heading 5 font size
###### Heading 6 font size

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/mattermost/e2e-tests/cypress/tests/fixtures/markdown/markdown_inline_code.md =====

### In-line Code

The word `monospace` should render as in-line code.

The following markdown in-line code should not render:
`_Italics_`, `*Italics*`, `**Bold**`, `***Bold-italics***`, `**Bold-italics_**`, `~~Strikethrough~~`, `:)` , `:-)` , `;)` , `:-O` , `:bamboo:` , `:gift_heart:` , `:dolls:` , `# Heading 1`, `## Heading 2`, `### Heading 3`, `#### Heading 4`, `##### Heading 5`, `###### Heading 6`

This GIF link should not preview: `http://i.giphy.com/xNrM4cGJ8u3ao.gif`
This link should not auto-link: `https://en.wikipedia.org/wiki/Dolphin`

This sentence with `
in-line code
` should appear on one line.
