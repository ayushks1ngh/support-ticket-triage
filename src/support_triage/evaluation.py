"""Measured evaluation against a labeled JSON dataset."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import TypeAdapter, ValidationError

from support_triage.batch import process_tickets
from support_triage.classifier import TicketClassifier
from support_triage.config import Settings
from support_triage.models import EvaluationCase, EvaluationReport


def load_evaluation_cases(path: Path) -> list[EvaluationCase]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        cases = TypeAdapter(list[EvaluationCase]).validate_python(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValidationError) as exc:
        raise ValueError("evaluation dataset is invalid") from exc
    if not cases:
        raise ValueError("evaluation dataset must not be empty")
    ids = [case.ticket.ticket_id for case in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("evaluation ticket IDs must be unique")
    return cases


def evaluate(
    cases: list[EvaluationCase],
    *,
    classifier: TicketClassifier,
    settings: Settings,
) -> EvaluationReport:
    batch = process_tickets(
        [case.ticket for case in cases],
        classifier=classifier,
        settings=settings,
    )
    expected_by_id = {case.ticket.ticket_id: case.expected for case in cases}
    total = len(cases)
    category_correct = urgency_correct = routing_correct = exact = 0
    true_positive = false_positive = false_negative = 0
    for result in batch.results:
        expected = expected_by_id[result.ticket_id]
        category_ok = result.category == expected.category
        urgency_ok = result.urgency == expected.urgency
        routing_ok = result.routing_team == expected.routing_team
        category_correct += int(category_ok)
        urgency_correct += int(urgency_ok)
        routing_correct += int(routing_ok)
        exact += int(category_ok and urgency_ok and routing_ok)
        true_positive += int(result.human_review and expected.human_review)
        false_positive += int(result.human_review and not expected.human_review)
        false_negative += int(not result.human_review and expected.human_review)
    precision_denominator = true_positive + false_positive
    recall_denominator = true_positive + false_negative
    return EvaluationReport(
        total=total,
        exact_accuracy=exact / total,
        category_accuracy=category_correct / total,
        urgency_accuracy=urgency_correct / total,
        routing_accuracy=routing_correct / total,
        human_review_precision=(
            true_positive / precision_denominator if precision_denominator else None
        ),
        human_review_recall=true_positive / recall_denominator if recall_denominator else None,
        api_calls=batch.metrics.api_calls,
        tickets_per_api_call=(
            batch.metrics.model_count / batch.metrics.api_calls if batch.metrics.api_calls else None
        ),
        latency_ms=batch.metrics.latency_ms,
        rule_count=batch.metrics.rule_count,
        model_count=batch.metrics.model_count,
        fallback_count=batch.metrics.fallback_count,
    )
