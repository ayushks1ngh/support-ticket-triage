"""Provider construction from validated settings."""

from support_triage.config import ProviderName, Settings
from support_triage.providers.base import LLMProvider


def create_provider(settings: Settings) -> LLMProvider:
    """Construct the selected adapter lazily to keep the dependency graph acyclic."""

    settings.require_api_key()
    if settings.provider is ProviderName.GROQ:
        from support_triage.providers.groq import GroqProvider

        return GroqProvider(settings)
    if settings.provider is ProviderName.NVIDIA:
        from support_triage.providers.nvidia import NvidiaNimProvider

        return NvidiaNimProvider(settings)
    raise ValueError(f"unsupported provider: {settings.provider}")


__all__ = ["LLMProvider", "create_provider"]
