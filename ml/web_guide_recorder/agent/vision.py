"""Ollama VLM client for step description.

Uses the chat API (`/api/chat`) with `images` attached to the user message,
which is the supported way to pass image input to multimodal Ollama models.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

import config

logger = logging.getLogger(__name__)

PROMPT_TEMPLATE = """You are a technical writer creating a step-by-step user guide.

Goal the user is trying to achieve: {goal}
Action just performed: {action_taken}

Look at this screenshot and write ONE clear instruction step that tells
a human user what to do on this page to achieve the goal.

Rules:
- Write in simple, clear language
- Be specific: name buttons, links, fields as they appear on screen
- One sentence or two maximum
- Do not describe what YOU see, write instructions FOR the user
- Include block index when available from action context.
- Strict format:
  "[Блок N] Click [element] to [result]"
  or
  "[Блок N] Enter [value] in [field]"
  If index is unknown, use [Блок ?].
"""


async def ollama_health_check() -> None:
    """Verify Ollama is reachable and the configured model is loaded."""
    timeout = httpx.Timeout(10.0)
    async with httpx.AsyncClient(base_url=config.OLLAMA_BASE_URL, timeout=timeout) as client:
        tags_response = await client.get("/api/tags")
        tags_response.raise_for_status()
        payload = tags_response.json()
        models = payload.get("models", [])
        available = {m.get("model") for m in models if isinstance(m, dict)}
        if config.OLLAMA_MODEL not in available:
            raise RuntimeError(
                f"Model '{config.OLLAMA_MODEL}' is not available in Ollama. "
                f"Found: {sorted(available)}"
            )


async def describe_step(screenshot_base64: str, action_taken: str, goal: str) -> str:
    """Send a screenshot + context to the VLM and return one short instruction."""
    prompt = PROMPT_TEMPLATE.format(goal=goal, action_taken=action_taken)
    body: dict[str, Any] = {
        "model": config.OLLAMA_MODEL,
        "messages": [
            {
                "role": "user",
                "content": prompt,
                "images": [screenshot_base64],
            }
        ],
        "stream": False,
        "options": {"num_ctx": config.OLLAMA_CTX_SIZE},
    }

    timeout = httpx.Timeout(config.STEP_TIMEOUT_SECONDS)
    try:
        async with httpx.AsyncClient(base_url=config.OLLAMA_BASE_URL, timeout=timeout) as client:
            response = await client.post("/api/chat", json=body)
            response.raise_for_status()
            payload = response.json()
            text = str(payload.get("message", {}).get("content", "")).strip()
            return text or "[автоопределение недоступно]"
    except Exception as exc:  # noqa: BLE001 — VLM must never crash the recorder
        logger.warning("VLM request failed: %s", exc)
        return "[автоопределение недоступно]"
