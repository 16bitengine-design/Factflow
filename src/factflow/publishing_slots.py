"""Select distinct, explicitly approved topics for QuantaTale's daily slots."""
from __future__ import annotations

from datetime import datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


DEFAULT_PUBLISH_SLOTS = ("12:00", "18:00")


def is_publishable_spec(item: dict[str, Any]) -> bool:
    """Return whether a spec clears the explicit approval and evidence gates."""
    if item.get("editorial_approved") is not True or item.get("status") != "approved_ready":
        return False
    if item.get("source_passage_verification_required_before_publication") is True:
        return False
    sources = item.get("sources", [])
    if not isinstance(sources, list):
        return False
    return not any(
        isinstance(source, dict)
        and str(source.get("review_status", "")).startswith("source_lead_requires_human")
        for source in sources
    )


def _parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"Datetime must include a timezone: {value!r}")
    return parsed


def select_next_slot(
    library: dict[str, Any],
    ledger: dict[str, Any],
    *,
    now: datetime | None = None,
    slot_times: tuple[str, ...] = DEFAULT_PUBLISH_SLOTS,
    min_lead: timedelta = timedelta(minutes=5),
    max_lead: timedelta = timedelta(minutes=30),
) -> dict[str, str] | None:
    """Return the next imminent slot and an unused approved spec, or None.

    The workflow is scheduled ahead of the public slot. A spec already reserved
    for any slot on the same local calendar day cannot be reused that day.
    """
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None or current.utcoffset() is None:
        raise ValueError("now must be timezone-aware")
    current_utc = current.astimezone(timezone.utc)

    approved = [
        item for item in library.get("production_specs", [])
        if isinstance(item, dict) and is_publishable_spec(item)
    ]
    if not approved:
        raise ValueError("No explicitly editorial-approved production specs are available.")

    # A slot already present in the ledger is occupied, even if its run failed
    # after reserving it. Fail closed rather than risk scheduling duplicate posts.
    occupied_slots: set[datetime] = set()
    for entry in ledger.values():
        if not isinstance(entry, dict) or not entry.get("due_at"):
            continue
        try:
            occupied_slots.add(_parse_datetime(entry["due_at"]).astimezone(timezone.utc))
        except (TypeError, ValueError):
            continue

    # Evaluate candidate slots in each spec's configured local timezone.
    candidates: list[tuple[datetime, dict[str, Any], str]] = []
    for spec in approved:
        zone_name = spec.get("publish_timezone")
        if not zone_name:
            raise ValueError(f"Approved spec {spec.get('spec_path')} has no publish_timezone.")
        zone = ZoneInfo(zone_name)
        local_now = current_utc.astimezone(zone)
        for offset in (0, 1):
            slot_date = local_now.date() + timedelta(days=offset)
            for slot_text in slot_times:
                slot_clock = time.fromisoformat(slot_text)
                slot_local = datetime.combine(slot_date, slot_clock, tzinfo=zone)
                slot_utc = slot_local.astimezone(timezone.utc)
                lead = slot_utc - current_utc
                if min_lead < lead <= max_lead and slot_utc not in occupied_slots:
                    candidates.append((slot_utc, spec, slot_local.isoformat(timespec="seconds")))

    if not candidates:
        return None

    # All production specs for a run are expected to use the same publishing
    # timezone and slot schedule; choose the earliest imminent slot.
    candidates.sort(key=lambda item: item[0])
    slot_utc, _, _ = candidates[0]
    slot_local_date = slot_utc.date()

    # Resolve local date in the timezone belonging to the chosen slot.
    chosen_specs = [
        spec for due, spec, _ in candidates if due == slot_utc
    ]
    zone = ZoneInfo(chosen_specs[0]["publish_timezone"])
    local_slot = slot_utc.astimezone(zone)
    local_date = local_slot.date()

    used_spec_paths: set[str] = set()
    for entry in ledger.values():
        if not isinstance(entry, dict) or not entry.get("spec") or not entry.get("due_at"):
            continue
        try:
            prior_due = _parse_datetime(entry["due_at"]).astimezone(zone)
        except (TypeError, ValueError):
            continue
        if prior_due.date() == local_date:
            used_spec_paths.add(str(entry["spec"]))

    eligible = [
        spec for spec in approved
        if str(spec.get("spec_path", "")) not in used_spec_paths
        and spec in chosen_specs
    ]
    if not eligible:
        raise ValueError(
            f"No unused approved topic remains for the {local_slot:%Y-%m-%d %H:%M} "
            f"{zone.key} publishing slot. Add and approve another distinct topic."
        )

    spec = sorted(eligible, key=lambda item: str(item.get("spec_path", "")))[0]
    prefix = str(spec.get("content_id_prefix", "")).strip()
    if not prefix:
        raise ValueError(f"Approved spec {spec.get('spec_path')} has no content_id_prefix.")
    content_id = f"{prefix}-{local_slot:%Y%m%d}-{local_slot:%H%M}"
    return {
        "spec_path": str(spec["spec_path"]),
        "content_id": content_id,
        "due_at": local_slot.isoformat(timespec="seconds"),
        "post_title": str(spec.get("post_title") or spec.get("title") or ""),
        "post_description": str(spec.get("post_description") or ""),
        "publish_timezone": zone.key,
        "slot_local": local_slot.strftime("%Y-%m-%d %H:%M"),
    }
