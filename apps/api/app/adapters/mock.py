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
    AnswerFeedback,
    AskResponse,
    ChunkMetadata,
    Citation,
    KnowledgeBaseChangeTask,
    LearningEvent,
    QualityReview,
    ResourceImportRequest,
    ResourceImportResponse,
    ResourceSummary,
    TaskTemplate,
)

MOCK_RESOURCES_EN: dict[str, list[dict]] = {
    "Computer Networking: A Top-Down Approach": [
        {
            "chunk_id": "chunk-app-http-001-en",
            "knowledge_point_ids": ["kp-application-http"],
            "content": (
                "HTTP uses TCP as its transport-layer protocol. "
                "After the client establishes a connection, "
                "messages are exchanged in a request-response pattern. "
                "A request message consists of a request line, "
                "header lines, and an entity body."
            ),
            "chapter": "Chapter 2 Application Layer",
            "page_start": 68,
            "page_end": 72,
        },
        {
            "chunk_id": "chunk-app-dns-001-en",
            "knowledge_point_ids": ["kp-application-dns"],
            "content": (
                "DNS is a distributed database with a hierarchical "
                "namespace. Recursive and iterative queries are the "
                "two main resolution methods. Local DNS servers "
                "typically cache query results to reduce latency."
            ),
            "chapter": "Chapter 2 Application Layer",
            "page_start": 93,
            "page_end": 98,
        },
        {
            "chunk_id": "chunk-transport-udp-001-en",
            "knowledge_point_ids": ["kp-transport-udp"],
            "content": (
                "UDP is a connectionless transport-layer protocol "
                "that provides multiplexing and error detection "
                "but does not guarantee reliable delivery. "
                "The UDP header is only 8 bytes, containing "
                "source port, destination port, length, and checksum."
            ),
            "chapter": "Chapter 3 Transport Layer",
            "page_start": 198,
            "page_end": 204,
        },
        {
            "chunk_id": "chunk-transport-tcp-001-en",
            "knowledge_point_ids": ["kp-transport-tcp-handshake"],
            "content": (
                "TCP uses a three-way handshake to synchronize "
                "the initial sequence numbers of both sides and "
                "confirm that both client and server have their "
                "send and receive capabilities available. "
                "SYN, SYN-ACK, and ACK messages complete the "
                "connection establishment."
            ),
            "chapter": "Chapter 3 Transport Layer",
            "page_start": 214,
            "page_end": 219,
        },
        {
            "chunk_id": "chunk-transport-congestion-001-en",
            "knowledge_point_ids": [
                "kp-transport-congestion-control",
            ],
            "content": (
                "TCP congestion control includes three phases: "
                "slow start, congestion avoidance, and fast recovery. "
                "The Reno algorithm adjusts the window size based on "
                "packet loss signals, while BBR proactively probes "
                "based on bandwidth and delay models."
            ),
            "chapter": "Chapter 3 Transport Layer",
            "page_start": 248,
            "page_end": 256,
        },
        {
            "chunk_id": "chunk-transport-compare-001-en",
            "knowledge_point_ids": ["kp-transport-udp", "kp-transport-tcp-handshake"],
            "content": (
                "UDP and TCP are both transport-layer protocols "
                "but differ significantly. UDP is connectionless, "
                "lightweight, and does not guarantee delivery, "
                "making it suitable for real-time applications "
                "like video streaming and DNS queries. TCP is "
                "connection-oriented, reliable, and uses flow "
                "and congestion control, making it suitable for "
                "applications requiring data integrity such as "
                "web browsing and file transfer."
            ),
            "chapter": "Chapter 3 Transport Layer",
            "page_start": 205,
            "page_end": 212,
        },
        {
            "chunk_id": "chunk-network-ip-001-en",
            "knowledge_point_ids": ["kp-network-addressing"],
            "content": (
                "IPv4 addresses are 32 bits, represented in "
                "dotted-decimal notation. Subnet masks distinguish "
                "the network prefix from the host number. "
                "Routers make forwarding decisions using "
                "longest prefix matching."
            ),
            "chapter": "Chapter 4 Network Layer",
            "page_start": 298,
            "page_end": 306,
        },
        {
            "chunk_id": "chunk-network-routing-001-en",
            "knowledge_point_ids": ["kp-network-routing"],
            "content": (
                "Routing algorithms fall into two categories: "
                "distance-vector and link-state. RIP uses "
                "distance-vector routing, OSPF uses link-state "
                "routing. BGP is the inter-autonomous-system "
                "routing protocol."
            ),
            "chapter": "Chapter 4 Network Layer",
            "page_start": 338,
            "page_end": 348,
        },
        {
            "chunk_id": "chunk-link-ethernet-001-en",
            "knowledge_point_ids": ["kp-link-ethernet"],
            "content": (
                "Ethernet is the most popular wired access technology, "
                "using the CSMA/CD protocol to resolve collisions "
                "on shared media. MAC addresses are 48 bits. "
                "The frame structure includes preamble, destination "
                "address, source address, type, data, and CRC."
            ),
            "chapter": "Chapter 5 Link Layer",
            "page_start": 412,
            "page_end": 422,
        },
    ],
    "Computer Networks Lab Manual": [
        {
            "chunk_id": "chunk-lab-wireshark-001-en",
            "knowledge_point_ids": [
                "kp-transport-tcp-handshake",
            ],
            "content": (
                "Capture TCP three-way handshake packets using "
                "Wireshark: set the filter tcp.flags.syn==1, "
                "observe the sequence and acknowledgment numbers "
                "of SYN, SYN-ACK, and ACK messages."
            ),
            "chapter": "Lab 3 TCP Protocol Analysis",
            "page_start": 28,
            "page_end": 33,
        },
        {
            "chunk_id": "chunk-lab-dns-001-en",
            "knowledge_point_ids": ["kp-application-dns"],
            "content": (
                "Use the nslookup command for DNS queries and "
                "observe the recursive resolution process. "
                "Capture DNS packets with Wireshark and analyze "
                "query type A and response records."
            ),
            "chapter": "Lab 2 DNS Protocol Analysis",
            "page_start": 18,
            "page_end": 24,
        },
    ],
}


