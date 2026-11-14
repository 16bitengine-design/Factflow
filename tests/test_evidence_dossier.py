"""Tests for Stage 4B independent-feed evidence dossiers."""
from factflow.evidence_dossier import build_evidence_dossier


def test_discovers_related_passage_groups_publishers_and_flags_numeric_difference():
    registry = {"publishers": [
        {"id": "NASA", "name": "NASA", "domains": ["nasa.gov"], "independence_group": "NASA"},
        {"id": "NOAA", "name": "NOAA", "domains": ["noaa.gov"], "independence_group": "NOAA"},
    ]}
    feeds = {"feeds": [{"publisher_id": "NOAA", "url": "https://www.noaa.gov/feed.xml"}]}
    feed_xml = """<rss><channel><item>
      <title>Earth atmosphere oxygen measurement update</title>
      <link>https://www.noaa.gov/story</link>
      <description>New reference information about Earth's atmosphere and oxygen.</description>
    </item></channel></rss>"""
    article_html = """<html><title>Atmosphere reference</title><article><p>
      Earth's atmosphere contains 21 percent oxygen according to this reference measurement.
    </p></article></html>"""
    original = {"claim_candidates": [{
        "candidate_id": "nasa-0001",
        "text": "Earth's atmosphere contains 20 percent oxygen according to this reference measurement.",
        "source_passage": "Earth's atmosphere contains 20 percent oxygen according to this reference measurement.",
        "publisher_id": "NASA", "source_url": "https://www.nasa.gov/original",
        "source_title": "Original", "status": "candidate_unreviewed",
    }]}

    report = build_evidence_dossier(
        original, registry, feeds,
        feed_fetcher=lambda url: feed_xml,
        article_fetcher=lambda url, publisher: {
            "final_url": url, "html": article_html, "content_type": "text/html"
        },
    )

    assert report["dossier_count"] == 1
    dossier = report["dossiers"][0]
    assert dossier["independent_source_group_count"] == 2
    assert dossier["assessment"] == "evidence_collected_pending_human_assessment"
    assert any(
        "possible_numerical_difference" in item["flags"]
        for item in dossier["possible_conflicts"]
    )
    assert dossier["editorial_review_required"] is True
    assert report["publication_gate"] == "blocked_pending_human_editorial_review"


def test_does_not_compare_sources_in_the_same_independence_group():
    registry = {"publishers": [
        {"id": "NASA", "domains": ["nasa.gov"], "independence_group": "US_GOV"},
        {"id": "NOAA", "domains": ["noaa.gov"], "independence_group": "US_GOV"},
    ]}
    feeds = {"feeds": [{"publisher_id": "NOAA", "url": "https://www.noaa.gov/feed.xml"}]}
    feed_xml = """<rss><channel><item>
      <title>Earth atmosphere oxygen measurement</title>
      <link>https://www.noaa.gov/story</link>
      <description>Atmosphere oxygen measurement details.</description>
    </item></channel></rss>"""
    article_html = """<article><p>Earth's atmosphere contains 21 percent oxygen according to this reference measurement.</p></article>"""
    original = {"claim_candidates": [{
        "candidate_id": "nasa-0001",
        "text": "Earth's atmosphere contains 20 percent oxygen according to this reference measurement.",
        "source_passage": "Earth's atmosphere contains 20 percent oxygen according to this reference measurement.",
        "publisher_id": "NASA", "source_url": "https://www.nasa.gov/original",
    }]}

    report = build_evidence_dossier(
        original, registry, feeds,
        feed_fetcher=lambda url: feed_xml,
        article_fetcher=lambda url, publisher: {
            "final_url": url, "html": article_html, "content_type": "text/html"
        },
    )

    dossier = report["dossiers"][0]
    assert dossier["independent_source_group_count"] == 1
    assert dossier["possible_conflicts"] == []


def test_empty_research_report_returns_empty_dossier_without_false_approval():
    report = build_evidence_dossier(
        {"claim_candidates": []},
        {"publishers": []},
        {"feeds": []},
        feed_fetcher=lambda url: "<rss><channel /></rss>",
    )
    assert report["dossier_count"] == 0
    assert report["publication_gate"] == "blocked_pending_human_editorial_review"
