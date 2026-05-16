from __future__ import annotations

import argparse
import asyncio
import logging

import config
from agent.recorder import Guide, GuideRecorder
from guide.exporter import export_html, export_markdown


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


async def export_outputs(guide: Guide, fmt: str) -> None:
    config.GUIDES_PATH.mkdir(parents=True, exist_ok=True)

    if fmt in ("md", "both"):
        path = await export_markdown(guide, str(config.GUIDES_PATH))
        print(f"✅ Markdown гайд: {path}")

    if fmt in ("html", "both"):
        path = await export_html(guide, str(config.GUIDES_PATH))
        print(f"✅ HTML гайд: {path}")


async def run() -> None:
    parser = argparse.ArgumentParser(description="Web Guide Recorder")
    parser.add_argument("--url", required=True, help="Стартовый URL")
    parser.add_argument("--goal", required=True, help="Цель навигации")
    parser.add_argument("--format", choices=["md", "html", "both"], default="both")
    parser.add_argument(
        "--headless",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Override BROWSER_HEADLESS from config; --no-headless to force GUI",
    )
    parser.add_argument("--max-steps", type=int, default=config.MAX_STEPS)
    args = parser.parse_args()

    setup_logging()

    recorder = GuideRecorder(headless=args.headless, max_steps=args.max_steps)
    guide: Guide | None = None

    try:
        guide = await recorder.record(start_url=args.url, goal=args.goal)
    except KeyboardInterrupt:
        logging.getLogger(__name__).warning("Получен Ctrl+C")

    if guide is not None:
        await export_outputs(guide, args.format)
    else:
        print("⚠️ Гайд не был создан")


if __name__ == "__main__":
    asyncio.run(run())
