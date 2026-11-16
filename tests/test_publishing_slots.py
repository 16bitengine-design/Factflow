from datetime import datetime, timedelta, timezone
import pytest
from factflow.publishing_slots import select_next_slot, select_immediate_slot

def _spec(path, prefix, title):
    return {"spec_path": path, "content_id_prefix": prefix, "title": title, "post_title": title,
        "post_description": "Evidence-backed description", "publish_timezone": "Africa/Kampala"}

def test_selects_noon_slot_twenty_minutes_ahead():
    now = datetime(2026, 11, 16, 8, 40, tzinfo=timezone.utc)
    result = select_next_slot({"production_specs": [_spec("a.json", "qt-a", "Topic A")]}, {}, now=now)
    assert result["slot_local"] == "2026-11-16 12:00"
    assert result["content_id"] == "qt-a-20261116-1200"
    assert result["due_at"] == "2026-11-16T12:00:00+03:00"

def test_selects_evening_slot_independently():
    now = datetime(2026, 11, 16, 14, 40, tzinfo=timezone.utc)
    result = select_next_slot({"production_specs": [_spec("a.json", "qt-a", "Topic A")]}, {}, now=now)
    assert result["slot_local"] == "2026-11-16 18:00"

def test_does_not_reuse_same_topic_twice_on_one_day():
    now = datetime(2026, 11, 16, 14, 40, tzinfo=timezone.utc)
    library = {"production_specs": [_spec("a.json", "qt-a", "A"), _spec("b.json", "qt-b", "B")]}
    ledger = {"a": {"spec": "a.json", "due_at": "2026-11-16T12:00:00+03:00"}}
    assert select_next_slot(library, ledger, now=now)["spec_path"] == "b.json"

def test_fails_when_only_used_topic_remains():
    now = datetime(2026, 11, 16, 14, 40, tzinfo=timezone.utc)
    library = {"production_specs": [_spec("a.json", "qt-a", "A")]}
    ledger = {"a": {"spec": "a.json", "due_at": "2026-11-16T12:00:00+03:00"}}
    with pytest.raises(ValueError, match="No unused eligible topic remains"):
        select_next_slot(library, ledger, now=now)

def test_topics_are_enabled_by_default_without_editorial_approval():
    now = datetime(2026, 11, 16, 8, 40, tzinfo=timezone.utc)
    spec = {**_spec("draft.json", "qt-draft", "Draft"), "editorial_approved": False}
    assert select_next_slot({"production_specs": [spec]}, {}, now=now)["spec_path"] == "draft.json"

def test_explicitly_disabled_topics_are_not_selectable():
    now = datetime(2026, 11, 16, 8, 40, tzinfo=timezone.utc)
    spec = {**_spec("disabled.json", "qt-disabled", "Disabled"), "publishing_enabled": False}
    with pytest.raises(ValueError, match="No enabled production specs"):
        select_next_slot({"production_specs": [spec]}, {}, now=now)

def test_returns_none_outside_scheduled_slot_window():
    now = datetime(2026, 11, 16, 9, 30, tzinfo=timezone.utc)
    assert select_next_slot({"production_specs": [_spec("a.json", "qt-a", "A")]}, {}, now=now) is None

def test_rejects_naive_current_time():
    with pytest.raises(ValueError, match="timezone-aware"):
        select_next_slot({"production_specs": [_spec("a.json", "qt-a", "A")]}, {},
            now=datetime(2026, 11, 16, 8, 40))

def test_does_not_select_reserved_slot():
    now = datetime(2026, 11, 16, 14, 40, tzinfo=timezone.utc)
    library = {"production_specs": [_spec("a.json", "qt-a", "A"), _spec("b.json", "qt-b", "B")]}
    ledger = {"a": {"spec": "a.json", "due_at": "2026-11-16T18:00:00+03:00"}}
    assert select_next_slot(library, ledger, now=now) is None

def test_evidence_passage_verification_still_blocks_publication():
    now = datetime(2026, 11, 16, 14, 40, tzinfo=timezone.utc)
    spec = {**_spec("moon.json", "qt-moon", "Moon"), "source_passage_verification_required_before_publication": True}
    with pytest.raises(ValueError, match="No enabled production specs"):
        select_next_slot({"production_specs": [spec]}, {}, now=now)

