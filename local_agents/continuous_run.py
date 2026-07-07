#!/usr/bin/env python3
"""continuous_run.py — EMBIZ continuous perfection orchestrator.

The heart of the "run it over and over until it is perfect" request. For every
raster image dropped into ``input_images/`` this orchestrator runs a perfection
loop over many EPOCHS. One epoch =

  1. Maya    : vectorizer refinement (vectorizer.optimize, ~300 hill-climb
               iterations per start per epoch; every attempt appended to
               ``vectorization_attempts.jsonl`` by vectorizer itself)
  2.           best SVG -> ``vectorized_svg/<stem>.svg`` -> rasterized at 600px
  3. Marnie  : digitizer.process_images() -> EXP/PES/preview/JSON sidecar in
               ``stitch_plans/`` + the 5x5in ruler/grid production layout
               JPEGs in ``production_runs/<stem>/``
  4. Margo   : posts the production layout JPEG (the ruler/grid image) to Slack
  5. Mercy   : QA verdict from the composite score (SSIM/edge/color/collapse)
  6. Mabel   : parameter learnings from parameter_correlation_index_vec.json
  7. Mira    : milestone detection/posting; Minerva: agent meetings

Convergence policy per image: keep looping epochs (hundreds -> thousands of
total vectorizer iterations) until ``target_ssim`` (default 0.98) is reached
or the best composite has not improved for ``stall_epochs`` (default 5)
consecutive epochs.

State is checkpointed to ``local_agents/state/continuous_run_state.json``
after EVERY epoch, so the run can stop and resume anywhere — this container
or the Mint machine (systemd unit: embiz-continuous-run.service,
Restart=always, so it truly runs over and over continuously).

Milestones -> ``reports/milestones.jsonl`` (+ Slack #embiz-milestones):
  * first_epoch_complete   per image
  * new_best_score         per image
  * target_reached         per image
  * all_images_pass        once all scanned images reach target
  * epoch_century          every 100 global epochs

Agent meetings -> ``reports/agent_meetings.jsonl`` (+ Slack #embiz-meetings):
every ``--meeting-interval`` epochs (default 25) and at every milestone.
Meeting reasoning goes through model_router (qwen3:8b locally); when no
Ollama/paid rung is available (e.g. THIS container) it falls back — explicitly
and non-fatally — to a deterministic template meeting.

CLI:
  python local_agents/continuous_run.py \
      [--epochs-budget N] [--time-budget-min M] [--images a.png b.png] \
      [--target-ssim 0.98] [--stall-epochs 5] [--iters-per-epoch 300] \
      [--meeting-interval 25]

With no budget flags the run is UNBOUNDED: when every image has converged it
idles and rescans ``input_images/`` for new work forever (the persistent
systemd mode). Budget flags bound a pass for CI/demo containers.
"""

from __future__ import annotations

import argparse
import datetime
import glob as globmod
import io
import json
import os
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent          # local_agents/
REPO_ROOT = Path(os.environ.get("EMBIZ_REPO_ROOT", _HERE.parent))
for p in (str(REPO_ROOT), str(_HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)

import vectorizer   # noqa: E402  repo-root module
import digitizer    # noqa: E402  repo-root module
from personas import CHANNELS, PERSONAS, post_as   # noqa: E402

STATE_DIR = Path(os.environ.get("EMBIZ_STATE_DIR", _HERE / "state"))
STATE_FILE = STATE_DIR / "continuous_run_state.json"
WORK_DIR = STATE_DIR / "continuous_run_work"

INPUT_DIR = REPO_ROOT / "input_images"
REPORTS_DIR = REPO_ROOT / "reports"
MILESTONES_LOG = REPORTS_DIR / "milestones.jsonl"
MEETINGS_LOG = REPORTS_DIR / "agent_meetings.jsonl"
PROD_DIR = REPO_ROOT / "production_runs"
STITCH_DIR = REPO_ROOT / "stitch_plans"
VEC_INDEX = REPO_ROOT / "parameter_correlation_index_vec.json"

RASTER_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".heic", ".bmp", ".gif"}
RASTER_WIDTH = 600            # SVG re-raster width fed to the digitizer
IMPROVE_EPS = 1e-4            # composite delta that counts as "improved"
CENTURY = 100                 # global-epoch milestone interval
IDLE_RESCAN_S = 60            # unbounded mode: rescan input_images this often

