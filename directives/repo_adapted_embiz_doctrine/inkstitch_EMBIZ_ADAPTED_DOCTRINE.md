# inkstitch EMBIZ ADAPTED DOCTRINE

## Source Material Read

**Repository:** inkstitch  
**Local Path:** `/root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkstitch`  
**Bundle:** `inkstitch_SOURCE_BUNDLE.md`

**Files Analyzed:**
- `dbus/select_elements.py` - DBus integration for Inkscape element selection
- `inkstitch.py` - Main entry point with debug/profiling infrastructure
- `lib/commands.py` - Command system for embroidery operations
- `lib/debug/` - Debug, logging, profiler infrastructure
- `lib/elements/` - Core embroidery element types (Fill, Satin, Stroke, Clone, Text, Image)
- `lib/elements/utils/` - Node iteration, stroke-to-satin conversion
- `lib/elements/validation.py` - Validation warnings/errors
- `lib/exceptions.py` - Exception handling and bug reporting
- `lib/extensions/` - 60+ Inkscape extensions (lettering, output, params, simulator, etc.)

**Core Architecture Identified:**
- Inkscape extension framework (inkex-based)
- SVG path → embroidery stitch conversion pipeline
- Element types: FillStitch, SatinColumn, Stroke, Clone, Text, Image
- Command system for machine control (trim, stop, jump)
- Thread/palette management
- Stitch plan generation and caching
- Multi-format output (PES, DST, EXP, etc.)

## What This Repo Contributes To EMBIZ

**Digitizing Intelligence:**
- **Path-to-stitch algorithms** for fill, satin, running stitch, ripple, zigzag, cross-stitch
- **Auto-routing** and jump stitch optimization
- **Underlay/overlay** generation
- **Density calculation** and stitch spacing
- **Validation rules** for embroiderable vs. non-embroiderable elements

**File Format Knowledge:**
- **Input:** SVG with inkstitch metadata
- **Output:** PES, DST, EXP, JEF, VP3, U01, and 20+ other formats via pyembroidery
- **Thread catalogs:** Madeira, Sulky, Robison-Anton, etc.

**Operational Patterns:**
- **Extension-based workflow:** Each operation is a discrete extension
- **Stitch plan caching:** Avoid re-digitizing unchanged elements
- **Command insertion:** Machine control commands embedded in SVG
- **Lettering system:** Font-based text-to-stitch with kerning

**Quality Control:**
- **Validation warnings:** Small fills, unconnected shapes, border crossings
- **Simulation:** Visual preview before stitching
- **Realistic rendering:** Thread texture and fabric interaction preview

## EMBIZ-Specific Adaptation

### 1. **Digitizing Pre-Flight Checks**
**Rule:** Never claim a design is digitized until validation passes.

```python
# Adapted from lib/elements/validation.py
EMBIZ_VALIDATION_GATES = {
    'small_fill': 'Flag for human review',
    'unconnected_shapes': 'Auto-break or human decision',
    'border_cross': 'Require manual path cleanup',
    'narrow_satin': 'Convert to running stitch or reject',
    'text_object': 'Require lettering tool or manual trace'
}
```

**Agent Responsibility:** Mila (Quality Control)
- Run validation before claiming "ready to stitch"
- Generate validation report with inkstitch's built-in checks
- Never auto-approve designs with ValidationError (only ValidationWarning with human review)

### 2. **File Existence Verification**
**Rule:** Never claim SVG/PES/DST exists unless verified on disk.

```bash
# Pre-digitizing check
if [ ! -f "$SVG_PATH" ]; then
    agent-msg --to maya --error "SVG not found: $SVG_PATH"
    exit 1
fi

# Post-digitizing check
if [ ! -f "$OUTPUT_PES" ]; then
    agent-msg --to maya --error "PES generation failed"
    exit 1
fi
```

**Agent Responsibility:** Madeline (File Operations)
- Verify input SVG exists before calling inkstitch
- Verify output embroidery file exists after generation
- Log file sizes and checksums

### 3. **Human Approval Gates**
**Rule:** Human approval required before:
1. Generating final embroidery files for customer
2. Claiming a design is "production-ready"
3. Sending any file to customer

```python
# Adapted workflow
def digitize_for_customer(svg_path, customer_id):
    # 1. Generate stitch plan
    stitch_plan = inkstitch_generate(svg_path)
    
    # 2. Run validation
    warnings = inkstitch_validate(svg_path)
    
    # 3. STOP - Human approval required
    approval_request = {
        'svg': svg_path,
        'warnings': warnings,
        'stitch_count': stitch_plan.num_stitches,
        'customer': customer_id
    }
    agent_msg('maya', 'APPROVAL_REQUIRED', approval_request)
    
    # 4. Wait for approval (blocking)
    if not wait_for_human_approval():
        return None
    
    # 5. Generate final files
    return inkstitch_output(svg_path, formats=['pes', 'dst'])
```

