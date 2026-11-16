"""Pure helpers for safely detecting missing QuantaTale publishing slots."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo


def upcoming_slot(
    now: datetime,
    *,
    timezone_name: str = "Africa/Kampala",
    slot_hours: tuple[int, ...] = (12, 18),
    min_lead: timedelta = timedelta(minutes=5),
    window: timedelta = timedelta(minutes=30),
) -> datetime | None:
    """Return a local slot in its pre-publication or missed-slot recovery window.

    Future slots retain the minimum lead-time guard. A slot that has just passed
    remains recoverable for one window, allowing a later watchdog tick to recover
    a dropped cron event without retrying an old slot indefinitely.
    """
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("now must be timezone-aware")
    local_now = now.astimezone(ZoneInfo(timezone_name))
    candidates = []
    for hour in slot_hours:
        due = local_now.replace(hour=hour, minute=0, second=0, microsecond=0)
        delta = due - local_now
        if min_lead < delta <= window or -window <= delta <= timedelta(0):
            candidates.append((abs(delta.total_seconds()), due))
    if not candidates:
        return None
    return min(candidates, key=lambda item: item[0])[1]


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


def find_recovery_entry(
    ledger: dict[str, Any],
    due: datetime,
    *,
    timezone_name: str = "Africa/Kampala",
    window: timedelta = timedelta(minutes=30),
) -> tuple[str, dict[str, Any]] | None:
    """Find an immediate-recovery reservation associated with a missed slot.

    Immediate recovery schedules the actual Buffer time slightly after the
    original slot. Treat a ledger entry within the following recovery window as
    the slot's recovery so later watchdog ticks do not dispatch duplicate posts.
    """
    zone = ZoneInfo(timezone_name)
    target = due.astimezone(zone)
    latest = target + window
    for content_id, entry in ledger.items():
        if not isinstance(entry, dict) or not entry.get("due_at"):
            continue
        try:
            recorded = datetime.fromisoformat(str(entry["due_at"]).replace("Z", "+00:00"))
            if recorded.tzinfo is None or recorded.utcoffset() is None:
                continue
            local_recorded = recorded.astimezone(zone)
            if target <= local_recorded <= latest and local_recorded.date() == target.date():
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
