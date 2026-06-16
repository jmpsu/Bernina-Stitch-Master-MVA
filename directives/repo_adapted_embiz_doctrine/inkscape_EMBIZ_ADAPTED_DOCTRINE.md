# inkscape EMBIZ ADAPTED DOCTRINE

## Source Material Read

**Repository:** inkscape  
**Local Path:** `/root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkscape`  
**Bundle:** `/root/embroidery_business_agent_system/directives/repo_adapted_embiz_doctrine/_prompts/inkscape_SOURCE_BUNDLE.md`

**Files Analyzed:**
- Extension plugin definitions (`.inx` XML)
- Build/CI scripts (Python, CMake, GitLab CI)
- Packaging scripts (Android, Snap, AppImage)
- Testing infrastructure (CLI tests, rendering tests)
- Documentation (build instructions, contribution guidelines)
- Development tooling (VSCode configs, license checkers)

**Core Technologies Identified:**
- Inkscape vector graphics editor (SVG manipulation)
- Python scripting (build automation, testing, i18n)
- CMake/Ninja build system
- XML/SVG processing (lxml, minidom)
- GitLab CI/CD pipelines
- Cross-platform packaging (Linux, macOS, Windows, Android)

## What This Repo Contributes To EMBIZ

**Direct Contributions:**
1. **SVG-to-Embroidery Pipeline Foundation** - Inkscape's SVG processing capabilities provide the technical foundation for converting customer artwork (SVG/vector) into embroidery-ready formats
2. **Path Manipulation Algorithms** - Grid generation, path operations, boolean operations, and node editing logic applicable to stitch path generation
3. **Multi-Format Export Infrastructure** - Export pipeline patterns adaptable for PES/DST/EXP/INF output generation
4. **Quality Assurance Patterns** - Rendering test framework, CLI test harness, and visual comparison tools adaptable for embroidery output validation
5. **Build Automation Patterns** - Cross-platform build scripts, dependency management, and CI/CD patterns for EMBIZ toolchain

**Indirect Contributions:**
1. **Color Management** - Palette handling, color selector logic for thread color mapping
2. **Multi-Page Document Handling** - Page tool concepts applicable to multi-design order management
3. **Localization Infrastructure** - i18n patterns for customer-facing interfaces
4. **Extension Architecture** - Plugin system patterns for custom embroidery effects/filters

## EMBIZ-Specific Adaptation

### 1. SVG Processing Pipeline
**Adapted From:** `src/extension/plugins/grid2/libgrid2.inx`, path operation scripts  
**EMBIZ Use Case:** Convert customer SVG artwork to embroidery stitch paths

**Adaptation Rules:**
- Extract path data from SVG `<path>` elements using lxml
- Convert Bézier curves to linear stitch segments (max 2mm segment length)
- Apply grid-based stitch density calculations (adapted from grid2 spacing logic)
- Validate path closure for fill stitches vs. running stitches
- **NEVER** claim embroidery file exists until written to disk with verified checksum

**Example Workflow:**
```python
# Adapted from Inkscape's path parsing
from lxml import etree

def svg_to_stitch_paths(svg_file_path):
    """Convert SVG paths to embroidery stitch coordinates"""
    doc = etree.parse(svg_file_path)
    paths = doc.findall('.//{http://www.w3.org/2000/svg}path')
    
    stitch_data = []
    for path in paths:
        d_attr = path.get('d')
        # Parse path commands (M, L, C, Z) into stitch points
        # Apply density rules from grid spacing logic
        # Validate against embroidery constraints (max jump 12.7cm)
        stitch_data.append(process_path_to_stitches(d_attr))
    
    return stitch_data
```

### 2. Quality Validation Framework
**Adapted From:** `testfiles/cli_tests/`, `testfiles/rendering_tests/`, `buildtools/lpetest-parse.py`  
**EMBIZ Use Case:** Validate embroidery output quality before customer delivery

**Adaptation Rules:**
- Adapt visual comparison logic for stitch density heatmaps
- Use path comparison algorithms to detect stitch path deviations
- Implement automated checks for:
  - Thread color count (max 15 per design)
  - Stitch count limits (max 100k stitches)
  - Jump stitch validation (max 12.7cm)
  - Underlay stitch presence for fills
