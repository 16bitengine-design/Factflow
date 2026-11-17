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


def test_future_or_unrelated_time_is_not_reported():
    assert unrecovered_missed_slot({}, _utc(8, 40)) is None
    assert unrecovered_missed_slot({}, _utc(11, 0)) is None


def test_naive_clock_rejected():
    with pytest.raises(ValueError):
        unrecovered_missed_slot({}, datetime(2026, 11, 16, 9, 10))
