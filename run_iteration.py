#!/usr/bin/env python3
"""Closed-loop optimization runner for Bernina Stitch Master.

Discovers the SVG/PES corpus, measures every artifact with metrics.py,
computes honest sub-scores and a weighted OVERALL_SCORE, and writes a full
report plus append-only ledgers for the learning loop.

Usage:
    TEST_BATCH_SIZE=ALL python3 run_iteration.py
    TEST_BATCH_SIZE=2   python3 run_iteration.py
"""

import glob
import json
import os
import time
from datetime import datetime, timezone

import metrics

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
VECTOR_DIR = os.path.join(REPO_ROOT, "vector_source")
STITCH_DIR = os.path.join(REPO_ROOT, "stitch_files")
REPORTS_DIR = os.path.join(REPO_ROOT, "reports")
WEIGHTS_PATH = os.path.join(REPO_ROOT, "weights.json")

OBSERVATIONS = os.path.join(REPO_ROOT, "observations.jsonl")
DECISION_TRACE = os.path.join(REPO_ROOT, "decision_trace.jsonl")
REWARD_LEDGER = os.path.join(REPO_ROOT, "reward_penalty_ledger.jsonl")
PARAM_INDEX = os.path.join(REPO_ROOT, "parameter_correlation_index.json")

# Sane embroidery stitch-density window (stitches per cm^2). Densities inside
# this band are considered "good" for embroidery_suitability scoring.
DENSITY_MIN = 40.0
DENSITY_MAX = 120.0


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def load_weights():
    with open(WEIGHTS_PATH) as f:
        return json.load(f)


def resolve_batch_size():
    raw = os.environ.get("TEST_BATCH_SIZE", "ALL").strip()
    if raw.upper() == "ALL":
        return None
    try:
        n = int(raw)
        return n if n > 0 else None
    except ValueError:
        return None


def discover(batch_size):
    svgs = sorted(glob.glob(os.path.join(VECTOR_DIR, "*.svg")))
    pess = sorted(glob.glob(os.path.join(STITCH_DIR, "*.pes")))
    if batch_size is not None:
        svgs = svgs[:batch_size]
        pess = pess[:batch_size]
    return svgs, pess


def next_iteration_number():
    os.makedirs(REPORTS_DIR, exist_ok=True)
    existing = glob.glob(os.path.join(REPORTS_DIR, "iteration_*.json"))
    nums = []
    for p in existing:
        base = os.path.basename(p)
        stem = base[len("iteration_"):-len(".json")]
        try:
            nums.append(int(stem))
        except ValueError:
            continue
    return (max(nums) + 1) if nums else 1


def measure_all(svgs, pess):
    """Measure every file, recording per-file runtime via perf_counter."""
    records = []
    for path in svgs:
        t0 = time.perf_counter()
        m = metrics.svg_metrics(path)
        m["runtime_s"] = round(time.perf_counter() - t0, 6)
        m["path"] = os.path.relpath(path, REPO_ROOT)
        records.append(m)
    for path in pess:
        t0 = time.perf_counter()
        m = metrics.pes_metrics(path)
        m["runtime_s"] = round(time.perf_counter() - t0, 6)
        m["path"] = os.path.relpath(path, REPO_ROOT)
        records.append(m)
    return records


def clamp01(x):
    return max(0.0, min(1.0, x))


