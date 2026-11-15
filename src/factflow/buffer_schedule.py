"""Schedule an approved QuantaTale video through Buffer."""
from __future__ import annotations
import argparse, json, os, re, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from .buffer_publish import PublishingIntegrationError, _buffer_graphql, _required_env, upload_video_to_cloudinary, verify_public_video_url

def normalize_due_at(value: str, *, now: datetime | None = None) -> str:
    """Require an explicit timezone and a publish time at least five minutes ahead."""
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise ValueError("due_at must be ISO-8601 with an explicit timezone.") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("due_at must include a timezone offset, e.g. +03:00.")
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    if parsed.astimezone(timezone.utc) < current.astimezone(timezone.utc) + timedelta(minutes=5):
        raise ValueError("Scheduled time must be at least five minutes in the future.")
    return parsed.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

def create_buffer_scheduled_video(*, target: str, channel_id: str, video_url: str, title: str,
                                  description: str, due_at: str, category_id: str = "27") -> dict[str, str]:
    """Create one automatically-published Buffer post at an exact UTC time."""
    if target not in {"youtube", "tiktok"}:
        raise ValueError("target must be 'youtube' or 'tiktok'")
    if not channel_id.strip():
        raise PublishingIntegrationError(f"The {target} Buffer channel ID is empty.")
    post_input: dict[str, Any] = {
        "channelId": channel_id, "text": description, "schedulingType": "automatic",
        "mode": "customScheduled", "dueAt": due_at, "saveToDraft": False,
        "assets": [{"video": {"url": video_url}}],
    }
    if target == "youtube":
        post_input["metadata"] = {"youtube": {"title": title[:100], "categoryId": category_id, "privacy": "public"}}
    query = """
    mutation ScheduleQuantaTaleVideo($input: CreatePostInput!) {
      createPost(input: $input) {
        ... on PostActionSuccess { post { id status dueAt } }
        ... on MutationError { message }
      }
    }
    """
    data = _buffer_graphql(query, {"input": post_input})
    result = (data.get("data") or {}).get("createPost") or {}
    if result.get("message"):
        raise PublishingIntegrationError(f"Buffer could not schedule the {target} video: {result['message']}")
    post = result.get("post")
    if not isinstance(post, dict) or not post.get("id"):
        raise PublishingIntegrationError(f"Buffer returned no successful scheduled {target} post.")
    status = str(post.get("status", "")).lower()
    if status not in {"buffer", "scheduled"}:
        raise PublishingIntegrationError(f"Buffer returned unexpected status '{status or 'missing'}' for {target}.")
    returned_due_at = post.get("dueAt")
    if not returned_due_at:
        raise PublishingIntegrationError(f"Buffer did not return a scheduled time for the {target} post.")
    try:
        expected_time = datetime.fromisoformat(due_at.replace("Z", "+00:00")).astimezone(timezone.utc)
        actual_time = datetime.fromisoformat(str(returned_due_at).replace("Z", "+00:00")).astimezone(timezone.utc)
    except (TypeError, ValueError) as exc:
        raise PublishingIntegrationError(f"Buffer returned an invalid scheduled time for {target}.") from exc
    if actual_time != expected_time:
        raise PublishingIntegrationError(
            f"Buffer returned {returned_due_at} for {target}, not the requested time {due_at}."
        )
    return {"target": target, "post_id": str(post["id"]), "status": status, "due_at": str(returned_due_at)}

def run_scheduled_publish(*, video_path: str, target: str, content_id: str, due_at: str,
                          title: str, description: str) -> list[dict[str, str]]:
    """Upload one video and schedule it on the selected Buffer channels."""
    if not os.path.isfile(video_path):
        raise PublishingIntegrationError(f"Rendered video does not exist: {video_path}")
    if not re.fullmatch(r"[a-z0-9][a-z0-9._-]{2,63}", content_id):
        raise ValueError("content_id must be 3-64 lowercase letters, digits, dots, underscores or hyphens.")
    scheduled_at = normalize_due_at(due_at)
    targets = ["youtube", "tiktok"] if target == "both" else [target]
    if any(item not in {"youtube", "tiktok"} for item in targets):
        raise ValueError("target must be youtube, tiktok or both")
    _required_env("BUFFER_API_KEY")
    _required_env("CLOUDINARY_CLOUD_NAME")
    _required_env("CLOUDINARY_API_KEY")
    _required_env("CLOUDINARY_API_SECRET")
    channel_ids = {}
    for platform in targets:
        secret = "BUFFER_YOUTUBE_CHANNEL_ID" if platform == "youtube" else "BUFFER_TIKTOK_CHANNEL_ID"
        channel_ids[platform] = _required_env(secret)
    video_url = upload_video_to_cloudinary(video_path, f"quantatale/production/{content_id}")
    verify_public_video_url(video_url)
    results = []
    for platform in targets:
        results.append(create_buffer_scheduled_video(
            target=platform, channel_id=channel_ids[platform], video_url=video_url,
            title=title, description=description, due_at=scheduled_at,
            category_id=os.environ.get("BUFFER_YOUTUBE_CATEGORY_ID") or "27",
        ))
    return results

def main() -> int:
    parser = argparse.ArgumentParser(description="Schedule an approved QuantaTale video through Buffer.")
    parser.add_argument("--video", required=True)
    parser.add_argument("--target", choices=("youtube", "tiktok", "both"), default="both")
    parser.add_argument("--content-id", required=True)
    parser.add_argument("--due-at", required=True, help="ISO-8601 datetime including timezone offset.")
    parser.add_argument("--title", required=True)
    parser.add_argument("--description", required=True)
    parser.add_argument("--results-file", help="Write structured Buffer post IDs and scheduling results to this JSON file.")
    args = parser.parse_args()
    try:
        results = run_scheduled_publish(video_path=args.video, target=args.target, content_id=args.content_id,
                                        due_at=args.due_at, title=args.title, description=args.description)
    except (OSError, ValueError, PublishingIntegrationError) as exc:
        print(f"BUFFER SCHEDULING FAILED: {exc}", file=sys.stderr)
        return 1
    if args.results_file:
        results_path = Path(args.results_file)
        results_path.parent.mkdir(parents=True, exist_ok=True)
        results_path.write_text(json.dumps(results, indent=2) + "\\n", encoding="utf-8")
    print("BUFFER SCHEDULING SUCCEEDED")
    for result in results:
        print(f"{result['target']}: post_id={result['post_id']} status={result['status']} due_at={result['due_at']}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
