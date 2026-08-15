"""Batch chunking, bounded concurrency, ordering, and metrics."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from time import perf_counter
from uuid import uuid4

from support_triage.classifier import TicketClassifier
from support_triage.config import Settings
from support_triage.models import BatchReport, DecisionSource, InputError, RunMetrics, Ticket


def process_tickets(
    tickets: list[Ticket],
    *,
    classifier: TicketClassifier,
    settings: Settings,
    input_errors: list[InputError] | None = None,
) -> BatchReport:
    started = perf_counter()
    by_id = {ticket.ticket_id: ticket for ticket in tickets}
    if len(by_id) != len(tickets):
        raise ValueError("ticket IDs must be unique")

    result_by_id = {}
    unresolved: list[Ticket] = []
    for ticket in tickets:
        result = classifier.classify_rule(ticket)
        if result is None:
            unresolved.append(ticket)
        else:
            result_by_id[ticket.ticket_id] = result

    chunks = [
        unresolved[index : index + settings.batch_size]
        for index in range(0, len(unresolved), settings.batch_size)
    ]
    retries = 0
    if chunks and settings.max_concurrency > 1:
        with ThreadPoolExecutor(max_workers=settings.max_concurrency) as executor:
            futures = {
                executor.submit(classifier.classify_model_chunk, chunk): chunk for chunk in chunks
            }
            for future in as_completed(futures):
                results, chunk_retries = future.result()
                retries += chunk_retries
                result_by_id.update((result.ticket_id, result) for result in results)
    else:
        for chunk in chunks:
            results, chunk_retries = classifier.classify_model_chunk(chunk)
            retries += chunk_retries
            result_by_id.update((result.ticket_id, result) for result in results)

    ordered = [result_by_id[ticket.ticket_id] for ticket in tickets]
    errors = input_errors or []
    rule_count = sum(result.source is DecisionSource.RULE for result in ordered)
    model_count = sum(result.source is DecisionSource.LLM for result in ordered)
    fallback_count = sum(result.source is DecisionSource.FALLBACK for result in ordered)
    provider = classifier.provider
    metrics = RunMetrics(
        request_id=str(uuid4()),
        ticket_count=len(tickets),
        rule_count=rule_count,
        model_count=model_count,
        fallback_count=fallback_count,
        human_review_count=sum(result.human_review for result in ordered),
        failure_count=len(errors) + fallback_count,
        api_calls=len(chunks) if provider is not None else 0,
        retries=retries,
        provider=provider.name if provider is not None else "offline",
        model_id=provider.model_id if provider is not None else "none",
        batch_size=settings.batch_size,
        latency_ms=round((perf_counter() - started) * 1000, 3),
    )
    return BatchReport(results=ordered, errors=errors, metrics=metrics)
