"""Browser tool: invokes web_guide_recorder via subprocess.

The recorder spins up a real browser (browser-use), navigates from a
start URL toward a natural-language goal and produces a markdown guide
with screenshots. Recorder stdout is inherited so its step-by-step
progress shows up in the same console as the ReAct agent.
"""

from __future__ import annotations

import asyncio
import logging
import re
import sys
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)

# project_llm/ — родитель agent/
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RECORDER_DIR = PROJECT_ROOT / "web_guide_recorder"
RECORDER_MAIN = RECORDER_DIR / "main.py"

DEFAULT_TIMEOUT_SECONDS = 900  # 15 минут на всю запись
GUIDE_PREVIEW_CHARS = 2000


_MD_PATH_PATTERN = re.compile(r"Markdown гайд:\s*(\S+)")


async def record_web_guide(
    start_url: str,
    goal: str,
    headless: bool = False,
    max_steps: int = 30,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> Dict[str, Any]:
    """Запускает web_guide_recorder и ждёт результата."""
    if not RECORDER_MAIN.exists():
        return {"error": f"web_guide_recorder/main.py not found at {RECORDER_MAIN}"}

    cmd = [
        sys.executable,
        str(RECORDER_MAIN),
        "--url", start_url,
        "--goal", goal,
        "--format", "md",
        "--max-steps", str(max_steps),
        "--headless" if headless else "--no-headless",
    ]
    logger.info("record_web_guide | start | url=%s goal=%r max_steps=%d", start_url, goal, max_steps)

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=str(RECORDER_DIR),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )

    lines: list[str] = []
    timed_out = False
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout_seconds

    while True:
        remaining = deadline - loop.time()
        if remaining <= 0:
            timed_out = True
            break

        try:
            line_bytes = await asyncio.wait_for(proc.stdout.readline(), timeout=remaining)
        except asyncio.TimeoutError:
            timed_out = True
            break

        if not line_bytes:
            break

        line = line_bytes.decode("utf-8", errors="replace").rstrip("\n")
        lines.append(line)
        # Пишем лог сразу, чтобы прогресс был "живым".
        logger.info("recorder | %s", line)

    if timed_out:
        proc.kill()
        await proc.wait()
        stdout = "\n".join(lines)
        logger.error("record_web_guide | timeout after %ds", timeout_seconds)
        return {"error": f"recorder timed out after {timeout_seconds}s", "stdout_tail": stdout[-1500:]}

    await proc.wait()
    stdout = "\n".join(lines)

    if proc.returncode != 0:
        logger.error("record_web_guide | rc=%s", proc.returncode)
        return {
            "error": f"recorder exited with code {proc.returncode}",
            "stdout_tail": stdout[-1500:],
        }

    md_match = _MD_PATH_PATTERN.search(stdout)
    md_path = md_match.group(1) if md_match else ""
    preview = ""
    if md_path and Path(md_path).exists():
        try:
            preview = Path(md_path).read_text(encoding="utf-8")[:GUIDE_PREVIEW_CHARS]
        except Exception as exc:  # noqa: BLE001
            preview = f"(failed to read guide: {exc})"

    logger.info("record_web_guide | done | md=%s preview_chars=%d", md_path, len(preview))
    return {
        "guide_path": md_path,
        "guide_preview": preview,
        "stdout_tail": stdout[-800:],
    }
