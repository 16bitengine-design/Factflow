"""Tests for deterministic source-backed claim candidate extraction."""
from factflow.fact_research import extract_claim_candidates, research_discovery_candidates


def registry():
    return {"publishers": [
        {"id": "NASA", "domains": ["nasa.gov"], "areas": ["space"], "independence_group": "NASA"}
    ]}


def test_extracts_sentences_and_preserves_source_passage():
    html = """<html><head><title>Atmosphere research</title></head>
    <body><nav><p>Subscribe to our newsletter.</p></nav>
    <article><p>Earth's atmosphere is a mixture of gases that surrounds the planet.
    It contains nitrogen and oxygen, and it protects life from many harmful conditions.</p>
    <script><p>This fake sentence is not part of the article.</p></script></article></body></html>"""
    result = extract_claim_candidates(html)
    assert result["page_title"] == "Atmosphere research"
    assert len(result["claim_candidates"]) == 2
    assert "Earth's atmosphere is a mixture" in result["claim_candidates"][0]["text"]
    assert "It contains nitrogen" in result["claim_candidates"][1]["source_passage"]


def test_candidates_are_not_marked_as_supported_or_verified():
    discovery = {"candidates": [{
        "publisher_id": "NASA", "url": "https://www.nasa.gov/story",
        "title": "NASA story"
    }]}
    html = "<article><p>Earth's atmosphere is a mixture of gases that surrounds the planet.</p></article>"
    report = research_discovery_candidates(
        discovery, registry(),
        fetcher=lambda url, publisher: {"final_url": url, "html": html, "content_type": "text/html"}
    )
    assert report["claim_candidate_count"] == 1
    item = report["claim_candidates"][0]
    assert item["status"] == "candidate_unreviewed"
    assert item["supports_claim"] is None
    assert item["editorial_review_required"] is True
    assert item["source_url"] == "https://www.nasa.gov/story"


def test_unregistered_or_mismatched_candidate_is_rejected_without_fetching():
    discovery = {"candidates": [{
        "publisher_id": "NASA", "url": "https://evil.example/story", "title": "Fake"
    }]}
    report = research_discovery_candidates(
        discovery, registry(),
        fetcher=lambda *_: (_ for _ in ()).throw(AssertionError("must not fetch"))
    )
    assert report["source_results"][0]["status"] == "rejected_unregistered_source"
    assert report["claim_candidate_count"] == 0


def test_candidate_limit_is_validated():
    try:
        extract_claim_candidates("<p>Text</p>", max_candidates=0)
    except ValueError as exc:
        assert "max_candidates" in str(exc)
    else:
        raise AssertionError("Expected max_candidates validation")
