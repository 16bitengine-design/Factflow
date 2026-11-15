"""Command-line interface for QuantaTale."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from factflow.discovery import discover_candidates, load_feed_config
from factflow.evidence_dossier import build_evidence_dossier
from factflow.evidence_comparison import compare_evidence
from factflow.fact_research import research_discovery_candidates
from factflow.research import build_research_report, load_source_registry
from factflow.scholarly_discovery import discover_scholarly_metadata
from factflow.scholarly_fulltext import retrieve_open_access_passages
from factflow.topic import TopicValidationError, load_topic
from factflow.topic_library import add_discovery_report, load_library, save_library, library_summary
from factflow.video_render import render_sample_video


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="quantatale", description="QuantaTale production tools.")
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

    candidates_parser = subparsers.add_parser(
        "research-candidates", help="Fetch discovered articles and extract unreviewed claim candidates."
    )
    candidates_parser.add_argument("discovery_report", help="Stage 3 discovery-candidates JSON file.")
    candidates_parser.add_argument("--registry", default=None, help="Optional publisher registry JSON.")
    candidates_parser.add_argument("--limit", type=int, default=10, help="Maximum article pages to retrieve (1-50).")
    candidates_parser.add_argument("--max-candidates-per-source", type=int, default=12)
    candidates_parser.add_argument("--output", default="build/research-candidates.json", help="JSON output path.")

    dossier_parser = subparsers.add_parser(
        "evidence-dossier", help="Discover related feed evidence and flag possible differences for review."
    )
    dossier_parser.add_argument("research_report", help="Stage 4A research-candidates JSON file.")
    dossier_parser.add_argument("--feeds", default=None, help="Optional discovery feed configuration.")
    dossier_parser.add_argument("--registry", default=None, help="Optional publisher registry JSON.")
    dossier_parser.add_argument("--feed-limit", type=int, default=100, help="Maximum feed leads to inspect (1-200).")
    dossier_parser.add_argument("--article-limit", type=int, default=20, help="Maximum related pages to retrieve (1-50).")
    dossier_parser.add_argument("--output", default="build/evidence-dossiers.json", help="JSON output path.")
    scholarly_parser = subparsers.add_parser(
        "scholarly-discover", help="Find unreviewed scholarly metadata leads via free Crossref and Europe PMC APIs."
    )
    scholarly_parser.add_argument("research_report", help="Stage 4A research-candidates JSON file.")
    scholarly_parser.add_argument("--claim-limit", type=int, default=20, help="Maximum claim candidates to search (1-50).")
    scholarly_parser.add_argument("--results-per-provider", type=int, default=5, help="Results per API and claim (1-10).")
    scholarly_parser.add_argument("--output", default="build/scholarly-leads.json", help="JSON output path.")

    comparison_parser = subparsers.add_parser(
        "evidence-compare", help="Compare collected passages with claim candidates and produce human-review signals."
    )
    comparison_parser.add_argument("research_report", help="Stage 4A research-candidates JSON file.")
    comparison_parser.add_argument("--scholarly", default=None, help="Optional Stage 4B-3 scholarly-passages JSON file.")
    comparison_parser.add_argument("--dossiers", default=None, help="Optional Stage 4B feed evidence-dossiers JSON file.")
    comparison_parser.add_argument("--passage-limit-per-claim", type=int, default=100, help="Maximum passages compared per claim (1-250).")
    comparison_parser.add_argument("--output", default="build/evidence-comparisons.json", help="JSON output path.")

    fulltext_parser = subparsers.add_parser(
        "scholarly-retrieve", help="Retrieve bounded full-text passages from explicitly open-access Europe PMC records."
    )
    fulltext_parser.add_argument("scholarly_report", help="Stage 4B-2 scholarly-leads JSON file.")
    fulltext_parser.add_argument("--article-limit", type=int, default=20, help="Maximum OA articles to retrieve (1-50).")
    fulltext_parser.add_argument("--passages-per-article", type=int, default=40, help="Maximum passages per article (1-40).")
    fulltext_parser.add_argument("--output", default="build/scholarly-passages.json", help="JSON output path.")
    library_parser = subparsers.add_parser(
        "library-add-discovery", help="Persist discovered story leads without approving them for production."
    )
    library_parser.add_argument("discovery_report", help="Discovery-candidates JSON report.")
    library_parser.add_argument("--library", default="production/topic-library.json", help="Persistent topic library JSON.")

    render_parser = subparsers.add_parser(
        "render-sample", help="Render a sourced sample short using free procedural graphics, TTS and FFmpeg."
    )
    render_parser.add_argument("spec_file", help="Sample video specification JSON.")
    render_parser.add_argument("--output-dir", default="build/sample-video", help="Directory for MP4 and sidecar files.")

    return parser


def main() -> int:
    args = build_parser().parse_args()

    if args.command == "library-add-discovery":
        try:
            report = json.loads(Path(args.discovery_report).read_text(encoding="utf-8"))
            library = load_library(args.library)
            result = add_discovery_report(library, report)
            save_library(library, args.library)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            print(f"TOPIC LIBRARY ERROR: {exc}", file=sys.stderr)
            return 1
        summary = library_summary(library)
        print(f"Added {result['added']} leads; skipped {result['duplicates']} duplicates.")
        print(f"Library totals: {summary}")
        print("All discovered leads remain unreviewed and blocked from production.")
        return 0

    if args.command == "render-sample":
        try:
            result = render_sample_video(args.spec_file, args.output_dir)
        except (OSError, json.JSONDecodeError, ValueError, RuntimeError) as exc:
            print(f"SAMPLE RENDER ERROR: {exc}", file=sys.stderr)
            return 1
        print("SAMPLE VIDEO RENDERED AND QUALITY-CHECKED")
        print(f"Video: {result['video']}")
        print(f"Duration: {result['duration_seconds']} seconds")
        print(f"Format: {result['width']}x{result['height']} at {result['fps']} fps")
        print(f"File size: {result['size_bytes']} bytes")
        print(f"Metadata: {result['metadata']}")
        return 0

    if args.command == "evidence-compare":
        if not 1 <= args.passage_limit_per_claim <= 250:
            print("EVIDENCE COMPARISON ERROR: passage limit must be between 1 and 250.", file=sys.stderr)
            return 1
        try:
            research = json.loads(Path(args.research_report).read_text(encoding="utf-8"))
            scholarly = json.loads(Path(args.scholarly).read_text(encoding="utf-8")) if args.scholarly else {}
            dossiers = json.loads(Path(args.dossiers).read_text(encoding="utf-8")) if args.dossiers else {}
            report = compare_evidence(
                research, scholarly, dossiers,
                passage_limit_per_claim=args.passage_limit_per_claim,
            )
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            print(f"EVIDENCE COMPARISON ERROR: {exc}", file=sys.stderr)
            return 1
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Compared passages for {report['candidate_count']} claim candidates; all signals remain unreviewed.")
        print(f"Evidence comparison report: {output_path}")
        return 0

    if args.command == "scholarly-retrieve":
        if not 1 <= args.article_limit <= 50 or not 1 <= args.passages_per_article <= 40:
            print("SCHOLARLY RETRIEVAL ERROR: limits out of range.", file=sys.stderr)
            return 1
        try:
            scholarly = json.loads(Path(args.scholarly_report).read_text(encoding="utf-8"))
            report = retrieve_open_access_passages(
                scholarly, article_limit=args.article_limit,
                passages_per_article=args.passages_per_article,
            )
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            print(f"SCHOLARLY RETRIEVAL ERROR: {exc}", file=sys.stderr)
            return 1
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Retrieved {report['passage_count']} unreviewed passages from {report['retrieved_article_count']} open-access articles.")
        print(f"Scholarly passage report: {output_path}")
        return 0

    if args.command == "scholarly-discover":
        if not 1 <= args.claim_limit <= 50 or not 1 <= args.results_per_provider <= 10:
            print("SCHOLARLY DISCOVERY ERROR: limits out of range.", file=sys.stderr)
            return 1
        try:
            research = json.loads(Path(args.research_report).read_text(encoding="utf-8"))
            report = discover_scholarly_metadata(research, claim_limit=args.claim_limit,
                                                 results_per_provider=args.results_per_provider)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            print(f"SCHOLARLY DISCOVERY ERROR: {exc}", file=sys.stderr)
            return 1
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Collected {report['lead_count']} unreviewed scholarly metadata leads.")
        print(f"Scholarly discovery report: {output_path}")
        return 0

    if args.command == "evidence-dossier":
        if not 1 <= args.feed_limit <= 200 or not 1 <= args.article_limit <= 50:
            print("DOSSIER ERROR: feed-limit must be 1-200 and article-limit must be 1-50.", file=sys.stderr)
            return 1
        try:
            research = json.loads(Path(args.research_report).read_text(encoding="utf-8"))
            registry = load_source_registry(args.registry) if args.registry else load_source_registry()
            feeds = load_feed_config(args.feeds) if args.feeds else load_feed_config()
            report = build_evidence_dossier(
                research, registry, feeds,
                feed_limit=args.feed_limit, article_limit=args.article_limit,
            )
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            print(f"DOSSIER ERROR: {exc}", file=sys.stderr)
            return 1
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        discovery = report["discovery"]
        print(
            f"Built {report['dossier_count']} evidence dossiers; "
            f"retrieved {discovery['retrieved_article_count']} related articles."
        )
        print(f"Evidence dossier report: {output_path}")
        return 0

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
