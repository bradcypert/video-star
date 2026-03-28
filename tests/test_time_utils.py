import pytest
from video_star.utils.time_utils import seconds_to_srt, seconds_to_youtube, youtube_to_seconds


class TestSecondsToSrt:
    def test_zero(self):
        assert seconds_to_srt(0) == "00:00:00,000"

    def test_sub_minute(self):
        assert seconds_to_srt(5.5) == "00:00:05,500"

    def test_minutes(self):
        assert seconds_to_srt(90.123) == "00:01:30,123"

    def test_hours(self):
        assert seconds_to_srt(3661.0) == "01:01:01,000"

    def test_rounding(self):
        # 1.9995 should round to ,000 of next second
        result = seconds_to_srt(1.9995)
        assert "," in result


class TestSecondsToYoutube:
    def test_zero(self):
        assert seconds_to_youtube(0) == "0:00"

    def test_sub_minute(self):
        assert seconds_to_youtube(45) == "0:45"

    def test_minutes(self):
        assert seconds_to_youtube(125) == "2:05"

    def test_hours(self):
        assert seconds_to_youtube(3661) == "1:01:01"

    def test_large(self):
        assert seconds_to_youtube(7200) == "2:00:00"


class TestYoutubeToSeconds:
    def test_mm_ss(self):
        assert youtube_to_seconds("2:05") == 125

    def test_h_mm_ss(self):
        assert youtube_to_seconds("1:01:01") == 3661

    def test_zero(self):
        assert youtube_to_seconds("0:00") == 0

    def test_invalid(self):
        with pytest.raises(ValueError):
            youtube_to_seconds("bad")
