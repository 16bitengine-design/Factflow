"""Collect candidate story leads from curated public RSS/Atom feeds.

Discovery records are leads, not verified facts. Feed descriptions are untrusted
metadata and must never be copied into narration without source review.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import socket
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from factflow.research import DEFAULT_REGISTRY, _host_matches_registry, load_source_registry

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FEEDS = PROJECT_ROOT / "data" / "discovery_feeds.json"


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def _clean_text(value: str, max_length: int = 700) -> str:
    parser = _TextExtractor()
    try:
        parser.feed(html.unescape(value or ""))
        text = " ".join(" ".join(parser.parts).split())
    except Exception:
        text = " ".join((value or "").split())
    return text[:max_length]


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def _child_text(element: ET.Element, names: set[str]) -> str:
    """Return all text nested in the first matching child element.

    RSS descriptions and Atom summaries may contain inline XML/HTML elements.
    Reading only child.text silently truncates content at the first tag.
    itertext preserves text before, inside and after those nested elements.
    """
    for child in element.iter():
        if child is element:
            continue
        if _local_name(child.tag) in names:
            value = "".join(child.itertext()).strip()
            if value:
                return value
    return ""


def parse_feed(xml_text: str, publisher_id: str, feed_url: str) -> list[dict[str, str]]:
    """Parse RSS 2.0 or Atom entries into normalized candidate records."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise ValueError(f"Feed is not valid XML: {exc}") from exc

    entries = [node for node in root.iter() if _local_name(node.tag) in {"item", "entry"}]
    results: list[dict[str, str]] = []
    for entry in entries:
        title = _child_text(entry, {"title"})
        link = ""
        for child in entry.iter():
            if _local_name(child.tag) == "link":
                href = child.attrib.get("href", "").strip()
                rel = child.attrib.get("rel", "alternate")
                if href and rel in {"alternate", ""}:
                    link = href
                    break
                if child.text and child.text.strip():
                    link = child.text.strip()
                    break
        description = _child_text(entry, {"description", "summary", "content", "encoded"})
        published = _child_text(entry, {"pubdate", "published", "updated", "date"})
        if not title or not link:
            continue
        parsed = urlparse(link)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            continue
        results.append({
            "publisher_id": publisher_id,
            "feed_url": feed_url,
            "title": _clean_text(title, 240),
            "url": link,
            "published": _clean_text(published, 80),
            "description": _clean_text(description),
        })
    return results


def load_feed_config(path: str | Path = DEFAULT_FEEDS) -> dict[str, Any]:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot load discovery feed configuration: {exc}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("feeds"), list):
        raise ValueError("Discovery feed configuration must contain a feeds list.")
    return data


def fetch_feed(url: str, timeout: int = 15) -> str:
    request = Request(url, headers={"User-Agent": "FactFlow/0.1 (+https://github.com/16bitengine-design/Factflow)", "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml"})
    with urlopen(request, timeout=timeout) as response:
        if response.status >= 400:
            raise ValueError(f"Feed returned HTTP {response.status}")
        return response.read(2_000_000).decode("utf-8", errors="replace")


def discover_candidates(
    feed_config: dict[str, Any],
    registry: dict[str, Any],
    fetcher=fetch_feed,
    limit: int = 30,
) -> dict[str, Any]:
    """Fetch curated feeds and return deduplicated, registry-aligned leads."""
    publishers = {
        item.get("id"): item
        for item in registry.get("publishers", [])
        if isinstance(item, dict) and item.get("id")
    }
    candidates: list[dict[str, str]] = []
    feed_results: list[dict[str, Any]] = []
    seen: set[str] = set()

    for feed in feed_config.get("feeds", []):
        if not isinstance(feed, dict):
            continue
        publisher_id, feed_url = feed.get("publisher_id", ""), feed.get("url", "")
        publisher = publishers.get(publisher_id)
        host = urlparse(feed_url).hostname or ""
        if not publisher or not _host_matches_registry(host, publisher.get("domains", [])):
            feed_results.append({"publisher_id": publisher_id, "feed_url": feed_url, "status": "rejected_unregistered_feed"})
            continue
        try:
            parsed = parse_feed(fetcher(feed_url), publisher_id, feed_url)
            accepted = 0
            for item in parsed:
                article_host = urlparse(item["url"]).hostname or ""
                if not _host_matches_registry(article_host, publisher.get("domains", [])):
                    continue
                key = item["url"].split("#", 1)[0]
                if key in seen:
                    continue
                seen.add(key)
                item["subject_areas"] = ", ".join(publisher.get("areas", []))
                item["discovery_status"] = "candidate_unreviewed"
                item["editorial_review_required"] = "true"
                candidates.append(item)
                accepted += 1
            feed_results.append({"publisher_id": publisher_id, "feed_url": feed_url, "status": "collected", "candidate_count": accepted})
        except (HTTPError, URLError, TimeoutError, socket.timeout, UnicodeError, ValueError) as exc:
            feed_results.append({"publisher_id": publisher_id, "feed_url": feed_url, "status": "feed_error", "error": str(exc)[:300]})

    candidates.sort(key=lambda item: (item["publisher_id"], item["title"].casefold()))
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "candidate_count": min(len(candidates), max(1, limit)),
        "candidates": candidates[:max(1, limit)],
        "feed_results": feed_results,
        "notice": "Discovery leads only. A feed listing is not evidence that its headline or description is accurate. Open the original source, inspect its context, extract specific claims and obtain independent evidence before publication.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Discover candidate topics from curated public feeds.")
    parser.add_argument("--feeds", default=str(DEFAULT_FEEDS))
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY))
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--output", default="build/discovery-candidates.json")
    args = parser.parse_args()
    if args.limit < 1 or args.limit > 200:
        parser.error("--limit must be between 1 and 200")
    try:
        config = load_feed_config(args.feeds)
        registry = load_source_registry(args.registry)
        report = discover_candidates(config, registry, limit=args.limit)
    except ValueError as exc:
        parser.exit(1, f"DISCOVERY ERROR: {exc}\n")
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Discovered {report['candidate_count']} candidate leads; report: {output}")
    for result in report["feed_results"]:
        print(f"- {result['publisher_id']}: {result['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