**Agent Responsibility:** Maya (Customer Relations)
- Never send files without human approval
- Present validation warnings to human
- Log approval timestamp and approver

### 4. **Inkstitch Extension Invocation**
**Adapted from inkstitch.py:**

```bash
#!/bin/bash
# EMBIZ wrapper for inkstitch extensions

INKSTITCH_ROOT="/root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkstitch"
SVG_INPUT="$1"
EXTENSION="$2"  # e.g., "params", "output", "simulator"

# Verify SVG exists
if [ ! -f "$SVG_INPUT" ]; then
    echo "ERROR: SVG not found: $SVG_INPUT" >&2
    exit 1
fi

# Set environment
export PYTHONPATH="$INKSTITCH_ROOT:$PYTHONPATH"
export INKSTITCH_OFFLINE_SCRIPT="True"

# Run extension
python3 "$INKSTITCH_ROOT/inkstitch.py" \
    --extension="$EXTENSION" \
    "$SVG_INPUT" \
    "$@"

# Verify output (extension-specific)
if [ "$EXTENSION" = "output" ]; then
    OUTPUT_DIR=$(dirname "$SVG_INPUT")
    if [ ! -f "$OUTPUT_DIR"/*.pes ]; then
        echo "ERROR: PES file not generated" >&2
        exit 1
    fi
fi
```

### 5. **Thread Palette Management**
**Adapted from lib/threads.py and extensions/apply_palette.py:**

```python
# EMBIZ thread inventory integration
from lib.threads import ThreadCatalog

def get_available_threads():
    """Query EMBIZ inventory for available thread colors"""
    catalog = ThreadCatalog()
    # Filter by what's actually in stock
    inventory = query_embiz_inventory()
    return [t for t in catalog.get_all_threads() 
            if t.number in inventory]

def validate_thread_availability(svg_path):
    """Ensure all colors in design are in stock"""
    design_colors = extract_colors_from_svg(svg_path)
    available = get_available_threads()
    
    missing = []
    for color in design_colors:
        if not find_nearest_available(color, available):
            missing.append(color)
    
    if missing:
        agent_msg('maya', 'THREAD_SHORTAGE', {
            'colors': missing,
            'design': svg_path
        })
        return False
    return True
```

**Agent Responsibility:** Mackenzie (Inventory)
- Verify thread availability before digitizing
- Suggest substitutions for out-of-stock colors
- Update thread catalog when new spools arrive

### 6. **Stitch Count Estimation**
**Adapted from lib/stitch_plan/:**

```python
def estimate_production_time(svg_path):
    """Estimate machine time for a design"""
    # Generate stitch plan (cached if unchanged)
    stitch_plan = inkstitch_generate_plan(svg_path)
    
    stitch_count = stitch_plan.num_stitches
    color_changes = stitch_plan.num_colors
    
    # EMBIZ machine specs
    STITCHES_PER_MINUTE = 800
    COLOR_CHANGE_MINUTES = 2
    
    stitch_time = stitch_count / STITCHES_PER_MINUTE
    color_time = color_changes * COLOR_CHANGE_MINUTES
    
    total_minutes = stitch_time + color_time
    
    return {
        'stitches': stitch_count,
        'colors': color_changes,
        'estimated_minutes': total_minutes,
        'machine_hours': total_minutes / 60
    }
```

**Agent Responsibility:** Melanie (Production Planning)
- Estimate time before quoting customer
- Schedule machine time based on stitch counts
- Track actual vs. estimated for calibration

## Assigned Agent Ownership

| Agent | Responsibility | Inkstitch Integration |
|-------|---------------|----------------------|
| **Maya** | Customer Relations | Approval gates, validation reports to customer |
| **Madeline** | File Operations | SVG/PES/DST verification, file I/O |
| **Morgan** | Order Management | Stitch count → pricing, production scheduling |
| **Mila** | Quality Control | Run inkstitch validation, flag warnings |
| **Melanie** | Production Planning | Time estimation, machine scheduling |
| **Mackenzie** | Inventory | Thread availability, palette management |
| **Marina** | Digitizing | Invoke inkstitch extensions, parameter tuning |
| **Monica** | Design Review | Simulation preview, visual QA |
| **Meredith** | Documentation | Log digitizing parameters, stitch plans |
| **Mckenna** | Testing | Run test swatches, validate output formats |