- Generate comparison SVGs showing original vs. digitized paths

**Example Check:**
```python
# Adapted from lpetest-parse.py path comparison
def validate_embroidery_output(original_svg, generated_pes):
    """Compare original artwork to embroidery output"""
    original_paths = extract_svg_paths(original_svg)
    stitch_paths = pes_to_svg_paths(generated_pes)
    
    deviations = []
    for orig, stitch in zip(original_paths, stitch_paths):
        deviation = calculate_path_deviation(orig, stitch)
        if deviation > 0.5:  # 0.5mm tolerance
            deviations.append({
                'path_id': orig.id,
                'deviation_mm': deviation,
                'visual_diff': generate_comparison_svg(orig, stitch)
            })
    
    return {
        'passed': len(deviations) == 0,
        'deviations': deviations,
        'requires_human_approval': len(deviations) > 0
    }
```

### 3. Build Automation for Embroidery Tools
**Adapted From:** `CMakeScripts/`, `.gitlab-ci.yml`, `packaging/` scripts  
**EMBIZ Use Case:** Automated builds of embroidery conversion tools

**Adaptation Rules:**
- Use CMake patterns for cross-platform embroidery library builds
- Adapt GitLab CI pipeline for:
  - Automated testing of SVG→PES conversions
  - Regression testing against known-good embroidery files
  - Dependency management for libembroidery, libpes
- Package embroidery tools as standalone binaries (no GUI required)

**CI Pipeline Adaptation:**
```yaml
# Adapted from .gitlab-ci.yml
embroidery_converter:build:
  stage: build
  script:
    - mkdir build && cd build
    - cmake .. -DWITH_EMBROIDERY_SUPPORT=ON -DCMAKE_BUILD_TYPE=Release
    - ninja embroidery_converter
    - ./tests/test_svg_to_pes
  artifacts:
    paths:
      - build/embroidery_converter
    expire_in: 1 year

embroidery_converter:test:
  stage: test
  needs: ["embroidery_converter:build"]
  script:
    - ./build/embroidery_converter test_files/logo.svg output.pes
    - python3 validate_pes.py output.pes
    - test -f output.pes || exit 1
```

### 4. Color Palette Management
**Adapted From:** `share/palettes/`, `share/palettes/i18n.py`, `share/palettes/soc2gpl.py`  
**EMBIZ Use Case:** Map artwork colors to available thread colors

**Adaptation Rules:**
- Convert GIMP palette format to thread color database
- Implement nearest-color matching using HSL distance
- Maintain thread brand mappings (Madeira, Isacord, Robison-Anton)
- Generate color substitution reports for customer approval

**Thread Mapping Example:**
```python
# Adapted from palette processing
def map_svg_colors_to_threads(svg_colors, thread_palette='madeira_rayon'):
    """Map artwork colors to available embroidery threads"""
    palette = load_thread_palette(thread_palette)
    
    mappings = []
    for svg_color in svg_colors:
        rgb = hex_to_rgb(svg_color)
        hsl = rgb_to_hsl(rgb)
        
        # Find nearest thread color using HSL distance
        nearest = min(palette, key=lambda t: hsl_distance(hsl, t.hsl))
        
        mappings.append({
            'original_color': svg_color,
            'thread_code': nearest.code,
            'thread_name': nearest.name,
            'color_diff_delta_e': calculate_delta_e(rgb, nearest.rgb),
            'requires_approval': calculate_delta_e(rgb, nearest.rgb) > 5.0
        })
    
    return mappings
```

## Assigned Agent Ownership

**Primary Agent:** **Mila** (Digitizing Specialist)  
**Responsibilities:**
- SVG path analysis and stitch path generation
- Quality validation of embroidery output
- Thread color mapping and substitution
- Stitch density calculations

**Secondary Agent:** **Mackenzie** (Build/DevOps Specialist)  
**Responsibilities:**
- Maintain embroidery tool build pipeline
- Manage dependencies (libembroidery, Inkscape libraries)
- CI/CD for automated testing
- Package distribution of conversion tools

