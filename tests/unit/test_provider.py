from support_triage.config import ProviderName, Settings
from support_triage.providers import create_provider
from support_triage.providers.groq import GroqProvider
from support_triage.providers.nvidia import NvidiaNimProvider


def test_factory_builds_groq_without_network() -> None:
    provider = create_provider(Settings(api_key="test-placeholder"))
    assert isinstance(provider, GroqProvider)
    assert provider.name == "groq"


def test_factory_builds_nvidia_without_network() -> None:
    provider = create_provider(
        Settings(
            provider=ProviderName.NVIDIA,
            model_id="test-model",
            base_url="https://integrate.api.nvidia.com/v1",
            api_key="test-placeholder",
        )
    )
    assert isinstance(provider, NvidiaNimProvider)
    assert provider.name == "nvidia"
