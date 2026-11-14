"""Bounded retrieval of Europe PMC open-access full text for human review.

Only PMCID records explicitly marked open access are retrieved. Extracted passages
remain unreviewed leads and are never treated as verified support or corroboration.
"""
from __future__ import annotations

import re
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

MAX_RESPONSE_BYTES = 2_000_000
MAX_ARTICLES = 20
MAX_PASSAGES_PER_ARTICLE = 40
MAX_PASSAGE_CHARS = 1_200
DEFAULT_TIMEOUT = 15
_USER_AGENT = "QuantaTaleResearchBot/0.3 (https://github.com/16bitengine-design/QuantaTale)"
_PMCID = re.compile(r"^PMC[0-9]+$", re.I)
_SKIP_TAGS = {"ref-list", "ref", "fig", "table-wrap", "supplementary-material", "ack", "author-notes"}


def fetch_full_text_xml(pmcid: str, timeout: int = DEFAULT_TIMEOUT) -> str:
    """Fetch an OA full-text XML document using a validated PMCID."""
    if not isinstance(pmcid, str) or not _PMCID.fullmatch(pmcid):
        raise ValueError("A valid PMCID (for example PMC123456) is required.")
    url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML"
    request = Request(url, headers={"User-Agent": _USER_AGENT, "Accept": "application/xml,text/xml"})
    with urlopen(request, timeout=timeout) as response:
        final_url = response.geturl()
        if not final_url.startswith("https://www.ebi.ac.uk/europepmc/webservices/rest/"):
            raise ValueError("Europe PMC full-text response redirected outside the approved API host.")
        raw = response.read(MAX_RESPONSE_BYTES + 1)
        if len(raw) > MAX_RESPONSE_BYTES:
            raise ValueError("Europe PMC full-text XML exceeds the 2 MB safety limit.")
    xml_text = raw.decode("utf-8", errors="replace")
    if "<!DOCTYPE" in xml_text.upper() or "<!ENTITY" in xml_text.upper():
        raise ValueError("XML document type and entity declarations are not accepted.")
    return xml_text


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def extract_full_text_passages(xml_text: str, *, limit: int = MAX_PASSAGES_PER_ARTICLE) -> list[dict[str, str]]:
    """Extract bounded abstract/body paragraphs with section labels."""
    if not 1 <= limit <= MAX_PASSAGES_PER_ARTICLE:
        raise ValueError(f"limit must be between 1 and {MAX_PASSAGES_PER_ARTICLE}.")
    if not isinstance(xml_text, str) or len(xml_text.encode("utf-8")) > MAX_RESPONSE_BYTES:
        raise ValueError("XML input is invalid or exceeds the 2 MB safety limit.")
    if "<!DOCTYPE" in xml_text.upper() or "<!ENTITY" in xml_text.upper():
        raise ValueError("XML document type and entity declarations are not accepted.")
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise ValueError(f"Invalid Europe PMC full-text XML: {exc}") from exc

    passages: list[dict[str, str]] = []
    seen: set[str] = set()

    def walk(node: ET.Element, section: str = "article") -> None:
        if len(passages) >= limit:
            return
        tag = _local_name(node.tag)
        if tag in _SKIP_TAGS:
            return
        current_section = section
        if tag == "abstract":
            current_section = "abstract"
        elif tag == "body":
            current_section = "body"
        elif tag == "sec":
            title = next((child for child in node if _local_name(child.tag) == "title"), None)
            if title is not None:
                heading = " ".join("".join(title.itertext()).split())
                if heading:
                    current_section = heading[:160]
        elif tag == "p":
            text = " ".join("".join(node.itertext()).split())
            normalized = text.casefold()
            if len(text) >= 40 and normalized not in seen:
                seen.add(normalized)
                passages.append({"section": current_section, "text": text[:MAX_PASSAGE_CHARS]})
                if len(passages) >= limit:
                    return
        for child in node:
            walk(child, current_section)
            if len(passages) >= limit:
                return

    walk(root)
    return passages


def retrieve_open_access_passages(
    scholarly_report: dict[str, Any],
    *,
    fetcher: Callable[[str], str] = fetch_full_text_xml,
    article_limit: int = MAX_ARTICLES,
    passages_per_article: int = MAX_PASSAGES_PER_ARTICLE,
) -> dict[str, Any]:
    """Retrieve passages only for explicit OA PMCID leads; retain provenance and errors."""
    if not 1 <= article_limit <= 50:
        raise ValueError("article_limit must be between 1 and 50.")
    if not 1 <= passages_per_article <= MAX_PASSAGES_PER_ARTICLE:
        raise ValueError(f"passages_per_article must be between 1 and {MAX_PASSAGES_PER_ARTICLE}.")
    leads = scholarly_report.get("leads", [])
    if not isinstance(leads, list):
        raise ValueError("Scholarly report must contain a leads list.")

    passages: list[dict[str, Any]] = []
    results: list[dict[str, Any]] = []
    seen_pmcids: set[str] = set()
    eligible_seen = 0

    for lead in leads:
        if not isinstance(lead, dict):
            continue
        pmcid = lead.get("pmcid")
        if lead.get("open_access") is not True or not isinstance(pmcid, str) or not _PMCID.fullmatch(pmcid):
            continue
        normalized_pmcid = pmcid.upper()
        if normalized_pmcid in seen_pmcids:
            continue
        seen_pmcids.add(normalized_pmcid)
        eligible_seen += 1
        if len(results) >= article_limit:
            break
        try:
            xml_text = fetcher(normalized_pmcid)
            extracted = extract_full_text_passages(xml_text, limit=passages_per_article)
            results.append({
                "pmcid": normalized_pmcid,
                "status": "retrieved" if extracted else "no_extractable_passages",
                "passage_count": len(extracted),
            })
            for index, passage in enumerate(extracted, start=1):
                passages.append({
                    "passage_id": f"{normalized_pmcid.lower()}-{index:03d}",
                    "claim_candidate_id": lead.get("claim_candidate_id"),
                    "pmcid": normalized_pmcid,
                    "title": lead.get("title"),
                    "doi": lead.get("doi"),
                    "pmid": lead.get("pmid"),
                    "journal_metadata": lead.get("journal"),
                    "publication_date": lead.get("published"),
                    "source_url": lead.get("url"),
                    "retrieval_url": f"https://www.ebi.ac.uk/europepmc/webservices/rest/{normalized_pmcid}/fullTextXML",
                    "metadata_provider": "Europe PMC",
                    "section": passage["section"],
                    "passage": passage["text"],
                    "evidence_status": "open_access_passage_unreviewed",
                    "publisher_identity_verified": False,
                    "supports_claim": None,
                    "editorial_review_required": True,
                })
        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
            results.append({
                "pmcid": normalized_pmcid,
                "status": "error",
                "error": f"{type(exc).__name__}: {exc}"[:300],
            })

    return {
        "schema_version": 1,
        "retrieved_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "eligible_open_access_articles_seen": eligible_seen,
        "article_result_count": len(results),
        "retrieved_article_count": sum(1 for item in results if item["status"] == "retrieved"),
        "passage_count": len(passages),
        "article_results": results,
        "passages": passages,
        "publication_gate": "blocked_pending_publisher_verification_and_human_editorial_review",
        "notice": (
            "Passages are extracted from Europe PMC full-text XML for records explicitly marked "
            "open access. Metadata and open-access flags are provider-supplied and do not establish "
            "publisher identity, licensing permission for redistribution, relevance, accuracy or "
            "claim support. Review the original article, license, methods and context before use. "
            "No passage is counted as corroboration or approved for narration."
        ),
    }
