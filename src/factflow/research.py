"""Evidence-led claim assessment for QuantaTale.

Checks evidence records against a curated publisher registry. These automated
checks do not decide whether a cited source truly proves a claim.
"""
from __future__ import annotations

import json
import socket
from datetime import date
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REGISTRY = PROJECT_ROOT / "data" / "source_registry.json"
TRUSTED_SOURCE_COUNT_FOR_CORROBORATION = 2


class ResearchValidationError(ValueError):
    """Raised when the source registry cannot be loaded or parsed."""


def load_source_registry(path: str | Path = DEFAULT_REGISTRY) -> dict[str, Any]:
    """Load the curated publisher registry."""
    try:
        registry = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ResearchValidationError(f"Cannot load source registry: {exc}") from exc
    if not isinstance(registry, dict) or not isinstance(registry.get("publishers"), list):
        raise ResearchValidationError("Source registry must contain a publishers list.")
    return registry


def _publisher_map(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        item["id"]: item
        for item in registry.get("publishers", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }


def _host_matches_registry(host: str, domains: list[str]) -> bool:
    host = host.lower().rstrip(".")
    return any(host == domain.lower() or host.endswith("." + domain.lower()) for domain in domains)


def evaluate_claims(topic: dict[str, Any], registry: dict[str, Any]) -> list[dict[str, Any]]:
    """Assess evidence coverage and independence for every claim.

    Corroborated means two distinct registered publisher groups are recorded as
    supporting the claim. It is not a truth guarantee or publication approval.
    """
    publishers = _publisher_map(registry)
    reports = []

    for index, claim in enumerate(topic.get("claims", [])):
        issues: list[str] = []
        supporting_groups: set[str] = set()
        supporting_ids: set[str] = set()
        registered_records = 0
        source_reports = []

        for source_index, source in enumerate(claim.get("sources", [])):
            publisher_id = source.get("publisher_id", "")
            publisher = publishers.get(publisher_id)
            host = urlparse(source.get("url", "")).hostname or ""
            source_issues: list[str] = []
            domain_matches = False

            if publisher is None:
                source_issues.append(f"Publisher '{publisher_id}' is not in the curated registry.")
            else:
                domain_matches = _host_matches_registry(host, publisher.get("domains", []))
                if not domain_matches:
                    source_issues.append(
                        f"URL host '{host}' does not match registered domains for {publisher_id}."
                    )
                else:
                    registered_records += 1

            try:
                date.fromisoformat(source.get("accessed_on", ""))
            except (TypeError, ValueError):
                source_issues.append("accessed_on must be a real date in YYYY-MM-DD format.")

            if publisher is not None and domain_matches and source.get("supports_claim") is True:
                supporting_groups.add(publisher.get("independence_group", publisher_id))
                supporting_ids.add(publisher_id)
            elif source.get("supports_claim") is False:
                source_issues.append("Source has not yet been confirmed as directly supporting this claim.")

            source_reports.append({
                "source_index": source_index,
                "publisher_id": publisher_id,
                "url": source.get("url", ""),
                "registered_publisher": publisher is not None,
                "domain_matches_registry": domain_matches,
                "issues": source_issues,
            })
            issues.extend(f"Source {source_index + 1}: {item}" for item in source_issues)

        count = len(supporting_groups)
        if count >= TRUSTED_SOURCE_COUNT_FOR_CORROBORATION:
            status = "corroborated_pending_editorial_review"
        elif count == 1:
            status = "single_registered_source_pending_editorial_review"
        elif registered_records:
            status = "evidence_not_yet_confirmed"
        else:
            status = "unsupported_or_unregistered"

        reports.append({
            "claim_index": index,
            "claim": claim.get("text", ""),
            "status": status,
            "independent_registered_publisher_groups": sorted(supporting_groups),
            "supporting_publishers": sorted(supporting_ids),
            "supporting_independent_group_count": count,
            "registered_source_record_count": registered_records,
            "sources": source_reports,
            "issues": issues,
            "editorial_review_required": True,
        })

    return reports


def check_source_url(url: str, timeout: int = 12) -> dict[str, Any]:
    """Check URL reachability only; this does not validate source content."""
    headers = {"User-Agent": "QuantaTaleResearchBot/0.1 (source-link-check)"}
    request = Request(url, headers=headers, method="HEAD")
    try:
        with urlopen(request, timeout=timeout) as response:
            return {
                "url": url, "reachable": 200 <= response.status < 400,
                "status_code": response.status, "final_url": response.geturl(), "error": None,
            }
    except HTTPError as exc:
        if exc.code in {403, 405, 501}:
            try:
                fallback = Request(url, headers=headers, method="GET")
                with urlopen(fallback, timeout=timeout) as response:
                    return {
                        "url": url, "reachable": 200 <= response.status < 400,
                        "status_code": response.status, "final_url": response.geturl(), "error": None,
                    }
            except (HTTPError, URLError, TimeoutError, socket.timeout) as fallback_exc:
                return {
                    "url": url, "reachable": False, "status_code": getattr(fallback_exc, "code", None),
                    "final_url": None, "error": str(fallback_exc),
                }
        return {
            "url": url, "reachable": False, "status_code": exc.code,
            "final_url": exc.geturl(), "error": str(exc),
        }
    except (URLError, TimeoutError, socket.timeout, ValueError) as exc:
        return {
            "url": url, "reachable": False, "status_code": None,
            "final_url": None, "error": str(exc),
        }


def build_research_report(
    topic: dict[str, Any], registry: dict[str, Any], check_links: bool = False
) -> dict[str, Any]:
    """Build a machine-readable evidence report for a topic."""
    claims = evaluate_claims(topic, registry)
    links = []
    if check_links:
        seen: set[str] = set()
        for claim in topic.get("claims", []):
            for source in claim.get("sources", []):
                url = source.get("url", "")
                if url and url not in seen:
                    seen.add(url)
                    links.append(check_source_url(url))

    return {
        "topic_id": topic.get("id"),
        "topic_title": topic.get("title"),
        "claim_count": len(claims),
        "claim_statuses": claims,
        "links_checked": len(links),
        "link_results": links,
        "publication_gate": "blocked_pending_editorial_review",
        "notice": (
            "Automated checks validate publisher registration, URL-domain alignment, "
            "evidence metadata and optional link reachability. They do not prove that "
            "a source supports a claim or that a claim is true. A human must review "
            "the cited material before publication."
        ),
    }
