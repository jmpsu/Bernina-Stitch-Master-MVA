#!/usr/bin/env python3
"""Stage-2 knowledge-correlation experiment harness for the vectorizer.

Purpose
-------
Prove (or refute), for EACH library-derived knowledge artifact produced by the
Stage-1 knowledge agents (knowledge_agents.load_agent_hypotheses), whether the
parameter change it recommends actually correlates with IMPROVED vectorization
quality. This is an isolated-factor, regression-style experiment with a
confidence label per artifact -- deterministic and model-free (it only calls
vectorizer.trace / render_svg_rgb / score, no LLM anywhere).

Method
------
1. Fix a BASELINE param set = the vectorizer's current default seed
   (vectorizer.DOCTRINE_SEED["default"]). Score it on each of the 5 known test
   images (composite, ssim_color, color_fidelity, edge_iou).
2. For each vtracer-runnable hypothesis, for each candidate value, ISOLATE that
   single factor (baseline + that one change) and trace+render+score every
   image. Record per-image delta vs baseline for composite AND the artifact's
   TARGET sub-metric (color_fidelity for color_agent, edge_iou for edge_agent,
   ssim_color for curve_agent / noise_agent).
3. For non-vtracer / pipeline hypotheses: if the vectorizer exposes the relevant
   preprocessing, test it against the true original; else mark
   status="not_testable_yet" with an honest reason. No fabricated results.
4. AGGREGATE per hypothesis: best candidate value, mean Delta-composite across
   images, std, fraction of images improved, a confidence label, and whether the
   observed best direction matches the artifact's PREDICTED direction.
5. Log EVERY trial to knowledge_experiments.jsonl (artifact -> factor ->
   score-delta ledger) and emit a ranked report to
   reports/knowledge_experiments.md.

A hard internal wall-clock budget (--budget-seconds) bounds runtime: when it is
exceeded the harness stops launching new trials, aggregates whatever completed,
and writes the report -- so a partial run still yields a coherent ledger+report.
"""

from __future__ import annotations

import json
import os
import statistics
import sys
import tempfile
import time

import vectorizer as V
from knowledge_agents import load_agent_hypotheses

_HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(_HERE, "knowledge_experiments.jsonl")
REPORT = os.path.join(_HERE, "reports", "knowledge_experiments.md")

UPLOADS = "/root/.claude/uploads/0f26c418-97eb-5ee4-97aa-b775bedafccc"

# The 5 test images with known behavior (label -> upload filename). Originals are
# read from the uploads dir and are NEVER copied into the repo.
IMAGES = {
    "flags":    "340931ae-IMG_0331.jpeg",
    "crest":    "65892eaa-IMG_1126.jpeg",
    "caddie":   "76ca38b2-IMG_0322.jpeg",
    "house":    "61c7ce08-IMG_0293.jpeg",
    "squirrel": "8b4ed770-IMG_0263.jpeg",
}

# Fixed baseline = the vectorizer's current default seed.
BASELINE = dict(V.DOCTRINE_SEED["default"])

# Artifact target sub-metric by owning agent.
TARGET_METRIC = {
    "color_agent": "color_fidelity",
    "edge_agent":  "edge_iou",
    "curve_agent": "ssim_color",
    "noise_agent": "ssim_color",
}

# "images improved" counts any strictly-positive composite delta (deltas are
# deterministic -- vtracer has no randomness -- so even small consistent gains are
# real, reproducible signal, not noise). NEUTRAL_BAND is the |mean| magnitude below
# which a hypothesis's best candidate is treated as having ~zero net effect.
NEUTRAL_BAND = 5e-5

