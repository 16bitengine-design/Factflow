"""Conservative claim-to-passage comparison signals for human review.

This module ranks lexical relevance and records possible polarity/numerical
differences. It does not determine truth, evidential support, contradiction,
or source independence.
"""
from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from typing import Any

_TOKEN = re.compile(r"[a-z][a-z0-9-]{2,}", re.I)
_NUMBER = re.compile(r"(?<![a-z])(-?\d+(?:[.,]\d+)?)\s*([%a-z]{0,12})", re.I)
_NEGATION = re.compile(
    r"\b(not|no|never|neither|without|cannot|can't|doesn't|isn't|aren't|wasn't|weren't|failed to|lack of)\b",
    re.I,
)
_HEDGE = re.compile(r"\b(may|might|could|possibly|potentially|suggests?|appears?|estimated|approximately|about)\b", re.I)
_STOPWORDS = {
    "about", "after", "also", "among", "been", "being", "could", "does",
    "from", "have", "into", "more", "most", "other", "over", "same",
    "some", "such", "than", "that", "their", "there", "these", "they",
    "this", "those", "through", "under", "very", "were", "what", "when",
    "where", "which", "while", "with", "would", "your", "according",
}


def _terms(value: str) -> set[str]:
    return {
        token.casefold() for token in _TOKEN.findall(value or "")
        if token.casefold() not in _STOPWORDS
    }


def _similarity(left: set[str], right: set[str]) -> tuple[float, int]:
    common = len(left & right)
    union = len(left | right)
    return (common / union if union else 0.0, common)


def _numeric_mentions(text: str) -> list[dict[str, str]]:
    mentions = []
    for match in _NUMBER.finditer(text or ""):
        raw, unit = match.group(1), match.group(2).casefold()
        try:
            value = str(float(raw.replace(",", ".")))
        except ValueError:
            continue
        start, end = match.span()
        mentions.append({
            "value": value,
            "unit": unit,
            "context": (text[max(0, start - 90):min(len(text), end + 90)]).strip(),
        })
    return mentions


def _source_identity(item: dict[str, Any]) -> str:
    for field in ("doi", "pmcid", "pmid", "source_url", "url"):
        value = item.get(field)
        if isinstance(value, str) and value.strip():
            return f"{field}:{value.strip().casefold()}"
    text = str(item.get("passage") or item.get("text") or "")
    return "passage:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _relation(claim: str, passage: str) -> tuple[str, str, float, int]:
    claim_terms, passage_terms = _terms(claim), _terms(passage)
    score, common = _similarity(claim_terms, passage_terms)
    if common < 2 or score < 0.08:
        return "inconclusive", "insufficient_shared_terms", round(score, 3), common

    claim_negated = bool(_NEGATION.search(claim))
    passage_negated = bool(_NEGATION.search(passage))
    if claim_negated != passage_negated:
        return "possible_opposition_signal", "negation_pattern_differs", round(score, 3), common

    if _HEDGE.search(passage) and not _HEDGE.search(claim):
        return "relevant_uncertain_or_qualified", "passage_contains_qualifying_language", round(score, 3), common

    # Similar wording is not proof of support; this is a relevance signal only.
    return "possible_support_signal", "lexical_overlap_and_no_detected_negation_difference", round(score, 3), common