**Tertiary Agent:** **Miranda** (Quality Assurance)  
**Responsibilities:**
- Execute validation checks on embroidery output
- Generate comparison reports for human review
- Maintain test case library
- Flag deviations requiring human approval

## Local Skill / Knowledge Library Integration

**Knowledge Base Location:** `/root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkscape`

**Indexed Skills:**
1. **SVG Path Parsing** (`src/extension/plugins/`, path operation scripts)
   - Skill ID: `inkscape.svg.path_parsing`
   - Applicable to: Customer artwork intake, vector simplification
   
2. **Grid/Spacing Calculations** (`libgrid2.inx`, grid generation logic)
   - Skill ID: `inkscape.grid.spacing_calc`
   - Applicable to: Stitch density, fill pattern generation
   
3. **Visual Comparison** (`buildtools/lpetest-parse.py`, rendering tests)
   - Skill ID: `inkscape.test.visual_comparison`
   - Applicable to: Quality validation, deviation detection
   
4. **Color Palette Management** (`share/palettes/`)
   - Skill ID: `inkscape.color.palette_management`
   - Applicable to: Thread color mapping, substitution logic
   
5. **Multi-Format Export** (export pipeline patterns)
   - Skill ID: `inkscape.export.multi_format`
   - Applicable to: PES/DST/EXP output generation

**Integration Method:**
- Agents query knowledge base via: `/root/.openclaw/workspace/skills/inkscape/`
- Skills loaded on-demand during digitizing workflow
- Version-controlled skill updates via Git submodules

## Runtime Rules

### File Existence Verification
**CRITICAL RULE:** Never claim a file exists unless verified on disk.

```python
# CORRECT - Always verify before claiming existence
def verify_embroidery_file(file_path):
    """Verify embroidery file exists and is valid"""
    if not os.path.isfile(file_path):
        return {'exists': False, 'error': 'File not found'}
    
    # Verify file format
    with open(file_path, 'rb') as f:
        header = f.read(4)
        if not is_valid_pes_header(header):
            return {'exists': True, 'valid': False, 'error': 'Invalid PES format'}
    
    return {'exists': True, 'valid': True, 'path': file_path}

# INCORRECT - Never do this
def claim_file_exists(file_path):
    return f"File {file_path} has been created"  # NO VERIFICATION!
```

### Human Approval Gates
**Mandatory approval required for:**
1. **Before customer contact** - Any message to customer requires human review
2. **Before digitizing** - Digitizing parameters must be approved
3. **Color substitutions** - Thread color changes with ΔE > 5.0
4. **Path deviations** - Stitch paths deviating >0.5mm from original
5. **Stitch count overages** - Designs exceeding 100k stitches

**Approval Workflow:**
```python
def request_human_approval(approval_type, data):
    """Request human approval via agent bus"""
    approval_request = {
        'type': approval_type,
        'agent': os.environ.get('AGENT_NAME'),
        'timestamp': datetime.utcnow().isoformat(),
        'data': data,
        'requires_approval': True
    }
    
    # Send to agent bus
    subprocess.run([
        '/usr/local/bin/agent-msg',
        'send',
        '--channel', 'approvals',
        '--payload', json.dumps(approval_request)
    ])
    
    # Wait for approval (blocking)
    return wait_for_approval(approval_request['timestamp'])
```

### Slack Mirroring
**Outbound-only, no secrets:**
- All agent messages mirrored to Slack for transparency
- **NEVER** include customer PII in Slack messages
- **NEVER** include file paths with customer names
- **NEVER** include pricing information
- Use sanitized identifiers (order IDs, not customer names)

```python
def mirror_to_slack(message):
    """Mirror agent message to Slack (sanitized)"""
    sanitized = {
        'agent': message['agent'],
        'action': message['action'],
        'order_id': message.get('order_id'),  # OK
        'status': message['status'],
        # REMOVE customer_name, file_paths, pricing
    }
    
    subprocess.run([
        '/usr/local/bin/agent-msg',
        'slack-mirror',
        '--payload', json.dumps(sanitized)
    ])
```

