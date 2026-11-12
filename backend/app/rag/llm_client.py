"""
Groq client wrapper with reasoning-model handling.

openai/gpt-oss-20b is a REASONING model: its hidden thinking tokens count
against max_tokens, and if the budget is small the model returns an EMPTY
content string with finish_reason="length" [citation:10].

Fixes:
- Pass reasoning_effort="low" to reduce hidden thinking.
- Raise max_tokens so reasoning + answer both fit.
- Detect empty content and raise a clear error instead of returning "".
"""
from __future__ import annotations

import logging
from typing import Any

from groq import Groq

from app.config.settings import settings

logger = logging.getLogger(__name__)

_client: Groq | None = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        if not settings.GROQ_API_KEY:
            raise RuntimeError("GROQ_API_KEY is not set in .env")
        _client = Groq(api_key=settings.GROQ_API_KEY, timeout=60.0)
    return _client


def chat(
    messages: list[dict[str, str]],
    *,
    model: str | None = None,
    temperature: float = 0.1,
    max_tokens: int = 2048,
    reasoning_effort: str = "low",
) -> dict[str, Any]:
    client = _get_client()
    chosen_model = model or settings.GROQ_MODEL

    kwargs: dict[str, Any] = {
        "model": chosen_model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    # Only gpt-oss models accept reasoning_effort on Groq.
    if "gpt-oss" in chosen_model:
       kwargs["extra_body"] = {"reasoning_effort": reasoning_effort}

    try:
        resp = client.chat.completions.create(**kwargs)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Groq call failed: %s", exc)
        raise RuntimeError(f"LLM call failed: {exc}") from exc

    choice = resp.choices[0]
    content = choice.message.content or ""

    if not content.strip():
        finish = getattr(choice, "finish_reason", "unknown")
        reasoning_used = getattr(resp.usage, "completion_tokens_details", None)
        logger.error(
            "Empty LLM content (model=%s, finish_reason=%s, usage=%s)",
            chosen_model, finish, reasoning_used,
        )
        raise RuntimeError(
            f"Model returned empty content (finish_reason={finish}). "
            "Reasoning tokens may have consumed the budget."
        )

    return {
        "content": content,
        "model": resp.model,
        "usage": {
            "prompt_tokens": getattr(resp.usage, "prompt_tokens", None),
            "completion_tokens": getattr(resp.usage, "completion_tokens", None),
        },
    }