## Local Skill / Knowledge Library Integration

**Corpus Location:** `/root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkstitch`

**Knowledge Extraction:**
```bash
# Index inkstitch documentation
/root/embroidery_business_agent_system/scripts/index_inkstitch_knowledge.sh

# Generates:
# - Element type reference (fill, satin, stroke)
# - Parameter documentation (all @param decorators)
# - Validation rule catalog
# - Extension usage examples
```

**Agent Query Pattern:**
```python
# Marina needs to know satin column parameters
knowledge = query_corpus(
    path="/0-platform-precursor-systems/imported/inkstitch/lib/elements/satin_column.py",
    query="What parameters control satin column density?"
)
# Returns: zigzag_spacing_mm, pull_compensation_mm, etc.
```

## Runtime Rules

### 1. **Never Run Inkstitch Without Input Validation**
```bash
# WRONG
python3 inkstitch.py --extension=output design.svg

# RIGHT
if [ -f design.svg ] && validate_svg design.svg; then
    python3 inkstitch.py --extension=output design.svg
else
    agent-msg --to maya --error "Invalid SVG"
fi
```

### 2. **Always Capture Inkstitch Errors**
```python
# Adapted from inkstitch.py exception handling
try:
    extension.run(args=remaining_args)
except InkstitchException as exc:
    agent_msg('maya', 'DIGITIZING_ERROR', {
        'error': str(exc),
        'svg': svg_path,
        'extension': extension_name
    })
    sys.exit(1)
except Exception:
    # Uncaught exception - bug report
    bug_report = format_uncaught_exception()
    agent_msg('meredith', 'BUG_REPORT', bug_report)
    sys.exit(1)
```

### 3. **Use Stitch Plan Caching**
```python
# Inkstitch caches stitch plans to avoid re-digitizing
# EMBIZ: Leverage this for quote revisions
def quote_revision(svg_path, changes):
    # If only thread colors changed, stitch plan is cached
    if changes['type'] == 'color_only':
        # Fast path - no re-digitizing
        apply_palette(svg_path, changes['new_palette'])
    else:
        # Slow path - invalidate cache
        invalidate_stitch_cache(svg_path)
        regenerate_stitch_plan(svg_path)
```

### 4. **Respect Inkscape Environment**
```bash
# Inkstitch expects Inkscape environment variables
export DOCUMENT_PATH="/path/to/design.svg"
export INKSCAPE_PROFILE_DIR="$HOME/.config/inkscape"

# For offline (non-Inkscape) operation
export INKSTITCH_OFFLINE_SCRIPT="True"
```

### 5. **Thread Catalog Consistency**
```python
# Always use inkstitch's thread catalog as source of truth
from lib.threads import ThreadCatalog

catalog = ThreadCatalog()
# Don't maintain separate thread database
# Sync EMBIZ inventory with catalog.get_all_threads()
```

## Required Files / Configs

### 1. **DEBUG.toml** (Development Only)
```toml
# /root/embroidery_business_agent_system/config/inkstitch_debug.toml
[DEBUG]
debug_enable = false  # Never enable in production
create_bash_script = false

[LOGGING]
log_config_file = "/root/embroidery_business_agent_system/logs/inkstitch_logging.toml"
disable_logging = false

[LIBRARY]
prefer_pip_inkex = true  # Use bundled inkex
```

### 2. **Logging Config**
```toml
# /root/embroidery_business_agent_system/logs/inkstitch_logging.toml
[root]
level = "INFO"
handlers = ["file"]

[handlers.file]
class = "logging.FileHandler"
filename = "/root/embroidery_business_agent_system/logs/inkstitch.log"
formatter = "standard"

[formatters.standard]
format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

### 3. **Extension Wrapper Scripts**
```bash
# /root/embroidery_business_agent_system/bin/inkstitch-*

# inkstitch-params (view/edit parameters)
#!/bin/bash
exec /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkstitch/inkstitch.py \
    --extension=params "$@"

# inkstitch-output (generate embroidery files)
#!/bin/bash
exec /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkstitch/inkstitch.py \
    --extension=output "$@"

# inkstitch-simulate (preview)
#!/bin/bash
exec /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkstitch/inkstitch.py \
    --extension=simulator "$@"