def score_topology(records):
    """Topology quality from SVG validity + reasonable node/path ratios.

    A healthy traced vector has multiple nodes per path (not 1-2). We reward
    paths whose average node count sits in a sensible band [3, 200] and that
    parse as valid SVG. Score is the mean per-SVG sub-score.
    """
    svgs = [r for r in records if r.get("kind") == "svg"]
    if not svgs:
        return None, "no SVG artifacts"
    per = []
    for r in svgs:
        if not r.get("valid"):
            per.append(0.0)
            continue
        paths = r.get("path_count", 0)
        nodes = r.get("node_count", 0)
        if paths <= 0:
            per.append(0.0)
            continue
        ratio = nodes / paths
        # Triangular preference centered around a rich-but-not-absurd ratio.
        if ratio < 3:
            sub = clamp01(ratio / 3.0)
        elif ratio <= 200:
            sub = 1.0
        else:
            sub = clamp01(1.0 - (ratio - 200) / 800.0)
        per.append(sub)
    val = sum(per) / len(per)
    note = "mean over %d SVGs of validity*node-per-path-band score" % len(svgs)
    return val, note


def score_embroidery(records):
    """Embroidery suitability from stitch density landing in [40,120] st/cm2."""
    pess = [r for r in records if r.get("kind") == "pes" and r.get("valid")]
    if not pess:
        return None, "no valid PES artifacts"
    per = []
    for r in pess:
        d = r.get("stitch_density_per_cm2", 0.0)
        if d <= 0:
            per.append(0.0)
        elif DENSITY_MIN <= d <= DENSITY_MAX:
            per.append(1.0)
        elif d < DENSITY_MIN:
            per.append(clamp01(d / DENSITY_MIN))
        else:  # d > DENSITY_MAX
            per.append(clamp01(1.0 - (d - DENSITY_MAX) / DENSITY_MAX))
    val = sum(per) / len(per)
    note = "mean over %d PES of density-in-[%g,%g]st/cm2 score" % (
        len(pess), DENSITY_MIN, DENSITY_MAX)
    return val, note


def score_performance(records):
    """Performance from total measurement runtime. Faster -> higher.

    Baseline reference: 2.0s budget for the whole batch. Score linearly
    degrades past the budget.
    """
    total_runtime = sum(r.get("runtime_s", 0.0) for r in records)
    budget = 2.0
    val = clamp01(1.0 - (total_runtime / budget)) if total_runtime > 0 else 1.0
    note = "1 - total_runtime(%.4fs)/budget(%.1fs)" % (total_runtime, budget)
    return val, note, total_runtime


def score_reliability(records):
    """Code reliability from the fraction of files measured without error."""
    if not records:
        return None, "no records"
    ok = sum(1 for r in records if r.get("valid") and "error" not in r)
    val = ok / len(records)
    note = "%d/%d files measured without error" % (ok, len(records))
    return val, note


def compute_overall(records, weights):
    """Compute sub-scores and renormalized weighted OVERALL_SCORE.

    visual_similarity is UNAVAILABLE this iteration (no reference raster images
    in reference_images/), so it is recorded as null and its weight is dropped.
    The remaining weights are renormalized to sum to 1.0 over the available
    sub-scores.
    """
    topo, topo_note = score_topology(records)
    emb, emb_note = score_embroidery(records)
    perf, perf_note, total_runtime = score_performance(records)
    rel, rel_note = score_reliability(records)

    subscores = {
        "visual_similarity": None,
        "topology_quality": topo,
        "embroidery_suitability": emb,
        "performance": perf,
        "code_reliability": rel,
    }
    notes = {
        "visual_similarity": "UNAVAILABLE: requires reference raster images in "
                             "reference_images/ (none present this iteration). "
                             "Not fabricated; marked null and weight renormalized.",
        "topology_quality": topo_note,
        "embroidery_suitability": emb_note,
        "performance": perf_note,
        "code_reliability": rel_note,
    }

    # Renormalize weights over the dimensions that have a non-null score.
    available = {k: weights[k] for k, v in subscores.items() if v is not None}
    weight_sum = sum(available.values())
    renorm = {k: (w / weight_sum) for k, w in available.items()} if weight_sum else {}

    overall = sum(renorm[k] * subscores[k] for k in renorm)

    renorm_explanation = (
        "Original weights summed to %.2f including visual_similarity=%.2f. "
        "visual_similarity is null (no reference images), so its weight was "
        "dropped and the remaining weights (%s) were divided by their sum "
        "%.2f to renormalize to 1.0. Renormalized weights: %s." % (
            sum(weights.values()),
            weights["visual_similarity"],
            ", ".join("%s=%.2f" % (k, available[k]) for k in available),
            weight_sum,
            ", ".join("%s=%.4f" % (k, renorm[k]) for k in renorm),
        )
    )

    return {
        "subscores": subscores,
        "subscore_notes": notes,
        "original_weights": weights,
        "renormalized_weights": renorm,
        "overall_score": round(overall, 6),
        "renormalization_explanation": renorm_explanation,
        "total_runtime_s": round(total_runtime, 6),
    }


