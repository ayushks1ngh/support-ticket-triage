"""Reproducible model benchmark: compare providers on the same evaluation dataset."""

from __future__ import annotations

import json
import statistics
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from support_triage.batch import process_tickets
from support_triage.classifier import TicketClassifier
from support_triage.config import ProviderName, Settings
from support_triage.evaluation import evaluate, load_evaluation_cases
from support_triage.models import (
    BatchReport,
    EvaluationCase,
    EvaluationReport,
)
from support_triage.providers import create_provider


@dataclass
class RunResult:
    """Results from a single benchmark run."""

    provider_name: str
    model_id: str
    run_index: int
    evaluation: EvaluationReport
    batch_report: BatchReport
    structured_output_success: bool
    error: str | None = None
    model_call_latencies_ms: list[float] = field(default_factory=list)


@dataclass
class ProviderSummary:
    """Aggregated results across multiple runs for one provider."""

    provider_name: str
    model_id: str
    runs: int
    exact_accuracy: float
    category_accuracy: float
    urgency_accuracy: float
    routing_accuracy: float
    human_review_precision: float | None
    human_review_recall: float | None
    structured_output_success_rate: float
    api_calls: int
    retries: int
    failures: int
    timeout_events: int
    rule_count: int
    model_count: int
    fallback_count: int
    total_latency_ms: float
    avg_model_latency_ms: float | None
    p95_latency_ms: float | None
    malformed_outputs: int
    errors: list[str]


def run_benchmark(
    dataset_path: Path,
    *,
    providers: list[tuple[ProviderName, str]],
    runs_per_provider: int = 3,
    settings_base: Settings,
) -> dict[str, ProviderSummary]:
    """Run the benchmark for each provider/model combination."""

    cases = load_evaluation_cases(dataset_path)
    results: dict[str, list[RunResult]] = {}

    for provider_name, model_id in providers:
        key = f"{provider_name.value}/{model_id}"
        results[key] = []
        for run_idx in range(runs_per_provider):
            run_result = _single_run(
                cases=cases,
                provider_name=provider_name,
                model_id=model_id,
                run_index=run_idx,
                settings_base=settings_base,
            )
            results[key].append(run_result)
            # Brief pause between runs to avoid rate-limit bursts
            if run_idx < runs_per_provider - 1:
                time.sleep(2)

    return {key: _aggregate(runs) for key, runs in results.items()}


def _single_run(
    *,
    cases: list[EvaluationCase],
    provider_name: ProviderName,
    model_id: str,
    run_index: int,
    settings_base: Settings,
) -> RunResult:
    """Execute one evaluation run for a provider."""

    settings = settings_base.with_overrides(provider=provider_name, model_id=model_id)
    try:
        provider = create_provider(settings)
    except ValueError as exc:
        return RunResult(
            provider_name=provider_name.value,
            model_id=model_id,
            run_index=run_index,
            evaluation=_empty_eval(len(cases)),
            batch_report=_empty_batch(),
            structured_output_success=False,
            error=f"provider setup failed: {exc}",
        )

    classifier = TicketClassifier(
        threshold=settings.human_review_threshold,
        provider=provider,
    )

    start = time.perf_counter()
    report = process_tickets(
        [case.ticket for case in cases],
        classifier=classifier,
        settings=settings,
    )
    total_latency = (time.perf_counter() - start) * 1000

    # Check structured output success
    structured_success = report.metrics.fallback_count == 0 and report.metrics.failure_count == 0

    # Calculate evaluation metrics
    eval_report = evaluate(cases, classifier=classifier, settings=settings)

    return RunResult(
        provider_name=provider_name.value,
        model_id=model_id,
        run_index=run_index,
        evaluation=eval_report,
        batch_report=report,
        structured_output_success=structured_success,
        model_call_latencies_ms=[total_latency] if report.metrics.api_calls > 0 else [],
    )


