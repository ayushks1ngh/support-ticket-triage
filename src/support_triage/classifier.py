"""Rule-first ticket classification orchestration."""

from __future__ import annotations

from support_triage.models import DecisionSource, Ticket, TicketResult
from support_triage.providers.base import LLMProvider, ProviderError
from support_triage.rules import classify_by_rule
from support_triage.validator import fallback_result, finalize_classification


class TicketClassifier:
    def __init__(self, *, threshold: float, provider: LLMProvider | None) -> None:
        self.threshold = threshold
        self.provider = provider

    def classify_rule(self, ticket: Ticket) -> TicketResult | None:
        classification = classify_by_rule(ticket)
        if classification is None:
            return None
        return finalize_classification(
            ticket,
            classification,
            source=DecisionSource.RULE,
            threshold=self.threshold,
        )

    def classify_model_chunk(self, tickets: list[Ticket]) -> tuple[list[TicketResult], int]:
        if self.provider is None:
            return (
                [
                    fallback_result(ticket, "Offline mode requires human review.")
                    for ticket in tickets
                ],
                0,
            )
        try:
            response = self.provider.classify(tickets)
            expected_ids = {ticket.ticket_id for ticket in tickets}
            actual_ids = {item.ticket_id for item in response.output.classifications}
            if expected_ids != actual_ids:
                raise ProviderError(
                    "structured output ticket IDs did not match the request",
                    retry_count=response.retry_count,
                )
            by_id = {item.ticket_id: item for item in response.output.classifications}
            results = [
                finalize_classification(
                    ticket,
                    by_id[ticket.ticket_id],
                    source=DecisionSource.LLM,
                    threshold=self.threshold,
                )
                for ticket in tickets
            ]
            return results, response.retry_count
        except ProviderError as exc:
            return [fallback_result(ticket, str(exc)) for ticket in tickets], exc.retry_count
