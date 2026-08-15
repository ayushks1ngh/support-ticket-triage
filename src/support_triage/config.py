"""Environment-backed application configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass, replace
from enum import StrEnum

from dotenv import load_dotenv


class ProviderName(StrEnum):
    GROQ = "groq"
    NVIDIA = "nvidia"


DEFAULT_MODELS = {
    ProviderName.GROQ: "llama-3.3-70b-versatile",
    ProviderName.NVIDIA: "nvidia/nemotron-3-nano-30b-a3b",
}
DEFAULT_BASE_URLS = {
    ProviderName.GROQ: "https://api.groq.com/openai/v1",
    ProviderName.NVIDIA: "https://integrate.api.nvidia.com/v1",
}
KEY_ENV = {
    ProviderName.GROQ: "GROQ_API_KEY",
    ProviderName.NVIDIA: "NVIDIA_API_KEY",
}


@dataclass(frozen=True)
class Settings:
    provider: ProviderName = ProviderName.GROQ
    model_id: str = DEFAULT_MODELS[ProviderName.GROQ]
    api_key: str | None = None
    base_url: str = DEFAULT_BASE_URLS[ProviderName.GROQ]
    human_review_threshold: float = 0.75
    batch_size: int = 10
    max_concurrency: int = 1
    max_retry_attempts: int = 3
    retry_initial_delay: int = 1
    retry_max_delay: int = 8
    model_max_tokens: int = 4096
    model_temperature: float = 0.01
    request_timeout: int = 30

    def __post_init__(self) -> None:
        if not self.model_id.strip():
            raise ValueError("MODEL_ID must not be empty")
        if not 0.0 <= self.human_review_threshold <= 1.0:
            raise ValueError("HUMAN_REVIEW_THRESHOLD must be between 0 and 1")
        if not 1 <= self.batch_size <= 25:
            raise ValueError("BATCH_SIZE must be between 1 and 25")
        if not 1 <= self.max_concurrency <= 4:
            raise ValueError("MAX_CONCURRENCY must be between 1 and 4")
        if not 1 <= self.max_retry_attempts <= 5:
            raise ValueError("MAX_RETRY_ATTEMPTS must be between 1 and 5")
        if not 0 <= self.retry_initial_delay <= 30:
            raise ValueError("RETRY_INITIAL_DELAY_SECONDS must be between 0 and 30")
        if not self.retry_initial_delay <= self.retry_max_delay <= 120:
            raise ValueError("RETRY_MAX_DELAY_SECONDS must be >= initial delay and <= 120")
        if not 256 <= self.model_max_tokens <= 16_384:
            raise ValueError("MODEL_MAX_TOKENS must be between 256 and 16384")
        if not 0.0 <= self.model_temperature <= 2.0:
            raise ValueError("MODEL_TEMPERATURE must be between 0 and 2")
        if not 5 <= self.request_timeout <= 120:
            raise ValueError("REQUEST_TIMEOUT_SECONDS must be between 5 and 120")

    @classmethod
    def from_env(cls, *, load_env_file: bool = True) -> Settings:
        if load_env_file:
            load_dotenv()
        raw_provider = os.getenv("MODEL_PROVIDER", ProviderName.GROQ.value).lower()
        try:
            provider = ProviderName(raw_provider)
        except ValueError as exc:
            raise ValueError("MODEL_PROVIDER must be 'groq' or 'nvidia'") from exc
        model_id = os.getenv("MODEL_ID") or DEFAULT_MODELS[provider]
        base_url = os.getenv("MODEL_BASE_URL") or DEFAULT_BASE_URLS[provider]
        return cls(
            provider=provider,
            model_id=model_id,
            api_key=os.getenv(KEY_ENV[provider]) or None,
            base_url=base_url,
            human_review_threshold=_float_env("HUMAN_REVIEW_THRESHOLD", 0.75),
            batch_size=_int_env("BATCH_SIZE", 10),
            max_concurrency=_int_env("MAX_CONCURRENCY", 1),
            max_retry_attempts=_int_env("MAX_RETRY_ATTEMPTS", 3),
            retry_initial_delay=_int_env("RETRY_INITIAL_DELAY_SECONDS", 1),
            retry_max_delay=_int_env("RETRY_MAX_DELAY_SECONDS", 8),
            model_max_tokens=_int_env("MODEL_MAX_TOKENS", 4096),
            model_temperature=_float_env("MODEL_TEMPERATURE", 0.01),
            request_timeout=_int_env("REQUEST_TIMEOUT_SECONDS", 30),
        )

    def require_api_key(self) -> str:
        if not self.api_key:
            raise ValueError(f"{KEY_ENV[self.provider]} is required for online mode")
        return self.api_key

    def with_overrides(
        self,
        *,
        provider: ProviderName | None = None,
        model_id: str | None = None,
        threshold: float | None = None,
        batch_size: int | None = None,
    ) -> Settings:
        selected = provider or self.provider
        provider_changed = provider is not None and provider != self.provider
        return replace(
            self,
            provider=selected,
            model_id=model_id or (DEFAULT_MODELS[selected] if provider_changed else self.model_id),
            api_key=(os.getenv(KEY_ENV[selected]) or None) if provider_changed else self.api_key,
            base_url=DEFAULT_BASE_URLS[selected] if provider_changed else self.base_url,
            human_review_threshold=(
                threshold if threshold is not None else self.human_review_threshold
            ),
            batch_size=batch_size if batch_size is not None else self.batch_size,
        )


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc


def _float_env(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError as exc:
        raise ValueError(f"{name} must be a number") from exc
