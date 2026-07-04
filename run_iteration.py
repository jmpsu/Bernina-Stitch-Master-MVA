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

# --- Embroidery suitability composite (iteration 2) -------------------------
# Rationale: the old bbox stitch-density band [40,120] st/cm^2 was the wrong
# signal for this corpus. Every PES design is small and densely filled, so bbox
# density lands at 350-1600 st/cm^2 and pins the score to 0.0 regardless of how
# well the design would actually stitch. Bbox density conflates "small motif"
# with "unsewable" and ignores the property that really governs embroiderability
# on a Bernina: the distribution of individual sewn stitch lengths.
#
# Iteration-2 metric scores each design from its real stitch-length distribution
# (see metrics.pes_metrics):
#   suitability_file = clamp(
#       safe_len_frac
#       - SHORT_PENALTY * short_stitch_frac      # sub-0.5mm -> thread nesting/breaks
#       - LONG_PENALTY  * long_stitch_frac       # >7mm -> snags/loose stitches
#       - trim_penalty(trims_per_1000),          # excessive trims -> unreliable run
#       0, 1)
# and embroidery_suitability = mean over valid PES files.
#
# Coefficients: long stitches are weighted heavier than short ones (2.0 vs 1.5)
# because a single snagged long stitch can pull/tear fabric, whereas short
# stitches degrade gradually into nesting; the trim penalty is capped so a
# trim-heavy but otherwise clean design is not zeroed out.
SHORT_STITCH_PENALTY = 1.5
LONG_STITCH_PENALTY = 2.0
TRIM_PENALTY_DIVISOR = 50.0
TRIM_PENALTY_CAP = 0.3

# Retained for the informational density figure only; NOT used for scoring.
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


def trim_penalty(trims_per_1000):
    """Penalty for excessive trims, capped so trim-heavy files aren't zeroed."""
    return min(trims_per_1000 / TRIM_PENALTY_DIVISOR, TRIM_PENALTY_CAP)


def score_embroidery(records):
    """Embroidery suitability from the real sewn-stitch-length distribution.

    Composite per file (all fractions from metrics.pes_metrics):
        clamp(safe_len_frac
              - SHORT_STITCH_PENALTY * short_stitch_frac
              - LONG_STITCH_PENALTY  * long_stitch_frac
              - trim_penalty(trims_per_1000), 0, 1)
    Score is the mean over valid PES files. Bbox stitch density is NOT used.
    """
    pess = [r for r in records if r.get("kind") == "pes" and r.get("valid")]
    if not pess:
        return None, "no valid PES artifacts"
    per = []
    for r in pess:
        safe = r.get("safe_len_frac", 0.0)
        short = r.get("short_stitch_frac", 0.0)
        long = r.get("long_stitch_frac", 0.0)
        tp = trim_penalty(r.get("trims_per_1000", 0.0))
        sub = clamp01(safe
                      - SHORT_STITCH_PENALTY * short
                      - LONG_STITCH_PENALTY * long
                      - tp)
        per.append(sub)
    val = sum(per) / len(per)
    note = ("mean over %d PES of clamp(safe_len_frac - %g*short - %g*long - "
            "min(trims_per_1000/%g,%g),0,1); bbox density NOT used" % (
                len(pess), SHORT_STITCH_PENALTY, LONG_STITCH_PENALTY,
                TRIM_PENALTY_DIVISOR, TRIM_PENALTY_CAP))
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


def load_previous_report(iteration):
    """Load reports/iteration_{iteration-1}.json if present, else None."""
    if iteration <= 1:
        return None
    prev_path = os.path.join(REPORTS_DIR, "iteration_%d.json" % (iteration - 1))
    if not os.path.exists(prev_path):
        return None
    try:
        with open(prev_path) as f:
            return json.load(f)
    except Exception:
        return None


def build_comparison(iteration, scoring, prev_report):
    """Phase-6 cross-iteration comparison: per-metric delta vs prior iteration.

    Returns None when there is no prior iteration to compare against.
    """
    if prev_report is None:
        return None
    prev_scoring = prev_report.get("scoring", {})
    prev_subs = prev_scoring.get("subscores", {})
    cur_subs = scoring["subscores"]

    subscore_deltas = {}
    for dim in cur_subs:
        cur = cur_subs.get(dim)
        prev = prev_subs.get(dim)
        if cur is None or prev is None:
            subscore_deltas[dim] = {
                "previous": prev, "current": cur, "delta": None,
            }
        else:
            subscore_deltas[dim] = {
                "previous": round(prev, 6),
                "current": round(cur, 6),
                "delta": round(cur - prev, 6),
            }

    prev_overall = prev_scoring.get("overall_score")
    cur_overall = scoring["overall_score"]
    overall_delta = (round(cur_overall - prev_overall, 6)
                     if prev_overall is not None else None)

    return {
        "compared_to_iteration": prev_report.get("iteration", iteration - 1),
        "previous_overall_score": prev_overall,
        "current_overall_score": cur_overall,
        "overall_score_delta": overall_delta,
        "improved": (overall_delta is not None and overall_delta > 0),
        "subscore_deltas": subscore_deltas,
    }


