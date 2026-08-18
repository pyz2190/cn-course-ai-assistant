import json
import statistics
import sys
from pathlib import Path
from time import perf_counter

PROJECT_ROOT = Path(__file__).resolve().parents[3]
API_ROOT = PROJECT_ROOT / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.core.dependencies import get_rag_service  # noqa: E402
from app.domain.rag import RetrievalScope  # noqa: E402

QUESTIONS = (
    "TCP 为什么需要三次握手？",
    "DNS 递归查询和迭代查询有什么区别？",
    "HTTP 请求报文包含哪些部分？",
    "RIP、OSPF 和 BGP 有什么区别？",
    "如何使用 Wireshark 捕获 TCP 握手？",
)


def percentile(values: list[float], ratio: float) -> float:
    ordered = sorted(values)
    index = min(len(ordered) - 1, round((len(ordered) - 1) * ratio))
    return ordered[index]


def main() -> int:
    service = get_rag_service()
    scope = RetrievalScope(course_id="computer-networks")
    for question in QUESTIONS:
        service.answer(question, scope)

    samples: list[float] = []
    for _ in range(4):
        for question in QUESTIONS:
            started = perf_counter()
            service.answer(question, scope)
            samples.append((perf_counter() - started) * 1000)

    result = {
        "samples": len(samples),
        "p50_ms": round(statistics.median(samples), 3),
        "p95_ms": round(percentile(samples, 0.95), 3),
        "max_ms": round(max(samples), 3),
        "limit_ms": 2000,
        "includes_external_generation": False,
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["max_ms"] <= result["limit_ms"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
