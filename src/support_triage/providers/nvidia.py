"""NVIDIA NIM adapter through Strands' OpenAI-compatible provider."""

from support_triage.agent import StrandsTicketAgent
from support_triage.config import ProviderName, Settings
from support_triage.models import Ticket
from support_triage.providers.base import LLMProvider, ProviderResponse


class NvidiaNimProvider(LLMProvider):
    def __init__(self, settings: Settings) -> None:
        if settings.provider is not ProviderName.NVIDIA:
            raise ValueError("NvidiaNimProvider requires MODEL_PROVIDER=nvidia")
        self._settings = settings
        self._agent = StrandsTicketAgent(settings)

    @property
    def name(self) -> str:
        return ProviderName.NVIDIA.value

    @property
    def model_id(self) -> str:
        return self._settings.model_id

    def classify(self, tickets: list[Ticket]) -> ProviderResponse:
        return self._agent.classify(tickets)
