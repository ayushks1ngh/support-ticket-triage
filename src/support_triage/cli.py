"""Command-line interface for classification and evaluation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from support_triage.batch import process_tickets
from support_triage.classifier import TicketClassifier
from support_triage.config import ProviderName, Settings
from support_triage.evaluation import evaluate, load_evaluation_cases
from support_triage.io import load_tickets, write_report
from support_triage.models import model_dump_jsonable
from support_triage.providers import create_provider


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Rule-first support ticket triage agent")
    subparsers = parser.add_subparsers(dest="command", required=True)

    classify = subparsers.add_parser("classify", help="classify JSON or CSV tickets")
    classify.add_argument("--input", required=True, type=Path)
    classify.add_argument("--output", required=True, type=Path)
    _add_runtime_arguments(classify)

    evaluation = subparsers.add_parser("evaluate", help="evaluate a labeled JSON dataset")
    evaluation.add_argument("--dataset", required=True, type=Path)
    _add_runtime_arguments(evaluation)
    return parser


def _add_runtime_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--offline", action="store_true", help="do not call an external model")
    parser.add_argument("--provider", choices=[item.value for item in ProviderName])
    parser.add_argument("--model-id")
    parser.add_argument("--threshold", type=float)
    parser.add_argument("--batch-size", type=int)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        settings = Settings.from_env().with_overrides(
            provider=ProviderName(args.provider) if args.provider else None,
            model_id=args.model_id,
            threshold=args.threshold,
            batch_size=args.batch_size,
        )
        provider = None if args.offline else create_provider(settings)
        classifier = TicketClassifier(
            threshold=settings.human_review_threshold,
            provider=provider,
        )
        if args.command == "classify":
            tickets, errors = load_tickets(args.input)
            report = process_tickets(
                tickets,
                classifier=classifier,
                settings=settings,
                input_errors=errors,
            )
            write_report(report, args.output)
            print(json.dumps(model_dump_jsonable(report.metrics), indent=2))
            if errors:
                print(
                    f"Rejected {len(errors)} invalid record(s); see JSON report errors.",
                    file=sys.stderr,
                )
                return 2
            return 0

        cases = load_evaluation_cases(args.dataset)
        evaluation_report = evaluate(cases, classifier=classifier, settings=settings)
        print(json.dumps(model_dump_jsonable(evaluation_report), indent=2))
        return 0
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
