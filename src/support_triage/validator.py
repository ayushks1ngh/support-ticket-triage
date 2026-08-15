"""Semantic validation, routing, and safe fallback decisions."""

from support_triage.models import (
    Category,
    DecisionSource,
    ModelClassification,
    Ticket,
    TicketResult,
    Urgency,
)
from support_triage.router import route_ticket
from support_triage.rules import assess_ticket


def finalize_classification(
    ticket: Ticket,
    classification: ModelClassification,
    *,
    source: DecisionSource,
    threshold: float,
) -> TicketResult:
    """Apply deterministic review policy to a validated classification."""

    review_reasons: list[str] = []
    assessment = assess_ticket(ticket)
    if classification.confidence < threshold:
        review_reasons.append(f"confidence below {threshold:.2f}")
    if classification.category is Category.OTHER:
        review_reasons.append("unsupported/other category")
    if assessment.has_conflict:
        review_reasons.append("conflicting deterministic category signals")
    if assessment.critical_signal and classification.urgency is not Urgency.CRITICAL:
        review_reasons.append("critical-impact language conflicts with urgency")

    reason = classification.reason
    if review_reasons:
        reason = f"{reason} Human review: {', '.join(review_reasons)}."
    return TicketResult(
        ticket_id=ticket.ticket_id,
        category=classification.category,
        urgency=classification.urgency,
        confidence=classification.confidence,
        routing_team=route_ticket(classification.category, classification.urgency),
        human_review=bool(review_reasons),
        reason=reason[:500],
        source=source,
    )


def fallback_result(ticket: Ticket, reason: str) -> TicketResult:
    """Create a safe result for offline, provider, or output failures."""

    clean_reason = " ".join(reason.split())[:430]
    return TicketResult(
        ticket_id=ticket.ticket_id,
        category=Category.OTHER,
        urgency=Urgency.MEDIUM,
        confidence=0.0,
        routing_team=route_ticket(Category.OTHER, Urgency.MEDIUM),
        human_review=True,
        reason=f"Automatic classification unavailable. {clean_reason}",
        source=DecisionSource.FALLBACK,
    )
