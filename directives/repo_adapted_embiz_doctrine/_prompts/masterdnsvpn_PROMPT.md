Read this local source bundle and create complete EMBIZ-specific operational doctrine.

Repository: masterdnsvpn
Local source: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/masterdnsvpn
Bundle: /root/embroidery_business_agent_system/directives/repo_adapted_embiz_doctrine/_prompts/masterdnsvpn_SOURCE_BUNDLE.md

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
# masterdnsvpn EMBIZ ADAPTED DOCTRINE
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


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/masterdnsvpn/cmd/client/versioninfo.json =====

{
    "FixedFileInfo": {
        "FileVersion": {
            "Major": 1,
            "Minor": 1,
            "Patch": 0,
            "Build": 0
        },
        "ProductVersion": {
            "Major": 1,
            "Minor": 1,
            "Patch": 0,
            "Build": 0
        },
        "FileFlagsMask": "3f",
        "FileFlags ": "00",
        "FileOS": "040004",
        "FileType": "01",
        "FileSubtype": "00"
    },
    "StringFileInfo": {
        "Comments": "MasterDnsVPN Client",
        "CompanyName": "MasterkinG32",
        "FileDescription": "MasterDnsVPN Client",
        "FileVersion": "1.1.0.0",
        "InternalName": "MasterDnsVPN_Client",
        "LegalCopyright": "Copyright (c) 2026 MasterkinG32",
        "LegalTrademarks": "",
        "OriginalFilename": "MasterDnsVPN_Client.exe",
        "ProductName": "MasterDnsVPN",
        "ProductVersion": "1.1.0.0"
    },
    "VarFileInfo": {
        "Translation": {
            "LangID": "0409",
            "CharsetID": "04B0"
        }
    },
    "IconPath": "../../assets/masterdnsvpn.ico"
}


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/masterdnsvpn/cmd/server/versioninfo.json =====

{
    "FixedFileInfo": {
        "FileVersion": {
            "Major": 1,
            "Minor": 0,
            "Patch": 0,
            "Build": 0
        },
        "ProductVersion": {
            "Major": 1,
            "Minor": 0,
            "Patch": 0,
            "Build": 0
        },
        "FileFlagsMask": "3f",
        "FileFlags ": "00",
        "FileOS": "040004",
        "FileType": "01",
        "FileSubtype": "00"
    },
    "StringFileInfo": {
        "Comments": "MasterDnsVPN Server",
        "CompanyName": "MasterkinG32",
        "FileDescription": "MasterDnsVPN Server",
        "FileVersion": "1.0.0.0",
        "InternalName": "MasterDnsVPN_Server",
        "LegalCopyright": "Copyright (c) 2026 MasterkinG32",
        "LegalTrademarks": "",
        "OriginalFilename": "MasterDnsVPN_Server.exe",
        "ProductName": "MasterDnsVPN",
        "ProductVersion": "1.0.0.0"
    },
    "VarFileInfo": {
        "Translation": {
            "LangID": "0409",
            "CharsetID": "04B0"
        }
    },
    "IconPath": "../../assets/masterdnsvpn.ico"
}


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/masterdnsvpn/.github/FUNDING.yml =====

# These are supported funding model platforms

github: masterking32


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/masterdnsvpn/.github/workflows/build-go.yml =====

name: Build and Release (Go)

on:
  workflow_dispatch: {}

permissions:
  contents: write
  packages: write

env:
  FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: "true"

jobs:
  preflight:
    name: Preflight - suggest secrets & generate tag
    runs-on: ubuntu-latest
    outputs:
      release_tag: ${{ steps.get_tag.outputs.tag }}
    steps:
      - name: Print recommended secrets and guidance
        run: |
          echo "Recommended repository secrets for this workflow:"
          echo " - GPG_SIGNING_KEY: (optional) ASCII-armored GPG private key for signing release artifacts"
          echo " - CODE_SIGN_CERT: (optional) Windows code-signing certificate (base64)"
          echo " - STORAGE_TOKEN: (optional) token for private artifact stores"
          echo
          echo "To add a secret: repository Settings → Secrets and variables → Actions → New repository secret"

      - name: Generate Release Tag
        id: get_tag
        run: |
          SHORT_SHA=$(echo ${GITHUB_SHA} | cut -c1-7)
          TS=$(date -u +%Y.%m.%d.%H%M%S)
          echo "tag=v${TS}-${SHORT_SHA}" >> "$GITHUB_OUTPUT"
          echo "Generated Tag: v${TS}-${SHORT_SHA}"

  build:
    name: Build (matrix)
    runs-on: ${{ matrix.os }}
    needs: preflight
    env:
      CODE_SIGN_CERT: ${{ secrets.CODE_SIGN_CERT }}
      CODE_SIGN_CERT_PASSWORD: ${{ secrets.CODE_SIGN_CERT_PASSWORD }}
    strategy:
      fail-fast: false
      matrix:
        include:
          - os: windows-latest
            platform: Windows
            arch: amd64
            ext: .exe
            package: zip
            go_arch: amd64
            go_os: windows
            cgo_enabled: "0"
            smoke_test: true
          - os: windows-latest
            platform: Windows
            arch: x86
            ext: .exe
            package: zip
            go_arch: 386
            go_os: windows
            cgo_enabled: "0"
            smoke_test: false
          - os: windows-latest
            platform: Windows
            arch: arm64
            ext: .exe
            package: zip
            go_arch: arm64
            go_os: windows
            cgo_enabled: "0"
            smoke_test: false
          - os: ubuntu-22.04
            platform: Linux
            arch: amd64
            ext: ""
            package: tar.gz
            go_arch: amd64
            go_os: linux
            cgo_enabled: "0"
            smoke_test: true
          - os: ubuntu-22.04
            platform: Linux
            arch: x86
            ext: ""
            package: tar.gz
            go_arch: 386
            go_os: linux
            cgo_enabled: "0"
            smoke_test: false
          - os: ubuntu-latest
            platform: Linux-Legacy
            arch: amd64
            ext: ""
            package: tar.gz
            go_arch: amd64
            go_os: linux
            cgo_enabled: "0"
            smoke_test: true
          - os: ubuntu-24.04-arm
            platform: Linux
            arch: arm64
            ext: ""
            package: tar.gz
            go_arch: arm64
            go_os: linux
            cgo_enabled: "0"
            smoke_test: true
          - os: ubuntu-24.04-arm
            platform: Linux-Legacy
            arch: arm64
            ext: ""
            package: tar.gz
            go_arch: arm64
            go_os: linux
            cgo_enabled: "0"
            smoke_test: false
          - os: ubuntu-22.04
            platform: Linux
            arch: armv7
            ext: ""
            package: tar.gz
            go_arch: arm
            go_arm: "7"
            go_os: linux
            cgo_enabled: "0"
            smoke_test: false
          - os: ubuntu-22.04
            platform: Linux
            arch: armv6
            ext: ""
            package: tar.gz
            go_arch: arm
            go_arm: "6"
            go_os: linux
            cgo_enabled: "0"
            smoke_test: false
          - os: ubuntu-22.04
            platform: Linux
            arch: armv5
            ext: ""
            package: tar.gz
            go_arch: arm
            go_arm: "5"
            go_os: linux
            cgo_enabled: "0"
            smoke_test: false
          - os: ubuntu-22.04
            platform: Linux
            arch: riscv64
            ext: ""
            package: tar.gz
            go_arch: riscv64
            go_os: linux
            cgo_enabled: "0"
            smoke_test: false
          - os: ubuntu-22.04
            platform: Linux
            arch: mips
            ext: ""
            package: tar.gz
            go_arch: mips
            go_os: linux
            go_mips: softfloat
            cgo_enabled: "0"
            smoke_test: false
          - os: ubuntu-22.04
            platform: Linux
            arch: mipsle
            ext: ""
            package: tar.gz
            go_arch: mipsle
            go_os: linux
            go_mips: softfloat
            cgo_enabled: "0"
            smoke_test: false
          - os: ubuntu-22.04
            platform: Linux


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/masterdnsvpn/.github/workflows/build-test.yml =====

name: Build Only (Test/Go)

on:
  workflow_dispatch: {}

permissions:
  contents: write

env:
  FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: "true"

jobs:
  preflight:
    name: Preflight - suggest secrets & generate tag
    runs-on: ubuntu-latest
    outputs:
      release_tag: ${{ steps.get_tag.outputs.tag }}
    steps:
      - name: Print recommended secrets and guidance
        run: |
          echo "Recommended repository secrets for this workflow:"
          echo " - GPG_SIGNING_KEY: (optional) ASCII-armored GPG private key for signing release artifacts"
          echo " - CODE_SIGN_CERT: (optional) Windows code-signing certificate (base64)"
          echo " - STORAGE_TOKEN: (optional) token for private artifact stores"
          echo
          echo "To add a secret: repository Settings → Secrets and variables → Actions → New repository secret"

      - name: Generate Release Tag
        id: get_tag
        run: |
          SHORT_SHA=$(echo ${GITHUB_SHA} | cut -c1-7)
          TS=$(date -u +%Y.%m.%d.%H%M%S)
          echo "tag=v${TS}-${SHORT_SHA}" >> "$GITHUB_OUTPUT"
          echo "Generated Tag: v${TS}-${SHORT_SHA}"

  build:
    name: Build (matrix)
    runs-on: ${{ matrix.os }}
    needs: preflight
    env:
      CODE_SIGN_CERT: ${{ secrets.CODE_SIGN_CERT }}
      CODE_SIGN_CERT_PASSWORD: ${{ secrets.CODE_SIGN_CERT_PASSWORD }}
    strategy:
      fail-fast: false
      matrix:
        include:
          - os: windows-latest
            platform: Windows
            arch: amd64
            ext: .exe
            package: zip
            go_arch: amd64
            go_os: windows
            cgo_enabled: "0"
            smoke_test: true
          - os: windows-latest
            platform: Windows
            arch: x86
            ext: .exe
            package: zip
            go_arch: 386
            go_os: windows
            cgo_enabled: "0"
            smoke_test: false
          - os: windows-latest
            platform: Windows
            arch: arm64
            ext: .exe
            package: zip
            go_arch: arm64
            go_os: windows
            cgo_enabled: "0"
            smoke_test: false
          - os: ubuntu-22.04
            platform: Linux
            arch: amd64
            ext: ""
            package: tar.gz
            go_arch: amd64
            go_os: linux
            cgo_enabled: "0"
            smoke_test: true
          - os: ubuntu-22.04
            platform: Linux
            arch: x86
            ext: ""
            package: tar.gz
            go_arch: 386
            go_os: linux
            cgo_enabled: "0"
            smoke_test: false
          - os: ubuntu-latest
            platform: Linux-Legacy
            arch: amd64
            ext: ""
            package: tar.gz
            go_arch: amd64
            go_os: linux
            cgo_enabled: "0"
            smoke_test: true
          - os: ubuntu-24.04-arm
            platform: Linux
            arch: arm64
            ext: ""
            package: tar.gz
            go_arch: arm64
            go_os: linux
            cgo_enabled: "0"
            smoke_test: true
          - os: ubuntu-24.04-arm
            platform: Linux-Legacy
            arch: arm64
            ext: ""
            package: tar.gz
            go_arch: arm64
            go_os: linux
            cgo_enabled: "0"
            smoke_test: false
          - os: ubuntu-22.04
            platform: Linux
            arch: armv7
            ext: ""
            package: tar.gz
            go_arch: arm
            go_arm: "7"
            go_os: linux
            cgo_enabled: "0"
            smoke_test: false
          - os: ubuntu-22.04
            platform: Linux
            arch: armv6
            ext: ""
            package: tar.gz
            go_arch: arm
            go_arm: "6"
            go_os: linux
            cgo_enabled: "0"
            smoke_test: false
          - os: ubuntu-22.04
            platform: Linux
            arch: armv5
            ext: ""
            package: tar.gz
            go_arch: arm
            go_arm: "5"
            go_os: linux
            cgo_enabled: "0"
            smoke_test: false
          - os: ubuntu-22.04
            platform: Linux
            arch: riscv64
            ext: ""
            package: tar.gz
            go_arch: riscv64
            go_os: linux
            cgo_enabled: "0"
            smoke_test: false
          - os: ubuntu-22.04
            platform: Linux
            arch: mips
            ext: ""
            package: tar.gz
            go_arch: mips
            go_os: linux
            go_mips: softfloat
            cgo_enabled: "0"
            smoke_test: false
          - os: ubuntu-22.04
            platform: Linux
            arch: mipsle
            ext: ""
            package: tar.gz
            go_arch: mipsle
            go_os: linux
            go_mips: softfloat
            cgo_enabled: "0"
            smoke_test: false
          - os: ubuntu-22.04
            platform: Linux
            arch: mips64


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/masterdnsvpn/.github/workflows/go-test.yml =====

name: Go Test

on:
  push:
  pull_request:

permissions:
  contents: read

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Go
        uses: actions/setup-go@v5
        with:
          go-version-file: go.mod
          cache: true

      - name: Run Tests
        run: go test ./...


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/masterdnsvpn/docker/docker-compose.yml =====

services:
  masterdnsvpn:
    image: ghcr.io/masterking32/masterdnsvpn:latest
    restart: unless-stopped
    environment:
      - DOMAIN=v.example.com
    volumes:
      - ./data:/data
    ports:
      - "53:53/tcp"
      - "53:53/udp"


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/masterdnsvpn/README.MD =====

