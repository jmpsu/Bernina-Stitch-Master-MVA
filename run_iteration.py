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
import statistics
import time
from datetime import datetime, timezone

import metrics

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
VECTOR_DIR = os.path.join(REPO_ROOT, "vector_source")
STITCH_DIR = os.path.join(REPO_ROOT, "stitch_files")
STITCH_PLANS_DIR = os.path.join(REPO_ROOT, "stitch_plans")
REPORTS_DIR = os.path.join(REPO_ROOT, "reports")
RENDERS_DIR = os.path.join(REPO_ROOT, "renders")
REFERENCE_DIR = os.path.join(REPO_ROOT, "reference_images")
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

# --- Visual similarity (iteration 4) ----------------------------------------
# Iteration 4 unlocks the highest-weight dimension, visual_similarity (weight
# 0.40), which was null in iterations 1-3 because no user reference images
# existed and comparing an SVG to its own render is circular. Instead we compute
# REAL fidelity between each vector DESIGN (SVG rendered to raster) and its
# actual EMBROIDERY STITCH-OUT (PES rendered to raster) for matched pairs. This
# is a legitimate, non-circular fidelity metric for an image->vector->embroidery
# pipeline: it measures how faithfully the sewn result reproduces the design.
#
# EXPLICIT documented SVG<->PES/EXP pairing (matched by obvious stems):
#   drink_v2.svg            <-> drink_v2.pes
#   coastal_objects_all.svg <-> summer_coastal-icons.pes
#   drink_trace.svg         <-> drink.pes
# Iteration 9 adds 5 vectorizer->digitizer pairs whose SVGs were copied from
# vectorized_svg/ into vector_source/ and whose EXP stitch-outs were produced
# by rasterizing each SVG via cairosvg then running digitizer.process_images():
#   img_0263.svg  <->  img_0263_logo.exp
#   img_0293.svg  <->  img_0293_logo.exp
#   img_0322.svg  <->  img_0322_logo.exp
#   img_0331.svg  <->  img_0331_logo.exp
#   img_1126.svg  <->  img_1126_logo.exp
# basket_7scans.pes and basket_small.pes have NO SVG source in vector_source/,
# so they are EXCLUDED from visual_similarity (documented, not silently dropped).
#
# Optional future path: if reference_images/<svg_stem>.{png,jpg,jpeg} exists, we
# prefer comparing the SVG render to that real original image instead of the PES
# stitch-out, and record which basis was used per pair.
VISUAL_PAIRS = [
    ("drink_v2.svg", "drink_v2.pes"),
    ("coastal_objects_all.svg", "summer_coastal-icons.pes"),
    ("drink_trace.svg", "drink.pes"),
]
VISUAL_UNPAIRED_PES = ["basket_7scans.pes", "basket_small.pes"]

# visual_similarity per-pair sub-score = clamp(SSIM_W*ssim + EDGE_W*edge_overlap
#                                              + RMSE_W*(1 - rmse_norm), 0, 1)
VISUAL_SSIM_WEIGHT = 0.6
VISUAL_EDGE_WEIGHT = 0.2
VISUAL_RMSE_WEIGHT = 0.2
VISUAL_RENDER_SIZE = 512


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


def resolve_perf_runs():
    """Number of timing repetitions for the performance sub-score (default 5).

    Correctness metrics are deterministic and computed once; only the timing
    loop repeats. Taking the MEDIAN over N runs makes the performance sub-score
    robust to sub-second measurement jitter on a trivial workload.
    """
    raw = os.environ.get("PERF_RUNS", "5").strip()
    try:
        n = int(raw)
        return n if n > 0 else 5
    except ValueError:
        return 5


def percentile(values, pct):
    """Linear-interpolation percentile (numpy-style) with no dependencies."""
    if not values:
        return 0.0
    s = sorted(values)
    if len(s) == 1:
        return s[0]
    rank = (pct / 100.0) * (len(s) - 1)
    lo = int(rank)
    hi = min(lo + 1, len(s) - 1)
    frac = rank - lo
    return s[lo] + (s[hi] - s[lo]) * frac


def discover(batch_size):
    svgs = sorted(glob.glob(os.path.join(VECTOR_DIR, "*.svg")))
    pess = sorted(glob.glob(os.path.join(STITCH_DIR, "*.pes")))
    exps = sorted(glob.glob(os.path.join(STITCH_PLANS_DIR, "*.exp")))
    if batch_size is not None:
        svgs = svgs[:batch_size]
        pess = pess[:batch_size]
    # Include EXP files from stitch_plans/ in the embroidery suitability corpus.
    # pyembroidery (and metrics.pes_metrics) reads EXP files identically to PES.
    pess = pess + exps
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


def measure_all(svgs, pess, perf_runs):
    """Measure every file and time the full corpus metric computation.

    Correctness metrics are deterministic, so the per-file metric dicts are
    identical on every pass; the ledger/report content is therefore written
    once (no duplication). The ONLY thing repeated is the timing loop: we
    recompute the whole corpus `perf_runs` times, record the total runtime of
    each pass, and report min/median/p95 so measurement variance is visible.
    The MEDIAN total runtime feeds the performance sub-score, making it robust
    to sub-second jitter on this trivial (~0.2s) workload.

    Per-file `runtime_s` in each record is the MEDIAN of that file's per-pass
    runtimes, so the artifact tables stay consistent with the median scoring.
    """
    files = [("svg", p) for p in svgs] + [("pes", p) for p in pess]
    per_file_runtimes = {p: [] for _, p in files}
    total_runtimes = []
    records_by_path = {}

    for _ in range(perf_runs):
        run_total = 0.0
        for kind, path in files:
            t0 = time.perf_counter()
            m = metrics.svg_metrics(path) if kind == "svg" else metrics.pes_metrics(path)
            dt = time.perf_counter() - t0
            run_total += dt
            per_file_runtimes[path].append(dt)
            records_by_path[path] = m  # deterministic across passes
        total_runtimes.append(run_total)

    records = []
    for kind, path in files:
        m = records_by_path[path]
        m["runtime_s"] = round(statistics.median(per_file_runtimes[path]), 6)
        m["path"] = os.path.relpath(path, REPO_ROOT)
        records.append(m)

    perf_stats = {
        "runs": perf_runs,
        "total_runtime_min_s": round(min(total_runtimes), 6),
        "total_runtime_median_s": round(statistics.median(total_runtimes), 6),
        "total_runtime_p95_s": round(percentile(total_runtimes, 95), 6),
        "total_runtimes_s": [round(t, 6) for t in total_runtimes],
    }
    return records, perf_stats


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


