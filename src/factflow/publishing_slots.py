"""Select distinct topics for QuantaTale's daily publishing slots."""
from __future__ import annotations
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo
from typing import Any

DEFAULT_PUBLISH_SLOTS = ("12:00", "18:00")

def is_publishable_spec(item: dict[str, Any]) -> bool:
    """Check default topic enablement and retain independent evidence safeguards."""
    if item.get("publishing_enabled") is False:
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

def select_next_slot(library: dict[str, Any], ledger: dict[str, Any], *,
    now: datetime | None = None, slot_times: tuple[str, ...] = DEFAULT_PUBLISH_SLOTS,
    min_lead: timedelta = timedelta(minutes=5), max_lead: timedelta = timedelta(minutes=30)
) -> dict[str, str] | None:
    """Return the next imminent slot and an unused enabled spec, or None.

    Specs are enabled by default unless explicitly disabled. Evidence checks
    remain mandatory. A spec cannot be reused twice on one local calendar day.
    """
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None or current.utcoffset() is None:
        raise ValueError("now must be timezone-aware")
    current_utc = current.astimezone(timezone.utc)
    eligible_specs = [item for item in library.get("production_specs", [])
        if isinstance(item, dict) and is_publishable_spec(item)]
    if not eligible_specs:
        raise ValueError("No enabled production specs clear the evidence safety gates.")
    occupied_slots: set[datetime] = set()
    for entry in ledger.values():
        if not isinstance(entry, dict) or not entry.get("due_at"):
            continue
        try:
            occupied_slots.add(_parse_datetime(entry["due_at"]).astimezone(timezone.utc))
        except (TypeError, ValueError):
            continue
    candidates: list[tuple[datetime, dict[str, Any]]] = []
    for spec in eligible_specs:
        zone_name = spec.get("publish_timezone")
        if not zone_name:
            raise ValueError(f"Eligible spec {spec.get('spec_path')} has no publish_timezone.")
        zone = ZoneInfo(zone_name)
        local_now = current_utc.astimezone(zone)
        for offset in (0, 1):
            slot_date = local_now.date() + timedelta(days=offset)
            for slot_text in slot_times:
                local_slot = datetime.combine(slot_date, time.fromisoformat(slot_text), tzinfo=zone)
                slot_utc = local_slot.astimezone(timezone.utc)
                lead = slot_utc - current_utc
                if min_lead < lead <= max_lead and slot_utc not in occupied_slots:
                    candidates.append((slot_utc, spec))
    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0])
    slot_utc = candidates[0][0]
    chosen_specs = [spec for due, spec in candidates if due == slot_utc]
    zone = ZoneInfo(chosen_specs[0]["publish_timezone"])
    local_slot = slot_utc.astimezone(zone)
    used_spec_paths: set[str] = set()
    for entry in ledger.values():
        if not isinstance(entry, dict) or not entry.get("spec") or not entry.get("due_at"):
            continue
        try:
            prior_due = _parse_datetime(entry["due_at"]).astimezone(zone)
        except (TypeError, ValueError):
            continue
        if prior_due.date() == local_slot.date():
            used_spec_paths.add(str(entry["spec"]))
    unused = [spec for spec in chosen_specs if str(spec.get("spec_path", "")) not in used_spec_paths]
    if not unused:
        raise ValueError(f"No unused eligible topic remains for the {local_slot:%Y-%m-%d %H:%M} {zone.key} publishing slot.")
    spec = sorted(unused, key=lambda item: str(item.get("spec_path", "")))[0]
    prefix = str(spec.get("content_id_prefix", "")).strip()
    if not prefix:
        raise ValueError(f"Eligible spec {spec.get('spec_path')} has no content_id_prefix.")
    return {
        "spec_path": str(spec["spec_path"]),
        "content_id": f"{prefix}-{local_slot:%Y%m%d}-{local_slot:%H%M}",
        "due_at": local_slot.isoformat(timespec="seconds"),
        "post_title": str(spec.get("post_title") or spec.get("title") or ""),
        "post_description": str(spec.get("post_description") or ""),
        "publish_timezone": zone.key,
        "slot_local": local_slot.strftime("%Y-%m-%d %H:%M"),
    }
