"""model_router.py — Local-first model escalation ladder for EMBIZ.

Implements the mandatory routing policy from
EMBIZ_Jupiter_LOCAL_FIRST_Autonomous_Agent_FULL_VERSION.md:

  Rung 1: qwen3:8b on the local GPU (primary — reasoning, planning, execution,
          Slack handling, automation).
  Rung 2: local retry with a larger context (8192 -> 16384) and/or a different
          local prompt strategy (/no_think toggle, task decomposition hint,
          lower temperature).
  Rung 3: other locally pulled Ollama models, discovered via /api/tags
          (the API equivalent of `ollama list`), tried one at a time — never in
          parallel (8 GB VRAM: one resident model only).
  Rung 4: ONLY THEN a paid API. Disabled unless explicitly configured via env
          (EMBIZ_PAID_PROVIDER, EMBIZ_PAID_MODEL, EMBIZ_PAID_API_KEY). Every
          paid call is appended to state/paid_usage_audit.jsonl and announced
          in the Slack alerts channel before and after (cost transparency).

No agent may call a paid API directly; everything goes through route().

Dependencies: stdlib + requests (+ slack_sdk only if Slack notification is
available; notification degrades gracefully to log-only).
"""

from __future__ import annotations

import datetime
import hashlib
import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

import requests

from qwen_client import (
    OllamaError,
    PRIMARY_MODEL,
    chat,
    list_local_models,
)

log = logging.getLogger("embiz.model_router")

STATE_DIR = Path(os.environ.get(
    "EMBIZ_STATE_DIR",
    Path(__file__).resolve().parent / "state",
))
PAID_AUDIT_LOG = STATE_DIR / "paid_usage_audit.jsonl"
ROUTER_EVENT_LOG = STATE_DIR / "router_events.jsonl"

# Repo-root decision trace convention (append-only ledger already in production).
REPO_ROOT = Path(os.environ.get("EMBIZ_REPO_ROOT", Path(__file__).resolve().parent.parent))
DECISION_TRACE = REPO_ROOT / "decision_trace.jsonl"


def _utcnow() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _append_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def _notify_slack(text: str) -> None:
    """Best-effort Slack alert (cost transparency). Never raises."""
    token = os.environ.get("SLACK_BOT_TOKEN")
    channel = os.environ.get("EMBIZ_SLACK_CHANNEL_ALERTS", "#embiz-alerts")
    if not token:
        log.warning("Slack not configured; alert only logged: %s", text)
        return
    try:
        requests.post(
            "https://slack.com/api/chat.postMessage",
            headers={"Authorization": f"Bearer {token}"},
            json={"channel": channel, "text": text},
            timeout=15,
        )
    except requests.RequestException as exc:
        log.warning("Slack alert failed (%s): %s", exc, text)


@dataclass
class TaskPolicy:
    """Per-task-type routing rules."""

    temperature: float = 0.4
    no_think: bool = False          # rung-1 default thinking mode
    rung2_ctx_steps: tuple = (8192, 16384)
    allow_rung3: bool = True
    allow_paid: bool = False        # rung 4 permitted for this task type?
    system: str = ""
    extra: dict = field(default_factory=dict)


# Routing table — mirrors the "Per-Task-Type Routing Rules" section of the doc.
TASK_POLICIES: dict[str, TaskPolicy] = {
    "slack_reply": TaskPolicy(
        no_think=True, temperature=0.5, allow_paid=False,
        system="You are an EMBIZ embroidery production agent replying in Slack. "
               "Be concise, factual, and cite local artifacts/ledgers when relevant.",
    ),
    "plan": TaskPolicy(
        no_think=False, temperature=0.3, allow_paid=True,
        system="You are the EMBIZ orchestrator planning a production job into "
               "explicit, verifiable steps over local deterministic tools.",
    ),
    "summarize": TaskPolicy(no_think=True, temperature=0.2, allow_paid=False),
    "qa_review": TaskPolicy(
        no_think=False, temperature=0.2, allow_paid=True,
        system="You review embroidery QA metrics and decide pass/fail with reasons.",
    ),
    "classify": TaskPolicy(no_think=True, temperature=0.0, allow_paid=False),
    "code": TaskPolicy(no_think=False, temperature=0.2, allow_paid=True),
    "customer_reply": TaskPolicy(
        no_think=True, temperature=0.5, allow_paid=True,
        system="Draft a professional customer message for Jupiter Embroidery. "
               "The draft ALWAYS requires human approval before sending.",
    ),
}
DEFAULT_POLICY = TaskPolicy()


