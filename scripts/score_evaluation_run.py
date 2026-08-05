from __future__ import annotations

import argparse
import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.domain.models import EvaluationAnnotation
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[1]

SCORE_FIELDS = ("correctness", "citation_accuracy", "hallucination_rate")
RUN_REQUIRED_FIELDS = {
    "run_id",
    "evaluation_id",
    "generated_answer",
    "citations",
    "scores",
    "error",
    "runtime",
}
SCORE_FILE_REQUIRED_FIELDS = {
    "run_id",
    "evaluation_id",
    "generated_answer",
    "citations",
    "key_points",
    "expected_citations",
    *SCORE_FIELDS,
    "reviewer",
    "notes",
}


@dataclass(frozen=True)
class ScoreIssue:
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
class JsonRecord:
    line_number: int
    raw: dict[str, Any]

    @property
    def evaluation_id(self) -> str:
        return self.raw["evaluation_id"]


@dataclass(frozen=True)
class ScoreCommandResult:
    exit_code: int
    output_path: Path | None
    issues: list[ScoreIssue]
    message: str


def _read_jsonl(path: Path, issues: list[ScoreIssue]) -> list[tuple[int, Any]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        issues.append(ScoreIssue(path, None, None, f"cannot read JSONL file: {error}"))
        return []
    records: list[tuple[int, Any]] = []
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            records.append((line_number, json.loads(line)))
        except json.JSONDecodeError as error:
            issues.append(
                ScoreIssue(path, line_number, None, f"invalid JSON: {error.msg}")
            )
    return records


def _validate_run_record(
    raw: object,
    path: Path,
    line_number: int,
    issues: list[ScoreIssue],
) -> JsonRecord | None:
    if not isinstance(raw, dict):
        issues.append(ScoreIssue(path, line_number, None, "run record must be an object"))
        return None
    evaluation_id = raw.get("evaluation_id")
    identifier = evaluation_id if isinstance(evaluation_id, str) else None
    missing = RUN_REQUIRED_FIELDS - raw.keys()
    if missing:
        issues.append(
            ScoreIssue(
                path,
                line_number,
                identifier,
                "missing required fields: " + ", ".join(sorted(missing)),
            )
        )
        return None
    if not isinstance(raw["run_id"], str) or not raw["run_id"].strip():
        issues.append(ScoreIssue(path, line_number, identifier, "run_id must be non-empty"))
    if not isinstance(evaluation_id, str) or not evaluation_id.strip():
        issues.append(
            ScoreIssue(path, line_number, identifier, "evaluation_id must be non-empty")
        )
    if not isinstance(raw["generated_answer"], str):
        issues.append(
            ScoreIssue(path, line_number, identifier, "generated_answer must be a string")
        )
    if not isinstance(raw["citations"], list):
        issues.append(ScoreIssue(path, line_number, identifier, "citations must be a list"))
    if raw["error"] is not None and not isinstance(raw["error"], str):
        issues.append(ScoreIssue(path, line_number, identifier, "error must be a string or null"))
    return JsonRecord(line_number, raw)


def _load_run_records(path: Path, issues: list[ScoreIssue]) -> list[JsonRecord]:
    records: list[JsonRecord] = []
    for line_number, raw in _read_jsonl(path, issues):
        record = _validate_run_record(raw, path, line_number, issues)
        if record is not None:
            records.append(record)
    _add_id_and_run_id_issues(records, path, issues, "run")
    return records


def _load_annotations(
    path: Path, issues: list[ScoreIssue]
) -> dict[str, EvaluationAnnotation]:
    annotations: dict[str, EvaluationAnnotation] = {}
    for line_number, raw in _read_jsonl(path, issues):
        if not isinstance(raw, dict):
            issues.append(
                ScoreIssue(path, line_number, None, "annotation record must be an object")
            )
            continue
        evaluation_id = raw.get("evaluation_id")
        try:
            annotation = EvaluationAnnotation.model_validate(raw)
        except ValidationError as error:
            issues.append(
                ScoreIssue(
                    path,
                    line_number,
                    evaluation_id if isinstance(evaluation_id, str) else None,
                    f"annotation validation failed: {error}",
                )
            )
            continue
        if annotation.evaluation_id in annotations:
            issues.append(
                ScoreIssue(
                    path,
                    line_number,
                    annotation.evaluation_id,
                    "duplicate evaluation_id in annotations",
                )
            )
            continue
        annotations[annotation.evaluation_id] = annotation
    return annotations


def _add_id_and_run_id_issues(
    records: list[JsonRecord],
    path: Path,
    issues: list[ScoreIssue],
    label: str,
) -> None:
    seen_ids: set[str] = set()
    run_ids: set[str] = set()
    for record in records:
        if record.evaluation_id in seen_ids:
            issues.append(
                ScoreIssue(
                    path,
                    record.line_number,
                    record.evaluation_id,
                    f"duplicate evaluation_id in {label} file",
                )
            )
        seen_ids.add(record.evaluation_id)
        run_ids.add(record.raw["run_id"])
    if len(run_ids) > 1:
        issues.append(ScoreIssue(path, None, None, f"multiple run_id values in {label} file"))


def _default_score_path(run_file: Path, run_id: str) -> Path:
    reports_directory = run_file.parent.parent
    return reports_directory / "scores" / f"{run_id}.jsonl"


def _scored_run_path(run_file: Path, run_id: str) -> Path:
    return run_file.with_name(f"{run_id}.scored.jsonl")


def _atomic_write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
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
                temporary_file.write(json.dumps(record, ensure_ascii=False) + "\n")
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def prepare_score_file(
    run_file: Path,
    *,
    annotations_path: Path | None = None,
    score_file: Path | None = None,
) -> ScoreCommandResult:
    issues: list[ScoreIssue] = []
    run_records = _load_run_records(run_file, issues)
    annotation_path = annotations_path or ROOT / "evaluation" / "annotations.jsonl"
    annotations = _load_annotations(annotation_path, issues)
    for record in run_records:
        if record.evaluation_id not in annotations:
            issues.append(
                ScoreIssue(
                    annotation_path,
                    None,
                    record.evaluation_id,
                    "run item has no matching annotation",
                )
            )
    if issues:
        return ScoreCommandResult(1, None, issues, "Score-file preparation failed.")
    if not run_records:
        return ScoreCommandResult(2, None, [], "Run file contains no results.")
    run_id = run_records[0].raw["run_id"]
    output_path = score_file or _default_score_path(run_file, run_id)
    if output_path.exists():
        return ScoreCommandResult(
            2,
            None,
            [],
            f"Score file already exists and was not overwritten: {output_path}",
        )
    prepared_records = []
    for record in run_records:
        annotation = annotations[record.evaluation_id]
        prepared_records.append(
            {
                "run_id": run_id,
                "evaluation_id": record.evaluation_id,
                "generated_answer": record.raw["generated_answer"],
                "citations": record.raw["citations"],
                "key_points": annotation.key_points,
                "expected_citations": [
                    citation.model_dump(mode="json")
                    for citation in annotation.expected_citations
                ],
                "correctness": None,
                "citation_accuracy": None,
                "hallucination_rate": None,
                "reviewer": None,
                "notes": "",
            }
        )
    _atomic_write_jsonl(output_path, prepared_records)
    return ScoreCommandResult(0, output_path, [], "Score file prepared.")


def _validate_score_number(
    value: object,
    field: str,
    path: Path,
    line_number: int,
    evaluation_id: str | None,
    issues: list[ScoreIssue],
) -> None:
    if value is None:
        return
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        issues.append(
            ScoreIssue(path, line_number, evaluation_id, f"{field} must be a number or null")
        )
        return
    lower, upper = (0, 1) if field == "hallucination_rate" else (0, 4)
    if not lower <= float(value) <= upper:
        issues.append(
            ScoreIssue(
                path,
                line_number,
                evaluation_id,
                f"{field} must be between {lower} and {upper}",
            )
        )
    elif field != "hallucination_rate" and int(value) != value:
        issues.append(
            ScoreIssue(
                path,
                line_number,
                evaluation_id,
                f"{field} must be an integer from 0 to 4",
            )
        )


def _validate_score_record(
    raw: object,
    path: Path,
    line_number: int,
    issues: list[ScoreIssue],
) -> JsonRecord | None:
    if not isinstance(raw, dict):
        issues.append(ScoreIssue(path, line_number, None, "score record must be an object"))
        return None
    evaluation_id = raw.get("evaluation_id")
    identifier = evaluation_id if isinstance(evaluation_id, str) else None
    missing = SCORE_FILE_REQUIRED_FIELDS - raw.keys()
    if missing:
        issues.append(
            ScoreIssue(
                path,
                line_number,
                identifier,
                "missing required fields: " + ", ".join(sorted(missing)),
            )
        )
        return None
    if not isinstance(raw["run_id"], str) or not raw["run_id"].strip():
        issues.append(ScoreIssue(path, line_number, identifier, "run_id must be non-empty"))
    if not isinstance(evaluation_id, str) or not evaluation_id.strip():
        issues.append(
            ScoreIssue(path, line_number, identifier, "evaluation_id must be non-empty")
        )
    if not isinstance(raw["generated_answer"], str):
        issues.append(
            ScoreIssue(path, line_number, identifier, "generated_answer must be a string")
        )
    if not isinstance(raw["citations"], list):
        issues.append(ScoreIssue(path, line_number, identifier, "citations must be a list"))
    if not isinstance(raw["key_points"], list):
        issues.append(ScoreIssue(path, line_number, identifier, "key_points must be a list"))
    if not isinstance(raw["expected_citations"], list):
        issues.append(
            ScoreIssue(path, line_number, identifier, "expected_citations must be a list")
        )
    if raw["reviewer"] is not None and not isinstance(raw["reviewer"], str):
        issues.append(ScoreIssue(path, line_number, identifier, "reviewer must be a string or null"))
    if not isinstance(raw["notes"], str):
        issues.append(ScoreIssue(path, line_number, identifier, "notes must be a string"))
    for field in SCORE_FIELDS:
        _validate_score_number(raw[field], field, path, line_number, identifier, issues)
    return JsonRecord(line_number, raw)


def _load_score_records(path: Path, issues: list[ScoreIssue]) -> list[JsonRecord]:
    records: list[JsonRecord] = []
    for line_number, raw in _read_jsonl(path, issues):
        record = _validate_score_record(raw, path, line_number, issues)
        if record is not None:
            records.append(record)
    _add_id_and_run_id_issues(records, path, issues, "score")
    return records


def apply_scores(run_file: Path, score_file: Path) -> ScoreCommandResult:
    issues: list[ScoreIssue] = []
    run_records = _load_run_records(run_file, issues)
    score_records = _load_score_records(score_file, issues)
    if issues:
        return ScoreCommandResult(1, None, issues, "Score application failed.")
    if not run_records:
        return ScoreCommandResult(2, None, [], "Run file contains no results.")
    run_id = run_records[0].raw["run_id"]
    score_ids = {record.evaluation_id for record in score_records}
    run_ids = {record.evaluation_id for record in run_records}
    if score_ids != run_ids:
        missing = sorted(run_ids - score_ids)
        extra = sorted(score_ids - run_ids)
        if missing:
            issues.append(
                ScoreIssue(score_file, None, None, "missing score items: " + ", ".join(missing))
            )
        if extra:
            issues.append(
                ScoreIssue(score_file, None, None, "extra score items: " + ", ".join(extra))
            )
    score_by_id = {record.evaluation_id: record for record in score_records}
    for record in score_records:
        if record.raw["run_id"] != run_id:
            issues.append(
                ScoreIssue(
                    score_file,
                    record.line_number,
                    record.evaluation_id,
                    "score record run_id does not match the run file",
                )
            )
    for run_record in run_records:
        score_record = score_by_id.get(run_record.evaluation_id)
        if score_record is None:
            continue
        scores = [score_record.raw[field] for field in SCORE_FIELDS]
        is_success = run_record.raw["error"] is None
        has_any_score = any(value is not None for value in scores)
        reviewer = score_record.raw["reviewer"]
        if is_success and not all(value is not None for value in scores):
            issues.append(
                ScoreIssue(
                    score_file,
                    score_record.line_number,
                    run_record.evaluation_id,
                    "successful run item requires complete scores",
                )
            )
        if is_success and (not isinstance(reviewer, str) or not reviewer.strip()):
            issues.append(
                ScoreIssue(
                    score_file,
                    score_record.line_number,
                    run_record.evaluation_id,
                    "successful run item requires a non-empty reviewer",
                )
            )
        if not is_success and has_any_score:
            if not all(value is not None for value in scores):
                issues.append(
                    ScoreIssue(
                        score_file,
                        score_record.line_number,
                        run_record.evaluation_id,
                        "partially scored failed item requires all score fields",
                    )
                )
            if not isinstance(reviewer, str) or not reviewer.strip():
                issues.append(
                    ScoreIssue(
                        score_file,
                        score_record.line_number,
                        run_record.evaluation_id,
                        "scored failed item requires a non-empty reviewer",
                    )
                )
    if issues:
        return ScoreCommandResult(1, None, issues, "Score application failed.")

    output_path = _scored_run_path(run_file, run_id)
    output_records: list[dict[str, Any]] = []
    for run_record in run_records:
        score_record = score_by_id[run_record.evaluation_id]
        output_records.append(
            {
                **run_record.raw,
                "scores": {field: score_record.raw[field] for field in SCORE_FIELDS},
                "score_reviewer": score_record.raw["reviewer"],
                "score_notes": score_record.raw["notes"],
            }
        )
    _atomic_write_jsonl(output_path, output_records)
    return ScoreCommandResult(0, output_path, [], "Scores applied to a new run file.")


def _print_result(result: ScoreCommandResult) -> None:
    if result.issues:
        print(f"Score command failed with {len(result.issues)} issue(s):")
        for issue in result.issues:
            print(f"- {issue.format()}")
        return
    print(result.message)
    if result.output_path is not None:
        print(f"Output: {result.output_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare and apply human evaluation scores.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare_parser = subparsers.add_parser("prepare")
    prepare_parser.add_argument("--run-file", type=Path, required=True)
    prepare_parser.add_argument("--annotations", type=Path, default=ROOT / "evaluation" / "annotations.jsonl")
    prepare_parser.add_argument("--score-file", type=Path, default=None)
    apply_parser = subparsers.add_parser("apply")
    apply_parser.add_argument("--run-file", type=Path, required=True)
    apply_parser.add_argument("--score-file", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "prepare":
        result = prepare_score_file(
            args.run_file,
            annotations_path=args.annotations,
            score_file=args.score_file,
        )
    else:
        result = apply_scores(args.run_file, args.score_file)
    _print_result(result)
    return result.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
