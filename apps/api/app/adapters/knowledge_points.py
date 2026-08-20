"""《计算机网络》课程知识点与知识图谱数据。

知识点通过 `parent_id` 组织章节层次，通过 `prerequisite_ids` 表达学习先后关系，
使任务、Chunk 和评测集里引用的 `knowledge_point_ids` 能解析为可读的知识点。
"""

from app.domain.enums import Difficulty, ReviewStatus
from app.domain.models import KnowledgePoint

MAINTAINER = "course-team"


def _kp(
    knowledge_point_id: str,
    name: str,
    chapter: str,
    kind: str,
    difficulty: Difficulty,
    summary: str,
    keywords_zh: list[str],
    keywords_en: list[str],
    *,
    parent_id: str | None = None,
    prerequisite_ids: list[str] | None = None,
) -> KnowledgePoint:
    return KnowledgePoint(
        knowledge_point_id=knowledge_point_id,
        name=name,
        chapter=chapter,
        parent_id=parent_id,
        kind=kind,
        difficulty=difficulty,
        keywords_zh=keywords_zh,
        keywords_en=keywords_en,
        prerequisite_ids=prerequisite_ids or [],
        summary=summary,
        review_status=ReviewStatus.APPROVED,
        maintainer=MAINTAINER,
    )