MIRA = PERSONAS["mira"]
MAYA = PERSONAS["maya"]
MARNIE = PERSONAS["marnie"]
MERCY = PERSONAS["mercy"]
MABEL = PERSONAS["mabel"]
MARGO = PERSONAS["margo"]
MINERVA = PERSONAS["minerva"]


def _utcnow() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _append_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# State (checkpointed after every epoch -> resumable anywhere)
# ---------------------------------------------------------------------------
def load_state(target_ssim: float, stall_epochs: int) -> dict:
    if STATE_FILE.exists():
        try:
            state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            state.setdefault("images", {})
            state.setdefault("global_epochs", 0)
            state["target_ssim"] = target_ssim
            state["stall_epochs"] = stall_epochs
            return state
        except ValueError:
            pass  # corrupt checkpoint -> start fresh (old file overwritten)
    return {
        "created": _utcnow(),
        "target_ssim": target_ssim,
        "stall_epochs": stall_epochs,
        "global_epochs": 0,
        "all_images_pass_announced": False,
        "images": {},
    }


def save_state(state: dict) -> None:
    state["updated"] = _utcnow()
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2), encoding="utf-8")
    tmp.replace(STATE_FILE)


def scan_inputs(only: list[str] | None = None) -> list[Path]:
    """Raster images in input_images/ (optionally restricted to --images)."""
    if not INPUT_DIR.exists():
        return []
    imgs = sorted(p for p in INPUT_DIR.iterdir()
                  if p.suffix.lower() in RASTER_EXTS and p.is_file())
    if only:
        wanted = {os.path.basename(x) for x in only}
        imgs = [p for p in imgs if p.name in wanted]
    return imgs


def _stem(path: Path) -> str:
    return digitizer._stem_from_path(str(path))


# ---------------------------------------------------------------------------
# Epoch pipeline pieces
# ---------------------------------------------------------------------------
def rasterize_best_svg(svg_path: Path, stem: str) -> Path | None:
    """Best SVG -> 600px raster (white background) for the digitizer."""
    import cairosvg
    from PIL import Image
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    out = WORK_DIR / f"{stem}.png"
    try:
        png = cairosvg.svg2png(url=str(svg_path), output_width=RASTER_WIDTH)
        img = Image.open(io.BytesIO(png)).convert("RGBA")
        bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
        bg.alpha_composite(img)
        bg.convert("RGB").save(out)
        return out
    except Exception as exc:  # noqa: BLE001
        post_as(MARNIE, CHANNELS["alerts"],
                text=f"SVG re-raster failed for {stem}: {exc}")
        return None


def digitize_epoch(raster: Path, stem: str) -> list[tuple]:
    """Run the digitizer on this epoch's raster. Clears the previous epoch's
    outputs for this stem first (digitizer.process_images is idempotent by
    stem and would otherwise skip)."""
    for f in globmod.glob(str(STITCH_DIR / f"{stem}_*")):
        try:
            os.remove(f)
        except OSError:
            pass
    return digitizer.process_images([str(raster)])


def production_jpeg(stem: str) -> str | None:
    """The 5x5in ruler/grid stitch-out JPEG for this stem (Margo's image)."""
    for name in ("3_stitchplan_on_ruler.jpg", "2_svg_on_ruler.jpg",
                 "1_original_on_ruler.jpg"):
        hits = sorted(globmod.glob(str(PROD_DIR / f"{stem}*" / name)))
        if hits:
            return hits[0]
    return None


