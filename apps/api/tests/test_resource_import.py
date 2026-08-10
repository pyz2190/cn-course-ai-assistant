"""B 模块测试：资源导入与 Chunk 元数据。"""

from app.adapters.mock import MOCK_CHUNKS, MOCK_RESOURCES, MockResourceImporter
from app.domain.enums import (
    AccessLevel,
    ContentType,
    Language,
    ParseStatus,
    SyncStatus,
)
from app.domain.models import ResourceImportRequest

importer = MockResourceImporter()

SAMPLE_REQUEST = ResourceImportRequest(
    course_id="course-cn-2026",
    resource_type="textbook",
    title="计算机网络：自顶向下方法",
    version="8e-zh",
    language=Language.ZH,
    content_type=ContentType.PDF,
)


def test_import_returns_completed_status():
    resp = importer.import_resource(SAMPLE_REQUEST)
    assert resp.sync_status == SyncStatus.COMPLETED
    assert resp.error is None


def test_import_returns_valid_chunk_metadata():
    resp = importer.import_resource(SAMPLE_REQUEST)
    meta = resp.metadata
    assert meta is not None
    assert meta.chunk_id
    assert meta.resource_id
    assert meta.title == "计算机网络：自顶向下方法"
    assert meta.chapter.startswith("第")
    assert meta.page_start >= 1
    assert meta.page_end >= meta.page_start
    assert meta.language == Language.ZH
    assert meta.content_type == ContentType.PDF
    assert meta.access_level == AccessLevel.COURSE
    assert meta.parse_status == ParseStatus.PARSED


def test_import_known_resource_has_real_content():
    resp = importer.import_resource(SAMPLE_REQUEST)
    meta = resp.metadata
    assert "骨架" not in meta.content
    assert "待人工审核" not in meta.chapter
    assert len(meta.content) > 20


def test_import_unknown_resource_returns_pending():
    req = ResourceImportRequest(
        course_id="course-cn-2026",
        resource_type="other",
        title="不存在的资料",
        version="v1",
        language=Language.ZH,
        content_type=ContentType.TEXT,
    )
    resp = importer.import_resource(req)
    assert resp.metadata is not None
    assert resp.metadata.parse_status == ParseStatus.PENDING
    assert resp.metadata.chapter == "待人工审核"


def test_import_all_chunks_returns_multiple():
    chunks = importer.import_all_chunks(SAMPLE_REQUEST)
    assert len(chunks) > 1
    assert all(c.resource_id == chunks[0].resource_id for c in chunks)
    assert all(c.title == "计算机网络：自顶向下方法" for c in chunks)


def test_all_mock_chunks_have_traceable_metadata():
    for chunk in MOCK_CHUNKS:
        assert chunk.chunk_id, "missing chunk_id"
        assert chunk.resource_id, "missing resource_id"
        assert chunk.knowledge_point_ids, f"{chunk.chunk_id} has no knowledge points"
        assert chunk.chapter and chunk.chapter != "待人工审核"
        assert chunk.page_start is not None
        assert chunk.content


def test_mock_resources_cover_all_chapters():
    all_chapters = {c["chapter"] for chunks in MOCK_RESOURCES.values() for c in chunks}
    assert any("第 2 章" in ch for ch in all_chapters), "missing application layer"
    assert any("第 3 章" in ch for ch in all_chapters), "missing transport layer"
    assert any("第 4 章" in ch for ch in all_chapters), "missing network layer"


def test_mock_chunks_have_unique_ids():
    ids = [c.chunk_id for c in MOCK_CHUNKS]
    assert len(ids) == len(set(ids)), "duplicate chunk_id found"


def test_resource_index_is_consistent():
    from app.adapters.mock import RESOURCE_INDEX

    assert set(RESOURCE_INDEX.keys()) == set(MOCK_RESOURCES.keys())
