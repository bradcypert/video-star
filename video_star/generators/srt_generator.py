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
        # Wrap long paragraphs into subtitle-sized chunks
        chunks = _split_paragraph(para)
        for start, end, text in chunks:
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
    """Split a long paragraph into ≤ _MAX_LINE_CHARS × _MAX_LINES chunks.

    Returns a list of (start_sec, end_sec, text) tuples.
    """
    text = para.text.strip()
    if not text:
        return []

    duration = para.end - para.start
    words = text.split()
    max_chars = _MAX_LINE_CHARS * _MAX_LINES

    if len(text) <= max_chars:
        return [(para.start, para.end, _wrap(text))]

    # Split into word-boundary chunks
    chunks: list[tuple[float, float, str]] = []
    current_words: list[str] = []
    total_words = len(words)

    def _flush(w: list[str], chunk_index: int, total_chunks: int) -> None:
        chunk_text = " ".join(w)
        chunk_start = para.start + (chunk_index / total_chunks) * duration
        chunk_end = para.start + ((chunk_index + 1) / total_chunks) * duration
        chunks.append((chunk_start, chunk_end, _wrap(chunk_text)))

    chunk_size = max(1, max_chars // (sum(len(w) + 1 for w in words) // max(1, len(words))))
    chunk_size = max(8, chunk_size)  # at least 8 words per chunk
    total_chunks = max(1, (total_words + chunk_size - 1) // chunk_size)

    for i, word in enumerate(words):
        current_words.append(word)
        if len(" ".join(current_words)) >= max_chars:
            chunk_idx = len(chunks)
            _flush(current_words, chunk_idx, total_chunks)
            current_words = []

    if current_words:
        _flush(current_words, len(chunks), total_chunks)

    return chunks if chunks else [(para.start, para.end, _wrap(text[:max_chars]))]


def _wrap(text: str) -> str:
    """Wrap text to two lines of _MAX_LINE_CHARS each."""
    lines = textwrap.wrap(text, width=_MAX_LINE_CHARS)
    return "\n".join(lines[:_MAX_LINES])
