from datetime import datetime, timedelta, timezone

import pytest

from factflow.publishing_slots import select_next_slot


def _spec(path, prefix, title):
    return {
        "spec_path": path,
        "content_id_prefix": prefix,
        "title": title,
        "post_title": title,
        "post_description": "Evidence-backed description",
        "publish_timezone": "Africa/Kampala",
        "editorial_approved": True,
        "status": "approved_ready",
    }


def test_selects_noon_slot_twenty_minutes_ahead():
    now = datetime(2026, 11, 16, 8, 40, tzinfo=timezone.utc)
    library = {"production_specs": [_spec("a.json", "qt-a", "Topic A")]}
    result = select_next_slot(library, {}, now=now)
    assert result["slot_local"] == "2026-11-16 12:00"
    assert result["content_id"] == "qt-a-20261116-1200"
    assert result["due_at"] == "2026-11-16T12:00:00+03:00"


def test_selects_evening_slot_independently():
    now = datetime(2026, 11, 16, 14, 40, tzinfo=timezone.utc)
    library = {"production_specs": [_spec("a.json", "qt-a", "Topic A")]}
    result = select_next_slot(library, {}, now=now)
    assert result["slot_local"] == "2026-11-16 18:00"
    assert result["content_id"] == "qt-a-20261116-1800"


def test_does_not_reuse_same_topic_twice_on_one_day():
    now = datetime(2026, 11, 16, 14, 40, tzinfo=timezone.utc)
    library = {"production_specs": [
        _spec("a.json", "qt-a", "Topic A"),
        _spec("b.json", "qt-b", "Topic B"),
    ]}
    ledger = {
        "qt-a-20261116-1200": {
            "spec": "a.json",
            "due_at": "2026-11-16T12:00:00+03:00",
            "status": "scheduled",
        }
    }
    result = select_next_slot(library, ledger, now=now)
    assert result["spec_path"] == "b.json"


def test_fails_loudly_when_only_used_topic_remains():
    now = datetime(2026, 11, 16, 14, 40, tzinfo=timezone.utc)
    library = {"production_specs": [_spec("a.json", "qt-a", "Topic A")]}
    ledger = {
        "qt-a-20261116-1200": {
            "spec": "a.json",
            "due_at": "2026-11-16T12:00:00+03:00",
            "status": "scheduled",
        }
    }
    with pytest.raises(ValueError, match="No unused approved topic remains"):
        select_next_slot(library, ledger, now=now)


def test_unapproved_discovery_leads_are_never_selectable():
    now = datetime(2026, 11, 16, 8, 40, tzinfo=timezone.utc)
    library = {
        "production_specs": [{
            **_spec("draft.json", "qt-draft", "Draft"),
            "editorial_approved": False,
            "status": "awaiting_editorial_review",
        }]
    }
    with pytest.raises(ValueError, match="No explicitly editorial-approved"):
        select_next_slot(library, {}, now=now)


def test_returns_none_outside_scheduled_slot_window():
    now = datetime(2026, 11, 16, 9, 30, tzinfo=timezone.utc)
    library = {"production_specs": [_spec("a.json", "qt-a", "Topic A")]}
    assert select_next_slot(library, {}, now=now) is None


def test_rejects_naive_current_time():
    library = {"production_specs": [_spec("a.json", "qt-a", "Topic A")]}
    with pytest.raises(ValueError, match="timezone-aware"):
        select_next_slot(library, {}, now=datetime(2026, 11, 16, 8, 40))
