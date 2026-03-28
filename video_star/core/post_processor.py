"""Convert a raw Deepgram response dict into a PipelineResult."""

from __future__ import annotations

import textwrap
from pathlib import Path

from video_star.models.pipeline_result import (
    Chapter,
    PipelineResult,
    TranscriptParagraph,
    TranscriptWord,
)


def process_response(raw: dict, video_path: Path, audio_path: Path) -> PipelineResult:
    results = raw.get("results", {})
    metadata = raw.get("metadata", {})

    duration: float = float(metadata.get("duration", 0.0))

    # --- Words ---
    words: list[TranscriptWord] = []
    try:
        raw_words = (
            results["channels"][0]["alternatives"][0].get("words", [])
        )
        for w in raw_words:
            words.append(
                TranscriptWord(
                    word=w.get("word", ""),
                    start=float(w.get("start", 0)),
                    end=float(w.get("end", 0)),
                    confidence=float(w.get("confidence", 0)),
                    speaker=w.get("speaker"),
                )
            )
    except (KeyError, IndexError):
        pass

    # --- Paragraphs ---
    paragraphs: list[TranscriptParagraph] = []
    try:
        raw_paras = (
            results["channels"][0]["alternatives"][0]
            ["paragraphs"]["paragraphs"]
        )
        for p in raw_paras:
            sentences = p.get("sentences", [])
            text = " ".join(s.get("text", "") for s in sentences).strip()
            paragraphs.append(
                TranscriptParagraph(
                    start=float(p.get("start", 0)),
                    end=float(p.get("end", 0)),
                    text=text,
                    speaker=p.get("speaker"),
                )
            )
    except (KeyError, IndexError):
        pass

    # --- Summary ---
    summary = ""
    try:
        summary = results["summary"]["short"]
    except (KeyError, TypeError):
        pass

    # --- Topics ---
    topics: list[str] = []
    try:
        segments = results["topics"]["segments"]
        seen: set[str] = set()
        for seg in segments:
            for topic_obj in seg.get("topics", []):
                t = topic_obj.get("topic", "").strip()
                if t and t not in seen:
                    topics.append(t)
                    seen.add(t)
    except (KeyError, TypeError):
        pass

    # --- Chapters ---
    chapters: list[Chapter] = _extract_or_synthesize_chapters(results, paragraphs, duration)

    return PipelineResult(
        video_path=video_path,
        audio_path=audio_path,
        duration=duration,
        words=words,
        paragraphs=paragraphs,
        chapters=chapters,
        summary=summary,
        topics=topics,
        raw_deepgram_response=raw,
    )


def _extract_or_synthesize_chapters(
    results: dict,
    paragraphs: list[TranscriptParagraph],
    duration: float,
) -> list[Chapter]:
    # Try Deepgram-native chapters first
    try:
        raw_chapters = results["chapters"]
        if raw_chapters:
            return [
                Chapter(
                    start=float(c.get("start", 0)),
                    title=c.get("summary", c.get("headline", "Chapter")),
                )
                for c in raw_chapters
            ]
    except (KeyError, TypeError):
        pass

    # Synthesize from paragraphs
    return _synthesize_chapters(paragraphs, duration)


def _synthesize_chapters(
    paragraphs: list[TranscriptParagraph],
    duration: float,
    target_chunk_seconds: float = 180.0,  # aim for ~3-minute chapters
) -> list[Chapter]:
    """Group paragraphs into chapters of roughly *target_chunk_seconds* each."""
    if not paragraphs:
        return [Chapter(start=0.0, title="Intro")]

    chapters: list[Chapter] = []
    chunk_start = paragraphs[0].start
    chunk_texts: list[str] = []

    def _flush(start: float, texts: list[str]) -> None:
        combined = " ".join(texts)
        # Use the first sentence as the chapter title (≤ 60 chars)
        first_sentence = combined.split(".")[0].strip()
        title = textwrap.shorten(first_sentence, width=60, placeholder="…") or "Chapter"
        chapters.append(Chapter(start=start, title=title))

    for para in paragraphs:
        chunk_texts.append(para.text)
        elapsed = para.end - chunk_start
        if elapsed >= target_chunk_seconds:
            _flush(chunk_start, chunk_texts)
            chunk_start = para.end
            chunk_texts = []

    if chunk_texts:
        _flush(chunk_start, chunk_texts)

    # Ensure first chapter starts at 0:00
    if chapters and chapters[0].start > 0:
        chapters.insert(0, Chapter(start=0.0, title="Intro"))

    # YouTube requires at least 3 chapters
    while len(chapters) < 3:
        chapters.append(
            Chapter(start=duration * (len(chapters) / 3), title="Chapter")
        )

    return chapters
