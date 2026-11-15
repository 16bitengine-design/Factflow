from datetime import datetime, timezone
import pytest
from factflow import buffer_schedule

def test_normalize_due_at_converts_offset_to_utc():
    now = datetime(2026, 11, 15, 10, 0, tzinfo=timezone.utc)
    assert buffer_schedule.normalize_due_at("2026-11-15T15:30:00+03:00", now=now) == "2026-11-15T12:30:00Z"

@pytest.mark.parametrize("value", ["2026-11-15T15:30:00", "not-a-date"])
def test_normalize_due_at_rejects_missing_timezone_or_invalid_value(value):
    with pytest.raises(ValueError):
        buffer_schedule.normalize_due_at(value, now=datetime(2026, 11, 15, 10, 0, tzinfo=timezone.utc))

def test_normalize_due_at_rejects_time_too_close():
    now = datetime(2026, 11, 15, 10, 0, tzinfo=timezone.utc)
    with pytest.raises(ValueError, match="five minutes"):
        buffer_schedule.normalize_due_at("2026-11-15T10:04:00Z", now=now)

def test_create_youtube_scheduled_post_uses_public_privacy_and_custom_time(monkeypatch):
    captured = {}
    def fake(query, variables):
        captured.update(variables["input"])
        return {"data": {"createPost": {"post": {"id": "post-123", "status": "buffer", "dueAt": "2026-11-15T12:30:00Z"}}}}
    monkeypatch.setattr(buffer_schedule, "_buffer_graphql", fake)
    result = buffer_schedule.create_buffer_scheduled_video(
        target="youtube", channel_id="yt-channel", video_url="https://res.cloudinary.com/demo/video/upload/a.mp4",
        title="Why Is the Sky Blue?", description="Explained. #Science", due_at="2026-11-15T12:30:00Z")
    assert result["post_id"] == "post-123"
    assert captured["mode"] == "customScheduled"
    assert captured["dueAt"] == "2026-11-15T12:30:00Z"
    assert captured["saveToDraft"] is False
    assert captured["metadata"]["youtube"]["privacy"] == "public"
    assert captured["assets"][0]["video"]["url"].endswith(".mp4")

def test_create_tiktok_scheduled_post_uses_video_asset(monkeypatch):
    captured = {}
    def fake(query, variables):
        captured.update(variables["input"])
        return {"data": {"createPost": {"post": {"id": "tt-123", "status": "buffer", "dueAt": "2026-11-15T12:30:00Z"}}}}
    monkeypatch.setattr(buffer_schedule, "_buffer_graphql", fake)
    result = buffer_schedule.create_buffer_scheduled_video(
        target="tiktok", channel_id="tt-channel", video_url="https://res.cloudinary.com/demo/video/upload/a.mp4",
        title="Title", description="Explained. #Science", due_at="2026-11-15T12:30:00Z")
    assert result["post_id"] == "tt-123"
    assert "metadata" not in captured
    assert captured["assets"] == [{"video": {"url": "https://res.cloudinary.com/demo/video/upload/a.mp4"}}]

def test_unexpected_buffer_status_is_not_reported_as_scheduled(monkeypatch):
    monkeypatch.setattr(buffer_schedule, "_buffer_graphql", lambda q, v: {"data": {"createPost": {"post": {
        "id": "post-123", "status": "draft", "dueAt": "2026-11-15T12:30:00Z"}}}})
    with pytest.raises(buffer_schedule.PublishingIntegrationError, match="unexpected status"):
        buffer_schedule.create_buffer_scheduled_video(
            target="tiktok", channel_id="tt-channel", video_url="https://example.com/video.mp4",
            title="Title", description="Caption", due_at="2026-11-15T12:30:00Z")

