"""Generate Markdown show notes from a PipelineResult."""

from __future__ import annotations

from video_star.models.pipeline_result import PipelineResult
from video_star.utils.time_utils import seconds_to_youtube


def generate_show_notes(result: PipelineResult) -> str:
    """Return a Markdown show notes document."""
    lines: list[str] = []
    stem = result.video_path.stem

    lines.append(f"# Show Notes: {stem}\n")

    # Summary
    if result.summary:
        lines.append("## Summary\n")
        lines.append(result.summary)
        lines.append("")

    # Topics
    if result.topics:
        lines.append("## Topics Covered\n")
        for topic in result.topics:
            lines.append(f"- {topic}")
        lines.append("")

    # Chapters with excerpt
    if result.chapters:
        lines.append("## Chapters\n")
        # Build a map from chapter start → next chapter start
        chapter_ends = [c.start for c in result.chapters[1:]] + [result.duration]
        for chapter, end in zip(result.chapters, chapter_ends):
            ts = seconds_to_youtube(chapter.start)
            lines.append(f"### {ts} — {chapter.title}\n")

            # Find paragraphs that fall within this chapter
            excerpt_paras = [
                p for p in result.paragraphs
                if chapter.start <= p.start < end
            ][:2]  # First two paragraphs as a preview
            for para in excerpt_paras:
                lines.append(f"> {para.text}")
                lines.append("")

    return "\n".join(lines).strip()
