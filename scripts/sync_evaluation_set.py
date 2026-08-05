from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ValidationError

ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.domain.enums import Difficulty, QuestionCategory
from app.domain.models import EvaluationAnnotation, EvaluationItem

MINIMUM_SET_SIZE = 15
PREFERRED_SET_SIZE = 18
CATEGORY_ORDER = list(QuestionCategory)
DIFFICULTY_ORDER = list(Difficulty)


@dataclass(frozen=True)
class SyncIssue:
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
class Record:
    line_number: int
    raw: dict[str, Any]
    value: EvaluationItem | EvaluationAnnotation

    @property
    def evaluation_id(self) -> str:
        return self.value.evaluation_id


@dataclass(frozen=True)
class SyncResult:
    exit_code: int
    selected_ids: list[str]
    approved_count: int
    issues: list[SyncIssue]
    wrote_output: bool
    message: str


def _validation_error_message(error: ValidationError) -> str:
    return "; ".join(
        f"{'.'.join(str(part) for part in item['loc'])}: {item['msg']}"
        for item in error.errors()
    )


def _load_jsonl(
    path: Path,
    model: type[BaseModel],
    issues: list[SyncIssue],
) -> list[Record]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        issues.append(SyncIssue(path, None, None, f"cannot read JSONL file: {error}"))
        return []

    records: list[Record] = []
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as error:
            issues.append(
                SyncIssue(path, line_number, None, f"invalid JSON: {error.msg}")
            )
            continue
        if not isinstance(raw, dict):
            issues.append(
                SyncIssue(path, line_number, None, "JSONL record must be an object")
            )
            continue
        evaluation_id = raw.get("evaluation_id")
        try:
            value = model.model_validate(raw)
        except ValidationError as error:
            issues.append(
                SyncIssue(
                    path,
                    line_number,
                    evaluation_id if isinstance(evaluation_id, str) else None,
                    f"model validation failed: {_validation_error_message(error)}",
                )
            )
            continue
        records.append(Record(line_number, raw, value))
    return records


def _add_duplicate_issues(
    records: list[Record], path: Path, issues: list[SyncIssue]
) -> None:
    records_by_id: dict[str, list[Record]] = defaultdict(list)
    for record in records:
        records_by_id[record.evaluation_id].append(record)
    for evaluation_id, matches in records_by_id.items():
        for record in matches[1:]:
            issues.append(
                SyncIssue(
                    path,
                    record.line_number,
                    evaluation_id,
                    f"duplicate evaluation_id; first appears on line {matches[0].line_number}",
                )
            )


def _category_quotas(target_size: int) -> dict[QuestionCategory, int]:
    base, remainder = divmod(target_size, len(CATEGORY_ORDER))
    return {
        category: base + (index < remainder)
        for index, category in enumerate(CATEGORY_ORDER)
    }


def _ordered_category_records(records: list[Record]) -> list[Record]:
    by_difficulty: dict[Difficulty, list[Record]] = defaultdict(list)
    for record in records:
        item = record.value
        if isinstance(item, EvaluationItem):
            by_difficulty[item.difficulty].append(record)
    for difficulty_records in by_difficulty.values():
        difficulty_records.sort(key=lambda record: record.evaluation_id)

    ordered: list[Record] = []
    while any(by_difficulty.values()):
        for difficulty in DIFFICULTY_ORDER:
            if by_difficulty[difficulty]:
                ordered.append(by_difficulty[difficulty].pop(0))
    return ordered


def _select_balanced_records(records: list[Record], target_size: int) -> list[Record]:
    by_category: dict[QuestionCategory, list[Record]] = defaultdict(list)
    for record in records:
        item = record.value
        if isinstance(item, EvaluationItem):
            by_category[item.category].append(record)

    ordered = {
        category: _ordered_category_records(by_category[category])
        for category in CATEGORY_ORDER
    }
    quotas = _category_quotas(target_size)
    selected_by_category: dict[QuestionCategory, list[Record]] = {}
    next_index: dict[QuestionCategory, int] = {}
    shortfall = 0
    for category in CATEGORY_ORDER:
        limit = min(quotas[category], len(ordered[category]))
        selected_by_category[category] = ordered[category][:limit]
        next_index[category] = limit
        shortfall += quotas[category] - limit

    while shortfall:
        candidates = [
            category
            for category in CATEGORY_ORDER
            if next_index[category] < len(ordered[category])
        ]
        if not candidates:
            break
        category = min(
            candidates,
            key=lambda value: (len(selected_by_category[value]), CATEGORY_ORDER.index(value)),
        )
        selected_by_category[category].append(ordered[category][next_index[category]])
        next_index[category] += 1
        shortfall -= 1

    selected = [record for category in CATEGORY_ORDER for record in selected_by_category[category]]
    selected_difficulties = Counter(
        record.value.difficulty
        for record in selected
        if isinstance(record.value, EvaluationItem)
    )
    selected_ids = {record.evaluation_id for record in selected}
    for difficulty in DIFFICULTY_ORDER:
        if selected_difficulties[difficulty]:
            continue
        replacement: tuple[int, Record, Record] | None = None
        for candidate in sorted(records, key=lambda record: record.evaluation_id):
            item = candidate.value
            if (
                candidate.evaluation_id in selected_ids
                or not isinstance(item, EvaluationItem)
                or item.difficulty != difficulty
            ):
                continue
            for index, selected_record in enumerate(selected):
                selected_item = selected_record.value
                if (
                    isinstance(selected_item, EvaluationItem)
                    and selected_item.category == item.category
                    and selected_difficulties[selected_item.difficulty] > 1
                ):
                    replacement = (index, selected_record, candidate)
                    break
            if replacement is not None:
                break
        if replacement is None:
            continue
        index, removed, added = replacement
        removed_item = removed.value
        added_item = added.value
        if isinstance(removed_item, EvaluationItem) and isinstance(added_item, EvaluationItem):
            selected[index] = added
            selected_ids.remove(removed.evaluation_id)
            selected_ids.add(added.evaluation_id)
            selected_difficulties[removed_item.difficulty] -= 1
            selected_difficulties[added_item.difficulty] += 1
    return sorted(selected, key=lambda record: record.evaluation_id)


