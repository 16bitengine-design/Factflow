import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_editorial_reserve_specs_are_complete_and_blocked_pending_review():
    library = json.loads((ROOT / "production/topic-library.json").read_text(encoding="utf-8"))
    reserve = [
        item for item in library["production_specs"]
        if item["spec_path"].startswith("production/specs/")
    ]
    assert len(reserve) == 10

    for record in reserve:
        path = ROOT / record["spec_path"]
        spec = json.loads(path.read_text(encoding="utf-8"))
        assert spec["editorial_approved"] is False
        assert record["editorial_approved"] is False
        assert record["status"] == "awaiting_editorial_review"
        assert spec["editorial_status"] == "awaiting_human_editorial_review"
        assert spec["editorial_review_required"] is True
        assert len(spec["narration"].split()) >= 45
        assert len(spec["sources"]) >= 2
        assert all(source["url"].startswith("https://") for source in spec["sources"])
        assert all(source["review_status"] == "source_lead_requires_human_passage_check"
                   for source in spec["sources"])


def test_editorial_reserve_has_unique_content_ids_and_spec_paths():
    library = json.loads((ROOT / "production/topic-library.json").read_text(encoding="utf-8"))
    reserve = [
        item for item in library["production_specs"]
        if item["spec_path"].startswith("production/specs/")
    ]
    assert len({item["spec_path"] for item in reserve}) == len(reserve)
    assert len({item["content_id_prefix"] for item in reserve}) == len(reserve)
