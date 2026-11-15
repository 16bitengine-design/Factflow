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