```

## Commands / Checks

### Validation
```bash
# Run inkstitch validation on SVG
inkstitch-validate() {
    local svg="$1"
    python3 -c "
from lib.elements.utils.nodes import nodes_to_elements, iterate_nodes
from inkex import load_svg
svg = load_svg('$svg')
elements = nodes_to_elements(iterate_nodes(svg.getroot()))
for elem in elements:
    for warning in elem.validation_warnings():
        print(f'{warning.name}: {warning.description}')
"
}

# Check if SVG is embroiderable
is_embroiderable() {
    local svg="$1"
    inkstitch-validate "$svg" | grep -q "ValidationError" && return 1
    return 0
}
```

### Stitch Count
```bash
# Get stitch count without generating files
stitch_count() {
    local svg="$1"
    python3 -c "
from lib.stitch_plan import stitch_groups_to_stitch_plan
from lib.elements.utils.nodes import nodes_to_elements, iterate_nodes
from inkex import load_svg
svg = load_svg('$svg')
elements = nodes_to_elements(iterate_nodes(svg.getroot()))
plan = stitch_groups_to_stitch_plan(elements)
print(plan.num_stitches)
"
}
```

### Thread List
```bash
# Extract thread colors from SVG
thread_list() {
    local svg="$1"
    python3 -c "
from lib.elements.utils.nodes import nodes_to_elements, iterate_nodes
from inkex import load_svg
svg = load_svg('$svg')
elements = nodes_to_elements(iterate_nodes(svg.getroot()))
colors = set(elem.color for elem in elements if hasattr(elem, 'color'))
for color in colors:
    print(color)
"
}
```

### Format Conversion
```bash
# Generate PES from SVG
svg_to_pes() {
    local svg="$1"
    local output="${svg%.svg}.pes"
    
    inkstitch-output \
        --format=pes \
        --output="$output" \
        "$svg"
    
    [ -f "$output" ] && echo "$output" || return 1
}

# Generate multiple formats
svg_to_all_formats() {
    local svg="$1"
    for fmt in pes dst exp jef; do
        svg_to_$fmt "$svg" || agent-msg --to maya --error "Failed: $fmt"
    done
}
```

## Security Restrictions

### 1. **No Arbitrary Code Execution**
```python
# NEVER allow user-supplied Python in inkstitch context
# Inkstitch extensions are safe (no eval/exec)
# But custom patterns/fonts must be sandboxed
```

### 2. **File Path Validation**
```python
def safe_svg_path(path):
    """Ensure SVG path is within allowed directories"""
    allowed = [
        '/root/embroidery_business_agent_system/designs',
        '/root/.openclaw/workspace'
    ]
    real_path = os.path.realpath(path)
    if not any(real_path.startswith(a) for a in allowed):
        raise SecurityError(f"Path outside allowed dirs: {path}")
    return real_path
```

### 3. **No Network Access**
```bash
# Inkstitch should never make network requests
# If it does, block with firewall rule
iptables -A OUTPUT -m owner --uid-owner inkstitch -j REJECT
```

### 4. **Secrets Isolation**
```bash
# Never pass customer data to inkstitch logs
# Sanitize SVG metadata before processing
strip_customer_metadata() {
    local svg="$1"
    xmlstarlet ed -d "//svg:metadata[@id='customer-info']" "$svg"
}
```

## Verification Checklist

**Before Digitizing:**
- [ ] SVG file exists on disk (`[ -f "$SVG_PATH" ]`)
- [ ] SVG is valid XML (`xmllint --noout "$SVG_PATH"`)
- [ ] SVG contains embroiderable elements (`inkstitch-validate`)
- [ ] Thread colors are in stock (`validate_thread_availability`)
- [ ] Customer approval obtained (if final output)

**After Digitizing:**
- [ ] Output file exists (`[ -f "$OUTPUT_PES" ]`)
- [ ] Output file size > 0 (`[ -s "$OUTPUT_PES" ]`)
- [ ] Stitch count matches estimate (±10%)
- [ ] No validation errors in log
- [ ] Thread list matches design

**Before Customer Delivery:**
- [ ] Human reviewed simulation
- [ ] Test swatch approved (if new design)
- [ ] File format matches customer machine
- [ ] Thread list included
- [ ] Production time estimated

## Build Tasks

### 1. **Index Inkstitch Knowledge**
```bash
# /root/embroidery_business_agent_system/scripts/index_inkstitch_knowledge.sh
#!/bin/bash
INKSTITCH_ROOT="/root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkstitch"
OUTPUT="/root/embroidery_business_agent_system/knowledge/inkstitch_index.json"

python3 << 'EOF'
import json
import ast
from pathlib import Path

