"""Generate SRT subtitles and plain-text transcript from a PipelineResult."""

from __future__ import annotations

import textwrap

from video_star.models.pipeline_result import PipelineResult, TranscriptParagraph
from video_star.utils.time_utils import seconds_to_srt

_MAX_LINE_CHARS = 84
_MAX_LINES = 2


def generate_srt(result: PipelineResult) -> str:
    """Return SRT-formatted subtitle content."""
    if not result.paragraphs:
        return ""

    blocks: list[str] = []
    index = 1

    for para in result.paragraphs:
        for start, end, text in _split_paragraph(para):
            ts_start = seconds_to_srt(start)
            ts_end = seconds_to_srt(end)
            blocks.append(f"{index}\n{ts_start} --> {ts_end}\n{text}\n")
            index += 1

    return "\n".join(blocks)


def generate_transcript_txt(result: PipelineResult) -> str:
    """Return plain text transcript, with optional speaker labels."""
    if not result.paragraphs:
        return ""

    lines: list[str] = []
    has_speakers = any(p.speaker is not None for p in result.paragraphs)

    for para in result.paragraphs:
        if has_speakers and para.speaker is not None:
            prefix = f"[Speaker {para.speaker}] "
        else:
            prefix = ""
        lines.append(f"{prefix}{para.text}")
        lines.append("")  # blank line between paragraphs

    return "\n".join(lines).strip()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _split_paragraph(
    para: TranscriptParagraph,
) -> list[tuple[float, float, str]]:
    """Split a paragraph into subtitle-sized (start, end, text) chunks.

    Each chunk fits within _MAX_LINE_CHARS × _MAX_LINES characters.
    Timestamps are interpolated linearly across chunks.
    """
    text = para.text.strip()
    if not text:
        return []

    max_chars = _MAX_LINE_CHARS * _MAX_LINES
    duration = para.end - para.start

    # Fast path: the whole paragraph fits in one block.
    if len(text) <= max_chars:
        return [(para.start, para.end, _wrap(text))]

    # Split at word boundaries without exceeding max_chars per chunk.
    raw_chunks: list[str] = []
    current: list[str] = []
    for word in text.split():
        candidate = " ".join(current + [word])
        if len(candidate) > max_chars and current:
            raw_chunks.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        raw_chunks.append(" ".join(current))

    if not raw_chunks:
        return [(para.start, para.end, _wrap(text))]

    # Distribute timestamps evenly across chunks.
    n = len(raw_chunks)
    return [
        (
            para.start + (i / n) * duration,
            para.start + ((i + 1) / n) * duration,
            _wrap(chunk),
        )
        for i, chunk in enumerate(raw_chunks)
    ]


def _wrap(text: str) -> str:
    """Wrap text to _MAX_LINES lines of _MAX_LINE_CHARS each."""
    lines = textwrap.wrap(text, width=_MAX_LINE_CHARS)
    return "\n".join(lines[:_MAX_LINES])
