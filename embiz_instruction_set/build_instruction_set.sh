#!/usr/bin/env bash
# =============================================================================
# build_instruction_set.sh
# The single command that (re)constructs every folder, file, and step of the
# EMBIZ deterministic instruction-set system, then verifies it end-to-end.
#
# Design note (BRD "Large Heredoc Command Risk", P11): the heavy content lives in
# version-controlled files, NOT in giant inline heredocs. This script only creates
# directories, runs the data-driven step generator, and self-tests. That is the
# BRD-prescribed mitigation: "Break large implementations into smaller scripts.
# Use Git for large files. Run py_compile before restarting services."
# =============================================================================
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

echo "[1/6] Creating directory scaffold..."
mkdir -p authority business_requirements engine bin contracts manifest recovery \
         validators state evidence logs artifacts
mkdir -p workflows/{00_bootstrap_environment,01_knowledge_library,02_intake,\
03_raster_analysis,04_vectorization_ihive,05_vector_validation,06_stitch_planning,\
07_stitch_validation,08_production_export,09_production_tracking,10_slack_collaboration,\
11_infrastructure_multicloud,12_agent_orchestration,13_dashboard_observability,\
14_qa_continuous_improvement,15_production_readiness}
touch evidence/.gitkeep logs/.gitkeep artifacts/.gitkeep

echo "[2/6] Preflight: compiling engine modules (py_compile)..."
python3 -m py_compile engine/*.py validators/*.py

echo "[3/6] Generating all step files + manifest + traceability..."
python3 engine/generate_steps.py

echo "[4/6] Initializing durable state..."
python3 engine/supervisor.py --init

echo "[5/6] Self-test: verify routing + guards + recovery + hash chain..."
python3 validators/selftest.py

echo "[6/6] Status:"
python3 engine/supervisor.py --status

echo
echo "DONE. Entry point: BEGIN_HERE.md"
echo "Steps live under workflows/ and recovery/. Routing authority: manifest/steps_index.json"
echo "BRD coverage: REQUIREMENTS_TRACEABILITY.md"
chmod +x bin/* 2>/dev/null || true
