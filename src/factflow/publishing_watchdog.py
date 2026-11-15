"""Pure helpers for safely detecting missing QuantaTale publishing slots."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo


def upcoming_slot(
    now: datetime,
    *,
    timezone_name: str = "Africa/Kampala",
    slot_hours: tuple[int, ...] = (12,  18),
    window: timedelta = timedelta(minutes=30),
) -> datetime | None:
    """Return the next local publishing slot inside the recovery window."""
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("now must be timezone-aware")
    local_now = now.astimezone(ZoneInfo(timezone_name))
    for hour in slot_hours:
        due = local_now.replace(hour=hour, minute=0, second=0, microsecond=0)
        lead = due - local_now
        if timedelta(0) < lead <= window:
            return due
    return None


def find_slot_entry(
    ledger: dict[str, Any],
    due: datetime,
    *,
    timezone_name: str = "Africa/Kampala",
) -> tuple[str, dict[str, Any]] | None:
    """Find the ledger entry for an exact publishing instant."""
    zone = ZoneInfo(timezone_name)
    target = due.astimezone(zone)
    for content_id, entry in ledger.items():
        if not isinstance(entry, dict) or not entry.get("due_at"):
            continue
        try:
            recorded = datetime.fromisoformat(str(entry["due_at"]).replace("Z", "+00:00"))
            if recorded.tzinfo is not None and recorded.astimezone(zone) == target:
                return content_id, entry
        except (TypeError, ValueError):
            continue
    return None


def slot_entry_state(entry: dict[str, Any]) -> str:
    """Classify a slot as safely scheduled or blocked/unsafe to retry."""
    posts = entry.get("buffer_posts")
    posts = posts if isinstance(posts, dict) else {}
    has_both = all(
        isinstance(posts.get(platform), dict) and posts[platform].get("post_id")
        for platform in ("youtube", "tiktok")
    )
    if entry.get("status") == "scheduled" and has_both:
        return "scheduled"
    return "blocked"
