import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    cors_origins: tuple[str, ...]
    model_provider: str
    vector_store: str
    resource_importer: str
    resource_storage_dir: str
    upload_temp_dir: str


def get_settings() -> Settings:
    origins = os.getenv(
        "CN_AI_CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    )
    return Settings(
        cors_origins=tuple(origin.strip() for origin in origins.split(",") if origin.strip()),
        model_provider=os.getenv("CN_AI_MODEL_PROVIDER", "mock"),
        vector_store=os.getenv("CN_AI_VECTOR_STORE", "mock"),
        resource_importer=os.getenv("CN_AI_RESOURCE_IMPORTER", "real"),
        resource_storage_dir=os.getenv("CN_AI_RESOURCE_STORAGE_DIR", "data/resources"),
        upload_temp_dir=os.getenv("CN_AI_UPLOAD_TEMP_DIR", "data/uploads"),
    )
