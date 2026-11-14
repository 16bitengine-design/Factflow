"""Tests for free scholarly metadata discovery."""
from factflow.scholarly_discovery import discover_scholarly_metadata


def test_crossref_and_europe_pmc_results_are_unreviewed_metadata_leads():
    crossref = {"message": {"items": [{
        "DOI": "10.1234/example", "title": ["A study of ocean temperatures"],
        "URL": "https://doi.org/10.1234/example", "publisher": "Example Press",
        "container-title": ["Ocean Research"], "published-online": {"date-parts": [[2025, 4, 3]]},
        "author": [{"given": "A.", "family": "Researcher"}],
    }]}}
    europe = {"resultList": {"result": [{
        "title": "Ocean temperature observations", "doi": "10.5678/ocean",
        "pmcid": "PMC12345", "journalTitle": "Marine Science",
        "firstPublicationDate": "2024-06-01", "isOpenAccess": "Y",
    }]}}
    def fetcher(url):
        return crossref if "api.crossref.org" in url else europe
    report = discover_scholarly_metadata(
        {"claim_candidates": [{"candidate_id": "c-1", "text": "Ocean temperatures have changed over time."}]},
        fetcher=fetcher,
    )
    assert report["lead_count"] == 2
    assert {item["provider"] for item in report["leads"]} == {"crossref", "europe_pmc"}
    assert all(item["evidence_status"] == "metadata_lead_unreviewed" for item in report["leads"])
    assert all(item["publisher_identity_verified"] is False for item in report["leads"])
    assert report["publication_gate"] == "blocked_pending_source_review_and_human_editorial_approval"


def test_provider_failure_does_not_discard_other_provider_results():
    def fetcher(url):
        if "crossref" in url:
            raise OSError("temporary outage")
        return {"resultList": {"result": [{
            "title": "A biomedical result", "pmid": "123456", "journalTitle": "Medical Journal",
        }]}}
    report = discover_scholarly_metadata(
        {"claim_candidates": [{"candidate_id": "c-2", "text": "A sufficiently long biomedical claim."}]},
        fetcher=fetcher,
    )
    assert report["lead_count"] == 1
    assert [item["status"] for item in report["provider_results"]] == ["error", "success"]


def test_invalid_limits_are_rejected():
    import pytest
    with pytest.raises(ValueError):
        discover_scholarly_metadata({"claim_candidates": []}, claim_limit=0)