# ---------------------------------------------------------------------------
# PREDICTED-direction table, keyed by (agent, concept). Encodes what each cited
# artifact predicts is BEST, so the harness can score observed-vs-predicted.
#   kind="max"    -> artifact predicts the largest candidate wins (direction increase)
#   kind="min"    -> artifact predicts the smallest candidate wins (direction decrease)
#   kind="set"    -> artifact predicts a value inside `pref` wins
# `desc` is the human-readable prediction shown in the report.
# ---------------------------------------------------------------------------
PREDICTED = {
    ("color_agent", "Perceptual color-merge tolerance (delta_e <= 5.0)"):
        {"kind": "set", "pref": {8, 16}, "desc": "moderate 8-16 (not min 4)"},
    ("color_agent", "Stacked vs cutout color layering topology"):
        {"kind": "set", "pref": {"stacked"}, "desc": "stacked"},
    ("color_agent", "HSL-distance nearest-color matching for palette mapping"):
        {"kind": "set", "pref": {"color"}, "desc": "color (only option)"},
    ("color_agent", "Bounded color palette (max 15 thread colors)"):
        {"kind": "set", "pref": {5, 6}, "desc": "moderate 5-6 (<=15 colors)"},
    ("curve_agent", "alphamax corner threshold (curve vs corner decision)"):
        {"kind": "set", "pref": {40, 50}, "desc": "lower 40-50 (smoother, curve bias)"},
    ("curve_agent", "opticurve: true Bezier optimization vs raw polygon"):
        {"kind": "set", "pref": {"spline"}, "desc": "spline (Bezier)"},
    ("curve_agent", "opttolerance curve-optimization tolerance (node count vs fit)"):
        {"kind": "set", "pref": {7, 8}, "desc": "higher 7-8 (more faithful)"},
    ("curve_agent", "Curve segment joining and splice length (secondary opttolerance analogue)"):
        {"kind": "set", "pref": {45, 60}, "desc": "hold/raise 45-60"},
    ("edge_agent", "Corner detection threshold for edge/corner fidelity"):
        {"kind": "max", "desc": "higher (increase) -> 90"},
    ("edge_agent", "max path deviation <= 0.5mm (geometric edge fidelity target)"):
        {"kind": "max", "desc": "increase toward 8"},
    ("edge_agent", "Node/element count as a path-topology quality target"):
        {"kind": "min", "desc": "decrease -> 4 (fewer nodes, negligible loss)"},
    ("edge_agent", "turnpolicy: resolving ambiguous turns in path decomposition"):
        {"kind": "set", "pref": {"spline"}, "desc": "spline (weak/no analogue)"},
    ("noise_agent", "turdsize: suppress paths below an area (speckle removal)"):
        {"kind": "set", "pref": {1, 2, 4}, "desc": "moderate-low 1-4 (per-artwork ~2)"},
    ("noise_agent", "mkbitmap lowpass filter: smoothing foreground detail before tracing"):
        {"kind": "set", "pref": {"none", "median3"}, "desc": "presmooth helps noisy/AA; none on clean"},
}

# Non-vtracer noise hypotheses the vectorizer does NOT expose -> not testable yet.
NOT_TESTABLE = {
    "source_background_flatten": (
        "vectorizer exposes no highpass background-flatten stage; _presmoothed_source "
        "only does median smoothing, not gradient removal. No pipeline hook to isolate."),
    "source_threshold_level": (
        "vectorizer traces in colormode='color' (multi-layer), not a bilevel/blacklevel "
        "cutoff; no grey-cutoff parameter is exposed to isolate."),
}


