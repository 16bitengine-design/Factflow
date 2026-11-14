"""Tests for bounded Europe PMC open-access full-text retrieval."""
import pytest

from factflow.scholarly_fulltext import (
    extract_full_text_passages,
    retrieve_open_access_passages,
)

XML = """<?xml version="1.0"?>
<article>
  <front><article-meta><abstract><p>This abstract explains the measured result and includes enough detail for extraction.</p></abstract></article-meta></front>
  <body>
    <sec><title>Methods</title><p>The researchers measured the samples using a calibrated instrument and recorded the observations.</p></sec>
    <sec><title>Results</title><p>The measured result was 42 units after the controlled experiment was completed.</p></sec>
    <ref-list><ref><p>This reference should not be extracted as evidence.</p></ref></ref-list>
  </body>
</article>
"""


def test_extracts_abstract_and_body_passages_with_section_context():
    passages = extract_full_text_passages(XML)
    assert [item["section"] for item in passages] == ["abstract", "Methods", "Results"]
    assert "42 units" in passages[2]["text"]
    assert all("reference should not" not in item["text"] for item in passages)


def test_retrieves_only_explicit_open_access_pmcid_records():
    report = {"leads": [
        {"pmcid": "PMC12345", "open_access": True, "title": "Open article", "claim_candidate_id": "c1"},
        {"pmcid": "PMC99999", "open_access": False, "title": "Closed article"},
        {"pmcid": "PMC12345", "open_access": True, "title": "Duplicate"},
        {"pmcid": None, "open_access": True},
    ]}
    calls = []
    result = retrieve_open_access_passages(report, fetcher=lambda pmcid: calls.append(pmcid) or XML)
    assert calls == ["PMC12345"]
    assert result["retrieved_article_count"] == 1
    assert result["passage_count"] == 3
    assert result["passages"][0]["evidence_status"] == "open_access_passage_unreviewed"
    assert result["passages"][0]["supports_claim"] is None
    assert result["passages"][0]["editorial_review_required"] is True
    assert result["publication_gate"].startswith("blocked_")


def test_provider_failure_is_recorded_without_discarding_other_articles():
    report = {"leads": [
        {"pmcid": "PMC12345", "open_access": True},
        {"pmcid": "PMC54321", "open_access": True},
    ]}
    def fetcher(pmcid):
        if pmcid == "PMC12345":
            raise TimeoutError("slow provider")
        return XML
    result = retrieve_open_access_passages(report, fetcher=fetcher)
    assert [item["status"] for item in result["article_results"]] == ["error", "retrieved"]
    assert result["passage_count"] == 3


def test_invalid_xml_and_entity_declarations_are_rejected():
    with pytest.raises(ValueError, match="Invalid Europe PMC"):
        extract_full_text_passages("<article>")
    with pytest.raises(ValueError, match="entity declarations"):
        extract_full_text_passages("<!DOCTYPE x [<!ENTITY a 'x'>]><article/>")


def test_limits_and_report_shape_are_validated():
    with pytest.raises(ValueError):
        extract_full_text_passages(XML, limit=0)
    with pytest.raises(ValueError):
        retrieve_open_access_passages({"leads": []}, article_limit=0)
    with pytest.raises(ValueError):
        retrieve_open_access_passages({"leads": {} })


def test_unreviewed_report_with_no_eligible_full_text_returns_empty_result():
    result = retrieve_open_access_passages({"leads": [
        {"pmcid": "PMC12345", "open_access": False}
    ]})
    assert result["passage_count"] == 0
    assert result["article_result_count"] == 0
    assert result["publication_gate"].startswith("blocked_")
