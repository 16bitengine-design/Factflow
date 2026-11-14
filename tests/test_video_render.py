"""Tests for the optional procedural video renderer."""
import pytest

from factflow.video_render import _caption_segments, _timestamp, validate_sample_spec


def valid_spec():
    return {
        "title": "Why Is the Sky Blue?",
        "narration": "Sunlight looks white but contains many colours. Air molecules scatter blue light.",
        "sources": [{"publisher": "NASA", "url": "https://spaceplace.nasa.gov/blue-sky/en/"}],
    }


def test_sample_spec_requires_title_narration_and_https_sources():
    validate_sample_spec(valid_spec())
    with pytest.raises(ValueError):
        validate_sample_spec({"title": "Test", "narration": "Too short.", "sources": []})
    with pytest.raises(ValueError):
        validate_sample_spec({**valid_spec(), "sources": [{"url": "http://example.com"}]})


def test_caption_segments_cover_duration_in_order():
    segments = _caption_segments("First sentence. Second sentence.", 12.0)
    assert segments[0][0] == 0
    assert segments[-1][1] == 12.0
    assert all(left[1] <= right[0] + 1e-9 for left, right in zip(segments, segments[1:]))


def test_srt_timestamp_formats_milliseconds():
    assert _timestamp(65.432) == "00:01:05,432"
