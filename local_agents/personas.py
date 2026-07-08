"""personas.py — the seven named EMBIZ agent personas and their Slack voice.

Every autonomous role in the continuous perfection run speaks as a named
agent. Slack messages are posted with ``chat.postMessage`` using the
``username`` + ``icon_emoji`` overrides so each message visibly comes from the
named agent (requires the ``chat:write.customize`` bot scope). When Slack is
not configured (no SLACK_BOT_TOKEN) nothing is lost: EVERY post — Slack or
not — is also appended to ``local_agents/state/transcripts/agent_feed.jsonl``
so the whole conversation is reviewable locally.

The seven personas (all names start with M):

  Mira    — Orchestrator / run director. Owns the continuous run + milestones.
  Maya    — Vectorization specialist. Runs vectorizer.py refinement epochs.
  Marnie  — Digitization specialist. Runs digitizer.py, stitch plans, EXP/PES.
  Mercy   — QA inspector. Composite/SSIM verdicts, flags weak outputs.
  Mabel   — Knowledge librarian. Parameter learnings, correlation index.
  Margo   — Operations reporter. Status posts + production layout images.
  Minerva — Meeting facilitator. Agent meetings, decisions, transcripts.

Knowledge-library specialist personas (Multimodal Knowledge Objects spec;
each maps to required corpora in knowledge_retrieval.AGENT_CORPORA):

  Mila      — Raster-to-vector specialist (raster-to-vector + vector-design
              + visual-semantics corpora).
  Melanie   — Vector-design / SVG specialist (vector-design +
              svg-specification + inkscape + svg-conformance corpora).
  Mckenna   — Ink/Stitch digitization specialist (ink-stitch corpora).
  Meredith  — Ink/Stitch automation specialist (ink-stitch corpora).
  Miranda   — Bernina B700 machine specialist (bernina-b700 corpus).
  Mackenzie — Visual QA specialist (visual-qa corpora).
  Monica    — Knowledge operations / corpus curator (global library).

Usage:
    from personas import PERSONAS, post_as
    post_as(PERSONAS["mira"], "#embiz-milestones", text="epoch 1 complete")
    post_as(PERSONAS["margo"], "#embiz-production",
            text="production layout", file="production_runs/x/3_stitchplan_on_ruler.jpg")

No call in this module ever raises: Slack failures degrade to the local feed.
"""

from __future__ import annotations

import datetime
import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

log = logging.getLogger("embiz.personas")

STATE_DIR = Path(os.environ.get(
    "EMBIZ_STATE_DIR", Path(__file__).resolve().parent / "state"))
TRANSCRIPTS_DIR = STATE_DIR / "transcripts"
AGENT_FEED = TRANSCRIPTS_DIR / "agent_feed.jsonl"

# Channel registry (env-overridable; see OUTPUTS.md for the full table).
CHANNELS = {
    "jobs": os.environ.get("EMBIZ_SLACK_CHANNEL_JOBS", "#embiz-jobs"),
    "alerts": os.environ.get("EMBIZ_SLACK_CHANNEL_ALERTS", "#embiz-alerts"),
    "qa": os.environ.get("EMBIZ_SLACK_CHANNEL_QA", "#embiz-qa"),
    "milestones": os.environ.get("EMBIZ_SLACK_CHANNEL_MILESTONES", "#embiz-milestones"),
    "meetings": os.environ.get("EMBIZ_SLACK_CHANNEL_MEETINGS", "#embiz-meetings"),
    "production": os.environ.get("EMBIZ_SLACK_CHANNEL_PRODUCTION", "#embiz-production"),
    "reports": os.environ.get("EMBIZ_SLACK_CHANNEL_REPORTS", "#embiz-reports"),
}


@dataclass(frozen=True)
class Persona:
    """One named agent voice. ``username``/``icon_emoji`` are the Slack
    chat.postMessage display overrides; ``style`` prefixes every message so
    the voice is recognizable even in the local feed."""

    key: str
    name: str
    role: str
    icon_emoji: str
    style: str = ""
    home_channels: tuple = field(default_factory=tuple)

    @property
    def username(self) -> str:
        return f"{self.name} · {self.role}"


