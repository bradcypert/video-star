"""Write all pipeline outputs to disk."""

from __future__ import annotations

import json
from pathlib import Path

from video_star.models.pipeline_result import PipelineResult
from video_star.utils.file_utils import make_output_dir


def write_outputs(result: PipelineResult, base_output_dir: Path) -> dict[str, Path]:
    """Write all generated content to a timestamped output directory.

    Returns a dict mapping output type → file path.
    """
    out_dir = make_output_dir(base_output_dir, result.video_path)
    result.output_dir = out_dir

    written: dict[str, Path] = {}

    def _write(name: str, content: str, subdir: str = "") -> Path:
        target_dir = out_dir / subdir if subdir else out_dir
        target_dir.mkdir(parents=True, exist_ok=True)
        p = target_dir / name
        p.write_text(content, encoding="utf-8")
        return p

    if result.srt_content:
        written["srt"] = _write("transcript.srt", result.srt_content)

    if result.transcript_txt_content:
        written["transcript_txt"] = _write("transcript.txt", result.transcript_txt_content)

    if result.chapters_content:
        written["chapters"] = _write("chapters.txt", result.chapters_content)

    if result.description_content:
        written["description"] = _write("description.txt", result.description_content)

    if result.show_notes_content:
        written["show_notes"] = _write("show_notes.md", result.show_notes_content)

    # Raw Deepgram JSON for offline re-processing
    raw_path = out_dir / "raw_deepgram.json"
    raw_path.write_text(
        json.dumps(result.raw_deepgram_response, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    written["raw_json"] = raw_path

    return written
