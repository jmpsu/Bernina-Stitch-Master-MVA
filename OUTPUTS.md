# OUTPUTS.md — every artifact the EMBIZ/Bernina system produces, and how to view it

Repo: `jmpsu/Bernina-Stitch-Master-MVA`. GitHub URL pattern for any committed
file: `https://github.com/jmpsu/Bernina-Stitch-Master-MVA/blob/<branch>/<path>`
(binary previews/JPEGs render directly in the GitHub file view).

> Source input images (`input_images/`) are **never committed** — they are
> customer/trademark/personal art. `.gitignore` excludes them, following the
> precedent set for `reference_images/`. Everything generated FROM them is
> committed.

## 1. Machine embroidery files — `stitch_plans/`

| Artifact | What it is | How to view |
|---|---|---|
| `stitch_plans/<stem>_<label>.exp` | Bernina B700 machine stitch file (the file the machine sews) | Load on the B700 (USB) or any embroidery software (Bernina ARTlink, Embrilliance, Ink/Stitch) |
| `stitch_plans/<stem>_<label>.pes` | Same design in Brother/PES format (broad software support) | Any embroidery viewer; Ink/Stitch (Inkscape) opens it free |
| `stitch_plans/<stem>_<label>_preview.png` | Rendered stitch-path preview (actual sewn paths, thread colors) | Any image viewer / GitHub file view |
| `stitch_plans/<stem>_<label>.json` | Sidecar: physical size (mm), stitch/jump/trim/color counts, thread RGBs, bg-removal method, file names | Any text editor / GitHub |

Design height is normalized to 76.2 mm (3 in) — `height_ok` in the sidecar
verifies it.

## 2. Production layout JPEGs — `production_runs/<stem>/`

The 5×5 in ruler/grid review images from `production_layout.py` (subject
composited at TRUE size onto a calibrated inch-ruler + 0.25-in grid, 283 px/in):

| File | Subject |
|---|---|
| `1_original_on_ruler.jpg` | Original raster, background removed |
| `2_svg_on_ruler.jpg` | The generated vector (SVG) render |
| `3_stitchplan_on_ruler.jpg` | The PES stitch-out render — **this is the image Margo posts to Slack** |

View: disk/GitHub, or Slack `#embiz-production` (posted every epoch by
**Margo**) and `#embiz-milestones` (attached to milestone posts).

## 3. Vector artifacts — `vectorized_svg/`

| Artifact | What it is | How to view |
|---|---|---|
| `vectorized_svg/<stem>.svg` | Best traced SVG for the image (vtracer, hill-climbed params) | Browser, Inkscape, GitHub renders SVG inline |
| `vectorized_svg/<stem>_compare.png` | Side-by-side original-vs-render comparison | Image viewer / GitHub |

## 4. Reports — `reports/`

| Artifact | What it is |
|---|---|
| `reports/iteration_N.md` / `.json` | Per-iteration self-improvement reports (human + machine readable) |
| `reports/milestones.jsonl` | Continuous-run milestone ledger: `first_epoch_complete`, `new_best_score`, `target_reached`, `all_images_pass`, `epoch_century` — one JSON per line with scores + production JPEG path |
| `reports/agent_meetings.jsonl` | Minerva's agent meetings: attendees, agenda (scores/stalls/learnings), summary (+ which reasoning engine: qwen3:8b router or explicit deterministic fallback), decisions, action items |
| `reports/vectorizer_v*.md` | Vectorizer version/promotion engineering notes |
| `reports/knowledge_experiments.md` | Stage-2 validation of library-doctrine artifacts |
| `reports/library_utilization_coverage.md`, `reports/slack_utilization_report.md`, `reports/production_visuals.md` | Coverage/utilization audits |
| `reports/slack_messages/*.txt` | Drafted Slack message bodies (posted when tokens present) |

View: text/Markdown on disk or GitHub; JSONL with `jq` or any editor.

## 5. Append-only ledgers (repo root)