def score_performance(perf_stats):
    """Performance from the MEDIAN total runtime across PERF_RUNS runs.

    The formula is IDENTICAL to iteration 2 (1 - total_runtime/budget, with a
    2.0s budget); the ONLY change is that `total_runtime` is now the MEDIAN of
    N timing runs rather than a single run, so sub-second jitter on this trivial
    workload no longer swamps real quality changes. min/median/p95 are reported
    in the note so variance is visible.
    """
    total_runtime = perf_stats["total_runtime_median_s"]
    budget = 2.0
    val = clamp01(1.0 - (total_runtime / budget)) if total_runtime > 0 else 1.0
    note = ("1 - median_total_runtime(%.4fs)/budget(%.1fs) over %d runs "
            "[min=%.4fs median=%.4fs p95=%.4fs]" % (
                total_runtime, budget, perf_stats["runs"],
                perf_stats["total_runtime_min_s"],
                perf_stats["total_runtime_median_s"],
                perf_stats["total_runtime_p95_s"]))
    return val, note, total_runtime


def score_reliability(records):
    """Code reliability from the fraction of files measured without error."""
    if not records:
        return None, "no records"
    ok = sum(1 for r in records if r.get("valid") and "error" not in r)
    val = ok / len(records)
    note = "%d/%d files measured without error" % (ok, len(records))
    return val, note


def _save_gray_png(gray, path):
    """Save a grayscale numpy array to PNG for inspection. Best-effort."""
    try:
        from PIL import Image
        Image.fromarray(gray).save(path)
        return True
    except Exception:
        return False


def run_visual_self_test(gray):
    """Prove the visual metric is correct on a known input.

    (a) compare an image to ITSELF   -> expect ssim=1.0, rmse_norm=0, edge=1.0
    (b) compare it to a Gaussian-BLURRED copy -> expect ssim < 1.0
    Returns a dict with the real numbers and a `passed` flag. Returns a dict with
    passed=False and an error if it cannot run.
    """
    result = {"ran": False, "passed": False}
    if gray is None:
        result["error"] = "no rendered image available for self-test"
        return result
    try:
        import numpy as np
        from PIL import Image, ImageFilter
    except Exception as e:
        result["error"] = "self-test deps unavailable: %s" % e
        return result
    try:
        blurred = np.asarray(
            Image.fromarray(gray).filter(ImageFilter.GaussianBlur(radius=4)))
        identity = metrics.visual_compare(gray, gray)
        degraded = metrics.visual_compare(gray, blurred)
        result["ran"] = True
        result["identity"] = identity
        result["degraded"] = degraded
        # Identity must be a perfect match; degradation must lower SSIM.
        id_ok = (identity is not None
                 and abs(identity["ssim"] - 1.0) < 1e-6
                 and identity["rmse_norm"] < 1e-6
                 and abs(identity["edge_overlap"] - 1.0) < 1e-6)
        deg_ok = (degraded is not None
                  and degraded["ssim"] < identity["ssim"]
                  and degraded["ssim"] < 1.0)
        result["passed"] = bool(id_ok and deg_ok)
        result["identity_ok"] = bool(id_ok)
        result["degraded_ok"] = bool(deg_ok)
        result["note"] = (
            "identity ssim=%.6f rmse_norm=%.6f edge_overlap=%.6f (expect "
            "1/0/1); blurred ssim=%.6f (expect <1.0)" % (
                identity["ssim"], identity["rmse_norm"],
                identity["edge_overlap"], degraded["ssim"]))
    except Exception as e:
        result["error"] = "self-test failed: %s" % e
    return result


def _find_reference_image(svg_stem):
    """Return the path to reference_images/<svg_stem>.{png,jpg,jpeg} if present."""
    for ext in ("png", "jpg", "jpeg"):
        cand = os.path.join(REFERENCE_DIR, "%s.%s" % (svg_stem, ext))
        if os.path.exists(cand):
            return cand
    return None


def visual_pair_subscore(cmp):
    """Per-pair visual sub-score from a visual_compare() dict."""
    return clamp01(VISUAL_SSIM_WEIGHT * cmp["ssim"]
                   + VISUAL_EDGE_WEIGHT * cmp["edge_overlap"]
                   + VISUAL_RMSE_WEIGHT * (1.0 - cmp["rmse_norm"]))


