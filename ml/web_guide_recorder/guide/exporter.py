from __future__ import annotations

import asyncio
import base64
import os
from datetime import datetime
from pathlib import Path

import aiofiles
from jinja2 import Environment, FileSystemLoader, select_autoescape

try:
    from web_guide_recorder import config
    from web_guide_recorder.agent.recorder import Guide
except ModuleNotFoundError:
    import config
    from agent.recorder import Guide


def _stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _rel_screenshot(screenshot_path: str, md_dir: Path) -> str:
    """Path to embed in Markdown — must be relative to the MD file's dir."""
    return os.path.relpath(screenshot_path, str(md_dir)).replace(os.sep, "/")


async def export_markdown(guide: Guide, output_path: str) -> str:
    out_dir = Path(output_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    file_path = out_dir / f"guide_{_stamp()}.md"

    lines = [f"# Гайд: {guide.goal}", f"Сайт: {guide.start_url}", ""]
    for step in guide.steps:
        rel = _rel_screenshot(step.screenshot_path, out_dir)
        lines.extend(
            [
                f"## Шаг {step.number}",
                f"![скриншот]({rel})",
                step.description,
                "",
            ]
        )

    async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
        await f.write("\n".join(lines))

    return str(file_path)


async def export_html(guide: Guide, output_path: str) -> str:
    out_dir = Path(output_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    file_path = out_dir / f"guide_{_stamp()}.html"

    env = Environment(
        loader=FileSystemLoader(str(config.BASE_DIR / "guide" / "templates")),
        autoescape=select_autoescape(["html", "xml"]),
    )
    tpl = env.get_template("guide.html.j2")

    async def to_b64(path: str) -> str:
        data = await asyncio.to_thread(Path(path).read_bytes)
        return base64.b64encode(data).decode("utf-8")

    steps = []
    for step in guide.steps:
        steps.append(
            {
                "number": step.number,
                "url": step.url,
                "description": step.description,
                "screenshot_base64": await to_b64(step.screenshot_path),
            }
        )

    html = tpl.render(guide=guide, steps=steps)
    async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
        await f.write(html)

    return str(file_path)
