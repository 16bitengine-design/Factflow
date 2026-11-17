"""Verify scheduled QuantaTale posts against Buffer's authoritative status."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
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


def find_posts_needing_attention(
    ledger: dict[str, Any],
    *,
    now: datetime | None = None,
    grace: timedelta = timedelta(minutes=15),
) -> list[dict[str, str]]:
    """Find failed/unknown posts and posts still unsent beyond a grace period.

    Elapsed time never changes a post to published or failed; overdue entries
    remain unconfirmed and are surfaced for operational investigation.
    """
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None or current.utcoffset() is None:
        raise ValueError("now must be timezone-aware")
    if grace < timedelta(0):
        raise ValueError("grace must not be negative")
    attention: list[dict[str, str]] = []
    for content_id, entry in ledger.items():
        platforms = entry.get("buffer_posts", {}) if isinstance(entry, dict) else {}
        if not isinstance(platforms, dict):
            continue
        for platform, record in platforms.items():
            if not isinstance(record, dict) or not record.get("post_id"):
                continue
            verification = record.get("verification", {})
            verification = verification if isinstance(verification, dict) else {}
            status = str(verification.get("status", "awaiting_confirmation"))
            reason = ""
            due_text = str(record.get("due_at") or entry.get("due_at") or "")
            if status in {"failed", "unknown"}:
                reason = f"Buffer verification status is {status}"
            elif status == "awaiting_confirmation":
                try:
                    due = datetime.fromisoformat(due_text.replace("Z", "+00:00"))
                    if due.tzinfo is None or due.utcoffset() is None:
                        raise ValueError("due_at has no timezone")
                    if due.astimezone(timezone.utc) <= current.astimezone(timezone.utc) - grace:
                        reason = f"still unconfirmed more than {int(grace.total_seconds() // 60)} minutes after due_at"
                except ValueError:
                    reason = "missing or invalid timezone-aware due_at for an unconfirmed post"
            if reason:
                attention.append({
                    "content_id": str(content_id),
                    "platform": str(platform),
                    "post_id": str(record["post_id"]),
                    "due_at": due_text,
                    "buffer_status": str(verification.get("buffer_status", record.get("buffer_status", "unknown"))),
                    "reason": reason,
                })
    return attention

# Outcomes that never change, so Buffer is not queried again. A post deleted on
# purpose is gone from Buffer and would otherwise fail every verification run.
FINAL_VERIFICATION_STATUSES = {"published", "failed", "deleted_as_duplicate"}


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
            if previous in FINAL_VERIFICATION_STATUSES:
                if previous in counts:
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
