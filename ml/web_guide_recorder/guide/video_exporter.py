from __future__ import annotations

import asyncio
import re
import shlex
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

try:
    from web_guide_recorder.agent.recorder import Guide, Step
except ModuleNotFoundError:
    from agent.recorder import Guide, Step


ARROW_COLOR = (255, 32, 32)
ARROW_OUTLINE = (255, 255, 255)
MARKER_OUTER = (255, 32, 32)
MARKER_INNER = (255, 255, 255)


def _stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _extract_block_index(step: Step) -> Optional[int]:
    if step.target_index is not None:
        return step.target_index
    m = re.search(r"\[Блок\s+(\d+)\]", step.description)
    if m:
        return int(m.group(1))
    return None


def _scale_bbox(
    bbox: tuple[int, int, int, int],
    viewport: Optional[tuple[int, int]],
    img_w: int,
    img_h: int,
) -> tuple[int, int, int, int]:
    """bbox приходит в CSS-пикселях viewport'а, скриншот может быть в физических
    пикселях (DPR != 1). Масштабируем линейно по ширине и высоте отдельно."""
    if not viewport:
        return bbox
    vw, vh = viewport
    if vw <= 0 or vh <= 0:
        return bbox
    sx = img_w / vw
    sy = img_h / vh
    x1, y1, x2, y2 = bbox
    return (int(x1 * sx), int(y1 * sy), int(x2 * sx), int(y2 * sy))


def _target_point(
    img_w: int, img_h: int, step: Step
) -> tuple[Optional[tuple[int, int]], Optional[tuple[int, int, int, int]]]:
    """Возвращает (center, scaled_bbox). Если bbox нет — center=None,
    стрелка тогда не рисуется (вместо мисса в верхнюю четверть экрана)."""
    if not step.target_bbox:
        return None, None
    bbox = _scale_bbox(step.target_bbox, step.viewport_size, img_w, img_h)
    x1, y1, x2, y2 = bbox
    # Зажимаем bbox в пределы изображения — на случай чуть некорректных координат.
    x1 = max(0, min(x1, img_w - 1))
    x2 = max(0, min(x2, img_w - 1))
    y1 = max(0, min(y1, img_h - 1))
    y2 = max(0, min(y2, img_h - 1))
    if x2 <= x1 or y2 <= y1:
        return None, None
    cx = (x1 + x2) // 2
    cy = (y1 + y2) // 2
    return (cx, cy), (x1, y1, x2, y2)


