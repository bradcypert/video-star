from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class TranscriptWord:
    word: str
    start: float  # seconds
    end: float
    confidence: float
    speaker: int | None = None


@dataclass
class TranscriptParagraph:
    start: float
    end: float
    text: str
    speaker: int | None = None


@dataclass
class Chapter:
    start: float  # seconds
    title: str


@dataclass
class PipelineResult:
    video_path: Path
    audio_path: Path
    duration: float
    words: list[TranscriptWord]
    paragraphs: list[TranscriptParagraph]
    chapters: list[Chapter]
    summary: str
    topics: list[str]
    raw_deepgram_response: dict

    # Populated by generators / output_writer
    srt_content: str = ""
    transcript_txt_content: str = ""
    description_content: str = ""
    chapters_content: str = ""
    show_notes_content: str = ""
    thumbnail_paths: list[Path] = field(default_factory=list)
    output_dir: Path | None = None