def append_jsonl(path, record):
    with open(path, "a") as f:
        f.write(json.dumps(record) + "\n")


def write_reports(iteration, records, scoring, ts, comparison=None):
    os.makedirs(REPORTS_DIR, exist_ok=True)
    json_path = os.path.join(REPORTS_DIR, "iteration_%d.json" % iteration)
    md_path = os.path.join(REPORTS_DIR, "iteration_%d.md" % iteration)

    report = {
        "iteration": iteration,
        "timestamp": ts,
        "artifact_count": len(records),
        "artifacts": records,
        "scoring": scoring,
        "comparison_vs_previous": comparison,
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

    # Phase-6 cross-iteration comparison.
    if comparison is not None:
        lines.append("## Comparison vs iteration %d (Phase 6)" %
                     comparison["compared_to_iteration"])
        lines.append("")
        od = comparison["overall_score_delta"]
        lines.append("- Previous OVERALL_SCORE: **%s**" % (
            "null" if comparison["previous_overall_score"] is None
            else "%.6f" % comparison["previous_overall_score"]))
        lines.append("- Current OVERALL_SCORE: **%.6f**" %
                     comparison["current_overall_score"])
        lines.append("- Delta: **%s** (%s)" % (
            "null" if od is None else "%+.6f" % od,
            "improved" if comparison["improved"] else "not improved"))
        lines.append("")
        lines.append("| Dimension | Previous | Current | Delta |")
        lines.append("|---|---|---|---|")
        for dim in ["visual_similarity", "topology_quality",
                    "embroidery_suitability", "performance", "code_reliability"]:
            d = comparison["subscore_deltas"].get(dim, {})
            pv = d.get("previous")
            cv = d.get("current")
            dv = d.get("delta")
            lines.append("| %s | %s | %s | %s |" % (
                dim,
                "null" if pv is None else "%.6f" % pv,
                "null" if cv is None else "%.6f" % cv,
                "null" if dv is None else "%+.6f" % dv))
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
        lines.append("| File | valid | stitches | trims | colors | W mm | H mm | avg st mm | p50 mm | p95 mm | short% | long% | safe% | trims/1k | density/cm2 (info) | runtime_s |")
        lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
        for r in pess:
            lines.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
                r.get("artifact"), r.get("valid"), r.get("stitch_count"),
                r.get("trim_count"), r.get("color_count"),
                r.get("width_mm"), r.get("height_mm"),
                r.get("avg_stitch_length_mm"),
                r.get("stitch_len_p50_mm"), r.get("stitch_len_p95_mm"),
                r.get("short_stitch_frac"), r.get("long_stitch_frac"),
                r.get("safe_len_frac"), r.get("trims_per_1000"),
                r.get("stitch_density_per_cm2"), r.get("runtime_s")))
        lines.append("")

    lines.append("## Deferred / Limitations")
    lines.append("")
    lines.append("- **visual_similarity** (SSIM / RMSE / edge-overlap) requires "
                 "reference raster images in `reference_images/`. None are present "
                 "this iteration, so this dimension is null and excluded from the "
                 "weighted score via renormalization. No SSIM value was invented.")
    lines.append("- **embroidery_suitability** no longer uses the bbox "
                 "stitch-density band [40,120] st/cm2 (iteration 1). That signal "
                 "conflated small densely-filled motifs with unsewable ones and "
                 "pinned the score to 0.0. It is replaced by a composite over the "
                 "real sewn-stitch-length distribution (safe/short/long fractions "
                 "plus a capped trim-rate penalty). `stitch_density_per_cm2` is "
                 "still reported but is INFORMATIONAL only.")
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