def _atomic_write_jsonl(path: Path, records: list[Record]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            for record in records:
                temporary_file.write(json.dumps(record.raw, ensure_ascii=False) + "\n")
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def _approved_category_summary(records: list[Record]) -> str:
    counts = {category: 0 for category in CATEGORY_ORDER}
    for record in records:
        item = record.value
        if isinstance(item, EvaluationItem):
            counts[item.category] += 1
    return ", ".join(f"{category.value}={counts[category]}" for category in CATEGORY_ORDER)


def sync_evaluation_set(
    evaluation_directory: Path | None = None,
    *,
    dry_run: bool = False,
) -> SyncResult:
    directory = evaluation_directory or ROOT / "evaluation"
    question_path = directory / "question_bank.jsonl"
    annotation_path = directory / "annotations.jsonl"
    output_path = directory / "evaluation_set.jsonl"
    issues: list[SyncIssue] = []
    questions = _load_jsonl(question_path, EvaluationItem, issues)
    annotations = _load_jsonl(annotation_path, EvaluationAnnotation, issues)
    _add_duplicate_issues(questions, question_path, issues)
    _add_duplicate_issues(annotations, annotation_path, issues)

    questions_by_id = {record.evaluation_id: record for record in questions}
    annotations_by_id = {record.evaluation_id: record for record in annotations}
    for evaluation_id, question in questions_by_id.items():
        if evaluation_id not in annotations_by_id:
            issues.append(
                SyncIssue(
                    question_path,
                    question.line_number,
                    evaluation_id,
                    "question has no matching annotation",
                )
            )
    for evaluation_id, annotation in annotations_by_id.items():
        if evaluation_id not in questions_by_id:
            issues.append(
                SyncIssue(
                    annotation_path,
                    annotation.line_number,
                    evaluation_id,
                    "annotation has no matching question",
                )
            )
        elif isinstance(annotation.value, EvaluationAnnotation) and (
            annotation.value.review_status.value == "approved"
            and not annotation.value.expected_citations
        ):
            issues.append(
                SyncIssue(
                    annotation_path,
                    annotation.line_number,
                    evaluation_id,
                    "approved annotation requires at least one expected citation",
                )
            )

    if issues:
        return SyncResult(1, [], 0, issues, False, "Input validation failed.")

    approved_questions = [
        questions_by_id[evaluation_id]
        for evaluation_id, annotation in annotations_by_id.items()
        if isinstance(annotation.value, EvaluationAnnotation)
        and annotation.value.review_status.value == "approved"
    ]
    approved_questions.sort(key=lambda record: record.evaluation_id)
    approved_count = len(approved_questions)
    if approved_count == 0:
        if not dry_run:
            _atomic_write_jsonl(output_path, [])
        return SyncResult(
            0,
            [],
            0,
            [],
            not dry_run,
            "No approved evaluation items; evaluation_set.jsonl remains empty.",
        )
    if approved_count < MINIMUM_SET_SIZE:
        missing = MINIMUM_SET_SIZE - approved_count
        summary = _approved_category_summary(approved_questions)
        return SyncResult(
            2,
            [],
            approved_count,
            [],
            False,
            f"Approved items are insufficient: missing {missing} to reach {MINIMUM_SET_SIZE}; "
            f"approved by category: {summary}.",
        )

    target_size = min(PREFERRED_SET_SIZE, approved_count)
    selected = _select_balanced_records(approved_questions, target_size)
    if not dry_run:
        _atomic_write_jsonl(output_path, selected)
    return SyncResult(
        0,
        [record.evaluation_id for record in selected],
        approved_count,
        [],
        not dry_run,
        f"Selected {len(selected)} of {approved_count} approved items for the formal evaluation set.",
    )


def _print_result(result: SyncResult, *, dry_run: bool) -> None:
    if result.issues:
        print(f"Evaluation data validation failed with {len(result.issues)} issue(s):")
        for issue in result.issues:
            print(f"- {issue.format()}")
        return
    print(result.message)
    if result.selected_ids:
        prefix = "Dry-run selection" if dry_run else "Synced evaluation IDs"
        print(f"{prefix}:")
        for evaluation_id in result.selected_ids:
            print(f"- {evaluation_id}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Synchronize approved evaluation items.")
    parser.add_argument(
        "--dry-run", action="store_true", help="validate and print the selection only"
    )
    parser.add_argument("--evaluation-dir", type=Path, default=ROOT / "evaluation")
    args = parser.parse_args()
    result = sync_evaluation_set(args.evaluation_dir, dry_run=args.dry_run)
    _print_result(result, dry_run=args.dry_run)
    return result.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
