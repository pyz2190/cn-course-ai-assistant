"""技术基线：用 D 的 RAG 适配器跑 C 的完整问答库。

这不是正式评测基线。正式基线只接受经人工交叉评审 `approved` 的标注
（见 `evaluation/review_workflow.md`），由 `scripts/run_evaluation_pipeline.py` 执行。
本脚本绕过评审门禁，只回答一个工程问题：
「问答库 → RAG 适配器 → 回答与引用」这条链路是否可执行，以及语料是否支撑得起问答库。

因此它的输出用于给交叉评审提供证据，不能作为质量结论或验收依据。
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT, ROOT / "apps" / "api"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from app.adapters.evaluation import InProcessRagAdapter
from app.adapters.mock import MOCK_CHUNKS
from app.core.dependencies import get_rag_service

from scripts.evaluate import RagRequest, RuntimeParameters


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def run_technical_baseline(evaluation_directory: Path) -> dict[str, Any]:
    questions = {
        item["evaluation_id"]: item
        for item in _load_jsonl(evaluation_directory / "question_bank.jsonl")
    }
    annotations = {
        item["evaluation_id"]: item
        for item in _load_jsonl(evaluation_directory / "annotations.jsonl")
    }
    corpus_chunk_ids = {chunk.chunk_id for chunk in MOCK_CHUNKS}

    unresolved_citations = [
        {"evaluation_id": evaluation_id, "chunk_id": citation["chunk_id"]}
        for evaluation_id, annotation in sorted(annotations.items())
        for citation in annotation["expected_citations"]
        if citation["chunk_id"] not in corpus_chunk_ids
    ]

    adapter = InProcessRagAdapter(get_rag_service())
    runtime = RuntimeParameters(
        model=None, embedding=None, reranker=None, top_k=None, git_commit=None
    )

    rows: list[dict[str, Any]] = []
    for evaluation_id in sorted(questions):
        question = questions[evaluation_id]
        expected = {
            citation["chunk_id"]
            for citation in annotations[evaluation_id]["expected_citations"]
        }
        try:
            response = adapter.answer(
                RagRequest(
                    evaluation_id, question["question"], question["knowledge_point_ids"]
                ),
                runtime,
            )
        except Exception as error:  # noqa: BLE001
            rows.append(
                {
                    "evaluation_id": evaluation_id,
                    "category": question["category"],
                    "citation_count": 0,
                    "expected_hit": False,
                    "refused": False,
                    "error": f"{type(error).__name__}: {error}",
                }
            )
            continue
        returned = {citation["chunk_id"] for citation in response.citations}
        rows.append(
            {
                "evaluation_id": evaluation_id,
                "category": question["category"],
                "citation_count": len(response.citations),
                "expected_hit": bool(expected & returned),
                "refused": not response.citations,
                "error": None,
            }
        )

    by_category: Counter[str] = Counter()
    hits_by_category: Counter[str] = Counter()
    for row in rows:
        by_category[row["category"]] += 1
        if row["expected_hit"]:
            hits_by_category[row["category"]] += 1

    return {
        "corpus_chunks": len(corpus_chunk_ids),
        "questions": len(rows),
        "unresolved_citations": unresolved_citations,
        "errors": sum(1 for row in rows if row["error"]),
        "refused": sum(1 for row in rows if row["refused"]),
        "expected_hits": sum(1 for row in rows if row["expected_hit"]),
        "by_category": {
            category: {
                "total": by_category[category],
                "hits": hits_by_category[category],
            }
            for category in sorted(by_category)
        },
        "rows": rows,
    }


def _print_summary(summary: dict[str, Any]) -> None:
    print("技术基线（非正式评测基线，不构成验收依据）")
    print(f"语料 Chunk 数: {summary['corpus_chunks']}")
    print(f"问答库题数: {summary['questions']}")
    print(f"期望引用无法在语料中解析: {len(summary['unresolved_citations'])}")
    print(f"执行异常: {summary['errors']}")
    print(f"安全拒答（返回 0 条引用）: {summary['refused']}")
    print(f"命中期望 Chunk: {summary['expected_hits']}/{summary['questions']}")
    print("按类别命中：")
    for category, counts in summary["by_category"].items():
        print(f"  {category:16} {counts['hits']}/{counts['total']}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evaluation-dir", type=Path, default=ROOT / "evaluation")
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "evaluation" / "reports" / "technical_baseline.json",
    )
    args = parser.parse_args()
    summary = run_technical_baseline(args.evaluation_dir)
    _print_summary(summary)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"\n明细写入: {args.output}")
    return 2 if summary["errors"] or summary["unresolved_citations"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
