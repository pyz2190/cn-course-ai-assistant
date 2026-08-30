"""《计算机网络》课程试题库。

试题是任务完成判据的可判定载体：`knowledge_point_ids` 把试题挂到知识图谱，
`resource_ids` 指回命题依据的课程资料，`TaskTemplate.exercise_ids` 把试题挂到任务，
使「任务 → 知识点 → 资料 → 试题 → AI 反馈」形成闭合的引用链。
"""

from app.domain.enums import Difficulty, ExerciseSource, ExerciseType, ReviewStatus
from app.domain.models import Exercise

TEXTBOOK = "resource-cn-textbook-001"


def _exercise(
    exercise_id: str,
    question: str,
    exercise_type: ExerciseType,
    knowledge_point_ids: list[str],
    difficulty: Difficulty,
    reference_answer: str,
    explanation: str,
    source: ExerciseSource,
    options: list[str] | None = None,
) -> Exercise:
    return Exercise(
        exercise_id=exercise_id,
        question=question,
        exercise_type=exercise_type,
        knowledge_point_ids=knowledge_point_ids,
        resource_ids=[TEXTBOOK],
        difficulty=difficulty,
        options=options or [],
        reference_answer=reference_answer,
        explanation=explanation,
        source=source,
        review_status=ReviewStatus.APPROVED,
    )


COURSE_EXERCISES: list[Exercise] = [
    _exercise(
        "ex-network-addressing-001",
        "路由表中同时存在 192.168.0.0/16、192.168.1.0/24 和 0.0.0.0/0 三条表项，"
        "转发目的地址 192.168.1.7 的分组时会命中哪一条？",
        ExerciseType.SINGLE_CHOICE,
        ["kp-network-addressing"],
        Difficulty.INTRODUCTORY,
        "192.168.1.0/24",
        "最长前缀匹配在所有可匹配表项中选择前缀最长的一条；/24 比 /16 和 /0 更具体，"
        "因此具体子网路由优先于覆盖范围更大的路由。",
        ExerciseSource.TEXTBOOK,
        options=["192.168.0.0/16", "192.168.1.0/24", "0.0.0.0/0", "三条等价，轮询选择"],
    ),
    _exercise(
        "ex-transport-handshake-001",
        "在 Wireshark 抓包中，如何依据标志位和序列号区分三次握手的 SYN、SYN-ACK 与 ACK 报文？",
        ExerciseType.ANALYSIS,
        ["kp-transport-tcp-handshake"],
        Difficulty.INTERMEDIATE,
        "第一个报文只置 SYN，携带客户端初始序列号 seq=x；第二个报文同时置 SYN 与 ACK，"
        "携带服务端初始序列号 seq=y 且 ack=x+1；第三个报文只置 ACK，seq=x+1 且 ack=y+1。",
        "三次握手的目的是同步双方初始序列号，因此判定依据是标志位组合加上序列号与确认号的递进关系，"
        "而不是报文出现的先后顺序。",
        ExerciseSource.LAB_GUIDE,
    ),
    _exercise(
        "ex-transport-congestion-001",
        "Reno 与 BBR 在拥塞控制上依据的控制信号和控制目标分别是什么？",
        ExerciseType.SHORT_ANSWER,
        ["kp-transport-congestion-control"],
        Difficulty.INTERMEDIATE,
        "Reno 以丢包作为拥塞信号，目标是在丢包发生后退避并重新探测可用带宽；"
        "BBR 以对瓶颈带宽和最小往返时延的估计作为控制依据，目标是把发送速率维持在带宽时延积附近。",
        "两者的差异在控制信号（丢包 vs 带宽时延模型）与控制目标（退避重探 vs 逼近 BDP），"
        "不能混淆为「快慢」或「新旧」之分。",
        ExerciseSource.PAST_EXAM,
    ),
    _exercise(
        "ex-application-load-balancing-001",
        "为边缘计算场景设计负载均衡策略时，请说明所选调度指标、故障切换判据，"
        "以及时延与可用性之间的权衡。",
        ExerciseType.DESIGN,
        ["kp-application-load-balancing"],
        Difficulty.ADVANCED,
        "需给出：调度指标（如节点往返时延、当前并发、剩余算力）、"
        "故障判据与切换阈值（连续健康检查失败次数与超时时间）、"
        "以及权衡说明（更激进的切换降低故障影响但可能造成抖动与重复计算）。",
        "该题不设唯一答案，评分看三项是否齐备且相互一致；缺少故障切换判据的方案不算完成。",
        ExerciseSource.COURSE_TEAM,
    ),
    _exercise(
        "ex-network-design-001",
        "为给定户型与设备清单设计智能家居网络时，拓扑、地址规划与安全边界三部分各应交付什么？",
        ExerciseType.DESIGN,
        ["kp-network-design"],
        Difficulty.ADVANCED,
        "拓扑需标出网关、无线接入点与有线干线及其冗余路径；"
        "地址规划需给出各网段的子网划分、地址分配方式与保留地址，且网段之间不重叠；"
        "安全边界需说明可信网段与访客/IoT 网段的隔离方式及跨段访问策略。",
        "三部分需相互印证：地址规划要覆盖拓扑中出现的每个网段，安全边界要落在具体网段上。",
        ExerciseSource.COURSE_TEAM,
    ),
    _exercise(
        "ex-application-dns-001",
        "排查 DNS 解析失败时，应按什么顺序收集证据并给出根因？",
        ExerciseType.SHORT_ANSWER,
        ["kp-application-dns"],
        Difficulty.INTERMEDIATE,
        "先确认本机 resolver 配置与目标域名，再抓包确认查询是否发出、"
        "是否收到响应以及响应码；然后按「查询未发出 / 未收到响应 / 收到错误响应」"
        "区分本地配置、网络可达性与权威服务器三类根因，最后用一次成功解析验证修复。",
        "根因必须由抓包现象与配置片段共同支持；两者矛盾时不能下结论，应补充证据。",
        ExerciseSource.LAB_GUIDE,
    ),
]


class InMemoryExerciseRepository:
    """离线试题仓库，默认返回课程内置试题。"""

    def __init__(self, exercises: list[Exercise] | None = None) -> None:
        self._exercises = list(exercises if exercises is not None else COURSE_EXERCISES)

    def list_exercises(
        self,
        knowledge_point_id: str | None = None,
        exercise_ids: list[str] | None = None,
    ) -> list[Exercise]:
        wanted = set(exercise_ids) if exercise_ids else None
        return [
            exercise
            for exercise in self._exercises
            if (knowledge_point_id is None or knowledge_point_id in exercise.knowledge_point_ids)
            and (wanted is None or exercise.exercise_id in wanted)
        ]

    def get_exercise(self, exercise_id: str) -> Exercise | None:
        for exercise in self._exercises:
            if exercise.exercise_id == exercise_id:
                return exercise
        return None
