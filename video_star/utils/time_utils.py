"""Timestamp formatting helpers."""

from __future__ import annotations


def seconds_to_srt(seconds: float) -> str:
    """Convert seconds to SRT timestamp format: HH:MM:SS,mmm"""
    total_ms = int(round(seconds * 1000))
    ms = total_ms % 1000
    total_s = total_ms // 1000
    s = total_s % 60
    total_m = total_s // 60
    m = total_m % 60
    h = total_m // 60
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def seconds_to_youtube(seconds: float) -> str:
    """Convert seconds to YouTube chapter timestamp format: M:SS or H:MM:SS"""
    total_s = int(seconds)
    s = total_s % 60
    total_m = total_s // 60
    m = total_m % 60
    h = total_m // 60
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def youtube_to_seconds(timestamp: str) -> float:
    """Parse a YouTube chapter timestamp (M:SS or H:MM:SS) into seconds."""
    parts = timestamp.strip().split(":")
    if len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    raise ValueError(f"Unrecognised timestamp format: {timestamp!r}")