### Path Handling
**Always use absolute paths:**
```python
# CORRECT
svg_path = os.path.abspath('/root/embroidery_business_agent_system/orders/12345/artwork.svg')

# INCORRECT
svg_path = 'artwork.svg'  # Relative paths forbidden
```

## Required Files / Configs

### 1. Embroidery Conversion Tool
**Location:** `/root/embroidery_business_agent_system/tools/svg_to_embroidery/`

**Required Files:**
```
svg_to_embroidery/
├── CMakeLists.txt          # Build configuration
├── src/
│   ├── svg_parser.cpp      # Adapted from Inkscape path parsing
│   ├── stitch_generator.cpp # Stitch path generation
│   ├── pes_writer.cpp      # PES format output
│   └── main.cpp
├── tests/
│   ├── test_svg_parsing.cpp
│   ├── test_stitch_generation.cpp
│   └── fixtures/
│       ├── simple_logo.svg
│       └── expected_output.pes
└── config/
    ├── thread_palettes/
    │   ├── madeira_rayon.gpl
    │   ├── isacord.gpl
    │   └── robison_anton.gpl
    └── stitch_params.yaml
```

### 2. Thread Color Database
**Location:** `/root/embroidery_business_agent_system/data/thread_colors/`

**Format:** GIMP Palette (adapted from Inkscape palettes)
```
GIMP Palette
Name: Madeira Rayon
Columns: 3
# Thread_Code R G B Thread_Name
1001 255 255 255 White
1002 0 0 0 Black
1003 255 0 0 Red
...
```

### 3. Validation Test Suite
**Location:** `/root/embroidery_business_agent_system/tests/embroidery_validation/`

**Required Files:**
```
embroidery_validation/
├── test_svg_to_pes.py      # Adapted from cli_tests
├── test_stitch_quality.py  # Adapted from rendering_tests
├── fixtures/
│   ├── known_good/
│   │   ├── logo_001.svg
│   │   ├── logo_001.pes
│   │   └── logo_001_expected.json
│   └── regression/
│       └── issue_*.svg
└── reports/
    └── validation_report_template.html
```

### 4. Agent Configuration
**Location:** `/root/embroidery_business_agent_system/config/agents/mila.yaml`

```yaml
agent:
  name: Mila
  role: Digitizing Specialist
  skills:
    - inkscape.svg.path_parsing
    - inkscape.grid.spacing_calc
    - inkscape.test.visual_comparison
    - inkscape.color.palette_management
  
  tools:
    svg_to_embroidery: /root/embroidery_business_agent_system/tools/svg_to_embroidery/build/svg_to_embroidery
    validation_suite: /root/embroidery_business_agent_system/tests/embroidery_validation/
  
  approval_gates:
    - before_digitizing
    - color_substitution_delta_e_gt_5
    - path_deviation_gt_0_5mm
    - stitch_count_gt_100k
  
  output_formats:
    - PES
    - DST
    - EXP
  
  quality_thresholds:
    max_stitch_count: 100000
    max_thread_colors: 15
    max_jump_stitch_mm: 127
    max_path_deviation_mm: 0.5
    max_color_delta_e: 5.0
```

## Commands / Checks

### Build Embroidery Conversion Tool
```bash
# From EMBIZ root
cd /root/embroidery_business_agent_system/tools/svg_to_embroidery
mkdir -p build && cd build

cmake .. \
  -DCMAKE_BUILD_TYPE=Release \
  -DWITH_INKSCAPE_LIBS=ON \
  -DCMAKE_INSTALL_PREFIX=/usr/local \
  -G Ninja

ninja
ninja test
sudo ninja install
```

### Convert SVG to Embroidery
```bash
# Mila executes this after human approval
svg_to_embroidery \
  --input /root/embroidery_business_agent_system/orders/12345/artwork.svg \
  --output /root/embroidery_business_agent_system/orders/12345/output.pes \
  --format PES \
  --thread-palette madeira_rayon \
  --max-stitch-count 100000 \
  --validate

# Verify output exists
test -f /root/embroidery_business_agent_system/orders/12345/output.pes || echo "ERROR: Output file not created"
```

