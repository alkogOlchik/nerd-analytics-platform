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
import ast
import json
import re

import imagehash
from PIL import Image

try:
    from web_guide_recorder import config
    from web_guide_recorder.agent.browser import build_agent, build_browser
    from web_guide_recorder.agent.vision import describe_step, ollama_health_check
except ModuleNotFoundError:
    import config
    from agent.browser import build_agent, build_browser
    from agent.vision import describe_step, ollama_health_check

logger = logging.getLogger(__name__)

# phash distance < this = "same screen". 0 = identical, ~64 = totally different.
PHASH_DIFF_THRESHOLD = 5
MAX_CONSECUTIVE_NOOP_STEPS = config.MAX_CONSECUTIVE_NOOP_STEPS
MAX_CONSECUTIVE_DUPLICATE_STEPS = config.MAX_CONSECUTIVE_DUPLICATE_STEPS


# NOTE: we don't raise from inside the new-step callback anymore —
# browser-use's Agent.run() swallows exceptions thrown from a step, so the
# loop kept going. Instead we call `agent.stop()` (which sets
# `agent.state.stopped = True`) and record the reason on the recorder.
STOP_REASON_GOAL = "goal_reached"
STOP_REASON_LOOP = "loop_detected"


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
    target_index: Optional[int]
    target_bbox: Optional[tuple[int, int, int, int]]
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
        self._consecutive_noop_steps = 0
        self._consecutive_duplicate_steps = 0
        self._agent: Any = None
        self._stop_reason: Optional[str] = None
        self._stop_detail: str = ""

    def _stop_agent(self, reason: str, detail: str) -> None:
        """Politely tell the browser-use Agent to stop after current step.

        We rely on `agent.state.stopped` (set by Agent.stop()), which
        Agent.run() checks between steps.
        """
        if self._stop_reason is not None:
            return  # already stopping
        self._stop_reason = reason
        self._stop_detail = detail
        logger.info("Запрос остановки агента: reason=%s | detail=%s", reason, detail)
        agent = self._agent
        if agent is None:
            return
        try:
            if hasattr(agent, "stop"):
                agent.stop()
                return
        except Exception:  # noqa: BLE001
            logger.debug("agent.stop() raised", exc_info=True)
        # Fallback: poke the internal state flag directly.
        state = getattr(agent, "state", None)
        if state is not None:
            try:
                state.stopped = True
            except Exception:  # noqa: BLE001
                logger.debug("setting state.stopped failed", exc_info=True)

    async def record(self, start_url: str, goal: str) -> Guide:
        await ollama_health_check()
        config.SCREENSHOTS_PATH.mkdir(parents=True, exist_ok=True)

        guide = Guide(goal=goal, start_url=start_url)
        self._guide = guide
        self._prev_url = ""
        self._prev_hash = None
        self._consecutive_noop_steps = 0
        self._consecutive_duplicate_steps = 0
        self._stop_reason = None
        self._stop_detail = ""

        browser = build_browser(headless=self.headless)
        task = (
            f"Achieve this goal on a website: '{goal}'. "
            f"Start at {start_url}. "
            "Work step by step until the goal is reached. "
            "Prioritize clicking visible navigation links/tabs/buttons and opening menus. "
            "If searching for a section, first look for exact text matches in links/menu items "
            "(for example: 'Спорт') and click them. "
            "Use scrolling only when interactive elements are not visible. "
            "\n"
            "HARD STOP RULES:\n"
            "- Maximum 2 attempts of the same approach. If something fails twice (element not "
            "clickable, no progress, same screen) — switch strategy or call `done`.\n"
            "- If the current page already matches the goal, call `done` with success=true IMMEDIATELY. "
            "Do not keep scrolling/clicking after the goal is reached.\n"
            "- Never emit an empty action — call `done` instead."
        )
        agent = build_agent(task=task, browser=browser, on_new_step=self._on_new_step)
        self._agent = agent

        try:
            await agent.run(max_steps=self.max_steps)
        except KeyboardInterrupt:
            logger.warning("Ctrl+C — сохраняю частичный гайд")
        except Exception as exc:  # noqa: BLE001 — let exporter still run on partial state
            logger.exception("Agent run failed: %s", exc)
        finally:
            if self._stop_reason:
                logger.info(
                    "Запись остановлена: reason=%s | %s", self._stop_reason, self._stop_detail
                )
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
            is_noop = self._is_noop_action(agent_output)
            if is_noop:
                self._consecutive_noop_steps += 1
            else:
                self._consecutive_noop_steps = 0

            target_index, target_bbox = self._extract_target(agent_output, browser_state)
            logger.info(
                "Шаг %s/%s | url=%s | action=%s | target_index=%s | noop=%s",
                step_number,
                self.max_steps,
                _short(url, 180) or "(empty)",
                _short(action_raw, 180) or "(empty)",
                target_index if target_index is not None else "?",
                is_noop,
            )
            # Early successful stop: goal URL already reached and model started no-oping.
            if is_noop and self._looks_goal_reached(url, guide.goal):
                self._stop_agent(STOP_REASON_GOAL, "Цель уже достигнута, получен no-op")
                return

            if self._consecutive_noop_steps >= MAX_CONSECUTIVE_NOOP_STEPS:
                if self._looks_goal_reached(url, guide.goal):
                    self._stop_agent(STOP_REASON_GOAL, "Цель достигнута, дальнейшие шаги не нужны")
                else:
                    self._stop_agent(
                        STOP_REASON_LOOP,
                        f"Получено {self._consecutive_noop_steps} пустых действий подряд",
                    )
                return

            if not png_bytes:
                logger.warning("Шаг %s: нет скриншота в state, пропускаю", step_number)
                return

            phash = await asyncio.to_thread(self._phash, png_bytes)
            if self._is_duplicate(url, phash):
                self._consecutive_duplicate_steps += 1
                logger.info("Шаг %s: пропуск (дубликат URL+экран)", step_number)
                if self._consecutive_duplicate_steps >= MAX_CONSECUTIVE_DUPLICATE_STEPS:
                    if self._looks_goal_reached(url, guide.goal):
                        self._stop_agent(
                            STOP_REASON_GOAL,
                            "Цель достигнута, повторяются одинаковые экраны",
                        )
                    else:
                        self._stop_agent(
                            STOP_REASON_LOOP,
                            f"Получено {self._consecutive_duplicate_steps} дубликатов экрана подряд",
                        )
                return
            self._consecutive_duplicate_steps = 0

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
            description = self._ensure_block_prefix(description, target_index)

            step = Step(
                number=next_index,
                url=url,
                screenshot_path=str(screenshot_path),
                description=description,
                action_raw=action_raw,
                target_index=target_index,
                target_bbox=target_bbox,
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
    def _extract_target(agent_output: Any, browser_state: Any) -> tuple[Optional[int], Optional[tuple[int, int, int, int]]]:
        action_obj = None
        for attr in ("action", "current_action", "next_action"):
            value = getattr(agent_output, attr, None)
            if value:
                action_obj = value
                break

        target_index = GuideRecorder._extract_index_from_action(action_obj)
        if target_index is None:
            target_index = GuideRecorder._extract_index_from_action(str(agent_output))

        if target_index is None:
            return None, None

        bbox = GuideRecorder._extract_bbox_from_state(browser_state, target_index)
        return target_index, bbox

    @staticmethod
    def _extract_index_from_action(action_obj: Any) -> Optional[int]:
        def walk(v: Any) -> Optional[int]:
            if isinstance(v, dict):
                if "index" in v and isinstance(v["index"], int):
                    return v["index"]
                for item in v.values():
                    hit = walk(item)
                    if hit is not None:
                        return hit
            elif isinstance(v, list):
                for item in v:
                    hit = walk(item)
                    if hit is not None:
                        return hit
            return None

        if action_obj is None:
            return None

        if isinstance(action_obj, (dict, list)):
            return walk(action_obj)

        if isinstance(action_obj, str):
            for parser in (json.loads, ast.literal_eval):
                try:
                    parsed = parser(action_obj)
                    hit = walk(parsed)
                    if hit is not None:
                        return hit
                except Exception:  # noqa: BLE001
                    continue
        return None

    @staticmethod
    def _extract_bbox_from_state(state: Any, index: int) -> Optional[tuple[int, int, int, int]]:
        selector_map = getattr(state, "selector_map", None)
        if not isinstance(selector_map, dict):
            return None
        node = selector_map.get(index)
        if node is None:
            node = selector_map.get(str(index))
        if node is None:
            return None

        def dig(o: Any, names: list[str]) -> Any:
            cur = o
            for name in names:
                if isinstance(cur, dict):
                    cur = cur.get(name)
                else:
                    cur = getattr(cur, name, None)
                if cur is None:
                    return None
            return cur

        x = dig(node, ["x"])
        y = dig(node, ["y"])
        w = dig(node, ["width"])
        h = dig(node, ["height"])
        if all(isinstance(v, (int, float)) for v in (x, y, w, h)):
            return (int(x), int(y), int(x + w), int(y + h))

        bbox = dig(node, ["bbox"])
        if isinstance(bbox, dict):
            x = bbox.get("x")
            y = bbox.get("y")
            w = bbox.get("width")
            h = bbox.get("height")
            if all(isinstance(v, (int, float)) for v in (x, y, w, h)):
                return (int(x), int(y), int(x + w), int(y + h))

        return None

    @staticmethod
    def _is_noop_action(agent_output: Any) -> bool:
        payload = None
        for attr in ("action", "current_action", "next_action"):
            value = getattr(agent_output, attr, None)
            if value is not None:
                payload = value
                break
        if payload is None:
            return True
        return not GuideRecorder._has_meaningful_action(payload)

    @staticmethod
    def _has_meaningful_action(value: Any) -> bool:
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return True
        if isinstance(value, str):
            return bool(value.strip()) and value.strip() not in ("{}", "[]")
        if isinstance(value, dict):
            for k, v in value.items():
                if k == "done" and not v:
                    continue
                if GuideRecorder._has_meaningful_action(v):
                    return True
            return False
        if isinstance(value, (list, tuple, set)):
            return any(GuideRecorder._has_meaningful_action(v) for v in value)
        if hasattr(value, "model_dump"):
            try:
                return GuideRecorder._has_meaningful_action(value.model_dump())
            except Exception:  # noqa: BLE001
                pass
        if hasattr(value, "__dict__"):
            try:
                return GuideRecorder._has_meaningful_action(vars(value))
            except Exception:  # noqa: BLE001
                pass
        return True

    @staticmethod
    def _ensure_block_prefix(description: str, target_index: Optional[int]) -> str:
        if not description:
            return "[Блок ?] [автоопределение недоступно]"
        if re.search(r"^\[Блок\s+[^]]+\]", description.strip()):
            return description
        if target_index is None:
            return f"[Блок ?] {description}"
        return f"[Блок {target_index}] {description}"

    @staticmethod
    def _looks_goal_reached(url: str, goal: str) -> bool:
        u = (url or "").lower()
        g = (goal or "").lower()
        if not u:
            return False
        # Practical heuristic for your main scenario.
        if "sport" in u or "спорт" in u:
            return True
        for token in ("спорт", "sport", "футбол", "football"):
            if token in g and token in u:
                return True
        return False

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