MOCK_RESOURCES: dict[str, list[dict]] = {
    "计算机网络：自顶向下方法": [
        {
            "chunk_id": "chunk-app-http-001",
            "knowledge_point_ids": ["kp-application-http"],
            "content": (
                "HTTP 使用 TCP 作为传输层协议，客户端发起连接后"
                "通过请求-响应模式交换报文。"
                "请求报文由请求行、首部行和实体体组成。"
            ),
            "chapter": "第 2 章 应用层",
            "page_start": 68,
            "page_end": 72,
        },
        {
            "chunk_id": "chunk-app-dns-001",
            "knowledge_point_ids": ["kp-application-dns"],
            "content": (
                "DNS 是分布式数据库，采用层次结构的域名空间。"
                "递归查询和迭代查询是两种主要的解析方式，"
                "本地 DNS 服务器通常缓存查询结果以减少延迟。"
            ),
            "chapter": "第 2 章 应用层",
            "page_start": 93,
            "page_end": 98,
        },
        {
            "chunk_id": "chunk-transport-udp-001",
            "knowledge_point_ids": ["kp-transport-udp"],
            "content": (
                "UDP 是无连接的传输层协议，"
                "提供多路复用、差错检测但不保证可靠传输。"
                "UDP 首部仅 8 字节，"
                "包含源端口、目的端口、长度和校验和。"
            ),
            "chapter": "第 3 章 运输层",
            "page_start": 198,
            "page_end": 204,
        },
        {
            "chunk_id": "chunk-transport-tcp-001",
            "knowledge_point_ids": ["kp-transport-tcp-handshake"],
            "content": (
                "TCP 使用三次握手同步双方的初始序列号，"
                "并确认客户端与服务器两个方向的"
                "发送和接收能力都可用。"
                "SYN、SYN-ACK、ACK 三类报文完成连接建立。"
            ),
            "chapter": "第 3 章 运输层",
            "page_start": 214,
            "page_end": 219,
        },
        {
            "chunk_id": "chunk-transport-congestion-001",
            "knowledge_point_ids": [
                "kp-transport-congestion-control",
            ],
            "content": (
                "TCP 拥塞控制包含慢启动、拥塞避免、"
                "快速恢复三个阶段。"
                "Reno 算法通过丢包信号调整窗口大小，"
                "BBR 则基于带宽和时延模型主动探测。"
            ),
            "chapter": "第 3 章 运输层",
            "page_start": 248,
            "page_end": 256,
        },
        {
            "chunk_id": "chunk-transport-compare-001",
            "knowledge_point_ids": ["kp-transport-udp", "kp-transport-tcp-handshake"],
            "content": (
                "UDP 和 TCP 都是运输层协议，但有显著区别。"
                "UDP 是无连接的，轻量级，不保证可靠交付，"
                "适合实时应用如视频流和 DNS 查询。"
                "TCP 是面向连接的，提供可靠传输、流量控制"
                "和拥塞控制，适合需要数据完整性的应用"
                "如网页浏览和文件传输。"
            ),
            "chapter": "第 3 章 运输层",
            "page_start": 205,
            "page_end": 212,
        },
        {
            "chunk_id": "chunk-network-ip-001",
            "knowledge_point_ids": ["kp-network-addressing"],
            "content": (
                "IPv4 地址 32 位，采用点分十进制表示。"
                "子网掩码用于区分网络前缀和主机号，"
                "路由器通过最长前缀匹配进行转发决策。"
            ),
            "chapter": "第 4 章 网络层",
            "page_start": 298,
            "page_end": 306,
        },
        {
            "chunk_id": "chunk-network-routing-001",
            "knowledge_point_ids": ["kp-network-routing"],
            "content": (
                "路由选择算法分为距离向量和链路状态两类。"
                "RIP 使用距离向量，OSPF 使用链路状态。"
                "BGP 是自治系统间的路由协议。"
            ),
            "chapter": "第 4 章 网络层",
            "page_start": 338,
            "page_end": 348,
        },
        {
            "chunk_id": "chunk-link-ethernet-001",
            "knowledge_point_ids": ["kp-link-ethernet"],
            "content": (
                "以太网是最流行的有线接入技术，"
                "使用 CSMA/CD 协议解决共享介质的碰撞问题。"
                "MAC 地址 48 位，帧结构包含前导码、"
                "目的地址、源地址、类型、数据和 CRC。"
            ),
            "chapter": "第 5 章 链路层",
            "page_start": 412,
            "page_end": 422,
        },
    ],
    "计算机网络实验指导书": [
        {
            "chunk_id": "chunk-lab-wireshark-001",
            "knowledge_point_ids": [
                "kp-transport-tcp-handshake",
            ],
            "content": (
                "使用 Wireshark 捕获 TCP 三次握手报文："
                "过滤条件 tcp.flags.syn==1，"
                "观察 SYN、SYN-ACK、ACK 的序列号"
                "和确认号变化。"
            ),
            "chapter": "实验 3 TCP 协议分析",
            "page_start": 28,
            "page_end": 33,
        },
        {
            "chunk_id": "chunk-lab-dns-001",
            "knowledge_point_ids": ["kp-application-dns"],
            "content": (
                "使用 nslookup 命令进行 DNS 查询，"
                "观察递归查询过程。"
                "通过 Wireshark 捕获 DNS 报文，"
                "分析查询类型 A 和响应记录。"
            ),
            "chapter": "实验 2 DNS 协议分析",
            "page_start": 18,
            "page_end": 24,
        },
    ],
}

