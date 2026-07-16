"""production_pipeline.py — the canonical EMBIZ production pipeline, end to end.

Drives every stage of the BRD's canonical pipeline for every raster in
``input_images/`` (BRD § "Production Pipeline Architecture"):

  intake (Madeline) -> artwork review + complexity (Mackenzie) ->
  knowledge retrieval -> vectorization with Bayesian-seeded exploration
  (Mila) -> locked archival tracing layer -> SVG topology QA (Melanie) ->
  production export (archival layer stripped) -> digitization with underlay /
  pull compensation / satin / trims / color-block optimization (Mckenna /
  Meredith) -> density + stitch QA (Margaret) -> B700 hoop & companion check
  (Miranda) -> dual-size export -> contract-structured approval / rejection
  events (Mallory) -> job status transitions with audit -> dashboard refresh.

Each pass writes a machine-readable summary to ``reports/e2e/pass_<n>.json``;
``scripts/regression_check.py`` compares consecutive passes and appends
verdicts to ``reports/regression_history.jsonl``.

Usage:
  python3 production_pipeline.py --build-corpus          # populate input_images/
  python3 production_pipeline.py --pass-id 1 [--limit N] [--budget 6]
"""

from __future__ import annotations

import argparse
import datetime
import json
import shutil
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "local_agents"))

import digitizer                    # noqa: E402
import ihive                        # noqa: E402
import svg_topology_qa              # noqa: E402
import vectorizer                   # noqa: E402
from local_agents import jobs as jobs_mod          # noqa: E402
from local_agents.agent_bus import (alert_event, approval_event,  # noqa: E402
                                    rejection_event, status_event)
from local_agents.intake import run_intake          # noqa: E402

INPUT_DIR = REPO / "input_images"
E2E_DIR = REPO / "reports" / "e2e"


def _utcnow() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def build_corpus() -> int:
    """Populate input_images/ (gitignored by design — sources never
    committed) from committed repository artifacts: production-run originals
    and stitch-plan previews. Yields a several-dozen-image corpus."""
    INPUT_DIR.mkdir(exist_ok=True)
    n = 0
    for d in sorted((REPO / "production_runs").iterdir()):
        src = d / "1_original_on_ruler.jpg"
        if src.exists():
            dst = INPUT_DIR / f"{d.name}_original.jpg"
            if not dst.exists():
                shutil.copy2(src, dst)
            n += 1
    for src in sorted((REPO / "stitch_plans").glob("*_preview.png")):
        dst = INPUT_DIR / src.name.replace("_preview", "")
        if not dst.exists():
            shutil.copy2(src, dst)
        n += 1
    return n


def scan_corpus(limit: int = 0) -> list[Path]:
    imgs = sorted(p for p in INPUT_DIR.iterdir()
                  if p.suffix.lower() in (".png", ".jpg", ".jpeg"))
    return imgs[:limit] if limit else imgs


