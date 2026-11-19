import json
from pathlib import Path

import pytest

from factflow.visual_motifs import MOTIFS, draw_motif

ROOT = Path(__file__).resolve().parents[1]


def _fonts():
    from PIL import ImageFont

    font = ImageFont.load_default()
    return {name: font for name in ("label", "tiny", "heading", "small")}


def test_every_spec_scene_motif_exists():
    for path in (ROOT / "production/specs").glob("*.json"):
        for scene in json.loads(path.read_text(encoding="utf-8")).get("scenes", []):
            assert scene.get("motif", "none") in set(MOTIFS) | {"none"}, path.name


def test_enabled_generic_topics_give_every_scene_a_motif():
    for slug in ("clouds-form", "ocean-blue", "old-faithful", "mercury-day"):
        scenes = json.loads((ROOT / f"production/specs/{slug}.json").read_text(encoding="utf-8"))["scenes"]
        assert all(s.get("motif") in MOTIFS for s in scenes), slug


@pytest.mark.parametrize("name", sorted(MOTIFS))
def test_every_motif_draws_at_several_progress_points(name):
    pytest.importorskip("PIL")
    from PIL import Image, ImageDraw

    for progress in (0.0, 0.5, 1.0):
        draw = ImageDraw.Draw(Image.new("RGBA", (720, 1280)), "RGBA")
        assert draw_motif(name, draw, progress, 1.0, _fonts(), (80, 200, 255)) is not False


def test_unknown_motif_returns_false_so_generic_scene_is_used():
    pytest.importorskip("PIL")
    from PIL import Image, ImageDraw

    draw = ImageDraw.Draw(Image.new("RGBA", (720, 1280)), "RGBA")
    assert draw_motif("nope", draw, 0.5, 1.0, _fonts(), (1, 2, 3)) is False
