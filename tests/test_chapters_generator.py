from pathlib import Path

from video_star.generators.chapters_generator import generate_chapters
from video_star.models.pipeline_result import Chapter, PipelineResult


def _minimal_result(chapters: list[Chapter]) -> PipelineResult:
    return PipelineResult(
        video_path=Path("test.mp4"),
        audio_path=Path("test.wav"),
        duration=600.0,
        words=[],
        paragraphs=[],
        chapters=chapters,
        summary="",
        topics=[],
        raw_deepgram_response={},
    )


class TestGenerateChapters:
    def test_basic(self):
        result = _minimal_result([
            Chapter(start=0.0, title="Intro"),
            Chapter(start=60.0, title="Main Topic"),
            Chapter(start=300.0, title="Wrap Up"),
        ])
        output = generate_chapters(result)
        lines = output.strip().split("\n")
        assert len(lines) == 3
        assert lines[0].startswith("0:00")
        assert "Intro" in lines[0]
        assert lines[1].startswith("1:00")

    def test_empty_chapters(self):
        result = _minimal_result([])
        assert generate_chapters(result) == ""

    def test_hour_long_video(self):
        result = _minimal_result([
            Chapter(start=0.0, title="Intro"),
            Chapter(start=3600.0, title="Hour Mark"),
        ])
        output = generate_chapters(result)
        assert "1:00:00" in output
