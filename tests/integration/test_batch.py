from support_triage.batch import process_tickets
from support_triage.classifier import TicketClassifier
from support_triage.config import Settings
from support_triage.models import DecisionSource, Ticket
from tests.fakes import FailingProvider, FakeProvider


def ambiguous(number: int) -> Ticket:
    return Ticket(
        ticket_id=f"A-{number}",
        subject=f"Dashboard behaves strangely {number}",
        body="A widget changed after the latest update",
    )


def test_mixed_batch_chunks_and_preserves_order() -> None:
    provider = FakeProvider(retry_count=1)
    settings = Settings(batch_size=2)
    tickets = [
        Ticket(ticket_id="R-1", subject="Duplicate charge", body="Charged twice"),
        ambiguous(1),
        ambiguous(2),
        ambiguous(3),
    ]
    report = process_tickets(
        tickets,
        classifier=TicketClassifier(threshold=0.75, provider=provider),
        settings=settings,
    )
    assert [result.ticket_id for result in report.results] == [
        "R-1",
        "A-1",
        "A-2",
        "A-3",
    ]
    assert provider.calls == [["A-1", "A-2"], ["A-3"]]
    assert report.metrics.api_calls == 2
    assert report.metrics.retries == 2
    assert report.metrics.rule_count == 1
    assert report.metrics.model_count == 3


def test_provider_failure_isolated_to_review_fallbacks() -> None:
    provider = FailingProvider(retry_count=2)
    report = process_tickets(
        [ambiguous(1), ambiguous(2)],
        classifier=TicketClassifier(threshold=0.75, provider=provider),
        settings=Settings(batch_size=1),
    )
    assert all(result.source is DecisionSource.FALLBACK for result in report.results)
    assert all(result.human_review for result in report.results)
    assert report.metrics.failure_count == 2
    assert report.metrics.api_calls == 2
    assert report.metrics.retries == 4


def test_offline_makes_no_api_calls() -> None:
    report = process_tickets(
        [ambiguous(1)],
        classifier=TicketClassifier(threshold=0.75, provider=None),
        settings=Settings(),
    )
    assert report.metrics.api_calls == 0
    assert report.metrics.provider == "offline"
    assert report.results[0].human_review
