"""Tests for FactFlow topic and evidence assessment."""

import json
from pathlib import Path

from factflow.research import evaluate_claims, load_source_registry
from factflow.topic import load_topic, validate_topic


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_PATH = ROOT / "examples/topics/why-the-sky-is-blue.json"


def read_example():
    return json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))


def test_example_topic_is_structurally_valid():
    assert validate_topic(read_example()) == []


def test_missing_required_field_is_reported():
    topic = read_example()
    del topic["narration"]
    assert "Missing required field: narration" in validate_topic(topic)


def test_evidence_without_metadata_is_rejected():
    topic = read_example()
    del topic["claims"][0]["sources"][0]["publisher_id"]
    assert any("publisher_id" in error for error in validate_topic(topic))


def test_invalid_visual_style_is_rejected():
    topic = read_example()
    topic["scenes"][0]["visual_style"] = "stock-footage"
    assert any("visual_style" in error for error in validate_topic(topic))


def test_boolean_is_not_accepted_as_duration():
    topic = read_example()
    topic["target_duration_seconds"] = True
    assert any("target_duration_seconds" in error for error in validate_topic(topic))


def test_load_topic_returns_parsed_document(tmp_path):
    topic = read_example()
    topic_file = tmp_path / "topic.json"
    topic_file.write_text(json.dumps(topic), encoding="utf-8")
    assert load_topic(topic_file)["id"] == "why-the-sky-is-blue"


def test_one_registered_publisher_is_not_called_corroborated():
    topic = read_example()
    registry = load_source_registry()
    reports = evaluate_claims(topic, registry)
    assert reports[0]["status"] == "single_registered_source_pending_editorial_review"


def test_two_independent_registered_publishers_are_corroborated_pending_review():
    topic = read_example()
    topic["claims"][0]["sources"].append({
        "publisher_id": "NOAA",
        "url": "https://www.noaa.gov/education/resource-collections/weather-atmosphere",
        "title": "Weather and atmosphere education resources",
        "accessed_on": "2026-11-14",
        "evidence_summary": "Additional independent educational source to be checked by an editor.",
        "supports_claim": True
    })
    reports = evaluate_claims(topic, load_source_registry())
    assert reports[0]["status"] == "corroborated_pending_editorial_review"
    assert reports[0]["supporting_publisher_count"] == 2


def test_unregistered_publisher_is_flagged():
    topic = read_example()
    topic["claims"][0]["sources"][0]["publisher_id"] = "UNKNOWN_SOURCE"
    reports = evaluate_claims(topic, load_source_registry())
    assert reports[0]["status"] == "unsupported_or_unregistered"
    assert "not in the curated registry" in reports[0]["issues"][0]


def test_publisher_domain_mismatch_is_flagged():
    topic = read_example()
    topic["claims"][0]["sources"][0]["url"] = "https://example.com/not-nasa"
    reports = evaluate_claims(topic, load_source_registry())
    assert reports[0]["status"] == "unsupported_or_unregistered"
    assert any("does not match registered domains" in issue for issue in reports[0]["issues"])
