from __future__ import annotations

import asyncio
import re
import shlex
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw

try:
    from web_guide_recorder.agent.recorder import Guide, Step
except ModuleNotFoundError:
    from agent.recorder import Guide, Step


def _stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _extract_block_index(step: Step) -> Optional[int]:
    if step.target_index is not None:
        return step.target_index
    m = re.search(r"\[Блок\s+(\d+)\]", step.description)
    if m:
        return int(m.group(1))
    return None


def _target_point(img_w: int, img_h: int, step: Step) -> tuple[int, int]:
    if step.target_bbox:
        x1, y1, x2, y2 = step.target_bbox
        return ((x1 + x2) // 2, (y1 + y2) // 2)
    return (img_w // 2, max(120, img_h // 4))


def _draw_arrow(draw: ImageDraw.ImageDraw, start: tuple[int, int], end: tuple[int, int], color: str = "#ff2020") -> None:
    draw.line([start, end], fill=color, width=8)
    ex, ey = end
    sx, sy = start
    dx = ex - sx
    dy = ey - sy
    length = max((dx * dx + dy * dy) ** 0.5, 1.0)
    ux = dx / length
    uy = dy / length
    left = (int(ex - 24 * ux - 12 * uy), int(ey - 24 * uy + 12 * ux))
    right = (int(ex - 24 * ux + 12 * uy), int(ey - 24 * uy - 12 * ux))
    draw.polygon([end, left, right], fill=color)


def _render_overlay_image(step: Step, out_path: Path) -> str:
    img = Image.open(step.screenshot_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    w, h = img.size
    tx, ty = _target_point(w, h, step)

    starts = [
        (40, 80),
        (w - 40, 80),
        (w // 2, 30),
    ]
    for start in starts:
        _draw_arrow(draw, start, (tx, ty))

    block_idx = _extract_block_index(step)
    label = f"Шаг {step.number}"
    if block_idx is not None:
        label += f" | Блок {block_idx}"
    draw.rectangle([20, h - 100, min(w - 20, 1000), h - 20], fill=(0, 0, 0))
    draw.text((40, h - 76), label, fill=(255, 255, 255))
    draw.text((40, h - 48), step.description[:120], fill=(255, 255, 255))

    img.save(out_path, format="JPEG", quality=90)
    return str(out_path)


def _tts_text(step: Step) -> str:
    block_idx = _extract_block_index(step)
    prefix = f"Нажмите на блок номер {block_idx}. " if block_idx is not None else "Выполните действие на этом экране. "
    return prefix + step.description


def _run(cmd: list[str]) -> None:
    proc = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(
            f"Command failed ({proc.returncode}): {' '.join(cmd)}\n"
            f"stderr: {(proc.stderr or '').strip()[-800:]}"
        )


async def export_video(guide: Guide, output_path: str) -> str:
    out_dir = Path(output_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    work_dir = out_dir / f"video_tmp_{_stamp()}"
    work_dir.mkdir(parents=True, exist_ok=True)
    video_path = out_dir / f"guide_{_stamp()}.mp4"

    segment_files: list[Path] = []

    for step in guide.steps:
        frame_path = work_dir / f"frame_{step.number:03d}.jpg"
        _render_overlay_image(step, frame_path)

        tts_aiff = work_dir / f"voice_{step.number:03d}.aiff"
        tts_wav = work_dir / f"voice_{step.number:03d}.wav"
        text = _tts_text(step)
        _run(["say", "-o", str(tts_aiff), text])
        _run(["ffmpeg", "-y", "-i", str(tts_aiff), str(tts_wav)])

        segment_path = work_dir / f"seg_{step.number:03d}.mp4"
        _run(
            [
                "ffmpeg",
                "-y",
                "-loop",
                "1",
                "-i",
                str(frame_path),
                "-i",
                str(tts_wav),
                "-vf",
                "scale=1280:-2",
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-crf",
                "28",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                "-threads",
                "1",
                "-shortest",
                str(segment_path),
            ]
        )
        segment_files.append(segment_path)

    concat_txt = work_dir / "concat.txt"
    concat_txt.write_text(
        "\n".join(f"file {shlex.quote(str(p))}" for p in segment_files),
        encoding="utf-8",
    )
    _run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_txt),
            "-c",
            "copy",
            str(video_path),
        ]
    )

    await asyncio.sleep(0)
    return str(video_path)
