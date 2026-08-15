"""JSON/CSV ticket and report I/O."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from support_triage.models import BatchReport, InputError, Ticket, model_dump_jsonable

MAX_INPUT_BYTES = 5 * 1024 * 1024
MAX_TICKETS = 1_000


def load_tickets(path: Path) -> tuple[list[Ticket], list[InputError]]:
    if not path.is_file():
        raise ValueError(f"input file does not exist: {path}")
    if path.stat().st_size > MAX_INPUT_BYTES:
        raise ValueError("input file exceeds 5 MiB limit")
    suffix = path.suffix.lower()
    if suffix == ".json":
        records = _load_json(path)
    elif suffix == ".csv":
        records = _load_csv(path)
    else:
        raise ValueError("input must be a .json or .csv file")
    if len(records) > MAX_TICKETS:
        raise ValueError(f"input contains more than {MAX_TICKETS} records")

    tickets: list[Ticket] = []
    errors: list[InputError] = []
    seen: set[str] = set()
    for index, record in enumerate(records):
        candidate_id = record.get("ticket_id") if isinstance(record, dict) else None
        safe_id = candidate_id[:128] if isinstance(candidate_id, str) else None
        try:
            ticket = Ticket.model_validate(record)
            if ticket.ticket_id in seen:
                raise ValueError("duplicate ticket_id")
            seen.add(ticket.ticket_id)
            tickets.append(ticket)
        except (ValidationError, ValueError) as exc:
            errors.append(
                InputError(
                    record_index=index,
                    ticket_id=safe_id,
                    message=_validation_message(exc),
                )
            )
    return tickets, errors


def write_report(report: BatchReport, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    suffix = path.suffix.lower()
    if suffix == ".json":
        path.write_text(
            json.dumps(model_dump_jsonable(report), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return
    if suffix == ".csv":
        _write_csv(report, path)
        return
    raise ValueError("output must be a .json or .csv file")


def _load_json(path: Path) -> list[Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("input is not valid UTF-8 JSON") from exc
    if isinstance(value, dict) and "tickets" in value:
        value = value["tickets"]
    if not isinstance(value, list):
        raise ValueError("JSON input must be an array or an object containing 'tickets'")
    return value


def _load_csv(path: Path) -> list[dict[str, str]]:
    try:
        with path.open(encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream)
            if reader.fieldnames is None or not {"ticket_id", "subject", "body"}.issubset(
                reader.fieldnames
            ):
                raise ValueError("CSV requires ticket_id, subject, and body headers")
            return list(reader)
    except UnicodeDecodeError as exc:
        raise ValueError("input is not valid UTF-8 CSV") from exc


def _write_csv(report: BatchReport, path: Path) -> None:
    fieldnames = [
        "ticket_id",
        "category",
        "urgency",
        "confidence",
        "routing_team",
        "human_review",
        "reason",
        "source",
    ]
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        for result in report.results:
            writer.writerow(result.model_dump(mode="json"))


def _validation_message(exc: Exception) -> str:
    if isinstance(exc, ValidationError):
        messages = []
        for error in exc.errors(include_url=False, include_input=False):
            location = ".".join(str(part) for part in error["loc"])
            messages.append(f"{location}: {error['msg']}")
        return "; ".join(messages)[:500]
    return str(exc)[:500]
