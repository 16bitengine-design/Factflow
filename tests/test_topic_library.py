import json

import pytest

from factflow.topic_library import (
    add_discovery_report,
    library_summary,
    load_library,
    register_production_spec,
    save_library,
)


def test_discovery_leads_are_persisted_and_deduplicated(tmp_path):
    path = tmp_path / "library.json"
    library = load_library(path)
    report = {"candidates": [
        {"title": "A new discovery", "url": "https://example.org/story?utm_source=rss", "publisher_id": "x"},
        {"title": "A new discovery", "url": "https://example.org/story", "publisher_id": "x"},
        {"title": "Another story", "url": "https://example.org/other", "publisher_id": "y"},
    ]}
    result = add_discovery_report(library, report)
    save_library(library, path)
    restored = load_library(path)
    assert result == {"added": 2, "duplicates": 1, "total_leads": 2}
    assert restored["discovery_leads"][0]["status"] == "candidate_unreviewed"
    assert restored["discovery_leads"][0]["editorial_review_required"] is True


def test_spec_requires_explicit_editorial_approval(tmp_path):
    library = load_library(tmp_path / "library.json")
    assert register_production_spec(library, "draft.json", {"content_id_prefix": "draft", "title": "Draft"}) is True
    assert library["production_specs"][0]["status"] == "awaiting_editorial_review"
    assert library["production_specs"][0]["editorial_approved"] is False
    assert register_production_spec(library, "approved.json", {
        "content_id_prefix": "approved", "post_title": "Approved", "editorial_approved": True
    }) is True
    assert library_summary(library)["approved_ready"] == 1


def test_invalid_library_schema_is_rejected(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text(json.dumps({"schema_version": 9}), encoding="utf-8")
    with pytest.raises(ValueError, match="Unsupported"):
        load_library(path)


def test_library_summary_reports_reserve_shortfall_without_approving_leads(tmp_path):
    library = load_library(tmp_path / "library.json")
    add_discovery_report(library, {"candidates": [
        {"title": "Unreviewed story", "url": "https://example.org/story"}
    ]})
    summary = library_summary(library)
    assert summary["approved_ready"] == 0
    assert summary["unreviewed_leads"] == 1



def test_registration_preserves_source_evidence_blockers(tmp_path):
    library = load_library(tmp_path / "library.json")
    spec = {
        "content_id_prefix": "moon",
        "title": "Moon phases",
        "editorial_approved": True,
        "source_passage_verification_required_before_publication": True,
        "sources": [{
            "publisher": "NASA",
            "url": "https://science.nasa.gov/moon/",
            "review_status": "source_lead_requires_human_passage_check",
        }],
    }
    register_production_spec(library, "moon.json", spec)
    record = library["production_specs"][0]
    assert record["source_passage_verification_required_before_publication"] is True
    assert record["sources"][0]["review_status"] == "source_lead_requires_human_passage_check"
    summary = library_summary(library)
    assert summary["approved_ready"] == 1
    assert summary["eligible_for_publishing"] == 0
    assert summary["blocked_by_evidence"] == 1
