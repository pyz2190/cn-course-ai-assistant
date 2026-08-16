from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validated RAG settings loaded from ``CN_AI_*`` environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="CN_AI_",
        case_sensitive=False,
        extra="ignore",
    )

    cors_origins: tuple[str, ...] = (
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    )
    mode: Literal["offline", "external"] = "offline"
    vector_store: Literal["memory", "local", "remote"] = "memory"
    qdrant_path: Path = Path(".data/qdrant")
    qdrant_url: str | None = None
    qdrant_api_key: SecretStr | None = None
    qdrant_collection_prefix: str = "cn_ai"

    embedding_provider: Literal["offline", "bge"] = "offline"
    embedding_model: str = "BAAI/bge-m3"
    offline_embedding_dimension: int = Field(default=384, ge=32, le=4096)
    reranker_enabled: bool = True
    reranker_provider: Literal["offline", "bge"] = "offline"
    reranker_model: str = "BAAI/bge-reranker-v2-m3"

    generator_provider: Literal["offline", "openai-compatible"] = "offline"
    generator_model: str = "offline-extractive-v1"
    model_base_url: str | None = None
    model_api_key: SecretStr | None = None

    top_k: int = Field(default=3, ge=1, le=10)
    fetch_k: int = Field(default=8, ge=1, le=50)
    min_retrieval_score: float = Field(default=0.15, ge=0, le=1)
    allow_degraded: bool = True
    connect_timeout_seconds: float = Field(default=3, gt=0, le=60)
    read_timeout_seconds: float = Field(default=30, gt=0, le=300)
    write_timeout_seconds: float = Field(default=10, gt=0, le=300)
    pool_timeout_seconds: float = Field(default=3, gt=0, le=60)
    max_retries: int = Field(default=1, ge=0, le=3)

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return tuple(item.strip() for item in value.split(",") if item.strip())
        return value

    @model_validator(mode="after")
    def validate_component_configuration(self) -> "Settings":
        if self.fetch_k < self.top_k:
            raise ValueError("fetch_k must be greater than or equal to top_k")
        if self.vector_store == "remote" and not self.qdrant_url:
            raise ValueError("qdrant_url is required for remote vector store")
        if self.mode == "external":
            if self.generator_provider != "openai-compatible":
                raise ValueError("external mode requires the openai-compatible generator")
            if not self.model_base_url:
                raise ValueError("model_base_url is required in external mode")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
