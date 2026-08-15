from __future__ import annotations

import os

import pytest

from support_triage.batch import process_tickets
from support_triage.classifier import TicketClassifier
from support_triage.config import Settings
from support_triage.models import Ticket
from support_triage.providers import create_provider


@pytest.mark.live
def test_live_provider_structured_output() -> None:
    """Opt-in smoke test; never runs in the credential-free core suite."""

    if os.getenv("RUN_LIVE_TESTS") != "1":
        pytest.skip("set RUN_LIVE_TESTS=1 to enable")
    settings = Settings.from_env(load_env_file=False)
    provider = create_provider(settings)
    report = process_tickets(
        [
            Ticket(
                ticket_id="LIVE-1",
                subject="Dashboard behavior changed",
                body="A report widget moved after yesterday's update; is this expected?",
            )
        ],
        classifier=TicketClassifier(
            threshold=settings.human_review_threshold,
            provider=provider,
        ),
        settings=settings,
    )
    assert len(report.results) == 1
    assert report.metrics.api_calls == 1