MOCK_CHUNKS_ZH = [
    ChunkMetadata(
        chunk_id=item["chunk_id"],
        resource_id=f"resource-{resource_idx:03d}",
        knowledge_point_ids=item["knowledge_point_ids"],
        title=resource_title,
        content=item["content"],
        chapter=item["chapter"],
        page_start=item["page_start"],
        page_end=item["page_end"],
        language=Language.ZH,
        content_type=ContentType.PDF,
        source_url=None,
        version="8e-zh",
        access_level=AccessLevel.COURSE,
        parse_status=ParseStatus.PARSED,
        updated_at=datetime(2026, 7, 28, tzinfo=UTC),
    )
    for resource_idx, (resource_title, chunks) in enumerate(MOCK_RESOURCES.items())
    for item in chunks
]

MOCK_CHUNKS_EN = [
    ChunkMetadata(
        chunk_id=item["chunk_id"],
        resource_id=f"resource-en-{resource_idx:03d}",
        knowledge_point_ids=item["knowledge_point_ids"],
        title=resource_title,
        content=item["content"],
        chapter=item["chapter"],
        page_start=item["page_start"],
        page_end=item["page_end"],
        language=Language.EN,
        content_type=ContentType.PDF,
        source_url=None,
        version="8e-en",
        access_level=AccessLevel.COURSE,
        parse_status=ParseStatus.PARSED,
        updated_at=datetime(2026, 7, 28, tzinfo=UTC),
    )
    for resource_idx, (resource_title, chunks) in enumerate(MOCK_RESOURCES_EN.items())
    for item in chunks
]

