"""Tests for curated-feed topic discovery."""
from factflow.discovery import discover_candidates, parse_feed

RSS = """<?xml version="1.0"?>
<rss version="2.0"><channel><item>
<title>New discovery in space</title>
<link>https://www.nasa.gov/example-story/</link>
<description>A <b>new</b> research update.</description>
<pubDate>Fri, 13 Nov 2026 10:00:00 GMT</pubDate>
</item></channel></rss>"""

ATOM = """<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom"><entry>
<title>Earth science update</title>
<link href="https://www.usgs.gov/news/example" />
<summary>Fresh earth science information.</summary>
<updated>2026-11-14T10:00:00Z</updated>
</entry></feed>"""


def registry():
    return {"publishers": [
        {"id":"NASA","domains":["nasa.gov"],"areas":["space"],"independence_group":"NASA"},
        {"id":"USGS","domains":["usgs.gov"],"areas":["earth science"],"independence_group":"USGS"}
    ]}


def test_parse_rss_feed():
    items = parse_feed(RSS, "NASA", "https://www.nasa.gov/news-release/feed/")
    assert len(items) == 1
    assert items[0]["title"] == "New discovery in space"
    assert items[0]["description"] == "A new research update."


def test_parse_atom_feed():
    items = parse_feed(ATOM, "USGS", "https://www.usgs.gov/news/feed")
    assert items[0]["url"] == "https://www.usgs.gov/news/example"


def test_discovery_only_accepts_registered_domains_and_deduplicates():
    config = {"feeds":[
        {"publisher_id":"NASA","url":"https://www.nasa.gov/feed"},
        {"publisher_id":"USGS","url":"https://www.usgs.gov/feed"},
        {"publisher_id":"NASA","url":"https://evil.example/feed"}
    ]}
    bodies = {
        "https://www.nasa.gov/feed": RSS,
        "https://www.usgs.gov/feed": ATOM
    }
    report = discover_candidates(config, registry(), fetcher=lambda url: bodies[url])
    assert report["candidate_count"] == 2
    assert report["feed_results"][2]["status"] == "rejected_unregistered_feed"
    assert all(item["discovery_status"] == "candidate_unreviewed" for item in report["candidates"])
    assert all(item["editorial_review_required"] == "true" for item in report["candidates"])


def test_discovery_rejects_article_link_outside_publisher_domain():
    malicious = RSS.replace("https://www.nasa.gov/example-story/", "https://example.com/story")
    config = {"feeds":[{"publisher_id":"NASA","url":"https://www.nasa.gov/feed"}]}
    report = discover_candidates(config, registry(), fetcher=lambda _: malicious)
    assert report["candidate_count"] == 0
