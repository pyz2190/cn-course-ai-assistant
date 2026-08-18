import json
from pathlib import Path

from scripts.score_evaluation_run import apply_scores, prepare_score_file

PROJECT_ROOT = Path(__file__).resolve().parents[3]
ANNOTATIONS = PROJECT_ROOT / "evaluation" / "annotations.jsonl"
RUN_ID = "RUN-20260803T000000Z-score-test"


def _write_jsonl(path: Path, records: list[dict[str, object]]) -> None:
    path.write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
        encoding="utf-8",
    )


def _load_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _run_record(evaluation_id: str, *, error: str | None = None) -> dict[str, object]:
    return {
        "run_id": RUN_ID,
        "evaluation_id": evaluation_id,
        "generated_answer": "generated answer" if error is None else "",
        "citations": [{"chunk_id": "chunk-test"}] if error is None else [],
        "scores": None,
        "error": error,
        "runtime": {
            "model": "test-model",
            "embedding": "test-embedding",
            "reranker": "test-reranker",
            "top_k": 5,
            "git_commit": "abc123def",
        },
    }


def _prepare_records(tmp_path: Path, records: list[dict[str, object]]) -> tuple[Path, Path]:
    run_file = tmp_path / f"{RUN_ID}.jsonl"
    score_file = tmp_path / f"{RUN_ID}.scores.jsonl"
    _write_jsonl(run_file, records)
    result = prepare_score_file(
        run_file,
        annotations_path=ANNOTATIONS,
        score_file=score_file,
    )
    assert result.exit_code == 0
    return run_file, score_file


def _complete_success_score(record: dict[str, object]) -> None:
    record.update(
        {
            "correctness": 4,
            "citation_accuracy": 3,
            "hallucination_rate": 0.25,
            "reviewer": "reviewer-test",
            "notes": "人工评分完成。",
        }
    )


def test_prepare_creates_blank_human_score_file(tmp_path: Path) -> None:
    run_file, score_file = _prepare_records(
        tmp_path,
        [_run_record("QA-CONCEPT-001"), _run_record("QA-LAB-002", error="timeout")],
    )

    prepared = _load_jsonl(score_file)

    assert len(prepared) == 2
    assert prepared[0]["run_id"] == RUN_ID
    assert prepared[0]["evaluation_id"] == "QA-CONCEPT-001"
    assert prepared[0]["generated_answer"] == "generated answer"
    assert prepared[0]["citations"] == [{"chunk_id": "chunk-test"}]
    assert prepared[0]["key_points"]
    # B 已补充引用，expected_citations 应非空
    assert prepared[0]["expected_citations"]
    assert all(record[field] is None for record in prepared for field in (
        "correctness",
        "citation_accuracy",
        "hallucination_rate",
        "reviewer",
    ))
    assert all(record["notes"] == "" for record in prepared)
    assert run_file.read_text(encoding="utf-8")


def test_apply_merges_valid_scores_and_allows_unscored_failure(tmp_path: Path) -> None:
    run_file, score_file = _prepare_records(
        tmp_path,
        [_run_record("QA-CONCEPT-001"), _run_record("QA-LAB-002", error="timeout")],
    )
    original_run = run_file.read_text(encoding="utf-8")
    score_records = _load_jsonl(score_file)
    _complete_success_score(score_records[0])
    _write_jsonl(score_file, score_records)

    result = apply_scores(run_file, score_file)

    assert result.exit_code == 0
    assert result.output_path == run_file.with_name(f"{RUN_ID}.scored.jsonl")
    assert run_file.read_text(encoding="utf-8") == original_run
    scored = _load_jsonl(result.output_path)
    assert scored[0]["scores"] == {
        "correctness": 4,
        "citation_accuracy": 3,
        "hallucination_rate": 0.25,
    }
    assert scored[0]["score_reviewer"] == "reviewer-test"
    assert scored[0]["score_notes"] == "人工评分完成。"
    assert scored[1]["scores"] == {
        "correctness": None,
        "citation_accuracy": None,
        "hallucination_rate": None,
    }
    assert scored[1]["score_reviewer"] is None


def test_apply_rejects_out_of_range_scores(tmp_path: Path) -> None:
    run_file, score_file = _prepare_records(tmp_path, [_run_record("QA-CONCEPT-001")])
    score_records = _load_jsonl(score_file)
    _complete_success_score(score_records[0])
    score_records[0]["correctness"] = 5
    _write_jsonl(score_file, score_records)

    result = apply_scores(run_file, score_file)

    assert result.exit_code != 0
    assert any("correctness must be between" in issue.reason for issue in result.issues)
    assert not run_file.with_name(f"{RUN_ID}.scored.jsonl").exists()


def test_apply_rejects_success_score_without_reviewer(tmp_path: Path) -> None:
    run_file, score_file = _prepare_records(tmp_path, [_run_record("QA-CONCEPT-001")])
    score_records = _load_jsonl(score_file)
    _complete_success_score(score_records[0])
    score_records[0]["reviewer"] = None
    _write_jsonl(score_file, score_records)

    result = apply_scores(run_file, score_file)

    assert result.exit_code != 0
    assert any("non-empty reviewer" in issue.reason for issue in result.issues)


def test_apply_rejects_score_id_mismatch(tmp_path: Path) -> None:
    run_file, score_file = _prepare_records(tmp_path, [_run_record("QA-CONCEPT-001")])
    score_records = _load_jsonl(score_file)
    score_records[0]["evaluation_id"] = "QA-UNEXPECTED-001"
    _write_jsonl(score_file, score_records)

    result = apply_scores(run_file, score_file)

    assert result.exit_code != 0
    assert any("missing score items" in issue.reason for issue in result.issues)
    assert any("extra score items" in issue.reason for issue in result.issues)


def test_apply_rejects_duplicate_score_entries(tmp_path: Path) -> None:
    run_file, score_file = _prepare_records(tmp_path, [_run_record("QA-CONCEPT-001")])
    score_records = _load_jsonl(score_file)
    _write_jsonl(score_file, [score_records[0], score_records[0]])

    result = apply_scores(run_file, score_file)

    assert result.exit_code != 0
    assert any("duplicate evaluation_id" in issue.reason for issue in result.issues)