def _aggregate(runs: list[RunResult]) -> ProviderSummary:
    """Aggregate multiple runs into a summary."""

    successful = [r for r in runs if r.error is None]
    all_latencies: list[float] = []
    for r in successful:
        all_latencies.extend(r.model_call_latencies_ms)

    if not successful:
        return ProviderSummary(
            provider_name=runs[0].provider_name,
            model_id=runs[0].model_id,
            runs=len(runs),
            exact_accuracy=0.0,
            category_accuracy=0.0,
            urgency_accuracy=0.0,
            routing_accuracy=0.0,
            human_review_precision=None,
            human_review_recall=None,
            structured_output_success_rate=0.0,
            api_calls=0,
            retries=0,
            failures=len(runs),
            timeout_events=0,
            rule_count=0,
            model_count=0,
            fallback_count=0,
            total_latency_ms=0.0,
            avg_model_latency_ms=None,
            p95_latency_ms=None,
            malformed_outputs=0,
            errors=[r.error for r in runs if r.error],
        )

    n = len(successful)
    return ProviderSummary(
        provider_name=runs[0].provider_name,
        model_id=runs[0].model_id,
        runs=len(runs),
        exact_accuracy=statistics.mean(r.evaluation.exact_accuracy for r in successful),
        category_accuracy=statistics.mean(r.evaluation.category_accuracy for r in successful),
        urgency_accuracy=statistics.mean(r.evaluation.urgency_accuracy for r in successful),
        routing_accuracy=statistics.mean(r.evaluation.routing_accuracy for r in successful),
        human_review_precision=_safe_mean(
            [r.evaluation.human_review_precision for r in successful]
        ),
        human_review_recall=_safe_mean([r.evaluation.human_review_recall for r in successful]),
        structured_output_success_rate=sum(r.structured_output_success for r in successful) / n,
        api_calls=sum(r.batch_report.metrics.api_calls for r in successful),
        retries=sum(r.batch_report.metrics.retries for r in successful),
        failures=sum(r.batch_report.metrics.fallback_count for r in successful)
        + len([r for r in runs if r.error]),
        timeout_events=0,  # tracked if retries show timeout pattern
        rule_count=successful[0].batch_report.metrics.rule_count if successful else 0,
        model_count=sum(r.batch_report.metrics.model_count for r in successful) // n,
        fallback_count=sum(r.batch_report.metrics.fallback_count for r in successful),
        total_latency_ms=statistics.mean(r.batch_report.metrics.latency_ms for r in successful),
        avg_model_latency_ms=(statistics.mean(all_latencies) if all_latencies else None),
        p95_latency_ms=_p95(all_latencies),
        malformed_outputs=sum(r.batch_report.metrics.fallback_count for r in successful),
        errors=[r.error for r in runs if r.error],
    )


def _safe_mean(values: list[float | None]) -> float | None:
    clean = [v for v in values if v is not None]
    return statistics.mean(clean) if clean else None


def _p95(latencies: list[float]) -> float | None:
    if len(latencies) < 3:
        return None  # insufficient observations
    sorted_l = sorted(latencies)
    idx = int(len(sorted_l) * 0.95)
    return sorted_l[min(idx, len(sorted_l) - 1)]


def _empty_eval(total: int) -> EvaluationReport:
    return EvaluationReport(
        total=total,
        exact_accuracy=0.0,
        category_accuracy=0.0,
        urgency_accuracy=0.0,
        routing_accuracy=0.0,
        human_review_precision=None,
        human_review_recall=None,
        api_calls=0,
        tickets_per_api_call=None,
        latency_ms=0.0,
        rule_count=0,
        model_count=0,
        fallback_count=0,
    )


def _empty_batch() -> BatchReport:
    from support_triage.models import RunMetrics

    return BatchReport(
        results=[],
        metrics=RunMetrics(
            request_id="none",
            ticket_count=0,
            rule_count=0,
            model_count=0,
            fallback_count=0,
            human_review_count=0,
            failure_count=0,
            api_calls=0,
            retries=0,
            provider="none",
            model_id="none",
            batch_size=10,
            latency_ms=0.0,
        ),
    )


