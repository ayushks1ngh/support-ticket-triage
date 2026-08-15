from support_triage.models import (
    Category,
    DecisionSource,
    ModelClassification,
    Ticket,
    Urgency,
)
from support_triage.validator import fallback_result, finalize_classification


def test_low_confidence_requires_review() -> None:
    ticket = Ticket(ticket_id="T", subject="Dashboard odd", body="Something changed")
    classification = ModelClassification(
        ticket_id="T",
        category=Category.PRODUCT,
        urgency=Urgency.MEDIUM,
        confidence=0.74,
        reason="Likely product behavior",
    )
    result = finalize_classification(
        ticket, classification, source=DecisionSource.LLM, threshold=0.75
    )
    assert result.human_review
    assert "confidence below" in result.reason


def test_high_confidence_routes_automatically() -> None:
    ticket = Ticket(ticket_id="T", subject="SDK bug", body="Method returns an error")
    classification = ModelClassification(
        ticket_id="T",
        category=Category.TECHNICAL,
        urgency=Urgency.MEDIUM,
        confidence=0.9,
        reason="Technical SDK failure",
    )
    result = finalize_classification(
        ticket, classification, source=DecisionSource.LLM, threshold=0.75
    )
    assert not result.human_review


def test_other_and_conflict_require_review() -> None:
    ticket = Ticket(
        ticket_id="T",
        subject="Cannot log in and duplicate charge",
        body="Password reset and refund needed",
    )
    classification = ModelClassification(
        ticket_id="T",
        category=Category.OTHER,
        urgency=Urgency.HIGH,
        confidence=0.95,
        reason="Mixed request",
    )
    result = finalize_classification(
        ticket, classification, source=DecisionSource.LLM, threshold=0.75
    )
    assert result.human_review
    assert "conflicting" in result.reason


def test_fallback_is_sanitized_and_reviewed() -> None:
    ticket = Ticket(ticket_id="T", subject="x", body="y")
    result = fallback_result(ticket, " provider\nfailed   temporarily ")
    assert result.source is DecisionSource.FALLBACK
    assert result.human_review
    assert "\n" not in result.reason
