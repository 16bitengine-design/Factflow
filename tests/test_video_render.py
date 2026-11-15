"""Tests for the optional procedural video renderer."""
import pytest

from factflow.video_render import _caption_segments, _scene_state, _timestamp, validate_sample_spec


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



def test_scene_state_advances_through_four_distinct_scenes():
    assert [_scene_state(value, 40)[0] for value in (0, 10, 20, 30)] == [0, 1, 2, 3]
    assert 0.0 <= _scene_state(15, 40)[1] <= 1.0


def test_holographic_storyboard_contains_required_visual_scenes():
    pytest.importorskip("PIL")
    from factflow.holographic_scenes import draw_holographic_scene
    from PIL import Image, ImageDraw, ImageFont

    image = Image.new("RGBA", (720, 1280))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    fonts = {name: font for name in ("label", "tiny", "heading", "small")}
    scenes = [draw_holographic_scene(draw, index, 0.5, 2.0, fonts) for index in range(4)]
    assert [item[0] for item in scenes] == [
        "SUNLIGHT ENTERS THE ATMOSPHERE",
        "MOLECULES REDIRECT THE LIGHT",
        "LIGHT ENTERS YOUR EYE",
        "WHY THE SKY LOOKS BLUE",
    ]


def test_sunlight_scene_renders_white_beam_and_all_spectrum_colours():
    pytest.importorskip("PIL")
    from factflow.holographic_scenes import SPECTRUM, draw_holographic_scene
    from PIL import Image, ImageDraw, ImageFont

    image = Image.new("RGBA", (720, 1280), (1, 7, 19, 255))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    fonts = {name: font for name in ("label", "tiny", "heading", "small")}
    draw_holographic_scene(draw, 0, 0.75, 2.0, fonts)
    pixels = list(image.getdata())

    # Exact opaque core strokes ensure every visible wavelength is actually drawn.
    for colour in SPECTRUM:
        assert pixels.count(colour) > 0
    # The incoming solar beam has a near-white core, distinct from the spectrum.
    assert any(r > 240 and g > 240 and b > 220 for r, g, b, _ in pixels)


def test_scene_callout_text_is_fitted_inside_panel():
    pytest.importorskip("PIL")
    from PIL import Image, ImageDraw, ImageFont
    from factflow.video_render import _fit_font

    image = Image.new("RGB", (720, 1280))
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
    headline = "SUNLIGHT ENTERS THE ATMOSPHERE"
    fitted = _fit_font(draw, headline, font, 532)
    assert draw.textbbox((0, 0), headline, font=fitted)[2] <= 532


def test_sunlight_spectrum_uses_a_legend_not_a_prism_fan():
    pytest.importorskip("PIL")
    from factflow.holographic_scenes import SPECTRUM, draw_holographic_scene
    from PIL import Image, ImageDraw, ImageFont

    image = Image.new("RGBA", (720, 1280), (1, 7, 19, 255))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    fonts = {name: font for name in ("label", "tiny", "heading", "small")}
    draw_holographic_scene(draw, 0, 0.75, 2.0, fonts)

    # Every visible wavelength is represented in the compact legend band.
    for colour in SPECTRUM:
        assert any(image.getpixel((x, y)) == colour
                   for x in range(150, 600) for y in range(785, 805))


def test_project_wide_voice_policy_requires_kokoro_and_defaults_to_af_heart():
    from factflow.production_standards import validate_production_voice
    assert validate_production_voice({}) == "af_heart"
    assert validate_production_voice({"voice": "af_heart"}) == "af_heart"
    with pytest.raises(ValueError, match="Kokoro"):
        validate_production_voice({"voice": "espeak"})


def test_project_wide_visual_standards_cover_holographic_motion_and_storytelling():
    from factflow.production_standards import PRODUCTION_STANDARDS
    required = set(PRODUCTION_STANDARDS["required_visual_properties"])
    assert {
        "holographic_subjects_and_environments",
        "continuous_subject_or_camera_motion",
        "transparent_layered_depth",
        "volumetric_light_and_glow",
    } <= required
    storytelling = set(PRODUCTION_STANDARDS["storytelling_requirements"])
    assert "every_important_narrated_concept_has_a_visual" in storytelling
    assert "muted_playback_remains_understandable" in storytelling


def test_renderer_refuses_to_reuse_sky_storyboard_for_another_topic():
    spec = {**valid_spec(), "visual_profile": "sunset_red_v1"}
    with pytest.raises(ValueError, match="unrelated storyboard"):
        validate_sample_spec(spec)
