"""Tests for knowledge base, ticket history, and batch delay."""

from __future__ import annotations

import time

from support_triage.batch import process_tickets
from support_triage.classifier import TicketClassifier
from support_triage.config import Settings
from support_triage.knowledge import (
    KnowledgeResult,
    get_ticket_history,
    search_knowledge_base,
)
from support_triage.models import Ticket
from tests.fakes import FakeProvider

# === KNOWLEDGE BASE ===


class TestKnowledgeBase:
    def test_search_finds_auth_knowledge(self) -> None:
        result = search_knowledge_base("oauth login sso")
        assert isinstance(result, KnowledgeResult)
        assert len(result.entries) > 0
        assert any("authentication" in e.lower() or "sso" in e.lower() for e in result.entries)

    def test_search_finds_billing_knowledge(self) -> None:
        result = search_knowledge_base("refund charge subscription")
        assert len(result.entries) > 0
        assert any("billing" in e.lower() or "charge" in e.lower() for e in result.entries)

    def test_search_empty_query_returns_empty(self) -> None:
        result = search_knowledge_base("")
        assert result.entries == []

    def test_search_no_match_returns_empty(self) -> None:
        result = search_knowledge_base("quantum physics relativity")
        assert result.entries == []

    def test_search_limits_results(self) -> None:
        # Even with broad query hitting multiple entries, max is 3
        result = search_knowledge_base("authentication billing outage product escalation password")
        assert len(result.entries) <= 3


# === TICKET HISTORY ===


class TestTicketHistory:
    def test_known_customer_returns_history(self) -> None:
        result = get_ticket_history("customer-001")
        assert len(result.tickets) == 2
        assert result.tickets[0]["category"] == "billing"

    def test_unknown_customer_returns_empty(self) -> None:
        result = get_ticket_history("unknown-customer")
        assert result.tickets == []

    def test_empty_customer_id_returns_empty(self) -> None:
        result = get_ticket_history("")
        assert result.tickets == []

    def test_history_is_read_only(self) -> None:
        result1 = get_ticket_history("customer-001")
        result2 = get_ticket_history("customer-001")
        assert result1.tickets == result2.tickets


# === BATCH DELAY ===


class TestBatchDelay:
    def test_zero_delay_is_fast(self) -> None:
        """Default batch_delay=0 should not add noticeable delay."""
        provider = FakeProvider()
        tickets = [
            Ticket(ticket_id=f"D-{i}", subject="Dashboard odd", body="Widget changed")
            for i in range(20)
        ]
        start = time.perf_counter()
        process_tickets(
            tickets,
            classifier=TicketClassifier(threshold=0.75, provider=provider),
            settings=Settings(batch_size=5, batch_delay=0.0),
        )
        elapsed = time.perf_counter() - start
        # Should be well under 1 second with no delay
        assert elapsed < 1.0

    def test_delay_adds_pauses_between_chunks(self) -> None:
        """Configured delay should pause between chunks but not after last."""
        provider = FakeProvider()
        tickets = [
            Ticket(ticket_id=f"D-{i}", subject="Dashboard odd", body="Widget changed")
            for i in range(15)
        ]
        start = time.perf_counter()
        # 15 tickets / batch_size 5 = 3 chunks → 2 delays of 0.3s each = ~0.6s minimum
        process_tickets(
            tickets,
            classifier=TicketClassifier(threshold=0.75, provider=provider),
            settings=Settings(batch_size=5, batch_delay=0.3),
        )
        elapsed = time.perf_counter() - start
        # At least 0.5s (2 delays × 0.3s with some tolerance)
        assert elapsed >= 0.5
        # But less than 1.5s (not delaying after the last chunk)
        assert elapsed < 1.5

    def test_single_chunk_no_delay(self) -> None:
        """If only one chunk exists, no delay is applied."""
        provider = FakeProvider()
        tickets = [Ticket(ticket_id="D-0", subject="Dashboard odd", body="Widget changed")]
        start = time.perf_counter()
        process_tickets(
            tickets,
            classifier=TicketClassifier(threshold=0.75, provider=provider),
            settings=Settings(batch_size=10, batch_delay=5.0),
        )
        elapsed = time.perf_counter() - start
        # Should not wait 5 seconds
        assert elapsed < 1.0