MOCK_CHUNKS = MOCK_CHUNKS_ZH + MOCK_CHUNKS_EN

RESOURCE_INDEX: dict[str, int] = {
    title: idx for idx, title in enumerate(MOCK_RESOURCES.keys())
}


def _task(
    task_id: str,
    title: str,
    description: str,
    task_type: TaskType,
    knowledge_point: str,
    criterion: str,
    feedback: str,
    exercise_id: str,
) -> TaskTemplate:
    return TaskTemplate(
        task_id=task_id,
        title=title,
        description=description,
        task_type=task_type,
        knowledge_point_ids=[knowledge_point],
        resource_ids=["resource-cn-textbook-001"],
        exercise_ids=[exercise_id],
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
        "ex-network-addressing-001",
    ),
    _task(
        "task-protocol-tcp-handshake",
        "Wireshark 分析 TCP 三次握手",
        "从抓包中定位 SYN、SYN-ACK 与 ACK。",
        TaskType.PROTOCOL_ANALYSIS,
        "kp-transport-tcp-handshake",
        "标注三类报文并解释序列号变化。",
        "提交报文编号后检查握手顺序。",
        "ex-transport-handshake-001",
    ),
    _task(
        "task-case-congestion",
        "Reno 与 BBR 拥塞控制案例",
        "比较丢包驱动和带宽时延模型驱动的拥塞控制。",
        TaskType.CASE_STUDY,
        "kp-transport-congestion-control",
        "给出两种算法在目标与信号上的差异。",
        "比较表缺项时提示从控制信号补充。",
        "ex-transport-congestion-001",
    ),
    _task(
        "task-innovation-edge",
        "边缘计算负载均衡挑战",
        "设计兼顾时延和故障切换的边缘负载均衡策略。",
        TaskType.INNOVATION_CHALLENGE,
        "kp-application-load-balancing",
        "提交架构图、关键指标和权衡说明。",
        "在选择策略后追问故障场景。",
        "ex-application-load-balancing-001",
    ),
    _task(
        "task-project-smart-home",
        "智能家居网络设计",
        "为给定户型和设备清单设计网络拓扑与协议选型。",
        TaskType.PROJECT_PRACTICE,
        "kp-network-design",
        "提交拓扑、地址规划和安全边界。",
        "检测单点故障与地址冲突。",
        "ex-network-design-001",
    ),
    _task(
        "task-troubleshooting-dns",
        "DNS 解析异常排错",
        "根据抓包和配置片段定位域名解析失败原因。",
        TaskType.TROUBLESHOOTING,
        "kp-application-dns",
        "给出故障根因、证据和修复步骤。",
        "每完成一个排查步骤后反馈证据充分性。",
        "ex-application-dns-001",
    ),
]


