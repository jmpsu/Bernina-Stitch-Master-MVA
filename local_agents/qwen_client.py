"""qwen_client.py — Ollama API client for the EMBIZ local-first agent system.

Talks to the local Ollama runtime (default http://localhost:11434) running
qwen3:8b at 100% GPU offload on the RTX PRO 2000 (8 GB VRAM, model ~6.2 GB).

Key behaviors:
  * qwen3 is a *thinking* model: it emits <think>...</think> blocks. Every
    response returned by this module is passed through strip_think() so callers
    never see thinking text. Callers that need structured output should pass
    no_think=True, which appends Ollama's "/no_think" soft switch.
  * VRAM budget: only ONE model may be resident at a time. This client never
    issues concurrent generations (a module-level lock serializes calls) and
    never preloads a second model.
  * Robust: bounded retries with backoff, explicit timeouts, and typed errors
    so the model router can treat failures as escalation-ladder rung failures.

Dependencies: stdlib + requests.
"""

from __future__ import annotations

import json
import logging
import os
import re
import threading
import time

import requests

log = logging.getLogger("embiz.qwen_client")

OLLAMA_URL = os.environ.get("EMBIZ_OLLAMA_URL", "http://localhost:11434").rstrip("/")
PRIMARY_MODEL = os.environ.get("EMBIZ_LOCAL_MODEL", "qwen3:8b")
DEFAULT_NUM_CTX = int(os.environ.get("EMBIZ_NUM_CTX_DEFAULT", "4096"))
MAX_NUM_CTX = int(os.environ.get("EMBIZ_NUM_CTX_MAX", "16384"))
GEN_TIMEOUT_S = int(os.environ.get("EMBIZ_GEN_TIMEOUT_S", "600"))

# Serialize all LLM calls: one model, one generation at a time (VRAM budget).
_GPU_LOCK = threading.Lock()

_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)


class OllamaError(RuntimeError):
    """Raised when the local Ollama runtime cannot complete a generation."""


class OllamaUnavailable(OllamaError):
    """Raised when the Ollama runtime itself is unreachable."""


def strip_think(text: str) -> str:
    """Remove qwen3 <think>...</think> blocks (and any unclosed trailing one)."""
    if not text:
        return ""
    text = _THINK_RE.sub("", text)
    # Unclosed think block (generation truncated mid-thought): drop it.
    idx = text.find("<think>")
    if idx != -1:
        text = text[:idx]
    return text.strip()


def ollama_alive(timeout: float = 5.0) -> bool:
    """Return True if the local Ollama runtime responds."""
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=timeout)
        return r.ok
    except requests.RequestException:
        return False


def list_local_models(timeout: float = 10.0) -> list[str]:
    """Enumerate locally pulled Ollama models (API equivalent of `ollama list`).

    Used by the model router for escalation rung 3.
    """
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=timeout)
        r.raise_for_status()
        return [m.get("name", "") for m in r.json().get("models", []) if m.get("name")]
    except requests.RequestException as exc:
        raise OllamaUnavailable(f"cannot list local models: {exc}") from exc


def chat(
    prompt: str,
    system: str | None = None,
    model: str = PRIMARY_MODEL,
    num_ctx: int = DEFAULT_NUM_CTX,
    temperature: float = 0.4,
    no_think: bool = False,
    retries: int = 2,
    timeout_s: int = GEN_TIMEOUT_S,
) -> str:
    """Run one chat completion on the local GPU and return think-stripped text.

    Raises OllamaUnavailable if the runtime is down, OllamaError on generation
    failure after retries. The model router interprets these as rung failures.
    """
    num_ctx = min(int(num_ctx), MAX_NUM_CTX)
    user_content = prompt + ("\n/no_think" if no_think else "")
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": user_content})

    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {"num_ctx": num_ctx, "temperature": temperature},
    }

    last_err: Exception | None = None
    for attempt in range(retries + 1):
        try:
            with _GPU_LOCK:  # one model, one generation at a time
                r = requests.post(
                    f"{OLLAMA_URL}/api/chat", json=payload, timeout=timeout_s
                )
            if r.status_code >= 500:
                raise OllamaError(f"ollama server error {r.status_code}: {r.text[:500]}")
            r.raise_for_status()
            body = r.json()
            content = (body.get("message") or {}).get("content", "")
            text = strip_think(content)
            if not text:
                raise OllamaError("empty response after think-stripping")
            return text
        except requests.ConnectionError as exc:
            last_err = OllamaUnavailable(f"ollama unreachable at {OLLAMA_URL}: {exc}")
        except requests.Timeout as exc:
            last_err = OllamaError(f"generation timed out after {timeout_s}s: {exc}")
        except (requests.RequestException, ValueError, OllamaError) as exc:
            last_err = exc if isinstance(exc, OllamaError) else OllamaError(str(exc))
        if attempt < retries:
            backoff = 2 ** attempt
            log.warning("ollama call failed (%s); retrying in %ss", last_err, backoff)
            time.sleep(backoff)
    assert last_err is not None
    raise last_err


def chat_json(
    prompt: str,
    system: str | None = None,
    model: str = PRIMARY_MODEL,
    num_ctx: int = DEFAULT_NUM_CTX,
    retries: int = 2,
) -> dict:
    """Chat expecting a JSON object back (temp 0, /no_think, fenced-JSON tolerant)."""
    text = chat(
        prompt,
        system=(system or "") + "\nRespond with a single valid JSON object and nothing else.",
        model=model,
        num_ctx=num_ctx,
        temperature=0.0,
        no_think=True,
        retries=retries,
    )
    # Tolerate ```json fences and leading prose.
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise OllamaError(f"no JSON object in model response: {text[:200]!r}")
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        raise OllamaError(f"invalid JSON from model: {exc}: {match.group(0)[:200]!r}") from exc
