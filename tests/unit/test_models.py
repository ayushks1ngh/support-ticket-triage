import pytest
from pydantic import ValidationError

from support_triage.models import (
    BatchModelOutput,
    Category,
    ModelClassification,
    Ticket,
    Urgency,
)


def test_ticket_trims_fields() -> None:
    ticket = Ticket(ticket_id=" T-1 ", subject=" Login ", body=" Help ")
    assert ticket.ticket_id == "T-1"
    assert ticket.subject == "Login"


def test_ticket_rejects_missing_and_extra_fields() -> None:
    with pytest.raises(ValidationError):
        Ticket.model_validate({"ticket_id": "T", "subject": "x"})
    with pytest.raises(ValidationError):
        Ticket.model_validate({"ticket_id": "T", "subject": "x", "body": "y", "x": 1})


def test_model_output_rejects_duplicate_ids() -> None:
    item = ModelClassification(
        ticket_id="T",
        category=Category.BILLING,
        urgency=Urgency.MEDIUM,
        confidence=0.8,
        reason="Invoice issue",
    )
    with pytest.raises(ValidationError):
        BatchModelOutput(classifications=[item, item])


def test_confidence_must_be_bounded_and_finite() -> None:
    for invalid in (-0.1, 1.1, float("nan")):
        with pytest.raises(ValidationError):
            ModelClassification(
                ticket_id="T",
                category=Category.OTHER,
                urgency=Urgency.LOW,
                confidence=invalid,
                reason="Unclear",
            )