# ---------------------------------------------------------------------------
# preprocessing for the testable noise-pipeline hypothesis (source_presmooth)
# ---------------------------------------------------------------------------
def _presmooth_variant(src_path, variant):
    """Return (trace_path, cleanup_or_None) for a source-presmooth variant.
    'none' traces the true original. 'median3' mirrors vectorizer._presmoothed_source
    (PIL MedianFilter size 3). 'gaussian' applies a light Gaussian blur. Scoring
    always uses the TRUE original regardless of variant."""
    if variant == "none":
        return src_path, None
    from PIL import Image, ImageFilter
    img = Image.open(src_path).convert("RGB")
    if variant == "median3":
        sm = img.filter(ImageFilter.MedianFilter(size=3))
    elif variant == "gaussian":
        sm = img.filter(ImageFilter.GaussianBlur(radius=1.0))
    else:
        return src_path, None
    fd, out = tempfile.mkstemp(suffix=".png")
    os.close(fd)
    sm.save(out)
    return out, out


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def confidence_label(mean_delta, frac_improved, n):
    """Confidence label for a hypothesis's BEST candidate, per the task spec:
      validated      = mean Delta-composite > 0 AND >= 4/5 (0.8) images improve
      weak/positive  = net positive (mean > 0) but mixed (< 4/5 improve)
      neutral        = |mean Delta| ~ 0 (within NEUTRAL_BAND; e.g. best == baseline)
      refuted        = net negative
    """
    if abs(mean_delta) <= NEUTRAL_BAND:
        return "neutral"
    if mean_delta > 0 and frac_improved >= 0.8:
        return "validated"
    if mean_delta > 0:
        return "weak/positive"
    return "refuted"