﻿# MasterDnsVPN Project 🔐

## | 🇮🇷 [فارسی](https://github.com/masterking32/MasterDnsVPN/blob/main/README_FA.MD) | 🇬🇧 [English](https://github.com/masterking32/MasterDnsVPN/blob/main/README.MD) | 🇷🇺 [Русский](https://github.com/masterking32/MasterDnsVPN/blob/main/README_RU.MD) | 🇨🇳 [中文](https://github.com/masterking32/MasterDnsVPN/blob/main/README_ZH.MD) | 🇪🇸 [Español](https://github.com/masterking32/MasterDnsVPN/blob/main/README_ES.MD) | 🇮🇹 [Italiano](https://github.com/masterking32/MasterDnsVPN/blob/main/README_IT.MD) |

**MasterDnsVPN** is a scientific and research-oriented project for carrying TCP traffic through DNS queries and responses. In broad goal, it is similar to projects such as DNSTT or SlipStream, but it follows a fundamentally different structure and implementation approach.
This system is designed around compatibility with many resolver behaviors and harsh network conditions, with the goal of preserving the highest possible stability and data delivery even in the worst cases.

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/masterking32/MasterDnsVPN)
[![oosmetrics](https://api.oosmetrics.com/api/v1/badge/achievement/5c7b2ce0-0af6-4648-8ded-fd1e847096cd.svg)](https://oosmetrics.com/achievement/5c7b2ce0-0af6-4648-8ded-fd1e847096cd)
[![oosmetrics](https://api.oosmetrics.com/api/v1/badge/achievement/355e590f-9b4a-4015-bb8c-a7f27b721711.svg)](https://oosmetrics.com/achievement/355e590f-9b4a-4015-bb8c-a7f27b721711)
[![oosmetrics](https://api.oosmetrics.com/api/v1/badge/achievement/4b98a42e-bf63-4f55-a382-0f10359a5e20.svg)](https://oosmetrics.com/achievement/4b98a42e-bf63-4f55-a382-0f10359a5e20)

<a href="https://trendshift.io/repositories/23688" target="_blank"><img src="https://trendshift.io/api/badge/repositories/23688" alt="masterking32%2FMasterDnsVPN | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/></a>

### 📊 MasterDnsVPN Compared with Similar Projects

| Feature | SlipStream | DNSTT | MasterDnsVPN |
| :--- | :--- | :--- | :--- |
| Protocol type | Advanced DNS tunnel | Classic DNS tunnel | Advanced DNS tunnel / VPN |
| Transport protocol | QUIC | KCP + Noise | Custom protocol + ARQ |
| Transport header overhead | 🟠 ~24B | 🔴 ~59B | 🟢 ~5–7B<br>≈88% lower than DNSTT<br>≈71% lower than SlipStream |
| Encryption style | TLS 1.3 (inside QUIC) | Noise (Curve25519) | AES / ChaCha20 / XOR (if XOR is used: lightweight with lower security and no extra overhead) |
| Architecture | Unified (QUIC handles everything) | Multi-layered (KCP + SMUX + Noise) | 🟢 Lightweight custom design optimized for DNS |
| Speed | 🟡 High (up to ~5× faster than DNSTT) | 🔴 Medium | 🟢 Faster than others<br>Up to ~9× faster than DNSTT<br>Up to ~3.6× faster than SlipStream |
| Stability under packet loss | 🟡 Good | 🟠 Medium | 🟢 Very high (Multipath + ARQ) |
| Multi-resolver support | Yes (multipath) | ❌ | Yes — advanced (multi-resolver + duplication) |
| Resilience under heavy censorship | Good | Medium | Very strong (a core project goal) |
| Setup complexity | Medium | Simple | Easier installation<br>More complex only if you heavily customize advanced settings |
| SOCKS5 support | Yes | Yes | Optimized for SOCKS5 / SOCKS4 with reduced SOCKS overhead |
| Shadowsocks support | ✅ | ❌ | Indirectly: TCP Forwarding mode can carry TCP-based protocols<br>e.g. Shadowsocks, VLESS/VMess, etc. |
| Real multipath | Yes (QUIC multipath) | ❌ | Yes (multi-resolver + duplication) |
| Adaptive routing | Limited | ❌ | Advanced (latency/loss based) |
| Design goal | High speed and efficiency | Simplicity and stability | Surviving the harshest networks — stability, speed, and efficiency |
| Implementation language | Rust | Go | Main version is Go<br>Legacy Python version also exists |
| Built-in balancer | 🔴 | ❌ | 🟢 (8 built-in balancing modes) |
| Duplication system | ❌ | ❌ | Yes — increases traffic to improve reliability (configurable or can be disabled) |
| MTU tolerance | Better than DNSTT | - | Works even with very small MTU because protocol overhead is very low |
| Failover system | ❌ | ❌ | ✅ |
| Download speed 10MB (Local) | 🟡 0.978s | 🔴 2.492s | 🟢 0.270s |
| Upload speed 10MB (Local) | 🟡 3.249s | 🔴 16.207s | 🟢 1.746s |
| Resolver health checks and auto-disable | ❌ | ❌ | ✅ |
| Background reactivation of healthy resolvers | ❌ | ❌ | ✅ |
| Local DNS service on client (to reduce DNS hijacking) | ❌ | ❌ | ✅ (with strong DNS caching) |
| DNS resolving through SOCKS5 | ❌ | ❌ | ✅ (with DNS caching) |
| Fine-grained professional configuration | 🟠 | 🟠 | 🟢 Almost every subsystem is configurable |
| No external helper software required | ❌ | ❌ | 🟢 No extra software is required; if needed, you can still combine it with SOCKS or tools such as Shadowsocks or OpenVPN |

---

### ❌ Disclaimer

MasterDnsVPN is provided as an educational and research project only.

- **Provided without warranty:** This software is provided “AS-IS”, without any express or implied warranty, including merchantability, fitness for a particular purpose, or non-infringement.
- **Limitation of liability:** The developers and contributors of this project accept no responsibility for any direct, indirect, incidental, consequential, or other damages arising from the use of this software or the inability to use it.
- **User responsibility:** Using this project outside test environments may disrupt or damage network behavior. The user alone is responsible for all consequences of installation, configuration, and use.
- **Legal compliance:** Using this project to bypass local laws may result in civil or criminal consequences. Please review the laws and regulations of your country before use. The developers accept no responsibility for violations of local, national, or international laws by users.
- **License terms:** Use, copying, distribution, or modification of this software is governed by the license in the `LICENSE` file of this repository. Any use outside those terms is prohibited.

---

## Announcement and Support Channel 📢

For the latest news, releases, and project updates, follow our Telegram channel: [Telegram Channel](https://t.me/masterdnsvpn)

---

### If you like this project, please support it by starring it on GitHub (⭐). It helps the project get discovered.

---

### Optional Financial Support 💸

- TON network:

`masterking32.ton`

- EVM-compatible networks (ETH and compatible chains):

`0x517f07305D6ED781A089322B6cD93d1461bF8652`

- TRC20 network (TRON):

`TLApdY8APWkFHHoxebxGY8JhMeChiETqFH`

Every contribution and every piece of feedback is appreciated. Support directly helps ongoing development and improvement.

---

## Key Features and Advantages ✨

A brief overview of the main capabilities of MasterDnsVPN:

- **Censorship resistance and harsh-network survivability:** 🛡️ Designed to work on filtered networks, unstable links, and strict MTU environments.
- **Lightweight custom protocol:** 🔄 Uses a custom protocol with retransmission logic to reduce overhead and increase usable DNS payload.
- **Multipath and packet duplication:** 📡 Sends traffic through multiple paths and supports selective duplication to increase delivery probability on unstable networks.
- **Smart resolver selection and health checks:** ⚡ Selects resolvers based on quality and health, and manages problematic resolvers automatically.
- **MTU discovery and synchronization:** 🧰 Detects the practical MTU of working paths and aligns around it to reduce fragmentation and improve stability.
- **SOCKS5 / SOCKS4 support and optimization:** 🧦 Optimized local proxy handling for common applications.
- **Packed control blocks and lower control overhead:** 📦 Groups ACK/control traffic together to reduce control chatter.
- **Optional compression and request packing:** 🗜️ Reduces request counts and improves efficiency under small-MTU conditions.
- **Flexible encryption:** 🔐 Supports multiple encryption methods to balance speed and security.
- **Optional client-side local DNS and caching:** 📛 Can expose a local DNS service, reduce latency, and limit hijacking opportunities.
- **Scalable resource control:** ⚙️ Can run on small servers or be tuned for heavier loads.

This list is only a high-level summary. The related sections below explain each area in more detail.

---

## 🌐 Battle-Tested During a Total Internet Blackout

MasterDnsVPN isn't just a theoretical project. It is battle-tested and proven to work in environments where the global internet is completely severed.

Recently, during the 88-day internet blackout in Iran, authorities didn't just block VPNs or filter websites—they completely pulled the plug on international bandwidth. With 99% of the connection to the outside world physically cut off, users were trapped inside a closed, local intranet. 

Standard circumvention tools are useless when there is no international internet to connect to. Yet, during this massive shutdown, MasterDnsVPN stood out as one of the very few lifelines that actually kept users connected to the global web.

**How did it survive a total shutdown?**
Instead of acting like a standard VPN, MasterDnsVPN relies on smart DNS tunneling techniques to pierce through the blackout:
* **Multiple Resolvers:** It routes traffic through various DNS resolvers, ensuring the connection never relies on a single, easily blockable path.
* **Encryption & Data Splitting:** It encrypts your data and breaks it down into tiny, scattered pieces.
* **Disguised as Legitimate Traffic:** It wraps these data pieces inside standard, perfectly normal DNS queries.
* **Bypassing Local Traps:** Because the traffic looks exactly like basic, everyday DNS requests, firewalls allow it through. The data gets resolved and reaches the outside world—even if the network forces you to use their own restricted, government-controlled local resolvers.

This exact combination is what allowed MasterDnsVPN to maintain a stable connection when the outside world was completely blocked.

---

# Setup and Getting Started 🧑‍💻

## Section 1: 🖥️ Server Setup

### Section 1.1: 🌐 Domain Setup and Preparation (Prerequisite)

To receive DNS requests directly on your server, you must delegate a subdomain to it. In short, create two records: one `A` record that points to your server IP, and one `NS` record that delegates the tunnel subdomain to that A record.

#### Step 1.1.1: 🅰️ Create an A Record (Server Address)

- **Type:** `A`
- **Name:** a short name such as `ns`
- **Value:** your server IPv4 address

> Example: `ns.example.com -> 1.2.3.4`

> Cloudflare note: if the domain uses Cloudflare, open the `DNS` page and click the cloud icon next to the `A` record so it becomes gray (`DNS only`). It must not remain proxied.

#### Step 1.1.2: 🏷️ Create an NS Record (Delegate the Subdomain)

- **Type:** `NS`
- **Name:** the tunnel subdomain, for example `v`
- **Value / Target:** `ns.example.com`

> Example: `v.example.com -> ns.example.com`

> Cloudflare note: add the `NS` record normally. Cloudflare does not proxy NS records, but make sure the `ns` A record is already set to `DNS only`.

#### Section 1.1.3: 💡 A Short Note About MTU

Shorter domain names leave more space for actual data inside each DNS request. For better throughput, keep names short. If you use Cloudflare, still keep the relevant records in `DNS only` mode.

---

### Section 1.2: 🐧 Quick Linux Server Installation

#### Step 1.2.1: Automatic Installation (Script)

If you want to deploy the server on Linux, the easiest method is the automatic installer script. Run this command on the server:

```bash
bash <(curl -Ls https://raw.githubusercontent.com/masterking32/MasterDnsVPN/main/server_linux_install.sh)
```

The script handles installation and configuration automatically. When it finishes, the server starts and the **encryption key** is shown in the terminal log and also written to `encrypt_key.txt` next to the executable. Keep this key safe.

#### Step 1.2.2: Important Notes After Installation

- During installation, you will be asked for a domain. It must be the same delegated subdomain you configured in the `NS` record, for example `v.example.com`.
- After creating DNS records, wait for propagation. This may take from a few minutes to several hours, and in some cases up to 48 hours depending on TTL and the DNS provider.
- To verify the DNS setup, you can use tools such as `dig` or `nslookup`, for example `dig v.example.com NS` or `nslookup -type=ns v.example.com`. For a direct query to the new nameserver: `dig @ns.example.com v.example.com A`.
- If the server firewall is enabled, allow UDP port 53. Example for `ufw`:


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/masterdnsvpn/README_ES.MD =====

# MasterDnsVPN Project 🔐

## | 🇮🇷 [فارسی](https://github.com/masterking32/MasterDnsVPN/blob/main/README_FA.MD) | 🇬🇧 [English](https://github.com/masterking32/MasterDnsVPN/blob/main/README.MD) | 🇷🇺 [Русский](https://github.com/masterking32/MasterDnsVPN/blob/main/README_RU.MD) | 🇨🇳 [中文](https://github.com/masterking32/MasterDnsVPN/blob/main/README_ZH.MD) | 🇪🇸 [Español](https://github.com/masterking32/MasterDnsVPN/blob/main/README_ES.MD) | 🇮🇹 [Italiano](https://github.com/masterking32/MasterDnsVPN/blob/main/README_IT.MD) |

**MasterDnsVPN** es un proyecto científico y orientado a la investigación para transportar tráfico TCP a través de consultas y respuestas DNS. En su objetivo general, es similar a proyectos como DNSTT o SlipStream, pero sigue una estructura y un enfoque de implementación fundamentalmente diferentes.
Este sistema está diseñado en torno a la compatibilidad con muchos comportamientos de resolutores y condiciones de red adversas, con el objetivo de preservar la mayor estabilidad y entrega de datos posibles incluso en los peores casos.


[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/masterking32/MasterDnsVPN)
[![oosmetrics](https://api.oosmetrics.com/api/v1/badge/achievement/5c7b2ce0-0af6-4648-8ded-fd1e847096cd.svg)](https://oosmetrics.com/achievement/5c7b2ce0-0af6-4648-8ded-fd1e847096cd)
[![oosmetrics](https://api.oosmetrics.com/api/v1/badge/achievement/355e590f-9b4a-4015-bb8c-a7f27b721711.svg)](https://oosmetrics.com/achievement/355e590f-9b4a-4015-bb8c-a7f27b721711)
[![oosmetrics](https://api.oosmetrics.com/api/v1/badge/achievement/4b98a42e-bf63-4f55-a382-0f10359a5e20.svg)](https://oosmetrics.com/achievement/4b98a42e-bf63-4f55-a382-0f10359a5e20)

<a href="https://trendshift.io/repositories/23688" target="_blank"><img src="https://trendshift.io/api/badge/repositories/23688" alt="masterking32%2FMasterDnsVPN | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/></a>

### 📊 MasterDnsVPN Comparado con Proyectos Similares

| Característica | SlipStream | DNSTT | MasterDnsVPN |
| :--- | :--- | :--- | :--- |
| Tipo de protocolo | Túnel DNS avanzado | Túnel DNS clásico | Túnel DNS avanzado / VPN |
| Protocolo de transporte | QUIC | KCP + Noise | Protocolo personalizado + ARQ |
| Sobrecarga de cabecera de transporte | 🟠 ~24B | 🔴 ~59B | 🟢 ~5–7B<br>≈88% menor que DNSTT<br>≈71% menor que SlipStream |
| Estilo de cifrado | TLS 1.3 (dentro de QUIC) | Noise (Curve25519) | AES / ChaCha20 / XOR (si se usa XOR: ligero, con menor seguridad y sin sobrecarga adicional) |
| Arquitectura | Unificada (QUIC gestiona todo) | Multicapa (KCP + SMUX + Noise) | 🟢 Diseño personalizado y ligero optimizado para DNS |
| Velocidad | 🟡 Alta (hasta ~5× más rápida que DNSTT) | 🔴 Media | 🟢 Más rápida que las demás<br>Hasta ~9× más rápida que DNSTT<br>Hasta ~3,6× más rápida que SlipStream |
| Estabilidad ante pérdida de paquetes | 🟡 Buena | 🟠 Media | 🟢 Muy alta (Multipath + ARQ) |
| Soporte multirresolutor | Sí (multipath) | ❌ | Sí — avanzado (multirresolutor + duplicación) |
| Resiliencia ante censura intensa | Buena | Media | Muy fuerte (un objetivo central del proyecto) |
| Complejidad de configuración | Media | Simple | Instalación más sencilla<br>Más compleja solo si personalizas mucho los ajustes avanzados |
| Soporte SOCKS5 | Sí | Sí | Optimizado para SOCKS5 / SOCKS4 con menor sobrecarga de SOCKS |
| Soporte Shadowsocks | ✅ | ❌ | Indirectamente: el modo TCP Forwarding puede transportar protocolos basados en TCP<br>p. ej. Shadowsocks, VLESS/VMess, etc. |
| Multipath real | Sí (QUIC multipath) | ❌ | Sí (multirresolutor + duplicación) |
| Enrutamiento adaptativo | Limitado | ❌ | Avanzado (basado en latencia/pérdida) |
| Objetivo de diseño | Alta velocidad y eficiencia | Simplicidad y estabilidad | Sobrevivir a las redes más adversas — estabilidad, velocidad y eficiencia |
| Lenguaje de implementación | Rust | Go | La versión principal es Go<br>También existe una versión heredada en Python |
| Balanceador integrado | 🔴 | ❌ | 🟢 (8 modos de balanceo integrados) |
| Sistema de duplicación | ❌ | ❌ | Sí — aumenta el tráfico para mejorar la fiabilidad (configurable o desactivable) |
| Tolerancia de MTU | Mejor que DNSTT | - | Funciona incluso con MTU muy pequeña porque la sobrecarga del protocolo es muy baja |
| Sistema de failover | ❌ | ❌ | ✅ |
| Velocidad de descarga 10MB (Local) | 🟡 0,978s | 🔴 2,492s | 🟢 0,270s |
| Velocidad de subida 10MB (Local) | 🟡 3,249s | 🔴 16,207s | 🟢 1,746s |
| Comprobaciones de salud de resolutores y desactivación automática | ❌ | ❌ | ✅ |
| Reactivación en segundo plano de resolutores saludables | ❌ | ❌ | ✅ |
| Servicio DNS local en el cliente (para reducir el secuestro de DNS) | ❌ | ❌ | ✅ (con caché DNS robusta) |
| Resolución DNS a través de SOCKS5 | ❌ | ❌ | ✅ (con caché DNS) |
| Configuración profesional de grano fino | 🟠 | 🟠 | 🟢 Casi cada subsistema es configurable |
| No requiere software auxiliar externo | ❌ | ❌ | 🟢 No se requiere software adicional; si es necesario, aún puedes combinarlo con SOCKS o herramientas como Shadowsocks u OpenVPN |

---

### ❌ Descargo de responsabilidad

MasterDnsVPN se proporciona únicamente como un proyecto educativo y de investigación.

- **Proporcionado sin garantía:** Este software se proporciona "TAL CUAL", sin ninguna garantía expresa o implícita, incluidas las de comerciabilidad, idoneidad para un fin particular o no infracción.
- **Limitación de responsabilidad:** Los desarrolladores y colaboradores de este proyecto no aceptan ninguna responsabilidad por daños directos, indirectos, incidentales, consecuentes o de otro tipo derivados del uso de este software o de la imposibilidad de usarlo.
- **Responsabilidad del usuario:** Usar este proyecto fuera de entornos de prueba puede interrumpir o dañar el comportamiento de la red. El usuario es el único responsable de todas las consecuencias de la instalación, configuración y uso.
- **Cumplimiento legal:** Usar este proyecto para eludir las leyes locales puede acarrear consecuencias civiles o penales. Por favor, revisa las leyes y regulaciones de tu país antes de usarlo. Los desarrolladores no aceptan ninguna responsabilidad por las infracciones de leyes locales, nacionales o internacionales por parte de los usuarios.
- **Términos de la licencia:** El uso, copia, distribución o modificación de este software se rige por la licencia del archivo `LICENSE` de este repositorio. Cualquier uso fuera de esos términos está prohibido.

---

## Canal de Anuncios y Soporte 📢

Para conocer las últimas noticias, lanzamientos y novedades del proyecto, sigue nuestro canal de Telegram: [Canal de Telegram](https://t.me/masterdnsvpn)

---

### Si te gusta este proyecto, apóyalo dándole una estrella en GitHub (⭐). Ayuda a que el proyecto sea descubierto.

---

### Apoyo Económico Opcional 💸

- Red TON:

`masterking32.ton`

- Redes compatibles con EVM (ETH y cadenas compatibles):

`0x517f07305D6ED781A089322B6cD93d1461bF8652`

- Red TRC20 (TRON):

`TLApdY8APWkFHHoxebxGY8JhMeChiETqFH`

Toda contribución y todo comentario son apreciados. El apoyo ayuda directamente al desarrollo y la mejora continuos.

---

## Características y Ventajas Clave ✨

Una breve descripción de las principales capacidades de MasterDnsVPN:

- **Resistencia a la censura y supervivencia en redes adversas:** 🛡️ Diseñado para funcionar en redes filtradas, enlaces inestables y entornos con MTU estricta.
- **Protocolo personalizado ligero:** 🔄 Usa un protocolo personalizado con lógica de retransmisión para reducir la sobrecarga y aumentar la carga útil DNS aprovechable.
- **Multipath y duplicación de paquetes:** 📡 Envía tráfico a través de múltiples rutas y admite la duplicación selectiva para aumentar la probabilidad de entrega en redes inestables.
- **Selección inteligente de resolutores y comprobaciones de salud:** ⚡ Selecciona resolutores según su calidad y salud, y gestiona automáticamente los resolutores problemáticos.
- **Descubrimiento y sincronización de MTU:** 🧰 Detecta la MTU práctica de las rutas operativas y se alinea en torno a ella para reducir la fragmentación y mejorar la estabilidad.
- **Soporte y optimización de SOCKS5 / SOCKS4:** 🧦 Gestión optimizada del proxy local para aplicaciones comunes.
- **Bloques de control empaquetados y menor sobrecarga de control:** 📦 Agrupa el tráfico de ACK/control para reducir el parloteo de control.
- **Compresión opcional y empaquetado de solicitudes:** 🗜️ Reduce el número de solicitudes y mejora la eficiencia en condiciones de MTU pequeña.
- **Cifrado flexible:** 🔐 Admite múltiples métodos de cifrado para equilibrar velocidad y seguridad.
- **DNS local opcional del lado del cliente y caché:** 📛 Puede exponer un servicio DNS local, reducir la latencia y limitar las oportunidades de secuestro.
- **Control de recursos escalable:** ⚙️ Puede ejecutarse en servidores pequeños o ajustarse para cargas más pesadas.

Esta lista es solo un resumen de alto nivel. Las secciones relacionadas a continuación explican cada área con más detalle.

---

## 🌐 Probado en Combate Durante un Apagón Total de Internet

MasterDnsVPN no es solo un proyecto teórico. Está probado en combate y se ha demostrado que funciona en entornos donde internet global está completamente cortado.

Recientemente, durante el apagón de internet de 88 días en Irán, las autoridades no solo bloquearon VPN o filtraron sitios web, sino que cortaron por completo el ancho de banda internacional. Con el 99% de la conexión con el mundo exterior físicamente cortada, los usuarios quedaron atrapados dentro de una intranet local cerrada.

Las herramientas de elusión estándar son inútiles cuando no hay internet internacional al que conectarse. Sin embargo, durante este cierre masivo, MasterDnsVPN destacó como uno de los muy pocos salvavidas que realmente mantuvo a los usuarios conectados a la red global.

**¿Cómo sobrevivió a un apagón total?**
En lugar de actuar como una VPN estándar, MasterDnsVPN se basa en técnicas inteligentes de tunelización DNS para atravesar el apagón:
* **Múltiples resolutores:** Enruta el tráfico a través de varios resolutores DNS, asegurando que la conexión nunca dependa de una única ruta fácilmente bloqueable.
* **Cifrado y división de datos:** Cifra tus datos y los divide en fragmentos diminutos y dispersos.
* **Disfrazado como tráfico legítimo:** Envuelve estos fragmentos de datos dentro de consultas DNS estándar, perfectamente normales.
* **Eludiendo las trampas locales:** Como el tráfico se ve exactamente igual que las solicitudes DNS básicas y cotidianas, los firewalls lo dejan pasar. Los datos se resuelven y llegan al mundo exterior, incluso si la red te obliga a usar sus propios resolutores locales restringidos y controlados por el gobierno.

Esta combinación exacta es lo que permitió a MasterDnsVPN mantener una conexión estable cuando el mundo exterior estaba completamente bloqueado.

---

# Configuración e Inicio 🧑‍💻

## Sección 1: 🖥️ Configuración del Servidor

### Sección 1.1: 🌐 Configuración y Preparación del Dominio (Requisito previo)

Para recibir solicitudes DNS directamente en tu servidor, debes delegarle un subdominio. En resumen, crea dos registros: un registro `A` que apunte a la IP de tu servidor y un registro `NS` que delegue el subdominio del túnel a ese registro A.

#### Paso 1.1.1: 🅰️ Crear un registro A (Dirección del servidor)

- **Tipo:** `A`
- **Nombre:** un nombre corto como `ns`
- **Valor:** la dirección IPv4 de tu servidor

> Ejemplo: `ns.example.com -> 1.2.3.4`

> Nota sobre Cloudflare: si el dominio usa Cloudflare, abre la página `DNS` y haz clic en el icono de nube junto al registro `A` para que se vuelva gris (`DNS only`). No debe permanecer proxificado.

#### Paso 1.1.2: 🏷️ Crear un registro NS (Delegar el subdominio)

- **Tipo:** `NS`
- **Nombre:** el subdominio del túnel, por ejemplo `v`
- **Valor / Destino:** `ns.example.com`

> Ejemplo: `v.example.com -> ns.example.com`

> Nota sobre Cloudflare: añade el registro `NS` con normalidad. Cloudflare no proxifica los registros NS, pero asegúrate de que el registro A `ns` ya esté configurado como `DNS only`.

#### Sección 1.1.3: 💡 Una breve nota sobre la MTU

Los nombres de dominio más cortos dejan más espacio para datos reales dentro de cada solicitud DNS. Para mejor rendimiento, mantén los nombres cortos. Si usas Cloudflare, mantén igualmente los registros relevantes en modo `DNS only`.

---

### Sección 1.2: 🐧 Instalación Rápida del Servidor en Linux

#### Paso 1.2.1: Instalación automática (Script)

Si quieres desplegar el servidor en Linux, el método más fácil es el script de instalación automática. Ejecuta este comando en el servidor:

```bash
bash <(curl -Ls https://raw.githubusercontent.com/masterking32/MasterDnsVPN/main/server_linux_install.sh)
```

El script gestiona la instalación y configuración automáticamente. Cuando termina, el servidor se inicia y la **clave de cifrado** se muestra en el registro de la terminal y también se escribe en `encrypt_key.txt` junto al ejecutable. Guarda esta clave en un lugar seguro.

#### Paso 1.2.2: Notas importantes tras la instalación

- Durante la instalación, se te pedirá un dominio. Debe ser el mismo subdominio delegado que configuraste en el registro `NS`, por ejemplo `v.example.com`.
- Tras crear los registros DNS, espera a la propagación. Esto puede tardar de unos minutos a varias horas, y en algunos casos hasta 48 horas dependiendo del TTL y del proveedor de DNS.
- Para verificar la configuración DNS, puedes usar herramientas como `dig` o `nslookup`, por ejemplo `dig v.example.com NS` o `nslookup -type=ns v.example.com`. Para una consulta directa al nuevo servidor de nombres: `dig @ns.example.com v.example.com A`.


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/masterdnsvpn/README_FA.MD =====

# پروژه MasterDnsVPN 🔐

## | 🇮🇷 [فارسی](https://github.com/masterking32/MasterDnsVPN/blob/main/README_FA.MD) | 🇬🇧 [English](https://github.com/masterking32/MasterDnsVPN/blob/main/README.MD) | 🇷🇺 [Русский](https://github.com/masterking32/MasterDnsVPN/blob/main/README_RU.MD) | 🇨🇳 [中文](https://github.com/masterking32/MasterDnsVPN/blob/main/README_ZH.MD) | 🇪🇸 [Español](https://github.com/masterking32/MasterDnsVPN/blob/main/README_ES.MD) | 🇮🇹 [Italiano](https://github.com/masterking32/MasterDnsVPN/blob/main/README_IT.MD) |

پروژه **MasterDnsVPN** یک پروژهٔ علمی-تحقیقاتی برای انتقال داده‌های TCP از طریق درخواست‌ها و پاسخ‌های DNS است. این پروژه در هدف کلی شبیه پروژه‌هایی مانند DNSTT یا SlipStream است، اما از نظر ساختار و روش پیاده‌سازی تفاوت‌های بنیادین دارد و رویکرد متفاوتی را دنبال می‌کند.
پیاده‌سازی این سیستم بر پایهٔ سازگاری با انواع شبکه‌ها و رزولورها و نیز توانایی تحمل محدودیت‌های شدید طراحی شده است، تا در بدترین شرایط ممکن بالاترین میزان انتقال داده و بیشترین پایداری را فراهم کند.

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/masterking32/MasterDnsVPN)
[![oosmetrics](https://api.oosmetrics.com/api/v1/badge/achievement/5c7b2ce0-0af6-4648-8ded-fd1e847096cd.svg)](https://oosmetrics.com/achievement/5c7b2ce0-0af6-4648-8ded-fd1e847096cd)
[![oosmetrics](https://api.oosmetrics.com/api/v1/badge/achievement/355e590f-9b4a-4015-bb8c-a7f27b721711.svg)](https://oosmetrics.com/achievement/355e590f-9b4a-4015-bb8c-a7f27b721711)
[![oosmetrics](https://api.oosmetrics.com/api/v1/badge/achievement/4b98a42e-bf63-4f55-a382-0f10359a5e20.svg)](https://oosmetrics.com/achievement/4b98a42e-bf63-4f55-a382-0f10359a5e20)

<a href="https://trendshift.io/repositories/23688" target="_blank"><img src="https://trendshift.io/api/badge/repositories/23688" alt="masterking32%2FMasterDnsVPN | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/></a>

### 📊  مقایسه MasterDnsVPN با پروژه‌های مشابه:

| ویژگی | SlipStream | DNSTT | MasterDnsVPN |
| :--- | :--- | :--- | :--- |
| نوع پروتکل | DNS Tunnel پیشرفته | DNS Tunnel کلاسیک | DNS Tunnel / VPN پیشرفته |
| پروتکل انتقال | QUIC | KCP + Noise | پروتکل اختصاصی + ARQ |
| سربار هدرهای انتقالی | 🟠 ~24B | 🔴 ~59B | 🟢 ~5–7B<br>≈88% کمتر از DNSTT<br> ≈71% کمتر از SlipStream |
| نوع رمزنگاری | TLS 1.3 (در QUIC) | Noise (Curve25519) | AES / ChaCha20 / XOR (در صورت استفاده از XOR: امنیت نسبی ولی بدون سربار اضافی) |
| معماری | یکپارچه (QUIC همه‌چیز را پوشش می‌دهد) | چندلایه (KCP + SMUX + Noise) | 🟢 طراحی اختصاصی سبک، بهینه برای DNS |
| سرعت | 🟡 بالا (تا ~5× سریع‌تر از DNSTT) | 🔴 متوسط | 🟢 سریعتر از بقیه<br>تا ~9× سریعتر از DNSTT<br>تا ~3.6× سریعتر از SlipStream |
| پایداری در Packet Loss | 🟡 خوب | 🟠 متوسط | 🟢 بسیار بالا (Multipath + ARQ) |
| استفاده از چند DNS resolver | بله (multipath) | ❌ | بله — پیشرفته (multi-resolver + duplication) |
| تحمل سانسور شدید | خوب | متوسط | بسیار قوی (هدف اصلی پروژه) |
| پیچیدگی راه‌اندازی | متوسط | ساده | نصب و راه اندازی ساده تر<br>در صورت نیاز به شخصی سازی با توجه به تنظیمات گسترده، کمی پیچیده تر |
| پشتیبانی SOCKS5 | بله | بله | بهینه‌شده برای SOCKS5 / SOCKS4 و کاهش سربارهای ساکس |
| پشتیبانی Shadowsocks | ✅ | ❌ | غیرمستقیم: در حالت TCP Forwarding از پروتکل‌های TCP پشتیبانی می‌کند<br> نظیر:<br>Shadowsocks, Vless/Vmess و ... |
| Multipath واقعی | بله (QUIC multipath) | ❌ | بله (multi-resolver + duplication) |
| Adaptive routing | محدود | ❌ | پیشرفته (مبتنی بر latency/loss) |
| هدف طراحی | سرعت و کارایی بالا | سادگی و پایداری | عبور از محدودترین شبکه‌ها — پایداری، سرعت و کارایی |
| زبان پیاده‌سازی | Rust | Go | نسخه اصلی Go<br>اما نسخه قدیمی Python نیز موجود است |
| بالانسر داخلی | 🔴 | ❌ | 🟢 (8 نوع بالانسر داخلی) |
| سیستم Duplication | ❌ | ❌ | بله — افزایش ترافیک برای تضمین پایداری (قابل تنظیم یا غیرفعال سازی) |
| MTU قابل پشتیبانی | بهتر از DNSTT | - | سازگار حتی با MTU کم به دلیل سربار بسیار پایین پروتکل |
| سیستم Failover | ❌ | ❌ | ✅ |
| سرعت دانلود 10 مگابایت در حالت لوکال | 🟡 0.978 ثانیه | 🔴 2.492 ثانیه | 🟢 0.270 ثانیه |
| سرعت آپلود 10 مگابایت در حالت لوکال | 🟡 3.249 ثانیه | 🔴 16.207 ثانیه  | 🟢 1.746 ثانیه |
| قابلیت فشرده سازی | ❌ | ❌ | 🟢<br> به سه روش مختلف قابل تنظیم<br>Off, ZSTD, LZ4, ZLIB |
| بررسی سلامت رزولورها و غیرفعال‌سازی خودکار | ❌ | ❌ | ✅ |
| بازفعال‌سازی رزولورها در صورت دسترسی دوباره (پس‌زمینه) | ❌ | ❌ | ✅ |
| ارائه DNS محلی در کلاینت (جلوگیری از DNS Hijacking) | ❌ | ❌ | ✅ (با DNS Caching حرفه‌ای برای کاهش درخواست‌ها) |
| قابلیت DNS resolving از طریق SOCKS5 | ❌ | ❌ | ✅ (با DNS Caching) |
| امکان پیکربندی حرفه‌ای و دلخواه | 🟠 | 🟠 | 🟢 امکان پیکربندی دقیق تمام بخش‌ها |
| بی‌نیاز از نرم‌افزارهای جانبی | ❌ | ❌ | 🟢 نیازی به نصب نرم‌افزار جانبی نیست؛ در صورت نیاز می‌توانید از SOCKS یا ابزارهای خارجی مانند Shadowsocks یا OpenVPN استفاده کنید. |

---

### ❌ رفع مسئولیت (Disclaimer):
پروژه MasterDnsVPN صرفاً یک ایدهٔ علمی و آموزشی است و بر همین اساس طراحی و پیاده‌سازی شده است.

- **ارائه بدون ضمانت:** این نرم‌افزار «همان‌طور که هست» (AS-IS) و بدون هیچ‌گونه ضمانت صریح یا ضمنی، از جمله ضمانت قابلیت فروش، مناسب‌بودن برای هدف خاص یا عدم نقض حقوق، ارائه می‌شود.
- **محدودیت مسئولیت:** توسعه‌دهندگان و مشارکت‌کنندگان این پروژه هیچ‌گونه مسئولیتی در قبال خسارات مستقیم، غیرمستقیم، تبعی، اتفاقی یا هر نوع خسارت دیگری ناشی از استفاده یا ناتوانی در استفاده از این نرم‌افزار نمی‌پذیرند.
- **مسئولیت کاربر:** استفاده از این پروژه در محیط‌های غیرآزمایشگاهی ممکن است به ساختار شبکه آسیب برساند. کاربر به‌تنهایی مسئول هرگونه پیامد ناشی از نصب، پیکربندی و استفاده از این نرم‌افزار است.
- **رعایت قوانین:** استفاده از این پروژه برای دور زدن قوانین کشورها می‌تواند با مسئولیت‌های مدنی و کیفری همراه باشد. لطفاً پیش از استفاده، قوانین و مقررات کشور خود را در این زمینه به‌دقت بررسی کنید. توسعه‌دهندگان هیچ مسئولیتی در قبال نقض قوانین محلی، ملی یا بین‌المللی توسط کاربران نمی‌پذیرند.
- **مجوز استفاده:** استفاده، کپی، توزیع یا تغییر این نرم‌افزار مشمول شرایط مجوز مندرج در فایل `LICENSE` این مخزن است. هرگونه استفاده خارج از چارچوب آن مجوز ممنوع است.

---

## کانال اطلاع‌رسانی و پشتیبانی 📢

برای دریافت آخرین اخبار، نسخه‌ها و اطلاعیه‌های پروژه، کانال تلگرام ما را دنبال کنید: [Telegram Channel](https://t.me/masterdnsvpn)

---

### اگر از پروژه راضی‌اید، با دادن ستاره (⭐) در گیت‌هاب از ما حمایت کنید — این کار به دیده‌شدن پروژه کمک می‌کند.

---

### حمایت مالی (اختیاری) 💸

- شبکه TON:

`masterking32.ton`

- آدرس روی شبکه‌های EVM (ETH و سازگارها): 

`0x517f07305D6ED781A089322B6cD93d1461bF8652`

- شبکه TRC20 (TRON):

`TLApdY8APWkFHHoxebxGY8JhMeChiETqFH`

از هر نوع حمایت و بازخورد شما سپاسگزاریم — کمک‌ها برای توسعه و بهبود پروژه بسیار ارزشمند است.

---

## ویژگی‌های کلیدی و مزایا ✨

نمای کلی و مختصر از قابلیت‌های اصلی MasterDnsVPN:

- **عبور از سانسور و تحمل شرایط سخت شبکه:** 🛡️ طراحی‌شده برای کار در شبکه‌های دارای فیلترینگ، قطعی و محدودیت MTU.
- **پروتکل سبک و کم‌سربار:** 🔄 پروتکل اختصاصی با مکانیزم ارسال مجدد برای کاهش سربار و افزایش ظرفیت داده در DNS.
- **قابلیت Multipath و تکثیر بسته‌ها:** 📡 ارسال همزمان از مسیرهای مختلف و تکثیر انتخابی برای افزایش شانس تحویل در شبکه‌های ناپایدار.
- **انتخاب هوشمند رزولورها و بررسی سلامت:** ⚡ انتخاب بر اساس کیفیت و وضعیت رزولورها و مدیریت خودکار رزولورهای مشکل‌دار.
- **کشف و همگام‌سازی MTU:** 🧰 تشخیص MTU عملیاتی مسیرها و تنظیم برای کاهش fragmentation و افزایش پایداری.
- **پشتیبانی و بهینه‌سازی SOCKS5/SOCKS4:** 🧦 مسیردهی و پردازش بهینه ترافیک پراکسی محلی برای برنامه‌ها.
- **تجمیع کنترل‌ها و کاهش سربار پاسخ‌ها:** 📦 جمع‌آوری ACK و پیام‌های کنترلی در یک پکت برای کاهش ترافیک کنترل.
- **فشرده‌سازی و تجمیع درخواست‌ها (اختیاری):** 🗜️ کاهش تعداد درخواست‌ها و افزایش بهره‌وری در شرایط MTU کوچک.
- **رمزنگاری انعطاف‌پذیر:** 🔐 پشتیبانی از چند الگوریتم رمزنگاری برای متعادل‌سازی سرعت و امنیت.
- **قابلیت DNS محلی و کشینگ در کلاینت:** 📛 ارائه DNS محلی، کاهش تأخیر و جلوگیری از حملات hijack.
- **مقیاس‌پذیری و کنترل منابع:** ⚙️ قابل اجرا از سرورهای کم‌منابع تا محیط‌های با بار زیاد.

این فهرست نمای کلی و مختصری از قابلیت‌هاست؛ برای جزئیات بیشتر به بخش‌های مرتبط در همین سند مراجعه کنید.

---

# راه‌اندازی و شروع بکار 🧑‍💻


## بخش ۱: 🖥️ راه‌اندازی سرور

### بخش ۱.۱: 🌐 راه‌اندازی و آماده‌سازی دامنه (پیش‌نیاز) 

برای دریافت مستقیم درخواست‌های DNS روی سرور باید یک زیردامنه را به سرورتان واگذار (delegate) کنید. به‌صورت خلاصه دو رکورد بسازید: یک رکورد `A` برای آدرس سرور و یک رکورد `NS` که زیردامنه را به آن A ارجاع دهد.

#### گام ۱.۱.۱: 🅰️ ساخت رکورد A (آدرس سرور) 

- **نوع:** `A`
- **نام:** نام کوتاه مثل `ns`
- **مقدار:** آدرس IPv4 سرور شما

> مثال: `ns.example.com -> 1.2.3.4`

> در Cloudflare - ⚠️ نکته سریع: اگر دامنه روی Cloudflare است، در صفحه `DNS` روی آیکون ابر کنار رکورد `A` کلیک کنید تا خاکستری (DNS only) شود؛ نباید Proxied (نارنجی) باشد.

#### گام ۱.۱.۲: 🏷️ ساخت رکورد NS (واگذاری زیردامنه)

- **نوع:** `NS`
- **نام:** زیردامنه‌ی تونل مثل `v`
- **مقدار (Target):** `ns.example.com`

> مثال: `v.example.com -> ns.example.com`

> در Cloudflare - ⚠️ نکته سریع: رکورد `NS` را اضافه کنید؛ Cloudflare رکورد NS را پروکسی نمی‌کند، فقط مطمئن شوید رکورد `ns` قبلاً روی DNS only قرار دارد.

#### بخش ۱.۱.۳: 💡 نکتهٔ کوتاه دربارهٔ MTU

هر چه نام‌های دامنه کوتاه‌تر باشند، فضای بیشتری برای داده در هر DNS request باقی می‌ماند. برای throughput بهتر از نام‌های کوتاه استفاده کنید. اگر از Cloudflare استفاده می‌کنید، باز هم رکوردها را DNS only نگه دارید.

---

### بخش ۱.۲: 🐧 نصب سریع سرور لینوکس

#### گام ۱.۲.۱: نصب خودکار (اسکریپت)

اگر قصد دارید سرور را روی یک سیستم لینوکسی راه‌اندازی کنید، ساده‌ترین راه استفاده از اسکریپت نصب خودکار است. کافی است دستور زیر را در ترمینال سرور وارد کنید:

```bash
bash <(curl -Ls https://raw.githubusercontent.com/masterking32/MasterDnsVPN/main/server_linux_install.sh)
```

این اسکریپت مراحل نصب و پیکربندی را خودکار انجام می‌دهد. بعد از پایان نصب، سرور اجرا می‌شود و **کلید رمزنگاری** در لاگ ترمینال نمایش داده می‌شود و همچنین در فایل `encrypt_key.txt` کنار فایل اجرایی ذخیره می‌گردد — این کلید را در جای امن نگه دارید.

#### گام ۱.۲.۲: نکات مهم پس از نصب

- در هنگام نصب از شما آدرس دامنه پرسیده می‌شود؛ باید همان زیردامنه‌ای باشد که در رکورد `NS` تنظیم کرده‌اید (مثلاً `v.example.com`).
- پس از ایجاد رکوردهای DNS، تا انتشار آن‌ها صبر کنید (ممکن است از چند دقیقه تا چند ساعت یا در موارد خاص تا 48 ساعت طول بکشد؛ بسته به TTL).
- برای بررسی صحت تنظیمات DNS می‌توانید از ابزارهایی مانند `dig` یا `nslookup` استفاده کنید (مثلاً `dig v.example.com NS` یا `nslookup -type=ns v.example.com`). برای پرس‌وجو مستقیم از nameserver جدید: `dig @ns.example.com v.example.com A`.
- اگر فایروال سرور فعال است، اجازه‌ی عبور UDP پورت 53 را بدهید. نمونه برای `ufw`:

```bash
sudo ufw allow 53/udp
sudo ufw reload
```

برای `firewalld`:

```bash
sudo firewall-cmd --add-port=53/udp --permanent
sudo firewall-cmd --reload
```

- اگر پورت `53` توسط سرویس دیگری اشغال شده باشد (مثلاً `systemd-resolved` در برخی توزیع‌ها)، راه‌حل را در بخش «رفع مشکل اشغال بودن پورت ۵۳» ببینید.
- کلید رمزنگاری (`encrypt_key.txt`) پس از نصب نمایش داده می‌شود؛ آن را کپی و امن نگه دارید، زیرا برای اتصال کلاینت لازم است.

---



===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/masterdnsvpn/README_IT.MD =====

# MasterDnsVPN Project 🔐

## | 🇮🇷 [فارسی](https://github.com/masterking32/MasterDnsVPN/blob/main/README_FA.MD) | 🇬🇧 [English](https://github.com/masterking32/MasterDnsVPN/blob/main/README.MD) | 🇷🇺 [Русский](https://github.com/masterking32/MasterDnsVPN/blob/main/README_RU.MD) | 🇨🇳 [中文](https://github.com/masterking32/MasterDnsVPN/blob/main/README_ZH.MD) | 🇪🇸 [Español](https://github.com/masterking32/MasterDnsVPN/blob/main/README_ES.MD) | 🇮🇹 [Italiano](https://github.com/masterking32/MasterDnsVPN/blob/main/README_IT.MD) |

**MasterDnsVPN** è un progetto a carattere scientifico e di ricerca per trasportare traffico TCP attraverso query e risposte DNS. Nell'obiettivo generale, è simile a progetti come DNSTT o SlipStream, ma segue una struttura e un approccio implementativo fondamentalmente diversi.
Questo sistema è progettato attorno alla compatibilità con molti comportamenti dei resolver e con condizioni di rete avverse, con l'obiettivo di preservare la massima stabilità possibile e la consegna dei dati anche nei casi peggiori.


[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/masterking32/MasterDnsVPN)
[![oosmetrics](https://api.oosmetrics.com/api/v1/badge/achievement/5c7b2ce0-0af6-4648-8ded-fd1e847096cd.svg)](https://oosmetrics.com/achievement/5c7b2ce0-0af6-4648-8ded-fd1e847096cd)
[![oosmetrics](https://api.oosmetrics.com/api/v1/badge/achievement/355e590f-9b4a-4015-bb8c-a7f27b721711.svg)](https://oosmetrics.com/achievement/355e590f-9b4a-4015-bb8c-a7f27b721711)
[![oosmetrics](https://api.oosmetrics.com/api/v1/badge/achievement/4b98a42e-bf63-4f55-a382-0f10359a5e20.svg)](https://oosmetrics.com/achievement/4b98a42e-bf63-4f55-a382-0f10359a5e20)

<a href="https://trendshift.io/repositories/23688" target="_blank"><img src="https://trendshift.io/api/badge/repositories/23688" alt="masterking32%2FMasterDnsVPN | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/></a>

### 📊 MasterDnsVPN a Confronto con Progetti Simili

| Caratteristica | SlipStream | DNSTT | MasterDnsVPN |
| :--- | :--- | :--- | :--- |
| Tipo di protocollo | Tunnel DNS avanzato | Tunnel DNS classico | Tunnel DNS avanzato / VPN |
| Protocollo di trasporto | QUIC | KCP + Noise | Protocollo personalizzato + ARQ |
| Overhead dell'header di trasporto | 🟠 ~24B | 🔴 ~59B | 🟢 ~5–7B<br>≈88% inferiore a DNSTT<br>≈71% inferiore a SlipStream |
| Tipo di cifratura | TLS 1.3 (all'interno di QUIC) | Noise (Curve25519) | AES / ChaCha20 / XOR (se si usa XOR: leggero con sicurezza inferiore e senza overhead aggiuntivo) |
| Architettura | Unificata (QUIC gestisce tutto) | A più livelli (KCP + SMUX + Noise) | 🟢 Design personalizzato leggero ottimizzato per DNS |
| Velocità | 🟡 Alta (fino a ~5× più veloce di DNSTT) | 🔴 Media | 🟢 Più veloce degli altri<br>Fino a ~9× più veloce di DNSTT<br>Fino a ~3,6× più veloce di SlipStream |
| Stabilità in caso di perdita di pacchetti | 🟡 Buona | 🟠 Media | 🟢 Molto alta (Multipath + ARQ) |
| Supporto multi-resolver | Sì (multipath) | ❌ | Sì — avanzato (multi-resolver + duplicazione) |
| Resilienza sotto forte censura | Buona | Media | Molto forte (un obiettivo centrale del progetto) |
| Complessità di configurazione | Media | Semplice | Installazione più facile<br>Più complessa solo se si personalizzano pesantemente le impostazioni avanzate |
| Supporto SOCKS5 | Sì | Sì | Ottimizzato per SOCKS5 / SOCKS4 con overhead SOCKS ridotto |
| Supporto Shadowsocks | ✅ | ❌ | Indirettamente: la modalità TCP Forwarding può trasportare protocolli basati su TCP<br>ad es. Shadowsocks, VLESS/VMess, ecc. |
| Multipath reale | Sì (multipath QUIC) | ❌ | Sì (multi-resolver + duplicazione) |
| Routing adattivo | Limitato | ❌ | Avanzato (basato su latenza/perdita) |
| Obiettivo di progettazione | Alta velocità ed efficienza | Semplicità e stabilità | Sopravvivere alle reti più ostili — stabilità, velocità ed efficienza |
| Linguaggio di implementazione | Rust | Go | La versione principale è in Go<br>Esiste anche una versione Python legacy |
| Bilanciatore integrato | 🔴 | ❌ | 🟢 (8 modalità di bilanciamento integrate) |
| Sistema di duplicazione | ❌ | ❌ | Sì — aumenta il traffico per migliorare l'affidabilità (configurabile o disattivabile) |
| Tolleranza all'MTU | Migliore di DNSTT | - | Funziona anche con MTU molto piccolo perché l'overhead del protocollo è molto basso |
| Sistema di failover | ❌ | ❌ | ✅ |
| Velocità di download 10MB (Locale) | 🟡 0,978s | 🔴 2,492s | 🟢 0,270s |
| Velocità di upload 10MB (Locale) | 🟡 3,249s | 🔴 16,207s | 🟢 1,746s |
| Controlli di salute dei resolver e disattivazione automatica | ❌ | ❌ | ✅ |
| Riattivazione in background dei resolver sani | ❌ | ❌ | ✅ |
| Servizio DNS locale sul client (per ridurre il DNS hijacking) | ❌ | ❌ | ✅ (con potente caching DNS) |
| Risoluzione DNS tramite SOCKS5 | ❌ | ❌ | ✅ (con caching DNS) |
| Configurazione professionale di precisione | 🟠 | 🟠 | 🟢 Quasi ogni sottosistema è configurabile |
| Nessun software ausiliario esterno richiesto | ❌ | ❌ | 🟢 Non è richiesto alcun software aggiuntivo; se necessario, è comunque possibile combinarlo con SOCKS o strumenti come Shadowsocks o OpenVPN |

---

### ❌ Disclaimer

MasterDnsVPN è fornito esclusivamente come progetto educativo e di ricerca.

- **Fornito senza garanzia:** Questo software è fornito "COSÌ COM'È", senza alcuna garanzia espressa o implicita, inclusa la commerciabilità, l'idoneità per uno scopo particolare o la non violazione di diritti.
- **Limitazione di responsabilità:** Gli sviluppatori e i collaboratori di questo progetto non si assumono alcuna responsabilità per eventuali danni diretti, indiretti, incidentali, consequenziali o di altro tipo derivanti dall'uso di questo software o dall'impossibilità di utilizzarlo.
- **Responsabilità dell'utente:** L'utilizzo di questo progetto al di fuori di ambienti di test può alterare o danneggiare il comportamento della rete. L'utente è l'unico responsabile di tutte le conseguenze derivanti dall'installazione, dalla configurazione e dall'uso.
- **Conformità legale:** L'utilizzo di questo progetto per aggirare le leggi locali può comportare conseguenze civili o penali. Si prega di esaminare le leggi e i regolamenti del proprio Paese prima dell'uso. Gli sviluppatori non si assumono alcuna responsabilità per violazioni di leggi locali, nazionali o internazionali da parte degli utenti.
- **Termini di licenza:** L'uso, la copia, la distribuzione o la modifica di questo software sono regolati dalla licenza presente nel file `LICENSE` di questo repository. Qualsiasi uso al di fuori di tali termini è proibito.

---

## Canale di Annunci e Supporto 📢

Per le ultime notizie, i rilasci e gli aggiornamenti del progetto, segui il nostro canale Telegram: [Canale Telegram](https://t.me/masterdnsvpn)

---

### Se ti piace questo progetto, supportalo mettendo una stella su GitHub (⭐). Aiuta il progetto a farsi conoscere.

---

### Supporto Economico Facoltativo 💸

- Rete TON:

`masterking32.ton`

- Reti compatibili EVM (ETH e chain compatibili):

`0x517f07305D6ED781A089322B6cD93d1461bF8652`

- Rete TRC20 (TRON):

`TLApdY8APWkFHHoxebxGY8JhMeChiETqFH`

Ogni contributo e ogni feedback è apprezzato. Il supporto aiuta direttamente lo sviluppo e il miglioramento continui.

---

## Caratteristiche e Vantaggi Principali ✨

Una breve panoramica delle principali capacità di MasterDnsVPN:

- **Resistenza alla censura e sopravvivenza in reti ostili:** 🛡️ Progettato per funzionare su reti filtrate, collegamenti instabili e ambienti con MTU rigorosi.
- **Protocollo personalizzato leggero:** 🔄 Utilizza un protocollo personalizzato con logica di ritrasmissione per ridurre l'overhead e aumentare il payload DNS utilizzabile.
- **Multipath e duplicazione dei pacchetti:** 📡 Invia il traffico attraverso percorsi multipli e supporta la duplicazione selettiva per aumentare la probabilità di consegna su reti instabili.
- **Selezione intelligente dei resolver e controlli di salute:** ⚡ Seleziona i resolver in base a qualità e salute, e gestisce automaticamente i resolver problematici.
- **Rilevamento e sincronizzazione dell'MTU:** 🧰 Rileva l'MTU pratico dei percorsi funzionanti e si allinea ad esso per ridurre la frammentazione e migliorare la stabilità.
- **Supporto e ottimizzazione SOCKS5 / SOCKS4:** 🧦 Gestione ottimizzata del proxy locale per le applicazioni più comuni.
- **Blocchi di controllo impacchettati e minore overhead di controllo:** 📦 Raggruppa il traffico ACK/di controllo per ridurre il chiacchiericcio di controllo.
- **Compressione e impacchettamento delle richieste facoltativi:** 🗜️ Riduce il numero di richieste e migliora l'efficienza in condizioni di MTU ridotto.
- **Cifratura flessibile:** 🔐 Supporta diversi metodi di cifratura per bilanciare velocità e sicurezza.
- **DNS locale lato client e caching facoltativi:** 📛 Può esporre un servizio DNS locale, ridurre la latenza e limitare le opportunità di hijacking.
- **Controllo scalabile delle risorse:** ⚙️ Può funzionare su piccoli server o essere ottimizzato per carichi più pesanti.

Questo elenco è solo un riepilogo ad alto livello. Le sezioni correlate qui sotto spiegano ciascuna area in maggior dettaglio.

---

## 🌐 Collaudato Durante un Totale Blackout di Internet

MasterDnsVPN non è solo un progetto teorico. È collaudato sul campo e ha dimostrato di funzionare in ambienti in cui Internet globale è completamente reciso.

Recentemente, durante il blackout di Internet di 88 giorni in Iran, le autorità non si sono limitate a bloccare le VPN o a filtrare i siti web—hanno completamente staccato la spina alla banda internazionale. Con il 99% della connessione verso il mondo esterno fisicamente tagliato, gli utenti sono rimasti intrappolati in una intranet locale chiusa.

Gli strumenti di elusione standard sono inutili quando non c'è alcun Internet internazionale a cui connettersi. Eppure, durante questo enorme blocco, MasterDnsVPN si è distinto come una delle pochissime ancore di salvezza che hanno effettivamente mantenuto gli utenti connessi al web globale.

**Come è sopravvissuto a un blocco totale?**
Invece di comportarsi come una VPN standard, MasterDnsVPN si affida a tecniche intelligenti di tunneling DNS per penetrare il blackout:
* **Resolver multipli:** Instrada il traffico attraverso vari resolver DNS, garantendo che la connessione non dipenda mai da un singolo percorso facilmente bloccabile.
* **Cifratura e suddivisione dei dati:** Cifra i tuoi dati e li scompone in frammenti minuscoli e sparsi.
* **Mascheramento come traffico legittimo:** Avvolge questi frammenti di dati all'interno di query DNS standard e perfettamente normali.
* **Aggiramento delle trappole locali:** Poiché il traffico assomiglia esattamente a richieste DNS di base e quotidiane, i firewall lo lasciano passare. I dati vengono risolti e raggiungono il mondo esterno—anche se la rete ti costringe a usare i loro resolver locali ristretti e controllati dal governo.

È esattamente questa combinazione che ha permesso a MasterDnsVPN di mantenere una connessione stabile quando il mondo esterno era completamente bloccato.

---

# Installazione e Primi Passi 🧑‍💻

## Sezione 1: 🖥️ Configurazione del Server

### Sezione 1.1: 🌐 Configurazione e Preparazione del Dominio (Prerequisito)

Per ricevere le richieste DNS direttamente sul tuo server, devi delegargli un sottodominio. In breve, crea due record: un record `A` che punti all'IP del tuo server e un record `NS` che deleghi il sottodominio del tunnel a quel record A.

#### Passo 1.1.1: 🅰️ Crea un Record A (Indirizzo del Server)

- **Tipo:** `A`
- **Nome:** un nome breve come `ns`
- **Valore:** l'indirizzo IPv4 del tuo server

> Esempio: `ns.example.com -> 1.2.3.4`

> Nota Cloudflare: se il dominio usa Cloudflare, apri la pagina `DNS` e clicca sull'icona della nuvola accanto al record `A` in modo che diventi grigia (`DNS only`). Non deve rimanere proxato.

#### Passo 1.1.2: 🏷️ Crea un Record NS (Delega il Sottodominio)

- **Tipo:** `NS`
- **Nome:** il sottodominio del tunnel, ad esempio `v`
- **Valore / Target:** `ns.example.com`

> Esempio: `v.example.com -> ns.example.com`

> Nota Cloudflare: aggiungi il record `NS` normalmente. Cloudflare non proxa i record NS, ma assicurati che il record A `ns` sia già impostato su `DNS only`.

#### Sezione 1.1.3: 💡 Una Breve Nota sull'MTU

Nomi di dominio più corti lasciano più spazio per i dati effettivi all'interno di ogni richiesta DNS. Per un throughput migliore, mantieni i nomi corti. Se usi Cloudflare, mantieni comunque i record pertinenti in modalità `DNS only`.

---

### Sezione 1.2: 🐧 Installazione Rapida del Server su Linux

#### Passo 1.2.1: Installazione Automatica (Script)

Se vuoi distribuire il server su Linux, il metodo più semplice è lo script di installazione automatica. Esegui questo comando sul server:

```bash
bash <(curl -Ls https://raw.githubusercontent.com/masterking32/MasterDnsVPN/main/server_linux_install.sh)
```

Lo script gestisce l'installazione e la configurazione automaticamente. Al termine, il server si avvia e la **chiave di cifratura** viene mostrata nel log del terminale e anche scritta nel file `encrypt_key.txt` accanto all'eseguibile. Conserva questa chiave al sicuro.

#### Passo 1.2.2: Note Importanti Dopo l'Installazione

- Durante l'installazione ti verrà chiesto un dominio. Deve essere lo stesso sottodominio delegato che hai configurato nel record `NS`, ad esempio `v.example.com`.
- Dopo aver creato i record DNS, attendi la propagazione. Questa può richiedere da pochi minuti a diverse ore, e in alcuni casi fino a 48 ore a seconda del TTL e del provider DNS.
- Per verificare la configurazione DNS, puoi usare strumenti come `dig` o `nslookup`, ad esempio `dig v.example.com NS` o `nslookup -type=ns v.example.com`. Per una query diretta al nuovo nameserver: `dig @ns.example.com v.example.com A`.


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/masterdnsvpn/README_RU.MD =====

﻿# MasterDnsVPN Project 🔐

## | 🇮🇷 [فارسی](https://github.com/masterking32/MasterDnsVPN/blob/main/README_FA.MD) | 🇬🇧 [English](https://github.com/masterking32/MasterDnsVPN/blob/main/README.MD) | 🇷🇺 [Русский](https://github.com/masterking32/MasterDnsVPN/blob/main/README_RU.MD) | 🇨🇳 [中文](https://github.com/masterking32/MasterDnsVPN/blob/main/README_ZH.MD) | 🇪🇸 [Español](https://github.com/masterking32/MasterDnsVPN/blob/main/README_ES.MD) | 🇮🇹 [Italiano](https://github.com/masterking32/MasterDnsVPN/blob/main/README_IT.MD) |

**MasterDnsVPN** - это научно-исследовательский проект, предназначенный для передачи TCP-трафика через DNS-запросы и ответы. В общем смысле он схож с проектами вроде DNSTT или SlipStream, однако использует принципиально иную архитектуру и подход к реализации.
Система спроектирована с учётом совместимости с различными типами DNS-резолверов и жёсткими сетевыми условиями, с целью обеспечить максимально возможную стабильность и доставку данных даже в неблагоприятных сценариях.

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/masterking32/MasterDnsVPN)
[![oosmetrics](https://api.oosmetrics.com/api/v1/badge/achievement/5c7b2ce0-0af6-4648-8ded-fd1e847096cd.svg)](https://oosmetrics.com/achievement/5c7b2ce0-0af6-4648-8ded-fd1e847096cd)
[![oosmetrics](https://api.oosmetrics.com/api/v1/badge/achievement/355e590f-9b4a-4015-bb8c-a7f27b721711.svg)](https://oosmetrics.com/achievement/355e590f-9b4a-4015-bb8c-a7f27b721711)
[![oosmetrics](https://api.oosmetrics.com/api/v1/badge/achievement/4b98a42e-bf63-4f55-a382-0f10359a5e20.svg)](https://oosmetrics.com/achievement/4b98a42e-bf63-4f55-a382-0f10359a5e20)

<a href="https://trendshift.io/repositories/23688" target="_blank"><img src="https://trendshift.io/api/badge/repositories/23688" alt="masterking32%2FMasterDnsVPN | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/></a>

### 📊 Сравнение MasterDnsVPN с аналогичными проектами

| Особенность | SlipStream | DNSTT | MasterDnsVPN |
| :--- | :--- | :--- | :--- |
| Тип протокола | Продвинутый DNS-туннель | Классический DNS-туннель | Продвинутый DNS-туннель / VPN |
| Транспортный протокол | QUIC | KCP + Noise | Кастомный протокол + ARQ |
| Накладные расходы заголовка | 🟠 ~24B | 🔴 ~59B | 🟢 ~5–7B<br>на ≈88% меньше DNSTT<br>на ≈71% меньше SlipStream |
| Тип шифрования | TLS 1.3 (внутри QUIC) | Noise (Curve25519) | AES / ChaCha20 / XOR (XOR легче, но менее безопасен) |
| Архитектура | Монолитная (QUIC обрабатывает всё) | Многоуровневая (KCP + SMUX + Noise) | 🟢 Лёгкая кастомная, оптимизированная под DNS |
| Скорость | 🟡 Высокая (до ~5 раз быстрее, чем DNSTT) | 🔴 Средняя | 🟢 Быстрее, чем другие<br>До ~9 раз быстрее, чем DNSTT<br>До ~3,6 раз быстрее, чем SlipStream |
| Устойчивость к потере пакетов | 🟡 Хорошая | 🟠 Средняя | 🟢 Очень высокая (Multipath + ARQ) |
| Поддержка нескольких резолверов | Да (multipath) | ❌ | Да — расширенный (несколько резолверов + дублирование) |
| Устойчивость к цензуре | Хорошая | Средняя | Очень высокая (основная цель проекта) |
| Сложность настройки | Средняя | Простая | Простая базовая, сложнее при тонкой настройке |
| Поддержка SOCKS5 | Да | Да | Оптимизировано для SOCKS5 / SOCKS4 с уменьшенными накладными расходами SOCKS |
| Поддержка Shadowsocks | ✅ | ❌ | Косвенно: режим TCP-передачи может поддерживать протоколы на основе TCP<br>, например Shadowsocks, VLESS/VMess и т. д. |
| Реальный multipath | Да (QUIC multipath) | ❌ | Да (мультирезолвер + дублирование) |
| Адаптивная маршрутизация | Ограниченная | ❌ | Расширенная (на основе задержки/потерь) |
| Цель проектирования | Высокая скорость и эффективность | Простота и стабильность | Работоспособность в самых сложных сетях — стабильность, скорость и эффективность |
| Язык реализации | Rust | Go | Go (основной), Python (legacy) |
| Встроенный балансировщик | 🔴 | ❌ | 🟢 (8 режимов) |
| Система дублирование пакетов | ❌ | ❌ | Да — увеличивает трафик для повышения надёжности (настраивается или может быть отключено) |
| Допуск MTU | Лучше чем DNSTT | - | Работает даже при очень маленьком значении MTU, т.к. накладные расходы протокола минимальны |
| Отказоустойчивость | ❌ | ❌ | ✅ |
| Скорость загрузки 10MB (Локально) | 🟡 0.978с | 🔴 2.492с | 🟢 0.270с |
| Скорость отправки 10MB (Локально) | 🟡 3.249с | 🔴 16.207с | 🟢 1.746s |
| Проверка состояния резолвера и авто-отключение | ❌ | ❌ | ✅ |
| Фоновая реактивация здоровых резолверов | ❌ | ❌ | ✅ |
| Локальный DNS на клиенте (для предотвращения перехвата DNS) | ❌ | ❌ | ✅ (с сильным/активным DNS кэшированием) |
| DNS через SOCKS5 | ❌ | ❌ | ✅ (с DNS кэшированием) |
| Тонкая настройка | 🟠 | 🟠 | 🟢 Большинство подсистем настраиваемы |
| Не требуется стороннее вспомогательное ПО | ❌ | ❌ | 🟢 Дополнительное программное обеспечение не требуется; при необходимости можно использовать совместно с SOCKS или такими инструментами, как Shadowsocks или OpenVPN
 |

---

### ❌ Отказ от ответственности / Disclaimer

MasterDnsVPN предоставляется исключительно в образовательных и исследовательских целях.

- **Предоставляется без гарантии:** Данное программное обеспечение предоставляется “КАК ЕСТЬ”, без каких-либо явных или подразумеваемых гарантий, включая гарантии товарной пригодности, пригодности для конкретной цели или отсутствия нарушений прав.
- **Ограничение ответственности:** Разработчики и участники проекта не несут ответственности за любые прямые, косвенные, случайные, последующие или иные убытки, возникающие в результате использования данного ПО или невозможности его использования.
- **Ответственность пользователя:** Использование данного проекта за пределами тестовых сред может привести к сбоям в работе сети или ее повреждению. Пользователь несет полную ответственность за все последствия установки, настройки и использования.
- **Соблюдение законодательства:** Использование данного проекта с целью обхода местного законодательства может повлечь за собой гражданско-правовые или уголовные последствия. Перед использованием ознакомьтесь с законодательством и нормативными актами вашей страны. Разработчики не несут ответственности за нарушение пользователями местного, национального или международного законодательства.
- **Условия лицензии:** Использование, копирование, распространение или модификация данного программного обеспечения регулируются условиями лицензии MIT, изложенными в файле [LICENSE](https://github.com/masterking32/MasterDnsVPN/blob/main/LICENSE) данного репозитория. Любое использование, не соответствующее этим условиям, запрещено.

---

## Канал новостей и поддержки 📢

Чтобы быть в курсе последних новостей, релизов и новостей о проектах, подпишитесь на наш канал в Telegram: [Telegram Channel](https://t.me/masterdnsvpn)

---

### Если вам понравился этот проект, пожалуйста, поддержите его, поставив звездочку на GitHub (⭐). Это поможет проекту привлечь внимание.

---

### Добровольная финансовая поддержка 💸

- TON:

`masterking32.ton`

- EVM-совместимые сети (ETH и совместимые цепочки):

`0x517f07305D6ED781A089322B6cD93d1461bF8652`

- TRC20 (TRON):

`TLApdY8APWkFHHoxebxGY8JhMeChiETqFH`

Мы ценим каждый вклад и каждый отзыв. Ваша поддержка напрямую способствует дальнейшему развитию и совершенствованию проекта..

---

## Основные характеристики и преимущества ✨

Краткий обзор основных возможностей MasterDnsVPN:

- **Устойчивость к цензуре и работоспособность в сложных сетях:** 🛡️ Разработан для работы в сетях с фильтрацией, при нестабильном соединении и в условиях жестких ограничений по размеру MTU.
- **Оптимизированный кастомный протокол:** 🔄 Использует кастомный протокол с механизмом повторной передачи данных, что позволяет сократить накладные расходы и увеличить полезный объем данных DNS.
- **Multipath и дублирование пакетов:** 📡 Трафик передается по нескольким маршрутам, а также поддерживается выборочное дублирование для повышения вероятности доставки в нестабильных сетях.
- **Умный выбор резолверов и проверка их работоспособности:** ⚡ Выбор резолверов на основе их качества и работоспособности, а также автоматическое управление проблемными резолверами.
- **Определение и синхронизация MTU:** 🧰 Определяет фактический размер MTU рабочих маршрутов и синхронизирует их с ним, чтобы уменьшить фрагментацию и повысить стабильность.
- **Поддержка и оптимизация SOCKS5 / SOCKS4:** 🧦 Оптимизирована работа с локальным прокси для популярных приложений.
- **Объединение блоков управления и снижение нагрузки на каналы управления:** 📦 Объединяет пакеты подтверждения (ACK) и управляющий трафик для уменьшения количества управляющих сообщений.
- **Опциональное сжатие и упаковка запросов:** 🗜️ Уменьшает количество запросов и повышает эффективность при использовании малых значений MTU.
- **Гибкое шифрование:** 🔐 Поддерживает несколько методов шифрования для обеспечения оптимального соотношения скорости и безопасности.
- **Опциональный клиентский DNS и кэширование:** 📛 Позволяет предоставлять доступ к локальному DNS-сервису, сокращать задержки и ограничивать возможности перехвата.
- **Масштабируемое управление ресурсами:** ⚙️ Может работать на небольших серверах или быть настроено для более высоких нагрузок.

Этот список представляет собой лишь общее краткое изложение. В соответствующих разделах ниже каждая область описана более подробно.

---

## 🌐 Проверенный в бою во время полного отключения интернета

MasterDnsVPN — это не просто теоретический проект. Он прошел испытание в реальных условиях и доказал свою эффективность в ситуациях, когда глобальный интернет полностью отключен.

Недавно, во время 88-дневного отключения интернета в Иране, власти не просто заблокировали VPN или отфильтровали сайты — они полностью отключили международную пропускную способность. Поскольку 99% связи с внешним миром было физически отключено, пользователи оказались запертыми в закрытой локальной сети. 

Стандартные инструменты обхода блокировок бесполезны, когда нет международного интернета, к которому можно подключиться. Однако во время этого масштабного отключения MasterDnsVPN выделился как один из немногих спасательных кругов, которые действительно позволили пользователям оставаться на связи с глобальной сетью.

**Как он выжил при полном отключении?**
Вместо того чтобы действовать как стандартный VPN, MasterDnsVPN использует интеллектуальные технологии DNS-туннелирования, чтобы пробиться сквозь блокировку:
* **Несколько резолверов:** он направляет трафик через различные DNS-резолверы, гарантируя, что соединение никогда не будет зависеть от одного, легко блокируемого пути.
* **Шифрование и разбиение данных:** он шифрует ваши данные и разбивает их на крошечные, разбросанные фрагменты.
* **Маскировка под легитимный трафик:** он упаковывает эти фрагменты данных в стандартные, совершенно обычные DNS-запросы. 
* **Обход локальных ограничений:** поскольку трафик выглядит точно так же, как обычные повседневные DNS-запросы, брандмауэры пропускают его. Данные преобразуются и попадают во внешний мир — даже если сеть заставляет вас использовать собственные ограниченные локальные серверы преобразования, контролируемые государством.

Именно эта комбинация позволила MasterDnsVPN поддерживать стабильное соединение, когда доступ к внешнему миру был полностью заблокирован.

---

# Установка и запуск 🧑‍💻

## Раздел 1: 🖥️ Настройка сервера

### Раздел 1.1: 🌐 Настройка и подготовка домена (Требования)

Чтобы принимать DNS-запросы непосредственно на вашем сервере, необходимо делегировать ему субдомен. Проще говоря, создайте две записи: одну `A` запись, указывающую на IP-адрес вашего сервера, и одну запись `NS`, делегирующую субдомен туннеля этой `A` записи.

#### Шаг 1.1.1: 🅰️ Создание A записи (Server Address)

- **Тип:** `A`
- **Имя:** короткое имя, например `ns`
- **Значение:** IPv4-адрес вашего сервера

> Пример: `ns.example.com -> 1.2.3.4`

> Примечание Cloudflare: если для домена используется Cloudflare, откройте страницу `DNS` и нажмите на значок облака рядом с `A` записью, чтобы он стал серым (`Только DNS`). Прокси должен быть отключён.

#### Шаг 1.1.2: 🏷️ Создание NS записи (Delegate the Subdomain)

- **Тип:** `NS`
- **Имя:** субдомен туннеля, например `v`
- **Значение / Цель:** `ns.example.com`

> Пример: `v.example.com -> ns.example.com`

> Примечание Cloudflare: добавьте запись `NS` в обычном порядке. Cloudflare не проксирует записи NS, но убедитесь, что для записи A `ns` уже установлен параметр `Только DNS`.

#### Шаг 1.1.3: 💡 Краткая информация о MTU

Более короткие доменные имена оставляют больше места для фактических данных в каждом DNS-запросе. Для повышения пропускной способности используйте короткие имена. Если вы используете Cloudflare, все равно сохраняйте соответствующие записи в режиме `Только DNS`.

---

### Раздел 1.2: 🐧 Быстрая установка на Linux

#### шаг 1.2.1: Автоматическая установка (Script)

Если вы хотите развернуть сервер MasterDnsVPN на Linux, проще всего воспользоваться скриптом автоматической установки. Выполните на Linux сервере следующую команду:

```bash
bash <(curl -Ls https://raw.githubusercontent.com/masterking32/MasterDnsVPN/main/server_linux_install.sh)
```

Скрипт автоматически выполняет установку и настройку. По завершении сервер запускается, а **ключ шифрования** отображается в терминале и записывается в файл `encrypt_key.txt`, расположенный рядом с исполняемым файлом. Храните этот ключ в надежном месте.

#### Шаг 1.2.2: Важные замечания после установки

- В процессе установки вам будет предложено указать домен. Это должен быть тот же делегированный субдомен, который вы настроили в `NS` записи, например `v.example.com`.
- После создания DNS-записей дождитесь их распространения (propagation). Это может занять от нескольких минут до нескольких часов, а в отдельных случаях — до 48 часов, в зависимости от значения TTL и используемого DNS-провайдера.
- Для проверки настройки DNS можно использовать утилиты `dig` или `nslookup`, например: `dig v.example.com NS` или `nslookup -type=ns v.example.com`. Для прямого запроса к новому DNS-серверу: `dig @ns.example.com v.example.com A`.


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/masterdnsvpn/README_ZH.MD =====

# MasterDnsVPN Project 🔐

## | 🇮🇷 [فارسی](https://github.com/masterking32/MasterDnsVPN/blob/main/README_FA.MD) | 🇬🇧 [English](https://github.com/masterking32/MasterDnsVPN/blob/main/README.MD) | 🇷🇺 [Русский](https://github.com/masterking32/MasterDnsVPN/blob/main/README_RU.MD) | 🇨🇳 [中文](https://github.com/masterking32/MasterDnsVPN/blob/main/README_ZH.MD) | 🇪🇸 [Español](https://github.com/masterking32/MasterDnsVPN/blob/main/README_ES.MD) | 🇮🇹 [Italiano](https://github.com/masterking32/MasterDnsVPN/blob/main/README_IT.MD) |

**MasterDnsVPN** 是一个面向科研的项目，旨在通过 DNS 查询和响应承载 TCP 流量。从总体目标上看，它与 DNSTT 或 SlipStream 等项目类似，但它遵循了根本不同的结构和实现思路。
本系统的设计目标是兼容多种解析器（resolver）行为以及恶劣的网络环境，力求即使在最糟糕的情况下也能保持尽可能高的稳定性和数据投递能力。


[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/masterking32/MasterDnsVPN)
[![oosmetrics](https://api.oosmetrics.com/api/v1/badge/achievement/5c7b2ce0-0af6-4648-8ded-fd1e847096cd.svg)](https://oosmetrics.com/achievement/5c7b2ce0-0af6-4648-8ded-fd1e847096cd)
[![oosmetrics](https://api.oosmetrics.com/api/v1/badge/achievement/355e590f-9b4a-4015-bb8c-a7f27b721711.svg)](https://oosmetrics.com/achievement/355e590f-9b4a-4015-bb8c-a7f27b721711)
[![oosmetrics](https://api.oosmetrics.com/api/v1/badge/achievement/4b98a42e-bf63-4f55-a382-0f10359a5e20.svg)](https://oosmetrics.com/achievement/4b98a42e-bf63-4f55-a382-0f10359a5e20)

<a href="https://trendshift.io/repositories/23688" target="_blank"><img src="https://trendshift.io/api/badge/repositories/23688" alt="masterking32%2FMasterDnsVPN | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/></a>

### 📊 MasterDnsVPN 与同类项目的对比

| 特性 | SlipStream | DNSTT | MasterDnsVPN |
| :--- | :--- | :--- | :--- |
| 协议类型 | 高级 DNS 隧道 | 经典 DNS 隧道 | 高级 DNS 隧道 / VPN |
| 传输协议 | QUIC | KCP + Noise | 自定义协议 + ARQ |
| 传输头部开销 | 🟠 约 24B | 🔴 约 59B | 🟢 约 5–7B<br>比 DNSTT 低约 88%<br>比 SlipStream 低约 71% |
| 加密方式 | TLS 1.3（QUIC 内部） | Noise（Curve25519） | AES / ChaCha20 / XOR（若使用 XOR：轻量、安全性较低且无额外开销） |
| 架构 | 统一式（QUIC 处理一切） | 多层式（KCP + SMUX + Noise） | 🟢 针对 DNS 优化的轻量自定义设计 |
| 速度 | 🟡 高（最高比 DNSTT 快约 5 倍） | 🔴 中 | 🟢 比其他项目更快<br>最高比 DNSTT 快约 9 倍<br>最高比 SlipStream 快约 3.6 倍 |
| 丢包下的稳定性 | 🟡 良好 | 🟠 中 | 🟢 极高（多路径 + ARQ） |
| 多解析器支持 | 是（多路径） | ❌ | 是 —— 高级（多解析器 + 冗余复制） |
| 重度审查下的抗封锁能力 | 良好 | 中 | 非常强（项目的核心目标） |
| 部署复杂度 | 中 | 简单 | 安装更简便<br>仅当你大量自定义高级设置时才更复杂 |
| SOCKS5 支持 | 是 | 是 | 针对 SOCKS5 / SOCKS4 优化，降低了 SOCKS 开销 |
| Shadowsocks 支持 | ✅ | ❌ | 间接支持：TCP 转发模式可承载基于 TCP 的协议<br>例如 Shadowsocks、VLESS/VMess 等 |
| 真正的多路径 | 是（QUIC 多路径） | ❌ | 是（多解析器 + 冗余复制） |
| 自适应路由 | 有限 | ❌ | 高级（基于延迟/丢包） |
| 设计目标 | 高速与高效 | 简单与稳定 | 在最恶劣的网络中存活 —— 稳定、速度与效率 |
| 实现语言 | Rust | Go | 主版本为 Go<br>同时也存在旧版 Python 版本 |
| 内置负载均衡器 | 🔴 | ❌ | 🟢（8 种内置均衡模式） |
| 冗余复制系统 | ❌ | ❌ | 是 —— 增加流量以提升可靠性（可配置或可禁用） |
| MTU 容忍度 | 优于 DNSTT | - | 即使 MTU 非常小也能工作，因为协议开销极低 |
| 故障切换系统 | ❌ | ❌ | ✅ |
| 下载速度 10MB（本地） | 🟡 0.978s | 🔴 2.492s | 🟢 0.270s |
| 上传速度 10MB（本地） | 🟡 3.249s | 🔴 16.207s | 🟢 1.746s |
| 解析器健康检查与自动禁用 | ❌ | ❌ | ✅ |
| 后台重新启用恢复健康的解析器 | ❌ | ❌ | ✅ |
| 客户端本地 DNS 服务（减少 DNS 劫持） | ❌ | ❌ | ✅（具备强力 DNS 缓存） |
| 通过 SOCKS5 进行 DNS 解析 | ❌ | ❌ | ✅（带 DNS 缓存） |
| 细粒度的专业配置 | 🟠 | 🟠 | 🟢 几乎每个子系统都可配置 |
| 无需外部辅助软件 | ❌ | ❌ | 🟢 无需额外软件；如有需要，仍可与 SOCKS 或 Shadowsocks、OpenVPN 等工具组合使用 |

---

### ❌ 免责声明

MasterDnsVPN 仅作为教育和研究项目提供。

- **不提供任何担保：** 本软件按“原样”（AS-IS）提供，不附带任何明示或暗示的担保，包括适销性、特定用途适用性或不侵权。
- **责任限制：** 本项目的开发者和贡献者对因使用本软件或无法使用本软件而引起的任何直接、间接、附带、后果性或其他损害概不负责。
- **用户责任：** 在测试环境之外使用本项目可能会扰乱或损害网络行为。用户需独自承担安装、配置和使用的一切后果。
- **法律合规：** 使用本项目绕过当地法律可能导致民事或刑事后果。请在使用前查阅你所在国家的法律法规。对于用户违反地方、国家或国际法律的行为，开发者概不负责。
- **许可条款：** 本软件的使用、复制、分发或修改受本仓库 `LICENSE` 文件中的许可协议约束。任何超出该条款的使用均被禁止。

---

## 公告与支持频道 📢

如需获取最新动态、发布信息和项目更新，请关注我们的 Telegram 频道：[Telegram Channel](https://t.me/masterdnsvpn)

---

### 如果你喜欢这个项目，请在 GitHub 上为它点亮星标（⭐）以示支持。这有助于让更多人发现本项目。

---

### 可选的资金支持 💸

- TON 网络：

`masterking32.ton`

- EVM 兼容网络（ETH 及兼容链）：

`0x517f07305D6ED781A089322B6cD93d1461bF8652`

- TRC20 网络（TRON）：

`TLApdY8APWkFHHoxebxGY8JhMeChiETqFH`

我们感谢每一份贡献和每一条反馈。你的支持将直接助力项目的持续开发与改进。

---

## 主要特性与优势 ✨

MasterDnsVPN 主要能力的简要概述：

- **抗审查与恶劣网络生存能力：** 🛡️ 设计用于在被过滤的网络、不稳定的链路以及严格的 MTU 环境中工作。
- **轻量自定义协议：** 🔄 采用带有重传逻辑的自定义协议，以降低开销并提升可用的 DNS 有效载荷。
- **多路径与数据包冗余复制：** 📡 通过多条路径发送流量，并支持选择性冗余复制，以提升在不稳定网络上的投递成功率。
- **智能解析器选择与健康检查：** ⚡ 根据质量与健康状况选择解析器，并自动管理有问题的解析器。
- **MTU 探测与同步：** 🧰 检测可用路径的实际 MTU 并据此对齐，以减少分片并提升稳定性。
- **SOCKS5 / SOCKS4 支持与优化：** 🧦 针对常见应用优化的本地代理处理。
- **打包控制块与更低的控制开销：** 📦 将 ACK/控制流量打包在一起，以减少控制信令的冗余。
- **可选的压缩与请求打包：** 🗜️ 减少请求数量，并在小 MTU 条件下提升效率。
- **灵活的加密：** 🔐 支持多种加密方法，以在速度与安全之间取得平衡。
- **可选的客户端本地 DNS 与缓存：** 📛 可对外提供本地 DNS 服务，降低延迟并减少劫持机会。
- **可伸缩的资源控制：** ⚙️ 既可运行在小型服务器上，也可针对更高负载进行调优。

此列表仅为高层次概述。下文的相关章节会更详细地解释每个领域。

---

## 🌐 在彻底的网络断网中经受实战检验

MasterDnsVPN 不只是一个理论项目。它经过实战检验，在全球互联网被完全切断的环境中也被证明可以工作。

最近，在伊朗持续 88 天的断网期间，当局不仅仅是封锁 VPN 或过滤网站——他们直接切断了国际带宽。在与外部世界的连接被物理切断 99% 的情况下，用户被困在一个封闭的本地内网之中。

当根本没有国际互联网可供连接时，标准的翻墙工具毫无用处。然而，在这场大规模断网期间，MasterDnsVPN 脱颖而出，成为极少数真正让用户保持连接到全球网络的“生命线”之一。

**它是如何在彻底断网中存活下来的？**
MasterDnsVPN 不像标准 VPN 那样工作，而是依靠智能的 DNS 隧道技术来穿透断网封锁：
* **多解析器：** 它通过多个 DNS 解析器路由流量，确保连接绝不依赖单一且容易被封锁的路径。
* **加密与数据切分：** 它对你的数据进行加密，并将其拆分成微小、分散的碎片。
* **伪装成合法流量：** 它将这些数据碎片包裹在标准且完全正常的 DNS 查询中。
* **绕过本地陷阱：** 由于流量看起来与基本的日常 DNS 请求一模一样，防火墙会允许其通过。即使网络强制你使用其自有的、受限的、由政府控制的本地解析器，数据依然会被解析并抵达外部世界。

正是这种精确的组合，使得 MasterDnsVPN 在外部世界被完全封锁时仍能维持稳定的连接。

---

# 安装与上手 🧑‍💻

## 第 1 部分：🖥️ 服务端部署

### 第 1.1 节：🌐 域名设置与准备（前置条件）

要在你的服务器上直接接收 DNS 请求，你必须将一个子域名委派给它。简而言之，需要创建两条记录：一条指向你服务器 IP 的 `A` 记录，以及一条将隧道子域名委派到该 A 记录的 `NS` 记录。

#### 步骤 1.1.1：🅰️ 创建 A 记录（服务器地址）

- **类型：** `A`
- **名称：** 一个简短的名称，例如 `ns`
- **值：** 你的服务器 IPv4 地址

> 示例：`ns.example.com -> 1.2.3.4`

> Cloudflare 提示：如果域名使用 Cloudflare，请打开 `DNS` 页面，并点击 `A` 记录旁边的云朵图标使其变为灰色（`DNS only`）。它绝不能保持被代理状态。

#### 步骤 1.1.2：🏷️ 创建 NS 记录（委派子域名）

- **类型：** `NS`
- **名称：** 隧道子域名，例如 `v`
- **值 / 目标：** `ns.example.com`

> 示例：`v.example.com -> ns.example.com`

> Cloudflare 提示：正常添加 `NS` 记录即可。Cloudflare 不会代理 NS 记录，但请确保 `ns` 这条 A 记录已被设置为 `DNS only`。

#### 第 1.1.3 节：💡 关于 MTU 的简短说明

较短的域名会在每个 DNS 请求中为实际数据留出更多空间。为了获得更好的吞吐量，请尽量保持名称简短。如果你使用 Cloudflare，仍应将相关记录保持为 `DNS only` 模式。

---

### 第 1.2 节：🐧 Linux 服务器快速安装

#### 步骤 1.2.1：自动安装（脚本）

如果你想在 Linux 上部署服务端，最简单的方法是使用自动安装脚本。在服务器上运行此命令：

```bash
bash <(curl -Ls https://raw.githubusercontent.com/masterking32/MasterDnsVPN/main/server_linux_install.sh)
```

该脚本会自动完成安装和配置。完成后，服务器会启动，**加密密钥**会显示在终端日志中，并同时写入可执行文件旁边的 `encrypt_key.txt`。请妥善保管此密钥。

#### 步骤 1.2.2：安装后的重要说明

- 安装期间，系统会询问你一个域名。它必须与你在 `NS` 记录中配置的、被委派的子域名相同，例如 `v.example.com`。
- 创建 DNS 记录后，请等待其生效传播。这可能需要几分钟到数小时，在某些情况下，视 TTL 和 DNS 提供商而定，最长可达 48 小时。
- 要验证 DNS 设置，你可以使用 `dig` 或 `nslookup` 等工具，例如 `dig v.example.com NS` 或 `nslookup -type=ns v.example.com`。如需直接向新的域名服务器查询：`dig @ns.example.com v.example.com A`。


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/masterdnsvpn/scripts/bench/README.md =====

# MasterDnsVPN Benchmark Suite

This directory contains the core benchmarking tools for MasterDnsVPN, now enhanced with high-precision timing and standalone tool capabilities inspired by the `slipstream-rust` methodology.

## Tools

### 1. `bench.go` (Go-based Orchestrator and Benchmarker)

The primary tool for end-to-end performance testing. It builds the server and client, orchestrates a local tunnel, and measures throughput using **First-Byte Timing**.

#### High-Precision Timing
Unlike simple timers, `bench.go` starts its measurement only when the **first byte** of the actual payload is sent or received. This ensures that connection establishment and handshake overheads do not skew the results, providing a true measure of tunnel throughput.

#### Usage (Full Orchestration)

To run a standard end-to-end benchmark through the MasterDnsVPN tunnel:

```bash
go run scripts/bench/bench.go -runs 3 -bytes 10485760
```

#### CLI Options
| Flag | Description | Default |
|------|-------------|---------|
| `-runs` | Number of runs for each direction | 3 |
| `-bytes` | Total payload size in bytes | 10MiB |
| `-force-build` | Rebuild server and client binaries | true |
| `-client-port` | Port for the local client listener | 18080 |
| `-server-port` | Port for the UDP server listener | 5300 |

---

### 2. Standalone Mode (Tool Mode)

`bench.go` can also be used as a standalone source/sink tool, similar to `tcp_bench.py`. This is useful for testing manual configurations or other TCP links.

#### Modes
- `sink`: Listens for a connection and discards received data (sends "OK" at the end).
- `source`: Listens for a connection and sends data.
- `send`: Connects to a target and sends data (waits for "OK" at the end).
- `recv`: Connects to a target and receives data.

#### Examples

**Start a sink server (receiver):**
```bash
go run scripts/bench/bench.go -mode sink -addr :9090
```

**Run a sender (client):**
```bash
go run scripts/bench/bench.go -mode send -addr 127.0.0.1:9090 -bytes 100000000
```

**JSON Output:**
To get raw data for analysis:
```bash
go run scripts/bench/bench.go -mode send -addr 127.0.0.1:9090 -json
```

---

## Directory Structure

- `.bench/local_snapshot_go/bin`: Compiled benchmark binaries.
- `.bench/local_snapshot_go/runtime`: Temporary configuration and log files.

## Methodology

1. **First-Byte Start**: The timer starts on the first successful `Read` or `Write` of the payload.
2. **ACK Synchronization**: For "Exfil" scenarios, the sink sends an "OK" acknowledgment to ensure all data has cleared the tunnel before the timer stops.
3. **Monotonic Timing**: Uses Go's monotonic clock for sub-millisecond precision.