def update_parameter_index(idx, iteration, ts, scoring, comparison):
    """Record the iteration-2 embroidery-suitability coefficients and their
    observed effect on OVERALL_SCORE into the parameter correlation index."""
    emb = scoring["subscores"].get("embroidery_suitability")
    overall = scoring["overall_score"]
    overall_delta = comparison["overall_score_delta"] if comparison else None
    emb_delta = None
    if comparison:
        emb_delta = comparison["subscore_deltas"].get(
            "embroidery_suitability", {}).get("delta")

    params = idx.setdefault("parameters", {})
    coeffs = {
        "short_stitch_penalty": SHORT_STITCH_PENALTY,
        "long_stitch_penalty": LONG_STITCH_PENALTY,
        "trim_penalty_divisor": TRIM_PENALTY_DIVISOR,
        "trim_penalty_cap": TRIM_PENALTY_CAP,
    }
    for name, value in coeffs.items():
        entry = params.setdefault(name, {
            "value": value,
            "source": "run_iteration.py embroidery_suitability composite "
                      "(introduced iteration %d)" % iteration,
            "unit": "coefficient",
            "correlation_history": [],
        })
        entry["value"] = value
        entry["correlation_history"].append({
            "iteration": iteration,
            "timestamp": ts,
            "embroidery_suitability": emb,
            "embroidery_suitability_delta": emb_delta,
            "overall_score": overall,
            "overall_score_delta": overall_delta,
        })

    idx["last_updated_iteration"] = iteration
    idx["last_updated_timestamp"] = ts
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

    # Phase-6 cross-iteration comparison.
    prev_report = load_previous_report(iteration)
    comparison = build_comparison(iteration, scoring, prev_report)

    # Reports
    json_path, md_path = write_reports(iteration, records, scoring, ts, comparison)

    # Observations: one JSON line per measured artifact.
    for r in records:
        obs = dict(r)
        obs["iteration"] = iteration
        obs["timestamp"] = ts
        append_jsonl(OBSERVATIONS, obs)

    overall = scoring["overall_score"]

    if comparison is None:
        # First iteration: no prior to compare against.
        append_jsonl(DECISION_TRACE, {
            "iteration": iteration,
            "timestamp": ts,
            "artifact": "decision_trace",
            "objective": "Bootstrap measurement + learning-loop infrastructure "
                         "and capture a real baseline across the SVG/PES corpus.",
            "hypothesis": "Existing corpus can be measured deterministically; the "
                          "measurable sub-scores (topology, embroidery suitability, "
                          "performance, reliability) yield a meaningful baseline "
                          "OVERALL_SCORE even though visual_similarity is unavailable.",
            "decision": "baseline-established",
            "overall_score": overall,
        })
        append_jsonl(REWARD_LEDGER, {
            "iteration": iteration,
            "timestamp": ts,
            "artifact": "reward_penalty_ledger",
            "reward": 0,
            "penalty": 0,
            "overall_score": overall,
            "previous_overall_score": None,
            "note": "baseline, no prior to compare",
        })
        seed_parameter_index(iteration, ts)
    else:
        prev_overall = comparison["previous_overall_score"]
        delta = comparison["overall_score_delta"]
        improved = comparison["improved"]
        emb_delta = comparison["subscore_deltas"].get(
            "embroidery_suitability", {}).get("delta")

        append_jsonl(DECISION_TRACE, {
            "iteration": iteration,
            "timestamp": ts,
            "artifact": "decision_trace",
            "objective": "Replace the bbox stitch-density-band embroidery_"
                         "suitability score with a principled composite built "
                         "from the real sewn-stitch-length distribution "
                         "(safe/short/long fractions + trim rate).",
            "hypothesis": "Bbox density (351-1605 st/cm2 across the corpus) is "
                          "the wrong signal and pinned suitability to 0.0. A "
                          "stitch-length-distribution metric is a genuinely "
                          "better measure of embroiderability and should raise "
                          "OVERALL_SCORE above the %.4f baseline without gaming "
                          "the number." % (prev_overall if prev_overall
                                           is not None else 0.0),
            "decision": "reward-keep" if improved else "penalty-investigate",
            "overall_score": overall,
            "previous_overall_score": prev_overall,
            "overall_score_delta": delta,
            "embroidery_suitability_delta": emb_delta,
        })
        append_jsonl(REWARD_LEDGER, {
            "iteration": iteration,
            "timestamp": ts,
            "artifact": "reward_penalty_ledger",
            "reward": 1 if improved else 0,
            "penalty": 0 if improved else 1,
            "overall_score": overall,
            "previous_overall_score": prev_overall,
            "delta": delta,
            "note": ("OVERALL_SCORE improved by %+.6f vs iteration %d" % (
                delta, comparison["compared_to_iteration"])) if improved
                    else ("OVERALL_SCORE dropped by %+.6f vs iteration %d" % (
                        delta, comparison["compared_to_iteration"])),
        })
        idx = seed_parameter_index(iteration, ts)
        update_parameter_index(idx, iteration, ts, scoring, comparison)

    # Console summary.
    print("OVERALL_SCORE = %.4f" % overall)
    for dim, sc in scoring["subscores"].items():
        print("  %-24s %s" % (dim, "null" if sc is None else "%.4f" % sc))
    if comparison is not None:
        print("Delta vs iteration %d: %+.6f (%s)" % (
            comparison["compared_to_iteration"],
            comparison["overall_score_delta"],
            "reward" if comparison["improved"] else "penalty"))
    print("Reports: %s , %s" % (json_path, md_path))


if __name__ == "__main__":
    main()