def mabel_learnings(vec_result: dict) -> str:
    """Parameter learnings for this image's feature bucket from the
    correlation index (Mabel keeps this current — vectorizer updates it)."""
    bucket = vec_result.get("feature_bucket", "?")
    try:
        index = json.loads(VEC_INDEX.read_text(encoding="utf-8"))
        entry = index.get(bucket)
        if entry:
            params = entry.get("params", {})
            keys = ("mode", "color_precision", "filter_speckle",
                    "corner_threshold", "layer_difference", "hierarchical")
            brief = ", ".join(f"{k}={params[k]}" for k in keys if k in params)
            return (f"bucket {bucket}: best composite "
                    f"{entry.get('composite')} with {brief}")
    except (OSError, ValueError):
        pass
    return f"bucket {bucket}: no prior in correlation index yet"


def mercy_verdict(vec_result: dict, stitch_rows: list, target: float) -> dict:
    ssim = vec_result.get("best_ssim", -1.0)
    composite = vec_result.get("best_composite", -1.0)
    collapsed = bool(vec_result.get("best_collapsed"))
    stitches = sum(s.get("stitch_count", 0) for _, _, s in stitch_rows)
    if collapsed:
        grade, note = "FAIL", "collapse guard tripped (flattened render)"
    elif ssim >= target:
        grade, note = "PASS", f"ssim {ssim:.4f} >= target {target}"
    elif composite >= 0.90:
        grade, note = "STRONG", f"composite {composite:.4f}, ssim {ssim:.4f}"
    elif composite >= 0.75:
        grade, note = "OK", f"composite {composite:.4f}, ssim {ssim:.4f}"
    else:
        grade, note = "WEAK", f"composite {composite:.4f} below 0.75 floor"
    return {"grade": grade, "note": note, "ssim": ssim,
            "composite": composite, "collapsed": collapsed,
            "stitch_count": stitches, "objects": len(stitch_rows)}


# ---------------------------------------------------------------------------
# Milestones (Mira announces, Margo attaches the production JPEG)
# ---------------------------------------------------------------------------
def emit_milestone(state: dict, kind: str, stem: str | None, detail: dict,
                   meeting_cb=None) -> None:
    record = {
        "timestamp": _utcnow(),
        "milestone": kind,
        "image": stem,
        "global_epoch": state["global_epochs"],
        **detail,
    }
    _append_jsonl(MILESTONES_LOG, record)

    text = {
        "first_epoch_complete": f"first epoch complete for *{stem}*",
        "new_best_score": f"new best score for *{stem}*",
        "target_reached": f"TARGET REACHED for *{stem}*",
        "all_images_pass": "ALL IMAGES PASS — every input at target",
        "epoch_century": f"global epoch {state['global_epochs']} checkpoint",
    }.get(kind, kind)
    extras = []
    if "best_ssim" in detail:
        extras.append(f"ssim={detail['best_ssim']:.4f}")
    if "best_composite" in detail:
        extras.append(f"composite={detail['best_composite']:.4f}")
    if "epoch" in detail:
        extras.append(f"epoch={detail['epoch']}")
    post_as(MIRA, CHANNELS["milestones"],
            text=f"MILESTONE [{kind}] {text} ({', '.join(extras)})")

    jpeg = production_jpeg(stem) if stem else None
    if jpeg:
        post_as(MARGO, CHANNELS["milestones"],
                text=f"production layout for {stem} at milestone [{kind}]",
                file=jpeg)
    if meeting_cb is not None:
        meeting_cb(f"milestone:{kind}", stem)


# ---------------------------------------------------------------------------
# Agent meetings (Minerva). model_router reasoning with an EXPLICIT
# deterministic-template fallback when no local model is reachable.
# ---------------------------------------------------------------------------
def _meeting_reasoning(agenda: dict) -> tuple[str, str]:
    """Return (summary_text, engine). Tries model_router (qwen3:8b via
    Ollama); in environments with no Ollama (this container) it falls back to
    a deterministic template. The fallback is explicit and non-fatal."""
    prompt = (
        "You are facilitating a short standup of the EMBIZ embroidery agents. "
        "Given this agenda JSON, produce 2-4 sentences: current state, the "
        "single biggest risk, and one concrete parameter action.\n"
        + json.dumps(agenda, default=str)[:4000]
    )
    try:
        import model_router
        text = model_router.route("summarize", prompt)
        return text, "model_router(qwen3:8b ladder)"
    except Exception as exc:  # noqa: BLE001 — includes EscalationExhausted
        worst = min(agenda["scores"], key=lambda s: s["best_composite"],
                    default=None) if agenda.get("scores") else None
        lines = [
            f"Deterministic template meeting (model_router unavailable: "
            f"{type(exc).__name__}).",
            f"{len(agenda.get('scores', []))} image(s) tracked at global "
            f"epoch {agenda.get('global_epoch')}; "
            f"{agenda.get('images_at_target', 0)} at target.",
        ]
        if worst:
            lines.append(
                f"Weakest image is {worst['image']} at composite "
                f"{worst['best_composite']:.4f} (stall {worst['stall']}); "
                f"next action: reseed its hill-climb from the correlation-"
                f"index bucket prior and continue epochs.")
        return " ".join(lines), "deterministic_template"


