"""Offline tests for the benchmark infrastructure."""

from pathlib import Path

from support_triage.benchmark import (
    ProviderSummary,
    RunResult,
    _aggregate,
    format_comparison,
)
from support_triage.config import ProviderName, Settings
from tests.fakes import FakeProvider


def test_benchmark_runs_with_fake_provider(tmp_path: Path, monkeypatch: object) -> None:
    """Verify benchmark infrastructure without live credentials."""

    from unittest.mock import patch

    from support_triage.benchmark import _single_run
    from support_triage.evaluation import load_evaluation_cases

    dataset = Path("data/evaluation.json")
    cases = load_evaluation_cases(dataset)
    settings = Settings(api_key="fake-key")

    with patch("support_triage.benchmark.create_provider") as mock_create:
        mock_create.return_value = FakeProvider(confidence=0.85)
        result = _single_run(
            cases=cases,
            provider_name=ProviderName.GROQ,
            model_id="fake-model",
            run_index=0,
            settings_base=settings,
        )

    assert result.error is None
    assert result.structured_output_success
    assert result.evaluation.total == 8
    assert result.batch_report.metrics.rule_count == 4


def test_aggregate_handles_failures() -> None:
    from support_triage.benchmark import _empty_batch, _empty_eval

    runs = [
        RunResult(
            provider_name="test",
            model_id="test-model",
            run_index=0,
            evaluation=_empty_eval(8),
            batch_report=_empty_batch(),
            structured_output_success=False,
            error="provider setup failed: no key",
        )
    ]
    summary = _aggregate(runs)
    assert summary.failures == 1
    assert summary.structured_output_success_rate == 0.0
    assert len(summary.errors) == 1


def test_format_comparison_produces_markdown() -> None:
    s = ProviderSummary(
        provider_name="groq",
        model_id="test",
        runs=1,
        exact_accuracy=0.75,
        category_accuracy=0.875,
        urgency_accuracy=0.875,
        routing_accuracy=0.75,
        human_review_precision=0.5,
        human_review_recall=1.0,
        structured_output_success_rate=1.0,
        api_calls=1,
        retries=0,
        failures=0,
        timeout_events=0,
        rule_count=4,
        model_count=4,
        fallback_count=0,
        total_latency_ms=1500.0,
        avg_model_latency_ms=1500.0,
        p95_latency_ms=None,
        malformed_outputs=0,
        errors=[],
    )
    table = format_comparison({"groq/test": s})
    assert "| Exact accuracy |" in table
    assert "0.750" in table
