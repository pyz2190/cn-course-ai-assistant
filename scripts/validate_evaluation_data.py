from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.domain.enums import QuestionCategory, ScoringDimension
from app.domain.models import EvaluationAnnotation, EvaluationItem
from pydantic import BaseModel, ValidationError

ROOT = Path(__file__).resolve().parents[1]

EXPECTED_CATEGORIES = set(QuestionCategory)
EXPECTED_DIMENSIONS = set(ScoringDimension)
PLACEHOLDER_PATTERN = re.compile(
    r"^(?:res|resource|chunk)[-_]?(?:1|01|id|placeholder|example|test)$"
)


@dataclass(frozen=True)
class ValidationIssue:
    path: Path
    line_number: int | None
    evaluation_id: str | None
    reason: str

    def format(self) -> str:
        location = str(self.path)
        if self.line_number is not None:
            location = f"{location}:{self.line_number}"
        identifier = self.evaluation_id or "unknown evaluation_id"
        return f"{location} [{identifier}] {self.reason}"


@dataclass(frozen=True)
class ValidatedRecord:
    path: Path
    line_number: int
    raw: dict[str, Any]
    value: EvaluationItem | EvaluationAnnotation

    @property
    def evaluation_id(self) -> str:
        return self.value.evaluation_id


@dataclass(frozen=True)
class ValidationResult:
    issues: list[ValidationIssue]
    question_count: int
    annotation_count: int
    evaluation_set_count: int
    status_counts: Counter[str]


def _raw_evaluation_id(payload: object) -> str | None:
    if isinstance(payload, dict) and isinstance(payload.get("evaluation_id"), str):
        return payload["evaluation_id"]
    return None


def _validation_error_message(error: ValidationError) -> str:
    details = []
    for item in error.errors():
        location = ".".join(str(part) for part in item["loc"])
        details.append(f"{location}: {item['msg']}")
    return "; ".join(details)


def _load_jsonl(
    path: Path,
    model: type[BaseModel],
    issues: list[ValidationIssue],
) -> list[ValidatedRecord]:
    records: list[ValidatedRecord] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        issues.append(
            ValidationIssue(path, None, None, f"cannot read JSONL file: {error}")
        )
        return records

    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as error:
            issues.append(
                ValidationIssue(path, line_number, None, f"invalid JSON: {error.msg}")
            )
            continue
        if not isinstance(payload, dict):
            issues.append(
                ValidationIssue(
                    path,
                    line_number,
                    None,
                    "JSONL record must be an object",
                )
            )
            continue
        try:
            value = model.model_validate(payload)
        except ValidationError as error:
            issues.append(
                ValidationIssue(
                    path,
                    line_number,
                    _raw_evaluation_id(payload),
                    f"model validation failed: {_validation_error_message(error)}",
                )
            )
            continue
        records.append(ValidatedRecord(path, line_number, payload, value))
    return records


def _check_duplicates(
    records: list[ValidatedRecord],
    issues: list[ValidationIssue],
) -> None:
    records_by_id: dict[str, list[ValidatedRecord]] = defaultdict(list)
    for record in records:
        records_by_id[record.evaluation_id].append(record)
    for evaluation_id, matching_records in records_by_id.items():
        for record in matching_records[1:]:
            first_line = matching_records[0].line_number
            issues.append(
                ValidationIssue(
                    record.path,
                    record.line_number,
                    evaluation_id,
                    f"duplicate evaluation_id; first appears on line {first_line}",
                )
            )


def _is_obvious_placeholder(value: str) -> bool:
    normalized = value.strip().lower()
    return (
        normalized in {"placeholder", "todo", "tbd"}
        or "placeholder" in normalized
        or PLACEHOLDER_PATTERN.fullmatch(normalized) is not None
    )


def _record_by_id(records: list[ValidatedRecord]) -> dict[str, ValidatedRecord]:
    return {record.evaluation_id: record for record in records}


