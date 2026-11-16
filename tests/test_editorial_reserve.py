import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_editorial_reserve_specs_are_owner_approved_but_require_source_verification():
    library = json.loads((ROOT / "production/topic-library.json").read_text(encoding="utf-8"))
    reserve = [item for item in library["production_specs"] if item["spec_path"].startswith("production/specs/") and item.get("editorial_approval_basis") == "explicit_project_owner_batch_approval"]
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


def test_new_sunset_spec_is_registered_after_source_passage_assessment():
    library = json.loads((ROOT / "production/topic-library.json").read_text(encoding="utf-8"))
    record = next(item for item in library["production_specs"] if item["spec_path"] == "production/specs/sunset-red.json")
    spec = json.loads((ROOT / record["spec_path"]).read_text(encoding="utf-8"))
    assert record["status"] == "approved_ready"
    assert record["source_passage_verification_required_before_publication"] is False
    assert spec["visual_profile"] == "sunset_red_v1"
    assert spec["source_passage_verification_required_before_publication"] is False
    assert len(spec["sources"]) == 2
    assert all(source["review_status"] == "passage_checked_supports_claim" for source in spec["sources"])


def test_today_noon_and_evening_slots_select_distinct_eligible_topics():
    from datetime import datetime, timezone
    from factflow.publishing_slots import select_next_slot

    library = json.loads((ROOT / "production/topic-library.json").read_text(encoding="utf-8"))
    ledger = {}
    noon = select_next_slot(
        library, ledger, now=datetime(2026, 11, 16, 8, 30, tzinfo=timezone.utc)
    )
    assert noon["spec_path"] == "examples/videos/why-the-sky-is-blue-production.json"
    ledger[noon["content_id"]] = {"spec": noon["spec_path"], "due_at": noon["due_at"]}
    evening = select_next_slot(
        library, ledger, now=datetime(2026, 11, 16, 14, 30, tzinfo=timezone.utc)
    )
    assert evening["spec_path"] == "production/specs/sunset-red.json"
    assert evening["content_id"] != noon["content_id"]
