"""Local knowledge base and ticket history for triage context enrichment."""

from __future__ import annotations

from dataclasses import dataclass

# === KNOWLEDGE BASE ===
# A small local document store of support knowledge, indexed by topic keywords.

_KNOWLEDGE_ENTRIES: list[dict[str, str]] = [
    {
        "topic": "authentication sso oauth saml login",
        "content": (
            "Authentication issues include SSO/SAML integration failures, OAuth token "
            "refresh problems, and MFA recovery. SSO and OAuth failures are account_auth "
            "category even when they produce API errors like 401. Root cause is authentication "
            "infrastructure, not general API availability."
        ),
    },
    {
        "topic": "billing subscription charge refund payment invoice",
        "content": (
            "Billing issues include duplicate charges, subscription management, pro-rated "
            "charges, refund processing, payment method updates, and invoice discrepancies. "
            "Unauthorized charges after account compromise should be routed to account security "
            "first, then billing."
        ),
    },
    {
        "topic": "outage downtime api server infrastructure deployment",
        "content": (
            "Technical/infrastructure issues are platform-wide: full outages, API endpoint "
            "failures, deployment problems, SSL/DNS issues, rate limiting, and backend service "
            "unavailability. These affect all users, not specific product features."
        ),
    },
    {
        "topic": "product feature dashboard ui app crash bug timeout editor",
        "content": (
            "Product issues involve specific user-facing features misbehaving: app crashes, "
            "feature timeouts, UI glitches, broken functionality, missing elements. Even if "
            "the symptom is a crash or timeout, if it affects a specific named feature "
            "(dashboard, editor, search, mobile app), it is a product issue."
        ),
    },
    {
        "topic": "escalation critical security breach data loss",
        "content": (
            "Critical tickets require immediate escalation: active widespread outages, "
            "security breaches, data loss, ransomware. These go to Incident Response "
            "regardless of the initial category."
        ),
    },
    {
        "topic": "password reset locked account access",
        "content": (
            "Password resets and account lockouts are high-urgency account_auth issues. "
            "If combined with billing complaints (e.g., charged during lockout), the ticket "
            "has multi-category signals and should be flagged for human review."
        ),
    },
]

# === TICKET HISTORY ===
# Mock customer history for prototype purposes.

_TICKET_HISTORY: dict[str, list[dict[str, str]]] = {
    "customer-001": [
        {"ticket_id": "HIST-001", "category": "billing", "summary": "Duplicate charge resolved"},
        {"ticket_id": "HIST-002", "category": "account_auth", "summary": "Password reset"},
    ],
    "customer-002": [
        {"ticket_id": "HIST-003", "category": "technical", "summary": "API timeout during outage"},
    ],
    "customer-003": [
        {"ticket_id": "HIST-004", "category": "product", "summary": "Dashboard widget broken"},
        {"ticket_id": "HIST-005", "category": "product", "summary": "Export feature request"},
    ],
}


@dataclass(frozen=True)
class KnowledgeResult:
    """Result from knowledge base search."""

    query: str
    entries: list[str]


@dataclass(frozen=True)
class HistoryResult:
    """Result from ticket history lookup."""

    customer_id: str
    tickets: list[dict[str, str]]


def search_knowledge_base(query: str) -> KnowledgeResult:
    """Search the local knowledge base for relevant support documentation.

    Returns entries whose topic keywords overlap with the query terms.
    This is a simple keyword-overlap retrieval — not vector search.
    """
    if not query or not query.strip():
        return KnowledgeResult(query=query, entries=[])

    query_terms = set(query.lower().split())
    results: list[str] = []

    for entry in _KNOWLEDGE_ENTRIES:
        topic_terms = set(entry["topic"].split())
        overlap = query_terms & topic_terms
        if len(overlap) >= 1:
            results.append(entry["content"])

    return KnowledgeResult(query=query, entries=results[:3])


def get_ticket_history(customer_id: str) -> HistoryResult:
    """Retrieve previous ticket history for a customer.

    Uses mock data for the prototype. Returns empty list for unknown customers.
    """
    if not customer_id or not customer_id.strip():
        return HistoryResult(customer_id=customer_id, tickets=[])

    tickets = _TICKET_HISTORY.get(customer_id.strip(), [])
    return HistoryResult(customer_id=customer_id, tickets=tickets)