def extract_params(file_path):
    """Extract @param decorators from Python files"""
    with open(file_path) as f:
        tree = ast.parse(f.read())
    
    params = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call) and decorator.func.id == 'param':
                    params.append({
                        'name': decorator.args[0].s,
                        'description': decorator.args[1].s,
                        'file': str(file_path)
                    })
    return params

inkstitch_root = Path("$INKSTITCH_ROOT")
all_params = []
for py_file in inkstitch_root.rglob("*.py"):
    all_params.extend(extract_params(py_file))

with open("$OUTPUT", 'w') as f:
    json.dump(all_params, f, indent=2)
EOF
```

### 2. **Generate Extension Wrappers**
```bash
# Auto-generate wrapper scripts for all extensions
for ext in params output simulator lettering auto_satin; do
    cat > "/root/embroidery_business_agent_system/bin/inkstitch-$ext" << EOF
#!/bin/bash
exec /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkstitch/inkstitch.py \\
    --extension=$ext "\$@"
EOF
    chmod +x "/root/embroidery_business_agent_system/bin/inkstitch-$ext"
done
```

### 3. **Thread Catalog Sync**
```bash
# Sync inkstitch thread catalog to EMBIZ inventory database
python3 << 'EOF'
from lib.threads import ThreadCatalog
import sqlite3

catalog = ThreadCatalog()
conn = sqlite3.connect('/root/embroidery_business_agent_system/data/inventory.db')

for thread in catalog.get_all_threads():
    conn.execute('''
        INSERT OR REPLACE INTO threads (brand, number, name, hex_color)
        VALUES (?, ?, ?, ?)
    ''', (thread.brand, thread.number, thread.name, thread.hex))

conn.commit()
EOF
```

## What Not To Use

### 1. **GUI Extensions (Require X11)**
- `lib/gui/*` - All GUI apps (About, Simulator, Lettering dialogs)
- **Reason:** EMBIZ runs headless
- **Alternative:** Use CLI extensions or generate previews as PNG

### 2. **Inkscape-Specific Features**
- `dbus/select_elements.py` - Requires running Inkscape
- **Reason:** EMBIZ processes SVGs offline
- **Alternative:** Manipulate SVG directly with lxml

### 3. **Interactive Debugging**
- `lib/debug/debugger.py` - VSCode/PyCharm remote debugging
- **Reason:** Production environment
- **Alternative:** Use logging only

### 4. **Experimental Features**
- `lib/stitches/meander_fill.py` - Marked as experimental
- `lib/stitches/tartan_fill.py` - Complex, may have edge cases
- **Reason:** Stability for customer orders
- **Alternative:** Stick to tatami_fill, contour_fill, satin_column

### 5. **Font Generation**
- `lib/extensions/letters_to_font.py` - Creates new fonts
- **Reason:** Not needed for production
- **Alternative:** Use pre-made fonts from inkstitch library

## Integration Status

**Status:** ✅ **ADAPTED - READY FOR AGENT USE**

**Completed:**
- [x] Source material analyzed
- [x] EMBIZ-specific rules defined
- [x] Agent ownership assigned
- [x] Validation gates documented
- [x] File verification protocols established
- [x] Human approval workflows defined
- [x] Command wrappers specified
- [x] Security restrictions documented

**Pending:**
- [ ] Build wrapper scripts (`/root/embroidery_business_agent_system/bin/inkstitch-*`)
- [ ] Index knowledge base (`scripts/index_inkstitch_knowledge.sh`)
- [ ] Sync thread catalog to inventory DB
- [ ] Test validation pipeline with sample SVGs
- [ ] Train agents on inkstitch parameter meanings
- [ ] Create test suite for format conversions

**Next Steps:**
1. **Madeline:** Create wrapper scripts and test file I/O
2. **Marina:** Test digitizing pipeline with 5 sample designs
3. **Mila:** Run validation on existing design library
4. **Mackenzie:** Sync thread catalog to inventory
5. **Maya:** Define approval workflow in Slack

**Integration Points:**
- **Agent Bus:** `/usr/local/bin/agent-msg` for error reporting
- **OpenClaw:** `/root/.openclaw/workspace` for design staging
- **Slack:** Outbound-only notifications for approvals
- **Inventory DB:** Thread availability checks

**Risk Mitigation:**
- **Never claim file exists without disk check** → Prevents customer disappointment
- **Human approval before delivery** → Prevents quality issues
- **Validation before digitizing** → Prevents wasted machine time
- **Thread availability check** → Prevents production delays

---

**This doctrine is now the authoritative guide for all EMBIZ agents interacting with inkstitch digitizing capabilities.**