def hold_meeting(state: dict, reason: str, focus_stem: str | None) -> dict:
    scores = []
    for stem, rec in state["images"].items():
        scores.append({
            "image": stem,
            "epochs": rec["epochs"],
            "best_composite": rec.get("best_composite", -1.0),
            "best_ssim": rec.get("best_ssim", -1.0),
            "stall": rec.get("stall", 0),
            "reached_target": rec.get("reached_target", False),
            "learnings": rec.get("learnings", ""),
        })
    agenda = {
        "reason": reason,
        "focus_image": focus_stem,
        "global_epoch": state["global_epochs"],
        "target_ssim": state["target_ssim"],
        "images_at_target": sum(1 for s in scores if s["reached_target"]),
        "scores": scores,
    }
    summary, engine = _meeting_reasoning(agenda)

    stalled = [s["image"] for s in scores
               if s["stall"] >= max(2, state["stall_epochs"] - 1)
               and not s["reached_target"]]
    decisions = []
    action_items = []
    if stalled:
        decisions.append(
            f"Reseed stalled image(s) {', '.join(stalled)} from their "
            f"correlation-index bucket priors on the next epoch.")
        action_items.append({"owner": "Maya",
                             "item": f"re-run refinement for {', '.join(stalled)}"})
        action_items.append({"owner": "Mabel",
                             "item": "verify bucket priors are current in "
                                     "parameter_correlation_index_vec.json"})
    else:
        decisions.append("Continue epochs unchanged; scores are moving.")
        action_items.append({"owner": "Mira", "item": "continue epoch loop"})
    action_items.append({"owner": "Mercy",
                         "item": "flag any composite < 0.75 in #embiz-qa"})
    action_items.append({"owner": "Margo",
                         "item": "post production layout JPEGs at milestones"})

    meeting = {
        "timestamp": _utcnow(),
        "facilitator": "Minerva",
        "attendees": [p.name for p in PERSONAS.values()],
        "reason": reason,
        "agenda": agenda,
        "summary": summary,
        "reasoning_engine": engine,
        "decisions": decisions,
        "action_items": action_items,
    }
    _append_jsonl(MEETINGS_LOG, meeting)
    post_as(MINERVA, CHANNELS["meetings"],
            text=(f"MEETING ({reason}) — attendees: "
                  f"{', '.join(meeting['attendees'])}. {summary} "
                  f"Decisions: {' | '.join(decisions)}"))
    return meeting


