import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_editorial_reserve_specs_are_owner_approved_but_require_source_verification():
    library = json.loads((ROOT / "production/topic-library.json").read_text(encoding="utf-8"))
    reserve = [item for item in library["production_specs"] if item["spec_path"].startswith("production/specs/")]
    assert len(reserve) == 14
    for record in reserve:
        spec = json.loads((ROOT / record["spec_path"]).read_text(encoding="utf-8"))
        assert spec["editorial_approved"] is True
        assert record["editorial_approved"] is True
        assert record["status"] == "approved_ready"
        assert spec["source_passage_verification_required_before_publication"] is True
        assert len(spec["sources"]) >= 2
        assert all(source["url"].startswith("https://") for source in spec["sources"])
        assert all(source["review_status"] == "source_lead_requires_human_passage_check" for source in spec["sources"])

def test_editorial_reserve_has_unique_content_ids_and_spec_paths():
    library = json.loads((ROOT / "production/topic-library.json").read_text(encoding="utf-8"))
    reserve = [item for item in library["production_specs"] if item["spec_path"].startswith("production/specs/")]
    assert len({item["spec_path"] for item in reserve}) == len(reserve)
    assert len({item["content_id_prefix"] for item in reserve}) == len(reserve)