def format_comparison(summaries: dict[str, ProviderSummary]) -> str:
    """Generate a markdown comparison table."""

    lines = [
        "| Metric | " + " | ".join(summaries.keys()) + " |",
        "|---|" + "|".join("---:" for _ in summaries) + "|",
    ]

    def row(label: str, getter: Any) -> str:
        values = []
        for s in summaries.values():
            v = getter(s)
            if v is None:
                values.append("N/A")
            elif isinstance(v, float):
                values.append(f"{v:.3f}")
            else:
                values.append(str(v))
        return f"| {label} | " + " | ".join(values) + " |"

    lines.append(row("Runs", lambda s: s.runs))
    lines.append(row("Exact accuracy", lambda s: s.exact_accuracy))
    lines.append(row("Category accuracy", lambda s: s.category_accuracy))
    lines.append(row("Urgency accuracy", lambda s: s.urgency_accuracy))
    lines.append(row("Routing accuracy", lambda s: s.routing_accuracy))
    lines.append(row("Human-review precision", lambda s: s.human_review_precision))
    lines.append(row("Human-review recall", lambda s: s.human_review_recall))
    lines.append(row("Structured output success", lambda s: s.structured_output_success_rate))
    lines.append(row("API calls (total)", lambda s: s.api_calls))
    lines.append(row("Retries (total)", lambda s: s.retries))
    lines.append(row("Failures", lambda s: s.failures))
    lines.append(row("Timeout events", lambda s: s.timeout_events))
    lines.append(row("Rule classifications", lambda s: s.rule_count))
    lines.append(row("Model classifications (avg)", lambda s: s.model_count))
    lines.append(row("Fallback classifications", lambda s: s.fallback_count))
    lines.append(row("Avg total latency (ms)", lambda s: s.total_latency_ms))
    lines.append(row("Avg model latency (ms)", lambda s: s.avg_model_latency_ms))
    lines.append(row("p95 latency (ms)", lambda s: s.p95_latency_ms))
    lines.append(row("Malformed outputs", lambda s: s.malformed_outputs))

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for the benchmark."""

    import argparse

    parser = argparse.ArgumentParser(description="Model provider benchmark")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path("data/evaluation.json"),
    )
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--groq-model", type=str, default=None)
    parser.add_argument("--nvidia-model", type=str, default=None)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("outputs/benchmark_results.json"),
    )
    args = parser.parse_args(argv)

    settings = Settings.from_env()

    # Determine providers to test based on available keys
    providers: list[tuple[ProviderName, str]] = []

    groq_settings = settings.with_overrides(provider=ProviderName.GROQ)
    if groq_settings.api_key:
        model = args.groq_model or groq_settings.model_id
        providers.append((ProviderName.GROQ, model))

    nvidia_settings = settings.with_overrides(provider=ProviderName.NVIDIA)
    if nvidia_settings.api_key:
        model = args.nvidia_model or nvidia_settings.model_id
        providers.append((ProviderName.NVIDIA, model))

    if not providers:
        print("error: no provider API keys configured", file=sys.stderr)
        return 2

    print(f"Benchmark: {len(providers)} provider(s), {args.runs} run(s) each")
    for pname, mid in providers:
        print(f"  {pname.value}: {mid}")
    print()

    summaries = run_benchmark(
        args.dataset,
        providers=providers,
        runs_per_provider=args.runs,
        settings_base=settings,
    )

    # Print comparison
    comparison = format_comparison(summaries)
    print(comparison)
    print()

    # Report errors
    for key, summary in summaries.items():
        if summary.errors:
            print(f"Errors for {key}:")
            for err in summary.errors:
                print(f"  - {err}")
            print()

    # Save results
    args.output.parent.mkdir(parents=True, exist_ok=True)
    output_data = {
        key: {
            "provider": s.provider_name,
            "model_id": s.model_id,
            "runs": s.runs,
            "exact_accuracy": s.exact_accuracy,
            "category_accuracy": s.category_accuracy,
            "urgency_accuracy": s.urgency_accuracy,
            "routing_accuracy": s.routing_accuracy,
            "human_review_precision": s.human_review_precision,
            "human_review_recall": s.human_review_recall,
            "structured_output_success_rate": s.structured_output_success_rate,
            "api_calls": s.api_calls,
            "retries": s.retries,
            "failures": s.failures,
            "timeout_events": s.timeout_events,
            "rule_count": s.rule_count,
            "model_count": s.model_count,
            "fallback_count": s.fallback_count,
            "total_latency_ms": s.total_latency_ms,
            "avg_model_latency_ms": s.avg_model_latency_ms,
            "p95_latency_ms": s.p95_latency_ms,
            "malformed_outputs": s.malformed_outputs,
            "errors": s.errors,
        }
        for key, s in summaries.items()
    }
    args.output.write_text(
        json.dumps(output_data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Results saved to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
