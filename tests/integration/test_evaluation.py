import json
from pathlib import Path

from support_triage.classifier import TicketClassifier
from support_triage.config import Settings
from support_triage.evaluation import evaluate, load_evaluation_cases
from tests.fakes import FakeProvider


def write_case(path: Path, *, category: str, team: str, review: bool) -> None:
    path.write_text(
        json.dumps(
            [
                {
                    "ticket": {
                        "ticket_id": "T",
                        "subject": "Dashboard changed",
                        "body": "Widget is odd",
                    },
                    "expected": {
                        "category": category,
                        "urgency": "medium",
                        "routing_team": team,
                        "human_review": review,
                    },
                }
            ]
        ),
        encoding="utf-8",
    )


def test_evaluation_reports_measured_metrics(tmp_path: Path) -> None:
    dataset = tmp_path / "evaluation.json"
    write_case(dataset, category="product", team="Product Support", review=False)
    cases = load_evaluation_cases(dataset)
    report = evaluate(
        cases,
        classifier=TicketClassifier(threshold=0.75, provider=FakeProvider()),
        settings=Settings(),
    )
    assert report.exact_accuracy == 1.0
    assert report.api_calls == 1
    assert report.tickets_per_api_call == 1.0


def test_offline_review_behavior_is_measured(tmp_path: Path) -> None:
    dataset = tmp_path / "evaluation.json"
    write_case(dataset, category="other", team="General Support", review=True)
    report = evaluate(
        load_evaluation_cases(dataset),
        classifier=TicketClassifier(threshold=0.75, provider=None),
        settings=Settings(),
    )
    assert report.human_review_precision == 1.0
    assert report.human_review_recall == 1.0
    assert report.api_calls == 0
