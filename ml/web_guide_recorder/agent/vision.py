"""Ollama VLM client for step description.

Uses the chat API (`/api/chat`) with `images` attached to the user message,
which is the supported way to pass image input to multimodal Ollama models.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

try:
    from web_guide_recorder import config
except ModuleNotFoundError:
    import config

logger = logging.getLogger(__name__)

PROMPT_TEMPLATE = """Ты пишешь подпись к одному шагу видео-инструкции на русском языке.

Цель: {goal}
Действие: {action_taken}
Тип действия: {action_type}
Введённый текст: {action_value}

Посмотри на скриншот. Напиши ОДНО короткое предложение — что нужно сделать на этом экране.

Правила:
- Одно предложение, до 12 слов.
- Начни с глагола: «Нажмите», «Введите», «Выберите», «Прокрутите», «Перейдите».
- Укажи название элемента в кавычках точно как на экране.
- Укажи где он находится (в шапке / в меню / слева / внизу).
- Первое слово строки — «[Блок N]» где N — номер интерактивного элемента.
  Если неизвестен — «[Блок ?]».
- Не используй слова «я вижу», «на скриншоте», «страница».

Пример: [Блок 8] Нажмите «Спорт» в верхнем меню.
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


async def describe_step(
    screenshot_base64: str,
    action_taken: str,
    goal: str,
    action_type: str | None = None,
    action_value: str | None = None,
) -> str:
    """Send a screenshot + context to the VLM and return a 2-3 sentence instruction."""
    prompt = PROMPT_TEMPLATE.format(
        goal=goal,
        action_taken=action_taken,
        action_type=action_type or "не определён",
        action_value=action_value or "—",
    )
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
