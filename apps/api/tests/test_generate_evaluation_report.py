import json
from pathlib import Path

from scripts.generate_evaluation_report import generate_evaluation_report

PROJECT_ROOT = Path(__file__).resolve().parents[3]
QUESTION_BANK = PROJECT_ROOT / "evaluation" / "question_bank.jsonl"


def _write_jsonl(path: Path, records: list[dict[str, object]]) -> None:
    path.write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
        encoding="utf-8",
    )


def _run_record(
    evaluation_id: str,
    *,
    scores: dict[str, float | None] | None,
    citations: list[dict[str, str]] | None = None,
    error: str | None = None,
    run_id: str = "RUN-20260803T000000Z-test",
) -> dict[str, object]:
    return {
        "run_id": run_id,
        "evaluation_id": evaluation_id,
        "generated_answer": "generated answer" if error is None else "",
        "citations": citations if citations is not None else [{"chunk_id": "chunk-1"}],
        "scores": scores,
        "error": error,
        "runtime": {
            "model": "test-model",
            "embedding": "test-embedding",
            "reranker": "test-reranker",
            "top_k": 5,
            "git_commit": "abc123def",
        },
    }


def test_generates_report_with_mixed_results_and_aggregates(tmp_path: Path) -> None:
    run_file = tmp_path / "run.jsonl"
    output_path = tmp_path / "baseline.md"
    _write_jsonl(
        run_file,
        [
            _run_record(
                "QA-CONCEPT-001",
                scores={
                    "correctness": 4,
                    "citation_accuracy": 3,
                    "hallucination_rate": 0.0,
                },
            ),
            _run_record(
                "QA-PROTOCOL-001",
                scores={
                    "correctness": 2,
                    "citation_accuracy": None,
                    "hallucination_rate": 0.5,
                },
                citations=[],
            ),
            _run_record(
                "QA-LAB-002",
                scores=None,
                citations=[],
                error="RuntimeError: adapter unavailable",
            ),
        ],
    )

    result = generate_evaluation_report(
        run_file,
        question_bank_path=QUESTION_BANK,
        output_path=output_path,
    )

    assert result.exit_code == 0
    assert result.report_path == output_path
    report = output_path.read_text(encoding="utf-8")
    assert "Total questions: 3" in report
    assert "Successful: 2" in report
    assert "Failed: 1" in report
    assert "| concept | 1 / 5 | 1 | 0 |" in report
    assert "| protocol_detail | 1 / 5 | 1 | 0 |" in report
    assert "| lab | 1 / 5 | 0 | 1 |" in report
    assert "| introductory | 1 / 7 | 1 | 0 |" in report
    assert "| intermediate | 1 / 18 | 1 | 0 |" in report
    assert "| advanced | 1 / 5 | 0 | 1 |" in report
    assert "| correctness | 3.00 (n=2) |" in report
    assert "| citation_accuracy | 3.00 (n=1) |" in report
    assert "| hallucination_rate | 0.250 (n=2) |" in report
    assert "QA-LAB-002" in report
    assert "test-model" in report
    assert "test-embedding" in report
    assert "test-reranker" in report
    assert "abc123def" in report
    assert "未定义，未计算" in report


def test_missing_required_field_does_not_overwrite_existing_report(tmp_path: Path) -> None:
    run_file = tmp_path / "run.jsonl"
    output_path = tmp_path / "baseline.md"
    record = _run_record(
        "QA-CONCEPT-001",
        scores={
            "correctness": 4,
            "citation_accuracy": 4,
            "hallucination_rate": 0.0,
        },
    )
    del record["runtime"]
    _write_jsonl(run_file, [record])
    output_path.write_text("existing report\n", encoding="utf-8")

    result = generate_evaluation_report(
        run_file,
        question_bank_path=QUESTION_BANK,
        output_path=output_path,
    )

    assert result.exit_code != 0
    assert any("missing required fields" in issue.reason for issue in result.issues)
    assert output_path.read_text(encoding="utf-8") == "existing report\n"


def test_no_scores_does_not_generate_or_overwrite_report(tmp_path: Path) -> None:
    run_file = tmp_path / "run.jsonl"
    output_path = tmp_path / "baseline.md"
    _write_jsonl(run_file, [_run_record("QA-CONCEPT-001", scores=None)])
    output_path.write_text("existing report\n", encoding="utf-8")

    result = generate_evaluation_report(
        run_file,
        question_bank_path=QUESTION_BANK,
        output_path=output_path,
    )

    assert result.exit_code != 0
    assert "no valid scores" in result.message
    assert output_path.read_text(encoding="utf-8") == "existing report\n"


def test_missing_run_file_does_not_overwrite_existing_report(tmp_path: Path) -> None:
    output_path = tmp_path / "baseline.md"
    output_path.write_text("existing report\n", encoding="utf-8")

    result = generate_evaluation_report(
        tmp_path / "missing-run.jsonl",
        question_bank_path=QUESTION_BANK,
        output_path=output_path,
    )

    assert result.exit_code != 0
    assert "does not exist" in result.message
    assert output_path.read_text(encoding="utf-8") == "existing report\n"


def test_multiple_run_ids_are_rejected_without_overwriting_report(tmp_path: Path) -> None:
    run_file = tmp_path / "run.jsonl"
    output_path = tmp_path / "baseline.md"
    records = [
        _run_record(
            "QA-CONCEPT-001",
            scores={
                "correctness": 4,
                "citation_accuracy": 4,
                "hallucination_rate": 0.0,
            },
        ),
        _run_record(
            "QA-PROTOCOL-001",
            scores={
                "correctness": 3,
                "citation_accuracy": 3,
                "hallucination_rate": 0.2,
            },
            run_id="RUN-20260803T000001Z-test",
        ),
    ]
    _write_jsonl(run_file, records)
    output_path.write_text("existing report\n", encoding="utf-8")

    result = generate_evaluation_report(
        run_file,
        question_bank_path=QUESTION_BANK,
        output_path=output_path,
    )

    assert result.exit_code != 0
    assert any("multiple run_id" in issue.reason for issue in result.issues)
    assert output_path.read_text(encoding="utf-8") == "existing report\n"
