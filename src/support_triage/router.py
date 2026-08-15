"""Deterministic category-to-team routing."""

from support_triage.models import Category, RoutingTeam, Urgency

_DEFAULT_ROUTES = {
    Category.ACCOUNT_AUTH: RoutingTeam.ACCOUNT,
    Category.BILLING: RoutingTeam.BILLING,
    Category.TECHNICAL: RoutingTeam.TECHNICAL,
    Category.PRODUCT: RoutingTeam.PRODUCT,
    Category.OTHER: RoutingTeam.GENERAL,
}


def route_ticket(category: Category, urgency: Urgency) -> RoutingTeam:
    """Return a stable operational route for a validated classification."""

    if urgency is Urgency.CRITICAL and category in {
        Category.TECHNICAL,
        Category.PRODUCT,
        Category.OTHER,
    }:
        return RoutingTeam.INCIDENT
    return _DEFAULT_ROUTES[category]
