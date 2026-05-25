"""Ollama VLM client.

Описания шагов теперь генерируются ОДНИМ проходом ПОСЛЕ записи через
`describe_all_steps(guide)`: модель видит контекст предыдущих описаний,
target_text целевого элемента, цель пользователя и сам скриншот.
"""

from __future__ import annotations

import asyncio
import base64
import logging
import re
from pathlib import Path
from typing import Any, TYPE_CHECKING

import httpx

try:
    from web_guide_recorder import config
except ModuleNotFoundError:
    import config

if TYPE_CHECKING:
    try:
        from web_guide_recorder.agent.recorder import Guide, Step
    except ModuleNotFoundError:
        from agent.recorder import Guide, Step

logger = logging.getLogger(__name__)


PROMPT_TEMPLATE = """Ты пишешь подпись к одному шагу видео-инструкции на русском языке.

Общая цель пользователя: {goal}
Сайт: {start_url}

Шаг номер: {step_number} из {total_steps}
Действие: {action_type}
Введённый текст: {action_value}
Текст целевого элемента (точно как на экране): {target_text}
Индекс блока: {target_index}

Предыдущие шаги (НЕ повторяйся, новый шаг должен быть про другое):
{previous_descriptions_numbered}

Посмотри на скриншот и опиши ТОЛЬКО ЭТОТ шаг.

Правила:
- Одно предложение, 8–14 слов.
- На русском, без английских слов и без URL.
- Начни с глагола в повелительном наклонении.
- Если есть «Текст целевого элемента» — назови его в «кавычках» именно с этим текстом.
- Укажи где элемент на экране (в шапке, в меню сверху, слева, внизу).
- Не пиши «я вижу», «на скриншоте», «страница».
- Первое слово строки — «[Блок N]» (если индекса нет — «[Блок ?]»).

Пример: [Блок 8] Нажмите ссылку «Спорт» в верхнем меню сайта.
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


def _ensure_block_prefix(description: str, target_index: Any) -> str:
    if not description:
        return "[Блок ?] [автоопределение недоступно]"
    if re.search(r"^\[Блок\s+[^]]+\]", description.strip()):
        return description.strip()
    if target_index is None:
        return f"[Блок ?] {description.strip()}"
    return f"[Блок {target_index}] {description.strip()}"


def _postprocess_description(text: str, target_index: Any) -> str:
    """Берём 1–2 предложения, чистим пустые строки, добавляем префикс."""
    s = (text or "").strip()
    # Срезаем модельные преамбулы.
    s = re.sub(r"^(вот|конечно|хорошо)[^.\n]*[.:]\s*", "", s, flags=re.IGNORECASE)
    # Берём первые 2 предложения максимум.
    parts = re.split(r"(?<=[\.\!\?])\s+", s)
    s = " ".join(p for p in parts[:2] if p)
    s = re.sub(r"\s+", " ", s).strip()
    return _ensure_block_prefix(s, target_index)


def _format_previous_descriptions(prev: list[str]) -> str:
    if not prev:
        return "(пока нет — это первый шаг)"
    lines = []
    for i, d in enumerate(prev, start=1):
        lines.append(f"{i}. {d}")
    return "\n".join(lines)


def _read_screenshot_b64(path: str) -> str:
    return base64.b64encode(Path(path).read_bytes()).decode("utf-8")


async def _describe_one(
    *,
    goal: str,
    start_url: str,
    step_number: int,
    total_steps: int,
    action_type: str | None,
    action_value: str | None,
    target_text: str | None,
    target_index: int | None,
    previous_descriptions: list[str],
    screenshot_path: str,
) -> str:
    prompt = PROMPT_TEMPLATE.format(
        goal=goal or "—",
        start_url=start_url or "—",
        step_number=step_number,
        total_steps=total_steps,
        action_type=action_type or "не определён",
        action_value=action_value or "—",
        target_text=target_text or "не определён",
        target_index=target_index if target_index is not None else "?",
        previous_descriptions_numbered=_format_previous_descriptions(previous_descriptions),
    )

    try:
        screenshot_b64 = await asyncio.to_thread(_read_screenshot_b64, screenshot_path)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Cannot read screenshot %s: %s", screenshot_path, exc)
        return _ensure_block_prefix("", target_index)

    body: dict[str, Any] = {
        "model": config.OLLAMA_MODEL,
        "messages": [
            {
                "role": "user",
                "content": prompt,
                "images": [screenshot_b64],
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
    except Exception as exc:  # noqa: BLE001 — VLM не должен ломать пайплайн
        logger.warning("VLM request failed (step %s): %s", step_number, exc)
        return _ensure_block_prefix("", target_index)

    return _postprocess_description(text, target_index)


async def describe_all_steps(guide: "Guide") -> None:
    """Single-pass генерация подписей для всех шагов гайда.

    Идём строго по порядку, чтобы модель видела ранее сгенерированные подписи
    и не повторялась. Заполняет `step.description` in-place.
    """
    if not guide.steps:
        return

    total = len(guide.steps)
    previous: list[str] = []
    for step in guide.steps:
        target_text = getattr(step, "target_text", None)
        description = await _describe_one(
            goal=guide.goal,
            start_url=guide.start_url,
            step_number=step.number,
            total_steps=total,
            action_type=step.action_type,
            action_value=step.action_value,
            target_text=target_text,
            target_index=step.target_index,
            previous_descriptions=previous,
            screenshot_path=step.screenshot_path,
        )
        step.description = description
        previous.append(description)
        logger.info(
            "Описание шага %s/%s готово: %s",
            step.number,
            total,
            (description[:160] + "…") if len(description) > 160 else description,
        )