class EscalationExhausted(RuntimeError):
    """All permitted rungs failed for this task."""


def _log_event(record: dict) -> None:
    record.setdefault("timestamp", _utcnow())
    _append_jsonl(ROUTER_EVENT_LOG, record)


def _local_only() -> bool:
    """Global no-spend kill switch. DEFAULT ON: every LLM task runs on the
    local Ollama rungs and the paid rung is unreachable, regardless of task
    policy or configured API keys. Paid escalation requires BOTH the
    EMBIZ_PAID_* config AND an explicit EMBIZ_LOCAL_ONLY=0 opt-out."""
    return os.environ.get("EMBIZ_LOCAL_ONLY", "1").lower() not in (
        "0", "false", "no", "off")


def _paid_call(prompt: str, system: str, audit: dict) -> str:
    """Rung 4 — paid API. Env-gated. Logged. Slack-announced before and after."""
    if _local_only():
        raise EscalationExhausted(
            "EMBIZ_LOCAL_ONLY is on (the default): paid escalation is "
            "disabled and this task fails locally instead of spending. "
            "Set EMBIZ_LOCAL_ONLY=0 explicitly to ever allow paid calls."
        )
    provider = os.environ.get("EMBIZ_PAID_PROVIDER")
    model = os.environ.get("EMBIZ_PAID_MODEL")
    api_key = os.environ.get("EMBIZ_PAID_API_KEY")
    if not (provider and model and api_key):
        raise EscalationExhausted(
            "paid escalation rung is not configured (EMBIZ_PAID_PROVIDER/"
            "EMBIZ_PAID_MODEL/EMBIZ_PAID_API_KEY unset) — failing locally "
            "instead of spending silently"
        )

    _notify_slack(
        f":money_with_wings: PAID ESCALATION START — task={audit['task_type']} "
        f"provider={provider} model={model}. Local rungs failed: "
        f"{audit['rung_failures']}"
    )

    if provider == "anthropic":
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": model,
                "max_tokens": 4096,
                "system": system or "",
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=300,
        )
        r.raise_for_status()
        body = r.json()
        text = "".join(b.get("text", "") for b in body.get("content", []))
        usage = body.get("usage", {})
    elif provider == "openai":
        messages = ([{"role": "system", "content": system}] if system else []) + [
            {"role": "user", "content": prompt}
        ]
        r = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"model": model, "messages": messages},
            timeout=300,
        )
        r.raise_for_status()
        body = r.json()
        text = body["choices"][0]["message"]["content"]
        usage = body.get("usage", {})
    else:
        raise EscalationExhausted(f"unknown paid provider {provider!r}")

    audit.update({
        "provider": provider,
        "model": model,
        "usage": usage,
        "timestamp": _utcnow(),
    })
    _append_jsonl(PAID_AUDIT_LOG, audit)
    _append_jsonl(DECISION_TRACE, {
        "timestamp": _utcnow(),
        "artifact": "decision_trace",
        "agent": "model_router",
        "decision": "paid-escalation",
        "task_type": audit["task_type"],
        "provider": provider,
        "model": model,
        "reason_no_local_fallback": audit["rung_failures"],
    })
    _notify_slack(
        f":money_with_wings: PAID ESCALATION DONE — task={audit['task_type']} "
        f"provider={provider} model={model} usage={json.dumps(usage)} "
        f"(audited in {PAID_AUDIT_LOG.name})"
    )
    return text.strip()


