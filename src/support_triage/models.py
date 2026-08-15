"""Validated domain and boundary models."""

from __future__ import annotations

from enum import StrEnum
from math import isfinite
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

NonEmpty = Annotated[str, Field(min_length=1)]


class StrictModel(BaseModel):
    """Base model that rejects silent schema drift."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Category(StrEnum):
    ACCOUNT_AUTH = "account_auth"
    BILLING = "billing"
    TECHNICAL = "technical"
    PRODUCT = "product"
    OTHER = "other"


class Urgency(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RoutingTeam(StrEnum):
    ACCOUNT = "Account Support"
    BILLING = "Billing Operations"
    TECHNICAL = "Technical Support"
    PRODUCT = "Product Support"
    GENERAL = "General Support"
    INCIDENT = "Incident Response"


class DecisionSource(StrEnum):
    RULE = "rule"
    LLM = "llm"
    FALLBACK = "fallback"


class Ticket(StrictModel):
    ticket_id: Annotated[str, Field(min_length=1, max_length=128)]
    subject: Annotated[str, Field(min_length=1, max_length=500)]
    body: Annotated[str, Field(min_length=1, max_length=10_000)]


class ModelClassification(StrictModel):
    ticket_id: Annotated[str, Field(min_length=1, max_length=128)]
    category: Category
    urgency: Urgency
    confidence: Annotated[float, Field(ge=0.0, le=1.0)]
    reason: Annotated[str, Field(min_length=1, max_length=300)]

    @field_validator("confidence")
    @classmethod
    def finite_confidence(cls, value: float) -> float:
        if not isfinite(value):
            raise ValueError("confidence must be finite")
        return value


class BatchModelOutput(StrictModel):
    classifications: Annotated[list[ModelClassification], Field(min_length=1, max_length=25)]

    @model_validator(mode="after")
    def unique_ticket_ids(self) -> BatchModelOutput:
        ids = [item.ticket_id for item in self.classifications]
        if len(ids) != len(set(ids)):
            raise ValueError("model output contains duplicate ticket_id values")
        return self


class TicketResult(StrictModel):
    ticket_id: Annotated[str, Field(min_length=1, max_length=128)]
    category: Category
    urgency: Urgency
    confidence: Annotated[float, Field(ge=0.0, le=1.0)]
    routing_team: RoutingTeam
    human_review: bool
    reason: Annotated[str, Field(min_length=1, max_length=500)]
    source: DecisionSource


class InputError(StrictModel):
    record_index: Annotated[int, Field(ge=0)]
    ticket_id: Annotated[str | None, Field(max_length=128)] = None
    message: Annotated[str, Field(min_length=1, max_length=500)]


class RunMetrics(StrictModel):
    request_id: str
    ticket_count: Annotated[int, Field(ge=0)]
    rule_count: Annotated[int, Field(ge=0)]
    model_count: Annotated[int, Field(ge=0)]
    fallback_count: Annotated[int, Field(ge=0)]
    human_review_count: Annotated[int, Field(ge=0)]
    failure_count: Annotated[int, Field(ge=0)]
    api_calls: Annotated[int, Field(ge=0)]
    retries: Annotated[int, Field(ge=0)]
    provider: str
    model_id: str
    batch_size: Annotated[int, Field(ge=1, le=25)]
    latency_ms: Annotated[float, Field(ge=0.0)]


class BatchReport(StrictModel):
    results: list[TicketResult]
    errors: list[InputError] = Field(default_factory=list)
    metrics: RunMetrics


class EvaluationExpected(StrictModel):
    category: Category
    urgency: Urgency
    routing_team: RoutingTeam
    human_review: bool


class EvaluationCase(StrictModel):
    ticket: Ticket
    expected: EvaluationExpected


class EvaluationReport(StrictModel):
    total: int
    exact_accuracy: float
    category_accuracy: float
    urgency_accuracy: float
    routing_accuracy: float
    human_review_precision: float | None
    human_review_recall: float | None
    api_calls: int
    tickets_per_api_call: float | None
    latency_ms: float
    rule_count: int
    model_count: int
    fallback_count: int


def model_dump_jsonable(model: BaseModel) -> dict[str, Any]:
    """Return JSON-compatible model data without custom encoders at call sites."""

    return model.model_dump(mode="json")
