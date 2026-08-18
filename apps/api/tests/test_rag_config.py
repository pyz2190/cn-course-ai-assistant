import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_offline_settings_are_safe_by_default() -> None:
    settings = Settings()

    assert settings.mode == "offline"
    assert settings.vector_store == "memory"
    assert settings.embedding_provider == "offline"
    assert settings.generator_provider == "offline"
    assert settings.model_api_key is None
    assert settings.fetch_k >= settings.top_k


def test_settings_parse_comma_separated_origins() -> None:
    settings = Settings(cors_origins="https://one.example, https://two.example")

    assert settings.cors_origins == ("https://one.example", "https://two.example")


def test_remote_qdrant_requires_url() -> None:
    with pytest.raises(ValidationError, match="qdrant_url"):
        Settings(vector_store="remote")


def test_external_mode_requires_generator_and_url() -> None:
    with pytest.raises(ValidationError, match="openai-compatible"):
        Settings(mode="external")

    settings = Settings(
        mode="external",
        generator_provider="openai-compatible",
        model_base_url="https://model.example/v1",
    )
    assert settings.mode == "external"


def test_fetch_k_cannot_be_smaller_than_top_k() -> None:
    with pytest.raises(ValidationError, match="fetch_k"):
        Settings(top_k=5, fetch_k=4)