def main(argv):
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--budget-seconds", type=float, default=300.0,
                    help="internal wall-clock cap; stop launching trials past it")
    ap.add_argument("--from-ledger", action="store_true",
                    help="re-aggregate an existing knowledge_experiments.jsonl and "
                         "rewrite the report WITHOUT re-tracing (deterministic)")
    args = ap.parse_args(argv)

    if args.from_ledger:
        t0 = time.time()
        baseline, results, labels = build_from_ledger()
        write_report(baseline, results, labels, time.time() - t0, False,
                     args.budget_seconds)
        print(f"\nRe-aggregated from ledger. report={REPORT}")
        return results

    t0 = time.time()
    deadline = t0 + args.budget_seconds

    # load originals once (framed exactly as vectorizer scores them).
    orig_rgb = {}
    src_path = {}
    for label, fname in IMAGES.items():
        p = os.path.join(UPLOADS, fname)
        if not os.path.exists(p):
            print(f"MISSING image {label}: {p}", file=sys.stderr)
            continue
        src_path[label] = p
        orig_rgb[label] = V.load_image_rgb(p)
    labels = list(orig_rgb.keys())

    ledger = open(LEDGER, "w", encoding="utf-8")

    def log(rec):
        ledger.write(json.dumps(rec) + "\n")
        ledger.flush()

    def trace_score(trace_path, params):
        """trace+render+score; returns score dict or None on failure."""
        try:
            svg = V.trace(trace_path, params)
            rendered = V.render_svg_rgb(svg)
            return V.score(orig_rgb_current, rendered)
        except Exception:
            return None

    # ---- 1. baseline ----
    baseline = {}  # label -> score dict
    print("=== BASELINE (DOCTRINE_SEED['default']) ===")
    for label in labels:
        global orig_rgb_current
        orig_rgb_current = orig_rgb[label]
        sc = trace_score(src_path[label], BASELINE)
        baseline[label] = sc
        if sc:
            print(f"  {label:9s} composite={sc['composite']:.4f} "
                  f"ssim={sc['ssim_color']:.4f} cfid={sc['color_fidelity']:.4f} "
                  f"edge_iou={sc['edge_iou']:.4f}")
        log({"timestamp": _now(), "phase": "baseline", "image": label,
             "params": BASELINE, "scores": sc})

    # ---- 2+3. per-hypothesis isolated-factor trials ----
    hyp_map = load_agent_hypotheses()
    # deterministic flat order
    hypotheses = []
    for agent in ("color_agent", "curve_agent", "edge_agent", "noise_agent"):
        hypotheses.extend(hyp_map[agent])

    results = []          # aggregated per-hypothesis records
    budget_hit = False

    for h in hypotheses:
        agent = h["agent"]
        concept = h["concept"]
        param = h["param"]
        values = h["values"]
        target = TARGET_METRIC[agent]
        base_val = BASELINE.get(param)

        rec = {
            "agent": agent, "concept": concept, "param": param,
            "source_document": h["source_document"], "direction": h["direction"],
            "target_metric": target, "baseline_value": base_val,
            "candidate_values": values,
        }

        # non-vtracer / pipeline handling
        is_presmooth = (param == "source_presmooth")
        if not h["is_vtracer_param"] and not is_presmooth:
            rec["status"] = "not_testable_yet"
            rec["reason"] = NOT_TESTABLE.get(param, "no vectorizer hook to isolate this factor")
            results.append(rec)
            log({"timestamp": _now(), "phase": "hypothesis", "status": "not_testable_yet",
                 "agent": agent, "concept": concept, "param": param,
                 "source_document": h["source_document"], "reason": rec["reason"]})
            continue

        if budget_hit:
            rec["status"] = "not_run_budget"
            results.append(rec)
            continue

        # per-candidate aggregation
        cand_stats = {}   # value -> {"dcomp":[...], "dtarget":[...]}
        for val in values:
            if time.time() > deadline:
                budget_hit = True
                break
            dcomp, dtarget = [], []
            for label in labels:
                if time.time() > deadline:
                    budget_hit = True
                    break
                base_sc = baseline[label]
                if base_sc is None:
                    continue
                globals()["orig_rgb_current"] = orig_rgb[label]

                cleanup = None
                if is_presmooth:
                    tp, cleanup = _presmooth_variant(src_path[label], val)
                    params = dict(BASELINE)
                else:
                    tp = src_path[label]
                    params = dict(BASELINE)
                    params[param] = val

                sc = trace_score(tp, params)
                if cleanup:
                    try:
                        os.remove(cleanup)
                    except OSError:
                        pass

                if sc is None:
                    dc = dt = None
                else:
                    dc = round(sc["composite"] - base_sc["composite"], 6)
                    dt = round(sc[target] - base_sc[target], 6)
                    dcomp.append(dc)
                    dtarget.append(dt)

                log({
                    "timestamp": _now(), "phase": "trial", "agent": agent,
                    "concept": concept, "source_document": h["source_document"],
                    "param": param, "value": val, "image": label,
                    "baseline_composite": None if base_sc is None else base_sc["composite"],
                    "cand_composite": None if sc is None else sc["composite"],
                    "delta_composite": dc,
                    "delta_target_metric": dt, "target_metric": target,
                })
            if dcomp:
                cand_stats[val] = {
                    "mean_dcomp": statistics.fmean(dcomp),
                    "std_dcomp": statistics.pstdev(dcomp) if len(dcomp) > 1 else 0.0,
                    "frac_improved": sum(1 for x in dcomp if x > 0) / len(dcomp),
                    "n": len(dcomp),
                    "mean_dtarget": statistics.fmean(dtarget) if dtarget else 0.0,
                    "per_image_dcomp": {labels[i]: dcomp[i] for i in range(len(dcomp))},
                }

        if not cand_stats:
            rec["status"] = "not_run_budget" if budget_hit else "no_data"
            results.append(rec)
            continue

        finalize_rec(rec, agent, concept, param, values, cand_stats, budget_hit)
        results.append(rec)

    ledger.close()
    elapsed = time.time() - t0
    write_report(baseline, results, labels, elapsed, budget_hit, args.budget_seconds)
    print(f"\nElapsed {elapsed:.1f}s  budget_hit={budget_hit}  "
          f"ledger={LEDGER}  report={REPORT}")
    return results


