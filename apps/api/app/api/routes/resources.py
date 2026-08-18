from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, status
from fastapi import File as FastAPIFile

from app.adapters.document_parser import RealResourceImporter
from app.core.config import get_settings
from app.core.dependencies import get_chunk_store, get_rag_service, get_resource_importer
from app.domain.enums import ContentType, Language, ParseStatus
from app.domain.models import (
    ChunkMetadata,
    ResourceImportRequest,
    ResourceImportResponse,
    ResourceSummary,
    ResourceUploadResponse,
)
from app.services.ports import ChunkStore, ResourceImporter
from app.services.rag import RagService

router = APIRouter(prefix="/resources", tags=["resources"])


@router.post("/import", response_model=ResourceImportResponse, status_code=status.HTTP_202_ACCEPTED)
def import_resource(
    request: ResourceImportRequest,
    importer: Annotated[ResourceImporter, Depends(get_resource_importer)],
) -> ResourceImportResponse:
    return importer.import_resource(request)


@router.post("/upload", response_model=ResourceUploadResponse, status_code=status.HTTP_201_CREATED)
def upload_and_parse(
    file: UploadFile = FastAPIFile(..., description="课程文件（PDF/PPT/SRT/VTT）"),  # noqa: B008
    course_id: str = Form(..., description="课程 ID"),
    title: str = Form(..., description="资料标题"),
    version: str = Form("v1", description="版本号"),
    language: str = Form("zh", description="语言：zh/en/bilingual"),
    content_type: str = Form(..., description="文件类型：pdf/ppt/subtitle"),
    knowledge_point_ids: str = Form("", description="知识点 ID，逗号分隔"),
    chunk_store: Annotated[ChunkStore, Depends(get_chunk_store)] = None,
    rag_service: Annotated[RagService, Depends(get_rag_service)] = None,
) -> ResourceUploadResponse:
    """上传课程文件，自动解析、切块、向量化入库。

    支持 PDF、PPT（.pptx）、SRT 和 VTT 字幕文件。
    解析后的 Chunk 会存入 ChunkStore，并增量写入向量库，
    使新导入的资料可以立即被问答检索和引用。
    """
    settings = get_settings()

    # 验证 content_type
    try:
        ct = ContentType(content_type)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"不支持的 content_type: {content_type}，支持: pdf/ppt/subtitle",
        ) from err

    # 验证 language
    try:
        lang = Language(language)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"不支持的 language: {language}，支持: zh/en/bilingual",
        ) from err

    # 验证文件扩展名
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="文件名不能为空",
        )

    suffix = Path(file.filename).suffix.lower()
    expected_suffixes = {
        ContentType.PDF: [".pdf"],
        ContentType.PPT: [".pptx", ".ppt"],
        ContentType.SUBTITLE: [".srt", ".vtt"],
    }
    if suffix not in expected_suffixes.get(ct, []):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"文件扩展名 {suffix} 与 content_type {content_type} 不匹配，"
            f"期望: {expected_suffixes[ct]}",
        )

    # 解析知识点 ID
    kp_ids = [kp.strip() for kp in knowledge_point_ids.split(",") if kp.strip()] or None

    # 保存上传文件到临时目录
    upload_dir = Path(settings.upload_temp_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    temp_path = upload_dir / file.filename
    try:
        file_content = file.file.read()
        temp_path.write_bytes(file_content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件保存失败: {e!s}",
        ) from e

    # 解析文件
    try:
        importer = RealResourceImporter(
            storage_dir=Path(settings.resource_storage_dir)
        )
        chunks = importer.import_from_file(
            file_path=temp_path,
            course_id=course_id,
            title=title,
            version=version,
            language=lang,
            content_type=ct,
            knowledge_point_ids=kp_ids,
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"文件不存在或无法读取: {file.filename}",
        ) from None
    except ValueError as e:
        return ResourceUploadResponse(
            resource_id="parse-failed",
            filename=file.filename,
            chunk_count=0,
            parse_status=ParseStatus.FAILED,
            chunks=[],
            error=str(e),
        )
    except Exception as e:
        return ResourceUploadResponse(
            resource_id="parse-failed",
            filename=file.filename,
            chunk_count=0,
            parse_status=ParseStatus.FAILED,
            chunks=[],
            error=f"解析异常: {e!s}",
        )
    finally:
        # 清理临时文件
        if temp_path.exists():
            temp_path.unlink()

    # 入库
    if chunk_store and chunks:
        chunk_store.save(chunks, course_id=course_id)

    # 向量化入库：不做这一步，导入的资料就永远检索不到
    indexed_chunks: int | None = None
    if rag_service and chunks:
        indexed_chunks = rag_service.index_chunks(course_id, chunks).indexed_chunks

    resource_id = chunks[0].resource_id if chunks else "no-chunks"

    return ResourceUploadResponse(
        resource_id=resource_id,
        filename=file.filename,
        chunk_count=len(chunks),
        parse_status=ParseStatus.PARSED if chunks else ParseStatus.FAILED,
        chunks=chunks,
        indexed_chunks=indexed_chunks,
        error=None,
    )


@router.get("", response_model=list[ResourceSummary])
def list_resources(
    chunk_store: Annotated[ChunkStore, Depends(get_chunk_store)],
    course_id: str | None = None,
) -> list[ResourceSummary]:
    """列出已导入的课程资料，便于确认解析结果是否入库。"""
    return chunk_store.list_resources(course_id=course_id)


@router.get("/{resource_id}/chunks", response_model=list[ChunkMetadata])
def list_resource_chunks(
    resource_id: str,
    chunk_store: Annotated[ChunkStore, Depends(get_chunk_store)],
) -> list[ChunkMetadata]:
    """读取某份资料解析出的全部 Chunk，用于人工核对切块与引用定位。"""
    chunks = chunk_store.list_by_resource(resource_id)
    if not chunks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"未找到资料或该资料没有 Chunk: {resource_id}",
        )
    return chunks