def route(task_type: str, prompt: str, system: str | None = None,
          context: str | None = None) -> str:
    """Route one LLM task through the local-first escalation ladder.

    Returns the model's text (always think-stripped). Raises
    EscalationExhausted if every permitted rung fails.
    """
    policy = TASK_POLICIES.get(task_type, DEFAULT_POLICY)
    sys_prompt = system if system is not None else policy.system
    full_prompt = f"{context}\n\n---\n\n{prompt}" if context else prompt
    prompt_hash = hashlib.sha256(full_prompt.encode()).hexdigest()[:16]
    failures: list[str] = []

    # ---- Rung 1: qwen3:8b on GPU, default context -------------------------
    try:
        text = chat(full_prompt, system=sys_prompt, model=PRIMARY_MODEL,
                    temperature=policy.temperature, no_think=policy.no_think)
        _log_event({"task_type": task_type, "rung": 1, "model": PRIMARY_MODEL,
                    "prompt_hash": prompt_hash, "outcome": "ok"})
        return text
    except OllamaError as exc:
        failures.append(f"rung1 {PRIMARY_MODEL}: {exc}")
        log.warning("rung 1 failed for %s: %s", task_type, exc)

    # ---- Rung 2: larger context / different local prompt strategy ---------
    for num_ctx in policy.rung2_ctx_steps:
        for flipped_think in (policy.no_think, not policy.no_think):
            try:
                text = chat(full_prompt, system=sys_prompt, model=PRIMARY_MODEL,
                            num_ctx=num_ctx, temperature=policy.temperature,
                            no_think=flipped_think)
                _log_event({"task_type": task_type, "rung": 2,
                            "model": PRIMARY_MODEL, "num_ctx": num_ctx,
                            "no_think": flipped_think,
                            "prompt_hash": prompt_hash, "outcome": "ok"})
                return text
            except OllamaError as exc:
                failures.append(f"rung2 ctx={num_ctx} no_think={flipped_think}: {exc}")

    # ---- Rung 3: other locally pulled Ollama models (serial, never parallel)
    if policy.allow_rung3:
        try:
            alternates = [m for m in list_local_models() if m != PRIMARY_MODEL]
        except OllamaError as exc:
            alternates = []
            failures.append(f"rung3 discovery: {exc}")
        for alt in alternates:
            try:
                text = chat(full_prompt, system=sys_prompt, model=alt,
                            temperature=policy.temperature,
                            no_think=policy.no_think)
                _log_event({"task_type": task_type, "rung": 3, "model": alt,
                            "prompt_hash": prompt_hash, "outcome": "ok"})
                _append_jsonl(DECISION_TRACE, {
                    "timestamp": _utcnow(), "artifact": "decision_trace",
                    "agent": "model_router", "decision": "local-model-swap",
                    "task_type": task_type, "model": alt,
                    "note": "model swap unloads qwen3:8b first (8GB VRAM, one model at a time)",
                })
                return text
            except OllamaError as exc:
                failures.append(f"rung3 {alt}: {exc}")

    # ---- Rung 4: paid API — only now, only if allowed and configured ------
    audit = {"task_type": task_type, "prompt_hash": prompt_hash,
             "rung_failures": failures}
    _log_event({"task_type": task_type, "rung": 4, "prompt_hash": prompt_hash,
                "outcome": "attempting-paid", "failures": failures})
    if not policy.allow_paid:
        _notify_slack(
            f":no_entry: Local model rungs exhausted for task={task_type} and "
            f"paid escalation is not permitted for this task type. Failing. "
            f"Failures: {failures[-1] if failures else 'n/a'}"
        )
        raise EscalationExhausted(
            f"task {task_type}: all local rungs failed and paid rung not "
            f"permitted; failures={failures}"
        )
    try:
        return _paid_call(full_prompt, sys_prompt or "", audit)
    except (requests.RequestException, EscalationExhausted) as exc:
        _notify_slack(f":rotating_light: Paid escalation failed for task={task_type}: {exc}")
        raise EscalationExhausted(
            f"task {task_type}: all rungs failed; failures={failures + [str(exc)]}"
        ) from exc