# ---------------------------------------------------------------------------
# One epoch for one image
# ---------------------------------------------------------------------------
def run_epoch(state: dict, path: Path, iters_per_epoch: int) -> dict:
    target = state["target_ssim"]
    stem = _stem(path)
    rec = state["images"].setdefault(stem, {
        "path": str(path), "epochs": 0, "best_composite": -1.0,
        "best_ssim": -1.0, "stall": 0, "reached_target": False,
        "done": False, "history": [],
    })
    epoch = rec["epochs"] + 1
    t0 = time.time()

    post_as(MAYA, CHANNELS["jobs"],
            text=f"epoch {epoch} for {stem}: vectorizer refinement "
                 f"({iters_per_epoch} iters/start, target ssim {target})")
    vec = vectorizer.optimize(str(path), max_iters=iters_per_epoch,
                              target_ssim=target, verbose=False)

    stitch_rows: list = []
    raster = rasterize_best_svg(Path(vec["svg_path"]), stem)
    if raster is not None:
        post_as(MARNIE, CHANNELS["jobs"],
                text=f"epoch {epoch} for {stem}: digitizing best SVG -> "
                     f"EXP/PES/preview + production layout")
        try:
            stitch_rows = digitize_epoch(raster, stem)
        except Exception as exc:  # noqa: BLE001
            post_as(MARNIE, CHANNELS["alerts"],
                    text=f"digitizer failed for {stem} epoch {epoch}: {exc}")

    verdict = mercy_verdict(vec, stitch_rows, target)
    qa_text = (f"{stem} epoch {epoch}: {verdict['grade']} — {verdict['note']}; "
               f"{verdict['stitch_count']} stitches / "
               f"{verdict['objects']} object(s)")
    post_as(MERCY, CHANNELS["qa"], text=qa_text)

    learn = mabel_learnings(vec)
    rec["learnings"] = learn
    post_as(MABEL, CHANNELS["reports"], text=f"{stem}: {learn}")

    jpeg = production_jpeg(stem)
    if jpeg:
        post_as(MARGO, CHANNELS["production"],
                text=f"{stem} epoch {epoch} production layout "
                     f"(5x5in ruler/grid, subject at true 3in)", file=jpeg)

    # ---- convergence bookkeeping ------------------------------------------
    improved = vec["best_composite"] > rec["best_composite"] + IMPROVE_EPS
    first_epoch = (epoch == 1)
    rec["epochs"] = epoch
    rec["stall"] = 0 if improved else rec["stall"] + 1
    if improved:
        rec["best_composite"] = vec["best_composite"]
        rec["best_ssim"] = max(rec["best_ssim"], vec["best_ssim"])
    reached_now = (not rec["reached_target"]) and vec["reached_target"]
    rec["reached_target"] = rec["reached_target"] or vec["reached_target"]
    rec["done"] = rec["reached_target"] or rec["stall"] >= state["stall_epochs"]
    if rec["done"] and not rec["reached_target"]:
        rec["done_reason"] = (f"stalled: no composite improvement for "
                              f"{rec['stall']} epochs")
    elif rec["reached_target"]:
        rec["done_reason"] = "target_reached"
    rec["history"].append({
        "epoch": epoch, "timestamp": _utcnow(),
        "composite": vec["best_composite"], "ssim": vec["best_ssim"],
        "vectorizer_iterations": vec["iterations"],
        "best_start": vec.get("best_start"),
        "qa": verdict["grade"], "stitches": verdict["stitch_count"],
        "duration_s": round(time.time() - t0, 1),
        "production_jpeg": jpeg,
    })
    state["global_epochs"] += 1

    # ---- milestones ---------------------------------------------------------
    meeting_cb = lambda reason, s: hold_meeting(state, reason, s)  # noqa: E731
    common = {"epoch": epoch, "best_ssim": rec["best_ssim"],
              "best_composite": rec["best_composite"],
              "production_jpeg": jpeg}
    if first_epoch:
        emit_milestone(state, "first_epoch_complete", stem, common, meeting_cb)
    if improved and not first_epoch:
        emit_milestone(state, "new_best_score", stem, common, meeting_cb)
    if reached_now:
        emit_milestone(state, "target_reached", stem, common, meeting_cb)
    if state["global_epochs"] % CENTURY == 0:
        emit_milestone(state, "epoch_century", stem, common, meeting_cb)
    all_pass = state["images"] and all(
        r.get("reached_target") for r in state["images"].values())
    if all_pass and not state.get("all_images_pass_announced"):
        state["all_images_pass_announced"] = True
        emit_milestone(state, "all_images_pass", stem,
                       {"images": sorted(state["images"])}, meeting_cb)

    save_state(state)  # checkpoint after EVERY epoch (resume anywhere)
    return rec


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="EMBIZ continuous perfection orchestrator")
    ap.add_argument("--epochs-budget", type=int, default=0,
                    help="max global epochs THIS invocation (0 = unlimited)")
    ap.add_argument("--time-budget-min", type=float, default=0,
                    help="wall-clock budget in minutes (0 = unlimited)")
    ap.add_argument("--images", nargs="*", default=None,
                    help="restrict to these input_images/ basenames")
    ap.add_argument("--target-ssim", type=float, default=0.98)
    ap.add_argument("--stall-epochs", type=int, default=5,
                    help="stop an image after N non-improving epochs")
    ap.add_argument("--iters-per-epoch", type=int, default=300,
                    help="vectorizer hill-climb iteration budget per start "
                         "per epoch")
    ap.add_argument("--meeting-interval", type=int, default=25,
                    help="hold an agent meeting every M global epochs")
    args = ap.parse_args(argv)

    bounded = bool(args.epochs_budget or args.time_budget_min)
    deadline = (time.time() + args.time_budget_min * 60
                if args.time_budget_min else None)
    state = load_state(args.target_ssim, args.stall_epochs)
    epochs_this_run = 0
    last_meeting_epoch = state["global_epochs"]

    post_as(MIRA, CHANNELS["jobs"],
            text=(f"continuous perfection run starting — resume point: "
                  f"global epoch {state['global_epochs']}, "
                  f"budget={'bounded' if bounded else 'UNBOUNDED (systemd)'}"
                  f" (epochs<={args.epochs_budget or 'inf'}, "
                  f"time<={args.time_budget_min or 'inf'}min), "
                  f"target ssim {args.target_ssim}"))

    def out_of_budget() -> bool:
        if args.epochs_budget and epochs_this_run >= args.epochs_budget:
            return True
        if deadline and time.time() >= deadline:
            return True
        return False

    try:
        while True:
            images = scan_inputs(args.images)
            if not images:
                post_as(MIRA, CHANNELS["alerts"],
                        text="no raster images found in input_images/ — "
                             "drop files there to start perfection loops")
                if not bounded:
                    time.sleep(IDLE_RESCAN_S)
                    continue
                break

            pending = [p for p in images
                       if not state["images"].get(_stem(p), {}).get("done")]
            if not pending:
                post_as(MIRA, CHANNELS["jobs"],
                        text=(f"all {len(images)} image(s) converged "
                              f"(target or stall). "
                              + ("Idling; rescanning input_images/ every "
                                 f"{IDLE_RESCAN_S}s." if not bounded
                                 else "Bounded pass complete.")))
                if not bounded:
                    time.sleep(IDLE_RESCAN_S)
                    continue
                break

            # Round-robin: one epoch per unfinished image per pass, so every
            # image gets first-epoch coverage before deep refinement.
            progressed = False
            for path in pending:
                if out_of_budget():
                    break
                run_epoch(state, path, args.iters_per_epoch)
                epochs_this_run += 1
                progressed = True
                if (state["global_epochs"] - last_meeting_epoch
                        >= args.meeting_interval):
                    last_meeting_epoch = state["global_epochs"]
                    hold_meeting(state, f"interval:{args.meeting_interval}",
                                 None)
            if out_of_budget() or not progressed:
                break
    except KeyboardInterrupt:
        post_as(MIRA, CHANNELS["alerts"],
                text="continuous run interrupted — state checkpointed, "
                     "safe to resume")
    finally:
        save_state(state)

    done = sum(1 for r in state["images"].values() if r.get("reached_target"))
    post_as(MIRA, CHANNELS["jobs"],
            text=(f"run pass ended: {epochs_this_run} epoch(s) this "
                  f"invocation, global epoch {state['global_epochs']}, "
                  f"{done}/{len(state['images'])} image(s) at target. "
                  f"State: {STATE_FILE.name} (resumable)"))

    print("\n=== continuous run summary ===")
    print(f"{'image':<20} {'epochs':>6} {'best_ssim':>10} "
          f"{'best_comp':>10} {'target':>7} {'done':>5}")
    for stem, rec in sorted(state["images"].items()):
        print(f"{stem:<20} {rec['epochs']:>6} {rec['best_ssim']:>10.4f} "
              f"{rec['best_composite']:>10.4f} "
              f"{str(rec['reached_target']):>7} {str(rec['done']):>5}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
