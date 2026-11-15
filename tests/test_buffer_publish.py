"""Tests for the safe Buffer draft integration."""
import os
from unittest.mock import patch

import pytest

from factflow.buffer_publish import (
    PublishingIntegrationError,
    create_buffer_video_draft,
    run_integration,
)


def test_youtube_draft_sets_private_privacy_and_save_to_draft():
    captured = {}

    def fake_graphql(query, variables):
        captured.update(variables["input"])
        return {"data": {"createPost": {"post": {"id": "post-123", "status": "draft"}}}}

    with patch("factflow.buffer_publish._buffer_graphql", side_effect=fake_graphql):
        result = create_buffer_video_draft(
            target="youtube",
            channel_id="youtube-channel",
            video_url="https://res.cloudinary.com/demo/video/upload/sample.mp4",
            title="Science sample",
            description="A sample description",
        )

    assert result == {"target": "youtube", "post_id": "post-123", "status": "draft"}
    assert captured["saveToDraft"] is True
    assert captured["metadata"]["youtube"] == {
        "title": "Science sample", "categoryId": "27", "privacy": "private"
    }
    assert captured["assets"][0]["video"]["url"].startswith("https://")


def test_tiktok_draft_uses_video_asset_and_draft_flag():
    captured = {}

    def fake_graphql(query, variables):
        captured.update(variables["input"])
        return {"data": {"createPost": {"post": {"id": "post-456", "status": "draft"}}}}

    with patch("factflow.buffer_publish._buffer_graphql", side_effect=fake_graphql):
        result = create_buffer_video_draft(
            target="tiktok", channel_id="tiktok-channel",
            video_url="https://res.cloudinary.com/demo/video/upload/sample.mp4",
            title="Science sample", description="A sample description",
        )

    assert result["status"] == "draft"
    assert captured["saveToDraft"] is True
    assert "metadata" not in captured


def test_rejects_unexpected_status_instead_of_claiming_success():
    with patch("factflow.buffer_publish._buffer_graphql", return_value={
        "data": {"createPost": {"post": {"id": "post-789", "status": "scheduled"}}}
    }):
        with pytest.raises(PublishingIntegrationError, match="unexpected status"):
            create_buffer_video_draft(
                target="tiktok", channel_id="channel",
                video_url="https://res.cloudinary.com/demo/video/upload/sample.mp4",
                title="Title", description="Description",
            )


def test_run_integration_uploads_once_and_creates_both_drafts(tmp_path):
    video = tmp_path / "sample.mp4"
    video.write_bytes(b"fake video")
    env = {
        "BUFFER_YOUTUBE_CHANNEL_ID": "youtube-id",
        "BUFFER_TIKTOK_CHANNEL_ID": "tiktok-id",
        "BUFFER_API_KEY": "test-api-key",
        "CLOUDINARY_CLOUD_NAME": "demo",
        "CLOUDINARY_API_KEY": "test-cloudinary-key",
        "CLOUDINARY_API_SECRET": "test-cloudinary-secret",
    }
    with patch.dict(os.environ, env, clear=False), \
         patch("factflow.buffer_publish.upload_video_to_cloudinary",
               return_value="https://res.cloudinary.com/demo/video/upload/sample.mp4") as upload, \
         patch("factflow.buffer_publish.verify_public_video_url") as verify, \
         patch("factflow.buffer_publish.create_buffer_video_draft",
               side_effect=[
                   {"target": "youtube", "post_id": "y1", "status": "draft"},
                   {"target": "tiktok", "post_id": "t1", "status": "draft"},
               ]) as create:
        results = run_integration(
            video_path=str(video), target="both", run_id="123",
            title="Title", description="Description",
        )

    assert [item["target"] for item in results] == ["youtube", "tiktok"]
    upload.assert_called_once()
    verify.assert_called_once()
    assert create.call_count == 2


def test_missing_channel_secret_fails_closed(tmp_path):
    video = tmp_path / "sample.mp4"
    video.write_bytes(b"fake video")
    env = {
        "BUFFER_API_KEY": "test-api-key",
        "BUFFER_TIKTOK_CHANNEL_ID": "",
        "CLOUDINARY_CLOUD_NAME": "demo",
        "CLOUDINARY_API_KEY": "test-cloudinary-key",
        "CLOUDINARY_API_SECRET": "test-cloudinary-secret",
    }
    with patch.dict(os.environ, env, clear=False), \
         patch("factflow.buffer_publish.upload_video_to_cloudinary",
               return_value="https://res.cloudinary.com/demo/video/upload/sample.mp4") as upload, \
         patch("factflow.buffer_publish.verify_public_video_url"), \
         patch("factflow.buffer_publish.create_buffer_video_draft") as create:
        with pytest.raises(PublishingIntegrationError, match="BUFFER_YOUTUBE_CHANNEL_ID"):
            run_integration(
                video_path=str(video), target="both", run_id="123",
                title="Title", description="Description",
            )
        create.assert_not_called()
        upload.assert_not_called()
