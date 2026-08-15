"""Provider-independent LLM classification contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from support_triage.models import BatchModelOutput, Ticket


class ProviderError(RuntimeError):
    """Sanitized external classification failure with retry metadata."""

    def __init__(self, message: str, *, retry_count: int = 0) -> None:
        super().__init__(message)
        self.retry_count = retry_count


@dataclass(frozen=True)
class ProviderResponse:
    output: BatchModelOutput
    retry_count: int = 0


class LLMProvider(ABC):
    """Minimal provider interface consumed by batch orchestration."""

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def model_id(self) -> str: ...

    @abstractmethod
    def classify(self, tickets: list[Ticket]) -> ProviderResponse: ...