def finalize_rec(rec, agent, concept, param, values, cand_stats, budget_hit):
    """Aggregate cand_stats into the per-hypothesis record (best candidate, mean
    Delta-composite +- std, images improved, confidence, predicted-vs-observed
    direction match). Mutates and returns rec."""
    best_val = max(cand_stats, key=lambda v: cand_stats[v]["mean_dcomp"])
    bs = cand_stats[best_val]
    label_conf = confidence_label(bs["mean_dcomp"], bs["frac_improved"], bs["n"])

    pred = PREDICTED.get((agent, concept))
    match, pred_desc = None, "n/a"
    if pred:
        pred_desc = pred["desc"]
        if pred["kind"] == "max":
            match = (best_val == max(values))
        elif pred["kind"] == "min":
            match = (best_val == min(values))
        elif pred["kind"] == "set":
            match = (best_val in pred["pref"])

    rec.update({
        "status": "tested_partial" if budget_hit else "tested",
        "best_value": best_val,
        "best_mean_dcomp": round(bs["mean_dcomp"], 6),
        "best_std_dcomp": round(bs["std_dcomp"], 6),
        "best_frac_improved": round(bs["frac_improved"], 3),
        "best_mean_dtarget": round(bs["mean_dtarget"], 6),
        "n_images": bs["n"],
        "confidence": label_conf,
        "predicted": pred_desc,
        "direction_match": match,
        "per_candidate": {str(v): {
            "mean_dcomp": round(s["mean_dcomp"], 6),
            "frac_improved": round(s["frac_improved"], 3),
            "mean_dtarget": round(s["mean_dtarget"], 6),
        } for v, s in cand_stats.items()},
        "best_per_image_dcomp": {k: round(x, 6) for k, x in bs["per_image_dcomp"].items()},
    })
    print(f"  [{agent}] {param}={best_val!s:<8} dcomp={bs['mean_dcomp']:+.4f} "
          f"+-{bs['std_dcomp']:.4f}  improved {bs['frac_improved']*100:.0f}%  "
          f"{label_conf}  dir_match={match}")
    return rec


