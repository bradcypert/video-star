from pathlib import Path

from video_star.core.post_processor import process_response


def _make_raw(
    words=None,
    paragraphs=None,
    summary=None,
    topics=None,
    duration=120.0,
    chapters=None,
) -> dict:
    alt: dict = {
        "transcript": "Hello world.",
        "words": words or [],
    }
    if paragraphs is not None:
        alt["paragraphs"] = {"paragraphs": paragraphs}

    raw: dict = {
        "metadata": {"duration": duration},
        "results": {
            "channels": [{"alternatives": [alt]}],
        },
    }
    if summary is not None:
        raw["results"]["summary"] = {"short": summary}
    if topics is not None:
        raw["results"]["topics"] = {"segments": topics}
    if chapters is not None:
        raw["results"]["chapters"] = chapters
    return raw


VIDEO = Path("test.mp4")
AUDIO = Path("test.wav")


class TestProcessResponse:
    def test_basic_structure(self):
        raw = _make_raw(duration=60.0)
        result = process_response(raw, VIDEO, AUDIO)
        assert result.duration == 60.0
        assert result.video_path == VIDEO

    def test_words_parsed(self):
        words = [
            {"word": "hello", "start": 0.0, "end": 0.5, "confidence": 0.99},
            {"word": "world", "start": 0.5, "end": 1.0, "confidence": 0.98},
        ]
        result = process_response(_make_raw(words=words), VIDEO, AUDIO)
        assert len(result.words) == 2
        assert result.words[0].word == "hello"

    def test_summary_extracted(self):
        result = process_response(_make_raw(summary="Great video."), VIDEO, AUDIO)
        assert result.summary == "Great video."

    def test_topics_extracted(self):
        topics = [
            {"topics": [{"topic": "Python"}, {"topic": "AI"}]},
            {"topics": [{"topic": "Python"}]},  # duplicate should be deduped
        ]
        result = process_response(_make_raw(topics=topics), VIDEO, AUDIO)
        assert "Python" in result.topics
        assert "AI" in result.topics
        assert result.topics.count("Python") == 1

    def test_native_chapters_used(self):
        chapters = [
            {"start": 0.0, "summary": "Intro"},
            {"start": 60.0, "summary": "Main"},
        ]
        result = process_response(_make_raw(chapters=chapters, duration=120.0), VIDEO, AUDIO)
        assert len(result.chapters) == 2
        assert result.chapters[0].title == "Intro"

    def test_synthesized_chapters_fallback(self):
        paras = [
            {
                "start": 0.0,
                "end": 10.0,
                "sentences": [{"text": "Welcome to this video."}],
            }
        ]
        result = process_response(
            _make_raw(paragraphs=paras, duration=60.0), VIDEO, AUDIO
        )
        # Should have synthesized at least one chapter
        assert len(result.chapters) >= 1
        assert result.chapters[0].start == 0.0

    def test_missing_keys_safe(self):
        """process_response should not raise on an empty/partial response."""
        result = process_response({}, VIDEO, AUDIO)
        assert result.duration == 0.0
        assert result.words == []
        assert result.summary == ""
