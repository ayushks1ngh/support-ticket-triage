from support_triage.classifier import TicketClassifier
from support_triage.models import DecisionSource, Ticket
from tests.fakes import FakeProvider, MissingIdProvider


def test_low_confidence_model_result_is_reviewed() -> None:
    classifier = TicketClassifier(threshold=0.75, provider=FakeProvider(confidence=0.5))
    results, _ = classifier.classify_model_chunk(
        [Ticket(ticket_id="T", subject="Dashboard odd", body="Widget changed")]
    )
    assert results[0].source is DecisionSource.LLM
    assert results[0].human_review


def test_invalid_model_ids_fail_closed() -> None:
    classifier = TicketClassifier(threshold=0.75, provider=MissingIdProvider())
    results, _ = classifier.classify_model_chunk(
        [Ticket(ticket_id="T", subject="Dashboard odd", body="Widget changed")]
    )
    assert results[0].source is DecisionSource.FALLBACK
    assert results[0].human_review