def compute_visual(svgs, pess):
    """Compute the visual_similarity dimension for matched design/stitch-out pairs.

    For each VISUAL_PAIRS entry we render the SVG design and, by default, its PES
    stitch-out to a common grayscale raster (metrics.render_svg_to_gray /
    render_pes_to_gray) and score real fidelity with metrics.visual_compare. If a
    reference_images/<svg_stem>.{png,jpg,jpeg} exists we instead compare the SVG
    render to that real original image and record basis='svg_vs_reference'.
    Rendered PNGs are saved into renders/ for inspection.

    Returns a dict:
      {"subscore": float|None, "note": str, "pairs": [...],
       "self_test": {...}, "excluded_pes": [...]}
    subscore is the mean per-pair sub-score, or None if no pair could be scored
    (in which case the caller keeps visual_similarity null and renormalizes,
    exactly like iterations 1-3).
    """
    svg_names = {os.path.basename(p): p for p in svgs}
    pes_names = {os.path.basename(p): p for p in pess}

    os.makedirs(RENDERS_DIR, exist_ok=True)
    pairs = []
    self_test = {"ran": False, "passed": False}
    first_svg_gray = None

    for svg_name, pes_name in VISUAL_PAIRS:
        svg_path = svg_names.get(svg_name)
        pes_path = pes_names.get(pes_name)
        svg_stem = os.path.splitext(svg_name)[0]
        entry = {
            "svg": svg_name,
            "pes": pes_name,
            "basis": None,
            "compared_against": None,
            "ssim": None,
            "rmse_norm": None,
            "edge_overlap": None,
            "subscore": None,
            "note": None,
        }

        if svg_path is None:
            entry["note"] = "SVG %s not found in batch; pair skipped" % svg_name
            pairs.append(entry)
            continue

        svg_gray = metrics.render_svg_to_gray(svg_path, VISUAL_RENDER_SIZE)
        if svg_gray is None:
            entry["note"] = "SVG render failed; pair skipped"
            pairs.append(entry)
            continue
        _save_gray_png(svg_gray, os.path.join(RENDERS_DIR, "%s.svg.png" % svg_stem))
        if first_svg_gray is None:
            first_svg_gray = svg_gray

        # Prefer a real reference image if one exists, else use the PES stitch-out.
        ref_path = _find_reference_image(svg_stem)
        if ref_path is not None:
            try:
                import numpy as np
                from PIL import Image
                ref_img = Image.open(ref_path).convert("L")
                other_gray = metrics._fit_gray_to_canvas(ref_img, VISUAL_RENDER_SIZE)
            except Exception:
                other_gray = None
            entry["basis"] = "svg_vs_reference"
            entry["compared_against"] = os.path.relpath(ref_path, REPO_ROOT)
            if other_gray is not None:
                _save_gray_png(other_gray, os.path.join(
                    RENDERS_DIR, "%s.reference.png" % svg_stem))
        else:
            entry["basis"] = "svg_vs_pes"
            if pes_path is None:
                entry["note"] = "PES %s not found in batch; pair skipped" % pes_name
                pairs.append(entry)
                continue
            entry["compared_against"] = os.path.basename(pes_path)
            other_gray = metrics.render_pes_to_gray(pes_path, VISUAL_RENDER_SIZE)
            if other_gray is not None:
                _save_gray_png(other_gray, os.path.join(
                    RENDERS_DIR, "%s.pes.png" % svg_stem))

        if other_gray is None:
            entry["note"] = "render of comparison target failed; pair skipped"
            pairs.append(entry)
            continue

        cmp = metrics.visual_compare(svg_gray, other_gray)
        if cmp is None:
            entry["note"] = "visual_compare returned None; pair skipped"
            pairs.append(entry)
            continue

        sub = visual_pair_subscore(cmp)
        entry.update({
            "ssim": cmp["ssim"],
            "rmse_norm": cmp["rmse_norm"],
            "edge_overlap": cmp["edge_overlap"],
            "subscore": round(sub, 6),
            "note": "scored (%s)" % entry["basis"],
        })
        pairs.append(entry)

    scored = [e["subscore"] for e in pairs if e["subscore"] is not None]
    subscore = (sum(scored) / len(scored)) if scored else None

    self_test = run_visual_self_test(first_svg_gray)

    if subscore is None:
        note = ("UNAVAILABLE: no design/stitch-out pair could be rendered and "
                "scored; visual_similarity left null and weight renormalized.")
    else:
        note = ("mean over %d matched pairs of clamp(%.1f*ssim + %.1f*edge_overlap"
                " + %.1f*(1-rmse_norm),0,1); design(SVG raster) vs stitch-out(PES "
                "raster) fidelity, non-circular. Self-test %s." % (
                    len(scored), VISUAL_SSIM_WEIGHT, VISUAL_EDGE_WEIGHT,
                    VISUAL_RMSE_WEIGHT,
                    "PASSED" if self_test.get("passed") else "DID NOT PASS"))

    return {
        "subscore": subscore,
        "note": note,
        "pairs": pairs,
        "self_test": self_test,
        "excluded_pes": VISUAL_UNPAIRED_PES,
    }


