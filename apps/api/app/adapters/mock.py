from datetime import UTC, datetime
from uuid import NAMESPACE_URL, uuid4, uuid5

from app.domain.enums import (
    AccessLevel,
    ContentType,
    Language,
    ParseStatus,
    SyncStatus,
    TaskStatus,
    TaskType,
)
from app.domain.models import (
    AskResponse,
    ChunkMetadata,
    Citation,
    LearningEvent,
    ResourceImportRequest,
    ResourceImportResponse,
    TaskTemplate,
)

MOCK_CHUNKS = [
    ChunkMetadata(
        chunk_id="chunk-tcp-handshake-001",
        resource_id="resource-cn-textbook-001",
        knowledge_point_ids=["kp-transport-tcp-handshake"],
        title="计算机网络：自顶向下方法",
        content=(
            "TCP 使用三次握手同步双方的初始序列号，并确认客户端与服务器两个方向的"
            "发送和接收能力都可用。"
        ),
        chapter="第 3 章 运输层",
        page_start=214,
        page_end=215,
        language=Language.ZH,
        content_type=ContentType.PDF,
        source_url=None,
        version="8e-zh",
        access_level=AccessLevel.COURSE,
        parse_status=ParseStatus.PARSED,
        updated_at=datetime(2026, 7, 28, tzinfo=UTC),
    )
]


def _task(
    task_id: str,
    title: str,
    description: str,
    task_type: TaskType,
    knowledge_point: str,
    criterion: str,
    feedback: str,
) -> TaskTemplate:
    return TaskTemplate(
        task_id=task_id,
        title=title,
        description=description,
        task_type=task_type,
        knowledge_point_ids=[knowledge_point],
        resource_ids=["resource-cn-textbook-001"],
        prerequisite_ids=[],
        completion_criteria=[criterion],
        ai_feedback_points=[feedback],
        status=TaskStatus.PUBLISHED,
    )


MOCK_TASKS = [
    _task(
        "task-foundation-addressing",
        "网络层寻址路径学习",
        "沿知识点路径理解 IP 地址、子网与路由表。",
        TaskType.FOUNDATION,
        "kp-network-addressing",
        "完成知识点自测并解释最长前缀匹配。",
        "自测错误时提示回看对应章节。",
    ),
    _task(
        "task-protocol-tcp-handshake",
        "Wireshark 分析 TCP 三次握手",
        "从抓包中定位 SYN、SYN-ACK 与 ACK。",
        TaskType.PROTOCOL_ANALYSIS,
        "kp-transport-tcp-handshake",
        "标注三类报文并解释序列号变化。",
        "提交报文编号后检查握手顺序。",
    ),
    _task(
        "task-case-congestion",
        "Reno 与 BBR 拥塞控制案例",
        "比较丢包驱动和带宽时延模型驱动的拥塞控制。",
        TaskType.CASE_STUDY,
        "kp-transport-congestion-control",
        "给出两种算法在目标与信号上的差异。",
        "比较表缺项时提示从控制信号补充。",
    ),
    _task(
        "task-innovation-edge",
        "边缘计算负载均衡挑战",
        "设计兼顾时延和故障切换的边缘负载均衡策略。",
        TaskType.INNOVATION_CHALLENGE,
        "kp-application-load-balancing",
        "提交架构图、关键指标和权衡说明。",
        "在选择策略后追问故障场景。",
    ),
    _task(
        "task-project-smart-home",
        "智能家居网络设计",
        "为给定户型和设备清单设计网络拓扑与协议选型。",
        TaskType.PROJECT_PRACTICE,
        "kp-network-design",
        "提交拓扑、地址规划和安全边界。",
        "检测单点故障与地址冲突。",
    ),
    _task(
        "task-troubleshooting-dns",
        "DNS 解析异常排错",
        "根据抓包和配置片段定位域名解析失败原因。",
        TaskType.TROUBLESHOOTING,
        "kp-application-dns",
        "给出故障根因、证据和修复步骤。",
        "每完成一个排查步骤后反馈证据充分性。",
    ),
]


class MockResourceImporter:
    def import_resource(self, request: ResourceImportRequest) -> ResourceImportResponse:
        resource_key = f"{request.course_id}:{request.title}:{request.version}"
        resource_id = f"resource-{uuid5(NAMESPACE_URL, resource_key).hex[:12]}"
        metadata = ChunkMetadata(
            chunk_id=f"chunk-{uuid5(NAMESPACE_URL, resource_id).hex[:12]}",
            resource_id=resource_id,
            knowledge_point_ids=["kp-pending-review"],
            title=request.title,
            content="这是骨架生成的离线模拟 Chunk，正式解析由知识库与语料模块实现。",
            chapter="待人工审核",
            page_start=1,
            page_end=1,
            language=request.language,
            content_type=request.content_type,
            source_url=request.source_url,
            version=request.version,
            access_level=AccessLevel.COURSE,
            parse_status=ParseStatus.PARSED,
            updated_at=datetime.now(UTC),
        )
        return ResourceImportResponse(
            resource_id=resource_id,
            sync_status=SyncStatus.COMPLETED,
            metadata=metadata,
            error=None,
        )


class MockRetriever:
    def retrieve(self, question: str, course_id: str) -> list[ChunkMetadata]:
        del question, course_id
        return MOCK_CHUNKS.copy()


class MockAnswerGenerator:
    def generate(self, question: str, chunks: list[ChunkMetadata]) -> AskResponse:
        del question
        chunk = chunks[0]
        citation = Citation(
            citation_id=f"citation-{chunk.chunk_id}",
            chunk_id=chunk.chunk_id,
            resource_id=chunk.resource_id,
            title=chunk.title,
            chapter=chunk.chapter,
            page_start=chunk.page_start,
            page_end=chunk.page_end,
            quote=chunk.content,
            source_url=chunk.source_url,
        )
        return AskResponse(
            answer=(
                "TCP 采用三次握手，是为了同步双方的初始序列号，并分别确认双向通信能力。"
                "当前回答来自离线 Mock 检索链路。"
            ),
            citations=[citation],
            confidence=0.92,
            request_id=f"req-{uuid4().hex}",
        )


class InMemoryTaskRepository:
    def list_tasks(self) -> list[TaskTemplate]:
        return MOCK_TASKS.copy()

    def get_task(self, task_id: str) -> TaskTemplate | None:
        return next((task for task in MOCK_TASKS if task.task_id == task_id), None)


class InMemoryEventSink:
    def __init__(self) -> None:
        self.events: list[LearningEvent] = []

    def record(self, event: LearningEvent) -> LearningEvent:
        self.events.append(event)
        return event