def process_image(img: Path, pass_id: int, budget: int, out_dir: Path) -> dict:
    """One image through the complete pipeline. Never raises; every failure
    is a rejection/alert with evidence."""
    row = {"image": img.name, "pass": pass_id, "started": _utcnow()}
    # --- intake (Madeline) ---------------------------------------------------
    job = run_intake(img)
    jid = row["job_id"] = job["job_id"]
    analysis = json.loads((jobs_mod._job_dir(jid) / "intake_analysis.json")
                          .read_text(encoding="utf-8"))
    complexity = analysis["complexity"]
    row["complexity"] = complexity["band"]
    row["suitability"] = (analysis["reviews"][0]["embroidery_suitability"]
                          if analysis["reviews"] else None)
    if job["status"] == "needs_customer_info":
        # File drops carry no order text; requirements come from defaults.
        jobs_mod.transition(jid, "artwork_needed", actor="madeline",
                            reason="file-drop corpus run: standard 3in defaults assumed")
        jobs_mod.transition(jid, "artwork_received", actor="madeline")
    jobs_mod.transition(jid, "artwork_review", actor="mackenzie")

    # --- vectorization (Mila), Bayesian-seeded -------------------------------
    iters = min(budget, complexity["experiment_budget_iters"])
    seeds = ihive.bayes_rank_candidates(top_k=3)
    extra = [(f"bayes_{i}", s["params"]) for i, s in enumerate(seeds, 1)]
    res = vectorizer.optimize(str(img), max_iters=iters,
                              target_ssim=complexity["qa_ssim_floor"],
                              verbose=False, extra_starts=extra or None)
    row["ssim"] = res["best_scores"]["ssim_color"]
    row["composite"] = res["best_composite"]
    row["vector_iters"] = res.get("iterations", iters)
    svg = Path(res["svg_path"])
    status_event("mila", jid, svg.name, "transformed",
                 f"ssim {row['ssim']:.4f} (floor {complexity['qa_ssim_floor']})")

    # --- locked archival layer + topology QA (Melanie) ------------------------
    work_svg = out_dir / f"{img.stem}_work.svg"
    ihive.add_locked_tracing_layer(svg, img, work_svg)
    prod_svg = out_dir / f"{img.stem}_production.svg"
    ihive.strip_archival_layers(work_svg, prod_svg)
    cleanup = ihive.cleanup_svg(prod_svg)
    row["svg_paths_deduped"] = cleanup["paths_removed"]
    qa = svg_topology_qa.run_qa(prod_svg, img,
                                report_path=out_dir / f"{img.stem}_svg_qa.json")
    row["svg_qa_ok"] = qa["ok"]
    row["svg_qa_blocking"] = qa["blocking_failures"]
    if not qa["ok"]:
        rejection_event("melanie", jid,
                        failed_gate=f"svg topology: {qa['blocking_failures']}",
                        defect=json.dumps({k: qa['checks'][k]
                                           for k in qa["blocking_failures"]})[:200],
                        likely_cause="vectorization artifacts",
                        file=prod_svg.name, next_action="re-vectorize (Mila)")
        jobs_mod.transition(jid, "blocked", actor="melanie",
                            reason="svg topology QA failed")
        row["finished"] = _utcnow()
        return row
    jobs_mod.transition(jid, "artwork_approved", actor="mackenzie",
                        svg_state="approved")
    approval_event("mackenzie", jid,
                   what_checked="SVG topology (8 automated checks) + silhouette",
                   how_checked="svg_topology_qa.run_qa against source raster",
                   why_passed=f"no blocking failures; ssim {row['ssim']:.4f}",
                   files=[prod_svg.name], next_owner="mckenna")

    # --- digitization (Mckenna/Meredith) --------------------------------------
    jobs_mod.transition(jid, "digitizing_plan", actor="mckenna")
    jobs_mod.transition(jid, "digitizing_in_progress", actor="meredith")
    old_out = digitizer.OUT_DIR
    digitizer.OUT_DIR = str(out_dir / "stitch")
    try:
        rows = digitizer.process_images([str(img)])
    finally:
        digitizer.OUT_DIR = old_out
    if not rows:
        alert_event("meredith", "production_failure",
                    f"digitizer produced no objects for {img.name}", jid)
        jobs_mod.transition(jid, "blocked", actor="meredith",
                            reason="no digitizable objects")
        row["finished"] = _utcnow()
        return row
    jobs_mod.transition(jid, "stitch_file_ready", actor="meredith",
                        stitch_file_state="exported")

    # --- stitch QA (Margaret) + machine compatibility (Miranda) ----------------
    jobs_mod.transition(jid, "qa_review", actor="margaret")
    densities, hoops, files = [], [], []
    dual_ok = False
    for stem, label, stats in rows:
        densities.append(stats["density"])
        sidecar = Path(digitizer.OUT_DIR)  # not used; stats carry everything
        files.append(f"{stem}_{label}.exp")
        hoops.append(digitizer.check_hoop_fit(stats["width_mm"],
                                              stats["height_mm"]))
        if label.endswith("_5in"):
            dual_ok = True
    stitch_dir = out_dir / "stitch"
    dual_ok = dual_ok or any(stitch_dir.glob("*_5in.exp"))
    companions_ok = all(
        (stitch_dir / f).with_suffix(".inf").exists()
        and (stitch_dir / f).with_suffix(".bmp").exists()
        for f in files if (stitch_dir / f).exists())
    density_ok = all(d["ok"] for d in densities)
    hoop_ok = all(h["fits"] for h in hoops)
    row.update({
        "objects": len(rows),
        "max_density": max(d["max_local_density_per_mm2"] for d in densities),
        "density_ok": density_ok,
        "underlay_runs": sum(s.get("underlay_runs", 0) for _, _, s in rows),
        "hoop_ok": hoop_ok,
        "smallest_hoop": hoops[0]["smallest_hoop"] if hoops else None,
        "dual_size_export": dual_ok,
        "companions_ok": companions_ok,
        "stitch_count": sum(s["stitch_count"] for _, _, s in rows),
    })
    if not (density_ok and hoop_ok):
        gate = "density" if not density_ok else "hoop fit"
        rejection_event("margaret" if not density_ok else "miranda", jid,
                        failed_gate=gate,
                        defect=f"max density {row['max_density']}/mm² or hoop miss",
                        likely_cause="fill density vs B700 limits",
                        file=files[0] if files else img.name,
                        next_action="re-digitize with wider spacing")
        jobs_mod.transition(jid, "blocked", actor="margaret",
                            reason=f"{gate} gate failed")
        row["finished"] = _utcnow()
        return row
    jobs_mod.transition(jid, "qa_passed", actor="margaret", qa_state="passed",
                        machine_compatibility_state="b700_ok")
    approval_event("margaret", jid,
                   what_checked=("stitch density (limit "
                                 f"{digitizer.MAX_LOCAL_DENSITY_PER_MM2}/mm²), "
                                 "hoop fit, EXP+INF+BMP companions, dual-size"),
                   how_checked="digitizer density report + check_hoop_fit + file census",
                   why_passed=(f"max density {row['max_density']}/mm² PASS; "
                               f"hoop {row['smallest_hoop']}; companions "
                               f"{'present' if companions_ok else 'partial'}"),
                   files=files, next_owner="miranda")
    jobs_mod.transition(jid, "customer_approval_needed", actor="maya")
    row["final_status"] = jobs_mod.load_job(jid)["status"]
    row["finished"] = _utcnow()
    return row