PERSONAS: dict[str, Persona] = {
    "mira": Persona(
        key="mira", name="Mira", role="Run Director",
        icon_emoji=":compass:",
        style="[Mira | run director]",
        home_channels=(CHANNELS["milestones"], CHANNELS["jobs"]),
    ),
    "maya": Persona(
        key="maya", name="Maya", role="Vectorization Specialist",
        icon_emoji=":triangular_ruler:",
        style="[Maya | vectorization]",
        home_channels=(CHANNELS["jobs"],),
    ),
    "marnie": Persona(
        key="marnie", name="Marnie", role="Digitization Specialist",
        icon_emoji=":thread:",
        style="[Marnie | digitization]",
        home_channels=(CHANNELS["jobs"],),
    ),
    "mercy": Persona(
        key="mercy", name="Mercy", role="QA Inspector",
        icon_emoji=":mag:",
        style="[Mercy | QA]",
        home_channels=(CHANNELS["qa"],),
    ),
    "mabel": Persona(
        key="mabel", name="Mabel", role="Knowledge Librarian",
        icon_emoji=":books:",
        style="[Mabel | knowledge]",
        home_channels=(CHANNELS["reports"],),
    ),
    "margo": Persona(
        key="margo", name="Margo", role="Operations Reporter",
        icon_emoji=":newspaper:",
        style="[Margo | ops]",
        home_channels=(CHANNELS["production"], CHANNELS["reports"]),
    ),
    "minerva": Persona(
        key="minerva", name="Minerva", role="Meeting Facilitator",
        icon_emoji=":owl:",
        style="[Minerva | meetings]",
        home_channels=(CHANNELS["meetings"],),
    ),
    # --- knowledge-library specialists (Multimodal Knowledge Objects spec) --
    "mila": Persona(
        key="mila", name="Mila", role="Raster-to-Vector Specialist",
        icon_emoji=":black_square_button:",
        style="[Mila | raster-to-vector]",
        home_channels=(CHANNELS["jobs"],),
    ),
    "melanie": Persona(
        key="melanie", name="Melanie", role="Vector Design / SVG Specialist",
        icon_emoji=":art:",
        style="[Melanie | vector design]",
        home_channels=(CHANNELS["jobs"],),
    ),
    "mckenna": Persona(
        key="mckenna", name="Mckenna", role="Ink/Stitch Digitization Specialist",
        icon_emoji=":sewing_needle:",
        style="[Mckenna | ink/stitch digitization]",
        home_channels=(CHANNELS["jobs"],),
    ),
    "meredith": Persona(
        key="meredith", name="Meredith", role="Ink/Stitch Automation Specialist",
        icon_emoji=":gear:",
        style="[Meredith | ink/stitch automation]",
        home_channels=(CHANNELS["jobs"],),
    ),
    "miranda": Persona(
        key="miranda", name="Miranda", role="Bernina B700 Machine Specialist",
        icon_emoji=":sewing_machine:",
        style="[Miranda | bernina b700]",
        home_channels=(CHANNELS["production"],),
    ),
    "mackenzie": Persona(
        key="mackenzie", name="Mackenzie", role="Visual QA Specialist",
        icon_emoji=":frame_with_picture:",
        style="[Mackenzie | visual QA]",
        home_channels=(CHANNELS["qa"],),
    ),
    "monica": Persona(
        key="monica", name="Monica", role="Knowledge Operations Curator",
        icon_emoji=":card_file_box:",
        style="[Monica | knowledge ops]",
        home_channels=(CHANNELS["reports"],),
    ),
}


def _utcnow() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _append_feed(record: dict) -> None:
    """Local agent feed — ALWAYS written, Slack or no Slack."""
    try:
        TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
        with AGENT_FEED.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError as exc:  # even the feed must never kill a run
        log.error("agent_feed write failed: %s", exc)


_web = None  # cached slack_sdk WebClient (or False when unavailable)


def _slack_client():
    """Return a cached WebClient, or None when Slack is not configured."""
    global _web
    if _web is False:
        return None
    if _web is not None:
        return _web
    token = os.environ.get("SLACK_BOT_TOKEN")
    if not token:
        _web = False
        return None
    try:
        from slack_sdk import WebClient
        _web = WebClient(token=token)
        return _web
    except Exception as exc:  # slack_sdk missing / broken
        log.warning("slack_sdk unavailable (%s); local feed only", exc)
        _web = False
        return None


def post_as(persona: Persona, channel: str, text: str | None = None,
            blocks: list | None = None, file: str | None = None,
            thread_ts: str | None = None) -> str | None:
    """Post to Slack AS a named persona (username + icon_emoji overrides) and
    always mirror the message into the local agent feed.

    ``file`` (a local path, e.g. a production-layout JPEG) is uploaded with
    ``files_upload_v2`` using ``text`` as the initial comment. Returns the
    Slack message ``ts`` when posted, else None. Never raises.
    """
    body = text or ""
    if persona.style and body:
        body = f"{persona.style} {body}"

    record = {
        "timestamp": _utcnow(),
        "persona": persona.key,
        "username": persona.username,
        "icon_emoji": persona.icon_emoji,
        "channel": channel,
        "text": body,
        "file": file,
        "delivered_to_slack": False,
    }

    ts = None
    client = _slack_client()
    if client is not None:
        try:
            if file and os.path.exists(file):
                resp = client.files_upload_v2(
                    channel=channel, file=file,
                    filename=os.path.basename(file),
                    initial_comment=body or os.path.basename(file),
                )
                record["delivered_to_slack"] = True
                record["slack_file"] = (resp.get("file") or {}).get("id")
            else:
                resp = client.chat_postMessage(
                    channel=channel, text=body, blocks=blocks,
                    thread_ts=thread_ts,
                    username=persona.username,
                    icon_emoji=persona.icon_emoji,
                )
                ts = resp.get("ts")
                record["delivered_to_slack"] = True
                record["slack_ts"] = ts
        except Exception as exc:  # noqa: BLE001 — never kill the run
            record["slack_error"] = str(exc)
            log.warning("post_as(%s -> %s) Slack failed: %s",
                        persona.name, channel, exc)
    _append_feed(record)
    return ts


def feed_tail(n: int = 20) -> list[dict]:
    """Last n agent-feed records (local visibility helper)."""
    if not AGENT_FEED.exists():
        return []
    lines = AGENT_FEED.read_text(encoding="utf-8").strip().splitlines()
    out = []
    for line in lines[-n:]:
        try:
            out.append(json.loads(line))
        except ValueError:
            continue
    return out


if __name__ == "__main__":
    # Smoke test: everyone says hello into the local feed (and Slack if up).
    for p in PERSONAS.values():
        post_as(p, p.home_channels[0] if p.home_channels else CHANNELS["jobs"],
                text=f"online — {p.role}")
    for rec in feed_tail(len(PERSONAS)):
        print(rec["timestamp"], rec["username"], "->", rec["channel"],
              ":", rec["text"])