def _collect_passages(
    candidate_id: str,
    scholarly_report: dict[str, Any],
    dossier_report: dict[str, Any],
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for item in scholarly_report.get("passages", []):
        if isinstance(item, dict) and item.get("claim_candidate_id") == candidate_id:
            items.append({
                **item,
                "passage": item.get("passage", ""),
                "source_type": "scholarly_full_text",
                "source_identity": _source_identity(item),
                "independence_group": None,
                "publisher_identity_verified": False,
            })

    for dossier in dossier_report.get("dossiers", []):
        if not isinstance(dossier, dict) or dossier.get("anchor_candidate_id") != candidate_id:
            continue
        for item in dossier.get("passages", []):
            if not isinstance(item, dict):
                continue
            passage = item.get("passage") or item.get("text") or ""
            if not passage:
                continue
            items.append({
                **item,
                "passage": passage,
                "source_type": "registered_publisher_page",
                "source_identity": _source_identity(item),
                "independence_group": item.get("independence_group"),
                "publisher_identity_verified": False,
            })

    unique: dict[str, dict[str, Any]] = {}
    for item in items:
        identity = item["source_identity"]
        # Keep separate passages from one source, but suppress duplicate records
        # for the same source and identical passage.
        digest = hashlib.sha256(item["passage"].casefold().encode("utf-8")).hexdigest()
        unique.setdefault(f"{identity}:{digest}", item)
    return list(unique.values())


def compare_evidence(
    research_report: dict[str, Any],
    scholarly_report: dict[str, Any] | None = None,
    dossier_report: dict[str, Any] | None = None,
    *,
    passage_limit_per_claim: int = 100,
) -> dict[str, Any]:
    """Compare collected passages to their assigned candidate claims.

    Inputs are existing Stage 4A candidate, Stage 4B-3 scholarly passage, and
    Stage 4B feed-dossier JSON reports. Missing optional reports are allowed.
    """
    if not 1 <= passage_limit_per_claim <= 250:
        raise ValueError("passage_limit_per_claim must be between 1 and 250.")
    candidates = research_report.get("claim_candidates", [])
    if not isinstance(candidates, list):
        raise ValueError("Research report must contain a claim_candidates list.")
    scholarly_report = scholarly_report or {}
    dossier_report = dossier_report or {}
    if not isinstance(scholarly_report.get("passages", []), list):
        raise ValueError("Scholarly report passages must be a list.")
    if not isinstance(dossier_report.get("dossiers", []), list):
        raise ValueError("Dossier report dossiers must be a list.")

    comparisons = []
    for index, candidate in enumerate(candidates):
        if not isinstance(candidate, dict):
            continue
        claim_id = candidate.get("candidate_id") or f"candidate-{index + 1:04d}"
        claim = str(candidate.get("text") or "").strip()
        if not claim:
            continue
        passages = _collect_passages(claim_id, scholarly_report, dossier_report)
        reviewed = []
        for item in passages[:passage_limit_per_claim]:
            passage = str(item.get("passage") or "").strip()
            relation, basis, score, common = _relation(claim, passage)
            reviewed.append({
                "source_identity": item["source_identity"],
                "source_type": item["source_type"],
                "source_url": item.get("source_url") or item.get("url"),
                "title": item.get("title") or item.get("source_title"),
                "publisher_id": item.get("publisher_id"),
                "independence_group": item.get("independence_group"),
                "publisher_identity_verified": False,
                "doi": item.get("doi"),
                "pmcid": item.get("pmcid"),
                "pmid": item.get("pmid"),
                "publication_date": item.get("publication_date") or item.get("published"),
                "section": item.get("section"),
                "passage": passage,
                "relation_signal": relation,
                "signal_basis": basis,
                "lexical_similarity": score,
                "shared_term_count": common,
                "hedged_language_detected": bool(_HEDGE.search(passage)),
                "numeric_mentions": _numeric_mentions(passage),
                "evidence_status": "comparison_signal_unreviewed",
                "editorial_review_required": True,
            })

        groups: dict[str, set[str]] = {}
        for item in reviewed:
            group = item.get("independence_group")
            publisher = item.get("publisher_id")
            if group and publisher:
                groups.setdefault(str(group), set()).add(str(publisher))

        numeric_differences = []
        for left_index, left in enumerate(reviewed):
            for right in reviewed[left_index + 1:]:
                if left["source_identity"] == right["source_identity"]:
                    continue
                for left_number in left["numeric_mentions"]:
                    for right_number in right["numeric_mentions"]:
                        if left_number["unit"] != right_number["unit"]:
                            continue
                        if left_number["value"] == right_number["value"]:
                            continue
                        numeric_differences.append({
                            "source_identities": [left["source_identity"], right["source_identity"]],
                            "unit": left_number["unit"],
                            "values": [left_number["value"], right_number["value"]],
                            "contexts": [left_number["context"], right_number["context"]],
                            "status": "possible_numerical_difference_requires_context_review",
                            "warning": (
                                "Matching units alone do not establish comparability. Check dates, "
                                "populations, definitions, methods, precision and measurement context."
                            ),
                        })

        comparisons.append({
            "candidate_id": claim_id,
            "claim_candidate": claim,
            "passage_count": len(reviewed),
            "passages": reviewed,
            "registered_publisher_group_count": len(groups),
            "registered_publisher_groups": [
                {"group_id": group, "publisher_ids": sorted(publishers)}
                for group, publishers in sorted(groups.items())
            ],
            "possible_numerical_differences": numeric_differences,
            "assessment": "comparison_signals_pending_human_review",
            "editorial_review_required": True,
        })

    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "candidate_count": len(comparisons),
        "comparisons": comparisons,
        "publication_gate": "blocked_pending_human_editorial_review",
        "notice": (
            "Relation labels are deterministic text-comparison signals, not judgments of truth or "
            "claim support. Lexical overlap can be misleading; negation detection is incomplete; "
            "numeric values may describe different populations, periods, definitions or methods. "
            "Scholarly metadata providers are not assumed to be publishers, and only registry group "
            "metadata is reported for feed-retrieved publisher pages. No passage is verified, "
            "counted as independent corroboration, or approved for narration."
        ),
    }