def test_run_publish_requires_all_secrets_before_upload(monkeypatch, tmp_path):
    video = tmp_path / "video.mp4"
    video.write_bytes(b"fake")
    for name in ("BUFFER_API_KEY", "BUFFER_YOUTUBE_CHANNEL_ID", "BUFFER_TIKTOK_CHANNEL_ID",
                 "CLOUDINARY_CLOUD_NAME", "CLOUDINARY_API_KEY", "CLOUDINARY_API_SECRET"):
        monkeypatch.delenv(name, raising=False)
    uploaded = []
    monkeypatch.setattr(buffer_schedule, "upload_video_to_cloudinary", lambda *a: uploaded.append(a))
    with pytest.raises(buffer_schedule.PublishingIntegrationError, match="BUFFER_API_KEY"):
        buffer_schedule.run_scheduled_publish(
            video_path=str(video), target="both", content_id="sky-blue-20261115",
            due_at="2026-11-16T15:00:00+03:00", title="Title", description="Caption")
    assert uploaded == []

def test_content_id_is_validated_before_upload(monkeypatch, tmp_path):
    video = tmp_path / "video.mp4"
    video.write_bytes(b"fake")
    monkeypatch.setattr(buffer_schedule, "upload_video_to_cloudinary", lambda *a: pytest.fail("must not upload"))
    with pytest.raises(ValueError, match="content_id"):
        buffer_schedule.run_scheduled_publish(
            video_path=str(video), target="youtube", content_id="../unsafe",
            due_at="2026-11-16T15:00:00+03:00", title="Title", description="Caption")

def test_create_post_rejects_buffer_returning_a_different_time(monkeypatch):
    monkeypatch.setattr(
        buffer_schedule, "_buffer_graphql",
        lambda query, variables: {"data": {"createPost": {"post": {
            "id": "post-456", "status": "buffer", "dueAt": "2026-11-15T13:00:00Z"
        }}}},
    )
    with pytest.raises(buffer_schedule.PublishingIntegrationError, match="not the requested time"):
        buffer_schedule.create_buffer_scheduled_video(
            target="tiktok", channel_id="tt-channel",
            video_url="https://example.com/video.mp4", title="Title",
            description="Caption", due_at="2026-11-15T12:30:00Z",
        )



def test_partial_platform_success_is_persisted_before_next_platform_fails(monkeypatch, tmp_path):
    import json
    from factflow.buffer_publish import PublishingIntegrationError

    video = tmp_path / "video.mp4"
    video.write_bytes(b"fake")
    results_path = tmp_path / "buffer-results.json"
    monkeypatch.setenv("BUFFER_API_KEY", "test-key")
    monkeypatch.setenv("BUFFER_YOUTUBE_CHANNEL_ID", "youtube-id")
    monkeypatch.setenv("BUFFER_TIKTOK_CHANNEL_ID", "tiktok-id")
    monkeypatch.setenv("CLOUDINARY_CLOUD_NAME", "demo")
    monkeypatch.setenv("CLOUDINARY_API_KEY", "cloud-key")
    monkeypatch.setenv("CLOUDINARY_API_SECRET", "cloud-secret")
    monkeypatch.setattr(buffer_schedule, "upload_video_to_cloudinary", lambda *a: "https://example.com/video.mp4")
    monkeypatch.setattr(buffer_schedule, "verify_public_video_url", lambda *a: None)
    outcomes = iter([
        {"target": "youtube", "post_id": "yt-1", "status": "buffer", "due_at": "2026-11-16T09:00:00Z"},
        PublishingIntegrationError("TikTok API unavailable"),
    ])
    def schedule_next(*args, **kwargs):
        outcome = next(outcomes)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome
    monkeypatch.setattr(buffer_schedule, "create_buffer_scheduled_video", schedule_next)

    with pytest.raises(PublishingIntegrationError, match="TikTok API unavailable"):
        buffer_schedule.run_scheduled_publish(
            video_path=str(video), target="both", content_id="qt-test-20261116-1200",
            due_at="2026-11-16T12:00:00+03:00", title="Title", description="Caption",
            results_file=results_path,
        )

    saved = json.loads(results_path.read_text(encoding="utf-8"))
    assert saved == [{
        "target": "youtube", "post_id": "yt-1", "status": "buffer",
        "due_at": "2026-11-16T09:00:00Z",
    }]
