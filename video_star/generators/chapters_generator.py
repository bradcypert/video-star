"""Generate YouTube chapter timestamp list from a PipelineResult."""

from __future__ import annotations

from video_star.models.pipeline_result import PipelineResult
from video_star.utils.time_utils import seconds_to_youtube


def generate_chapters(result: PipelineResult) -> str:
    """Return a newline-separated string of YouTube chapter timestamps.

    Format:
        0:00 Intro
        1:23 Some Topic Title
        …
    """
    chapters = result.chapters
    if not chapters:
        return ""

    lines: list[str] = []
    for chapter in chapters:
        ts = seconds_to_youtube(chapter.start)
        lines.append(f"{ts} {chapter.title}")

    return "\n".join(lines)
