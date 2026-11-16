from __future__ import annotations

import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / ".github" / "scripts" / "build_weekly_ideas.py"
SPEC = importlib.util.spec_from_file_location("weekly_ideas", SCRIPT)
assert SPEC and SPEC.loader
weekly_ideas = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(weekly_ideas)


def candidate(index: int) -> dict:
    return {
        "text": f"Researchers report that this example topic contains a distinct source-backed finding number {index}.",
        "source_url": f"https://example.org/article-{index}",
        "final_url": f"https://example.org/article-{index}",
        "publisher_id": "NASA" if index % 2 else "USGS",
        "source_title": f"Research article {index}",
        "discovered_title": f"Fresh topic {index}",
    }


def test_choose_ideas_returns_five_distinct_source_articles():
    report = {"claim_candidates": [candidate(index) for index in range(1, 8)]}
    ideas = weekly_ideas.choose_ideas(report, {"production_specs": [], "discovery_leads": []})
    assert len(ideas) == 5
    assert len({item["source_url"] for item in ideas}) == 5


def test_choose_ideas_excludes_existing_production_topics_but_not_discovery_leads():
    report = {"claim_candidates": [candidate(index) for index in range(1, 8)]}
    library = {
        "production_specs": [{"title": "Fresh topic 1"}],
        "discovery_leads": [{"title": "Fresh topic 2"}],
    }
    ideas = weekly_ideas.choose_ideas(report, library)
    assert len(ideas) == 5
    assert all(item["discovered_title"] != "Fresh topic 1" for item in ideas)
    assert any(item["discovered_title"] == "Fresh topic 2" for item in ideas)


def test_choose_ideas_deduplicates_titles_and_urls():
    first = candidate(1)
    duplicate = {**candidate(2), "discovered_title": first["discovered_title"]}
    report = {"claim_candidates": [first, duplicate, *[candidate(index) for index in range(3, 8)]]}
    ideas = weekly_ideas.choose_ideas(report, {"production_specs": []})
    assert len(ideas) == 5
    assert len({item["discovered_title"] for item in ideas}) == 5


def test_render_idea_keeps_claim_unverified_and_links_source():
    rendered = weekly_ideas.render_idea(1, candidate(1))
    assert "candidate_unreviewed" in rendered
    assert "not verified" in rendered
    assert "https://example.org/article-1" in rendered
    assert "Scene-by-scene visual plan" in rendered
