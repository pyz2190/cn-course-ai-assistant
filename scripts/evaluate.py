from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol
from uuid import uuid4

from pydantic import BaseModel, ValidationError

ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.domain.models import EvaluationAnnotation, EvaluationItem


@dataclass(frozen=True)
class DataIssue:
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
class RuntimeParameters:
    model: str | None
    embedding: str | None
    reranker: str | None
    top_k: int | None
    git_commit: str | None


@dataclass(frozen=True)
class AdapterResponse:
    generated_answer: str
    citations: list[dict[str, Any]]
    runtime: dict[str, Any] | None = None


@dataclass(frozen=True)
class RagRequest:
    evaluation_id: str
    question: str
    knowledge_point_ids: list[str]


class RagAdapter(Protocol):
    def answer(
        self,
        item: RagRequest,
        runtime: RuntimeParameters,
    ) -> AdapterResponse: ...


class UnconfiguredRagAdapter:
    def answer(
        self,
        item: RagRequest,
        runtime: RuntimeParameters,
    ) -> AdapterResponse:
        del item, runtime
        raise NotImplementedError("Member D RAG adapter is not configured.")


@dataclass(frozen=True)
class EvaluationRun:
    run_id: str
    exit_code: int
    report_path: Path | None
    data_issues: list[DataIssue]
    results: list[dict[str, Any]]
    planned_evaluation_ids: list[str]


def _validation_error_message(error: ValidationError) -> str:
    return "; ".join(
        f"{'.'.join(str(part) for part in item['loc'])}: {item['msg']}"
        for item in error.errors()
    )


def _load_jsonl(
    path: Path,
    model: type[BaseModel],
    issues: list[DataIssue],
) -> list[Record]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        issues.append(DataIssue(path, None, None, f"cannot read JSONL file: {error}"))
        return []

    records: list[Record] = []
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as error:
            issues.append(
                DataIssue(path, line_number, None, f"invalid JSON: {error.msg}")
            )
            continue
        if not isinstance(payload, dict):
            issues.append(
                DataIssue(path, line_number, None, "JSONL record must be an object")
            )
            continue
        evaluation_id = payload.get("evaluation_id")
        try:
            value = model.model_validate(payload)
        except ValidationError as error:
            issues.append(
                DataIssue(
                    path,
                    line_number,
                    evaluation_id if isinstance(evaluation_id, str) else None,
                    f"model validation failed: {_validation_error_message(error)}",
                )
            )
            continue
        records.append(Record(line_number, payload, value))
    return records


def _add_duplicate_issues(
    records: list[Record], path: Path, issues: list[DataIssue]
) -> None:
    records_by_id: dict[str, list[Record]] = defaultdict(list)
    for record in records:
        records_by_id[record.evaluation_id].append(record)
    for evaluation_id, matches in records_by_id.items():
        for record in matches[1:]:
            issues.append(
                DataIssue(
                    path,
                    record.line_number,
                    evaluation_id,
                    f"duplicate evaluation_id; first appears on line {matches[0].line_number}",
                )
            )


def _git_commit() -> str | None:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        capture_output=True,
        check=False,
        text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def _new_run_id() -> str:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"RUN-{timestamp}-{uuid4().hex[:8]}"


def _runtime_parameters(
    model: str | None,
    embedding: str | None,
    reranker: str | None,
    top_k: int | None,
) -> RuntimeParameters:
    return RuntimeParameters(
        model=model,
        embedding=embedding,
        reranker=reranker,
        top_k=top_k,
        git_commit=_git_commit(),
    )


def _validate_execution_data(
    evaluation_directory: Path,
) -> tuple[list[Record], list[DataIssue]]:
    issues: list[DataIssue] = []
    evaluation_set_path = evaluation_directory / "evaluation_set.jsonl"
    annotations_path = evaluation_directory / "annotations.jsonl"
    evaluation_set = _load_jsonl(evaluation_set_path, EvaluationItem, issues)
    annotations = _load_jsonl(annotations_path, EvaluationAnnotation, issues)
    _add_duplicate_issues(evaluation_set, evaluation_set_path, issues)
    _add_duplicate_issues(annotations, annotations_path, issues)

    annotations_by_id = {record.evaluation_id: record for record in annotations}
    for evaluation_item in evaluation_set:
        annotation = annotations_by_id.get(evaluation_item.evaluation_id)
        if annotation is None:
            issues.append(
                DataIssue(
                    evaluation_set_path,
                    evaluation_item.line_number,
                    evaluation_item.evaluation_id,
                    "evaluation set item has no matching annotation",
                )
            )
            continue
        annotation_value = annotation.value
        if not isinstance(annotation_value, EvaluationAnnotation):
            continue
        if annotation_value.review_status.value != "approved":
            issues.append(
                DataIssue(
                    evaluation_set_path,
                    evaluation_item.line_number,
                    evaluation_item.evaluation_id,
                    "evaluation set item is not approved",
                )
            )
        if not annotation_value.expected_citations:
            issues.append(
                DataIssue(
                    annotations_path,
                    annotation.line_number,
                    evaluation_item.evaluation_id,
                    "approved evaluation item requires at least one expected citation",
                )
            )
    return evaluation_set, issues


