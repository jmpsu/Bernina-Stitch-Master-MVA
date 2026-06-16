# potrace EMBIZ ADAPTED DOCTRINE

## Source Material Read

Complete source bundle read from `/root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/potrace/`. This is the **Potrace** bitmap tracing library and command-line tool by Peter Selinger (GPL licensed), which converts bitmap images (PBM, PGM, BMP) into smooth vector graphics (SVG, EPS, PDF, PostScript, DXF, GeoJSON, XFig).

**Core capabilities identified:**
- Bitmap-to-vector conversion (tracing)
- Multiple input formats: PBM, PGM, PPM, BMP
- Multiple output backends: SVG, EPS, PDF, PostScript, DXF, GeoJSON, XFig, PGM
- Curve optimization (Bezier curve fitting)
- Compression support (zlib/flate, LZW)
- Path decomposition and polygon optimization
- Configurable parameters: turdsize, turnpolicy, alphamax, opttolerance

## What This Repo Contributes To EMBIZ

Potrace provides **critical bitmap-to-vector conversion** capability for the embroidery digitizing pipeline:

1. **Pre-digitizing artwork preparation**: Convert customer-supplied raster logos/artwork (PNG, JPG converted to PBM/PGM) into clean vector paths
2. **Path extraction for digitizing**: Generate smooth Bezier curves that can be analyzed for stitch path planning
3. **Quality control**: Render digitized designs back to bitmap for visual comparison
4. **Format bridging**: Convert between raster and vector representations during the design review process

**EMBIZ-specific value:**
- Enables automated logo tracing before human digitizer review
- Provides mathematical path data (curves, corners) for stitch density calculations
- Supports quality metrics (comparing source artwork to digitized output)
- Reduces manual tracing time for simple logos

## EMBIZ-Specific Adaptation

### Integration Points

1. **Input Pipeline**: Customer uploads raster logo → ImageMagick converts to PGM → Potrace generates SVG → Human reviews vector quality
2. **Digitizing Prep**: Traced SVG paths analyzed for complexity scoring (stitch count estimation)
3. **Output Validation**: Render PES/DST back to bitmap → Compare against original using pgmdiff utility
4. **Approval Workflow**: Vector preview generated for customer approval before digitizing begins

### Prohibited Uses