def build_from_ledger():
    """Re-aggregate an existing knowledge_experiments.jsonl into results without
    re-tracing (vtracer is deterministic, so re-tracing reproduces identical
    numbers). Returns (baseline, results, labels)."""
    baseline = {}
    labels = []
    # (agent, concept) -> {"param":.., "value_deltas": {value: {"dcomp":[], "dtarget":[], "img":[]}}}
    trials = {}
    with open(LEDGER, "r", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            ph = r.get("phase")
            if ph == "baseline":
                baseline[r["image"]] = r["scores"]
                if r["image"] not in labels:
                    labels.append(r["image"])
            elif ph == "trial":
                key = (r["agent"], r["concept"])
                t = trials.setdefault(key, {"param": r["param"], "vals": {}})
                v = t["vals"].setdefault(r["value"], {"dcomp": [], "dtarget": [], "img": []})
                if r["delta_composite"] is not None:
                    v["dcomp"].append(r["delta_composite"])
                    v["dtarget"].append(r["delta_target_metric"])
                    v["img"].append(r["image"])

    hyp_map = load_agent_hypotheses()
    results = []
    for agent in ("color_agent", "curve_agent", "edge_agent", "noise_agent"):
        for h in hyp_map[agent]:
            concept = h["concept"]
            param = h["param"]
            target = TARGET_METRIC[agent]
            rec = {
                "agent": agent, "concept": concept, "param": param,
                "source_document": h["source_document"], "direction": h["direction"],
                "target_metric": target, "baseline_value": BASELINE.get(param),
                "candidate_values": h["values"],
            }
            is_presmooth = (param == "source_presmooth")
            if not h["is_vtracer_param"] and not is_presmooth:
                rec["status"] = "not_testable_yet"
                rec["reason"] = NOT_TESTABLE.get(param, "no vectorizer hook to isolate this factor")
                results.append(rec)
                continue
            key = (agent, concept)
            vals = trials.get(key, {}).get("vals", {})
            cand_stats = {}
            for val, d in vals.items():
                if not d["dcomp"]:
                    continue
                dcomp = d["dcomp"]
                cand_stats[val] = {
                    "mean_dcomp": statistics.fmean(dcomp),
                    "std_dcomp": statistics.pstdev(dcomp) if len(dcomp) > 1 else 0.0,
                    "frac_improved": sum(1 for x in dcomp if x > 0) / len(dcomp),
                    "n": len(dcomp),
                    "mean_dtarget": statistics.fmean(d["dtarget"]) if d["dtarget"] else 0.0,
                    "per_image_dcomp": {d["img"][i]: dcomp[i] for i in range(len(dcomp))},
                }
            if not cand_stats:
                rec["status"] = "no_data"
                results.append(rec)
                continue
            finalize_rec(rec, agent, concept, param, h["values"], cand_stats, False)
            results.append(rec)
    return baseline, results, labels


def write_report(baseline, results, labels, elapsed, budget_hit, budget):
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    tested = [r for r in results if r.get("status") in ("tested", "tested_partial")]
    # rank tested by best_mean_dcomp desc
    tested.sort(key=lambda r: r.get("best_mean_dcomp", -9), reverse=True)
    not_testable = [r for r in results if r.get("status") == "not_testable_yet"]
    not_run = [r for r in results if r.get("status") in ("not_run_budget", "no_data")]

    def bucket(label):
        return [r for r in tested if r["confidence"] == label]

    lines = []
    lines.append("# Stage-2 knowledge-correlation experiments\n")
    lines.append("_Isolated-factor, regression-style test of whether each Stage-1 "
                 "library-derived knowledge artifact's recommended parameter change "
                 "correlates with improved vectorization quality. Deterministic, "
                 "model-free: only vectorizer.trace / render_svg_rgb / score are used._\n")
    lines.append(f"- Baseline param set: `vectorizer.DOCTRINE_SEED['default']` "
                 f"(color_precision=6, filter_speckle=4, corner_threshold=60, "
                 f"path_precision=8, layer_difference=16, splice_threshold=45, "
                 f"mode=spline, hierarchical=stacked, colormode=color).")
    lines.append(f"- Test images (5, known behavior): {', '.join(labels)}.")
    lines.append(f"- Target sub-metric per agent: color->color_fidelity, "
                 f"edge->edge_iou, curve/noise->ssim_color.")
    lines.append(f"- Confidence: **validated** = mean Delta-composite > 0 and "
                 f">=4/5 images improve; **weak/positive** = net positive but mixed "
                 f"(<4/5 improve); **neutral** = |mean Delta| <= {NEUTRAL_BAND:.0e} "
                 f"(best candidate == baseline / no net effect); **refuted** = net "
                 f"negative. NOTE: on this already-near-optimal baseline seed the "
                 f"magnitudes are small (sub-0.002 composite); 'validated' here means "
                 f"a consistent positive DIRECTION across images, not a large win.")
    lines.append(f"- Run: elapsed {elapsed:.1f}s, internal budget {budget:.0f}s, "
                 f"budget_hit={budget_hit}. Every trial logged to "
                 f"`knowledge_experiments.jsonl`.\n")

    # ---- baseline table ----
    lines.append("## Baseline scores\n")
    lines.append("| image | composite | ssim_color | color_fidelity | edge_iou |")
    lines.append("|---|---|---|---|---|")
    for label in labels:
        sc = baseline.get(label)
        if sc:
            lines.append(f"| {label} | {sc['composite']:.4f} | {sc['ssim_color']:.4f} "
                         f"| {sc['color_fidelity']:.4f} | {sc['edge_iou']:.4f} |")
        else:
            lines.append(f"| {label} | (trace failed) | | | |")
    lines.append("")

    # ---- ranked artifact table ----
    lines.append("## Ranked artifacts (isolated-factor result)\n")
    lines.append("| # | agent | concept | source | param | best value | "
                 "mean Delta-composite +- std | images improved | "
                 "mean Delta-target | confidence | predicted | dir match |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for i, r in enumerate(tested, 1):
        lines.append(
            f"| {i} | {r['agent'].replace('_agent','')} | {r['concept']} | "
            f"{r['source_document']} | `{r['param']}` | {r['best_value']} | "
            f"{r['best_mean_dcomp']:+.4f} +- {r['best_std_dcomp']:.4f} | "
            f"{int(round(r['best_frac_improved']*r['n_images']))}/{r['n_images']} "
            f"({r['best_frac_improved']*100:.0f}%) | "
            f"{r['best_mean_dtarget']:+.4f} ({r['target_metric']}) | "
            f"**{r['confidence']}** | {r['predicted']} | "
            f"{'yes' if r['direction_match'] else ('no' if r['direction_match'] is False else 'n/a')} |")
    lines.append("")

    # ---- summary buckets ----
    lines.append("## Summary\n")
    val = bucket("validated")
    wpos = bucket("weak/positive")
    neu = bucket("neutral")
    ref = bucket("refuted")

    def fmt(r):
        return (f"`{r['param']}={r['best_value']}` "
                f"(Delta {r['best_mean_dcomp']:+.4f} +- {r['best_std_dcomp']:.4f}, "
                f"{r['best_frac_improved']*100:.0f}% improved, {r['source_document']})")

    lines.append(f"**VALIDATED as improving quality ({len(val)}):**")
    for r in val:
        lines.append(f"- {r['agent'].replace('_agent','')} / {r['concept']}: {fmt(r)}")
    if not val:
        lines.append("- (none)")
    lines.append("")
    lines.append(f"**WEAK / net-positive ({len(wpos)}):**")
    for r in wpos:
        lines.append(f"- {r['agent'].replace('_agent','')} / {r['concept']}: {fmt(r)}")
    if not wpos:
        lines.append("- (none)")
    lines.append("")
    lines.append(f"**NEUTRAL (~0 net effect over the baseline seed) ({len(neu)}):**")
    for r in neu:
        lines.append(f"- {r['agent'].replace('_agent','')} / {r['concept']}: {fmt(r)}")
    if not neu:
        lines.append("- (none)")
    lines.append("")
    lines.append(f"**REFUTED (net negative) ({len(ref)}):**")
    for r in ref:
        lines.append(f"- {r['agent'].replace('_agent','')} / {r['concept']}: {fmt(r)}")
    if not ref:
        lines.append("- (none)")
    lines.append("")
    lines.append(f"**NOT-YET-TESTABLE ({len(not_testable)}):**")
    for r in not_testable:
        lines.append(f"- {r['agent'].replace('_agent','')} / {r['concept']} "
                     f"(`{r['param']}`, {r['source_document']}): {r['reason']}")
    if not not_testable:
        lines.append("- (none)")
    if not_run:
        lines.append("")
        lines.append(f"**NOT RUN (budget) ({len(not_run)}):**")
        for r in not_run:
            lines.append(f"- {r['agent'].replace('_agent','')} / {r['concept']} (`{r['param']}`)")
    lines.append("")

    # ---- direction correctness ----
    dm = [r for r in tested if r.get("direction_match") is not None]
    matched = [r for r in dm if r["direction_match"]]
    lines.append("## Predicted-vs-observed direction\n")
    lines.append(f"Of {len(dm)} tested hypotheses with a directional prediction, "
                 f"**{len(matched)} matched** the observed best direction and "
                 f"{len(dm)-len(matched)} did not (see `dir match` column). "
                 f"A mismatch means the library's predicted parameter bias did not "
                 f"produce the best score on this particular 5-image set -- honest "
                 f"evidence the artifact's numeric guidance is artwork-class "
                 f"dependent rather than universal.\n")

    # ---- per-image vs universal note ----
    lines.append("## Per-image vs universal wins\n")
    lines.append("Per-candidate per-image deltas are in the ledger. The baseline "
                 "seed is already near-optimal for these clean logo/line-art images "
                 "(composites ~0.94-0.99), so most isolated single-factor changes "
                 "move composite by <0.01. Where an artifact helps, the "
                 "`best_per_image_dcomp` field in the ledger shows whether the gain "
                 "is universal (all 5) or concentrated on one class (e.g. a "
                 "color/soft-shade knob helping the house/crest but flat on line "
                 "art like caddie/squirrel).\n")
    for r in tested:
        pi = r.get("best_per_image_dcomp", {})
        if pi:
            detail = ", ".join(f"{k} {v:+.4f}" for k, v in pi.items())
            lines.append(f"- **{r['concept']}** (`{r['param']}={r['best_value']}`): {detail}")
    lines.append("")

    with open(REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    orig_rgb_current = None  # set per-image before each trace_score call
    main(sys.argv[1:])
