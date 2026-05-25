from __future__ import annotations

import asyncio
import logging
import re
import shlex
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from PIL import Image, ImageDraw, ImageFont

try:
    from web_guide_recorder.agent.recorder import Guide, Step
except ModuleNotFoundError:
    from agent.recorder import Guide, Step


logger = logging.getLogger(__name__)


ARROW_COLOR = (255, 32, 32)
ARROW_OUTLINE = (255, 255, 255)
MARKER_OUTER = (255, 32, 32)
MARKER_INNER = (255, 255, 255)

VIDEO_W = 1280
VIDEO_H = 720
URL_CARD_BG = (18, 18, 28)
URL_CARD_LABEL = (255, 220, 80)
URL_CARD_URL = (255, 255, 255)
URL_CARD_HINT = (180, 180, 200)


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
    if not step.target_bbox:
        return None, None
    bbox = _scale_bbox(step.target_bbox, step.viewport_size, img_w, img_h)
    x1, y1, x2, y2 = bbox
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
    tx, ty = target
    margin = 60
    candidates = [
        (margin, margin),
        (img_w - margin, margin),
        (margin, img_h - margin),
        (img_w - margin, img_h - margin),
        (img_w // 2, margin),
    ]
    best = candidates[0]
    best_score = float("-inf")
    for cand in candidates:
        dx = tx - cand[0]
        dy = ty - cand[1]
        dist = (dx * dx + dy * dy) ** 0.5
        if dist < 180:
            continue
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
    draw.ellipse(
        [cx - radius, cy - radius, cx + radius, cy + radius],
        outline=MARKER_OUTER,
        width=6,
    )
    inner = 6
    draw.ellipse(
        [cx - inner, cy - inner, cx + inner, cy + inner],
        fill=MARKER_INNER,
        outline=MARKER_OUTER,
        width=2,
    )


def _draw_bbox(draw: ImageDraw.ImageDraw, bbox: tuple[int, int, int, int]) -> None:
    x1, y1, x2, y2 = bbox
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


def _render_url_card(start_url: str, out_path: Path) -> str:
    """Первый кадр видео: тёмный фон + URL по центру + подсказка снизу."""
    img = Image.new("RGB", (VIDEO_W, VIDEO_H), color=URL_CARD_BG)
    draw = ImageDraw.Draw(img)

    label_font = _load_font(34)
    url_font = _load_font(54)
    hint_font = _load_font(26)

    label = "Шаг 1 · Открытие сайта"
    label_w = label_font.getbbox(label)[2]
    draw.text(((VIDEO_W - label_w) // 2, 80), label, fill=URL_CARD_LABEL, font=label_font)

    url_lines = _wrap(start_url, url_font, VIDEO_W - 120)
    line_h = 70
    block_h = len(url_lines) * line_h
    y = (VIDEO_H - block_h) // 2 - 20
    for line in url_lines:
        w_line = url_font.getbbox(line)[2]
        draw.text(((VIDEO_W - w_line) // 2, y), line, fill=URL_CARD_URL, font=url_font)
        y += line_h

    hint = "Введите этот адрес в адресную строку браузера"
    hint_w = hint_font.getbbox(hint)[2]
    draw.text(((VIDEO_W - hint_w) // 2, VIDEO_H - 90), hint, fill=URL_CARD_HINT, font=hint_font)

    img.save(out_path, format="JPEG", quality=90)
    return str(out_path)


_LATIN_WORD_RE = re.compile(r"[A-Za-z]+(?:[A-Za-z0-9_-]*[A-Za-z])?")
_URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)
_QUOTE_RE = re.compile(r"[«»\"“”„‟❝❞''‘’`]")
_DASH_RE = re.compile(r"[—–−-]{1,}")
_SPECIAL_RE = re.compile(r"[\\|/<>{}\[\]_~^@#&*]")
_MD_RE = re.compile(r"[*`#]+")


def _clean_for_tts(text: str) -> str:
    """Умеренная чистка для русского TTS Milena.

    - убрать markdown, URL
    - заменить латинские слова на пробел (цифры оставить)
    - заменить служебные символы на пробел
    - длинные тире → запятая
    - кавычки → удалить (имена внутри читаются нормально)
    """
    if not text:
        return ""
    s = text
    s = _MD_RE.sub(" ", s)
    s = _URL_RE.sub(" ", s)
    s = _LATIN_WORD_RE.sub(" ", s)
    s = _SPECIAL_RE.sub(" ", s)
    s = _DASH_RE.sub(", ", s)
    s = _QUOTE_RE.sub("", s)
    s = re.sub(r"\s+([,.\!\?\:])", r"\1", s)
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"(,\s*){2,}", ", ", s)
    s = s.strip(" ,.")
    return s


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
                return f"{verb} {step.action_value}."
            if step.action_type == "go_to_url" and step.action_value:
                return f"{verb} {step.action_value}."
            return f"{verb}."
    block_idx = _extract_block_index(step)
    if block_idx is not None:
        return f"Нажмите на блок номер {block_idx}."
    return "Выполните действие на этом экране."


def _tts_text(step: Step) -> str:
    description = re.sub(r"^\[Блок[^\]]*\]\s*", "", (step.description or "").strip())
    cleaned = _clean_for_tts(description)
    if cleaned:
        return cleaned
    fallback = _clean_for_tts(_action_prefix(step))
    return fallback or "Выполните действие на этом экране"


def _url_intro_text(start_url: str) -> str:
    try:
        parsed = urlparse(start_url)
        host = parsed.netloc or parsed.path
    except Exception:  # noqa: BLE001
        host = start_url
    host = host.strip("/").strip()
    cleaned = _clean_for_tts(host)
    if not cleaned:
        return "Перейдите на сайт по указанному адресу"
    return f"Перейдите на сайт {cleaned}"


def _run(cmd: list[str]) -> None:
    proc = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(
            f"Command failed ({proc.returncode}): {' '.join(cmd)}\n"
            f"stderr: {(proc.stderr or '').strip()[-800:]}"
        )


def _tts_to_wav(text: str, aiff_path: Path, wav_path: Path, *, rate: int = 180) -> None:
    safe = text.strip() or "Шаг."
    _run(["say", "-v", "Milena", "-r", str(rate), "-o", str(aiff_path), safe])
    _run(["ffmpeg", "-y", "-i", str(aiff_path), str(wav_path)])


def _make_video_segment(frame_path: Path, audio_path: Path, out_path: Path) -> None:
    """Универсальный ffmpeg-сегмент: ровно 1280x720, h264+aac, yuv420p,
    setsar=1 — чтобы concat -c copy не сломал поток между разными источниками."""
    _run(
        [
            "ffmpeg",
            "-y",
            "-loop",
            "1",
            "-i",
            str(frame_path),
            "-i",
            str(audio_path),
            "-vf",
            f"scale={VIDEO_W}:{VIDEO_H}:force_original_aspect_ratio=decrease,"
            f"pad={VIDEO_W}:{VIDEO_H}:(ow-iw)/2:(oh-ih)/2:color=black,"
            "format=yuv420p,setsar=1",
            "-r",
            "30",
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
            "-b:a",
            "128k",
            "-ar",
            "44100",
            "-ac",
            "2",
            "-threads",
            "1",
            "-shortest",
            str(out_path),
        ]
    )


async def export_video(guide: Guide, output_path: str) -> str:
    out_dir = Path(output_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    work_dir = out_dir / f"video_tmp_{_stamp()}"
    work_dir.mkdir(parents=True, exist_ok=True)
    video_path = out_dir / f"guide_{_stamp()}.mp4"

    segment_files: list[Path] = []

    # Шаг 1 видео: URL-карточка вместо белого скриншота.
    try:
        url_frame = work_dir / "frame_000_url.jpg"
        _render_url_card(guide.start_url, url_frame)

        url_aiff = work_dir / "voice_000_url.aiff"
        url_wav = work_dir / "voice_000_url.wav"
        _tts_to_wav(_url_intro_text(guide.start_url), url_aiff, url_wav, rate=160)

        url_seg = work_dir / "seg_000_url.mp4"
        _make_video_segment(url_frame, url_wav, url_seg)
        segment_files.append(url_seg)
    except Exception as exc:  # noqa: BLE001
        logger.warning("URL-карточка не собрана: %s", exc)

    for step in guide.steps:
        try:
            frame_path = work_dir / f"frame_{step.number:03d}.jpg"
            _render_overlay_image(step, frame_path)

            tts_aiff = work_dir / f"voice_{step.number:03d}.aiff"
            tts_wav = work_dir / f"voice_{step.number:03d}.wav"
            _tts_to_wav(_tts_text(step), tts_aiff, tts_wav, rate=180)

            segment_path = work_dir / f"seg_{step.number:03d}.mp4"
            _make_video_segment(frame_path, tts_wav, segment_path)
            segment_files.append(segment_path)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Шаг %s: сегмент не собран (%s)", step.number, exc)

    if not segment_files:
        raise RuntimeError("Нет ни одного сегмента видео для склейки")

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