### Validate Embroidery Output
```bash
# Miranda executes this
cd /root/embroidery_business_agent_system/tests/embroidery_validation

python3 test_stitch_quality.py \
  --original /root/embroidery_business_agent_system/orders/12345/artwork.svg \
  --embroidery /root/embroidery_business_agent_system/orders/12345/output.pes \
  --report /root/embroidery_business_agent_system/orders/12345/validation_report.html

# Check exit code
if [ $? -ne 0 ]; then
  agent-msg send --channel approvals --payload '{"requires_human_review": true, "order_id": "12345"}'
fi
```

### Update Thread Color Database
```bash
# Mackenzie maintains this
cd /root/embroidery_business_agent_system/data/thread_colors

# Convert vendor CSV to GIMP palette format
python3 /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkscape/share/palettes/soc2gpl.py \
  --name "Madeira Rayon 2024" \
  vendor_colors.csv > madeira_rayon_2024.gpl

# Validate palette
python3 validate_thread_palette.py madeira_rayon_2024.gpl
```

### Run Regression Tests
```bash
# Automated CI check (Mackenzie)
cd /root/embroidery_business_agent_system/tests/embroidery_validation

# Run all regression tests
pytest test_svg_to_pes.py -v --junit-xml=results.xml

# Compare against known-good outputs
python3 compare_embroidery_outputs.py \
  --fixtures fixtures/known_good/ \
  --output-dir /tmp/test_outputs/ \
  --generate-report
```

## Security Restrictions

### 1. File System Access
**Allowed:**
- Read: `/root/embroidery_business_agent_system/orders/*/` (order-specific directories)
- Write: `/root/embroidery_business_agent_system/orders/*/` (order-specific directories)
- Read: `/root/web-archive/ai_agents_skills_library/` (knowledge base)
- Read: `/root/embroidery_business_agent_system/data/` (thread colors, templates)

**Forbidden:**
- Write to knowledge base (`/root/web-archive/`)
- Access to `/root/.ssh/`, `/root/.aws/`, `/etc/` (secrets)
- Network access (except agent bus and Slack mirror)

### 2. Customer Data Protection
**PII Handling:**
- Customer names **NEVER** in file paths (use order IDs)
- Customer emails **NEVER** in logs or Slack
- Pricing information **NEVER** in agent messages
- File paths sanitized before Slack mirroring

**Example:**
```python
# CORRECT
order_dir = f'/root/embroidery_business_agent_system/orders/{order_id}/'

# INCORRECT
order_dir = f'/root/embroidery_business_agent_system/orders/{customer_name}/'  # PII in path!
```

### 3. Secrets Management
**No secrets in:**
- Agent configuration files
- Log files
- Slack messages
- Git commits

**Secrets stored in:**
- Environment variables (loaded by systemd)
- `/root/.openclaw/secrets/` (encrypted, not in Git)

### 4. Code Execution Restrictions
**Allowed:**
- Execute pre-approved binaries (`svg_to_embroidery`, `agent-msg`)
- Run Python scripts in `/root/embroidery_business_agent_system/`
- Execute validation tests

**Forbidden:**
- Arbitrary code execution from customer uploads
- Shell command injection from user input
- Dynamic imports from untrusted sources

**Example:**
```python
# CORRECT - Sanitized input
def convert_svg(svg_path, output_path):
    if not svg_path.startswith('/root/embroidery_business_agent_system/orders/'):
        raise SecurityError("Invalid path")
    
    subprocess.run([
        '/usr/local/bin/svg_to_embroidery',
        '--input', svg_path,
        '--output', output_path
    ], check=True)

# INCORRECT - Command injection risk
def convert_svg_unsafe(svg_path):
    os.system(f'svg_to_embroidery --input {svg_path}')  # NEVER DO THIS
```

## Verification Checklist

