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

from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.domain.enums import Difficulty, QuestionCategory  # noqa: E402
from app.domain.models import EvaluationItem  # noqa: E402


SCORE_RANGES = {
    "correctness": (0.0, 4.0),
    "citation_accuracy": (0.0, 4.0),
    "hallucination_rate": (0.0, 1.0),
}
REQUIRED_RESULT_FIELDS = {
    "run_id",
    "evaluation_id",
    "generated_answer",
    "citations",
    "scores",
    "error",
    "runtime",
}


@dataclass(frozen=True)
class ReportIssue:
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
class RunRecord:
    line_number: int
    raw: dict[str, Any]

    @property
    def evaluation_id(self) -> str:
        return self.raw["evaluation_id"]


@dataclass(frozen=True)
class ReportResult:
    exit_code: int
    report_path: Path | None
    issues: list[ReportIssue]
    message: str


def _read_jsonl(path: Path, issues: list[ReportIssue]) -> list[tuple[int, Any]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        issues.append(ReportIssue(path, None, None, f"cannot read JSONL file: {error}"))
        return []

    records: list[tuple[int, Any]] = []
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            records.append((line_number, json.loads(line)))
        except json.JSONDecodeError as error:
            issues.append(
                ReportIssue(path, line_number, None, f"invalid JSON: {error.msg}")
            )
    return records


def _load_question_bank(path: Path, issues: list[ReportIssue]) -> dict[str, EvaluationItem]:
    items: dict[str, EvaluationItem] = {}
    for line_number, raw in _read_jsonl(path, issues):
        if not isinstance(raw, dict):
            issues.append(
                ReportIssue(path, line_number, None, "JSONL record must be an object")
            )
            continue
        evaluation_id = raw.get("evaluation_id")
        try:
            item = EvaluationItem.model_validate(raw)
        except ValidationError as error:
            issues.append(
                ReportIssue(
                    path,
                    line_number,
                    evaluation_id if isinstance(evaluation_id, str) else None,
                    f"question-bank validation failed: {error}",
                )
            )
            continue
        if item.evaluation_id in items:
            issues.append(
                ReportIssue(
                    path,
                    line_number,
                    item.evaluation_id,
                    "duplicate evaluation_id in question bank",
                )
            )
            continue
        items[item.evaluation_id] = item
    return items


def _validate_score_value(
    value: object,
    metric: str,
    path: Path,
    line_number: int,
    evaluation_id: str | None,
    issues: list[ReportIssue],
) -> None:
    if value is None:
        return
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        issues.append(
            ReportIssue(
                path,
                line_number,
                evaluation_id,
                f"scores.{metric} must be a number or null",
            )
        )
        return
    lower, upper = SCORE_RANGES[metric]
    if not lower <= float(value) <= upper:
        issues.append(
            ReportIssue(
                path,
                line_number,
                evaluation_id,
                f"scores.{metric} must be between {lower} and {upper}",
            )
        )


def _validate_run_record(
    raw: object,
    path: Path,
    line_number: int,
    issues: list[ReportIssue],
) -> RunRecord | None:
    if not isinstance(raw, dict):
        issues.append(ReportIssue(path, line_number, None, "run record must be an object"))
        return None
    evaluation_id = raw.get("evaluation_id")
    identifier = evaluation_id if isinstance(evaluation_id, str) else None
    missing_fields = REQUIRED_RESULT_FIELDS - raw.keys()
    if missing_fields:
        issues.append(
            ReportIssue(
                path,
                line_number,
                identifier,
                "missing required fields: " + ", ".join(sorted(missing_fields)),
            )
        )
        return None
    if not isinstance(raw["run_id"], str) or not raw["run_id"].strip():
        issues.append(ReportIssue(path, line_number, identifier, "run_id must be non-empty"))
    if not isinstance(evaluation_id, str) or not evaluation_id.strip():
        issues.append(
            ReportIssue(path, line_number, identifier, "evaluation_id must be non-empty")
        )
    if not isinstance(raw["generated_answer"], str):
        issues.append(
            ReportIssue(path, line_number, identifier, "generated_answer must be a string")
        )
    if not isinstance(raw["citations"], list):
        issues.append(ReportIssue(path, line_number, identifier, "citations must be a list"))
    if raw["error"] is not None and not isinstance(raw["error"], str):
        issues.append(ReportIssue(path, line_number, identifier, "error must be a string or null"))
    runtime = raw["runtime"]
    if not isinstance(runtime, dict):
        issues.append(ReportIssue(path, line_number, identifier, "runtime must be an object"))
    elif "git_commit" not in runtime:
        issues.append(
            ReportIssue(path, line_number, identifier, "runtime.git_commit is required")
        )

    scores = raw["scores"]
    if scores is not None:
        if not isinstance(scores, dict):
            issues.append(ReportIssue(path, line_number, identifier, "scores must be an object or null"))
        else:
            missing_metrics = set(SCORE_RANGES) - scores.keys()
            if missing_metrics:
                issues.append(
                    ReportIssue(
                        path,
                        line_number,
                        identifier,
                        "scores missing metrics: " + ", ".join(sorted(missing_metrics)),
                    )
                )
            for metric in set(SCORE_RANGES) & scores.keys():
                _validate_score_value(
                    scores[metric], metric, path, line_number, identifier, issues
                )
    return RunRecord(line_number, raw)


def _load_run_file(path: Path, issues: list[ReportIssue]) -> list[RunRecord]:
    records: list[RunRecord] = []
    for line_number, raw in _read_jsonl(path, issues):
        record = _validate_run_record(raw, path, line_number, issues)
        if record is not None:
            records.append(record)
    seen_ids: set[str] = set()
    run_ids: set[str] = set()
    for record in records:
        if record.evaluation_id in seen_ids:
            issues.append(
                ReportIssue(
                    path,
                    record.line_number,
                    record.evaluation_id,
                    "duplicate evaluation_id in run file",
                )
            )
        seen_ids.add(record.evaluation_id)
        run_ids.add(record.raw["run_id"])
    if len(run_ids) > 1:
        issues.append(
            ReportIssue(path, None, None, "multiple run_id values in one run file")
        )
    return records


def _format_value(value: object) -> str:
    if value is None:
        return "`null`"
    return f"`{value}`"


def _format_average(values: list[float], precision: int) -> str:
    if not values:
        return "暂不可评 (n=0)"
    return f"{sum(values) / len(values):.{precision}f} (n={len(values)})"


def _list_ids(evaluation_ids: list[str]) -> str:
    return ", ".join(f"`{evaluation_id}`" for evaluation_id in evaluation_ids) or "无"


def _runtime_values(records: list[RunRecord], field: str) -> str:
    values = {
        json.dumps(record.raw["runtime"].get(field), ensure_ascii=False, sort_keys=True)
        for record in records
        if isinstance(record.raw["runtime"], dict)
    }
    return ", ".join(f"`{value}`" for value in sorted(values)) or "`null`"


def _build_report(run_file: Path, records: list[RunRecord], questions: dict[str, EvaluationItem]) -> str:
    run_id = records[0].raw["run_id"]
    failed_ids = [record.evaluation_id for record in records if record.raw["error"] is not None]
    successful_ids = [record.evaluation_id for record in records if record.raw["error"] is None]
    unscored_ids: list[str] = []
    uncited_ids: list[str] = []
    score_values: dict[str, list[float]] = defaultdict(list)
    category_counts: dict[QuestionCategory, Counter[str]] = {
        category: Counter() for category in QuestionCategory
    }
    difficulty_counts: dict[Difficulty, Counter[str]] = {
        difficulty: Counter() for difficulty in Difficulty
    }
    question_category_totals = Counter(item.category for item in questions.values())
    question_difficulty_totals = Counter(item.difficulty for item in questions.values())

    for record in records:
        item = questions[record.evaluation_id]
        state = "failed" if record.raw["error"] is not None else "successful"
        category_counts[item.category]["completed"] += 1
        category_counts[item.category][state] += 1
        difficulty_counts[item.difficulty]["completed"] += 1
        difficulty_counts[item.difficulty][state] += 1
        if not record.raw["citations"]:
            uncited_ids.append(record.evaluation_id)
        scores = record.raw["scores"]
        if scores is None or not any(value is not None for value in scores.values()):
            unscored_ids.append(record.evaluation_id)
            continue
        for metric in SCORE_RANGES:
            value = scores[metric]
            if value is not None:
                score_values[metric].append(float(value))

    lines = [
        "# Evaluation Baseline Report",
        "",
        f"- Run ID: `{run_id}`",
        f"- Run file: `{run_file}`",
        "- Total-score formula: 未定义，未计算。",
        "",
        "## Runtime",
        "",
        "| Parameter | Value |",
        "| --- | --- |",
        f"| Model | {_runtime_values(records, 'model')} |",
        f"| Embedding | {_runtime_values(records, 'embedding')} |",
        f"| Reranker | {_runtime_values(records, 'reranker')} |",
        f"| top_k | {_runtime_values(records, 'top_k')} |",
        f"| Git commit | {_runtime_values(records, 'git_commit')} |",
        "",
        "## Execution Summary",
        "",
        f"- Total questions: {len(records)}",
        f"- Successful: {len(successful_ids)}",
        f"- Failed: {len(failed_ids)}",
        "",
        "## Completion by Category",
        "",
        "| Category | Completed / question bank | Successful | Failed |",
        "| --- | ---: | ---: | ---: |",
    ]
    for category in QuestionCategory:
        counts = category_counts[category]
        lines.append(
            f"| {category.value} | {counts['completed']} / "
            f"{question_category_totals[category]} | {counts['successful']} | {counts['failed']} |"
        )
    lines.extend(
        [
            "",
            "## Completion by Difficulty",
            "",
            "| Difficulty | Completed / question bank | Successful | Failed |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for difficulty in Difficulty:
        counts = difficulty_counts[difficulty]
        lines.append(
            f"| {difficulty.value} | {counts['completed']} / "
            f"{question_difficulty_totals[difficulty]} | {counts['successful']} | {counts['failed']} |"
        )
    lines.extend(
        [
            "",
            "## Metric Averages",
            "",
            "| Metric | Average |",
            "| --- | ---: |",
            f"| correctness | {_format_average(score_values['correctness'], 2)} |",
            f"| citation_accuracy | {_format_average(score_values['citation_accuracy'], 2)} |",
            f"| hallucination_rate | {_format_average(score_values['hallucination_rate'], 3)} |",
            "",
            "## Items Requiring Follow-up",
            "",
            f"- No scores: {_list_ids(unscored_ids)}",
            f"- No citations: {_list_ids(uncited_ids)}",
            f"- Execution failures: {_list_ids(failed_ids)}",
            "",
        ]
    )
    return "\n".join(lines)


def _atomic_write_text(path: Path, content: str) -> None:
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
            temporary_file.write(content)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def generate_evaluation_report(
    run_file: Path,
    *,
    question_bank_path: Path | None = None,
    output_path: Path | None = None,
) -> ReportResult:
    questions_path = question_bank_path or ROOT / "evaluation" / "question_bank.jsonl"
    report_path = output_path or ROOT / "evaluation" / "reports" / "baseline.md"
    if not run_file.is_file():
        return ReportResult(
            2,
            None,
            [],
            "Run file does not exist; baseline report was not generated.",
        )
    issues: list[ReportIssue] = []
    questions = _load_question_bank(questions_path, issues)
    records = _load_run_file(run_file, issues)
    for record in records:
        if record.evaluation_id not in questions:
            issues.append(
                ReportIssue(
                    run_file,
                    record.line_number,
                    record.evaluation_id,
                    "evaluation_id is not present in question bank",
                )
            )
    if issues:
        return ReportResult(1, None, issues, "Run-file validation failed.")
    if not records:
        return ReportResult(2, None, [], "Run file contains no evaluation results.")
    has_score = any(
        record.raw["scores"] is not None
        and any(value is not None for value in record.raw["scores"].values())
        for record in records
    )
    if not has_score:
        return ReportResult(
            2,
            None,
            [],
            "Run file has no valid scores; baseline report was not generated.",
        )
    _atomic_write_text(report_path, _build_report(run_file, records, questions))
    return ReportResult(0, report_path, [], "Baseline report generated.")


def _print_result(result: ReportResult) -> None:
    if result.issues:
        print(f"Evaluation report generation failed with {len(result.issues)} issue(s):")
        for issue in result.issues:
            print(f"- {issue.format()}")
        return
    print(result.message)
    if result.report_path is not None:
        print(f"Report: {result.report_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate an evaluation summary report.")
    parser.add_argument("--run-file", type=Path, required=True)
    parser.add_argument(
        "--question-bank", type=Path, default=ROOT / "evaluation" / "question_bank.jsonl"
    )
    parser.add_argument(
        "--output", type=Path, default=ROOT / "evaluation" / "reports" / "baseline.md"
    )
    args = parser.parse_args()
    result = generate_evaluation_report(
        args.run_file,
        question_bank_path=args.question_bank,
        output_path=args.output,
    )
    _print_result(result)
    return result.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