| Ledger | What each line records |
|---|---|
| `observations.jsonl` | Raw observations from iteration runs |
| `decision_trace.jsonl` | Every agent decision (incl. paid-escalation and model-swap decisions from the model router) |
| `reward_penalty_ledger.jsonl` | Reward/penalty scoring per iteration |
| `vectorization_attempts.jsonl` | EVERY vectorizer hill-climb attempt: params, ssim/edge/rmse/color-fidelity/composite, accepted flag — the full search history across all epochs |
| `parameter_correlation_index.json` / `parameter_correlation_index_vec.json` | Best-known parameters per image-feature bucket (cross-image transfer; Mabel's library) |
| `knowledge_experiments.jsonl`, `knowledge/` | Library-doctrine experiment records + extracted knowledge |
| `weights.json`, `metrics.py` outputs | Scoring weights / metric definitions |

View: `jq . <file>` or any editor; each line is standalone JSON.

## 6. local_agents runtime — `local_agents/state/`

| Artifact | What it is |
|---|---|
| `state/continuous_run_state.json` | Continuous-run checkpoint (per-image epochs, best scores, stall counters, history). Written after EVERY epoch — resume on this container or the Mint machine |
| `state/transcripts/agent_feed.jsonl` | **Every persona message**, Slack-delivered or not — the full agent conversation is always viewable locally here |
| `state/slack_transcript.jsonl` | Slack daemon in/outbound transcript (responsibility 12) |
| `state/paid_usage_audit.jsonl` | Every paid-API escalation (cost transparency; empty unless rung 4 ever fires) |
| `state/router_events.jsonl` | Every model-router rung attempt/outcome |
| `state/queue/{pending,active,done,failed}/` | Filesystem job queue (Slack-triggered jobs) |
| `state/approvals/{pending,decided}/` | Human approval gate records |
| `state/continuous_run_work/` | Per-epoch SVG re-rasters fed to the digitizer (transient) |
| `state/daemon_heartbeat.json` | Slack daemon liveness |

## 7. Slack channels — who posts what

All persona posts use `chat.postMessage` with `username` + `icon_emoji`
overrides (bot scope `chat:write.customize`), so messages appear from the
named agent. Without tokens, every post still lands in
`local_agents/state/transcripts/agent_feed.jsonl`.

| Channel | Persona(s) | Content |
|---|---|---|
| `#embiz-jobs` | **Mira** (run start/stop, convergence), **Maya** (epoch vectorization status), **Marnie** (digitization status), slack_daemon (job queue/status) | Run + job lifecycle |
| `#embiz-alerts` | **Mira**/**Marnie** (failures, interrupts), model_router (paid-escalation transparency), slack_daemon (errors, ops reports) | Errors and operational alerts |
| `#embiz-qa` | **Mercy** | Per-epoch QA verdicts (PASS/STRONG/OK/WEAK/FAIL with SSIM/composite evidence), weak-output flags |
| `#embiz-milestones` | **Mira** (milestone text), **Margo** (production JPEG attachment) | first-epoch, new-best, target-reached, all-images-pass, every-100-epochs |
| `#embiz-meetings` | **Minerva** | Agent meeting summaries: attendees, agenda, decisions, action items (full record in `reports/agent_meetings.jsonl`) |
| `#embiz-production` | **Margo** | The 5×5 in ruler/grid production layout JPEG for every epoch's stitch plan |
| `#embiz-reports` | **Mabel** (parameter learnings / correlation-index updates), **Margo** (status digests) | Knowledge + reporting |

Channel names are env-overridable (`EMBIZ_SLACK_CHANNEL_*`; see
`local_agents/personas.py`).

## 8. The seven agent personas

| Name | Role |
|---|---|
| **Mira** | Orchestrator / run director — owns the continuous run and milestones |
| **Maya** | Vectorization specialist — vectorizer.py refinement epochs |
| **Marnie** | Digitization specialist — digitizer.py, stitch plans, EXP/PES |
| **Mercy** | QA inspector — scores, SSIM verdicts, flags weak outputs |
| **Mabel** | Knowledge librarian — parameter learnings, correlation-index updates |
| **Margo** | Operations reporter — status posts, production layout images |
| **Minerva** | Meeting facilitator — agent meetings, decisions, transcripts |

## 9. How to run the continuous perfection loop

```bash
# bounded pass (container/demo):
python local_agents/continuous_run.py --time-budget-min 15
# unbounded persistent run (Mint machine):
systemctl --user enable --now embiz-continuous-run.service
```

Drop raster images (png/jpg/jpeg/webp/heic) into `input_images/` — they are
picked up automatically, refined over epochs until SSIM ≥ 0.98 (default) or a
5-epoch stall, and every artifact above is regenerated per epoch.