### Pre-Digitizing Checklist (Mila)
- [ ] SVG file exists on disk (verified with `os.path.isfile()`)
- [ ] SVG is valid XML (parsed with lxml without errors)
- [ ] SVG contains at least one `<path>` element
- [ ] All paths are closed (for fill stitches) or explicitly marked as running stitches
- [ ] Color count ≤ 15 (thread color limit)
- [ ] Estimated stitch count ≤ 100,000
- [ ] Human approval received for digitizing parameters
- [ ] Thread palette selected (default: Madeira Rayon)

### Post-Digitizing Checklist (Miranda)
- [ ] Output file exists on disk (verified with `os.path.isfile()`)
- [ ] Output file is valid PES/DST/EXP format (header check)
- [ ] Stitch count within limits (≤ 100,000)
- [ ] Thread color count within limits (≤ 15)
- [ ] No jump stitches > 12.7cm
- [ ] Path deviation from original ≤ 0.5mm (95th percentile)
- [ ] Color substitutions ΔE ≤ 5.0 or human-approved
- [ ] Validation report generated
- [ ] Human approval received if any thresholds exceeded

### Pre-Customer-Contact Checklist (Any Agent)
- [ ] Message sanitized (no PII, no file paths, no pricing)
- [ ] Human approval received for message content
- [ ] Order ID referenced (not customer name)
- [ ] Attachments verified to exist on disk
- [ ] Slack mirror payload sanitized

### Build/Deploy Checklist (Mackenzie)
- [ ] All tests passing (`ninja test`)
- [ ] Regression tests passing (no deviations from known-good outputs)
- [ ] Dependencies up-to-date (libembroidery, Inkscape libs)
- [ ] Thread color database current (last updated < 6 months)
- [ ] CI pipeline green (GitLab CI)
- [ ] Binary installed to `/usr/local/bin/`
- [ ] Agent configurations updated (`/root/embroidery_business_agent_system/config/agents/`)

## Build Tasks

### Task 1: Build Embroidery Conversion Tool
**Owner:** Mackenzie  
**Frequency:** On code changes, weekly dependency updates

```bash
#!/bin/bash
# /root/embroidery_business_agent_system/scripts/build_embroidery_tools.sh

set -e

cd /root/embroidery_business_agent_system/tools/svg_to_embroidery

# Clean previous build
rm -rf build
mkdir build && cd build

# Configure with CMake
cmake .. \
  -DCMAKE_BUILD_TYPE=Release \
  -DWITH_INKSCAPE_LIBS=ON \
  -DWITH_LIBEMBROIDERY=ON \
  -DCMAKE_INSTALL_PREFIX=/usr/local \
  -DCMAKE_C_COMPILER_LAUNCHER=ccache \
  -DCMAKE_CXX_COMPILER_LAUNCHER=ccache \
  -G Ninja

# Build
ninja -j$(nproc)

# Run tests
ninja test

# Install (requires sudo)
sudo ninja install

# Verify installation
which svg_to_embroidery || exit 1
svg_to_embroidery --version || exit 1

echo "Build complete: $(svg_to_embroidery --version)"
```

### Task 2: Update Thread Color Database
**Owner:** Mackenzie  
**Frequency:** Quarterly, or when vendor updates available

```bash
#!/bin/bash
# /root/embroidery_business_agent_system/scripts/update_thread_colors.sh

set -e

cd /root/embroidery_business_agent_system/data/thread_colors

# Backup existing palettes
tar -czf backup_$(date +%Y%m%d).tar.gz *.gpl

# Download vendor updates (example)
# wget https://vendor.com/thread_colors.csv -O madeira_rayon_new.csv

# Convert to GIMP palette format
python3 /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkscape/share/palettes/soc2gpl.py \
  --name "Madeira Rayon $(date +%Y)" \
  madeira_rayon_new.csv > madeira_rayon_$(date +%Y).gpl

# Validate palette
python3 validate_thread_palette.py madeira_rayon_$(date +%Y).gpl

# Update symlink to latest
ln -sf madeira_rayon_$(date +%Y).gpl madeira_rayon_latest.gpl

echo "Thread color database updated: $(date)"
```

### Task 3: Run Nightly Regression Tests
**Owner:** Miranda  
**Frequency:** Nightly (cron job)