COURSE_KNOWLEDGE_POINTS: list[KnowledgePoint] = [
    _kp(
        "kp-network-overview",
        "计算机网络与协议分层",
        "第 1 章 计算机网络和因特网",
        "concept",
        Difficulty.INTRODUCTORY,
        "因特网由端系统、分组交换设备和链路构成，协议分层把复杂通信拆分为可组合的层次，"
        "每层向上层提供服务并依赖下层服务。",
        ["协议分层", "端系统", "分组交换", "TCP/IP 模型"],
        ["protocol layering", "end system", "packet switching"],
    ),
    _kp(
        "kp-application-http",
        "HTTP 协议",
        "第 2 章 应用层",
        "protocol",
        Difficulty.INTRODUCTORY,
        "HTTP 以 TCP 为传输层协议，采用请求-响应模式交换报文；"
        "请求报文由请求行、首部行和实体体组成。",
        ["HTTP", "请求响应", "首部行", "持久连接"],
        ["HTTP", "request-response", "header line"],
        parent_id="kp-network-overview",
        prerequisite_ids=["kp-network-overview"],
    ),
    _kp(
        "kp-application-dns",
        "DNS 域名解析",
        "第 2 章 应用层",
        "protocol",
        Difficulty.INTERMEDIATE,
        "DNS 是层次化命名的分布式数据库，通过递归查询与迭代查询完成域名到地址的解析，"
        "本地 DNS 服务器通过缓存降低时延。",
        ["DNS", "递归查询", "迭代查询", "缓存"],
        ["DNS", "recursive query", "iterative query", "cache"],
        parent_id="kp-network-overview",
        prerequisite_ids=["kp-network-overview"],
    ),
    _kp(
        "kp-application-load-balancing",
        "负载均衡与内容分发",
        "第 2 章 应用层",
        "design",
        Difficulty.ADVANCED,
        "负载均衡在多个服务实例之间分配请求，结合 DNS 调度、反向代理和边缘节点，"
        "在时延、吞吐与可用性之间取得平衡。",
        ["负载均衡", "CDN", "边缘计算", "调度策略"],
        ["load balancing", "CDN", "edge computing"],
        parent_id="kp-network-overview",
        prerequisite_ids=["kp-application-dns", "kp-application-http"],
    ),
    _kp(
        "kp-transport-udp",
        "UDP 协议",
        "第 3 章 运输层",
        "protocol",
        Difficulty.INTRODUCTORY,
        "UDP 是无连接的运输层协议，提供复用分用与差错检测，但不保证可靠交付；"
        "首部仅 8 字节，包含源端口、目的端口、长度和校验和。",
        ["UDP", "无连接", "复用分用", "校验和"],
        ["UDP", "connectionless", "multiplexing", "checksum"],
        parent_id="kp-network-overview",
        prerequisite_ids=["kp-network-overview"],
    ),
    _kp(
        "kp-transport-tcp-handshake",
        "TCP 三次握手",
        "第 3 章 运输层",
        "protocol",
        Difficulty.INTERMEDIATE,
        "TCP 通过三次握手同步双方初始序列号，并确认收发能力均可用；"
        "SYN、SYN-ACK 与 ACK 三类报文完成连接建立。",
        ["三次握手", "序列号", "SYN", "连接建立"],
        ["three-way handshake", "sequence number", "SYN"],
        parent_id="kp-network-overview",
        prerequisite_ids=["kp-transport-udp"],
    ),
    _kp(
        "kp-transport-congestion-control",
        "TCP 拥塞控制",
        "第 3 章 运输层",
        "mechanism",
        Difficulty.ADVANCED,
        "TCP 拥塞控制包含慢启动、拥塞避免和快速恢复三个阶段；"
        "Reno 依据丢包信号调整窗口，BBR 依据带宽与时延模型主动探测。",
        ["拥塞控制", "慢启动", "Reno", "BBR"],
        ["congestion control", "slow start", "Reno", "BBR"],
        parent_id="kp-network-overview",
        prerequisite_ids=["kp-transport-tcp-handshake"],
    ),
    _kp(
        "kp-network-addressing",
        "IP 编址与最长前缀匹配",
        "第 4 章 网络层",
        "concept",
        Difficulty.INTERMEDIATE,
        "IPv4 地址为 32 位点分十进制表示，子网掩码区分网络前缀与主机号；"
        "路由器依据最长前缀匹配做出转发决策。",
        ["IP 地址", "子网掩码", "最长前缀匹配", "子网划分"],
        ["IP address", "subnet mask", "longest prefix matching"],
        parent_id="kp-network-overview",
        prerequisite_ids=["kp-network-overview"],
    ),
    _kp(
        "kp-network-routing",
        "路由算法与路由协议",
        "第 4 章 网络层",
        "mechanism",
        Difficulty.ADVANCED,
        "路由算法分为距离向量与链路状态两类：RIP 采用距离向量，OSPF 采用链路状态，"
        "BGP 是自治系统之间的路由协议。",
        ["距离向量", "链路状态", "RIP", "OSPF", "BGP"],
        ["distance vector", "link state", "RIP", "OSPF", "BGP"],
        parent_id="kp-network-overview",
        prerequisite_ids=["kp-network-addressing"],
    ),
    _kp(
        "kp-network-design",
        "网络拓扑与地址规划设计",
        "第 4 章 网络层",
        "design",
        Difficulty.ADVANCED,
        "网络设计需要结合需求确定拓扑、划分子网、规划地址并选择协议，"
        "同时兼顾冗余、安全边界与可扩展性。",
        ["拓扑设计", "地址规划", "VLAN", "安全边界"],
        ["topology design", "address planning", "VLAN"],
        parent_id="kp-network-overview",
        prerequisite_ids=["kp-network-addressing", "kp-network-routing"],
    ),
    _kp(
        "kp-link-ethernet",
        "以太网与 CSMA/CD",
        "第 5 章 链路层",
        "protocol",
        Difficulty.INTERMEDIATE,
        "以太网是最常见的有线接入技术，使用 CSMA/CD 处理共享介质上的冲突；"
        "MAC 地址为 48 位，帧结构包含前导码、目的地址、源地址、类型、数据和 CRC。",
        ["以太网", "CSMA/CD", "MAC 地址", "帧结构"],
        ["Ethernet", "CSMA/CD", "MAC address", "frame"],
        parent_id="kp-network-overview",
        prerequisite_ids=["kp-network-overview"],
    ),
]


class InMemoryKnowledgePointRepository:
    """内存知识点仓库，提供知识图谱的查询入口。"""

    def __init__(self, knowledge_points: list[KnowledgePoint] | None = None) -> None:
        source = knowledge_points if knowledge_points is not None else COURSE_KNOWLEDGE_POINTS
        self._knowledge_points = {item.knowledge_point_id: item for item in source}

    def list_knowledge_points(
        self,
        chapter: str | None = None,
        parent_id: str | None = None,
    ) -> list[KnowledgePoint]:
        return [
            item
            for item in self._knowledge_points.values()
            if (chapter is None or item.chapter == chapter)
            and (parent_id is None or item.parent_id == parent_id)
        ]

    def get_knowledge_point(self, knowledge_point_id: str) -> KnowledgePoint | None:
        return self._knowledge_points.get(knowledge_point_id)
