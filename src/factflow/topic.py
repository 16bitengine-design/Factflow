"""Load and validate FactFlow topic specifications."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


REQUIRED_FIELDS = (
    "id", "title", "category", "target_duration_seconds",
    "audience", "hook", "narration", "claims", "scenes",
)


class TopicValidationError(ValueError):
    """Raised when a topic specification is incomplete or invalid."""


def _is_http_url(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def validate_topic(data: Any) -> list[str]:
    """Return structural errors; an empty list means the topic is well formed."""
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["Topic must be a JSON object."]

    for field in REQUIRED_FIELDS:
        if field not in data:
            errors.append(f"Missing required field: {field}")
    if errors:
        return errors

    topic_id = data["id"]
    if not isinstance(topic_id, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", topic_id):
        errors.append("id must use lowercase letters, numbers and single hyphens.")

    for field in ("title", "category", "audience", "hook", "narration"):
        if not isinstance(data[field], str) or not data[field].strip():
            errors.append(f"{field} must be a non-empty string.")

    duration = data["target_duration_seconds"]
    if isinstance(duration, bool) or not isinstance(duration, int) or not 10 <= duration <= 180:
        errors.append("target_duration_seconds must be an integer from 10 to 180.")

    claims = data["claims"]
    if not isinstance(claims, list) or not claims:
        errors.append("claims must be a non-empty list.")
    else:
        for index, claim in enumerate(claims):
            prefix = f"claims[{index}]"
            if not isinstance(claim, dict):
                errors.append(f"{prefix} must be an object.")
                continue
            if not isinstance(claim.get("text"), str) or not claim["text"].strip():
                errors.append(f"{prefix}.text must be a non-empty string.")
            evidence = claim.get("sources")
            if not isinstance(evidence, list) or not evidence:
                errors.append(f"{prefix}.sources must contain at least one evidence record.")
                continue
            for source_index, source in enumerate(evidence):
                source_prefix = f"{prefix}.sources[{source_index}]"
                if not isinstance(source, dict):
                    errors.append(f"{source_prefix} must be an object.")
                    continue
                for field in ("publisher_id", "url", "title", "accessed_on", "evidence_summary"):
                    if not isinstance(source.get(field), str) or not source[field].strip():
                        errors.append(f"{source_prefix}.{field} must be a non-empty string.")
                if not _is_http_url(source.get("url")):
                    errors.append(f"{source_prefix}.url must be a valid HTTP or HTTPS URL.")
                if not isinstance(source.get("supports_claim"), bool):
                    errors.append(f"{source_prefix}.supports_claim must be true or false.")

    scenes = data["scenes"]
    if not isinstance(scenes, list) or not scenes:
        errors.append("scenes must be a non-empty list.")
    else:
        for index, scene in enumerate(scenes):
            prefix = f"scenes[{index}]"
            if not isinstance(scene, dict):
                errors.append(f"{prefix} must be an object.")
                continue
            for field in ("narration_segment", "visual_description"):
                if not isinstance(scene.get(field), str) or not scene[field].strip():
                    errors.append(f"{prefix}.{field} must be a non-empty string.")
            if scene.get("visual_style") not in {"2d", "3d", "hybrid"}:
                errors.append(f"{prefix}.visual_style must be 2d, 3d or hybrid.")

    return errors


def load_topic(path: str | Path) -> dict[str, Any]:
    """Load JSON and raise a useful error for malformed input."""
    topic_path = Path(path)
    try:
        data = json.loads(topic_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise TopicValidationError(f"Topic file not found: {topic_path}") from exc
    except json.JSONDecodeError as exc:
        raise TopicValidationError(
            f"Invalid JSON in {topic_path} at line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc

    errors = validate_topic(data)
    if errors:
        raise TopicValidationError("\n".join(errors))
    return data