def validate_evaluation_data(
    evaluation_directory: Path | None = None,
) -> ValidationResult:
    directory = evaluation_directory or ROOT / "evaluation"
    issues: list[ValidationIssue] = []
    questions = _load_jsonl(directory / "question_bank.jsonl", EvaluationItem, issues)
    annotations = _load_jsonl(
        directory / "annotations.jsonl", EvaluationAnnotation, issues
    )
    evaluation_set = _load_jsonl(
        directory / "evaluation_set.jsonl", EvaluationItem, issues
    )

    for records in (questions, annotations, evaluation_set):
        _check_duplicates(records, issues)

    questions_by_id = _record_by_id(questions)
    annotations_by_id = _record_by_id(annotations)
    evaluation_set_by_id = _record_by_id(evaluation_set)

    for evaluation_id, question in questions_by_id.items():
        if evaluation_id not in annotations_by_id:
            issues.append(
                ValidationIssue(
                    question.path,
                    question.line_number,
                    evaluation_id,
                    "question has no matching annotation",
                )
            )
    for evaluation_id, annotation in annotations_by_id.items():
        if evaluation_id not in questions_by_id:
            issues.append(
                ValidationIssue(
                    annotation.path,
                    annotation.line_number,
                    evaluation_id,
                    "annotation has no matching question",
                )
            )

    categories = {
        record.value.category
        for record in questions
        if isinstance(record.value, EvaluationItem)
    }
    missing_categories = EXPECTED_CATEGORIES - categories
    if missing_categories:
        issues.append(
            ValidationIssue(
                directory / "question_bank.jsonl",
                None,
                None,
                "missing categories: "
                + ", ".join(sorted(category.value for category in missing_categories)),
            )
        )

    for question in questions:
        value = question.value
        if not isinstance(value, EvaluationItem):
            continue
        if not value.knowledge_point_ids:
            issues.append(
                ValidationIssue(
                    question.path,
                    question.line_number,
                    question.evaluation_id,
                    "knowledge_point_ids must not be empty",
                )
            )
        if (
            len(value.scoring_dimensions) != len(EXPECTED_DIMENSIONS)
            or set(value.scoring_dimensions) != EXPECTED_DIMENSIONS
        ):
            issues.append(
                ValidationIssue(
                    question.path,
                    question.line_number,
                    question.evaluation_id,
                    "scoring_dimensions must contain each required dimension exactly once",
                )
            )

    approved_ids: set[str] = set()
    status_counts: Counter[str] = Counter()
    for annotation in annotations:
        value = annotation.value
        if not isinstance(value, EvaluationAnnotation):
            continue
        status = value.review_status.value
        status_counts[status] += 1
        if status in {"approved", "rejected"} and (
            not value.reviewer or value.reviewed_at is None
        ):
            issues.append(
                ValidationIssue(
                    annotation.path,
                    annotation.line_number,
                    annotation.evaluation_id,
                    f"{status} annotation requires reviewer and reviewed_at",
                )
            )
        if status == "approved":
            approved_ids.add(annotation.evaluation_id)
            if not value.expected_citations:
                issues.append(
                    ValidationIssue(
                        annotation.path,
                        annotation.line_number,
                        annotation.evaluation_id,
                        "approved annotation requires at least one expected citation",
                    )
                )
        for citation in value.expected_citations:
            if _is_obvious_placeholder(citation.resource_id):
                issues.append(
                    ValidationIssue(
                        annotation.path,
                        annotation.line_number,
                        annotation.evaluation_id,
                        "citation resource_id uses an obvious placeholder value",
                    )
                )
            if citation.chunk_id and _is_obvious_placeholder(citation.chunk_id):
                issues.append(
                    ValidationIssue(
                        annotation.path,
                        annotation.line_number,
                        annotation.evaluation_id,
                        "citation chunk_id uses an obvious placeholder value",
                    )
                )

    for evaluation_id, evaluation_item in evaluation_set_by_id.items():
        annotation = annotations_by_id.get(evaluation_id)
        source_item = questions_by_id.get(evaluation_id)
        if annotation is None:
            issues.append(
                ValidationIssue(
                    evaluation_item.path,
                    evaluation_item.line_number,
                    evaluation_id,
                    "evaluation set item has no matching annotation",
                )
            )
        elif not isinstance(annotation.value, EvaluationAnnotation) or (
            annotation.value.review_status.value != "approved"
        ):
            issues.append(
                ValidationIssue(
                    evaluation_item.path,
                    evaluation_item.line_number,
                    evaluation_id,
                    "evaluation set item is not approved",
                )
            )
        if source_item is None:
            issues.append(
                ValidationIssue(
                    evaluation_item.path,
                    evaluation_item.line_number,
                    evaluation_id,
                    "evaluation set item has no matching question-bank record",
                )
            )
        elif evaluation_item.raw != source_item.raw:
            issues.append(
                ValidationIssue(
                    evaluation_item.path,
                    evaluation_item.line_number,
                    evaluation_id,
                    "evaluation set item differs from the question-bank record",
                )
            )

    for evaluation_id in approved_ids - set(evaluation_set_by_id):
        annotation = annotations_by_id[evaluation_id]
        issues.append(
            ValidationIssue(
                annotation.path,
                annotation.line_number,
                evaluation_id,
                "approved annotation is missing from the evaluation set",
            )
        )

    return ValidationResult(
        issues=issues,
        question_count=len(questions),
        annotation_count=len(annotations),
        evaluation_set_count=len(evaluation_set),
        status_counts=status_counts,
    )


def _print_summary(result: ValidationResult) -> None:
    print(f"Question bank records: {result.question_count}")
    print(f"Annotation records: {result.annotation_count}")
    print(f"Evaluation set records: {result.evaluation_set_count}")
    print("Review status counts:")
    for status, count in sorted(result.status_counts.items()):
        print(f"- {status}: {count}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate evaluation JSONL data.")
    parser.add_argument(
        "--evaluation-dir",
        type=Path,
        default=ROOT / "evaluation",
        help="directory containing the three evaluation JSONL files",
    )
    args = parser.parse_args()
    result = validate_evaluation_data(args.evaluation_dir)
    _print_summary(result)
    if not result.issues:
        print("Evaluation data validation passed.")
        return 0

    print(f"Evaluation data validation failed with {len(result.issues)} issue(s):")
    for issue in result.issues:
        print(f"- {issue.format()}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
