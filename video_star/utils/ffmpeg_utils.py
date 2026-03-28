"""ffmpeg detection and helper utilities."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path


class FFmpegNotFoundError(Exception):
    pass


def find_ffmpeg(override: str = "") -> str:
    """Return the path to the ffmpeg binary.

    Search order:
    1. ``override`` (from Settings.FFMPEG_PATH)
    2. System PATH
    3. Bundled binary next to this package (assets/bin/ffmpeg or ffmpeg.exe)
    """
    if override:
        p = Path(override)
        if p.is_file():
            return str(p)
        raise FFmpegNotFoundError(f"ffmpeg not found at configured path: {override}")

    found = shutil.which("ffmpeg")
    if found:
        return found

    # Check for a bundled binary shipped alongside the package
    bundled = Path(__file__).parent.parent.parent / "assets" / "bin" / "ffmpeg"
    if bundled.exists():
        return str(bundled)
    bundled_win = bundled.with_suffix(".exe")
    if bundled_win.exists():
        return str(bundled_win)

    raise FFmpegNotFoundError(
        "ffmpeg was not found. Install it with:\n"
        "  Windows: winget install Gyan.FFmpeg\n"
        "  macOS:   brew install ffmpeg\n"
        "  Linux:   sudo apt install ffmpeg\n"
        "Or set FFMPEG_PATH in Settings."
    )


def find_ffprobe(ffmpeg_path: str) -> str:
    """Return the path to ffprobe, co-located with ffmpeg."""
    probe = shutil.which("ffprobe")
    if probe:
        return probe
    # Try same directory as ffmpeg
    p = Path(ffmpeg_path)
    candidate = p.parent / "ffprobe"
    if candidate.exists():
        return str(candidate)
    candidate_win = p.parent / "ffprobe.exe"
    if candidate_win.exists():
        return str(candidate_win)
    raise FFmpegNotFoundError("ffprobe not found alongside ffmpeg.")


def probe_duration(video_path: Path, ffprobe: str) -> float:
    """Return the duration of a media file in seconds using ffprobe."""
    cmd = [
        ffprobe,
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        str(video_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)
    return float(data["format"]["duration"])
