"""Small, conflict-aware deterministic triage rules."""

from __future__ import annotations

import re
from dataclasses import dataclass

from support_triage.models import Category, ModelClassification, Ticket, Urgency

_CATEGORY_PHRASES: dict[Category, tuple[str, ...]] = {
    Category.ACCOUNT_AUTH: (
        "password reset",
        "cannot log in",
        "can't log in",
        "cannot sign in",
        "can't sign in",
        "account locked",
        "two factor",
        "2fa",
    ),
    Category.BILLING: (
        "duplicate charge",
        "charged twice",
        "refund",
        "payment failed",
        "invoice",
    ),
    Category.TECHNICAL: (
        "service is down",
        "server is down",
        "api unavailable",
        "api is unavailable",
        "system outage",
        "500 error",
    ),
    Category.PRODUCT: ("feature request",),
}

# Broader vocabulary signals for cross-category conflict detection.
# These are NOT strong enough to classify on their own, but indicate
# that a second category may be relevant when a rule already matched one.
_CATEGORY_VOCABULARY: dict[Category, tuple[str, ...]] = {
    Category.ACCOUNT_AUTH: (
        "log in",
        "sign in",
        "password",
        "account",
        "locked",
        "access",
        "authentication",
        "credential",
    ),
    Category.BILLING: (
        "charge",
        "payment",
        "refund",
        "billing",
        "invoice",
        "subscription",
        "money",
        "paid",
        "price",
    ),
    Category.TECHNICAL: (
        "outage",
        "server",
        "api",
        "down",
        "503",
        "500",
        "infrastructure",
        "deploy",
        "network",
    ),
    Category.PRODUCT: (
        "feature",
        "dark mode",
        "ui",
        "layout",
        "widget",
        "dashboard",
        "editor",
        "search",
        "notification",
        "mobile app",
        "crash",
        "broken",
        "bug",
    ),
}

_CRITICAL_PHRASES = (
    "all users",
    "company-wide",
    "production outage",
    "security breach",
    "data breach",
)
_HIGH_PHRASES = (
    "account locked",
    "cannot log in",
    "cannot sign in",
    "charged twice",
    "duplicate charge",
    "production",
    "urgent",
)
_LOW_PHRASES = ("feature request", "how do i", "how to", "cosmetic")


@dataclass(frozen=True)
class RuleAssessment:
    matched_categories: frozenset[Category]
    critical_signal: bool

    @property
    def has_conflict(self) -> bool:
        return len(self.matched_categories) > 1


def assess_ticket(ticket: Ticket) -> RuleAssessment:
    text = _normalized_text(ticket)
    matches = {
        category
        for category, phrases in _CATEGORY_PHRASES.items()
        if any(_contains_phrase(text, phrase) for phrase in phrases)
    }
    return RuleAssessment(
        matched_categories=frozenset(matches),
        critical_signal=any(_contains_phrase(text, phrase) for phrase in _CRITICAL_PHRASES),
    )


def classify_by_rule(ticket: Ticket) -> ModelClassification | None:
    """Classify only a ticket with one clear category signal."""

    assessment = assess_ticket(ticket)
    if len(assessment.matched_categories) != 1:
        return None
    category = next(iter(assessment.matched_categories))
    text = _normalized_text(ticket)

    # Check for vocabulary signals from OTHER categories.
    # If present, the ticket has cross-category evidence and should defer to the model.
    if _has_cross_category_vocabulary(text, category):
        return None

    urgency = _rule_urgency(text, assessment.critical_signal, category)
    return ModelClassification(
        ticket_id=ticket.ticket_id,
        category=category,
        urgency=urgency,
        confidence=0.96,
        reason=f"Clear deterministic {category.value} phrase matched.",
    )


def _rule_urgency(text: str, critical_signal: bool, category: Category) -> Urgency:
    if critical_signal and category in {Category.TECHNICAL, Category.PRODUCT}:
        return Urgency.CRITICAL
    if any(_contains_phrase(text, phrase) for phrase in _HIGH_PHRASES):
        return Urgency.HIGH
    if any(_contains_phrase(text, phrase) for phrase in _LOW_PHRASES):
        return Urgency.LOW
    return Urgency.MEDIUM


def _normalized_text(ticket: Ticket) -> str:
    return f"{ticket.subject}\n{ticket.body}".lower()


def _contains_phrase(text: str, phrase: str) -> bool:
    return re.search(rf"(?<!\w){re.escape(phrase)}(?!\w)", text) is not None


def _has_cross_category_vocabulary(text: str, matched_category: Category) -> bool:
    """Check if vocabulary from a different category is present in the ticket text."""
    for category, vocab in _CATEGORY_VOCABULARY.items():
        if category == matched_category:
            continue
        if any(_contains_phrase(text, term) for term in vocab):
            return True
    return False