def test_unverified_source_lead_still_blocks_publication():
    now = datetime(2026, 11, 16, 14, 40, tzinfo=timezone.utc)
    spec = {**_spec("moon.json", "qt-moon", "Moon"),
        "sources": [{"review_status": "source_lead_requires_human_passage_check"}]}
    with pytest.raises(ValueError, match="No enabled production specs"):
        select_next_slot({"production_specs": [spec]}, {}, now=now)


def test_immediate_selection_uses_safe_future_time_and_unused_topic():
    now = datetime(2026, 11, 16, 14, 11, tzinfo=timezone.utc)
    library = {"production_specs": [
        _spec("already-used.json", "qt-used", "Used"),
        _spec("next.json", "qt-next", "Next"),
    ]}
    ledger = {"used": {"spec": "already-used.json", "due_at": "2026-11-16T12:00:00+03:00",
                       "publish_timezone": "Africa/Kampala"}}
    result = select_immediate_slot(library, ledger, now=now)
    assert result["spec_path"] == "next.json"
    assert result["due_at"] == "2026-11-16T17:31:00+03:00"
    assert result["content_id"] == "qt-next-20261116-1731"

def test_immediate_selection_keeps_evidence_safety_gate():
    now = datetime(2026, 11, 16, 14, 11, tzinfo=timezone.utc)
    blocked = {**_spec("blocked.json", "qt-blocked", "Blocked"),
               "source_passage_verification_required_before_publication": True}
    with pytest.raises(ValueError, match="No enabled production specs"):
        select_immediate_slot({"production_specs": [blocked]}, {}, now=now)

def test_immediate_selection_requires_rendering_lead_time():
    now = datetime(2026, 11, 16, 14, 11, tzinfo=timezone.utc)
    with pytest.raises(ValueError, match="at least ten minutes"):
        select_immediate_slot({"production_specs": [_spec("a.json", "qt-a", "A")]}, {},
                              now=now, lead_time=timedelta(minutes=5))

def test_next_slot_never_reuses_a_topic_published_on_a_previous_day():
    now = datetime(2026, 11, 16, 14, 40, tzinfo=timezone.utc)
    library = {"production_specs": [_spec("yesterday.json", "qt-yesterday", "Yesterday"),
                                   _spec("fresh.json", "qt-fresh", "Fresh")]}
    ledger = {"yesterday": {"spec": "yesterday.json", "due_at": "2026-11-15T18:00:00+03:00",
                            "status": "published"}}
    assert select_next_slot(library, ledger, now=now)["spec_path"] == "fresh.json"


def test_next_slot_fails_closed_when_only_previously_published_topic_remains():
    now = datetime(2026, 11, 16, 14, 40, tzinfo=timezone.utc)
    library = {"production_specs": [_spec("yesterday.json", "qt-yesterday", "Yesterday")]}
    ledger = {"yesterday": {"spec": "yesterday.json", "due_at": "2026-11-15T18:00:00+03:00",
                            "status": "published"}}
    with pytest.raises(ValueError, match="publishing history"):
        select_next_slot(library, ledger, now=now)


def test_immediate_selection_never_reuses_a_topic_from_a_previous_day():
    now = datetime(2026, 11, 16, 14, 11, tzinfo=timezone.utc)
    library = {"production_specs": [_spec("yesterday.json", "qt-yesterday", "Yesterday"),
                                   _spec("fresh.json", "qt-fresh", "Fresh")]}
    ledger = {"yesterday": {"spec": "yesterday.json", "due_at": "2026-11-15T18:00:00+03:00",
                            "status": "published", "publish_timezone": "Africa/Kampala"}}
    assert select_immediate_slot(library, ledger, now=now)["spec_path"] == "fresh.json"


def test_immediate_selection_fails_closed_when_all_topics_were_used_before():
    now = datetime(2026, 11, 16, 14, 11, tzinfo=timezone.utc)
    library = {"production_specs": [_spec("yesterday.json", "qt-yesterday", "Yesterday")]}
    ledger = {"yesterday": {"spec": "yesterday.json", "due_at": "2026-11-15T18:00:00+03:00",
                            "status": "published", "publish_timezone": "Africa/Kampala"}}
    with pytest.raises(ValueError, match="publishing history"):
        select_immediate_slot(library, ledger, now=now)
