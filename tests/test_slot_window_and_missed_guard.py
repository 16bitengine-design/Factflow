from datetime import datetime, timezone

import pytest

from factflow.publishing_slots import select_next_slot
from factflow.publishing_watchdog import unrecovered_missed_slot

LIB = {"production_specs": [{
    "spec_path": "a.json", "content_id_prefix": "qt-a", "title": "A", "post_title": "A",
    "post_description": "d", "publish_timezone": "Africa/Kampala"}]}


def _utc(h, m):
    return datetime(2026, 11, 16, h, m, tzinfo=timezone.utc)


def test_delayed_run_two_hours_early_still_selects_noon_slot():
    assert select_next_slot(LIB, {}, now=_utc(7, 10))["slot_local"] == "2026-11-16 12:00"


def test_slot_not_selectable_beyond_window():
    assert select_next_slot(LIB, {}, now=_utc(6, 0)) is None


def test_slot_too_close_for_rendering_is_not_selected():
    assert select_next_slot(LIB, {}, now=_utc(8, 50)) is None


def test_evening_slot_selectable_early():
    assert select_next_slot(LIB, {}, now=_utc(13, 10))["slot_local"] == "2026-11-16 18:00"


def test_missed_slot_without_entry_is_reported():
    due = unrecovered_missed_slot({}, _utc(9, 10))
    assert due is not None and due.hour == 12


def test_missed_slot_with_slot_entry_is_not_reported():
    ledger = {"x": {"due_at": "2026-11-16T12:00:00+03:00"}}
    assert unrecovered_missed_slot(ledger, _utc(9, 10)) is None


def test_missed_slot_with_recovery_entry_is_not_reported():
    ledger = {"x": {"due_at": "2026-11-16T12:20:00+03:00"}}
    assert unrecovered_missed_slot(ledger, _utc(9, 10)) is None


def test_future_slot_or_slot_older_than_horizon_is_not_reported():
    assert unrecovered_missed_slot({}, _utc(8, 40)) is None
    # 20:30 UTC is 23:30 local: noon is 11.5 h old and evening was covered below
    ledger = {"e": {"due_at": "2026-11-16T18:00:00+03:00"}}
    assert unrecovered_missed_slot({"x": {"due_at": "2026-11-16T12:00:00+03:00"}, **ledger}, _utc(20, 30)) is None


def test_hours_late_slot_is_still_caught_up():
    due = unrecovered_missed_slot({}, _utc(11, 0))
    assert due is not None and due.hour == 12


def test_oldest_uncovered_slot_is_reported_first():
    ledger = {"x": {"due_at": "2026-11-16T12:00:00+03:00"}}
    due = unrecovered_missed_slot(ledger, _utc(17, 0))
    assert due is not None and due.hour == 18


def test_catch_up_reservation_covers_its_slot():
    ledger = {"x": {"due_at": "2026-11-16T14:20:00+03:00", "recovers_slot": "2026-11-16 12:00"}}
    assert unrecovered_missed_slot(ledger, _utc(11, 30)) is None


def test_cancelled_catch_up_does_not_cover_its_slot():
    ledger = {"x": {"due_at": "2026-11-16T14:20:00+03:00", "recovers_slot": "2026-11-16 12:00",
        "status": "cancelled_duplicate"}}
    assert unrecovered_missed_slot(ledger, _utc(11, 30)) is not None


def test_naive_clock_rejected():
    with pytest.raises(ValueError):
        unrecovered_missed_slot({}, datetime(2026, 11, 16, 9, 10))
