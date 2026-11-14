"""Tests for the initial FactFlow topic specification."""

from copy import deepcopy
import json

from factflow.topic import load_topic, validate_topic


EXAMPLE_PATH = "examples/topics/why-the-sky-is-blue.json"


def test_example_topic_is_valid():
    with open(EXAMPLE_PATH, encoding="utf-8") as file:
        topic = json.load(file)
    assert validate_topic(topic) == []


def test_missing_required_field_is_reported():
    with open(EXAMPLE_PATH, encoding="utf-8") as file:
        topic = json.load(file)
    del topic["narration"]
    errors = validate_topic(topic)
    assert "Missing required field: narration" in errors


def test_claim_without_source_is_rejected():
    with open(EXAMPLE_PATH, encoding="utf-8") as file:
        topic = json.load(file)
    topic["claims"][0]["sources"] = []
    assert any("claims[0].sources" in error for error in validate_topic(topic))


def test_invalid_visual_style_is_rejected():
    with open(EXAMPLE_PATH, encoding="utf-8") as file:
        topic = json.load(file)
    topic["scenes"][0]["visual_style"] = "stock-footage"
    assert any("visual_style" in error for error in validate_topic(topic))


def test_boolean_is_not_accepted_as_duration():
    with open(EXAMPLE_PATH, encoding="utf-8") as file:
        topic = json.load(file)
    topic["target_duration_seconds"] = True
    assert any("target_duration_seconds" in error for error in validate_topic(topic))


def test_load_topic_returns_parsed_document(tmp_path):
    with open(EXAMPLE_PATH, encoding="utf-8") as file:
        topic = json.load(file)
    topic_file = tmp_path / "topic.json"
    topic_file.write_text(json.dumps(deepcopy(topic)), encoding="utf-8")
    assert load_topic(topic_file)["id"] == "why-the-sky-is-blue"
