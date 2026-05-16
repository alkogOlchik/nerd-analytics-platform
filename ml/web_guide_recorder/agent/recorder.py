"""Guide recorder: runs one browser-use Agent for the whole task and
records each new step via the Agent's callback.

Deduplication uses perceptual hashing (imagehash.phash): tiny animations,
ads, blinking cursors etc. won't break it the way an exact byte hash does.
"""

from __future__ import annotations

import asyncio
import base64
import io
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import imagehash
from PIL import Image

import config
from agent.browser import build_agent, build_browser
from agent.vision import describe_step, ollama_health_check

logger = logging.getLogger(__name__)

# phash distance < this = "same screen". 0 = identical, ~64 = totally different.
PHASH_DIFF_THRESHOLD = 5


def _short(text: Any, limit: int = 220) -> str:
    s = str(text or "").replace("\n", " ").strip()
    if len(s) <= limit:
        return s
    return s[:limit] + f"…[+{len(s)-limit} chars]"


@dataclass
class Step:
    number: int
    url: str
    screenshot_path: str
    description: str
    action_raw: str
    timestamp: float


@dataclass
class Guide:
    goal: str
    start_url: str
    steps: list[Step] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)


class GuideRecorder:
    def __init__(
        self,
        headless: bool | None = None,
        max_steps: int = config.MAX_STEPS,
    ) -> None:
        self.headless = headless
        self.max_steps = max_steps
        self._guide: Optional[Guide] = None
        self._prev_url = ""
        self._prev_hash: Optional[imagehash.ImageHash] = None

    async def record(self, start_url: str, goal: str) -> Guide:
        await ollama_health_check()
        config.SCREENSHOTS_PATH.mkdir(parents=True, exist_ok=True)

        guide = Guide(goal=goal, start_url=start_url)
        self._guide = guide
        self._prev_url = ""
        self._prev_hash = None

        browser = build_browser(headless=self.headless)
        task = (
            f"Achieve this goal on a website: '{goal}'. "
            f"Start at {start_url}. "
            "Work step by step until the goal is reached. "
            "Prioritize clicking visible navigation links/tabs/buttons and opening menus. "
            "If searching for a section, first look for exact text matches in links/menu items "
            "(for example: 'Спорт') and click them. "
            "Use scrolling only when interactive elements are not visible. "
            "Avoid repeating the same scroll direction multiple times in a row."
        )
        agent = build_agent(task=task, browser=browser, on_new_step=self._on_new_step)

        try:
            await agent.run(max_steps=self.max_steps)
        except KeyboardInterrupt:
            logger.warning("Ctrl+C — сохраняю частичный гайд")
        except Exception as exc:  # noqa: BLE001 — let exporter still run on partial state
            logger.exception("Agent run failed: %s", exc)
        finally:
            try:
                await browser.close()
            except Exception:  # noqa: BLE001
                logger.debug("Browser close raised", exc_info=True)

        return guide

    async def _on_new_step(
        self,
        browser_state: Any,
        agent_output: Any,
        step_number: int,
    ) -> None:
        """browser-use calls this after each step. Never raise from here —
        a failed callback should not break the browsing agent."""
        guide = self._guide
        if guide is None:
            return

        try:
            url = self._extract_url(browser_state)
            png_bytes = self._extract_screenshot(browser_state)
            action_raw = self._extract_action(agent_output)
            logger.info(
                "Шаг %s/%s | url=%s | action=%s",
                step_number,
                self.max_steps,
                _short(url, 180) or "(empty)",
                _short(action_raw, 180) or "(empty)",
            )

            if not png_bytes:
                logger.warning("Шаг %s: нет скриншота в state, пропускаю", step_number)
                return

            phash = await asyncio.to_thread(self._phash, png_bytes)
            if self._is_duplicate(url, phash):
                logger.info("Шаг %s: пропуск (дубликат URL+экран)", step_number)
                return

            next_index = len(guide.steps) + 1
            screenshot_path = await self._save_jpeg(png_bytes, next_index)
            screenshot_b64 = base64.b64encode(png_bytes).decode("utf-8")

            description = await asyncio.wait_for(
                describe_step(
                    screenshot_base64=screenshot_b64,
                    action_taken=action_raw,
                    goal=guide.goal,
                ),
                timeout=config.STEP_TIMEOUT_SECONDS,
            )

            step = Step(
                number=next_index,
                url=url,
                screenshot_path=str(screenshot_path),
                description=description,
                action_raw=action_raw,
                timestamp=time.time(),
            )
            guide.steps.append(step)
            self._prev_url = url
            self._prev_hash = phash
            logger.info(
                "Сохранен шаг %s/%s | url=%s | action=%s | desc=%s | shot=%s",
                next_index,
                self.max_steps,
                _short(url, 160) or "(empty)",
                _short(action_raw, 160) or "(empty)",
                _short(description, 180) or "(empty)",
                screenshot_path.name,
            )
        except asyncio.TimeoutError:
            logger.warning("Шаг %s: таймаут VLM, пропускаю шаг", step_number)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Шаг %s: ошибка записи (%s)", step_number, exc)

    @staticmethod
    def _extract_url(state: Any) -> str:
        for attr in ("url", "current_url"):
            value = getattr(state, attr, None)
            if value:
                return str(value)
        return ""

    @staticmethod
    def _extract_screenshot(state: Any) -> Optional[bytes]:
        # browser-use BrowserState exposes a base64-encoded PNG screenshot.
        b64 = getattr(state, "screenshot", None)
        if not b64:
            return None
        try:
            return base64.b64decode(b64)
        except Exception:  # noqa: BLE001
            return None

    @staticmethod
    def _extract_action(agent_output: Any) -> str:
        # Different browser-use versions name this differently; try common fields.
        for attr in ("action", "current_action", "next_action", "thought"):
            value = getattr(agent_output, attr, None)
            if value:
                return str(value)[:300]
        return str(agent_output)[:300]

    @staticmethod
    def _phash(png_bytes: bytes) -> imagehash.ImageHash:
        with Image.open(io.BytesIO(png_bytes)) as img:
            return imagehash.phash(img.convert("RGB"))

    def _is_duplicate(self, url: str, phash: imagehash.ImageHash) -> bool:
        if self._prev_hash is None:
            return False
        if url != self._prev_url:
            return False
        return (phash - self._prev_hash) < PHASH_DIFF_THRESHOLD

    async def _save_jpeg(self, png_bytes: bytes, index: int) -> Path:
        out_path = config.SCREENSHOTS_PATH / f"step_{index:03d}.jpg"

        def _write() -> None:
            with Image.open(io.BytesIO(png_bytes)) as img:
                img.convert("RGB").save(
                    out_path,
                    format="JPEG",
                    quality=config.SCREENSHOT_QUALITY,
                    optimize=True,
                )

        await asyncio.to_thread(_write)
        return out_path
