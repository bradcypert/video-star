from pathlib import Path

from video_star.generators.srt_generator import generate_srt, generate_transcript_txt
from video_star.models.pipeline_result import PipelineResult, TranscriptParagraph


def _result_with_paragraphs(paragraphs: list[TranscriptParagraph]) -> PipelineResult:
    return PipelineResult(
        video_path=Path("test.mp4"),
        audio_path=Path("test.wav"),
        duration=120.0,
        words=[],
        paragraphs=paragraphs,
        chapters=[],
        summary="",
        topics=[],
        raw_deepgram_response={},
    )


class TestGenerateSrt:
    def test_basic_output(self):
        result = _result_with_paragraphs([
            TranscriptParagraph(start=0.0, end=5.0, text="Hello world."),
            TranscriptParagraph(start=5.0, end=10.0, text="This is a test."),
        ])
        srt = generate_srt(result)
        assert "1\n" in srt
        assert "00:00:00,000 --> 00:00:05,000" in srt
        assert "Hello world." in srt

    def test_empty_paragraphs(self):
        result = _result_with_paragraphs([])
        assert generate_srt(result) == ""

    def test_sequential_indices(self):
        paras = [
            TranscriptParagraph(start=float(i), end=float(i + 1), text=f"Sentence {i}.")
            for i in range(5)
        ]
        result = _result_with_paragraphs(paras)
        srt = generate_srt(result)
        # All 5 blocks should be present
        for i in range(1, 6):
            assert f"{i}\n" in srt


class TestGenerateTranscriptTxt:
    def test_no_speakers(self):
        result = _result_with_paragraphs([
            TranscriptParagraph(start=0.0, end=5.0, text="Hello world."),
        ])
        txt = generate_transcript_txt(result)
        assert "Hello world." in txt
        assert "Speaker" not in txt

    def test_with_speakers(self):
        result = _result_with_paragraphs([
            TranscriptParagraph(start=0.0, end=5.0, text="Hello.", speaker=0),
            TranscriptParagraph(start=5.0, end=10.0, text="Hi there.", speaker=1),
        ])
        txt = generate_transcript_txt(result)
        assert "[Speaker 0]" in txt
        assert "[Speaker 1]" in txt
