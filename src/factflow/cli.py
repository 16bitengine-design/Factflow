"""Command-line interface for the FactFlow foundation and research tools."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from factflow.research import build_research_report, load_source_registry
from factflow.topic import TopicValidationError, load_topic


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="factflow", description="FactFlow production tools.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="Validate a topic JSON file.")
    validate_parser.add_argument("topic_file", help="Path to the topic JSON file.")

    research_parser = subparsers.add_parser(
        "research-report", help="Assess registered evidence for each topic claim."
    )
    research_parser.add_argument("topic_file", help="Path to the topic JSON file.")
    research_parser.add_argument(
        "--registry", default=None, help="Optional path to a publisher registry JSON file."
    )
    research_parser.add_argument(
        "--check-links", action="store_true",
        help="Check source URL reachability (requires outbound internet access)."
    )
    research_parser.add_argument(
        "--output", default=None, help="Optional path for the JSON report."
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    try:
        topic = load_topic(args.topic_file)
    except TopicValidationError as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 1

    if args.command == "validate":
        print(f"VALID: {topic['title']} ({topic['id']})")
        print(f"Claims: {len(topic['claims'])} | Scenes: {len(topic['scenes'])}")
        return 0

    try:
        registry = load_source_registry(args.registry) if args.registry else load_source_registry()
    except ValueError as exc:
        print(f"RESEARCH ERROR: {exc}", file=sys.stderr)
        return 1

    report = build_research_report(topic, registry, check_links=args.check_links)
    rendered = json.dumps(report, indent=2, ensure_ascii=False)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered + "\n", encoding="utf-8")
        print(f"Research report written to {output_path}")
    else:
        print(rendered)

    if any(item["status"] == "unsupported_or_unregistered" for item in report["claim_statuses"]):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