- **NEVER** claim potrace output is "digitized embroidery" (it's just vector tracing)
- **NEVER** bypass human digitizer approval based on potrace output
- **NEVER** use potrace output directly as stitch paths (embroidery requires specialized pathing)
- **NEVER** process customer files without explicit approval

### Required Workflow Gates

1. **Before tracing**: Verify source image exists on disk, check file format compatibility
2. **After tracing**: Human reviews SVG quality, approves for digitizing or requests re-trace with different parameters
3. **Before customer contact**: Human approves any artwork previews or complexity estimates derived from traced paths

## Assigned Agent Ownership

**Primary: Mila** (Technical Integration Specialist)
- Manages potrace binary execution and parameter tuning
- Handles format conversions (PGM input preparation, SVG output parsing)
- Monitors trace quality metrics
- Maintains potrace build and dependencies

**Secondary: Morgan** (Quality Assurance)
- Reviews traced vector output quality
- Compares traced paths against source artwork
- Validates pgmdiff results for output verification
- Documents tracing parameter recommendations per artwork type

**Tertiary: Madeline** (Customer Communication)
- Presents traced vector previews to customers (after human approval)
- Explains tracing limitations vs. digitizing
- Manages customer expectations about vector quality

## Local Skill / Knowledge Library Integration

**Location**: `/root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/potrace/`

**Knowledge artifacts to create:**

1. **`/root/embroidery_business_agent_system/knowledge/potrace_parameter_guide.md`**
   - Recommended settings per artwork type (text, logos, photos)
   - Turdsize values for noise filtering
   - Turnpolicy selection guide
   - Opttolerance tuning for curve smoothness

2. **`/root/embroidery_business_agent_system/knowledge/vector_quality_checklist.md`**
   - Visual inspection criteria for traced output
   - Common tracing artifacts and fixes
   - When to reject trace and request manual vectorization

3. **`/root/embroidery_business_agent_system/skills/trace_artwork.sh`**
   - Wrapper script for potrace execution
   - Input validation and format conversion
   - Output verification and logging

4. **`/root/embroidery_business_agent_system/skills/compare_bitmap_output.sh`**
   - Uses pgmdiff to compare rendered embroidery output against source
   - Generates quality score
   - Logs discrepancies

## Runtime Rules

### Execution Rules

1. **Always verify input file exists** before calling potrace:
   ```bash
   if [[ ! -f "$input_pgm" ]]; then
     echo "ERROR: Input file does not exist: $input_pgm" >&2
     exit 1
   fi
   ```

2. **Always specify output format explicitly**:
   ```bash
   potrace -s -o output.svg input.pgm  # SVG output
   potrace -b pdf -o output.pdf input.pgm  # PDF output
   ```

3. **Always log potrace parameters used**:
   ```bash
   echo "$(date -Iseconds) TRACE_START input=$input_pgm turdsize=$turdsize turnpolicy=$turnpolicy" >> /var/log/embiz/potrace.log
   ```

4. **Never overwrite existing traced files** without backup:
   ```bash
   if [[ -f "$output_svg" ]]; then
     mv "$output_svg" "$output_svg.$(date +%s).bak"
   fi
   ```

### Parameter Constraints

- **turdsize**: Range 2-100 (default 2). Higher values remove more noise but may lose detail.
- **turnpolicy**: `black`, `white`, `left`, `right`, `minority`, `majority`, `random` (default `minority`)
- **alphamax**: Range 0.0-1.3334 (default 1.0). Controls corner sharpness.
- **opttolerance**: Range 0.0-1.0 (default 0.2). Higher = smoother curves, fewer points.

### Quality Gates

- **Minimum input resolution**: 300 DPI for logos, 600 DPI for text
- **Maximum input size**: 10000x10000 pixels (memory constraint)
- **Trace time limit**: 60 seconds per image (timeout and log error)
- **Output validation**: SVG must parse as valid XML, contain `<path>` elements

## Required Files / Configs

### Binary Location
- **Potrace binary**: `/usr/local/bin/potrace` (or `/usr/bin/potrace` if system-installed)
- **Verify installation**: `which potrace && potrace --version`

### Configuration Files

**`/root/embroidery_business_agent_system/config/potrace_defaults.conf`**:
```ini
[defaults]
turdsize=2
turnpolicy=minority
alphamax=1.0
opttolerance=0.2
unit=10

[logo_preset]
turdsize=5
turnpolicy=majority
alphamax=0.8
opttolerance=0.3

[text_preset]
turdsize=2
turnpolicy=black
alphamax=1.2
opttolerance=0.1
```

### Working Directories

- **Input staging**: `/root/.openclaw/workspace/potrace_input/`
- **Output staging**: `/root/.openclaw/workspace/potrace_output/`
- **Logs**: `/var/log/embiz/potrace.log`
- **Backups**: `/root/.openclaw/workspace/potrace_backups/`

### Required Dependencies

- **ImageMagick**: For format conversion (PNG/JPG → PGM)
- **libpotrace**: Shared library (if using programmatic API)
- **zlib**: For compressed output formats

## Commands / Checks

### Installation Verification
```bash
# Check potrace is installed
potrace --version || echo "ERROR: potrace not installed"

# Check dependencies
convert --version | grep ImageMagick || echo "ERROR: ImageMagick missing"
ldconfig -p | grep libz || echo "ERROR: zlib missing"
```

### Basic Tracing Command
```bash
# Convert PNG to PGM, then trace to SVG
convert input.png -colorspace Gray input.pgm
potrace -s -o output.svg input.pgm

# Verify output
xmllint --noout output.svg && echo "Valid SVG" || echo "Invalid SVG"
```

### Quality Comparison
```bash
# Render SVG back to PGM (requires rsvg-convert or inkscape)
rsvg-convert -f png -o rendered.png output.svg
convert rendered.png -colorspace Gray rendered.pgm

# Compare against original
pgmdiff input.pgm rendered.pgm
# Output: numerical difference (0 = identical)
```

### Parameter Tuning Example
```bash
# High-quality logo trace
potrace -s \
  --turdsize 5 \
  --turnpolicy majority \
  --alphamax 0.8 \
  --opttolerance 0.3 \
  --unit 10 \
  -o logo_traced.svg \
  logo_input.pgm
```

### Batch Processing
```bash
# Trace all PGM files in directory
for pgm in /root/.openclaw/workspace/potrace_input/*.pgm; do
  base=$(basename "$pgm" .pgm)
  potrace -s -o "/root/.openclaw/workspace/potrace_output/${base}.svg" "$pgm"
  echo "Traced: $base"
done
```

### Health Check Script
```bash
#!/bin/bash
# /root/embroidery_business_agent_system/scripts/check_potrace.sh

echo "=== Potrace Health Check ==="
potrace --version || { echo "FAIL: potrace not found"; exit 1; }
echo "PASS: potrace installed"

test -d /root/.openclaw/workspace/potrace_input || mkdir -p /root/.openclaw/workspace/potrace_input
test -d /root/.openclaw/workspace/potrace_output || mkdir -p /root/.openclaw/workspace/potrace_output
echo "PASS: working directories exist"

convert --version | grep -q ImageMagick || { echo "WARN: ImageMagick not found"; }
echo "=== Health Check Complete ==="
```

## Security Restrictions

### Input Validation

1. **File type whitelist**: Only accept `.pbm`, `.pgm`, `.ppm`, `.bmp` files
   ```bash
   case "$input_file" in
     *.pbm|*.pgm|*.ppm|*.bmp) ;;
     *) echo "ERROR: Invalid file type"; exit 1 ;;
   esac
   ```

2. **File size limits**: Reject files >50MB
   ```bash
   max_size=$((50 * 1024 * 1024))
   file_size=$(stat -f%z "$input_file" 2>/dev/null || stat -c%s "$input_file")
   if [[ $file_size -gt $max_size ]]; then
     echo "ERROR: File too large ($file_size bytes)"
     exit 1
   fi
   ```

3. **Path traversal prevention**: Never use user-supplied paths directly
   ```bash
   # BAD: potrace -o "$user_output_path" input.pgm
   # GOOD:
   safe_name=$(basename "$user_output_path")
   potrace -o "/root/.openclaw/workspace/potrace_output/$safe_name" input.pgm
   ```

### Execution Constraints

- **Run as non-root**: Potrace should execute under `embiz` user (not root)
- **Timeout enforcement**: Use `timeout 60s potrace ...` to prevent hangs
- **Resource limits**: Set `ulimit -v 2097152` (2GB virtual memory limit)
- **No shell injection**: Never pass unsanitized user input to potrace parameters

### Output Handling

- **Sanitize SVG output**: Parse and validate XML before serving to customer
- **Strip metadata**: Remove any embedded comments or metadata from traced files
- **Watermark previews**: Add "PREVIEW - NOT FOR PRODUCTION" text to customer-facing SVGs

### Audit Trail

- **Log all executions**: Record input file, parameters, output file, timestamp, user
- **Retain source files**: Keep original uploaded artwork for 90 days
- **Version traced outputs**: Never overwrite previous traces without backup

## Verification Checklist

### Pre-Execution Checklist
- [ ] Input file exists on disk (not just claimed to exist)
- [ ] Input file format is supported (pbm/pgm/ppm/bmp)
- [ ] Input file size is within limits (<50MB)
- [ ] Output directory is writable
- [ ] Potrace binary is executable
- [ ] Required parameters are validated (turdsize, turnpolicy, etc.)

### Post-Execution Checklist
- [ ] Potrace exit code is 0 (success)
- [ ] Output file was created
- [ ] Output file is valid SVG/PDF/EPS (XML parse succeeds)
- [ ] Output file contains path data (`<path>` elements for SVG)
- [ ] Execution time was logged
- [ ] Output file was backed up if overwriting existing file

### Quality Review Checklist (Human)
- [ ] Traced paths follow source artwork accurately
- [ ] No excessive noise or artifacts
- [ ] Curves are smooth (not jaggy)
- [ ] Text is legible (if applicable)
- [ ] Corner sharpness is appropriate
- [ ] File size is reasonable (<5MB for typical logo)

### Customer Approval Checklist
- [ ] Human reviewed traced output quality
- [ ] Customer approved vector preview (if shown)
- [ ] Complexity estimate was explained (not guaranteed)
- [ ] Customer understands this is NOT final embroidery
- [ ] Approval logged in customer record

## Build Tasks

### Compile from Source (if needed)
```bash
cd /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/potrace/
./configure --prefix=/usr/local
make
sudo make install
potrace --version  # Verify installation
```

### Build Utilities
```bash
# Build pgmdiff for quality comparison
cd /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/potrace/check/
gcc -o pgmdiff pgmdiff.c ../src/greymap.c -I../src -lm
sudo cp pgmdiff /usr/local/bin/
```

### Create Wrapper Scripts
```bash
# /root/embroidery_business_agent_system/skills/trace_artwork.sh
#!/bin/bash
set -euo pipefail

input_pgm="$1"
output_svg="$2"
preset="${3:-default}"

# Load config
source /root/embroidery_business_agent_system/config/potrace_defaults.conf

# Validate input
[[ -f "$input_pgm" ]] || { echo "ERROR: Input not found"; exit 1; }

# Execute with timeout
timeout 60s potrace -s \
  --turdsize "${turdsize}" \
  --turnpolicy "${turnpolicy}" \
  --alphamax "${alphamax}" \
  --opttolerance "${opttolerance}" \
  -o "$output_svg" \
  "$input_pgm"

# Log
echo "$(date -Iseconds) TRACED input=$input_pgm output=$output_svg preset=$preset" >> /var/log/embiz/potrace.log
```

## What Not To Use

### Excluded Components

1. **Backend formats NOT used in EMBIZ**:
   - **XFig backend** (`backend_xfig.c`): Obsolete format, not relevant to embroidery
   - **GeoJSON backend** (`backend_geojson.c`): Geographic data format, no embroidery use case
   - **DXF backend** (`backend_dxf.c`): CAD format, not compatible with embroidery machines

2. **Compression features NOT needed**:
   - **LZW compression** (`lzw.c`): Only relevant for PostScript Level 2, we use SVG/PDF
   - **Flate compression** (`flate.c`): Only for PS/PDF internal compression, handled by libraries

3. **Debug/test utilities NOT for production**:
   - **checkbin** (`check/checkbin.c`): Line ending checker, development tool only
   - **pgmdiff** (`check/pgmdiff.c`): Useful for QA, but not in customer-facing workflows

### Misuse Scenarios to Avoid

- **Do NOT use potrace for stitch generation**: Traced paths are NOT stitch paths (wrong scale, no underlay, no pull compensation)
- **Do NOT use PGM backend for customer output**: PGM is raster, defeats purpose of vectorization
- **Do NOT use potrace for photo embroidery**: Photo stitch requires specialized algorithms (not simple tracing)
- **Do NOT bypass ImageMagick**: Potrace only accepts PBM/PGM/PPM/BMP, use ImageMagick for PNG/JPG conversion
- **Do NOT use `--longcoding` flag**: PostScript optimization, irrelevant for SVG output

### Deprecated/Unsafe Patterns

- **Avoid `system()` calls with user input**: Use execve() or parameterized execution
- **Avoid hardcoded paths**: Use config file for all paths
- **Avoid synchronous blocking**: Wrap potrace in async job queue for large files
- **Avoid missing error handling**: Always check potrace exit code and log failures

## Integration Status

**Current Status**: ⚠️ **INTEGRATION REQUIRED**

### Completed
- [x] Source code reviewed and understood
- [x] EMBIZ use cases identified
- [x] Agent ownership assigned
- [x] Security restrictions defined
- [x] Workflow gates documented

### In Progress
- [ ] Potrace binary installation verification
- [ ] Wrapper scripts creation (`trace_artwork.sh`, `compare_bitmap_output.sh`)
- [ ] Configuration file setup (`potrace_defaults.conf`)
- [ ] Working directory structure creation
- [ ] Logging infrastructure setup

### Pending
- [ ] Integration with customer upload pipeline (ImageMagick → Potrace → SVG preview)
- [ ] Quality comparison workflow (pgmdiff integration)
- [ ] Parameter tuning guide completion (artwork-type-specific presets)
- [ ] Agent training on potrace output review
- [ ] Customer-facing documentation (explaining vector preview vs. final embroidery)
- [ ] Automated testing (trace sample logos, verify output quality)

### Blockers
- **None identified** (potrace is mature, stable, well-documented)

### Next Steps (Priority Order)
1. **Mila**: Install potrace binary, verify dependencies, create wrapper scripts
2. **Morgan**: Define quality review checklist, test pgmdiff utility
3. **Madeline**: Draft customer communication templates for vector previews
4. **Mila**: Integrate with existing upload pipeline (add potrace step after ImageMagick conversion)
5. **All agents**: Test end-to-end workflow with sample customer artwork

---

**Doctrine Completed**: 2024-01-09  
**Last Updated**: 2024-01-09  
**Reviewed By**: System Architect (AI)  
**Approved For**: Production Integration (Pending Implementation)