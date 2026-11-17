from pathlib import Path
import json
import pytest
from factflow import buffer_verify


@pytest.mark.parametrize(("status", "expected"), [
    ("sent", "published"),
    ("error", "failed"),
    ("scheduled", "awaiting_confirmation"),
    ("sending", "awaiting_confirmation"),
    ("buffer", "awaiting_confirmation"),
    ("draft", "awaiting_confirmation"),
    ("unexpected", "unknown"),
])
def test_classify_post_uses_explicit_buffer_status(status, expected):
    result = buffer_verify.classify_post({
        "id": "post-1", "status": status, "sentAt": None, "externalLink": None
    })
    assert result["status"] == expected


def test_sent_post_preserves_publication_evidence():
    result = buffer_verify.classify_post({
        "id": "post-1", "status": "sent", "sentAt": "2026-11-15T12:00:00Z",
        "externalLink": "https://youtube.com/shorts/example",
    })
    assert result["published_at"] == "2026-11-15T12:00:00Z"
    assert result["external_link"].startswith("https://")


def test_verify_ledger_persists_separate_platform_results(monkeypatch, tmp_path):
    ledger_path = tmp_path / "ledger.json"
    ledger_path.write_text(json.dumps({
        "content-1": {"buffer_posts": {
            "youtube": {"post_id": "yt-1"},
            "tiktok": {"post_id": "tt-1"},
        }}
    }))
    statuses = {"yt-1": "sent", "tt-1": "error"}
    monkeypatch.setattr(buffer_verify, "fetch_buffer_post", lambda post_id: {
        "id": post_id, "status": statuses[post_id],
        "sentAt": "2026-11-15T12:00:00Z" if statuses[post_id] == "sent" else None,
        "externalLink": None, "error": {"message": "Rejected"} if statuses[post_id] == "error" else None,
    })
    counts = buffer_verify.verify_ledger(ledger_path)
    saved = json.loads(ledger_path.read_text())
    assert saved["content-1"]["buffer_posts"]["youtube"]["verification"]["status"] == "published"
    assert saved["content-1"]["buffer_posts"]["tiktok"]["verification"]["status"] == "failed"
    assert counts["published"] == 1 and counts["failed"] == 1


def test_verify_does_not_call_buffer_again_for_final_outcomes(monkeypatch, tmp_path):
    ledger_path = tmp_path / "ledger.json"
    ledger_path.write_text(json.dumps({"content-1": {"buffer_posts": {
        "youtube": {"post_id": "yt-1", "verification": {"status": "published"}}
    }}}))
    monkeypatch.setattr(buffer_verify, "fetch_buffer_post", lambda _: pytest.fail("final post must not be fetched"))
    counts = buffer_verify.verify_ledger(ledger_path)
    assert counts["published"] == 1


def test_overdue_scheduled_post_is_flagged_but_not_claimed_failed():
    from datetime import datetime, timezone
    ledger = {"content-1": {"buffer_posts": {
        "youtube": {
            "post_id": "yt-1",
            "due_at": "2026-11-16T09:00:00Z",
            "verification": {"status": "awaiting_confirmation", "buffer_status": "scheduled"},
        }
    }}}
    result = buffer_verify.find_posts_needing_attention(
        ledger, now=datetime(2026, 11, 16, 9, 20, tzinfo=timezone.utc)
    )
    assert len(result) == 1
    assert result[0]["reason"] == "still unconfirmed more than 15 minutes after due_at"
    assert ledger["content-1"]["buffer_posts"]["youtube"]["verification"]["status"] == "awaiting_confirmation"


def test_scheduled_future_and_published_posts_do_not_raise_attention():
    from datetime import datetime, timezone
    ledger = {"content-1": {"buffer_posts": {
        "youtube": {
            "post_id": "yt-1", "due_at": "2026-11-16T10:00:00Z",
            "verification": {"status": "awaiting_confirmation", "buffer_status": "scheduled"},
        },
        "tiktok": {
            "post_id": "tt-1", "due_at": "2026-11-16T09:00:00Z",
            "verification": {"status": "published", "buffer_status": "sent"},
        },
    }}}
    assert buffer_verify.find_posts_needing_attention(
        ledger, now=datetime(2026, 11, 16, 9, 20, tzinfo=timezone.utc)
    ) == []


def test_failed_or_unknown_buffer_posts_raise_attention():
    ledger = {"content-1": {"buffer_posts": {
        "youtube": {"post_id": "yt-1", "verification": {"status": "failed"}},
        "tiktok": {"post_id": "tt-1", "verification": {"status": "unknown"}},
    }}}
    result = buffer_verify.find_posts_needing_attention(ledger)
    assert {item["platform"] for item in result} == {"youtube", "tiktok"}


def test_overdue_detection_requires_timezone_aware_clock():
    from datetime import datetime
    with pytest.raises(ValueError, match="timezone-aware"):
        buffer_verify.find_posts_needing_attention({}, now=datetime(2026, 11, 16, 9, 20))


def test_verify_skips_posts_deleted_as_duplicate(monkeypatch, tmp_path):
    ledger_path = tmp_path / "ledger.json"
    ledger_path.write_text(json.dumps({"qt-dup": {"status": "cancelled_duplicate", "buffer_posts": {
        "youtube": {"post_id": "gone", "verification": {"status": "deleted_as_duplicate"}},
    }}}), encoding="utf-8")
    monkeypatch.setattr(buffer_verify, "fetch_buffer_post", lambda _: pytest.fail("deleted post must not be fetched"))
    counts = buffer_verify.verify_ledger(ledger_path)
    assert counts == {"published": 0, "failed": 0, "awaiting_confirmation": 0, "unknown": 0}