class MockResourceImporter:
    """B 模块：课程资料导入适配器。

    将课程资料拆分为带元数据的 Chunk，每个 Chunk 携带章节、页码和
    知识点关联信息，保证检索片段可追溯到原始材料。
    """

    def import_resource(self, request: ResourceImportRequest) -> ResourceImportResponse:
        resource_key = f"{request.course_id}:{request.title}:{request.version}"
        resource_id = f"resource-{uuid5(NAMESPACE_URL, resource_key).hex[:12]}"

        known_chunks = MOCK_RESOURCES.get(request.title)
        if known_chunks:
            chunk = known_chunks[0]
            metadata = ChunkMetadata(
                chunk_id=chunk["chunk_id"],
                resource_id=resource_id,
                knowledge_point_ids=chunk["knowledge_point_ids"],
                title=request.title,
                content=chunk["content"],
                chapter=chunk["chapter"],
                page_start=chunk["page_start"],
                page_end=chunk["page_end"],
                language=request.language,
                content_type=request.content_type,
                source_url=request.source_url,
                version=request.version,
                access_level=AccessLevel.COURSE,
                parse_status=ParseStatus.PARSED,
                updated_at=datetime.now(UTC),
            )
        else:
            metadata = ChunkMetadata(
                chunk_id=f"chunk-{uuid5(NAMESPACE_URL, resource_id).hex[:12]}",
                resource_id=resource_id,
                knowledge_point_ids=["kp-pending-review"],
                title=request.title,
                content="该资料尚未录入课程知识库，待人工审核后生成结构化 Chunk。",
                chapter="待人工审核",
                page_start=1,
                page_end=1,
                language=request.language,
                content_type=request.content_type,
                source_url=request.source_url,
                version=request.version,
                access_level=AccessLevel.COURSE,
                parse_status=ParseStatus.PENDING,
                updated_at=datetime.now(UTC),
            )

        return ResourceImportResponse(
            resource_id=resource_id,
            sync_status=SyncStatus.COMPLETED,
            metadata=metadata,
            error=None,
        )

    def import_all_chunks(self, request: ResourceImportRequest) -> list[ChunkMetadata]:
        """导入一份资料的全部 Chunk，用于批量构建知识库。"""
        resource_key = f"{request.course_id}:{request.title}:{request.version}"
        resource_id = f"resource-{uuid5(NAMESPACE_URL, resource_key).hex[:12]}"

        known_chunks = MOCK_RESOURCES.get(request.title)
        if not known_chunks:
            return []

        return [
            ChunkMetadata(
                chunk_id=chunk["chunk_id"],
                resource_id=resource_id,
                knowledge_point_ids=chunk["knowledge_point_ids"],
                title=request.title,
                content=chunk["content"],
                chapter=chunk["chapter"],
                page_start=chunk["page_start"],
                page_end=chunk["page_end"],
                language=request.language,
                content_type=request.content_type,
                source_url=request.source_url,
                version=request.version,
                access_level=AccessLevel.COURSE,
                parse_status=ParseStatus.PARSED,
                updated_at=datetime.now(UTC),
            )
            for chunk in known_chunks
        ]


class MockRetriever:
    """B 模块：模拟检索适配器。

    根据问题关键词匹配最相关的 Chunk，支持中英双语检索。
    """

    _KEYWORD_MAP_ZH: dict[str, str] = {
        "区别": "chunk-transport-compare-001",
        "不同": "chunk-transport-compare-001",
        "对比": "chunk-transport-compare-001",
        "TCP": "chunk-transport-tcp-001",
        "握手": "chunk-transport-tcp-001",
        "拥塞": "chunk-transport-congestion-001",
        "UDP": "chunk-transport-udp-001",
        "DNS": "chunk-app-dns-001",
        "HTTP": "chunk-app-http-001",
        "IP": "chunk-network-ip-001",
        "地址": "chunk-network-ip-001",
        "路由": "chunk-network-routing-001",
        "以太网": "chunk-link-ethernet-001",
        "Wireshark": "chunk-lab-wireshark-001",
    }

    _KEYWORD_MAP_EN: dict[str, str] = {
        "difference": "chunk-transport-compare-001-en",
        "compare": "chunk-transport-compare-001-en",
        "versus": "chunk-transport-compare-001-en",
        "handshake": "chunk-transport-tcp-001-en",
        "three-way": "chunk-transport-tcp-001-en",
        "congestion": "chunk-transport-congestion-001-en",
        "UDP": "chunk-transport-udp-001-en",
        "DNS": "chunk-app-dns-001-en",
        "HTTP": "chunk-app-http-001-en",
        "IP": "chunk-network-ip-001-en",
        "address": "chunk-network-ip-001-en",
        "routing": "chunk-network-routing-001-en",
        "ethernet": "chunk-link-ethernet-001-en",
        "Wireshark": "chunk-lab-wireshark-001-en",
    }

    @staticmethod
    def _is_english_question(question: str) -> bool:
        """简单判断提问语言：英文字符占比超过 50% 则为英文。"""
        alpha_chars = [c for c in question if c.isalpha()]
        if not alpha_chars:
            return False
        en_chars = [c for c in alpha_chars if ord(c) < 128]
        return len(en_chars) / len(alpha_chars) > 0.5

    def retrieve(self, question: str, course_id: str) -> list[ChunkMetadata]:
        del course_id
        is_en = self._is_english_question(question)
        keyword_map = self._KEYWORD_MAP_EN if is_en else self._KEYWORD_MAP_ZH
        chunk_pool = MOCK_CHUNKS_EN if is_en else MOCK_CHUNKS_ZH

        for keyword, chunk_id in keyword_map.items():
            if keyword.lower() in question.lower():
                match = next(
                    (c for c in chunk_pool if c.chunk_id == chunk_id), None
                )
                if match:
                    return [match]
        return chunk_pool[:1]


