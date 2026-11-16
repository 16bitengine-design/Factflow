from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from factflow.publishing_watchdog import find_slot_entry, slot_entry_state, upcoming_slot


def test_detects_noon_slot_inside_recovery_window():
    now = datetime(2026, 11, 16, 8, 35, tzinfo=timezone.utc)
    assert upcoming_slot(now) == datetime(2026, 11, 16, 12, 0, tzinfo=ZoneInfo("Africa/Kampala"))


def test_ignores_slots_outside_recovery_window():
    now = datetime(2026, 11, 16, 8, 20, tzinfo=timezone.utc)
    assert upcoming_slot(now) is None


def test_recovers_recently_missed_noon_slot():
    now = datetime(2026, 11, 16, 9, 10, tzinfo=timezone.utc)
    assert upcoming_slot(now) == datetime(2026, 11, 16, 12, 0, tzinfo=ZoneInfo("Africa/Kampala"))


def test_does_not_recover_a_slot_older_than_thirty_minutes():
    now = datetime(2026, 11, 16, 9, 31, tzinfo=timezone.utc)
    assert upcoming_slot(now) is None


def test_rejects_naive_watchdog_clock():
    with pytest.raises(ValueError, match="timezone-aware"):
        upcoming_slot(datetime(2026, 11, 16, 8, 35))


def test_finds_ledger_entry_by_exact_slot_in_kampala_time():
    due = datetime(2026, 11, 16, 18, 0, tzinfo=ZoneInfo("Africa/Kampala"))
    ledger = {
        "qt-evening": {
            "due_at": "2026-11-16T15:00:00Z",
            "status": "reserved",
        }
    }
    assert find_slot_entry(ledger, due)[0] == "qt-evening"


def test_missing_slot_entry_is_not_found():
    due = datetime(2026, 11, 16, 12, 0, tzinfo=ZoneInfo("Africa/Kampala"))
    assert find_slot_entry({}, due) is None


def test_slot_is_healthy_only_with_both_buffer_post_ids():
    entry = {
        "status": "scheduled",
        "buffer_posts": {
            "youtube": {"post_id": "yt-1"},
            "tiktok": {"post_id": "tt-1"},
        },
    }
    assert slot_entry_state(entry) == "scheduled"


@pytest.mark.parametrize("entry", [
    {"status": "reserved"},
    {"status": "scheduled", "buffer_posts": {"youtube": {"post_id": "yt-1"}}},
    {"status": "scheduled", "buffer_posts": {}},
])
def test_incomplete_slot_is_blocked_from_automatic_redispatch(entry):
    assert slot_entry_state(entry) == "blocked"


def test_ignores_exact_five_minute_boundary_used_by_selector():
    now = datetime(2026, 11, 16, 8, 55, tzinfo=timezone.utc)
    assert upcoming_slot(now) is None
