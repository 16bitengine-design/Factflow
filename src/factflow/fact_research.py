"""Retrieve registered publisher pages and extract reviewable claim candidates.

This module performs deterministic extraction only. It does not determine whether
a sentence is true, whether the page supports it, or whether sources are independent.
"""
from __future__ import annotations

import argparse
import json
import re
import socket
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

from factflow.discovery import DEFAULT_FEEDS, load_feed_config
from factflow.research import DEFAULT_REGISTRY, _host_matches_registry, load_source_registry

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MAX_PAGE_BYTES = 2_000_000
DEFAULT_TIMEOUT = 15
DEFAULT_CANDIDATES_PER_SOURCE = 12
_MIN_SENTENCE_LENGTH = 45
_MAX_SENTENCE_LENGTH = 420
_SENTENCE_SPLIT = re.compile(r"""(?<=[.!?])\s+(?=[A-Z0-9“"'])""")


class _ArticleParser(HTMLParser):
    """Extract page title and paragraph text while ignoring executable markup."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_parts: list[str] = []
        self.paragraphs: list[str] = []
        self._title_depth = 0
        self._paragraph_depth = 0
        self._skip_depth = 0
        self._parts: list[str] = []
        self._paragraphs_in_content: list[str] = []
        self._content_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_map = dict(attrs)
        if tag in {"script", "style", "noscript", "svg", "form"}:
            self._skip_depth += 1
        if tag == "title":
            self._title_depth += 1
        if tag in {"article", "main"}:
            self._content_depth += 1
        if tag == "p" and self._skip_depth == 0:
            self._paragraph_depth += 1
            self._parts = []

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript", "svg", "form"} and self._skip_depth:
            self._skip_depth -= 1
        if tag == "title" and self._title_depth:
            self._title_depth -= 1
        if tag in {"article", "main"} and self._content_depth:
            self._content_depth -= 1
        if tag == "p" and self._paragraph_depth:
            value = " ".join(" ".join(self._parts).split())
            if value:
                self.paragraphs.append(value)
                if self._content_depth:
                    self._paragraphs_in_content.append(value)
            self._paragraph_depth -= 1
            self._parts = []

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        if self._title_depth:
            self.title_parts.append(data)
        if self._paragraph_depth:
            self._parts.append(data)

    def result(self) -> tuple[str, list[str]]:
        title = " ".join(" ".join(self.title_parts).split())
        paragraphs = self._paragraphs_in_content or self.paragraphs
        return title, paragraphs


class _SafeRedirectHandler(HTTPRedirectHandler):
    """Reject redirects outside the publisher's registered domain set."""

    def __init__(self, allowed_domains: list[str]) -> None:
        super().__init__()
        self.allowed_domains = allowed_domains

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        target = urlparse(urljoin(req.full_url, newurl))
        if target.scheme not in {"http", "https"} or not _host_matches_registry(
            target.hostname or "", self.allowed_domains
        ):
            raise ValueError("Redirect target is outside the publisher's registered domains.")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _publisher_for_url(url: str, registry: dict[str, Any]) -> dict[str, Any] | None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
        return None
    for publisher in registry.get("publishers", []):
        if isinstance(publisher, dict) and _host_matches_registry(
            parsed.hostname, publisher.get("domains", [])
        ):
            return publisher
    return None


