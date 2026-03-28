"""Pipeline orchestration: ties all stages together."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from video_star.config import Settings
from video_star.core.audio_extractor import extract_audio
from video_star.core.output_writer import write_outputs
from video_star.core.post_processor import process_response
from video_star.core.transcriber import transcribe
from video_star.generators.chapters_generator import generate_chapters
from video_star.generators.description_generator import generate_description
from video_star.generators.show_notes_generator import generate_show_notes
from video_star.generators.srt_generator import generate_srt, generate_transcript_txt
from video_star.generators.thumbnail_extractor import extract_thumbnail_candidates
from video_star.models.pipeline_result import PipelineResult


@dataclass
class PipelineCallbacks:
    on_stage: Callable[[str, float], None] = field(default=lambda s, p: None)
    on_log: Callable[[str], None] = field(default=lambda msg: None)
    on_complete: Callable[[PipelineResult, dict], None] = field(
        default=lambda r, w: None
    )
    on_error: Callable[[Exception], None] = field(default=lambda e: None)


class PipelineRunner:
    def __init__(self, settings: Settings, callbacks: PipelineCallbacks) -> None:
        self._settings = settings
        self._cb = callbacks

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run_async(self, video_path: Path) -> threading.Thread:
        """Start the pipeline in a background thread and return the thread."""
        t = threading.Thread(target=self._run, args=(video_path,), daemon=True)
        t.start()
        return t

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _run(self, video_path: Path) -> None:
        cb = self._cb
        s = self._settings
        audio_path: Path | None = None

        try:
            s.validate()

            # Stage 1 – Audio extraction
            cb.on_stage("Extracting audio…", 0.05)
            cb.on_log("Starting audio extraction with ffmpeg…")

            def _audio_progress(pct: float) -> None:
                cb.on_stage("Extracting audio…", 0.05 + pct * 0.10)

            audio_path = extract_audio(
                video_path,
                ffmpeg_path=s.FFMPEG_PATH,
                on_progress=_audio_progress,
            )
            cb.on_log(f"Audio extracted to temporary file: {audio_path.name}")

            # Stage 2 – Transcription
            cb.on_stage("Transcribing (this may take 1–3 min)…", 0.15)
            raw = transcribe(
                audio_path,
                api_key=s.DEEPGRAM_API_KEY,
                on_log=cb.on_log,
            )
            cb.on_stage("Transcription complete.", 0.55)

            # Stage 3 – Post-processing
            cb.on_stage("Processing transcript…", 0.60)
            cb.on_log("Parsing Deepgram response…")
            result = process_response(raw, video_path, audio_path)
            cb.on_log(
                f"Parsed {len(result.words)} words, "
                f"{len(result.paragraphs)} paragraphs, "
                f"{len(result.chapters)} chapters."
            )

            # Stage 4 – Generate outputs
            cb.on_stage("Generating outputs…", 0.70)

            cb.on_log("Generating SRT transcript…")
            result.srt_content = generate_srt(result)
            result.transcript_txt_content = generate_transcript_txt(result)

            cb.on_log("Generating chapter timestamps…")
            result.chapters_content = generate_chapters(result)

            cb.on_log("Generating description…")
            result.description_content = generate_description(result, s)

            cb.on_log("Generating show notes…")
            result.show_notes_content = generate_show_notes(result)

            cb.on_stage("Extracting thumbnail candidates…", 0.82)
            cb.on_log("Extracting thumbnail frames…")
            result.thumbnail_paths = extract_thumbnail_candidates(
                video_path=video_path,
                chapters=result.chapters,
                count=s.THUMBNAIL_COUNT,
                output_dir=s.OUTPUT_DIR / "_thumbnails_tmp",
                ffmpeg_path=s.FFMPEG_PATH,
                use_overlay=s.USE_THUMBNAIL_OVERLAY,
            )
            cb.on_log(f"Extracted {len(result.thumbnail_paths)} thumbnail candidates.")

            # Stage 5 – Write files
            cb.on_stage("Writing output files…", 0.90)
            cb.on_log(f"Writing outputs to {s.OUTPUT_DIR}…")
            written = write_outputs(result, s.OUTPUT_DIR)
            for key, path in written.items():
                cb.on_log(f"  ✓ {key}: {path.name}")

            # Move thumbnails into the output folder
            if result.thumbnail_paths and result.output_dir:
                thumb_dir = result.output_dir / "thumbnails"
                thumb_dir.mkdir(exist_ok=True)
                moved: list[Path] = []
                for tp in result.thumbnail_paths:
                    dest = thumb_dir / tp.name
                    try:
                        tp.rename(dest)
                        moved.append(dest)
                    except Exception:
                        moved.append(tp)
                result.thumbnail_paths = moved

            cb.on_stage("Done!", 1.0)
            cb.on_complete(result, written)

        except Exception as exc:
            cb.on_error(exc)
        finally:
            if audio_path and audio_path.exists():
                try:
                    audio_path.unlink()
                except Exception:
                    pass
