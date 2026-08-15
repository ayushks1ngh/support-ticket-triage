from pathlib import Path

import pytest

from support_triage.io import load_tickets, write_report
from support_triage.models import BatchReport, InputError, RunMetrics


def test_json_load_reports_malformed_and_duplicate_records(tmp_path: Path) -> None:
    path = tmp_path / "tickets.json"
    path.write_text(
        '[{"ticket_id":"T","subject":"x","body":"y"},'
        '{"ticket_id":"T","subject":"again","body":"y"},'
        '{"ticket_id":"M","subject":"","body":"y"}]',
        encoding="utf-8",
    )
    tickets, errors = load_tickets(path)
    assert [ticket.ticket_id for ticket in tickets] == ["T"]
    assert len(errors) == 2


def test_csv_requires_headers(tmp_path: Path) -> None:
    path = tmp_path / "tickets.csv"
    path.write_text("id,title\n1,test\n", encoding="utf-8")
    with pytest.raises(ValueError, match="requires"):
        load_tickets(path)


def test_csv_report_writes_results_only(tmp_path: Path) -> None:
    report = BatchReport(
        results=[],
        errors=[InputError(record_index=0, message="bad")],
        metrics=RunMetrics(
            request_id="R",
            ticket_count=0,
            rule_count=0,
            model_count=0,
            fallback_count=0,
            human_review_count=0,
            failure_count=1,
            api_calls=0,
            retries=0,
            provider="offline",
            model_id="none",
            batch_size=10,
            latency_ms=0,
        ),
    )
    output = tmp_path / "report.csv"
    write_report(report, output)
    assert output.read_text(encoding="utf-8").startswith("ticket_id,category")