def run_pass(pass_id: int, limit: int = 0, budget: int = 8) -> dict:
    imgs = scan_corpus(limit)
    if not imgs:
        raise SystemExit("input_images/ is empty — run --build-corpus first")
    out_dir = E2E_DIR / f"pass_{pass_id:02d}"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "stitch").mkdir(exist_ok=True)
    rows = []
    for i, img in enumerate(imgs, 1):
        print(f"[pass {pass_id}] {i}/{len(imgs)} {img.name}", flush=True)
        try:
            rows.append(process_image(img, pass_id, budget, out_dir))
        except Exception as exc:  # every failure becomes evidence, not a crash
            alert_event("maya", "pipeline_interruption",
                        f"{img.name}: {type(exc).__name__}: {exc}")
            rows.append({"image": img.name, "pass": pass_id,
                         "error": f"{type(exc).__name__}: {exc}"})
    done = [r for r in rows if r.get("final_status")]
    summary = {
        "pass": pass_id, "timestamp": _utcnow(), "images": len(rows),
        "completed": len(done),
        "blocked_or_error": len(rows) - len(done),
        "mean_ssim": round(sum(r["ssim"] for r in rows if "ssim" in r)
                           / max(1, sum(1 for r in rows if "ssim" in r)), 4),
        "mean_composite": round(sum(r["composite"] for r in rows
                                    if "composite" in r)
                                / max(1, sum(1 for r in rows
                                             if "composite" in r)), 4),
        "density_pass_rate": round(sum(1 for r in rows if r.get("density_ok"))
                                   / max(1, len(rows)), 4),
        "dual_size_rate": round(sum(1 for r in rows
                                    if r.get("dual_size_export"))
                                / max(1, len(rows)), 4),
        "companion_rate": round(sum(1 for r in rows if r.get("companions_ok"))
                                / max(1, len(rows)), 4),
        "rows": rows,
    }
    (E2E_DIR / f"pass_{pass_id:02d}.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    # dashboard refresh is part of the pass (BRD: observability)
    from local_agents import dashboard
    dashboard.generate()
    print(f"[pass {pass_id}] images={summary['images']} "
          f"completed={summary['completed']} mean_ssim={summary['mean_ssim']} "
          f"density_pass={summary['density_pass_rate']}")
    return summary


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--build-corpus", action="store_true")
    ap.add_argument("--pass-id", type=int, default=1)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--budget", type=int, default=8)
    args = ap.parse_args()
    if args.build_corpus:
        print(f"corpus images: {build_corpus()}")
    else:
        run_pass(args.pass_id, args.limit, args.budget)