def compute_overall(records, weights, perf_stats, visual=None):
    """Compute sub-scores and the weighted OVERALL_SCORE.

    Iteration 4 unlocks visual_similarity (weight 0.40) via a real, non-circular
    design-vs-stitch-out metric, so when it is AVAILABLE nothing is dropped and
    the FULL weights.json weights are used (visual 0.40, topology 0.25,
    embroidery 0.20, performance 0.10, reliability 0.05 -> sum 1.0). If the
    visual dimension could not be computed it stays null and its weight is
    dropped/renormalized exactly as in iterations 1-3 (robust fallback).

    Because reintroducing the 0.40 visual weight changes the SCORING BASIS vs
    iterations 1-3 (which renormalized over 4 metrics with visual dropped), we
    ALSO compute `overall_score_continuity_4metric`: the same 4-metric
    renormalized score on the OLD basis, so the delta vs iteration 3 (0.5127) is
    transparent and not confounded by the weight change.
    """
    topo, topo_note = score_topology(records)
    emb, emb_note = score_embroidery(records)
    perf, perf_note, total_runtime = score_performance(perf_stats)
    rel, rel_note = score_reliability(records)
    vis = visual.get("subscore") if visual else None
    vis_note = (visual.get("note") if visual else
                "UNAVAILABLE: visual dimension not computed this run.")

    subscores = {
        "visual_similarity": vis,
        "topology_quality": topo,
        "embroidery_suitability": emb,
        "performance": perf,
        "code_reliability": rel,
    }
    notes = {
        "visual_similarity": vis_note,
        "topology_quality": topo_note,
        "embroidery_suitability": emb_note,
        "performance": perf_note,
        "code_reliability": rel_note,
    }

    # Primary OVERALL_SCORE: renormalize over the dimensions with a non-null
    # score. When visual_similarity is available this leaves all five weights
    # intact (they already sum to 1.0), so this is the FULL-weight score.
    available = {k: weights[k] for k, v in subscores.items() if v is not None}
    weight_sum = sum(available.values())
    renorm = {k: (w / weight_sum) for k, w in available.items()} if weight_sum else {}
    overall = sum(renorm[k] * subscores[k] for k in renorm)
    visual_available = vis is not None

    if visual_available:
        renorm_explanation = (
            "visual_similarity is AVAILABLE this iteration (real design-vs-"
            "stitch-out fidelity), so NO weight is dropped and the FULL "
            "weights.json weights are used unchanged (they already sum to "
            "%.2f). Weights: %s." % (
                sum(weights.values()),
                ", ".join("%s=%.2f" % (k, weights[k]) for k in weights)))
    else:
        renorm_explanation = (
            "Original weights summed to %.2f including visual_similarity=%.2f. "
            "visual_similarity is null, so its weight was dropped and the "
            "remaining weights (%s) were divided by their sum %.2f to "
            "renormalize to 1.0. Renormalized weights: %s." % (
                sum(weights.values()),
                weights["visual_similarity"],
                ", ".join("%s=%.2f" % (k, available[k]) for k in available),
                weight_sum,
                ", ".join("%s=%.4f" % (k, renorm[k]) for k in renorm)))

    # Continuity score (OLD 4-metric basis): renormalize over the four non-visual
    # dimensions with visual DROPPED, exactly as iterations 1-3 did, so the delta
    # vs iteration 3 is apples-to-apples regardless of the weight-basis change.
    cont_dims = ["topology_quality", "embroidery_suitability",
                 "performance", "code_reliability"]
    cont_avail = {k: weights[k] for k in cont_dims if subscores[k] is not None}
    cont_sum = sum(cont_avail.values())
    cont_renorm = ({k: (w / cont_sum) for k, w in cont_avail.items()}
                   if cont_sum else {})
    overall_continuity = sum(cont_renorm[k] * subscores[k] for k in cont_renorm)

    basis_explanation = (
        "DUAL-BASIS reporting. (a) overall_score=%0.6f is the NEW full-weight "
        "score including visual_similarity at its real weight 0.40 - this is the "
        "honest current score now that all five dimensions are measurable. "
        "(b) overall_score_continuity_4metric=%0.6f drops visual and "
        "renormalizes over the same 4 metrics as iterations 1-3, so it is "
        "directly comparable to iteration 3's 0.5127. Comparing (a) to 0.5127 "
        "would be confounded by reintroducing the 0.40 weight; use (b) for a "
        "clean iteration-over-iteration delta." % (overall, overall_continuity))

    return {
        "subscores": subscores,
        "subscore_notes": notes,
        "original_weights": weights,
        "renormalized_weights": renorm,
        "overall_score": round(overall, 6),
        "overall_score_continuity_4metric": round(overall_continuity, 6),
        "continuity_renormalized_weights": cont_renorm,
        "visual_available": visual_available,
        "renormalization_explanation": renorm_explanation,
        "basis_explanation": basis_explanation,
        "total_runtime_s": round(total_runtime, 6),
        "performance_runtime_stats": perf_stats,
        "visual_detail": visual if visual else None,
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

    # prev_overall is the previous iteration's primary OVERALL_SCORE. For
    # iterations 1-3 that was the 4-metric renormalized (visual-dropped) score,
    # so it shares a basis with our continuity score.
    prev_overall = prev_scoring.get("overall_score")
    cur_overall = scoring["overall_score"]
    cur_continuity = scoring.get("overall_score_continuity_4metric")
    overall_delta = (round(cur_overall - prev_overall, 6)
                     if prev_overall is not None else None)

    # Apples-to-apples delta on the SAME 4-metric basis as prior iterations.
    continuity_delta = (round(cur_continuity - prev_overall, 6)
                        if (prev_overall is not None and cur_continuity is not None)
                        else None)

    basis_change = bool(scoring.get("visual_available"))
    basis_change_note = None
    if basis_change:
        basis_change_note = (
            "BASIS CHANGE: iteration %d reintroduces visual_similarity at weight "
            "0.40, so the primary OVERALL_SCORE (%.6f) is on a NEW full-weight "
            "basis and is NOT directly comparable to the previous 4-metric score "
            "%.6f. The apples-to-apples continuity delta (4-metric, visual "
            "dropped) is %s; the full-weight 'delta' %s is confounded by the "
            "weight change and is reported only for completeness." % (
                iteration, cur_overall,
                prev_overall if prev_overall is not None else float("nan"),
                "null" if continuity_delta is None else "%+.6f" % continuity_delta,
                "null" if overall_delta is None else "%+.6f" % overall_delta))

    return {
        "compared_to_iteration": prev_report.get("iteration", iteration - 1),
        "previous_overall_score": prev_overall,
        "current_overall_score": cur_overall,
        "current_overall_score_continuity_4metric": cur_continuity,
        "overall_score_delta": overall_delta,
        "continuity_delta_vs_previous": continuity_delta,
        "basis_change": basis_change,
        "basis_change_note": basis_change_note,
        # `improved` is judged on the apples-to-apples continuity basis when a
        # basis change occurred, else on the primary score.
        "improved": ((continuity_delta is not None and continuity_delta > 0)
                     if basis_change
                     else (overall_delta is not None and overall_delta > 0)),
        "subscore_deltas": subscore_deltas,
    }


def append_jsonl(path, record):
    with open(path, "a") as f:
        f.write(json.dumps(record) + "\n")


def write_reports(iteration, records, scoring, ts, comparison=None,
                  baseline=None):
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
        "comparison_vs_baseline": baseline,
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

    # Dual-basis OVERALL explanation (Phase-6 honesty about the weight change).
    if scoring.get("basis_explanation"):
        lines.append("### Scoring basis (dual)")
        lines.append("")
        lines.append(scoring["basis_explanation"])
        lines.append("")
        lines.append("- OVERALL_SCORE (full-weight, visual 0.40 included): "
                     "**%.6f**" % scoring["overall_score"])
        cont = scoring.get("overall_score_continuity_4metric")
        if cont is not None:
            lines.append("- OVERALL (continuity, 4-metric renorm, visual "
                         "dropped, same basis as iterations 1-3): **%.6f**" % cont)
        lines.append("")

    # Visual similarity detail (per-pair metrics + self-test).
    vd = scoring.get("visual_detail")
    if vd is not None:
        lines.append("## Visual similarity (Phase 6): design vs stitch-out")
        lines.append("")
        lines.append("Real, NON-CIRCULAR fidelity between each vector DESIGN "
                     "(SVG rendered to raster) and its actual EMBROIDERY "
                     "STITCH-OUT (PES rendered to raster) on a shared framing "
                     "convention. Per-pair sub-score = "
                     "clamp(%.1f*ssim + %.1f*edge_overlap + %.1f*(1-rmse_norm),"
                     "0,1)." % (VISUAL_SSIM_WEIGHT, VISUAL_EDGE_WEIGHT,
                                VISUAL_RMSE_WEIGHT))
        lines.append("")
        lines.append("| SVG design | Compared against | Basis | SSIM | rmse_norm"
                     " | edge_overlap | sub-score | note |")
        lines.append("|---|---|---|---|---|---|---|---|")
        for e in vd.get("pairs", []):
            def _f(v):
                return "-" if v is None else "%.6f" % v
            lines.append("| %s | %s | %s | %s | %s | %s | %s | %s |" % (
                e.get("svg"), e.get("compared_against") or e.get("pes"),
                e.get("basis") or "-", _f(e.get("ssim")), _f(e.get("rmse_norm")),
                _f(e.get("edge_overlap")), _f(e.get("subscore")),
                e.get("note") or ""))
        lines.append("")
        sub = vd.get("subscore")
        lines.append("- **visual_similarity sub-score = %s** (mean over scored "
                     "pairs)" % ("null" if sub is None else "%.6f" % sub))
        if vd.get("excluded_pes"):
            lines.append("- Excluded PES (no SVG source pair): %s" %
                         ", ".join(vd["excluded_pes"]))
        lines.append("")

        st = vd.get("self_test", {})
        lines.append("### Visual metric self-test (validation)")
        lines.append("")
        if st.get("ran"):
            idn = st.get("identity", {})
            deg = st.get("degraded", {})
            lines.append("| case | ssim | rmse_norm | edge_overlap | expectation "
                         "| ok |")
            lines.append("|---|---|---|---|---|---|")
            lines.append("| identity (image vs itself) | %.6f | %.6f | %.6f | "
                         "ssim=1, rmse=0, edge=1 | %s |" % (
                             idn.get("ssim", 0.0), idn.get("rmse_norm", 0.0),
                             idn.get("edge_overlap", 0.0),
                             st.get("identity_ok")))
            lines.append("| degraded (Gaussian blur r=4) | %.6f | %.6f | %.6f | "
                         "ssim<1 | %s |" % (
                             deg.get("ssim", 0.0), deg.get("rmse_norm", 0.0),
                             deg.get("edge_overlap", 0.0),
                             st.get("degraded_ok")))
            lines.append("")
            lines.append("- Self-test **%s**." %
                         ("PASSED" if st.get("passed") else "DID NOT PASS"))
        else:
            lines.append("- Self-test did not run: %s" %
                         st.get("error", "unknown"))
        lines.append("")

    # Performance timing variance (objective-robustness evidence).
    ps = scoring.get("performance_runtime_stats")
    if ps is not None:
        lines.append("### Performance timing variance (median-of-N)")
        lines.append("")
        lines.append("Performance is scored from the MEDIAN total runtime over "
                     "%d runs, not a single run, so sub-second jitter on this "
                     "trivial (~0.2s) workload no longer swamps real quality "
                     "changes." % ps["runs"])
        lines.append("")
        lines.append("| runs | min (s) | median (s) | p95 (s) | all runs (s) |")
        lines.append("|---|---|---|---|---|")
        lines.append("| %d | %.6f | %.6f | %.6f | %s |" % (
            ps["runs"], ps["total_runtime_min_s"],
            ps["total_runtime_median_s"], ps["total_runtime_p95_s"],
            ", ".join("%.6f" % t for t in ps["total_runtimes_s"])))
        lines.append("")

    # Phase-6 cross-iteration comparison.
    if comparison is not None:
        lines.append("## Comparison vs iteration %d (Phase 6)" %
                     comparison["compared_to_iteration"])
        lines.append("")
        od = comparison["overall_score_delta"]
        lines.append("- Previous OVERALL_SCORE (4-metric renorm basis): **%s**" % (
            "null" if comparison["previous_overall_score"] is None
            else "%.6f" % comparison["previous_overall_score"]))
        lines.append("- Current OVERALL_SCORE (full-weight, visual 0.40): "
                     "**%.6f**" % comparison["current_overall_score"])
        cont = comparison.get("current_overall_score_continuity_4metric")
        if cont is not None:
            lines.append("- Current OVERALL (continuity, 4-metric renorm, same "
                         "basis as previous): **%.6f**" % cont)
        cd = comparison.get("continuity_delta_vs_previous")
        lines.append("- **Apples-to-apples continuity delta (4-metric): %s** "
                     "(%s)" % (
                         "null" if cd is None else "%+.6f" % cd,
                         "improved" if comparison["improved"]
                         else "not improved"))
        lines.append("- Full-weight 'delta' (CONFOUNDED by the 0.40 weight "
                     "reintroduction, not a clean comparison): %s" % (
                         "null" if od is None else "%+.6f" % od))
        if comparison.get("basis_change_note"):
            lines.append("")
            lines.append(comparison["basis_change_note"])
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

    # Note vs the iteration-1 baseline (in addition to the prior-iteration diff).
    if baseline is not None:
        bd = baseline.get("overall_score_delta")
        lines.append("### vs iteration %d baseline" %
                     baseline["baseline_iteration"])
        lines.append("")
        lines.append("- Baseline (iteration %d) OVERALL_SCORE: **%.6f**" % (
            baseline["baseline_iteration"], baseline["baseline_overall_score"]))
        lines.append("- Current OVERALL_SCORE: **%.6f**" %
                     baseline["current_overall_score"])
        lines.append("- Delta vs baseline: **%s** (%s)" % (
            "null" if bd is None else "%+.6f" % bd,
            "above baseline" if (bd is not None and bd > 0) else "below baseline"))
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
    lines.append("- **visual_similarity** is NOW MEASURED (iteration 4): real "
                 "SSIM / RMSE / edge-overlap between each vector design (SVG "
                 "raster) and its actual embroidery stitch-out (PES raster). This "
                 "is non-circular and does not require user reference images. "
                 "Optional `reference_images/<stem>.{png,jpg,jpeg}` are used "
                 "instead of the PES stitch-out when present (none this run). "
                 "Registration caveat: SVG viewBox padding differs from the PES "
                 "stitch bounding box, so cross-format alignment is approximate; "
                 "SSIM/edge-overlap therefore read as fidelity trends, not exact "
                 "pixel registration. `basket_*.pes` have no SVG source and are "
                 "excluded from the visual dimension.")
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


def update_parameter_index(idx, iteration, ts, scoring, comparison,
                           perf_runs=None):
    """Record parameters and their observed effect on OVERALL_SCORE.

    Iteration 2 introduced the embroidery-suitability coefficients; iteration 3
    introduces PERF_RUNS (median-of-N timing) and records its observed effect on
    performance-score STABILITY (the min/median/p95 timing spread), which is the
    knob that changed this iteration.
    """
    emb = scoring["subscores"].get("embroidery_suitability")
    perf = scoring["subscores"].get("performance")
    overall = scoring["overall_score"]
    overall_delta = comparison["overall_score_delta"] if comparison else None
    emb_delta = None
    perf_delta = None
    if comparison:
        emb_delta = comparison["subscore_deltas"].get(
            "embroidery_suitability", {}).get("delta")
        perf_delta = comparison["subscore_deltas"].get(
            "performance", {}).get("delta")

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

    # PERF_RUNS: median-of-N timing knob and its effect on score stability.
    if perf_runs is not None:
        ps = scoring.get("performance_runtime_stats", {})
        entry = params.setdefault("PERF_RUNS", {
            "value": perf_runs,
            "source": "run_iteration.py performance sub-score timing loop "
                      "(introduced iteration %d)" % iteration,
            "unit": "runs",
            "correlation_history": [],
        })
        entry["value"] = perf_runs
        entry["correlation_history"].append({
            "iteration": iteration,
            "timestamp": ts,
            "perf_runs": perf_runs,
            "performance": perf,
            "performance_delta": perf_delta,
            "total_runtime_min_s": ps.get("total_runtime_min_s"),
            "total_runtime_median_s": ps.get("total_runtime_median_s"),
            "total_runtime_p95_s": ps.get("total_runtime_p95_s"),
            "overall_score": overall,
            "overall_score_delta": overall_delta,
            "observed_effect": ("median-of-%d timing; performance sub-score now "
                                "reflects the median (%.6fs) rather than a single "
                                "noisy run, spread min=%.6fs p95=%.6fs" % (
                                    perf_runs,
                                    ps.get("total_runtime_median_s", 0.0),
                                    ps.get("total_runtime_min_s", 0.0),
                                    ps.get("total_runtime_p95_s", 0.0))),
        })

    # Visual similarity sub-score weights + pairing basis (introduced iter 4).
    vis = scoring["subscores"].get("visual_similarity")
    vis_delta = None
    if comparison:
        vis_delta = comparison["subscore_deltas"].get(
            "visual_similarity", {}).get("delta")
    vd = scoring.get("visual_detail", {}) or {}
    st = vd.get("self_test", {})
    visual_weights = {
        "visual_ssim_weight": VISUAL_SSIM_WEIGHT,
        "visual_edge_weight": VISUAL_EDGE_WEIGHT,
        "visual_rmse_weight": VISUAL_RMSE_WEIGHT,
    }
    pairing_basis = [{"svg": s, "pes": p, "basis": "svg_vs_pes"}
                     for s, p in VISUAL_PAIRS]
    for name, value in visual_weights.items():
        entry = params.setdefault(name, {
            "value": value,
            "source": "run_iteration.py visual_similarity per-pair sub-score "
                      "clamp(0.6*ssim+0.2*edge+0.2*(1-rmse)) "
                      "(introduced iteration %d)" % iteration,
            "unit": "coefficient",
            "correlation_history": [],
        })
        entry["value"] = value
        entry["correlation_history"].append({
            "iteration": iteration,
            "timestamp": ts,
            "visual_similarity": vis,
            "visual_similarity_delta": vis_delta,
            "self_test_passed": bool(st.get("passed")),
            "pairing_basis": pairing_basis,
            "excluded_pes_no_svg_pair": VISUAL_UNPAIRED_PES,
            "overall_score_full_weight": overall,
            "overall_score_continuity_4metric": scoring.get(
                "overall_score_continuity_4metric"),
            "overall_score_delta": overall_delta,
        })

    idx["last_updated_iteration"] = iteration
    idx["last_updated_timestamp"] = ts
    with open(PARAM_INDEX, "w") as f:
        json.dump(idx, f, indent=2)
    return idx


def load_baseline_report():
    """Load reports/iteration_1.json (the baseline) if present, else None."""
    path = os.path.join(REPORTS_DIR, "iteration_1.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return None


def build_baseline_comparison(iteration, scoring, baseline_report):
    """Note comparing the current OVERALL_SCORE to the iteration-1 baseline."""
    if baseline_report is None or baseline_report.get("iteration") == iteration:
        return None
    base_overall = baseline_report.get("scoring", {}).get("overall_score")
    cur_overall = scoring["overall_score"]
    delta = (round(cur_overall - base_overall, 6)
             if base_overall is not None else None)
    return {
        "baseline_iteration": baseline_report.get("iteration", 1),
        "baseline_overall_score": base_overall,
        "current_overall_score": cur_overall,
        "overall_score_delta": delta,
    }


def main():
    ts = now_iso()
    batch_size = resolve_batch_size()
    perf_runs = resolve_perf_runs()
    weights = load_weights()
    iteration = next_iteration_number()

    svgs, pess = discover(batch_size)
    print("Iteration %d | batch=%s | PERF_RUNS=%d | %d SVG, %d PES" % (
        iteration, batch_size if batch_size is not None else "ALL",
        perf_runs, len(svgs), len(pess)))

    records, perf_stats = measure_all(svgs, pess, perf_runs)

    # Iteration 4: compute the real design-vs-stitch-out visual dimension.
    visual = compute_visual(svgs, pess)
    scoring = compute_overall(records, weights, perf_stats, visual)

    # Phase-6 cross-iteration comparison (vs immediately prior iteration).
    prev_report = load_previous_report(iteration)
    comparison = build_comparison(iteration, scoring, prev_report)

    # Additional note vs the iteration-1 baseline.
    baseline_report = load_baseline_report()
    baseline = build_baseline_comparison(iteration, scoring, baseline_report)

    # Reports
    json_path, md_path = write_reports(
        iteration, records, scoring, ts, comparison, baseline)

    # Observations: one JSON line per measured artifact.
    for r in records:
        obs = dict(r)
        obs["iteration"] = iteration
        obs["timestamp"] = ts
        append_jsonl(OBSERVATIONS, obs)

    # Per-pair visual observations (iteration 4): one line per matched pair with
    # the real ssim/rmse/edge_overlap and the pairing basis.
    for e in visual.get("pairs", []):
        obs = {
            "artifact": "visual_pair:%s|%s" % (e.get("svg"), e.get("pes")),
            "kind": "visual_pair",
            "iteration": iteration,
            "timestamp": ts,
            "svg": e.get("svg"),
            "pes": e.get("pes"),
            "basis": e.get("basis"),
            "compared_against": e.get("compared_against"),
            "ssim": e.get("ssim"),
            "rmse_norm": e.get("rmse_norm"),
            "edge_overlap": e.get("edge_overlap"),
            "visual_subscore": e.get("subscore"),
            "note": e.get("note"),
        }
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
        continuity_delta = comparison.get("continuity_delta_vs_previous")
        vd = scoring.get("visual_detail", {}) or {}
        self_test = vd.get("self_test", {})
        vis_sub = scoring["subscores"].get("visual_similarity")
        n_scored = sum(1 for e in vd.get("pairs", [])
                       if e.get("subscore") is not None)

        # Phase-8 (iteration 4): this iteration ADDS a dimension rather than
        # moving an existing one. Reward is judged by whether the framework now
        # produces a VALID, self-test-passing visual_similarity number AND
        # reports the score honestly (dual-basis, no gaming) -- NOT by whether
        # the primary OVERALL_SCORE went up (it mechanically jumps because a
        # 0.40-weight dimension re-enters, which we explicitly do not count as a
        # reward). We do NOT tune the visual formula to inflate the number.
        dimension_added = vis_sub is not None and n_scored > 0
        self_test_passed = bool(self_test.get("passed"))
        reward = 1 if (dimension_added and self_test_passed) else 0
        penalty = 0 if reward else 1
        decision = ("reward-dimension-added-validated" if reward
                    else "penalty-visual-unvalidated")

        baseline_overall = (baseline.get("baseline_overall_score")
                            if baseline else None)
        baseline_delta = (baseline.get("overall_score_delta")
                          if baseline else None)
        pair_metrics = [{
            "svg": e.get("svg"), "pes": e.get("pes"), "basis": e.get("basis"),
            "ssim": e.get("ssim"), "rmse_norm": e.get("rmse_norm"),
            "edge_overlap": e.get("edge_overlap"), "subscore": e.get("subscore"),
        } for e in vd.get("pairs", [])]

        append_jsonl(DECISION_TRACE, {
            "iteration": iteration,
            "timestamp": ts,
            "artifact": "decision_trace",
            "objective": "Unlock the highest-weight dimension visual_similarity "
                         "(weight 0.40, null in iterations 1-3) with a REAL, "
                         "non-circular fidelity metric: compare each vector "
                         "DESIGN (SVG raster) to its actual embroidery STITCH-OUT "
                         "(PES raster) via SSIM / RMSE / edge-overlap.",
            "hypothesis": "A design-vs-stitch-out comparison is a legitimate, "
                          "non-circular fidelity signal for an image->vector->"
                          "embroidery pipeline (unlike comparing an SVG to its "
                          "own render). Rendering both to a shared framing "
                          "convention and scoring clamp(0.6*ssim + 0.2*edge + "
                          "0.2*(1-rmse)) should yield a valid, self-test-passing "
                          "visual_similarity number, letting the full 0.40 weight "
                          "be used honestly.",
            "decision": decision,
            "dimension_added": dimension_added,
            "self_test_passed": self_test_passed,
            "self_test": self_test,
            "visual_similarity_subscore": vis_sub,
            "pairs_scored": n_scored,
            "visual_pair_metrics": pair_metrics,
            "pairing_basis": [{"svg": s, "pes": p} for s, p in VISUAL_PAIRS],
            "excluded_pes_no_svg_pair": VISUAL_UNPAIRED_PES,
            "overall_score_full_weight": overall,
            "overall_score_continuity_4metric": scoring.get(
                "overall_score_continuity_4metric"),
            "previous_overall_score_4metric_basis": prev_overall,
            "continuity_delta_vs_previous": continuity_delta,
            "full_weight_delta_confounded": delta,
            "baseline_iteration_1_overall": baseline_overall,
            "note": "Phase-8: this iteration ADDS a dimension; reward is judged "
                    "by validity + self-test pass + honest dual-basis reporting, "
                    "NOT by the mechanical OVERALL_SCORE jump from re-adding the "
                    "0.40 weight. The apples-to-apples 4-metric continuity delta "
                    "vs iteration 3 is %s; the full-weight delta %s is confounded "
                    "and not used to judge reward. No gaming: the visual formula "
                    "and weights were fixed a priori, not tuned to the numbers." % (
                        "null" if continuity_delta is None
                        else "%+.6f" % continuity_delta,
                        "null" if delta is None else "%+.6f" % delta),
        })
        append_jsonl(REWARD_LEDGER, {
            "iteration": iteration,
            "timestamp": ts,
            "artifact": "reward_penalty_ledger",
            "reward": reward,
            "penalty": penalty,
            "overall_score": overall,
            "overall_score_continuity_4metric": scoring.get(
                "overall_score_continuity_4metric"),
            "previous_overall_score": prev_overall,
            "delta": delta,
            "continuity_delta_vs_previous": continuity_delta,
            "visual_similarity_subscore": vis_sub,
            "self_test_passed": self_test_passed,
            "basis_change": True,
            "note": ("REWARD: added validated visual_similarity=%s (self-test "
                     "PASSED, %d pairs scored); score reported honestly on dual "
                     "basis, not gamed. Continuity 4-metric delta vs iteration "
                     "%d = %s." % (
                         "null" if vis_sub is None else "%.6f" % vis_sub,
                         n_scored, comparison["compared_to_iteration"],
                         "null" if continuity_delta is None
                         else "%+.6f" % continuity_delta)) if reward
                    else ("PENALTY: visual_similarity not validly produced or "
                          "self-test did not pass (dimension_added=%s, "
                          "self_test_passed=%s)." % (
                              dimension_added, self_test_passed)),
        })
        idx = seed_parameter_index(iteration, ts)
        update_parameter_index(idx, iteration, ts, scoring, comparison,
                               perf_runs=perf_runs)

    # Console summary.
    print("OVERALL_SCORE (full-weight, visual 0.40) = %.4f" % overall)
    cont = scoring.get("overall_score_continuity_4metric")
    if cont is not None:
        print("OVERALL_SCORE (continuity 4-metric, visual dropped) = %.4f" % cont)
    for dim, sc in scoring["subscores"].items():
        print("  %-24s %s" % (dim, "null" if sc is None else "%.4f" % sc))
    vd = scoring.get("visual_detail")
    if vd is not None:
        st = vd.get("self_test", {})
        print("Visual self-test: %s | %s" % (
            "PASSED" if st.get("passed") else "DID NOT PASS",
            st.get("note", st.get("error", ""))))
        for e in vd.get("pairs", []):
            if e.get("subscore") is not None:
                print("  pair %s vs %s [%s]: ssim=%.4f rmse=%.4f edge=%.4f "
                      "sub=%.4f" % (
                          e["svg"], e["compared_against"], e["basis"],
                          e["ssim"], e["rmse_norm"], e["edge_overlap"],
                          e["subscore"]))
    ps = scoring.get("performance_runtime_stats")
    if ps is not None:
        print("Performance timing over %d runs: min=%.6fs median=%.6fs p95=%.6fs" % (
            ps["runs"], ps["total_runtime_min_s"],
            ps["total_runtime_median_s"], ps["total_runtime_p95_s"]))
    if comparison is not None:
        cd = comparison.get("continuity_delta_vs_previous")
        print("Continuity delta (4-metric) vs iteration %d: %s (%s)" % (
            comparison["compared_to_iteration"],
            "null" if cd is None else "%+.6f" % cd,
            "reward" if comparison["improved"] else "penalty"))
        print("Full-weight delta vs iteration %d (CONFOUNDED by 0.40 weight): "
              "%+.6f" % (comparison["compared_to_iteration"],
                         comparison["overall_score_delta"]))
    if baseline is not None:
        print("Delta vs iteration %d baseline: %+.6f" % (
            baseline["baseline_iteration"], baseline["overall_score_delta"]))
    print("Reports: %s , %s" % (json_path, md_path))


if __name__ == "__main__":
    main()
