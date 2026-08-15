from support_triage.models import Category, RoutingTeam, Urgency
from support_triage.router import route_ticket


def test_routes_categories() -> None:
    assert route_ticket(Category.ACCOUNT_AUTH, Urgency.MEDIUM) is RoutingTeam.ACCOUNT
    assert route_ticket(Category.BILLING, Urgency.HIGH) is RoutingTeam.BILLING
    assert route_ticket(Category.PRODUCT, Urgency.LOW) is RoutingTeam.PRODUCT


def test_routes_critical_technical_to_incident() -> None:
    assert route_ticket(Category.TECHNICAL, Urgency.CRITICAL) is RoutingTeam.INCIDENT
    assert route_ticket(Category.OTHER, Urgency.CRITICAL) is RoutingTeam.INCIDENT
