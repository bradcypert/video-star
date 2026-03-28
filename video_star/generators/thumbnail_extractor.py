"""Extract thumbnail candidate frames from a video file using ffmpeg."""

from __future__ import annotations

import subprocess
from pathlib import Path

from video_star.models.pipeline_result import Chapter
from video_star.utils.ffmpeg_utils import find_ffmpeg, find_ffprobe, probe_duration


def extract_thumbnail_candidates(
    video_path: Path,
    chapters: list[Chapter],
    count: int,
    output_dir: Path,
    ffmpeg_path: str = "",
    use_overlay: bool = False,
) -> list[Path]:
    """Extract *count* frame images from *video_path*.

    Frames are extracted at:
      1. Each chapter boundary (up to ``count`` chapters)
      2. Percentage-of-duration marks (10 %, 30 %, 50 %) to fill remaining slots

    If *use_overlay* is True and Pillow is available, a semi-transparent bar
    with the chapter title is drawn on chapter-boundary frames.

    Returns a list of paths to the extracted JPEG files.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    ffmpeg = find_ffmpeg(ffmpeg_path)

    try:
        ffprobe = find_ffprobe(ffmpeg)
        duration = probe_duration(video_path, ffprobe)
    except Exception:
        duration = 0.0

    # Build list of (timestamp_seconds, label) to extract
    timestamps: list[tuple[float, str]] = []

    for chapter in chapters[:count]:
        timestamps.append((chapter.start, chapter.title))

    # Fill remaining slots with percentage marks
    pct_marks = [0.10, 0.30, 0.50, 0.70, 0.90]
    for pct in pct_marks:
        if len(timestamps) >= count:
            break
        if duration > 0:
            t = duration * pct
            timestamps.append((t, f"{int(pct * 100)}pct"))

    extracted: list[Path] = []
    for idx, (ts, label) in enumerate(timestamps):
        safe_label = "".join(c if c.isalnum() or c in "-_" else "_" for c in label)
        out_path = output_dir / f"thumb_{idx:02d}_{safe_label}.jpg"
        success = _extract_frame(ffmpeg, video_path, ts, out_path)
        if success:
            if use_overlay:
                _apply_overlay(out_path, label)
            extracted.append(out_path)

    return extracted


def _extract_frame(ffmpeg: str, video_path: Path, ts: float, out_path: Path) -> bool:
    cmd = [
        ffmpeg,
        "-y",
        "-ss", str(ts),
        "-i", str(video_path),
        "-frames:v", "1",
        "-q:v", "2",
        str(out_path),
    ]
    result = subprocess.run(cmd, capture_output=True)
    return result.returncode == 0 and out_path.exists()


def _apply_overlay(image_path: Path, label: str) -> None:
    """Draw a text bar at the bottom of the image using Pillow."""
    try:
        from PIL import Image, ImageDraw, ImageFont

        img = Image.open(image_path).convert("RGB")
        w, h = img.size
        bar_h = max(40, h // 10)

        overlay = Image.new("RGBA", (w, bar_h), (0, 0, 0, 160))
        img_rgba = img.convert("RGBA")
        img_rgba.paste(overlay, (0, h - bar_h), overlay)
        img_rgb = img_rgba.convert("RGB")

        draw = ImageDraw.Draw(img_rgb)
        try:
            font = ImageFont.truetype("arial.ttf", size=bar_h // 2)
        except OSError:
            font = ImageFont.load_default()

        text_y = h - bar_h + (bar_h - bar_h // 2) // 2
        draw.text((10, text_y), label, fill=(255, 255, 255), font=font)
        img_rgb.save(image_path, "JPEG", quality=92)
    except ImportError:
        pass  # Pillow not available — skip overlay silently
    except Exception:
        pass  # Non-fatal