def _arrow_start(img_w: int, img_h: int, target: tuple[int, int]) -> tuple[int, int]:
    """Выбираем стартовую точку стрелки с ближайшего «свободного» края экрана,
    чтобы стрелка не пересекала важный контент."""
    tx, ty = target
    margin = 60
    candidates = [
        (margin, margin),                          # сверху-слева
        (img_w - margin, margin),                  # сверху-справа
        (margin, img_h - margin),                  # снизу-слева
        (img_w - margin, img_h - margin),          # снизу-справа
        (img_w // 2, margin),                      # сверху по центру
    ]
    # Берём самый близкий по диагонали, но с минимальной длиной (≥180px), иначе
    # стрелка будет почти точкой.
    best = candidates[0]
    best_score = float("-inf")
    for cand in candidates:
        dx = tx - cand[0]
        dy = ty - cand[1]
        dist = (dx * dx + dy * dy) ** 0.5
        if dist < 180:
            continue
        # Чем ближе — тем лучше (берём максимум отрицательного расстояния).
        score = -dist
        if score > best_score:
            best_score = score
            best = cand
    return best


def _draw_arrow(
    draw: ImageDraw.ImageDraw,
    start: tuple[int, int],
    end: tuple[int, int],
) -> None:
    # Белая обводка под красной линией — стрелка читается на любом фоне.
    draw.line([start, end], fill=ARROW_OUTLINE, width=14)
    draw.line([start, end], fill=ARROW_COLOR, width=8)

    ex, ey = end
    sx, sy = start
    dx = ex - sx
    dy = ey - sy
    length = max((dx * dx + dy * dy) ** 0.5, 1.0)
    ux = dx / length
    uy = dy / length
    head = 28
    side = 14
    left = (int(ex - head * ux - side * uy), int(ey - head * uy + side * ux))
    right = (int(ex - head * ux + side * uy), int(ey - head * uy - side * ux))
    draw.polygon([end, left, right], fill=ARROW_COLOR, outline=ARROW_OUTLINE)


def _draw_marker(draw: ImageDraw.ImageDraw, center: tuple[int, int], radius: int = 26) -> None:
    cx, cy = center
    # Внешнее красное кольцо.
    draw.ellipse(
        [cx - radius, cy - radius, cx + radius, cy + radius],
        outline=MARKER_OUTER,
        width=6,
    )
    # Внутреннее маленькое белое — точка прицеливания.
    inner = 6
    draw.ellipse(
        [cx - inner, cy - inner, cx + inner, cy + inner],
        fill=MARKER_INNER,
        outline=MARKER_OUTER,
        width=2,
    )


def _draw_bbox(draw: ImageDraw.ImageDraw, bbox: tuple[int, int, int, int]) -> None:
    x1, y1, x2, y2 = bbox
    # Полупрозрачную заливку через PIL не сделать в режиме RGB без alpha-композита,
    # поэтому рисуем рамку 4px красная + 2px белый внутри для контраста.
    draw.rectangle([x1, y1, x2, y2], outline=ARROW_OUTLINE, width=6)
    draw.rectangle([x1 + 3, y1 + 3, x2 - 3, y2 - 3], outline=ARROW_COLOR, width=4)


def _load_font(size: int) -> ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def _wrap(text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    cur = ""
    for w in words:
        candidate = f"{cur} {w}".strip()
        bbox = font.getbbox(candidate)
        if bbox[2] - bbox[0] <= max_width or not cur:
            cur = candidate
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def _render_overlay_image(step: Step, out_path: Path) -> str:
    img = Image.open(step.screenshot_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    w, h = img.size

    center, scaled_bbox = _target_point(w, h, step)
    if center is not None and scaled_bbox is not None:
        _draw_bbox(draw, scaled_bbox)
        start = _arrow_start(w, h, center)
        _draw_arrow(draw, start, center)
        _draw_marker(draw, center)

    block_idx = _extract_block_index(step)
    title = f"Шаг {step.number}"
    if block_idx is not None:
        title += f" · Блок {block_idx}"
    if step.action_type:
        title += f" · {step.action_type}"

    title_font = _load_font(28)
    body_font = _load_font(22)

    caption = step.description
    # Срезаем префикс "[Блок N]" — он уже в title.
    caption = re.sub(r"^\[Блок[^\]]*\]\s*", "", caption.strip())

    max_text_width = w - 80
    body_lines = _wrap(caption, body_font, max_text_width)[:4]
    line_h = 28
    panel_h = 28 + 8 + len(body_lines) * line_h + 16
    panel_top = h - panel_h - 20

    draw.rectangle([20, panel_top, w - 20, h - 20], fill=(0, 0, 0))
    draw.rectangle([20, panel_top, w - 20, h - 20], outline=ARROW_COLOR, width=3)
    draw.text((40, panel_top + 10), title, fill=(255, 220, 80), font=title_font)
    y = panel_top + 10 + 28 + 8
    for line in body_lines:
        draw.text((40, y), line, fill=(255, 255, 255), font=body_font)
        y += line_h

    img.save(out_path, format="JPEG", quality=90)
    return str(out_path)


_ACTION_VERB = {
    "click_element": "Нажмите",
    "click": "Нажмите",
    "click_element_by_index": "Нажмите",
    "input_text": "Введите текст",
    "type": "Введите текст",
    "scroll_down": "Прокрутите страницу вниз",
    "scroll_up": "Прокрутите страницу вверх",
    "scroll": "Прокрутите страницу",
    "go_to_url": "Перейдите по адресу",
    "open_tab": "Откройте новую вкладку",
    "switch_tab": "Переключитесь на вкладку",
    "extract_content": "Изучите содержимое страницы",
    "wait": "Подождите загрузки страницы",
    "send_keys": "Нажмите клавиши на клавиатуре",
    "done": "Цель достигнута",
}


def _action_prefix(step: Step) -> str:
    if step.action_type:
        verb = _ACTION_VERB.get(step.action_type)
        if verb:
            if step.action_type in ("input_text", "type") and step.action_value:
                return f"{verb} «{step.action_value}»."
            if step.action_type == "go_to_url" and step.action_value:
                return f"{verb} {step.action_value}."
            return f"{verb}."
    block_idx = _extract_block_index(step)
    if block_idx is not None:
        return f"Нажмите на блок номер {block_idx}."
    return "Выполните действие на этом экране."


def _tts_text(step: Step) -> str:
    # Убираем префикс [Блок N] из описания — он не для озвучки.
    description = re.sub(r"^\[Блок[^\]]*\]\s*", "", step.description.strip())
    prefix = _action_prefix(step)
    if description:
        return f"{prefix} {description}"
    return prefix


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
        _run(["say", "-v", "Milena", "-r", "180", "-o", str(tts_aiff), text])
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
