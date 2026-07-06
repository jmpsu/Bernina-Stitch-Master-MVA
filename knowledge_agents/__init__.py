"""Specialized vectorization knowledge agents.

Four element specialists mine the local EMBIZ library (potrace / inkscape /
inkstitch doctrine + upstream source bundles) into cited knowledge objects and
candidate parameter-strategy hypotheses, each mapped into the vectorizer's actual
vtracer parameter space (see vectorizer.py PARAM_GRID / DOCTRINE_SEED).

This is Stage-1 KNOWLEDGE EXTRACTION. No experiments are run here. The cited
knowledge objects live as JSON under:

    knowledge/vectorization/<agent>/<concept>.json

Each agent OWNS one vectorization element:

    color_agent  -- color quantization / layering / color fidelity
                    (inkscape delta_e<=5.0, HSL matching, <=15 colors;
                     -> color_precision, layer_difference, hierarchical, colormode)
    curve_agent  -- bezier curve & node smoothness/optimization
                    (potrace alphamax, opttolerance, opticurve, turnpolicy;
                     -> corner_threshold, path_precision, mode, splice_threshold,
                        length_threshold)
    noise_agent  -- speckle/noise removal & silhouette preservation
                    (potrace turdsize, mkbitmap lowpass/highpass, blacklevel;
                     -> filter_speckle + pre-tracer denoise/threshold knobs)
    edge_agent   -- edge/corner fidelity & path topology
                    (corner detection, inkscape max_path_deviation_mm<=0.5,
                     node-count/topology targets;
                     -> corner_threshold, mode, path_precision, node-count checks)

`load_agent_hypotheses()` parses the JSON artifacts and returns, per agent, the
list of candidate isolated-factor experiments the Stage-2 experiment harness will
consume. A "vtracer-real" experiment targets a param the vectorizer actually
exposes (see _VTRACER_PARAMS); others are pipeline/pre-tracer knobs or topology
checks flagged with is_vtracer_param=False so Stage 2 can filter them.
"""

from __future__ import annotations

import glob
import json
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(_HERE)
KNOWLEDGE_DIR = os.path.join(_REPO, "knowledge", "vectorization")

AGENTS = ("color_agent", "curve_agent", "noise_agent", "edge_agent")

# vtracer params the vectorizer actually exposes (mirrors vectorizer._ALLOWED /
# PARAM_GRID). A knowledge object whose param_mapping.vtracer_param is in this set
# is a directly-runnable isolated-factor experiment; anything else is a pipeline
# knob (pre-tracer denoise/threshold) or a topology check.
_VTRACER_PARAMS = frozenset({
    "colormode", "hierarchical", "mode", "filter_speckle", "color_precision",
    "layer_difference", "corner_threshold", "length_threshold",
    "splice_threshold", "path_precision",
})


def _load_agent_artifacts(agent):
    """Load and parse every knowledge-object JSON for one agent, sorted by
    filename for deterministic ordering."""
    agent_dir = os.path.join(KNOWLEDGE_DIR, agent)
    artifacts = []
    for path in sorted(glob.glob(os.path.join(agent_dir, "*.json"))):
        with open(path, "r", encoding="utf-8") as f:
            obj = json.load(f)
        obj["_source_json"] = os.path.relpath(path, _REPO)
        artifacts.append(obj)
    return artifacts


def _artifact_to_experiment(agent, obj):
    """Turn one cited knowledge object into a candidate isolated-factor
    experiment record for the Stage-2 harness."""
    pm = obj.get("param_mapping", {})
    param = pm.get("vtracer_param")
    return {
        "agent": agent,
        "element": obj.get("element"),
        "concept": obj.get("concept"),
        "param": param,
        "values": pm.get("candidate_values", []),
        "direction": pm.get("direction"),
        "source_concept": obj.get("concept"),
        "source_document": obj.get("source_document"),
        "source_json": obj.get("_source_json"),
        "hypothesis": obj.get("hypothesis"),
        "rationale": pm.get("rationale"),
        # True => param is directly settable on vtracer (runnable as-is);
        # False => pre-tracer pipeline knob or topology check, needs harness support.
        "is_vtracer_param": param in _VTRACER_PARAMS,
    }


def load_agent_hypotheses():
    """Return {agent_name: [experiment, ...]} for all four agents.

    Each experiment is a candidate isolated-factor experiment parsed from a cited
    knowledge object: param, candidate values, expected direction, source concept,
    hypothesis, and whether the param is directly runnable on vtracer. This is the
    input the Stage-2 experiment harness consumes.
    """
    out = {}
    for agent in AGENTS:
        out[agent] = [_artifact_to_experiment(agent, obj)
                      for obj in _load_agent_artifacts(agent)]
    return out


def iter_experiments():
    """Flat iterator over every candidate experiment across all agents."""
    for agent, exps in load_agent_hypotheses().items():
        for exp in exps:
            yield exp


def summary():
    """Small dict summarizing extraction: artifact/experiment counts per agent
    and how many map onto directly-runnable vtracer params."""
    hyp = load_agent_hypotheses()
    total = sum(len(v) for v in hyp.values())
    runnable = sum(1 for e in iter_experiments() if e["is_vtracer_param"])
    return {
        "agents": {a: len(hyp[a]) for a in AGENTS},
        "total_experiments": total,
        "vtracer_runnable": runnable,
        "pipeline_or_topology": total - runnable,
    }


if __name__ == "__main__":
    import pprint
    pprint.pprint(summary())
