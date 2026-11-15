"""Upload a rendered video to Cloudinary and save a non-publishing Buffer draft.

This module deliberately never schedules or publishes posts. It is used by the
manual GitHub Actions integration check until the editorial publishing gate is
implemented.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BUFFER_ENDPOINT = "https://api.buffer.com"


class PublishingIntegrationError(RuntimeError):
    """Raised when media hosting or Buffer draft creation fails."""


def _required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise PublishingIntegrationError(f"Required GitHub secret/environment value is missing: {name}")
    return value


def upload_video_to_cloudinary(video_path: str, public_id: str) -> str:
    """Upload a video using server-side Cloudinary credentials and return its public URL."""
    try:
        import cloudinary
        import cloudinary.uploader
    except ImportError as exc:
        raise PublishingIntegrationError(
            "Cloudinary SDK is missing; install the 'cloudinary' package."
        ) from exc

    cloudinary.config(
        cloud_name=_required_env("CLOUDINARY_CLOUD_NAME"),
        api_key=_required_env("CLOUDINARY_API_KEY"),
        api_secret=_required_env("CLOUDINARY_API_SECRET"),
        secure=True,
    )
    try:
        result = cloudinary.uploader.upload(
            video_path,
            resource_type="video",
            public_id=public_id,
            overwrite=False,
        )
    except Exception as exc:  # SDK exceptions vary by HTTP/API failure.
        raise PublishingIntegrationError(f"Cloudinary video upload failed: {exc}") from exc

    url = result.get("secure_url") if isinstance(result, dict) else None
    if not isinstance(url, str) or not url.startswith("https://res.cloudinary.com/"):
        raise PublishingIntegrationError("Cloudinary did not return a valid HTTPS delivery URL.")
    return url


def verify_public_video_url(url: str) -> None:
    """Confirm Cloudinary serves the media publicly before asking Buffer to fetch it."""
    request = Request(url, method="HEAD", headers={"User-Agent": "QuantaTale/BufferIntegrationCheck"})
    try:
        with urlopen(request, timeout=30) as response:
            content_type = response.headers.get("Content-Type", "").lower()
            if response.status != 200:
                raise PublishingIntegrationError(
                    f"Cloudinary delivery URL returned HTTP {response.status}."
                )
            if not content_type.startswith("video/"):
                raise PublishingIntegrationError(
                    f"Cloudinary URL is reachable but has unexpected content type: {content_type or 'missing'}."
                )
    except (HTTPError, URLError, TimeoutError) as exc:
        raise PublishingIntegrationError(f"Cloudinary delivery URL is not publicly reachable: {exc}") from exc


def _buffer_graphql(query: str, variables: dict[str, Any]) -> dict[str, Any]:
    payload = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    request = Request(
        BUFFER_ENDPOINT,
        data=payload,
        headers={
            "Authorization": f"Bearer {_required_env('BUFFER_API_KEY')}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=45) as response:
            data = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        # Never include request headers or credential values in error output.
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise PublishingIntegrationError(
            f"Buffer API returned HTTP {exc.code}: {detail}"
        ) from exc
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise PublishingIntegrationError(f"Buffer API request failed: {exc}") from exc

    if data.get("errors"):
        messages = "; ".join(
            str(item.get("message", "GraphQL error")) for item in data["errors"]
        )
        raise PublishingIntegrationError(f"Buffer API rejected the request: {messages}")
    return data


def create_buffer_video_draft(
    *,
    target: str,
    channel_id: str,
    video_url: str,
    title: str,
    description: str,
    category_id: str = "27",
) -> dict[str, str]:
    """Create a Buffer draft with a video asset; it cannot publish automatically."""
    if target not in {"youtube", "tiktok"}:
        raise ValueError("target must be 'youtube' or 'tiktok'")
    if not channel_id.strip():
        raise PublishingIntegrationError(f"The {target} Buffer channel ID is empty.")

    post_input: dict[str, Any] = {
        "channelId": channel_id,
        "text": description,
        "schedulingType": "automatic",
        "mode": "addToQueue",
        "saveToDraft": True,
        "assets": [{"video": {"url": video_url}}],
    }
    if target == "youtube":
        post_input["metadata"] = {
            "youtube": {
                "title": title[:100],
                "categoryId": category_id,
                "privacy": "private",
            }
        }

    query = """
    mutation CreateQuantaTaleDraft($input: CreatePostInput!) {
      createPost(input: $input) {
        ... on PostActionSuccess {
          post { id status text }
        }
        ... on MutationError {
          message
        }
      }
    }
    """
    data = _buffer_graphql(query, {"input": post_input})
    result = (data.get("data") or {}).get("createPost") or {}
    if result.get("message"):
        raise PublishingIntegrationError(f"Buffer could not create the {target} draft: {result['message']}")
    post = result.get("post")
    if not isinstance(post, dict) or not post.get("id"):
        raise PublishingIntegrationError(
            f"Buffer returned no successful {target} draft. Response: {json.dumps(result)[:500]}"
        )
    status = str(post.get("status", "")).lower()
    if status not in {"draft", "needs_approval"}:
        raise PublishingIntegrationError(
            f"Buffer returned unexpected status '{status or 'missing'}' for {target}; refusing to report success."
        )
    return {"target": target, "post_id": str(post["id"]), "status": status}


def run_integration(
    *, video_path: str, target: str, run_id: str, title: str, description: str
) -> list[dict[str, str]]:
    """Upload once, verify public access, then save a draft per selected channel."""
    if not os.path.isfile(video_path):
        raise PublishingIntegrationError(f"Rendered video does not exist: {video_path}")
    targets = ["youtube", "tiktok"] if target == "both" else [target]
    if any(item not in {"youtube", "tiktok"} for item in targets):
        raise ValueError("target must be youtube, tiktok or both")

    public_id = f"quantatale/draft-tests/{run_id}"
    video_url = upload_video_to_cloudinary(video_path, public_id)
    verify_public_video_url(video_url)

    results = []
    for platform in targets:
        secret_name = (
            "BUFFER_YOUTUBE_CHANNEL_ID" if platform == "youtube"
            else "BUFFER_TIKTOK_CHANNEL_ID"
        )
        channel_id = _required_env(secret_name)
        results.append(
            create_buffer_video_draft(
                target=platform,
                channel_id=channel_id,
                video_url=video_url,
                title=title,
                description=description,
                category_id=os.environ.get("BUFFER_YOUTUBE_CATEGORY_ID", "27"),
            )
        )
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Upload a QuantaTale sample and save Buffer drafts.")
    parser.add_argument("--video", required=True)
    parser.add_argument("--target", choices=("youtube", "tiktok", "both"), default="both")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--description", required=True)
    args = parser.parse_args()
    try:
        results = run_integration(
            video_path=args.video,
            target=args.target,
            run_id=args.run_id,
            title=args.title,
            description=args.description,
        )
    except (OSError, ValueError, PublishingIntegrationError) as exc:
        print(f"BUFFER DRAFT INTEGRATION FAILED: {exc}", file=sys.stderr)
        return 1
    print("BUFFER DRAFT INTEGRATION SUCCEEDED — NO POSTS WERE PUBLISHED")
    for result in results:
        print(f"{result['target']}: draft_id={result['post_id']} status={result['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
