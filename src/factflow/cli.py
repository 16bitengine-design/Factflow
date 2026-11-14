"""Command-line interface for the FactFlow foundation."""

from __future__ import annotations

import argparse
import sys

from factflow.topic import TopicValidationError, load_topic


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="factflow", description="FactFlow production tools.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="Validate a topic JSON file.")
    validate_parser.add_argument("topic_file", help="Path to the topic JSON file.")
    return parser


def main() -> int:
    args = build_parser().parse_args()

    if args.command == "validate":
        try:
            topic = load_topic(args.topic_file)
        except TopicValidationError as exc:
            print(f"INVALID: {exc}", file=sys.stderr)
            return 1

        print(f"VALID: {topic['title']} ({topic['id']})")
        print(f"Claims: {len(topic['claims'])} | Scenes: {len(topic['scenes'])}")
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
