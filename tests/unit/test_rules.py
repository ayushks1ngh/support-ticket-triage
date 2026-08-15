from support_triage.models import Category, Ticket, Urgency
from support_triage.rules import assess_ticket, classify_by_rule


def ticket(subject: str, body: str = "Please help") -> Ticket:
    return Ticket(ticket_id="T-1", subject=subject, body=body)


def test_obvious_auth_rule() -> None:
    result = classify_by_rule(ticket("Cannot sign in", "My account is locked"))
    assert result is not None
    assert result.category is Category.ACCOUNT_AUTH
    assert result.urgency is Urgency.HIGH


def test_obvious_billing_rule() -> None:
    result = classify_by_rule(ticket("Duplicate charge", "I was charged twice"))
    assert result is not None
    assert result.category is Category.BILLING


def test_widespread_outage_is_critical() -> None:
    result = classify_by_rule(ticket("Production outage", "API unavailable for all users"))
    assert result is not None
    assert result.category is Category.TECHNICAL
    assert result.urgency is Urgency.CRITICAL


def test_feature_request_is_low_product() -> None:
    result = classify_by_rule(ticket("Feature request", "Please add dark mode"))
    assert result is not None
    assert result.category is Category.PRODUCT
    assert result.urgency is Urgency.LOW


def test_ambiguous_ticket_defers() -> None:
    assert classify_by_rule(ticket("Unexpected behavior", "The dashboard feels wrong")) is None


def test_cross_category_conflict_defers() -> None:
    item = ticket("Cannot log in after duplicate charge", "I need a refund and password reset")
    assert classify_by_rule(item) is None
    assert assess_ticket(item).has_conflict


# === Cross-category vocabulary conflict detection regression tests ===


def test_x003_refund_with_product_vocabulary_defers() -> None:
    """X-003: 'refund' matches billing rule, but 'dark mode broke' is product vocabulary."""
    item = ticket(
        "Feature broken and need refund",
        "Dark mode broke my layout and I want my money back.",
    )
    # Should NOT be resolved by rule because product vocabulary is present
    assert classify_by_rule(item) is None


def test_x004_auth_with_outage_vocabulary_defers() -> None:
    """X-004: 'can't log in' matches auth rule, but 'outage' is technical vocabulary."""
    item = ticket(
        "Account locked during outage",
        "I can't log in but the status page shows system issues.",
    )
    # Should NOT be resolved by rule because technical vocabulary is present
    assert classify_by_rule(item) is None


def test_pure_auth_still_resolves() -> None:
    """Unambiguous auth ticket with no cross-category vocabulary still works."""
    result = classify_by_rule(ticket("Cannot sign in", "The password reset link expired."))
    assert result is not None
    assert result.category is Category.ACCOUNT_AUTH
    assert result.confidence == 0.96


def test_pure_billing_still_resolves() -> None:
    """Unambiguous billing ticket with no cross-category vocabulary still works."""
    result = classify_by_rule(ticket("Duplicate charge", "I was charged twice this month."))
    assert result is not None
    assert result.category is Category.BILLING
    assert result.confidence == 0.96


def test_pure_outage_still_resolves() -> None:
    """Unambiguous outage with no cross-category vocabulary still works."""
    result = classify_by_rule(
        ticket("System outage", "The service is down for all users company-wide.")
    )
    assert result is not None
    assert result.category is Category.TECHNICAL
    assert result.urgency is Urgency.CRITICAL