def fetch_article(url: str, publisher: dict[str, Any], timeout: int = DEFAULT_TIMEOUT) -> dict[str, Any]:
    """Fetch a bounded HTML page; redirects must remain on registered publisher domains."""
    allowed_domains = publisher.get("domains", [])
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or not _host_matches_registry(
        parsed.hostname, allowed_domains
    ):
        raise ValueError("Article URL is not on the publisher's registered domains.")

    request = Request(
        url,
        headers={
            "User-Agent": "QuantaTaleResearchBot/0.1 (+https://github.com/16bitengine-design/Factflow)",
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    opener = build_opener(_SafeRedirectHandler(allowed_domains))
    with opener.open(request, timeout=timeout) as response:
        final_url = response.geturl()
        final_host = urlparse(final_url).hostname or ""
        if not _host_matches_registry(final_host, allowed_domains):
            raise ValueError("Final article URL is outside the publisher's registered domains.")
        content_type = response.headers.get("Content-Type", "").lower()
        if content_type and "html" not in content_type and "text/" not in content_type:
            raise ValueError(f"Unsupported article content type: {content_type}")
        raw = response.read(MAX_PAGE_BYTES + 1)
        if len(raw) > MAX_PAGE_BYTES:
            raise ValueError(f"Article page exceeds the {MAX_PAGE_BYTES}-byte safety limit.")
        charset = response.headers.get_content_charset() or "utf-8"
        return {
            "final_url": final_url,
            "html": raw.decode(charset, errors="replace"),
            "content_type": content_type,
        }


def extract_claim_candidates(
    html_text: str, *, max_candidates: int = DEFAULT_CANDIDATES_PER_SOURCE
) -> dict[str, Any]:
    """Extract sentence-shaped candidates with their original paragraph context."""
    if max_candidates < 1 or max_candidates > 50:
        raise ValueError("max_candidates must be between 1 and 50.")
    parser = _ArticleParser()
    parser.feed(html_text)
    title, paragraphs = parser.result()
    candidates: list[dict[str, str]] = []
    seen: set[str] = set()
    for paragraph in paragraphs:
        for sentence in _SENTENCE_SPLIT.split(paragraph):
            sentence = " ".join(sentence.split()).strip(" \t\r\n-•")
            normalized = sentence.casefold()
            if not (_MIN_SENTENCE_LENGTH <= len(sentence) <= _MAX_SENTENCE_LENGTH):
                continue
            if normalized in seen or not re.search(r"\b(is|are|was|were|has|have|can|may|causes?|increases?|decreases?|contains?|occurs?|means?|known as)\b", normalized):
                continue
            if normalized.startswith(("read more", "subscribe", "share this", "cookie")):
                continue
            seen.add(normalized)
            candidates.append({"text": sentence, "source_passage": paragraph})
            if len(candidates) >= max_candidates:
                return {"page_title": title, "claim_candidates": candidates}
    return {"page_title": title, "claim_candidates": candidates}


def research_discovery_candidates(
    discovery_report: dict[str, Any],
    registry: dict[str, Any],
    fetcher=fetch_article,
    *,
    limit: int = 10,
    max_candidates_per_source: int = DEFAULT_CANDIDATES_PER_SOURCE,
) -> dict[str, Any]:
    """Fetch candidate articles and produce traceable, unreviewed claim candidates."""
    if limit < 1 or limit > 50:
        raise ValueError("limit must be between 1 and 50.")
    publishers = {
        item.get("id"): item for item in registry.get("publishers", [])
        if isinstance(item, dict) and item.get("id")
    }
    results: list[dict[str, Any]] = []
    source_results: list[dict[str, Any]] = []
    for candidate in discovery_report.get("candidates", [])[:limit]:
        publisher_id = candidate.get("publisher_id", "")
        publisher = publishers.get(publisher_id)
        url = candidate.get("url", "")
        matched = _publisher_for_url(url, registry)
        if not publisher or not matched or matched.get("id") != publisher_id:
            source_results.append({
                "url": url, "publisher_id": publisher_id,
                "status": "rejected_unregistered_source",
                "error": "Candidate URL does not match its registered publisher.",
            })
            continue
        try:
            page = fetcher(url, publisher)
            extracted = extract_claim_candidates(
                page["html"], max_candidates=max_candidates_per_source
            )
            source_results.append({
                "url": url, "final_url": page["final_url"],
                "publisher_id": publisher_id, "status": "collected",
                "claim_candidate_count": len(extracted["claim_candidates"]),
            })
            for index, item in enumerate(extracted["claim_candidates"], start=1):
                results.append({
                    "candidate_id": f"{publisher_id.lower()}-{len(results) + 1:04d}",
                    "text": item["text"],
                    "source_passage": item["source_passage"],
                    "publisher_id": publisher_id,
                    "source_url": url,
                    "final_url": page["final_url"],
                    "source_title": extracted["page_title"] or candidate.get("title", ""),
                    "discovered_title": candidate.get("title", ""),
                    "extracted_at": datetime.now(timezone.utc).isoformat(),
                    "status": "candidate_unreviewed",
                    "supports_claim": None,
                    "editorial_review_required": True,
                })
        except (HTTPError, URLError, TimeoutError, socket.timeout, UnicodeError, ValueError, OSError) as exc:
            source_results.append({
                "url": url, "publisher_id": publisher_id,
                "status": "source_error", "error": str(exc)[:300],
            })

    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_count": len(source_results),
        "claim_candidate_count": len(results),
        "source_results": source_results,
        "claim_candidates": results,
        "notice": (
            "These are automatically extracted sentence candidates, not verified claims. "
            "The source passage and URL are retained for review. No candidate is considered "
            "supported, corroborated, accurate or approved for narration until a human "
            "checks the original page and records evidence."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract reviewable claim candidates from discovered articles.")
    parser.add_argument("discovery_report", help="Stage 3 discovery-candidates JSON file.")
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY))
    parser.add_argument("--limit", type=int, default=10, help="Maximum article pages to retrieve (1-50).")
    parser.add_argument("--max-candidates-per-source", type=int, default=DEFAULT_CANDIDATES_PER_SOURCE)
    parser.add_argument("--output", default="build/research-candidates.json")
    args = parser.parse_args()
    try:
        if not 1 <= args.limit <= 50:
            raise ValueError("--limit must be between 1 and 50.")
        discovery = json.loads(Path(args.discovery_report).read_text(encoding="utf-8"))
        registry = load_source_registry(args.registry)
        report = research_discovery_candidates(
            discovery, registry, limit=args.limit,
            max_candidates_per_source=args.max_candidates_per_source,
        )
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        parser.exit(1, f"RESEARCH ERROR: {exc}\n")
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Extracted {report['claim_candidate_count']} unreviewed claim candidates from {report['source_count']} sources.")
    print(f"Research candidate report: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
