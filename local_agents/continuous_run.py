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
or the best composite has not improved for ``stall_epochs`` (default 10)
consecutive epochs. Epochs after a non-improving one are STALL-BREAK epochs:
the deterministic preset starts are skipped and jittered + pure-random
restarts (seeded per image+epoch, radius escalating with the stall count)
are injected, so continued epochs actually explore new parameter regions
instead of repeating byte-identical greedy descents.

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
  * production_run_finalized  per image, once ALL finalization criteria hold:
      hundreds of attempts w/ different method combos, convergence, satin-fill
      borders passing the B700 density guardrails, and a knowledge-fetch pass.
      Emits the FINAL Slack production message (Margo) with the three ruler
      JPEGs attached as native image uploads (drafted locally when no Slack).

Agent meetings -> ``reports/agent_meetings.jsonl`` (+ Slack #embiz-meetings):
every ``--meeting-interval`` epochs (default 25) and at every milestone.
Meeting reasoning goes through model_router (qwen3:8b locally); when no
Ollama/paid rung is available (e.g. THIS container) it falls back — explicitly
and non-fatally — to a deterministic template meeting.

CLI:
  python local_agents/continuous_run.py \
      [--epochs-budget N] [--time-budget-min M] [--images a.png b.png] \
      [--target-ssim 0.98] [--stall-epochs 10] [--iters-per-epoch 300] \
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
import random
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

# --- stall-breaking exploration -------------------------------------------
# Without this, epochs are DETERMINISTIC: the vectorizer's multi-start list is
# fixed (DOCTRINE_SEED presets + the correlation-index prior, which is the
# image's OWN previous best), and coordinate descent is greedy, so a stalled
# image repeats byte-identical epochs forever. When rec["stall"] >= 1 the next
# epoch injects jittered + random restarts (RNG seeded from image+epoch, so
# runs are reproducible but each epoch explores differently) and drops the
# already-exhausted preset starts.
STALL_JITTER_STARTS = 4       # jittered variants of the best-known params
STALL_RANDOM_STARTS = 2       # pure random samples from PARAM_GRID
STALL_ESCALATE_AT = 3         # stall count at which exploration widens
DEFAULT_STALL_EPOCHS = 10     # raised from 5: stalled epochs now differ
KNOWLEDGE_VEC_DIR = REPO_ROOT / "knowledge" / "vectorization"
STALL_WINS_LOG = KNOWLEDGE_VEC_DIR / "stall_break_wins.jsonl"

# --- production-run finalization -------------------------------------------
# A production run is FINALIZED only when ALL of:
#   1. attempts   : >= FINALIZE_MIN_ATTEMPTS vectorizer attempts accumulated
#                   across epochs with different method combinations (the
#                   stall-break jitter/random starts provide the diversity);
#                   BYPASSED when the image reached the SSIM target — target
#                   reached = perfection reached, no more attempts needed,
#   2. convergence: the image is done — target reached or stalled out, i.e.
#                   further improvement makes no visible difference,
#   3. stitch     : the regenerated stitch plan uses SATIN FILL borders and
#                   passes the B700 density guardrails (digitizer's
#                   _density_report: local density <= 1.2 stitches/mm^2,
#                   satin width 1-7 mm, spacing floor 0.35 mm),
#   4. knowledge  : Mabel loaded every knowledge modular object + the
#                   correlation indexes and recorded what was consulted.
# On finalization: `production_run_finalized` milestone + a FINAL Slack
# message (Margo -> #embiz-production) with the three ruler JPEGs attached as
# NATIVE image uploads (slack_sdk files_upload_v2, multi-file, one message).
# Without Slack tokens the exact payload is drafted to the agent feed and
# reports/slack_messages/.
FINALIZE_MIN_ATTEMPTS = 200
SLACK_DRAFTS_DIR = REPORTS_DIR / "slack_messages"
RULER_JPEGS = ("1_original_on_ruler.jpg", "2_svg_on_ruler.jpg",
               "3_stitchplan_on_ruler.jpg")

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
            # Re-activate images stalled out under a LOWER stall limit: with
            # stall-breaking, continued epochs explore differently, so give
            # them the (raised) allowance again.
            for rec in state["images"].values():
                if (rec.get("done") and not rec.get("reached_target")
                        and rec.get("stall", 0) < stall_epochs):
                    rec["done"] = False
                    rec.pop("done_reason", None)
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
        "production_run_finalized": f"PRODUCTION RUN FINALIZED for *{stem}*",
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
        # Short-circuit: when Ollama is plainly unreachable (e.g. THIS
        # container has no GPU/Ollama) skip the retry ladder instead of
        # burning ~30s of connection retries per meeting.
        from qwen_client import ollama_alive
        if not ollama_alive():
            raise RuntimeError("ollama unreachable (pre-check)")
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
# Stall-breaking exploration (jittered + random restarts)
# ---------------------------------------------------------------------------
def _jitter_params(base: dict, radius: int, rng: random.Random) -> dict:
    """Perturb each PARAM_GRID factor of `base` by +/-1..radius grid steps
    (categorical factors flip with probability proportional to radius)."""
    p = dict(base)
    for name, ladder in vectorizer.PARAM_GRID.items():
        cur = p.get(name, ladder[len(ladder) // 2])
        if isinstance(cur, str) or isinstance(ladder[0], str):
            if rng.random() < 0.25 * radius:
                others = [v for v in ladder if v != cur]
                if others:
                    p[name] = rng.choice(others)
            continue
        if cur in ladder:
            i = ladder.index(cur)
        else:  # off-grid value -> nearest rung
            i = min(range(len(ladder)), key=lambda j: abs(ladder[j] - cur))
        step = rng.choice([-1, 1]) * rng.randint(1, max(1, radius))
        p[name] = ladder[max(0, min(len(ladder) - 1, i + step))]
    return p


def _random_params(base: dict, rng: random.Random) -> dict:
    """Uniform random sample of every PARAM_GRID factor (non-grid keys such
    as colormode/hierarchical are inherited from `base`)."""
    p = dict(base)
    for name, ladder in vectorizer.PARAM_GRID.items():
        p[name] = rng.choice(ladder)
    return p


def _stall_base_params(rec: dict, path: Path) -> dict:
    """Best-known params for this image: from state if recorded, else the
    correlation-index bucket prior (the image's own previous winner)."""
    if rec.get("best_params"):
        return dict(rec["best_params"])
    try:
        feat = vectorizer.image_features(str(path))
        params, _src = vectorizer._seed_from_index(feat)
        return dict(params)
    except Exception:  # noqa: BLE001
        return dict(vectorizer.DOCTRINE_SEED["default"])


def plan_stall_break(state: dict, rec: dict, stem: str, path: Path,
                     epoch: int) -> list[tuple]:
    """Build the injected start list for a stalled image's next epoch and
    record the decision as a Minerva meeting entry. Escalates with stall:
    stall < STALL_ESCALATE_AT -> radius 1; else radius 2 + more randoms."""
    stall = rec.get("stall", 0)
    radius = 1 if stall < STALL_ESCALATE_AT else 2
    n_jitter = STALL_JITTER_STARTS
    n_random = (STALL_RANDOM_STARTS if stall < STALL_ESCALATE_AT
                else STALL_RANDOM_STARTS + 2)
    # Seeded from image + epoch number: reproducible run-to-run, but every
    # epoch explores a DIFFERENT region (this is what breaks determinism).
    rng = random.Random(f"{stem}:epoch{epoch}")
    base = _stall_base_params(rec, path)
    extra = []
    for i in range(n_jitter):
        extra.append((f"stall{stall}_jitter{i}_r{radius}",
                      _jitter_params(base, radius, rng)))
    for i in range(n_random):
        extra.append((f"stall{stall}_random{i}", _random_params(base, rng)))

    decision = (f"stall {stall} on {stem}: injecting {n_jitter} jittered + "
                f"{n_random} random starts, radius {radius}")
    meeting = {
        "timestamp": _utcnow(),
        "facilitator": "Minerva",
        "attendees": [MAYA.name, MABEL.name, MERCY.name, MINERVA.name],
        "reason": f"stall_break:{stem}",
        "global_epoch": state["global_epochs"],
        "image": stem,
        "epoch": epoch,
        "stall": stall,
        "decisions": [decision],
        "action_items": [
            {"owner": "Maya",
             "item": f"run stall-break epoch {epoch} for {stem} with the "
                     f"injected starts (preset starts skipped)"},
            {"owner": "Mabel",
             "item": "log a knowledge note if an injected start beats the "
                     "previous best"},
        ],
        "injected_starts": [lbl for lbl, _ in extra],
    }
    _append_jsonl(MEETINGS_LOG, meeting)
    post_as(MINERVA, CHANNELS["meetings"],
            text=f"MEETING (stall-break) — {decision}")
    return extra


def mabel_stall_break_note(stem: str, epoch: int, prev_best: float,
                           vec: dict) -> None:
    """Knowledge note when a stall-break (jittered/random) start beats the
    previous best: what start won, what the params were, score delta."""
    KNOWLEDGE_VEC_DIR.mkdir(parents=True, exist_ok=True)
    note = {
        "timestamp": _utcnow(),
        "event": "stall_break_improvement",
        "image": stem,
        "epoch": epoch,
        "winning_start": vec.get("best_start"),
        "prev_best_composite": prev_best,
        "new_best_composite": vec.get("best_composite"),
        "new_best_ssim": vec.get("best_ssim"),
        "feature_bucket": vec.get("feature_bucket"),
        "winning_params": vec.get("best_params"),
    }
    _append_jsonl(STALL_WINS_LOG, note)
    post_as(MABEL, CHANNELS["reports"],
            text=(f"{stem}: stall-break start {vec.get('best_start')} beat "
                  f"the previous best (composite {prev_best:.4f} -> "
                  f"{vec.get('best_composite'):.4f}); params recorded in "
                  f"knowledge/vectorization/{STALL_WINS_LOG.name} and the "
                  f"correlation index"))


# ---------------------------------------------------------------------------
# Production-run finalization
# ---------------------------------------------------------------------------
def _ruler_jpegs(stem: str) -> list[str]:
    """The three 5x5in ruler/grid review JPEGs for this stem, in order."""
    out = []
    for name in RULER_JPEGS:
        hits = sorted(globmod.glob(str(PROD_DIR / f"{stem}*" / name)))
        if hits:
            out.append(hits[0])
    return out


def _finalization_retrievals(stem: str, rec: dict) -> list[dict]:
    """Route real queries — derived from the image's weaknesses — through the
    knowledge-retrieval router (Mabel + the relevant specialists). Returns the
    retrieval-proof lines (each is also appended to reports/retrieval_log.jsonl
    by the router). Gate failures (MISSING_REQUIRED_CORPUS) are recorded
    honestly, never converted into passes. Never raises."""
    try:
        from knowledge_retrieval import route
    except Exception as exc:  # noqa: BLE001 — never kill the run
        return [{"status": "router_unavailable", "error": str(exc)}]

    ssim = rec.get("best_ssim", -1.0)
    stalls = rec.get("stall", 0)
    weak = ssim < 0.90
    queries = [
        ("mabel", "finalization",
         f"finalization checklist density satin corner fidelity {stem}"),
        ("mila", "vectorization",
         "preserve source silhouette during raster to vector conversion"
         + (" corner detection sharp turns" if weak or stalls else
            " polygon tracing")),
        ("mckenna", "digitization",
         "satin column density avoid jamming spacing floor"),
        ("melanie", "svg-authoring",
         "svg path fill rule viewBox stroke to path"),
        ("miranda", "machine-setup",
         "bernina b700 hoop size density limits"),
    ]
    proofs = []
    for agent, task_type, query in queries:
        try:
            res = route(agent, job_id=f"finalize:{stem}",
                        task_type=task_type, query=query,
                        source_file=rec.get("path"),
                        current_phase="finalization")
            proofs.append(res["retrieval_proof"])
        except Exception as exc:  # noqa: BLE001
            proofs.append({"agent": agent, "query": query,
                           "status": "error", "error": str(exc)})
    return proofs


def mabel_knowledge_pass(state: dict, stem: str, rec: dict) -> dict:
    """Criterion 4: load ALL knowledge modular objects
    (knowledge/vectorization/**/*.json[l]) + parameter_correlation_index*.json
    and record which techniques were consulted/applied, AND route real
    weakness-derived queries through the knowledge-retrieval router for Mabel
    + the specialist personas (proof lines land in
    reports/retrieval_log.jsonl and in the finalization record). Logged as a
    meeting entry (Mabel reporting to Minerva's log)."""
    consulted = []
    if KNOWLEDGE_VEC_DIR.exists():
        for p in sorted(KNOWLEDGE_VEC_DIR.rglob("*.json*")):
            rel = str(p.relative_to(REPO_ROOT))
            try:
                txt = p.read_text(encoding="utf-8")
                if p.suffix == ".jsonl":
                    n = sum(1 for ln in txt.splitlines() if ln.strip())
                    consulted.append({"source": rel, "objects": n})
                else:
                    obj = json.loads(txt)
                    concept = (obj.get("concept") or obj.get("title")
                               or obj.get("hypothesis") or p.stem)
                    consulted.append({"source": rel, "concept": concept})
            except (OSError, ValueError):
                continue
    for name in ("parameter_correlation_index_vec.json",
                 "parameter_correlation_index.json"):
        p = REPO_ROOT / name
        if not p.exists():
            continue
        try:
            idx = json.loads(p.read_text(encoding="utf-8"))
            consulted.append({"source": name, "objects": len(idx),
                              "buckets": sorted(idx)[:16]})
        except (OSError, ValueError):
            continue
    applied = {
        "winning_params": rec.get("best_params"),
        "learnings": rec.get("learnings"),
        "stall_break_epochs": sum(1 for h in rec.get("history", [])
                                  if h.get("stall_break")),
    }

    # Knowledge-library retrieval router pass (Mabel + specialists) --------
    retrievals = _finalization_retrievals(stem, rec)
    n_selected = sum(len(p.get("records_selected", [])) for p in retrievals)
    gate_failures = sorted({p.get("gate") for p in retrievals
                            if p.get("status") == "gate_failed"})
    summary = (f"{len(consulted)} knowledge object(s) consulted "
               f"({sum(1 for c in consulted if 'concept' in c)} technique "
               f"notes + correlation indexes); applied: bucket prior + "
               f"{applied['stall_break_epochs']} stall-break epoch(s); "
               f"library router: {len(retrievals)} retrieval(s), "
               f"{n_selected} object(s) selected"
               + (f", GATES FAILED: {'; '.join(gate_failures)}"
                  if gate_failures else ""))
    _append_jsonl(MEETINGS_LOG, {
        "timestamp": _utcnow(),
        "facilitator": "Minerva",
        "attendees": [MABEL.name, MINERVA.name],
        "reason": f"knowledge_fetch:{stem}",
        "image": stem,
        "global_epoch": state["global_epochs"],
        "decisions": [f"knowledge-fetch pass for {stem} finalization: "
                      f"{summary}"],
        "consulted": consulted,
        "applied": applied,
        "retrieval_proofs": retrievals,
    })
    post_as(MABEL, CHANNELS["reports"],
            text=f"{stem} finalization knowledge pass: {summary}")
    return {"met": bool(consulted), "objects_consulted": len(consulted),
            "sources": [c["source"] for c in consulted],
            "applied": applied, "summary": summary,
            "retrieval_proofs": retrievals,
            "retrieval_gate_failures": gate_failures}


def post_final_production_message(stem: str, rec: dict, criteria: dict,
                                  jpegs: list[str]) -> None:
    """The FINAL production-run Slack message (Margo -> #embiz-production):
    stats + the three ruler JPEGs attached as NATIVE image uploads in ONE
    message (slack_sdk files_upload_v2 with file_uploads=[...]) so they render
    as tappable images on mobile. Without Slack tokens the exact payload is
    drafted to the agent feed and reports/slack_messages/."""
    from personas import _append_feed, _slack_client
    sat = criteria["stitch_safety"]
    text = (
        f"FINAL PRODUCTION RUN — {stem}\n"
        f"attempts: {criteria['attempts']['total_attempts']} across "
        f"{rec['epochs']} epoch(s), "
        f"{criteria['attempts']['method_combinations']} method combination(s)\n"
        f"final quality: ssim {rec['best_ssim']:.4f} / composite "
        f"{rec['best_composite']:.4f} ({rec.get('done_reason')})\n"
        f"stitch safety: {sat['summary']}\n"
        f"knowledge: {criteria['knowledge']['summary']}\n"
        f"attached: original / SVG / stitch plan on the 5x5in ruler grid"
    )
    body = f"{MARGO.style} {text}"
    channel = CHANNELS["production"]
    files = [f for f in jpegs if f and os.path.exists(f)]

    record = {
        "timestamp": _utcnow(),
        "persona": MARGO.key,
        "username": MARGO.username,
        "icon_emoji": MARGO.icon_emoji,
        "channel": channel,
        "text": body,
        "files": files,
        "final_production_message": True,
        "delivered_to_slack": False,
    }
    client = _slack_client()
    if client is not None:
        try:
            resp = client.files_upload_v2(
                channel=channel,
                initial_comment=body,
                file_uploads=[{"file": f,
                               "filename": os.path.basename(f),
                               "title": f"{stem} {os.path.basename(f)}"}
                              for f in files],
            )
            record["delivered_to_slack"] = True
            record["slack_files"] = [
                (f or {}).get("id") for f in (resp.get("files") or [])]
        except Exception as exc:  # noqa: BLE001 — never kill the run
            record["slack_error"] = str(exc)
    _append_feed(record)

    # Draft copy (exact payload + file list) for review/replay when Slack is
    # not configured in this environment.
    SLACK_DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
    draft = SLACK_DRAFTS_DIR / f"{stem}_final_production_message.json"
    draft.write_text(json.dumps({
        "channel": channel,
        "method": "files_upload_v2",
        "initial_comment": body,
        "file_uploads": [{"file": f, "filename": os.path.basename(f),
                          "title": f"{stem} {os.path.basename(f)}"}
                         for f in files],
        "delivered_to_slack": record["delivered_to_slack"],
        "criteria": criteria,
        "timestamp": record["timestamp"],
    }, indent=2), encoding="utf-8")


def finalize_production_run(state: dict, stem: str, rec: dict) -> bool:
    """Evaluate the four finalization criteria for a DONE image; when all are
    met, regenerate the stitch plan with satin borders, mark the image
    finalized, emit the `production_run_finalized` milestone and send the
    final Slack production message. Returns True when finalized."""
    if rec.get("finalized") or not rec.get("done"):
        return False

    # 1. attempts + method diversity ----------------------------------------
    total_attempts = rec.get("total_attempts") or sum(
        h.get("vectorizer_iterations", 0) for h in rec.get("history", []))
    rec["total_attempts"] = total_attempts
    combos = set()
    for h in rec.get("history", []):
        if h.get("best_start"):
            combos.add(h["best_start"])
        combos.update(h.get("injected_starts", []))
    # An image that REACHED the SSIM target has converged by definition —
    # perfection reached means no more attempts are needed — so
    # reached_target bypasses the minimum-attempts threshold (which exists to
    # guarantee method diversity for images that merely stalled out).
    attempts_met = (total_attempts >= FINALIZE_MIN_ATTEMPTS
                    or bool(rec.get("reached_target")))
    attempts_crit = {"met": attempts_met,
                     "total_attempts": total_attempts,
                     "min_required": FINALIZE_MIN_ATTEMPTS,
                     "target_reached_bypass": bool(rec.get("reached_target")),
                     "method_combinations": len(combos)}

    # 2. convergence ----------------------------------------------------------
    convergence_crit = {"met": bool(rec.get("done")),
                        "reason": rec.get("done_reason"),
                        "best_ssim": rec.get("best_ssim"),
                        "best_composite": rec.get("best_composite")}

    # 3. satin fill + density guardrails (regenerate the plan) ---------------
    rows: list = []
    svg = REPO_ROOT / "vectorized_svg" / f"{stem}.svg"
    if svg.exists():
        raster = rasterize_best_svg(svg, stem)
        if raster is not None:
            try:
                rows = digitize_epoch(raster, stem)
            except Exception as exc:  # noqa: BLE001
                post_as(MARNIE, CHANNELS["alerts"],
                        text=f"finalization digitize failed for {stem}: {exc}")
    objects = []
    for _stem_r, label, s in rows:
        objects.append({
            "object": label,
            "satin_borders": s.get("satin_borders", 0),
            "satin_width_mm": s.get("satin_width_mm"),
            "satin_spacing_mm": s.get("satin_spacing_mm"),
            "line_art": s.get("line_art"),
            "fill_regions": s.get("fill_regions"),
            "line_regions": s.get("line_regions"),
            "density": s.get("density"),
        })
    density_ok = bool(rows) and all(
        (s.get("density") or {}).get("ok") for _, _, s in rows)
    # Satin borders are the border treatment for FILL regions only; thin
    # line-like regions correctly use running stitch (a satin column would
    # double-hit them). An object is satin-compliant when it has satin
    # borders, is line art, or contains no fill regions at all (region-level
    # line art — zero satin borders is the correct treatment there).
    satin_used = bool(rows) and all(
        s.get("satin_borders", 0) > 0 or s.get("line_art")
        or s.get("fill_regions", 1) == 0
        for _, _, s in rows)
    if rows:
        max_d = max((s.get("density") or {}).get(
            "max_local_density_per_mm2", -1) for _, _, s in rows)
        n_satin = sum(s.get("satin_borders", 0) for _, _, s in rows)
        sat_summary = (f"satin borders x{n_satin}, max local density "
                       f"{max_d:.3f}/mm^2 (limit "
                       f"{digitizer.MAX_LOCAL_DENSITY_PER_MM2}), "
                       f"{'PASS' if density_ok else 'FAIL'}")
    else:
        sat_summary = "stitch plan regeneration failed"
    stitch_crit = {"met": density_ok and satin_used, "objects": objects,
                   "summary": sat_summary}

    # 4. knowledge-fetch pass -------------------------------------------------
    knowledge_crit = mabel_knowledge_pass(state, stem, rec)

    criteria = {"attempts": attempts_crit, "convergence": convergence_crit,
                "stitch_safety": stitch_crit, "knowledge": knowledge_crit}
    rec["finalization"] = {"timestamp": _utcnow(), "criteria": criteria}

    unmet = [k for k, c in criteria.items() if not c["met"]]
    if unmet:
        rec["finalization_blocked_by"] = unmet
        post_as(MIRA, CHANNELS["jobs"],
                text=(f"{stem}: finalization blocked by {', '.join(unmet)} "
                      f"(attempts={total_attempts}, "
                      f"stitch: {sat_summary})"))
        save_state(state)
        return False

    rec.pop("finalization_blocked_by", None)
    rec["finalized"] = True
    rec["finalized_at"] = _utcnow()
    jpegs = _ruler_jpegs(stem)
    emit_milestone(state, "production_run_finalized", stem, {
        "best_ssim": rec.get("best_ssim", -1.0),
        "best_composite": rec.get("best_composite", -1.0),
        "epoch": rec.get("epochs"),
        "total_attempts": total_attempts,
        "method_combinations": attempts_crit["method_combinations"],
        "stitch_safety": sat_summary,
        "knowledge_objects": knowledge_crit["objects_consulted"],
        "ruler_jpegs": jpegs,
    })
    post_final_production_message(stem, rec, criteria, jpegs)
    save_state(state)
    return True


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

    # Stall-breaking: if the last epoch(s) did not improve, this epoch must
    # explore differently — inject jittered + random restarts and skip the
    # deterministic preset starts (only the index start, which reproduces the
    # best-known score, is kept as a no-regression floor).
    stall_break = rec.get("stall", 0) >= 1 and not rec.get("reached_target")
    extra_starts = (plan_stall_break(state, rec, stem, path, epoch)
                    if stall_break else None)

    post_as(MAYA, CHANNELS["jobs"],
            text=(f"epoch {epoch} for {stem}: vectorizer refinement "
                  f"({iters_per_epoch} iters/start, target ssim {target}"
                  + (f", stall-break with {len(extra_starts)} injected starts"
                     if extra_starts else "") + ")"))
    vec = vectorizer.optimize(str(path), max_iters=iters_per_epoch,
                              target_ssim=target, verbose=False,
                              extra_starts=extra_starts,
                              skip_preset_starts=stall_break)

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
    rec["total_attempts"] = (
        (rec.get("total_attempts")
         or sum(h.get("vectorizer_iterations", 0) for h in rec["history"]))
        + int(vec.get("iterations", 0)))
    prev_best = rec["best_composite"]
    rec["stall"] = 0 if improved else rec["stall"] + 1
    if improved:
        rec["best_composite"] = vec["best_composite"]
        rec["best_ssim"] = max(rec["best_ssim"], vec["best_ssim"])
        rec["best_params"] = vec.get("best_params")
        if stall_break and str(vec.get("best_start", "")).startswith("stall"):
            mabel_stall_break_note(stem, epoch, prev_best, vec)
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
        "stall_break": stall_break,
        "injected_starts": [lbl for lbl, _ in (extra_starts or [])],
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

    # ---- production-run finalization (target reached OR stalled out) -------
    if rec["done"] and not rec.get("finalized"):
        finalize_production_run(state, stem, rec)
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
    ap.add_argument("--stall-epochs", type=int, default=DEFAULT_STALL_EPOCHS,
                    help="stop an image after N non-improving epochs "
                         "(raised from 5: stall-break epochs each explore "
                         "a different region, so more attempts pay off)")
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

            # Finalization sweep: converged images that still need their
            # production-run finalization (satin regeneration + density
            # validation + knowledge pass + final Slack message). Attempted
            # once; a blocked image is not retried until its state changes.
            for path in images:
                fstem = _stem(path)
                frec = state["images"].get(fstem)
                if (frec and frec.get("done") and not frec.get("finalized")
                        and "finalization_blocked_by" not in frec):
                    finalize_production_run(state, fstem, frec)

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
