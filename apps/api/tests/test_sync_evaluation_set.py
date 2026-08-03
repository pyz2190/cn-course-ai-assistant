import json
from collections import Counter
from pathlib import Path

from scripts.sync_evaluation_set import sync_evaluation_set

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


def _approve_items(directory: Path, evaluation_ids: set[str]) -> None:
    annotations_path = directory / "annotations.jsonl"
    annotations = _load_jsonl(annotations_path)
    for annotation in annotations:
        if annotation["evaluation_id"] not in evaluation_ids:
            continue
        annotation.update(
            {
                "review_status": "approved",
                "reviewer": "reviewer-test",
                "reviewed_at": "2026-08-03T00:00:00Z",
                "expected_citations": [
                    {
                        "resource_id": "resource-test-citation",
                        "chunk_id": "chunk-test-citation",
                    }
                ],
            }
        )
    _write_jsonl(annotations_path, annotations)


def _balanced_approved_ids(directory: Path) -> set[str]:
    questions = _load_jsonl(directory / "question_bank.jsonl")
    by_category: dict[str, list[str]] = {}
    for question in questions:
        by_category.setdefault(question["category"], []).append(question["evaluation_id"])
    return {
        evaluation_id
        for category_ids in by_category.values()
        for evaluation_id in category_ids[:3]
    }


def test_sync_current_data_with_no_approved_items_keeps_empty_set(tmp_path: Path) -> None:
    directory = _copy_evaluation_data(tmp_path)

    result = sync_evaluation_set(directory)

    assert result.exit_code == 0
    assert result.selected_ids == []
    assert "No approved evaluation items" in result.message
    assert (directory / "evaluation_set.jsonl").read_text(encoding="utf-8") == ""


def test_sync_dry_run_does_not_write_output(tmp_path: Path) -> None:
    directory = _copy_evaluation_data(tmp_path)
    approved_ids = _balanced_approved_ids(directory)
    _approve_items(directory, approved_ids)
    output_path = directory / "evaluation_set.jsonl"
    output_path.write_text("existing formal data\n", encoding="utf-8")

    result = sync_evaluation_set(directory, dry_run=True)

    assert result.exit_code == 0
    assert set(result.selected_ids) == approved_ids
    assert result.wrote_output is False
    assert output_path.read_text(encoding="utf-8") == "existing formal data\n"


def test_sync_insufficient_approved_items_preserves_existing_set(tmp_path: Path) -> None:
    directory = _copy_evaluation_data(tmp_path)
    questions = _load_jsonl(directory / "question_bank.jsonl")
    _approve_items(directory, {item["evaluation_id"] for item in questions[:14]})
    output_path = directory / "evaluation_set.jsonl"
    output_path.write_text("existing formal data\n", encoding="utf-8")

    result = sync_evaluation_set(directory)

    assert result.exit_code != 0
    assert result.selected_ids == []
    assert "missing 1" in result.message
    assert "approved by category" in result.message
    assert output_path.read_text(encoding="utf-8") == "existing formal data\n"


def test_sync_selects_only_approved_balanced_original_records_deterministically(
    tmp_path: Path,
) -> None:
    directory = _copy_evaluation_data(tmp_path)
    approved_ids = _balanced_approved_ids(directory)
    _approve_items(directory, approved_ids)
    question_by_id = {
        item["evaluation_id"]: item
        for item in _load_jsonl(directory / "question_bank.jsonl")
    }

    first_result = sync_evaluation_set(directory)
    first_output = (directory / "evaluation_set.jsonl").read_text(encoding="utf-8")
    selected = _load_jsonl(directory / "evaluation_set.jsonl")
    second_result = sync_evaluation_set(directory)
    second_output = (directory / "evaluation_set.jsonl").read_text(encoding="utf-8")

    assert first_result.exit_code == 0
    assert second_result.exit_code == 0
    assert len(selected) == 18
    assert set(first_result.selected_ids) == approved_ids
    assert first_result.selected_ids == second_result.selected_ids
    assert first_output == second_output
    assert {item["evaluation_id"] for item in selected} == approved_ids
    assert Counter(item["category"] for item in selected) == {
        "concept": 3,
        "protocol_detail": 3,
        "tool_tutorial": 3,
        "lab": 3,
        "common_error": 3,
        "review": 3,
    }
    assert {item["difficulty"] for item in selected} == {
        "introductory",
        "intermediate",
        "advanced",
    }
    assert all(item == question_by_id[item["evaluation_id"]] for item in selected)
