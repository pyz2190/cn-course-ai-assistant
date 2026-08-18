import sys
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.dependencies import (  # noqa: E402
    get_chunk_store,
    get_event_sink,
    get_feedback_store,
    get_knowledge_base_change_store,
    get_qa_service,
    get_rag_service,
    get_task_repository,
)
from app.main import create_app  # noqa: E402


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    get_task_repository.cache_clear()
    get_event_sink.cache_clear()
    get_feedback_store.cache_clear()
    get_knowledge_base_change_store.cache_clear()
    get_chunk_store.cache_clear()
    # QaService 持有 RagService 实例，必须一起失效，否则问答会命中旧索引
    get_rag_service.cache_clear()
    get_qa_service.cache_clear()
    with TestClient(create_app()) as test_client:
        yield test_client
