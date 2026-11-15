"""Verify scheduled QuantaTale posts against Buffer's authoritative status."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .buffer_publish import PublishingIntegrationError, _buffer_graphql


def fetch_buffer_post(post_id: str) -> dict[str, Any]:
    """Retrieve one exact Buffer post by its persisted ID."""
    query = """
    query VerifyQuantaTalePost($input: PostInput!) {
      post(input: $input) {
        id status dueAt sentAt externalLink
        error { message }
      }
    }
    """
    data = _buffer_graphql(query, {"input": {"id": post_id}})
    post = (data.get("data") or {}).get("post")
    if not isinstance(post, dict) or str(post.get("id", "")) != post_id:
        raise PublishingIntegrationError(f"Buffer did not return the requested post {post_id}.")
    return post


def classify_post(post: dict[str, Any]) -> dict[str, Any]:
    """Map Buffer lifecycle states without inferring publication from elapsed time."""
    status = str(post.get("status", "")).lower()
    if status == "sent":
        outcome = "published"
    elif status == "error":
        outcome = "failed"
    elif status in {"scheduled", "buffer", "sending", "draft", "needs_approval"}:
        outcome = "awaiting_confirmation"
    else:
        outcome = "unknown"
    result: dict[str, Any] = {
        "status": outcome,
        "buffer_status": status or "missing",
        "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    for source, target in (("sentAt", "published_at"), ("externalLink", "external_link")):
        if post.get(source):
            result[target] = post[source]
    error = post.get("error")
    if isinstance(error, dict) and error.get("message"):
        result["error"] = str(error["message"])
    return result


def verify_ledger(ledger_path: Path) -> dict[str, int]:
    """Refresh each non-final platform outcome in the publishing ledger."""
    if not ledger_path.exists():
        raise FileNotFoundError(f"Publishing ledger not found: {ledger_path}")
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    counts = {"published": 0, "failed": 0, "awaiting_confirmation": 0, "unknown": 0}
    changed = False
    for content_id, entry in ledger.items():
        platforms = entry.get("buffer_posts", {})
        if not isinstance(platforms, dict):
            continue
        for platform, record in platforms.items():
            if not isinstance(record, dict) or not record.get("post_id"):
                continue
            previous = record.get("verification", {}).get("status")
            if previous in {"published", "failed"}:
                counts[previous] += 1
                continue
            post = fetch_buffer_post(str(record["post_id"]))
            outcome = classify_post(post)
            record["verification"] = outcome
            counts[outcome["status"]] += 1
            changed = True
            print(f"{content_id} {platform}: {outcome['status']} (Buffer: {outcome['buffer_status']})")
    if changed:
        ledger_path.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
    return counts


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify QuantaTale Buffer publication outcomes.")
    parser.add_argument("--ledger", default="production/publishing-ledger.json")
    args = parser.parse_args()
    try:
        counts = verify_ledger(Path(args.ledger))
    except (OSError, ValueError, PublishingIntegrationError) as exc:
        print(f"BUFFER VERIFICATION FAILED: {exc}", file=sys.stderr)
        return 1
    print("BUFFER VERIFICATION SUMMARY: " + json.dumps(counts, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
