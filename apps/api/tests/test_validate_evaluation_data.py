import json
from pathlib import Path

from scripts.validate_evaluation_data import validate_evaluation_data

PROJECT_ROOT = Path(__file__).resolve().parents[3]
EVALUATION_DIRECTORY = PROJECT_ROOT / "evaluation"
JSONL_FILES = (
    "question_bank.jsonl",
    "annotations.jsonl",
    "evaluation_set.jsonl",
)


def _copy_evaluation_data(tmp_path: Path) -> Path:
    for name in JSONL_FILES:
        (tmp_path / name).write_text(
            (EVALUATION_DIRECTORY / name).read_text(encoding="utf-8"),
            encoding="utf-8",
        )
    return tmp_path


def _load_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _write_jsonl(path: Path, records: list[dict[str, object]]) -> None:
    path.write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
        encoding="utf-8",
    )


def _issue_reasons(tmp_path: Path) -> list[str]:
    return [issue.reason for issue in validate_evaluation_data(tmp_path).issues]


def test_current_evaluation_data_passes_validation() -> None:
    result = validate_evaluation_data(EVALUATION_DIRECTORY)

    assert result.issues == []
    assert result.question_count == 12
    assert result.annotation_count == 12
    assert result.evaluation_set_count == 0


def test_validator_reports_invalid_json(tmp_path: Path) -> None:
    directory = _copy_evaluation_data(tmp_path)
    question_bank = directory / "question_bank.jsonl"
    question_bank.write_text(
        question_bank.read_text(encoding="utf-8") + "{not valid json}\n",
        encoding="utf-8",
    )

    assert any("invalid JSON" in reason for reason in _issue_reasons(directory))


def test_validator_reports_duplicate_ids(tmp_path: Path) -> None:
    directory = _copy_evaluation_data(tmp_path)
    question_bank = directory / "question_bank.jsonl"
    question_bank.write_text(
        question_bank.read_text(encoding="utf-8")
        + question_bank.read_text(encoding="utf-8").splitlines()[0]
        + "\n",
        encoding="utf-8",
    )

    assert any("duplicate evaluation_id" in reason for reason in _issue_reasons(directory))


def test_validator_reports_orphan_annotation(tmp_path: Path) -> None:
    directory = _copy_evaluation_data(tmp_path)
    annotations_path = directory / "annotations.jsonl"
    annotations = _load_jsonl(annotations_path)
    annotations[0]["evaluation_id"] = "QA-ORPHAN-001"
    _write_jsonl(annotations_path, annotations)

    assert any(
        "annotation has no matching question" in reason for reason in _issue_reasons(directory)
    )


def test_validator_reports_approved_annotation_without_citation(tmp_path: Path) -> None:
    directory = _copy_evaluation_data(tmp_path)
    annotations_path = directory / "annotations.jsonl"
    annotations = _load_jsonl(annotations_path)
    annotations[0].update(
        {
            "review_status": "approved",
            "reviewer": "reviewer-1",
            "reviewed_at": "2026-08-03T00:00:00Z",
            "expected_citations": [],
        }
    )
    _write_jsonl(annotations_path, annotations)

    assert any(
        "approved annotation requires at least one expected citation" in reason
        for reason in _issue_reasons(directory)
    )


def test_validator_reports_unapproved_item_in_evaluation_set(tmp_path: Path) -> None:
    directory = _copy_evaluation_data(tmp_path)
    questions = _load_jsonl(directory / "question_bank.jsonl")
    _write_jsonl(directory / "evaluation_set.jsonl", [questions[0]])

    assert any(
        "evaluation set item is not approved" in reason for reason in _issue_reasons(directory)
    )


def test_validator_reports_tampered_evaluation_set_item(tmp_path: Path) -> None:
    directory = _copy_evaluation_data(tmp_path)
    annotations_path = directory / "annotations.jsonl"
    annotations = _load_jsonl(annotations_path)
    annotations[0].update(
        {
            "review_status": "approved",
            "reviewer": "reviewer-1",
            "reviewed_at": "2026-08-03T00:00:00Z",
            "expected_citations": [
                {
                    "resource_id": "course-resource-001",
                    "chunk_id": "course-chunk-001",
                }
            ],
        }
    )
    _write_jsonl(annotations_path, annotations)
    evaluation_set_item = _load_jsonl(directory / "question_bank.jsonl")[0]
    evaluation_set_item["question"] = "tampered question"
    _write_jsonl(directory / "evaluation_set.jsonl", [evaluation_set_item])

    assert any(
        "evaluation set item differs from the question-bank record" in reason
        for reason in _issue_reasons(directory)
    )
