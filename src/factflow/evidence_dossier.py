"""Independent-feed evidence discovery and conservative comparison dossiers.

This deterministic stage finds potentially relevant articles in configured feeds,
retrieves bounded publisher pages, groups source passages by publisher independence
group, and flags possible differences for human review. It never verifies truth.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from factflow.discovery import discover_candidates, load_feed_config
from factflow.fact_research import research_discovery_candidates
from factflow.research import load_source_registry

_TOKEN = re.compile(r"[a-z][a-z0-9-]{2,}", re.I)
_NUMBER = re.compile(r"(?<![a-z])(-?\d+(?:[.,]\d+)?)\s*([%a-z]{0,12})", re.I)
_STOPWORDS = {
    "about", "after", "also", "among", "been", "being", "could", "does",
    "from", "have", "into", "more", "most", "other", "over", "same",
    "some", "such", "than", "that", "their", "there", "these", "they",
    "this", "those", "through", "under", "very", "were", "what", "when",
    "where", "which", "while", "with", "would", "your",
}
_NEGATION = re.compile(r"\b(not|no|never|neither|without|cannot|can't|doesn't|isn't|aren't|wasn't|weren't)\b", re.I)


def _terms(value: str) -> set[str]:
    return {token.casefold() for token in _TOKEN.findall(value or "") if token.casefold() not in _STOPWORDS}


def _similarity(left: set[str], right: set[str]) -> tuple[float, int]:
    common = len(left & right)
    union = len(left | right)
    return (common / union if union else 0.0, common)


def _numeric_values(text: str) -> set[tuple[str, str]]:
    values = set()
    for number, unit in _NUMBER.findall(text or ""):
        try:
            normalized = str(float(number.replace(",", ".")))
        except ValueError:
            continue
        values.add((normalized, unit.casefold()))
    return values


def _candidate_record(item: dict[str, Any], registry: dict[str, Any]) -> dict[str, Any]:
    publishers = {
        p.get("id"): p for p in registry.get("publishers", [])
        if isinstance(p, dict) and p.get("id")
    }
    publisher_id = item.get("publisher_id", "")
    publisher = publishers.get(publisher_id, {})
    return {
        "candidate_id": item.get("candidate_id", ""),
        "text": item.get("text", ""),
        "passage": item.get("source_passage", ""),
        "publisher_id": publisher_id,
        "publisher_name": publisher.get("name", publisher_id),
        "independence_group": publisher.get("independence_group", publisher_id or "unknown"),
        "source_url": item.get("source_url", item.get("url", "")),
        "source_title": item.get("source_title", item.get("title", "")),
        "status": item.get("status", "candidate_unreviewed"),
    }


def _compare_pair(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any] | None:
    left_text = left["text"] or left["passage"]
    right_text = right["text"] or right["passage"]
    left_terms, right_terms = _terms(left_text), _terms(right_text)
    similarity, common = _similarity(left_terms, right_terms)
    if common < 2 or similarity < 0.18:
        return None

    flags: list[str] = []
    left_negated = bool(_NEGATION.search(left_text))
    right_negated = bool(_NEGATION.search(right_text))
    if left_negated != right_negated:
        flags.append("possible_polarity_difference")

    left_numbers, right_numbers = _numeric_values(left_text), _numeric_values(right_text)
    shared_units = {unit for _, unit in left_numbers} & {unit for _, unit in right_numbers}
    for unit in sorted(shared_units):
        lvals = {value for value, found_unit in left_numbers if found_unit == unit}
        rvals = {value for value, found_unit in right_numbers if found_unit == unit}
        if lvals and rvals and lvals != rvals:
            flags.append("possible_numerical_difference")
            break

    if not flags:
        return None
    return {
        "candidate_ids": [left["candidate_id"], right["candidate_id"]],
        "publisher_ids": [left["publisher_id"], right["publisher_id"]],
        "shared_term_count": common,
        "lexical_similarity": round(similarity, 3),
        "flags": flags,
        "review_status": "unresolved_requires_human_comparison",
        "notice": "Heuristic difference signal only; context, units, dates and definitions may explain it.",
    }


def build_evidence_dossier(
    research_report: dict[str, Any],
    registry: dict[str, Any],
    feed_config: dict[str, Any],
    *,
    feed_fetcher=None,
    article_fetcher=None,
    feed_limit: int = 100,
    article_limit: int = 20,
) -> dict[str, Any]:
    """Discover feed articles related to existing candidates and create review dossiers."""
    if not 1 <= feed_limit <= 200:
        raise ValueError("feed_limit must be between 1 and 200.")
    if not 1 <= article_limit <= 50:
        raise ValueError("article_limit must be between 1 and 50.")

    originals = research_report.get("claim_candidates", [])
    if not isinstance(originals, list):
        raise ValueError("Research report must contain a claim_candidates list.")

    discovered = discover_candidates(
        feed_config, registry,
        **({"fetcher": feed_fetcher} if feed_fetcher else {}),
        limit=feed_limit,
    )
    claim_terms = [
        _terms(item.get("text", "") + " " + item.get("source_passage", ""))
        for item in originals if isinstance(item, dict)
    ]
    relevant = []
    seen_urls = set()
    for lead in discovered.get("candidates", []):
        lead_terms = _terms(lead.get("title", "") + " " + lead.get("description", ""))
        if not lead_terms:
            continue
        best = max((_similarity(terms, lead_terms) for terms in claim_terms), default=(0.0, 0))
        if best[1] >= 2 and best[0] >= 0.12 and lead.get("url") not in seen_urls:
            relevant.append(lead)
            seen_urls.add(lead.get("url"))

    retrieval_input = {"candidates": relevant[:article_limit]}
    retrieved = research_discovery_candidates(
        retrieval_input, registry,
        **({"fetcher": article_fetcher} if article_fetcher else {}),
        limit=article_limit,
    )
    combined = [
        _candidate_record(item, registry)
        for item in originals + retrieved.get("claim_candidates", [])
        if isinstance(item, dict)
    ]

    # Assign each passage to the closest existing claim candidate. Keep one dossier
    # per original candidate to avoid merging unrelated claims through transitive links.
    dossiers = []
    for index, original in enumerate(originals):
        if not isinstance(original, dict):
            continue
        anchor = _candidate_record(original, registry)
        anchor_terms = _terms(anchor["text"] + " " + anchor["passage"])
        related = [anchor]
        for item in combined[len(originals):]:
            item_terms = _terms(item["text"] + " " + item["passage"])
            similarity, common = _similarity(anchor_terms, item_terms)
            if common >= 2 and similarity >= 0.12:
                related.append(item)

        # Avoid duplicate publisher independence groups inflating corroboration.
        groups: dict[str, list[dict[str, Any]]] = {}
        for item in related:
            groups.setdefault(item["independence_group"], []).append(item)

        comparisons = []
        for i, left in enumerate(related):
            for right in related[i + 1:]:
                if left["independence_group"] == right["independence_group"]:
                    continue
                comparison = _compare_pair(left, right)
                if comparison:
                    comparisons.append(comparison)

        dossiers.append({
            "dossier_id": f"dossier-{index + 1:04d}",
            "anchor_candidate_id": anchor["candidate_id"],
            "claim_candidate": anchor["text"],
            "passages": related,
            "independent_source_groups": [
                {"group_id": group, "publisher_ids": sorted({p["publisher_id"] for p in items}),
                 "passage_count": len(items)}
                for group, items in sorted(groups.items())
            ],
            "independent_source_group_count": len(groups),
            "possible_conflicts": comparisons,
            "assessment": "evidence_collected_pending_human_assessment",
            "editorial_review_required": True,
        })

    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "discovery": {
            "feed_candidate_count": discovered.get("candidate_count", 0),
            "relevant_article_count": len(relevant),
            "retrieved_article_count": retrieved.get("source_count", 0),
            "retrieved_claim_candidate_count": retrieved.get("claim_candidate_count", 0),
            "feed_results": discovered.get("feed_results", []),
            "source_results": retrieved.get("source_results", []),
        },
        "dossier_count": len(dossiers),
        "dossiers": dossiers,
        "publication_gate": "blocked_pending_human_editorial_review",
        "notice": (
            "Feed matches and extracted passages are research leads, not proof. "
            "Independence groups reduce duplicate counting but do not establish source independence. "
            "Possible conflict flags are heuristic and require a human to compare full context, "
            "definitions, dates, methods and units. No claim is verified or approved for narration."
        ),
    }