```bash
#!/bin/bash
# /root/embroidery_business_agent_system/scripts/nightly_regression_tests.sh

set -e

cd /root/embroidery_business_agent_system/tests/embroidery_validation

# Run all regression tests
pytest test_svg_to_pes.py \
  test_stitch_quality.py \
  test_color_mapping.py \
  -v \
  --junit-xml=results_$(date +%Y%m%d).xml \
  --html=report_$(date +%Y%m%d).html

# Compare against known-good outputs
python3 compare_embroidery_outputs.py \
  --fixtures fixtures/known_good/ \
  --output-dir /tmp/nightly_test_outputs_$(date +%Y%m%d)/ \
  --generate-report

# Send results to agent bus
if [ $? -eq 0 ]; then
  agent-msg send --channel test-results --payload '{"status": "passed", "date": "'$(date -I)'"}'
else
  agent-msg send --channel test-results --payload '{"status": "failed", "date": "'$(date -I)'", "requires_review": true}'
fi
```

### Task 4: Sync Inkscape Knowledge Base
**Owner:** Mackenzie  
**Frequency:** Weekly

```bash
#!/bin/bash
# /root/embroidery_business_agent_system/scripts/sync_inkscape_knowledge.sh

set -e

cd /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkscape

# Pull latest changes
git fetch origin
git pull --recurse-submodules

# Update submodules
git submodule update --recursive --remote

# Re-index skills
python3 /root/embroidery_business_agent_system/scripts/index_skills.py \
  --source /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkscape \
  --output /root/.openclaw/workspace/skills/inkscape/

echo "Inkscape knowledge base synced: $(git log -1 --format=%cd)"
```

## What Not To Use

### 1. GUI Components
**Do NOT use:**
- Inkscape's GTK-based UI code (`src/ui/`, dialog implementations)
- Interactive tools (selection tool, node tool, etc.)
- On-canvas editing features
- Preferences dialogs

**Reason:** EMBIZ is a headless, automated system. GUI code adds unnecessary dependencies and complexity.

**Use instead:** Command-line tools, Python scripts, headless rendering

### 2. Inkscape Extensions System
**Do NOT use:**
- Extension plugin architecture (`src/extension/`)
- Python-based Inkscape extensions
- Extension dependency management

**Reason:** Extensions are designed for interactive use within Inkscape. EMBIZ needs standalone, scriptable tools.

**Use instead:** Standalone Python scripts adapted from extension logic

### 3. Interactive Snapping
**Do NOT use:**
- On-canvas snapping logic (`src/ui/tools/`, snap indicators)
- Snap popover dialog
- Interactive alignment guides

**Reason:** Snapping is for manual editing. EMBIZ uses algorithmic stitch placement.

**Use instead:** Grid-based stitch density calculations (adapted from `libgrid2`)

### 4. Live Path Effects (LPEs)
**Do NOT use:**
- LPE system (`src/live_effects/`)
- Interactive LPE editing
- LPE test framework (except for path comparison algorithms)

**Reason:** LPEs are for interactive design. EMBIZ needs deterministic, batch-processable path operations.

**Use instead:** Direct path manipulation algorithms (boolean ops, simplification)

### 5. Inkscape's Build System (for EMBIZ tools)
**Do NOT use:**
- Full Inkscape CMake build (too complex, too many dependencies)
- Inkscape's packaging scripts (AppImage, Snap, etc.)

**Reason:** EMBIZ tools are lightweight, standalone binaries. Full Inkscape build is overkill.

**Use instead:** Minimal CMake configuration linking only required Inkscape libraries (path parsing, SVG I/O)

### 6. Localization (i18n) Infrastructure
**Do NOT use:**
- Inkscape's translation system (`po/`, `share/*/i18n.py`)
- Gettext integration
- Localized UI strings

**Reason:** EMBIZ agents operate in English. Customer-facing messages are templated and human-approved.

**Use instead:** Simple English strings in code, templated customer messages

### 7. Multi-Page Document Handling
**Do NOT use:**
- Page tool logic
- Multi-page PDF export
- Page management UI

**