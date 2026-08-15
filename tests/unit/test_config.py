import pytest

from support_triage.config import DEFAULT_BASE_URLS, DEFAULT_MODELS, ProviderName, Settings


def test_provider_specific_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MODEL_PROVIDER", "nvidia")
    monkeypatch.delenv("MODEL_ID", raising=False)
    monkeypatch.delenv("MODEL_BASE_URL", raising=False)
    settings = Settings.from_env(load_env_file=False)
    assert settings.model_id == DEFAULT_MODELS[ProviderName.NVIDIA]
    assert settings.base_url == DEFAULT_BASE_URLS[ProviderName.NVIDIA]


def test_missing_key_is_safe_error() -> None:
    with pytest.raises(ValueError, match="GROQ_API_KEY"):
        Settings().require_api_key()


def test_invalid_bounds() -> None:
    with pytest.raises(ValueError, match="BATCH_SIZE"):
        Settings(batch_size=0)
    with pytest.raises(ValueError, match="HUMAN_REVIEW_THRESHOLD"):
        Settings(human_review_threshold=1.1)
    with pytest.raises(ValueError, match="MAX_CONCURRENCY"):
        Settings(max_concurrency=5)


def test_invalid_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MODEL_PROVIDER", "unknown")
    with pytest.raises(ValueError, match="groq.*nvidia"):
        Settings.from_env(load_env_file=False)