def append_jsonl(path, record):
    with open(path, "a") as f:
        f.write(json.dumps(record) + "\n")


def write_reports(iteration, records, scoring, ts):
    os.makedirs(REPORTS_DIR, exist_ok=True)
    json_path = os.path.join(REPORTS_DIR, "iteration_%d.json" % iteration)
    md_path = os.path.join(REPORTS_DIR, "iteration_%d.md" % iteration)

    report = {
        "iteration": iteration,
        "timestamp": ts,
        "artifact_count": len(records),
        "artifacts": records,
        "scoring": scoring,
    }
    with open(json_path, "w") as f:
        json.dump(report, f, indent=2)

    # Markdown
    lines = []
    lines.append("# Iteration %d Report" % iteration)
    lines.append("")
    lines.append("- Timestamp: `%s`" % ts)
    lines.append("- Artifacts measured: **%d**" % len(records))
    lines.append("- **OVERALL_SCORE: %.4f**" % scoring["overall_score"])
    lines.append("")
    lines.append("## Sub-scores")
    lines.append("")
    lines.append("| Dimension | Score | Original wt | Renorm wt | Note |")
    lines.append("|---|---|---|---|---|")
    for dim in ["visual_similarity", "topology_quality",
                "embroidery_suitability", "performance", "code_reliability"]:
        sc = scoring["subscores"][dim]
        sc_str = "null" if sc is None else "%.4f" % sc
        ow = scoring["original_weights"][dim]
        rw = scoring["renormalized_weights"].get(dim)
        rw_str = "dropped" if rw is None else "%.4f" % rw
        lines.append("| %s | %s | %.2f | %s | %s |" % (
            dim, sc_str, ow, rw_str, scoring["subscore_notes"][dim]))
    lines.append("")
    lines.append("### Renormalization")
    lines.append("")
    lines.append(scoring["renormalization_explanation"])
    lines.append("")

    # SVG table
    svgs = [r for r in records if r.get("kind") == "svg"]
    if svgs:
        lines.append("## SVG metrics")
        lines.append("")
        lines.append("| File | valid | paths | nodes | groups | elements | bytes | runtime_s |")
        lines.append("|---|---|---|---|---|---|---|---|")
        for r in svgs:
            lines.append("| %s | %s | %s | %s | %s | %s | %s | %s |" % (
                r.get("artifact"), r.get("valid"), r.get("path_count"),
                r.get("node_count"), r.get("group_count"),
                r.get("element_count"), r.get("bytes"), r.get("runtime_s")))
        lines.append("")

    # PES table
    pess = [r for r in records if r.get("kind") == "pes"]
    if pess:
        lines.append("## PES metrics")
        lines.append("")
        lines.append("| File | valid | stitches | jumps | trims | colorchg | colors | W mm | H mm | travel mm | avg st mm | density/cm2 | bytes | runtime_s |")
        lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
        for r in pess:
            lines.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
                r.get("artifact"), r.get("valid"), r.get("stitch_count"),
                r.get("jump_count"), r.get("trim_count"),
                r.get("color_change_count"), r.get("color_count"),
                r.get("width_mm"), r.get("height_mm"),
                r.get("total_travel_mm"), r.get("avg_stitch_length_mm"),
                r.get("stitch_density_per_cm2"), r.get("bytes"),
                r.get("runtime_s")))
        lines.append("")

    lines.append("## Deferred / Limitations")
    lines.append("")
    lines.append("- **visual_similarity** (SSIM / RMSE / edge-overlap) requires "
                 "reference raster images in `reference_images/`. None are present "
                 "this iteration, so this dimension is null and excluded from the "
                 "weighted score via renormalization. No SSIM value was invented.")
    lines.append("")

    with open(md_path, "w") as f:
        f.write("\n".join(lines))

    return json_path, md_path