def run_evaluation(
    evaluation_directory: Path | None = None,
    reports_directory: Path | None = None,
    adapter: RagAdapter | None = None,
    *,
    dry_run: bool = False,
    model: str | None = None,
    embedding: str | None = None,
    reranker: str | None = None,
    top_k: int | None = None,
) -> EvaluationRun:
    directory = evaluation_directory or ROOT / "evaluation"
    run_id = _new_run_id()
    evaluation_set, data_issues = _validate_execution_data(directory)
    planned_evaluation_ids = [record.evaluation_id for record in evaluation_set]
    if data_issues:
        return EvaluationRun(run_id, 1, None, data_issues, [], planned_evaluation_ids)
    if not evaluation_set or dry_run:
        return EvaluationRun(run_id, 0, None, [], [], planned_evaluation_ids)

    runtime = _runtime_parameters(model, embedding, reranker, top_k)
    active_adapter = adapter or UnconfiguredRagAdapter()
    results: list[dict[str, Any]] = []
    had_execution_error = False
    for record in evaluation_set:
        item = record.value
        if not isinstance(item, EvaluationItem):
            continue
        request = RagRequest(
            evaluation_id=item.evaluation_id,
            question=item.question,
            knowledge_point_ids=item.knowledge_point_ids,
        )
        try:
            response = active_adapter.answer(request, runtime)
            generated_answer = response.generated_answer
            citations = response.citations
            error_message = None
        except Exception as error:
            generated_answer = ""
            citations = []
            error_message = f"{type(error).__name__}: {error}"
            had_execution_error = True
        results.append(
            {
                "run_id": run_id,
                "evaluation_id": item.evaluation_id,
                "generated_answer": generated_answer,
                "citations": citations,
                "scores": None,
                "error": error_message,
                "runtime": {
                    **asdict(runtime),
                    "adapter": response.runtime if error_message is None else None,
                },
            }
        )

    output_directory = reports_directory or directory / "reports" / "runs"
    output_directory.mkdir(parents=True, exist_ok=True)
    report_path = output_directory / f"{run_id}.jsonl"
    report_path.write_text(
        "".join(json.dumps(result, ensure_ascii=False) + "\n" for result in results),
        encoding="utf-8",
    )
    return EvaluationRun(
        run_id,
        2 if had_execution_error else 0,
        report_path,
        [],
        results,
        planned_evaluation_ids,
    )


def _print_run(run: EvaluationRun, *, dry_run: bool) -> None:
    print(f"Run ID: {run.run_id}")
    if run.data_issues:
        print(
            f"Evaluation data validation failed with {len(run.data_issues)} issue(s):"
        )
        for issue in run.data_issues:
            print(f"- {issue.format()}")
        return
    if not run.planned_evaluation_ids:
        print("No executable evaluation items.")
        return
    if dry_run:
        print("Dry run: validated execution plan without calling a RAG adapter.")
        for evaluation_id in run.planned_evaluation_ids:
            print(f"- {evaluation_id}")
        return
    print(f"Executed items: {len(run.results)}")
    print(f"Report: {run.report_path}")
    if run.exit_code == 2:
        print("One or more RAG calls failed; see the report for per-item errors.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run approved evaluation items.")
    parser.add_argument(
        "--dry-run", action="store_true", help="validate and print the execution plan"
    )
    parser.add_argument("--evaluation-dir", type=Path, default=ROOT / "evaluation")
    parser.add_argument("--reports-dir", type=Path, default=None)
    parser.add_argument("--model", default=None)
    parser.add_argument("--embedding", default=None)
    parser.add_argument("--reranker", default=None)
    parser.add_argument("--top-k", type=int, default=None)
    args = parser.parse_args()
    run = run_evaluation(
        args.evaluation_dir,
        args.reports_dir,
        dry_run=args.dry_run,
        model=args.model,
        embedding=args.embedding,
        reranker=args.reranker,
        top_k=args.top_k,
    )
    _print_run(run, dry_run=args.dry_run)
    return run.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
