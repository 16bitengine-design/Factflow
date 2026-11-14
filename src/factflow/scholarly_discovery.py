"""Free scholarly-metadata discovery adapters for Stage 4B.

Crossref and Europe PMC return bibliographic metadata, not proof or extracted
supporting passages. Records from these APIs remain unreviewed research leads.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

MAX_RESPONSE_BYTES = 2_000_000
DEFAULT_TIMEOUT = 15
USER_AGENT = "QuantaTaleResearchBot/0.2 (https://github.com/16bitengine-design/QuantaTale)"


def fetch_json(url: str, timeout: int = DEFAULT_TIMEOUT) -> dict[str, Any]:
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urlopen(request, timeout=timeout) as response:
        raw = response.read(MAX_RESPONSE_BYTES + 1)
        if len(raw) > MAX_RESPONSE_BYTES:
            raise ValueError("Research API response exceeds the 2 MB safety limit.")
        payload = json.loads(raw.decode("utf-8", errors="replace"))
    if not isinstance(payload, dict):
        raise ValueError("Research API returned an unexpected JSON document.")
    return payload


def _query_text(claim: str) -> str:
    return " ".join((claim or "").split())[:240]


def _date_from_parts(value: Any) -> str | None:
    if not isinstance(value, dict):
        return None
    parts = value.get("date-parts")
    if not isinstance(parts, list) or not parts or not isinstance(parts[0], list):
        return None
    values = parts[0]
    if not values or not all(isinstance(item, int) for item in values[:3]):
        return None
    return "-".join(str(item).zfill(2) if index > 0 else str(item) for index, item in enumerate(values[:3]))


def _crossref_records(payload: dict[str, Any], claim_id: str) -> list[dict[str, Any]]:
    items = payload.get("message", {}).get("items", [])
    records = []
    for item in items if isinstance(items, list) else []:
        if not isinstance(item, dict):
            continue
        titles = item.get("title") or []
        title = titles[0].strip() if titles and isinstance(titles[0], str) else ""
        doi = (item.get("DOI") or "").strip()
        if not title or not doi:
            continue
        containers = item.get("container-title") or []
        records.append({
            "claim_candidate_id": claim_id,
            "provider": "crossref",
            "title": title,
            "doi": doi,
            "url": item.get("URL") or f"https://doi.org/{doi}",
            "publisher_metadata": item.get("publisher"),
            "journal": containers[0] if containers else None,
            "published": _date_from_parts(item.get("published-online") or item.get("published-print") or item.get("issued")),
            "authors": [
                " ".join(part for part in (author.get("given"), author.get("family")) if part)
                for author in item.get("author", [])[:8] if isinstance(author, dict)
            ],
            "metadata_url": f"https://api.crossref.org/works/{doi}",
            "evidence_status": "metadata_lead_unreviewed",
            "publisher_identity_verified": False,
        })
    return records


def _europe_pmc_records(payload: dict[str, Any], claim_id: str) -> list[dict[str, Any]]:
    items = payload.get("resultList", {}).get("result", [])
    records = []
    for item in items if isinstance(items, list) else []:
        if not isinstance(item, dict) or not item.get("title"):
            continue
        doi = (item.get("doi") or "").strip()
        pmcid = (item.get("pmcid") or "").strip()
        pmid = (item.get("pmid") or "").strip()
        if doi:
            url = f"https://doi.org/{doi}"
        elif pmcid:
            url = f"https://europepmc.org/articles/{pmcid}"
        elif pmid:
            url = f"https://europepmc.org/article/MED/{pmid}"
        else:
            url = None
        records.append({
            "claim_candidate_id": claim_id,
            "provider": "europe_pmc",
            "title": " ".join(item["title"].split()),
            "doi": doi or None,
            "pmcid": pmcid or None,
            "pmid": pmid or None,
            "url": url,
            "publisher_metadata": item.get("journalTitle"),
            "journal": item.get("journalTitle"),
            "published": item.get("firstPublicationDate"),
            "authors": [item.get("authorString")] if item.get("authorString") else [],
            "open_access": item.get("isOpenAccess") == "Y",
            "metadata_url": (
                f"https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML"
                if pmcid else None
            ),
            "evidence_status": "metadata_lead_unreviewed",
            "publisher_identity_verified": False,
        })
    return records


def discover_scholarly_metadata(
    research_report: dict[str, Any],
    *,
    fetcher: Callable[[str], dict[str, Any]] = fetch_json,
    claim_limit: int = 20,
    results_per_provider: int = 5,
) -> dict[str, Any]:
    """Search free Crossref and Europe PMC metadata APIs for claim-related leads."""
    if not 1 <= claim_limit <= 50:
        raise ValueError("claim_limit must be between 1 and 50.")
    if not 1 <= results_per_provider <= 10:
        raise ValueError("results_per_provider must be between 1 and 10.")
    candidates = research_report.get("claim_candidates", [])
    if not isinstance(candidates, list):
        raise ValueError("Research report must contain a claim_candidates list.")

    records: list[dict[str, Any]] = []
    provider_results: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    searched = 0

    for candidate in candidates[:claim_limit]:
        if not isinstance(candidate, dict):
            continue
        claim = _query_text(candidate.get("text", ""))
        claim_id = candidate.get("candidate_id") or f"candidate-{searched + 1:04d}"
        if len(claim) < 12:
            continue
        searched += 1
        providers = (
            ("crossref", "https://api.crossref.org/works?" + urlencode({
                "query.bibliographic": claim, "rows": results_per_provider,
                "select": "DOI,title,URL,publisher,container-title,published-online,published-print,issued,author",
            }), _crossref_records),
            ("europe_pmc", "https://www.ebi.ac.uk/europepmc/webservices/rest/search?" + urlencode({
                "query": claim, "format": "json", "resultType": "lite",
                "pageSize": results_per_provider,
            }), _europe_pmc_records),
        )
        for provider, url, normalizer in providers:
            try:
                payload = fetcher(url)
                found = normalizer(payload, claim_id)
                added = 0
                for record in found:
                    identity = (provider, (record.get("doi") or record.get("pmid") or record["title"]).casefold())
                    if identity in seen:
                        continue
                    seen.add(identity)
                    records.append(record)
                    added += 1
                provider_results.append({
                    "claim_candidate_id": claim_id, "provider": provider,
                    "status": "success", "result_count": len(found), "new_lead_count": added,
                })
            except (HTTPError, URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError) as exc:
                provider_results.append({
                    "claim_candidate_id": claim_id, "provider": provider,
                    "status": "error", "error": f"{type(exc).__name__}: {exc}",
                })

    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "providers": ["Crossref REST API", "Europe PMC REST API"],
        "claim_candidates_searched": searched,
        "lead_count": len(records),
        "provider_results": provider_results,
        "leads": records,
        "publication_gate": "blocked_pending_source_review_and_human_editorial_approval",
        "notice": (
            "These are bibliographic metadata leads, not evidence passages or verified claims. "
            "Metadata provider is not necessarily the publisher. Publisher identity, source domain, "
            "full text, methods, relevance and claim support must be independently checked before "
            "a lead can enter an evidence dossier. No lead is counted as corroboration."
        ),
    }
