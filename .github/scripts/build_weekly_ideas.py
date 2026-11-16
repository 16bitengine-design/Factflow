"""Build a conservative weekly Shorts idea pack from QuantaTale research outputs."""
from __future__ import annotations
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

def read_json(path: str) -> dict[str, Any]:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))

def words(value: str) -> list[str]:
    return re.findall(r"\b[\w’'-]+\b", value)

def normalize_title(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value).casefold()).strip()

def choose_ideas(report: dict[str, Any], library: dict[str, Any], limit: int = 5) -> list[dict[str, Any]]:
    # Discovery leads are the inputs to this research run, not previously produced
    # videos. Exclude only existing production specs; otherwise every newly
    # discovered article is incorrectly filtered out by its own lead title.
    existing_titles = {
        normalize_title(item.get("title", ""))
        for item in library.get("production_specs", [])
        if isinstance(item, dict)
    }
    chosen: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    seen_titles: set[str] = set()
    for item in report.get("claim_candidates", []):
        if not isinstance(item, dict):
            continue
        claim = " ".join(str(item.get("text", "")).split())
        url = str(item.get("final_url") or item.get("source_url") or "").strip()
        publisher = str(item.get("publisher_id", "")).strip()
        title = str(item.get("discovered_title") or item.get("source_title") or "").strip()
        normalized_title = normalize_title(title)
        if not (45 <= len(claim) <= 220) or not (8 <= len(words(claim)) <= 25):
            continue
        if not url or not title or url in seen_urls or normalized_title in existing_titles or normalized_title in seen_titles:
            continue
        chosen.append(item)
        seen_urls.add(url)
        seen_titles.add(normalized_title)
        if len(chosen) == limit:
            break
    return chosen

def render_idea(index: int, item: dict[str, Any]) -> str:
    title = str(item.get("discovered_title") or item.get("source_title") or "Untitled research lead").strip()
    source_title = str(item.get("source_title") or title).strip()
    publisher = str(item.get("publisher_id") or "Registered publisher")
    url = str(item.get("final_url") or item.get("source_url") or "")
    claim = " ".join(str(item.get("text", "")).split())
    hook = f"What is really happening behind this story: {title.rstrip('?.!')}?"
    narration = (
        f"{hook} The original source, {source_title}, reports: “{claim}” "
        f"That is a useful starting point, not a final verdict. In this short, we would "
        f"unpack the source's context, explain the key idea in plain language, and show "
        f"what the available evidence can—and cannot—tell us. The takeaway is simple: "
        f"follow the evidence beyond the headline."
    )
    scenes = [
        ("0–5s", "Hook", f"Reveal the question “{hook}” on a midnight-navy canvas with a restrained cyan holographic title animation."),
        ("5–15s", "Source context", f"Introduce the source title and publisher label ({publisher}); show the original article URL as a small source card."),
        ("15–30s", "Explain the idea", "Build an original 2D/3D explanatory diagram around the key nouns in the claim. Do not add measurements, causal arrows or visual details that the source does not establish."),
        ("30–45s", "Evidence and uncertainty", "Place the extracted sentence beside a clearly labelled “unreviewed source lead” marker; visually distinguish what the article says from what still needs corroboration."),
        ("45–55s", "Takeaway", "Return to the opening question, reveal one concise evidence-led takeaway after editorial review, then close with the QuantaTale identity."),
    ]
    lines = [
        f"## Idea {index}: {title}", "",
        f"**Hook:** {hook}", "",
        f"**Draft narration (about {len(words(narration))} words):**", "",
        narration, "", "**Scene-by-scene visual plan:**", "",
    ]
    for timing, label, description in scenes:
        lines.append(f"- **{timing} — {label}:** {description}")
    lines.extend([
        "", "**Extracted claim candidate (not verified):**", "",
        f"> {claim}", "",
        f"**Primary source:** [{source_title}]({url})",
        f"**Publisher registry ID:** {publisher}",
        "**Editorial status:** candidate_unreviewed — human review of the original page and independent evidence is mandatory. This idea is not approved for publication.",
        "", "---", "",
    ])
    return "\n".join(lines)

def main() -> int:
    report = read_json("build/weekly-research-candidates.json")
    library = read_json("production/topic-library.json")
    ideas = choose_ideas(report, library, limit=5)
    if len(ideas) < 5:
        raise SystemExit(
            f"Only {len(ideas)} sufficiently short, distinct, not-yet-produced source-backed candidates were found; "
            "refusing to pad the weekly pack with repeated or unsupported topics."
        )
    output = [
        "# QuantaTale — Weekly Shorts idea pack", "",
        "Five fresh research-led ideas prepared from registered publisher pages.", "",
        "> **Editorial warning:** These are unreviewed research candidates, not verified facts or publish-ready scripts. The quoted sentence is an extracted source passage. A human must inspect the original page, check context and independent evidence, and explicitly approve any production specification before publishing.", "",
        f"Research candidates examined: {report.get('claim_candidate_count', 0)}", "", "---", "",
    ]
    output.extend(render_idea(index, item) for index, item in enumerate(ideas, start=1))
    Path("build/weekly-shorts-ideas.md").write_text("\n".join(output), encoding="utf-8")
    print("Created five editorial-review idea drafts in build/weekly-shorts-ideas.md")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
