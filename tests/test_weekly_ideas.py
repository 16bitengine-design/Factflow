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


def test_choose_ideas_excludes_topics_already_in_the_library():
    report = {"claim_candidates": [candidate(index) for index in range(1, 8)]}
    library = {
        "production_specs": [{"title": "Fresh topic 1"}],
        "discovery_leads": [{"title": "Fresh topic 2"}],
    }

    ideas = weekly_ideas.choose_ideas(report, library)

    assert len(ideas) == 5
    assert all(item["discovered_title"] not in {"Fresh topic 1", "Fresh topic 2"} for item in ideas)


def test_render_idea_keeps_claim_unverified_and_links_source():
    item = candidate(1)

    rendered = weekly_ideas.render_idea(1, item)

    assert "candidate_unreviewed" in rendered
    assert "not verified" in rendered
    assert "https://example.org/article-1" in rendered
    assert "Scene-by-scene visual plan" in rendered