def seed_parameter_index(iteration, ts):
    """Create or load the parameter correlation index with known seeds."""
    if os.path.exists(PARAM_INDEX):
        with open(PARAM_INDEX) as f:
            return json.load(f)
    idx = {
        "description": "Known optimization parameters and their correlation "
                       "history with OVERALL_SCORE. Correlation history is "
                       "populated as future iterations vary parameters.",
        "created_iteration": iteration,
        "created_timestamp": ts,
        "parameters": {
            "min_len_mm": {
                "value": 1.2,
                "source": "stitchscale_L3.sh",
                "unit": "mm",
                "correlation_history": []
            },
            "collapse_len_mm": {
                "value": 3.0,
                "source": "inkstitch doc default",
                "unit": "mm",
                "correlation_history": []
            },
            "min_stitch_len_mm": {
                "value": 0.25,
                "source": "inkstitch doc default",
                "unit": "mm",
                "correlation_history": []
            }
        }
    }
    with open(PARAM_INDEX, "w") as f:
        json.dump(idx, f, indent=2)
    return idx


def main():
    ts = now_iso()
    batch_size = resolve_batch_size()
    weights = load_weights()
    iteration = next_iteration_number()

    svgs, pess = discover(batch_size)
    print("Iteration %d | batch=%s | %d SVG, %d PES" % (
        iteration, batch_size if batch_size is not None else "ALL",
        len(svgs), len(pess)))

    records = measure_all(svgs, pess)
    scoring = compute_overall(records, weights)

    # Reports
    json_path, md_path = write_reports(iteration, records, scoring, ts)

    # Observations: one JSON line per measured artifact.
    for r in records:
        obs = dict(r)
        obs["iteration"] = iteration
        obs["timestamp"] = ts
        append_jsonl(OBSERVATIONS, obs)

    # Decision trace.
    append_jsonl(DECISION_TRACE, {
        "iteration": iteration,
        "timestamp": ts,
        "artifact": "decision_trace",
        "objective": "Bootstrap measurement + learning-loop infrastructure and "
                     "capture a real baseline across the SVG/PES corpus.",
        "hypothesis": "Existing corpus can be measured deterministically; the "
                      "measurable sub-scores (topology, embroidery suitability, "
                      "performance, reliability) yield a meaningful baseline "
                      "OVERALL_SCORE even though visual_similarity is unavailable.",
        "decision": "baseline-established",
        "overall_score": scoring["overall_score"],
    })

    # Reward/penalty ledger (first iteration: no prior to compare).
    append_jsonl(REWARD_LEDGER, {
        "iteration": iteration,
        "timestamp": ts,
        "artifact": "reward_penalty_ledger",
        "reward": 0,
        "penalty": 0,
        "overall_score": scoring["overall_score"],
        "previous_overall_score": None,
        "note": "baseline, no prior to compare",
    })

    # Parameter correlation index.
    seed_parameter_index(iteration, ts)

    # Console summary.
    print("OVERALL_SCORE = %.4f" % scoring["overall_score"])
    for dim, sc in scoring["subscores"].items():
        print("  %-24s %s" % (dim, "null" if sc is None else "%.4f" % sc))
    print("Reports: %s , %s" % (json_path, md_path))


if __name__ == "__main__":
    main()
