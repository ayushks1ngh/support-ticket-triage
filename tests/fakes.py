"""Shared deterministic fake providers for offline tests."""

from __future__ import annotations

from support_triage.models import BatchModelOutput, Category, ModelClassification, Ticket, Urgency
from support_triage.providers.base import LLMProvider, ProviderError, ProviderResponse


class FakeProvider(LLMProvider):
    def __init__(self, *, confidence: float = 0.9, retry_count: int = 0) -> None:
        self.confidence = confidence
        self.retry_count = retry_count
        self.calls: list[list[str]] = []

    @property
    def name(self) -> str:
        return "fake"

    @property
    def model_id(self) -> str:
        return "fake-model"

    def classify(self, tickets: list[Ticket]) -> ProviderResponse:
        self.calls.append([ticket.ticket_id for ticket in tickets])
        classifications = []
        for ticket in reversed(tickets):
            category = (
                Category.PRODUCT if "dashboard" in ticket.subject.lower() else Category.TECHNICAL
            )
            classifications.append(
                ModelClassification(
                    ticket_id=ticket.ticket_id,
                    category=category,
                    urgency=Urgency.MEDIUM,
                    confidence=self.confidence,
                    reason="Deterministic fake classification",
                )
            )
        return ProviderResponse(
            output=BatchModelOutput(classifications=classifications),
            retry_count=self.retry_count,
        )


class FailingProvider(FakeProvider):
    def classify(self, tickets: list[Ticket]) -> ProviderResponse:
        self.calls.append([ticket.ticket_id for ticket in tickets])
        raise ProviderError("provider unavailable", retry_count=self.retry_count)


class MissingIdProvider(FakeProvider):
    def classify(self, tickets: list[Ticket]) -> ProviderResponse:
        self.calls.append([ticket.ticket_id for ticket in tickets])
        return ProviderResponse(
            output=BatchModelOutput(
                classifications=[
                    ModelClassification(
                        ticket_id="UNKNOWN",
                        category=Category.OTHER,
                        urgency=Urgency.LOW,
                        confidence=0.9,
                        reason="Wrong ID",
                    )
                ]
            )
        )