class MockAnswerGenerator:
    _ANSWERS_ZH = {
        "kp-transport-tcp-handshake": (
            "TCP 采用三次握手，是为了同步双方的初始序列号，并分别确认双向通信能力。"
        ),
        "kp-transport-udp": (
            "UDP 和 TCP 都是运输层协议。UDP 无连接、不保证可靠交付，"
            "适合实时应用；TCP 面向连接、提供可靠传输和拥塞控制，"
            "适合需要数据完整性的应用。"
        ),
        "kp-transport-congestion-control": (
            "TCP 拥塞控制包含慢启动、拥塞避免和快速恢复三个阶段。"
            "Reno 以丢包为信号，BBR 以带宽时延模型为信号。"
        ),
        "kp-application-dns": (
            "DNS 是分布式层次数据库，支持递归和迭代两种查询方式。"
        ),
        "kp-network-addressing": (
            "IPv4 地址 32 位，采用点分十进制表示。"
            "子网掩码区分网络前缀和主机号，"
            "路由器通过最长前缀匹配进行转发决策。"
        ),
        "kp-application-http": (
            "HTTP 使用 TCP 传输，采用请求-响应模式交换报文。"
        ),
    }

    _ANSWERS_EN = {
        "kp-transport-tcp-handshake": (
            "TCP uses a three-way handshake to synchronize "
            "initial sequence numbers and confirm bidirectional "
            "communication capability."
        ),
        "kp-transport-udp": (
            "UDP and TCP are both transport-layer protocols. "
            "UDP is connectionless and does not guarantee "
            "reliable delivery, suitable for real-time apps. "
            "TCP is connection-oriented with reliable delivery "
            "and congestion control, suitable for applications "
            "requiring data integrity."
        ),
        "kp-transport-congestion-control": (
            "TCP congestion control includes slow start, "
            "congestion avoidance, and fast recovery phases. "
            "Reno uses packet loss signals, while BBR uses "
            "bandwidth-delay models."
        ),
        "kp-network-addressing": (
            "IPv4 addresses are 32 bits in dotted-decimal "
            "notation. Subnet masks distinguish the network "
            "prefix from the host number. Routers use longest "
            "prefix matching for forwarding decisions."
        ),
        "kp-application-dns": (
            "DNS is a distributed hierarchical database that "
            "supports both recursive and iterative queries."
        ),
        "kp-application-http": (
            "HTTP uses TCP for transport and exchanges messages "
            "in a request-response pattern."
        ),
    }

    def generate(self, question: str, chunks: list[ChunkMetadata]) -> AskResponse:
        del question
        chunk = chunks[0]
        is_en = chunk.language == Language.EN
        answers = self._ANSWERS_EN if is_en else self._ANSWERS_ZH

        # 根据知识点选择回答
        answer = None
        for kp_id in chunk.knowledge_point_ids:
            if kp_id in answers:
                answer = answers[kp_id]
                break

        if answer is None:
            answer = (
                "This answer is generated from the offline mock retrieval pipeline."
                if is_en
                else "当前回答来自离线 Mock 检索链路。"
            )

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
            answer=answer + (" [Mock]" if not is_en else " [Mock]"),
            citations=[citation],
            confidence=0.92,
            request_id=f"req-{uuid4().hex}",
        )


class InMemoryTaskRepository:
    def __init__(self) -> None:
        self._tasks = {task.task_id: task for task in MOCK_TASKS}

    def create(self, task: TaskTemplate) -> TaskTemplate:
        if task.task_id in self._tasks:
            raise ValueError(f"task already exists: {task.task_id}")
        self._tasks[task.task_id] = task
        return task

    def list_tasks(self) -> list[TaskTemplate]:
        return list(self._tasks.values())

    def get_task(self, task_id: str) -> TaskTemplate | None:
        return self._tasks.get(task_id)

    def update_status(self, task_id: str, status: TaskStatus) -> TaskTemplate | None:
        task = self._tasks.get(task_id)
        if task is None:
            return None
        updated = task.model_copy(update={"status": status})
        self._tasks[task_id] = updated
        return updated


