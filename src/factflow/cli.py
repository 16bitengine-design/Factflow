"""Command-line interface for FactFlow."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from factflow.discovery import discover_candidates, load_feed_config
from factflow.fact_research import research_discovery_candidates
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
    research_parser.add_argument("--registry", default=None, help="Optional publisher registry JSON.")
    research_parser.add_argument("--check-links", action="store_true", help="Check source URL reachability.")
    research_parser.add_argument("--output", default=None, help="Optional path for the JSON report.")

    discover_parser = subparsers.add_parser(
        "discover", help="Collect candidate story leads from curated public RSS/Atom feeds."
    )
    discover_parser.add_argument("--feeds", default=None, help="Optional discovery feed configuration.")
    discover_parser.add_argument("--registry", default=None, help="Optional publisher registry JSON.")
    discover_parser.add_argument("--limit", type=int, default=30, help="Maximum candidate leads (1-200).")
    discover_parser.add_argument("--output", default="build/discovery-candidates.json", help="JSON output path.")

    candidates_parser = subparsers.add_parser("research-candidates", help="Fetch discovered articles and extract unreviewed claim candidates.")
    candidates_parser.add_argument("discovery_report", help="Stage 3 discovery-candidates JSON file.")
    candidates_parser.add_argument("--registry", default=None, help="Optional publisher registry JSON.")
    candidates_parser.add_argument("--limit", type=int, default=10, help="Maximum article pages to retrieve (1-50).")
    candidates_parser.add_argument("--max-candidates-per-source", type=int, default=12)
    candidates_parser.add_argument("--output", default="build/research-candidates.json", help="JSON output path.")
    return parser


def main() -> int:
    args = build_parser().parse_args()

    if args.command == "research-candidates":
        if not 1 <= args.limit <= 50:
            print("RESEARCH ERROR: --limit must be between 1 and 50.", file=sys.stderr)
            return 1
        try:
            discovery = json.loads(Path(args.discovery_report).read_text(encoding="utf-8"))
            registry = load_source_registry(args.registry) if args.registry else load_source_registry()
            report = research_discovery_candidates(
                discovery, registry, limit=args.limit,
                max_candidates_per_source=args.max_candidates_per_source,
            )
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            print(f"RESEARCH ERROR: {exc}", file=sys.stderr)
            return 1
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Extracted {report['claim_candidate_count']} unreviewed claim candidates from {report['source_count']} sources.")
        print(f"Research candidate report: {output_path}")
        return 0
    if args.command == "discover":
        if not 1 <= args.limit <= 200:
            print("DISCOVERY ERROR: --limit must be between 1 and 200.", file=sys.stderr)
            return 1
        try:
            config = load_feed_config(args.feeds) if args.feeds else load_feed_config()
            registry = load_source_registry(args.registry) if args.registry else load_source_registry()
            report = discover_candidates(config, registry, limit=args.limit)
        except ValueError as exc:
            print(f"DISCOVERY ERROR: {exc}", file=sys.stderr)
            return 1
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Discovered {report['candidate_count']} candidate leads; report: {output_path}")
        for result in report["feed_results"]:
            print(f"- {result['publisher_id']}: {result['status']}")
        return 0

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