class InMemoryEventSink:
    def __init__(self) -> None:
        self.events: list[LearningEvent] = []

    def record(self, event: LearningEvent) -> LearningEvent:
        self.events.append(event)
        return event

    def query(
        self,
        *,
        course_id: str | None = None,
        user_id: str | None = None,
        event_type: str | None = None,
        object_id: str | None = None,
    ) -> list[LearningEvent]:
        events = self.events
        if course_id is not None:
            events = [event for event in events if event.course_id == course_id]
        if user_id is not None:
            events = [event for event in events if event.user_id == user_id]
        if event_type is not None:
            events = [event for event in events if event.event_type == event_type]
        if object_id is not None:
            events = [event for event in events if event.object_id == object_id]
        return sorted(events, key=lambda event: (event.occurred_at, event.event_id))


class InMemoryFeedbackStore:
    def __init__(self) -> None:
        self._feedback: dict[str, AnswerFeedback] = {}

    def create(self, feedback: AnswerFeedback) -> AnswerFeedback:
        self._feedback[feedback.feedback_id] = feedback
        return feedback

    def get(self, feedback_id: str) -> AnswerFeedback | None:
        return self._feedback.get(feedback_id)

    def list_all(self) -> list[AnswerFeedback]:
        return list(self._feedback.values())

    def replace(self, feedback: AnswerFeedback) -> AnswerFeedback:
        if feedback.feedback_id not in self._feedback:
            raise KeyError(feedback.feedback_id)
        self._feedback[feedback.feedback_id] = feedback
        return feedback


class InMemoryKnowledgeBaseChangeStore:
    def __init__(self) -> None:
        self._changes: dict[str, KnowledgeBaseChangeTask] = {}

    def create(self, change: KnowledgeBaseChangeTask) -> KnowledgeBaseChangeTask:
        self._changes[change.change_id] = change
        return change

    def get(self, change_id: str) -> KnowledgeBaseChangeTask | None:
        return self._changes.get(change_id)

    def list_all(self) -> list[KnowledgeBaseChangeTask]:
        return list(self._changes.values())

    def replace(self, change: KnowledgeBaseChangeTask) -> KnowledgeBaseChangeTask:
        if change.change_id not in self._changes:
            raise KeyError(change.change_id)
        self._changes[change.change_id] = change
        return change


class InMemoryChunkStore:
    """内存 Chunk 存储，用于测试和离线演示。

    `ChunkMetadata` 本身不含 `course_id`，因此课程归属在存储层单独记录。
    """

    def __init__(self) -> None:
        self._chunks: list[ChunkMetadata] = []
        self._course_by_resource: dict[str, str] = {}

    def save(self, chunks: list[ChunkMetadata], course_id: str | None = None) -> int:
        self._chunks.extend(chunks)
        if course_id:
            for chunk in chunks:
                self._course_by_resource[chunk.resource_id] = course_id
        return len(chunks)

    def list_by_resource(self, resource_id: str) -> list[ChunkMetadata]:
        return [c for c in self._chunks if c.resource_id == resource_id]

    def list_all(self) -> list[ChunkMetadata]:
        return self._chunks.copy()

    def list_resources(self, course_id: str | None = None) -> list[ResourceSummary]:
        summaries: dict[str, ResourceSummary] = {}
        for chunk in self._chunks:
            owner = self._course_by_resource.get(chunk.resource_id, "unknown")
            if course_id is not None and owner != course_id:
                continue
            existing = summaries.get(chunk.resource_id)
            if existing is None:
                summaries[chunk.resource_id] = ResourceSummary(
                    resource_id=chunk.resource_id,
                    course_id=owner,
                    title=chunk.title,
                    chunk_count=1,
                    language=chunk.language,
                    content_type=chunk.content_type,
                    version=chunk.version,
                    updated_at=chunk.updated_at,
                )
            else:
                summaries[chunk.resource_id] = existing.model_copy(
                    update={
                        "chunk_count": existing.chunk_count + 1,
                        "updated_at": max(existing.updated_at, chunk.updated_at),
                    }
                )
        return sorted(summaries.values(), key=lambda item: item.resource_id)

    def count(self) -> int:
        return len(self._chunks)


class InMemoryQualityReviewStore:
    """内存质量审查存储。"""

    def __init__(self) -> None:
        self._reviews: list[QualityReview] = []

    def save(self, review: QualityReview) -> QualityReview:
        self._reviews.append(review)
        return review

    def list_all(self) -> list[QualityReview]:
        return self._reviews.copy()

    def list_by_chunk(self, chunk_id: str) -> list[QualityReview]:
        return [r for r in self._reviews if r.chunk_id == chunk_id]

    def get(self, review_id: str) -> QualityReview | None:
        return next((r for r in self._reviews if r.review_id == review_id), None)
